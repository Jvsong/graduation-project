#!/usr/bin/env python3
"""
浏览器工厂
为测试框架统一创建 WebDriver 实例
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService


class BrowserFactory:
    """创建浏览器驱动实例。"""

    def create_driver(
        self,
        browser_name: str = "edge",
        headless: bool = False,
        window_size: Optional[str] = None,
        implicit_wait: int = 10,
        page_load_timeout: int = 30,
        **_: object,
    ):
        browser = (browser_name or "edge").lower()

        if browser == "chrome":
            driver = self._create_chrome_driver(headless=headless, window_size=window_size)
        elif browser == "edge":
            driver = self._create_edge_driver(headless=headless, window_size=window_size)
        elif browser == "firefox":
            driver = self._create_firefox_driver(headless=headless, window_size=window_size)
        else:
            raise ValueError(f"不支持的浏览器类型: {browser_name}")

        driver.implicitly_wait(implicit_wait)
        driver.set_page_load_timeout(page_load_timeout)
        return driver

    def _create_chrome_driver(self, headless: bool, window_size: Optional[str]):
        options = ChromeOptions()
        binary = self._first_existing_path(
            [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            ]
        )
        if binary:
            options.binary_location = binary

        self._apply_common_chromium_options(options, headless, window_size)
        service = ChromeService(executable_path=self._find_chromedriver())
        return webdriver.Chrome(service=service, options=options)

    def _create_edge_driver(self, headless: bool, window_size: Optional[str]):
        options = EdgeOptions()
        binary = self._first_existing_path(
            [
                r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            ]
        )
        if binary:
            options.binary_location = binary

        self._apply_common_chromium_options(options, headless, window_size)
        service = EdgeService(executable_path=self._find_edgedriver())
        return webdriver.Edge(service=service, options=options)

    def _create_firefox_driver(self, headless: bool, window_size: Optional[str]):
        options = FirefoxOptions()
        binary = self._first_existing_path(
            [
                r"C:\Program Files\Mozilla Firefox\firefox.exe",
                r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
            ]
        )
        if binary:
            options.binary_location = binary

        if headless:
            options.add_argument("-headless")

        service = FirefoxService(executable_path=self._find_geckodriver())
        driver = webdriver.Firefox(service=service, options=options)
        if window_size and "x" in window_size.lower():
            width, height = window_size.lower().split("x", 1)
            driver.set_window_size(int(width), int(height))
        return driver

    def _apply_common_chromium_options(self, options, headless: bool, window_size: Optional[str]) -> None:
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--remote-allow-origins=*")
        if headless:
            options.add_argument("--headless=new")
        if window_size and "x" in window_size.lower():
            options.add_argument(f"--window-size={window_size.lower().replace('x', ',')}")

    def _find_chromedriver(self) -> str:
        home = Path.home()
        candidates = sorted(home.glob(".wdm/drivers/chromedriver/win64/*/chromedriver-win32/chromedriver.exe"))
        if candidates:
            return str(candidates[-1])
        return "chromedriver"

    def _find_edgedriver(self) -> str:
        home = Path.home()
        candidates = sorted(home.glob(".cache/selenium/msedgedriver/win64/*/msedgedriver.exe"))
        if candidates:
            return str(candidates[-1])
        return "msedgedriver"

    def _find_geckodriver(self) -> str:
        home = Path.home()
        candidates = sorted(home.glob(".wdm/drivers/geckodriver/win64/*/geckodriver.exe"))
        if candidates:
            return str(candidates[-1])
        return "geckodriver"

    def _first_existing_path(self, paths: list[str]) -> Optional[str]:
        for raw_path in paths:
            path = Path(raw_path)
            if path.exists():
                return str(path)
        return None
