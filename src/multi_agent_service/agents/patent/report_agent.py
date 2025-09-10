"""Patent report generation agent implementation."""

import asyncio
import logging
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from .base import PatentBaseAgent
from ...models.base import UserRequest, AgentResponse, Action
from ...models.config import AgentConfig
from ...models.enums import AgentType
from ...services.model_client import BaseModelClient


logger = logging.getLogger(__name__)


class PatentReportAgent(PatentBaseAgent):
    """专利报告生成Agent，负责生成专业的专利分析报告."""
    
    def __init__(self, config: AgentConfig, model_client: BaseModelClient):
        """初始化专利报告Agent."""
        super().__init__(config, model_client)
        
        # 报告生成相关关键词
        self.report_keywords = [
            "报告", "生成", "导出", "下载", "文档", "PDF", "HTML", "图表",
            "可视化", "总结", "汇总", "整理", "输出", "保存", "文件",
            "report", "generate", "export", "download", "document", "chart",
            "visualization", "summary", "output", "save", "file"
        ]
        
        # 报告配置
        self.report_config = {
            "default_format": "html",
            "supported_formats": ["html", "pdf", "json"],
            "max_charts_per_report": 10,
            "chart_width": 800,
            "chart_height": 600,
            "template_dir": "templates/patent",
            "output_dir": "reports/patent",
            "cache_reports": True,
            "report_ttl": 7200  # 2小时
        }
        
        # 确保输出目录存在
        self._ensure_directories()
        
        # 初始化组件（延迟加载）
        self._template_engine = None
        self._chart_generator = None
        self._content_generator = None
        self._report_exporter = None
    
    def _ensure_directories(self):
        """确保必要的目录存在."""
        try:
            template_dir = Path(self.report_config["template_dir"])
            output_dir = Path(self.report_config["output_dir"])
            
            template_dir.mkdir(parents=True, exist_ok=True)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"Ensured directories: {template_dir}, {output_dir}")
            
        except Exception as e:
            self.logger.error(f"Error creating directories: {str(e)}")
    
    async def can_handle_request(self, request: UserRequest) -> float:
        """判断是否能处理报告生成相关请求."""
        # 先调用父类的专利相关判断
        base_confidence = await super().can_handle_request(request)
        
        content = request.content.lower()
        
        # 检查报告生成关键词
        report_matches = sum(1 for keyword in self.report_keywords if keyword in content)
        report_score = min(report_matches * 0.3, 0.8)
        
        # 检查报告特定模式
        import re
        report_patterns = [
            r"(生成|制作|创建).*?(报告|文档)",
            r"(导出|下载|保存).*?(分析|结果|数据)",
            r"(PDF|HTML|图表).*?(报告|文件)",
            r"(可视化|图表|统计图)",
            r"(generate|create).*?(report|document)",
            r"(export|download|save).*?(analysis|result|data)",
            r"(visualization|chart|graph)"
        ]
        
        pattern_score = 0
        for pattern in report_patterns:
            if re.search(pattern, content):
                pattern_score += 0.25
        
        # 综合评分
        total_score = min(base_confidence + report_score + pattern_score, 1.0)
        
        return max(total_score, 0.0)
    
    async def get_capabilities(self) -> List[str]:
        """获取报告Agent的能力列表."""
        base_capabilities = await super().get_capabilities()
        report_capabilities = [
            "HTML报告生成",
            "PDF报告导出",
            "图表生成和可视化",
            "报告模板管理",
            "多格式数据导出",
            "报告内容智能生成",
            "报告质量检查",
            "报告版本管理",
            "报告缓存和分发"
        ]
        return base_capabilities + report_capabilities
    
    async def estimate_processing_time(self, request: UserRequest) -> int:
        """估算报告生成处理时间."""
        content = request.content.lower()
        
        # 简单报告：20-30秒
        if any(word in content for word in ["简单", "基础", "快速"]):
            return 25
        
        # 标准报告：45-60秒
        if any(word in content for word in ["标准", "完整", "详细"]):
            return 50
        
        # 复杂报告：90-120秒
        if any(word in content for word in ["复杂", "全面", "深度", "PDF"]):
            return 105
        
        # 默认报告生成时间
        return 60
    
    async def _process_request_specific(self, request: UserRequest) -> AgentResponse:
        """处理报告生成相关的具体请求."""
        start_time = datetime.now()
        
        try:
            # 解析报告生成请求
            report_params = self._parse_report_request(request.content)
            
            # 检查缓存
            cache_key = self._generate_report_cache_key(report_params)
            cached_result = await self.get_from_cache(cache_key)
            
            if cached_result and self.report_config["cache_reports"]:
                self.logger.info("Returning cached report")
                return AgentResponse(
                    agent_id=self.agent_id,
                    agent_type=self.agent_type,
                    response_content=cached_result["response_content"],
                    confidence=0.9,
                    metadata={
                        **cached_result.get("metadata", {}),
                        "from_cache": True
                    }
                )
            
            # 获取分析数据（模拟从分析Agent获取）
            analysis_data = await self._get_analysis_data_for_report(report_params)
            
            if not analysis_data:
                return AgentResponse(
                    agent_id=self.agent_id,
                    agent_type=self.agent_type,
                    response_content="无法获取分析数据，请先进行专利分析或检查数据源。",
                    confidence=0.3,
                    collaboration_needed=True,
                    metadata={"missing_analysis_data": True}
                )
            
            # 初始化组件（延迟加载）
            await self._initialize_components()
            
            # 生成报告
            report_result = await self._generate_comprehensive_report(analysis_data, report_params)
            
            # 生成响应内容
            response_content = await self._generate_report_response(report_result, report_params)
            
            # 生成后续动作
            next_actions = self._generate_report_actions(report_result)
            
            # 缓存结果
            result_data = {
                "response_content": response_content,
                "metadata": {
                    "report_params": report_params,
                    "processing_time": (datetime.now() - start_time).total_seconds(),
                    "report_files": report_result.get("files", {}),
                    "charts_generated": len(report_result.get("charts", {}))
                }
            }
            
            if self.report_config["cache_reports"]:
                await self.save_to_cache(cache_key, result_data)
            
            # 记录性能指标
            duration = (datetime.now() - start_time).total_seconds()
            self.log_performance_metrics("report_generation", duration, True)
            
            return AgentResponse(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                response_content=response_content,
                confidence=0.9,
                next_actions=next_actions,
                collaboration_needed=False,
                metadata=result_data["metadata"]
            )
            
        except Exception as e:
            self.logger.error(f"Error processing report request: {str(e)}")
            
            # 记录失败指标
            duration = (datetime.now() - start_time).total_seconds()
            self.log_performance_metrics("report_generation", duration, False)
            
            return AgentResponse(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                response_content=f"报告生成过程中发生错误: {str(e)}。请稍后重试或联系技术支持。",
                confidence=0.0,
                collaboration_needed=True,
                metadata={
                    "error": str(e),
                    "processing_time": duration
                }
            )
    
    def _parse_report_request(self, content: str) -> Dict[str, Any]:
        """解析报告生成请求参数."""
        params = {
            "format": self.report_config["default_format"],
            "include_charts": True,
            "include_raw_data": False,
            "template": "standard",
            "sections": ["summary", "trend", "competition", "technology"],
            "chart_types": ["line", "pie", "bar"],
            "language": "zh"
        }
        
        content_lower = content.lower()
        
        # 检测格式
        if "pdf" in content_lower:
            params["format"] = "pdf"
        elif "html" in content_lower:
            params["format"] = "html"
        elif "json" in content_lower:
            params["format"] = "json"
        
        # 检测模板类型
        if any(word in content_lower for word in ["简单", "基础", "simple"]):
            params["template"] = "simple"
        elif any(word in content_lower for word in ["详细", "完整", "detailed"]):
            params["template"] = "detailed"
        elif any(word in content_lower for word in ["执行", "管理", "executive"]):
            params["template"] = "executive"
        
        # 检测是否包含图表
        if any(word in content_lower for word in ["无图", "不要图", "no chart"]):
            params["include_charts"] = False
        
        # 检测是否包含原始数据
        if any(word in content_lower for word in ["原始数据", "详细数据", "raw data"]):
            params["include_raw_data"] = True
        
        # 检测语言
        if any(word in content_lower for word in ["english", "英文", "en"]):
            params["language"] = "en"
        
        return params
    
    def _generate_report_cache_key(self, report_params: Dict[str, Any]) -> str:
        """生成报告缓存键."""
        key_parts = [
            "report",
            report_params["format"],
            report_params["template"],
            "_".join(sorted(report_params["sections"])),
            str(report_params["include_charts"]),
            str(report_params["include_raw_data"])
        ]
        return "_".join(key_parts)
    
    async def _get_analysis_data_for_report(self, report_params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """获取用于报告生成的分析数据（模拟从分析Agent获取）."""
        # 这里应该调用专利分析Agent或从缓存/数据库获取数据
        # 现在提供模拟数据用于演示
        
        try:
            # 模拟分析数据
            mock_analysis_data = {
                "trend_analysis": {
                    "yearly_counts": {
                        "2020": 45,
                        "2021": 52,
                        "2022": 68,
                        "2023": 73,
                        "2024": 41
                    },
                    "growth_rates": {
                        "2021": 15.6,
                        "2022": 30.8,
                        "2023": 7.4,
                        "2024": -43.8
                    },
                    "trend_direction": "increasing",
                    "analysis_summary": "整体呈上升趋势，2024年数据不完整"
                },
                "competition_analysis": {
                    "top_applicants": [
                        ("华为技术有限公司", 28),
                        ("腾讯科技", 15),
                        ("阿里巴巴", 12),
                        ("百度", 8),
                        ("字节跳动", 6)
                    ],
                    "market_concentration": 0.65,
                    "applicant_distribution": {
                        "华为技术有限公司": 28,
                        "腾讯科技": 15,
                        "阿里巴巴": 12,
                        "百度": 8,
                        "字节跳动": 6,
                        "其他": 31
                    }
                },
                "technology_analysis": {
                    "main_technologies": [
                        "人工智能算法",
                        "机器学习模型",
                        "深度学习网络",
                        "自然语言处理",
                        "计算机视觉"
                    ],
                    "ipc_distribution": {
                        "G06F": 45,
                        "G06N": 32,
                        "H04L": 18,
                        "G06K": 15,
                        "G06T": 12
                    },
                    "keyword_clusters": [
                        {"cluster": "AI算法", "keywords": ["算法", "人工智能", "机器学习"], "count": 45},
                        {"cluster": "数据处理", "keywords": ["数据", "处理", "分析"], "count": 32},
                        {"cluster": "网络通信", "keywords": ["网络", "通信", "传输"], "count": 18}
                    ]
                },
                "geographic_analysis": {
                    "country_distribution": {
                        "CN": 85,
                        "US": 12,
                        "JP": 5,
                        "KR": 3,
                        "DE": 2
                    },
                    "country_percentages": {
                        "CN": 79.4,
                        "US": 11.2,
                        "JP": 4.7,
                        "KR": 2.8,
                        "DE": 1.9
                    }
                },
                "insights": {
                    "key_findings": [
                        "人工智能技术专利申请量持续增长",
                        "华为在该领域占据主导地位",
                        "中国是主要的专利申请国"
                    ],
                    "trends": [
                        "技术发展处于快速增长期",
                        "竞争格局相对集中",
                        "创新活动主要集中在亚洲"
                    ],
                    "recommendations": [
                        "持续关注AI技术发展趋势",
                        "重点监控主要竞争对手动态",
                        "考虑在新兴技术领域布局"
                    ]
                },
                "metadata": {
                    "analysis_date": datetime.now().isoformat(),
                    "data_source": "patent_analysis_agent",
                    "total_patents": 107,
                    "analysis_keywords": ["人工智能", "机器学习", "深度学习"]
                }
            }
            
            self.logger.info("Generated mock analysis data for report")
            return mock_analysis_data
            
        except Exception as e:
            self.logger.error(f"Error getting analysis data: {str(e)}")
            return None
    
    async def _initialize_components(self):
        """初始化报告生成组件（延迟加载）."""
        try:
            if not self._template_engine:
                self._template_engine = await self._create_template_engine()
            
            if not self._chart_generator:
                self._chart_generator = await self._create_chart_generator()
            
            if not self._content_generator:
                self._content_generator = await self._create_content_generator()
            
            if not self._report_exporter:
                self._report_exporter = await self._create_report_exporter()
            
            self.logger.info("Report generation components initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing components: {str(e)}")
            raise
    
    async def _create_template_engine(self):
        """创建模板引擎."""
        from .template_engine import PatentTemplateEngine
        template_engine = PatentTemplateEngine(
            template_dir=self.report_config["template_dir"],
            config=self.report_config
        )
        # 创建默认模板
        template_engine._create_default_templates()
        return template_engine
    
    async def _create_chart_generator(self):
        """创建图表生成器."""
        from .chart_generator import ChartGenerator
        return ChartGenerator(self.report_config)
    
    async def _create_content_generator(self):
        """创建内容生成器."""
        from .content_generator import ReportContentGenerator
        return ReportContentGenerator(
            model_client=self.model_client,
            config=self.report_config
        )
    
    async def _create_report_exporter(self):
        """创建报告导出器."""
        from .report_exporter import ReportExporter
        return ReportExporter(config=self.report_config)
    
    async def _generate_comprehensive_report(self, analysis_data: Dict[str, Any], report_params: Dict[str, Any]) -> Dict[str, Any]:
        """生成综合报告."""
        try:
            report_result = {
                "charts": {},
                "content": {},
                "files": {},
                "metadata": {}
            }
            
            # 生成图表（如果需要）
            if report_params["include_charts"]:
                report_result["charts"] = await self._chart_generator.generate_charts(analysis_data, report_params)
            
            # 生成内容
            report_result["content"] = await self._content_generator.generate_content(analysis_data, report_params)
            
            # 渲染模板 - 优先使用Jinja2
            try:
                rendered_content = await self._template_engine.render_template_with_jinja2(
                    template_name=report_params["template"],
                    content=report_result["content"],
                    charts=report_result["charts"],
                    params=report_params
                )
            except Exception as e:
                self.logger.warning(f"Jinja2 rendering failed, using fallback: {str(e)}")
                rendered_content = await self._template_engine.render_template(
                    template_name=report_params["template"],
                    content=report_result["content"],
                    charts=report_result["charts"],
                    params=report_params
                )
            
            # 导出文件
            report_result["files"] = await self._report_exporter.export_report(
                content=rendered_content,
                format=report_params["format"],
                params=report_params
            )
            
            # 添加元数据
            report_result["metadata"] = {
                "generation_time": datetime.now().isoformat(),
                "format": report_params["format"],
                "template": report_params["template"],
                "charts_count": len(report_result["charts"]),
                "sections_count": len(report_params["sections"])
            }
            
            return report_result
            
        except Exception as e:
            self.logger.error(f"Error generating comprehensive report: {str(e)}")
            raise
    
    async def _generate_report_response(self, report_result: Dict[str, Any], report_params: Dict[str, Any]) -> str:
        """生成报告响应内容."""
        try:
            response_parts = []
            
            # 添加报告生成概述
            response_parts.append("## 📊 专利分析报告生成完成")
            response_parts.append("")
            
            # 报告基本信息
            response_parts.append("### 📋 报告信息")
            response_parts.append(f"- **格式**: {report_params['format'].upper()}")
            response_parts.append(f"- **模板**: {report_params['template']}")
            response_parts.append(f"- **生成时间**: {report_result['metadata']['generation_time']}")
            response_parts.append(f"- **包含图表**: {'是' if report_params['include_charts'] else '否'}")
            response_parts.append("")
            
            # 报告内容概述
            if report_result.get("content"):
                response_parts.append("### 📄 报告内容")
                content = report_result["content"]
                
                if "summary" in content:
                    response_parts.append(f"- **执行摘要**: {len(content['summary'])}字")
                
                if "sections" in content:
                    response_parts.append(f"- **分析章节**: {len(content['sections'])}个")
                
                response_parts.append("")
            
            # 图表信息
            if report_result.get("charts"):
                charts = report_result["charts"]
                response_parts.append("### 📈 生成图表")
                
                for chart_name, chart_info in charts.items():
                    chart_type = chart_info.get("type", "未知")
                    response_parts.append(f"- **{chart_name}**: {chart_type}图表")
                
                response_parts.append("")
            
            # 文件信息
            if report_result.get("files"):
                files = report_result["files"]
                response_parts.append("### 📁 生成文件")
                
                for file_type, file_info in files.items():
                    file_path = file_info.get("path", "未知路径")
                    file_size = file_info.get("size", "未知大小")
                    response_parts.append(f"- **{file_type.upper()}文件**: {file_path} ({file_size})")
                
                response_parts.append("")
            
            # 下载和使用说明
            response_parts.append("### 💡 使用说明")
            response_parts.append("- 报告文件已保存到指定目录")
            response_parts.append("- 可通过文件路径直接访问和下载")
            response_parts.append("- 图表支持交互式查看和导出")
            response_parts.append("- 建议定期更新数据并重新生成报告")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            self.logger.error(f"Error generating report response: {str(e)}")
            return f"报告生成完成，但响应生成过程中发生错误: {str(e)}"
    
    def _generate_report_actions(self, report_result: Dict[str, Any]) -> List[Action]:
        """生成报告后续动作."""
        actions = []
        
        try:
            # 基础后续动作
            actions.append(Action(
                action_type="download_report",
                parameters={"files": report_result.get("files", {})},
                description="下载生成的报告文件"
            ))
            
            actions.append(Action(
                action_type="share_report",
                parameters={"format": "email", "recipients": []},
                description="分享报告给相关人员"
            ))
            
            actions.append(Action(
                action_type="schedule_update",
                parameters={"frequency": "monthly", "auto_generate": True},
                description="设置报告定期更新"
            ))
            
            # 基于报告内容的特定动作
            if report_result.get("charts"):
                actions.append(Action(
                    action_type="export_charts",
                    parameters={"format": "png", "resolution": "high"},
                    description="单独导出图表文件"
                ))
            
            return actions
            
        except Exception as e:
            self.logger.error(f"Error generating report actions: {str(e)}")
            return []
    
    async def get_report_templates(self) -> List[Dict[str, Any]]:
        """获取可用的报告模板."""
        try:
            if not self._template_engine:
                await self._initialize_components()
            
            return await self._template_engine.list_templates_with_info()
            
        except Exception as e:
            self.logger.error(f"Error getting report templates: {str(e)}")
            return []
    
    async def create_custom_template(self, template_name: str, template_content: str) -> Dict[str, Any]:
        """创建自定义报告模板."""
        try:
            if not self._template_engine:
                await self._initialize_components()
            
            return await self._template_engine.create_custom_template(template_name, template_content)
            
        except Exception as e:
            self.logger.error(f"Error creating custom template: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def generate_report_with_custom_charts(self, analysis_data: Dict[str, Any], 
                                               chart_configs: List[Dict[str, Any]], 
                                               report_params: Dict[str, Any]) -> Dict[str, Any]:
        """使用自定义图表配置生成报告."""
        try:
            # 初始化组件
            await self._initialize_components()
            
            # 生成自定义图表
            custom_charts = {}
            for i, chart_config in enumerate(chart_configs):
                chart_name = chart_config.get("name", f"custom_chart_{i}")
                chart_type = chart_config.get("type", "bar")
                chart_data = chart_config.get("data", {})
                chart_style = chart_config.get("style", "default")
                
                try:
                    chart_result = await self._chart_generator.create_custom_chart_with_style(
                        chart_type, chart_data, chart_config, chart_style
                    )
                    
                    if "error" not in chart_result:
                        custom_charts[chart_name] = {
                            "type": chart_type,
                            "path": chart_result,
                            "config": chart_config
                        }
                except Exception as e:
                    self.logger.warning(f"Failed to create custom chart {chart_name}: {str(e)}")
            
            # 生成内容
            content = await self._content_generator.generate_content(analysis_data, report_params)
            
            # 渲染模板
            rendered_content = await self._template_engine.render_template_with_jinja2(
                template_name=report_params.get("template", "standard"),
                content=content,
                charts=custom_charts,
                params=report_params
            )
            
            # 导出报告
            export_result = await self._report_exporter.export_report(
                content=rendered_content,
                format=report_params.get("format", "html"),
                params=report_params
            )
            
            return {
                "status": "success",
                "content": content,
                "charts": custom_charts,
                "export_result": export_result,
                "custom_charts_count": len(custom_charts)
            }
            
        except Exception as e:
            self.logger.error(f"Error generating report with custom charts: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def get_report_generation_status(self, report_id: str) -> Dict[str, Any]:
        """获取报告生成状态."""
        try:
            if not self._report_exporter:
                await self._initialize_components()
            
            # 从版本管理器获取状态
            version_info = await self._report_exporter.version_manager.get_version_by_filename(f"{report_id}.html")
            
            if version_info:
                return {
                    "report_id": report_id,
                    "status": version_info.get("status", "unknown"),
                    "created_at": version_info.get("created_at"),
                    "updated_at": version_info.get("updated_at"),
                    "version_number": version_info.get("version_number"),
                    "metadata": version_info.get("metadata", {})
                }
            else:
                return {
                    "report_id": report_id,
                    "status": "not_found",
                    "error": "Report not found"
                }
                
        except Exception as e:
            self.logger.error(f"Error getting report status: {str(e)}")
            return {
                "report_id": report_id,
                "status": "error",
                "error": str(e)
            }
    
    async def list_generated_reports(self, limit: int = 10, format_filter: str = None) -> List[Dict[str, Any]]:
        """列出已生成的报告."""
        try:
            if not self._report_exporter:
                await self._initialize_components()
            
            return await self._report_exporter.list_exported_reports(limit, format_filter)
            
        except Exception as e:
            self.logger.error(f"Error listing reports: {str(e)}")
            return []
    
    async def delete_report(self, filename: str, delete_versions: bool = False) -> Dict[str, Any]:
        """删除指定报告."""
        try:
            if not self._report_exporter:
                await self._initialize_components()
            
            return await self._report_exporter.delete_report(filename, delete_versions)
            
        except Exception as e:
            self.logger.error(f"Error deleting report: {str(e)}")
            return {
                "deleted": False,
                "filename": filename,
                "error": str(e)
            }
    
    async def get_report_statistics(self) -> Dict[str, Any]:
        """获取报告生成统计信息."""
        try:
            if not self._report_exporter:
                await self._initialize_components()
            
            # 获取存储统计
            storage_stats = await self._report_exporter.storage_manager.get_storage_stats()
            
            # 获取导出器信息
            exporter_info = await self._report_exporter.get_export_info()
            
            # 获取图表生成器信息
            chart_info = self._chart_generator.get_cache_info() if self._chart_generator else {}
            
            return {
                "storage_statistics": storage_stats,
                "exporter_info": exporter_info,
                "chart_info": chart_info,
                "agent_info": {
                    "agent_id": self.agent_id,
                    "agent_type": str(self.agent_type),
                    "capabilities_count": len(await self.get_capabilities())
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting storage stats: {str(e)}")
            return {
                "storage_statistics": {"total_files": 0, "total_size": 0, "format_distribution": {}},
                "exporter_info": {},
                "chart_info": {},
                "agent_info": {
                    "agent_id": self.agent_id,
                    "agent_type": str(self.agent_type),
                    "capabilities_count": 0
                },
                "error": str(e)
            }
    
    async def cleanup_old_reports(self, days: int = None) -> Dict[str, Any]:
        """清理旧报告."""
        try:
            if not self._report_exporter:
                await self._initialize_components()
            
            cleanup_days = days or self.report_config.get("auto_cleanup_days", 30)
            return await self._report_exporter.cleanup_old_reports(cleanup_days)
            
        except Exception as e:
            self.logger.error(f"Error cleaning up reports: {str(e)}")
            return {
                "reports_deleted": 0,
                "versions_cleaned": 0,
                "temp_files_deleted": 0,
                "total_space_freed": 0,
                "errors": [str(e)]
            }


