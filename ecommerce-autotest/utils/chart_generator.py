#!/usr/bin/env python3
"""
图表生成工具
生成测试报告的统计图表，支持多种图表类型
"""

import os
import json
import math
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
from enum import Enum

from utils.logger import get_logger


class ChartType(Enum):
    """图表类型枚举"""
    PIE = "pie"  # 饼图
    BAR = "bar"  # 柱状图
    LINE = "line"  # 折线图
    DONUT = "donut"  # 环形图
    HORIZONTAL_BAR = "horizontal_bar"  # 横向柱状图
    STACKED_BAR = "stacked_bar"  # 堆叠柱状图


class ChartColorScheme(Enum):
    """图表颜色方案枚举"""
    DEFAULT = "default"  # 默认方案
    PASTEL = "pastel"  # 柔和色彩
    VIBRANT = "vibrant"  # 鲜艳色彩
    MONOCHROME = "monochrome"  # 单色方案
    CATEGORY10 = "category10"  # 分类10色


class ChartGenerator:
    """
    图表生成器
    生成各种类型的图表，支持HTML/SVG格式
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化图表生成器

        Args:
            config: 配置字典
        """
        self.logger = get_logger(self.__class__.__name__)

        # 获取配置
        if config is None:
            from utils.config_manager import get_config
            self.config = get_config()
        else:
            self.config = config

        # 图表配置
        self.chart_config = self.config.get('chart', {})
        self.default_width = self.chart_config.get('width', 600)
        self.default_height = self.chart_config.get('height', 400)
        self.default_color_scheme = self.chart_config.get('color_scheme', 'default')

        # 颜色方案
        self.color_schemes = self._init_color_schemes()

        self.logger.info("图表生成器初始化完成")

    def _init_color_schemes(self) -> Dict[str, List[str]]:
        """初始化颜色方案"""
        return {
            "default": [
                "#4e79a7", "#f28e2c", "#e15759", "#76b7b2",
                "#59a14f", "#edc949", "#af7aa1", "#ff9da7",
                "#9c755f", "#bab0ab"
            ],
            "pastel": [
                "#a1c9f4", "#ffb482", "#8de5a1", "#ff9f9b",
                "#d0bbff", "#debb9b", "#fab0e4", "#cfcfcf",
                "#fffea3", "#b9f2f0"
            ],
            "vibrant": [
                "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
                "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
                "#bcbd22", "#17becf"
            ],
            "monochrome": [
                "#f7fbff", "#deebf7", "#c6dbef", "#9ecae1",
                "#6baed6", "#4292c6", "#2171b5", "#08519c",
                "#08306b"
            ],
            "category10": [
                "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
                "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
                "#bcbd22", "#17becf"
            ]
        }

    def generate_pie_chart(self,
                          data: Dict[str, Union[int, float]],
                          title: str = "",
                          width: int = 400,
                          height: int = 400,
                          color_scheme: Optional[str] = None) -> str:
        """
        生成饼图（SVG格式）

        Args:
            data: 数据字典 {标签: 值}
            title: 图表标题
            width: 图表宽度
            height: 图表高度
            color_scheme: 颜色方案

        Returns:
            str: SVG图表代码
        """
        self.logger.info(f"生成饼图: {title}")

        # 计算总和
        total = sum(data.values())
        if total == 0:
            return self._generate_empty_chart("无数据", width, height)

        # 获取颜色
        colors = self._get_colors(color_scheme, len(data))

        # 计算角度
        center_x = width // 2
        center_y = height // 2
        radius = min(width, height) // 2 - 20

        # 生成SVG
        svg_parts = [
            f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">'
        ]

        # 标题
        if title:
            svg_parts.append(f'<text x="{center_x}" y="20" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold">{title}</text>')

        # 绘制扇形
        start_angle = 0
        for i, (label, value) in enumerate(data.items()):
            percentage = value / total
            angle = percentage * 360

            if angle > 0:
                # 计算扇形路径
                path = self._create_pie_slice(center_x, center_y, radius, start_angle, angle)

                svg_parts.append(f'<path d="{path}" fill="{colors[i % len(colors)]}" stroke="white" stroke-width="1" />')

                # 添加标签线
                mid_angle = start_angle + angle / 2
                label_path = self._create_label_line(center_x, center_y, radius, mid_angle)
                if label_path:
                    svg_parts.append(f'<path d="{label_path}" fill="none" stroke="#666" stroke-width="1" />')

                    # 添加标签文本
                    label_x, label_y = self._calculate_label_position(center_x, center_y, radius, mid_angle)
                    text_anchor = "start" if label_x > center_x else "end"
                    svg_parts.append(f'<text x="{label_x}" y="{label_y}" text-anchor="{text_anchor}" font-family="Arial" font-size="10" fill="#333">{label}: {percentage:.1%}</text>')

            start_angle += angle

        # 中心圆（制作环形图效果）
        center_radius = radius // 3
        svg_parts.append(f'<circle cx="{center_x}" cy="{center_y}" r="{center_radius}" fill="white" />')

        # 添加总计
        svg_parts.append(f'<text x="{center_x}" y="{center_y - 5}" text-anchor="middle" font-family="Arial" font-size="12" font-weight="bold">总计</text>')
        svg_parts.append(f'<text x="{center_x}" y="{center_y + 10}" text-anchor="middle" font-family="Arial" font-size="10">{total}</text>')

        svg_parts.append('</svg>')

        return '\n'.join(svg_parts)

    def generate_bar_chart(self,
                          data: Dict[str, Union[int, float]],
                          title: str = "",
                          width: int = 600,
                          height: int = 400,
                          color_scheme: Optional[str] = None,
                          horizontal: bool = False) -> str:
        """
        生成柱状图（SVG格式）

        Args:
            data: 数据字典 {标签: 值}
            title: 图表标题
            width: 图表宽度
            height: 图表高度
            color_scheme: 颜色方案
            horizontal: 是否横向显示

        Returns:
            str: SVG图表代码
        """
        self.logger.info(f"生成柱状图: {title}")

        if not data:
            return self._generate_empty_chart("无数据", width, height)

        # 获取颜色
        colors = self._get_colors(color_scheme, len(data))

        # 计算最大值
        max_value = max(data.values())
        if max_value == 0:
            max_value = 1

        # 图表边距
        margin_top = 40 if title else 20
        margin_bottom = 40
        margin_left = 60
        margin_right = 40

        chart_width = width - margin_left - margin_right
        chart_height = height - margin_top - margin_bottom

        # 生成SVG
        svg_parts = [
            f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">'
        ]

        # 标题
        if title:
            svg_parts.append(f'<text x="{width // 2}" y="{margin_top // 2 + 5}" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold">{title}</text>')

        # 绘制坐标轴
        svg_parts.append(f'<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{height - margin_bottom}" stroke="#333" stroke-width="1" />')
        svg_parts.append(f'<line x1="{margin_left}" y1="{height - margin_bottom}" x2="{width - margin_right}" y2="{height - margin_bottom}" stroke="#333" stroke-width="1" />')

        if horizontal:
            # 横向柱状图
            bar_height = chart_height / len(data) * 0.6
            bar_spacing = chart_height / len(data) * 0.4

            for i, (label, value) in enumerate(data.items()):
                y = margin_top + i * (bar_height + bar_spacing) + bar_spacing / 2
                bar_width = (value / max_value) * chart_width

                # 绘制柱子
                svg_parts.append(f'<rect x="{margin_left}" y="{y}" width="{bar_width}" height="{bar_height}" fill="{colors[i % len(colors)]}" rx="2" ry="2" />')

                # 绘制值标签
                if value > 0:
                    svg_parts.append(f'<text x="{margin_left + bar_width + 5}" y="{y + bar_height / 2 + 4}" font-family="Arial" font-size="10" fill="#333">{value}</text>')

                # 绘制分类标签
                svg_parts.append(f'<text x="{margin_left - 5}" y="{y + bar_height / 2 + 4}" text-anchor="end" font-family="Arial" font-size="10" fill="#333">{label}</text>')

            # Y轴标签
            svg_parts.append(f'<text x="{margin_left // 2}" y="{height // 2}" text-anchor="middle" font-family="Arial" font-size="12" fill="#333" transform="rotate(-90, {margin_left // 2}, {height // 2})">数值</text>')

        else:
            # 纵向柱状图
            bar_width = chart_width / len(data) * 0.6
            bar_spacing = chart_width / len(data) * 0.4

            for i, (label, value) in enumerate(data.items()):
                x = margin_left + i * (bar_width + bar_spacing) + bar_spacing / 2
                bar_height = (value / max_value) * chart_height

                # 绘制柱子
                svg_parts.append(f'<rect x="{x}" y="{height - margin_bottom - bar_height}" width="{bar_width}" height="{bar_height}" fill="{colors[i % len(colors)]}" rx="2" ry="2" />')

                # 绘制值标签
                if value > 0:
                    svg_parts.append(f'<text x="{x + bar_width / 2}" y="{height - margin_bottom - bar_height - 5}" text-anchor="middle" font-family="Arial" font-size="10" fill="#333">{value}</text>')

                # 绘制分类标签
                svg_parts.append(f'<text x="{x + bar_width / 2}" y="{height - margin_bottom + 15}" text-anchor="middle" font-family="Arial" font-size="10" fill="#333">{label}</text>')

            # Y轴标签
            svg_parts.append(f'<text x="{margin_left // 2}" y="{height // 2}" text-anchor="middle" font-family="Arial" font-size="12" fill="#333" transform="rotate(-90, {margin_left // 2}, {height // 2})">数值</text>')

        svg_parts.append('</svg>')

        return '\n'.join(svg_parts)

    def generate_line_chart(self,
                           data: Dict[str, List[Union[int, float]]],
                           title: str = "",
                           width: int = 600,
                           height: int = 400,
                           color_scheme: Optional[str] = None) -> str:
        """
        生成折线图（SVG格式）

        Args:
            data: 数据字典 {线条名: 数据点列表}
            title: 图表标题
            width: 图表宽度
            height: 图表高度
            color_scheme: 颜色方案

        Returns:
            str: SVG图表代码
        """
        self.logger.info(f"生成折线图: {title}")

        if not data:
            return self._generate_empty_chart("无数据", width, height)

        # 获取颜色
        colors = self._get_colors(color_scheme, len(data))

        # 计算数据范围
        all_values = [value for values in data.values() for value in values]
        if not all_values:
            return self._generate_empty_chart("无数据", width, height)

        max_value = max(all_values)
        min_value = min(all_values)
        if max_value == min_value:
            max_value = min_value + 1

        # 图表边距
        margin_top = 40 if title else 20
        margin_bottom = 40
        margin_left = 60
        margin_right = 40

        chart_width = width - margin_left - margin_right
        chart_height = height - margin_top - margin_bottom

        # 生成SVG
        svg_parts = [
            f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">'
        ]

        # 标题
        if title:
            svg_parts.append(f'<text x="{width // 2}" y="{margin_top // 2 + 5}" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold">{title}</text>')

        # 绘制坐标轴
        svg_parts.append(f'<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{height - margin_bottom}" stroke="#333" stroke-width="1" />')
        svg_parts.append(f'<line x1="{margin_left}" y1="{height - margin_bottom}" x2="{width - margin_right}" y2="{height - margin_bottom}" stroke="#333" stroke-width="1" />')

        # 绘制网格线
        grid_lines = 5
        for i in range(grid_lines + 1):
            y = margin_top + (chart_height / grid_lines) * i
            value = max_value - (max_value - min_value) / grid_lines * i

            svg_parts.append(f'<line x1="{margin_left}" y1="{y}" x2="{width - margin_right}" y2="{y}" stroke="#eee" stroke-width="1" />')
            svg_parts.append(f'<text x="{margin_left - 5}" y="{y + 3}" text-anchor="end" font-family="Arial" font-size="10" fill="#666">{value:.1f}</text>')

        # 绘制每条线
        for line_idx, (line_name, values) in enumerate(data.items()):
            if len(values) < 2:
                continue

            # 生成路径
            path_parts = []
            for i, value in enumerate(values):
                x = margin_left + (chart_width / (len(values) - 1)) * i
                y = margin_top + chart_height - ((value - min_value) / (max_value - min_value)) * chart_height

                if i == 0:
                    path_parts.append(f'M {x} {y}')
                else:
                    path_parts.append(f'L {x} {y}')

            path = ' '.join(path_parts)

            svg_parts.append(f'<path d="{path}" fill="none" stroke="{colors[line_idx % len(colors)]}" stroke-width="2" />')

            # 绘制数据点
            for i, value in enumerate(values):
                x = margin_left + (chart_width / (len(values) - 1)) * i
                y = margin_top + chart_height - ((value - min_value) / (max_value - min_value)) * chart_height

                svg_parts.append(f'<circle cx="{x}" cy="{y}" r="3" fill="{colors[line_idx % len(colors)]}" stroke="white" stroke-width="1" />')

            # 添加图例
            legend_x = margin_left + 10
            legend_y = margin_top + 20 * line_idx
            svg_parts.append(f'<rect x="{legend_x}" y="{legend_y - 8}" width="12" height="12" fill="{colors[line_idx % len(colors)]}" rx="2" ry="2" />')
            svg_parts.append(f'<text x="{legend_x + 18}" y="{legend_y}" font-family="Arial" font-size="10" fill="#333">{line_name}</text>')

        svg_parts.append('</svg>')

        return '\n'.join(svg_parts)

    def generate_html_chart(self,
                           chart_type: ChartType,
                           data: Dict[str, Any],
                           title: str = "",
                           width: int = 600,
                           height: int = 400,
                           color_scheme: Optional[str] = None) -> str:
        """
        生成HTML格式的图表（使用CSS和JS）

        Args:
            chart_type: 图表类型
            data: 图表数据
            title: 图表标题
            width: 图表宽度
            height: 图表高度
            color_scheme: 颜色方案

        Returns:
            str: HTML图表代码
        """
        self.logger.info(f"生成HTML图表: {title}")

        # 生成图表容器和简单JS
        chart_id = f"chart_{hash(str(data) + str(datetime.now()))}"

        html = f'''
        <div id="{chart_id}" style="width: {width}px; height: {height}px; border: 1px solid #ddd; border-radius: 4px; padding: 10px;">
            <div style="text-align: center; font-weight: bold; margin-bottom: 10px;">{title}</div>
            <div style="width: 100%; height: calc(100% - 30px); display: flex; align-items: center; justify-content: center;">
                <div style="color: #999; font-style: italic;">
                    图表类型: {chart_type.value}<br>
                    数据点: {len(data)}<br>
                    需要JavaScript渲染
                </div>
            </div>
        </div>
        <script>
            // 简单的图表渲染（简化版）
            document.addEventListener('DOMContentLoaded', function() {{
                const container = document.getElementById('{chart_id}');
                const data = {json.dumps(data, ensure_ascii=False)};

                // 这里可以添加实际的图表渲染逻辑
                console.log('渲染图表:', data);
            }});
        </script>
        '''

        return html

    def save_chart_to_file(self,
                          chart_svg: str,
                          output_path: str) -> bool:
        """
        保存图表到文件

        Args:
            chart_svg: SVG图表代码
            output_path: 输出文件路径

        Returns:
            bool: 是否保存成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(chart_svg)

            self.logger.info(f"图表保存到: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"保存图表失败: {e}")
            return False

    def _create_pie_slice(self, cx: int, cy: int, r: int, start_angle: float, angle: float) -> str:
        """
        创建饼图扇形路径

        Args:
            cx: 圆心x坐标
            cy: 圆心y坐标
            r: 半径
            start_angle: 起始角度（度）
            angle: 角度（度）

        Returns:
            str: SVG路径
        """
        if angle >= 360:
            # 完整的圆
            return f'M {cx} {cy} m -{r}, 0 a {r},{r} 0 1,0 {r*2},0 a {r},{r} 0 1,0 -{r*2},0'

        # 将角度转换为弧度
        start_rad = math.radians(start_angle - 90)  # SVG的0度在12点方向
        end_rad = math.radians(start_angle + angle - 90)

        # 计算起点和终点
        x1 = cx + r * math.cos(start_rad)
        y1 = cy + r * math.sin(start_rad)
        x2 = cx + r * math.cos(end_rad)
        y2 = cy + r * math.sin(end_rad)

        # 大弧标志
        large_arc = 1 if angle > 180 else 0

        return f'M {cx} {cy} L {x1} {y1} A {r} {r} 0 {large_arc} 1 {x2} {y2} Z'

    def _create_label_line(self, cx: int, cy: int, r: int, angle: float) -> str:
        """
        创建标签线

        Args:
            cx: 圆心x坐标
            cy: 圆心y坐标
            r: 半径
            angle: 角度（度）

        Returns:
            str: SVG路径
        """
        # 将角度转换为弧度
        angle_rad = math.radians(angle - 90)

        # 计算线上点
        x1 = cx + r * math.cos(angle_rad)
        y1 = cy + r * math.sin(angle_rad)
        x2 = cx + (r + 20) * math.cos(angle_rad)
        y2 = cy + (r + 20) * math.sin(angle_rad)

        return f'M {x1} {y1} L {x2} {y2}'

    def _calculate_label_position(self, cx: int, cy: int, r: int, angle: float) -> Tuple[int, int]:
        """
        计算标签位置

        Args:
            cx: 圆心x坐标
            cy: 圆心y坐标
            r: 半径
            angle: 角度（度）

        Returns:
            Tuple[int, int]: (x, y)坐标
        """
        # 将角度转换为弧度
        angle_rad = math.radians(angle - 90)

        # 计算位置
        x = cx + (r + 30) * math.cos(angle_rad)
        y = cy + (r + 30) * math.sin(angle_rad)

        return int(x), int(y)

    def _get_colors(self, color_scheme: Optional[str], count: int) -> List[str]:
        """
        获取颜色列表

        Args:
            color_scheme: 颜色方案名称
            count: 需要颜色数量

        Returns:
            List[str]: 颜色列表
        """
        scheme_name = color_scheme or self.default_color_scheme
        scheme = self.color_schemes.get(scheme_name, self.color_schemes["default"])

        # 如果需要的颜色多于方案中的颜色，循环使用
        if count <= len(scheme):
            return scheme[:count]
        else:
            colors = []
            for i in range(count):
                colors.append(scheme[i % len(scheme)])
            return colors

    def _generate_empty_chart(self, message: str, width: int, height: int) -> str:
        """生成空图表"""
        return f'''
        <svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" fill="#f8f9fa" />
            <text x="{width // 2}" y="{height // 2}" text-anchor="middle" font-family="Arial" font-size="14" fill="#999">{message}</text>
        </svg>
        '''


# 快捷函数
def get_chart_generator(config: Optional[Dict[str, Any]] = None) -> ChartGenerator:
    """
    获取图表生成器实例

    Args:
        config: 配置字典

    Returns:
        ChartGenerator: 图表生成器实例
    """
    return ChartGenerator(config)


def generate_test_result_chart(test_results: Dict[str, int]) -> str:
    """
    生成测试结果图表（饼图）

    Args:
        test_results: 测试结果字典 {状态: 数量}

    Returns:
        str: SVG图表代码
    """
    generator = ChartGenerator()
    return generator.generate_pie_chart(test_results, "测试结果分布", 400, 300)


def generate_module_pass_rate_chart(module_stats: Dict[str, float]) -> str:
    """
    生成模块通过率图表（柱状图）

    Args:
        module_stats: 模块通过率字典 {模块名: 通过率}

    Returns:
        str: SVG图表代码
    """
    generator = ChartGenerator()
    return generator.generate_bar_chart(module_stats, "模块通过率", 600, 400)


if __name__ == "__main__":
    # 测试ChartGenerator类
    print("测试ChartGenerator类...")

    # 创建图表生成器
    generator = ChartGenerator()

    # 测试数据
    test_results = {
        "通过": 85,
        "失败": 10,
        "错误": 5,
        "跳过": 2
    }

    module_pass_rates = {
        "登录模块": 95.5,
        "商品管理": 88.2,
        "订单管理": 92.7,
        "用户管理": 97.1,
        "权限管理": 83.4
    }

    trend_data = {
        "通过率": [85, 87, 89, 88, 90, 92, 91],
        "失败率": [15, 13, 11, 12, 10, 8, 9]
    }

    # 生成饼图
    pie_chart = generator.generate_pie_chart(test_results, "测试结果分布", 500, 400)
    print(f"饼图生成成功，长度: {len(pie_chart)} 字符")

    # 生成柱状图
    bar_chart = generator.generate_bar_chart(module_pass_rates, "模块通过率", 600, 400)
    print(f"柱状图生成成功，长度: {len(bar_chart)} 字符")

    # 生成横向柱状图
    horizontal_bar_chart = generator.generate_bar_chart(
        module_pass_rates, "模块通过率（横向）", 600, 400, horizontal=True
    )
    print(f"横向柱状图生成成功，长度: {len(horizontal_bar_chart)} 字符")

    # 生成折线图
    line_chart = generator.generate_line_chart(trend_data, "通过率趋势", 600, 400)
    print(f"折线图生成成功，长度: {len(line_chart)} 字符")

    # 保存图表到文件
    output_dir = "test_charts"
    os.makedirs(output_dir, exist_ok=True)

    generator.save_chart_to_file(pie_chart, os.path.join(output_dir, "pie_chart.svg"))
    generator.save_chart_to_file(bar_chart, os.path.join(output_dir, "bar_chart.svg"))
    generator.save_chart_to_file(line_chart, os.path.join(output_dir, "line_chart.svg"))

    print(f"图表已保存到 {output_dir} 目录")

    # 测试快捷函数
    test_chart = generate_test_result_chart(test_results)
    print(f"快捷函数生成饼图成功，长度: {len(test_chart)} 字符")

    print("测试完成")