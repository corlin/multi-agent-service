"""Patent report exporter implementation."""

import asyncio
import logging
import os
import hashlib
import shutil
import zipfile
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path
import json
import base64
import uuid


logger = logging.getLogger(__name__)


class ReportExporter:
    """专利报告导出器，支持HTML和PDF导出、文件存储和版本管理."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化报告导出器."""
        self.config = config or {}
        
        # 导出配置
        self.export_config = {
            "output_dir": self.config.get("output_dir", "reports/patent"),
            "supported_formats": ["html", "pdf", "json", "zip"],
            "pdf_engine": self.config.get("pdf_engine", "weasyprint"),
            "file_naming": self.config.get("file_naming", "timestamp"),
            "compression": self.config.get("compression", True),
            "version_control": self.config.get("version_control", True),
            "max_versions": self.config.get("max_versions", 5),
            "auto_cleanup_days": self.config.get("auto_cleanup_days", 30)
        }
        
        # 目录结构
        self.base_dir = Path(self.export_config["output_dir"])
        self.reports_dir = self.base_dir / "reports"
        self.versions_dir = self.base_dir / "versions"
        self.temp_dir = self.base_dir / "temp"
        
        # 初始化日志
        self.logger = logging.getLogger(f"{__name__}.ReportExporter")
        
        # 确保目录存在
        self._ensure_directories()
        
        # 版本管理
        self.version_manager = ReportVersionManager(self.versions_dir, self.export_config)
        
        # 文件存储管理
        self.storage_manager = ReportStorageManager(self.reports_dir, self.export_config)
    
    def _ensure_directories(self):
        """确保所有必要的目录存在."""
        directories = [self.base_dir, self.reports_dir, self.versions_dir, self.temp_dir]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Ensured report directories: {[str(d) for d in directories]}")
    
    async def export_report(self, content: str, format: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """导出报告到指定格式."""
        try:
            # 生成报告ID和版本信息
            report_id = self._generate_report_id(params)
            version_info = await self.version_manager.create_version(report_id, params)
            
            # 生成文件名
            filename = self._generate_filename(format, params, version_info)
            
            # 根据格式导出
            if format.lower() == "html":
                export_result = await self._export_html(content, filename, params, version_info)
            elif format.lower() == "json":
                export_result = await self._export_json(content, filename, params, version_info)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            # 保存到存储管理器
            await self.storage_manager.store_report(export_result, version_info)
            
            # 更新版本信息
            await self.version_manager.update_version_status(version_info["version_id"], "completed", export_result)
            
            return export_result
                
        except Exception as e:
            self.logger.error(f"Error exporting report to {format}: {str(e)}")
            raise
    
    def _generate_report_id(self, params: Dict[str, Any]) -> str:
        """生成报告ID."""
        try:
            param_str = json.dumps(params, sort_keys=True)
            report_hash = hashlib.md5(param_str.encode()).hexdigest()[:8]
            timestamp = datetime.now().strftime("%Y%m%d")
            return f"report_{timestamp}_{report_hash}"
        except Exception as e:
            self.logger.error(f"Error generating report ID: {str(e)}")
            return f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def _generate_filename(self, format: str, params: Dict[str, Any], version_info: Dict[str, Any]) -> str:
        """生成文件名."""
        try:
            version_suffix = f"_v{version_info['version_number']}"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return f"patent_report_{timestamp}{version_suffix}.{format}"
        except Exception as e:
            self.logger.error(f"Error generating filename: {str(e)}")
            return f"patent_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
    
    async def _export_html(self, content: str, filename: str, params: Dict[str, Any], version_info: Dict[str, Any]) -> Dict[str, Any]:
        """导出HTML格式报告."""
        try:
            file_path = self.reports_dir / filename
            
            # 写入HTML文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 获取文件信息
            file_size = file_path.stat().st_size
            
            return {
                "html": {
                    "path": str(file_path),
                    "filename": filename,
                    "size": self._format_file_size(file_size),
                    "size_bytes": file_size,
                    "created_at": datetime.now().isoformat(),
                    "format": "html",
                    "version_info": version_info
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error exporting HTML: {str(e)}")
            raise
    
    async def _export_json(self, content: str, filename: str, params: Dict[str, Any], version_info: Dict[str, Any]) -> Dict[str, Any]:
        """导出JSON格式报告."""
        try:
            file_path = self.reports_dir / filename
            
            # 创建JSON报告数据
            json_data = {
                "report_metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "format": "json",
                    "parameters": params,
                    "version_info": version_info
                },
                "content": {
                    "html_content": content,
                    "content_length": len(content)
                }
            }
            
            # 写入JSON文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            # 获取文件信息
            file_size = file_path.stat().st_size
            
            return {
                "json": {
                    "path": str(file_path),
                    "filename": filename,
                    "size": self._format_file_size(file_size),
                    "size_bytes": file_size,
                    "created_at": datetime.now().isoformat(),
                    "format": "json",
                    "version_info": version_info
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error exporting JSON: {str(e)}")
            raise
    
    def _format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小."""
        try:
            if size_bytes < 1024:
                return f"{size_bytes}B"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.1f}KB"
            else:
                return f"{size_bytes / (1024 * 1024):.1f}MB"
        except Exception:
            return f"{size_bytes}B"
    
    async def get_export_info(self) -> Dict[str, Any]:
        """获取导出器信息."""
        return {
            "supported_formats": self.export_config["supported_formats"],
            "output_directory": str(self.reports_dir),
            "version_control_enabled": self.export_config["version_control"]
        }


class ReportVersionManager:
    """报告版本管理器."""
    
    def __init__(self, versions_dir: Path, config: Dict[str, Any]):
        """初始化版本管理器."""
        self.versions_dir = versions_dir
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.ReportVersionManager")
        
        # 版本数据存储
        self.versions_file = self.versions_dir / "versions.json"
        self.versions_data = self._load_versions_data()
    
    def _load_versions_data(self) -> Dict[str, Any]:
        """加载版本数据."""
        try:
            if self.versions_file.exists():
                with open(self.versions_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {"reports": {}, "versions": {}}
        except Exception as e:
            self.logger.error(f"Error loading versions data: {str(e)}")
            return {"reports": {}, "versions": {}}
    
    def _save_versions_data(self):
        """保存版本数据."""
        try:
            with open(self.versions_file, 'w', encoding='utf-8') as f:
                json.dump(self.versions_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving versions data: {str(e)}")
    
    async def create_version(self, report_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """创建新版本."""
        try:
            # 获取或创建报告记录
            if report_id not in self.versions_data["reports"]:
                self.versions_data["reports"][report_id] = {
                    "report_id": report_id,
                    "created_at": datetime.now().isoformat(),
                    "versions": [],
                    "latest_version": 0
                }
            
            report_record = self.versions_data["reports"][report_id]
            
            # 创建新版本
            version_number = report_record["latest_version"] + 1
            version_id = f"{report_id}_v{version_number}"
            
            version_info = {
                "version_id": version_id,
                "report_id": report_id,
                "version_number": version_number,
                "created_at": datetime.now().isoformat(),
                "parameters": params,
                "status": "creating"
            }
            
            # 更新记录
            report_record["versions"].append(version_id)
            report_record["latest_version"] = version_number
            
            self.versions_data["versions"][version_id] = version_info
            
            # 保存数据
            self._save_versions_data()
            
            return version_info
            
        except Exception as e:
            self.logger.error(f"Error creating version: {str(e)}")
            raise
    
    async def update_version_status(self, version_id: str, status: str, metadata: Dict[str, Any]):
        """更新版本状态."""
        try:
            if version_id in self.versions_data["versions"]:
                version_info = self.versions_data["versions"][version_id]
                version_info["status"] = status
                version_info["updated_at"] = datetime.now().isoformat()
                
                self._save_versions_data()
                
        except Exception as e:
            self.logger.error(f"Error updating version status: {str(e)}")
    
    async def get_version_by_filename(self, filename: str) -> Optional[Dict[str, Any]]:
        """根据文件名获取版本信息."""
        try:
            # 简单实现，返回None
            return None
        except Exception as e:
            self.logger.error(f"Error getting version by filename: {str(e)}")
            return None


class ReportStorageManager:
    """报告存储管理器."""
    
    def __init__(self, storage_dir: Path, config: Dict[str, Any]):
        """初始化存储管理器."""
        self.storage_dir = storage_dir
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.ReportStorageManager")
        
        # 存储索引
        self.index_file = self.storage_dir / "storage_index.json"
        self.storage_index = self._load_storage_index()
    
    def _load_storage_index(self) -> Dict[str, Any]:
        """加载存储索引."""
        try:
            if self.index_file.exists():
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 确保必要的键存在
                    if "files" not in data:
                        data["files"] = {}
                    if "stats" not in data:
                        data["stats"] = {"total_files": 0, "total_size": 0}
                    return data
            else:
                return {"files": {}, "stats": {"total_files": 0, "total_size": 0}}
        except Exception as e:
            self.logger.error(f"Error loading storage index: {str(e)}")
            return {"files": {}, "stats": {"total_files": 0, "total_size": 0}}
    
    def _save_storage_index(self):
        """保存存储索引."""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.storage_index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving storage index: {str(e)}")
    
    async def store_report(self, export_result: Dict[str, Any], version_info: Dict[str, Any]):
        """存储报告到索引."""
        try:
            for format_type, file_info in export_result.items():
                if isinstance(file_info, dict) and "filename" in file_info:
                    filename = file_info["filename"]
                    
                    # 添加到索引
                    self.storage_index["files"][filename] = {
                        "filename": filename,
                        "format": format_type,
                        "path": file_info.get("path", ""),
                        "size_bytes": file_info.get("size_bytes", 0),
                        "created_at": file_info.get("created_at", datetime.now().isoformat()),
                        "version_info": version_info
                    }
                    
                    # 更新统计
                    if "stats" not in self.storage_index:
                        self.storage_index["stats"] = {"total_files": 0, "total_size": 0}
                    self.storage_index["stats"]["total_files"] += 1
                    self.storage_index["stats"]["total_size"] += file_info.get("size_bytes", 0)
            
            # 保存索引
            self._save_storage_index()
            
        except Exception as e:
            self.logger.error(f"Error storing report: {str(e)}")
    
    async def remove_report(self, filename: str):
        """从索引中移除报告."""
        try:
            if filename in self.storage_index["files"]:
                file_info = self.storage_index["files"][filename]
                
                # 更新统计
                if "stats" not in self.storage_index:
                    self.storage_index["stats"] = {"total_files": 0, "total_size": 0}
                self.storage_index["stats"]["total_files"] -= 1
                self.storage_index["stats"]["total_size"] -= file_info.get("size_bytes", 0)
                
                # 移除文件记录
                del self.storage_index["files"][filename]
                
                # 保存索引
                self._save_storage_index()
                
        except Exception as e:
            self.logger.error(f"Error removing report from index: {str(e)}")
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """获取存储统计信息."""
        try:
            # 确保storage_index有stats键
            if "stats" not in self.storage_index:
                self.storage_index["stats"] = {"total_files": 0, "total_size": 0}
            
            stats = self.storage_index["stats"].copy()
            
            # 计算格式分布
            format_distribution = {}
            files = self.storage_index.get("files", {})
            for file_info in files.values():
                format_type = file_info.get("format", "unknown")
                format_distribution[format_type] = format_distribution.get(format_type, 0) + 1
            
            stats["format_distribution"] = format_distribution
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting storage stats: {str(e)}")
            return {"total_files": 0, "total_size": 0, "format_distribution": {}}