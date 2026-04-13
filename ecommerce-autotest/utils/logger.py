#!/usr/bin/env python3
"""
日志系统模块
提供统一、灵活的日志记录功能
支持控制台和文件输出，支持日志轮转
"""

import os
import sys
import logging
import logging.handlers
from typing import Dict, Optional, Any
from datetime import datetime


class Logger:
    """
    日志管理器
    单例模式，提供统一的日志接口
    """

    _instance = None
    _loggers = {}  # 缓存日志器实例
    _config = None
    _default_level = logging.INFO

    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_logger(cls, name: str = "ecommerce_test") -> logging.Logger:
        """
        获取日志器

        Args:
            name: 日志器名称

        Returns:
            logging.Logger: 日志器实例
        """
        if name not in cls._loggers:
            cls._loggers[name] = cls._create_logger(name)
        return cls._loggers[name]

    @classmethod
    def configure(cls, config: Optional[Dict] = None) -> None:
        """
        配置日志系统

        Args:
            config: 日志配置字典
        """
        if config is None:
            config = cls._get_default_config()

        cls._config = config
        cls._default_level = getattr(logging, config.get('level', 'INFO'))

        # 更新已存在的日志器
        for name, logger in cls._loggers.items():
            cls._update_logger(logger, name, config)

    @classmethod
    def set_level(cls, level: str) -> None:
        """
        设置日志级别

        Args:
            level: 日志级别，如 'DEBUG', 'INFO', 'WARNING', 'ERROR'
        """
        try:
            cls._default_level = getattr(logging, level.upper())
            for logger in cls._loggers.values():
                logger.setLevel(cls._default_level)
        except AttributeError:
            print(f"无效的日志级别: {level}")

    @classmethod
    def _create_logger(cls, name: str) -> logging.Logger:
        """创建日志器"""
        logger = logging.getLogger(name)
        logger.setLevel(cls._default_level)

        # 避免重复添加处理器
        if logger.handlers:
            return logger

        # 使用配置或默认配置
        config = cls._config or cls._get_default_config()

        # 添加处理器
        cls._add_handlers(logger, name, config)

        return logger

    @classmethod
    def _update_logger(cls, logger: logging.Logger, name: str, config: Dict) -> None:
        """更新日志器配置"""
        # 清除现有处理器
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        # 重新添加处理器
        cls._add_handlers(logger, name, config)

    @classmethod
    def _add_handlers(cls, logger: logging.Logger, name: str, config: Dict) -> None:
        """添加日志处理器"""
        formatter = cls._create_formatter(config)

        # 控制台处理器
        if config.get('console', True):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            console_handler.setLevel(cls._default_level)
            logger.addHandler(console_handler)

        # 文件处理器
        if config.get('file'):
            file_config = config['file']
            file_path = file_config.get('path', './logs/test.log')

            # 确保日志目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # 创建文件处理器
            if file_config.get('rotate', True):
                # 使用轮转文件处理器
                max_size = file_config.get('max_size', 10 * 1024 * 1024)  # 默认10MB
                backup_count = file_config.get('backup_count', 5)
                file_handler = logging.handlers.RotatingFileHandler(
                    file_path,
                    maxBytes=max_size,
                    backupCount=backup_count,
                    encoding='utf-8'
                )
            else:
                # 普通文件处理器
                file_handler = logging.FileHandler(file_path, encoding='utf-8')

            file_handler.setFormatter(formatter)
            file_handler.setLevel(cls._default_level)
            logger.addHandler(file_handler)

    @classmethod
    def _create_formatter(cls, config: Dict) -> logging.Formatter:
        """创建日志格式化器"""
        log_format = config.get('format',
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        date_format = config.get('date_format', '%Y-%m-%d %H:%M:%S')
        return logging.Formatter(log_format, date_format)

    @classmethod
    def _get_default_config(cls) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'level': 'INFO',
            'console': True,
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'date_format': '%Y-%m-%d %H:%M:%S',
            'file': {
                'path': './logs/test.log',
                'rotate': True,
                'max_size': 10 * 1024 * 1024,  # 10MB
                'backup_count': 5
            }
        }

    @classmethod
    def shutdown(cls) -> None:
        """关闭日志系统"""
        for logger in cls._loggers.values():
            for handler in logger.handlers:
                handler.close()
        cls._loggers.clear()


