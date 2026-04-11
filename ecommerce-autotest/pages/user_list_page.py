#!/usr/bin/env python3
"""
用户列表页面对象
实现电商后台管理系统的用户列表功能页面操作
"""

import time
from typing import Optional, Tuple, List, Dict, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from pages.base_page import BasePage


class UserListPage(BasePage):
    """
    用户列表页面对象类
    封装用户列表页面的所有元素和操作
    """

    # 页面URL
    url = "/admin/users"

    # 页面元素定位器 - 根据config/testdata/user.yaml配置
    # 用户列表页面元素
    SEARCH_INPUT = (By.ID, "search-input")
    SEARCH_BUTTON = (By.ID, "search-btn")
    ROLE_FILTER = (By.ID, "role-filter")
    STATUS_FILTER = (By.ID, "status-filter")
    USER_TABLE = (By.ID, "user-table")
    ADD_USER_BUTTON = (By.ID, "add-user-btn")
    BATCH_OPERATION_BUTTON = (By.ID, "batch-operation-btn")
    EXPORT_BUTTON = (By.ID, "export-btn")

    # 用户表格相关元素
    TABLE_ROWS = (By.CSS_SELECTOR, "#user-table tbody tr")
    TABLE_HEADERS = (By.CSS_SELECTOR, "#user-table thead th")
    SELECT_ALL_CHECKBOX = (By.ID, "select-all")
    USER_CHECKBOX = (By.CSS_SELECTOR, ".user-checkbox")
    EDIT_BUTTON = (By.CSS_SELECTOR, ".edit-btn")
    DELETE_BUTTON = (By.CSS_SELECTOR, ".delete-btn")
    VIEW_BUTTON = (By.CSS_SELECTOR, ".view-btn")
    DISABLE_BUTTON = (By.CSS_SELECTOR, ".disable-btn")
    ENABLE_BUTTON = (By.CSS_SELECTOR, ".enable-btn")
    RESET_PASSWORD_BUTTON = (By.CSS_SELECTOR, ".reset-password-btn")

    # 分页元素
    PAGINATION = (By.CLASS_NAME, "pagination")
    PAGE_NEXT = (By.CLASS_NAME, "page-next")
    PAGE_PREV = (By.CLASS_NAME, "page-prev")
    PAGE_NUMBER = (By.CLASS_NAME, "page-number")
    CURRENT_PAGE = (By.CLASS_NAME, "current-page")

    # 排序元素
    SORT_BY_USERNAME = (By.ID, "sort-by-username")
    SORT_BY_REAL_NAME = (By.ID, "sort-by-real-name")
    SORT_BY_CREATE_TIME = (By.ID, "sort-by-create-time")
    SORT_BY_LAST_LOGIN = (By.ID, "sort-by-last-login")

    # 筛选器元素
    FILTER_APPLY_BUTTON = (By.ID, "filter-apply")
    FILTER_RESET_BUTTON = (By.ID, "filter-reset")

    # 时间范围筛选元素
    CREATE_TIME_START = (By.ID, "create-time-start")
    CREATE_TIME_END = (By.ID, "create-time-end")

    def __init__(self, driver):
        """
        初始化用户列表页面

        Args:
            driver: WebDriver实例
        """
        super().__init__(driver)
        self.logger.info("初始化用户列表页面对象")

    def open_user_list_page(self, base_url: Optional[str] = None) -> None:
        """
        打开用户列表页面

        Args:
            base_url: 基础URL，如果为None则使用配置中的base_url
        """
        if base_url:
            full_url = f"{base_url}{self.url}"
        else:
            # 从配置获取base_url
            from utils.config_manager import get_config
            config = get_config()
            base_url = config.get('environment.base_url', 'http://test.ecommerce.com/admin')
            full_url = f"{base_url}{self.url}"

        self.logger.info(f"打开用户列表页面: {full_url}")
        self.open(full_url)
        self.wait_for_page_load()
        self.wait_for_user_table_loaded()

    def wait_for_user_table_loaded(self, timeout: int = 30) -> None:
        """
        等待用户表格加载完成

        Args:
            timeout: 等待超时时间
        """
        self.logger.info("等待用户表格加载完成")
        self.find_element(self.USER_TABLE, timeout=timeout)
        # 等待至少一行数据加载（如果有数据的话）
        try:
            rows = self.find_elements(self.TABLE_ROWS, timeout=5)
            if rows:
                self.logger.info(f"用户表格加载完成，找到 {len(rows)} 行数据")
        except Exception:
            self.logger.info("用户表格已加载，可能没有数据")

    def search_user(self, keyword: str, search_type: str = "username") -> None:
        """
        搜索用户

        Args:
            keyword: 搜索关键词
            search_type: 搜索类型，如 "username", "phone", "email", "real_name"
        """
        self.logger.info(f"搜索用户 - 类型: {search_type}, 关键词: {keyword}")

        # 选择搜索类型（如果页面支持）
        if search_type != "username":
            # 假设有搜索类型下拉框
            search_type_select = (By.ID, "search-type-select")
            if self.is_element_present(search_type_select, timeout=2):
                select = Select(self.find_element(search_type_select))
                select.select_by_value(search_type)

        # 输入搜索关键词
        self.type(self.SEARCH_INPUT, keyword)

        # 点击搜索按钮
        self.click(self.SEARCH_BUTTON)

        # 等待搜索结果
        time.sleep(1)
        self.wait_for_user_table_loaded()

    def filter_by_role(self, role: str) -> None:
        """
        按角色筛选用户

        Args:
            role: 角色名称
        """
        self.logger.info(f"按角色筛选用户: {role}")

        # 查找角色筛选器
        role_filter = self.find_element(self.ROLE_FILTER)

        # 使用Select类处理下拉选择
        select = Select(role_filter)
        select.select_by_visible_text(role)

        # 应用筛选
        self.click(self.FILTER_APPLY_BUTTON)

        # 等待筛选结果
        time.sleep(1)
        self.wait_for_user_table_loaded()

    def filter_by_status(self, status: str) -> None:
        """
        按状态筛选用户

        Args:
            status: 状态，如 "active", "disabled", "locked", "pending_activation"
        """
        self.logger.info(f"按状态筛选用户: {status}")

        # 查找状态筛选器
        status_filter = self.find_element(self.STATUS_FILTER)

        # 使用Select类处理下拉选择
        select = Select(status_filter)
        select.select_by_visible_text(status)

        # 应用筛选
        self.click(self.FILTER_APPLY_BUTTON)

        # 等待筛选结果
        time.sleep(1)
        self.wait_for_user_table_loaded()

    def filter_by_create_time_range(self, start_date: str, end_date: str) -> None:
        """
        按注册时间范围筛选用户

        Args:
            start_date: 开始日期，格式如 "2024-01-01"
            end_date: 结束日期，格式如 "2024-12-31"
        """
        self.logger.info(f"按注册时间范围筛选用户: {start_date} 至 {end_date}")

        # 输入开始日期
        self.type(self.CREATE_TIME_START, start_date)

        # 输入结束日期
        self.type(self.CREATE_TIME_END, end_date)

        # 应用筛选
        self.click(self.FILTER_APPLY_BUTTON)

        # 等待筛选结果
        time.sleep(1)
        self.wait_for_user_table_loaded()

    def sort_by(self, sort_option: str) -> None:
        """
        排序用户

        Args:
            sort_option: 排序选项，如 "username_asc", "username_desc", "create_time_desc", "create_time_asc"
        """
        self.logger.info(f"排序用户: {sort_option}")

        # 根据排序选项选择对应的排序元素
        sort_locators = {
            "username_asc": self.SORT_BY_USERNAME,
            "username_desc": self.SORT_BY_USERNAME,  # 可能需要点击两次
            "real_name_asc": self.SORT_BY_REAL_NAME,
            "real_name_desc": self.SORT_BY_REAL_NAME,
            "create_time_asc": self.SORT_BY_CREATE_TIME,
            "create_time_desc": self.SORT_BY_CREATE_TIME,
            "last_login_asc": self.SORT_BY_LAST_LOGIN,
            "last_login_desc": self.SORT_BY_LAST_LOGIN,
        }

        if sort_option in sort_locators:
            sort_locator = sort_locators[sort_option]
            self.click(sort_locator)

            # 等待排序完成
            time.sleep(1)
            self.wait_for_user_table_loaded()
        else:
            self.logger.warning(f"不支持的排序选项: {sort_option}")

    def get_user_count(self) -> int:
        """
        获取用户数量

        Returns:
            int: 用户数量
        """
        rows = self.find_elements(self.TABLE_ROWS, timeout=5)
        count = len(rows)
        self.logger.debug(f"用户数量: {count}")
        return count

    def get_user_rows(self) -> List[Dict[str, Any]]:
        """
        获取用户行数据

        Returns:
            List[Dict[str, Any]]: 用户行数据列表
        """
        rows = self.find_elements(self.TABLE_ROWS, timeout=5)
        users = []

        for i, row in enumerate(rows):
            try:
                # 获取行内单元格数据
                cells = row.find_elements(By.TAG_NAME, "td")

                user_data = {
                    "row_index": i,
                    "user_id": cells[0].text if len(cells) > 0 else "",
                    "username": cells[1].text if len(cells) > 1 else "",
                    "real_name": cells[2].text if len(cells) > 2 else "",
                    "email": cells[3].text if len(cells) > 3 else "",
                    "phone": cells[4].text if len(cells) > 4 else "",
                    "role": cells[5].text if len(cells) > 5 else "",
                    "status": cells[6].text if len(cells) > 6 else "",
                    "create_time": cells[7].text if len(cells) > 7 else "",
                    "last_login": cells[8].text if len(cells) > 8 else "",
                }
                users.append(user_data)

            except Exception as e:
                self.logger.warning(f"获取第 {i} 行用户数据失败: {e}")

        self.logger.debug(f"获取到 {len(users)} 条用户数据")
        return users

    def select_user_by_index(self, index: int) -> None:
        """
        通过索引选择用户

        Args:
            index: 用户行索引（从0开始）
        """
        self.logger.info(f"选择第 {index} 个用户")

        rows = self.find_elements(self.TABLE_ROWS, timeout=5)
        if index < len(rows):
            checkbox = rows[index].find_element(By.CSS_SELECTOR, ".user-checkbox")
            checkbox.click()
        else:
            raise IndexError(f"用户索引超出范围: {index}，总共 {len(rows)} 个用户")

    def select_user_by_username(self, username: str) -> bool:
        """
        通过用户名选择用户

        Args:
            username: 用户名

        Returns:
            bool: 如果找到并选择了用户则返回True
        """
        self.logger.info(f"通过用户名选择用户: {username}")

        rows = self.get_user_rows()
        for i, user in enumerate(rows):
            if user.get("username") == username:
                self.select_user_by_index(i)
                return True

        self.logger.warning(f"未找到用户: {username}")
        return False

    def click_add_user_button(self) -> None:
        """点击新增用户按钮"""
        self.logger.info("点击新增用户按钮")
        self.click(self.ADD_USER_BUTTON)

    def click_edit_user_button(self, username: str) -> bool:
        """
        点击编辑用户按钮

        Args:
            username: 用户名

        Returns:
            bool: 如果找到并点击了编辑按钮则返回True
        """
        self.logger.info(f"点击编辑用户按钮: {username}")

        rows = self.get_user_rows()
        for i, user in enumerate(rows):
            if user.get("username") == username:
                # 找到对应的行，点击编辑按钮
                rows_elements = self.find_elements(self.TABLE_ROWS, timeout=5)
                if i < len(rows_elements):
                    edit_button = rows_elements[i].find_element(By.CSS_SELECTOR, ".edit-btn")
                    edit_button.click()
                    return True

        self.logger.warning(f"未找到用户或编辑按钮: {username}")
        return False

    def click_view_user_button(self, username: str) -> bool:
        """
        点击查看用户按钮

        Args:
            username: 用户名

        Returns:
            bool: 如果找到并点击了查看按钮则返回True
        """
        self.logger.info(f"点击查看用户按钮: {username}")

        rows = self.get_user_rows()
        for i, user in enumerate(rows):
            if user.get("username") == username:
                # 找到对应的行，点击查看按钮
                rows_elements = self.find_elements(self.TABLE_ROWS, timeout=5)
                if i < len(rows_elements):
                    view_button = rows_elements[i].find_element(By.CSS_SELECTOR, ".view-btn")
                    view_button.click()
                    return True

        self.logger.warning(f"未找到用户或查看按钮: {username}")
        return False

    def click_disable_user_button(self, username: str) -> bool:
        """
        点击禁用用户按钮

        Args:
            username: 用户名

        Returns:
            bool: 如果找到并点击了禁用按钮则返回True
        """
        self.logger.info(f"点击禁用用户按钮: {username}")

        rows = self.get_user_rows()
        for i, user in enumerate(rows):
            if user.get("username") == username:
                # 找到对应的行，点击禁用按钮
                rows_elements = self.find_elements(self.TABLE_ROWS, timeout=5)
                if i < len(rows_elements):
                    disable_button = rows_elements[i].find_element(By.CSS_SELECTOR, ".disable-btn")
                    disable_button.click()
                    return True

        self.logger.warning(f"未找到用户或禁用按钮: {username}")
        return False

    def click_enable_user_button(self, username: str) -> bool:
        """
        点击启用用户按钮

        Args:
            username: 用户名

        Returns:
            bool: 如果找到并点击了启用按钮则返回True
        """
        self.logger.info(f"点击启用用户按钮: {username}")

        rows = self.get_user_rows()
        for i, user in enumerate(rows):
            if user.get("username") == username and user.get("status") == "禁用":
                # 找到对应的行，点击启用按钮
                rows_elements = self.find_elements(self.TABLE_ROWS, timeout=5)
                if i < len(rows_elements):
                    enable_button = rows_elements[i].find_element(By.CSS_SELECTOR, ".enable-btn")
                    enable_button.click()
                    return True

        self.logger.warning(f"未找到用户或启用按钮: {username}")
        return False

    def click_reset_password_button(self, username: str) -> bool:
        """
        点击重置密码按钮

        Args:
            username: 用户名

        Returns:
            bool: 如果找到并点击了重置密码按钮则返回True
        """
        self.logger.info(f"点击重置密码按钮: {username}")

        rows = self.get_user_rows()
        for i, user in enumerate(rows):
            if user.get("username") == username:
                # 找到对应的行，点击重置密码按钮
                rows_elements = self.find_elements(self.TABLE_ROWS, timeout=5)
                if i < len(rows_elements):
                    reset_button = rows_elements[i].find_element(By.CSS_SELECTOR, ".reset-password-btn")
                    reset_button.click()
                    return True

        self.logger.warning(f"未找到用户或重置密码按钮: {username}")
        return False

    def get_user_status(self, username: str) -> Optional[str]:
        """
        获取用户状态

        Args:
            username: 用户名

        Returns:
            Optional[str]: 用户状态，如果未找到则返回None
        """
        rows = self.get_user_rows()
        for user in rows:
            if user.get("username") == username:
                return user.get("status")
        return None

    def verify_user_exists(self, username: str) -> bool:
        """
        验证用户是否存在

        Args:
            username: 用户名

        Returns:
            bool: 如果用户存在则返回True
        """
        rows = self.get_user_rows()
        for user in rows:
            if user.get("username") == username:
                return True
        return False

    def verify_search_results(self, keyword: str, search_type: str = "username") -> bool:
        """
        验证搜索结果

        Args:
            keyword: 搜索关键词
            search_type: 搜索类型

        Returns:
            bool: 如果搜索结果包含关键词则返回True
        """
        rows = self.get_user_rows()
        if not rows:
            return False

        for user in rows:
            field_value = ""
            if search_type == "username":
                field_value = user.get("username", "")
            elif search_type == "real_name":
                field_value = user.get("real_name", "")
            elif search_type == "email":
                field_value = user.get("email", "")
            elif search_type == "phone":
                field_value = user.get("phone", "")

            if keyword.lower() in field_value.lower():
                return True

        return False

    def reset_filters(self) -> None:
        """重置所有筛选条件"""
        self.logger.info("重置所有筛选条件")
        self.click(self.FILTER_RESET_BUTTON)
        time.sleep(1)
        self.wait_for_user_table_loaded()

    def export_users(self, export_format: str = "excel") -> None:
        """
        导出用户数据

        Args:
            export_format: 导出格式，如 "excel", "csv", "pdf"
        """
        self.logger.info(f"导出用户数据 - 格式: {export_format}")

        # 点击导出按钮
        self.click(self.EXPORT_BUTTON)

        # 选择导出格式（如果页面支持）
        format_select = (By.ID, "export-format-select")
        if self.is_element_present(format_select, timeout=2):
            select = Select(self.find_element(format_select))
            select.select_by_value(export_format)

            # 确认导出
            confirm_button = (By.ID, "export-confirm")
            self.click(confirm_button)

        # 等待导出完成
        time.sleep(2)


# 快捷函数
def create_user_list_page(driver):
    """
    创建用户列表页面对象的快捷函数

    Args:
        driver: WebDriver实例

    Returns:
        UserListPage: 用户列表页面对象实例
    """
    return UserListPage(driver)


if __name__ == "__main__":
    # 测试UserListPage类
    print("测试UserListPage类...")

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

        # 创建用户列表页面对象
        user_list_page = UserListPage(driver)
        print("UserListPage类导入和实例化成功")

        # 测试页面元素常量
        print(f"搜索输入框定位器: {user_list_page.SEARCH_INPUT}")
        print(f"角色筛选器定位器: {user_list_page.ROLE_FILTER}")
        print(f"用户表格定位器: {user_list_page.USER_TABLE}")

        driver.quit()
        print("测试完成")

    except Exception as e:
        print(f"测试过程中出错: {e}")
        print("注意：此测试需要安装ChromeDriver")
