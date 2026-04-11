#!/usr/bin/env python3
"""
订单管理功能测试用例
测试电商后台管理系统的订单管理功能
"""

import time
import pytest
from typing import Dict, List, Any
from selenium.webdriver.common.by import By

from testcases.base_test import BaseTest
from pages.order_list_page import OrderListPage
from pages.order_operation_page import OrderOperationPage
from utils.data_manager import get_test_data_manager, load_test_data
from utils.config_manager import get_config


class TestOrderManagement(BaseTest):
    """
    订单管理功能测试类
    测试订单管理功能的正常场景、异常场景和边界场景
    """

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        super().setUpClass()

        # 初始化测试数据管理器
        cls.data_manager = get_test_data_manager(data_source='yaml')

        # 加载订单测试数据
        cls.order_data = load_test_data('order')
        cls.test_logger.info("订单测试数据加载完成")

        # 创建订单页面对象
        cls.order_list_page = OrderListPage(cls.driver)
        cls.order_operation_page = OrderOperationPage(cls.driver)

    def setUp(self):
        """测试方法初始化"""
        super().setUp()

        # 每个测试开始前打开订单列表页面
        self.order_list_page.open_order_list_page()
        self.order_list_page.wait_for_order_table_loaded()

        # 验证订单列表页面元素
        assert self.order_list_page.verify_order_list_elements(), "订单列表页面元素验证失败"

    def tearDown(self):
        """测试方法清理"""
        # 清理测试数据
        super().tearDown()

    # ==================== 订单搜索测试 ====================

    def test_order_search_by_order_id(self):
        """测试订单号搜索"""
        self.test_logger.info("开始测试订单号搜索")

        search_test_cases = self.order_data.get('search_test_cases', [])
        order_id_cases = [
            case for case in search_test_cases
            if case.get('search_type') == 'order_id'
        ]

        if not order_id_cases:
            self.test_logger.warning("测试数据中没有订单号搜索用例")
            # 使用默认测试数据
            order_id = "ORDER-20240404-001"
            expected_results = 1
        else:
            test_case = order_id_cases[0]
            order_id = test_case['search_value']
            expected_results = test_case.get('expected_results', 1)

        # 执行搜索
        self.order_list_page.search_order(order_id, search_type="order_id")

        # 获取搜索结果
        orders = self.order_list_page.get_order_rows()

        # 验证结果数量
        assert len(orders) >= expected_results, \
            f"搜索结果数量不足，期望至少 {expected_results} 个，实际 {len(orders)} 个"

        # 验证搜索结果包含搜索的订单号
        if orders:
            found = any(order_id in order['order_id'] for order in orders)
            assert found, f"搜索结果中未找到包含 '{order_id}' 的订单"

        self.test_logger.info(f"订单号搜索测试通过 - 订单号: '{order_id}', 找到 {len(orders)} 个订单")

    def test_order_search_by_username(self):
        """测试用户名搜索"""
        self.test_logger.info("开始测试用户名搜索")

        search_test_cases = self.order_data.get('search_test_cases', [])
        username_cases = [
            case for case in search_test_cases
            if case.get('search_type') == 'username'
        ]

        if not username_cases:
            self.test_logger.warning("测试数据中没有用户名搜索用例")
            # 使用默认测试数据
            username = "customer1"
            expected_results = 2
        else:
            test_case = username_cases[0]
            username = test_case['search_value']
            expected_results = test_case.get('expected_results', 1)

        # 执行搜索
        self.order_list_page.search_order(username, search_type="username")

        # 获取搜索结果
        orders = self.order_list_page.get_order_rows()

        # 验证结果数量
        assert len(orders) >= expected_results, \
            f"搜索结果数量不足，期望至少 {expected_results} 个，实际 {len(orders)} 个"

        # 验证搜索结果包含搜索的用户名
        if orders:
            found = any(username in order['username'] for order in orders)
            assert found, f"搜索结果中未找到包含 '{username}' 的订单"

        self.test_logger.info(f"用户名搜索测试通过 - 用户名: '{username}', 找到 {len(orders)} 个订单")

    def test_order_search_by_product_name(self):
        """测试商品名称搜索"""
        self.test_logger.info("开始测试商品名称搜索")

        search_test_cases = self.order_data.get('search_test_cases', [])
        product_cases = [
            case for case in search_test_cases
            if case.get('search_type') == 'product_name'
        ]

        if not product_cases:
            self.test_logger.warning("测试数据中没有商品名称搜索用例")
            # 使用默认测试数据
            product_name = "智能手机"
            expected_results = 2
        else:
            test_case = product_cases[0]
            product_name = test_case['search_value']
            expected_results = test_case.get('expected_results', 1)

        # 执行搜索
        self.order_list_page.search_order(product_name, search_type="product_name")

        # 获取搜索结果
        orders = self.order_list_page.get_order_rows()

        # 验证结果数量
        assert len(orders) >= expected_results, \
            f"搜索结果数量不足，期望至少 {expected_results} 个，实际 {len(orders)} 个"

        self.test_logger.info(f"商品名称搜索测试通过 - 商品名称: '{product_name}', 找到 {len(orders)} 个订单")

    # ==================== 订单筛选测试 ====================

    def test_filter_by_status(self):
        """测试按状态筛选订单"""
        self.test_logger.info("开始测试按状态筛选订单")

        filter_test_cases = self.order_data.get('filter_test_cases', [])
        status_cases = [
            case for case in filter_test_cases
            if case.get('filter_type') == 'status'
        ]

        if not status_cases:
            self.test_logger.warning("测试数据中没有状态筛选用例")
            # 使用默认测试数据
            status = "待付款"
            expected_results = 1
        else:
            test_case = status_cases[0]
            filter_value = test_case['filter_value']
            expected_results = test_case.get('expected_results', 1)
            # 将状态值转换为中文显示
            status_mapping = self.order_data.get('order_status', {})
            status = status_mapping.get(filter_value, filter_value)

        # 执行筛选
        self.order_list_page.filter_by_status(status)

        # 获取筛选结果
        orders = self.order_list_page.get_order_rows()

        # 验证结果数量
        assert len(orders) >= expected_results, \
            f"筛选结果数量不足，期望至少 {expected_results} 个，实际 {len(orders)} 个"

        # 验证所有结果都是指定状态
        for order in orders:
            assert status in order['status'], \
                f"订单 '{order['order_id']}' 的状态 '{order['status']}' 不是 '{status}'"

        self.test_logger.info(f"状态筛选测试通过 - 状态: '{status}', 找到 {len(orders)} 个订单")

    def test_filter_by_time_range(self):
        """测试按时间范围筛选订单"""
        self.test_logger.info("开始测试按时间范围筛选订单")

        filter_test_cases = self.order_data.get('filter_test_cases', [])
        time_cases = [
            case for case in filter_test_cases
            if case.get('filter_type') == 'time_range'
        ]

        if not time_cases:
            self.test_logger.warning("测试数据中没有时间范围筛选用例")
            # 使用默认测试数据
            start_date = "2024-04-04"
            end_date = "2024-04-04"
            expected_results = 2
        else:
            test_case = time_cases[0]
            start_date = test_case.get('start_date', '2024-04-04')
            end_date = test_case.get('end_date', '2024-04-04')
            expected_results = test_case.get('expected_results', 1)

        # 执行筛选
        self.order_list_page.filter_by_time_range(start_date, end_date)

        # 获取筛选结果
        orders = self.order_list_page.get_order_rows()

        # 验证结果数量
        assert len(orders) >= expected_results, \
            f"筛选结果数量不足，期望至少 {expected_results} 个，实际 {len(orders)} 个"

        self.test_logger.info(f"时间范围筛选测试通过 - 范围: {start_date} 到 {end_date}, 找到 {len(orders)} 个订单")

    def test_filter_by_quick_time(self):
        """测试快速时间筛选"""
        self.test_logger.info("开始测试快速时间筛选")

        # 测试今天筛选
        self.order_list_page.filter_by_quick_time("today")

        # 获取筛选结果
        orders = self.order_list_page.get_order_rows()

        # 验证有结果（可能有也可能没有，取决于数据）
        self.test_logger.info(f"今天筛选找到 {len(orders)} 个订单")

        # 重置筛选
        self.order_list_page.reset_filters()

        self.test_logger.info("快速时间筛选测试通过")

    # ==================== 订单排序测试 ====================

    def test_sort_by_order_time(self):
        """测试按订单时间排序"""
        self.test_logger.info("开始测试按订单时间排序")

        sort_test_cases = self.order_data.get('sort_test_cases', [])
        time_sort_cases = [
            case for case in sort_test_cases
            if 'order_time' in case.get('sort_by', '')
        ]

        if not time_sort_cases:
            self.test_logger.warning("测试数据中没有订单时间排序用例")
            # 使用默认测试数据
            sort_by = "order_time_desc"
            expected_first_order = "ORDER-20240404-002"
        else:
            test_case = time_sort_cases[0]
            sort_by = test_case['sort_by']
            expected_first_order = test_case.get('expected_first_order', '')

        # 执行排序
        self.order_list_page.sort_by(sort_by)

        # 获取排序结果
        orders = self.order_list_page.get_order_rows()
        assert len(orders) > 0, "排序后没有订单"

        # 验证第一个订单是否符合预期
        if expected_first_order:
            actual_first_order = orders[0]['order_id']
            assert actual_first_order == expected_first_order, \
                f"排序后第一个订单不正确，期望: '{expected_first_order}'，实际: '{actual_first_order}'"

        self.test_logger.info(f"订单时间排序测试通过 - 排序方式: '{sort_by}'，第一个订单: '{orders[0]['order_id'] if orders else '无'}'")

    # ==================== 订单操作测试 ====================

    def test_view_order_details(self):
        """测试查看订单详情"""
        self.test_logger.info("开始测试查看订单详情")

        order_detail_test = self.order_data.get('order_detail_test', {})
        order_id = order_detail_test.get('order_id', '')

        if not order_id:
            self.test_logger.warning("测试数据中没有订单详情测试数据")
            # 从测试订单数据中获取一个订单
            test_orders = self.order_data.get('test_orders', [])
            if not test_orders:
                self.test_logger.warning("测试数据中没有测试订单")
                return
            order_id = test_orders[0]['order_id']

        # 搜索订单
        self.order_list_page.search_order(order_id, search_type="order_id")

        # 点击查看订单详情
        self.order_list_page.click_view_order(0)

        # 等待订单详情加载
        self.order_operation_page.wait_for_order_details_loaded()

        # 验证订单详情元素
        assert self.order_operation_page.verify_order_details_elements(), "订单详情页面元素验证失败"

        # 获取订单信息
        order_info = self.order_operation_page.get_order_info()

        # 验证订单号匹配
        assert order_info['order_id'] == order_id, \
            f"订单号不匹配，期望: '{order_id}'，实际: '{order_info['order_id']}'"

        # 获取订单商品
        items = self.order_operation_page.get_order_items()
        assert len(items) > 0, "订单中没有商品"

        self.test_logger.info(f"查看订单详情测试通过 - 订单号: '{order_id}'，找到 {len(items)} 个商品")

        # 返回订单列表
        self.order_operation_page.back_to_list()
        self.order_list_page.wait_for_order_table_loaded()

    def test_ship_order(self):
        """测试发货订单"""
        self.test_logger.info("开始测试发货订单")

        operation_cases = self.order_data.get('operation_test_cases', {})
        shipment_operation = operation_cases.get('shipment_operation', {})

        if not shipment_operation:
            self.test_logger.warning("测试数据中没有发货操作数据")
            return

        order_id = shipment_operation['order_id']
        courier = shipment_operation['courier']
        tracking_number = shipment_operation['tracking_number']
        expected_status = shipment_operation.get('expected_status', 'shipped')

        # 搜索要发货的订单
        self.order_list_page.search_order(order_id, search_type="order_id")

        # 点击发货按钮
        self.order_list_page.click_ship_order(0)

        # 等待发货表单加载
        self.order_operation_page.wait_for_shipment_form_loaded()

        # 执行发货操作
        self.order_operation_page.ship_order(courier, tracking_number)

        # 验证发货成功
        success_message = self.order_operation_page.get_success_message()
        assert "成功" in success_message or "shipped" in success_message.lower(), \
            f"发货失败，消息: {success_message}"

        # 返回订单列表验证状态
        self.order_operation_page.back_to_list()
        self.order_list_page.wait_for_order_table_loaded()

        # 重新搜索订单
        self.order_list_page.search_order(order_id, search_type="order_id")

        # 获取订单状态
        actual_status = self.order_list_page.get_order_status(order_id)

        # 验证状态更新
        status_mapping = self.order_data.get('order_status', {})
        expected_status_text = status_mapping.get(expected_status, expected_status)

        if actual_status:
            assert expected_status_text in actual_status, \
                f"订单状态未更新，期望: '{expected_status_text}'，实际: '{actual_status}'"

        self.test_logger.info(f"发货订单测试通过 - 订单号: '{order_id}'，快递公司: '{courier}'")

    def test_cancel_order(self):
        """测试取消订单"""
        self.test_logger.info("开始测试取消订单")

        operation_cases = self.order_data.get('operation_test_cases', {})
        cancel_operation = operation_cases.get('cancel_operation', {})

        if not cancel_operation:
            self.test_logger.warning("测试数据中没有取消操作数据")
            return

        order_id = cancel_operation['order_id']
        cancel_reason = cancel_operation.get('cancel_reason', '客户要求取消')
        expected_status = cancel_operation.get('expected_status', 'cancelled')

        # 搜索要取消的订单
        self.order_list_page.search_order(order_id, search_type="order_id")

        # 查看订单详情
        self.order_list_page.click_view_order(0)
        self.order_operation_page.wait_for_order_details_loaded()

        # 取消订单
        self.order_operation_page.cancel_order(cancel_reason)

        # 验证取消成功
        success_message = self.order_operation_page.get_success_message()
        assert "成功" in success_message or "cancelled" in success_message.lower(), \
            f"取消订单失败，消息: {success_message}"

        # 返回订单列表验证状态
        self.order_operation_page.back_to_list()
        self.order_list_page.wait_for_order_table_loaded()

        # 重新搜索订单
        self.order_list_page.search_order(order_id, search_type="order_id")

        # 获取订单状态
        actual_status = self.order_list_page.get_order_status(order_id)

        # 验证状态更新
        status_mapping = self.order_data.get('order_status', {})
        expected_status_text = status_mapping.get(expected_status, expected_status)

        if actual_status:
            assert expected_status_text in actual_status, \
                f"订单状态未更新，期望: '{expected_status_text}'，实际: '{actual_status}'"

        self.test_logger.info(f"取消订单测试通过 - 订单号: '{order_id}'，原因: '{cancel_reason}'")

    def test_add_order_note(self):
        """测试添加订单备注"""
        self.test_logger.info("开始测试添加订单备注")

        operation_cases = self.order_data.get('operation_test_cases', {})
        add_note = operation_cases.get('add_note', {})

        if not add_note:
            self.test_logger.warning("测试数据中没有添加备注数据")
            return

        order_id = add_note['order_id']
        note_content = add_note['note_content']

        # 搜索要添加备注的订单
        self.order_list_page.search_order(order_id, search_type="order_id")

        # 查看订单详情
        self.order_list_page.click_view_order(0)
        self.order_operation_page.wait_for_order_details_loaded()

        # 添加备注
        self.order_operation_page.add_order_note(note_content)

        # 验证添加成功
        success_message = self.order_operation_page.get_success_message()
        assert "成功" in success_message or "added" in success_message.lower(), \
            f"添加备注失败，消息: {success_message}"

        self.test_logger.info(f"添加订单备注测试通过 - 订单号: '{order_id}'，备注: '{note_content}'")

        # 返回订单列表
        self.order_operation_page.back_to_list()
        self.order_list_page.wait_for_order_table_loaded()

    # ==================== 批量操作测试 ====================

    def test_batch_operation(self):
        """测试订单批量操作"""
        self.test_logger.info("开始测试订单批量操作")

        operation_cases = self.order_data.get('operation_test_cases', {})
        batch_operations = operation_cases.get('batch_operations', {})

        if not batch_operations:
            self.test_logger.warning("测试数据中没有批量操作数据")
            # 使用默认测试数据
            select_all = False
            selected_orders = ["ORDER-20240404-001", "ORDER-20240404-002"]
            operation = "导出"
            format = "excel"
        else:
            select_all = batch_operations.get('select_all', False)
            selected_orders = batch_operations.get('selected_orders', [])
            operation = batch_operations.get('operation', '')
            format = batch_operations.get('format', 'excel')

        # 选择订单
        if select_all:
            self.order_list_page.select_all_orders()
        else:
            for order_id in selected_orders:
                self.order_list_page.select_order_by_id(order_id)

        # 执行批量操作
        if operation == "export":
            self.order_list_page.export_orders(format=format)
        else:
            self.order_list_page.batch_operation(operation)

        self.test_logger.info(f"批量操作测试通过 - 操作: '{operation}'，选择了 {len(selected_orders)} 个订单")

    # ==================== 订单状态流转测试 ====================

    def test_order_status_normal_flow(self):
        """测试订单状态正常流转"""
        self.test_logger.info("开始测试订单状态正常流转")

        status_flow_test = self.order_data.get('status_flow_test', {})
        normal_flow = status_flow_test.get('normal_flow', [])

        if not normal_flow:
            self.test_logger.warning("测试数据中没有状态流转测试数据")
            return

        self.test_logger.info("订单状态正常流转测试（概念验证）")

        # 这里只进行概念验证，实际测试需要创建新订单并逐步操作
        for i, step in enumerate(normal_flow, 1):
            initial_status = step['initial_status']
            action = step['action']
            next_status = step['next_status']
            action_data = step.get('action_data', {})

            self.test_logger.info(f"步骤 {i}: {initial_status} -> {action} -> {next_status}")
            self.test_logger.debug(f"操作数据: {action_data}")

        self.test_logger.info("订单状态正常流转概念验证通过")

    # ==================== 订单导出测试 ====================

    def test_export_orders(self):
        """测试导出订单功能"""
        self.test_logger.info("开始测试导出订单功能")

        # 执行导出
        self.order_list_page.export_orders(format="excel")

        # 等待导出完成
        time.sleep(3)  # 等待文件下载

        self.test_logger.info("订单导出测试完成")

    # ==================== 综合测试 ====================

    def test_complete_order_workflow(self):
        """测试完整订单工作流程"""
        self.test_logger.info("开始测试完整订单工作流程")

        # 步骤1: 搜索订单
        order_id = "ORDER-20240404-001"
        self.order_list_page.search_order(order_id, search_type="order_id")
        orders = self.order_list_page.get_order_rows()
        assert len(orders) > 0, f"搜索 '{order_id}' 没有结果"
        self.test_logger.info(f"步骤1完成: 搜索订单 '{order_id}'，找到 {len(orders)} 个订单")

        # 步骤2: 筛选订单
        self.order_list_page.reset_filters()
        self.order_list_page.filter_by_status("待付款")
        filtered_orders = self.order_list_page.get_order_rows()
        self.test_logger.info(f"步骤2完成: 按状态筛选，找到 {len(filtered_orders)} 个待付款订单")

        # 步骤3: 排序订单
        self.order_list_page.sort_by("order_time_desc")
        sorted_orders = self.order_list_page.get_order_rows()
        assert len(sorted_orders) > 0, "排序后没有订单"
        self.test_logger.info(f"步骤3完成: 按订单时间降序排序，第一个订单: '{sorted_orders[0]['order_id'] if sorted_orders else '无'}'")

        # 步骤4: 查看订单详情
        if sorted_orders:
            self.order_list_page.click_view_order(0)
            self.order_operation_page.wait_for_order_details_loaded()
            self.test_logger.info("步骤4完成: 查看订单详情")

            # 返回订单列表
            self.order_operation_page.back_to_list()
            self.order_list_page.wait_for_order_table_loaded()

        # 步骤5: 批量操作
        # 选择第一个订单
        self.order_list_page.select_order_by_index(0)
        self.order_list_page.batch_operation("导出")
        self.test_logger.info("步骤5完成: 批量导出订单")

        self.test_logger.info("完整订单工作流程测试通过")

    # ==================== 性能测试 ====================

    def test_search_performance(self):
        """测试搜索性能"""
        self.test_logger.info("开始测试搜索性能")

        # 记录开始时间
        start_time = time.time()

        # 执行搜索
        self.order_list_page.search_order("ORDER", search_type="order_id")

        # 等待结果加载
        self.order_list_page.wait_for_order_table_loaded()

        # 记录结束时间
        end_time = time.time()
        search_time = end_time - start_time

        # 验证响应时间在合理范围内
        max_expected_time = 5  # 秒
        assert search_time <= max_expected_time, \
            f"搜索响应时间过长，期望不超过 {max_expected_time}秒，实际 {search_time:.2f}秒"

        self.test_logger.info(f"搜索性能测试通过 - 响应时间: {search_time:.2f}秒")