class TestLogger:
    """
    测试专用的日志器
    提供额外的测试日志功能
    """

    def __init__(self, test_name: str):
        """
        初始化测试日志器

        Args:
            test_name: 测试名称
        """
        self.test_name = test_name
        self.logger = Logger.get_logger(f"test.{test_name}")
        self.start_time = None
        self.step_count = 0

    def start_test(self, description: str = "") -> None:
        """
        开始测试日志

        Args:
            description: 测试描述
        """
        self.start_time = datetime.now()
        self.step_count = 0
        self.logger.info("=" * 60)
        self.logger.info(f"开始测试: {self.test_name}")
        if description:
            self.logger.info(f"测试描述: {description}")
        self.logger.info(f"开始时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("=" * 60)

    def end_test(self, status: str = "完成", message: str = "") -> None:
        """
        结束测试日志

        Args:
            status: 测试状态，如 '通过', '失败', '错误'
            message: 附加消息
        """
        if self.start_time is None:
            self.logger.warning("测试未开始")
            return

        end_time = datetime.now()
        duration = end_time - self.start_time

        self.logger.info("=" * 60)
        self.logger.info(f"结束测试: {self.test_name}")
        self.logger.info(f"测试状态: {status}")
        if message:
            self.logger.info(f"测试结果: {message}")
        self.logger.info(f"结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"持续时间: {duration.total_seconds():.2f}秒")
        self.logger.info(f"执行步骤: {self.step_count}个")
        self.logger.info("=" * 60)

    def log_step(self, step_number: int, action: str, details: str = "") -> None:
        """
        记录测试步骤

        Args:
            step_number: 步骤编号
            action: 执行的操作
            details: 详细信息
        """
        self.step_count += 1
        if details:
            self.logger.info(f"步骤 {step_number}: {action} - {details}")
        else:
            self.logger.info(f"步骤 {step_number}: {action}")

    def log_action(self, action: str, details: str = "") -> None:
        """
        记录操作

        Args:
            action: 操作描述
            details: 详细信息
        """
        if details:
            self.logger.debug(f"操作: {action} - {details}")
        else:
            self.logger.debug(f"操作: {action}")

    def log_check(self, check: str, result: bool, details: str = "") -> None:
        """
        记录检查点

        Args:
            check: 检查内容
            result: 检查结果
            details: 详细信息
        """
        status = "通过" if result else "失败"
        if details:
            self.logger.info(f"检查: {check} - {status} ({details})")
        else:
            self.logger.info(f"检查: {check} - {status}")

    def log_error(self, error: str, details: str = "") -> None:
        """
        记录错误

        Args:
            error: 错误描述
            details: 错误详情
        """
        if details:
            self.logger.error(f"错误: {error} - {details}")
        else:
            self.logger.error(f"错误: {error}")

    def log_warning(self, warning: str, details: str = "") -> None:
        """
        记录警告

        Args:
            warning: 警告描述
            details: 警告详情
        """
        if details:
            self.logger.warning(f"警告: {warning} - {details}")
        else:
            self.logger.warning(f"警告: {warning}")

    def log_screenshot(self, filename: str, description: str = "") -> None:
        """
        记录截图

        Args:
            filename: 截图文件名
            description: 截图描述
        """
        if description:
            self.logger.info(f"截图保存: {filename} ({description})")
        else:
            self.logger.info(f"截图保存: {filename}")

    def log_data(self, data_type: str, data: Any) -> None:
        """
        记录测试数据

        Args:
            data_type: 数据类型，如 '输入数据', '预期结果', '实际结果'
            data: 数据内容
        """
        self.logger.debug(f"{data_type}: {data}")



    def debug(self, message: str, *args, **kwargs) -> None:
        self.logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs) -> None:
        self.logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs) -> None:
        self.logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs) -> None:
        self.logger.error(message, *args, **kwargs)

    def exception(self, message: str, *args, **kwargs) -> None:
        self.logger.exception(message, *args, **kwargs)

# 快捷函数
def get_logger(name: str = "ecommerce_test") -> logging.Logger:
    """
    获取日志器实例的快捷函数

    Args:
        name: 日志器名称

    Returns:
        logging.Logger: 日志器实例
    """
    return Logger.get_logger(name)


def configure_logging(config: Optional[Dict] = None) -> None:
    """
    配置日志系统的快捷函数

    Args:
        config: 日志配置字典
    """
    Logger.configure(config)


def setup_test_logging() -> TestLogger:
    """
    设置测试日志环境的快捷函数

    Returns:
        TestLogger: 测试日志器实例
    """
    # 配置测试专用日志格式
    config = {
        'level': 'DEBUG',
        'format': '%(asctime)s - %(levelname)8s - %(name)s - %(message)s',
        'console': True,
        'file': {
            'path': './logs/test_execution.log',
            'rotate': True,
            'max_size': 5 * 1024 * 1024,  # 5MB
            'backup_count': 10
        }
    }
    configure_logging(config)

    return TestLogger("system_setup")


if __name__ == "__main__":
    # 测试日志系统
    print("测试日志系统...")

    # 配置日志系统
    config = {
        'level': 'DEBUG',
        'format': '%(asctime)s - %(levelname)8s - %(name)s - %(message)s',
        'date_format': '%Y-%m-%d %H:%M:%S',
        'console': True,
        'file': {
            'path': './logs/test.log',
            'rotate': True,
            'max_size': 1024 * 1024,  # 1MB for testing
            'backup_count': 3
        }
    }
    configure_logging(config)

    # 获取日志器
    logger = get_logger("test_module")

    # 测试不同级别的日志
    logger.debug("这是一条调试信息")
    logger.info("这是一条普通信息")
    logger.warning("这是一条警告信息")
    logger.error("这是一条错误信息")

    # 测试TestLogger
    print("\n测试TestLogger...")
    test_logger = TestLogger("sample_test")
    test_logger.start_test("测试日志功能")
    test_logger.log_step(1, "打开浏览器", "使用Chrome浏览器")
    test_logger.log_action("输入用户名", "用户名: admin")
    test_logger.log_check("登录按钮是否可用", True, "按钮状态正常")
    test_logger.log_screenshot("login_page.png", "登录页面截图")
    test_logger.log_error("元素未找到", "ID为username的元素不存在")
    test_logger.end_test("通过", "所有测试步骤执行完成")

    # 测试文件处理器
    file_logger = get_logger("file_test")
    for i in range(100):
        file_logger.info(f"测试日志消息 {i+1}")

    print("\n日志系统测试完成")
    print("请检查 ./logs/test.log 文件")