#!/usr/bin/env python3
"""
AI 失败分析与报告总结模块
基于 OpenAI 兼容接口对测试失败结果进行辅助分析，并生成测试报告摘要。
"""

from __future__ import annotations

import json
import os
import re
from collections import Counter
from typing import Any, Dict, List, Optional

import requests


class AIAnalysisService:
    """AI 分析服务。"""

    DEFAULT_FAILURE_ANALYSIS = {
        "root_cause": "无法确定",
        "location": "无法确定",
        "fix_suggestion": "请结合原始错误堆栈、截图和页面操作日志进一步排查。",
        "severity": "medium",
        "confidence": 0.0,
        "category": "other",
    }

    DEFAULT_SUMMARY = {
        "summary": "本次测试未生成 AI 摘要。",
        "risk_modules": [],
        "recommendations": [],
        "rerun_suggestion": "建议先检查失败用例后再决定是否回归。",
        "stability_trend": "unknown",
        "root_cause_summary": [],
        "confidence_score": 0.0,
        "trend_analysis": "",
        "key_findings": [],
        "improvement_areas": [],
        "execution_quality": "unknown",
    }

    def __init__(self, config: Any):
        self.config = config
        self.enabled = bool(config.get("ai.enabled", False))
        self.api_base = (
            os.getenv("OPENAI_API_BASE")
            or config.get("ai.api_base", "https://api.openai.com/v1")
            or ""
        ).rstrip("/")
        self.api_key = self._resolve_api_key(config)
        self.model = os.getenv("OPENAI_MODEL") or config.get("ai.model", "gpt-4.1-mini")
        self.chat_endpoint = str(config.get("ai.chat_endpoint", "/chat/completions") or "/chat/completions")
        self.timeout = int(config.get("ai.timeout", 45) or 45)
        self.max_input_chars = int(config.get("ai.max_input_chars", 6000) or 6000)
        self.temperature = float(config.get("ai.temperature", 0.2) or 0.2)
        self.extra_headers = config.get("ai.extra_headers", {}) or {}
        # 重试配置
        self.max_retries = int(config.get("ai.max_retries", 2) or 2)
        self.retry_delay = float(config.get("ai.retry_delay", 1.0) or 1.0)
        self.retry_on_status_codes = [429, 500, 502, 503, 504]  # 可重试的状态码

    def is_available(self) -> bool:
        """判断 AI 服务是否可用。"""
        return self.enabled and bool(self.api_key) and bool(self.api_base) and bool(self.model)

    def health_check(self) -> Dict[str, Any]:
        """检查 AI 服务连通性与鉴权状态。"""
        if not self.enabled:
            return {
                "ok": False,
                "status": "disabled",
                "message": "AI 功能已关闭，请先将 ai.enabled 设为 true。",
            }

        missing_fields = []
        if not self.api_key:
            missing_fields.append("api_key")
        if not self.api_base:
            missing_fields.append("api_base")
        if not self.model:
            missing_fields.append("model")

        if missing_fields:
            return {
                "ok": False,
                "status": "misconfigured",
                "message": "AI 配置不完整，缺少: " + ", ".join(missing_fields),
            }

        content = self._call_model(
            "请返回 JSON：{\"status\":\"ok\",\"message\":\"health_check\"}"
        )
        parsed = self._parse_json_response(content)
        if parsed and not parsed.get("error"):
            return {
                "ok": True,
                "status": "ok",
                "message": "AI 服务可用。",
                "model": self.model,
                "api_base": self.api_base,
            }

        error_message = parsed.get("error", "") if parsed else "AI 服务返回了无法解析的内容。"
        return {
            "ok": False,
            "status": "error",
            "message": error_message,
            "model": self.model,
            "api_base": self.api_base,
        }

    def analyze_failures(self, failed_tests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量分析失败用例。"""
        analyzed_results: List[Dict[str, Any]] = []
        for test in failed_tests:
            enriched = dict(test)
            enriched["ai_analysis"] = self.analyze_failure(test)
            analyzed_results.append(enriched)
        return analyzed_results

    def analyze_failure(self, test_result: Dict[str, Any]) -> Dict[str, Any]:
        """分析单个失败用例。"""
        if not self.is_available():
            return {
                **self.DEFAULT_FAILURE_ANALYSIS,
                "source": "disabled",
                "raw_response": "",
            }

        prompt = self._build_failure_prompt(test_result)
        content = self._call_model(prompt)
        parsed = self._parse_json_response(content)
        if not parsed or parsed.get("error"):
            fallback = self._build_local_failure_analysis(test_result)
            fallback["source"] = "service_error" if parsed and parsed.get("error") else "heuristic"
            fallback["raw_response"] = content
            fallback["service_error"] = parsed.get("error", "") if parsed else ""
            return fallback

        return {
            "root_cause": parsed.get("root_cause", self.DEFAULT_FAILURE_ANALYSIS["root_cause"]),
            "location": parsed.get("location", self.DEFAULT_FAILURE_ANALYSIS["location"]),
            "fix_suggestion": parsed.get("fix_suggestion", self.DEFAULT_FAILURE_ANALYSIS["fix_suggestion"]),
            "severity": str(parsed.get("severity", "medium")).lower(),
            "confidence": self._normalize_confidence(parsed.get("confidence")),
            "category": parsed.get("category", self.DEFAULT_FAILURE_ANALYSIS["category"]),
            "source": "ai",
            "raw_response": content,
            "service_error": "",
        }

    def summarize_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成测试报告摘要。"""
        if not self.is_available():
            return {
                **self.DEFAULT_SUMMARY,
                "source": "disabled",
                "raw_response": "",
            }

        prompt = self._build_summary_prompt(report_data)
        content = self._call_model(prompt)
        parsed = self._parse_json_response(content)
        if not parsed or parsed.get("error"):
            fallback = self._build_local_summary(report_data)
            fallback["source"] = "service_error" if parsed and parsed.get("error") else "heuristic"
            fallback["raw_response"] = content
            fallback["service_error"] = parsed.get("error", "") if parsed else ""
            return fallback

        risk_modules = parsed.get("risk_modules", [])
        recommendations = parsed.get("recommendations", [])
        key_findings = parsed.get("key_findings", [])
        improvement_areas = parsed.get("improvement_areas", [])

        return {
            "summary": parsed.get("summary", self.DEFAULT_SUMMARY["summary"]),
            "risk_modules": risk_modules if isinstance(risk_modules, list) else [],
            "recommendations": recommendations if isinstance(recommendations, list) else [],
            "rerun_suggestion": parsed.get("rerun_suggestion", self.DEFAULT_SUMMARY["rerun_suggestion"]),
            "stability_trend": parsed.get("stability_trend", self.DEFAULT_SUMMARY["stability_trend"]),
            "root_cause_summary": parsed.get("root_cause_summary", self.DEFAULT_SUMMARY["root_cause_summary"]),
            "confidence_score": self._normalize_confidence(parsed.get("confidence_score", 0.0)),
            "trend_analysis": parsed.get("trend_analysis", self.DEFAULT_SUMMARY["trend_analysis"]),
            "key_findings": key_findings if isinstance(key_findings, list) else [],
            "improvement_areas": improvement_areas if isinstance(improvement_areas, list) else [],
            "execution_quality": parsed.get("execution_quality", self.DEFAULT_SUMMARY["execution_quality"]),
            "source": "ai",
            "raw_response": content,
            "service_error": "",
        }

    def _resolve_api_key(self, config: Any) -> str:
        """解析 API Key，优先环境变量，其次配置项。"""
        env_key = os.getenv("OPENAI_API_KEY")
        if env_key:
            return env_key.strip()
        return str(config.get("ai.api_key", "") or "").strip()

    def _call_model(self, prompt: str) -> str:
        """调用大模型接口，支持重试机制。"""
        import time

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        for key, value in self.extra_headers.items():
            headers[str(key)] = str(value)

        request_data = {
            "model": self.model,
            "temperature": self.temperature,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是一名自动化测试分析助手。"
                        "你只能基于提供的信息给出辅助判断，"
                        "不能编造不存在的结论，必须输出 JSON。"
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        }

        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.post(
                    f"{self.api_base}{self.chat_endpoint}",
                    headers=headers,
                    json=request_data,
                    timeout=self.timeout,
                )

                if response.status_code < 400:
                    payload = response.json()
                    content = (
                        payload.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                        .strip()
                    )
                    return content

                # 处理错误响应
                body_preview = response.text[:500]
                error_info = {
                    "error": self._format_http_error(response.status_code, body_preview),
                    "status_code": response.status_code,
                    "response_body": body_preview,
                    "attempt": attempt,
                    "max_retries": self.max_retries,
                }

                # 检查是否应该重试
                should_retry = (
                    attempt < self.max_retries and
                    response.status_code in self.retry_on_status_codes
                )

                if should_retry:
                    wait_time = self.retry_delay * (2 ** attempt)  # 指数退避
                    time.sleep(wait_time)
                    continue
                else:
                    return json.dumps(error_info, ensure_ascii=False)

            except requests.exceptions.Timeout as e:
                last_exception = e
                error_type = "timeout"
                error_msg = f"AI 调用超时: {e}"
            except requests.exceptions.ConnectionError as e:
                last_exception = e
                error_type = "connection"
                error_msg = f"AI 连接失败: {e}"
            except requests.exceptions.RequestException as e:
                last_exception = e
                error_type = "request"
                error_msg = f"AI 请求异常: {e}"
            except Exception as e:
                last_exception = e
                error_type = "unknown"
                error_msg = f"AI 调用失败: {e}"

            # 决定是否重试
            if attempt < self.max_retries and error_type in ["timeout", "connection"]:
                wait_time = self.retry_delay * (2 ** attempt)
                time.sleep(wait_time)
                continue
            else:
                error_info = {
                    "error": error_msg,
                    "error_type": error_type,
                    "attempt": attempt,
                    "max_retries": self.max_retries,
                    "exception": str(last_exception) if last_exception else "",
                }
                return json.dumps(error_info, ensure_ascii=False)

        # 不应该到达这里，但为了安全返回
        return json.dumps(
            {"error": "AI 调用失败: 未知错误", "error_type": "unknown"},
            ensure_ascii=False,
        )

    def _format_http_error(self, status_code: int, response_text: str) -> str:
        """格式化 HTTP 错误信息。"""
        response_text = (response_text or "").strip()
        if status_code == 401:
            return (
                "AI 调用失败: 401 Unauthorized。"
                "当前 api_key 与 api_base 不匹配，或该 key 无权访问当前模型/端点。"
            )
        if status_code == 403:
            return "AI 调用失败: 403 Forbidden。当前账号无权访问该模型或接口。"
        if status_code == 404:
            return "AI 调用失败: 404 Not Found。请检查 ai.api_base 或 ai.chat_endpoint 是否正确。"
        if status_code == 429:
            return "AI 调用失败: 429 Too Many Requests。请求过于频繁或额度不足。"
        if status_code >= 500:
            return f"AI 调用失败: {status_code} 服务端异常。请稍后重试。"
        return f"AI 调用失败: HTTP {status_code}。响应: {response_text[:200]}"

    def _build_failure_prompt(self, test_result: Dict[str, Any]) -> str:
        """构建失败分析提示词。"""
        sanitized_result = {
            "name": test_result.get("name", ""),
            "module": test_result.get("module", ""),
            "status": test_result.get("status", ""),
            "duration": test_result.get("duration", ""),
            "error_message": self._sanitize_text(test_result.get("error_message", "")),
            "traceback": self._sanitize_text(test_result.get("traceback", "")),
            "screenshot": test_result.get("screenshot", ""),
        }
        body = json.dumps(sanitized_result, ensure_ascii=False, indent=2)
        return (
            "你是一个自动化测试分析专家，请分析下面的测试失败用例，提供详细且可操作的诊断。\n"
            "请返回 JSON 格式，包含以下字段：\n"
            "1. root_cause: 失败的根本原因（尽可能具体，如：元素定位器失效、断言值不匹配、页面加载超时、网络错误等）\n"
            "2. location: 代码位置（从堆栈中提取文件名和行号，如：login_page.py:42）\n"
            "3. fix_suggestion: 具体的修复建议（包括代码修改示例、配置调整或测试步骤优化）\n"
            "4. severity: 严重程度（仅允许：low, medium, high）\n"
            "5. confidence: 置信度（0到1之间的小数，基于可用信息的完整性）\n"
            "6. category: 问题分类（可选：locator, assertion, timeout, network, authentication, data, environment, other）\n"
            "如果信息不足无法确定，请将 root_cause 设为“无法确定”，confidence 设为 0。\n"
            "请基于错误信息和堆栈跟踪提供专业分析。\n"
            f"失败用例信息:\n{body}"
        )

    def _build_summary_prompt(self, report_data: Dict[str, Any]) -> str:
        """构建报告摘要提示词。"""
        summary_payload = {
            "project": report_data.get("project", {}),
            "execution": report_data.get("execution", {}),
            "stats": report_data.get("stats", {}),
            "module_stats": report_data.get("module_stats", []),
            "failed_tests": [
                {
                    "name": item.get("name", ""),
                    "module": item.get("module", ""),
                    "error_message": self._sanitize_text(item.get("error_message", "")),
                    "severity": item.get("ai_analysis", {}).get("severity", ""),
                }
                for item in report_data.get("failed_tests", [])
            ],
        }
        body = json.dumps(summary_payload, ensure_ascii=False, indent=2)
        return (
            "你是一个测试报告分析专家，请基于以下自动化测试报告数据，生成专业、结构化的 JSON 摘要。\n"
            "输出字段必须包含：\n"
            "1. summary: 总体结论，突出通过率、主要问题和稳定性评估\n"
            "2. risk_modules: 高风险模块数组，每个元素包含模块名称、风险等级（high/medium/low）、失败原因和修复优先级\n"
            "3. recommendations: 具体建议数组，每条建议应可操作、有针对性\n"
            "4. rerun_suggestion: 回归测试建议（是否立即回归、回归范围、重点关注模块）\n"
            "5. stability_trend: 稳定性趋势评估（improving, stable, declining, unknown）\n"
            "6. root_cause_summary: 失败根本原因分类统计（如：定位问题、断言问题、超时问题等）\n"
            "7. confidence_score: 分析结果的置信度评分（0-1之间的浮点数）\n"
            "8. trend_analysis: 趋势分析（如果有历史数据，提供与历史执行的对比分析）\n"
            "9. key_findings: 关键发现摘要数组，突出最重要的发现\n"
            "10. improvement_areas: 需要改进的领域数组（如：测试稳定性、执行效率、覆盖率等）\n"
            "11. execution_quality: 执行质量评估（excellent, good, acceptable, poor, unknown）\n"
            "请提供详细、实用的分析，帮助团队快速定位问题和改进测试质量。\n"
            f"报告数据:\n{body}"
        )

    def _build_local_failure_analysis(self, test_result: Dict[str, Any]) -> Dict[str, Any]:
        """在 AI 服务不可用时使用本地规则分析失败原因。"""
        error_message = str(test_result.get("error_message", "") or "")
        traceback = str(test_result.get("traceback", "") or "")
        combined = f"{error_message}\n{traceback}"

        analysis = dict(self.DEFAULT_FAILURE_ANALYSIS)

        line_match = re.search(r"([A-Za-z0-9_./\\\\-]+\.py:\d+)", combined)
        if line_match:
            analysis["location"] = line_match.group(1)

        if "AssertionError" in combined:
            analysis["severity"] = "medium"
            analysis["confidence"] = 0.72
            analysis["root_cause"] = "断言结果与页面实际表现不一致。"
            analysis["fix_suggestion"] = "优先检查断言预期值、页面提示文案和被测系统当前业务规则是否一致。"

            mismatch = re.search(
                r"_matches_error\((.+?),\s*(.+?)\)\s*E\s+AssertionError",
                combined,
                re.S
            )
            if mismatch or "get_error_message()" in combined:
                analysis["root_cause"] = "页面实际错误提示与测试用例期望文案不一致，导致断言失败。"
                analysis["fix_suggestion"] = "检查测试数据中的 expected_error 是否仍然匹配当前页面提示，同时确认登录失败提示逻辑是否已变更。"
                analysis["confidence"] = 0.9

        elif "NoSuchElementException" in combined or "NoSuchElement" in combined:
            analysis["root_cause"] = "页面元素未找到，可能是定位器失效或页面尚未加载完成。"
            analysis["fix_suggestion"] = "检查页面定位器是否变化，并补充显式等待或页面稳定性判断。"
            analysis["severity"] = "high"
            analysis["confidence"] = 0.93

        elif "TimeoutException" in combined or "超时" in combined or "timed out" in combined.lower():
            analysis["root_cause"] = "页面加载或元素等待超时，测试执行节奏与页面响应不匹配。"
            analysis["fix_suggestion"] = "适当增加等待时间，或在关键步骤前增加页面状态校验。"
            analysis["severity"] = "high"
            analysis["confidence"] = 0.9

        elif "ElementClickInterceptedException" in combined or "not interactable" in combined.lower():
            analysis["root_cause"] = "元素可见但当前不可点击，可能被遮挡或页面状态未就绪。"
            analysis["fix_suggestion"] = "检查弹窗遮挡、滚动定位和元素可交互条件。"
            analysis["severity"] = "medium"
            analysis["confidence"] = 0.88

        elif "401 Client Error" in combined or "Unauthorized" in combined:
            analysis["root_cause"] = "AI 服务认证失败，接口密钥或接口地址配置不正确。"
            analysis["fix_suggestion"] = "检查 ai.api_base 与 ai.api_key 是否匹配当前服务商，确认该密钥对当前模型和端点有访问权限。"
            analysis["severity"] = "high"
            analysis["confidence"] = 0.98

        # 设置分类
        if "NoSuchElementException" in combined or "NoSuchElement" in combined:
            analysis["category"] = "locator"
        elif "TimeoutException" in combined or "超时" in combined or "timed out" in combined.lower():
            analysis["category"] = "timeout"
        elif "AssertionError" in combined:
            analysis["category"] = "assertion"
        elif "401 Client Error" in combined or "Unauthorized" in combined:
            analysis["category"] = "authentication"
        elif "ElementClickInterceptedException" in combined or "not interactable" in combined.lower():
            analysis["category"] = "interaction"
        else:
            analysis["category"] = "other"

        return analysis

    def _build_local_summary(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """在 AI 服务不可用时生成本地摘要。"""
        stats = report_data.get("stats", {}) or {}
        module_stats = report_data.get("module_stats", []) or []
        failed_tests = report_data.get("failed_tests", []) or []

        total = int(stats.get("total_tests", 0) or 0)
        passed = int(stats.get("passed_tests", 0) or 0)
        failed = int(stats.get("failed_tests", 0) or 0)
        errors = int(stats.get("error_tests", 0) or 0)
        pass_rate = float(stats.get("pass_rate", 0) or 0)

        risk_modules = []
        for module in sorted(module_stats, key=lambda item: float(item.get("pass_rate", 0) or 0)):
            if int(module.get("failed", 0) or 0) > 0 or int(module.get("error", 0) or 0) > 0:
                risk_modules.append(str(module.get("name", "unknown")))
        risk_modules = risk_modules[:3]

        recommendations: List[str] = []
        service_errors = []
        issue_counter: Counter[str] = Counter()

        for item in failed_tests:
            analysis = item.get("ai_analysis", {}) or {}
            service_error = analysis.get("service_error", "")
            if service_error:
                service_errors.append(service_error)

            issue_type = self._classify_issue_type(
                str(item.get("error_message", "")),
                str(item.get("traceback", "")),
            )
            if issue_type:
                issue_counter[issue_type] += 1

        if service_errors:
            recommendations.append("当前 AI 服务调用失败，请优先检查 ai.api_base、ai.api_key 与模型配置是否匹配。")

        if issue_counter.get("assertion_mismatch"):
            recommendations.append("优先核对失败用例中的 expected_error 与页面当前提示文案是否一致。")
        if issue_counter.get("locator_issue"):
            recommendations.append("检查页面元素定位器是否失效，并补充显式等待。")
        if issue_counter.get("timeout_issue"):
            recommendations.append("适当增加等待策略，排查页面响应速度和异步加载问题。")

        if not recommendations:
            recommendations.append("建议先从失败最多的模块入手，结合原始错误堆栈和截图逐条排查。")

        if failed or errors:
            summary = f"本轮测试共执行 {total} 条，用例通过率 {pass_rate:.1f}%，存在 {failed} 条失败、{errors} 条错误，建议优先处理失败集中模块。"
            rerun_suggestion = "建议先修复失败用例并完成关键模块回归后，再执行全量测试。"
        else:
            summary = f"本轮测试共执行 {total} 条，用例全部通过，通过率 {pass_rate:.1f}%。"
            rerun_suggestion = "当前结果稳定，可在下一次代码变更后继续执行冒烟验证。"

        # 生成根本原因摘要
        root_cause_summary = []
        for issue_type, count in issue_counter.items():
            if issue_type == "locator_issue":
                root_cause_summary.append({"category": "元素定位", "count": count})
            elif issue_type == "timeout_issue":
                root_cause_summary.append({"category": "超时", "count": count})
            elif issue_type == "assertion_mismatch":
                root_cause_summary.append({"category": "断言不匹配", "count": count})
            else:
                root_cause_summary.append({"category": issue_type, "count": count})

        # 评估执行质量
        if pass_rate >= 95:
            execution_quality = "excellent"
        elif pass_rate >= 85:
            execution_quality = "good"
        elif pass_rate >= 70:
            execution_quality = "acceptable"
        else:
            execution_quality = "poor"

        # 关键发现
        key_findings = []
        if failed > 0:
            key_findings.append(f"发现 {failed} 个失败用例需要优先处理")
        if errors > 0:
            key_findings.append(f"发现 {errors} 个错误用例需要排查")
        if not failed and not errors:
            key_findings.append("所有用例执行成功，测试质量良好")

        # 改进领域
        improvement_areas = []
        if pass_rate < 90:
            improvement_areas.append("测试用例稳定性")
        if issue_counter:
            improvement_areas.append("失败用例分析效率")
        if len(risk_modules) > 0:
            improvement_areas.append(f"高风险模块({', '.join(risk_modules)})的测试覆盖")

        return {
            "summary": summary,
            "risk_modules": risk_modules,
            "recommendations": recommendations[:5],
            "rerun_suggestion": rerun_suggestion,
            "stability_trend": "unknown",
            "root_cause_summary": root_cause_summary,
            "confidence_score": 0.5,  # 本地分析的置信度较低
            "trend_analysis": "无历史数据对比",
            "key_findings": key_findings,
            "improvement_areas": improvement_areas,
            "execution_quality": execution_quality,
        }

    def _classify_issue_type(self, error_message: str, traceback: str) -> str:
        """归类失败类型，用于本地摘要。"""
        combined = f"{error_message}\n{traceback}"
        if "NoSuchElement" in combined:
            return "locator_issue"
        if "TimeoutException" in combined or "timeout" in combined.lower():
            return "timeout_issue"
        if "AssertionError" in combined:
            return "assertion_mismatch"
        return ""

    def _sanitize_text(self, value: Any) -> str:
        """清洗并截断发送给模型的文本。"""
        text = str(value or "")
        text = re.sub(r"(?i)(password|passwd|pwd)\s*[:=]\s*[^\s,;]+", r"\1=[REDACTED]", text)
        text = re.sub(r"(?i)(api[_-]?key)\s*[:=]\s*[^\s,;]+", r"\1=[REDACTED]", text)
        text = re.sub(r"sk-[A-Za-z0-9]+", "sk-[REDACTED]", text)
        return text[: self.max_input_chars]

    def _parse_json_response(self, content: str) -> Optional[Dict[str, Any]]:
        """解析模型返回内容中的 JSON。"""
        if not content:
            return None

        text = content.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)

        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            return None

        try:
            parsed = json.loads(match.group(0))
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None

    def _normalize_confidence(self, value: Any) -> float:
        """规整置信度到 0-1。"""
        try:
            confidence = float(value)
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, min(1.0, confidence))
