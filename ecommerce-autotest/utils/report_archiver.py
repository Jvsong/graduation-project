#!/usr/bin/env python3
"""
历史报告管理系统
管理测试报告的归档、查询和清理
"""

import os
import sys
import shutil
import json
import sqlite3
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum

from utils.logger import get_logger
from utils.config_manager import get_config


class ArchiveStatus(Enum):
    """归档状态枚举"""
    ARCHIVED = "archived"
    DELETED = "deleted"
    EXPIRED = "expired"
    ACTIVE = "active"


class ReportMetadata:
    """
    报告元数据
    存储报告的元信息
    """

    def __init__(self,
                 report_id: str,
                 report_path: str,
                 project_name: str,
                 project_version: str):
        """
        初始化报告元数据

        Args:
            report_id: 报告ID
            report_path: 报告文件路径
            project_name: 项目名称
            project_version: 项目版本
        """
        self.report_id = report_id
        self.report_path = report_path
        self.project_name = project_name
        self.project_version = project_version

        # 基本信息
        self.filename = os.path.basename(report_path)
        self.file_size = 0
        self.checksum = ""
        self.creation_time = datetime.now()
        self.modification_time = datetime.now()

        # 执行信息
        self.execution_time: Optional[datetime] = None
        self.duration: float = 0.0
        self.environment: str = "test"
        self.browser: str = "chrome"

        # 测试结果
        self.total_tests: int = 0
        self.passed_tests: int = 0
        self.failed_tests: int = 0
        self.error_tests: int = 0
        self.pass_rate: float = 0.0

        # 归档信息
        self.archive_time: Optional[datetime] = None
        self.archive_path: Optional[str] = None
        self.status: ArchiveStatus = ArchiveStatus.ACTIVE
        self.tags: List[str] = []
        self.notes: str = ""

        # 自定义字段
        self.custom_fields: Dict[str, Any] = {}

        # 计算文件信息
        self._calculate_file_info()

    def _calculate_file_info(self) -> None:
        """计算文件信息"""
        try:
            if os.path.exists(self.report_path):
                stat = os.stat(self.report_path)
                self.file_size = stat.st_size
                self.modification_time = datetime.fromtimestamp(stat.st_mtime)

                # 计算校验和
                with open(self.report_path, 'rb') as f:
                    file_content = f.read()
                    self.checksum = hashlib.md5(file_content).hexdigest()

        except Exception as e:
            print(f"计算文件信息失败: {e}")

    def update_from_report_data(self, report_data: Dict[str, Any]) -> None:
        """
        从报告数据更新元数据

        Args:
            report_data: 报告数据字典
        """
        # 更新执行信息
        execution_info = report_data.get('execution_info', {}) or report_data.get('execution', {})
        if execution_info.get('start_time'):
            try:
                self.execution_time = datetime.fromisoformat(execution_info['start_time'])
            except (ValueError, TypeError):
                pass

        self.duration = execution_info.get('duration', 0.0)
        self.environment = execution_info.get('environment', 'test')
        self.browser = execution_info.get('browser', 'chrome')

        # 更新测试结果
        stats = report_data.get('global_stats', {}) or report_data.get('stats', {})
        self.total_tests = stats.get('total_tests', 0)
        self.passed_tests = stats.get('passed_tests', 0)
        self.failed_tests = stats.get('failed_tests', 0)
        self.error_tests = stats.get('error_tests', 0)
        self.pass_rate = stats.get('pass_rate', 0.0)

    def archive(self, archive_dir: str) -> bool:
        """
        归档报告

        Args:
            archive_dir: 归档目录

        Returns:
            bool: 归档是否成功
        """
        try:
            archive_time = datetime.now()
            archive_subdir = os.path.join(
                archive_dir,
                archive_time.strftime("%Y"),
                archive_time.strftime("%m"),
                archive_time.strftime("%d")
            )
            os.makedirs(archive_subdir, exist_ok=True)

            # 生成归档文件名（包含时间戳和报告ID）
            timestamp = archive_time.strftime("%Y%m%d_%H%M%S")
            archive_filename = f"{timestamp}_{self.report_id}_{self.filename}"
            self.archive_path = os.path.join(archive_subdir, archive_filename)

            # 复制文件到归档目录
            shutil.copy2(self.report_path, self.archive_path)

            # 更新归档信息
            self.archive_time = archive_time
            self.status = ArchiveStatus.ARCHIVED

            return True

        except Exception as e:
            print(f"归档报告失败: {e}")
            return False

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典

        Returns:
            Dict[str, Any]: 字典表示
        """
        return {
            "report_id": self.report_id,
            "report_path": self.report_path,
            "archive_path": self.archive_path,
            "project_name": self.project_name,
            "project_version": self.project_version,
            "filename": self.filename,
            "file_size": self.file_size,
            "checksum": self.checksum,
            "creation_time": self.creation_time.isoformat() if self.creation_time else None,
            "modification_time": self.modification_time.isoformat() if self.modification_time else None,
            "execution_time": self.execution_time.isoformat() if self.execution_time else None,
            "duration": self.duration,
            "environment": self.environment,
            "browser": self.browser,
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "error_tests": self.error_tests,
            "pass_rate": self.pass_rate,
            "archive_time": self.archive_time.isoformat() if self.archive_time else None,
            "status": self.status.value,
            "tags": self.tags,
            "notes": self.notes,
            "custom_fields": self.custom_fields
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReportMetadata':
        """
        从字典创建实例

        Args:
            data: 字典数据

        Returns:
            ReportMetadata: 报告元数据实例
        """
        metadata = cls(
            report_id=data["report_id"],
            report_path=data["report_path"],
            project_name=data.get("project_name", ""),
            project_version=data.get("project_version", "")
        )

        # 恢复基本属性
        metadata.filename = data.get("filename", "")
        metadata.file_size = data.get("file_size", 0)
        metadata.checksum = data.get("checksum", "")

        if data.get("creation_time"):
            metadata.creation_time = datetime.fromisoformat(data["creation_time"])
        if data.get("modification_time"):
            metadata.modification_time = datetime.fromisoformat(data["modification_time"])
        if data.get("execution_time"):
            metadata.execution_time = datetime.fromisoformat(data["execution_time"])

        metadata.duration = data.get("duration", 0.0)
        metadata.environment = data.get("environment", "test")
        metadata.browser = data.get("browser", "chrome")

        metadata.total_tests = data.get("total_tests", 0)
        metadata.passed_tests = data.get("passed_tests", 0)
        metadata.failed_tests = data.get("failed_tests", 0)
        metadata.error_tests = data.get("error_tests", 0)
        metadata.pass_rate = data.get("pass_rate", 0.0)

        if data.get("archive_time"):
            metadata.archive_time = datetime.fromisoformat(data["archive_time"])
        metadata.archive_path = data.get("archive_path")
        metadata.status = ArchiveStatus(data.get("status", "active"))
        metadata.tags = data.get("tags", [])
        metadata.notes = data.get("notes", "")
        metadata.custom_fields = data.get("custom_fields", {})

        return metadata

    def __str__(self) -> str:
        """字符串表示"""
        return f"ReportMetadata({self.report_id}: {self.filename}, 通过率: {self.pass_rate:.1f}%)"


class ReportArchiver:
    """
    报告归档管理器
    管理历史报告的存储和查询
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化报告归档管理器

        Args:
            config: 配置字典
        """
        self.logger = get_logger(self.__class__.__name__)

        # 获取配置
        if config is None:
            self.config = get_config()
        else:
            self.config = config

        # 归档配置
        report_config = self.config.get('report', {})
        self.output_dir = report_config.get('output_dir', './reports')
        self.archive_dir = os.path.join(self.output_dir, 'history')
        self.database_file = os.path.join(self.archive_dir, 'reports.db')
        self.retention_days = report_config.get('retention_days', 30)  # 默认保留30天

        # 创建归档目录
        os.makedirs(self.archive_dir, exist_ok=True)

        # 初始化数据库
        self._init_database()

    def _init_database(self) -> None:
        """初始化数据库"""
        try:
            conn = sqlite3.connect(self.database_file)
            cursor = conn.cursor()

            # 创建报告元数据表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reports (
                    report_id TEXT PRIMARY KEY,
                    report_path TEXT,
                    archive_path TEXT,
                    project_name TEXT,
                    project_version TEXT,
                    filename TEXT,
                    file_size INTEGER,
                    checksum TEXT,
                    creation_time TIMESTAMP,
                    modification_time TIMESTAMP,
                    execution_time TIMESTAMP,
                    duration REAL,
                    environment TEXT,
                    browser TEXT,
                    total_tests INTEGER,
                    passed_tests INTEGER,
                    failed_tests INTEGER,
                    error_tests INTEGER,
                    pass_rate REAL,
                    archive_time TIMESTAMP,
                    status TEXT,
                    tags TEXT,
                    notes TEXT,
                    custom_fields TEXT
                )
            ''')

            # 创建索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_creation_time ON reports(creation_time)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_project ON reports(project_name, project_version)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_status ON reports(status)
            ''')

            conn.commit()
            conn.close()

            self.logger.info(f"数据库初始化完成: {self.database_file}")

        except Exception as e:
            self.logger.error(f"数据库初始化失败: {e}")

    def archive_report(self,
                      report_file: str,
                      report_data: Optional[Dict[str, Any]] = None,
                      tags: Optional[List[str]] = None,
                      notes: str = "") -> Optional[str]:
        """
        归档报告文件

        Args:
            report_file: 报告文件路径
            report_data: 报告数据（可选）
            tags: 标签列表
            notes: 备注

        Returns:
            Optional[str]: 归档ID，如果失败则返回None
        """
        try:
            # 验证报告文件
            if not os.path.exists(report_file):
                self.logger.error(f"报告文件不存在: {report_file}")
                return None

            # 生成报告ID（基于文件内容和时间戳）
            file_hash = self._calculate_file_hash(report_file)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            report_id = f"{timestamp}_{file_hash[:8]}"

            # 创建报告元数据
            metadata = ReportMetadata(
                report_id=report_id,
                report_path=report_file,
                project_name=self.config.get('project', {}).get('name', 'Unknown'),
                project_version=self.config.get('project', {}).get('version', '1.0.0')
            )

            # 更新标签和备注
            if tags:
                metadata.tags = tags
            metadata.notes = notes

            # 从报告数据更新元数据
            if report_data:
                metadata.update_from_report_data(report_data)

            # 归档报告
            if metadata.archive(self.archive_dir):
                # 保存到数据库
                self._save_to_database(metadata)

                self.logger.info(f"报告归档成功: {report_id}")
                return report_id
            else:
                self.logger.error("报告归档失败")
                return None

        except Exception as e:
            self.logger.error(f"归档报告失败: {e}")
            return None

    def _calculate_file_hash(self, file_path: str) -> str:
        """
        计算文件哈希

        Args:
            file_path: 文件路径

        Returns:
            str: 文件哈希值
        """
        try:
            with open(file_path, 'rb') as f:
                file_content = f.read()
                return hashlib.md5(file_content).hexdigest()
        except Exception as e:
            self.logger.error(f"计算文件哈希失败: {e}")
            return ""

    def _save_to_database(self, metadata: ReportMetadata) -> bool:
        """
        保存元数据到数据库

        Args:
            metadata: 报告元数据

        Returns:
            bool: 保存是否成功
        """
        try:
            conn = sqlite3.connect(self.database_file)
            cursor = conn.cursor()

            # 准备数据
            data = metadata.to_dict()
            tags_json = json.dumps(data["tags"], ensure_ascii=False)
            custom_fields_json = json.dumps(data["custom_fields"], ensure_ascii=False)

            # 插入或更新记录
            cursor.execute('''
                INSERT OR REPLACE INTO reports VALUES (
                    :report_id, :report_path, :archive_path, :project_name, :project_version,
                    :filename, :file_size, :checksum, :creation_time, :modification_time,
                    :execution_time, :duration, :environment, :browser, :total_tests,
                    :passed_tests, :failed_tests, :error_tests, :pass_rate, :archive_time,
                    :status, :tags, :notes, :custom_fields
                )
            ''', {
                'report_id': data["report_id"],
                'report_path': data["report_path"],
                'archive_path': data["archive_path"],
                'project_name': data["project_name"],
                'project_version': data["project_version"],
                'filename': data["filename"],
                'file_size': data["file_size"],
                'checksum': data["checksum"],
                'creation_time': data["creation_time"],
                'modification_time': data["modification_time"],
                'execution_time': data["execution_time"],
                'duration': data["duration"],
                'environment': data["environment"],
                'browser': data["browser"],
                'total_tests': data["total_tests"],
                'passed_tests': data["passed_tests"],
                'failed_tests': data["failed_tests"],
                'error_tests': data["error_tests"],
                'pass_rate': data["pass_rate"],
                'archive_time': data["archive_time"],
                'status': data["status"],
                'tags': tags_json,
                'notes': data["notes"],
                'custom_fields': custom_fields_json
            })

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            self.logger.error(f"保存到数据库失败: {e}")
            return False

    def list_reports(self,
                     start_date: Optional[datetime] = None,
                     end_date: Optional[datetime] = None,
                     project_name: Optional[str] = None,
                     status: Optional[ArchiveStatus] = None,
                     tags: Optional[List[str]] = None,
                     limit: int = 100,
                     offset: int = 0) -> List[ReportMetadata]:
        """
        列出报告

        Args:
            start_date: 开始日期
            end_date: 结束日期
            project_name: 项目名称
            status: 归档状态
            tags: 标签列表
            limit: 限制数量
            offset: 偏移量

        Returns:
            List[ReportMetadata]: 报告元数据列表
        """
        try:
            conn = sqlite3.connect(self.database_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 构建查询
            query = "SELECT * FROM reports WHERE 1=1"
            params = []

            if start_date:
                query += " AND creation_time >= ?"
                params.append(start_date.isoformat())

            if end_date:
                query += " AND creation_time <= ?"
                params.append(end_date.isoformat())

            if project_name:
                query += " AND project_name = ?"
                params.append(project_name)

            if status:
                query += " AND status = ?"
                params.append(status.value)

            # 排序和限制
            query += " ORDER BY creation_time DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            # 执行查询
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            # 转换为ReportMetadata对象
            reports = []
            for row in rows:
                data = dict(row)
                # 解析JSON字段
                if data.get('tags'):
                    data['tags'] = json.loads(data['tags'])
                if data.get('custom_fields'):
                    data['custom_fields'] = json.loads(data['custom_fields'])

                reports.append(ReportMetadata.from_dict(data))

            return reports

        except Exception as e:
            self.logger.error(f"查询报告失败: {e}")
            return []

    def get_report(self, report_id: str) -> Optional[ReportMetadata]:
        """
        获取单个报告

        Args:
            report_id: 报告ID

        Returns:
            Optional[ReportMetadata]: 报告元数据，如果不存在则返回None
        """
        try:
            conn = sqlite3.connect(self.database_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM reports WHERE report_id = ?", (report_id,))
            row = cursor.fetchone()
            conn.close()

            if row:
                data = dict(row)
                # 解析JSON字段
                if data.get('tags'):
                    data['tags'] = json.loads(data['tags'])
                if data.get('custom_fields'):
                    data['custom_fields'] = json.loads(data['custom_fields'])

                return ReportMetadata.from_dict(data)

            return None

        except Exception as e:
            self.logger.error(f"获取报告失败: {e}")
            return None

    def delete_report(self, report_id: str) -> bool:
        """
        删除报告

        Args:
            report_id: 报告ID

        Returns:
            bool: 删除是否成功
        """
        try:
            # 获取报告信息
            metadata = self.get_report(report_id)
            if not metadata:
                self.logger.error(f"报告不存在: {report_id}")
                return False

            # 删除归档文件
            if metadata.archive_path and os.path.exists(metadata.archive_path):
                os.remove(metadata.archive_path)
                self.logger.info(f"删除归档文件: {metadata.archive_path}")

            # 更新数据库状态
            conn = sqlite3.connect(self.database_file)
            cursor = conn.cursor()

            cursor.execute(
                "UPDATE reports SET status = ? WHERE report_id = ?",
                (ArchiveStatus.DELETED.value, report_id)
            )

            conn.commit()
            conn.close()

            self.logger.info(f"标记报告为已删除: {report_id}")
            return True

        except Exception as e:
            self.logger.error(f"删除报告失败: {e}")
            return False

    def cleanup_expired_reports(self) -> int:
        """
        清理过期报告

        Returns:
            int: 清理的报告数量
        """
        try:
            # 计算过期时间
            expire_date = datetime.now() - timedelta(days=self.retention_days)

            # 获取过期报告
            conn = sqlite3.connect(self.database_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM reports WHERE creation_time < ? AND status != ?",
                (expire_date.isoformat(), ArchiveStatus.DELETED.value)
            )
            rows = cursor.fetchall()

            # 删除过期报告
            deleted_count = 0
            for row in rows:
                data = dict(row)
                report_id = data['report_id']
                archive_path = data['archive_path']

                # 删除归档文件
                if archive_path and os.path.exists(archive_path):
                    os.remove(archive_path)

                # 更新数据库状态
                cursor.execute(
                    "UPDATE reports SET status = ? WHERE report_id = ?",
                    (ArchiveStatus.EXPIRED.value, report_id)
                )

                deleted_count += 1

            conn.commit()
            conn.close()

            self.logger.info(f"清理过期报告完成: {deleted_count} 个")
            return deleted_count

        except Exception as e:
            self.logger.error(f"清理过期报告失败: {e}")
            return 0

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取归档统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            conn = sqlite3.connect(self.database_file)
            cursor = conn.cursor()

            # 总报告数
            cursor.execute("SELECT COUNT(*) FROM reports")
            total_reports = cursor.fetchone()[0]

            # 按状态统计
            cursor.execute("SELECT status, COUNT(*) FROM reports GROUP BY status")
            status_stats = {row[0]: row[1] for row in cursor.fetchall()}

            # 按项目统计
            cursor.execute("SELECT project_name, COUNT(*) FROM reports GROUP BY project_name")
            project_stats = {row[0]: row[1] for row in cursor.fetchall()}

            # 总文件大小
            cursor.execute("SELECT SUM(file_size) FROM reports")
            total_size = cursor.fetchone()[0] or 0

            # 最近7天报告数
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            cursor.execute("SELECT COUNT(*) FROM reports WHERE creation_time >= ?", (week_ago,))
            recent_reports = cursor.fetchone()[0]

            conn.close()

            return {
                'total_reports': total_reports,
                'status_distribution': status_stats,
                'project_distribution': project_stats,
                'total_size': total_size,
                'recent_reports_7d': recent_reports,
                'retention_days': self.retention_days,
                'archive_dir': self.archive_dir,
                'database_file': self.database_file
            }

        except Exception as e:
            self.logger.error(f"获取统计信息失败: {e}")
            return {}


# 快捷函数
def archive_report(report_file: str,
                   report_data: Optional[Dict[str, Any]] = None,
                   tags: Optional[List[str]] = None) -> Optional[str]:
    """
    快捷函数：归档报告

    Args:
        report_file: 报告文件路径
        report_data: 报告数据
        tags: 标签列表

    Returns:
        Optional[str]: 归档ID
    """
    archiver = ReportArchiver()
    return archiver.archive_report(report_file, report_data, tags)


if __name__ == "__main__":
    # 测试报告归档功能
    print("测试报告归档功能...")

    # 创建测试配置
    test_config = {
        'project': {
            'name': '测试项目',
            'version': '1.0.0'
        },
        'report': {
            'output_dir': './reports',
            'retention_days': 7
        }
    }

    # 创建归档管理器
    archiver = ReportArchiver(test_config)

    # 创建测试报告文件
    test_report = "test_report.html"
    with open(test_report, 'w', encoding='utf-8') as f:
        f.write("<html><body><h1>测试报告</h1><p>这是一个测试报告</p></body></html>")

    print(f"创建测试报告文件: {test_report}")

    # 归档报告
    report_data = {
        'execution_info': {
            'start_time': datetime.now().isoformat(),
            'duration': 120.5,
            'environment': 'test',
            'browser': 'chrome'
        },
        'global_stats': {
            'total_tests': 10,
            'passed_tests': 8,
            'failed_tests': 1,
            'error_tests': 1,
            'pass_rate': 80.0
        }
    }

    report_id = archiver.archive_report(
        report_file=test_report,
        report_data=report_data,
        tags=['test', 'automation'],
        notes="这是一个测试报告归档"
    )

    if report_id:
        print(f"报告归档成功，ID: {report_id}")

        # 获取报告
        metadata = archiver.get_report(report_id)
        if metadata:
            print(f"报告信息: {metadata}")
            print(f"文件大小: {metadata.file_size} bytes")
            print(f"通过率: {metadata.pass_rate}%")

        # 列出报告
        reports = archiver.list_reports(limit=5)
        print(f"最近报告: {len(reports)} 个")

        # 获取统计信息
        stats = archiver.get_statistics()
        print(f"归档统计: {stats}")

    # 清理测试文件
    if os.path.exists(test_report):
        os.remove(test_report)

    print("报告归档功能测试完成")
