#!/usr/bin/env python3
"""
邮件发送工具
发送测试报告邮件，支持HTML格式和附件
"""

import os
import sys
import smtplib
import ssl
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.header import Header
from email.utils import formataddr

from utils.logger import get_logger
from utils.config_manager import get_config


class EmailSender:
    """
    邮件发送器
    发送测试报告邮件
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化邮件发送器

        Args:
            config: 配置字典
        """
        self.logger = get_logger(self.__class__.__name__)

        # 获取配置
        if config is None:
            self.config = get_config()
        else:
            self.config = config

        # 邮件配置
        self.email_config = self.config.get('report', {}).get('email_config', {})
        self.smtp_server = self.email_config.get('smtp_server', '')
        self.smtp_port = self.email_config.get('smtp_port', 587)
        self.username = self.email_config.get('username', '')
        self.password = self.email_config.get('password', '')
        self.use_tls = self.email_config.get('use_tls', True)
        self.use_ssl = self.email_config.get('use_ssl', False)
        self.sender = self.email_config.get('sender', '')
        self.sender_name = self.email_config.get('sender_name', '自动化测试系统')
        self.default_receivers = self.email_config.get('receivers', [])
        self.default_cc = self.email_config.get('cc', [])
        self.default_bcc = self.email_config.get('bcc', [])

        # 验证配置
        if not self.smtp_server or not self.sender:
            self.logger.warning("邮件服务器配置不完整，邮件发送功能可能无法正常工作")

    def send_email(self,
                   subject: str,
                   content: str,
                   receivers: Optional[List[str]] = None,
                   cc: Optional[List[str]] = None,
                   bcc: Optional[List[str]] = None,
                   attachments: Optional[List[str]] = None,
                   html_content: Optional[str] = None,
                   content_type: str = "plain") -> bool:
        """
        发送邮件

        Args:
            subject: 邮件主题
            content: 邮件内容（纯文本）
            receivers: 收件人列表
            cc: 抄送列表
            bcc: 密送列表
            attachments: 附件路径列表
            html_content: HTML内容（如果提供，将替代纯文本内容）
            content_type: 内容类型 plain/html

        Returns:
            bool: 发送是否成功
        """
        # 使用默认收件人
        if receivers is None:
            receivers = self.default_receivers
        if cc is None:
            cc = self.default_cc
        if bcc is None:
            bcc = self.default_bcc

        # 验证收件人
        if not receivers:
            self.logger.error("没有指定收件人")
            return False

        try:
            # 创建邮件消息
            msg = MIMEMultipart()
            msg['From'] = formataddr((str(Header(self.sender_name, 'utf-8')), self.sender))
            msg['To'] = ', '.join(receivers)
            if cc:
                msg['Cc'] = ', '.join(cc)
            if bcc:
                # BCC不在邮件头中显示
                pass

            msg['Subject'] = Header(subject, 'utf-8').encode()
            msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0800')

            # 添加邮件正文
            if html_content:
                # 添加HTML内容
                html_part = MIMEText(html_content, 'html', 'utf-8')
                msg.attach(html_part)
                # 同时添加纯文本版本以便兼容
                text_part = MIMEText(content, 'plain', 'utf-8')
                msg.attach(text_part)
            else:
                # 添加纯文本内容
                if content_type.lower() == 'html':
                    text_part = MIMEText(content, 'html', 'utf-8')
                else:
                    text_part = MIMEText(content, 'plain', 'utf-8')
                msg.attach(text_part)

            # 添加附件
            if attachments:
                for attachment_path in attachments:
                    if os.path.exists(attachment_path):
                        self._add_attachment(msg, attachment_path)
                    else:
                        self.logger.warning(f"附件不存在: {attachment_path}")

            # 发送邮件
            return self._send_smtp(msg, receivers + cc + bcc)

        except Exception as e:
            self.logger.error(f"发送邮件失败: {e}")
            return False

    def send_test_report(self,
                        report_file: str,
                        subject: Optional[str] = None,
                        receivers: Optional[List[str]] = None,
                        cc: Optional[List[str]] = None,
                        bcc: Optional[List[str]] = None,
                        include_summary: bool = True) -> bool:
        """
        发送测试报告邮件

        Args:
            report_file: 测试报告文件路径
            subject: 邮件主题（默认自动生成）
            receivers: 收件人列表
            cc: 抄送列表
            bcc: 密送列表
            include_summary: 是否在邮件正文中包含报告摘要

        Returns:
            bool: 发送是否成功
        """
        if not os.path.exists(report_file):
            self.logger.error(f"测试报告文件不存在: {report_file}")
            return False

        # 生成邮件主题
        if subject is None:
            report_name = os.path.basename(report_file)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            subject = f"测试报告 - {report_name} - {timestamp}"

        # 生成邮件内容
        content = self._generate_report_email_content(report_file, include_summary)

        # 发送邮件
        return self.send_email(
            subject=subject,
            content=content,
            receivers=receivers,
            cc=cc,
            bcc=bcc,
            attachments=[report_file],
            content_type="html"
        )

    def _add_attachment(self, msg: MIMEMultipart, file_path: str) -> None:
        """
        添加附件到邮件

        Args:
            msg: 邮件消息对象
            file_path: 文件路径
        """
        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()

            filename = os.path.basename(file_path)
            attachment = MIMEApplication(file_data, Name=filename)
            attachment['Content-Disposition'] = f'attachment; filename="{filename}"'

            msg.attach(attachment)
            self.logger.info(f"添加附件: {filename}")

        except Exception as e:
            self.logger.error(f"添加附件失败 {file_path}: {e}")

    def _send_smtp(self, msg: MIMEMultipart, recipients: List[str]) -> bool:
        """
        通过SMTP发送邮件

        Args:
            msg: 邮件消息对象
            recipients: 收件人列表

        Returns:
            bool: 发送是否成功
        """
        try:
            # 连接到SMTP服务器
            if self.use_ssl:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                if self.use_tls:
                    server.starttls()

            # 登录
            if self.username and self.password:
                server.login(self.username, self.password)

            # 发送邮件
            server.send_message(msg, from_addr=self.sender, to_addrs=recipients)

            # 断开连接
            server.quit()

            self.logger.info(f"邮件发送成功，收件人: {', '.join(recipients)}")
            return True

        except Exception as e:
            self.logger.error(f"SMTP发送失败: {e}")
            return False

    def _generate_report_email_content(self, report_file: str, include_summary: bool = True) -> str:
        """
        生成报告邮件内容

        Args:
            report_file: 报告文件路径
            include_summary: 是否包含摘要

        Returns:
            str: HTML邮件内容
        """
        # 基本的邮件模板
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 800px; margin: 0 auto; padding: 20px; }
                .header { background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
                .header h1 { color: #007bff; margin: 0; }
                .info { background-color: #e9ecef; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
                .summary { background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
                .summary h2 { color: #28a745; margin-top: 0; }
                .summary-item { margin-bottom: 10px; }
                .label { font-weight: bold; display: inline-block; width: 150px; }
                .attachment { background-color: #e9ecef; padding: 15px; border-radius: 5px; }
                .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; color: #6c757d; font-size: 0.9em; }
                .success { color: #28a745; }
                .warning { color: #ffc107; }
                .danger { color: #dc3545; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 自动化测试报告</h1>
                    <p>电商后台管理系统自动化测试报告已生成</p>
                </div>
        """

        # 添加报告信息
        html_content += f"""
                <div class="info">
                    <h2>报告信息</h2>
                    <div class="summary-item">
                        <span class="label">报告文件:</span>
                        <span>{os.path.basename(report_file)}</span>
                    </div>
                    <div class="summary-item">
                        <span class="label">生成时间:</span>
                        <span>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
                    </div>
                    <div class="summary-item">
                        <span class="label">文件大小:</span>
                        <span>{self._format_file_size(os.path.getsize(report_file))}</span>
                    </div>
                </div>
        """

        # 如果包含摘要，这里可以添加更多信息
        # 注意：在实际使用中，应该从报告文件中提取摘要信息
        if include_summary:
            html_content += """
                <div class="summary">
                    <h2>📋 报告摘要</h2>
                    <div class="summary-item">
                        <span class="label">报告类型:</span>
                        <span>自动化测试执行报告</span>
                    </div>
                    <div class="summary-item">
                        <span class="label">包含内容:</span>
                        <span>测试结果、错误详情、执行统计、截图等</span>
                    </div>
                    <p>详细测试结果请查看附件中的HTML报告文件。</p>
                </div>
            """

        # 添加附件信息
        html_content += f"""
                <div class="attachment">
                    <h2>📎 附件信息</h2>
                    <p>测试报告文件已作为附件发送，请下载查看详细信息。</p>
                    <ul>
                        <li><strong>{os.path.basename(report_file)}</strong> - 完整HTML测试报告</li>
                    </ul>
                </div>

                <div class="footer">
                    <p>此邮件由电商后台自动化测试系统自动发送</p>
                    <p>如有问题，请联系系统管理员</p>
                    <p>发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
            </div>
        </body>
        </html>
        """

        return html_content

    def _format_file_size(self, size_in_bytes: int) -> str:
        """
        格式化文件大小

        Args:
            size_in_bytes: 文件大小（字节）

        Returns:
            str: 格式化后的文件大小
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_in_bytes < 1024.0:
                return f"{size_in_bytes:.1f} {unit}"
            size_in_bytes /= 1024.0
        return f"{size_in_bytes:.1f} TB"

    def test_connection(self) -> bool:
        """
        测试SMTP连接

        Returns:
            bool: 连接是否成功
        """
        try:
            if self.use_ssl:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                if self.use_tls:
                    server.starttls()

            if self.username and self.password:
                server.login(self.username, self.password)

            server.quit()
            self.logger.info("SMTP连接测试成功")
            return True

        except Exception as e:
            self.logger.error(f"SMTP连接测试失败: {e}")
            return False


# 快捷函数
def send_test_report(report_file: str,
                     subject: Optional[str] = None,
                     receivers: Optional[List[str]] = None) -> bool:
    """
    快捷函数：发送测试报告邮件

    Args:
        report_file: 测试报告文件路径
        subject: 邮件主题
        receivers: 收件人列表

    Returns:
        bool: 发送是否成功
    """
    sender = EmailSender()
    return sender.send_test_report(report_file, subject, receivers)


if __name__ == "__main__":
    # 测试邮件发送功能
    print("测试邮件发送功能...")

    # 创建配置
    test_config = {
        'report': {
            'email_config': {
                'smtp_server': 'smtp.example.com',
                'smtp_port': 587,
                'username': 'test@example.com',
                'password': 'password',
                'use_tls': True,
                'use_ssl': False,
                'sender': 'test@example.com',
                'receivers': ['admin@example.com']
            }
        }
    }

    # 创建邮件发送器
    email_sender = EmailSender(test_config)

    # 测试连接
    print("测试SMTP连接...")
    if email_sender.test_connection():
        print("✓ SMTP连接测试成功")
    else:
        print("✗ SMTP连接测试失败（这可能是预期的，因为使用了测试配置）")

    # 创建测试报告文件
    test_report = "test_report.html"
    with open(test_report, 'w', encoding='utf-8') as f:
        f.write("<html><body><h1>测试报告</h1><p>这是一个测试报告</p></body></html>")

    print(f"创建测试报告文件: {test_report}")

    # 发送测试邮件（在实际环境中需要真实的SMTP配置）
    print("注意：要实际发送邮件，请更新配置文件中的真实SMTP信息")

    print("邮件发送工具测试完成")