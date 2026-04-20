#!/usr/bin/env python3
"""
电商后台自动化测试 - 主执行脚本
支持多种执行模式和参数配置
"""

import os
import sys
import argparse
import subprocess
import time
import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

# 导入自定义工具
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from utils.email_sender import EmailSender
    from utils.report_archiver import ReportArchiver
    from utils.html_report_generator import HTMLReportGenerator
    from utils.report_data import ReportData, create_report_data
    from utils.config_manager import get_config, init_config
    from utils.ai_analysis import AIAnalysisService
    from utils.test_executor import TestExecutor
    from utils.parallel_executor import ParallelExecutor
except ImportError as e:
    print(f"导入工具模块失败: {e}")
    print("请确保所有依赖已安装并运行在正确的环境中")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AUTOTEST_ROOT = Path(__file__).resolve().parent
SUPPORTED_TEST_TYPES = ['all', 'login', 'product', 'order', 'user', 'permission', 'smoke', 'regression']
SUPPORTED_COMMANDS = ['check', 'ai-check', 'list', 'cleanup', 'install-drivers', 'run', 'test', 'help', *SUPPORTED_TEST_TYPES]


def build_html_report_path(test_type: str) -> Path:
    """构建统一的 HTML 报告路径。"""
    init_config(str(AUTOTEST_ROOT / 'config' / 'config.yaml'))
    config = get_config()
    output_dir = config.get('report.output_dir', './reports')
    report_root = (PROJECT_ROOT / output_dir).resolve() / 'html'
    day_stamp = datetime.now().strftime("%Y-%m-%d")
    time_stamp = datetime.now().strftime("%H%M%S")
    report_dir = report_root / day_stamp / test_type / time_stamp
    report_dir.mkdir(parents=True, exist_ok=True)
    return report_dir / f"{test_type}.html"


def print_banner():
    """打印项目横幅"""
    banner = """
    ========================================================
        电商后台管理系统自动化测试框架
        版本: 1.0.0
        作者: 宋佳伟
        日期: 2026-04-04
    ========================================================
    """
    print(banner)


def print_quick_start():
    """打印更简洁的快速使用说明。"""
    print("常用命令:")
    print("  python run.py check                 # 检查环境和配置")
    print("  python run.py list                  # 查看可运行模块")
    print("  python run.py ai-check              # 检查 AI 配置和接口可用性")
    print("  python run.py login                 # 运行登录测试")
    print("  python run.py product               # 运行商品测试")
    print("  python run.py smoke                 # 运行冒烟测试")
    print("  python run.py all -j 4              # 并行运行全部测试")
    print("  python run.py regression --headless # 无头运行回归测试")
    print("")
    print("兼容旧写法:")
    print("  python run.py --run login")
    print("  python run.py --check")
    print("")

def check_dependencies():
    """检查项目依赖"""
    print("检查项目依赖...")

    required_packages = {
        'selenium': 'selenium',
        'pytest': 'pytest',
        'pytest-html': 'pytest_html',
        'PyYAML': 'yaml',
        'openpyxl': 'openpyxl',
        'Pillow': 'PIL',
        'requests': 'requests',
    }

    missing_packages = []
    for package, import_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"缺少依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False

    print("所有依赖包已安装")
    return True

def check_config():
    """检查配置文件"""
    print("检查配置文件...")

    config_path = AUTOTEST_ROOT / 'config' / 'config.yaml'
    example_path = AUTOTEST_ROOT / 'config' / 'config.yaml.example'

    if not config_path.exists() or config_path.stat().st_size == 0:
        if example_path.exists():
            print(f"配置文件 {config_path} 不存在或为空")
            print(f"正在从 {example_path} 复制配置模板...")
            try:
                import shutil
                shutil.copy2(example_path, config_path)
                print("配置模板已复制，请编辑 config/config.yaml 文件设置您的测试环境")
                print("重要: 需要设置 environment.base_url 为您的电商后台管理系统地址")
                return False
            except Exception as e:
                print(f"复制配置文件失败: {e}")
                return False
        else:
            print(f"配置模板文件 {example_path} 不存在")
            return False
    else:
        # 检查配置文件内容
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            init_config(str(config_path))

            base_url = config.get('environment', {}).get('base_url', '')
            if not base_url or base_url == 'http://test.ecommerce.com/admin':
                print(f"警告: 配置文件中的 base_url 仍然是示例地址: {base_url}")
                print("请编辑 config/config.yaml 文件，设置为您要测试的实际系统地址")
                return False

            print(f"配置文件检查通过，base_url: {base_url}")

            ai_enabled = config.get('ai', {}).get('enabled', False)
            if ai_enabled:
                ai_api_base = config.get('ai', {}).get('api_base', '')
                ai_model = config.get('ai', {}).get('model', '')
                print(f"AI 配置已启用，api_base: {ai_api_base}, model: {ai_model}")
            return True

        except Exception as e:
            print(f"配置文件解析失败: {e}")
            return False


