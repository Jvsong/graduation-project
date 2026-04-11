#!/usr/bin/env python3
"""
浏览器驱动自动安装工具
支持自动下载和安装 ChromeDriver、GeckoDriver、EdgeDriver
"""

import os
import sys
import zipfile
import tarfile
import platform
import subprocess
import stat
from pathlib import Path
import requests
import re
import shutil

class DriverInstaller:
    """浏览器驱动安装器"""

    def __init__(self, install_dir=None):
        """
        初始化安装器

        Args:
            install_dir: 驱动安装目录，默认为项目根目录下的browsers文件夹
        """
        self.install_dir = install_dir or os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'config', 'browsers'
        )
        os.makedirs(self.install_dir, exist_ok=True)

        # 系统信息
        self.system = platform.system().lower()  # windows, linux, darwin
        self.architecture = platform.machine().lower()  # x86_64, amd64, arm64

    def install_all_drivers(self):
        """安装所有浏览器驱动"""
        print("开始安装浏览器驱动...")

        drivers_installed = []

        # 安装 ChromeDriver
        try:
            chrome_path = self.install_chromedriver()
            if chrome_path:
                drivers_installed.append(('ChromeDriver', chrome_path))
        except Exception as e:
            print(f"ChromeDriver 安装失败: {e}")

        # 安装 GeckoDriver (Firefox)
        try:
            firefox_path = self.install_geckodriver()
            if firefox_path:
                drivers_installed.append(('GeckoDriver', firefox_path))
        except Exception as e:
            print(f"GeckoDriver 安装失败: {e}")

        # 安装 EdgeDriver
        try:
            edge_path = self.install_edgedriver()
            if edge_path:
                drivers_installed.append(('EdgeDriver', edge_path))
        except Exception as e:
            print(f"EdgeDriver 安装失败: {e}")

        print("\n安装完成!")
        for name, path in drivers_installed:
            print(f"  {name}: {path}")

        return drivers_installed

    def install_chromedriver(self):
        """安装 ChromeDriver"""
        print("\n正在安装 ChromeDriver...")

        # 获取 Chrome 版本
        chrome_version = self._get_chrome_version()
        if not chrome_version:
            chrome_version = "114.0.5735.90"  # 默认版本

        print(f"检测到 Chrome 版本: {chrome_version}")

        # 获取 ChromeDriver 版本
        driver_version = self._get_chromedriver_version(chrome_version)
        print(f"将安装 ChromeDriver 版本: {driver_version}")

        # 下载 ChromeDriver
        download_url = self._get_chromedriver_download_url(driver_version)
        driver_path = self._download_and_extract(download_url, 'chromedriver')

        if driver_path:
            print(f"ChromeDriver 安装成功: {driver_path}")
            return driver_path

        return None

    def install_geckodriver(self):
        """安装 GeckoDriver (Firefox)"""
        print("\n正在安装 GeckoDriver...")

        # 获取最新版本
        latest_version = self._get_latest_geckodriver_version()
        print(f"将安装 GeckoDriver 版本: {latest_version}")

        # 下载 GeckoDriver
        download_url = self._get_geckodriver_download_url(latest_version)
        driver_path = self._download_and_extract(download_url, 'geckodriver')

        if driver_path:
            print(f"GeckoDriver 安装成功: {driver_path}")
            return driver_path

        return None

    def install_edgedriver(self):
        """安装 EdgeDriver"""
        print("\n正在安装 EdgeDriver...")

        # 获取 Edge 版本
        edge_version = self._get_edge_version()
        if not edge_version:
            edge_version = "114.0.1823.58"  # 默认版本

        print(f"检测到 Edge 版本: {edge_version}")

        # 获取 EdgeDriver 版本
        driver_version = self._get_edgedriver_version(edge_version)
        print(f"将安装 EdgeDriver 版本: {driver_version}")

        # 下载 EdgeDriver
        download_url = self._get_edgedriver_download_url(driver_version)
        driver_path = self._download_and_extract(download_url, 'msedgedriver')

        if driver_path:
            print(f"EdgeDriver 安装成功: {driver_path}")
            return driver_path

        return None

    def _get_chrome_version(self):
        """获取 Chrome 浏览器版本"""
        try:
            if self.system == 'windows':
                # Windows 注册表查找 Chrome 版本
                import winreg
                try:
                    key = winreg.OpenKey(
                        winreg.HKEY_CURRENT_USER,
                        r"Software\Google\Chrome\BLBeacon"
                    )
                    version, _ = winreg.QueryValueEx(key, "version")
                    winreg.CloseKey(key)
                    return version
                except:
                    # 尝试在程序文件中查找
                    chrome_paths = [
                        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
                        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
                        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe")
                    ]

                    for path in chrome_paths:
                        if os.path.exists(path):
                            version = subprocess.check_output(
                                [path, '--version'],
                                stderr=subprocess.STDOUT,
                                text=True
                            ).strip()
                            match = re.search(r'(\d+\.\d+\.\d+\.\d+)', version)
                            if match:
                                return match.group(1)

            elif self.system == 'darwin':  # macOS
                # macOS 通过命令行获取 Chrome 版本
                version = subprocess.check_output(
                    ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '--version'],
                    stderr=subprocess.STDOUT,
                    text=True
                ).strip()
                match = re.search(r'(\d+\.\d+\.\d+\.\d+)', version)
                if match:
                    return match.group(1)

            elif self.system == 'linux':
                # Linux 通过命令行获取 Chrome 版本
                version = subprocess.check_output(
                    ['google-chrome', '--version'],
                    stderr=subprocess.STDOUT,
                    text=True
                ).strip()
                match = re.search(r'(\d+\.\d+\.\d+\.\d+)', version)
                if match:
                    return match.group(1)

        except Exception as e:
            print(f"获取 Chrome 版本失败: {e}")

        return None

    def _get_edge_version(self):
        """获取 Edge 浏览器版本"""
        try:
            if self.system == 'windows':
                # Windows 注册表查找 Edge 版本
                import winreg
                try:
                    key = winreg.OpenKey(
                        winreg.HKEY_CURRENT_USER,
                        r"Software\Microsoft\Edge\BLBeacon"
                    )
                    version, _ = winreg.QueryValueEx(key, "version")
                    winreg.CloseKey(key)
                    return version
                except:
                    # 尝试在程序文件中查找
                    edge_paths = [
                        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
                        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
                        os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe")
                    ]

                    for path in edge_paths:
                        if os.path.exists(path):
                            version = subprocess.check_output(
                                [path, '--version'],
                                stderr=subprocess.STDOUT,
                                text=True
                            ).strip()
                            match = re.search(r'(\d+\.\d+\.\d+\.\d+)', version)
                            if match:
                                return match.group(1)

            elif self.system == 'darwin':  # macOS
                # macOS 通过命令行获取 Edge 版本
                version = subprocess.check_output(
                    ['/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge', '--version'],
                    stderr=subprocess.STDOUT,
                    text=True
                ).strip()
                match = re.search(r'(\d+\.\d+\.\d+\.\d+)', version)
                if match:
                    return match.group(1)

            elif self.system == 'linux':
                # Linux 通过命令行获取 Edge 版本
                version = subprocess.check_output(
                    ['microsoft-edge', '--version'],
                    stderr=subprocess.STDOUT,
                    text=True
                ).strip()
                match = re.search(r'(\d+\.\d+\.\d+\.\d+)', version)
                if match:
                    return match.group(1)

        except Exception as e:
            print(f"获取 Edge 版本失败: {e}")

        return None

    def _get_chromedriver_version(self, chrome_version):
        """根据 Chrome 版本获取对应的 ChromeDriver 版本"""
        # 简化版本匹配：取主要版本号
        major_version = chrome_version.split('.')[0]

        # 尝试获取准确的版本匹配
        try:
            # 从 ChromeDriver 版本列表获取匹配的版本
            version_url = "https://chromedriver.storage.googleapis.com/LATEST_RELEASE"
            response = requests.get(version_url, timeout=10)
            latest_version = response.text.strip()

            # 检查是否有特定版本的发布
            specific_version_url = f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{major_version}"
            response = requests.get(specific_version_url, timeout=10)
            if response.status_code == 200:
                return response.text.strip()
            else:
                return latest_version
        except:
            # 如果网络请求失败，使用主要版本号
            return f"{major_version}.0.0.0"

    def _get_latest_geckodriver_version(self):
        """获取最新的 GeckoDriver 版本"""
        try:
            # 从 GitHub API 获取最新版本
            api_url = "https://api.github.com/repos/mozilla/geckodriver/releases/latest"
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data['tag_name'].lstrip('v')
        except:
            pass

        # 如果获取失败，返回一个稳定版本
        return "0.34.0"

    def _get_edgedriver_version(self, edge_version):
        """根据 Edge 版本获取对应的 EdgeDriver 版本"""
        # 简化版本匹配：取主要版本号
        major_version = edge_version.split('.')[0]
        return f"{major_version}.0.0.0"

    def _get_chromedriver_download_url(self, version):
        """获取 ChromeDriver 下载 URL"""
        # 系统架构映射
        arch_map = {
            'windows': 'win32',
            'darwin': 'mac64',
            'linux': 'linux64'
        }

        system_key = arch_map.get(self.system, 'win32')

        # ChromeDriver 下载 URL 模板
        if self.system == 'windows':
            filename = f"chromedriver_{system_key}.zip"
        else:
            filename = f"chromedriver_{system_key}.zip"

        return f"https://chromedriver.storage.googleapis.com/{version}/{filename}"

    def _get_geckodriver_download_url(self, version):
        """获取 GeckoDriver 下载 URL"""
        # 系统架构映射
        arch_map = {
            'windows': 'win32',
            'darwin': 'macos',
            'linux': 'linux64'
        }

        system_key = arch_map.get(self.system, 'win32')

        # GeckoDriver 下载 URL 模板
        if self.system == 'windows':
            filename = f"geckodriver-{version}-{system_key}.zip"
        elif self.system == 'darwin':
            if 'arm' in self.architecture:
                filename = f"geckodriver-{version}-macos-aarch64.tar.gz"
            else:
                filename = f"geckodriver-{version}-macos.tar.gz"
        else:
            filename = f"geckodriver-{version}-{system_key}.tar.gz"

        return f"https://github.com/mozilla/geckodriver/releases/download/v{version}/{filename}"

    def _get_edgedriver_download_url(self, version):
        """获取 EdgeDriver 下载 URL"""
        # 系统架构映射
        arch_map = {
            'windows': 'win32',
            'darwin': 'mac64',
            'linux': 'linux64'
        }

        system_key = arch_map.get(self.system, 'win32')

        # EdgeDriver 下载 URL 模板
        if self.system == 'windows':
            filename = f"edgedriver_{system_key}.zip"
        elif self.system == 'darwin':
            if 'arm' in self.architecture:
                filename = f"edgedriver_{system_key}_arm64.zip"
            else:
                filename = f"edgedriver_{system_key}.zip"
        else:
            filename = f"edgedriver_{system_key}.zip"

        return f"https://msedgedriver.azureedge.net/{version}/{filename}"

    def _download_and_extract(self, url, driver_name):
        """下载并解压驱动文件"""
        try:
            print(f"下载驱动: {url}")

            # 下载文件
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            # 保存压缩文件
            temp_dir = os.path.join(self.install_dir, 'temp')
            os.makedirs(temp_dir, exist_ok=True)

            zip_filename = os.path.join(temp_dir, f"{driver_name}.zip")
            tar_filename = os.path.join(temp_dir, f"{driver_name}.tar.gz")

            if url.endswith('.zip'):
                filepath = zip_filename
            else:
                filepath = tar_filename

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            print(f"下载完成: {filepath}")

            # 解压文件
            extract_dir = os.path.join(temp_dir, driver_name)
            os.makedirs(extract_dir, exist_ok=True)

            if filepath.endswith('.zip'):
                with zipfile.ZipFile(filepath, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
            else:
                with tarfile.open(filepath, 'r:gz') as tar_ref:
                    tar_ref.extractall(extract_dir)

            print(f"解压完成: {extract_dir}")

            # 查找驱动可执行文件
            driver_file = None
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    if driver_name in file.lower() and not file.endswith('.exe') and not file.endswith('.md'):
                        # 对于非Windows系统，需要查找无扩展名的文件
                        driver_file = os.path.join(root, file)
                        break
                    elif file.lower().endswith('.exe') and driver_name in file.lower():
                        driver_file = os.path.join(root, file)
                        break

            if not driver_file:
                # 如果没有找到，尝试查找第一个可执行文件
                for root, dirs, files in os.walk(extract_dir):
                    for file in files:
                        if self.system == 'windows' and file.endswith('.exe'):
                            driver_file = os.path.join(root, file)
                            break
                        elif self.system != 'windows' and not file.endswith('.md'):
                            driver_file = os.path.join(root, file)
                            break

            if driver_file:
                # 复制到安装目录
                final_path = os.path.join(self.install_dir, os.path.basename(driver_file))
                shutil.copy2(driver_file, final_path)

                # 设置可执行权限（非Windows系统）
                if self.system != 'windows':
                    os.chmod(final_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

                # 清理临时文件
                shutil.rmtree(temp_dir, ignore_errors=True)

                return final_path
            else:
                print(f"未找到驱动可执行文件")
                return None

        except Exception as e:
            print(f"下载或解压失败: {e}")
            import traceback
            traceback.print_exc()
            return None

def main():
    """主函数"""
    print("=" * 60)
    print("电商后台自动化测试 - 浏览器驱动安装工具")
    print("=" * 60)

    # 创建安装器
    installer = DriverInstaller()

    # 安装所有驱动
    drivers = installer.install_all_drivers()

    if drivers:
        print("\n驱动安装完成！")
        print("请将以下路径添加到系统 PATH 环境变量:")
        for name, path in drivers:
            print(f"  {name}: {os.path.dirname(path)}")
    else:
        print("\n驱动安装失败，请手动下载并安装浏览器驱动。")
        print("参考链接:")
        print("  ChromeDriver: https://chromedriver.chromium.org/")
        print("  GeckoDriver: https://github.com/mozilla/geckodriver")
        print("  EdgeDriver: https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/")

if __name__ == "__main__":
    main()