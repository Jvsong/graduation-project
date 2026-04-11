#!/usr/bin/env python3
"""
报告数据模型
定义测试报告的数据结构和相关操作
"""

import os
import json
import copy
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from enum import Enum


class TestStatus(Enum):
    """测试状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


class TestResult:
    """
    测试结果类
    表示单个测试用例的结果
    """

    def __init__(self,
                 test_id: str,
                 name: str,
                 module: str = "",
                 description: str = ""):
        """
        初始化测试结果

        Args:
            test_id: 测试ID
            name: 测试名称
            module: 模块名称
            description: 测试描述
        """
        self.test_id = test_id
        self.name = name
        self.module = module
        self.description = description

        # 执行信息
        self.status = TestStatus.PENDING
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.duration: float = 0.0  # 单位：秒

        # 重试信息
        self.retry_count = 0
        self.max_retries = 0
        self.retry_history: List[Dict[str, Any]] = []

        # 错误信息
        self.error_message: Optional[str] = None
        self.error_traceback: Optional[str] = None
        self.error_type: Optional[str] = None

        # 附加信息
        self.screenshot_path: Optional[str] = None
        self.log_file: Optional[str] = None
        self.tags: List[str] = []
        self.priority: str = "P1"  # P0, P1, P2, P3
        self.requirements: List[str] = []  # 关联的需求ID
        self.defects: List[str] = []  # 关联的缺陷ID

        # 自定义属性
        self.custom_fields: Dict[str, Any] = {}

    def start(self) -> None:
        """开始测试"""
        self.status = TestStatus.RUNNING
        self.start_time = datetime.now()

    def end(self, status: TestStatus) -> None:
        """
        结束测试

        Args:
            status: 最终状态
        """
        self.status = status
        self.end_time = datetime.now()

        if self.start_time and self.end_time:
            self.duration = (self.end_time - self.start_time).total_seconds()

    def add_retry(self, status: TestStatus, error_message: Optional[str] = None) -> None:
        """
        添加重试记录

        Args:
            status: 重试状态
            error_message: 错误信息
        """
        self.retry_count += 1
        self.retry_history.append({
            "attempt": self.retry_count,
            "status": status.value,
            "error_message": error_message,
            "timestamp": datetime.now().isoformat()
        })

    def set_error(self, error_message: str, error_traceback: Optional[str] = None) -> None:
        """
        设置错误信息

        Args:
            error_message: 错误消息
            error_traceback: 错误堆栈
        """
        self.error_message = error_message
        self.error_traceback = error_traceback

        # 尝试从错误消息中提取错误类型
        if error_message:
            # 简单的错误类型提取
            if "AssertionError" in error_message:
                self.error_type = "AssertionError"
            elif "Timeout" in error_message or "超时" in error_message:
                self.error_type = "TimeoutError"
            elif "NoSuchElement" in error_message:
                self.error_type = "ElementNotFound"
            elif "Connection" in error_message or "网络" in error_message:
                self.error_type = "NetworkError"
            else:
                self.error_type = "UnknownError"

    def add_tag(self, tag: str) -> None:
        """
        添加标签

        Args:
            tag: 标签
        """
        if tag not in self.tags:
            self.tags.append(tag)

    def add_requirement(self, requirement_id: str) -> None:
        """
        添加需求关联

        Args:
            requirement_id: 需求ID
        """
        if requirement_id not in self.requirements:
            self.requirements.append(requirement_id)

    def add_defect(self, defect_id: str) -> None:
        """
        添加缺陷关联

        Args:
            defect_id: 缺陷ID
        """
        if defect_id not in self.defects:
            self.defects.append(defect_id)

    def set_custom_field(self, key: str, value: Any) -> None:
        """
        设置自定义字段

        Args:
            key: 字段名
            value: 字段值
        """
        self.custom_fields[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典

        Returns:
            Dict[str, Any]: 字典表示
        """
        return {
            "test_id": self.test_id,
            "name": self.name,
            "module": self.module,
            "description": self.description,
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "retry_history": self.retry_history,
            "error_message": self.error_message,
            "error_traceback": self.error_traceback,
            "error_type": self.error_type,
            "screenshot_path": self.screenshot_path,
            "log_file": self.log_file,
            "tags": self.tags,
            "priority": self.priority,
            "requirements": self.requirements,
            "defects": self.defects,
            "custom_fields": self.custom_fields
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestResult':
        """
        从字典创建实例

        Args:
            data: 字典数据

        Returns:
            TestResult: 测试结果实例
        """
        test_result = cls(
            test_id=data["test_id"],
            name=data["name"],
            module=data.get("module", ""),
            description=data.get("description", "")
        )

        # 恢复基本属性
        test_result.status = TestStatus(data.get("status", "pending"))

        if data.get("start_time"):
            test_result.start_time = datetime.fromisoformat(data["start_time"])
        if data.get("end_time"):
            test_result.end_time = datetime.fromisoformat(data["end_time"])

        test_result.duration = data.get("duration", 0.0)
        test_result.retry_count = data.get("retry_count", 0)
        test_result.max_retries = data.get("max_retries", 0)
        test_result.retry_history = data.get("retry_history", [])
        test_result.error_message = data.get("error_message")
        test_result.error_traceback = data.get("error_traceback")
        test_result.error_type = data.get("error_type")
        test_result.screenshot_path = data.get("screenshot_path")
        test_result.log_file = data.get("log_file")
        test_result.tags = data.get("tags", [])
        test_result.priority = data.get("priority", "P1")
        test_result.requirements = data.get("requirements", [])
        test_result.defects = data.get("defects", [])
        test_result.custom_fields = data.get("custom_fields", {})

        return test_result

    def __str__(self) -> str:
        """字符串表示"""
        return f"TestResult({self.test_id}: {self.status.value}, {self.duration:.2f}s)"


class ModuleStats:
    """
    模块统计类
    统计一个模块的测试结果
    """

    def __init__(self, module_name: str):
        """
        初始化模块统计

        Args:
            module_name: 模块名称
        """
        self.module_name = module_name
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.error_tests = 0
        self.skipped_tests = 0
        self.blocked_tests = 0
        self.total_duration = 0.0
        self.test_results: List[TestResult] = []

    def add_test_result(self, test_result: TestResult) -> None:
        """
        添加测试结果

        Args:
            test_result: 测试结果
        """
        self.test_results.append(test_result)
        self.total_tests += 1
        self.total_duration += test_result.duration

        if test_result.status == TestStatus.PASSED:
            self.passed_tests += 1
        elif test_result.status == TestStatus.FAILED:
            self.failed_tests += 1
        elif test_result.status == TestStatus.ERROR:
            self.error_tests += 1
        elif test_result.status == TestStatus.SKIPPED:
            self.skipped_tests += 1
        elif test_result.status == TestStatus.BLOCKED:
            self.blocked_tests += 1

    def get_pass_rate(self) -> float:
        """
        获取通过率

        Returns:
            float: 通过率（百分比）
        """
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100

    def get_average_duration(self) -> float:
        """
        获取平均执行时间

        Returns:
            float: 平均执行时间（秒）
        """
        if self.total_tests == 0:
            return 0.0
        return self.total_duration / self.total_tests

    def get_status_distribution(self) -> Dict[str, int]:
        """
        获取状态分布

        Returns:
            Dict[str, int]: 状态分布字典
        """
        return {
            "passed": self.passed_tests,
            "failed": self.failed_tests,
            "error": self.error_tests,
            "skipped": self.skipped_tests,
            "blocked": self.blocked_tests,
            "total": self.total_tests
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典

        Returns:
            Dict[str, Any]: 字典表示
        """
        return {
            "module_name": self.module_name,
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "error_tests": self.error_tests,
            "skipped_tests": self.skipped_tests,
            "blocked_tests": self.blocked_tests,
            "total_duration": self.total_duration,
            "average_duration": self.get_average_duration(),
            "pass_rate": self.get_pass_rate(),
            "status_distribution": self.get_status_distribution()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModuleStats':
        """
        从字典创建实例

        Args:
            data: 字典数据

        Returns:
            ModuleStats: 模块统计实例
        """
        module_stats = cls(data["module_name"])
        module_stats.total_tests = data.get("total_tests", 0)
        module_stats.passed_tests = data.get("passed_tests", 0)
        module_stats.failed_tests = data.get("failed_tests", 0)
        module_stats.error_tests = data.get("error_tests", 0)
        module_stats.skipped_tests = data.get("skipped_tests", 0)
        module_stats.blocked_tests = data.get("blocked_tests", 0)
        module_stats.total_duration = data.get("total_duration", 0.0)

        # 注意：test_results 需要单独恢复
        return module_stats


class ReportData:
    """
    报告数据类
    包含完整的测试报告数据
    """

    def __init__(self, project_name: str = "", project_version: str = ""):
        """
        初始化报告数据

        Args:
            project_name: 项目名称
            project_version: 项目版本
        """
        # 项目信息
        self.project_info: Dict[str, Any] = {
            "name": project_name,
            "version": project_version,
            "description": "",
            "start_date": datetime.now().date().isoformat(),
            "end_date": None
        }

        # 执行信息
        self.execution_info: Dict[str, Any] = {
            "start_time": None,
            "end_time": None,
            "duration": 0.0,
            "environment": "test",
            "browser": "chrome",
            "execution_mode": "sequential",
            "parallel_workers": 1,
            "retry_count": 0,
            "timeout": 30
        }

        # 测试结果
        self.test_results: List[TestResult] = []

        # 模块统计
        self.module_stats: Dict[str, ModuleStats] = {}

        # 全局统计
        self.global_stats: Dict[str, Any] = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "error_tests": 0,
            "skipped_tests": 0,
            "blocked_tests": 0,
            "total_duration": 0.0,
            "pass_rate": 0.0
        }

        # 趋势数据（用于历史对比）
        self.trend_data: List[Dict[str, Any]] = []

        # 自定义数据
        self.custom_data: Dict[str, Any] = {}

    def add_test_result(self, test_result: TestResult) -> None:
        """
        添加测试结果

        Args:
            test_result: 测试结果
        """
        self.test_results.append(test_result)

        # 更新全局统计
        self._update_global_stats(test_result)

        # 更新模块统计
        module_name = test_result.module or "unknown"
        if module_name not in self.module_stats:
            self.module_stats[module_name] = ModuleStats(module_name)
        self.module_stats[module_name].add_test_result(test_result)

    def set_project_info(self, **kwargs) -> None:
        """
        设置项目信息

        Args:
            **kwargs: 项目信息字段
        """
        for key, value in kwargs.items():
            if key in self.project_info:
                self.project_info[key] = value

    def set_execution_info(self, **kwargs) -> None:
        """
        设置执行信息

        Args:
            **kwargs: 执行信息字段
        """
        for key, value in kwargs.items():
            if key in self.execution_info:
                self.execution_info[key] = value

    def start_execution(self) -> None:
        """开始执行"""
        self.execution_info["start_time"] = datetime.now()

    def end_execution(self) -> None:
        """结束执行"""
        self.execution_info["end_time"] = datetime.now()

        # 计算总时长
        start_time = self.execution_info["start_time"]
        end_time = self.execution_info["end_time"]

        if start_time and end_time:
            duration = (end_time - start_time).total_seconds()
            self.execution_info["duration"] = duration

        # 更新全局统计
        self._calculate_global_stats()

    def _update_global_stats(self, test_result: TestResult) -> None:
        """
        更新全局统计

        Args:
            test_result: 测试结果
        """
        self.global_stats["total_tests"] += 1
        self.global_stats["total_duration"] += test_result.duration

        if test_result.status == TestStatus.PASSED:
            self.global_stats["passed_tests"] += 1
        elif test_result.status == TestStatus.FAILED:
            self.global_stats["failed_tests"] += 1
        elif test_result.status == TestStatus.ERROR:
            self.global_stats["error_tests"] += 1
        elif test_result.status == TestStatus.SKIPPED:
            self.global_stats["skipped_tests"] += 1
        elif test_result.status == TestStatus.BLOCKED:
            self.global_stats["blocked_tests"] += 1

    def _calculate_global_stats(self) -> None:
        """计算全局统计"""
        total = self.global_stats["total_tests"]
        passed = self.global_stats["passed_tests"]

        if total > 0:
            self.global_stats["pass_rate"] = (passed / total) * 100
        else:
            self.global_stats["pass_rate"] = 0.0

    def get_summary(self) -> Dict[str, Any]:
        """
        获取报告摘要

        Returns:
            Dict[str, Any]: 报告摘要
        """
        # 计算模块统计摘要
        module_summary = []
        for module_name, stats in self.module_stats.items():
            module_summary.append(stats.to_dict())

        # 按通过率排序
        module_summary.sort(key=lambda x: x["pass_rate"], reverse=True)

        # 准备执行信息
        execution_info = copy.deepcopy(self.execution_info)
        if isinstance(execution_info.get("start_time"), datetime):
            execution_info["start_time"] = execution_info["start_time"].isoformat()
        if isinstance(execution_info.get("end_time"), datetime):
            execution_info["end_time"] = execution_info["end_time"].isoformat()

        return {
            "project": self.project_info,
            "execution": execution_info,
            "stats": self.global_stats,
            "module_stats": module_summary,
            "total_modules": len(self.module_stats),
            "generation_time": datetime.now().isoformat()
        }

    def get_test_results_by_status(self, status: TestStatus) -> List[TestResult]:
        """
        按状态获取测试结果

        Args:
            status: 测试状态

        Returns:
            List[TestResult]: 测试结果列表
        """
        return [tr for tr in self.test_results if tr.status == status]

    def get_test_results_by_module(self, module_name: str) -> List[TestResult]:
        """
        按模块获取测试结果

        Args:
            module_name: 模块名称

        Returns:
            List[TestResult]: 测试结果列表
        """
        return [tr for tr in self.test_results if tr.module == module_name]

    def get_failed_tests_with_errors(self) -> List[Dict[str, Any]]:
        """
        获取失败的测试及其错误信息

        Returns:
            List[Dict[str, Any]]: 失败测试列表
        """
        failed_tests = []

        for test_result in self.test_results:
            if test_result.status in [TestStatus.FAILED, TestStatus.ERROR]:
                failed_tests.append({
                    "test_id": test_result.test_id,
                    "name": test_result.name,
                    "module": test_result.module,
                    "error_message": test_result.error_message,
                    "error_type": test_result.error_type,
                    "screenshot": test_result.screenshot_path
                })

        return failed_tests

    def add_trend_data(self, trend_point: Dict[str, Any]) -> None:
        """
        添加趋势数据点

        Args:
            trend_point: 趋势数据点
        """
        self.trend_data.append(trend_point)

    def get_trend_summary(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        获取趋势摘要

        Args:
            days: 天数

        Returns:
            List[Dict[str, Any]]: 趋势摘要
        """
        if not self.trend_data:
            return []

        # 按日期排序
        sorted_data = sorted(self.trend_data, key=lambda x: x.get("date", ""))

        # 取最近N天的数据
        return sorted_data[-days:]

    def save_to_file(self, file_path: str) -> bool:
        """
        保存到文件

        Args:
            file_path: 文件路径

        Returns:
            bool: 是否保存成功
        """
        try:
            data = self.to_dict()

            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)

            return True

        except Exception as e:
            print(f"保存报告数据失败: {e}")
            return False

    @classmethod
    def load_from_file(cls, file_path: str) -> Optional['ReportData']:
        """
        从文件加载

        Args:
            file_path: 文件路径

        Returns:
            Optional[ReportData]: 报告数据实例，如果失败则返回None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return cls.from_dict(data)

        except Exception as e:
            print(f"加载报告数据失败: {e}")
            return None

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典

        Returns:
            Dict[str, Any]: 字典表示
        """
        return {
            "project_info": self.project_info,
            "execution_info": self._serialize_execution_info(),
            "test_results": [tr.to_dict() for tr in self.test_results],
            "module_stats": {name: stats.to_dict() for name, stats in self.module_stats.items()},
            "global_stats": self.global_stats,
            "trend_data": self.trend_data,
            "custom_data": self.custom_data
        }

    def _serialize_execution_info(self) -> Dict[str, Any]:
        """序列化执行信息"""
        execution_info = copy.deepcopy(self.execution_info)

        # 序列化datetime对象
        for key in ["start_time", "end_time"]:
            if isinstance(execution_info.get(key), datetime):
                execution_info[key] = execution_info[key].isoformat()

        return execution_info

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReportData':
        """
        从字典创建实例

        Args:
            data: 字典数据

        Returns:
            ReportData: 报告数据实例
        """
        # 创建实例
        project_info = data.get("project_info", {})
        report_data = cls(
            project_name=project_info.get("name", ""),
            project_version=project_info.get("version", "")
        )

        # 恢复项目信息
        report_data.project_info.update(project_info)

        # 恢复执行信息
        execution_info = data.get("execution_info", {})
        for key, value in execution_info.items():
            if key in ["start_time", "end_time"] and value:
                try:
                    execution_info[key] = datetime.fromisoformat(value)
                except (ValueError, TypeError):
                    execution_info[key] = value
        report_data.execution_info.update(execution_info)

        # 恢复测试结果
        test_results_data = data.get("test_results", [])
        for test_result_data in test_results_data:
            test_result = TestResult.from_dict(test_result_data)
            report_data.add_test_result(test_result)

        # 恢复模块统计
        module_stats_data = data.get("module_stats", {})
        for module_name, stats_data in module_stats_data.items():
            module_stats = ModuleStats.from_dict(stats_data)
            report_data.module_stats[module_name] = module_stats

        # 恢复全局统计
        report_data.global_stats = data.get("global_stats", {})

        # 恢复趋势数据
        report_data.trend_data = data.get("trend_data", [])

        # 恢复自定义数据
        report_data.custom_data = data.get("custom_data", {})

        return report_data

    def __str__(self) -> str:
        """字符串表示"""
        total = self.global_stats.get("total_tests", 0)
        passed = self.global_stats.get("passed_tests", 0)
        pass_rate = self.global_stats.get("pass_rate", 0.0)

        return f"ReportData(项目: {self.project_info.get('name')}, 测试: {total}个, 通过率: {pass_rate:.1f}%)"


# 快捷函数
def create_report_data(project_name: str = "", project_version: str = "") -> ReportData:
    """
    创建报告数据实例

    Args:
        project_name: 项目名称
        project_version: 项目版本

    Returns:
        ReportData: 报告数据实例
    """
    return ReportData(project_name, project_version)


def create_test_result(test_id: str,
                      name: str,
                      module: str = "",
                      description: str = "") -> TestResult:
    """
    创建测试结果实例

    Args:
        test_id: 测试ID
        name: 测试名称
        module: 模块名称
        description: 测试描述

    Returns:
        TestResult: 测试结果实例
    """
    return TestResult(test_id, name, module, description)


if __name__ == "__main__":
    # 测试ReportData类
    print("测试ReportData类...")

    # 创建报告数据
    report = create_report_data("电商后台测试系统", "1.0.0")

    # 设置项目信息
    report.set_project_info(
        description="电商后台管理系统自动化测试",
        start_date="2026-04-01",
        end_date="2026-04-04"
    )

    # 设置执行信息
    report.start_execution()
    report.set_execution_info(
        environment="test",
        browser="chrome",
        execution_mode="parallel",
        parallel_workers=4,
        retry_count=2
    )

    # 创建测试结果
    test1 = create_test_result("TC001", "test_valid_login", "login", "测试有效登录")
    test1.start()
    test1.end(TestStatus.PASSED)
    test1.duration = 2.5
    report.add_test_result(test1)

    test2 = create_test_result("TC002", "test_invalid_password", "login", "测试无效密码")
    test2.start()
    test2.set_error("密码验证失败", "AssertionError: Password is incorrect")
    test2.end(TestStatus.FAILED)
    test2.duration = 1.8
    test2.screenshot_path = "/reports/screenshots/test2.png"
    report.add_test_result(test2)

    test3 = create_test_result("TC003", "test_product_search", "product", "测试商品搜索")
    test3.start()
    test3.end(TestStatus.PASSED)
    test3.duration = 3.2
    report.add_test_result(test3)

    # 结束执行
    report.end_execution()

    # 获取摘要
    summary = report.get_summary()
    print(f"报告摘要:")
    print(f"  项目: {summary['project']['name']} v{summary['project']['version']}")
    print(f"  总测试数: {summary['stats']['total_tests']}")
    print(f"  通过: {summary['stats']['passed_tests']}")
    print(f"  失败: {summary['stats']['failed_tests']}")
    print(f"  通过率: {summary['stats']['pass_rate']:.1f}%")

    # 获取模块统计
    print(f"模块统计:")
    for module in summary['module_stats']:
        print(f"  {module['module_name']}: {module['passed_tests']}/{module['total_tests']} 通过 ({module['pass_rate']:.1f}%)")

    # 获取失败测试
    failed_tests = report.get_failed_tests_with_errors()
    print(f"失败测试:")
    for test in failed_tests:
        print(f"  {test['name']}: {test['error_message']}")

    # 保存到文件
    save_path = "test_report_data.json"
    if report.save_to_file(save_path):
        print(f"报告数据保存到: {save_path}")

        # 从文件加载
        loaded_report = ReportData.load_from_file(save_path)
        if loaded_report:
            print(f"从文件加载成功: {loaded_report}")

    print("测试完成")