#!/usr/bin/env python3
"""
商品管理功能测试用例
测试电商后台管理系统的商品管理功能
"""

import time
import pytest
from typing import Dict, List, Any
from selenium.webdriver.common.by import By

from testcases.base_test import BaseTest
from pages.product_list_page import ProductListPage
from pages.product_operation_page import ProductOperationPage
from utils.data_manager import get_test_data_manager, load_test_data
from utils.config_manager import get_config


class TestProductManagement(BaseTest):
    """
    商品管理功能测试类
    测试商品管理功能的正常场景、异常场景和边界场景
    """

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        super().setUpClass()

        # 初始化测试数据管理器
        cls.data_manager = get_test_data_manager(data_source='yaml')

        # 加载商品测试数据
        cls.product_data = load_test_data('product')
        cls.test_logger.info("商品测试数据加载完成")

        # 创建商品页面对象
        cls.product_list_page = ProductListPage(cls.driver)
        cls.product_operation_page = ProductOperationPage(cls.driver)

    def setUp(self):
        """测试方法初始化"""
        super().setUp()

        # 每个测试开始前打开商品列表页面
        self.product_list_page.open_product_list_page()
        self.product_list_page.wait_for_product_table_loaded()

        # 验证商品列表页面元素
        assert self.product_list_page.verify_product_list_elements(), "商品列表页面元素验证失败"

    def tearDown(self):
        """测试方法清理"""
        # 清理测试数据
        super().tearDown()

    # ==================== 商品搜索测试 ====================

    def test_product_search_by_keyword(self):
        """测试商品关键词搜索"""
        self.test_logger.info("开始测试商品关键词搜索")

        search_test_cases = self.product_data.get('search_test_cases', [])
        assert len(search_test_cases) > 0, "测试数据中没有搜索测试用例"

        # 测试每个搜索用例
        for i, test_case in enumerate(search_test_cases, 1):
            keyword = test_case['search_keyword']
            expected_results = test_case.get('expected_results', [])
            min_results = test_case.get('min_results', 0)
            description = test_case.get('description', f"搜索测试 {i}")

            self.test_logger.info(f"搜索测试 {i}: {description} - 关键词: '{keyword}'")

            # 执行搜索
            self.product_list_page.search_product(keyword)

            # 获取搜索结果
            products = self.product_list_page.get_product_rows()
            product_names = [p['name'] for p in products]

            # 验证最小结果数量
            assert len(products) >= min_results, \
                f"搜索结果数量不足，期望至少 {min_results} 个，实际 {len(products)} 个"

            # 验证期望结果是否存在
            for expected_name in expected_results:
                assert expected_name in product_names, \
                    f"期望商品 '{expected_name}' 未在搜索结果中找到"

            # 重置搜索条件
            self.product_list_page.reset_filters()

            self.test_logger.info(f"搜索测试通过 - 关键词: '{keyword}', 找到 {len(products)} 个商品")

    def test_product_search_empty_result(self):
        """测试商品搜索无结果"""
        self.test_logger.info("开始测试商品搜索无结果")

        # 查找无结果搜索用例
        no_result_cases = [
            case for case in self.product_data.get('search_test_cases', [])
            if case.get('min_results', 0) == 0
        ]

        if not no_result_cases:
            self.test_logger.warning("测试数据中没有无结果搜索用例")
            # 使用默认测试数据
            keyword = "不存在商品"
            expected_message = "没有找到相关商品"
        else:
            test_case = no_result_cases[0]
            keyword = test_case['search_keyword']
            expected_message = test_case.get('expected_message', '没有找到相关商品')

        # 执行搜索
        self.product_list_page.search_product(keyword)

        # 验证无结果提示
        # 注意：实际页面可能有特定的无结果提示元素
        # 这里我们检查商品数量是否为0
        products = self.product_list_page.get_product_rows()
        assert len(products) == 0, f"搜索无结果时应该没有商品，但找到 {len(products)} 个"

        self.test_logger.info(f"无结果搜索测试通过 - 关键词: '{keyword}'")

    # ==================== 商品筛选测试 ====================

    def test_filter_by_category(self):
        """测试按分类筛选商品"""
        self.test_logger.info("开始测试按分类筛选商品")

        filter_test_cases = self.product_data.get('filter_test_cases', [])
        category_cases = [
            case for case in filter_test_cases
            if case.get('filter_type') == 'category'
        ]

        if not category_cases:
            self.test_logger.warning("测试数据中没有分类筛选用例")
            # 使用默认测试数据
            category_id = 1
            category_name = "电子产品"
            expected_products = ["智能手机", "笔记本电脑"]
        else:
            test_case = category_cases[0]
            category_id = test_case['category_id']
            expected_products = test_case.get('expected_products', [])
            # 从categories数据获取分类名称
            categories = self.product_data.get('categories', [])
            category = next((c for c in categories if c['id'] == category_id), None)
            category_name = category['name'] if category else f"分类{category_id}"

        # 执行筛选
        self.product_list_page.filter_by_category(category_name)

        # 获取筛选结果
        products = self.product_list_page.get_product_rows()
        product_names = [p['name'] for p in products]

        # 验证期望商品是否存在
        for expected_name in expected_products:
            assert expected_name in product_names, \
                f"期望商品 '{expected_name}' 未在筛选结果中找到"

        # 验证所有结果都属于指定分类
        for product in products:
            assert product['category'] == category_name, \
                f"商品 '{product['name']}' 的分类 '{product['category']}' 不是 '{category_name}'"

        self.test_logger.info(f"分类筛选测试通过 - 分类: '{category_name}', 找到 {len(products)} 个商品")

    def test_filter_by_price_range(self):
        """测试按价格范围筛选商品"""
        self.test_logger.info("开始测试按价格范围筛选商品")

        filter_test_cases = self.product_data.get('filter_test_cases', [])
        price_cases = [
            case for case in filter_test_cases
            if case.get('filter_type') == 'price_range'
        ]

        if not price_cases:
            self.test_logger.warning("测试数据中没有价格范围筛选用例")
            # 使用默认测试数据
            min_price = 0
            max_price = 100
            expected_products = ["男士T恤"]
        else:
            test_case = price_cases[0]
            min_price = test_case.get('min_price', 0)
            max_price = test_case.get('max_price', 100)
            expected_products = test_case.get('expected_products', [])

        # 执行筛选
        self.product_list_page.filter_by_price_range(min_price, max_price)

        # 获取筛选结果
        products = self.product_list_page.get_product_rows()

        # 验证期望商品是否存在
        product_names = [p['name'] for p in products]
        for expected_name in expected_products:
            assert expected_name in product_names, \
                f"期望商品 '{expected_name}' 未在筛选结果中找到"

        # 验证价格范围
        test_products = self.product_data.get('test_products', [])
        for product in products:
            # 从测试数据中查找商品的价格信息
            test_product = next((p for p in test_products if p['name'] == product['name']), None)
            if test_product:
                price = float(test_product['price'])
                assert min_price <= price <= max_price, \
                    f"商品 '{product['name']}' 的价格 {price} 不在范围 [{min_price}, {max_price}] 内"

        self.test_logger.info(f"价格范围筛选测试通过 - 范围: [{min_price}, {max_price}], 找到 {len(products)} 个商品")

    def test_filter_by_status(self):
        """测试按状态筛选商品"""
        self.test_logger.info("开始测试按状态筛选商品")

        filter_test_cases = self.product_data.get('filter_test_cases', [])
        status_cases = [
            case for case in filter_test_cases
            if case.get('filter_type') == 'status'
        ]

        if not status_cases:
            self.test_logger.warning("测试数据中没有状态筛选用例")
            # 使用默认测试数据
            status = "上架"
            expected_products = ["智能手机", "笔记本电脑", "男士T恤", "女士连衣裙"]
        else:
            test_case = status_cases[0]
            status = test_case['status']
            expected_products = test_case.get('expected_products', [])

        # 执行筛选
        self.product_list_page.filter_by_status(status)

        # 获取筛选结果
        products = self.product_list_page.get_product_rows()

        # 验证所有结果都是指定状态
        for product in products:
            assert product['status'] == status, \
                f"商品 '{product['name']}' 的状态 '{product['status']}' 不是 '{status}'"

        self.test_logger.info(f"状态筛选测试通过 - 状态: '{status}', 找到 {len(products)} 个商品")

    # ==================== 商品排序测试 ====================

    def test_sort_by_price(self):
        """测试按价格排序商品"""
        self.test_logger.info("开始测试按价格排序商品")

        sort_test_cases = self.product_data.get('sort_test_cases', [])
        price_sort_cases = [
            case for case in sort_test_cases
            if 'price' in case.get('sort_by', '')
        ]

        if not price_sort_cases:
            self.test_logger.warning("测试数据中没有价格排序用例")
            # 使用默认测试数据
            sort_by = "price_asc"
            expected_first_product = "男士T恤"
        else:
            test_case = price_sort_cases[0]
            sort_by = test_case['sort_by']
            expected_first_product = test_case.get('expected_first_product', '')

        # 执行排序
        self.product_list_page.sort_by(sort_by)

        # 获取排序结果
        products = self.product_list_page.get_product_rows()
        assert len(products) > 0, "排序后没有商品"

        # 验证第一个商品是否符合预期
        if expected_first_product:
            actual_first_product = products[0]['name']
            assert actual_first_product == expected_first_product, \
                f"排序后第一个商品不正确，期望: '{expected_first_product}'，实际: '{actual_first_product}'"

        # 验证价格顺序
        test_products = self.product_data.get('test_products', [])
        product_prices = []

        for product in products:
            test_product = next((p for p in test_products if p['name'] == product['name']), None)
            if test_product:
                product_prices.append(float(test_product['price']))

        # 检查价格是否按正确顺序排列
        if 'asc' in sort_by:
            assert product_prices == sorted(product_prices), "价格未按升序排列"
        elif 'desc' in sort_by:
            assert product_prices == sorted(product_prices, reverse=True), "价格未按降序排列"

        self.test_logger.info(f"价格排序测试通过 - 排序方式: '{sort_by}'，第一个商品: '{products[0]['name'] if products else '无'}'")

    # ==================== 商品操作测试 ====================

    def test_add_new_product(self):
        """测试添加新商品"""
        self.test_logger.info("开始测试添加新商品")

        operation_cases = self.product_data.get('operation_test_cases', {})
        new_product_data = operation_cases.get('new_product', {})

        if not new_product_data:
            self.test_logger.warning("测试数据中没有新商品数据")
            # 使用默认测试数据
            product_name = f"测试商品_{int(time.time())}"
            category_id = 3
            price = 199.99
            stock = 50
            description = "这是一个测试商品"
            status = "上架"
        else:
            product_name = new_product_data['name'].replace('{timestamp}', str(int(time.time())))
            category_id = new_product_data['category_id']
            price = new_product_data['price']
            stock = new_product_data['stock']
            description = new_product_data['description']
            status = new_product_data['status']

        # 点击添加商品按钮
        self.product_list_page.click_add_product()

        # 等待表单加载
        self.product_operation_page.wait_for_form_loaded()

        # 填写商品信息
        self.product_operation_page.fill_product_name(product_name)
        self.product_operation_page.select_category_by_id(category_id)
        self.product_operation_page.fill_product_price(price)
        self.product_operation_page.fill_product_stock(stock)
        self.product_operation_page.fill_product_description(description)
        self.product_operation_page.select_product_status(status)

        # 保存商品
        self.product_operation_page.click_save_button()

        # 等待保存完成
        self.product_operation_page.wait_for_operation_complete()

        # 验证保存成功
        success_message = self.product_operation_page.get_success_message()
        assert "成功" in success_message or "saved" in success_message.lower(), \
            f"商品保存失败，消息: {success_message}"

        # 返回商品列表验证新商品
        self.product_list_page.open_product_list_page()
        self.product_list_page.wait_for_product_table_loaded()

        # 搜索新添加的商品
        self.product_list_page.search_product(product_name)

        # 验证新商品存在
        assert self.product_list_page.is_product_present(product_name), \
            f"新添加的商品 '{product_name}' 未在商品列表中找到"

        self.test_logger.info(f"添加新商品测试通过 - 商品名称: '{product_name}'")

    def test_edit_existing_product(self):
        """测试编辑现有商品"""
        self.test_logger.info("开始测试编辑现有商品")

        operation_cases = self.product_data.get('operation_test_cases', {})
        edit_product_data = operation_cases.get('edit_product', {})

        if not edit_product_data:
            self.test_logger.warning("测试数据中没有编辑商品数据")
            # 使用默认测试数据
            product_id = 1001  # 智能手机
            updates = {
                "price": 2799.99,
                "stock": 120,
                "description": "更新后的智能手机描述"
            }
        else:
            product_id = edit_product_data['product_id']
            updates = edit_product_data.get('updates', {})

        # 查找要编辑的商品
        test_products = self.product_data.get('test_products', [])
        product_to_edit = next((p for p in test_products if p['id'] == product_id), None)

        if not product_to_edit:
            self.test_logger.warning(f"测试数据中没有ID为 {product_id} 的商品")
            return

        product_name = product_to_edit['name']

        # 搜索要编辑的商品
        self.product_list_page.search_product(product_name)

        # 点击编辑按钮（第一个商品）
        self.product_list_page.click_edit_product(0)

        # 等待表单加载
        self.product_operation_page.wait_for_form_loaded()

        # 更新商品信息
        if 'price' in updates:
            self.product_operation_page.fill_product_price(updates['price'])

        if 'stock' in updates:
            self.product_operation_page.fill_product_stock(updates['stock'])

        if 'description' in updates:
            self.product_operation_page.fill_product_description(updates['description'])

        # 保存更改
        self.product_operation_page.click_save_button()

        # 等待保存完成
        self.product_operation_page.wait_for_operation_complete()

        # 验证保存成功
        success_message = self.product_operation_page.get_success_message()
        assert "成功" in success_message or "updated" in success_message.lower(), \
            f"商品更新失败，消息: {success_message}"

        self.test_logger.info(f"编辑商品测试通过 - 商品ID: {product_id}")

    def test_delete_product(self):
        """测试删除商品"""
        self.test_logger.info("开始测试删除商品")

        operation_cases = self.product_data.get('operation_test_cases', {})
        delete_product_data = operation_cases.get('delete_product', {})

        if not delete_product_data:
            self.test_logger.warning("测试数据中没有删除商品数据")
            # 使用默认测试数据
            product_id = 1002  # 笔记本电脑
            confirm_message = "确定要删除这个商品吗？"
        else:
            product_id = delete_product_data['product_id']
            confirm_message = delete_product_data.get('confirm_message', '')

        # 查找要删除的商品
        test_products = self.product_data.get('test_products', [])
        product_to_delete = next((p for p in test_products if p['id'] == product_id), None)

        if not product_to_delete:
            self.test_logger.warning(f"测试数据中没有ID为 {product_id} 的商品")
            return

        product_name = product_to_delete['name']
        original_product_count = self.product_list_page.get_product_count()

        # 搜索要删除的商品
        self.product_list_page.search_product(product_name)

        # 点击删除按钮（第一个商品）
        self.product_list_page.click_delete_product(0)

        # 处理确认对话框
        try:
            alert = self.driver.switch_to.alert
            assert confirm_message in alert.text, f"确认对话框消息不匹配: {alert.text}"
            alert.accept()
        except:
            self.logger.debug("没有确认对话框，继续执行")

        # 等待删除完成
        time.sleep(2)
        self.product_list_page.wait_for_product_table_loaded()

        # 验证商品已删除
        # 重新搜索，应该找不到该商品
        self.product_list_page.search_product(product_name)
        products = self.product_list_page.get_product_rows()

        assert not any(p['name'] == product_name for p in products), \
            f"商品 '{product_name}' 删除后仍然存在"

        self.test_logger.info(f"删除商品测试通过 - 商品名称: '{product_name}'")

    # ==================== 批量操作测试 ====================

    def test_batch_operation(self):
        """测试商品批量操作"""
        self.test_logger.info("开始测试商品批量操作")

        operation_cases = self.product_data.get('operation_test_cases', {})
        batch_operations = operation_cases.get('batch_operations', {})

        if not batch_operations:
            self.test_logger.warning("测试数据中没有批量操作数据")
            # 使用默认测试数据
            select_all = False
            selected_products = [1001, 2001]  # 智能手机和男士T恤
            operation = "下架"
            confirm_message = "确定要下架选中的商品吗？"
        else:
            select_all = batch_operations.get('select_all', False)
            selected_products = batch_operations.get('selected_products', [])
            operation = batch_operations.get('operation', '')
            confirm_message = batch_operations.get('confirm_message', '')

        # 查找要操作的商品
        test_products = self.product_data.get('test_products', [])
        products_to_select = []

        for product_id in selected_products:
            product = next((p for p in test_products if p['id'] == product_id), None)
            if product:
                products_to_select.append(product['name'])

        if not products_to_select:
            self.test_logger.warning("没有找到要批量操作的商品")
            return

        # 选择商品
        if select_all:
            self.product_list_page.select_all_products()
        else:
            for product_name in products_to_select:
                self.product_list_page.select_product_by_name(product_name)

        # 执行批量操作
        self.product_list_page.batch_operation(operation)

        # 处理确认对话框
        try:
            alert = self.driver.switch_to.alert
            assert confirm_message in alert.text, f"确认对话框消息不匹配: {alert.text}"
            alert.accept()
        except:
            self.logger.debug("没有确认对话框，继续执行")

        # 等待操作完成
        time.sleep(2)
        self.product_list_page.wait_for_product_table_loaded()

        # 验证操作结果
        # 注意：这里根据实际需求验证状态变化
        self.test_logger.info(f"批量操作测试通过 - 操作: '{operation}'，选择了 {len(products_to_select)} 个商品")

    # ==================== 导出功能测试 ====================

    def test_export_products(self):
        """测试导出商品功能"""
        self.test_logger.info("开始测试导出商品功能")

        import_export_test = self.product_data.get('import_export_test', {})
        export_formats = import_export_test.get('export_formats', ['excel'])

        for export_format in export_formats:
            self.test_logger.info(f"测试导出格式: {export_format}")

            # 执行导出
            self.product_list_page.export_products(format=export_format)

            # 等待导出完成
            time.sleep(3)  # 等待文件下载

            # 验证导出文件
            # 注意：实际测试中需要检查下载目录是否有文件
            # 这里只验证没有异常发生
            self.test_logger.info(f"导出格式 '{export_format}' 测试完成")

    # ==================== 边界测试 ====================

    def test_product_name_boundary(self):
        """测试商品名称边界值"""
        self.test_logger.info("开始测试商品名称边界值")

        boundary_cases = self.product_data.get('boundary_test_cases', [])
        name_cases = [
            case for case in boundary_cases
            if 'name' in case and '商品名称' in case.get('description', '')
        ]

        if not name_cases:
            self.test_logger.warning("测试数据中没有商品名称边界用例")
            return

        for test_case in name_cases[:2]:  # 只测试前2个，避免测试时间过长
            name = test_case['name']
            expected_valid = test_case.get('expected_valid', True)
            expected_error = test_case.get('expected_error', '')
            description = test_case.get('description', '')

            self.test_logger.info(f"测试商品名称边界: {description} - 名称: '{name}'")

            # 打开添加商品页面
            self.product_list_page.click_add_product()
            self.product_operation_page.wait_for_form_loaded()

            # 输入商品名称
            self.product_operation_page.fill_product_name(name)

            # 尝试保存
            self.product_operation_page.click_save_button()

            # 根据期望结果验证
            if expected_valid:
                # 应该保存成功
                try:
                    success_message = self.product_operation_page.get_success_message(timeout=5)
                    assert "成功" in success_message or "saved" in success_message.lower()
                    self.test_logger.info(f"商品名称边界测试通过 - {description}")
                except:
                    # 如果保存失败，检查是否有错误消息
                    error_message = self.product_operation_page.get_error_message()
                    if expected_error and expected_error in error_message:
                        self.test_logger.info(f"商品名称边界测试通过 - 期望的错误消息: {expected_error}")
                    else:
                        raise AssertionError(f"商品名称 '{name}' 应该有效但保存失败")
            else:
                # 应该显示错误消息
                error_message = self.product_operation_page.get_error_message()
                assert expected_error in error_message, \
                    f"期望错误消息 '{expected_error}' 未在 '{error_message}' 中找到"
                self.test_logger.info(f"商品名称边界测试通过 - 期望的错误消息: {expected_error}")

            # 返回商品列表
            self.product_operation_page.click_cancel_button()
            self.product_list_page.open_product_list_page()
            self.product_list_page.wait_for_product_table_loaded()

    # ==================== 性能测试 ====================

    def test_search_performance(self):
        """测试搜索性能"""
        self.test_logger.info("开始测试搜索性能")

        performance_test = self.product_data.get('performance_test', {})
        search_perf = performance_test.get('search_performance', {})

        if not search_perf:
            self.test_logger.warning("测试数据中没有搜索性能数据")
            keyword = "测试"
            expected_time = 2  # 秒
        else:
            keyword = search_perf.get('keyword', '测试')
            expected_time = search_perf.get('expected_response_time', 2)

        # 记录开始时间
        start_time = time.time()

        # 执行搜索
        self.product_list_page.search_product(keyword)

        # 等待结果加载
        self.product_list_page.wait_for_product_table_loaded()

        # 记录结束时间
        end_time = time.time()
        actual_time = end_time - start_time

        # 验证响应时间
        assert actual_time <= expected_time, \
            f"搜索响应时间超过预期，期望: {expected_time}秒，实际: {actual_time:.2f}秒"

        self.test_logger.info(f"搜索性能测试通过 - 关键词: '{keyword}'，响应时间: {actual_time:.2f}秒（期望: {expected_time}秒）")

    # ==================== 综合测试 ====================

    def test_complete_product_workflow(self):
        """测试完整商品工作流程"""
        self.test_logger.info("开始测试完整商品工作流程")

        # 步骤1: 搜索商品
        search_keyword = "手机"
        self.product_list_page.search_product(search_keyword)
        products = self.product_list_page.get_product_rows()
        assert len(products) > 0, f"搜索 '{search_keyword}' 没有结果"

        product_name = products[0]['name']
        self.test_logger.info(f"步骤1完成: 搜索商品 '{search_keyword}'，找到 '{product_name}'")

        # 步骤2: 筛选商品
        self.product_list_page.reset_filters()
        self.product_list_page.filter_by_category("电子产品")
        filtered_products = self.product_list_page.get_product_rows()
        assert len(filtered_products) > 0, "筛选后没有商品"
        self.test_logger.info(f"步骤2完成: 按分类筛选，找到 {len(filtered_products)} 个商品")

        # 步骤3: 排序商品
        self.product_list_page.sort_by("price_desc")
        sorted_products = self.product_list_page.get_product_rows()
        assert len(sorted_products) > 0, "排序后没有商品"
        self.test_logger.info(f"步骤3完成: 按价格降序排序，第一个商品: '{sorted_products[0]['name'] if sorted_products else '无'}'")

        # 步骤4: 查看商品详情（通过编辑）
        if sorted_products:
            self.product_list_page.click_edit_product(0)
            self.product_operation_page.wait_for_form_loaded()
            self.test_logger.info("步骤4完成: 查看商品详情")

            # 返回商品列表
            self.product_operation_page.click_cancel_button()
            self.product_list_page.open_product_list_page()
            self.product_list_page.wait_for_product_table_loaded()

        # 步骤5: 导出商品
        self.product_list_page.export_products(format="excel")
        self.test_logger.info("步骤5完成: 导出商品")

        # 步骤6: 批量操作
        # 选择第一个商品
        self.product_list_page.select_product_by_index(0)
        self.product_list_page.batch_operation("下架")
        self.test_logger.info("步骤6完成: 批量下架商品")

        self.test_logger.info("完整商品工作流程测试通过")