def check_ai_service():
    """检查 AI 服务配置与可用性。"""
    print("检查 AI 服务...")
    init_config(str(AUTOTEST_ROOT / 'config' / 'config.yaml'))
    config = get_config()
    ai_service = AIAnalysisService(config)
    result = ai_service.health_check()

    print(f"状态: {result.get('status')}")
    print(f"信息: {result.get('message')}")
    if result.get('api_base'):
        print(f"接口地址: {result.get('api_base')}")
    if result.get('model'):
        print(f"模型: {result.get('model')}")

    return bool(result.get("ok"))

def process_report(report_file, test_type, execution_time, success, args=None):
    """
    处理测试报告：归档、发送邮件等

    Args:
        report_file: 报告文件路径
        test_type: 测试类型
        execution_time: 执行时间
        success: 是否成功

    Returns:
        bool: 处理是否成功
    """
    try:
        print(f"处理测试报告: {report_file}")

        # 获取配置
        config = get_config()
        report_config = config.get('report', {})
        send_email = report_config.get('send_email', False)
        auto_archive = report_config.get('auto_archive', True)

        # 命令行参数覆盖配置
        if args:
            if args.email:
                send_email = True
            if args.no_email:
                send_email = False
            if args.archive:
                auto_archive = True
            if args.no_archive:
                auto_archive = False

        # 归档报告
        if auto_archive and os.path.exists(report_file):
            print("归档测试报告...")
            try:
                from utils.report_archiver import archive_report

                # 尝试加载报告数据
                report_data = None
                report_data_file = report_file.replace('.html', '.json')
                if os.path.exists(report_data_file):
                    with open(report_data_file, 'r', encoding='utf-8') as f:
                        report_data = json.load(f)

                # 归档报告
                archive_id = archive_report(
                    report_file=report_file,
                    report_data=report_data,
                    tags=[test_type, 'automated']
                )

                if archive_id:
                    print(f"[OK] 报告归档成功，ID: {archive_id}")
                else:
                    print("[WARN] 报告归档失败")

            except Exception as e:
                print(f"归档报告时出错: {e}")

        # 发送邮件
        if send_email and os.path.exists(report_file):
            print("发送测试报告邮件...")
            try:
                from utils.email_sender import send_test_report

                # 生成邮件主题
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                subject = f"测试报告 - {test_type} - {timestamp}"

                # 发送邮件
                email_sent = send_test_report(
                    report_file=report_file,
                    subject=subject
                )

                if email_sent:
                    print("[OK] 测试报告邮件发送成功")
                else:
                    print("[WARN] 测试报告邮件发送失败")

            except Exception as e:
                print(f"发送邮件时出错: {e}")

        return True

    except Exception as e:
        print(f"处理报告时出错: {e}")
        return False

def cleanup_reports():
    """
    清理过期报告
    """
    try:
        print("清理过期报告...")

        # 获取配置
        config = get_config()
        report_config = config.get('report', {})
        retention_days = report_config.get('retention_days', 30)

        print(f"清理策略: 保留最近 {retention_days} 天的报告")

        # 导入归档管理器
        from utils.report_archiver import ReportArchiver

        # 创建归档管理器
        archiver = ReportArchiver(config)

        # 清理过期报告
        cleaned_count = archiver.cleanup_expired_reports()

        if cleaned_count > 0:
            print(f"[OK] 清理完成，共清理 {cleaned_count} 个过期报告")
        else:
            print("[OK] 没有需要清理的过期报告")

        # 显示统计信息
        stats = archiver.get_statistics()
        print(f"当前归档统计:")
        print(f"  总报告数: {stats.get('total_reports', 0)}")
        print(f"  总大小: {stats.get('total_size', 0) / (1024*1024):.2f} MB")
        print(f"  最近7天报告数: {stats.get('recent_reports_7d', 0)}")

        return True

    except Exception as e:
        print(f"清理报告时出错: {e}")
        return False

