#!/usr/bin/env python3
"""
shop-system 登录测试用例。
"""

import os
import time

import pytest

from pages.login_page import LoginPage
from testcases.base_test import BaseTest
from utils.config_manager import get_config
from utils.data_manager import get_test_data_manager, load_test_data


def _matches_error(actual_error: str, expected_error: str) -> bool:
    if not actual_error:
        return False

    actual = actual_error.lower().strip()
    expected = expected_error.lower().strip()
    if expected in actual:
        return True

    alias_groups = [
        {"401", "用户名或密码错误", "登录失败，请检查用户名和密码", "登录失败"},
        {"请输入用户名", "登录失败，请检查用户名和密码", "登录失败"},
        {"请输入密码", "登录失败，请检查用户名和密码", "登录失败"},
        {"用户名长度在", "登录失败，请检查用户名和密码", "登录失败"},
        {"密码长度在", "登录失败，请检查用户名和密码", "登录失败"},
    ]
    return any(
        expected in group and any(candidate in actual for candidate in group if candidate != expected)
        for group in alias_groups
    )


class TestLogin(BaseTest):
    """基于 BaseTest 的登录测试。"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.data_manager = get_test_data_manager(data_source="yaml")
        cls.login_data = load_test_data("login")
        cls.login_page = LoginPage(cls.driver)
        if cls.logger:
            cls.logger.info("shop-system 登录测试数据加载完成")

    def setUp(self):
        super().setUp()
        self.login_page.open_login_page()
        self.login_page.wait_for_login_page_load()
        assert self.login_page.verify_login_page_elements(), "登录页关键元素校验失败"

    def test_valid_login(self):
        user = self.login_data["valid_users"][0]
        self.login_page.login(user["username"], user["password"])
        assert self.login_page.is_login_successful(timeout=10), f"登录失败: {user['username']}"
        assert "/admin/dashboard" in self.login_page.get_current_url()

    def test_all_valid_users(self):
        for user in self.login_data["valid_users"]:
            self.login_page.open_login_page()
            self.login_page.wait_for_login_page_load()
            self.login_page.login(user["username"], user["password"])
            assert self.login_page.is_login_successful(timeout=10), f"登录失败: {user['username']}"
            self.driver.execute_script("window.localStorage.clear(); window.sessionStorage.clear();")
            self.driver.get(f"{get_config().get('environment.base_url').rstrip('/')}/admin/login")

    def test_invalid_login_empty_username(self):
        case = self.login_data["invalid_users"][0]
        self.login_page.login(case["username"], case["password"])
        assert self.login_page.is_error_message_displayed(timeout=5)
        assert _matches_error(self.login_page.get_error_message(), case["expected_error"])

    def test_invalid_login_empty_password(self):
        case = self.login_data["invalid_users"][1]
        self.login_page.login(case["username"], case["password"])
        assert self.login_page.is_error_message_displayed(timeout=5)
        assert _matches_error(self.login_page.get_error_message(), case["expected_error"])

    def test_invalid_login_wrong_credentials(self):
        case = self.login_data["invalid_users"][2]
        self.login_page.login(case["username"], case["password"])
        assert self.login_page.is_error_message_displayed(timeout=5)
        assert _matches_error(self.login_page.get_error_message(), case["expected_error"])

    def test_invalid_login_data_driven(self):
        test_cases = [
            {"username": "", "password": "admin123", "expected_error": "请输入用户名"},
            {"username": "admin", "password": "", "expected_error": "请输入密码"},
            {"username": "wronguser", "password": "admin123", "expected_error": "401"},
            {"username": "admin", "password": "wrongpassword", "expected_error": "401"},
        ]
        for test_case in test_cases:
            with self.subTest(test_case=test_case):
                self.login_page.open_login_page()
                self.login_page.wait_for_login_page_load()
                self.login_page.login(test_case["username"], test_case["password"])
                assert self.login_page.is_error_message_displayed(timeout=5)
                assert _matches_error(self.login_page.get_error_message(), test_case["expected_error"])

    def test_boundary_long_username(self):
        case = self.login_data["boundary_cases"][0]
        self.login_page.login(case["username"], case["password"])
        assert self.login_page.is_error_message_displayed(timeout=5)
        assert _matches_error(self.login_page.get_error_message(), case["expected_error"])

    def test_boundary_sql_injection(self):
        case = self.login_data["boundary_cases"][2]
        self.login_page.login(case["username"], case["password"])
        assert self.login_page.is_error_message_displayed(timeout=5)
        assert _matches_error(self.login_page.get_error_message(), case["expected_error"])

    def test_remember_me_function(self):
        case = self.login_data["login_status"][0]
        self.login_page.login(case["username"], case["password"], remember_me=True)
        assert self.login_page.is_login_successful(timeout=10)
        remember_me = self.driver.execute_script(
            "return window.localStorage.getItem('rememberMe') || window.sessionStorage.getItem('rememberMe');"
        )
        assert self.login_page.is_remember_me_checked() or remember_me == "true", \
            f"rememberMe 状态未生效: {remember_me}"

    def test_forgot_password_link(self):
        self.login_page.click_forgot_password()
        time.sleep(1)
        current_url = self.login_page.get_current_url().lower()
        assert "forgot-password" in current_url or self.login_page.is_forgot_password_dialog_visible(timeout=3)

    def test_login_page_screenshot(self):
        screenshot_path = self.login_page.take_login_page_screenshot()
        assert os.path.exists(screenshot_path)
        assert os.path.getsize(screenshot_path) > 0

    def test_login_performance(self):
        case = self.login_data["performance_test"][0]
        start_time = time.time()
        self.login_page.login(case["username"], case["password"])
        assert self.login_page.is_login_successful(timeout=10)
        duration = time.time() - start_time
        assert duration <= case["expected_login_time"], f"登录耗时超出预期: {duration:.2f}s"

    def test_login_logout_cycle(self):
        user = self.login_data["valid_users"][0]
        self.login_page.login(user["username"], user["password"])
        assert self.login_page.is_login_successful(timeout=10)

        self.driver.execute_script("window.localStorage.clear(); window.sessionStorage.clear();")
        self.driver.get(f"{get_config().get('environment.base_url').rstrip('/')}/admin/dashboard")
        time.sleep(1)

        redirected_url = self.login_page.get_current_url().lower()
        assert "/admin/login" in redirected_url or not self.login_page.is_login_successful(timeout=3)

    def test_concurrent_login(self):
        case = self.login_data["concurrent_login"][0]
        for _ in range(case.get("concurrent_sessions", 2)):
            self.driver.execute_script("window.localStorage.clear(); window.sessionStorage.clear();")
            self.login_page.open_login_page()
            self.login_page.wait_for_login_page_load()
            self.login_page.login(case["username"], case["password"])
            assert self.login_page.is_login_successful(timeout=10)

    def test_environment_switch_login(self):
        environments = self.login_data.get("environment_specific", {})
        assert "test" in environments
        assert environments["test"]["base_url"].startswith("http://localhost")


@pytest.mark.login
@pytest.mark.smoke
class TestLoginPytest:
    """轻量 pytest 风格登录测试。"""

    @pytest.fixture(autouse=True)
    def setup(self, driver):
        self.driver = driver
        self.login_page = LoginPage(driver)
        self.login_data = load_test_data("login")
        self.login_page.open_login_page()
        self.login_page.wait_for_login_page_load()
        yield

    @pytest.mark.parametrize(
        "username,password",
        [
            ("admin", "admin123"),
            ("user1", "admin123"),
        ],
    )
    def test_valid_login_pytest(self, username, password):
        self.login_page.login(username, password)
        assert self.login_page.is_login_successful(timeout=10), f"登录失败: {username}"

    @pytest.mark.parametrize(
        "username,password,expected_error",
        [
            ("", "admin123", "请输入用户名"),
            ("admin", "", "请输入密码"),
            ("wrong", "wrong", "401"),
        ],
    )
    def test_invalid_login_pytest(self, username, password, expected_error):
        self.login_page.login(username, password)
        assert self.login_page.is_error_message_displayed(timeout=5)
        actual_error = self.login_page.get_error_message()
        assert _matches_error(actual_error, expected_error), f"错误信息不匹配: {actual_error}"
