#!/usr/bin/env python3
"""
shop-system Dashboard AI 页面对象。
"""

import time
from typing import Dict, List, Optional

from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class DashboardAIPage(BasePage):
    """封装 Dashboard 摘要区与智能问讯抽屉操作。"""

    url = "/admin/dashboard"

    DASHBOARD_ROOT = (By.CSS_SELECTOR, ".dashboard-container")
    SUMMARY_TITLE = (
        By.XPATH,
        "//article[contains(@class,'summary-card')]//h2[normalize-space()='今日运营摘要']",
    )
    SUMMARY_TEXT = (By.CSS_SELECTOR, ".summary-card .summary-text")
    SUMMARY_RANGE_TAG = (By.CSS_SELECTOR, ".summary-card .el-tag")
    SUMMARY_SIGNAL_ITEMS = (By.CSS_SELECTOR, ".signal-list .signal-item")

    OPEN_ASSISTANT_BUTTON = (
        By.XPATH,
        "//button[.//span[normalize-space()='打开智能问讯'] or normalize-space()='打开智能问讯']",
    )
    ASSISTANT_DRAWER = (By.CSS_SELECTOR, ".assistant-panel")
    ASSISTANT_DRAWER_TITLE = (
        By.XPATH,
        "//div[contains(@class,'assistant-panel__header')]//h2[normalize-space()='智能问讯窗口']",
    )
    ASSISTANT_CURRENT_LABEL = (By.CSS_SELECTOR, ".assistant-panel__desc")
    ASSISTANT_SUMMARY_TAG = (By.CSS_SELECTOR, ".assistant-summary__tag")
    ASSISTANT_SUMMARY_TEXT = (By.CSS_SELECTOR, ".assistant-summary p")
    ASSISTANT_SUGGESTIONS = (By.CSS_SELECTOR, ".assistant-suggestions .assistant-suggestion")
    ASSISTANT_METRICS = (By.CSS_SELECTOR, ".assistant-metrics .assistant-metric")
    ASSISTANT_RANGE_SELECT = (By.CSS_SELECTOR, ".assistant-toolbar__select")
    ASSISTANT_LOADING_MASK = (By.CSS_SELECTOR, ".assistant-result .el-loading-mask")

    QUESTION_LABELS = {
        "DAILY_SUMMARY": "今日运营建议",
        "HOT_PRODUCTS": "热销商品",
        "RESTOCK_SUGGESTION": "补货建议",
        "ORDER_ALERT": "异常提醒",
    }

    RANGE_LABELS = {
        "7d": "最近 7 天",
        "15d": "最近 15 天",
        "30d": "最近 30 天",
    }

    def open_dashboard(self, base_url: Optional[str] = None) -> None:
        if not base_url:
            from utils.config_manager import get_config

            config = get_config()
            base_url = config.get("environment.base_url", "http://localhost:3000")

        full_url = f"{base_url.rstrip('/')}{self.url}"
        self.logger.info(f"打开 Dashboard 页面: {full_url}")
        self.open(full_url)

    def wait_for_dashboard_ready(self, timeout: int = 20) -> None:
        self.wait_for_page_load(timeout)
        self.find_visible_element(self.DASHBOARD_ROOT, timeout=timeout)
        self.find_visible_element(self.SUMMARY_TITLE, timeout=timeout)
        self.wait_for_non_empty_text(self.SUMMARY_TEXT, timeout=timeout)

    def wait_for_non_empty_text(self, locator, timeout: int = 15, exclude_text: Optional[str] = None) -> str:
        end_time = time.time() + timeout
        last_text = ""
        while time.time() < end_time:
            try:
                text = self.get_text(locator, timeout=2).strip()
                last_text = text
                if text and (exclude_text is None or text != exclude_text):
                    return text
            except Exception:
                pass
            time.sleep(0.3)
        raise AssertionError(f"元素文本在 {timeout}s 内未达到预期: {locator}, last_text={last_text!r}")

    def get_daily_summary_text(self) -> str:
        return self.get_text(self.SUMMARY_TEXT).strip()

    def get_summary_range_label(self) -> str:
        return self.get_text(self.SUMMARY_RANGE_TAG).strip()

    def get_highlighted_suggestion_count(self) -> int:
        return len(self.find_elements(self.SUMMARY_SIGNAL_ITEMS, timeout=5))

    def open_assistant_drawer(self) -> None:
        self.safe_click(self.OPEN_ASSISTANT_BUTTON)
        self.find_visible_element(self.ASSISTANT_DRAWER, timeout=10)
        self.find_visible_element(self.ASSISTANT_DRAWER_TITLE, timeout=10)
        self.wait_for_assistant_result()

    def is_assistant_drawer_visible(self, timeout: int = 5) -> bool:
        return self.is_displayed(self.ASSISTANT_DRAWER, timeout=timeout)

    def wait_for_assistant_result(self, timeout: int = 15) -> None:
        self.wait_for_page_load(timeout)
        self.wait_for_element_disappear(self.ASSISTANT_LOADING_MASK, timeout=timeout)
        self.wait_for_non_empty_text(
            self.ASSISTANT_SUMMARY_TEXT,
            timeout=timeout,
            exclude_text="请选择一个问题开始问讯。",
        )

    def get_assistant_summary_text(self) -> str:
        return self.get_text(self.ASSISTANT_SUMMARY_TEXT).strip()

    def get_assistant_range_tag(self) -> str:
        return self.get_text(self.ASSISTANT_SUMMARY_TAG).strip()

    def get_current_question_label(self) -> str:
        return self.get_text(self.ASSISTANT_CURRENT_LABEL).strip()

    def select_question_type(self, question_type: str) -> None:
        label = self.QUESTION_LABELS[question_type]
        chip_locator = (
            By.XPATH,
            f"//button[contains(@class,'mini-chip')]//*[normalize-space()='{label}']"
            f"/ancestor::button[contains(@class,'mini-chip')]"
            f"|//button[contains(@class,'mini-chip')][normalize-space()='{label}']",
        )
        current_summary = self.get_assistant_summary_text() if self.is_assistant_drawer_visible(timeout=2) else ""
        self.safe_click(chip_locator)
        self.wait_for_assistant_result_change(previous_summary=current_summary)

    def wait_for_assistant_result_change(self, previous_summary: str = "", timeout: int = 15) -> None:
        end_time = time.time() + timeout
        while time.time() < end_time:
            try:
                self.wait_for_element_disappear(self.ASSISTANT_LOADING_MASK, timeout=2)
                summary = self.get_text(self.ASSISTANT_SUMMARY_TEXT, timeout=2).strip()
                if summary and (not previous_summary or summary != previous_summary):
                    return
                suggestions = self.find_elements(self.ASSISTANT_SUGGESTIONS, timeout=2)
                if summary and suggestions:
                    return
            except Exception:
                pass
            time.sleep(0.3)
        raise AssertionError("智能问讯结果未在预期时间内刷新")

    def open_range_dropdown(self) -> None:
        wrapper_locator = (
            By.CSS_SELECTOR,
            ".assistant-toolbar__select .el-select__wrapper, .assistant-toolbar__select .el-input__wrapper",
        )
        self.safe_click(wrapper_locator)

    def select_assistant_range(self, range_type: str) -> None:
        label = self.RANGE_LABELS[range_type]
        current_tag = self.get_assistant_range_tag() if self.is_assistant_drawer_visible(timeout=2) else ""
        self.open_range_dropdown()
        option_locator = (
            By.XPATH,
            f"//div[contains(@class,'el-select-dropdown')]//li[normalize-space()='{label}']"
            f"|//div[contains(@class,'el-select-dropdown')]//*[contains(@class,'el-select-dropdown__item') and normalize-space()='{label}']",
        )
        self.safe_click(option_locator)
        self.wait_for_range_tag(label, previous_tag=current_tag)

    def wait_for_range_tag(self, expected_label: str, previous_tag: str = "", timeout: int = 15) -> None:
        end_time = time.time() + timeout
        while time.time() < end_time:
            try:
                self.wait_for_element_disappear(self.ASSISTANT_LOADING_MASK, timeout=2)
                current_tag = self.get_text(self.ASSISTANT_SUMMARY_TAG, timeout=2).strip()
                if current_tag == expected_label and (not previous_tag or current_tag != previous_tag or expected_label == previous_tag):
                    return
            except Exception:
                pass
            time.sleep(0.3)
        raise AssertionError(f"时间范围未切换到: {expected_label}")

    def get_assistant_metric_map(self) -> Dict[str, str]:
        metrics: Dict[str, str] = {}
        cards = self.find_elements(self.ASSISTANT_METRICS, timeout=5)
        for card in cards:
            try:
                label = card.find_element(By.TAG_NAME, "span").text.strip()
                value = card.find_element(By.TAG_NAME, "strong").text.strip()
                if label:
                    metrics[label] = value
            except Exception:
                continue
        return metrics

    def get_assistant_suggestion_titles(self) -> List[str]:
        titles: List[str] = []
        cards = self.find_elements(self.ASSISTANT_SUGGESTIONS, timeout=5)
        for card in cards:
            try:
                title = card.find_element(By.TAG_NAME, "strong").text.strip()
                if title:
                    titles.append(title)
            except Exception:
                continue
        return titles

    def click_first_assistant_suggestion_action(self) -> None:
        locator = (
            By.CSS_SELECTOR,
            ".assistant-suggestions .assistant-suggestion .signal-link",
        )
        self.safe_click(locator)

    def wait_for_url_contains(self, expected_path: str, timeout: int = 10) -> None:
        end_time = time.time() + timeout
        while time.time() < end_time:
            if expected_path in self.get_current_url():
                return
            time.sleep(0.2)
        raise AssertionError(f"当前 URL 未跳转到预期路径: expected={expected_path}, actual={self.get_current_url()}")

    def safe_click(self, locator, timeout: int = 10) -> None:
        element = self.find_clickable_element(locator, timeout=timeout)
        try:
            element.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", element)
