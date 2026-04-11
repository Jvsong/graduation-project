#!/usr/bin/env python3
"""
定时任务调度器
支持cron表达式定时执行测试任务
"""

import os
import sys
import time
import threading
import re
import json
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from enum import Enum

from utils.logger import get_logger
from utils.config_manager import get_config


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class TaskType(Enum):
    """任务类型枚举"""
    TEST_SUITE = "test_suite"
    TEST_MODULE = "test_module"
    CUSTOM_COMMAND = "custom_command"


class ScheduledTask:
    """
    定时任务类
    封装定时任务的配置和执行逻辑
    """

    def __init__(self,
                 task_id: str,
                 task_type: TaskType,
                 cron_expression: str,
                 task_config: Dict[str, Any],
                 callback: Optional[Callable] = None):
        """
        初始化定时任务

        Args:
            task_id: 任务ID
            task_type: 任务类型
            cron_expression: cron表达式 (分钟 小时 日 月 星期)
            task_config: 任务配置
            callback: 任务完成后的回调函数
        """
        self.task_id = task_id
        self.task_type = task_type
        self.cron_expression = cron_expression
        self.task_config = task_config
        self.callback = callback

        # 任务状态
        self.status = TaskStatus.PENDING
        self.last_run_time: Optional[datetime] = None
        self.next_run_time: Optional[datetime] = None
        self.execution_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.last_error: Optional[str] = None

        # 解析cron表达式
        self.minute, self.hour, self.day, self.month, self.weekday = self._parse_cron(cron_expression)

        # 计算下次执行时间
        self._calculate_next_run()

    def _parse_cron(self, cron_expr: str) -> tuple:
        """
        解析cron表达式

        Args:
            cron_expr: cron表达式字符串

        Returns:
            tuple: (分钟, 小时, 日, 月, 星期)
        """
        parts = cron_expr.strip().split()
        if len(parts) != 5:
            raise ValueError(f"无效的cron表达式: {cron_expr}，应为5个部分: 分钟 小时 日 月 星期")

        # 解析每个部分
        minute = self._parse_cron_part(parts[0], 0, 59)
        hour = self._parse_cron_part(parts[1], 0, 23)
        day = self._parse_cron_part(parts[2], 1, 31)
        month = self._parse_cron_part(parts[3], 1, 12)
        weekday = self._parse_cron_part(parts[4], 0, 6)  # 0=周日, 1=周一, ..., 6=周六

        return minute, hour, day, month, weekday

    def _parse_cron_part(self, part: str, min_val: int, max_val: int) -> List[int]:
        """
        解析cron表达式的单个部分

        Args:
            part: cron部分字符串
            min_val: 最小值
            max_val: 最大值

        Returns:
            List[int]: 允许的值列表
        """
        if part == "*":
            return list(range(min_val, max_val + 1))

        # 处理逗号分隔的值
        if "," in part:
            values = []
            for subpart in part.split(","):
                values.extend(self._parse_cron_part(subpart.strip(), min_val, max_val))
            return sorted(set(values))

        # 处理范围
        if "-" in part:
            start_str, end_str = part.split("-")
            start = int(start_str)
            end = int(end_str)
            if start < min_val or end > max_val or start > end:
                raise ValueError(f"范围 {part} 超出允许范围 {min_val}-{max_val}")
            return list(range(start, end + 1))

        # 处理步长
        if "/" in part:
            step_part, step_str = part.split("/")
            step = int(step_str)

            # 如果步长前是范围
            if "-" in step_part:
                range_start_str, range_end_str = step_part.split("-")
                range_start = int(range_start_str)
                range_end = int(range_end_str)
                return list(range(range_start, range_end + 1, step))
            # 如果步长前是*
            elif step_part == "*":
                return list(range(min_val, max_val + 1, step))
            # 如果步长前是单个值
            else:
                start = int(step_part)
                return [start + i * step for i in range((max_val - start) // step + 1)]

        # 单个值
        value = int(part)
        if value < min_val or value > max_val:
            raise ValueError(f"值 {value} 超出允许范围 {min_val}-{max_val}")
        return [value]

    def _calculate_next_run(self, now: Optional[datetime] = None) -> None:
        """
        计算下次执行时间

        Args:
            now: 当前时间，如果为None则使用当前系统时间
        """
        if now is None:
            now = datetime.now()

        # 从下一分钟开始
        candidate = now.replace(second=0, microsecond=0) + timedelta(minutes=1)

        # 寻找匹配的时间
        for _ in range(100000):  # 防止无限循环
            # 检查月份
            if candidate.month not in self.month:
                # 跳到下个月的第一天
                next_month = candidate.month + 1
                next_year = candidate.year
                if next_month > 12:
                    next_month = 1
                    next_year += 1
                candidate = candidate.replace(year=next_year, month=next_month, day=1, hour=0, minute=0)
                continue

            # 检查日期
            if candidate.day not in self.day:
                # 跳到下一天
                candidate += timedelta(days=1)
                candidate = candidate.replace(hour=0, minute=0)
                continue

            # 检查星期
            weekday = candidate.weekday()  # 0=周一, 6=周日
            # 转换为cron格式 (0=周日, 1=周一, ..., 6=周六)
            cron_weekday = (weekday + 1) % 7
            if cron_weekday not in self.weekday:
                # 跳到下一天
                candidate += timedelta(days=1)
                candidate = candidate.replace(hour=0, minute=0)
                continue

            # 检查小时
            if candidate.hour not in self.hour:
                # 跳到下一小时
                candidate += timedelta(hours=1)
                candidate = candidate.replace(minute=0)
                continue

            # 检查分钟
            if candidate.minute not in self.minute:
                # 跳到下一分钟
                candidate += timedelta(minutes=1)
                continue

            # 找到匹配的时间
            self.next_run_time = candidate
            return

        # 如果找不到匹配时间，设置为None
        self.next_run_time = None

    def should_run(self, now: Optional[datetime] = None) -> bool:
        """
        检查任务是否应该执行

        Args:
            now: 当前时间

        Returns:
            bool: 是否应该执行
        """
        if now is None:
            now = datetime.now()

        # 检查是否有下次执行时间
        if self.next_run_time is None:
            return False

        # 检查是否到达执行时间
        return now >= self.next_run_time

    def execute(self) -> bool:
        """
        执行任务

        Returns:
            bool: 执行是否成功
        """
        self.status = TaskStatus.RUNNING
        self.last_run_time = datetime.now()
        self.execution_count += 1

        try:
            # 根据任务类型执行
            if self.task_type == TaskType.TEST_SUITE:
                result = self._execute_test_suite()
            elif self.task_type == TaskType.TEST_MODULE:
                result = self._execute_test_module()
            elif self.task_type == TaskType.CUSTOM_COMMAND:
                result = self._execute_custom_command()
            else:
                raise ValueError(f"不支持的任务类型: {self.task_type}")

            # 更新状态
            if result:
                self.status = TaskStatus.COMPLETED
                self.success_count += 1
                self.last_error = None
            else:
                self.status = TaskStatus.FAILED
                self.failure_count += 1

            # 调用回调函数
            if self.callback:
                self.callback(self, result)

            # 计算下次执行时间
            self._calculate_next_run()

            return result

        except Exception as e:
            self.status = TaskStatus.FAILED
            self.failure_count += 1
            self.last_error = str(e)

            # 调用回调函数
            if self.callback:
                self.callback(self, False)

            # 计算下次执行时间
            self._calculate_next_run()

            return False

    def _execute_test_suite(self) -> bool:
        """执行测试套件"""
        suite_name = self.task_config.get("suite_name", "smoke")

        # 这里调用实际的测试执行器
        # 暂时返回模拟结果
        print(f"执行测试套件: {suite_name}")
        return True

    def _execute_test_module(self) -> bool:
        """执行测试模块"""
        module_name = self.task_config.get("module_name", "")

        # 这里调用实际的测试执行器
        # 暂时返回模拟结果
        print(f"执行测试模块: {module_name}")
        return True

    def _execute_custom_command(self) -> bool:
        """执行自定义命令"""
        command = self.task_config.get("command", "")

        # 执行命令
        print(f"执行自定义命令: {command}")
        return True

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type.value,
            "cron_expression": self.cron_expression,
            "task_config": self.task_config,
            "status": self.status.value,
            "last_run_time": self.last_run_time.isoformat() if self.last_run_time else None,
            "next_run_time": self.next_run_time.isoformat() if self.next_run_time else None,
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "last_error": self.last_error
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScheduledTask':
        """从字典创建实例"""
        task = cls(
            task_id=data["task_id"],
            task_type=TaskType(data["task_type"]),
            cron_expression=data["cron_expression"],
            task_config=data["task_config"],
            callback=None  # 回调函数需要单独设置
        )

        # 恢复状态
        if data.get("last_run_time"):
            task.last_run_time = datetime.fromisoformat(data["last_run_time"])
        if data.get("next_run_time"):
            task.next_run_time = datetime.fromisoformat(data["next_run_time"])

        task.status = TaskStatus(data.get("status", "pending"))
        task.execution_count = data.get("execution_count", 0)
        task.success_count = data.get("success_count", 0)
        task.failure_count = data.get("failure_count", 0)
        task.last_error = data.get("last_error")

        return task


class TaskScheduler:
    """
    任务调度器
    管理多个定时任务的执行
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化任务调度器

        Args:
            config: 配置字典
        """
        self.logger = get_logger(self.__class__.__name__)

        # 获取配置
        if config is None:
            self.config = get_config()
        else:
            self.config = config

        # 任务存储
        self.tasks: Dict[str, ScheduledTask] = {}
        self.task_lock = threading.Lock()

        # 调度器状态
        self.running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        self.check_interval = 60  # 检查间隔（秒）

        # 任务存储文件
        self.storage_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'config', 'scheduled_tasks.json'
        )

        self.logger.info("任务调度器初始化完成")

    def add_task(self, task: ScheduledTask) -> bool:
        """
        添加定时任务

        Args:
            task: 定时任务

        Returns:
            bool: 是否添加成功
        """
        with self.task_lock:
            if task.task_id in self.tasks:
                self.logger.error(f"任务ID已存在: {task.task_id}")
                return False

            self.tasks[task.task_id] = task
            self.logger.info(f"添加定时任务: {task.task_id} ({task.task_type.value})")

            # 保存到文件
            self._save_tasks()

            return True

    def remove_task(self, task_id: str) -> bool:
        """
        移除定时任务

        Args:
            task_id: 任务ID

        Returns:
            bool: 是否移除成功
        """
        with self.task_lock:
            if task_id not in self.tasks:
                self.logger.error(f"任务ID不存在: {task_id}")
                return False

            del self.tasks[task_id]
            self.logger.info(f"移除定时任务: {task_id}")

            # 保存到文件
            self._save_tasks()

            return True

    def update_task(self, task_id: str, **kwargs) -> bool:
        """
        更新定时任务

        Args:
            task_id: 任务ID
            **kwargs: 更新参数

        Returns:
            bool: 是否更新成功
        """
        with self.task_lock:
            if task_id not in self.tasks:
                self.logger.error(f"任务ID不存在: {task_id}")
                return False

            task = self.tasks[task_id]

            # 更新任务属性
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)
                else:
                    self.logger.warning(f"任务没有属性: {key}")

            # 重新计算下次执行时间
            if 'cron_expression' in kwargs:
                task._calculate_next_run()

            self.logger.info(f"更新定时任务: {task_id}")

            # 保存到文件
            self._save_tasks()

            return True

    def start(self) -> bool:
        """
        启动调度器

        Returns:
            bool: 是否启动成功
        """
        if self.running:
            self.logger.warning("调度器已经在运行")
            return False

        # 加载保存的任务
        self._load_tasks()

        # 启动调度线程
        self.running = True
        self.scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            name="TaskScheduler",
            daemon=True
        )
        self.scheduler_thread.start()

        self.logger.info("任务调度器已启动")
        return True

    def stop(self) -> bool:
        """
        停止调度器

        Returns:
            bool: 是否停止成功
        """
        if not self.running:
            self.logger.warning("调度器已经停止")
            return False

        self.running = False

        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=10)

        self.logger.info("任务调度器已停止")
        return True

    def run_once(self) -> None:
        """执行一次任务检查"""
        now = datetime.now()
        tasks_to_run = []

        with self.task_lock:
            # 找出需要执行的任务
            for task in self.tasks.values():
                if task.should_run(now):
                    tasks_to_run.append(task)

        # 执行任务
        for task in tasks_to_run:
            self.logger.info(f"执行定时任务: {task.task_id}")

            # 在线程中执行任务
            def execute_task(t=task):
                try:
                    t.execute()
                except Exception as e:
                    self.logger.error(f"任务执行异常: {t.task_id} - {e}")

            thread = threading.Thread(target=execute_task, daemon=True)
            thread.start()

    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """
        获取任务

        Args:
            task_id: 任务ID

        Returns:
            Optional[ScheduledTask]: 任务对象，如果不存在则返回None
        """
        with self.task_lock:
            return self.tasks.get(task_id)

    def list_tasks(self) -> List[Dict[str, Any]]:
        """
        列出所有任务

        Returns:
            List[Dict[str, Any]]: 任务信息列表
        """
        with self.task_lock:
            return [task.to_dict() for task in self.tasks.values()]

    def get_task_summary(self) -> Dict[str, Any]:
        """
        获取任务摘要

        Returns:
            Dict[str, Any]: 任务摘要信息
        """
        with self.task_lock:
            total = len(self.tasks)
            running = len([t for t in self.tasks.values() if t.status == TaskStatus.RUNNING])
            pending = len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING])
            completed = len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED])
            failed = len([t for t in self.tasks.values() if t.status == TaskStatus.FAILED])

            total_executions = sum(t.execution_count for t in self.tasks.values())
            total_success = sum(t.success_count for t in self.tasks.values())
            total_failure = sum(t.failure_count for t in self.tasks.values())

            success_rate = (total_success / total_executions * 100) if total_executions > 0 else 0

            return {
                "total_tasks": total,
                "running_tasks": running,
                "pending_tasks": pending,
                "completed_tasks": completed,
                "failed_tasks": failed,
                "total_executions": total_executions,
                "total_success": total_success,
                "total_failure": total_failure,
                "success_rate": success_rate,
                "scheduler_running": self.running,
                "check_interval": self.check_interval
            }

    def _scheduler_loop(self) -> None:
        """调度器主循环"""
        self.logger.info("调度器主循环启动")

        while self.running:
            try:
                # 执行任务检查
                self.run_once()

                # 等待下次检查
                for _ in range(self.check_interval):
                    if not self.running:
                        break
                    time.sleep(1)

            except Exception as e:
                self.logger.error(f"调度器循环异常: {e}")
                time.sleep(10)  # 出错后等待10秒

        self.logger.info("调度器主循环结束")

    def _save_tasks(self) -> bool:
        """保存任务到文件"""
        try:
            # 转换为可序列化的格式
            tasks_data = {
                task_id: task.to_dict()
                for task_id, task in self.tasks.items()
            }

            # 确保目录存在
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)

            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(tasks_data, f, indent=2, ensure_ascii=False)

            self.logger.debug(f"任务保存到文件: {self.storage_file}")
            return True

        except Exception as e:
            self.logger.error(f"保存任务失败: {e}")
            return False

    def _load_tasks(self) -> bool:
        """从文件加载任务"""
        try:
            if not os.path.exists(self.storage_file):
                self.logger.warning(f"任务存储文件不存在: {self.storage_file}")
                return False

            with open(self.storage_file, 'r', encoding='utf-8') as f:
                tasks_data = json.load(f)

            # 加载任务
            with self.task_lock:
                self.tasks.clear()
                for task_id, task_dict in tasks_data.items():
                    try:
                        task = ScheduledTask.from_dict(task_dict)
                        self.tasks[task_id] = task
                    except Exception as e:
                        self.logger.error(f"加载任务失败 {task_id}: {e}")

            self.logger.info(f"从文件加载 {len(self.tasks)} 个任务")
            return True

        except Exception as e:
            self.logger.error(f"加载任务失败: {e}")
            return False


