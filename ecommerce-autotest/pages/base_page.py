#!/usr/bin/env python3
"""
基础页面类
所有页面对象的基类，提供通用的页面操作和元素定位方法
"""

import os
import time
from typing import Tuple, Optional, List, Any, Union
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
    ElementNotInteractableException
)

from utils.logger import get_logger


class BasePage:
    """
    页面对象模型（POM）基类
    提供统一的页面操作方法
    """

    # 默认等待时间
    DEFAULT_TIMEOUT = 30
    DEFAULT_POLL_FREQUENCY = 0.5

    def __init__(self, driver: WebDriver):
        """
        初始化页面对象

        Args:
            driver: WebDriver实例
        """
        self.driver = driver
        self.timeout = self.DEFAULT_TIMEOUT
        self.poll_frequency = self.DEFAULT_POLL_FREQUENCY
        self.wait = WebDriverWait(
            driver,
            self.timeout,
            poll_frequency=self.poll_frequency
        )

        # 获取日志器
        self.logger = get_logger(self.__class__.__name__)

        # 页面URL（优先使用子类定义的类属性）
        self.url = getattr(self, "url", None)

    # ==================== 页面导航方法 ====================

    def open(self, url: Optional[str] = None) -> None:
        """
        打开页面

        Args:
            url: 页面URL，如果为None则使用self.url
        """
        target_url = url or self.url
        if not target_url:
            raise ValueError("页面URL未设置")

        self.logger.info(f"打开页面: {target_url}")
        self.driver.get(target_url)
        self.wait_for_page_load()

    def refresh(self) -> None:
        """刷新当前页面"""
        self.logger.debug("刷新页面")
        self.driver.refresh()
        self.wait_for_page_load()

    def go_back(self) -> None:
        """返回上一页"""
        self.logger.debug("返回上一页")
        self.driver.back()
        self.wait_for_page_load()

    def go_forward(self) -> None:
        """前进到下一页"""
        self.logger.debug("前进到下一页")
        self.driver.forward()
        self.wait_for_page_load()

    def get_current_url(self) -> str:
        """获取当前页面URL"""
        return self.driver.current_url

    def get_title(self) -> str:
        """获取页面标题"""
        return self.driver.title

    # ==================== 元素定位方法 ====================

    def find_element(self, locator: Tuple[By, str], timeout: Optional[float] = None) -> WebElement:
        """
        查找单个元素（带等待）

        Args:
            locator: 定位器元组，如 (By.ID, 'username')
            timeout: 等待超时时间，如果为None则使用self.timeout

        Returns:
            WebElement: 找到的元素
        """
        by, value = locator
        wait_timeout = timeout or self.timeout

        self.logger.debug(f"查找元素: {by}='{value}' (timeout={wait_timeout})")

        try:
            element = WebDriverWait(
                self.driver,
                wait_timeout,
                poll_frequency=self.poll_frequency
            ).until(
                EC.presence_of_element_located(locator)
            )
            self.logger.debug(f"元素找到: {by}='{value}'")
            return element

        except TimeoutException:
            self.logger.error(f"元素未找到: {by}='{value}' (timeout={wait_timeout}s)")
            raise

    def find_elements(self, locator: Tuple[By, str], timeout: Optional[float] = None) -> List[WebElement]:
        """
        查找多个元素（带等待）

        Args:
            locator: 定位器元组
            timeout: 等待超时时间

        Returns:
            List[WebElement]: 找到的元素列表
        """
        by, value = locator
        wait_timeout = timeout or self.timeout

        self.logger.debug(f"查找多个元素: {by}='{value}' (timeout={wait_timeout})")

        try:
            elements = WebDriverWait(
                self.driver,
                wait_timeout,
                poll_frequency=self.poll_frequency
            ).until(
                EC.presence_of_all_elements_located(locator)
            )
            self.logger.debug(f"找到 {len(elements)} 个元素: {by}='{value}'")
            return elements

        except TimeoutException:
            self.logger.warning(f"未找到任何元素: {by}='{value}'")
            return []

    def find_visible_element(self, locator: Tuple[By, str], timeout: Optional[float] = None) -> WebElement:
        """
        查找可见的元素

        Args:
            locator: 定位器元组
            timeout: 等待超时时间

        Returns:
            WebElement: 找到的可见元素
        """
        by, value = locator
        wait_timeout = timeout or self.timeout

        self.logger.debug(f"查找可见元素: {by}='{value}'")

        try:
            element = WebDriverWait(
                self.driver,
                wait_timeout,
                poll_frequency=self.poll_frequency
            ).until(
                EC.visibility_of_element_located(locator)
            )
            self.logger.debug(f"可见元素找到: {by}='{value}'")
            return element

        except TimeoutException:
            self.logger.error(f"可见元素未找到: {by}='{value}'")
            raise

    def find_clickable_element(self, locator: Tuple[By, str], timeout: Optional[float] = None) -> WebElement:
        """
        查找可点击的元素

        Args:
            locator: 定位器元组
            timeout: 等待超时时间

        Returns:
            WebElement: 找到的可点击元素
        """
        by, value = locator
        wait_timeout = timeout or self.timeout

        self.logger.debug(f"查找可点击元素: {by}='{value}'")

        try:
            element = WebDriverWait(
                self.driver,
                wait_timeout,
                poll_frequency=self.poll_frequency
            ).until(
                EC.element_to_be_clickable(locator)
            )
            self.logger.debug(f"可点击元素找到: {by}='{value}'")
            return element

        except TimeoutException:
            self.logger.error(f"可点击元素未找到: {by}='{value}'")
            raise

    # ==================== 元素操作方法 ====================

    def click(self, locator: Tuple[By, str], timeout: Optional[float] = None) -> None:
        """
        点击元素

        Args:
            locator: 定位器元组
            timeout: 等待超时时间
        """
        by, value = locator
        self.logger.debug(f"点击元素: {by}='{value}'")

        element = self.find_clickable_element(locator, timeout)

        try:
            element.click()
            self.logger.debug(f"元素点击成功: {by}='{value}'")
        except Exception as e:
            self.logger.error(f"元素点击失败: {by}='{value}', 错误: {e}")
            raise

    def type(self, locator: Tuple[By, str], text: str, timeout: Optional[float] = None) -> None:
        """
        在输入框中输入文本

        Args:
            locator: 定位器元组
            text: 要输入的文本
            timeout: 等待超时时间
        """
        by, value = locator
        self.logger.debug(f"输入文本到元素: {by}='{value}', 文本: '{text}'")

        element = self.find_visible_element(locator, timeout)

        try:
            # 清空输入框
            element.clear()
            # 输入文本
            element.send_keys(text)
            self.logger.debug(f"文本输入成功: {by}='{value}'")
        except Exception as e:
            self.logger.error(f"文本输入失败: {by}='{value}', 错误: {e}")
            raise

    def get_text(self, locator: Tuple[By, str], timeout: Optional[float] = None) -> str:
        """
        获取元素的文本内容

        Args:
            locator: 定位器元组
            timeout: 等待超时时间

        Returns:
            str: 元素的文本内容
        """
        by, value = locator
        self.logger.debug(f"获取元素文本: {by}='{value}'")

        element = self.find_visible_element(locator, timeout)

        try:
            text = element.text
            self.logger.debug(f"获取到文本: '{text}' (元素: {by}='{value}')")
            return text
        except Exception as e:
            self.logger.error(f"获取文本失败: {by}='{value}', 错误: {e}")
            raise

    def get_attribute(self, locator: Tuple[By, str], attribute: str, timeout: Optional[float] = None) -> str:
        """
        获取元素的属性值

        Args:
            locator: 定位器元组
            attribute: 属性名
            timeout: 等待超时时间

        Returns:
            str: 属性值
        """
        by, value = locator
        self.logger.debug(f"获取元素属性: {by}='{value}', 属性: '{attribute}'")

        element = self.find_element(locator, timeout)

        try:
            value = element.get_attribute(attribute)
            self.logger.debug(f"获取到属性值: '{value}' (元素: {by}='{value}', 属性: '{attribute}')")
            return value or ""
        except Exception as e:
            self.logger.error(f"获取属性失败: {by}='{value}', 属性: '{attribute}', 错误: {e}")
            raise

    def is_displayed(self, locator: Tuple[By, str], timeout: Optional[float] = None) -> bool:
        """
        检查元素是否显示

        Args:
            locator: 定位器元组
            timeout: 等待超时时间

        Returns:
            bool: 如果元素显示则返回True
        """
        by, value = locator

        try:
            element = self.find_visible_element(locator, timeout)
            displayed = element.is_displayed()
            self.logger.debug(f"元素显示状态: {displayed} (元素: {by}='{value}')")
            return displayed
        except (TimeoutException, NoSuchElementException):
            self.logger.debug(f"元素未找到或不可见: {by}='{value}'")
            return False

    def is_enabled(self, locator: Tuple[By, str], timeout: Optional[float] = None) -> bool:
        """
        检查元素是否启用

        Args:
            locator: 定位器元组
            timeout: 等待超时时间

        Returns:
            bool: 如果元素启用则返回True
        """
        by, value = locator

        try:
            element = self.find_element(locator, timeout)
            enabled = element.is_enabled()
            self.logger.debug(f"元素启用状态: {enabled} (元素: {by}='{value}')")
            return enabled
        except (TimeoutException, NoSuchElementException):
            self.logger.debug(f"元素未找到: {by}='{value}'")
            return False

    def is_selected(self, locator: Tuple[By, str], timeout: Optional[float] = None) -> bool:
        """
        检查元素是否被选中（用于复选框、单选框）

        Args:
            locator: 定位器元组
            timeout: 等待超时时间

        Returns:
            bool: 如果元素被选中则返回True
        """
        by, value = locator

        try:
            element = self.find_element(locator, timeout)
            selected = element.is_selected()
            self.logger.debug(f"元素选中状态: {selected} (元素: {by}='{value}')")
            return selected
        except (TimeoutException, NoSuchElementException):
            self.logger.debug(f"元素未找到: {by}='{value}'")
            return False

    # ==================== 等待方法 ====================

    def wait_for_page_load(self, timeout: Optional[float] = None) -> None:
        """
        等待页面加载完成

        Args:
            timeout: 等待超时时间
        """
        wait_timeout = timeout or self.timeout

        self.logger.debug(f"等待页面加载完成 (timeout={wait_timeout})")

        try:
            WebDriverWait(self.driver, wait_timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            self.logger.debug("页面加载完成")
        except TimeoutException:
            self.logger.warning(f"页面加载超时 (timeout={wait_timeout}s)")

    def wait_for_element(self, locator: Tuple[By, str], timeout: Optional[float] = None) -> WebElement:
        """
        等待元素出现（同find_element）

        Args:
            locator: 定位器元组
            timeout: 等待超时时间

        Returns:
            WebElement: 找到的元素
        """
        return self.find_element(locator, timeout)

    def wait_for_element_visible(self, locator: Tuple[By, str], timeout: Optional[float] = None) -> WebElement:
        """
        等待元素可见

        Args:
            locator: 定位器元组
            timeout: 等待超时时间

        Returns:
            WebElement: 找到的可见元素
        """
        return self.find_visible_element(locator, timeout)

    def wait_for_element_clickable(self, locator: Tuple[By, str], timeout: Optional[float] = None) -> WebElement:
        """
        等待元素可点击

        Args:
            locator: 定位器元组
            timeout: 等待超时时间

        Returns:
            WebElement: 找到的可点击元素
        """
        return self.find_clickable_element(locator, timeout)

    def wait_for_element_disappear(self, locator: Tuple[By, str], timeout: Optional[float] = None) -> bool:
        """
        等待元素消失

        Args:
            locator: 定位器元组
            timeout: 等待超时时间

        Returns:
            bool: 如果元素消失则返回True
        """
        by, value = locator
        wait_timeout = timeout or self.timeout

        self.logger.debug(f"等待元素消失: {by}='{value}'")

        try:
            WebDriverWait(self.driver, wait_timeout).until(
                EC.invisibility_of_element_located(locator)
            )
            self.logger.debug(f"元素已消失: {by}='{value}'")
            return True
        except TimeoutException:
            self.logger.warning(f"元素未消失: {by}='{value}' (timeout={wait_timeout}s)")
            return False

    # ==================== JavaScript操作 ====================

    def execute_script(self, script: str, *args) -> Any:
        """
        执行JavaScript脚本

        Args:
            script: JavaScript代码
            *args: 传递给脚本的参数

        Returns:
            Any: 脚本执行结果
        """
        self.logger.debug(f"执行JavaScript脚本: {script[:100]}...")

        try:
            result = self.driver.execute_script(script, *args)
            self.logger.debug("JavaScript脚本执行成功")
            return result
        except Exception as e:
            self.logger.error(f"JavaScript脚本执行失败: {e}")
            raise

    def scroll_to_element(self, locator: Tuple[By, str]) -> None:
        """
        滚动到指定元素

        Args:
            locator: 定位器元组
        """
        by, value = locator
        self.logger.debug(f"滚动到元素: {by}='{value}'")

        element = self.find_element(locator)
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)

    def scroll_to_top(self) -> None:
        """滚动到页面顶部"""
        self.logger.debug("滚动到页面顶部")
        self.driver.execute_script("window.scrollTo(0, 0);")

    def scroll_to_bottom(self) -> None:
        """滚动到页面底部"""
        self.logger.debug("滚动到页面底部")
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # ==================== 截图方法 ====================

    def take_screenshot(self, filename: str, description: str = "") -> str:
        """
        截图并保存

        Args:
            filename: 截图文件名
            description: 截图描述

        Returns:
            str: 截图文件路径
        """
        # 确保截图目录存在
        screenshot_dir = os.path.dirname(filename)
        if screenshot_dir and not os.path.exists(screenshot_dir):
            os.makedirs(screenshot_dir, exist_ok=True)

        # 截图
        self.driver.save_screenshot(filename)

        # 记录日志
        if description:
            self.logger.info(f"截图保存: {filename} ({description})")
        else:
            self.logger.info(f"截图保存: {filename}")

        return filename

    def take_element_screenshot(self, locator: Tuple[By, str], filename: str) -> str:
        """
        截取指定元素的截图

        Args:
            locator: 定位器元组
            filename: 截图文件名

        Returns:
            str: 截图文件路径
        """
        by, value = locator
        self.logger.debug(f"截取元素截图: {by}='{value}'")

        element = self.find_element(locator)

        # 确保截图目录存在
        screenshot_dir = os.path.dirname(filename)
        if screenshot_dir and not os.path.exists(screenshot_dir):
            os.makedirs(screenshot_dir, exist_ok=True)

        # 截取元素截图
        element.screenshot(filename)

        self.logger.info(f"元素截图保存: {filename} (元素: {by}='{value}')")
        return filename

    # ==================== 页面验证方法 ====================

    def verify_title_contains(self, expected_text: str) -> bool:
        """
        验证页面标题包含指定文本

        Args:
            expected_text: 期望的文本

        Returns:
            bool: 如果标题包含指定文本则返回True
        """
        title = self.get_title()
        result = expected_text in title

        self.logger.debug(f"验证页面标题包含 '{expected_text}': {result} (实际标题: '{title}')")
        return result

    def verify_url_contains(self, expected_text: str) -> bool:
        """
        验证URL包含指定文本

        Args:
            expected_text: 期望的文本

        Returns:
            bool: 如果URL包含指定文本则返回True
        """
        url = self.get_current_url()
        result = expected_text in url

        self.logger.debug(f"验证URL包含 '{expected_text}': {result} (实际URL: '{url}')")
        return result

    def verify_element_text(self, locator: Tuple[By, str], expected_text: str, exact_match: bool = False) -> bool:
        """
        验证元素文本

        Args:
            locator: 定位器元组
            expected_text: 期望的文本
            exact_match: 是否完全匹配

        Returns:
            bool: 如果文本匹配则返回True
        """
        by, value = locator
        actual_text = self.get_text(locator)

        if exact_match:
            result = actual_text == expected_text
        else:
            result = expected_text in actual_text

        self.logger.debug(f"验证元素文本: {by}='{value}' (期望: '{expected_text}', 实际: '{actual_text}', 结果: {result})")
        return result

    def verify_element_exists(self, locator: Tuple[By, str]) -> bool:
        """
        验证元素存在

        Args:
            locator: 定位器元组

        Returns:
            bool: 如果元素存在则返回True
        """
        by, value = locator

        try:
            # 使用较短的超时时间
            self.find_element(locator, timeout=5)
            self.logger.debug(f"元素存在: {by}='{value}'")
            return True
        except TimeoutException:
            self.logger.debug(f"元素不存在: {by}='{value}'")
            return False

    # ==================== 实用方法 ====================

    def switch_to_frame(self, locator: Optional[Tuple[By, str]] = None) -> None:
        """
        切换到iframe

        Args:
            locator: iframe的定位器，如果为None则切换到默认iframe
        """
        if locator:
            by, value = locator
            self.logger.debug(f"切换到iframe: {by}='{value}'")
            frame = self.find_element(locator)
            self.driver.switch_to.frame(frame)
        else:
            self.logger.debug("切换到默认iframe")
            self.driver.switch_to.default_content()

    def switch_to_window(self, window_handle: Optional[str] = None) -> None:
        """
        切换到指定窗口

        Args:
            window_handle: 窗口句柄，如果为None则切换到最新窗口
        """
        if window_handle:
            self.logger.debug(f"切换到窗口: {window_handle}")
            self.driver.switch_to.window(window_handle)
        else:
            # 切换到最新窗口
            handles = self.driver.window_handles
            if len(handles) > 1:
                new_handle = handles[-1]
                self.logger.debug(f"切换到最新窗口: {new_handle}")
                self.driver.switch_to.window(new_handle)

    def accept_alert(self) -> None:
        """接受警告框"""
        self.logger.debug("接受警告框")
        self.driver.switch_to.alert.accept()

    def dismiss_alert(self) -> None:
        """取消警告框"""
        self.logger.debug("取消警告框")
        self.driver.switch_to.alert.dismiss()

    def get_alert_text(self) -> str:
        """获取警告框文本"""
        self.logger.debug("获取警告框文本")
        return self.driver.switch_to.alert.text

    # ==================== 清理方法 ====================

    def close(self) -> None:
        """关闭页面（如果是标签页）"""
        self.logger.debug("关闭页面")
        self.driver.close()

    def quit(self) -> None:
        """退出浏览器（由测试类管理）"""
        # BasePage不管理浏览器的退出，由BaseTest负责
        pass