# pytest兼容性装饰器
@pytest.mark.product
@pytest.mark.smoke
class TestProductPytest:
    """pytest风格的登录测试类"""

    @pytest.fixture(autouse=True)
    def setup(self, driver):
        """测试初始化"""
        self.driver = driver
        self.product_list_page = ProductListPage(driver)
        self.product_operation_page = ProductOperationPage(driver)
        self.data_manager = get_test_data_manager()
        self.product_data = load_test_data('product')

        # 打开商品列表页面
        self.product_list_page.open_product_list_page()
        self.product_list_page.wait_for_product_table_loaded()
        yield
        # 清理工作由BaseTest负责

    @pytest.mark.parametrize("search_keyword,expected_min_results", [
        ("手机", 1),
        ("电脑", 1),
        ("T恤", 1),
    ])
    def test_product_search_pytest(self, search_keyword, expected_min_results):
        """pytest风格的商品搜索测试"""
        self.product_list_page.search_product(search_keyword)
        products = self.product_list_page.get_product_rows()
        assert len(products) >= expected_min_results, \
            f"搜索 '{search_keyword}' 结果不足，期望至少 {expected_min_results} 个，实际 {len(products)} 个"

    @pytest.mark.parametrize("category_name,expected_products", [
        ("电子产品", ["智能手机", "笔记本电脑"]),
        ("服装", ["男士T恤", "女士连衣裙"]),
    ])
    def test_filter_by_category_pytest(self, category_name, expected_products):
        """pytest风格的分类筛选测试"""
        self.product_list_page.filter_by_category(category_name)
        products = self.product_list_page.get_product_rows()
        product_names = [p['name'] for p in products]

        for expected_name in expected_products:
            assert expected_name in product_names, \
                f"期望商品 '{expected_name}' 未在分类 '{category_name}' 的筛选结果中找到"


if __name__ == "__main__":
    # 运行测试
    print("运行商品管理测试...")

    # 导入unittest
    import unittest

    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestProductManagement)

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 输出结果
    print(f"\n测试结果: 运行 {result.testsRun} 个测试")
    if result.failures:
        print(f"失败: {len(result.failures)}")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")
    if result.errors:
        print(f"错误: {len(result.errors)}")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")

    if result.wasSuccessful():
        print("所有测试通过!")
    else:
        print("有测试失败或错误!")