# 快捷函数
def get_task_scheduler(config: Optional[Dict[str, Any]] = None) -> TaskScheduler:
    """
    获取任务调度器实例

    Args:
        config: 配置字典

    Returns:
        TaskScheduler: 任务调度器实例
    """
    return TaskScheduler(config)


def create_test_task(task_id: str,
                     task_type: TaskType,
                     cron_expression: str,
                     **kwargs) -> ScheduledTask:
    """
    创建测试任务

    Args:
        task_id: 任务ID
        task_type: 任务类型
        cron_expression: cron表达式
        **kwargs: 任务配置

    Returns:
        ScheduledTask: 定时任务实例
    """
    task_config = {}

    if task_type == TaskType.TEST_SUITE:
        task_config["suite_name"] = kwargs.get("suite_name", "smoke")
    elif task_type == TaskType.TEST_MODULE:
        task_config["module_name"] = kwargs.get("module_name", "")
    elif task_type == TaskType.CUSTOM_COMMAND:
        task_config["command"] = kwargs.get("command", "")

    return ScheduledTask(
        task_id=task_id,
        task_type=task_type,
        cron_expression=cron_expression,
        task_config=task_config
    )


if __name__ == "__main__":
    # 测试TaskScheduler类
    print("测试TaskScheduler类...")

    # 创建调度器
    scheduler = TaskScheduler()

    # 创建测试任务
    smoke_task = create_test_task(
        task_id="daily_smoke_test",
        task_type=TaskType.TEST_SUITE,
        cron_expression="0 2 * * *",  # 每天凌晨2点
        suite_name="smoke"
    )

    regression_task = create_test_task(
        task_id="weekly_regression_test",
        task_type=TaskType.TEST_SUITE,
        cron_expression="0 4 * * 0",  # 每周日凌晨4点
        suite_name="regression"
    )

    # 添加任务
    scheduler.add_task(smoke_task)
    scheduler.add_task(regression_task)

    # 列出任务
    tasks = scheduler.list_tasks()
    print(f"任务数量: {len(tasks)}")
    for task in tasks:
        print(f"  - {task['task_id']}: {task['cron_expression']} ({task['task_type']})")

    # 获取摘要
    summary = scheduler.get_task_summary()
    print(f"任务摘要: {summary}")

    # 测试单次执行
    print("执行一次任务检查...")
    scheduler.run_once()

    # 清理
    scheduler.remove_task("daily_smoke_test")
    scheduler.remove_task("weekly_regression_test")

    print("测试完成")