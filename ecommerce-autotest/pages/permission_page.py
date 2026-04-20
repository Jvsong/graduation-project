#!/usr/bin/env python3
"""
权限管理页面对象。
适配当前 shop-system 的权限管理页。
"""

import time
from typing import Any, Dict, List, Optional

from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class PermissionPage(BasePage):
    url_role_list = "/admin/permissions"
    url_role_add = "/admin/permissions"
    url_role_edit = "/admin/permissions"
    url_permission_manage = "/admin/permissions"

    PAGE_TITLE = (By.XPATH, "//*[contains(normalize-space(), '权限管理')]")
    ROLE_SEARCH_INPUT = (By.CSS_SELECTOR, ".search-form .el-input input")
    STATUS_FILTER = (
        By.XPATH,
        "(//div[contains(@class,'search-form')]//div[contains(@class,'el-select__wrapper')])[1]",
    )
    ROLE_SEARCH_BUTTON = (By.XPATH, "//button[.//span[contains(normalize-space(), '搜索')]]")
    RESET_BUTTON = (By.XPATH, "//button[.//span[contains(normalize-space(), '重置')]]")
    ADD_ROLE_BUTTON = (By.XPATH, "//button[.//span[contains(normalize-space(), '新增角色')]]")
    ROLE_TABLE = (By.CSS_SELECTOR, ".table-card .el-table, .table-card table")
    ROLE_TABLE_ROWS = (
        By.CSS_SELECTOR,
        ".table-card .el-table__body-wrapper tbody tr, .table-card .el-table__body tbody tr, .table-card table tbody tr",
    )
    SUCCESS_MESSAGE = (By.CSS_SELECTOR, ".el-message--success, .success-message")

    ROLE_NAME_INPUT = (
        By.XPATH,
        "//div[contains(@class,'el-dialog')]//input[contains(@placeholder,'角色名称') or contains(@placeholder,'请输入角色名称')]",
    )
    ROLE_CODE_INPUT = (
        By.XPATH,
        "//div[contains(@class,'el-dialog')]//input[contains(@placeholder,'角色编码') or contains(@placeholder,'请输入角色编码')]",
    )
    ROLE_DESCRIPTION_TEXTAREA = (
        By.XPATH,
        "//div[contains(@class,'el-dialog')]//textarea[contains(@placeholder,'角色描述') or contains(@placeholder,'请输入角色描述')]",
    )
    ROLE_STATUS_SELECT = (
        By.XPATH,
        "(//div[contains(@class,'el-dialog')]//div[contains(@class,'el-select__wrapper')])[1]",
    )
    ROLE_SAVE_BUTTON = (
        By.XPATH,
        "//div[contains(@class,'el-dialog')]//button[.//span[contains(normalize-space(), '保存') or contains(normalize-space(), '确定')]]",
    )

    PERMISSION_TREE = (By.XPATH, "//div[contains(@class,'el-tree') or contains(@class,'permission-tree')]")

    def __init__(self, driver):
        super().__init__(driver)
        self.logger.info("初始化权限管理页面对象")

    def open_role_list_page(self, base_url: Optional[str] = None) -> None:
        if not base_url:
            from utils.config_manager import get_config

            config = get_config()
            base_url = config.get("environment.base_url", "http://localhost:3000")

        full_url = f"{base_url.rstrip('/')}{self.url_role_list}"
        self.logger.info(f"打开角色列表页面: {full_url}")
        self.open(full_url)
        self.wait_for_page_load()
        self.wait_for_role_table_loaded()

    def open_role_add_page(self, base_url: Optional[str] = None) -> None:
        self.open_role_list_page(base_url=base_url)
        self.click(self.ADD_ROLE_BUTTON)
        self.wait_for_role_form_loaded()

    def open_role_edit_page(self, role_id: int, base_url: Optional[str] = None) -> None:
        self.open_role_list_page(base_url=base_url)
        rows = self.get_role_rows()
        for row in rows:
            if str(row.get("role_id")) == str(role_id):
                self._click_row_action(row["row_index"], "编辑")
                self.wait_for_role_form_loaded()
                return
        raise ValueError(f"未找到角色ID: {role_id}")

    def open_permission_manage_page(self, role_id: Optional[int] = None, base_url: Optional[str] = None) -> None:
        self.open_role_list_page(base_url=base_url)
        if role_id is not None:
            rows = self.get_role_rows()
            for row in rows:
                if str(row.get("role_id")) == str(role_id):
                    self._click_row_action(row["row_index"], "分配权限")
                    self.wait_for_permission_tree_loaded()
                    return
        self.wait_for_role_table_loaded()

    def wait_for_role_table_loaded(self, timeout: int = 30) -> None:
        self.find_element(self.PAGE_TITLE, timeout=timeout)
        self.find_element(self.ROLE_TABLE, timeout=timeout)
        time.sleep(1)

    def wait_for_role_form_loaded(self, timeout: int = 30) -> None:
        self.find_element(self.ROLE_NAME_INPUT, timeout=timeout)

    def wait_for_permission_tree_loaded(self, timeout: int = 30) -> None:
        self.find_element(self.PERMISSION_TREE, timeout=timeout)

    def search_role(self, keyword: str) -> None:
        self.type(self.ROLE_SEARCH_INPUT, keyword)
        self.click(self.ROLE_SEARCH_BUTTON)
        time.sleep(1)
        self.wait_for_role_table_loaded()

    def get_role_rows(self) -> List[Dict[str, Any]]:
        rows = self.find_elements(self.ROLE_TABLE_ROWS, timeout=5)
        roles: List[Dict[str, Any]] = []
        for index, row in enumerate(rows):
            text = row.text.strip()
            if not text or "暂无数据" in text:
                continue
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) < 7:
                continue
            roles.append(
                {
                    "row_index": index,
                    "role_id": cells[0].text.strip() if len(cells) > 0 else "",
                    "role_name": cells[1].text.strip() if len(cells) > 1 else "",
                    "role_code": cells[2].text.strip() if len(cells) > 2 else "",
                    "description": cells[3].text.strip() if len(cells) > 3 else "",
                    "permission_count": cells[4].text.strip() if len(cells) > 4 else "",
                    "status": cells[5].text.strip() if len(cells) > 5 else "",
                    "create_time": cells[6].text.strip() if len(cells) > 6 else "",
                }
            )
        return roles

    def _click_row_action(self, row_index: int, action_text: str) -> None:
        rows = self.find_elements(self.ROLE_TABLE_ROWS, timeout=5)
        target = rows[row_index].find_element(
            By.XPATH,
            f".//*[self::button or self::a or self::span][contains(normalize-space(), '{action_text}')]",
        )
        target.click()

    def create_role(self, role_data: Dict[str, Any]) -> bool:
        self.open_role_add_page()
        self.type(self.ROLE_NAME_INPUT, role_data.get("name", ""))
        self.type(self.ROLE_CODE_INPUT, role_data.get("code", ""))
        if role_data.get("description") and self.is_element_present(self.ROLE_DESCRIPTION_TEXTAREA, timeout=2):
            self.type(self.ROLE_DESCRIPTION_TEXTAREA, role_data["description"])
        if role_data.get("status") and self.is_element_present(self.ROLE_STATUS_SELECT, timeout=2):
            self.click(self.ROLE_STATUS_SELECT)
            option = (
                By.XPATH,
                f"//div[contains(@class,'el-select-dropdown')]//*[contains(@class,'el-select-dropdown__item')][contains(normalize-space(), '{role_data['status']}')]",
            )
            if self.is_element_present(option, timeout=2):
                self.click(option)
        self.click(self.ROLE_SAVE_BUTTON)
        time.sleep(1)
        return True

    def edit_role(self, role_id: int, updates: Dict[str, Any]) -> bool:
        self.open_role_edit_page(role_id)
        if updates.get("name"):
            self.type(self.ROLE_NAME_INPUT, updates["name"])
        if updates.get("description") and self.is_element_present(self.ROLE_DESCRIPTION_TEXTAREA, timeout=2):
            self.type(self.ROLE_DESCRIPTION_TEXTAREA, updates["description"])
        self.click(self.ROLE_SAVE_BUTTON)
        time.sleep(1)
        return True

    def delete_role(self, role_id: int) -> bool:
        self.open_role_list_page()
        rows = self.get_role_rows()
        for row in rows:
            if str(row.get("role_id")) == str(role_id):
                self._click_row_action(row["row_index"], "删除")
                confirm = (
                    By.XPATH,
                    "//button[.//span[contains(normalize-space(), '确定') or contains(normalize-space(), '删除')]]",
                )
                if self.is_element_present(confirm, timeout=3):
                    self.click(confirm)
                time.sleep(1)
                return True
        return False

    def assign_permissions_to_role(self, role_id: int, permissions: List[str]) -> bool:
        self.open_permission_manage_page(role_id)
        for permission in permissions:
            node = (
                By.XPATH,
                f"//*[contains(@class,'el-tree-node') and contains(normalize-space(), '{permission}')]//label[contains(@class,'el-checkbox')]",
            )
            if self.is_element_present(node, timeout=2):
                self.click(node)
        save_button = (
            By.XPATH,
            "//button[.//span[contains(normalize-space(), '保存') or contains(normalize-space(), '确定')]]",
        )
        if self.is_element_present(save_button, timeout=2):
            self.click(save_button)
        time.sleep(1)
        return True

    def assign_users_to_role(self, role_id: int, usernames: List[str]) -> bool:
        self.open_role_list_page()
        rows = self.get_role_rows()
        for row in rows:
            if str(row.get("role_id")) == str(role_id):
                self._click_row_action(row["row_index"], "分配用户")
                for username in usernames:
                    search_input = (
                        By.XPATH,
                        "//div[contains(@class,'el-dialog')]//input[contains(@placeholder,'用户') or contains(@placeholder,'搜索')]",
                    )
                    if self.is_element_present(search_input, timeout=2):
                        self.type(search_input, username)
                save_button = (
                    By.XPATH,
                    "//div[contains(@class,'el-dialog')]//button[.//span[contains(normalize-space(), '保存') or contains(normalize-space(), '确定')]]",
                )
                if self.is_element_present(save_button, timeout=2):
                    self.click(save_button)
                time.sleep(1)
                return True
        return False

    def get_role_permissions(self, role_id: int) -> List[str]:
        self.open_permission_manage_page(role_id)
        labels = self.find_elements((By.CSS_SELECTOR, ".el-tree-node__label"), timeout=5)
        return [label.text.strip() for label in labels if label.text.strip()]

    def verify_permission_assigned(self, role_id: int, permission: str) -> bool:
        return any(permission in item for item in self.get_role_permissions(role_id))

    def switch_permission_tab(self, tab_name: str) -> None:
        tab = (
            By.XPATH,
            f"//*[contains(@class,'el-tabs__item') and contains(normalize-space(), '{tab_name}')]",
        )
        self.click(tab)
        time.sleep(1)

    def get_success_message(self) -> str:
        try:
            return self.get_text(self.SUCCESS_MESSAGE, timeout=3)
        except Exception:
            return ""

    def verify_role_exists(self, role_name: str) -> bool:
        return any(role.get("role_name") == role_name for role in self.get_role_rows())

    def is_element_present(self, locator, timeout: Optional[int] = None) -> bool:
        try:
            self.find_element(locator, timeout=timeout)
            return True
        except Exception:
            return False


def create_permission_page(driver):
    return PermissionPage(driver)
