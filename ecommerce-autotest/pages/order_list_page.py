#!/usr/bin/env python3
"""
订单列表页面对象。
适配当前 shop-system 的 Element Plus 订单管理页。
"""

import time
from typing import Any, Dict, List, Optional

from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class OrderListPage(BasePage):
    url = "/admin/orders"

    PAGE_TITLE = (By.XPATH, "//*[contains(normalize-space(), '订单管理')]")
    ORDER_ID_INPUT = (By.XPATH, "(//div[contains(@class,'search-form')]//input)[1]")
    USERNAME_INPUT = (By.XPATH, "(//div[contains(@class,'search-form')]//input)[2]")
    STATUS_FILTER = (
        By.XPATH,
        "(//div[contains(@class,'search-form')]//div[contains(@class,'el-select__wrapper')])[1]",
    )
    START_DATE_INPUT = (By.XPATH, "(//div[contains(@class,'search-form')]//input[contains(@placeholder,'开始日期')])[1]")
    END_DATE_INPUT = (By.XPATH, "(//div[contains(@class,'search-form')]//input[contains(@placeholder,'结束日期')])[1]")
    SEARCH_BUTTON = (By.XPATH, "//button[.//span[contains(normalize-space(), '搜索')]]")
    RESET_BUTTON = (By.XPATH, "//button[.//span[contains(normalize-space(), '重置')]]")

    ORDER_TABLE = (By.CSS_SELECTOR, ".table-card .el-table, .table-card table")
    TABLE_ROWS = (
        By.CSS_SELECTOR,
        ".table-card .el-table__body-wrapper tbody tr, .table-card .el-table__body tbody tr, .table-card table tbody tr",
    )
    SELECT_ALL_CHECKBOX = (By.CSS_SELECTOR, ".table-card .el-table__header-wrapper .el-checkbox")
    NO_DATA = (By.XPATH, "//div[contains(@class,'el-table__empty-text') and contains(normalize-space(), '暂无数据')]")

    def __init__(self, driver):
        super().__init__(driver)
        self.logger.info("初始化订单列表页面对象")

    def open_order_list_page(self, base_url: Optional[str] = None) -> None:
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
        self.find_element(self.PAGE_TITLE, timeout=timeout)
        self.find_element(self.ORDER_TABLE, timeout=timeout)
        time.sleep(1)

    def _select_dropdown_option(self, trigger, visible_text: str) -> None:
        self.click(trigger)
        option = (
            By.XPATH,
            f"//div[contains(@class,'el-select-dropdown')]//*[contains(@class,'el-select-dropdown__item')][normalize-space()='{visible_text}']",
        )
        self.click(option)

    def search_order(self, keyword: str, search_type: str = "order_id") -> None:
        self.logger.info(f"搜索订单 - 类型: {search_type}, 关键词: {keyword}")
        target = self.ORDER_ID_INPUT if search_type in {"order_id", "product_name"} else self.USERNAME_INPUT
        self.type(target, keyword)
        self.click(self.SEARCH_BUTTON)
        time.sleep(1)
        self.wait_for_order_table_loaded()

    def filter_by_status(self, status: str) -> None:
        self._select_dropdown_option(self.STATUS_FILTER, status)
        self.click(self.SEARCH_BUTTON)
        time.sleep(1)
        self.wait_for_order_table_loaded()

    def filter_by_time_range(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> None:
        if start_date and self.is_element_present(self.START_DATE_INPUT, timeout=2):
            self.type(self.START_DATE_INPUT, start_date)
        if end_date and self.is_element_present(self.END_DATE_INPUT, timeout=2):
            self.type(self.END_DATE_INPUT, end_date)
        self.click(self.SEARCH_BUTTON)
        time.sleep(1)
        self.wait_for_order_table_loaded()

    def filter_by_quick_time(self, quick_option: str) -> None:
        self.logger.info(f"当前订单页未提供快捷时间筛选，跳过: {quick_option}")
        self.wait_for_order_table_loaded()

    def get_order_rows(self) -> List[Dict[str, Any]]:
        if self.is_element_present(self.NO_DATA, timeout=2):
            return []

        rows = self.find_elements(self.TABLE_ROWS, timeout=5)
        orders: List[Dict[str, Any]] = []
        for index, row in enumerate(rows):
            text = row.text.strip()
            if not text or "暂无数据" in text:
                continue

            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) < 6:
                continue

            customer_lines = [line.strip() for line in cells[2].text.splitlines() if line.strip()]
            orders.append(
                {
                    "row_index": index,
                    "order_id": cells[1].text.strip() if len(cells) > 1 else "",
                    "username": customer_lines[0] if customer_lines else "",
                    "total_amount": cells[3].text.strip() if len(cells) > 3 else "",
                    "status": cells[4].text.strip() if len(cells) > 4 else "",
                    "payment_method": "",
                    "order_time": cells[5].text.strip() if len(cells) > 5 else "",
                }
            )
        return orders

    def select_order_by_index(self, index: int) -> None:
        rows = self.find_elements(self.TABLE_ROWS, timeout=5)
        if index >= len(rows):
            raise IndexError(f"订单索引超出范围: {index}")
        checkbox = rows[index].find_element(By.CSS_SELECTOR, ".el-checkbox")
        checkbox.click()

    def select_order_by_id(self, order_id: str) -> bool:
        for order in self.get_order_rows():
            if order.get("order_id") == order_id:
                self.select_order_by_index(order["row_index"])
                return True
        return False

    def select_all_orders(self) -> None:
        self.click(self.SELECT_ALL_CHECKBOX)

    def click_view_order(self, index: int) -> None:
        rows = self.find_elements(self.TABLE_ROWS, timeout=5)
        if index >= len(rows):
            raise IndexError(f"订单索引超出范围: {index}")
        target = rows[index].find_element(
            By.XPATH,
            ".//*[self::button or self::a or self::span][contains(normalize-space(), '详情')]",
        )
        target.click()

    def click_ship_order(self, index: int) -> None:
        rows = self.find_elements(self.TABLE_ROWS, timeout=5)
        if index >= len(rows):
            raise IndexError(f"订单索引超出范围: {index}")
        row = rows[index]
        more_button = row.find_element(
            By.XPATH,
            ".//*[self::button or self::a or self::span][contains(normalize-space(), '更多')]",
        )
        more_button.click()
        ship_action = (
            By.XPATH,
            "//div[contains(@class,'el-dropdown-menu')]//*[contains(normalize-space(), '发货')]",
        )
        self.click(ship_action)

    def batch_operation(self, operation: str) -> None:
        button = (
            By.XPATH,
            f"//button[.//span[contains(normalize-space(), '{operation}')]]",
        )
        self.click(button)

    def export_orders(self, format: str = "excel") -> None:
        export_button = (By.XPATH, "//button[.//span[contains(normalize-space(), '导出')]]")
        if self.is_element_present(export_button, timeout=2):
            self.click(export_button)
            time.sleep(1)
        else:
            self.logger.info(f"当前订单页未提供导出按钮，跳过导出: {format}")

    def reset_filters(self) -> None:
        self.click(self.RESET_BUTTON)
        time.sleep(1)
        self.wait_for_order_table_loaded()

    def sort_by(self, sort_by: str) -> None:
        label = "下单时间" if "order_time" in sort_by else "金额"
        clicks = 2 if sort_by.endswith("_desc") else 1
        header = (By.XPATH, f"//th[.//*[contains(normalize-space(), '{label}')]]")
        for _ in range(clicks):
            self.click(header)
            time.sleep(0.5)
        self.wait_for_order_table_loaded()

    def get_order_status(self, order_id: str) -> Optional[str]:
        for order in self.get_order_rows():
            if order.get("order_id") == order_id:
                return order.get("status")
        return None

    def verify_order_list_elements(self) -> bool:
        elements = [
            self.ORDER_ID_INPUT,
            self.USERNAME_INPUT,
            self.STATUS_FILTER,
            self.SEARCH_BUTTON,
            self.ORDER_TABLE,
        ]
        return all(self.is_element_present(locator, timeout=3) for locator in elements)

    def is_element_present(self, locator, timeout: Optional[int] = None) -> bool:
        try:
            self.find_element(locator, timeout=timeout)
            return True
        except Exception:
            return False


def create_order_list_page(driver):
    return OrderListPage(driver)
