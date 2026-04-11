#!/usr/bin/env python3
"""
配置管理模块
实现配置文件的加载、解析和管理功能
支持单例模式，确保全局配置一致
"""

import os
import yaml
from typing import Any, Dict, Optional


class ConfigManager:
    """
    配置管理器（单例模式）
    负责加载、解析和管理项目的所有配置
    """

    _instance = None
    _config = None
    _config_path = None

    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """初始化配置管理器"""
        if not self._initialized:
            self._config = {}
            self._config_path = None
            self._initialized = True

    def load_config(self, config_path: Optional[str] = None) -> bool:
        """
        加载配置文件

        Args:
            config_path: 配置文件路径，如果为None则使用默认路径

        Returns:
            bool: 是否加载成功
        """
        try:
            if config_path is None:
                # 默认配置文件路径
                base_dir = os.path.dirname(os.path.dirname(__file__))
                self._config_path = os.path.join(base_dir, 'config', 'config.yaml')
            else:
                self._config_path = config_path

            # 检查配置文件是否存在
            if not os.path.exists(self._config_path):
                raise FileNotFoundError(f"配置文件不存在: {self._config_path}")

            # 读取配置文件
            with open(self._config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)

            # 验证必要配置项
            self._validate_config()

            print(f"配置文件加载成功: {self._config_path}")
            return True

        except Exception as e:
            print(f"配置文件加载失败: {e}")
            # 使用默认配置
            self._set_default_config()
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键，支持点分隔符，如 'browser.name'
            default: 默认值，如果配置不存在则返回此值

        Returns:
            Any: 配置值
        """
        if self._config is None:
            self.load_config()

        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> bool:
        """
        设置配置值

        Args:
            key: 配置键，支持点分隔符
            value: 配置值

        Returns:
            bool: 是否设置成功
        """
        if self._config is None:
            self.load_config()

        keys = key.split('.')
        config = self._config

        # 遍历创建嵌套字典
        for i, k in enumerate(keys[:-1]):
            if k not in config:
                config[k] = {}
            elif not isinstance(config[k], dict):
                # 如果中间节点不是字典，则转换为字典
                config[k] = {'_value': config[k]}
            config = config[k]

        # 设置最终值
        config[keys[-1]] = value
        return True

    def set_environment(self, env: str) -> bool:
        """
        设置测试环境

        Args:
            env: 环境名称，支持 'test', 'staging', 'prod'

        Returns:
            bool: 是否设置成功
        """
        env_configs = {
            'test': {
                'base_url': 'http://test.ecommerce.com/admin',
                'test_env': 'test'
            },
            'staging': {
                'base_url': 'http://staging.ecommerce.com/admin',
                'test_env': 'staging'
            },
            'prod': {
                'base_url': 'http://ecommerce.com/admin',
                'test_env': 'prod'
            }
        }

        if env not in env_configs:
            print(f"不支持的环境: {env}，支持的环境: {list(env_configs.keys())}")
            return False

        env_config = env_configs[env]
        for key, value in env_config.items():
            self.set(f'environment.{key}', value)

        print(f"环境已切换到: {env}")
        return True

    def save_config(self, config_path: Optional[str] = None) -> bool:
        """
        保存配置到文件

        Args:
            config_path: 配置文件路径，如果为None则使用当前加载的路径

        Returns:
            bool: 是否保存成功
        """
        try:
            save_path = config_path or self._config_path
            if save_path is None:
                save_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    'config', 'config.yaml'
                )

            # 确保目录存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True, indent=2)

            print(f"配置文件保存成功: {save_path}")
            return True

        except Exception as e:
            print(f"配置文件保存失败: {e}")
            return False

    def reload(self) -> bool:
        """重新加载配置文件"""
        if self._config_path:
            return self.load_config(self._config_path)
        return False

    def get_all(self) -> Dict:
        """
        获取所有配置

        Returns:
            Dict: 所有配置的字典
        """
        if self._config is None:
            self.load_config()
        return self._config.copy()

    def _validate_config(self) -> None:
        """
        验证配置文件的基本结构
        确保必要的配置项存在
        """
        required_sections = ['project', 'environment', 'browser', 'test']

        for section in required_sections:
            if section not in self._config:
                raise ValueError(f"配置文件缺少必要部分: {section}")

        # 检查必要的配置项
        required_items = [
            'environment.base_url',
            'browser.name',
            'browser.implicit_wait',
            'test.retry_count',
            'test.timeout'
        ]

        for item in required_items:
            if self.get(item) is None:
                raise ValueError(f"配置文件缺少必要配置项: {item}")

    def _set_default_config(self) -> None:
        """设置默认配置"""
        self._config = {
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
            }
        }

        print("已使用默认配置")

    def __str__(self) -> str:
        """返回配置的字符串表示"""
        return yaml.dump(self._config, default_flow_style=False, allow_unicode=True)


# 全局配置管理器实例
config_manager = ConfigManager()


def get_config() -> ConfigManager:
    """
    获取全局配置管理器实例

    Returns:
        ConfigManager: 配置管理器实例
    """
    return config_manager


def init_config(config_path: Optional[str] = None) -> bool:
    """
    初始化配置

    Args:
        config_path: 配置文件路径

    Returns:
        bool: 是否初始化成功
    """
    return config_manager.load_config(config_path)


if __name__ == "__main__":
    # 测试配置管理器
    manager = get_config()
    manager.load_config()

    print("当前配置:")
    print(manager)

    # 测试获取配置
    print(f"浏览器名称: {manager.get('browser.name')}")
    print(f"基础URL: {manager.get('environment.base_url')}")

    # 测试设置配置
    manager.set('browser.headless', True)
    print(f"无头模式: {manager.get('browser.headless')}")

    # 测试环境切换
    manager.set_environment('staging')
    print(f"切换后基础URL: {manager.get('environment.base_url')}")