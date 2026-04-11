#!/usr/bin/env python3
"""
并行测试执行器
支持多线程/多进程并行执行测试，提高测试效率
"""

import os
import sys
import time
import threading
import concurrent.futures
from typing import List, Dict, Any, Optional, Callable, Tuple
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from datetime import datetime

from utils.logger import get_logger
from utils.config_manager import get_config


class ParallelExecutor:
    """
    并行测试执行器
    支持多线程和多进程并行执行
    """

    def __init__(self,
                 max_workers: Optional[int] = None,
                 executor_type: str = "thread",
                 config: Optional[Dict[str, Any]] = None):
        """
        初始化并行执行器

        Args:
            max_workers: 最大工作线程/进程数
            executor_type: 执行器类型 ("thread" 或 "process")
            config: 配置字典
        """
        self.logger = get_logger(self.__class__.__name__)

        # 获取配置
        if config is None:
            self.config = get_config()
        else:
            self.config = config

        # 执行配置
        self.executor_type = executor_type
        self.max_workers = max_workers or self.config.get('test', {}).get('max_workers', 5)

        # 创建执行器
        if executor_type == "process":
            self.executor = ProcessPoolExecutor(max_workers=self.max_workers)
            self.logger.info(f"初始化进程池执行器，最大进程数: {self.max_workers}")
        else:
            self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
            self.logger.info(f"初始化线程池执行器，最大线程数: {self.max_workers}")

        # 结果存储
        self.results: List[Dict[str, Any]] = []
        self.lock = threading.Lock()
        self.task_counter = 0
        self.completed_counter = 0

    def execute_tasks(self,
                     tasks: List[Callable],
                     task_names: Optional[List[str]] = None,
                     timeout: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        并行执行任务列表

        Args:
            tasks: 任务函数列表
            task_names: 任务名称列表（可选）
            timeout: 超时时间（秒）

        Returns:
            List[Dict[str, Any]]: 任务结果列表
        """
        self.logger.info(f"开始并行执行 {len(tasks)} 个任务，执行器类型: {self.executor_type}")

        if task_names is None:
            task_names = [f"Task-{i}" for i in range(len(tasks))]

        if len(tasks) != len(task_names):
            raise ValueError("任务数量和任务名称数量不匹配")

        # 重置状态
        self.results = []
        self.task_counter = len(tasks)
        self.completed_counter = 0

        # 提交任务
        future_to_task = {}
        for task, name in zip(tasks, task_names):
            future = self.executor.submit(self._wrap_task, task, name)
            future_to_task[future] = (task, name)

        # 收集结果
        start_time = time.time()
        try:
            for future in as_completed(future_to_task.keys(), timeout=timeout):
                task_func, task_name = future_to_task[future]
                try:
                    result = future.result(timeout=10)  # 每个任务单独超时
                    self._record_result(task_name, "COMPLETED", result)
                except concurrent.futures.TimeoutError:
                    self._record_result(task_name, "TIMEOUT", None, "任务执行超时")
                except Exception as e:
                    self._record_result(task_name, "FAILED", None, str(e))
        except concurrent.futures.TimeoutError:
            self.logger.warning(f"整体执行超时 ({timeout}秒)")

        end_time = time.time()
        total_duration = end_time - start_time

        self.logger.info(f"并行执行完成，总耗时: {total_duration:.2f}秒")
        self.logger.info(f"任务统计: 总共 {self.task_counter} 个, 完成 {self.completed_counter} 个")

        return self.results

    def execute_test_suites(self,
                           test_suites: List[List[str]],
                           suite_names: Optional[List[str]] = None,
                           timeout: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        并行执行多个测试套件

        Args:
            test_suites: 测试套件列表，每个套件是测试用例名称列表
            suite_names: 套件名称列表
            timeout: 超时时间

        Returns:
            List[Dict[str, Any]]: 套件执行结果
        """
        self.logger.info(f"开始并行执行 {len(test_suites)} 个测试套件")

        if suite_names is None:
            suite_names = [f"TestSuite-{i}" for i in range(len(test_suites))]

        # 创建任务函数
        tasks = []
        for test_suite in test_suites:
            # 这里需要实际的测试套件执行函数
            # 暂时使用模拟函数
            def create_suite_task(suite=test_suite):
                return self._execute_test_suite(suite)

            tasks.append(create_suite_task)

        # 执行任务
        return self.execute_tasks(tasks, suite_names, timeout)

    def execute_by_module(self,
                         modules: List[str],
                         module_names: Optional[List[str]] = None,
                         timeout: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        按模块并行执行测试

        Args:
            modules: 模块名称列表
            module_names: 模块显示名称列表
            timeout: 超时时间

        Returns:
            List[Dict[str, Any]]: 模块执行结果
        """
        self.logger.info(f"开始并行执行 {len(modules)} 个模块")

        # 创建任务函数
        tasks = []
        for module in modules:
            def create_module_task(mod=module):
                return self._execute_test_module(mod)

            tasks.append(create_module_task)

        # 执行任务
        return self.execute_tasks(tasks, module_names or modules, timeout)

    def _wrap_task(self, task_func: Callable, task_name: str) -> Any:
        """
        包装任务函数，添加日志和异常处理

        Args:
            task_func: 任务函数
            task_name: 任务名称

        Returns:
            Any: 任务执行结果
        """
        self.logger.info(f"开始执行任务: {task_name}")
        start_time = time.time()

        try:
            result = task_func()
            end_time = time.time()
            duration = end_time - start_time

            self.logger.info(f"任务完成: {task_name}，耗时: {duration:.2f}秒")
            return result

        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time

            self.logger.error(f"任务失败: {task_name}，耗时: {duration:.2f}秒，错误: {e}")
            raise

    def _execute_test_suite(self, test_suite: List[str]) -> Dict[str, Any]:
        """
        执行测试套件

        Args:
            test_suite: 测试用例名称列表

        Returns:
            Dict[str, Any]: 执行结果
        """
        # 这里需要调用实际的测试执行器
        # 暂时返回模拟结果
        time.sleep(1)  # 模拟执行时间
        return {
            "suite_name": str(test_suite),
            "test_count": len(test_suite),
            "passed": len(test_suite) - 1,
            "failed": 1,
            "duration": 1.0
        }

    def _execute_test_module(self, module_name: str) -> Dict[str, Any]:
        """
        执行测试模块

        Args:
            module_name: 模块名称

        Returns:
            Dict[str, Any]: 执行结果
        """
        # 这里需要调用实际的测试执行器
        # 暂时返回模拟结果
        time.sleep(0.5)  # 模拟执行时间
        return {
            "module_name": module_name,
            "test_count": 10,
            "passed": 9,
            "failed": 1,
            "duration": 0.5
        }

    def _record_result(self,
                      task_name: str,
                      status: str,
                      result: Optional[Any] = None,
                      error: Optional[str] = None) -> None:
        """
        记录任务执行结果

        Args:
            task_name: 任务名称
            status: 状态 (COMPLETED, FAILED, TIMEOUT)
            result: 执行结果
            error: 错误信息
        """
        with self.lock:
            self.completed_counter += 1

            result_data = {
                "task_name": task_name,
                "status": status,
                "result": result,
                "error": error,
                "completion_time": datetime.now().isoformat(),
                "completed_count": self.completed_counter,
                "total_count": self.task_counter
            }

            self.results.append(result_data)

            # 进度日志
            progress = (self.completed_counter / self.task_counter) * 100
            self.logger.info(f"任务进度: {progress:.1f}% ({self.completed_counter}/{self.task_counter})")

    def get_execution_summary(self) -> Dict[str, Any]:
        """
        获取执行摘要

        Returns:
            Dict[str, Any]: 执行摘要
        """
        total = len(self.results)
        if total == 0:
            return {}

        completed = len([r for r in self.results if r["status"] == "COMPLETED"])
        failed = len([r for r in self.results if r["status"] == "FAILED"])
        timeout = len([r for r in self.results if r["status"] == "TIMEOUT"])

        # 计算总时长
        total_duration = 0
        for result in self.results:
            if result.get("result") and "duration" in result["result"]:
                total_duration += result["result"]["duration"]

        return {
            "total_tasks": total,
            "completed_tasks": completed,
            "failed_tasks": failed,
            "timeout_tasks": timeout,
            "completion_rate": (completed / total) * 100 if total > 0 else 0,
            "total_duration": total_duration,
            "executor_type": self.executor_type,
            "max_workers": self.max_workers
        }

    def shutdown(self, wait: bool = True) -> None:
        """
        关闭执行器

        Args:
            wait: 是否等待任务完成
        """
        self.executor.shutdown(wait=wait)
        self.logger.info(f"并行执行器已关闭 (等待: {wait})")


# 快捷函数
def get_parallel_executor(max_workers: Optional[int] = None,
                         executor_type: str = "thread",
                         config: Optional[Dict[str, Any]] = None) -> ParallelExecutor:
    """
    获取并行执行器实例

    Args:
        max_workers: 最大工作线程/进程数
        executor_type: 执行器类型
        config: 配置字典

    Returns:
        ParallelExecutor: 并行执行器实例
    """
    return ParallelExecutor(max_workers, executor_type, config)


if __name__ == "__main__":
    # 测试ParallelExecutor类
    print("测试ParallelExecutor类...")

    # 创建并行执行器
    executor = ParallelExecutor(max_workers=3, executor_type="thread")

    # 创建测试任务
    def task1():
        time.sleep(1)
        return {"result": "Task 1 completed"}

    def task2():
        time.sleep(2)
        return {"result": "Task 2 completed"}

    def task3():
        time.sleep(0.5)
        return {"result": "Task 3 completed"}

    tasks = [task1, task2, task3]
    task_names = ["Task-1", "Task-2", "Task-3"]

    # 执行任务
    print(f"开始执行 {len(tasks)} 个任务...")
    results = executor.execute_tasks(tasks, task_names, timeout=5)

    # 打印结果
    for result in results:
        print(f"任务: {result['task_name']}, 状态: {result['status']}")

    # 获取摘要
    summary = executor.get_execution_summary()
    print(f"执行摘要: {summary}")

    # 关闭执行器
    executor.shutdown()
    print("测试完成")