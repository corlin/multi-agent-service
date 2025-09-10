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
from urllib.parse import quote


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
            "auto_cleanup_days": self.config.get("auto_cleanup_days", 30),
            "pdf_options": {
                "page_size": "A4",
                "margin": "2cm",
                "encoding": "utf-8",
                "optimize_images": True
            }
        }
        
        # 目录结构
        self.base_dir = Path(self.export_config["output_dir"])
        self.reports_dir = self.base_dir / "reports"
        self.versions_dir = self.base_dir / "versions"
        self.temp_dir = self.base_dir / "temp"
        self.assets_dir = self.base_dir / "assets"
        
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
        directories = [
            self.base_dir,
            self.reports_dir,
            self.versions_dir,
            self.temp_dir,
            self.assets_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Ensured report directories: {[str(d) for d in directories]}")
    
    async def export_report(self, content: str, format: str, 
                          params: Dict[str, Any]) -> Dict[str, Any]:
        """导出报告到指定格式，支持版本管理和文件存储."""
        try:
            # 生成报告ID和版本信息
            report_id = self._generate_report_id(params)
            version_info = await self.version_manager.create_version(report_id, params)
            
            # 生成文件名
            filename = self._generate_filename(format, params, version_info)
            
            # 根据格式导出
            export_result = {}
            
            if format.lower() == "html":
                export_result = await self._export_html(content, filename, params, version_info)
            elif format.lower() == "pdf":
                export_result = await self._export_pdf(content, filename, params, version_info)
            elif format.lower() == "json":
                export_result = await self._export_json(content, filename, params, version_info)
            elif format.lower() == "zip":
                export_result = await self._export_zip(content, filename, params, version_info)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            # 保存到存储管理器
            await self.storage_manager.store_report(export_result, version_info)
            
            # 更新版本信息
            await self.version_manager.update_version_status(version_info["version_id"], "completed", export_result)
            
            return export_result
                
        except Exception as e:
            self.logger.error(f"Error exporting report to {format}: {str(e)}")
            # 如果有版本信息，标记为失败
            if 'version_info' in locals():
                await self.version_manager.update_version_status(version_info["version_id"], "failed", {"error": str(e)})
            raise
    
    def _generate_report_id(self, params: Dict[str, Any]) -> str:
        """生成报告ID."""
        try:
            # 基于参数生成唯一ID
            param_str = json.dumps(params, sort_keys=True)
            report_hash = hashlib.md5(param_str.encode()).hexdigest()[:8]
            timestamp = datetime.now().strftime("%Y%m%d")
            return f"report_{timestamp}_{report_hash}"
        except Exception as e:
            self.logger.error(f"Error generating report ID: {str(e)}")
            return f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def _generate_filename(self, format: str, params: Dict[str, Any], version_info: Dict[str, Any]) -> str:
        """生成文件名，包含版本信息."""
        try:
            naming_strategy = self.export_config["file_naming"]
            version_suffix = f"_v{version_info['version_number']}"
            
            if naming_strategy == "timestamp":
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                return f"patent_report_{timestamp}{version_suffix}.{format}"
            
            elif naming_strategy == "keywords":
                keywords = params.get("keywords", ["patent"])
                keyword_str = "_".join(k.replace(" ", "_") for k in keywords[:3])  # 最多3个关键词
                timestamp = datetime.now().strftime("%Y%m%d")
                return f"patent_report_{keyword_str}_{timestamp}{version_suffix}.{format}"
            
            elif naming_strategy == "report_id":
                report_id = version_info.get("report_id", "unknown")
                return f"{report_id}{version_suffix}.{format}"
            
            else:
                # 默认使用时间戳
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                return f"patent_report_{timestamp}{version_suffix}.{format}"
                
        except Exception as e:
            self.logger.error(f"Error generating filename: {str(e)}")
            # 后备文件名
            version_suffix = f"_v{version_info.get('version_number', 1)}"
            return f"patent_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}{version_suffix}.{format}"
    
    async def _export_html(self, content: str, filename: str, 
                         params: Dict[str, Any], version_info: Dict[str, Any]) -> Dict[str, Any]:
        """导出HTML格式报告."""
        try:
            file_path = self.reports_dir / filename
            
            # 增强HTML内容（添加样式和元数据）
            enhanced_content = self._enhance_html_content(content, params, version_info)
            
            # 写入HTML文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(enhanced_content)
            
            # 获取文件信息
            file_size = file_path.stat().st_size
            file_hash = self._calculate_file_hash(file_path)
            
            return {
                "html": {
                    "path": str(file_path),
                    "filename": filename,
                    "size": self._format_file_size(file_size),
                    "size_bytes": file_size,
                    "hash": file_hash,
                    "created_at": datetime.now().isoformat(),
                    "format": "html",
                    "version_info": version_info,
                    "download_url": f"/api/v1/patent/reports/download/{filename}",
                    "view_url": f"/api/v1/patent/reports/view/{filename}"
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error exporting HTML: {str(e)}")
            raise
    
    async def _export_pdf(self, content: str, filename: str, 
                        params: Dict[str, Any], version_info: Dict[str, Any]) -> Dict[str, Any]:
        """导出PDF格式报告，使用weasyprint进行PDF生成."""
        try:
            file_path = self.reports_dir / filename
            
            # 准备PDF内容
            pdf_content = self._prepare_pdf_content(content, params, version_info)
            
            # 生成PDF
            pdf_bytes = await self._generate_pdf_with_weasyprint(pdf_content, params)
            
            # 写入PDF文件
            with open(file_path, 'wb') as f:
                f.write(pdf_bytes)
            
            # 获取文件信息
            file_size = file_path.stat().st_size
            file_hash = self._calculate_file_hash(file_path)
            
            return {
                "pdf": {
                    "path": str(file_path),
                    "filename": filename,
                    "size": self._format_file_size(file_size),
                    "size_bytes": file_size,
                    "hash": file_hash,
                    "created_at": datetime.now().isoformat(),
                    "format": "pdf",
                    "version_info": version_info,
                    "download_url": f"/api/v1/patent/reports/download/{filename}",
                    "pdf_info": {
                        "engine": self.export_config["pdf_engine"],
                        "page_size": self.export_config["pdf_options"]["page_size"],
                        "margin": self.export_config["pdf_options"]["margin"]
                    }
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error exporting PDF: {str(e)}")
            # 如果PDF生成失败，尝试生成备用格式
            return await self._export_pdf_fallback(content, filename, params, version_info, str(e))
    
    async def _export_json(self, content: str, filename: str, 
                         params: Dict[str, Any], version_info: Dict[str, Any]) -> Dict[str, Any]:
        """导出JSON格式报告."""
        try:
            file_path = self.reports_dir / filename
            
            # 创建增强的JSON报告数据
            json_data = {
                "report_metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "format": "json",
                    "parameters": params,
                    "version_info": version_info,
                    "exporter_version": "2.0"
                },
                "content": {
                    "html_content": content,
                    "content_length": len(content),
                    "content_hash": hashlib.md5(content.encode()).hexdigest()
                },
                "export_info": {
                    "exporter": "ReportExporter",
                    "export_time": datetime.now().isoformat(),
                    "export_config": self.export_config
                },
                "file_info": {
                    "filename": filename,
                    "format": "json"
                }
            }
            
            # 写入JSON文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            # 获取文件信息
            file_size = file_path.stat().st_size
            file_hash = self._calculate_file_hash(file_path)
            
            return {
                "json": {
                    "path": str(file_path),
                    "filename": filename,
                    "size": self._format_file_size(file_size),
                    "size_bytes": file_size,
                    "hash": file_hash,
                    "created_at": datetime.now().isoformat(),
                    "format": "json",
                    "version_info": version_info,
                    "download_url": f"/api/v1/patent/reports/download/{filename}"
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error exporting JSON: {str(e)}")
            raise
    
    async def _export_zip(self, content: str, filename: str, 
                        params: Dict[str, Any], version_info: Dict[str, Any]) -> Dict[str, Any]:
        """导出ZIP格式报告包，包含HTML、PDF和JSON格式."""
        try:
            file_path = self.reports_dir / filename
            temp_dir = self.temp_dir / f"zip_export_{uuid.uuid4().hex[:8]}"
            temp_dir.mkdir(exist_ok=True)
            
            try:
                # 生成各种格式的文件
                base_name = filename.replace('.zip', '')
                
                # HTML文件
                html_result = await self._export_html(content, f"{base_name}.html", params, version_info)
                html_file = Path(html_result["html"]["path"])
                
                # JSON文件
                json_result = await self._export_json(content, f"{base_name}.json", params, version_info)
                json_file = Path(json_result["json"]["path"])
                
                # 尝试生成PDF文件
                try:
                    pdf_result = await self._export_pdf(content, f"{base_name}.pdf", params, version_info)
                    pdf_file = Path(pdf_result["pdf"]["path"])
                    include_pdf = True
                except Exception as e:
                    self.logger.warning(f"PDF generation failed for ZIP export: {str(e)}")
                    include_pdf = False
                
                # 创建ZIP文件
                with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    # 添加HTML文件
                    zipf.write(html_file, f"{base_name}.html")
                    
                    # 添加JSON文件
                    zipf.write(json_file, f"{base_name}.json")
                    
                    # 添加PDF文件（如果生成成功）
                    if include_pdf and pdf_file.exists():
                        zipf.write(pdf_file, f"{base_name}.pdf")
                    
                    # 添加元数据文件
                    metadata = {
                        "package_info": {
                            "created_at": datetime.now().isoformat(),
                            "version_info": version_info,
                            "parameters": params,
                            "included_formats": ["html", "json"] + (["pdf"] if include_pdf else [])
                        },
                        "files": {
                            "html": html_result["html"],
                            "json": json_result["json"]
                        }
                    }
                    
                    if include_pdf:
                        metadata["files"]["pdf"] = pdf_result["pdf"]
                    
                    # 写入元数据
                    metadata_json = json.dumps(metadata, ensure_ascii=False, indent=2)
                    zipf.writestr("metadata.json", metadata_json)
                
                # 获取文件信息
                file_size = file_path.stat().st_size
                file_hash = self._calculate_file_hash(file_path)
                
                return {
                    "zip": {
                        "path": str(file_path),
                        "filename": filename,
                        "size": self._format_file_size(file_size),
                        "size_bytes": file_size,
                        "hash": file_hash,
                        "created_at": datetime.now().isoformat(),
                        "format": "zip",
                        "version_info": version_info,
                        "download_url": f"/api/v1/patent/reports/download/{filename}",
                        "package_info": {
                            "included_formats": ["html", "json"] + (["pdf"] if include_pdf else []),
                            "total_files": 3 + (1 if include_pdf else 0),  # +1 for metadata.json
                            "pdf_included": include_pdf
                        }
                    }
                }
                
            finally:
                # 清理临时目录
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
            
        except Exception as e:
            self.logger.error(f"Error exporting ZIP: {str(e)}")
            raise
    
    def _enhance_html_content(self, content: str, params: Dict[str, Any], version_info: Dict[str, Any]) -> str:
        """增强HTML内容，添加样式和元数据."""
        try:
            # 添加版本信息和元数据到HTML头部
            metadata_html = f"""
<!-- Report Metadata -->
<meta name="report-id" content="{version_info.get('report_id', 'unknown')}">
<meta name="report-version" content="{version_info.get('version_number', 1)}">
<meta name="generated-at" content="{datetime.now().isoformat()}">
<meta name="exporter" content="ReportExporter v2.0">

<!-- Enhanced Styles -->
<style>
.report-header {{
    border-bottom: 2px solid #007bff;
    padding-bottom: 10px;
    margin-bottom: 20px;
}}
.report-metadata {{
    background-color: #f8f9fa;
    padding: 10px;
    border-radius: 5px;
    margin-bottom: 20px;
    font-size: 0.9em;
}}
.version-info {{
    float: right;
    color: #6c757d;
}}
@media print {{
    .no-print {{ display: none; }}
}}
</style>
"""
            
            # 如果内容已经包含<head>标签，插入到其中
            if "<head>" in content:
                content = content.replace("<head>", f"<head>{metadata_html}")
            else:
                # 否则在内容开头添加
                content = f"<html><head>{metadata_html}</head><body>{content}</body></html>"
            
            return content
            
        except Exception as e:
            self.logger.error(f"Error enhancing HTML content: {str(e)}")
            return content
    
    def _prepare_pdf_content(self, content: str, params: Dict[str, Any], version_info: Dict[str, Any]) -> str:
        """准备PDF内容，优化PDF生成."""
        try:
            # 为PDF优化HTML内容
            pdf_styles = """
<style>
@page {
    size: A4;
    margin: 2cm;
}
body {
    font-family: 'DejaVu Sans', Arial, sans-serif;
    font-size: 12pt;
    line-height: 1.4;
    color: #333;
}
h1, h2, h3 {
    color: #2c3e50;
    page-break-after: avoid;
}
table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 1em;
}
th, td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
}
th {
    background-color: #f2f2f2;
}
.page-break {
    page-break-before: always;
}
.no-break {
    page-break-inside: avoid;
}
</style>
"""
            
            # 增强内容
            enhanced_content = self._enhance_html_content(content, params, version_info)
            
            # 添加PDF特定样式
            if "<head>" in enhanced_content:
                enhanced_content = enhanced_content.replace("</head>", f"{pdf_styles}</head>")
            else:
                enhanced_content = f"<html><head>{pdf_styles}</head><body>{enhanced_content}</body></html>"
            
            return enhanced_content
            
        except Exception as e:
            self.logger.error(f"Error preparing PDF content: {str(e)}")
            return content
    
    async def _generate_pdf_with_weasyprint(self, html_content: str, params: Dict[str, Any]) -> bytes:
        """使用weasyprint生成PDF."""
        try:
            # 尝试导入weasyprint
            try:
                import weasyprint
                from weasyprint import HTML, CSS
            except ImportError:
                raise ImportError("weasyprint is not installed. Please install it with: pip install weasyprint")
            
            # 配置PDF选项
            pdf_options = self.export_config["pdf_options"]
            
            # 创建CSS样式
            css_styles = CSS(string=f"""
                @page {{
                    size: {pdf_options['page_size']};
                    margin: {pdf_options['margin']};
                }}
            """)
            
            # 生成PDF
            html_doc = HTML(string=html_content, encoding=pdf_options['encoding'])
            pdf_bytes = html_doc.write_pdf(stylesheets=[css_styles])
            
            return pdf_bytes
            
        except ImportError as e:
            self.logger.error(f"weasyprint not available: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Error generating PDF with weasyprint: {str(e)}")
            raise
    
    async def _export_pdf_fallback(self, content: str, filename: str, 
                                 params: Dict[str, Any], version_info: Dict[str, Any], error: str) -> Dict[str, Any]:
        """PDF导出失败时的备用方案."""
        try:
            # 生成HTML文件作为备用
            html_filename = filename.replace('.pdf', '_pdf_fallback.html')
            html_result = await self._export_html(content, html_filename, params, version_info)
            
            # 创建错误信息文件
            error_filename = filename.replace('.pdf', '_pdf_error.txt')
            error_path = self.reports_dir / error_filename
            
            error_content = f"""
PDF Export Error Report
Generated: {datetime.now().isoformat()}
Original filename: {filename}

Error: {error}

A fallback HTML file has been generated: {html_filename}

To generate PDF manually:
1. Open the HTML file in a web browser
2. Use the browser's "Print to PDF" function
3. Or install weasyprint: pip install weasyprint

Report ID: {version_info.get('report_id', 'unknown')}
Version: {version_info.get('version_number', 1)}
"""
            
            with open(error_path, 'w', encoding='utf-8') as f:
                f.write(error_content)
            
            file_size = error_path.stat().st_size
            
            return {
                "pdf": {
                    "path": str(error_path),
                    "filename": error_filename,
                    "size": self._format_file_size(file_size),
                    "size_bytes": file_size,
                    "created_at": datetime.now().isoformat(),
                    "format": "pdf_error",
                    "version_info": version_info,
                    "error": error,
                    "fallback_html": html_result["html"],
                    "download_url": f"/api/v1/patent/reports/download/{error_filename}"
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in PDF fallback: {str(e)}")
            raise
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """计算文件哈希值."""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            self.logger.error(f"Error calculating file hash: {str(e)}")
            return "unknown"
    
    def _format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小."""
        try:
            if size_bytes < 1024:
                return f"{size_bytes}B"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.1f}KB"
            elif size_bytes < 1024 * 1024 * 1024:
                return f"{size_bytes / (1024 * 1024):.1f}MB"
            else:
                return f"{size_bytes / (1024 * 1024 * 1024):.1f}GB"
        except:
            return f"{size_bytes}B"
    
    async def get_export_info(self) -> Dict[str, Any]:
        """获取导出器信息."""
        return {
            "supported_formats": self.export_config["supported_formats"],
            "output_directory": str(self.reports_dir),
            "pdf_engine": self.export_config["pdf_engine"],
            "file_naming_strategy": self.export_config["file_naming"],
            "compression_enabled": self.export_config["compression"],
            "version_control_enabled": self.export_config["version_control"],
            "max_versions": self.export_config["max_versions"],
            "auto_cleanup_days": self.export_config["auto_cleanup_days"],
            "directories": {
                "reports": str(self.reports_dir),
                "versions": str(self.versions_dir),
                "temp": str(self.temp_dir),
                "assets": str(self.assets_dir)
            }
        }
    
    async def list_exported_reports(self, limit: int = 10, format_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出已导出的报告，支持格式过滤."""
        try:
            reports = []
            
            # 扫描报告目录
            for file_path in self.reports_dir.iterdir():
                if file_path.is_file():
                    file_format = file_path.suffix[1:].lower()  # 去掉点号
                    
                    # 格式过滤
                    if format_filter and file_format != format_filter.lower():
                        continue
                    
                    if file_format in ['html', 'pdf', 'json', 'zip', 'txt']:
                        stat = file_path.stat()
                        file_hash = self._calculate_file_hash(file_path)
                        
                        report_info = {
                            "filename": file_path.name,
                            "path": str(file_path),
                            "size": self._format_file_size(stat.st_size),
                            "size_bytes": stat.st_size,
                            "hash": file_hash,
                            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            "format": file_format,
                            "download_url": f"/api/v1/patent/reports/download/{file_path.name}"
                        }
                        
                        # 尝试获取版本信息
                        version_info = await self.version_manager.get_version_by_filename(file_path.name)
                        if version_info:
                            report_info["version_info"] = version_info
                        
                        reports.append(report_info)
            
            # 按创建时间排序，返回最新的
            reports.sort(key=lambda x: x["created_at"], reverse=True)
            return reports[:limit]
            
        except Exception as e:
            self.logger.error(f"Error listing exported reports: {str(e)}")
            return []
    
    async def delete_report(self, filename: str, delete_versions: bool = False) -> Dict[str, Any]:
        """删除指定的报告文件，可选择是否删除所有版本."""
        try:
            file_path = self.reports_dir / filename
            result = {
                "deleted": False,
                "filename": filename,
                "versions_deleted": 0,
                "error": None
            }
            
            if file_path.exists() and file_path.is_file():
                # 获取版本信息
                version_info = await self.version_manager.get_version_by_filename(filename)
                
                # 删除主文件
                file_path.unlink()
                result["deleted"] = True
                self.logger.info(f"Deleted report file: {filename}")
                
                # 如果需要删除版本
                if delete_versions and version_info:
                    versions_deleted = await self.version_manager.delete_report_versions(version_info["report_id"])
                    result["versions_deleted"] = versions_deleted
                
                # 从存储管理器中移除
                await self.storage_manager.remove_report(filename)
                
            else:
                result["error"] = "Report file not found"
                self.logger.warning(f"Report file not found: {filename}")
            
            return result
                
        except Exception as e:
            self.logger.error(f"Error deleting report {filename}: {str(e)}")
            return {
                "deleted": False,
                "filename": filename,
                "versions_deleted": 0,
                "error": str(e)
            }
    
    async def cleanup_old_reports(self, days: Optional[int] = None) -> Dict[str, Any]:
        """清理旧的报告文件和版本."""
        try:
            cleanup_days = days or self.export_config["auto_cleanup_days"]
            cutoff_time = datetime.now().timestamp() - (cleanup_days * 24 * 60 * 60)
            
            result = {
                "reports_deleted": 0,
                "versions_cleaned": 0,
                "temp_files_deleted": 0,
                "total_space_freed": 0,
                "errors": []
            }
            
            # 清理主报告文件
            for file_path in self.reports_dir.iterdir():
                if file_path.is_file() and file_path.stat().st_ctime < cutoff_time:
                    try:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        result["reports_deleted"] += 1
                        result["total_space_freed"] += file_size
                        self.logger.info(f"Deleted old report: {file_path.name}")
                    except Exception as e:
                        error_msg = f"Error deleting {file_path.name}: {str(e)}"
                        result["errors"].append(error_msg)
                        self.logger.error(error_msg)
            
            # 清理版本文件
            versions_cleaned = await self.version_manager.cleanup_old_versions(cleanup_days)
            result["versions_cleaned"] = versions_cleaned
            
            # 清理临时文件
            for temp_file in self.temp_dir.iterdir():
                if temp_file.is_file():
                    try:
                        file_size = temp_file.stat().st_size
                        temp_file.unlink()
                        result["temp_files_deleted"] += 1
                        result["total_space_freed"] += file_size
                    except Exception as e:
                        error_msg = f"Error deleting temp file {temp_file.name}: {str(e)}"
                        result["errors"].append(error_msg)
                elif temp_file.is_dir():
                    try:
                        shutil.rmtree(temp_file)
                        result["temp_files_deleted"] += 1
                    except Exception as e:
                        error_msg = f"Error deleting temp dir {temp_file.name}: {str(e)}"
                        result["errors"].append(error_msg)
            
            self.logger.info(f"Cleanup completed: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
            return {
                "reports_deleted": 0,
                "versions_cleaned": 0,
                "temp_files_deleted": 0,
                "total_space_freed": 0,
                "errors": [str(e)]
            }
    
    async def get_report_by_filename(self, filename: str) -> Optional[Dict[str, Any]]:
        """根据文件名获取报告信息."""
        try:
            file_path = self.reports_dir / filename
            
            if not file_path.exists():
                return None
            
            stat = file_path.stat()
            file_hash = self._calculate_file_hash(file_path)
            
            report_info = {
                "filename": filename,
                "path": str(file_path),
                "size": self._format_file_size(stat.st_size),
                "size_bytes": stat.st_size,
                "hash": file_hash,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "format": file_path.suffix[1:].lower(),
                "download_url": f"/api/v1/patent/reports/download/{filename}"
            }
            
            # 获取版本信息
            version_info = await self.version_manager.get_version_by_filename(filename)
            if version_info:
                report_info["version_info"] = version_info
            
            return report_info
            
        except Exception as e:
            self.logger.error(f"Error getting report {filename}: {str(e)}")
            return None
    
    async def get_download_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """获取文件下载信息."""
        try:
            report_info = await self.get_report_by_filename(filename)
            
            if not report_info:
                return None
            
            file_path = Path(report_info["path"])
            
            # 确定MIME类型
            mime_types = {
                "html": "text/html",
                "pdf": "application/pdf",
                "json": "application/json",
                "zip": "application/zip",
                "txt": "text/plain"
            }
            
            file_format = report_info["format"]
            mime_type = mime_types.get(file_format, "application/octet-stream")
            
            return {
                "filename": filename,
                "path": str(file_path),
                "mime_type": mime_type,
                "size_bytes": report_info["size_bytes"],
                "format": file_format,
                "download_name": filename,
                "exists": file_path.exists()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting download info for {filename}: {str(e)}")
            return None


# 版本管理器
class ReportVersionManager:
    """报告版本管理器."""
    
    def __init__(self, versions_dir: Path, config: Dict[str, Any]):
        self.versions_dir = versions_dir
        self.config = config
        self.max_versions = config.get("max_versions", 5)
        self.logger = logging.getLogger(f"{__name__}.ReportVersionManager")
        
        # 版本索引文件
        self.index_file = versions_dir / "versions_index.json"
        self._ensure_index_file()
    
    def _ensure_index_file(self):
        """确保版本索引文件存在."""
        if not self.index_file.exists():
            initial_data = {
                "created_at": datetime.now().isoformat(),
                "version": "1.0",
                "reports": {}
            }
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, ensure_ascii=False, indent=2)
    
    async def create_version(self, report_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """创建新版本."""
        try:
            # 读取索引
            with open(self.index_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            # 获取或创建报告记录
            if report_id not in index_data["reports"]:
                index_data["reports"][report_id] = {
                    "created_at": datetime.now().isoformat(),
                    "versions": [],
                    "latest_version": 0
                }
            
            report_data = index_data["reports"][report_id]
            
            # 创建新版本
            new_version_number = report_data["latest_version"] + 1
            version_id = f"{report_id}_v{new_version_number}"
            
            version_info = {
                "version_id": version_id,
                "report_id": report_id,
                "version_number": new_version_number,
                "created_at": datetime.now().isoformat(),
                "parameters": params,
                "status": "creating",
                "files": {}
            }
            
            # 添加到版本列表
            report_data["versions"].append(version_info)
            report_data["latest_version"] = new_version_number
            
            # 清理旧版本（如果超过最大数量）
            if len(report_data["versions"]) > self.max_versions:
                old_versions = report_data["versions"][:-self.max_versions]
                report_data["versions"] = report_data["versions"][-self.max_versions:]
                
                # 删除旧版本文件
                for old_version in old_versions:
                    await self._delete_version_files(old_version)
            
            # 保存索引
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)
            
            return version_info
            
        except Exception as e:
            self.logger.error(f"Error creating version for {report_id}: {str(e)}")
            raise
    
    async def update_version_status(self, version_id: str, status: str, files: Dict[str, Any]):
        """更新版本状态."""
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            # 查找并更新版本
            for report_id, report_data in index_data["reports"].items():
                for version in report_data["versions"]:
                    if version["version_id"] == version_id:
                        version["status"] = status
                        version["updated_at"] = datetime.now().isoformat()
                        if files:
                            version["files"] = files
                        break
            
            # 保存索引
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            self.logger.error(f"Error updating version status {version_id}: {str(e)}")
    
    async def get_version_by_filename(self, filename: str) -> Optional[Dict[str, Any]]:
        """根据文件名获取版本信息."""
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            # 搜索包含该文件名的版本
            for report_id, report_data in index_data["reports"].items():
                for version in report_data["versions"]:
                    if "files" in version:
                        for file_format, file_info in version["files"].items():
                            if file_info.get("filename") == filename:
                                return version
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting version by filename {filename}: {str(e)}")
            return None
    
    async def delete_report_versions(self, report_id: str) -> int:
        """删除报告的所有版本."""
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            if report_id not in index_data["reports"]:
                return 0
            
            report_data = index_data["reports"][report_id]
            versions_count = len(report_data["versions"])
            
            # 删除版本文件
            for version in report_data["versions"]:
                await self._delete_version_files(version)
            
            # 从索引中删除
            del index_data["reports"][report_id]
            
            # 保存索引
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)
            
            return versions_count
            
        except Exception as e:
            self.logger.error(f"Error deleting versions for {report_id}: {str(e)}")
            return 0
    
    async def cleanup_old_versions(self, days: int) -> int:
        """清理旧版本."""
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            cleaned_count = 0
            
            with open(self.index_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            for report_id, report_data in list(index_data["reports"].items()):
                versions_to_keep = []
                
                for version in report_data["versions"]:
                    version_time = datetime.fromisoformat(version["created_at"])
                    
                    if version_time < cutoff_time:
                        await self._delete_version_files(version)
                        cleaned_count += 1
                    else:
                        versions_to_keep.append(version)
                
                if versions_to_keep:
                    report_data["versions"] = versions_to_keep
                else:
                    # 如果没有版本保留，删除整个报告记录
                    del index_data["reports"][report_id]
            
            # 保存索引
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)
            
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old versions: {str(e)}")
            return 0
    
    async def _delete_version_files(self, version: Dict[str, Any]):
        """删除版本相关的文件."""
        try:
            if "files" in version:
                for file_format, file_info in version["files"].items():
                    file_path = Path(file_info.get("path", ""))
                    if file_path.exists():
                        file_path.unlink()
                        self.logger.info(f"Deleted version file: {file_path}")
        except Exception as e:
            self.logger.error(f"Error deleting version files: {str(e)}")


# 存储管理器
class ReportStorageManager:
    """报告存储管理器."""
    
    def __init__(self, reports_dir: Path, config: Dict[str, Any]):
        self.reports_dir = reports_dir
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.ReportStorageManager")
        
        # 存储索引文件
        self.storage_index = reports_dir / "storage_index.json"
        self._ensure_storage_index()
    
    def _ensure_storage_index(self):
        """确保存储索引文件存在."""
        if not self.storage_index.exists():
            initial_data = {
                "created_at": datetime.now().isoformat(),
                "version": "1.0",
                "files": {}
            }
            with open(self.storage_index, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, ensure_ascii=False, indent=2)
    
    async def store_report(self, export_result: Dict[str, Any], version_info: Dict[str, Any]):
        """存储报告信息到索引."""
        try:
            with open(self.storage_index, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            # 为每个导出的文件添加存储记录
            for file_format, file_info in export_result.items():
                filename = file_info.get("filename")
                if filename:
                    index_data["files"][filename] = {
                        "format": file_format,
                        "stored_at": datetime.now().isoformat(),
                        "version_info": version_info,
                        "file_info": file_info
                    }
            
            # 保存索引
            with open(self.storage_index, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            self.logger.error(f"Error storing report info: {str(e)}")
    
    async def remove_report(self, filename: str):
        """从存储索引中移除报告."""
        try:
            with open(self.storage_index, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            if filename in index_data["files"]:
                del index_data["files"][filename]
                
                # 保存索引
                with open(self.storage_index, 'w', encoding='utf-8') as f:
                    json.dump(index_data, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            self.logger.error(f"Error removing report from storage index: {str(e)}")


# 为了向后兼容，保留原类名
PatentReportExporter = ReportExporter