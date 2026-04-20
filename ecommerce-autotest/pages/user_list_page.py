#!/usr/bin/env python3
"""
用户列表页面对象。
适配当前 shop-system 的 Element Plus 用户管理页。
"""

import time
from typing import Any, Dict, List, Optional

from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class UserListPage(BasePage):
    url = "/admin/users"

    SEARCH_INPUT = (By.CSS_SELECTOR, ".search-form .el-input input")
    STATUS_FILTER = (
        By.XPATH,
        "(//div[contains(@class,'search-form')]//div[contains(@class,'el-select__wrapper')])[1]",
    )
    USER_TYPE_FILTER = (
        By.XPATH,
        "(//div[contains(@class,'search-form')]//div[contains(@class,'el-select__wrapper')])[2]",
    )
    SEARCH_BUTTON = (By.XPATH, "//button[.//span[contains(normalize-space(), '搜索')]]")
    RESET_BUTTON = (By.XPATH, "//button[.//span[contains(normalize-space(), '重置')]]")
    ADD_USER_BUTTON = (By.XPATH, "//button[.//span[contains(normalize-space(), '添加用户')]]")

    USER_TABLE = (By.CSS_SELECTOR, ".table-card .el-table, .table-card table")
    TABLE_ROWS = (
        By.CSS_SELECTOR,
        ".table-card .el-table__body-wrapper tbody tr, .table-card .el-table__body tbody tr, .table-card table tbody tr",
    )
    TABLE_HEADERS = (By.CSS_SELECTOR, ".table-card .el-table__header-wrapper th, .table-card table thead th")
    NO_DATA = (By.XPATH, "//div[contains(@class,'el-table__empty-text') and contains(normalize-space(), '暂无数据')]")
    SORTABLE_HEADER = (
        By.XPATH,
        "//th[.//*[contains(normalize-space(), '用户名') or contains(normalize-space(), '注册时间') or contains(normalize-space(), '最后登录')]]",
    )

    def __init__(self, driver):
        super().__init__(driver)
        self.logger.info("初始化用户列表页面对象")

    def open_user_list_page(self, base_url: Optional[str] = None) -> None:
        if not base_url:
            from utils.config_manager import get_config

            config = get_config()
            base_url = config.get("environment.base_url", "http://localhost:3000")

        full_url = f"{base_url.rstrip('/')}{self.url}"
        self.logger.info(f"打开用户列表页面: {full_url}")
        self.open(full_url)
        self.wait_for_page_load()
        self.wait_for_user_table_loaded()

    def wait_for_user_table_loaded(self, timeout: int = 30) -> None:
        self.logger.info("等待用户表格加载完成")
        self.find_element(self.USER_TABLE, timeout=timeout)
        time.sleep(1)

    def _select_dropdown_option(self, trigger, visible_text: str) -> None:
        self.click(trigger)
        option = (
            By.XPATH,
            f"//div[contains(@class,'el-select-dropdown')]//*[contains(@class,'el-select-dropdown__item')][normalize-space()='{visible_text}']",
        )
        self.click(option)

    def search_user(self, keyword: str, search_type: str = "username") -> None:
        self.logger.info(f"搜索用户 - 类型: {search_type}, 关键词: {keyword}")
        self.type(self.SEARCH_INPUT, keyword)
        self.click(self.SEARCH_BUTTON)
        time.sleep(1)
        self.wait_for_user_table_loaded()

    def filter_by_role(self, role: str) -> None:
        self.logger.info(f"按用户类型筛选用户: {role}")
        self._select_dropdown_option(self.USER_TYPE_FILTER, role)
        self.click(self.SEARCH_BUTTON)
        time.sleep(1)
        self.wait_for_user_table_loaded()

    def filter_by_status(self, status: str) -> None:
        self.logger.info(f"按状态筛选用户: {status}")
        self._select_dropdown_option(self.STATUS_FILTER, status)
        self.click(self.SEARCH_BUTTON)
        time.sleep(1)
        self.wait_for_user_table_loaded()

    def sort_by(self, sort_option: str) -> None:
        mapping = {
            "username_asc": "用户名",
            "username_desc": "用户名",
            "create_time_asc": "注册时间",
            "create_time_desc": "注册时间",
            "last_login_asc": "最后登录",
            "last_login_desc": "最后登录",
        }
        label = mapping.get(sort_option)
        if not label:
            self.logger.warning(f"不支持的排序选项: {sort_option}")
            return

        clicks = 2 if sort_option.endswith("_desc") else 1
        header = (
            By.XPATH,
            f"//th[.//*[contains(normalize-space(), '{label}')]]",
        )
        for _ in range(clicks):
            self.click(header)
            time.sleep(0.5)
        self.wait_for_user_table_loaded()

    def get_user_rows(self) -> List[Dict[str, Any]]:
        if self.is_element_present(self.NO_DATA, timeout=2):
            return []

        rows = self.find_elements(self.TABLE_ROWS, timeout=5)
        users: List[Dict[str, Any]] = []
        for index, row in enumerate(rows):
            text = row.text.strip()
            if not text or "暂无数据" in text:
                continue

            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) < 8:
                continue

            username_lines = [line.strip() for line in cells[2].text.splitlines() if line.strip()]
            users.append(
                {
                    "row_index": index,
                    "user_id": cells[1].text.strip() if len(cells) > 1 else "",
                    "username": username_lines[0] if username_lines else "",
                    "email": cells[3].text.strip() if len(cells) > 3 else "",
                    "phone": cells[4].text.strip() if len(cells) > 4 else "",
                    "role": cells[5].text.strip() if len(cells) > 5 else "",
                    "status": cells[6].text.strip() if len(cells) > 6 else "",
                    "create_time": cells[8].text.strip() if len(cells) > 8 else "",
                    "last_login": cells[7].text.strip() if len(cells) > 7 else "",
                }
            )
        return users

    def get_user_count(self) -> int:
        return len(self.get_user_rows())

    def get_user_status(self, username: str) -> Optional[str]:
        for user in self.get_user_rows():
            if user.get("username") == username:
                return user.get("status")
        return None

    def verify_user_exists(self, username: str) -> bool:
        return any(user.get("username") == username for user in self.get_user_rows())

    def verify_search_results(self, keyword: str, search_type: str = "username") -> bool:
        keyword = keyword.lower()
        for user in self.get_user_rows():
            if search_type == "username":
                value = user.get("username", "")
            elif search_type == "email":
                value = user.get("email", "")
            elif search_type == "phone":
                value = user.get("phone", "")
            else:
                value = user.get("role", "")
            if keyword in value.lower():
                return True
        return False

    def reset_filters(self) -> None:
        self.click(self.RESET_BUTTON)
        time.sleep(1)
        self.wait_for_user_table_loaded()

    def export_users(self, export_format: str = "excel") -> None:
        export_button = (By.XPATH, "//button[.//span[contains(normalize-space(), '导出')]]")
        if self.is_element_present(export_button, timeout=2):
            self.click(export_button)
            time.sleep(1)
        else:
            self.logger.info("当前用户页未提供导出按钮，跳过导出")

    def verify_user_list_elements(self) -> bool:
        elements = [
            self.SEARCH_INPUT,
            self.SEARCH_BUTTON,
            self.RESET_BUTTON,
            self.USER_TABLE,
            self.ADD_USER_BUTTON,
        ]
        return all(self.is_element_present(locator, timeout=3) for locator in elements)

    def is_element_present(self, locator, timeout: Optional[int] = None) -> bool:
        try:
            self.find_element(locator, timeout=timeout)
            return True
        except Exception:
            return False


def create_user_list_page(driver):
    return UserListPage(driver)
