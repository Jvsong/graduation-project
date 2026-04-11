#!/usr/bin/env python3
"""
权限管理页面对象
实现电商后台管理系统的角色管理和权限分配功能
"""

import time
from typing import Optional, Tuple, List, Dict, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from pages.base_page import BasePage


class PermissionPage(BasePage):
    """
    权限管理页面对象类
    封装角色管理、权限分配等操作的所有元素和操作
    """

    # 页面URL
    url_role_list = "/admin/permissions"
    url_role_add = "/admin/permissions"
    url_role_edit = "/admin/permissions"
    url_permission_manage = "/admin/permissions"

    # 角色列表页面元素
    ROLE_SEARCH_INPUT = (By.ID, "role-search-input")
    ROLE_SEARCH_BUTTON = (By.ID, "role-search-btn")
    ROLE_TABLE = (By.ID, "role-table")
    ADD_ROLE_BUTTON = (By.ID, "add-role-btn")
    ROLE_TABLE_ROWS = (By.CSS_SELECTOR, "#role-table tbody tr")

    # 角色操作按钮
    ROLE_EDIT_BUTTON = (By.CSS_SELECTOR, ".role-edit-btn")
    ROLE_DELETE_BUTTON = (By.CSS_SELECTOR, ".role-delete-btn")
    ROLE_PERMISSION_BUTTON = (By.CSS_SELECTOR, ".role-permission-btn")
    ROLE_USERS_BUTTON = (By.CSS_SELECTOR, ".role-users-btn")

    # 角色表单元素
    ROLE_NAME_INPUT = (By.ID, "role-name")
    ROLE_CODE_INPUT = (By.ID, "role-code")
    ROLE_DESCRIPTION_TEXTAREA = (By.ID, "role-description")
    ROLE_STATUS_SELECT = (By.ID, "role-status")

    # 权限管理元素
    PERMISSION_TREE = (By.ID, "permission-tree")
    PERMISSION_GROUP = (By.CLASS_NAME, "permission-group")
    PERMISSION_ITEM = (By.CLASS_NAME, "permission-item")
    PERMISSION_CHECKBOX = (By.CLASS_NAME, "permission-checkbox")
    SELECT_ALL_PERMISSIONS = (By.ID, "select-all-permissions")
    EXPAND_ALL_PERMISSIONS = (By.ID, "expand-all-permissions")
    COLLAPSE_ALL_PERMISSIONS = (By.ID, "collapse-all-permissions")

    # 权限分类
    SYSTEM_PERMISSIONS_TAB = (By.ID, "system-permissions-tab")
    PRODUCT_PERMISSIONS_TAB = (By.ID, "product-permissions-tab")
    ORDER_PERMISSIONS_TAB = (By.ID, "order-permissions-tab")
    USER_PERMISSIONS_TAB = (By.ID, "user-permissions-tab")
    FINANCE_PERMISSIONS_TAB = (By.ID, "finance-permissions-tab")
    REPORT_PERMISSIONS_TAB = (By.ID, "report-permissions-tab")

    # 表单按钮
    ROLE_SAVE_BUTTON = (By.ID, "role-save-btn")
    ROLE_CANCEL_BUTTON = (By.ID, "role-cancel-btn")
    PERMISSION_SAVE_BUTTON = (By.ID, "permission-save-btn")
    PERMISSION_CANCEL_BUTTON = (By.ID, "permission-cancel-btn")

    # 确认对话框
    CONFIRM_DIALOG = (By.CLASS_NAME, "confirm-dialog")
    CONFIRM_YES_BUTTON = (By.ID, "confirm-yes")
    CONFIRM_NO_BUTTON = (By.ID, "confirm-no")

    # 消息提示
    SUCCESS_MESSAGE = (By.CLASS_NAME, "success-message")
    ERROR_MESSAGE = (By.CLASS_NAME, "error-message")
    WARNING_MESSAGE = (By.CLASS_NAME, "warning-message")

    # 用户分配元素
    ASSIGNED_USERS_LIST = (By.ID, "assigned-users-list")
    AVAILABLE_USERS_LIST = (By.ID, "available-users-list")
    ASSIGN_USER_BUTTON = (By.ID, "assign-user-btn")
    REMOVE_USER_BUTTON = (By.ID, "remove-user-btn")
    USER_SEARCH_INPUT = (By.ID, "user-search-input")

    def __init__(self, driver):
        """
        初始化权限管理页面

        Args:
            driver: WebDriver实例
        """
        super().__init__(driver)
        self.logger.info("初始化权限管理页面对象")

    def open_role_list_page(self, base_url: Optional[str] = None) -> None:
        """
        打开角色列表页面

        Args:
            base_url: 基础URL，如果为None则使用配置中的base_url
        """
        if base_url:
            full_url = f"{base_url}{self.url_role_list}"
        else:
            # 从配置获取base_url
            from utils.config_manager import get_config
            config = get_config()
            base_url = config.get('environment.base_url', 'http://test.ecommerce.com/admin')
            full_url = f"{base_url}{self.url_role_list}"

        self.logger.info(f"打开角色列表页面: {full_url}")
        self.open(full_url)
        self.wait_for_page_load()
        self.wait_for_role_table_loaded()

    def open_role_add_page(self, base_url: Optional[str] = None) -> None:
        """
        打开添加角色页面

        Args:
            base_url: 基础URL，如果为None则使用配置中的base_url
        """
        if base_url:
            full_url = f"{base_url}{self.url_role_add}"
        else:
            # 从配置获取base_url
            from utils.config_manager import get_config
            config = get_config()
            base_url = config.get('environment.base_url', 'http://test.ecommerce.com/admin')
            full_url = f"{base_url}{self.url_role_add}"

        self.logger.info(f"打开添加角色页面: {full_url}")
        self.open(full_url)
        self.wait_for_page_load()
        self.wait_for_role_form_loaded()

    def open_role_edit_page(self, role_id: int, base_url: Optional[str] = None) -> None:
        """
        打开编辑角色页面

        Args:
            role_id: 角色ID
            base_url: 基础URL，如果为None则使用配置中的base_url
        """
        if base_url:
            full_url = f"{base_url}{self.url_role_edit}/{role_id}"
        else:
            # 从配置获取base_url
            from utils.config_manager import get_config
            config = get_config()
            base_url = config.get('environment.base_url', 'http://test.ecommerce.com/admin')
            full_url = f"{base_url}{self.url_role_edit}/{role_id}"

        self.logger.info(f"打开编辑角色页面: {full_url}")
        self.open(full_url)
        self.wait_for_page_load()
        self.wait_for_role_form_loaded()

    def open_permission_manage_page(self, role_id: Optional[int] = None, base_url: Optional[str] = None) -> None:
        """
        打开权限管理页面

        Args:
            role_id: 角色ID，如果为None则打开通用权限管理页面
            base_url: 基础URL，如果为None则使用配置中的base_url
        """
        if role_id:
            if base_url:
                full_url = f"{base_url}{self.url_permission_manage}/{role_id}"
            else:
                # 从配置获取base_url
                from utils.config_manager import get_config
                config = get_config()
                base_url = config.get('environment.base_url', 'http://test.ecommerce.com/admin')
                full_url = f"{base_url}{self.url_permission_manage}/{role_id}"
        else:
            if base_url:
                full_url = f"{base_url}{self.url_permission_manage}"
            else:
                # 从配置获取base_url
                from utils.config_manager import get_config
                config = get_config()
                base_url = config.get('environment.base_url', 'http://test.ecommerce.com/admin')
                full_url = f"{base_url}{self.url_permission_manage}"

        self.logger.info(f"打开权限管理页面: {full_url}")
        self.open(full_url)
        self.wait_for_page_load()
        self.wait_for_permission_tree_loaded()

    def wait_for_role_table_loaded(self, timeout: int = 30) -> None:
        """
        等待角色表格加载完成

        Args:
            timeout: 等待超时时间
        """
        self.logger.info("等待角色表格加载完成")
        self.find_element(self.ROLE_TABLE, timeout=timeout)

    def wait_for_role_form_loaded(self, timeout: int = 30) -> None:
        """
        等待角色表单加载完成

        Args:
            timeout: 等待超时时间
        """
        self.logger.info("等待角色表单加载完成")
        self.find_element(self.ROLE_NAME_INPUT, timeout=timeout)

    def wait_for_permission_tree_loaded(self, timeout: int = 30) -> None:
        """
        等待权限树加载完成

        Args:
            timeout: 等待超时时间
        """
        self.logger.info("等待权限树加载完成")
        self.find_element(self.PERMISSION_TREE, timeout=timeout)

    def search_role(self, keyword: str) -> None:
        """
        搜索角色

        Args:
            keyword: 搜索关键词
        """
        self.logger.info(f"搜索角色: {keyword}")

        # 输入搜索关键词
        self.type(self.ROLE_SEARCH_INPUT, keyword)

        # 点击搜索按钮
        self.click(self.ROLE_SEARCH_BUTTON)

        # 等待搜索结果
        time.sleep(1)
        self.wait_for_role_table_loaded()

    def get_role_rows(self) -> List[Dict[str, Any]]:
        """
        获取角色行数据

        Returns:
            List[Dict[str, Any]]: 角色行数据列表
        """
        rows = self.find_elements(self.ROLE_TABLE_ROWS, timeout=5)
        roles = []

        for i, row in enumerate(rows):
            try:
                # 获取行内单元格数据
                cells = row.find_elements(By.TAG_NAME, "td")

                role_data = {
                    "row_index": i,
                    "role_id": cells[0].text if len(cells) > 0 else "",
                    "role_name": cells[1].text if len(cells) > 1 else "",
                    "role_code": cells[2].text if len(cells) > 2 else "",
                    "user_count": cells[3].text if len(cells) > 3 else "",
                    "permission_count": cells[4].text if len(cells) > 4 else "",
                    "description": cells[5].text if len(cells) > 5 else "",
                    "status": cells[6].text if len(cells) > 6 else "",
                }
                roles.append(role_data)

            except Exception as e:
                self.logger.warning(f"获取第 {i} 行角色数据失败: {e}")

        self.logger.debug(f"获取到 {len(roles)} 条角色数据")
        return roles

    def create_role(self, role_data: Dict[str, Any]) -> bool:
        """
        创建新角色

        Args:
            role_data: 角色数据字典，包含name, code, description等字段

        Returns:
            bool: 如果创建成功则返回True
        """
        self.logger.info(f"创建新角色: {role_data.get('name', '未知角色')}")

        # 打开添加角色页面
        self.open_role_add_page()

        # 填写角色信息
        if "name" in role_data:
            self.type(self.ROLE_NAME_INPUT, role_data["name"])

        if "code" in role_data:
            self.type(self.ROLE_CODE_INPUT, role_data["code"])

        if "description" in role_data:
            self.type(self.ROLE_DESCRIPTION_TEXTAREA, role_data["description"])

        if "status" in role_data:
            status_select = self.find_element(self.ROLE_STATUS_SELECT)
            select = Select(status_select)
            select.select_by_visible_text(role_data["status"])

        # 点击保存按钮
        self.click(self.ROLE_SAVE_BUTTON)

        # 等待操作完成
        time.sleep(2)

        # 检查是否成功
        return self.is_success_message_displayed()

    def edit_role(self, role_id: int, updates: Dict[str, Any]) -> bool:
        """
        编辑角色信息

        Args:
            role_id: 角色ID
            updates: 要更新的字段字典

        Returns:
            bool: 如果编辑成功则返回True
        """
        self.logger.info(f"编辑角色信息: 角色ID={role_id}, 更新字段={updates.keys()}")

        # 打开编辑角色页面
        self.open_role_edit_page(role_id)

        # 更新角色信息
        if "name" in updates:
            self.type(self.ROLE_NAME_INPUT, updates["name"])

        if "code" in updates:
            self.type(self.ROLE_CODE_INPUT, updates["code"])

        if "description" in updates:
            self.type(self.ROLE_DESCRIPTION_TEXTAREA, updates["description"])

        if "status" in updates:
            status_select = self.find_element(self.ROLE_STATUS_SELECT)
            select = Select(status_select)
            select.select_by_visible_text(updates["status"])

        # 点击保存按钮
        self.click(self.ROLE_SAVE_BUTTON)

        # 等待操作完成
        time.sleep(2)

        # 检查是否成功
        return self.is_success_message_displayed()

    def delete_role(self, role_id: int) -> bool:
        """
        删除角色

        Args:
            role_id: 角色ID

        Returns:
            bool: 如果删除成功则返回True
        """
        self.logger.info(f"删除角色: 角色ID={role_id}")

        # 打开角色列表页面
        self.open_role_list_page()

        # 找到角色并点击删除按钮
        rows = self.get_role_rows()
        for i, role in enumerate(rows):
            if role.get("role_id") == str(role_id):
                # 找到对应的行，点击删除按钮
                rows_elements = self.find_elements(self.ROLE_TABLE_ROWS, timeout=5)
                if i < len(rows_elements):
                    delete_button = rows_elements[i].find_element(By.CSS_SELECTOR, ".role-delete-btn")
                    delete_button.click()

                    # 处理确认对话框
                    if self.is_element_present(self.CONFIRM_DIALOG, timeout=5):
                        self.click(self.CONFIRM_YES_BUTTON)

                    # 等待操作完成
                    time.sleep(2)

                    # 检查是否成功
                    return self.is_success_message_displayed()

        self.logger.warning(f"未找到角色: ID={role_id}")
        return False

    def assign_permissions_to_role(self, role_id: int, permissions: List[str]) -> bool:
        """
        为角色分配权限

        Args:
            role_id: 角色ID
            permissions: 权限列表

        Returns:
            bool: 如果分配成功则返回True
        """
        self.logger.info(f"为角色分配权限: 角色ID={role_id}, 权限数量={len(permissions)}")

        # 打开权限管理页面
        self.open_permission_manage_page(role_id)

        # 先取消选择所有权限
        self.click(self.COLLAPSE_ALL_PERMISSIONS)
        time.sleep(1)

        # 选择指定的权限
        for permission in permissions:
            # 根据权限名称查找对应的复选框
            # 假设权限复选框的ID格式为 "permission-{permission}"
            permission_checkbox = (By.ID, f"permission-{permission}")
            if self.is_element_present(permission_checkbox, timeout=2):
                # 确保权限可见
                self.scroll_to_element(permission_checkbox)
                self.click(permission_checkbox)
            else:
                self.logger.warning(f"未找到权限复选框: {permission}")

        # 点击保存按钮
        self.click(self.PERMISSION_SAVE_BUTTON)

        # 等待操作完成
        time.sleep(2)

        # 检查是否成功
        return self.is_success_message_displayed()

    def get_role_permissions(self, role_id: int) -> List[str]:
        """
        获取角色的权限列表

        Args:
            role_id: 角色ID

        Returns:
            List[str]: 权限列表
        """
        self.logger.info(f"获取角色权限列表: 角色ID={role_id}")

        # 打开权限管理页面
        self.open_permission_manage_page(role_id)

        # 等待权限树加载
        self.wait_for_permission_tree_loaded()

        # 获取所有选中的权限
        permissions = []
        try:
            # 展开所有权限
            self.click(self.EXPAND_ALL_PERMISSIONS)
            time.sleep(1)

            # 查找所有选中的复选框
            checkboxes = self.find_elements(self.PERMISSION_CHECKBOX, timeout=5)
            for checkbox in checkboxes:
                if checkbox.is_selected():
                    # 获取权限ID或名称
                    permission_id = checkbox.get_attribute("id")
                    if permission_id:
                        permissions.append(permission_id.replace("permission-", ""))

        except Exception as e:
            self.logger.error(f"获取角色权限失败: {e}")

        return permissions

    def assign_users_to_role(self, role_id: int, usernames: List[str]) -> bool:
        """
        为用户分配角色

        Args:
            role_id: 角色ID
            usernames: 用户名列表

        Returns:
            bool: 如果分配成功则返回True
        """
        self.logger.info(f"为用户分配角色: 角色ID={role_id}, 用户数量={len(usernames)}")

        # 打开角色编辑页面
        self.open_role_edit_page(role_id)

        # 查找用户分配相关元素（假设有用户分配功能）
        # 这里简化处理，实际可能需要更复杂的逻辑
        for username in usernames:
            # 搜索用户
            self.type(self.USER_SEARCH_INPUT, username)
            time.sleep(1)

            # 选择用户（假设有选择框）
            user_checkbox = (By.CSS_SELECTOR, f"input[data-username='{username}']")
            if self.is_element_present(user_checkbox, timeout=2):
                self.click(user_checkbox)

        # 点击分配按钮
        self.click(self.ASSIGN_USER_BUTTON)

        # 等待操作完成
        time.sleep(2)

        # 点击保存按钮
        self.click(self.ROLE_SAVE_BUTTON)

        # 等待操作完成
        time.sleep(2)

        # 检查是否成功
        return self.is_success_message_displayed()

    def switch_permission_tab(self, tab_name: str) -> None:
        """
        切换到指定权限标签页

        Args:
            tab_name: 标签页名称，如 "system", "product", "order", "user", "finance", "report"
        """
        self.logger.info(f"切换到权限标签页: {tab_name}")

        tab_locators = {
            "system": self.SYSTEM_PERMISSIONS_TAB,
            "product": self.PRODUCT_PERMISSIONS_TAB,
            "order": self.ORDER_PERMISSIONS_TAB,
            "user": self.USER_PERMISSIONS_TAB,
            "finance": self.FINANCE_PERMISSIONS_TAB,
            "report": self.REPORT_PERMISSIONS_TAB
        }

        if tab_name in tab_locators:
            self.click(tab_locators[tab_name])
            time.sleep(1)
        else:
            self.logger.warning(f"未知的权限标签页: {tab_name}")

    def verify_role_exists(self, role_name: str) -> bool:
        """
        验证角色是否存在

        Args:
            role_name: 角色名称

        Returns:
            bool: 如果角色存在则返回True
        """
        rows = self.get_role_rows()
        for role in rows:
            if role.get("role_name") == role_name:
                return True
        return False

    def verify_permission_assigned(self, role_id: int, permission: str) -> bool:
        """
        验证权限是否已分配给角色

        Args:
            role_id: 角色ID
            permission: 权限名称

        Returns:
            bool: 如果权限已分配则返回True
        """
        permissions = self.get_role_permissions(role_id)
        return permission in permissions

    def is_success_message_displayed(self, timeout: int = 5) -> bool:
        """
        检查是否显示成功消息

        Args:
            timeout: 等待超时时间

        Returns:
            bool: 如果成功消息显示则返回True
        """
        return self.is_element_present(self.SUCCESS_MESSAGE, timeout)

    def get_success_message(self) -> str:
        """
        获取成功消息文本

        Returns:
            str: 成功消息文本，如果没有则返回空字符串
        """
        try:
            return self.get_text(self.SUCCESS_MESSAGE, timeout=2)
        except Exception:
            return ""

    def get_error_message(self) -> str:
        """
        获取错误消息文本

        Returns:
            str: 错误消息文本，如果没有则返回空字符串
        """
        try:
            return self.get_text(self.ERROR_MESSAGE, timeout=2)
        except Exception:
            return ""

    def click_add_role_button(self) -> None:
        """点击新增角色按钮"""
        self.logger.info("点击新增角色按钮")
        self.click(self.ADD_ROLE_BUTTON)


# 快捷函数
def create_permission_page(driver):
    """
    创建权限管理页面对象的快捷函数

    Args:
        driver: WebDriver实例

    Returns:
        PermissionPage: 权限管理页面对象实例
    """
    return PermissionPage(driver)


if __name__ == "__main__":
    # 测试PermissionPage类
    print("测试PermissionPage类...")

    # 注意：实际测试需要真实的WebDriver实例
    # 这里只进行导入测试
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options

        # 创建headless浏览器
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(options=chrome_options)

        # 创建权限管理页面对象
        permission_page = PermissionPage(driver)
        print("PermissionPage类导入和实例化成功")

        # 测试页面元素常量
        print(f"角色搜索输入框定位器: {permission_page.ROLE_SEARCH_INPUT}")
        print(f"角色表格定位器: {permission_page.ROLE_TABLE}")
        print(f"权限树定位器: {permission_page.PERMISSION_TREE}")

        driver.quit()
        print("测试完成")

    except Exception as e:
        print(f"测试过程中出错: {e}")
        print("注意：此测试需要安装ChromeDriver")
