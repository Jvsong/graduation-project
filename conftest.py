from __future__ import annotations

import base64
import html
import json
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


def _build_run_stamp() -> tuple[str, str]:
    now = datetime.now()
    return now.strftime("%Y-%m-%d"), now.strftime("%H%M%S")


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
    day_stamp, time_stamp = _build_run_stamp()
    report_dir = report_root / day_stamp / report_label / time_stamp
    report_dir.mkdir(parents=True, exist_ok=True)
    return report_dir / f"{report_label}.html"


def _build_screenshot_path(item) -> Path:
    from utils.config_manager import get_config, init_config

    init_config()
    config = get_config()
    screenshot_dir = config.get("test.screenshot_path", "./reports/screenshots")
    screenshot_root = (PROJECT_ROOT / screenshot_dir).resolve()
    day_stamp, _ = _build_run_stamp()
    module_name = _extract_module_name(item.nodeid)
    screenshot_root = screenshot_root / day_stamp / module_name
    screenshot_root.mkdir(parents=True, exist_ok=True)

    safe_name = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in item.nodeid)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return screenshot_root / f"{safe_name}_{timestamp}.png"


def _get_ai_store(config: pytest.Config) -> dict:
    store = getattr(config, "_ai_report_store", None)
    if store is None:
        store = {
            "start_time": None,
            "end_time": None,
            "tests": {},
            "report_json_path": None,
        }
        setattr(config, "_ai_report_store", store)
    return store


def _extract_module_name(nodeid: str) -> str:
    raw = nodeid.split("::", 1)[0]
    module_name = Path(raw).stem
    return module_name[5:] if module_name.startswith("test_") else module_name


def _build_json_report_path(config: pytest.Config) -> Path | None:
    html_path = getattr(config.option, "htmlpath", None)
    if not html_path:
        return None
    return Path(str(html_path)).with_suffix(".json")


def _to_file_uri(path_value: str) -> str:
    return Path(path_value).resolve().as_uri()


def _format_duration(seconds: float) -> str:
    return f"{seconds:.2f}s"


def _collect_failure_tests(test_items: list[dict]) -> list[dict]:
    return [item for item in test_items if item.get("status") in {"failed", "error"}]


def _build_ai_payload(config: pytest.Config) -> dict:
    from utils.ai_analysis import AIAnalysisService
    from utils.config_manager import get_config, init_config

    init_config()
    app_config = get_config()
    store = _get_ai_store(config)

    tests = list(store["tests"].values())
    tests.sort(key=lambda item: item.get("name", ""))

    total = len(tests)
    passed = sum(1 for item in tests if item.get("status") == "passed")
    failed = sum(1 for item in tests if item.get("status") == "failed")
    error = sum(1 for item in tests if item.get("status") == "error")
    skipped = sum(1 for item in tests if item.get("status") == "skipped")
    total_duration = sum(float(item.get("duration") or 0.0) for item in tests)

    module_map: dict[str, dict] = {}
    for item in tests:
        module = item.get("module") or "unknown"
        stats = module_map.setdefault(
            module,
            {
                "name": module,
                "total": 0,
                "passed": 0,
                "failed": 0,
                "error": 0,
                "skipped": 0,
                "pass_rate": 0.0,
            },
        )
        stats["total"] += 1
        status = item.get("status")
        if status == "passed":
            stats["passed"] += 1
        elif status == "failed":
            stats["failed"] += 1
        elif status == "error":
            stats["error"] += 1
        elif status == "skipped":
            stats["skipped"] += 1

    module_stats = []
    for module_name, stats in module_map.items():
        total_count = stats["total"]
        stats["pass_rate"] = round((stats["passed"] / total_count * 100) if total_count else 0.0, 2)
        module_stats.append(stats)
    module_stats.sort(key=lambda item: item["pass_rate"])

    failed_tests = _collect_failure_tests(tests)
    ai_service = AIAnalysisService(app_config)
    analyzed_failures = failed_tests
    ai_summary = {}

    if app_config.get("ai.analyze_failures", True):
        analyzed_failures = ai_service.analyze_failures(failed_tests)

    if app_config.get("ai.generate_summary", True):
        ai_summary = ai_service.summarize_report(
            {
                "project": {
                    "name": app_config.get("project.name", "电商后台自动化测试系统"),
                    "version": app_config.get("project.version", "1.0.0"),
                },
                "execution": {
                    "start_time": store["start_time"].isoformat() if store["start_time"] else "",
                    "end_time": store["end_time"].isoformat() if store["end_time"] else "",
                    "duration": _format_duration(total_duration),
                    "environment": app_config.get("environment.test_env", "test"),
                    "browser": app_config.get("browser.name", "chrome"),
                },
                "stats": {
                    "total_tests": total,
                    "passed_tests": passed,
                    "failed_tests": failed,
                    "error_tests": error,
                    "skipped_tests": skipped,
                    "pass_rate": round((passed / total * 100) if total else 0.0, 2),
                },
                "module_stats": module_stats,
                "failed_tests": analyzed_failures,
            }
        )

    failure_map = {item["name"]: item for item in analyzed_failures}
    merged_tests = []
    for item in tests:
        merged = dict(item)
        if item["name"] in failure_map:
            merged["ai_analysis"] = failure_map[item["name"]].get("ai_analysis", {})
        merged_tests.append(merged)

    return {
        "project": {
            "name": app_config.get("project.name", "电商后台自动化测试系统"),
            "version": app_config.get("project.version", "1.0.0"),
        },
        "execution": {
            "start_time": store["start_time"].isoformat() if store["start_time"] else "",
            "end_time": store["end_time"].isoformat() if store["end_time"] else "",
            "duration": _format_duration(total_duration),
            "environment": app_config.get("environment.test_env", "test"),
            "browser": app_config.get("browser.name", "chrome"),
            "total_duration": _format_duration(total_duration),
            "average_duration": _format_duration(total_duration / total) if total else "0.00s",
            "retry_count": app_config.get("test.retry_count", 0),
            "execution_mode": "parallel" if getattr(config.option, "numprocesses", 0) not in (0, 1, None) else "sequential",
        },
        "stats": {
            "total_tests": total,
            "passed_tests": passed,
            "failed_tests": failed,
            "error_tests": error,
            "skipped_tests": skipped,
            "pass_rate": round((passed / total * 100) if total else 0.0, 2),
        },
        "module_stats": module_stats,
        "test_results": merged_tests,
        "failed_tests": analyzed_failures,
        "ai_summary": ai_summary,
        "generated_at": datetime.now().isoformat(),
    }


