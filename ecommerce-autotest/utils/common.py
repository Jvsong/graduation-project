#!/usr/bin/env python3
"""
通用工具函数模块
提供文件操作、时间处理、字符串处理等通用功能
"""

import os
import sys
import json
import time
import random
import string
import hashlib
import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path


class FileUtils:
    """文件操作工具类"""

    @staticmethod
    def ensure_directory(directory: str) -> bool:
        """
        确保目录存在，如果不存在则创建

        Args:
            directory: 目录路径

        Returns:
            bool: 是否成功
        """
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"创建目录失败: {directory}, 错误: {e}")
            return False

    @staticmethod
    def file_exists(filepath: str) -> bool:
        """
        检查文件是否存在

        Args:
            filepath: 文件路径

        Returns:
            bool: 文件是否存在
        """
        return Path(filepath).exists()

    @staticmethod
    def read_file(filepath: str, encoding: str = 'utf-8') -> Optional[str]:
        """
        读取文件内容

        Args:
            filepath: 文件路径
            encoding: 文件编码

        Returns:
            Optional[str]: 文件内容，如果读取失败则返回None
        """
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                return f.read()
        except Exception as e:
            print(f"读取文件失败: {filepath}, 错误: {e}")
            return None

    @staticmethod
    def write_file(filepath: str, content: str, encoding: str = 'utf-8') -> bool:
        """
        写入文件内容

        Args:
            filepath: 文件路径
            content: 文件内容
            encoding: 文件编码

        Returns:
            bool: 是否成功
        """
        try:
            # 确保目录存在
            FileUtils.ensure_directory(os.path.dirname(filepath))

            with open(filepath, 'w', encoding=encoding) as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"写入文件失败: {filepath}, 错误: {e}")
            return False

    @staticmethod
    def append_file(filepath: str, content: str, encoding: str = 'utf-8') -> bool:
        """
        追加文件内容

        Args:
            filepath: 文件路径
            content: 文件内容
            encoding: 文件编码

        Returns:
            bool: 是否成功
        """
        try:
            # 确保目录存在
            FileUtils.ensure_directory(os.path.dirname(filepath))

            with open(filepath, 'a', encoding=encoding) as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"追加文件失败: {filepath}, 错误: {e}")
            return False

    @staticmethod
    def delete_file(filepath: str) -> bool:
        """
        删除文件

        Args:
            filepath: 文件路径

        Returns:
            bool: 是否成功
        """
        try:
            if Path(filepath).exists():
                Path(filepath).unlink()
            return True
        except Exception as e:
            print(f"删除文件失败: {filepath}, 错误: {e}")
            return False

    @staticmethod
    def list_files(directory: str, pattern: str = "*") -> List[str]:
        """
        列出目录中的文件

        Args:
            directory: 目录路径
            pattern: 文件匹配模式

        Returns:
            List[str]: 文件路径列表
        """
        try:
            if not Path(directory).exists():
                return []

            files = []
            for item in Path(directory).glob(pattern):
                if item.is_file():
                    files.append(str(item))
            return sorted(files)
        except Exception as e:
            print(f"列出文件失败: {directory}, 错误: {e}")
            return []

    @staticmethod
    def get_file_size(filepath: str) -> int:
        """
        获取文件大小（字节）

        Args:
            filepath: 文件路径

        Returns:
            int: 文件大小（字节）
        """
        try:
            return Path(filepath).stat().st_size
        except Exception as e:
            print(f"获取文件大小失败: {filepath}, 错误: {e}")
            return 0

    @staticmethod
    def get_file_modified_time(filepath: str) -> Optional[datetime.datetime]:
        """
        获取文件修改时间

        Args:
            filepath: 文件路径

        Returns:
            Optional[datetime.datetime]: 修改时间
        """
        try:
            timestamp = Path(filepath).stat().st_mtime
            return datetime.datetime.fromtimestamp(timestamp)
        except Exception as e:
            print(f"获取文件修改时间失败: {filepath}, 错误: {e}")
            return None

    @staticmethod
    def copy_file(src: str, dst: str) -> bool:
        """
        复制文件

        Args:
            src: 源文件路径
            dst: 目标文件路径

        Returns:
            bool: 是否成功
        """
        try:
            # 确保目标目录存在
            FileUtils.ensure_directory(os.path.dirname(dst))

            import shutil
            shutil.copy2(src, dst)
            return True
        except Exception as e:
            print(f"复制文件失败: {src} -> {dst}, 错误: {e}")
            return False

    @staticmethod
    def move_file(src: str, dst: str) -> bool:
        """
        移动文件

        Args:
            src: 源文件路径
            dst: 目标文件路径

        Returns:
            bool: 是否成功
        """
        try:
            # 确保目标目录存在
            FileUtils.ensure_directory(os.path.dirname(dst))

            import shutil
            shutil.move(src, dst)
            return True
        except Exception as e:
            print(f"移动文件失败: {src} -> {dst}, 错误: {e}")
            return False


