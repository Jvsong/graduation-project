#!/usr/bin/env python3
"""
订单列表页面对象
适配 shop-system 的 Vue + Element Plus 订单管理页面。
"""

import time
from typing import Any, Dict, List, Optional

from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class OrderListPage(BasePage):
    """订单列表页面对象类。"""

    url = "/admin/orders"

    PAGE_TITLE = (By.CSS_SELECTOR, ".page-title")
    SEARCH_INPUT = (By.CSS_SELECTOR, ".search-form .el-input input")
    SEARCH_BUTTON = (By.CSS_SELECTOR, ".search-actions .el-button--primary")
    RESET_BUTTON = (By.XPATH, "//button[.//span[contains(normalize-space(), '重置')]]")
    STATUS_FILTER = (By.CSS_SELECTOR, ".search-form .el-select .el-select__wrapper")
    START_DATE_INPUT = (By.CSS_SELECTOR, ".search-form .el-date-editor .el-range-input:nth-of-type(1)")
    END_DATE_INPUT = (By.CSS_SELECTOR, ".search-form .el-date-editor .el-range-input:nth-of-type(2)")
    ORDER_TABLE = (By.CSS_SELECTOR, ".table-card .el-table")
    TABLE_ROWS = (By.CSS_SELECTOR, ".table-card .el-table__body-wrapper tbody tr")
    SELECT_ALL_CHECKBOX = (By.CSS_SELECTOR, ".table-card .el-table__header-wrapper .el-checkbox")
    ORDER_CHECKBOX = (By.CSS_SELECTOR, ".el-checkbox")
    VIEW_BUTTON = (By.XPATH, ".//button[.//span[contains(normalize-space(), '详情')]]")
    SHIP_BUTTON = (By.XPATH, ".//button[.//span[contains(normalize-space(), '发货')]]")
    BATCH_CANCEL_BUTTON = (By.XPATH, "//button[.//span[contains(normalize-space(), '批量取消')]]")
    BATCH_SHIP_BUTTON = (By.XPATH, "//button[.//span[contains(normalize-space(), '批量发货')]]")

    def __init__(self, driver):
        super().__init__(driver)
        self.logger.info("初始化订单列表页面对象")

    def open_order_list_page(self, base_url: Optional[str] = None) -> None:
        """打开订单列表页面。"""
        if not base_url:
            from utils.config_manager import get_config

            config = get_config()
            base_url = config.get("environment.base_url", "http://localhost:3000")

        full_url = f"{base_url.rstrip('/')}{self.url}"
        self.logger.info(f"打开订单列表页面: {full_url}")
        self.open(full_url)
        self.wait_for_page_load()
        self.wait_for_order_table_loaded()

    def wait_for_order_table_loaded(self, timeout: int = 30) -> None:
        """等待订单页主结构加载完成。"""
        self.logger.info("等待订单表格加载完成")
        self.find_element(self.PAGE_TITLE, timeout=timeout)
        self.find_element(self.ORDER_TABLE, timeout=timeout)
        try:
            rows = self.find_elements(self.TABLE_ROWS, timeout=5)
            self.logger.info(f"订单表格加载完成，找到 {len(rows)} 行")
        except Exception:
            self.logger.info("订单表格已加载，当前没有可见数据行")

    def search_order(self, keyword: str, search_type: str = "order_id") -> None:
        """
        搜索订单。
        当前 shop-system 页面只有订单号输入框，因此其他 search_type 也复用这个输入框。
        """
        self.logger.info(f"搜索订单 - 类型: {search_type}, 关键词: {keyword}")
        self.type(self.SEARCH_INPUT, keyword)
        self.click(self.SEARCH_BUTTON)
        time.sleep(1)
        self.wait_for_order_table_loaded()

    def filter_by_status(self, status: str) -> None:
        """按状态筛选订单。"""
        self.logger.info(f"按状态筛选订单: {status}")
        self.click(self.STATUS_FILTER)
        option = (
            By.XPATH,
            f"//div[contains(@class,'el-select-dropdown')]//li[normalize-space()='{status}']",
        )
        self.click(option)
        time.sleep(1)
        self.wait_for_order_table_loaded()

    def filter_by_time_range(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> None:
        """按时间范围筛选订单。"""
        self.logger.info(f"按时间范围筛选订单: {start_date} - {end_date}")
        if start_date:
            self.type(self.START_DATE_INPUT, start_date)
        if end_date:
            self.type(self.END_DATE_INPUT, end_date)
        time.sleep(1)
        self.wait_for_order_table_loaded()

    def filter_by_quick_time(self, quick_option: str) -> None:
        """当前页面没有快捷时间按钮，保留兼容调用。"""
        self.logger.info(f"快速时间筛选在当前页面未实现，跳过: {quick_option}")
        self.wait_for_order_table_loaded()

    def filter_by_user(self, user_info: str) -> None:
        """兼容旧测试入口，当前页面复用订单号搜索框。"""
        self.search_order(user_info, search_type="username")

    def get_order_count(self) -> int:
        """获取订单数量。"""
        return len(self.get_order_rows())

    def get_order_rows(self) -> List[Dict[str, Any]]:
        """获取订单行数据。"""
        rows = self.find_elements(self.TABLE_ROWS, timeout=5)
        orders: List[Dict[str, Any]] = []

        for i, row in enumerate(rows):
            try:
                row_class = row.get_attribute("class") or ""
                if "no-data" in row_class:
                    continue

                cells = row.find_elements(By.CSS_SELECTOR, "td .cell")
                if not cells:
                    continue

                orders.append(
                    {
                        "row_index": i,
                        "order_id": cells[0].text.strip() if len(cells) > 0 else "",
                        "username": cells[1].text.strip() if len(cells) > 1 else "",
                        "total_amount": cells[2].text.strip() if len(cells) > 2 else "",
                        "status": cells[3].text.strip() if len(cells) > 3 else "",
                        "payment_method": "",
                        "order_time": cells[4].text.strip() if len(cells) > 4 else "",
                    }
                )
            except Exception as exc:
                self.logger.warning(f"获取第 {i} 行订单数据失败: {exc}")

        self.logger.debug(f"获取到 {len(orders)} 条订单数据")
        return orders

    def select_order_by_index(self, index: int) -> None:
        """按行号勾选订单。"""
        rows = self.find_elements(self.TABLE_ROWS, timeout=5)
        if index >= len(rows):
            raise IndexError(f"订单索引超出范围: {index}")
        checkbox = rows[index].find_element(self.ORDER_CHECKBOX[0], self.ORDER_CHECKBOX[1])
        checkbox.click()

    def select_order_by_id(self, order_id: str) -> bool:
        """按订单号勾选订单。"""
        orders = self.get_order_rows()
        for i, order in enumerate(orders):
            if order["order_id"] == order_id:
                self.select_order_by_index(i)
                return True
        self.logger.warning(f"未找到订单: {order_id}")
        return False

    def select_all_orders(self) -> None:
        """勾选全部订单。"""
        self.click(self.SELECT_ALL_CHECKBOX)

    def click_view_order(self, index: int) -> None:
        """点击查看订单详情。"""
        rows = self.find_elements(self.TABLE_ROWS, timeout=5)
        if index >= len(rows):
            raise IndexError(f"订单索引超出范围: {index}")
        rows[index].find_element(self.VIEW_BUTTON[0], self.VIEW_BUTTON[1]).click()

    def click_ship_order(self, index: int) -> None:
        """点击发货按钮。"""
        rows = self.find_elements(self.TABLE_ROWS, timeout=5)
        if index >= len(rows):
            raise IndexError(f"订单索引超出范围: {index}")
        rows[index].find_element(self.SHIP_BUTTON[0], self.SHIP_BUTTON[1]).click()

    def click_edit_order(self, index: int) -> None:
        """当前页面没有独立编辑按钮，复用详情入口。"""
        self.click_view_order(index)

    def batch_operation(self, operation: str) -> None:
        """执行批量操作。"""
        self.logger.info(f"批量操作: {operation}")
        if "发货" in operation:
            self.click(self.BATCH_SHIP_BUTTON)
            return
        if "取消" in operation:
            self.click(self.BATCH_CANCEL_BUTTON)
            return
        raise NotImplementedError(f"当前页面未实现批量操作: {operation}")

    def export_orders(self, format: str = "excel") -> None:
        """当前页面没有显式导出按钮，保留接口兼容并记录。"""
        self.logger.info(f"当前订单页未提供导出按钮，跳过导出: {format}")

    def print_orders(self) -> None:
        """当前页面没有显式打印按钮。"""
        self.logger.info("当前订单页未提供打印按钮，跳过打印")

    def reset_filters(self) -> None:
        """重置筛选器。"""
        self.click(self.RESET_BUTTON)
        time.sleep(1)
        self.wait_for_order_table_loaded()

    def go_to_next_page(self) -> None:
        self.click((By.CSS_SELECTOR, ".el-pagination .btn-next"))
        self.wait_for_order_table_loaded()

    def go_to_previous_page(self) -> None:
        self.click((By.CSS_SELECTOR, ".el-pagination .btn-prev"))
        self.wait_for_order_table_loaded()

    def go_to_page(self, page_number: int) -> None:
        locator = (
            By.XPATH,
            f"//ul[contains(@class,'el-pager')]//li[normalize-space()='{page_number}']",
        )
        self.click(locator)
        self.wait_for_order_table_loaded()

    def get_current_page(self) -> int:
        try:
            current_page = self.find_element((By.CSS_SELECTOR, ".el-pagination .el-pager li.is-active"), timeout=5)
            return int(current_page.text.strip())
        except Exception:
            return 1

    def is_order_present(self, order_id: str) -> bool:
        return any(order["order_id"] == order_id for order in self.get_order_rows())

    def get_order_status(self, order_id: str) -> Optional[str]:
        for order in self.get_order_rows():
            if order["order_id"] == order_id:
                return order["status"]
        return None

    def verify_order_list_elements(self) -> bool:
        """校验订单列表页面关键元素。"""
        self.logger.info("验证订单列表页面关键元素")
        elements_to_check = [
            self.PAGE_TITLE,
            self.SEARCH_INPUT,
            self.SEARCH_BUTTON,
            self.ORDER_TABLE,
            self.STATUS_FILTER,
        ]
        for locator in elements_to_check:
            if not self.is_element_present(locator, timeout=5):
                self.logger.warning(f"页面关键元素不存在: {locator}")
                return False
        return True

    def take_order_list_screenshot(self, filename: Optional[str] = None) -> str:
        if filename is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"order_list_{timestamp}.png"
        return self.take_screenshot(filename, "订单列表页面截图")

    def wait_for_operation_complete(self, timeout: int = 10) -> None:
        """等待页面稳定。"""
        time.sleep(min(timeout, 2))
        self.wait_for_order_table_loaded(timeout=timeout)

    def is_element_present(self, locator, timeout: Optional[int] = None) -> bool:
        try:
            self.find_element(locator, timeout=timeout)
            return True
        except Exception:
            return False


def create_order_list_page(driver):
    """创建订单列表页面对象。"""
    return OrderListPage(driver)
