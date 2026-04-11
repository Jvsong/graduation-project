#!/usr/bin/env python3
"""
用户操作页面对象
实现电商后台管理系统的用户添加、编辑、权限分配等操作功能
"""

import time
from typing import Optional, Tuple, List, Dict, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from pages.base_page import BasePage


class UserOperationPage(BasePage):
    """
    用户操作页面对象类
    封装用户添加、编辑、权限分配等操作的所有元素和操作
    """

    # 页面URL
    url_add = "/user/add"
    url_edit = "/user/edit"
    url_detail = "/user/detail"

    # 用户表单元素 - 根据config/testdata/user.yaml配置
    USERNAME_INPUT = (By.ID, "username")
    PASSWORD_INPUT = (By.ID, "password")
    CONFIRM_PASSWORD_INPUT = (By.ID, "confirm-password")
    EMAIL_INPUT = (By.ID, "email")
    PHONE_INPUT = (By.ID, "phone")
    REAL_NAME_INPUT = (By.ID, "real-name")
    ROLE_SELECT = (By.ID, "role")
    STATUS_SELECT = (By.ID, "status")
    DESCRIPTION_TEXTAREA = (By.ID, "description")

    # 用户详细信息元素
    USER_ID_DISPLAY = (By.ID, "user-id")
    CREATE_TIME_DISPLAY = (By.ID, "create-time")
    LAST_LOGIN_DISPLAY = (By.ID, "last-login")
    LOGIN_COUNT_DISPLAY = (By.ID, "login-count")

    # 用户权限相关元素
    PERMISSION_GROUPS = (By.CLASS_NAME, "permission-group")
    PERMISSION_CHECKBOX = (By.CLASS_NAME, "permission-checkbox")
    SELECT_ALL_PERMISSIONS = (By.ID, "select-all-permissions")
    RESET_PERMISSIONS = (By.ID, "reset-permissions")

    # 用户状态操作元素
    DISABLE_BUTTON = (By.ID, "disable-btn")
    ENABLE_BUTTON = (By.ID, "enable-btn")
    LOCK_BUTTON = (By.ID, "lock-btn")
    UNLOCK_BUTTON = (By.ID, "unlock-btn")
    RESET_PASSWORD_BUTTON = (By.ID, "reset-password-btn")
    SEND_ACTIVATION_BUTTON = (By.ID, "send-activation-btn")

    # 表单按钮
    SAVE_BUTTON = (By.ID, "save-btn")
    CANCEL_BUTTON = (By.ID, "cancel-btn")
    SUBMIT_BUTTON = (By.ID, "submit-btn")
    RESET_BUTTON = (By.ID, "reset-btn")
    DELETE_BUTTON = (By.ID, "delete-btn")
    BACK_BUTTON = (By.ID, "back-btn")

    # 验证消息
    SUCCESS_MESSAGE = (By.CLASS_NAME, "success-message")
    ERROR_MESSAGE = (By.CLASS_NAME, "error-message")
    VALIDATION_ERROR = (By.CLASS_NAME, "validation-error")
    CONFIRM_DIALOG = (By.CLASS_NAME, "confirm-dialog")
    CONFIRM_YES_BUTTON = (By.ID, "confirm-yes")
    CONFIRM_NO_BUTTON = (By.ID, "confirm-no")

    # 标签页元素
    BASIC_INFO_TAB = (By.ID, "basic-info-tab")
    PERMISSION_TAB = (By.ID, "permission-tab")
    LOGIN_HISTORY_TAB = (By.ID, "login-history-tab")
    OPERATION_LOG_TAB = (By.ID, "operation-log-tab")

    def __init__(self, driver):
        """
        初始化用户操作页面

        Args:
            driver: WebDriver实例
        """
        super().__init__(driver)
        self.logger.info("初始化用户操作页面对象")

    def open_add_user_page(self, base_url: Optional[str] = None) -> None:
        """
        打开添加用户页面

        Args:
            base_url: 基础URL，如果为None则使用配置中的base_url
        """
        if base_url:
            full_url = f"{base_url}{self.url_add}"
        else:
            # 从配置获取base_url
            from utils.config_manager import get_config
            config = get_config()
            base_url = config.get('environment.base_url', 'http://test.ecommerce.com/admin')
            full_url = f"{base_url}{self.url_add}"

        self.logger.info(f"打开添加用户页面: {full_url}")
        self.open(full_url)
        self.wait_for_page_load()
        self.wait_for_form_loaded()

    def open_edit_user_page(self, user_id: int, base_url: Optional[str] = None) -> None:
        """
        打开编辑用户页面

        Args:
            user_id: 用户ID
            base_url: 基础URL，如果为None则使用配置中的base_url
        """
        if base_url:
            full_url = f"{base_url}{self.url_edit}/{user_id}"
        else:
            # 从配置获取base_url
            from utils.config_manager import get_config
            config = get_config()
            base_url = config.get('environment.base_url', 'http://test.ecommerce.com/admin')
            full_url = f"{base_url}{self.url_edit}/{user_id}"

        self.logger.info(f"打开编辑用户页面: {full_url}")
        self.open(full_url)
        self.wait_for_page_load()
        self.wait_for_form_loaded()

    def open_user_detail_page(self, user_id: int, base_url: Optional[str] = None) -> None:
        """
        打开用户详情页面

        Args:
            user_id: 用户ID
            base_url: 基础URL，如果为None则使用配置中的base_url
        """
        if base_url:
            full_url = f"{base_url}{self.url_detail}/{user_id}"
        else:
            # 从配置获取base_url
            from utils.config_manager import get_config
            config = get_config()
            base_url = config.get('environment.base_url', 'http://test.ecommerce.com/admin')
            full_url = f"{base_url}{self.url_detail}/{user_id}"

        self.logger.info(f"打开用户详情页面: {full_url}")
        self.open(full_url)
        self.wait_for_page_load()
        self.wait_for_form_loaded()

    def wait_for_form_loaded(self, timeout: int = 30) -> None:
        """
        等待表单加载完成

        Args:
            timeout: 等待超时时间
        """
        self.logger.info("等待用户表单加载完成")
        # 检查用户名输入框是否存在
        self.find_element(self.USERNAME_INPUT, timeout=timeout)

    def fill_basic_info(self, user_data: Dict[str, Any]) -> None:
        """
        填写用户基本信息

        Args:
            user_data: 用户数据字典，包含username, password, email等字段
        """
        self.logger.info(f"填写用户基本信息: {user_data.get('username', '未知用户')}")

        # 填写用户名
        if "username" in user_data:
            self.type(self.USERNAME_INPUT, user_data["username"])

        # 填写密码（如果有）
        if "password" in user_data:
            self.type(self.PASSWORD_INPUT, user_data["password"])

        # 确认密码（如果有）
        if "confirm_password" in user_data:
            self.type(self.CONFIRM_PASSWORD_INPUT, user_data["confirm_password"])

        # 填写邮箱
        if "email" in user_data:
            self.type(self.EMAIL_INPUT, user_data["email"])

        # 填写手机号
        if "phone" in user_data:
            self.type(self.PHONE_INPUT, user_data["phone"])

        # 填写真实姓名
        if "real_name" in user_data:
            self.type(self.REAL_NAME_INPUT, user_data["real_name"])

        # 选择角色
        if "role" in user_data:
            role_select = self.find_element(self.ROLE_SELECT)
            select = Select(role_select)
            select.select_by_visible_text(user_data["role"])

        # 选择状态
        if "status" in user_data:
            status_select = self.find_element(self.STATUS_SELECT)
            select = Select(status_select)
            select.select_by_visible_text(user_data["status"])

        # 填写描述
        if "description" in user_data:
            self.type(self.DESCRIPTION_TEXTAREA, user_data["description"])

    def add_user(self, user_data: Dict[str, Any]) -> bool:
        """
        添加新用户

        Args:
            user_data: 用户数据字典

        Returns:
            bool: 如果添加成功则返回True
        """
        self.logger.info(f"添加新用户: {user_data.get('username', '未知用户')}")

        # 打开添加用户页面
        self.open_add_user_page()

        # 填写用户信息
        self.fill_basic_info(user_data)

        # 点击保存按钮
        self.click(self.SAVE_BUTTON)

        # 等待操作完成
        time.sleep(2)

        # 检查是否成功
        return self.is_success_message_displayed()

    def edit_user(self, user_id: int, updates: Dict[str, Any]) -> bool:
        """
        编辑用户信息

        Args:
            user_id: 用户ID
            updates: 要更新的字段字典

        Returns:
            bool: 如果编辑成功则返回True
        """
        self.logger.info(f"编辑用户信息: 用户ID={user_id}, 更新字段={updates.keys()}")

        # 打开编辑用户页面
        self.open_edit_user_page(user_id)

        # 填写更新信息
        self.fill_basic_info(updates)

        # 点击保存按钮
        self.click(self.SAVE_BUTTON)

        # 等待操作完成
        time.sleep(2)

        # 检查是否成功
        return self.is_success_message_displayed()

    def view_user_detail(self, user_id: int) -> Dict[str, Any]:
        """
        查看用户详情

        Args:
            user_id: 用户ID

        Returns:
            Dict[str, Any]: 用户详情信息
        """
        self.logger.info(f"查看用户详情: 用户ID={user_id}")

        # 打开用户详情页面
        self.open_user_detail_page(user_id)

        # 等待页面加载
        self.wait_for_form_loaded()

        # 获取用户信息
        user_info = {}

        try:
            user_info["user_id"] = self.get_text(self.USER_ID_DISPLAY)
            user_info["username"] = self.get_attribute(self.USERNAME_INPUT, "value")
            user_info["email"] = self.get_attribute(self.EMAIL_INPUT, "value")
            user_info["phone"] = self.get_attribute(self.PHONE_INPUT, "value")
            user_info["real_name"] = self.get_attribute(self.REAL_NAME_INPUT, "value")
            user_info["create_time"] = self.get_text(self.CREATE_TIME_DISPLAY)
            user_info["last_login"] = self.get_text(self.LAST_LOGIN_DISPLAY)
            user_info["login_count"] = self.get_text(self.LOGIN_COUNT_DISPLAY)

            # 获取角色和状态
            role_select = self.find_element(self.ROLE_SELECT)
            select = Select(role_select)
            user_info["role"] = select.first_selected_option.text

            status_select = self.find_element(self.STATUS_SELECT)
            select = Select(status_select)
            user_info["status"] = select.first_selected_option.text

        except Exception as e:
            self.logger.error(f"获取用户详情失败: {e}")

        return user_info

    def assign_role(self, user_id: int, role: str) -> bool:
        """
        分配用户角色

        Args:
            user_id: 用户ID
            role: 角色名称

        Returns:
            bool: 如果分配成功则返回True
        """
        self.logger.info(f"分配用户角色: 用户ID={user_id}, 角色={role}")

        # 打开编辑用户页面
        self.open_edit_user_page(user_id)

        # 选择角色
        role_select = self.find_element(self.ROLE_SELECT)
        select = Select(role_select)
        select.select_by_visible_text(role)

        # 点击保存按钮
        self.click(self.SAVE_BUTTON)

        # 等待操作完成
        time.sleep(2)

        # 检查是否成功
        return self.is_success_message_displayed()

    def set_user_status(self, user_id: int, status: str) -> bool:
        """
        设置用户状态

        Args:
            user_id: 用户ID
            status: 状态名称，如 "active", "disabled", "locked"

        Returns:
            bool: 如果设置成功则返回True
        """
        self.logger.info(f"设置用户状态: 用户ID={user_id}, 状态={status}")

        # 打开编辑用户页面
        self.open_edit_user_page(user_id)

        # 选择状态
        status_select = self.find_element(self.STATUS_SELECT)
        select = Select(status_select)
        select.select_by_visible_text(status)

        # 点击保存按钮
        self.click(self.SAVE_BUTTON)

        # 等待操作完成
        time.sleep(2)

        # 检查是否成功
        return self.is_success_message_displayed()

    def disable_user(self, user_id: int) -> bool:
        """
        禁用用户

        Args:
            user_id: 用户ID

        Returns:
            bool: 如果禁用成功则返回True
        """
        self.logger.info(f"禁用用户: 用户ID={user_id}")

        # 打开用户详情页面
        self.open_user_detail_page(user_id)

        # 点击禁用按钮
        self.click(self.DISABLE_BUTTON)

        # 处理确认对话框
        if self.is_element_present(self.CONFIRM_DIALOG, timeout=5):
            self.click(self.CONFIRM_YES_BUTTON)

        # 等待操作完成
        time.sleep(2)

        # 检查是否成功
        return self.is_success_message_displayed()

    def enable_user(self, user_id: int) -> bool:
        """
        启用用户

        Args:
            user_id: 用户ID

        Returns:
            bool: 如果启用成功则返回True
        """
        self.logger.info(f"启用用户: 用户ID={user_id}")

        # 打开用户详情页面
        self.open_user_detail_page(user_id)

        # 点击启用按钮
        self.click(self.ENABLE_BUTTON)

        # 处理确认对话框
        if self.is_element_present(self.CONFIRM_DIALOG, timeout=5):
            self.click(self.CONFIRM_YES_BUTTON)

        # 等待操作完成
        time.sleep(2)

        # 检查是否成功
        return self.is_success_message_displayed()

    def reset_password(self, user_id: int, new_password: str, confirm_password: str, notify_user: bool = False) -> bool:
        """
        重置用户密码

        Args:
            user_id: 用户ID
            new_password: 新密码
            confirm_password: 确认密码
            notify_user: 是否通知用户

        Returns:
            bool: 如果重置成功则返回True
        """
        self.logger.info(f"重置用户密码: 用户ID={user_id}")

        # 打开用户详情页面
        self.open_user_detail_page(user_id)

        # 点击重置密码按钮
        self.click(self.RESET_PASSWORD_BUTTON)

        # 等待密码重置表单出现
        time.sleep(1)

        # 填写新密码
        self.type(self.PASSWORD_INPUT, new_password)
        self.type(self.CONFIRM_PASSWORD_INPUT, confirm_password)

        # 处理通知选项（如果有）
        if notify_user:
            notify_checkbox = (By.ID, "notify-user")
            if self.is_element_present(notify_checkbox, timeout=2):
                self.click(notify_checkbox)

        # 提交表单
        submit_button = (By.ID, "reset-password-submit")
        self.click(submit_button)

        # 处理确认对话框
        if self.is_element_present(self.CONFIRM_DIALOG, timeout=5):
            self.click(self.CONFIRM_YES_BUTTON)

        # 等待操作完成
        time.sleep(2)

        # 检查是否成功
        return self.is_success_message_displayed()

    def delete_user(self, user_id: int) -> bool:
        """
        删除用户

        Args:
            user_id: 用户ID

        Returns:
            bool: 如果删除成功则返回True
        """
        self.logger.info(f"删除用户: 用户ID={user_id}")

        # 打开用户详情页面
        self.open_user_detail_page(user_id)

        # 点击删除按钮
        self.click(self.DELETE_BUTTON)

        # 处理确认对话框
        if self.is_element_present(self.CONFIRM_DIALOG, timeout=5):
            # 输入确认文本（如果有）
            confirm_input = (By.ID, "confirm-input")
            if self.is_element_present(confirm_input, timeout=2):
                self.type(confirm_input, "DELETE")

            self.click(self.CONFIRM_YES_BUTTON)

        # 等待操作完成
        time.sleep(2)

        # 检查是否成功（重定向到用户列表页面）
        current_url = self.get_current_url()
        return "user/list" in current_url

    def assign_permissions(self, user_id: int, permissions: List[str]) -> bool:
        """
        分配用户权限

        Args:
            user_id: 用户ID
            permissions: 权限列表

        Returns:
            bool: 如果分配成功则返回True
        """
        self.logger.info(f"分配用户权限: 用户ID={user_id}, 权限数量={len(permissions)}")

        # 打开编辑用户页面并切换到权限标签页
        self.open_edit_user_page(user_id)
        self.click(self.PERMISSION_TAB)
        time.sleep(1)

        # 先取消选择所有权限
        self.click(self.RESET_PERMISSIONS)

        # 选择指定的权限
        for permission in permissions:
            # 根据权限名称查找对应的复选框
            # 假设权限复选框的ID格式为 "permission-{permission}"
            permission_checkbox = (By.ID, f"permission-{permission}")
            if self.is_element_present(permission_checkbox, timeout=2):
                self.click(permission_checkbox)
            else:
                self.logger.warning(f"未找到权限复选框: {permission}")

        # 点击保存按钮
        self.click(self.SAVE_BUTTON)

        # 等待操作完成
        time.sleep(2)

        # 检查是否成功
        return self.is_success_message_displayed()

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

    def get_validation_errors(self) -> List[str]:
        """
        获取所有验证错误消息

        Returns:
            List[str]: 验证错误消息列表
        """
        errors = []
        try:
            error_elements = self.find_elements(self.VALIDATION_ERROR, timeout=2)
            for element in error_elements:
                errors.append(element.text)
        except Exception:
            pass
        return errors

    def clear_form(self) -> None:
        """清空表单"""
        self.logger.info("清空用户表单")

        # 清空输入框
        fields_to_clear = [
            self.USERNAME_INPUT,
            self.PASSWORD_INPUT,
            self.CONFIRM_PASSWORD_INPUT,
            self.EMAIL_INPUT,
            self.PHONE_INPUT,
            self.REAL_NAME_INPUT,
            self.DESCRIPTION_TEXTAREA
        ]

        for field in fields_to_clear:
            try:
                element = self.find_element(field, timeout=2)
                element.clear()
            except Exception:
                pass

        # 重置选择框到默认值
        try:
            role_select = self.find_element(self.ROLE_SELECT, timeout=2)
            select = Select(role_select)
            select.select_by_index(0)
        except Exception:
            pass

        try:
            status_select = self.find_element(self.STATUS_SELECT, timeout=2)
            select = Select(status_select)
            select.select_by_index(0)
        except Exception:
            pass

    def switch_to_tab(self, tab_name: str) -> None:
        """
        切换到指定标签页

        Args:
            tab_name: 标签页名称，如 "basic_info", "permission", "login_history", "operation_log"
        """
        self.logger.info(f"切换到标签页: {tab_name}")

        tab_locators = {
            "basic_info": self.BASIC_INFO_TAB,
            "permission": self.PERMISSION_TAB,
            "login_history": self.LOGIN_HISTORY_TAB,
            "operation_log": self.OPERATION_LOG_TAB
        }

        if tab_name in tab_locators:
            self.click(tab_locators[tab_name])
            time.sleep(1)
        else:
            self.logger.warning(f"未知的标签页: {tab_name}")


# 快捷函数
def create_user_operation_page(driver):
    """
    创建用户操作页面对象的快捷函数

    Args:
        driver: WebDriver实例

    Returns:
        UserOperationPage: 用户操作页面对象实例
    """
    return UserOperationPage(driver)


if __name__ == "__main__":
    # 测试UserOperationPage类
    print("测试UserOperationPage类...")

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

        # 创建用户操作页面对象
        user_operation_page = UserOperationPage(driver)
        print("UserOperationPage类导入和实例化成功")

        # 测试页面元素常量
        print(f"用户名输入框定位器: {user_operation_page.USERNAME_INPUT}")
        print(f"邮箱输入框定位器: {user_operation_page.EMAIL_INPUT}")
        print(f"角色选择框定位器: {user_operation_page.ROLE_SELECT}")

        driver.quit()
        print("测试完成")

    except Exception as e:
        print(f"测试过程中出错: {e}")
        print("注意：此测试需要安装ChromeDriver")