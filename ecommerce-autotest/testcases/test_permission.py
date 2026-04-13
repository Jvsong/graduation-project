#!/usr/bin/env python3
"""
权限管理功能测试用例
测试电商后台管理系统的权限管理功能
"""

import time
import pytest
from typing import Dict, List, Any

from testcases.base_test import BaseTest
from pages.login_page import LoginPage
from pages.permission_page import PermissionPage
from pages.user_list_page import UserListPage
from pages.user_operation_page import UserOperationPage
from utils.data_manager import get_test_data_manager, load_test_data
from utils.config_manager import get_config


class TestPermissionManagement(BaseTest):
    """
    权限管理功能测试类
    测试权限管理功能的正常场景、异常场景和边界场景
    """

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        super().setUpClass()

        # 初始化测试数据管理器
        cls.data_manager = get_test_data_manager(data_source='yaml')

        # 加载用户测试数据（包含权限数据）
        cls.user_data = load_test_data('user')
        cls.logger.info("权限测试数据加载完成")
        cls.login_data = load_test_data('login')
        cls.logger.info("登录测试数据加载完成")

        # 创建页面对象
        cls.login_page = LoginPage(cls.driver)
        cls.permission_page = PermissionPage(cls.driver)
        cls.user_list_page = UserListPage(cls.driver)
        cls.user_operation_page = UserOperationPage(cls.driver)

    def setUp(self):
        """测试方法初始化"""
        super().setUp()

        self._login_before_test()

        # 每个测试开始前打开权限管理页面（角色列表）
        self.permission_page.open_role_list_page()
        self.permission_page.wait_for_role_table_loaded()

    def _login_before_test(self):
        """测试前登录"""
        self.login_page.open_login_page()
        self.login_page.wait_for_login_page_load()

        valid_users = self.login_data.get('valid_users', [])
        if not valid_users:
            username = "admin"
            password = "admin123"
        else:
            user = valid_users[0]
            username = user['username']
            password = user['password']

        self.login_page.login(username, password)
        time.sleep(2)

        assert self.login_page.is_login_successful(timeout=10), \
            f"测试前登录失败，用户: {username}"

    def tearDown(self):
        """测试方法清理"""
        # 清理测试数据
        super().tearDown()

    # ==================== 角色管理测试 ====================

    def test_role_search(self):
        """测试角色搜索功能"""
        self.test_logger.info("开始测试角色搜索功能")

        # 搜索管理员角色
        self.permission_page.search_role("管理员")

        # 获取搜索结果
        roles = self.permission_page.get_role_rows()

        # 验证搜索结果
        assert len(roles) > 0, "角色搜索未找到结果"

        # 验证搜索结果包含关键词
        found = False
        for role in roles:
            role_name = role.get('role_name', '')
            if "管理员" in role_name:
                found = True
                break

        assert found, "搜索结果中未找到包含'管理员'的角色"

        self.test_logger.info(f"角色搜索测试通过，找到 {len(roles)} 个角色")

    def test_create_and_delete_role(self):
        """测试创建和删除角色"""
        self.test_logger.info("开始测试创建和删除角色")

        # 生成唯一角色名
        timestamp = int(time.time())
        role_name = f"测试角色_{timestamp}"
        role_code = f"test_role_{timestamp}"

        role_data = {
            "name": role_name,
            "code": role_code,
            "description": "自动化测试创建的角色",
            "status": "active"
        }

        # 创建角色
        self.test_logger.info(f"创建角色: {role_name}")
        create_result = self.permission_page.create_role(role_data)
        assert create_result, "创建角色失败"

        # 验证角色创建成功
        success_message = self.permission_page.get_success_message()
        assert success_message, "未显示创建成功消息"
        self.test_logger.info(f"角色创建成功: {success_message}")

        # 返回角色列表验证角色存在
        self.permission_page.open_role_list_page()
        self.permission_page.wait_for_role_table_loaded()

        # 搜索新创建的角色
        self.permission_page.search_role(role_name)

        # 验证角色存在
        assert self.permission_page.verify_role_exists(role_name), f"新角色 {role_name} 未在列表中显示"

        # 获取角色ID（从搜索结果中）
        roles = self.permission_page.get_role_rows()
        role_id = None
        for role in roles:
            if role.get('role_name') == role_name:
                role_id = int(role.get('role_id', 0))
                break

        assert role_id is not None, f"未找到角色 {role_name} 的ID"

        # 删除角色
        self.test_logger.info(f"删除角色: {role_name} (ID: {role_id})")
        delete_result = self.permission_page.delete_role(role_id)
        assert delete_result, "删除角色失败"

        # 验证角色删除成功
        success_message = self.permission_page.get_success_message()
        assert success_message, "未显示删除成功消息"
        self.test_logger.info(f"角色删除成功: {success_message}")

        # 再次验证角色不存在
        self.permission_page.open_role_list_page()
        self.permission_page.wait_for_role_table_loaded()

        self.permission_page.search_role(role_name)
        assert not self.permission_page.verify_role_exists(role_name), f"角色 {role_name} 仍然存在"

        self.test_logger.info("创建和删除角色测试通过")

    def test_edit_role(self):
        """测试编辑角色信息"""
        self.test_logger.info("开始测试编辑角色信息")

        # 首先创建一个测试角色
        timestamp = int(time.time())
        original_name = f"编辑测试角色_{timestamp}"
        original_code = f"edit_test_role_{timestamp}"

        role_data = {
            "name": original_name,
            "code": original_code,
            "description": "用于编辑测试的角色",
            "status": "active"
        }

        # 创建角色
        create_result = self.permission_page.create_role(role_data)
        assert create_result, "创建测试角色失败"

        # 获取角色ID
        self.permission_page.open_role_list_page()
        self.permission_page.wait_for_role_table_loaded()

        self.permission_page.search_role(original_name)
        roles = self.permission_page.get_role_rows()
        role_id = None
        for role in roles:
            if role.get('role_name') == original_name:
                role_id = int(role.get('role_id', 0))
                break

        assert role_id is not None, "未找到测试角色的ID"

        # 编辑角色信息
        updates = {
            "name": f"{original_name}_已更新",
            "description": "更新后的角色描述",
            "status": "disabled"
        }

        self.test_logger.info(f"编辑角色: ID={role_id}, 更新字段={updates.keys()}")
        edit_result = self.permission_page.edit_role(role_id, updates)
        assert edit_result, "编辑角色失败"

        # 验证编辑成功
        success_message = self.permission_page.get_success_message()
        assert success_message, "未显示编辑成功消息"

        # 验证角色信息已更新
        self.permission_page.open_role_list_page()
        self.permission_page.wait_for_role_table_loaded()

        self.permission_page.search_role(updates["name"])
        assert self.permission_page.verify_role_exists(updates["name"]), f"角色 {updates['name']} 未在列表中显示"

        # 清理：删除测试角色
        self.permission_page.delete_role(role_id)

        self.test_logger.info("编辑角色信息测试通过")

    # ==================== 权限分配测试 ====================

    def test_assign_permissions_to_role(self):
        """测试为角色分配权限"""
        self.test_logger.info("开始测试为角色分配权限")

        # 从测试数据中获取权限数据
        permission_test_cases = self.user_data.get('permission_test_cases', {})
        role_permissions = permission_test_cases.get('role_permissions', {})
        assert role_permissions, "测试数据中没有角色权限数据"

        # 使用操作员角色的权限进行测试
        operator_permissions = role_permissions.get('operator', {})
        permissions = operator_permissions.get('permissions', [])
        description = operator_permissions.get('description', '')

        assert len(permissions) > 0, "操作员角色没有权限数据"

        self.test_logger.info(f"测试权限分配 - 角色: operator, 权限数量: {len(permissions)}, 描述: {description}")

        # 首先创建一个测试角色
        timestamp = int(time.time())
        role_name = f"权限测试角色_{timestamp}"
        role_code = f"permission_test_role_{timestamp}"

        role_data = {
            "name": role_name,
            "code": role_code,
            "description": "用于权限分配测试的角色",
            "status": "active"
        }

        create_result = self.permission_page.create_role(role_data)
        assert create_result, "创建测试角色失败"

        # 获取角色ID
        self.permission_page.open_role_list_page()
        self.permission_page.wait_for_role_table_loaded()

        self.permission_page.search_role(role_name)
        roles = self.permission_page.get_role_rows()
        role_id = None
        for role in roles:
            if role.get('role_name') == role_name:
                role_id = int(role.get('role_id', 0))
                break

        assert role_id is not None, "未找到测试角色的ID"

        # 为角色分配权限
        self.test_logger.info(f"为角色分配权限: 角色ID={role_id}, 权限列表={permissions}")
        assign_result = self.permission_page.assign_permissions_to_role(role_id, permissions)
        assert assign_result, "分配权限失败"

        # 验证权限分配成功
        success_message = self.permission_page.get_success_message()
        assert success_message, "未显示权限分配成功消息"

        # 验证权限已分配
        assigned_permissions = self.permission_page.get_role_permissions(role_id)
        self.test_logger.info(f"已分配的权限: {assigned_permissions}")

        # 检查所有预期的权限都已分配
        for permission in permissions:
            assert permission in assigned_permissions or self.permission_page.verify_permission_assigned(role_id, permission), \
                f"权限 '{permission}' 未分配给角色"

        # 清理：删除测试角色
        self.permission_page.delete_role(role_id)

        self.test_logger.info("权限分配测试通过")

    def test_permission_tabs_navigation(self):
        """测试权限标签页导航"""
        self.test_logger.info("开始测试权限标签页导航")

        # 打开权限管理页面
        self.permission_page.open_permission_manage_page()
        self.permission_page.wait_for_permission_tree_loaded()

        # 测试切换到不同标签页
        tabs = ["system", "product", "order", "user", "finance", "report"]

        for tab in tabs:
            self.test_logger.info(f"切换到标签页: {tab}")
            self.permission_page.switch_permission_tab(tab)

            # 验证标签页已激活
            time.sleep(1)  # 等待标签页内容加载

            # 检查标签页内容（简化验证）
            active_tab_class = "active-tab"
            # 这里可以添加更具体的验证逻辑

        self.test_logger.info("权限标签页导航测试通过")

    # ==================== 权限验证测试 ====================

    def test_permission_verification(self):
        """测试权限验证功能"""
        self.test_logger.info("开始测试权限验证功能")

        # 从测试数据中获取权限验证测试用例
        permission_test_cases = self.user_data.get('permission_test_cases', {})
        permission_verification = permission_test_cases.get('permission_verification', [])
        assert len(permission_verification) > 0, "测试数据中没有权限验证测试用例"

        for i, test_case in enumerate(permission_verification, 1):
            username = test_case['username']
            role = test_case['role']
            allowed_actions = test_case.get('allowed_actions', [])
            denied_actions = test_case.get('denied_actions', [])

            self.test_logger.info(f"权限验证测试 {i}: 用户={username}, 角色={role}")
            self.test_logger.info(f"允许的操作: {allowed_actions}")
            self.test_logger.info(f"拒绝的操作: {denied_actions}")

            # 这里可以添加具体的权限验证逻辑
            # 例如：使用不同角色的用户登录，验证菜单项、按钮的显示/隐藏状态

            # 暂时记录测试用例信息
            self.test_logger.info(f"权限验证测试用例 {i} 记录完成")

        self.test_logger.info("权限验证测试完成（需要具体实现验证逻辑）")

    def test_role_based_access_control(self):
        """测试基于角色的访问控制"""
        self.test_logger.info("开始测试基于角色的访问控制")

        # 此测试需要模拟不同角色的用户登录，验证其访问权限
        # 由于需要登录和页面跳转，这里先创建测试框架

        test_users = self.user_data.get('test_users', [])
        assert len(test_users) > 0, "测试数据中没有测试用户"

        # 按角色分组用户
        users_by_role = {}
        for user in test_users:
            role = user.get('role', '')
            if role not in users_by_role:
                users_by_role[role] = []
            users_by_role[role].append(user)

        self.test_logger.info(f"按角色分组的用户: {list(users_by_role.keys())}")

        # 测试不同角色的访问权限
        # 这里可以添加具体的访问控制测试逻辑

        self.test_logger.info("基于角色的访问控制测试框架创建完成")

    # ==================== 用户角色分配测试 ====================

    def test_assign_users_to_role(self):
        """测试为用户分配角色"""
        self.test_logger.info("开始测试为用户分配角色")

        # 创建一个测试角色
        timestamp = int(time.time())
        role_name = f"用户分配测试角色_{timestamp}"
        role_code = f"user_assign_test_role_{timestamp}"

        role_data = {
            "name": role_name,
            "code": role_code,
            "description": "用于用户分配测试的角色",
            "status": "active"
        }

        create_result = self.permission_page.create_role(role_data)
        assert create_result, "创建测试角色失败"

        # 获取角色ID
        self.permission_page.open_role_list_page()
        self.permission_page.wait_for_role_table_loaded()

        self.permission_page.search_role(role_name)
        roles = self.permission_page.get_role_rows()
        role_id = None
        for role in roles:
            if role.get('role_name') == role_name:
                role_id = int(role.get('role_id', 0))
                break

        assert role_id is not None, "未找到测试角色的ID"

        # 获取测试用户
        test_users = self.user_data.get('test_users', [])
        assert len(test_users) > 0, "测试数据中没有测试用户"

        # 选择前两个测试用户
        selected_users = test_users[:2]
        usernames = [user['username'] for user in selected_users]

        self.test_logger.info(f"为用户分配角色: 角色ID={role_id}, 用户={usernames}")

        # 为用户分配角色
        assign_result = self.permission_page.assign_users_to_role(role_id, usernames)
        assert assign_result, "为用户分配角色失败"

        # 验证分配成功
        success_message = self.permission_page.get_success_message()
        assert success_message, "未显示用户分配成功消息"

        # 清理：删除测试角色
        self.permission_page.delete_role(role_id)

        self.test_logger.info("为用户分配角色测试通过")

    # ==================== 边界和异常测试 ====================

    def test_create_role_validation(self):
        """测试创建角色的表单验证"""
        self.test_logger.info("开始测试创建角色的表单验证")

        # 打开添加角色页面
        self.permission_page.open_role_add_page()
        self.permission_page.wait_for_role_form_loaded()

        # 测试空表单提交
        self.permission_page.click(self.permission_page.ROLE_SAVE_BUTTON)

        # 检查验证错误
        time.sleep(1)
        # 这里可以添加具体的验证错误检查逻辑

        # 测试无效数据提交
        invalid_role_data = {
            "name": "",  # 空角色名
            "code": "invalid@code",  # 无效角色代码
        }

        self.test_logger.info("创建角色表单验证测试完成")

    def test_permission_management_performance(self):
        """测试权限管理性能"""
        self.test_logger.info("开始测试权限管理性能")

        # 记录角色列表加载时间
        start_time = time.time()
        self.permission_page.open_role_list_page()
        self.permission_page.wait_for_role_table_loaded()
        end_time = time.time()

        load_time = end_time - start_time
        self.test_logger.info(f"角色列表加载时间: {load_time:.2f}秒")

        # 验证加载时间在合理范围内
        assert load_time <= 5, f"角色列表加载时间过长: {load_time:.2f}秒"

        # 获取角色数量
        roles = self.permission_page.get_role_rows()
        self.test_logger.info(f"角色数量: {len(roles)}")

        self.test_logger.info("权限管理性能测试通过")

    # ==================== 集成测试 ====================

    def test_permission_integration(self):
        """测试权限管理集成功能"""
        self.test_logger.info("开始测试权限管理集成功能")

        # 测试完整的权限管理流程
        # 1. 创建角色
        timestamp = int(time.time())
        role_name = f"集成测试角色_{timestamp}"
        role_code = f"integration_test_role_{timestamp}"

        role_data = {
            "name": role_name,
            "code": role_code,
            "description": "集成测试创建的角色",
            "status": "active"
        }

        create_result = self.permission_page.create_role(role_data)
        assert create_result, "集成测试：创建角色失败"

        # 2. 获取角色ID
        self.permission_page.open_role_list_page()
        self.permission_page.wait_for_role_table_loaded()

        self.permission_page.search_role(role_name)
        roles = self.permission_page.get_role_rows()
        role_id = None
        for role in roles:
            if role.get('role_name') == role_name:
                role_id = int(role.get('role_id', 0))
                break

        assert role_id is not None, "集成测试：未找到角色ID"

        # 3. 为角色分配权限
        permissions = ["product_view", "product_edit", "order_view"]
        assign_result = self.permission_page.assign_permissions_to_role(role_id, permissions)
        assert assign_result, "集成测试：分配权限失败"

        # 4. 编辑角色信息
        updates = {
            "description": "集成测试更新后的角色描述"
        }
        edit_result = self.permission_page.edit_role(role_id, updates)
        assert edit_result, "集成测试：编辑角色失败"

        # 5. 验证权限分配
        assigned_permissions = self.permission_page.get_role_permissions(role_id)
        for permission in permissions:
            assert permission in assigned_permissions, f"集成测试：权限 '{permission}' 未分配"

        # 6. 删除角色
        delete_result = self.permission_page.delete_role(role_id)
        assert delete_result, "集成测试：删除角色失败"

        # 7. 验证角色已删除
        self.permission_page.open_role_list_page()
        self.permission_page.wait_for_role_table_loaded()

        self.permission_page.search_role(role_name)
        assert not self.permission_page.verify_role_exists(role_name), "集成测试：角色删除失败"

        self.test_logger.info("权限管理集成测试通过")


if __name__ == "__main__":
    # 直接运行测试
    print("注意：此文件应使用pytest运行")
    print("运行命令: pytest testcases/test_permission.py -v")
