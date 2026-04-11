#!/usr/bin/env python3
"""
订单操作页面对象
实现电商后台管理系统的订单详情查看、发货、退款等操作功能
"""

import time
from typing import Optional, Tuple, List, Dict, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from pages.base_page import BasePage


class OrderOperationPage(BasePage):
    """
    订单操作页面对象类
    封装订单详情、发货、退款等操作的所有元素和操作
    """

    # 页面URL模式
    url_view = "/order/view/"
    url_edit = "/order/edit/"
    url_ship = "/order/ship/"
    url_refund = "/order/refund/"

    # 订单基本信息元素
    ORDER_ID = (By.ID, "order-id")
    ORDER_STATUS = (By.ID, "order-status")
    ORDER_TIME = (By.ID, "order-time")
    TOTAL_AMOUNT = (By.ID, "total-amount")
    PAYMENT_METHOD = (By.ID, "payment-method")
    PAYMENT_STATUS = (By.ID, "payment-status")

    # 用户信息元素
    USERNAME = (By.ID, "username")
    PHONE = (By.ID, "phone")
    EMAIL = (By.ID, "email")
    SHIPPING_ADDRESS = (By.ID, "shipping-address")

    # 订单商品列表
    ORDER_ITEMS_TABLE = (By.ID, "order-items-table")
    ITEM_ROWS = (By.CSS_SELECTOR, "#order-items-table tbody tr")
    ITEM_NAME = (By.CLASS_NAME, "item-name")
    ITEM_QUANTITY = (By.CLASS_NAME, "item-quantity")
    ITEM_PRICE = (By.CLASS_NAME, "item-price")
    ITEM_SUBTOTAL = (By.CLASS_NAME, "item-subtotal")

    # 发货信息元素
    SHIPMENT_SECTION = (By.ID, "shipment-section")
    COURIER_SELECT = (By.ID, "courier-select")
    TRACKING_NUMBER_INPUT = (By.ID, "tracking-number")
    SHIPMENT_TIME_INPUT = (By.ID, "shipment-time")
    SHIP_BUTTON = (By.ID, "ship-btn")
    CANCEL_SHIPMENT_BUTTON = (By.ID, "cancel-shipment-btn")

    # 退款信息元素
    REFUND_SECTION = (By.ID, "refund-section")
    REFUND_AMOUNT_INPUT = (By.ID, "refund-amount")
    REFUND_REASON_SELECT = (By.ID, "refund-reason")
    REFUND_REASON_INPUT = (By.ID, "refund-reason-input")
    REFUND_BUTTON = (By.ID, "refund-btn")
    CANCEL_REFUND_BUTTON = (By.ID, "cancel-refund-btn")

    # 订单操作按钮
    EDIT_ORDER_BUTTON = (By.ID, "edit-order-btn")
    CANCEL_ORDER_BUTTON = (By.ID, "cancel-order-btn")
    DELETE_ORDER_BUTTON = (By.ID, "delete-order-btn")
    PRINT_ORDER_BUTTON = (By.ID, "print-order-btn")
    EXPORT_ORDER_BUTTON = (By.ID, "export-order-btn")
    BACK_TO_LIST_BUTTON = (By.ID, "back-to-list-btn")

    # 订单备注
    NOTES_SECTION = (By.ID, "notes-section")
    ADD_NOTE_BUTTON = (By.ID, "add-note-btn")
    NOTE_INPUT = (By.ID, "note-input")
    NOTES_LIST = (By.ID, "notes-list")

    # 订单历史
    HISTORY_SECTION = (By.ID, "history-section")
    HISTORY_ITEMS = (By.CLASS_NAME, "history-item")

    # 状态操作按钮
    CONFIRM_PAYMENT_BUTTON = (By.ID, "confirm-payment-btn")
    CONFIRM_SHIPMENT_BUTTON = (By.ID, "confirm-shipment-btn")
    CONFIRM_DELIVERY_BUTTON = (By.ID, "confirm-delivery-btn")
    CONFIRM_COMPLETION_BUTTON = (By.ID, "confirm-completion-btn")

    # 表单按钮
    SAVE_BUTTON = (By.ID, "save-btn")
    SUBMIT_BUTTON = (By.ID, "submit-btn")
    CANCEL_BUTTON = (By.ID, "cancel-btn")

    # 消息元素
    SUCCESS_MESSAGE = (By.CLASS_NAME, "success-message")
    ERROR_MESSAGE = (By.CLASS_NAME, "error-message")
    WARNING_MESSAGE = (By.CLASS_NAME, "warning-message")

    def __init__(self, driver):
        """
        初始化订单操作页面

        Args:
            driver: WebDriver实例
        """
        super().__init__(driver)
        self.logger.info("初始化订单操作页面对象")

    def open_order_view_page(self, order_id: str, base_url: Optional[str] = None) -> None:
        """
        打开订单详情页面

        Args:
            order_id: 订单号
            base_url: 基础URL，如果为None则使用配置中的base_url
        """
        if base_url:
            full_url = f"{base_url}{self.url_view}{order_id}"
        else:
            # 从配置获取base_url
            from utils.config_manager import get_config
            config = get_config()
            base_url = config.get('environment.base_url', 'http://test.ecommerce.com/admin')
            full_url = f"{base_url}{self.url_view}{order_id}"

        self.logger.info(f"打开订单详情页面: {full_url}")
        self.open(full_url)
        self.wait_for_page_load()
        self.wait_for_order_details_loaded()

    def open_order_edit_page(self, order_id: str, base_url: Optional[str] = None) -> None:
        """
        打开订单编辑页面

        Args:
            order_id: 订单号
            base_url: 基础URL，如果为None则使用配置中的base_url
        """
        if base_url:
            full_url = f"{base_url}{self.url_edit}{order_id}"
        else:
            # 从配置获取base_url
            from utils.config_manager import get_config
            config = get_config()
            base_url = config.get('environment.base_url', 'http://test.ecommerce.com/admin')
            full_url = f"{base_url}{self.url_edit}{order_id}"

        self.logger.info(f"打开订单编辑页面: {full_url}")
        self.open(full_url)
        self.wait_for_page_load()
        self.wait_for_order_form_loaded()

    def open_shipment_page(self, order_id: str, base_url: Optional[str] = None) -> None:
        """
        打开发货页面

        Args:
            order_id: 订单号
            base_url: 基础URL，如果为None则使用配置中的base_url
        """
        if base_url:
            full_url = f"{base_url}{self.url_ship}{order_id}"
        else:
            # 从配置获取base_url
            from utils.config_manager import get_config
            config = get_config()
            base_url = config.get('environment.base_url', 'http://test.ecommerce.com/admin')
            full_url = f"{base_url}{self.url_ship}{order_id}"

        self.logger.info(f"打开发货页面: {full_url}")
        self.open(full_url)
        self.wait_for_page_load()
        self.wait_for_shipment_form_loaded()

    def open_refund_page(self, order_id: str, base_url: Optional[str] = None) -> None:
        """
        打开退款页面

        Args:
            order_id: 订单号
            base_url: 基础URL，如果为None则使用配置中的base_url
        """
        if base_url:
            full_url = f"{base_url}{self.url_refund}{order_id}"
        else:
            # 从配置获取base_url
            from utils.config_manager import get_config
            config = get_config()
            base_url = config.get('environment.base_url', 'http://test.ecommerce.com/admin')
            full_url = f"{base_url}{self.url_refund}{order_id}"

        self.logger.info(f"打开退款页面: {full_url}")
        self.open(full_url)
        self.wait_for_page_load()
        self.wait_for_refund_form_loaded()

    def wait_for_order_details_loaded(self, timeout: int = 30) -> None:
        """
        等待订单详情加载完成

        Args:
            timeout: 等待超时时间
        """
        self.logger.info("等待订单详情加载完成")
        self.find_element(self.ORDER_ID, timeout=timeout)
        self.find_element(self.ORDER_STATUS, timeout=timeout)

    def wait_for_order_form_loaded(self, timeout: int = 30) -> None:
        """
        等待订单表单加载完成

        Args:
            timeout: 等待超时时间
        """
        self.logger.info("等待订单表单加载完成")
        self.find_element(self.ORDER_ID, timeout=timeout)
        self.find_element(self.SAVE_BUTTON, timeout=timeout)

    def wait_for_shipment_form_loaded(self, timeout: int = 30) -> None:
        """
        等待发货表单加载完成

        Args:
            timeout: 等待超时时间
        """
        self.logger.info("等待发货表单加载完成")
        self.find_element(self.SHIPMENT_SECTION, timeout=timeout)
        self.find_element(self.SHIP_BUTTON, timeout=timeout)

    def wait_for_refund_form_loaded(self, timeout: int = 30) -> None:
        """
        等待退款表单加载完成

        Args:
            timeout: 等待超时时间
        """
        self.logger.info("等待退款表单加载完成")
        self.find_element(self.REFUND_SECTION, timeout=timeout)
        self.find_element(self.REFUND_BUTTON, timeout=timeout)

    def get_order_info(self) -> Dict[str, str]:
        """
        获取订单基本信息

        Returns:
            Dict[str, str]: 订单信息字典
        """
        self.logger.info("获取订单基本信息")

        order_info = {
            "order_id": self.get_element_text(self.ORDER_ID),
            "status": self.get_element_text(self.ORDER_STATUS),
            "order_time": self.get_element_text(self.ORDER_TIME),
            "total_amount": self.get_element_text(self.TOTAL_AMOUNT),
            "payment_method": self.get_element_text(self.PAYMENT_METHOD),
            "payment_status": self.get_element_text(self.PAYMENT_STATUS),
            "username": self.get_element_text(self.USERNAME),
            "phone": self.get_element_text(self.PHONE),
            "email": self.get_element_text(self.EMAIL),
            "shipping_address": self.get_element_text(self.SHIPPING_ADDRESS),
        }

        self.logger.debug(f"订单信息: {order_info}")
        return order_info

    def get_order_items(self) -> List[Dict[str, Any]]:
        """
        获取订单商品列表

        Returns:
            List[Dict[str, Any]]: 订单商品列表
        """
        self.logger.info("获取订单商品列表")

        rows = self.find_elements(self.ITEM_ROWS, timeout=5)
        items = []

        for i, row in enumerate(rows):
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                item_data = {
                    "row_index": i,
                    "name": cells[1].text if len(cells) > 1 else "",
                    "quantity": cells[2].text if len(cells) > 2 else "",
                    "price": cells[3].text if len(cells) > 3 else "",
                    "subtotal": cells[4].text if len(cells) > 4 else "",
                }
                items.append(item_data)
            except Exception as e:
                self.logger.warning(f"获取第 {i} 个商品失败: {e}")

        self.logger.debug(f"获取到 {len(items)} 个订单商品")
        return items

    def ship_order(self, courier: str, tracking_number: str) -> None:
        """
        发货订单

        Args:
            courier: 快递公司
            tracking_number: 运单号
        """
        self.logger.info(f"发货订单 - 快递公司: {courier}, 运单号: {tracking_number}")

        # 选择快递公司
        courier_select = self.find_element(self.COURIER_SELECT)
        select = Select(courier_select)
        select.select_by_visible_text(courier)

        # 输入运单号
        self.type(self.TRACKING_NUMBER_INPUT, tracking_number)

        # 点击发货按钮
        self.click(self.SHIP_BUTTON)

        # 等待操作完成
        self.wait_for_operation_complete()

    def cancel_shipment(self) -> None:
        """取消发货"""
        self.logger.info("取消发货")
        self.click(self.CANCEL_SHIPMENT_BUTTON)

        # 处理确认对话框
        try:
            alert = self.driver.switch_to.alert
            alert.accept()
        except:
            pass

        self.wait_for_operation_complete()

    def refund_order(self, amount: float, reason: str, custom_reason: Optional[str] = None) -> None:
        """
        退款订单

        Args:
            amount: 退款金额
            reason: 退款原因
            custom_reason: 自定义原因（如果选择了"其他"）
        """
        self.logger.info(f"退款订单 - 金额: {amount}, 原因: {reason}")

        # 输入退款金额
        self.type(self.REFUND_AMOUNT_INPUT, str(amount))

        # 选择退款原因
        reason_select = self.find_element(self.REFUND_REASON_SELECT)
        select = Select(reason_select)
        select.select_by_visible_text(reason)

        # 如果是其他原因，输入自定义原因
        if reason == "其他" and custom_reason:
            self.type(self.REFUND_REASON_INPUT, custom_reason)

        # 点击退款按钮
        self.click(self.REFUND_BUTTON)

        # 等待操作完成
        self.wait_for_operation_complete()

    def cancel_refund(self) -> None:
        """取消退款"""
        self.logger.info("取消退款")
        self.click(self.CANCEL_REFUND_BUTTON)

        # 处理确认对话框
        try:
            alert = self.driver.switch_to.alert
            alert.accept()
        except:
            pass

        self.wait_for_operation_complete()

    def edit_order_info(self, updates: Dict[str, Any]) -> None:
        """
        编辑订单信息

        Args:
            updates: 要更新的信息字典
        """
        self.logger.info(f"编辑订单信息: {updates}")

        # 点击编辑按钮
        self.click(self.EDIT_ORDER_BUTTON)

        # 等待表单加载
        self.wait_for_order_form_loaded()

        # 根据updates更新表单字段
        # 这里需要根据实际表单字段进行处理
        # 示例:
        # if 'shipping_address' in updates:
        #     shipping_address_input = (By.ID, "shipping-address-input")
        #     self.type(shipping_address_input, updates['shipping_address'])

        # 保存更改
        self.click(self.SAVE_BUTTON)

        # 等待操作完成
        self.wait_for_operation_complete()

    def cancel_order(self, reason: Optional[str] = None) -> None:
        """
        取消订单

        Args:
            reason: 取消原因
        """
        self.logger.info("取消订单")

        # 点击取消订单按钮
        self.click(self.CANCEL_ORDER_BUTTON)

        # 如果有取消原因对话框，输入原因
        if reason:
            try:
                reason_input = (By.ID, "cancel-reason")
                self.type(reason_input, reason)
            except:
                pass

        # 处理确认对话框
        try:
            alert = self.driver.switch_to.alert
            alert.accept()
        except:
            pass

        self.wait_for_operation_complete()

    def delete_order(self) -> None:
        """删除订单"""
        self.logger.info("删除订单")

        # 点击删除订单按钮
        self.click(self.DELETE_ORDER_BUTTON)

        # 处理确认对话框
        try:
            alert = self.driver.switch_to.alert
            alert.accept()
        except:
            pass

        self.wait_for_operation_complete()

    def add_order_note(self, note: str) -> None:
        """
        添加订单备注

        Args:
            note: 备注内容
        """
        self.logger.info(f"添加订单备注: {note}")

        # 点击添加备注按钮
        self.click(self.ADD_NOTE_BUTTON)

        # 输入备注内容
        self.type(self.NOTE_INPUT, note)

        # 提交备注
        submit_note_button = (By.ID, "submit-note-btn")
        self.click(submit_note_button)

        self.wait_for_operation_complete()

    def confirm_payment(self) -> None:
        """确认收款"""
        self.logger.info("确认收款")
        self.click(self.CONFIRM_PAYMENT_BUTTON)
        self.wait_for_operation_complete()

    def confirm_shipment(self) -> None:
        """确认发货"""
        self.logger.info("确认发货")
        self.click(self.CONFIRM_SHIPMENT_BUTTON)
        self.wait_for_operation_complete()

    def confirm_delivery(self) -> None:
        """确认送达"""
        self.logger.info("确认送达")
        self.click(self.CONFIRM_DELIVERY_BUTTON)
        self.wait_for_operation_complete()

    def confirm_completion(self) -> None:
        """确认完成"""
        self.logger.info("确认完成")
        self.click(self.CONFIRM_COMPLETION_BUTTON)
        self.wait_for_operation_complete()

    def print_order(self) -> None:
        """打印订单"""
        self.logger.info("打印订单")
        self.click(self.PRINT_ORDER_BUTTON)

    def export_order(self, format: str = "pdf") -> None:
        """
        导出订单

        Args:
            format: 导出格式，如 "pdf", "excel"
        """
        self.logger.info(f"导出订单，格式: {format}")
        self.click(self.EXPORT_ORDER_BUTTON)

        # 选择导出格式（如果有）
        try:
            format_select = (By.ID, "export-format")
            self.click(format_select)

            format_option = (By.XPATH, f"//option[text()='{format}']")
            self.click(format_option)

            confirm_button = (By.ID, "export-confirm")
            self.click(confirm_button)
        except:
            pass

    def back_to_list(self) -> None:
        """返回订单列表"""
        self.logger.info("返回订单列表")
        self.click(self.BACK_TO_LIST_BUTTON)

    def get_success_message(self, timeout: int = 5) -> str:
        """
        获取成功消息

        Args:
            timeout: 等待超时时间

        Returns:
            str: 成功消息文本
        """
        try:
            element = self.find_element(self.SUCCESS_MESSAGE, timeout=timeout)
            return element.text
        except:
            return ""

    def get_error_message(self, timeout: int = 5) -> str:
        """
        获取错误消息

        Args:
            timeout: 等待超时时间

        Returns:
            str: 错误消息文本
        """
        try:
            element = self.find_element(self.ERROR_MESSAGE, timeout=timeout)
            return element.text
        except:
            return ""

    def get_warning_message(self, timeout: int = 5) -> str:
        """
        获取警告消息

        Args:
            timeout: 等待超时时间

        Returns:
            str: 警告消息文本
        """
        try:
            element = self.find_element(self.WARNING_MESSAGE, timeout=timeout)
            return element.text
        except:
            return ""

    def take_order_screenshot(self, filename: Optional[str] = None) -> str:
        """
        截取订单页面截图

        Args:
            filename: 截图文件名，如果为None则自动生成

        Returns:
            str: 截图文件路径
        """
        if filename is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"order_{timestamp}.png"

        screenshot_path = self.take_screenshot(filename, "订单页面截图")
        return screenshot_path

    def verify_order_details_elements(self) -> bool:
        """
        验证订单详情页面所有关键元素是否存在

        Returns:
            bool: 如果所有关键元素都存在则返回True
        """
        self.logger.info("验证订单详情页面关键元素")

        elements_to_check = [
            ("订单号", self.ORDER_ID),
            ("订单状态", self.ORDER_STATUS),
            ("订单金额", self.TOTAL_AMOUNT),
            ("商品列表", self.ORDER_ITEMS_TABLE),
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
def create_order_operation_page(driver):
    """
    创建订单操作页面对象的快捷函数

    Args:
        driver: WebDriver实例

    Returns:
        OrderOperationPage: 订单操作页面对象实例
    """
    return OrderOperationPage(driver)


if __name__ == "__main__":
    # 测试订单操作页面类
    print("测试OrderOperationPage类...")

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

        # 创建订单操作页面对象
        order_operation_page = OrderOperationPage(driver)
        print("OrderOperationPage类导入和实例化成功")

        # 测试页面元素常量
        print(f"订单号定位器: {order_operation_page.ORDER_ID}")
        print(f"订单状态定位器: {order_operation_page.ORDER_STATUS}")
        print(f"发货按钮定位器: {order_operation_page.SHIP_BUTTON}")

        driver.quit()
        print("测试完成")

    except Exception as e:
        print(f"测试过程中出错: {e}")
        print("注意：此测试需要安装ChromeDriver")