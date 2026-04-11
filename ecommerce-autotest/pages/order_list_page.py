#!/usr/bin/env python3
"""
订单列表页面对象
实现电商后台管理系统的订单列表功能页面操作
"""

import time
from typing import Optional, Tuple, List, Dict, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from pages.base_page import BasePage


class OrderListPage(BasePage):
    """
    订单列表页面对象类
    封装订单列表页面的所有元素和操作
    """

    # 页面URL
    url = "/admin/orders"

    # 页面元素定位器 - 根据config/testdata/order.yaml配置
    # 订单列表页面元素
    SEARCH_INPUT = (By.ID, "search-input")
    SEARCH_BUTTON = (By.ID, "search-btn")
    STATUS_FILTER = (By.ID, "status-filter")
    TIME_FILTER = (By.ID, "time-filter")
    USER_FILTER = (By.ID, "user-filter")
    ORDER_TABLE = (By.ID, "order-table")
    EXPORT_BUTTON = (By.ID, "export-btn")
    PRINT_BUTTON = (By.ID, "print-btn")

    # 订单表格相关元素
    TABLE_ROWS = (By.CSS_SELECTOR, "#order-table tbody tr")
    TABLE_HEADERS = (By.CSS_SELECTOR, "#order-table thead th")
    SELECT_ALL_CHECKBOX = (By.ID, "select-all")
    ORDER_CHECKBOX = (By.CSS_SELECTOR, ".order-checkbox")
    VIEW_BUTTON = (By.CSS_SELECTOR, ".view-btn")
    EDIT_BUTTON = (By.CSS_SELECTOR, ".edit-btn")
    DELETE_BUTTON = (By.CSS_SELECTOR, ".delete-btn")
    SHIP_BUTTON = (By.CSS_SELECTOR, ".ship-btn")

    # 分页元素
    PAGINATION = (By.CLASS_NAME, "pagination")
    PAGE_NEXT = (By.CLASS_NAME, "page-next")
    PAGE_PREV = (By.CLASS_NAME, "page-prev")
    PAGE_NUMBER = (By.CLASS_NAME, "page-number")
    CURRENT_PAGE = (By.CLASS_NAME, "current-page")

    # 时间筛选器元素
    START_DATE_INPUT = (By.ID, "start-date")
    END_DATE_INPUT = (By.ID, "end-date")
    QUICK_TIME_BUTTONS = (By.CLASS_NAME, "quick-time")
    FILTER_APPLY_BUTTON = (By.ID, "filter-apply")
    FILTER_RESET_BUTTON = (By.ID, "filter-reset")

    # 订单状态标签
    STATUS_LABEL = (By.CLASS_NAME, "status-label")
    PENDING_PAYMENT = (By.CLASS_NAME, "status-pending-payment")
    PAID = (By.CLASS_NAME, "status-paid")
    PENDING_SHIPMENT = (By.CLASS_NAME, "status-pending-shipment")
    SHIPPED = (By.CLASS_NAME, "status-shipped")
    COMPLETED = (By.CLASS_NAME, "status-completed")
    CANCELLED = (By.CLASS_NAME, "status-cancelled")

    # 批量操作
    BATCH_OPERATION_SELECT = (By.ID, "batch-operation-select")
    BATCH_OPERATION_BUTTON = (By.ID, "batch-operation-btn")

    def __init__(self, driver):
        """
        初始化订单列表页面

        Args:
            driver: WebDriver实例
        """
        super().__init__(driver)
        self.logger.info("初始化订单列表页面对象")

    def open_order_list_page(self, base_url: Optional[str] = None) -> None:
        """
        打开订单列表页面

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

        self.logger.info(f"打开订单列表页面: {full_url}")
        self.open(full_url)
        self.wait_for_page_load()
        self.wait_for_order_table_loaded()

    def wait_for_order_table_loaded(self, timeout: int = 30) -> None:
        """
        等待订单表格加载完成

        Args:
            timeout: 等待超时时间
        """
        self.logger.info("等待订单表格加载完成")
        self.find_element(self.ORDER_TABLE, timeout=timeout)
        # 等待至少一行数据加载（如果有数据的话）
        try:
            rows = self.find_elements(self.TABLE_ROWS, timeout=5)
            if rows:
                self.logger.info(f"订单表格加载完成，找到 {len(rows)} 行数据")
        except Exception:
            self.logger.info("订单表格已加载，可能没有数据")

    def search_order(self, keyword: str, search_type: str = "order_id") -> None:
        """
        搜索订单

        Args:
            keyword: 搜索关键词
            search_type: 搜索类型，如 "order_id", "username", "phone"
        """
        self.logger.info(f"搜索订单 - 类型: {search_type}, 关键词: {keyword}")

        # 如果有搜索类型选择器，先选择搜索类型
        try:
            search_type_select = (By.ID, "search-type-select")
            select_element = self.find_element(search_type_select)
            select = Select(select_element)
            select.select_by_value(search_type)
        except Exception:
            self.logger.debug("没有搜索类型选择器，使用默认搜索")

        # 输入搜索关键词
        self.type(self.SEARCH_INPUT, keyword)

        # 点击搜索按钮
        self.click(self.SEARCH_BUTTON)

        # 等待搜索结果
        time.sleep(1)
        self.wait_for_order_table_loaded()

    def filter_by_status(self, status: str) -> None:
        """
        按状态筛选订单

        Args:
            status: 状态，如 "待付款", "待发货", "已发货"
        """
        self.logger.info(f"按状态筛选订单: {status}")

        # 查找状态筛选器
        status_filter = self.find_element(self.STATUS_FILTER)

        # 使用Select类处理下拉选择
        select = Select(status_filter)
        select.select_by_visible_text(status)

        # 应用筛选
        self.click(self.FILTER_APPLY_BUTTON)

        # 等待筛选结果
        time.sleep(1)
        self.wait_for_order_table_loaded()

    def filter_by_time_range(self, start_date: Optional[str] = None,
                             end_date: Optional[str] = None) -> None:
        """
        按时间范围筛选订单

        Args:
            start_date: 开始日期，格式: "YYYY-MM-DD"
            end_date: 结束日期，格式: "YYYY-MM-DD"
        """
        self.logger.info(f"按时间范围筛选订单: {start_date} - {end_date}")

        # 输入开始日期
        if start_date:
            self.type(self.START_DATE_INPUT, start_date)

        # 输入结束日期
        if end_date:
            self.type(self.END_DATE_INPUT, end_date)

        # 应用筛选
        self.click(self.FILTER_APPLY_BUTTON)

        # 等待筛选结果
        time.sleep(1)
        self.wait_for_order_table_loaded()

    def filter_by_quick_time(self, quick_option: str) -> None:
        """
        使用快速时间筛选

        Args:
            quick_option: 快速选项，如 "today", "yesterday", "this_week", "this_month"
        """
        self.logger.info(f"使用快速时间筛选: {quick_option}")

        # 查找快速时间按钮
        quick_buttons = self.find_elements(self.QUICK_TIME_BUTTONS)
        button_texts = {
            "today": "今天",
            "yesterday": "昨天",
            "this_week": "本周",
            "this_month": "本月",
            "last_week": "上周",
            "last_month": "上月",
        }

        target_text = button_texts.get(quick_option, quick_option)

        for button in quick_buttons:
            if target_text in button.text:
                button.click()
                break

        # 等待筛选结果
        time.sleep(1)
        self.wait_for_order_table_loaded()

    def filter_by_user(self, user_info: str) -> None:
        """
        按用户筛选订单

        Args:
            user_info: 用户信息，如用户名、手机号、邮箱
        """
        self.logger.info(f"按用户筛选订单: {user_info}")

        # 查找用户筛选器
        user_filter = self.find_element(self.USER_FILTER)

        # 输入用户信息
        user_filter.clear()
        user_filter.send_keys(user_info)

        # 应用筛选
        self.click(self.FILTER_APPLY_BUTTON)

        # 等待筛选结果
        time.sleep(1)
        self.wait_for_order_table_loaded()

    def get_order_count(self) -> int:
        """
        获取订单数量

        Returns:
            int: 订单数量
        """
        rows = self.find_elements(self.TABLE_ROWS, timeout=5)
        count = len(rows)
        self.logger.debug(f"订单数量: {count}")
        return count

    def get_order_rows(self) -> List[Dict[str, Any]]:
        """
        获取订单行数据

        Returns:
            List[Dict[str, Any]]: 订单行数据列表
        """
        rows = self.find_elements(self.TABLE_ROWS, timeout=5)
        orders = []

        for i, row in enumerate(rows):
            try:
                # 获取行内单元格数据
                cells = row.find_elements(By.TAG_NAME, "td")

                order_data = {
                    "row_index": i,
                    "order_id": cells[1].text if len(cells) > 1 else "",
                    "username": cells[2].text if len(cells) > 2 else "",
                    "order_time": cells[3].text if len(cells) > 3 else "",
                    "total_amount": cells[4].text if len(cells) > 4 else "",
                    "status": cells[5].text if len(cells) > 5 else "",
                    "payment_method": cells[6].text if len(cells) > 6 else "",
                }
                orders.append(order_data)

            except Exception as e:
                self.logger.warning(f"获取第 {i} 行订单数据失败: {e}")

        self.logger.debug(f"获取到 {len(orders)} 条订单数据")
        return orders

    def select_order_by_index(self, index: int) -> None:
        """
        通过索引选择订单

        Args:
            index: 订单行索引（从0开始）
        """
        self.logger.info(f"选择第 {index} 个订单")

        rows = self.find_elements(self.TABLE_ROWS, timeout=5)
        if index < len(rows):
            checkbox = rows[index].find_element(By.CSS_SELECTOR, ".order-checkbox")
            checkbox.click()
        else:
            raise IndexError(f"订单索引超出范围: {index}，总共 {len(rows)} 个订单")

    def select_order_by_id(self, order_id: str) -> bool:
        """
        通过订单号选择订单

        Args:
            order_id: 订单号

        Returns:
            bool: 如果找到并选择了订单则返回True
        """
        self.logger.info(f"选择订单: {order_id}")

        orders = self.get_order_rows()
        for i, order in enumerate(orders):
            if order["order_id"] == order_id:
                self.select_order_by_index(i)
                return True

        self.logger.warning(f"未找到订单: {order_id}")
        return False

    def select_all_orders(self) -> None:
        """选择所有订单"""
        self.logger.info("选择所有订单")
        self.click(self.SELECT_ALL_CHECKBOX)

    def click_view_order(self, index: int) -> None:
        """
        点击查看订单按钮

        Args:
            index: 订单行索引
        """
        self.logger.info(f"点击查看第 {index} 个订单")

        rows = self.find_elements(self.TABLE_ROWS, timeout=5)
        if index < len(rows):
            view_button = rows[index].find_element(By.CSS_SELECTOR, ".view-btn")
            view_button.click()
        else:
            raise IndexError(f"订单索引超出范围: {index}")

    def click_ship_order(self, index: int) -> None:
        """
        点击发货按钮

        Args:
            index: 订单行索引
        """
        self.logger.info(f"点击发货第 {index} 个订单")

        rows = self.find_elements(self.TABLE_ROWS, timeout=5)
        if index < len(rows):
            ship_button = rows[index].find_element(By.CSS_SELECTOR, ".ship-btn")
            ship_button.click()
        else:
            raise IndexError(f"订单索引超出范围: {index}")

    def click_edit_order(self, index: int) -> None:
        """
        点击编辑订单按钮

        Args:
            index: 订单行索引
        """
        self.logger.info(f"点击编辑第 {index} 个订单")

        rows = self.find_elements(self.TABLE_ROWS, timeout=5)
        if index < len(rows):
            edit_button = rows[index].find_element(By.CSS_SELECTOR, ".edit-btn")
            edit_button.click()
        else:
            raise IndexError(f"订单索引超出范围: {index}")

    def batch_operation(self, operation: str) -> None:
        """
        批量操作

        Args:
            operation: 操作类型，如 "发货", "取消", "删除", "导出"
        """
        self.logger.info(f"批量操作: {operation}")

        # 选择批量操作类型
        operation_select = self.find_element(self.BATCH_OPERATION_SELECT)
        select = Select(operation_select)
        select.select_by_visible_text(operation)

        # 点击批量操作按钮
        self.click(self.BATCH_OPERATION_BUTTON)

    def export_orders(self, format: str = "excel") -> None:
        """
        导出订单

        Args:
            format: 导出格式，如 "excel", "csv", "pdf"
        """
        self.logger.info(f"导出订单，格式: {format}")

        # 点击导出按钮
        self.click(self.EXPORT_BUTTON)

        # 选择导出格式（如果页面有格式选择）
        try:
            format_select = (By.ID, "export-format")
            self.click(format_select)

            format_option = (By.XPATH, f"//option[text()='{format}']")
            self.click(format_option)
        except Exception:
            self.logger.debug("页面没有导出格式选择，使用默认格式")

        # 确认导出（如果有确认对话框）
        try:
            confirm_button = (By.ID, "export-confirm")
            self.click(confirm_button)
        except Exception:
            self.logger.debug("没有导出确认对话框")

    def print_orders(self) -> None:
        """打印订单"""
        self.logger.info("打印订单")
        self.click(self.PRINT_BUTTON)

    def reset_filters(self) -> None:
        """重置筛选器"""
        self.logger.info("重置筛选器")
        self.click(self.FILTER_RESET_BUTTON)
        self.wait_for_order_table_loaded()

    def go_to_next_page(self) -> None:
        """转到下一页"""
        self.logger.info("转到下一页")
        self.click(self.PAGE_NEXT)
        self.wait_for_order_table_loaded()

    def go_to_previous_page(self) -> None:
        """转到上一页"""
        self.logger.info("转到上一页")
        self.click(self.PAGE_PREV)
        self.wait_for_order_table_loaded()

    def go_to_page(self, page_number: int) -> None:
        """
        转到指定页码

        Args:
            page_number: 页码
        """
        self.logger.info(f"转到第 {page_number} 页")

        # 查找页码链接
        page_link = (By.XPATH, f"//a[contains(@class, 'page-number') and text()='{page_number}']")
        try:
            self.click(page_link)
            self.wait_for_order_table_loaded()
        except Exception:
            self.logger.warning(f"第 {page_number} 页链接不存在")

    def get_current_page(self) -> int:
        """
        获取当前页码

        Returns:
            int: 当前页码
        """
        try:
            current_page_element = self.find_element(self.CURRENT_PAGE, timeout=5)
            page_text = current_page_element.text
            # 从文本中提取页码
            import re
            match = re.search(r'\d+', page_text)
            if match:
                return int(match.group())
        except Exception:
            pass

        # 默认返回第1页
        return 1

    def is_order_present(self, order_id: str) -> bool:
        """
        检查订单是否存在

        Args:
            order_id: 订单号

        Returns:
            bool: 如果订单存在则返回True
        """
        orders = self.get_order_rows()
        for order in orders:
            if order["order_id"] == order_id:
                return True
        return False

    def get_order_status(self, order_id: str) -> Optional[str]:
        """
        获取订单状态

        Args:
            order_id: 订单号

        Returns:
            Optional[str]: 订单状态，如果找不到订单则返回None
        """
        orders = self.get_order_rows()
        for order in orders:
            if order["order_id"] == order_id:
                return order["status"]
        return None

    def verify_order_list_elements(self) -> bool:
        """
        验证订单列表页面所有关键元素是否存在

        Returns:
            bool: 如果所有关键元素都存在则返回True
        """
        self.logger.info("验证订单列表页面关键元素")

        elements_to_check = [
            ("搜索输入框", self.SEARCH_INPUT),
            ("搜索按钮", self.SEARCH_BUTTON),
            ("订单表格", self.ORDER_TABLE),
            ("状态筛选器", self.STATUS_FILTER),
        ]

        all_present = True
        for element_name, locator in elements_to_check:
            try:
                self.find_element(locator, timeout=5)
                self.logger.debug(f"元素存在: {element_name}")
            except Exception:
                self.logger.warning(f"元素不存在: {element_name}")
                all_present = False

        return all_present

    def take_order_list_screenshot(self, filename: Optional[str] = None) -> str:
        """
        截取订单列表页面截图

        Args:
            filename: 截图文件名，如果为None则自动生成

        Returns:
            str: 截图文件路径
        """
        if filename is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"order_list_{timestamp}.png"

        screenshot_path = self.take_screenshot(filename, "订单列表页面截图")
        return screenshot_path

    def wait_for_operation_complete(self, timeout: int = 10) -> None:
        """
        等待操作完成

        Args:
            timeout: 等待超时时间
        """
        self.logger.info("等待操作完成")

        # 等待加载指示器消失（如果有）
        try:
            loading_indicator = (By.CLASS_NAME, "loading-indicator")
            self.wait_for_element_disappear(loading_indicator, timeout=timeout)
        except Exception:
            pass

        # 等待页面稳定
        time.sleep(1)


# 快捷函数
def create_order_list_page(driver):
    """
    创建订单列表页面对象的快捷函数

    Args:
        driver: WebDriver实例

    Returns:
        OrderListPage: 订单列表页面对象实例
    """
    return OrderListPage(driver)


if __name__ == "__main__":
    # 测试订单列表页面类
    print("测试OrderListPage类...")

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

        # 创建订单列表页面对象
        order_list_page = OrderListPage(driver)
        print("OrderListPage类导入和实例化成功")

        # 测试页面元素常量
        print(f"搜索输入框定位器: {order_list_page.SEARCH_INPUT}")
        print(f"订单表格定位器: {order_list_page.ORDER_TABLE}")
        print(f"状态筛选器定位器: {order_list_page.STATUS_FILTER}")

        driver.quit()
        print("测试完成")

    except Exception as e:
        print(f"测试过程中出错: {e}")
        print("注意：此测试需要安装ChromeDriver")