class TimeUtils:
    """时间处理工具类"""

    @staticmethod
    def get_current_time() -> str:
        """
        获取当前时间字符串

        Returns:
            str: 格式为 YYYY-MM-DD HH:MM:SS 的时间字符串
        """
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def get_current_timestamp() -> float:
        """
        获取当前时间戳

        Returns:
            float: 时间戳（秒）
        """
        return time.time()

    @staticmethod
    def format_timestamp(timestamp: float, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
        """
        格式化时间戳

        Args:
            timestamp: 时间戳（秒）
            fmt: 时间格式

        Returns:
            str: 格式化后的时间字符串
        """
        return datetime.datetime.fromtimestamp(timestamp).strftime(fmt)

    @staticmethod
    def sleep(seconds: float) -> None:
        """
        睡眠指定秒数

        Args:
            seconds: 秒数
        """
        time.sleep(seconds)

    @staticmethod
    def calculate_duration(start_time: float, end_time: Optional[float] = None) -> float:
        """
        计算持续时间

        Args:
            start_time: 开始时间戳
            end_time: 结束时间戳，如果为None则使用当前时间

        Returns:
            float: 持续时间（秒）
        """
        if end_time is None:
            end_time = time.time()
        return end_time - start_time

    @staticmethod
    def format_duration(seconds: float) -> str:
        """
        格式化持续时间

        Args:
            seconds: 秒数

        Returns:
            str: 格式化的持续时间字符串
        """
        if seconds < 60:
            return f"{seconds:.2f}秒"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.2f}分钟"
        elif seconds < 86400:
            hours = seconds / 3600
            return f"{hours:.2f}小时"
        else:
            days = seconds / 86400
            return f"{days:.2f}天"

    @staticmethod
    def get_date_range(start_date: str, end_date: str, date_format: str = "%Y-%m-%d") -> List[str]:
        """
        获取日期范围内的所有日期

        Args:
            start_date: 开始日期
            end_date: 结束日期
            date_format: 日期格式

        Returns:
            List[str]: 日期字符串列表
        """
        try:
            start = datetime.datetime.strptime(start_date, date_format)
            end = datetime.datetime.strptime(end_date, date_format)

            dates = []
            current = start
            while current <= end:
                dates.append(current.strftime(date_format))
                current += datetime.timedelta(days=1)

            return dates
        except Exception as e:
            print(f"获取日期范围失败: {start_date} - {end_date}, 错误: {e}")
            return []


