#!/usr/bin/env python3
"""
冒烟测试套件
包含电商后台管理系统最核心、最基本的测试用例
确保系统基本功能正常，可用于快速验证部署
"""

from typing import List, Dict, Any


class SmokeTestSuite:
    """
    冒烟测试套件
    包含系统最核心功能的测试用例
    """

    def __init__(self):
        """初始化冒烟测试套件"""
        self.suite_name = "smoke"
        self.description = "电商后台管理系统冒烟测试套件"
        self.priority = "P0"  # 最高优先级

    def get_test_cases(self) -> List[Dict[str, Any]]:
        """
        获取测试用例列表

        Returns:
            List[Dict[str, Any]]: 测试用例配置列表
        """
        test_cases = [
            # 登录模块
            {
                "module": "login",
                "class": "TestLogin",
                "method": "test_valid_login",
                "description": "管理员正常登录",
                "priority": "P0",
                "timeout": 30
            },
            {
                "module": "login",
                "class": "TestLogin",
                "method": "test_invalid_password",
                "description": "错误密码登录",
                "priority": "P0",
                "timeout": 30
            },

            # 商品管理模块
            {
                "module": "product",
                "class": "TestProductManagement",
                "method": "test_product_search",
                "description": "商品搜索功能",
                "priority": "P0",
                "timeout": 30
            },
            {
                "module": "product",
                "class": "TestProductManagement",
                "method": "test_view_product_detail",
                "description": "查看商品详情",
                "priority": "P0",
                "timeout": 30
            },

            # 订单管理模块
            {
                "module": "order",
                "class": "TestOrderManagement",
                "method": "test_order_search",
                "description": "订单搜索功能",
                "priority": "P0",
                "timeout": 30
            },
            {
                "module": "order",
                "class": "TestOrderManagement",
                "method": "test_view_order_detail",
                "description": "查看订单详情",
                "priority": "P0",
                "timeout": 30
            },

            # 用户管理模块
            {
                "module": "user",
                "class": "TestUserManagement",
                "method": "test_user_search_by_username",
                "description": "用户搜索功能",
                "priority": "P0",
                "timeout": 30
            },
            {
                "module": "user",
                "class": "TestUserManagement",
                "method": "test_view_user_detail",
                "description": "查看用户详情",
                "priority": "P0",
                "timeout": 30
            },

            # 权限管理模块
            {
                "module": "permission",
                "class": "TestPermissionManagement",
                "method": "test_role_search",
                "description": "角色搜索功能",
                "priority": "P0",
                "timeout": 30
            },
            {
                "module": "permission",
                "class": "TestPermissionManagement",
                "method": "test_create_and_delete_role",
                "description": "角色创建和删除",
                "priority": "P0",
                "timeout": 60
            }
        ]

        return test_cases

    def get_test_case_names(self) -> List[str]:
        """
        获取测试用例名称列表（格式：module.class.method）

        Returns:
            List[str]: 测试用例名称列表
        """
        test_cases = self.get_test_cases()
        return [
            f"{tc['module']}.{tc['class']}.{tc['method']}"
            for tc in test_cases
        ]

    def get_module_coverage(self) -> Dict[str, int]:
        """
        获取模块覆盖统计

        Returns:
            Dict[str, int]: 模块名称到测试用例数量的映射
        """
        test_cases = self.get_test_cases()
        coverage = {}

        for tc in test_cases:
            module = tc["module"]
            coverage[module] = coverage.get(module, 0) + 1

        return coverage

    def get_priority_distribution(self) -> Dict[str, int]:
        """
        获取优先级分布

        Returns:
            Dict[str, int]: 优先级到测试用例数量的映射
        """
        test_cases = self.get_test_cases()
        distribution = {"P0": 0, "P1": 0, "P2": 0}

        for tc in test_cases:
            priority = tc.get("priority", "P0")
            distribution[priority] = distribution.get(priority, 0) + 1

        return distribution

    def get_suite_summary(self) -> Dict[str, Any]:
        """
        获取测试套件摘要

        Returns:
            Dict[str, Any]: 测试套件摘要信息
        """
        test_cases = self.get_test_cases()

        total_cases = len(test_cases)
        total_timeout = sum(tc.get("timeout", 30) for tc in test_cases)
        avg_timeout = total_timeout / total_cases if total_cases > 0 else 0

        return {
            "suite_name": self.suite_name,
            "description": self.description,
            "total_cases": total_cases,
            "estimated_total_time": total_timeout,
            "average_timeout": avg_timeout,
            "module_coverage": self.get_module_coverage(),
            "priority_distribution": self.get_priority_distribution(),
            "modules": list(self.get_module_coverage().keys())
        }

    def filter_by_module(self, module: str) -> List[Dict[str, Any]]:
        """
        按模块筛选测试用例

        Args:
            module: 模块名称

        Returns:
            List[Dict[str, Any]]: 筛选后的测试用例
        """
        test_cases = self.get_test_cases()
        return [tc for tc in test_cases if tc["module"] == module]

    def filter_by_priority(self, priority: str) -> List[Dict[str, Any]]:
        """
        按优先级筛选测试用例

        Args:
            priority: 优先级 (P0, P1, P2)

        Returns:
            List[Dict[str, Any]]: 筛选后的测试用例
        """
        test_cases = self.get_test_cases()
        return [tc for tc in test_cases if tc.get("priority") == priority]


# 快捷函数
def create_smoke_suite() -> SmokeTestSuite:
    """
    创建冒烟测试套件

    Returns:
        SmokeTestSuite: 冒烟测试套件实例
    """
    return SmokeTestSuite()


if __name__ == "__main__":
    # 测试SmokeTestSuite类
    print("测试SmokeTestSuite类...")

    suite = SmokeTestSuite()
    summary = suite.get_suite_summary()

    print(f"测试套件名称: {summary['suite_name']}")
    print(f"描述: {summary['description']}")
    print(f"测试用例总数: {summary['total_cases']}")
    print(f"预估总执行时间: {summary['estimated_total_time']}秒")
    print(f"模块覆盖: {summary['module_coverage']}")
    print(f"优先级分布: {summary['priority_distribution']}")

    # 打印测试用例列表
    print("\n测试用例列表:")
    for i, test_case in enumerate(suite.get_test_cases(), 1):
        print(f"{i:2d}. {test_case['module']}.{test_case['class']}.{test_case['method']} "
              f"- {test_case['description']} (优先级: {test_case['priority']})")

    print("\n测试完成")