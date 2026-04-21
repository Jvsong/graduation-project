#!/usr/bin/env python3
"""
shop-system API 调用工具。
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import requests

from utils.config_manager import get_config
from utils.logger import get_logger


class ShopSystemApiClient:
    """提供登录与 AI 问讯相关的 API 封装。"""

    def __init__(self, base_url: Optional[str] = None, timeout: Optional[int] = None):
        config = get_config()
        self.base_url = (base_url or config.get("environment.api_base_url", "http://localhost:8083/api")).rstrip("/")
        self.timeout = timeout or config.get("test.timeout", 30)
        self.session = requests.Session()
        self.logger = get_logger(self.__class__.__name__)
        self.token: Optional[str] = None

    def _build_url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return f"{self.base_url}/{path.lstrip('/')}"

    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        timeout = kwargs.pop("timeout", self.timeout)
        url = self._build_url(path)
        self.logger.info(f"API 请求: {method.upper()} {url}")
        response = self.session.request(method=method.upper(), url=url, timeout=timeout, **kwargs)
        self.logger.info(f"API 响应: {response.status_code} {url}")
        return response

    def request_json(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        response = self.request(method, path, **kwargs)
        try:
            return response.json()
        except ValueError as exc:
            raise AssertionError(f"接口未返回合法 JSON: {response.text[:500]}") from exc

    def login(self, username: str, password: str, remember_me: bool = False) -> Dict[str, Any]:
        payload = {
            "username": username,
            "password": password,
            "rememberMe": remember_me,
        }
        response = self.request_json("post", "/auth/login", json=payload)
        if response.get("code") != 200:
            raise AssertionError(f"API 登录失败: {response}")

        token = ((response.get("data") or {}).get("token")) or ""
        if not token:
            raise AssertionError(f"API 登录成功但未返回 token: {response}")

        self.token = token
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        return response

    def get_ai_assistant(
        self,
        question_type: Optional[str] = None,
        range_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if question_type is not None:
            params["questionType"] = question_type
        if range_type is not None:
            params["rangeType"] = range_type
        if start_date is not None:
            params["startDate"] = start_date
        if end_date is not None:
            params["endDate"] = end_date
        return self.request_json("get", "/admin/ai-assistant/ask", params=params)

    def get_order_statistics(self, start_date: str, end_date: str) -> Dict[str, Any]:
        return self.request_json(
            "get",
            "/admin/orders/statistics",
            params={"startDate": start_date, "endDate": end_date},
        )

    def get_restock_analysis(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if start_date is not None:
            params["startDate"] = start_date
        if end_date is not None:
            params["endDate"] = end_date
        return self.request_json("get", "/admin/orders/restock-analysis", params=params)