def _build_ai_html(payload: dict) -> str:
    summary = payload.get("ai_summary", {}) or {}
    failed_tests = payload.get("failed_tests", []) or []
    execution = payload.get("execution", {}) or {}
    stats = payload.get("stats", {}) or {}
    module_stats = payload.get("module_stats", []) or []
    json_path = payload.get("report_json_path", "")
    summary_service_error = summary.get("service_error", "")

    nav_html = (
        '<nav class="ai-report-nav">'
        '<a href="#ai-overview">总览</a>'
        '<a href="#ai-modules">模块风险</a>'
        '<a href="#ai-failures">失败分析</a>'
        '<a href="#ai-details">执行详情</a>'
    )
    if json_path:
        nav_html += f'<a href="{html.escape(_to_file_uri(json_path))}" target="_blank">JSON 数据</a>'
    nav_html += '</nav>'

    overview_cards = (
        '<div class="ai-overview-cards">'
        f'<div class="ai-overview-card"><span>通过率</span><strong>{stats.get("pass_rate", 0)}%</strong></div>'
        f'<div class="ai-overview-card"><span>测试总数</span><strong>{stats.get("total_tests", 0)}</strong></div>'
        f'<div class="ai-overview-card"><span>失败 / 错误</span><strong>{stats.get("failed_tests", 0)} / {stats.get("error_tests", 0)}</strong></div>'
        f'<div class="ai-overview-card"><span>执行时长</span><strong>{html.escape(str(execution.get("total_duration", "-")))}</strong></div>'
        '</div>'
    )

    summary_html = (
        '<section id="ai-overview" class="ai-report-section ai-hero-section">'
        '<div class="ai-section-header"><div><p class="ai-eyebrow">AI Enhanced Report</p><h2>智能测试总览</h2></div>'
        f'<div class="ai-run-meta">{html.escape(str(execution.get("environment", "test")))} | {html.escape(str(execution.get("browser", "chrome")))} | {html.escape(str(execution.get("execution_mode", "sequential")))}</div></div>'
        f'{overview_cards}'
        '<div class="ai-summary-layout">'
        f'<div class="ai-summary-panel"><h3>结论</h3><p class="ai-summary">{html.escape(summary.get("summary", "本次未生成 AI 摘要。"))}</p></div>'
        '<div class="ai-summary-grid">'
        f'<div><strong>高风险模块</strong><div>{html.escape("、".join(summary.get("risk_modules", [])) or "无")}</div></div>'
        f'<div><strong>回归建议</strong><div>{html.escape(summary.get("rerun_suggestion", "无"))}</div></div>'
        '</div>'
        '</div>'
        '<div class="ai-inline-title">建议处理项</div>'
        '<ul class="ai-recommendations">'
    )
    if summary_service_error:
        summary_html += f'<div class="ai-service-warning"><strong>AI 服务状态：</strong>{html.escape(summary_service_error)}</div>'

    recommendations = summary.get("recommendations", [])
    if recommendations:
        summary_html += "".join(f"<li>{html.escape(str(item))}</li>" for item in recommendations)
    else:
        summary_html += "<li>无</li>"
    summary_html += "</ul></section>"

    module_rows = []
    for module in module_stats:
        module_rows.append(
            "<tr>"
            f"<td>{html.escape(str(module.get('name', 'unknown')))}</td>"
            f"<td>{module.get('total', 0)}</td>"
            f"<td>{module.get('passed', 0)}</td>"
            f"<td>{module.get('failed', 0)}</td>"
            f"<td>{module.get('error', 0)}</td>"
            f"<td>{module.get('pass_rate', 0)}%</td>"
            "</tr>"
        )
    module_rows_html = "".join(module_rows) if module_rows else '<tr><td colspan="6">暂无模块数据</td></tr>'

    modules_html = (
        '<section id="ai-modules" class="ai-report-section">'
        '<div class="ai-section-header"><div><p class="ai-eyebrow">Module View</p><h2>模块风险概览</h2></div></div>'
        '<div class="ai-table-wrap"><table class="ai-table">'
        '<thead><tr><th>模块</th><th>总数</th><th>通过</th><th>失败</th><th>错误</th><th>通过率</th></tr></thead>'
        f"<tbody>{module_rows_html}</tbody>"
        '</table></div></section>'
    )

    failure_html = [
        '<section id="ai-failures" class="ai-report-section">',
        '<div class="ai-section-header"><div><p class="ai-eyebrow">Failure Insight</p><h2>AI 失败分析</h2></div></div>',
    ]
    if not failed_tests:
        failure_html.append('<div class="ai-empty">本轮没有失败用例。</div>')
    else:
        for item in failed_tests:
            analysis = item.get("ai_analysis", {}) or {}
            screenshot = item.get("screenshot", "")
            screenshot_link = ""
            if screenshot:
                screenshot_link = f'<a class="ai-link" href="{html.escape(_to_file_uri(screenshot))}" target="_blank">打开失败截图</a>'
            service_error_html = ""
            if analysis.get("service_error"):
                service_error_html = f'<p class="ai-service-warning"><strong>服务异常：</strong>{html.escape(str(analysis.get("service_error", "")))}</p>'
            failure_html.append(
                '<div class="ai-failure-card">'
                f'<div class="ai-failure-head"><h3>{html.escape(item.get("name", ""))}</h3>'
                f'<span class="ai-severity ai-severity-{html.escape(str(analysis.get("severity", "medium")).lower())}">{html.escape(str(analysis.get("severity", "medium")).upper())}</span></div>'
                f'<div class="ai-meta">模块：{html.escape(item.get("module", ""))} | 状态：{html.escape(item.get("status", ""))}</div>'
                f'<p><strong>分析来源：</strong>{html.escape(str(analysis.get("source", "unknown")))}</p>'
                f'<p><strong>原始错误：</strong>{html.escape(item.get("error_message", "") or "无")}</p>'
                f'<p><strong>失败原因：</strong>{html.escape(str(analysis.get("root_cause", "无法确定")))}</p>'
                f'<p><strong>疑似位置：</strong>{html.escape(str(analysis.get("location", "无法确定")))}</p>'
                f'<p><strong>修复建议：</strong>{html.escape(str(analysis.get("fix_suggestion", "请结合原始日志排查")))}</p>'
                f'<p><strong>风险等级：</strong>{html.escape(str(analysis.get("severity", "medium")))} '
                f'| <strong>置信度：</strong>{analysis.get("confidence", 0.0)}</p>'
                f'{service_error_html}'
                f'{screenshot_link}'
                '</div>'
            )
    failure_html.append("</section>")

    details_html = (
        '<section id="ai-details" class="ai-report-section">'
        '<div class="ai-section-header"><div><p class="ai-eyebrow">Execution</p><h2>执行详情</h2></div></div>'
        '<div class="ai-detail-grid">'
        f'<div><span>开始时间</span><strong>{html.escape(str(execution.get("start_time", "-")))}</strong></div>'
        f'<div><span>结束时间</span><strong>{html.escape(str(execution.get("end_time", "-")))}</strong></div>'
        f'<div><span>平均耗时</span><strong>{html.escape(str(execution.get("average_duration", "-")))}</strong></div>'
        f'<div><span>重试次数</span><strong>{html.escape(str(execution.get("retry_count", 0)))}</strong></div>'
        '</div></section>'
    )

    style = """
<style>
.ai-report-anchor { position: relative; top: -12px; }
.ai-report-shell { margin: 28px 0 20px; color: #0f172a; font-family: "Segoe UI", "Microsoft YaHei", sans-serif; }
.ai-report-nav { position: sticky; top: 12px; z-index: 30; display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 18px; padding: 14px 16px; background: rgba(15, 23, 42, 0.9); backdrop-filter: blur(10px); border-radius: 16px; box-shadow: 0 12px 32px rgba(15, 23, 42, 0.22); }
.ai-report-nav a { color: #eff6ff; text-decoration: none; font-size: 13px; padding: 8px 12px; border-radius: 999px; background: rgba(255,255,255,0.08); }
.ai-report-nav a:hover { background: rgba(255,255,255,0.18); }
.ai-report-section { margin: 18px 0; padding: 24px; background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%); border: 1px solid #dbeafe; border-radius: 22px; box-shadow: 0 14px 36px rgba(15, 23, 42, 0.08); }
.ai-hero-section { background: radial-gradient(circle at top left, #e0f2fe 0%, #f8fbff 48%, #ffffff 100%); }
.ai-section-header { display: flex; justify-content: space-between; gap: 18px; align-items: flex-start; margin-bottom: 16px; }
.ai-eyebrow { margin: 0 0 6px; color: #2563eb; font-size: 12px; letter-spacing: 0.18em; text-transform: uppercase; font-weight: 700; }
.ai-report-section h2 { margin: 0; color: #0f172a; font-size: 28px; }
.ai-run-meta { color: #475569; font-size: 14px; }
.ai-overview-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 14px; margin-bottom: 18px; }
.ai-overview-card { padding: 16px 18px; background: rgba(255,255,255,0.9); border-radius: 18px; border: 1px solid #e2e8f0; }
.ai-overview-card span { display: block; color: #64748b; font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px; }
.ai-overview-card strong { font-size: 28px; color: #0f172a; }
.ai-summary-layout { display: grid; grid-template-columns: 1.6fr 1fr; gap: 16px; margin-bottom: 16px; }
.ai-summary-panel { padding: 18px; border-radius: 18px; background: rgba(255,255,255,0.9); border: 1px solid #e2e8f0; }
.ai-summary-panel h3 { margin: 0 0 10px; font-size: 16px; color: #1e3a8a; }
.ai-summary { margin-bottom: 0; line-height: 1.8; font-size: 15px; color: #334155; }
.ai-summary-grid { display: grid; gap: 12px; }
.ai-summary-grid > div { padding: 16px; background: rgba(255,255,255,0.9); border-radius: 18px; border: 1px solid #e2e8f0; line-height: 1.7; }
.ai-inline-title { margin-bottom: 10px; font-weight: 700; color: #1e293b; }
.ai-recommendations { margin: 0; padding-left: 20px; color: #334155; line-height: 1.8; }
.ai-table-wrap { overflow-x: auto; }
.ai-table { width: 100%; border-collapse: collapse; }
.ai-table th, .ai-table td { padding: 12px 14px; border-bottom: 1px solid #e2e8f0; text-align: left; }
.ai-table th { color: #334155; background: #eff6ff; font-size: 13px; text-transform: uppercase; letter-spacing: 0.04em; }
.ai-failure-card { margin-top: 14px; padding: 18px; background: #fff; border: 1px solid #e2e8f0; border-radius: 18px; box-shadow: 0 8px 20px rgba(15, 23, 42, 0.05); }
.ai-failure-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 8px; }
.ai-failure-card h3 { margin: 0; font-size: 17px; color: #0f172a; }
.ai-meta { margin-bottom: 10px; color: #64748b; font-size: 13px; }
.ai-severity { display: inline-flex; align-items: center; justify-content: center; min-width: 74px; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; }
.ai-severity-low { background: #dcfce7; color: #166534; }
.ai-severity-medium { background: #fef3c7; color: #92400e; }
.ai-severity-high { background: #fee2e2; color: #991b1b; }
.ai-link { display: inline-block; margin-top: 8px; color: #2563eb; text-decoration: none; font-weight: 600; }
.ai-link:hover { text-decoration: underline; }
.ai-service-warning { margin: 12px 0; padding: 12px 14px; border-radius: 14px; background: #fff7ed; color: #9a3412; border: 1px solid #fed7aa; }
.ai-detail-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; }
.ai-detail-grid > div { padding: 16px; background: #fff; border: 1px solid #e2e8f0; border-radius: 18px; }
.ai-detail-grid span { display: block; margin-bottom: 8px; color: #64748b; font-size: 12px; text-transform: uppercase; letter-spacing: 0.06em; }
.ai-detail-grid strong { font-size: 16px; color: #0f172a; }
.ai-empty { padding: 20px; border-radius: 16px; background: #f8fafc; color: #64748b; text-align: center; }
@media (max-width: 900px) { .ai-summary-layout { grid-template-columns: 1fr; } .ai-section-header { flex-direction: column; } }
</style>
"""
    shell_open = '<div class="ai-report-shell"><span class="ai-report-anchor" id="ai-report-top"></span>'
    shell_close = '</div>'
    return style + shell_open + nav_html + summary_html + modules_html + "".join(failure_html) + details_html + shell_close


