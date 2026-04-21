#!/usr/bin/env python3
"""
HTML报告生成器
生成美观的HTML测试报告，支持模板和自定义样式
"""

import os
import sys
import json
import time
import shutil
import re
import html
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from string import Template

from utils.logger import get_logger
from utils.config_manager import get_config


class HTMLReportGenerator:
    """
    HTML报告生成器
    生成详细的HTML测试报告
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化HTML报告生成器

        Args:
            config: 配置字典
        """
        self.logger = get_logger(self.__class__.__name__)

        # 获取配置
        if config is None:
            self.config = get_config()
        else:
            self.config = config

        # 报告配置
        self.report_config = self.config.get('report', {})
        self.output_dir = self.report_config.get('output_dir', './reports')
        self.template_name = self.report_config.get('template', 'default.html')
        self.send_email = self.report_config.get('send_email', False)

        # 模板目录
        self.template_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'templates'
        )

        # 确保目录存在
        os.makedirs(self.output_dir, exist_ok=True)

        self.logger.info(f"HTML报告生成器初始化完成，输出目录: {self.output_dir}")

    def generate_report(self,
                       report_data: Dict[str, Any],
                       report_name: Optional[str] = None,
                       template_name: Optional[str] = None) -> str:
        """
        生成HTML报告

        Args:
            report_data: 报告数据
            report_name: 报告名称，如果为None则自动生成
            template_name: 模板名称，如果为None则使用配置的模板

        Returns:
            str: 生成的报告文件路径
        """
        start_time = time.time()

        # 确定模板名称
        if template_name is None:
            template_name = self.template_name

        # 加载模板
        template_content = self._load_template(template_name)
        if template_content is None:
            self.logger.error(f"模板加载失败: {template_name}")
            return ""

        # 准备报告数据
        processed_data = self._prepare_report_data(report_data)

        # 渲染模板
        html_content = self._render_template(template_content, processed_data)
        if not html_content:
            self.logger.error("模板渲染失败")
            return ""

        # 生成报告文件名
        if report_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_name = f"test_report_{timestamp}.html"

        # 创建报告目录
        report_dir = os.path.join(self.output_dir, f"report_{datetime.now().strftime('%Y%m%d')}")
        os.makedirs(report_dir, exist_ok=True)

        # 保存报告
        report_file = os.path.join(report_dir, report_name)
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        end_time = time.time()
        generation_time = end_time - start_time

        self.logger.info(f"HTML报告生成成功: {report_file}")
        self.logger.info(f"报告生成耗时: {generation_time:.2f}秒")

        # 如果需要，发送邮件
        if self.send_email:
            self._send_email_with_report(report_file, processed_data)

        return report_file

    def generate_summary_report(self,
                               summary_data: Dict[str, Any],
                               historical_data: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        生成摘要报告（用于多日或多次执行的汇总）

        Args:
            summary_data: 摘要数据
            historical_data: 历史数据

        Returns:
            str: 生成的报告文件路径
        """
        self.logger.info("生成摘要报告")

        # 准备摘要数据
        report_data = {
            "project": summary_data.get("project", {
                "name": "电商后台自动化测试系统",
                "version": "1.0.0"
            }),
            "execution": summary_data.get("execution", {}),
            "stats": summary_data.get("stats", {}),
            "module_stats": summary_data.get("module_stats", []),
            "test_results": summary_data.get("test_results", []),
            "historical_data": historical_data or [],
            "summary_type": "summary"
        }

        # 使用summary模板或默认模板
        template_name = "summary.html" if self._template_exists("summary.html") else self.template_name

        return self.generate_report(report_data, "summary_report.html", template_name)

    def generate_comparison_report(self,
                                  comparison_data: Dict[str, Any]) -> str:
        """
        生成对比报告（用于不同环境或版本的对比）

        Args:
            comparison_data: 对比数据

        Returns:
            str: 生成的报告文件路径
        """
        self.logger.info("生成对比报告")

        # 准备对比数据
        report_data = {
            "project": comparison_data.get("project", {}),
            "comparisons": comparison_data.get("comparisons", []),
            "summary_type": "comparison"
        }

        # 使用comparison模板或默认模板
        template_name = "comparison.html" if self._template_exists("comparison.html") else self.template_name

        return self.generate_report(report_data, "comparison_report.html", template_name)

    def _load_template(self, template_name: str) -> Optional[str]:
        """
        加载模板文件

        Args:
            template_name: 模板文件名

        Returns:
            Optional[str]: 模板内容，如果失败则返回None
        """
        # 尝试多个路径
        possible_paths = [
            os.path.join(self.template_dir, template_name),
            os.path.join(self.template_dir, template_name + '.html'),
            template_name  # 绝对路径
        ]

        for template_path in possible_paths:
            if os.path.exists(template_path):
                try:
                    with open(template_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    self.logger.debug(f"模板加载成功: {template_path}")
                    return content
                except Exception as e:
                    self.logger.error(f"模板读取失败 {template_path}: {e}")

        self.logger.error(f"找不到模板文件: {template_name}")
        return None

    def _prepare_report_data(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        准备报告数据，确保所有必要的字段都存在

        Args:
            report_data: 原始报告数据

        Returns:
            Dict[str, Any]: 处理后的报告数据
        """
        # 默认项目信息
        project_info = report_data.get("project", {})
        project_info.setdefault("name", "电商后台自动化测试系统")
        project_info.setdefault("version", "1.0.0")

        # 默认执行信息
        execution_info = report_data.get("execution", {})
        execution_info.setdefault("start_time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        execution_info.setdefault("end_time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        execution_info.setdefault("duration", "0秒")
        execution_info.setdefault("environment", "test")
        execution_info.setdefault("browser", "chrome")
        execution_info.setdefault("total_duration", "0秒")
        execution_info.setdefault("average_duration", "0秒")
        execution_info.setdefault("retry_count", 0)
        execution_info.setdefault("execution_mode", "sequential")

        # 默认统计信息
        stats_info = report_data.get("stats", {})
        stats_info.setdefault("total_tests", 0)
        stats_info.setdefault("passed_tests", 0)
        stats_info.setdefault("failed_tests", 0)
        stats_info.setdefault("error_tests", 0)
        stats_info.setdefault("skipped_tests", 0)

        # 计算通过率
        total = stats_info["total_tests"]
        passed = stats_info["passed_tests"]
        if total > 0:
            pass_rate = (passed / total) * 100
        else:
            pass_rate = 0.0
        stats_info["pass_rate"] = round(pass_rate, 2)

        # 处理测试结果
        test_results = report_data.get("test_results", [])
        for i, test_result in enumerate(test_results):
            # 确保所有测试结果都有必要字段
            test_result.setdefault("id", i + 1)
            test_result.setdefault("name", f"Test Case {i + 1}")
            test_result.setdefault("module", "unknown")
            test_result.setdefault("status", "unknown")
            test_result.setdefault("duration", 0.0)
            test_result.setdefault("retry_count", 0)
            test_result.setdefault("error_message", "")
            test_result.setdefault("screenshot", "")
            test_result.setdefault("ai_analysis", {})

            # 格式化持续时间
            if isinstance(test_result["duration"], (int, float)):
                test_result["duration_str"] = f"{test_result['duration']:.2f}s"
            else:
                test_result["duration_str"] = str(test_result["duration"])

        ai_summary = report_data.get("ai_summary", {}) or {}
        ai_summary.setdefault("summary", "本次未生成 AI 摘要。")
        ai_summary.setdefault("risk_modules", [])
        ai_summary.setdefault("recommendations", [])
        ai_summary.setdefault("rerun_suggestion", "建议先检查失败用例后再决定是否回归。")
        ai_summary.setdefault("stability_trend", "unknown")
        ai_summary.setdefault("root_cause_summary", [])
        ai_summary.setdefault("confidence_score", 0.0)
        ai_summary.setdefault("trend_analysis", "")
        ai_summary.setdefault("key_findings", [])
        ai_summary.setdefault("improvement_areas", [])
        ai_summary.setdefault("execution_quality", "unknown")

        failed_tests = report_data.get("failed_tests", [])
        if not failed_tests:
            failed_tests = [
                test for test in test_results
                if str(test.get("status", "")).lower() in {"failed", "error"}
            ]

        # 模块统计
        module_stats = report_data.get("module_stats", [])
        if not module_stats and test_results:
            # 从测试结果自动生成模块统计
            module_stats = self._generate_module_stats(test_results)

        # 历史数据
        historical_data = report_data.get("historical_data", [])

        # 汇总数据
        processed_data = {
            "project": project_info,
            "execution": execution_info,
            "stats": stats_info,
            "module_stats": module_stats,
            "test_results": test_results,
            "failed_tests": failed_tests,
            "ai_summary": ai_summary,
            "historical_data": historical_data,
            "summary_type": report_data.get("summary_type", "default"),
            "generation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        processed_data["module_stats_html"] = self._build_module_stats_html(module_stats)
        processed_data["test_results_rows_html"] = self._build_test_results_rows_html(test_results)
        processed_data["ai_recommendations_html"] = self._build_ai_recommendations_html(ai_summary)
        processed_data["ai_failure_cards_html"] = self._build_ai_failure_cards_html(failed_tests)
        processed_data["ai_risk_modules_text"] = "、".join(ai_summary.get("risk_modules", [])) or "无"
        processed_data["ai_stability_trend"] = ai_summary.get("stability_trend", "unknown")
        # 新字段处理
        processed_data["ai_confidence_score"] = f"{float(ai_summary.get('confidence_score', 0.0)):.1%}"
        processed_data["ai_trend_analysis"] = ai_summary.get("trend_analysis", "无趋势分析数据")
        processed_data["ai_execution_quality"] = ai_summary.get("execution_quality", "unknown")
        # 关键发现HTML
        key_findings = ai_summary.get("key_findings", [])
        if key_findings:
            html_items = []
            for item in key_findings:
                html_items.append(f"<li>{html.escape(str(item))}</li>")
            processed_data["ai_key_findings_html"] = "<ul>" + "".join(html_items) + "</ul>"
        else:
            processed_data["ai_key_findings_html"] = "<p>无关键发现</p>"
        # 改进领域HTML
        improvement_areas = ai_summary.get("improvement_areas", [])
        if improvement_areas:
            html_items = []
            for item in improvement_areas:
                html_items.append(f"<li>{html.escape(str(item))}</li>")
            processed_data["ai_improvement_areas_html"] = "<ul>" + "".join(html_items) + "</ul>"
        else:
            processed_data["ai_improvement_areas_html"] = "<p>无明确改进领域</p>"
        # 构建根本原因摘要HTML
        root_cause_summary = ai_summary.get("root_cause_summary", [])
        if root_cause_summary:
            html_items = []
            for item in root_cause_summary:
                category = item.get("category", "未知")
                count = item.get("count", 0)
                html_items.append(f"<li>{category}: {count} 个</li>")
            processed_data["ai_root_cause_summary_html"] = "<ul>" + "".join(html_items) + "</ul>"
        else:
            processed_data["ai_root_cause_summary_html"] = "<p>无分类数据</p>"

        return processed_data

    def _generate_module_stats(self, test_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        从测试结果生成模块统计

        Args:
            test_results: 测试结果列表

        Returns:
            List[Dict[str, Any]]: 模块统计列表
        """
        module_data = {}

        for test in test_results:
            module = test.get("module", "unknown")
            if module not in module_data:
                module_data[module] = {
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "error": 0,
                    "skipped": 0
                }

            module_stats = module_data[module]
            module_stats["total"] += 1

            status = test.get("status", "").lower()
            if status == "passed":
                module_stats["passed"] += 1
            elif status == "failed":
                module_stats["failed"] += 1
            elif status == "error":
                module_stats["error"] += 1
            elif status == "skipped":
                module_stats["skipped"] += 1

        # 转换为输出格式
        module_stats_list = []
        for module_name, stats in module_data.items():
            total = stats["total"]
            passed = stats["passed"]
            pass_rate = (passed / total * 100) if total > 0 else 0

            module_stats_list.append({
                "name": module_name,
                "total": total,
                "passed": passed,
                "failed": stats["failed"],
                "error": stats["error"],
                "skipped": stats["skipped"],
                "pass_rate": round(pass_rate, 2)
            })

        # 按通过率排序
        module_stats_list.sort(key=lambda x: x["pass_rate"], reverse=True)

        return module_stats_list

    def _render_template(self, template_content: str, data: Dict[str, Any]) -> str:
        """
        渲染模板

        Args:
            template_content: 模板内容
            data: 模板数据

        Returns:
            str: 渲染后的HTML内容
        """
        # 首先尝试使用_simple_template_render，它支持{{variable}}语法
        try:
            before_placeholder_count = len(re.findall(r'\{\{[^}]+\}\}', template_content))
            result = self._simple_template_render(template_content, data)
            after_placeholder_count = len(re.findall(r'\{\{[^}]+\}\}', result))
            if after_placeholder_count == 0 or after_placeholder_count < before_placeholder_count:
                return result
        except Exception as e:
            self.logger.error(f"简单模板渲染失败: {e}")

        # 回退到原始的Template方法（支持${variable}语法）
        try:
            template = Template(template_content)
            safe_data = self._make_template_safe(data)
            result = template.safe_substitute(safe_data)
            return result
        except Exception as e:
            self.logger.error(f"模板渲染失败: {e}")
            return template_content  # 返回原始内容

    def _build_module_stats_html(self, module_stats: List[Dict[str, Any]]) -> str:
        """构建模块统计 HTML。"""
        if not module_stats:
            return '<div class="empty-state">暂无模块统计数据</div>'

        cards = []
        for module in module_stats:
            pass_rate = float(module.get("pass_rate", 0) or 0)
            state_class = "module-passed" if pass_rate >= 80 else "module-failed"
            cards.append(
                f'''
                <div class="module-item {state_class}">
                    <div class="module-name">{html.escape(str(module.get("name", "unknown")))}</div>
                    <div class="module-progress">
                        <div class="module-progress-bar" style="width: {pass_rate}%"></div>
                    </div>
                    <div class="module-info">
                        <span>{module.get("passed", 0)}/{module.get("total", 0)} 通过</span>
                        <span>{pass_rate:.2f}%</span>
                    </div>
                </div>
                '''
            )
        return "".join(cards)

    def _build_test_results_rows_html(self, test_results: List[Dict[str, Any]]) -> str:
        """构建测试结果表格行 HTML。"""
        if not test_results:
            return '<tr><td colspan="9" class="empty-state">暂无测试结果</td></tr>'

        rows = []
        for index, test in enumerate(test_results, start=1):
            status = str(test.get("status", "unknown")).lower()
            error_message = str(test.get("error_message", "") or "")
            screenshot = str(test.get("screenshot", "") or "")
            ai_analysis = test.get("ai_analysis", {}) or {}
            root_cause = str(ai_analysis.get("root_cause", "-"))
            severity = str(ai_analysis.get("severity", "-")).upper()
            category = str(ai_analysis.get("category", "-"))
            confidence = str(ai_analysis.get("confidence", "-"))
            ai_summary = html.escape(root_cause) if ai_analysis else "-"
            ai_tooltip = f"严重程度: {severity}\n分类: {category}\n置信度: {confidence}\n原因: {root_cause}"

            if screenshot:
                screenshot_html = f'<a href="{html.escape(screenshot)}" target="_blank">查看</a>'
            else:
                screenshot_html = '-'

            rows.append(
                f'''
                <tr>
                    <td>{index}</td>
                    <td>
                        <div class="test-name">{html.escape(str(test.get("name", f"Test Case {index}")))}</div>
                        <div class="test-module">{html.escape(str(test.get("module", "unknown")))}</div>
                    </td>
                    <td>{html.escape(str(test.get("module", "unknown")))}</td>
                    <td><span class="status-badge status-{status}">{html.escape(status)}</span></td>
                    <td class="duration">{html.escape(str(test.get("duration_str", test.get("duration", "-"))))}</td>
                    <td>{html.escape(str(test.get("retry_count", 0)))}</td>
                    <td class="error-details" title="{html.escape(error_message)}">{html.escape(error_message[:120] if error_message else "-")}</td>
                    <td class="ai-cell" title="{ai_tooltip}">{ai_summary}</td>
                    <td>{screenshot_html}</td>
                </tr>
                '''
            )
        return "".join(rows)

    def _build_ai_recommendations_html(self, ai_summary: Dict[str, Any]) -> str:
        """构建 AI 建议列表 HTML。"""
        recommendations = ai_summary.get("recommendations", [])
        if not recommendations:
            return "<li>无</li>"
        return "".join(f"<li>{html.escape(str(item))}</li>" for item in recommendations)

    def _build_ai_failure_cards_html(self, failed_tests: List[Dict[str, Any]]) -> str:
        """构建 AI 失败分析卡片 HTML。"""
        if not failed_tests:
            return '<div class="empty-state">本轮没有失败用例。</div>'

        cards = []
        for test in failed_tests:
            analysis = test.get("ai_analysis", {}) or {}
            cards.append(
                f'''
                <article class="ai-failure-card">
                    <div class="ai-failure-head">
                        <h3>{html.escape(str(test.get("name", "unknown")))} </h3>
                        <span class="severity-badge severity-{html.escape(str(analysis.get("severity", "medium")).lower())}">
                            {html.escape(str(analysis.get("severity", "medium")).upper())}
                        </span>
                    </div>
                    <p class="ai-meta">模块：{html.escape(str(test.get("module", "unknown")))} | 状态：{html.escape(str(test.get("status", "")))}</p>
                    <p><strong>原始错误：</strong>{html.escape(str(test.get("error_message", "") or "无"))}</p>
                    <p><strong>失败原因：</strong>{html.escape(str(analysis.get("root_cause", "无法确定")))}</p>
                    <p><strong>问题分类：</strong>{html.escape(str(analysis.get("category", "其他")))}</p>
                    <p><strong>疑似位置：</strong>{html.escape(str(analysis.get("location", "无法确定")))}</p>
                    <p><strong>修复建议：</strong>{html.escape(str(analysis.get("fix_suggestion", "请结合原始日志排查")))}</p>
                    <p><strong>置信度：</strong>{html.escape(str(analysis.get("confidence", 0.0)))}</p>
                    <p><strong>分析来源：</strong>{html.escape(str(analysis.get("source", "未知")))}</p>
                </article>
                '''
            )
        return "".join(cards)

    def _simple_template_render(self, template_content: str, data: Dict[str, Any]) -> str:
        """
        简单的模板渲染（字符串替换）

        Args:
            template_content: 模板内容
            data: 模板数据

        Returns:
            str: 渲染后的HTML内容
        """
        result = template_content

        # 扁平化数据字典
        flat_data = self._flatten_dict(data)

        # 进行替换 - 支持 {{variable}} 语法
        for key, value in flat_data.items():
            # 尝试 {{variable}} 语法
            placeholder1 = "{{" + key + "}}"
            if placeholder1 in result:
                result = result.replace(placeholder1, str(value))

            # 也支持 ${variable} 语法以保持向后兼容性
            placeholder2 = "${" + key + "}"
            if placeholder2 in result:
                result = result.replace(placeholder2, str(value))

        return result

    def _make_template_safe(self, data: Dict[str, Any]) -> Dict[str, str]:
        """
        使数据对模板安全（转换为字符串）

        Args:
            data: 原始数据

        Returns:
            Dict[str, str]: 安全的模板数据
        """
        safe_data = {}

        def process_value(value):
            """处理值，转换为字符串"""
            if isinstance(value, (str, int, float, bool)):
                return str(value)
            elif isinstance(value, (list, dict)):
                return json.dumps(value, ensure_ascii=False)
            elif value is None:
                return ""
            else:
                return str(value)

        # 扁平化处理
        flat_data = self._flatten_dict(data)
        for key, value in flat_data.items():
            safe_data[key] = process_value(value)

        return safe_data

    def _flatten_dict(self, data: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
        """
        扁平化嵌套字典

        Args:
            data: 嵌套字典
            parent_key: 父键
            sep: 分隔符

        Returns:
            Dict[str, Any]: 扁平化字典
        """
        items = []
        for key, value in data.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key

            if isinstance(value, dict):
                items.extend(self._flatten_dict(value, new_key, sep).items())
            elif isinstance(value, list):
                # 对于列表，我们只取前几个元素
                if value and isinstance(value[0], dict):
                    # 如果是字典列表，转换为JSON字符串
                    items.append((new_key, json.dumps(value[:10], ensure_ascii=False)))
                else:
                    items.append((new_key, str(value[:10])))
            else:
                items.append((new_key, value))

        return dict(items)

    def _template_exists(self, template_name: str) -> bool:
        """
        检查模板是否存在

        Args:
            template_name: 模板名称

        Returns:
            bool: 是否存在
        """
        template_path = os.path.join(self.template_dir, template_name)
        return os.path.exists(template_path)

    def _send_email_with_report(self, report_file: str, report_data: Dict[str, Any]) -> bool:
        """
        发送带报告的邮件

        Args:
            report_file: 报告文件路径
            report_data: 报告数据

        Returns:
            bool: 是否发送成功
        """
        try:
            # 导入邮件发送器
            from utils.email_sender import get_email_sender

            # 获取邮件配置
            email_config = self.report_config.get('email_config', {})
            if not email_config:
                self.logger.warning("邮件配置为空，跳过邮件发送")
                return False

            # 创建邮件发送器
            email_sender = get_email_sender(email_config)

            # 准备邮件内容
            subject = f"测试报告 - {report_data['project']['name']} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            body = self._generate_email_body(report_data)

            # 发送邮件
            success = email_sender.send_email_with_attachment(
                subject=subject,
                body=body,
                attachment_paths=[report_file]
            )

            if success:
                self.logger.info(f"测试报告邮件发送成功: {report_file}")
            else:
                self.logger.error("测试报告邮件发送失败")

            return success

        except ImportError:
            self.logger.error("邮件发送器模块未找到，请确保utils/email_sender.py存在")
            return False
        except Exception as e:
            self.logger.error(f"发送邮件失败: {e}")
            return False

    def _generate_email_body(self, report_data: Dict[str, Any]) -> str:
        """
        生成邮件正文

        Args:
            report_data: 报告数据

        Returns:
            str: 邮件正文
        """
        project = report_data['project']
        stats = report_data['stats']
        execution = report_data['execution']

        body = f"""
        <html>
        <body>
            <h2>{project['name']} 测试报告</h2>
            <p>版本: {project['version']}</p>

            <h3>执行摘要</h3>
            <table border="1" cellpadding="5" cellspacing="0">
                <tr>
                    <td><strong>总测试数</strong></td>
                    <td>{stats['total_tests']}</td>
                </tr>
                <tr>
                    <td><strong>通过</strong></td>
                    <td>{stats['passed_tests']} ({stats['pass_rate']}%)</td>
                </tr>
                <tr>
                    <td><strong>失败</strong></td>
                    <td>{stats['failed_tests']}</td>
                </tr>
                <tr>
                    <td><strong>错误</strong></td>
                    <td>{stats['error_tests']}</td>
                </tr>
                <tr>
                    <td><strong>开始时间</strong></td>
                    <td>{execution['start_time']}</td>
                </tr>
                <tr>
                    <td><strong>结束时间</strong></td>
                    <td>{execution['end_time']}</td>
                </tr>
                <tr>
                    <td><strong>总时长</strong></td>
                    <td>{execution['total_duration']}</td>
                </tr>
            </table>

            <p>详细的HTML报告请查看附件。</p>
            <p>报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </body>
        </html>
        """

        return body

    def list_available_templates(self) -> List[str]:
        """
        列出可用的模板

        Returns:
            List[str]: 模板文件名列表
        """
        templates = []

        if os.path.exists(self.template_dir):
            for file in os.listdir(self.template_dir):
                if file.endswith('.html'):
                    templates.append(file)

        return templates

    def get_template_info(self, template_name: str) -> Dict[str, Any]:
        """
        获取模板信息

        Args:
            template_name: 模板名称

        Returns:
            Dict[str, Any]: 模板信息
        """
        template_path = os.path.join(self.template_dir, template_name)

        if not os.path.exists(template_path):
            return {"error": "Template not found"}

        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 分析模板中的变量
            import re
            variables = re.findall(r'\$\{(\w+)\}', content)

            info = {
                "name": template_name,
                "path": template_path,
                "size": os.path.getsize(template_path),
                "modified": datetime.fromtimestamp(os.path.getmtime(template_path)).isoformat(),
                "variable_count": len(variables),
                "variables": list(set(variables))[:20]  # 去重并限制数量
            }

            return info

        except Exception as e:
            return {"error": str(e)}


# 快捷函数
def get_html_report_generator(config: Optional[Dict[str, Any]] = None) -> HTMLReportGenerator:
    """
    获取HTML报告生成器实例

    Args:
        config: 配置字典

    Returns:
        HTMLReportGenerator: HTML报告生成器实例
    """
    return HTMLReportGenerator(config)


def generate_test_report(test_results: List[Dict[str, Any]],
                        project_info: Optional[Dict[str, Any]] = None,
                        execution_info: Optional[Dict[str, Any]] = None,
                        output_file: Optional[str] = None) -> str:
    """
    快捷函数：生成测试报告

    Args:
        test_results: 测试结果列表
        project_info: 项目信息
        execution_info: 执行信息
        output_file: 输出文件名

    Returns:
        str: 生成的报告文件路径
    """
    generator = HTMLReportGenerator()

    # 准备报告数据
    report_data = {
        "project": project_info or {
            "name": "电商后台自动化测试系统",
            "version": "1.0.0"
        },
        "execution": execution_info or {
            "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "duration": "0秒",
            "environment": "test",
            "browser": "chrome"
        },
        "test_results": test_results
    }

    # 生成报告
    return generator.generate_report(report_data, output_file)


if __name__ == "__main__":
    # 测试HTMLReportGenerator类
    print("测试HTMLReportGenerator类...")

    # 创建生成器
    generator = HTMLReportGenerator()

    # 列出可用模板
    templates = generator.list_available_templates()
    print(f"可用模板: {templates}")

    # 查看模板信息
    for template in templates[:2]:
        info = generator.get_template_info(template)
        print(f"模板信息 {template}: {info.get('variable_count', 0)} 个变量")

    # 创建测试数据
    test_results = [
        {
            "name": "test_valid_login",
            "module": "login",
            "status": "passed",
            "duration": 2.5,
            "retry_count": 0,
            "error_message": "",
            "screenshot": ""
        },
        {
            "name": "test_invalid_password",
            "module": "login",
            "status": "failed",
            "duration": 1.8,
            "retry_count": 1,
            "error_message": "密码验证失败",
            "screenshot": "/reports/screenshots/test1.png"
        },
        {
            "name": "test_product_search",
            "module": "product",
            "status": "passed",
            "duration": 3.2,
            "retry_count": 0,
            "error_message": "",
            "screenshot": ""
        }
    ]

    project_info = {
        "name": "电商后台测试系统",
        "version": "1.0.0"
    }

    execution_info = {
        "start_time": "2026-04-04 10:00:00",
        "end_time": "2026-04-04 10:05:30",
        "duration": "5分30秒",
        "environment": "test",
        "browser": "chrome",
        "total_duration": "330秒",
        "average_duration": "110秒",
        "retry_count": 1,
        "execution_mode": "sequential"
    }

    # 生成报告
    report_file = generate_test_report(test_results, project_info, execution_info, "test_report.html")
    print(f"测试报告生成成功: {report_file}")

    # 测试摘要报告
    summary_data = {
        "project": project_info,
        "execution": execution_info,
        "stats": {
            "total_tests": 150,
            "passed_tests": 140,
            "failed_tests": 8,
            "error_tests": 2
        },
        "module_stats": [
            {"name": "login", "total": 30, "passed": 28, "pass_rate": 93.3},
            {"name": "product", "total": 40, "passed": 38, "pass_rate": 95.0},
            {"name": "order", "total": 50, "passed": 45, "pass_rate": 90.0},
            {"name": "user", "total": 30, "passed": 29, "pass_rate": 96.7}
        ]
    }

    # 生成摘要报告
    summary_file = generator.generate_summary_report(summary_data)
    if summary_file:
        print(f"摘要报告生成成功: {summary_file}")

    print("测试完成")
