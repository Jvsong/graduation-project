#!/usr/bin/env python3
"""
测试执行引擎
负责测试用例的发现、执行、结果收集和报告生成
"""

import os
import sys
import time
import importlib
import traceback
from typing import List, Dict, Any, Optional, Tuple, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from utils.logger import get_logger
from utils.config_manager import get_config
from utils.data_manager import get_test_data_manager, load_test_data


class TestResult:
    """测试结果类"""

    def __init__(self):
        self.test_name = ""
        self.module_name = ""
        self.class_name = ""
        self.method_name = ""
        self.start_time = None
        self.end_time = None
        self.duration = 0.0
        self.status = "PENDING"  # PENDING, RUNNING, PASSED, FAILED, ERROR, SKIPPED
        self.error_message = ""
        self.error_traceback = ""
        self.screenshot_path = ""
        self.logs = []
        self.retry_count = 0
        self.max_retries = 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "test_name": self.test_name,
            "module_name": self.module_name,
            "class_name": self.class_name,
            "method_name": self.method_name,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "status": self.status,
            "error_message": self.error_message,
            "error_traceback": self.error_traceback,
            "screenshot_path": self.screenshot_path,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries
        }


class TestExecutor:
    """
    测试执行引擎
    负责测试用例的执行管理
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化测试执行引擎

        Args:
            config: 配置字典，如果为None则使用全局配置
        """
        self.logger = get_logger(self.__class__.__name__)

        # 获取配置
        if config is None:
            self.config = get_config()
        else:
            self.config = config

        # 执行配置
        self.test_config = self.config.get('test', {})
        self.max_workers = self.test_config.get('max_workers', 1)
        self.retry_count = self.test_config.get('retry_count', 0)
        self.timeout = self.test_config.get('timeout', 30)
        self.screenshot_on_failure = self.test_config.get('screenshot_on_failure', True)
        self.screenshot_path = self.test_config.get('screenshot_path', './reports/screenshots')

        # 结果存储
        self.results: List[TestResult] = []
        self.failed_tests: List[TestResult] = []
        self.passed_tests: List[TestResult] = []

        # 执行器
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)

        self.logger.info(f"测试执行引擎初始化完成，最大工作线程数: {self.max_workers}")

    def discover_tests(self,
                      test_path: str = "./testcases",
                      pattern: str = "test_*.py",
                      test_suite: Optional[List[str]] = None) -> List[Tuple[str, str, str]]:
        """
        发现测试用例

        Args:
            test_path: 测试用例目录路径
            pattern: 测试文件模式
            test_suite: 测试套件列表，如果提供则只执行这些测试

        Returns:
            List[Tuple[str, str, str]]: (模块路径, 类名, 方法名) 列表
        """
        self.logger.info(f"发现测试用例，路径: {test_path}, 模式: {pattern}")

        discovered_tests = []

        # 如果指定了测试套件，直接使用
        if test_suite:
            for test_spec in test_suite:
                parts = test_spec.split('.')
                if len(parts) == 3:
                    discovered_tests.append((parts[0], parts[1], parts[2]))
            return discovered_tests

        # 否则扫描目录
        if not os.path.exists(test_path):
            self.logger.error(f"测试路径不存在: {test_path}")
            return discovered_tests

        # 扫描测试文件
        for root, dirs, files in os.walk(test_path):
            for file in files:
                if file.endswith('.py') and file.startswith('test_'):
                    module_path = os.path.join(root, file)
                    relative_path = os.path.relpath(module_path, test_path)
                    module_name = relative_path.replace(os.path.sep, '.')[:-3]

                    # 导入模块并获取测试类
                    try:
                        spec = importlib.util.spec_from_file_location(module_name, module_path)
                        module = importlib.util.module_from_spec(spec)
                        sys.modules[module_name] = module
                        spec.loader.exec_module(module)

                        # 查找测试类
                        for attr_name in dir(module):
                            attr = getattr(module, attr_name)
                            if (isinstance(attr, type) and
                                attr_name.startswith('Test') and
                                hasattr(attr, '__module__')):
                                # 查找测试方法
                                for method_name in dir(attr):
                                    method = getattr(attr, method_name)
                                    if (callable(method) and
                                        method_name.startswith('test_') and
                                        not method_name.startswith('__')):
                                        discovered_tests.append((module_name, attr_name, method_name))

                    except Exception as e:
                        self.logger.error(f"导入模块失败 {module_path}: {e}")

        self.logger.info(f"发现 {len(discovered_tests)} 个测试用例")
        return discovered_tests

    def execute_test(self, test_info: Tuple[str, str, str]) -> TestResult:
        """
        执行单个测试用例

        Args:
            test_info: (模块名, 类名, 方法名)

        Returns:
            TestResult: 测试结果
        """
        module_name, class_name, method_name = test_info
        test_result = TestResult()
        test_result.test_name = f"{module_name}.{class_name}.{method_name}"
        test_result.module_name = module_name
        test_result.class_name = class_name
        test_result.method_name = method_name
        test_result.max_retries = self.retry_count

        self.logger.info(f"开始执行测试: {test_result.test_name}")

        # 重试逻辑
        for retry in range(self.retry_count + 1):
            test_result.retry_count = retry
            test_result.start_time = datetime.now()

            try:
                # 导入测试类
                module = importlib.import_module(module_name)
                test_class = getattr(module, class_name)

                # 创建测试实例
                test_instance = test_class()

                # 执行测试方法
                test_method = getattr(test_instance, method_name)

                # 调用setUp方法
                if hasattr(test_instance, 'setUp'):
                    test_instance.setUp()

                # 执行测试方法
                test_method()

                # 调用tearDown方法
                if hasattr(test_instance, 'tearDown'):
                    test_instance.tearDown()

                # 测试通过
                test_result.status = "PASSED"
                test_result.end_time = datetime.now()
                test_result.duration = (test_result.end_time - test_result.start_time).total_seconds()

                self.logger.info(f"测试通过: {test_result.test_name} (重试次数: {retry})")
                return test_result

            except AssertionError as e:
                # 断言失败
                test_result.status = "FAILED"
                test_result.error_message = str(e)
                test_result.error_traceback = traceback.format_exc()

            except Exception as e:
                # 其他错误
                test_result.status = "ERROR"
                test_result.error_message = str(e)
                test_result.error_traceback = traceback.format_exc()

            finally:
                test_result.end_time = datetime.now()
                test_result.duration = (test_result.end_time - test_result.start_time).total_seconds()

                # 截图处理
                if test_result.status in ["FAILED", "ERROR"] and self.screenshot_on_failure:
                    try:
                        screenshot_file = self._take_screenshot(test_result)
                        test_result.screenshot_path = screenshot_file
                    except Exception as e:
                        self.logger.error(f"截图失败: {e}")

            # 如果测试失败且还有重试次数，继续重试
            if test_result.status in ["FAILED", "ERROR"] and retry < self.retry_count:
                self.logger.info(f"测试失败，准备重试 ({retry + 1}/{self.retry_count}): {test_result.test_name}")
                time.sleep(1)  # 重试前等待1秒
            else:
                break

        # 记录最终结果
        if test_result.status in ["FAILED", "ERROR"]:
            self.logger.error(f"测试失败: {test_result.test_name} - {test_result.error_message}")
        elif test_result.status == "PASSED":
            self.logger.info(f"测试通过: {test_result.test_name}")

        return test_result

    def execute_tests(self,
                     test_suite: Optional[List[str]] = None,
                     test_path: str = "./testcases",
                     pattern: str = "test_*.py",
                     parallel: bool = False) -> List[TestResult]:
        """
        执行测试用例

        Args:
            test_suite: 测试套件列表
            test_path: 测试路径
            pattern: 文件模式
            parallel: 是否并行执行

        Returns:
            List[TestResult]: 测试结果列表
        """
        self.logger.info(f"开始执行测试，并行模式: {parallel}")

        # 发现测试用例
        discovered_tests = self.discover_tests(test_path, pattern, test_suite)

        if not discovered_tests:
            self.logger.warning("未发现测试用例")
            return []

        self.logger.info(f"总共发现 {len(discovered_tests)} 个测试用例")

        # 执行测试
        start_time = time.time()

        if parallel and self.max_workers > 1:
            self.results = self._execute_parallel(discovered_tests)
        else:
            self.results = self._execute_sequential(discovered_tests)

        end_time = time.time()
        total_duration = end_time - start_time

        # 统计结果
        self._analyze_results()

        self.logger.info(f"测试执行完成，总耗时: {total_duration:.2f}秒")
        self.logger.info(f"测试统计: 总共 {len(self.results)} 个, 通过 {len(self.passed_tests)} 个, 失败 {len(self.failed_tests)} 个")

        return self.results

    def _execute_sequential(self, test_list: List[Tuple[str, str, str]]) -> List[TestResult]:
        """顺序执行测试"""
        results = []
        total_tests = len(test_list)

        for i, test_info in enumerate(test_list, 1):
            self.logger.info(f"执行测试 [{i}/{total_tests}]: {test_info[0]}.{test_info[1]}.{test_info[2]}")
            result = self.execute_test(test_info)
            results.append(result)

        return results

    def _execute_parallel(self, test_list: List[Tuple[str, str, str]]) -> List[TestResult]:
        """并行执行测试"""
        results = []
        futures = []

        # 提交任务
        for test_info in test_list:
            future = self.executor.submit(self.execute_test, test_info)
            futures.append(future)

        # 收集结果
        for i, future in enumerate(as_completed(futures), 1):
            try:
                result = future.result(timeout=self.timeout)
                results.append(result)
                self.logger.info(f"并行任务完成 [{i}/{len(futures)}]: {result.test_name}")
            except Exception as e:
                self.logger.error(f"并行任务执行失败: {e}")

        return results

    def _analyze_results(self) -> None:
        """分析测试结果"""
        self.passed_tests = [r for r in self.results if r.status == "PASSED"]
        self.failed_tests = [r for r in self.results if r.status in ["FAILED", "ERROR"]]

    def _take_screenshot(self, test_result: TestResult) -> str:
        """
        截图

        Args:
            test_result: 测试结果

        Returns:
            str: 截图文件路径
        """
        # 确保目录存在
        os.makedirs(self.screenshot_path, exist_ok=True)

        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_test_name = test_result.test_name.replace('.', '_').replace(':', '_')
        screenshot_file = os.path.join(
            self.screenshot_path,
            f"{timestamp}_{safe_test_name}.png"
        )

        # 这里需要实际的截图逻辑
        # 由于没有driver实例，这里只返回路径
        # 实际使用时应该在execute_test中通过test_instance.driver截图

        self.logger.info(f"截图保存到: {screenshot_file}")
        return screenshot_file

    def get_summary(self) -> Dict[str, Any]:
        """获取测试摘要"""
        total = len(self.results)
        passed = len(self.passed_tests)
        failed = len(self.failed_tests)

        if total > 0:
            pass_rate = (passed / total) * 100
        else:
            pass_rate = 0.0

        # 计算总时长
        total_duration = sum(r.duration for r in self.results)

        return {
            "total_tests": total,
            "passed_tests": passed,
            "failed_tests": failed,
            "pass_rate": pass_rate,
            "total_duration": total_duration,
            "average_duration": total_duration / total if total > 0 else 0,
            "retry_count": self.retry_count,
            "max_workers": self.max_workers,
            "execution_mode": "parallel" if self.max_workers > 1 else "sequential"
        }

    def generate_report(self, report_format: str = "html", output_dir: str = "./reports") -> str:
        """
        生成测试报告

        Args:
            report_format: 报告格式 (html, json, xml)
            output_dir: 输出目录

        Returns:
            str: 报告文件路径
        """
        # 这里调用报告生成器
        # 暂时返回空字符串，后续实现
        return ""

    def shutdown(self) -> None:
        """关闭执行引擎"""
        self.executor.shutdown(wait=True)
        self.logger.info("测试执行引擎已关闭")


# 快捷函数
def get_test_executor(config: Optional[Dict[str, Any]] = None) -> TestExecutor:
    """
    获取测试执行引擎实例

    Args:
        config: 配置字典

    Returns:
        TestExecutor: 测试执行引擎实例
    """
    return TestExecutor(config)


if __name__ == "__main__":
    # 测试TestExecutor类
    print("测试TestExecutor类...")

    # 创建测试执行引擎
    executor = TestExecutor()

    # 测试发现测试用例
    tests = executor.discover_tests()
    print(f"发现的测试用例数量: {len(tests)}")

    # 测试执行（不实际执行，因为需要测试环境）
    print("测试执行引擎初始化成功")
    print(f"最大工作线程数: {executor.max_workers}")
    print(f"失败重试次数: {executor.retry_count}")
    print(f"超时时间: {executor.timeout}秒")

    # 关闭执行引擎
    executor.shutdown()
    print("测试完成")