def install_browser_drivers():
    """安装浏览器驱动"""
    print("安装浏览器驱动...")

    drivers_path = os.path.join('utils', 'install_drivers.py')
    if os.path.exists(drivers_path):
        try:
            print("运行浏览器驱动安装工具...")
            subprocess.run([sys.executable, drivers_path], check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"驱动安装失败: {e}")
            print("请手动下载并安装浏览器驱动:")
            print("  ChromeDriver: https://chromedriver.chromium.org/")
            print("  GeckoDriver: https://github.com/mozilla/geckodriver")
            print("  EdgeDriver: https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/")
            return False
    else:
        print(f"驱动安装脚本不存在: {drivers_path}")
        return False

def run_tests(test_type, args):
    """运行测试"""
    print(f"运行 {test_type} 测试...")

    report_file = str(build_html_report_path(test_type))

    # 构建pytest命令
    pytest_args = [
        sys.executable, '-m', 'pytest',
        '-v',
        '--html=' + report_file,
        '--self-contained-html',
        '--capture=tee-sys'
    ]

    # 根据测试类型添加不同参数
    if test_type == 'all':
        pytest_args.extend(['testcases/'])
    elif test_type == 'login':
        pytest_args.extend(['testcases/test_login.py'])
    elif test_type == 'product':
        pytest_args.extend(['testcases/test_product.py'])
    elif test_type == 'order':
        pytest_args.extend(['testcases/test_order.py'])
    elif test_type == 'user':
        pytest_args.extend(['testcases/test_user.py'])
    elif test_type == 'permission':
        pytest_args.extend(['testcases/test_permission.py'])
    elif test_type == 'smoke':
        pytest_args.extend(['-m', 'smoke', 'testcases/'])
    elif test_type == 'regression':
        pytest_args.extend(['-m', 'regression', 'testcases/'])

    # 添加额外参数
    if args.workers and args.workers > 1:
        pytest_args.extend(['-n', str(args.workers)])

    if args.headless:
        pytest_args.extend(['--headless'])

    print(f"执行命令: {' '.join(pytest_args)}")

    try:
        start_time = time.time()
        result = subprocess.run(pytest_args, check=False, cwd=AUTOTEST_ROOT)
        end_time = time.time()

        execution_time = end_time - start_time
        print(f"\n测试执行完成，耗时: {execution_time:.2f} 秒")

        if result.returncode == 0:
            print(f"[SUCCESS] 所有测试通过!")
        else:
            print(f"[WARN]  有测试失败，返回码: {result.returncode}")

        print(f"\n测试报告已生成: {report_file}")
        print(f"日志文件: logs/test.log")

        # 处理报告（归档、发送邮件等）
        if os.path.exists(report_file):
            process_report(report_file, test_type, execution_time, result.returncode == 0, args)

        return result.returncode == 0

    except KeyboardInterrupt:
        print("\n测试被用户中断")
        return False
    except Exception as e:
        print(f"测试执行异常: {e}")
        return False

def show_test_cases():
    """显示可用的测试用例"""
    print("可用的测试用例:")
    print("")

    test_modules = [
        ("登录功能", "testcases/test_login.py", "测试用户登录、注销、异常登录等"),
        ("商品管理", "testcases/test_product.py", "测试商品增删改查、搜索筛选等"),
        ("订单管理", "testcases/test_order.py", "测试订单处理、状态流转、统计导出等"),
        ("用户管理", "testcases/test_user.py", "测试用户增删改查、权限分配等"),
        ("权限管理", "testcases/test_permission.py", "测试角色管理、权限验证等"),
    ]

    for name, path, desc in test_modules:
        if os.path.exists(path):
            print(f"  * {name}")
            print(f"     文件: {path}")
            print(f"     描述: {desc}")
            print("")
        else:
            print(f"  * {name} (文件不存在: {path})")
            print("")


