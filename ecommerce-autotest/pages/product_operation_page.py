#!/usr/bin/env python3
"""
商品操作页面对象
实现电商后台管理系统的商品添加、编辑等操作功能
"""

import time
from typing import Optional, Tuple, List, Dict, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from pages.base_page import BasePage


class ProductOperationPage(BasePage):
    """
    商品操作页面对象类
    封装商品添加、编辑等操作的所有元素和操作
    """

    # 页面URL
    url_add = "/product/add"
    url_edit = "/product/edit"

    # 商品表单元素
    NAME_INPUT = (By.ID, "product-name")
    CATEGORY_SELECT = (By.ID, "product-category")
    PRICE_INPUT = (By.ID, "product-price")
    STOCK_INPUT = (By.ID, "product-stock")
    SKU_INPUT = (By.ID, "product-sku")
    DESCRIPTION_TEXTAREA = (By.ID, "product-description")
    STATUS_SELECT = (By.ID, "product-status")

    # 商品属性
    BRAND_INPUT = (By.ID, "product-brand")
    WEIGHT_INPUT = (By.ID, "product-weight")
    DIMENSIONS_INPUT = (By.ID, "product-dimensions")
    COLOR_SELECT = (By.ID, "product-color")
    SIZE_SELECT = (By.ID, "product-size")

    # 商品图片上传
    IMAGE_UPLOAD_INPUT = (By.ID, "product-images")
    MAIN_IMAGE_CHECKBOX = (By.ID, "main-image")
    IMAGE_PREVIEW = (By.CLASS_NAME, "image-preview")
    REMOVE_IMAGE_BUTTON = (By.CLASS_NAME, "remove-image")

    # SKU管理
    ADD_SKU_BUTTON = (By.ID, "add-sku")
    SKU_TABLE = (By.ID, "sku-table")
    SKU_ATTRIBUTES = (By.ID, "sku-attributes")

    # 商品标签
    TAGS_INPUT = (By.ID, "product-tags")
    ADD_TAG_BUTTON = (By.ID, "add-tag")
    TAGS_CONTAINER = (By.ID, "tags-container")

    # 表单按钮
    SAVE_BUTTON = (By.ID, "save-btn")
    CANCEL_BUTTON = (By.ID, "cancel-btn")
    SUBMIT_BUTTON = (By.ID, "submit-btn")
    RESET_BUTTON = (By.ID, "reset-btn")

    # 验证消息
    SUCCESS_MESSAGE = (By.CLASS_NAME, "success-message")
    ERROR_MESSAGE = (By.CLASS_NAME, "error-message")
    VALIDATION_ERROR = (By.CLASS_NAME, "validation-error")

    # 富文本编辑器
    EDITOR_TOOLBAR = (By.CLASS_NAME, "editor-toolbar")
    EDITOR_CONTENT = (By.CLASS_NAME, "editor-content")

    def __init__(self, driver):
        """
        初始化商品操作页面

        Args:
            driver: WebDriver实例
        """
        super().__init__(driver)
        self.logger.info("初始化商品操作页面对象")

    def open_add_product_page(self, base_url: Optional[str] = None) -> None:
        """
        打开添加商品页面

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

        self.logger.info(f"打开添加商品页面: {full_url}")
        self.open(full_url)
        self.wait_for_page_load()
        self.wait_for_form_loaded()

    def open_edit_product_page(self, product_id: str, base_url: Optional[str] = None) -> None:
        """
        打开编辑商品页面

        Args:
            product_id: 商品ID
            base_url: 基础URL，如果为None则使用配置中的base_url
        """
        if base_url:
            full_url = f"{base_url}{self.url_edit}/{product_id}"
        else:
            # 从配置获取base_url
            from utils.config_manager import get_config
            config = get_config()
            base_url = config.get('environment.base_url', 'http://test.ecommerce.com/admin')
            full_url = f"{base_url}{self.url_edit}/{product_id}"

        self.logger.info(f"打开编辑商品页面: {full_url}")
        self.open(full_url)
        self.wait_for_page_load()
        self.wait_for_form_loaded()

    def wait_for_form_loaded(self, timeout: int = 30) -> None:
        """
        等待表单加载完成

        Args:
            timeout: 等待超时时间
        """
        self.logger.info("等待商品表单加载完成")
        # 等待关键表单元素加载
        self.find_element(self.NAME_INPUT, timeout=timeout)
        self.find_element(self.SAVE_BUTTON, timeout=timeout)

    def enter_product_name(self, name: str) -> None:
        """
        输入商品名称

        Args:
            name: 商品名称
        """
        self.logger.info(f"输入商品名称: {name}")
        self.type(self.NAME_INPUT, name)

    def select_category(self, category: str) -> None:
        """
        选择商品分类

        Args:
            category: 分类名称
        """
        self.logger.info(f"选择商品分类: {category}")

        # 查找分类选择器
        category_select = self.find_element(self.CATEGORY_SELECT)

        # 使用Select类处理下拉选择
        select = Select(category_select)
        select.select_by_visible_text(category)

    def enter_price(self, price: float) -> None:
        """
        输入商品价格

        Args:
            price: 商品价格
        """
        self.logger.info(f"输入商品价格: {price}")
        self.type(self.PRICE_INPUT, str(price))

    def enter_stock(self, stock: int) -> None:
        """
        输入商品库存

        Args:
            stock: 商品库存
        """
        self.logger.info(f"输入商品库存: {stock}")
        self.type(self.STOCK_INPUT, str(stock))

    def enter_sku(self, sku: str) -> None:
        """
        输入商品SKU

        Args:
            sku: 商品SKU
        """
        self.logger.info(f"输入商品SKU: {sku}")
        self.type(self.SKU_INPUT, sku)

    def enter_description(self, description: str) -> None:
        """
        输入商品描述

        Args:
            description: 商品描述
        """
        self.logger.info(f"输入商品描述: {description[:50]}...")
        self.type(self.DESCRIPTION_TEXTAREA, description)

    def select_status(self, status: str) -> None:
        """
        选择商品状态

        Args:
            status: 商品状态，如 "上架", "下架"
        """
        self.logger.info(f"选择商品状态: {status}")

        # 查找状态选择器
        status_select = self.find_element(self.STATUS_SELECT)

        # 使用Select类处理下拉选择
        select = Select(status_select)
        select.select_by_visible_text(status)

    def enter_brand(self, brand: str) -> None:
        """
        输入商品品牌

        Args:
            brand: 商品品牌
        """
        self.logger.info(f"输入商品品牌: {brand}")
        self.type(self.BRAND_INPUT, brand)

    def upload_image(self, image_path: str) -> None:
        """
        上传商品图片

        Args:
            image_path: 图片文件路径
        """
        self.logger.info(f"上传商品图片: {image_path}")

        # 查找图片上传输入框
        image_input = self.find_element(self.IMAGE_UPLOAD_INPUT)

        # 设置文件路径
        image_input.send_keys(image_path)

        # 等待图片上传完成
        time.sleep(2)

    def set_main_image(self) -> None:
        """设置主图片"""
        self.logger.info("设置主图片")

        # 点击主图片复选框
        self.click(self.MAIN_IMAGE_CHECKBOX)

    def add_sku(self, sku_data: Dict[str, Any]) -> None:
        """
        添加SKU

        Args:
            sku_data: SKU数据，如 {"color": "红色", "size": "M", "price": 99.99, "stock": 50}
        """
        self.logger.info(f"添加SKU: {sku_data}")

        # 点击添加SKU按钮
        self.click(self.ADD_SKU_BUTTON)

        # 等待SKU表单加载
        time.sleep(1)

        # 填写SKU信息
        # 这里假设有动态生成的SKU表单字段
        # 实际实现需要根据页面结构调整

    def add_tag(self, tag: str) -> None:
        """
        添加商品标签

        Args:
            tag: 标签
        """
        self.logger.info(f"添加商品标签: {tag}")

        # 输入标签
        self.type(self.TAGS_INPUT, tag)

        # 点击添加标签按钮
        self.click(self.ADD_TAG_BUTTON)

    def click_save(self) -> None:
        """点击保存按钮"""
        self.logger.info("点击保存按钮")
        self.click(self.SAVE_BUTTON)

    def click_submit(self) -> None:
        """点击提交按钮"""
        self.logger.info("点击提交按钮")
        self.click(self.SUBMIT_BUTTON)

    def click_cancel(self) -> None:
        """点击取消按钮"""
        self.logger.info("点击取消按钮")
        self.click(self.CANCEL_BUTTON)

    def click_reset(self) -> None:
        """点击重置按钮"""
        self.logger.info("点击重置按钮")
        self.click(self.RESET_BUTTON)

    def fill_product_form(self, product_data: Dict[str, Any]) -> None:
        """
        填写商品表单

        Args:
            product_data: 商品数据字典
        """
        self.logger.info(f"填写商品表单: {product_data}")

        # 填写必填字段
        if 'name' in product_data:
            self.enter_product_name(product_data['name'])

        if 'category' in product_data:
            self.select_category(product_data['category'])

        if 'price' in product_data:
            self.enter_price(product_data['price'])

        if 'stock' in product_data:
            self.enter_stock(product_data['stock'])

        if 'sku' in product_data:
            self.enter_sku(product_data['sku'])

        if 'description' in product_data:
            self.enter_description(product_data['description'])

        if 'status' in product_data:
            self.select_status(product_data['status'])

        # 填写可选字段
        if 'brand' in product_data:
            self.enter_brand(product_data['brand'])

        if 'tags' in product_data:
            if isinstance(product_data['tags'], list):
                for tag in product_data['tags']:
                    self.add_tag(tag)
            elif isinstance(product_data['tags'], str):
                self.add_tag(product_data['tags'])

    def add_product(self, product_data: Dict[str, Any]) -> bool:
        """
        添加商品

        Args:
            product_data: 商品数据

        Returns:
            bool: 如果添加成功则返回True
        """
        self.logger.info(f"添加商品: {product_data}")

        # 打开添加商品页面
        self.open_add_product_page()

        # 填写表单
        self.fill_product_form(product_data)

        # 点击保存
        self.click_save()

        # 等待操作完成
        self.wait_for_operation_complete()

        # 验证是否成功
        return self.is_success_message_displayed()

    def edit_product(self, product_id: str, updates: Dict[str, Any]) -> bool:
        """
        编辑商品

        Args:
            product_id: 商品ID
            updates: 更新数据

        Returns:
            bool: 如果编辑成功则返回True
        """
        self.logger.info(f"编辑商品 {product_id}: {updates}")

        # 打开编辑商品页面
        self.open_edit_product_page(product_id)

        # 填写更新数据
        self.fill_product_form(updates)

        # 点击保存
        self.click_save()

        # 等待操作完成
        self.wait_for_operation_complete()

        # 验证是否成功
        return self.is_success_message_displayed()

    def is_success_message_displayed(self, timeout: int = 5) -> bool:
        """
        检查成功消息是否显示

        Args:
            timeout: 等待超时时间

        Returns:
            bool: 如果成功消息显示则返回True
        """
        try:
            self.find_element(self.SUCCESS_MESSAGE, timeout=timeout)
            message_text = self.get_text(self.SUCCESS_MESSAGE)
            self.logger.info(f"成功消息: {message_text}")
            return True
        except Exception:
            return False

    def is_error_message_displayed(self, timeout: int = 5) -> bool:
        """
        检查错误消息是否显示

        Args:
            timeout: 等待超时时间

        Returns:
            bool: 如果错误消息显示则返回True
        """
        try:
            self.find_element(self.ERROR_MESSAGE, timeout=timeout)
            message_text = self.get_text(self.ERROR_MESSAGE)
            self.logger.info(f"错误消息: {message_text}")
            return True
        except Exception:
            return False

    def get_validation_errors(self) -> List[str]:
        """
        获取验证错误信息

        Returns:
            List[str]: 验证错误信息列表
        """
        errors = []
        try:
            error_elements = self.find_elements(self.VALIDATION_ERROR, timeout=5)
            for element in error_elements:
                errors.append(element.text)
        except Exception:
            pass

        return errors

    def clear_product_form(self) -> None:
        """清空商品表单"""
        self.logger.info("清空商品表单")

        # 清空输入框
        fields_to_clear = [
            self.NAME_INPUT,
            self.PRICE_INPUT,
            self.STOCK_INPUT,
            self.SKU_INPUT,
            self.DESCRIPTION_TEXTAREA,
            self.BRAND_INPUT,
        ]

        for locator in fields_to_clear:
            try:
                element = self.find_element(locator, timeout=2)
                element.clear()
            except Exception:
                pass

        # 重置选择框到默认值
        try:
            category_select = Select(self.find_element(self.CATEGORY_SELECT))
            category_select.select_by_index(0)
        except Exception:
            pass

        try:
            status_select = Select(self.find_element(self.STATUS_SELECT))
            status_select.select_by_index(0)
        except Exception:
            pass

    def verify_product_form_elements(self) -> bool:
        """
        验证商品表单所有关键元素是否存在

        Returns:
            bool: 如果所有关键元素都存在则返回True
        """
        self.logger.info("验证商品表单关键元素")

        elements_to_check = [
            ("商品名称输入框", self.NAME_INPUT),
            ("分类选择器", self.CATEGORY_SELECT),
            ("价格输入框", self.PRICE_INPUT),
            ("库存输入框", self.STOCK_INPUT),
            ("保存按钮", self.SAVE_BUTTON),
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

    def take_product_form_screenshot(self, filename: Optional[str] = None) -> str:
        """
        截取商品表单页面截图

        Args:
            filename: 截图文件名，如果为None则自动生成

        Returns:
            str: 截图文件路径
        """
        if filename is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"product_form_{timestamp}.png"

        screenshot_path = self.take_screenshot(filename, "商品表单页面截图")
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

        # 等待成功/错误消息显示
        time.sleep(2)

    def get_form_data(self) -> Dict[str, Any]:
        """
        获取表单当前数据

        Returns:
            Dict[str, Any]: 表单数据字典
        """
        form_data = {}

        try:
            form_data['name'] = self.get_attribute(self.NAME_INPUT, "value")
        except Exception:
            form_data['name'] = ""

        try:
            category_select = Select(self.find_element(self.CATEGORY_SELECT))
            form_data['category'] = category_select.first_selected_option.text
        except Exception:
            form_data['category'] = ""

        try:
            form_data['price'] = self.get_attribute(self.PRICE_INPUT, "value")
        except Exception:
            form_data['price'] = ""

        try:
            form_data['stock'] = self.get_attribute(self.STOCK_INPUT, "value")
        except Exception:
            form_data['stock'] = ""

        try:
            form_data['sku'] = self.get_attribute(self.SKU_INPUT, "value")
        except Exception:
            form_data['sku'] = ""

        try:
            form_data['description'] = self.get_text(self.DESCRIPTION_TEXTAREA)
        except Exception:
            form_data['description'] = ""

        try:
            status_select = Select(self.find_element(self.STATUS_SELECT))
            form_data['status'] = status_select.first_selected_option.text
        except Exception:
            form_data['status'] = ""

        return form_data


# 快捷函数


    def fill_product_name(self, name: str) -> None:
        self.enter_product_name(name)

    def fill_product_price(self, price: float) -> None:
        self.enter_price(price)

    def fill_product_stock(self, stock: int) -> None:
        self.enter_stock(stock)

    def fill_product_description(self, description: str) -> None:
        self.enter_description(description)

    def click_save_button(self) -> None:
        self.click_save()

    def click_cancel_button(self) -> None:
        self.click_cancel()

    def get_success_message(self, timeout: int = 5) -> str:
        return self.get_text(self.SUCCESS_MESSAGE, timeout=timeout)

    def get_error_message(self, timeout: int = 5) -> str:
        return self.get_text(self.ERROR_MESSAGE, timeout=timeout)

    def fill_product_name(self, name: str) -> None:
        self.enter_product_name(name)

    def fill_product_price(self, price: float) -> None:
        self.enter_price(price)

    def fill_product_stock(self, stock: int) -> None:
        self.enter_stock(stock)

    def fill_product_description(self, description: str) -> None:
        self.enter_description(description)

    def select_category_by_id(self, category_id: int) -> None:
        category_select = Select(self.find_element(self.CATEGORY_SELECT))
        category_select.select_by_index(category_id)

    def select_product_status(self, status: str) -> None:
        self.select_status(status)

    def click_save_button(self) -> None:
        self.click_save()

    def click_cancel_button(self) -> None:
        self.click_cancel()

    def get_success_message(self, timeout: int = 5) -> str:
        return self.get_text(self.SUCCESS_MESSAGE, timeout=timeout)

    def get_error_message(self, timeout: int = 5) -> str:
        return self.get_text(self.ERROR_MESSAGE, timeout=timeout)

def create_product_operation_page(driver):
    """
    创建商品操作页面对象的快捷函数

    Args:
        driver: WebDriver实例

    Returns:
        ProductOperationPage: 商品操作页面对象实例
    """
    return ProductOperationPage(driver)


if __name__ == "__main__":
    # 测试商品操作页面类
    print("测试ProductOperationPage类...")

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

        # 创建商品操作页面对象
        product_op_page = ProductOperationPage(driver)
        print("ProductOperationPage类导入和实例化成功")

        # 测试页面元素常量
        print(f"商品名称输入框定位器: {product_op_page.NAME_INPUT}")
        print(f"价格输入框定位器: {product_op_page.PRICE_INPUT}")
        print(f"保存按钮定位器: {product_op_page.SAVE_BUTTON}")

        driver.quit()
        print("测试完成")

    except Exception as e:
        print(f"测试过程中出错: {e}")
        print("注意：此测试需要安装ChromeDriver")