class StringUtils:
    """字符串处理工具类"""

    @staticmethod
    def generate_random_string(length: int = 10, include_digits: bool = True,
                               include_special: bool = False) -> str:
        """
        生成随机字符串

        Args:
            length: 字符串长度
            include_digits: 是否包含数字
            include_special: 是否包含特殊字符

        Returns:
            str: 随机字符串
        """
        chars = string.ascii_letters
        if include_digits:
            chars += string.digits
        if include_special:
            chars += string.punctuation

        return ''.join(random.choice(chars) for _ in range(length))

    @staticmethod
    def generate_random_email(domain: str = "example.com") -> str:
        """
        生成随机邮箱地址

        Args:
            domain: 邮箱域名

        Returns:
            str: 随机邮箱地址
        """
        username = StringUtils.generate_random_string(8, include_digits=True, include_special=False)
        return f"{username}@{domain}"

    @staticmethod
    def generate_random_phone(country_code: str = "86") -> str:
        """
        生成随机手机号

        Args:
            country_code: 国家代码

        Returns:
            str: 随机手机号
        """
        # 生成11位手机号（中国大陆格式）
        prefix = random.choice(["130", "131", "132", "133", "134", "135", "136",
                               "137", "138", "139", "150", "151", "152", "153",
                               "155", "156", "157", "158", "159", "170", "171",
                               "172", "173", "174", "175", "176", "177", "178",
                               "180", "181", "182", "183", "184", "185", "186",
                               "187", "188", "189"])
        suffix = ''.join(random.choice(string.digits) for _ in range(8))
        return f"{country_code}{prefix}{suffix}"

    @staticmethod
    def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
        """
        截断字符串

        Args:
            text: 原始字符串
            max_length: 最大长度
            suffix: 后缀

        Returns:
            str: 截断后的字符串
        """
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix

    @staticmethod
    def is_valid_email(email: str) -> bool:
        """
        验证邮箱格式

        Args:
            email: 邮箱地址

        Returns:
            bool: 是否有效
        """
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    @staticmethod
    def is_valid_phone(phone: str) -> bool:
        """
        验证手机号格式（中国大陆）

        Args:
            phone: 手机号

        Returns:
            bool: 是否有效
        """
        import re
        pattern = r'^1[3-9]\d{9}$'
        return bool(re.match(pattern, phone))

    @staticmethod
    def mask_string(text: str, visible_start: int = 3, visible_end: int = 4,
                    mask_char: str = "*") -> str:
        """
        掩码字符串（用于隐藏敏感信息）

        Args:
            text: 原始字符串
            visible_start: 开头可见字符数
            visible_end: 结尾可见字符数
            mask_char: 掩码字符

        Returns:
            str: 掩码后的字符串
        """
        if len(text) <= visible_start + visible_end:
            return text

        start = text[:visible_start]
        end = text[-visible_end:] if visible_end > 0 else ""
        middle = mask_char * (len(text) - visible_start - visible_end)

        return start + middle + end

    @staticmethod
    def camel_to_snake(text: str) -> str:
        """
        驼峰命名转蛇形命名

        Args:
            text: 驼峰命名字符串

        Returns:
            str: 蛇形命名字符串
        """
        import re
        # 在大写字母前插入下划线，然后全部转小写
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    @staticmethod
    def snake_to_camel(text: str) -> str:
        """
        蛇形命名转驼峰命名

        Args:
            text: 蛇形命名字符串

        Returns:
            str: 驼峰命名字符串
        """
        components = text.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])


