#!/usr/bin/env python3
"""
配置文件验证模块
验证配置文件的格式、必填项和数据类型
"""

import os
import sys
import yaml
from typing import Dict, List, Any, Optional


class ConfigValidator:
    """配置文件验证器"""

    def __init__(self):
        self.errors = []
        self.warnings = []

    def validate_file(self, config_path: str) -> bool:
        """
        验证配置文件

        Args:
            config_path: 配置文件路径

        Returns:
            bool: 是否验证通过
        """
        self.errors.clear()
        self.warnings.clear()

        # 检查文件是否存在
        if not os.path.exists(config_path):
            self.errors.append(f"配置文件不存在: {config_path}")
            return False

        try:
            # 读取配置文件
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # 验证YAML格式
            if config is None:
                self.errors.append("配置文件为空")
                return False

            # 验证配置结构
            self._validate_structure(config)

            # 验证数据完整性
            self._validate_completeness(config)

            # 验证数据类型
            self._validate_data_types(config)

            # 验证数值范围
            self._validate_value_ranges(config)

            # 验证依赖关系
            self._validate_dependencies(config)

            # 输出验证结果
            self._print_results()

            return len(self.errors) == 0

        except yaml.YAMLError as e:
            self.errors.append(f"YAML格式错误: {e}")
            return False
        except Exception as e:
            self.errors.append(f"验证过程中发生错误: {e}")
            return False

    def _validate_structure(self, config: Dict) -> None:
        """验证配置结构"""
        required_sections = [
            'project',
            'environment',
            'browser',
            'test',
            'report',
            'logging'
        ]

        for section in required_sections:
            if section not in config:
                self.errors.append(f"缺少必要的配置节: {section}")
            elif not isinstance(config[section], dict):
                self.errors.append(f"配置节 '{section}' 必须是字典类型")

    def _validate_completeness(self, config: Dict) -> None:
        """验证数据完整性"""
        # 项目信息验证
        if 'project' in config:
            project = config['project']
            required_fields = ['name', 'version']
            for field in required_fields:
                if field not in project:
                    self.errors.append(f"project节缺少字段: {field}")

        # 环境配置验证
        if 'environment' in config:
            env = config['environment']
            if 'base_url' not in env:
                self.errors.append("environment节缺少字段: base_url")
            elif not isinstance(env.get('base_url'), str):
                self.errors.append("environment.base_url必须是字符串类型")

        # 浏览器配置验证
        if 'browser' in config:
            browser = config['browser']
            required_fields = ['name', 'implicit_wait', 'page_load_timeout']
            for field in required_fields:
                if field not in browser:
                    self.errors.append(f"browser节缺少字段: {field}")

            # 检查浏览器名称是否支持
            if 'name' in browser:
                supported_browsers = ['chrome', 'firefox', 'edge']
                if browser['name'] not in supported_browsers:
                    self.warnings.append(f"不支持的浏览器: {browser['name']}，支持: {supported_browsers}")

        # 测试配置验证
        if 'test' in config:
            test = config['test']
            required_fields = ['retry_count', 'timeout']
            for field in required_fields:
                if field not in test:
                    self.errors.append(f"test节缺少字段: {field}")

        # 报告配置验证
        if 'report' in config:
            report = config['report']
            if 'send_email' in report and report['send_email']:
                if 'email_config' not in report:
                    self.errors.append("启用邮件发送但缺少email_config配置")
                else:
                    email_config = report['email_config']
                    required_email_fields = ['smtp_server', 'smtp_port', 'sender', 'receivers']
                    for field in required_email_fields:
                        if field not in email_config:
                            self.errors.append(f"email_config缺少字段: {field}")

    def _validate_data_types(self, config: Dict) -> None:
        """验证数据类型"""
        type_checks = [
            # 路径: 字符串
            ('browser.download_path', str, False),
            ('test.screenshot_path', str, False),
            ('report.output_dir', str, False),
            ('logging.file', str, False),

            # 数值: 整数
            ('browser.implicit_wait', int, True),
            ('browser.page_load_timeout', int, True),
            ('test.retry_count', int, True),
            ('test.timeout', int, True),
            ('logging.max_size', int, True),
            ('logging.backup_count', int, True),

            # 布尔值
            ('browser.headless', bool, False),
            ('test.screenshot_on_failure', bool, False),
            ('report.send_email', bool, False),
        ]

        for key, expected_type, required in type_checks:
            try:
                keys = key.split('.')
                value = config
                for k in keys:
                    if isinstance(value, dict) and k in value:
                        value = value[k]
                    else:
                        if required:
                            self.errors.append(f"配置项 {key} 不存在")
                        break
                else:
                    if value is not None and not isinstance(value, expected_type):
                        self.errors.append(f"配置项 {key} 类型错误: 期望 {expected_type.__name__}, 实际 {type(value).__name__}")
            except Exception as e:
                self.errors.append(f"验证配置项 {key} 时发生错误: {e}")

    def _validate_value_ranges(self, config: Dict) -> None:
        """验证数值范围"""
        range_checks = [
            ('browser.implicit_wait', 1, 60, "隐式等待时间应在1-60秒之间"),
            ('browser.page_load_timeout', 10, 300, "页面加载超时应为10-300秒"),
            ('test.retry_count', 0, 5, "重试次数应在0-5次之间"),
            ('test.timeout', 10, 600, "测试超时应为10-600秒"),
            ('logging.max_size', 1024, 104857600, "日志文件最大大小应在1KB-100MB之间"),
            ('logging.backup_count', 0, 100, "日志备份数量应在0-100之间"),
        ]

        for key, min_val, max_val, message in range_checks:
            try:
                keys = key.split('.')
                value = config
                for k in keys:
                    if isinstance(value, dict) and k in value:
                        value = value[k]
                    else:
                        break
                else:
                    if isinstance(value, (int, float)):
                        if value < min_val or value > max_val:
                            self.warnings.append(f"{key}: {message} (当前值: {value})")
            except Exception:
                pass

    def _validate_dependencies(self, config: Dict) -> None:
        """验证配置依赖关系"""
        # 如果启用邮件发送，必须配置邮件服务器
        if ('report' in config and
            config['report'].get('send_email', False) and
            'email_config' not in config['report']):
            self.errors.append("启用邮件发送但缺少邮件配置")

        # 如果启用截图功能，截图路径必须可写
        if ('test' in config and
            config['test'].get('screenshot_on_failure', False) and
            'screenshot_path' in config['test']):
            screenshot_path = config['test']['screenshot_path']
            try:
                # 检查目录是否可写
                test_file = os.path.join(screenshot_path, '.test_write')
                os.makedirs(screenshot_path, exist_ok=True)
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
            except Exception as e:
                self.warnings.append(f"截图路径可能不可写: {screenshot_path} ({e})")

    def _print_results(self) -> None:
        """打印验证结果"""
        if self.errors or self.warnings:
            print("配置文件验证结果:")
            print("-" * 50)

            if self.errors:
                print("❌ 错误:")
                for error in self.errors:
                    print(f"  - {error}")
                print()

            if self.warnings:
                print("⚠️  警告:")
                for warning in self.warnings:
                    print(f"  - {warning}")
                print()

            if not self.errors:
                print("✅ 配置文件格式正确")
            else:
                print(f"❌ 发现 {len(self.errors)} 个错误")

            print("-" * 50)
        else:
            print("✅ 配置文件验证通过，无错误和警告")

    def get_errors(self) -> List[str]:
        """获取错误列表"""
        return self.errors.copy()

    def get_warnings(self) -> List[str]:
        """获取警告列表"""
        return self.warnings.copy()