def _build_pytest_html_theme_assets() -> str:
    """构建 pytest-html 统一主题样式和增强脚本。"""
    return """
<style id="codex-pytest-theme">
body {
  margin: 0;
  padding: 28px;
  background:
    radial-gradient(circle at top left, rgba(59,130,246,0.15), transparent 30%),
    linear-gradient(180deg, #f3f8ff 0%, #eef4ff 24%, #f8fafc 100%);
  color: #0f172a;
  font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
}
body.codex-themed-report {
  max-width: 1480px;
  margin: 0 auto;
}
#title {
  margin: 0;
  font-size: 34px;
  line-height: 1.15;
  letter-spacing: -0.03em;
  color: #0f172a;
}
#title + p {
  margin: 10px 0 0;
  color: #475569;
  font-size: 14px;
}
#title + p a {
  color: #2563eb;
  text-decoration: none;
}
#environment-header h2,
.summary__data h2 {
  margin: 0;
  font-size: 22px;
  color: #0f172a;
}
.report-hero {
  margin-bottom: 22px;
  padding: 28px 30px;
  border-radius: 28px;
  background: linear-gradient(135deg, rgba(255,255,255,0.98), rgba(239,246,255,0.92));
  box-shadow: 0 22px 48px rgba(15,23,42,0.1);
  border: 1px solid rgba(191,219,254,0.9);
}
.report-hero__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  margin-top: 18px;
}
.report-hero__pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border-radius: 999px;
  font-size: 13px;
  color: #1e293b;
  background: rgba(255,255,255,0.88);
  border: 1px solid #dbeafe;
}
#environment-header,
#environment {
  margin-top: 18px;
}
#environment {
  width: 100%;
  border-collapse: collapse;
  overflow: hidden;
  border-radius: 18px;
  background: rgba(255,255,255,0.92);
  box-shadow: 0 10px 28px rgba(15,23,42,0.06);
}
#environment tr:nth-child(odd) {
  background: rgba(248,250,252,0.9);
}
#environment td {
  padding: 12px 16px;
  border-bottom: 1px solid #e2e8f0;
}
.summary {
  margin: 26px 0 22px;
  padding: 24px 26px;
  border-radius: 24px;
  background: rgba(255,255,255,0.92);
  box-shadow: 0 18px 40px rgba(15,23,42,0.08);
  border: 1px solid #dbeafe;
}
.summary__data {
  display: grid;
  gap: 16px;
}
.summary__spacer {
  display: none;
}
.run-count,
.filter {
  margin: 0;
  color: #475569;
}
.controls {
  display: grid;
  gap: 16px;
}
.filters,
.collapse {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px 12px;
}
.filters input.filter {
  display: none;
}
.filters span,
.collapse button,
#show_all_details,
#hide_all_details {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 38px;
  padding: 0 14px;
  border-radius: 999px;
  border: 1px solid #dbeafe;
  background: #f8fbff;
  color: #1e293b;
  font-size: 13px;
  font-weight: 600;
}
.filters .passed { background: #ecfdf3; color: #166534; border-color: #bbf7d0; }
.filters .failed { background: #fef2f2; color: #991b1b; border-color: #fecaca; }
.filters .skipped { background: #fff7ed; color: #9a3412; border-color: #fed7aa; }
.filters .xfailed,
.filters .rerun { background: #faf5ff; color: #6b21a8; border-color: #e9d5ff; }
.filters .error,
.filters .xpassed { background: #fff1f2; color: #9f1239; border-color: #fecdd3; }
.collapse button,
#show_all_details,
#hide_all_details {
  cursor: pointer;
  transition: all 0.2s ease;
}
.collapse button:hover,
#show_all_details:hover,
#hide_all_details:hover {
  background: #2563eb;
  color: #fff;
  border-color: #2563eb;
}
#results-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0 12px;
}
#results-table-head th {
  position: sticky;
  top: 10px;
  z-index: 15;
  padding: 14px 16px;
  background: #0f172a;
  color: #eff6ff;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  border: 0;
}
#results-table-head th:first-child { border-radius: 16px 0 0 16px; }
#results-table-head th:last-child { border-radius: 0 16px 16px 0; }
.results-table-row .collapsible td {
  padding: 16px;
  background: rgba(255,255,255,0.95);
  border-top: 1px solid #e2e8f0;
  border-bottom: 1px solid #e2e8f0;
  color: #1e293b;
  vertical-align: top;
}
.results-table-row .collapsible td:first-child {
  border-left: 1px solid #e2e8f0;
  border-radius: 18px 0 0 18px;
  font-weight: 700;
}
.results-table-row .collapsible td:last-child {
  border-right: 1px solid #e2e8f0;
  border-radius: 0 18px 18px 0;
}
.results-table-row .collapsible:hover td {
  transform: translateY(-1px);
  box-shadow: 0 10px 24px rgba(15,23,42,0.05);
}
.results-table-row.status-passed .collapsible td:first-child {
  border-left-color: #22c55e;
  box-shadow: inset 4px 0 0 #22c55e;
}
.results-table-row.status-failed .collapsible td:first-child,
.results-table-row.status-error .collapsible td:first-child {
  border-left-color: #ef4444;
  box-shadow: inset 4px 0 0 #ef4444;
}
.results-table-row.status-skipped .collapsible td:first-child {
  border-left-color: #f59e0b;
  box-shadow: inset 4px 0 0 #f59e0b;
}
.results-table-row.status-rerun .collapsible td:first-child,
.results-table-row.status-xfailed .collapsible td:first-child {
  border-left-color: #8b5cf6;
  box-shadow: inset 4px 0 0 #8b5cf6;
}
.results-table-row .extras-row td {
  padding: 0;
  border: 0;
  background: transparent;
}
.results-table-row .extra {
  padding: 0 !important;
}
.results-table-row .extra > div,
.results-table-row .logwrapper,
.results-table-row .media {
  margin-top: 8px;
  padding: 20px;
  border-radius: 20px;
  background: rgba(255,255,255,0.98);
  border: 1px solid #cfe0ff;
  box-shadow: 0 16px 30px rgba(15,23,42,0.08);
}
.results-table-row .logwrapper {
  position: relative;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
}
.results-table-row .logwrapper .logexpander {
  position: absolute;
  top: 18px;
  right: 18px;
  z-index: 5;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 34px;
  padding: 0 12px;
  border-radius: 999px;
  border: 1px solid #cbd5e1;
  background: rgba(255,255,255,0.92);
  color: #334155;
  font-size: 12px;
  font-weight: 600;
  box-shadow: 0 8px 18px rgba(15,23,42,0.12);
}
.results-table-row .logwrapper .logexpander:hover {
  background: #eff6ff;
  color: #1d4ed8;
  border-color: #bfdbfe;
}
.log {
  max-height: 720px;
  min-height: 240px;
  overflow: auto;
  border-radius: 18px;
  background: linear-gradient(180deg, #fcfdff 0%, #f8fbff 100%);
  color: #0f172a;
  padding: 18px;
  border: 1px solid #dbeafe;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.7);
  font-family: "Cascadia Code", "JetBrains Mono", Consolas, "Courier New", monospace;
  font-size: 14px;
  line-height: 1.72;
  letter-spacing: 0.01em;
  white-space: pre-wrap;
  word-break: break-word;
  overflow-wrap: anywhere;
  tab-size: 2;
  scrollbar-width: thin;
  scrollbar-color: #94a3b8 #eff6ff;
}
.log::-webkit-scrollbar {
  width: 12px;
  height: 12px;
}
.log::-webkit-scrollbar-track {
  background: #eff6ff;
  border-radius: 999px;
}
.log::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, #94a3b8 0%, #64748b 100%);
  border-radius: 999px;
  border: 2px solid #eff6ff;
}
.log *,
.log pre,
.log code,
.log span,
.log div {
  background: transparent !important;
}
.codex-detail-label {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 14px;
  padding: 6px 12px;
  border-radius: 999px;
  background: #eff6ff;
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
.codex-log-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}
.codex-log-title {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #0f172a;
  font-size: 15px;
  font-weight: 700;
}
.codex-log-title::before {
  content: "";
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: linear-gradient(180deg, #ef4444 0%, #f97316 100%);
  box-shadow: 0 0 0 6px rgba(239,68,68,0.12);
}
.codex-log-copy {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 34px;
  padding: 0 12px;
  border-radius: 999px;
  border: 1px solid #cbd5e1;
  background: #ffffff;
  color: #334155;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}
.codex-log-copy:hover {
  background: #eff6ff;
  color: #1d4ed8;
  border-color: #bfdbfe;
}
.codex-log-summary {
  margin-bottom: 14px;
  padding: 14px 16px;
  border-radius: 16px;
  background: #fff7ed;
  border: 1px solid #fed7aa;
  color: #9a3412;
  font-size: 13px;
  line-height: 1.7;
}
.codex-log-lines {
  display: grid;
  gap: 2px;
}
.codex-log-line {
  padding: 4px 10px;
  border-radius: 10px;
  color: #1e293b;
  white-space: pre-wrap;
  word-break: break-word;
}
.codex-log-line.is-section {
  margin-top: 8px;
  padding: 10px 12px;
  background: #dbeafe;
  color: #1d4ed8;
  font-weight: 700;
}
.codex-log-line.is-error {
  background: #fef2f2;
  color: #b91c1c;
  font-weight: 700;
}
.codex-log-line.is-pointer {
  background: #eef2ff;
  color: #4338ca;
  font-weight: 700;
}
.codex-log-line.is-location {
  background: #f8fafc;
  color: #475569;
}
.codex-log-line.is-assert {
  background: #fff7ed;
  color: #c2410c;
  font-weight: 700;
}
.log a {
  color: #2563eb;
}
.log b,
.log strong {
  color: #0f172a;
}
.results-table-row.status-failed .log,
.results-table-row.status-error .log {
  border-color: #fecaca;
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,0.7),
    0 14px 30px rgba(127,29,29,0.08);
}
.results-table-row .media {
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
}
.media-container__viewport {
  border-radius: 18px;
  overflow: hidden;
  background: #0f172a;
  border: 1px solid #cbd5e1;
}
.media-container__viewport img,
.media-container__viewport video {
  max-height: 620px;
  width: 100%;
  object-fit: contain;
}
.results-table-row .media a {
  color: #2563eb;
  font-weight: 600;
}
.extraHTML {
  color: #1e293b;
  line-height: 1.8;
  font-size: 14px;
}
.extraHTML pre,
.extraHTML code {
  white-space: pre-wrap;
  word-break: break-word;
}
#not-found-message td {
  padding: 24px !important;
  border-radius: 18px;
  text-align: center;
  color: #64748b;
  background: rgba(255,255,255,0.9);
}
footer {
  margin-top: 18px;
}
@media (max-width: 900px) {
  body { padding: 16px; }
  .report-hero,
  .summary { padding: 20px; }
  #results-table-head th { position: static; }
  .results-table-row .extra > div,
  .results-table-row .logwrapper,
  .results-table-row .media { padding: 16px; }
  .results-table-row .logwrapper .logexpander {
    position: static;
    margin-bottom: 12px;
  }
  .log {
    min-height: 180px;
    max-height: 520px;
    padding: 18px;
    font-size: 13px;
  }
}
</style>
<script id="codex-pytest-theme-script">
(function() {
  function applyTheme() {
    document.body.classList.add('codex-themed-report');

    var title = document.getElementById('title');
    if (title && !document.querySelector('.report-hero')) {
      var hero = document.createElement('section');
      hero.className = 'report-hero';

      var titleMeta = document.createElement('div');
      titleMeta.className = 'report-hero__meta';

      var generated = title.nextElementSibling;
      if (generated && generated.tagName === 'P') {
        var generatedClone = generated.cloneNode(true);
        var pill = document.createElement('div');
        pill.className = 'report-hero__pill';
        pill.innerHTML = generatedClone.innerHTML;
        titleMeta.appendChild(pill);
        generated.remove();
      }

      var resultsTable = document.getElementById('results-table');
      var envHeader = document.getElementById('environment-header');
      var envTable = document.getElementById('environment');

      title.parentNode.insertBefore(hero, title);
      hero.appendChild(title);
      if (titleMeta.children.length) {
        hero.appendChild(titleMeta);
      }
      if (envHeader) {
        hero.appendChild(envHeader);
      }
      if (envTable) {
        hero.appendChild(envTable);
      }
      if (resultsTable) {
        hero.insertAdjacentElement('afterend', resultsTable);
      }
    }

    document.querySelectorAll('.results-table-row').forEach(function(tbody) {
      var row = tbody.querySelector('tr.collapsible');
      if (!row || tbody.dataset.codexStyled === 'true') return;
      var firstCell = row.querySelector('td');
      if (!firstCell) return;
      var status = firstCell.textContent.trim().toLowerCase().replace(/\\s+/g, '-');
      tbody.classList.add('status-' + status);
      tbody.dataset.codexStyled = 'true';
    });

    document.querySelectorAll('.logwrapper').forEach(function(wrapper) {
      if (!wrapper.querySelector('.codex-detail-label')) {
        var label = document.createElement('div');
        label.className = 'codex-detail-label';
        label.textContent = '错误堆栈';
        wrapper.insertBefore(label, wrapper.firstChild);
      }
    });

    document.querySelectorAll('.media').forEach(function(media) {
      if (!media.querySelector('.codex-detail-label')) {
        var label = document.createElement('div');
        label.className = 'codex-detail-label';
        label.textContent = '失败截图';
        media.insertBefore(label, media.firstChild);
      }
    });

    document.querySelectorAll('.logwrapper .log').forEach(function(log) {
      if (log.dataset.codexEnhanced === 'true') return;

      var rawText = (log.textContent || '').replace(/\\r\\n/g, '\\n').trimEnd();
      if (!rawText.trim()) {
        log.dataset.codexEnhanced = 'true';
        return;
      }

      var lines = rawText.split('\\n');
      var summaryLine = lines.find(function(line) {
        return /AssertionError|Traceback|TimeoutException|NoSuchElement|StaleElementReference|ElementClickIntercepted|Error:|Exception:/i.test(line) || /^E\\s+/.test(line);
      }) || lines.find(function(line) {
        return line.trim();
      }) || '失败详情';

      var toolbar = document.createElement('div');
      toolbar.className = 'codex-log-toolbar';

      var title = document.createElement('div');
      title.className = 'codex-log-title';
      title.textContent = '原始失败详情';
      toolbar.appendChild(title);

      var copyButton = document.createElement('button');
      copyButton.type = 'button';
      copyButton.className = 'codex-log-copy';
      copyButton.textContent = '复制堆栈';
      copyButton.addEventListener('click', function() {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(rawText).then(function() {
            copyButton.textContent = '已复制';
            window.setTimeout(function() { copyButton.textContent = '复制堆栈'; }, 1600);
          });
        }
      });
      toolbar.appendChild(copyButton);

      var summary = document.createElement('div');
      summary.className = 'codex-log-summary';
      summary.textContent = summaryLine.trim();

      var content = document.createElement('div');
      content.className = 'codex-log-lines';

      lines.forEach(function(line) {
        var row = document.createElement('div');
        row.className = 'codex-log-line';
        if (/^-{10,}\\s*Captured/i.test(line) || /^-{10,}/.test(line)) {
          row.classList.add('is-section');
        } else if (/^E\\s+/.test(line) || /AssertionError|TimeoutException|NoSuchElement|StaleElementReference|ElementClickIntercepted|Error:|Exception:/i.test(line)) {
          row.classList.add('is-error');
        } else if (/^>\\s+/.test(line)) {
          row.classList.add('is-pointer');
        } else if (/\\.py:\\d+:/i.test(line) || /^[A-Za-z]:.*\\.py$/i.test(line)) {
          row.classList.add('is-location');
        } else if (/\\bassert\\b|\\bwhere\\s+\\d+\\s+=\\s+/i.test(line)) {
          row.classList.add('is-assert');
        }
        row.textContent = line || ' ';
        content.appendChild(row);
      });

      log.innerHTML = '';
      log.appendChild(toolbar);
      log.appendChild(summary);
      log.appendChild(content);
      log.dataset.codexEnhanced = 'true';
    });
  }

  document.addEventListener('DOMContentLoaded', function() {
    applyTheme();
    var observer = new MutationObserver(function() { applyTheme(); });
    observer.observe(document.body, { childList: true, subtree: true });
  });
})();
</script>
"""


