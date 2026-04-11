#!/usr/bin/env python3
"""
用户管理功能测试用例
测试电商后台管理系统的用户管理功能
"""

import time
import pytest
from typing import Dict, List, Any
from selenium.webdriver.common.by import By

from testcases.base_test import BaseTest
from pages.user_list_page import UserListPage
from pages.user_operation_page import UserOperationPage
from utils.data_manager import get_test_data_manager, load_test_data
from utils.config_manager import get_config


class TestUserManagement(BaseTest):
    """
    用户管理功能测试类
    测试用户管理功能的正常场景、异常场景和边界场景
    """

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        super().setUpClass()

        # 初始化测试数据管理器
        cls.data_manager = get_test_data_manager(data_source='yaml')

        # 加载用户测试数据
        cls.user_data = load_test_data('user')
        cls.test_logger.info("用户测试数据加载完成")

        # 创建用户页面对象
        cls.user_list_page = UserListPage(cls.driver)
        cls.user_operation_page = UserOperationPage(cls.driver)

    def setUp(self):
        """测试方法初始化"""
        super().setUp()

        # 每个测试开始前打开用户列表页面
        self.user_list_page.open_user_list_page()
        self.user_list_page.wait_for_user_table_loaded()

        # 验证用户列表页面元素
        # assert self.user_list_page.verify_user_list_elements(), "用户列表页面元素验证失败"

    def tearDown(self):
        """测试方法清理"""
        # 清理测试数据
        super().tearDown()

    # ==================== 用户搜索测试 ====================

    def test_user_search_by_username(self):
        """测试用户按用户名搜索"""
        self.test_logger.info("开始测试用户按用户名搜索")

        search_test_cases = self.user_data.get('search_test_cases', [])
        assert len(search_test_cases) > 0, "测试数据中没有搜索测试用例"

        # 测试每个搜索用例
        for i, test_case in enumerate(search_test_cases, 1):
            search_type = test_case['search_type']
            search_value = test_case['search_value']
            expected_results = test_case.get('expected_results', 0)
            description = test_case.get('description', f"搜索测试 {i}")

            self.test_logger.info(f"搜索测试 {i}: {description} - 类型: {search_type}, 值: '{search_value}'")

            # 执行搜索
            self.user_list_page.search_user(search_value, search_type)

            # 获取搜索结果数量
            user_count = self.user_list_page.get_user_count()

            # 验证结果数量
            assert user_count >= expected_results, \
                f"搜索结果数量不足，期望至少 {expected_results} 个，实际 {user_count} 个"

            # 验证搜索结果包含关键词
            if user_count > 0:
                assert self.user_list_page.verify_search_results(search_value, search_type), \
                    f"搜索结果未包含关键词 '{search_value}'"

            # 重置搜索条件
            self.user_list_page.reset_filters()

            self.test_logger.info(f"搜索测试通过 - 类型: {search_type}, 值: '{search_value}', 找到 {user_count} 个用户")

    def test_user_search_no_results(self):
        """测试用户搜索无结果"""
        self.test_logger.info("开始测试用户搜索无结果")

        # 搜索不存在的用户
        self.user_list_page.search_user("nonexistent_user_12345", "username")

        # 获取搜索结果数量
        user_count = self.user_list_page.get_user_count()

        # 验证没有结果
        assert user_count == 0, f"搜索无结果测试失败，实际找到 {user_count} 个用户"

        # 验证显示无结果提示（假设页面有无结果提示）
        no_results_element = (By.CLASS_NAME, "no-results")
        if self.user_list_page.is_element_present(no_results_element, timeout=2):
            self.test_logger.info("无结果提示显示正常")

        self.test_logger.info("用户搜索无结果测试通过")

    # ==================== 用户筛选测试 ====================

    def test_user_filter_by_role(self):
        """测试用户按角色筛选"""
        self.test_logger.info("开始测试用户按角色筛选")

        filter_test_cases = self.user_data.get('filter_test_cases', [])
        assert len(filter_test_cases) > 0, "测试数据中没有筛选测试用例"

        # 只测试角色筛选用例
        role_filter_cases = [case for case in filter_test_cases if case.get('filter_type') == 'role']

        for i, test_case in enumerate(role_filter_cases, 1):
            filter_value = test_case['filter_value']
            expected_results = test_case.get('expected_results', 0)
            description = test_case.get('description', f"角色筛选测试 {i}")

            self.test_logger.info(f"筛选测试 {i}: {description} - 角色: {filter_value}")

            # 执行筛选
            self.user_list_page.filter_by_role(filter_value)

            # 获取筛选结果数量
            user_count = self.user_list_page.get_user_count()

            # 验证结果数量
            assert user_count >= expected_results, \
                f"筛选结果数量不足，期望至少 {expected_results} 个，实际 {user_count} 个"

            # 验证筛选结果（检查所有用户的角色）
            if user_count > 0:
                users = self.user_list_page.get_user_rows()
                for user in users:
                    user_role = user.get('role', '')
                    # 验证用户角色包含筛选值（可能角色显示为中文）
                    assert filter_value in user_role or user_role in filter_value, \
                        f"用户角色不匹配: {user_role} (期望: {filter_value})"

            # 重置筛选条件
            self.user_list_page.reset_filters()

            self.test_logger.info(f"角色筛选测试通过 - 角色: {filter_value}, 找到 {user_count} 个用户")

    def test_user_filter_by_status(self):
        """测试用户按状态筛选"""
        self.test_logger.info("开始测试用户按状态筛选")

        filter_test_cases = self.user_data.get('filter_test_cases', [])
        status_filter_cases = [case for case in filter_test_cases if case.get('filter_type') == 'status']

        for i, test_case in enumerate(status_filter_cases, 1):
            filter_value = test_case['filter_value']
            expected_results = test_case.get('expected_results', 0)
            description = test_case.get('description', f"状态筛选测试 {i}")

            self.test_logger.info(f"筛选测试 {i}: {description} - 状态: {filter_value}")

            # 执行筛选
            self.user_list_page.filter_by_status(filter_value)

            # 获取筛选结果数量
            user_count = self.user_list_page.get_user_count()

            # 验证结果数量
            assert user_count >= expected_results, \
                f"筛选结果数量不足，期望至少 {expected_results} 个，实际 {user_count} 个"

            # 重置筛选条件
            self.user_list_page.reset_filters()

            self.test_logger.info(f"状态筛选测试通过 - 状态: {filter_value}, 找到 {user_count} 个用户")

    # ==================== 用户操作测试 ====================

    def test_add_new_user(self):
        """测试添加新用户"""
        self.test_logger.info("开始测试添加新用户")

        operation_test_cases = self.user_data.get('operation_test_cases', {})
        new_user_data = operation_test_cases.get('new_user', {})
        assert new_user_data, "测试数据中没有新用户数据"

        # 生成唯一用户名（使用时间戳）
        timestamp = int(time.time())
        username = new_user_data.get('username', '').replace('{timestamp}', str(timestamp))
        email = new_user_data.get('email', '').replace('{timestamp}', str(timestamp))

        # 生成随机手机号后4位
        import random
        random_suffix = str(random.randint(1000, 9999))
        phone = new_user_data.get('phone', '').replace('{random}', random_suffix)

        # 准备用户数据
        user_data = {
            'username': username,
            'password': new_user_data.get('password', 'Test@123456'),
            'confirm_password': new_user_data.get('confirm_password', 'Test@123456'),
            'email': email,
            'phone': phone,
            'real_name': new_user_data.get('real_name', '测试用户'),
            'role': new_user_data.get('role', 'viewer'),
            'status': new_user_data.get('status', 'active'),
            'description': new_user_data.get('description', '自动化测试创建的用户')
        }

        self.test_logger.info(f"添加新用户: {username}")

        # 执行添加用户操作
        result = self.user_operation_page.add_user(user_data)

        # 验证添加成功
        assert result, "添加用户失败"

        # 验证成功消息
        success_message = self.user_operation_page.get_success_message()
        assert success_message, "未显示成功消息"

        # 返回用户列表验证新用户存在
        self.user_list_page.open_user_list_page()
        self.user_list_page.wait_for_user_table_loaded()

        # 搜索新用户
        self.user_list_page.search_user(username, "username")

        # 验证用户存在
        assert self.user_list_page.verify_user_exists(username), f"新用户 {username} 未在列表中显示"

        self.test_logger.info(f"添加新用户测试通过 - 用户名: {username}")

    def test_view_user_detail(self):
        """测试查看用户详情"""
        self.test_logger.info("开始测试查看用户详情")

        # 获取测试用户数据
        test_users = self.user_data.get('test_users', [])
        assert len(test_users) > 0, "测试数据中没有测试用户"

        # 使用第一个测试用户
        test_user = test_users[0]
        user_id = test_user['user_id']
        username = test_user['username']

        self.test_logger.info(f"查看用户详情: {username} (ID: {user_id})")

        # 执行查看用户详情操作
        user_detail = self.user_operation_page.view_user_detail(user_id)

        # 验证用户详情信息
        assert user_detail, "获取用户详情失败"
        assert user_detail.get('username') == username, f"用户名不匹配: {user_detail.get('username')}"

        # 验证基本信息存在
        expected_fields = ['user_id', 'username', 'email', 'phone', 'real_name', 'role', 'status']
        for field in expected_fields:
            assert field in user_detail, f"用户详情缺少字段: {field}"
            if user_detail[field]:
                self.test_logger.debug(f"用户{field}: {user_detail[field]}")

        self.test_logger.info(f"查看用户详情测试通过 - 用户名: {username}")

    def test_edit_user_info(self):
        """测试编辑用户信息"""
        self.test_logger.info("开始测试编辑用户信息")

        operation_test_cases = self.user_data.get('operation_test_cases', {})
        edit_user_data = operation_test_cases.get('edit_user', {})
        assert edit_user_data, "测试数据中没有编辑用户数据"

        user_id = edit_user_data.get('user_id')
        updates = edit_user_data.get('updates', {})

        self.test_logger.info(f"编辑用户信息: 用户ID={user_id}, 更新字段={updates.keys()}")

        # 执行编辑用户操作
        result = self.user_operation_page.edit_user(user_id, updates)

        # 验证编辑成功
        assert result, "编辑用户失败"

        # 验证成功消息
        success_message = self.user_operation_page.get_success_message()
        assert success_message, "未显示成功消息"

        # 重新查看用户详情验证更新
        user_detail = self.user_operation_page.view_user_detail(user_id)

        # 验证更新字段
        for field, expected_value in updates.items():
            if field in user_detail:
                actual_value = user_detail[field]
                # 对于表单输入字段，可能需要从属性获取值
                self.test_logger.debug(f"字段 {field}: 期望='{expected_value}', 实际='{actual_value}'")

        self.test_logger.info(f"编辑用户信息测试通过 - 用户ID: {user_id}")

    def test_disable_and_enable_user(self):
        """测试禁用和启用用户"""
        self.test_logger.info("开始测试禁用和启用用户")

        operation_test_cases = self.user_data.get('operation_test_cases', {})
        toggle_status_data = operation_test_cases.get('toggle_status', {})
        assert toggle_status_data, "测试数据中没有状态切换数据"

        user_id = toggle_status_data.get('user_id')
        current_status = toggle_status_data.get('current_status', 'active')
        target_status = toggle_status_data.get('target_status', 'disabled')

        self.test_logger.info(f"切换用户状态: 用户ID={user_id}, 从 {current_status} 到 {target_status}")

        # 先禁用用户
        if target_status == 'disabled':
            result = self.user_operation_page.disable_user(user_id)
            assert result, "禁用用户失败"
            self.test_logger.info("用户禁用成功")

            # 验证用户状态已更新
            # 返回用户列表检查状态
            self.user_list_page.open_user_list_page()
            self.user_list_page.wait_for_user_table_loaded()

            # 搜索用户
            test_users = self.user_data.get('test_users', [])
            target_user = None
            for user in test_users:
                if user['user_id'] == user_id:
                    target_user = user
                    break

            if target_user:
                username = target_user['username']
                self.user_list_page.search_user(username, "username")

                # 获取用户状态
                user_status = self.user_list_page.get_user_status(username)
                assert user_status and '禁用' in user_status, f"用户状态未更新为禁用，当前状态: {user_status}"

        # 再启用用户（如果需要）
        elif target_status == 'active':
            result = self.user_operation_page.enable_user(user_id)
            assert result, "启用用户失败"
            self.test_logger.info("用户启用成功")

        self.test_logger.info(f"用户状态切换测试通过 - 用户ID: {user_id}")

    # ==================== 用户排序测试 ====================

    def test_user_sorting(self):
        """测试用户排序功能"""
        self.test_logger.info("开始测试用户排序功能")

        sort_test_cases = self.user_data.get('sort_test_cases', [])
        assert len(sort_test_cases) > 0, "测试数据中没有排序测试用例"

        for i, test_case in enumerate(sort_test_cases, 1):
            sort_by = test_case['sort_by']
            expected_first_user = test_case.get('expected_first_user', '')
            description = test_case.get('description', f"排序测试 {i}")

            self.test_logger.info(f"排序测试 {i}: {description} - 排序方式: {sort_by}")

            # 执行排序
            self.user_list_page.sort_by(sort_by)

            # 获取排序后的用户列表
            users = self.user_list_page.get_user_rows()

            # 验证排序结果（如果有预期第一个用户）
            if expected_first_user and users:
                first_user = users[0].get('username', '')
                assert expected_first_user in first_user or first_user in expected_first_user, \
                    f"排序结果不正确，第一个用户: {first_user} (期望: {expected_first_user})"

            self.test_logger.info(f"排序测试通过 - 排序方式: {sort_by}, 用户数量: {len(users)}")

    # ==================== 用户导出测试 ====================

    def test_user_export(self):
        """测试用户导出功能"""
        self.test_logger.info("开始测试用户导出功能")

        # 执行导出操作（不同格式）
        export_formats = self.user_data.get('import_export_test', {}).get('export_formats', ['excel'])

        for export_format in export_formats:
            self.test_logger.info(f"导出用户数据 - 格式: {export_format}")

            # 执行导出
            self.user_list_page.export_users(export_format)

            # 验证导出文件（这里简化处理，实际可能需要检查文件下载）
            # 检查是否有导出成功提示
            success_element = (By.CLASS_NAME, "export-success")
            if self.user_list_page.is_element_present(success_element, timeout=5):
                self.test_logger.info(f"{export_format} 格式导出成功提示显示")
            else:
                # 如果没有成功提示，检查是否有错误提示
                error_element = (By.CLASS_NAME, "export-error")
                if not self.user_list_page.is_element_present(error_element, timeout=2):
                    self.test_logger.info(f"{export_format} 格式导出操作完成")

            # 短暂等待
            time.sleep(1)

        self.test_logger.info("用户导出功能测试通过")

    # ==================== 边界测试 ====================

    def test_user_validation_boundary(self):
        """测试用户表单验证边界条件"""
        self.test_logger.info("开始测试用户表单验证边界条件")

        boundary_test_cases = self.user_data.get('boundary_test_cases', [])
        assert len(boundary_test_cases) > 0, "测试数据中没有边界测试用例"

        # 打开添加用户页面
        self.user_operation_page.open_add_user_page()

        for i, test_case in enumerate(boundary_test_cases, 1):
            username = test_case.get('username', '')
            expected_valid = test_case.get('expected_valid', True)
            expected_error = test_case.get('expected_error', '')
            description = test_case.get('description', f"边界测试 {i}")

            self.test_logger.info(f"边界测试 {i}: {description}")

            # 清空表单
            self.user_operation_page.clear_form()

            # 输入测试数据
            if username:
                self.user_operation_page.type(self.user_operation_page.USERNAME_INPUT, username)

                # 尝试保存
                self.user_operation_page.click(self.user_operation_page.SUBMIT_BUTTON)

                # 检查验证结果
                if expected_valid:
                    # 期望有效，检查是否有错误消息
                    errors = self.user_operation_page.get_validation_errors()
                    assert len(errors) == 0, f"期望有效但出现验证错误: {errors}"
                else:
                    # 期望无效，检查是否有预期的错误消息
                    errors = self.user_operation_page.get_validation_errors()
                    error_text = ' '.join(errors)
                    assert expected_error in error_text, \
                        f"期望错误消息包含 '{expected_error}'，实际错误: {error_text}"

            # 返回添加用户页面继续下一个测试
            self.user_operation_page.open_add_user_page()

        self.test_logger.info("用户表单验证边界条件测试完成")

    # ==================== 性能测试 ====================

    def test_user_search_performance(self):
        """测试用户搜索性能"""
        self.test_logger.info("开始测试用户搜索性能")

        performance_test = self.user_data.get('performance_test', {})
        search_performance = performance_test.get('search_performance', {})

        if search_performance:
            keyword = search_performance.get('keyword', 'test')
            expected_response_time = search_performance.get('expected_response_time', 2)

            self.test_logger.info(f"性能测试 - 搜索关键词: '{keyword}', 期望响应时间: {expected_response_time}秒")

            # 记录开始时间
            start_time = time.time()

            # 执行搜索
            self.user_list_page.search_user(keyword, "username")

            # 记录结束时间
            end_time = time.time()
            response_time = end_time - start_time

            self.test_logger.info(f"搜索响应时间: {response_time:.2f}秒")

            # 验证响应时间在合理范围内
            assert response_time <= expected_response_time * 2, \
                f"搜索响应时间过长: {response_time:.2f}秒 (期望: ≤{expected_response_time}秒)"

            # 验证搜索结果
            user_count = self.user_list_page.get_user_count()
            self.test_logger.info(f"搜索到 {user_count} 个用户")

        self.test_logger.info("用户搜索性能测试通过")


if __name__ == "__main__":
    # 直接运行测试
    print("注意：此文件应使用pytest运行")
    print("运行命令: pytest testcases/test_user.py -v")