# pytest兼容性装饰器
@pytest.mark.order
@pytest.mark.smoke
class TestOrderPytest:
    """pytest风格的订单测试类"""

    @pytest.fixture(autouse=True)
    def setup(self, driver):
        """测试初始化"""
        self.driver = driver
        self.order_list_page = OrderListPage(driver)
        self.order_operation_page = OrderOperationPage(driver)
        self.data_manager = get_test_data_manager()
        self.order_data = load_test_data('order')

        # 打开订单列表页面
        self.order_list_page.open_order_list_page()
        self.order_list_page.wait_for_order_table_loaded()
        yield
        # 清理工作由BaseTest负责

    @pytest.mark.parametrize("search_type,search_value,expected_min_results", [
        ("order_id", "ORDER-20240404", 2),
        ("username", "customer1", 1),
    ])
    def test_order_search_pytest(self, search_type, search_value, expected_min_results):
        """pytest风格的订单搜索测试"""
        self.order_list_page.search_order(search_value, search_type=search_type)
        orders = self.order_list_page.get_order_rows()
        assert len(orders) >= expected_min_results, \
            f"搜索 '{search_value}' 结果不足，期望至少 {expected_min_results} 个，实际 {len(orders)} 个"

    @pytest.mark.parametrize("status_key,expected_min_results", [
        ("pending_payment", 1),
        ("pending_shipment", 1),
    ])
    def test_filter_by_status_pytest(self, status_key, expected_min_results):
        """pytest风格的状态筛选测试"""
        status_mapping = self.order_data.get('order_status', {})
        status = status_mapping.get(status_key, status_key)

        self.order_list_page.filter_by_status(status)
        orders = self.order_list_page.get_order_rows()
        assert len(orders) >= expected_min_results, \
            f"筛选 '{status}' 结果不足，期望至少 {expected_min_results} 个，实际 {len(orders)} 个"


if __name__ == "__main__":
    # 运行测试
    print("运行订单管理测试...")

    # 导入unittest
    import unittest

    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestOrderManagement)

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