def _inject_ai_into_html_report(config: pytest.Config, payload: dict) -> None:
    html_path = getattr(config.option, "htmlpath", None)
    if not html_path:
        return

    report_file = Path(str(html_path))
    if not report_file.exists():
        return

    payload["report_json_path"] = payload.get("report_json_path") or str(_build_json_report_path(config) or "")
    ai_html = _build_ai_html(payload)
    theme_assets = _build_pytest_html_theme_assets()
    content = report_file.read_text(encoding="utf-8", errors="ignore")
    if "AI 测试总结" in content and "codex-pytest-theme" in content:
        return

    if "</head>" in content:
        ai_head_style, ai_body = ai_html.split("</style>", 1)
        content = content.replace("</head>", theme_assets + ai_head_style + "</style>\n</head>", 1)
    else:
        ai_body = theme_assets + ai_html

    insert_markers = [
        '<div id="results-table">',
        '<div class="summary">',
        '<body>',
    ]
    inserted = False
    for marker in insert_markers:
        if marker in content:
            content = content.replace(marker, marker + "\n" + ai_body, 1)
            inserted = True
            break
    if not inserted:
        if "</body>" in content:
            content = content.replace("</body>", ai_body + "\n</body>", 1)
        else:
            content += ai_body

    report_file.write_text(content, encoding="utf-8")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when != "call":
        return

    store = _get_ai_store(item.config)
    if report.passed:
        status = "passed"
    elif report.failed:
        status = "failed"
    elif report.skipped:
        status = "skipped"
    else:
        status = "error"

    longrepr_text = str(getattr(report, "longreprtext", "") or "")
    store["tests"][report.nodeid] = {
        "id": len(store["tests"]) + 1,
        "name": report.nodeid,
        "module": _extract_module_name(report.nodeid),
        "status": status,
        "duration": round(float(getattr(report, "duration", 0.0) or 0.0), 4),
        "retry_count": 0,
        "error_message": longrepr_text.splitlines()[-1][:500] if report.failed and longrepr_text else "",
        "traceback": longrepr_text[:4000] if report.failed else "",
        "screenshot": "",
    }

    if report.passed:
        return

    driver = _get_driver_from_item(item)
    if driver is None:
        return

    try:
        png_bytes = driver.get_screenshot_as_png()
        screenshot_path = _build_screenshot_path(item)
        screenshot_path.write_bytes(png_bytes)
        setattr(item, "_failure_screenshot_path", str(screenshot_path))

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
        store["tests"][report.nodeid]["screenshot"] = str(screenshot_path)
    except Exception:
        # 报告增强失败时不影响原始测试结果
        return


def pytest_sessionstart(session):
    store = _get_ai_store(session.config)
    store["start_time"] = datetime.now()


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    store = _get_ai_store(session.config)
    store["end_time"] = datetime.now()
    payload = _build_ai_payload(session.config)
    store["payload"] = payload

    json_path = _build_json_report_path(session.config)
    if json_path:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        store["report_json_path"] = str(json_path)


def pytest_configure(config):
    global pytest_html
    pytest_html = config.pluginmanager.getplugin("html")

    if pytest_html is None:
        return

    if not getattr(config.option, "htmlpath", None):
        config.option.htmlpath = str(_build_report_path(config))

    if not getattr(config.option, "self_contained_html", False):
        config.option.self_contained_html = True


@pytest.hookimpl(trylast=True)
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    store = _get_ai_store(config)
    payload = store.get("payload")
    if payload:
        _inject_ai_into_html_report(config, payload)

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
