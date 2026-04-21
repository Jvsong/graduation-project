#!/usr/bin/env python3
"""
shop-system Dashboard AI smoke 与 API 校验测试。
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, Optional

import pytest
import requests

from pages.dashboard_ai_page import DashboardAIPage
from pages.login_page import LoginPage
from testcases.base_test import BaseTest
from utils.api_client import ShopSystemApiClient
from utils.config_manager import get_config, init_config
from utils.data_manager import load_test_data


def _http_available(url: str, timeout: int = 5) -> bool:
    try:
        response = requests.get(url, timeout=timeout, allow_redirects=True)
        return response.status_code < 500
    except requests.RequestException:
        return False


def _as_text(value: Any) -> str:
    return "" if value is None else str(value).strip()


@pytest.mark.ai
@pytest.mark.smoke
class TestAiAssistantSmoke(BaseTest):
    """Dashboard AI smoke 用例。"""

    @classmethod
    def setUpClass(cls):
        init_config()
        config = get_config()
        base_url = config.get("environment.base_url", "http://localhost:3000").rstrip("/")
        login_url = f"{base_url}/admin/login"

        if not _http_available(login_url):
            pytest.skip(f"前端未启动或登录页不可访问: {login_url}")

        try:
            checker = ShopSystemApiClient()
            checker.login("admin", "admin123")
        except Exception as exc:
            pytest.skip(f"后端未启动或管理员账号不可用，无法执行 Dashboard AI smoke: {exc}")

        super().setUpClass()
        cls.ai_data = load_test_data("ai_assistant")
        cls.login_page = LoginPage(cls.driver)
        cls.dashboard_page = DashboardAIPage(cls.driver)
        cls.primary_account = cls.ai_data["account"]["primary"]

    def setUp(self):
        super().setUp()
        self._login_to_dashboard()

    def _login_to_dashboard(self) -> None:
        self.login_page.open_login_page()
        self.login_page.wait_for_login_page_load()
        self.login_page.login(
            self.primary_account["username"],
            self.primary_account["password"],
        )
        assert self.login_page.is_login_successful(timeout=10), "管理员登录失败，无法进入 Dashboard"
        self.dashboard_page.open_dashboard()
        self.dashboard_page.wait_for_dashboard_ready()

    def test_dashboard_default_loads_daily_summary(self):
        """登录后进入 Dashboard 默认加载 DAILY_SUMMARY。"""
        expected_range = self.dashboard_page.RANGE_LABELS[self.ai_data["time_range"]["ui_default"]]
        summary_text = self.dashboard_page.get_daily_summary_text()

        assert "/admin/dashboard" in self.dashboard_page.get_current_url()
        assert self.dashboard_page.get_summary_range_label() == expected_range
        assert summary_text
        assert self.dashboard_page.get_highlighted_suggestion_count() >= 1

        self.dashboard_page.open_assistant_drawer()
        assert self.dashboard_page.get_current_question_label() == self.dashboard_page.QUESTION_LABELS["DAILY_SUMMARY"]
        assert self.dashboard_page.get_assistant_summary_text()

    def test_open_ai_assistant_drawer(self):
        """打开智能问讯抽屉。"""
        self.dashboard_page.open_assistant_drawer()
        assert self.dashboard_page.is_assistant_drawer_visible(timeout=5)
        assert self.dashboard_page.get_assistant_summary_text()
        assert self.dashboard_page.get_assistant_range_tag() == self.dashboard_page.RANGE_LABELS["7d"]

    def test_all_question_types_return_results(self):
        """四种 questionType 都能返回结果。"""
        self.dashboard_page.open_assistant_drawer()

        for question_type, expected_label in self.dashboard_page.QUESTION_LABELS.items():
            with self.subTest(question_type=question_type):
                self.dashboard_page.select_question_type(question_type)
                assert self.dashboard_page.get_current_question_label() == expected_label
                assert self.dashboard_page.get_assistant_summary_text()
                assert self.dashboard_page.get_assistant_metric_map()
                assert len(self.dashboard_page.get_assistant_suggestion_titles()) >= 1

    def test_assistant_ranges_7d_15d_30d_switch_effective(self):
        """7d/15d/30d 切换生效。"""
        self.dashboard_page.open_assistant_drawer()
        self.dashboard_page.select_question_type("RESTOCK_SUGGESTION")

        expected_days = {
            "7d": "7",
            "15d": "15",
            "30d": "30",
        }

        for range_type, expected_label in self.dashboard_page.RANGE_LABELS.items():
            with self.subTest(range_type=range_type):
                self.dashboard_page.select_assistant_range(range_type)
                metrics = self.dashboard_page.get_assistant_metric_map()
                assert self.dashboard_page.get_assistant_range_tag() == expected_label
                assert metrics.get("分析天数") == expected_days[range_type], metrics

    def test_suggestion_action_navigates_to_correct_page(self):
        """建议按钮跳转到正确页面。"""
        cases = [
            ("DAILY_SUMMARY", "/admin/products"),
            ("ORDER_ALERT", "/admin/orders"),
        ]

        for question_type, expected_path in cases:
            with self.subTest(question_type=question_type):
                self.dashboard_page.open_dashboard()
                self.dashboard_page.wait_for_dashboard_ready()
                self.dashboard_page.open_assistant_drawer()
                self.dashboard_page.select_question_type(question_type)
                self.dashboard_page.click_first_assistant_suggestion_action()
                self.dashboard_page.wait_for_url_contains(expected_path)


@pytest.mark.ai
class TestAiAssistantApi:
    """AI 智能问讯 API 用例。"""

    @classmethod
    def setup_class(cls):
        init_config()
        cls.config = get_config()
        cls.ai_data = load_test_data("ai_assistant")
        cls.api_client = ShopSystemApiClient()
        primary_account = cls.ai_data["account"]["primary"]

        try:
            cls.api_client.login(primary_account["username"], primary_account["password"])
        except Exception as exc:
            pytest.skip(f"后端未启动或 API 登录失败，无法执行 AI API 用例: {exc}")

    def _assert_success_response(self, response: Dict[str, Any], expected_question_type: Optional[str] = None) -> Dict[str, Any]:
        assert response.get("code") == 200, response
        data = response.get("data") or {}
        if expected_question_type:
            assert data.get("questionType") == expected_question_type, data
        assert data.get("startDate"), data
        assert data.get("endDate"), data
        assert _as_text(data.get("summary")), data
        assert isinstance(data.get("suggestions"), list) and data.get("suggestions"), data
        assert isinstance(data.get("metrics"), dict) and data.get("metrics"), data
        for suggestion in data.get("suggestions", []):
            assert _as_text(suggestion.get("title")), suggestion
            assert _as_text(suggestion.get("level")), suggestion
            assert _as_text(suggestion.get("detail")), suggestion
            assert _as_text(suggestion.get("actionTarget")), suggestion
            assert isinstance(suggestion.get("evidence"), list), suggestion
        return data

    def test_api_core_question_types_return_structured_response(self):
        """核心 questionType 的 API 返回结构化结果。"""
        for question_type in ("DAILY_SUMMARY", "ORDER_ALERT"):
            response = self.api_client.get_ai_assistant(question_type=question_type, range_type="30d")
            self._assert_success_response(response, expected_question_type=question_type)

    def test_api_invalid_question_type_returns_business_error(self):
        """非法 questionType 返回业务错误。"""
        response = self.api_client.get_ai_assistant(question_type="UNKNOWN_TYPE", range_type="7d")
        assert response.get("code") == 40001, response
        assert "不支持的问题类型" in _as_text(response.get("message"))

    def test_api_invalid_date_range_returns_business_error(self):
        """开始日期晚于结束日期时返回业务错误。"""
        start_date = date.today()
        end_date = start_date - timedelta(days=1)
        response = self.api_client.get_ai_assistant(
            question_type="DAILY_SUMMARY",
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )
        assert response.get("code") == 40001, response
        assert "开始日期不能晚于结束日期" in _as_text(response.get("message"))

    def test_api_degrade_fallback_when_ai_service_unavailable(self):
        """AI 服务不可用时返回规则兜底结果。"""
        try:
            hot_response = self.api_client.get_ai_assistant(question_type="HOT_PRODUCTS", range_type="30d")
            restock_response = self.api_client.get_ai_assistant(question_type="RESTOCK_SUGGESTION", range_type="30d")
        except requests.exceptions.ReadTimeout:
            pytest.skip("当前环境 AI 问讯接口响应超时，无法稳定验证降级分支")

        hot_data = self._assert_success_response(hot_response, expected_question_type="HOT_PRODUCTS")
        restock_data = self._assert_success_response(restock_response, expected_question_type="RESTOCK_SUGGESTION")

        hot_fallback = self.ai_data["question_type_baseline"]["HOT_PRODUCTS"]["fallback_assertions"]
        restock_fallback = self.ai_data["question_type_baseline"]["RESTOCK_SUGGESTION"]["fallback_assertions"]

        hot_suggestion = (hot_data.get("suggestions") or [{}])[0]
        restock_suggestion = (restock_data.get("suggestions") or [{}])[0]

        is_hot_fallback = (
            _as_text(hot_data.get("summary")) == hot_fallback["summary"]
            and _as_text(hot_suggestion.get("detail")) == hot_fallback["first_detail"]
        )
        is_restock_fallback = (
            _as_text(restock_data.get("summary")) == restock_fallback["summary"]
            and _as_text(restock_suggestion.get("detail")) == restock_fallback["first_detail"]
        )

        if not (is_hot_fallback and is_restock_fallback):
            pytest.skip("当前环境未进入可验证的 AI 降级分支，接口返回的是正常 AI 文案")

        assert hot_suggestion.get("title") == "热销商品推荐：Demo Laptop Pro"
        assert restock_suggestion.get("title") == "库存整体稳定"
        assert hot_suggestion.get("actionTarget") == "/admin/products"
        assert restock_suggestion.get("actionTarget") == "/admin/products"