def validate_config_file(config_path: str) -> bool:
    """
    验证配置文件的快捷函数

    Args:
        config_path: 配置文件路径

    Returns:
        bool: 是否验证通过
    """
    validator = ConfigValidator()
    return validator.validate_file(config_path)


def create_default_config(config_path: str) -> bool:
    """
    创建默认配置文件

    Args:
        config_path: 配置文件路径

    Returns:
        bool: 是否创建成功
    """
    default_config = {
        'project': {
            'name': '电商后台自动化测试系统',
            'version': '1.0.0'
        },
        'environment': {
            'base_url': 'http://test.ecommerce.com/admin',
            'test_env': 'test'
        },
        'browser': {
            'name': 'chrome',
            'headless': False,
            'window_size': '1920x1080',
            'implicit_wait': 10,
            'page_load_timeout': 30,
            'download_path': './downloads'
        },
        'test': {
            'retry_count': 2,
            'timeout': 30,
            'screenshot_on_failure': True,
            'screenshot_path': './reports/screenshots'
        },
        'report': {
            'output_dir': './reports',
            'template': 'default.html',
            'send_email': False,
            'email_config': {
                'smtp_server': 'smtp.example.com',
                'smtp_port': 587,
                'sender': 'test@example.com',
                'receivers': ['admin@example.com']
            }
        },
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'file': './logs/test.log',
            'max_size': 10485760,
            'backup_count': 5
        },
        'test_data': {
            'login': {
                'valid_users': [
                    {
                        'username': 'admin',
                        'password': 'password123',
                        'role': '管理员'
                    },
                    {
                        'username': 'operator',
                        'password': 'operator123',
                        'role': '操作员'
                    }
                ],
                'invalid_users': [
                    {
                        'username': '',
                        'password': 'password123',
                        'expected_error': '用户名不能为空'
                    },
                    {
                        'username': 'admin',
                        'password': '',
                        'expected_error': '密码不能为空'
                    }
                ]
            }
        }
    }

    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(config_path), exist_ok=True)

        # 写入配置文件
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True, indent=2)

        print(f"✅ 默认配置文件已创建: {config_path}")
        return True

    except Exception as e:
        print(f"❌ 创建默认配置文件失败: {e}")
        return False


if __name__ == "__main__":
    # 命令行接口
    import argparse

    parser = argparse.ArgumentParser(description='配置文件验证工具')
    parser.add_argument('config_path', nargs='?', default='config/config.yaml',
                       help='配置文件路径 (默认: config/config.yaml)')
    parser.add_argument('--create', action='store_true',
                       help='创建默认配置文件')
    parser.add_argument('--fix', action='store_true',
                       help='尝试修复配置文件问题')

    args = parser.parse_args()

    if args.create:
        # 创建默认配置文件
        success = create_default_config(args.config_path)
        sys.exit(0 if success else 1)

    # 验证配置文件
    validator = ConfigValidator()
    success = validator.validate_file(args.config_path)

    if not success and args.fix:
        print("\n尝试修复配置文件...")
        # 这里可以添加修复逻辑
        print("修复功能尚未实现")

    sys.exit(0 if success else 1)