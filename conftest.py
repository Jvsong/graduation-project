from __future__ import annotations

import base64
import html
import sys
from datetime import datetime
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parent
AUTOTEST_ROOT = PROJECT_ROOT / "ecommerce-autotest"
DEFAULT_REPORT_ROOT = PROJECT_ROOT / "reports" / "html"

autotest_root_str = str(AUTOTEST_ROOT)
if autotest_root_str not in sys.path:
    sys.path.insert(0, autotest_root_str)


def _get_driver_from_item(item):
    driver = item.funcargs.get("driver") if hasattr(item, "funcargs") else None
    if driver:
        return driver

    instance = getattr(item, "instance", None)
    if instance is not None:
        driver = getattr(instance, "driver", None)
        if driver:
            return driver

    cls = getattr(item, "cls", None)
    if cls is not None:
        driver = getattr(cls, "driver", None)
        if driver:
            return driver

    return None


def _resolve_report_root() -> Path:
    from utils.config_manager import get_config, init_config

    init_config()
    config = get_config()
    output_dir = config.get("report.output_dir", "./reports")
    report_root = (PROJECT_ROOT / output_dir).resolve() / "html"
    report_root.mkdir(parents=True, exist_ok=True)
    return report_root


def _sanitize_report_name(raw_name: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in raw_name)
    cleaned = cleaned.strip("._-")
    return cleaned or "all"


def _infer_report_label(pytest_args: tuple[str, ...]) -> str:
    positional_args = [arg for arg in pytest_args if arg and not arg.startswith("-")]
    if positional_args:
        candidate = Path(positional_args[-1]).stem
        return _sanitize_report_name(candidate)

    for index, arg in enumerate(pytest_args):
        if arg == "-m" and index + 1 < len(pytest_args):
            return _sanitize_report_name(f"mark_{pytest_args[index + 1]}")
        if arg.startswith("-m") and len(arg) > 2:
            return _sanitize_report_name(f"mark_{arg[2:]}")

    return "all"


def _build_report_path(config: pytest.Config) -> Path:
    report_root = _resolve_report_root()
    report_label = _infer_report_label(tuple(config.invocation_params.args))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return report_root / f"{report_label}_{timestamp}.html"


def _build_screenshot_path(item) -> Path:
    from utils.config_manager import get_config, init_config

    init_config()
    config = get_config()
    screenshot_dir = config.get("test.screenshot_path", "./reports/screenshots")
    screenshot_root = (PROJECT_ROOT / screenshot_dir).resolve()
    screenshot_root.mkdir(parents=True, exist_ok=True)

    safe_name = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in item.nodeid)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return screenshot_root / f"{safe_name}_{timestamp}.png"


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when != "call" or report.passed:
        return

    driver = _get_driver_from_item(item)
    if driver is None:
        return

    try:
        png_bytes = driver.get_screenshot_as_png()
        screenshot_path = _build_screenshot_path(item)
        screenshot_path.write_bytes(png_bytes)

        extras = getattr(report, "extras", [])
        base64_image = base64.b64encode(png_bytes).decode("utf-8")
        escaped_path = html.escape(str(screenshot_path))
        file_uri = "file:///" + escaped_path.replace("\\", "/")

        extras.append(
            pytest_html.extras.html(
                (
                    '<div class="failed-screenshot">'
                    '<div><strong>失败截图</strong></div>'
                    f'<div><a href="{file_uri}" target="_blank">'
                    "打开原图</a></div>"
                    f'<img src="data:image/png;base64,{base64_image}" '
                    'alt="failed screenshot" '
                    'style="margin-top:8px; max-width:100%; border:1px solid #ddd;" />'
                    "</div>"
                )
            )
        )
        report.extras = extras
    except Exception:
        # 报告增强失败时不影响原始测试结果
        return


def pytest_configure(config):
    global pytest_html
    pytest_html = config.pluginmanager.getplugin("html")

    if pytest_html is None:
        return

    if not getattr(config.option, "htmlpath", None):
        config.option.htmlpath = str(_build_report_path(config))

    if not getattr(config.option, "self_contained_html", False):
        config.option.self_contained_html = True


@pytest.fixture
def driver():
    from utils.browser_factory import BrowserFactory
    from utils.config_manager import get_config, init_config

    init_config()
    config = get_config()

    factory = BrowserFactory()
    web_driver = factory.create_driver(
        browser_name=config.get("browser.name", "chrome"),
        headless=config.get("browser.headless", False),
        window_size=config.get("browser.window_size"),
        implicit_wait=config.get("browser.implicit_wait", 10),
        page_load_timeout=config.get("browser.page_load_timeout", 30),
    )

    try:
        yield web_driver
    finally:
        try:
            web_driver.quit()
        except Exception:
            pass