def resolve_action(args) -> Tuple[Optional[str], Optional[str]]:
    """
    解析命令动作。

    Returns:
        (action, test_type)
    """
    if args.check:
        return "check", None
    if args.install_drivers:
        return "install-drivers", None
    if getattr(args, "ai_check", False):
        return "ai-check", None
    if args.cleanup:
        return "cleanup", None
    if args.list:
        return "list", None
    if args.run:
        return "run", args.run

    command = (args.command or "").strip().lower()
    target = (args.target or "").strip().lower()

    if not command:
        return None, None

    if command in SUPPORTED_TEST_TYPES:
        return "run", command

    if command in {"run", "test"}:
        if target in SUPPORTED_TEST_TYPES:
            return "run", target
        return "invalid-run", None

    if command in {"check", "ai-check", "list", "cleanup", "install-drivers", "help"}:
        return command, None

    return "unknown", None

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='电商后台管理系统自动化测试框架',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s check                     # 检查环境和配置
  %(prog)s ai-check                  # 检查 AI 配置和接口
  %(prog)s login                     # 运行登录测试
  %(prog)s smoke -j 4                # 使用4个worker运行冒烟测试
  %(prog)s run product --headless    # 无头运行商品测试
  %(prog)s list                      # 列出所有测试用例
  %(prog)s --run all                 # 兼容旧写法
        """
    )

    parser.add_argument('command', nargs='?', help='简化命令：check/list/login/product/order/user/permission/smoke/regression/all')
    parser.add_argument('target', nargs='?', help='当使用 run/test 时指定测试目标')
    parser.add_argument('--check', action='store_true',
                       help='检查项目环境和配置')
    parser.add_argument('--ai-check', action='store_true',
                       help='检查 AI 配置与接口连通性')
    parser.add_argument('--install-drivers', action='store_true',
                       help='安装浏览器驱动')
    parser.add_argument('--run', choices=SUPPORTED_TEST_TYPES,
                       help='运行指定类型的测试')
    parser.add_argument('-j', '--workers', type=int, default=1,
                       help='并行执行的工作进程数 (默认: 1)')
    parser.add_argument('-H', '--headless', action='store_true',
                       help='使用无头浏览器模式')
    parser.add_argument('--list', action='store_true',
                       help='列出所有可用的测试用例')
    parser.add_argument('--email', action='store_true',
                       help='发送测试报告邮件（覆盖配置文件设置）')
    parser.add_argument('--no-email', action='store_true',
                       help='不发送测试报告邮件（覆盖配置文件设置）')
    parser.add_argument('--archive', action='store_true',
                       help='归档测试报告（覆盖配置文件设置）')
    parser.add_argument('--no-archive', action='store_true',
                       help='不归档测试报告（覆盖配置文件设置）')
    parser.add_argument('--cleanup', action='store_true',
                       help='清理过期报告')

    args = parser.parse_args()

    # 打印横幅
    print_banner()

    action, test_type = resolve_action(args)

    # 如果没有参数，显示更友好的快速提示
    if action is None:
        print_quick_start()
        parser.print_help()
        return 0

    if action == "help":
        print_quick_start()
        parser.print_help()
        return 0

    if action == "unknown":
        print(f"[ERROR] 不支持的命令: {args.command}")
        print_quick_start()
        return 1

    if action == "invalid-run":
        print("[ERROR] 请指定要运行的测试目标。")
        print("可选值: " + ", ".join(SUPPORTED_TEST_TYPES))
        print("")
        print("例如:")
        print("  python run.py run login")
        print("  python run.py test smoke")
        return 1

    # 检查环境和配置
    if action == "check":
        print("执行环境检查...")
        deps_ok = check_dependencies()
        config_ok = check_config()

        if deps_ok and config_ok:
            print("[OK] 环境和配置检查通过")
            return 0
        else:
            print("[ERROR] 环境或配置检查未通过")
            return 1

    if action == "ai-check":
        deps_ok = check_dependencies()
        config_ok = check_config()
        if not deps_ok or not config_ok:
            print("[ERROR] 基础环境或配置检查未通过，无法继续检查 AI 服务。")
            return 1
        return 0 if check_ai_service() else 1

    # 安装浏览器驱动
    if action == "install-drivers":
        return 0 if install_browser_drivers() else 1

    # 清理过期报告
    if action == "cleanup":
        return 0 if cleanup_reports() else 1

    # 列出测试用例
    if action == "list":
        show_test_cases()
        return 0

    # 运行测试
    if action == "run" and test_type:
        # 先检查环境和配置
        if not check_dependencies():
            print("[ERROR] 依赖检查失败，请先运行: python run.py --check")
            return 1

        if not check_config():
            print("[ERROR] 配置检查失败，请先编辑 config/config.yaml 文件")
            print("   然后运行: python run.py --check")
            return 1

        # 运行测试
        success = run_tests(test_type, args)
        return 0 if success else 1

    return 0

if __name__ == '__main__':
    sys.exit(main())
