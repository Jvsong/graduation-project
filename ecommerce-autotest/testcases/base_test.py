#!/usr/bin/env python3
"""
基础测试类
所有测试用例的基类，提供统一的测试环境管理和常用测试方法
"""

import os
import sys
import time
import pytest
import unittest
from typing import Optional, Dict, Any, Tuple
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from utils.config_manager import get_config, init_config
from utils.logger import TestLogger, get_logger, configure_logging
from utils.common import file_utils, time_utils
from pages.base_page import BasePage


class BaseTest(unittest.TestCase):
    """
    自动化测试基类
    继承自unittest.TestCase，提供统一的测试框架
    """

    # 类级配置
    config = None
    driver: Optional[WebDriver] = None
    test_logger: Optional[TestLogger] = None
    logger = None

    # 测试配置
    SCREENSHOT_ON_FAILURE = True
    SCREENSHOT_DIR = "./reports/screenshots"
    RETRY_COUNT = 2
    IMPLICIT_WAIT = 10

    @classmethod
    def setUpClass(cls) -> None:
        """
        测试类级别的初始化
        在整个测试类开始前执行一次
        """
        cls._setup_config()
        cls._setup_logging()
        cls._setup_driver()

    @classmethod
    def tearDownClass(cls) -> None:
        """
        测试类级别的清理
        在整个测试类结束后执行一次
        """
        cls._teardown_driver()

    def setUp(self) -> None:
        """
        测试方法级别的初始化
        在每个测试方法开始前执行
        """
        self._setup_test_logger()
        self._setup_test_environment()
        self.test_logger.start_test(self._get_test_description())

    def tearDown(self) -> None:
        """
        测试方法级别的清理
        在每个测试方法结束后执行
        """
        self._handle_test_result()
        self._cleanup_test_data()
        self.test_logger.end_test(self._get_test_status(), self._get_test_message())

    # ==================== 配置管理 ====================

    @classmethod
    def _setup_config(cls) -> None:
        """设置配置"""
        try:
            # 初始化配置
            config_loaded = init_config()
            if not config_loaded:
                print("警告: 使用默认配置")

            cls.config = get_config()

            # 更新测试配置
            cls.SCREENSHOT_ON_FAILURE = cls.config.get('test.screenshot_on_failure', True)
            cls.SCREENSHOT_DIR = cls.config.get('test.screenshot_path', './reports/screenshots')
            cls.RETRY_COUNT = cls.config.get('test.retry_count', 2)
            cls.IMPLICIT_WAIT = cls.config.get('browser.implicit_wait', 10)

        except Exception as e:
            print(f"配置设置失败: {e}")
            cls.config = None

    @classmethod
    def _setup_logging(cls) -> None:
        """设置日志系统"""
        try:
            # 获取日志配置
            log_config = cls._get_logging_config()
            configure_logging(log_config)

            # 获取类级别日志器
            cls.logger = get_logger(cls.__name__)
            cls.logger.info(f"测试类初始化: {cls.__name__}")

        except Exception as e:
            print(f"日志系统设置失败: {e}")

    @classmethod
    def _get_logging_config(cls) -> Dict[str, Any]:
        """获取日志配置"""
        if cls.config:
            return {
                'level': cls.config.get('logging.level', 'INFO'),
                'format': cls.config.get('logging.format',
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
                'console': True,
                'file': {
                    'path': cls.config.get('logging.file', './logs/test.log'),
                    'rotate': True,
                    'max_size': cls.config.get('logging.max_size', 10 * 1024 * 1024),
                    'backup_count': cls.config.get('logging.backup_count', 5)
                }
            }
        else:
            return {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'console': True,
                'file': {
                    'path': './logs/test.log',
                    'rotate': True,
                    'max_size': 10 * 1024 * 1024,
                    'backup_count': 5
                }
            }

    # ==================== 浏览器驱动管理 ====================

    @classmethod
    def _setup_driver(cls) -> None:
        """设置浏览器驱动"""
        try:
            from utils.browser_factory import BrowserFactory

            # 获取浏览器配置
            browser_config = cls._get_browser_config()

            # 创建浏览器实例
            factory = BrowserFactory()
            cls.driver = factory.create_driver(**browser_config)

            # 设置隐式等待
            cls.driver.implicitly_wait(cls.IMPLICIT_WAIT)

            # 最大化窗口（如果配置了窗口大小则不最大化）
            if not browser_config.get('window_size'):
                cls.driver.maximize_window()

            cls.logger.info(f"浏览器驱动初始化完成: {browser_config.get('browser_name', 'chrome')}")

        except Exception as e:
            cls.logger.error(f"浏览器驱动初始化失败: {e}")
            raise

    @classmethod
    def _get_browser_config(cls) -> Dict[str, Any]:
        """获取浏览器配置"""
        if cls.config:
            return {
                'browser_name': cls.config.get('browser.name', 'chrome'),
                'headless': cls.config.get('browser.headless', False),
                'window_size': cls.config.get('browser.window_size'),
                'implicit_wait': cls.config.get('browser.implicit_wait', 10),
                'page_load_timeout': cls.config.get('browser.page_load_timeout', 30)
            }
        else:
            return {
                'browser_name': 'chrome',
                'headless': False,
                'implicit_wait': 10,
                'page_load_timeout': 30
            }

    @classmethod
    def _teardown_driver(cls) -> None:
        """清理浏览器驱动"""
        if cls.driver:
            try:
                cls.driver.quit()
                cls.logger.info("浏览器驱动已关闭")
            except Exception as e:
                cls.logger.error(f"关闭浏览器驱动时出错: {e}")
            finally:
                cls.driver = None

    def get_driver(self) -> WebDriver:
        """
        获取浏览器驱动实例

        Returns:
            WebDriver: 浏览器驱动实例
        """
        if not self.driver:
            raise RuntimeError("浏览器驱动未初始化")
        return self.driver

    # ==================== 测试日志管理 ====================

    def _setup_test_logger(self) -> None:
        """设置测试日志器"""
        test_name = self._get_test_name()
        self.test_logger = TestLogger(test_name)

    def _get_test_name(self) -> str:
        """获取测试名称"""
        # 使用测试方法名作为测试名称
        return self._testMethodName

    def _get_test_description(self) -> str:
        """获取测试描述"""
        # 使用测试方法的文档字符串作为描述
        test_method = getattr(self, self._testMethodName, None)
        if test_method and test_method.__doc__:
            return test_method.__doc__.strip()
        return self._get_test_name()

    def _get_test_status(self) -> str:
        """获取测试状态"""
        # 检查是否有测试失败或错误
        if hasattr(self, '_outcome'):
            result = getattr(self._outcome, 'result', None)
            errors = getattr(result, 'errors', [])
            failures = getattr(result, 'failures', [])
            if errors or failures:
                return "失败"
        return "通过"

    def _get_test_message(self) -> str:
        """获取测试消息"""
        # 如果有错误信息，返回错误信息
        if hasattr(self, '_outcome'):
            result = getattr(self._outcome, 'result', None)
            errors = getattr(result, 'errors', [])
            failures = getattr(result, 'failures', [])
            if errors:
                error = errors[0][1]
                return str(error)
            elif failures:
                failure = failures[0][1]
                return str(failure)
        return ""

    # ==================== 测试环境管理 ====================

    def _setup_test_environment(self) -> None:
        """设置测试环境"""
        # 确保截图目录存在
        if self.SCREENSHOT_ON_FAILURE:
            file_utils.ensure_directory(self.SCREENSHOT_DIR)

        # 记录测试开始时间
        self.test_start_time = time_utils.get_current_timestamp()

        # 打开基础URL
        if self.config and self.config.get('environment.base_url'):
            base_url = self.config.get('environment.base_url')
            try:
                self.driver.get(base_url)
                self.test_logger.log_action("打开基础URL", base_url)
            except Exception as e:
                self.test_logger.log_warning(f"打开基础URL失败: {e}")

    def _handle_test_result(self) -> None:
        """处理测试结果"""
        # 计算测试持续时间
        test_end_time = time_utils.get_current_timestamp()
        duration = time_utils.calculate_duration(self.test_start_time, test_end_time)
        self.test_logger.log_data("测试持续时间", f"{duration:.2f}秒")

        # 检查测试是否失败
        test_passed = self._is_test_passed()

        # 如果测试失败且启用了截图功能，则截图
        if not test_passed and self.SCREENSHOT_ON_FAILURE:
            self._take_failure_screenshot()

    def _is_test_passed(self) -> bool:
        """检查测试是否通过"""
        # 检查是否有未捕获的异常
        if hasattr(self, '_outcome'):
            result = getattr(self._outcome, 'result', None)
            errors = getattr(result, 'errors', [])
            failures = getattr(result, 'failures', [])
            return not (errors or failures)
        return True

    def _take_failure_screenshot(self) -> None:
        """失败时截图"""
        try:
            # 生成截图文件名
            timestamp = time_utils.get_current_time().replace(':', '-').replace(' ', '_')
            test_name = self._get_test_name()
            filename = f"{self.SCREENSHOT_DIR}/{test_name}_{timestamp}.png"

            # 截图
            self.driver.save_screenshot(filename)

            # 记录日志
            self.test_logger.log_screenshot(filename, "测试失败截图")

        except Exception as e:
            self.test_logger.log_error("截图失败", str(e))

    def _cleanup_test_data(self) -> None:
        """清理测试数据"""
        # 清理cookies
        try:
            self.driver.delete_all_cookies()
            self.test_logger.log_action("清理cookies")
        except Exception as e:
            self.test_logger.log_warning(f"清理cookies失败: {e}")

        # 清理本地存储
        try:
            self.driver.execute_script("window.localStorage.clear();")
            self.driver.execute_script("window.sessionStorage.clear();")
            self.test_logger.log_action("清理本地存储")
        except Exception as e:
            self.test_logger.log_warning(f"清理本地存储失败: {e}")

    # ==================== 页面对象管理 ====================

    def create_page(self, page_class, *args, **kwargs) -> BasePage:
        """
        创建页面对象实例

        Args:
            page_class: 页面类
            *args: 传递给页面类的参数
            **kwargs: 传递给页面类的关键字参数

        Returns:
            BasePage: 页面对象实例
        """
        return page_class(self.driver, *args, **kwargs)

    # ==================== 断言方法扩展 ====================

    def assert_element_exists(self, locator: Tuple, timeout: Optional[int] = None,
                              message: Optional[str] = None) -> WebElement:
        """
        断言元素存在

        Args:
            locator: 元素定位器
            timeout: 等待超时时间
            message: 断言失败时的消息

        Returns:
            WebElement: 找到的元素

        Raises:
            AssertionError: 如果元素不存在
        """
        from pages.base_page import BasePage
        page = BasePage(self.driver)

        try:
            element = page.find_element(locator, timeout)
            self.test_logger.log_check(f"元素存在: {locator}", True)
            return element
        except Exception as e:
            if message is None:
                message = f"元素不存在: {locator}"
            self.test_logger.log_check(f"元素存在: {locator}", False, str(e))
            raise AssertionError(message) from e

    def assert_element_visible(self, locator: Tuple, timeout: Optional[int] = None,
                               message: Optional[str] = None) -> WebElement:
        """
        断言元素可见

        Args:
            locator: 元素定位器
            timeout: 等待超时时间
            message: 断言失败时的消息

        Returns:
            WebElement: 找到的可见元素

        Raises:
            AssertionError: 如果元素不可见
        """
        from pages.base_page import BasePage
        page = BasePage(self.driver)

        try:
            element = page.find_visible_element(locator, timeout)
            self.test_logger.log_check(f"元素可见: {locator}", True)
            return element
        except Exception as e:
            if message is None:
                message = f"元素不可见: {locator}"
            self.test_logger.log_check(f"元素可见: {locator}", False, str(e))
            raise AssertionError(message) from e

    def assert_element_text(self, locator: Tuple, expected_text: str,
                            exact_match: bool = False, timeout: Optional[int] = None,
                            message: Optional[str] = None) -> None:
        """
        断言元素文本

        Args:
            locator: 元素定位器
            expected_text: 期望的文本
            exact_match: 是否完全匹配
            timeout: 等待超时时间
            message: 断言失败时的消息

        Raises:
            AssertionError: 如果文本不匹配
        """
        from pages.base_page import BasePage
        page = BasePage(self.driver)

        try:
            actual_text = page.get_text(locator, timeout)

            if exact_match:
                passed = actual_text == expected_text
                comparison = f"期望: '{expected_text}', 实际: '{actual_text}'"
            else:
                passed = expected_text in actual_text
                comparison = f"期望包含: '{expected_text}', 实际: '{actual_text}'"

            if passed:
                self.test_logger.log_check(f"元素文本: {locator}", True, comparison)
            else:
                self.test_logger.log_check(f"元素文本: {locator}", False, comparison)
                if message is None:
                    message = f"元素文本不匹配: {comparison}"
                raise AssertionError(message)

        except Exception as e:
            if message is None:
                message = f"验证元素文本失败: {locator}"
            self.test_logger.log_check(f"元素文本: {locator}", False, str(e))
            raise AssertionError(message) from e

    def assert_page_title_contains(self, expected_text: str, message: Optional[str] = None) -> None:
        """
        断言页面标题包含指定文本

        Args:
            expected_text: 期望的文本
            message: 断言失败时的消息

        Raises:
            AssertionError: 如果标题不包含指定文本
        """
        from pages.base_page import BasePage
        page = BasePage(self.driver)

        try:
            actual_title = page.get_title()
            passed = expected_text in actual_title

            if passed:
                self.test_logger.log_check(f"页面标题包含: '{expected_text}'", True,
                                          f"实际标题: '{actual_title}'")
            else:
                self.test_logger.log_check(f"页面标题包含: '{expected_text}'", False,
                                          f"实际标题: '{actual_title}'")
                if message is None:
                    message = f"页面标题不包含 '{expected_text}'，实际标题: '{actual_title}'"
                raise AssertionError(message)

        except Exception as e:
            if message is None:
                message = f"验证页面标题失败: {expected_text}"
            self.test_logger.log_check(f"页面标题包含: '{expected_text}'", False, str(e))
            raise AssertionError(message) from e

    def assert_page_url_contains(self, expected_text: str, message: Optional[str] = None) -> None:
        """
        断言页面URL包含指定文本

        Args:
            expected_text: 期望的文本
            message: 断言失败时的消息

        Raises:
            AssertionError: 如果URL不包含指定文本
        """
        from pages.base_page import BasePage
        page = BasePage(self.driver)

        try:
            actual_url = page.get_current_url()
            passed = expected_text in actual_url

            if passed:
                self.test_logger.log_check(f"页面URL包含: '{expected_text}'", True,
                                          f"实际URL: '{actual_url}'")
            else:
                self.test_logger.log_check(f"页面URL包含: '{expected_text}'", False,
                                          f"实际URL: '{actual_url}'")
                if message is None:
                    message = f"页面URL不包含 '{expected_text}'，实际URL: '{actual_url}'"
                raise AssertionError(message)

        except Exception as e:
            if message is None:
                message = f"验证页面URL失败: {expected_text}"
            self.test_logger.log_check(f"页面URL包含: '{expected_text}'", False, str(e))
            raise AssertionError(message) from e

    # ==================== 实用方法 ====================

    def wait_for(self, seconds: float) -> None:
        """
        等待指定秒数

        Args:
            seconds: 等待的秒数
        """
        self.test_logger.log_action(f"等待 {seconds} 秒")
        time.sleep(seconds)

    def take_screenshot(self, description: str = "") -> str:
        """
        截图

        Args:
            description: 截图描述

        Returns:
            str: 截图文件路径
        """
        from pages.base_page import BasePage
        page = BasePage(self.driver)

        # 生成截图文件名
        timestamp = time_utils.get_current_time().replace(':', '-').replace(' ', '_')
        test_name = self._get_test_name()
        filename = f"{self.SCREENSHOT_DIR}/{test_name}_{timestamp}.png"

        # 截图
        screenshot_path = page.take_screenshot(filename, description)
        self.test_logger.log_screenshot(screenshot_path, description)

        return screenshot_path

    def switch_to_new_window(self) -> None:
        """切换到新窗口"""
        from pages.base_page import BasePage
        page = BasePage(self.driver)
        page.switch_to_window()
        self.test_logger.log_action("切换到新窗口")

    def accept_alert(self) -> None:
        """接受警告框"""
        from pages.base_page import BasePage
        page = BasePage(self.driver)
        page.accept_alert()
        self.test_logger.log_action("接受警告框")

    def dismiss_alert(self) -> None:
        """取消警告框"""
        from pages.base_page import BasePage
        page = BasePage(self.driver)
        page.dismiss_alert()
        self.test_logger.log_action("取消警告框")

    # ==================== pytest兼容性 ====================

    @pytest.fixture(autouse=True)
    def pytest_setup_teardown(self):
        """pytest兼容性设置"""
        yield


if __name__ == "__main__":
    # 测试BaseTest类
    print("测试BaseTest类...")

    # 创建测试配置
    test_config = {
        'project': {
            'name': '测试项目',
            'version': '1.0.0'
        },
        'environment': {
            'base_url': 'https://www.example.com',
            'test_env': 'test'
        },
        'browser': {
            'name': 'chrome',
            'headless': True,
            'window_size': '1920x1080',
            'implicit_wait': 10,
            'page_load_timeout': 30
        },
        'test': {
            'retry_count': 2,
            'timeout': 30,
            'screenshot_on_failure': True,
            'screenshot_path': './reports/screenshots'
        },
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'file': './logs/test.log',
            'max_size': 10485760,
            'backup_count': 5
        }
    }

    # 保存测试配置
    import yaml
    os.makedirs('./config', exist_ok=True)
    with open('./config/test_config.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(test_config, f, default_flow_style=False, allow_unicode=True)

    print("测试配置已创建: ./config/test_config.yaml")
    print("BaseTest类测试完成")