class DataUtils:
    """数据处理工具类"""

    @staticmethod
    def dict_to_json(data: Dict, indent: int = 2) -> Optional[str]:
        """
        字典转JSON字符串

        Args:
            data: 字典数据
            indent: 缩进空格数

        Returns:
            Optional[str]: JSON字符串
        """
        try:
            return json.dumps(data, ensure_ascii=False, indent=indent)
        except Exception as e:
            print(f"字典转JSON失败: {e}")
            return None

    @staticmethod
    def json_to_dict(json_str: str) -> Optional[Dict]:
        """
        JSON字符串转字典

        Args:
            json_str: JSON字符串

        Returns:
            Optional[Dict]: 字典数据
        """
        try:
            return json.loads(json_str)
        except Exception as e:
            print(f"JSON转字典失败: {e}")
            return None

    @staticmethod
    def save_json(data: Dict, filepath: str, indent: int = 2) -> bool:
        """
        保存字典为JSON文件

        Args:
            data: 字典数据
            filepath: 文件路径
            indent: 缩进空格数

        Returns:
            bool: 是否成功
        """
        try:
            FileUtils.ensure_directory(os.path.dirname(filepath))
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=indent)
            return True
        except Exception as e:
            print(f"保存JSON文件失败: {filepath}, 错误: {e}")
            return False

    @staticmethod
    def load_json(filepath: str) -> Optional[Dict]:
        """
        加载JSON文件

        Args:
            filepath: 文件路径

        Returns:
            Optional[Dict]: 字典数据
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载JSON文件失败: {filepath}, 错误: {e}")
            return None

    @staticmethod
    def get_md5(text: str) -> str:
        """
        计算字符串的MD5值

        Args:
            text: 输入字符串

        Returns:
            str: MD5哈希值
        """
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    @staticmethod
    def get_file_md5(filepath: str) -> Optional[str]:
        """
        计算文件的MD5值

        Args:
            filepath: 文件路径

        Returns:
            Optional[str]: MD5哈希值
        """
        try:
            hash_md5 = hashlib.md5()
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            print(f"计算文件MD5失败: {filepath}, 错误: {e}")
            return None

    @staticmethod
    def deep_merge(dict1: Dict, dict2: Dict) -> Dict:
        """
        深度合并两个字典

        Args:
            dict1: 第一个字典
            dict2: 第二个字典

        Returns:
            Dict: 合并后的字典
        """
        result = dict1.copy()

        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = DataUtils.deep_merge(result[key], value)
            else:
                result[key] = value

        return result


class ValidationUtils:
    """数据验证工具类"""

    @staticmethod
    def is_none_or_empty(value: Any) -> bool:
        """
        检查值是否为None或空字符串

        Args:
            value: 要检查的值

        Returns:
            bool: 是否为None或空
        """
        return value is None or (isinstance(value, str) and value.strip() == "")

    @staticmethod
    def is_valid_integer(value: Any) -> bool:
        """
        检查值是否为有效整数

        Args:
            value: 要检查的值

        Returns:
            bool: 是否为有效整数
        """
        try:
            if isinstance(value, int):
                return True
            if isinstance(value, str):
                int(value)
                return True
            return False
        except (ValueError, TypeError):
            return False

    @staticmethod
    def is_valid_float(value: Any) -> bool:
        """
        检查值是否为有效浮点数

        Args:
            value: 要检查的值

        Returns:
            bool: 是否为有效浮点数
        """
        try:
            if isinstance(value, (int, float)):
                return True
            if isinstance(value, str):
                float(value)
                return True
            return False
        except (ValueError, TypeError):
            return False

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """
        检查URL是否有效

        Args:
            url: URL字符串

        Returns:
            bool: 是否有效
        """
        import re
        pattern = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return bool(re.match(pattern, url))

    @staticmethod
    def is_valid_date(date_string: str, fmt: str = "%Y-%m-%d") -> bool:
        """
        检查日期字符串是否有效

        Args:
            date_string: 日期字符串
            fmt: 日期格式

        Returns:
            bool: 是否有效
        """
        try:
            datetime.datetime.strptime(date_string, fmt)
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_required(data: Dict, required_fields: List[str]) -> Tuple[bool, List[str]]:
        """
        验证必要字段

        Args:
            data: 数据字典
            required_fields: 必要字段列表

        Returns:
            Tuple[bool, List[str]]: (是否通过验证, 缺失字段列表)
        """
        missing_fields = []
        for field in required_fields:
            if field not in data or ValidationUtils.is_none_or_empty(data[field]):
                missing_fields.append(field)

        return len(missing_fields) == 0, missing_fields


# 创建工具类实例
file_utils = FileUtils()
time_utils = TimeUtils()
string_utils = StringUtils()
data_utils = DataUtils()
validation_utils = ValidationUtils()


if __name__ == "__main__":
    # 测试工具函数
    print("测试通用工具函数...")

    # 测试文件操作
    test_file = "./test_tool.txt"
    content = "测试内容"
    file_utils.write_file(test_file, content)
    read_content = file_utils.read_file(test_file)
    print(f"文件读写测试: {read_content == content}")
    file_utils.delete_file(test_file)

    # 测试时间处理
    print(f"当前时间: {time_utils.get_current_time()}")
    print(f"当前时间戳: {time_utils.get_current_timestamp()}")

    # 测试字符串处理
    random_str = string_utils.generate_random_string()
    print(f"随机字符串: {random_str}")
    print(f"随机邮箱: {string_utils.generate_random_email()}")
    print(f"随机手机号: {string_utils.generate_random_phone()}")

    # 测试数据处理
    test_dict = {"name": "测试", "value": 123}
    json_str = data_utils.dict_to_json(test_dict)
    print(f"JSON转换测试: {json_str}")

    # 测试数据验证
    print(f"邮箱验证: {validation_utils.is_valid_email('test@example.com')}")
    print(f"手机号验证: {validation_utils.is_valid_phone('13800138000')}")

    print("\n通用工具函数测试完成")