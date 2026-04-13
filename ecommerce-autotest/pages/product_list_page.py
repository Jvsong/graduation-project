#!/usr/bin/env python3
"""
商品列表页面对象
实现电商后台管理系统的商品列表功能页面操作
"""

import time
from typing import Optional, Tuple, List, Dict, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from pages.base_page import BasePage


class ProductListPage(BasePage):
    """
    商品列表页面对象类
    封装商品列表页面的所有元素和操作
    """

    # 页面URL
    url = "/admin/products"

    # 页面元素定位器 - 根据config/testdata/product.yaml配置
    # 商品列表页面元素
    SEARCH_INPUT = (By.ID, "search-input")
    SEARCH_BUTTON = (By.ID, "search-btn")
    CATEGORY_FILTER = (By.ID, "category-filter")
    PRICE_FILTER = (By.ID, "price-filter")
    STATUS_FILTER = (By.ID, "status-filter")
    PRODUCT_TABLE = (By.ID, "product-table")
    ADD_PRODUCT_BUTTON = (By.ID, "add-product-btn")
    BATCH_OPERATION_BUTTON = (By.ID, "batch-operation-btn")
    EXPORT_BUTTON = (By.ID, "export-btn")

    # 商品表格相关元素
    TABLE_ROWS = (By.CSS_SELECTOR, "#product-table tbody tr")
    TABLE_HEADERS = (By.CSS_SELECTOR, "#product-table thead th")
    SELECT_ALL_CHECKBOX = (By.ID, "select-all")
    PRODUCT_CHECKBOX = (By.CSS_SELECTOR, ".product-checkbox")
    EDIT_BUTTON = (By.CSS_SELECTOR, ".edit-btn")
    DELETE_BUTTON = (By.CSS_SELECTOR, ".delete-btn")

    # 分页元素
    PAGINATION = (By.CLASS_NAME, "pagination")
    PAGE_NEXT = (By.CLASS_NAME, "page-next")
    PAGE_PREV = (By.CLASS_NAME, "page-prev")
    PAGE_NUMBER = (By.CLASS_NAME, "page-number")
    CURRENT_PAGE = (By.CLASS_NAME, "current-page")

    # 排序元素
    SORT_BY_NAME = (By.ID, "sort-by-name")
    SORT_BY_PRICE = (By.ID, "sort-by-price")
    SORT_BY_STOCK = (By.ID, "sort-by-stock")
    SORT_BY_DATE = (By.ID, "sort-by-date")

    # 筛选器元素
    FILTER_APPLY_BUTTON = (By.ID, "filter-apply")
    FILTER_RESET_BUTTON = (By.ID, "filter-reset")

    def __init__(self, driver):
        """
        初始化商品列表页面

        Args:
            driver: WebDriver实例
        """
        super().__init__(driver)
        self.logger.info("初始化商品列表页面对象")

    def open_product_list_page(self, base_url: Optional[str] = None) -> None:
        """
        打开商品列表页面

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

        self.logger.info(f"打开商品列表页面: {full_url}")
        self.open(full_url)
        self.wait_for_page_load()
        self.wait_for_product_table_loaded()

    def wait_for_product_table_loaded(self, timeout: int = 30) -> None:
        """
        等待商品表格加载完成

        Args:
            timeout: 等待超时时间
        """
        self.logger.info("等待商品表格加载完成")
        self.find_element(self.PRODUCT_TABLE, timeout=timeout)
        # 等待至少一行数据加载（如果有数据的话）
        try:
            rows = self.find_elements(self.TABLE_ROWS, timeout=5)
            if rows:
                self.logger.info(f"商品表格加载完成，找到 {len(rows)} 行数据")
        except Exception:
            self.logger.info("商品表格已加载，可能没有数据")

    def search_product(self, keyword: str) -> None:
        """
        搜索商品

        Args:
            keyword: 搜索关键词
        """
        self.logger.info(f"搜索商品: {keyword}")

        # 输入搜索关键词
        self.type(self.SEARCH_INPUT, keyword)

        # 点击搜索按钮
        self.click(self.SEARCH_BUTTON)

        # 等待搜索结果
        time.sleep(1)
        self.wait_for_product_table_loaded()

    def filter_by_category(self, category: str) -> None:
        """
        按分类筛选商品

        Args:
            category: 分类名称
        """
        self.logger.info(f"按分类筛选商品: {category}")

        # 查找分类筛选器
        category_filter = self.find_element(self.CATEGORY_FILTER)

        # 使用Select类处理下拉选择
        select = Select(category_filter)
        select.select_by_visible_text(category)

        # 应用筛选
        self.click(self.FILTER_APPLY_BUTTON)

        # 等待筛选结果
        time.sleep(1)
        self.wait_for_product_table_loaded()

    def filter_by_price_range(self, min_price: Optional[float] = None,
                              max_price: Optional[float] = None) -> None:
        """
        按价格范围筛选商品

        Args:
            min_price: 最低价格
            max_price: 最高价格
        """
        self.logger.info(f"按价格范围筛选商品: {min_price} - {max_price}")

        # 查找价格筛选器
        price_filter = self.find_element(self.PRICE_FILTER)

        # 输入价格范围
        # 注意：实际页面可能有多个输入框，这里简化处理
        if min_price is not None:
            min_input = (By.ID, "price-min")
            self.type(min_input, str(min_price))

        if max_price is not None:
            max_input = (By.ID, "price-max")
            self.type(max_input, str(max_price))

        # 应用筛选
        self.click(self.FILTER_APPLY_BUTTON)

        # 等待筛选结果
        time.sleep(1)
        self.wait_for_product_table_loaded()

    def filter_by_status(self, status: str) -> None:
        """
        按状态筛选商品

        Args:
            status: 状态，如 "上架", "下架"
        """
        self.logger.info(f"按状态筛选商品: {status}")

        # 查找状态筛选器
        status_filter = self.find_element(self.STATUS_FILTER)

        # 使用Select类处理下拉选择
        select = Select(status_filter)
        select.select_by_visible_text(status)

        # 应用筛选
        self.click(self.FILTER_APPLY_BUTTON)

        # 等待筛选结果
        time.sleep(1)
        self.wait_for_product_table_loaded()

    def sort_by(self, sort_option: str) -> None:
        """
        排序商品

        Args:
            sort_option: 排序选项，如 "price_asc", "price_desc", "name_asc", "name_desc"
        """
        self.logger.info(f"排序商品: {sort_option}")

        # 根据排序选项选择对应的排序元素
        sort_locators = {
            "name_asc": self.SORT_BY_NAME,
            "name_desc": self.SORT_BY_NAME,  # 可能需要点击两次
            "price_asc": self.SORT_BY_PRICE,
            "price_desc": self.SORT_BY_PRICE,
            "stock_asc": self.SORT_BY_STOCK,
            "stock_desc": self.SORT_BY_STOCK,
            "date_asc": self.SORT_BY_DATE,
            "date_desc": self.SORT_BY_DATE,
        }

        if sort_option in sort_locators:
            sort_locator = sort_locators[sort_option]
            self.click(sort_locator)

            # 等待排序完成
            time.sleep(1)
            self.wait_for_product_table_loaded()
        else:
            self.logger.warning(f"不支持的排序选项: {sort_option}")

    def get_product_count(self) -> int:
        """
        获取商品数量

        Returns:
            int: 商品数量
        """
        rows = self.find_elements(self.TABLE_ROWS, timeout=5)
        count = len(rows)
        self.logger.debug(f"商品数量: {count}")
        return count

    def get_product_rows(self) -> List[Dict[str, Any]]:
        """
        ???????
        Returns:
            List[Dict[str, Any]]: ???????
        """
        rows = self.find_elements(self.TABLE_ROWS, timeout=5)
        products = []

        for i, row in enumerate(rows):
            try:
                empty_cells = row.find_elements(By.CSS_SELECTOR, 'td.empty-cell')
                if empty_cells:
                    continue

                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) < 6:
                    continue

                name = ""
                description = ""
                name_elements = row.find_elements(By.CSS_SELECTOR, '.product-name')
                desc_elements = row.find_elements(By.CSS_SELECTOR, '.product-desc')
                if name_elements:
                    name = name_elements[0].text.strip()
                elif len(cells) > 1:
                    name = cells[1].text.splitlines()[0].strip()

                if desc_elements:
                    description = desc_elements[0].text.strip()
                elif len(cells) > 1:
                    lines = [line.strip() for line in cells[1].text.splitlines() if line.strip()]
                    if len(lines) > 1:
                        description = lines[1]

                product_data = {
                    "row_index": i,
                    "name": name,
                    "description": description,
                    "category": cells[2].text.strip() if len(cells) > 2 else "",
                    "price": cells[3].text.strip() if len(cells) > 3 else "",
                    "stock": cells[4].text.strip() if len(cells) > 4 else "",
                    "status": cells[5].text.strip() if len(cells) > 5 else "",
                }

                if product_data['name']:
                    products.append(product_data)

            except Exception as e:
                self.logger.warning(f"???{i} ???????: {e}")

        self.logger.debug(f"???{len(products)} ?????")
        return products

    def select_product_by_index(self, index: int) -> None:
        """
        通过索引选择商品

        Args:
            index: 商品行索引（从0开始）
        """
        self.logger.info(f"选择第 {index} 个商品")

        rows = self.find_elements(self.TABLE_ROWS, timeout=5)
        if index < len(rows):
            checkbox = rows[index].find_element(By.CSS_SELECTOR, ".product-checkbox")
            checkbox.click()
        else:
            raise IndexError(f"商品索引超出范围: {index}，总共 {len(rows)} 个商品")

    def select_product_by_name(self, product_name: str) -> bool:
        """
        通过商品名称选择商品

        Args:
            product_name: 商品名称

        Returns:
            bool: 如果找到并选择了商品则返回True
        """
        self.logger.info(f"选择商品: {product_name}")

        products = self.get_product_rows()
        for i, product in enumerate(products):
            if product["name"] == product_name:
                self.select_product_by_index(i)
                return True

        self.logger.warning(f"未找到商品: {product_name}")
        return False

    def select_all_products(self) -> None:
        """选择所有商品"""
        self.logger.info("选择所有商品")
        self.click(self.SELECT_ALL_CHECKBOX)

    def click_add_product(self) -> None:
        """点击添加商品按钮"""
        self.logger.info("点击添加商品按钮")
        self.click(self.ADD_PRODUCT_BUTTON)

    def click_edit_product(self, index: int) -> None:
        """
        点击编辑商品按钮

        Args:
            index: 商品行索引
        """
        self.logger.info(f"点击编辑第 {index} 个商品")

        rows = self.find_elements(self.TABLE_ROWS, timeout=5)
        if index < len(rows):
            edit_button = rows[index].find_element(By.CSS_SELECTOR, ".edit-btn")
            edit_button.click()
        else:
            raise IndexError(f"商品索引超出范围: {index}")

    def click_delete_product(self, index: int) -> None:
        """
        点击删除商品按钮

        Args:
            index: 商品行索引
        """
        self.logger.info(f"点击删除第 {index} 个商品")

        rows = self.find_elements(self.TABLE_ROWS, timeout=5)
        if index < len(rows):
            delete_button = rows[index].find_element(By.CSS_SELECTOR, ".delete-btn")
            delete_button.click()
        else:
            raise IndexError(f"商品索引超出范围: {index}")

    def batch_operation(self, operation: str) -> None:
        """
        批量操作

        Args:
            operation: 操作类型，如 "上架", "下架", "删除"
        """
        self.logger.info(f"批量操作: {operation}")

        # 这里是原生 select，直接点击 option 容易卡在等待或被浏览器拦截
        operation_select = Select(self.find_element((By.ID, "batch-operation-select")))
        operation_select.select_by_visible_text(operation)

        # 点击批量操作按钮
        self.click(self.BATCH_OPERATION_BUTTON)

    def export_products(self, format: str = "excel") -> None:
        """
        导出商品

        Args:
            format: 导出格式，如 "excel", "csv", "pdf"
        """
        self.logger.info(f"导出商品，格式: {format}")

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

    def reset_filters(self) -> None:
        """重置筛选器"""
        self.logger.info("重置筛选器")
        self.click(self.FILTER_RESET_BUTTON)
        self.wait_for_product_table_loaded()

    def go_to_next_page(self) -> None:
        """转到下一页"""
        self.logger.info("转到下一页")
        self.click(self.PAGE_NEXT)
        self.wait_for_product_table_loaded()

    def go_to_previous_page(self) -> None:
        """转到上一页"""
        self.logger.info("转到上一页")
        self.click(self.PAGE_PREV)
        self.wait_for_product_table_loaded()

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
            self.wait_for_product_table_loaded()
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

    def is_product_present(self, product_name: str) -> bool:
        """
        检查商品是否存在

        Args:
            product_name: 商品名称

        Returns:
            bool: 如果商品存在则返回True
        """
        products = self.get_product_rows()
        for product in products:
            if product["name"] == product_name:
                return True
        return False

    def verify_product_list_elements(self) -> bool:
        """
        验证商品列表页面所有关键元素是否存在

        Returns:
            bool: 如果所有关键元素都存在则返回True
        """
        self.logger.info("验证商品列表页面关键元素")

        elements_to_check = [
            ("搜索输入框", self.SEARCH_INPUT),
            ("搜索按钮", self.SEARCH_BUTTON),
            ("商品表格", self.PRODUCT_TABLE),
            ("添加商品按钮", self.ADD_PRODUCT_BUTTON),
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

    def take_product_list_screenshot(self, filename: Optional[str] = None) -> str:
        """
        截取商品列表页面截图

        Args:
            filename: 截图文件名，如果为None则自动生成

        Returns:
            str: 截图文件路径
        """
        if filename is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"product_list_{timestamp}.png"

        screenshot_path = self.take_screenshot(filename, "商品列表页面截图")
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
def create_product_list_page(driver):
    """
    创建商品列表页面对象的快捷函数

    Args:
        driver: WebDriver实例

    Returns:
        ProductListPage: 商品列表页面对象实例
    """
    return ProductListPage(driver)


if __name__ == "__main__":
    # 测试商品列表页面类
    print("测试ProductListPage类...")

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

        # 创建商品列表页面对象
        product_list_page = ProductListPage(driver)
        print("ProductListPage类导入和实例化成功")

        # 测试页面元素常量
        print(f"搜索输入框定位器: {product_list_page.SEARCH_INPUT}")
        print(f"商品表格定位器: {product_list_page.PRODUCT_TABLE}")
        print(f"添加商品按钮定位器: {product_list_page.ADD_PRODUCT_BUTTON}")

        driver.quit()
        print("测试完成")

    except Exception as e:
        print(f"测试过程中出错: {e}")
        print("注意：此测试需要安装ChromeDriver")
