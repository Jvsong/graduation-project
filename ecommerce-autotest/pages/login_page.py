#!/usr/bin/env python3
"""
shop-system 登录页页面对象。
"""

import time
from typing import Optional, Tuple

from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class LoginPage(BasePage):
    """封装 shop-system 登录页相关操作。"""

    url = "/admin/login"

    USERNAME_INPUT = (By.ID, "username")
    PASSWORD_INPUT = (By.ID, "password")
    LOGIN_BUTTON = (By.ID, "login-btn")
    ERROR_MESSAGE = (By.ID, "error-msg")
    REMEMBER_ME_CHECKBOX = (
        By.XPATH,
        "//*[@id='remember-me' or @for='remember-me' or self::label[contains(normalize-space(.), '记住我')] or .//span[contains(normalize-space(.), '记住我')]]",
    )
    FORGOT_PASSWORD_LINK = (
        By.XPATH,
        "//*[@id='forgot-password' or self::a[contains(normalize-space(.), '忘记密码')] or self::button[contains(normalize-space(.), '忘记密码')] or .//span[contains(normalize-space(.), '忘记密码')]]",
    )
    FORGOT_PASSWORD_MODAL = (
        By.XPATH,
        "//div[contains(@class,'el-dialog') and .//*[contains(normalize-space(.), '忘记密码')]]",
    )

    DASHBOARD_MARKER = (By.CSS_SELECTOR, ".main-content")
    TOP_NAVBAR = (By.CSS_SELECTOR, ".navbar")
    SUB_NAVBAR = (By.CSS_SELECTOR, "#sidebar")
    APP_ROOT = (By.ID, "app")
    CURRENT_USERNAME = (By.CSS_SELECTOR, ".user-info span")

    def __init__(self, driver):
        super().__init__(driver)
        self.logger.info("初始化 shop-system 登录页面对象")

    def open_login_page(self, base_url: Optional[str] = None) -> None:
        if not base_url:
            from utils.config_manager import get_config

            config = get_config()
            base_url = config.get("environment.base_url", "http://localhost:3000")

        full_url = f"{base_url.rstrip('/')}{self.url}"
        self.logger.info(f"打开登录页面: {full_url}")
        self.open(full_url)

    def enter_username(self, username: str) -> None:
        self.type(self.USERNAME_INPUT, username)

    def enter_password(self, password: str) -> None:
        self.type(self.PASSWORD_INPUT, password)

    def click_login_button(self) -> None:
        self.click(self.LOGIN_BUTTON)

    def click_remember_me(self) -> None:
        element = self.find_clickable_element(self.REMEMBER_ME_CHECKBOX, timeout=5)
        try:
            element.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", element)

    def click_forgot_password(self) -> None:
        element = self.find_clickable_element(self.FORGOT_PASSWORD_LINK, timeout=5)
        try:
            element.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", element)

    def login(self, username: str, password: str, remember_me: bool = False) -> None:
        self.enter_username(username)
        self.enter_password(password)

        if remember_me and not self.is_remember_me_checked():
            self.click_remember_me()

        self.click_login_button()
        time.sleep(1)

    def get_error_message(self) -> str:
        try:
            return self.get_text(self.ERROR_MESSAGE, timeout=5)
        except Exception:
            return ""

    def is_login_successful(self, timeout: int = 10) -> bool:
        try:
            current_url = self.get_current_url()
            if "/admin/dashboard" in current_url or "/admin/products" in current_url or "/admin/orders" in current_url:
                return True

            token = self.execute_script("return window.localStorage.getItem('token');")
            auth_state = self.execute_script("return window.localStorage.getItem('auth_state');")
            if (token or auth_state) and (
                self.is_element_present(self.TOP_NAVBAR, timeout=3)
                or self.is_element_present(self.SUB_NAVBAR, timeout=3)
                or self.is_element_present(self.DASHBOARD_MARKER, timeout=3)
            ):
                return True

            return self.is_element_present(self.DASHBOARD_MARKER, timeout=timeout)
        except Exception:
            return False

    def is_error_message_displayed(self, timeout: int = 5) -> bool:
        return self.is_element_present(self.ERROR_MESSAGE, timeout=timeout)

    def is_remember_me_checked(self) -> bool:
        try:
            checkbox = self.find_element((By.ID, "remember-me"), timeout=2)
            return checkbox.is_selected()
        except Exception:
            try:
                element = self.find_element(self.REMEMBER_ME_CHECKBOX, timeout=2)
                checked = element.get_attribute("aria-checked")
                classes = element.get_attribute("class") or ""
                return checked == "true" or "is-checked" in classes
            except Exception:
                return False

    def is_forgot_password_dialog_visible(self, timeout: int = 5) -> bool:
        return self.is_element_present(self.FORGOT_PASSWORD_MODAL, timeout=timeout)

    def is_element_present(self, locator: Tuple[By, str], timeout: Optional[int] = None) -> bool:
        try:
            self.find_element(locator, timeout=timeout)
            return True
        except Exception:
            return False

    def clear_login_form(self) -> None:
        self.find_element(self.USERNAME_INPUT).clear()
        self.find_element(self.PASSWORD_INPUT).clear()

    def wait_for_login_page_load(self, timeout: int = 30) -> None:
        self.wait_for_page_load(timeout)
        self.find_visible_element(self.USERNAME_INPUT, timeout=10)
        self.find_visible_element(self.PASSWORD_INPUT, timeout=10)
        self.find_clickable_element(self.LOGIN_BUTTON, timeout=10)

    def take_login_page_screenshot(self, filename: Optional[str] = None) -> str:
        if filename is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"./reports/screenshots/login_page_{timestamp}.png"
        return self.take_screenshot(filename, "登录页面截图")

    def get_page_title(self) -> str:
        return self.get_title()

    def verify_login_page_elements(self) -> bool:
        elements = [
            self.USERNAME_INPUT,
            self.PASSWORD_INPUT,
            self.LOGIN_BUTTON,
            self.REMEMBER_ME_CHECKBOX,
            self.FORGOT_PASSWORD_LINK,
            self.APP_ROOT,
        ]
        return all(self.is_element_present(locator, timeout=5) for locator in elements)


def create_login_page(driver):
    return LoginPage(driver)
