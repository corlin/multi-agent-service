"""Patent report generation agent."""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import uuid4

from .base import PatentBaseAgent
from ...models.enums import AgentType
from ...models.config import AgentConfig
from ...services.model_client import BaseModelClient

from ..models.requests import PatentAnalysisRequest
from ..models.results import PatentAnalysisResult
from ..models.reports import Report, ReportContent


logger = logging.getLogger(__name__)


class PatentReportAgent(PatentBaseAgent):
    """专利报告生成智能体，负责生成分析报告."""
    
    agent_type = AgentType.PATENT_REPORT
    
    def __init__(self, config: AgentConfig, model_client: BaseModelClient):
        """初始化专利报告智能体."""
        super().__init__(config, model_client)
        
        # 报告生成专用配置
        self.report_config = {
            'supported_formats': ['html', 'pdf'],
            'template_directory': 'templates/patent',
            'chart_generation_enabled': True,
            'max_report_size': 50 * 1024 * 1024,  # 50MB
            'default_template': 'comprehensive_report.html'
        }
        
        # 报告模板配置
        self.report_templates = {
            'comprehensive': {
                'template_file': 'comprehensive_report.html',
                'sections': ['summary', 'trend', 'technology', 'competition', 'conclusions'],
                'charts': ['trend_chart', 'tech_pie_chart', 'competition_bar_chart']
            },
            'executive': {
                'template_file': 'executive_summary.html',
                'sections': ['summary', 'key_insights', 'recommendations'],
                'charts': ['trend_chart']
            },
            'technical': {
                'template_file': 'technical_report.html',
                'sections': ['technology', 'classification', 'evolution'],
                'charts': ['tech_pie_chart', 'evolution_chart']
            }
        }
        
        self.logger = logging.getLogger(f"{__name__}.PatentReportAgent")
    
    async def can_handle_request(self, request) -> float:
        """判断是否能处理请求."""
        # 调用父类的实现
        base_confidence = await super().can_handle_request(request)
        
        # 检查报告相关关键词
        content = getattr(request, 'content', str(request)).lower()
        report_keywords = ["报告", "生成", "导出", "可视化", "图表"]
        keyword_matches = sum(1 for keyword in report_keywords if keyword in content)
        
        # 提高报告相关请求的置信度
        report_boost = min(keyword_matches * 0.2, 0.3)
        
        return min(base_confidence + report_boost, 1.0)
    
    async def get_capabilities(self) -> List[str]:
        """获取Agent能力列表."""
        base_capabilities = await super().get_capabilities()
        specific_capabilities = await self._get_specific_capabilities()
        return base_capabilities + specific_capabilities
    
    async def estimate_processing_time(self, request) -> int:
        """估算处理时间."""
        # 报告生成任务通常需要中等时间
        base_time = await super().estimate_processing_time(request)
        return base_time + 25  # 报告生成额外需要25秒
    
    async def _process_request_specific(self, request) -> 'AgentResponse':
        """处理具体的报告生成请求."""
        from ...models.base import AgentResponse
        
        try:
            # 如果是PatentAnalysisRequest对象，直接处理
            if hasattr(request, 'analysis_types'):
                result = await self._process_patent_request_specific(request)
            else:
                # 如果是普通请求，转换为分析请求
                from ..models.requests import PatentAnalysisRequest, AnalysisType
                
                # 从请求内容提取关键词
                content = getattr(request, 'content', str(request))
                keywords = content.split()[:5]  # 简单提取前5个词作为关键词
                
                analysis_request = PatentAnalysisRequest(
                    request_id=str(uuid4()),
                    keywords=keywords,
                    analysis_types=[AnalysisType.COMPREHENSIVE],
                    date_range={"start": "2020-01-01", "end": "2024-12-31"},
                    countries=["US", "CN", "EP"],
                    max_patents=1000
                )
                
                result = await self._process_patent_request_specific(analysis_request)
            
            # 生成响应内容
            response_content = f"专利报告生成完成。状态: {result.get('status', 'unknown')}"
            
            return AgentResponse(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                response_content=response_content,
                confidence=0.8,
                metadata=result
            )
            
        except Exception as e:
            self.logger.error(f"Error processing report generation request: {str(e)}")
            return AgentResponse(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                response_content=f"报告生成处理失败: {str(e)}",
                confidence=0.0,
                metadata={"error": str(e)}
            )
    
    async def _process_patent_request_specific(self, request) -> Dict[str, Any]:
        """处理专利特定请求."""
        try:
            # 模拟报告生成处理
            return {
                "status": "success",
                "report_format": "html",
                "report_size": "2.5MB",
                "processing_time": 45.0
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _get_specific_capabilities(self) -> List[str]:
        """获取报告生成智能体的特定能力."""
        return [
            "专利分析报告生成",
            "多格式报告导出",
            "图表自动生成",
            "报告模板管理",
            "内容质量检查",
            "报告版本控制",
            "批量报告生成"
        ]
    
    async def _process_patent_request(self, request: PatentAnalysisRequest) -> Dict[str, Any]:
        """处理专利报告生成请求."""
        start_time = datetime.now()
        report_id = f"report_{request.request_id}_{int(datetime.now().timestamp())}"
        
        try:
            self.logger.info(f"Starting report generation {report_id} for request {request.request_id}")
            
            # 检查缓存
            cache_key = f"patent_report_{hash(str(request.keywords))}_{request.report_format}"
            cached_result = await self._get_from_cache(cache_key)
            if cached_result:
                self.logger.info(f"Using cached report for request {request.request_id}")
                return cached_result
            
            # 模拟获取分析结果（实际实现中会从PatentAnalysisAgent获取）
            analysis_result = await self._get_analysis_result(request)
            
            if not analysis_result:
                raise Exception("No analysis result available for report generation")
            
            # 生成报告
            report = await self._generate_comprehensive_report(report_id, request, analysis_result)
            
            # 验证报告质量
            quality_score = await self._validate_report_quality(report)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                "status": "completed",
                "report": report,
                "report_id": report_id,
                "quality_score": quality_score,
                "processing_time": processing_time,
                "formats_generated": [request.report_format],
                "file_size": len(report.html_content) if report else 0
            }
            
            # 保存到缓存
            await self._save_to_cache(cache_key, result)
            
            self.logger.info(f"Report generation {report_id} completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Report generation {report_id} failed: {str(e)}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "status": "failed",
                "report_id": report_id,
                "error": str(e),
                "processing_time": processing_time,
                "formats_generated": []
            }
    
    async def _get_analysis_result(self, request: PatentAnalysisRequest) -> Optional[PatentAnalysisResult]:
        """获取分析结果（模拟实现）."""
        # 实际实现中会从PatentAnalysisAgent或协调结果中获取
        from ..models.results import (
            PatentAnalysisResult, TrendAnalysisModel, 
            TechClassificationModel, CompetitionAnalysisModel
        )
        
        # 模拟分析结果
        trend_analysis = TrendAnalysisModel(
            yearly_counts={2020: 45, 2021: 52, 2022: 68, 2023: 78, 2024: 85},
            growth_rates={2021: 0.16, 2022: 0.31, 2023: 0.15, 2024: 0.09},
            trend_direction="increasing",
            peak_year=2024,
            total_patents=328,
            average_annual_growth=0.18
        )
        
        tech_classification = TechClassificationModel(
            ipc_distribution={"G06F": 45, "H04L": 32, "G06N": 28, "H04W": 22, "G06Q": 18},
            keyword_clusters=[
                {"cluster_id": 0, "main_keyword": "artificial intelligence", "patent_count": 35},
                {"cluster_id": 1, "main_keyword": "machine learning", "patent_count": 28},
                {"cluster_id": 2, "main_keyword": "neural network", "patent_count": 22}
            ],
            main_technologies=["G06F (45 patents)", "H04L (32 patents)", "G06N (28 patents)"]
        )
        
        competition_analysis = CompetitionAnalysisModel(
            applicant_distribution={"Company A": 25, "Company B": 18, "Company C": 15, "Company D": 12},
            top_applicants=[("Company A", 25), ("Company B", 18), ("Company C", 15)],
            market_concentration=0.42,
            hhi_index=0.18
        )
        
        return PatentAnalysisResult(
            request_id=request.request_id,
            analysis_date=datetime.now(),
            trend_analysis=trend_analysis,
            tech_classification=tech_classification,
            competition_analysis=competition_analysis,
            insights=[
                "专利申请呈稳定增长趋势，年均增长率18%",
                "人工智能相关技术占主导地位",
                "市场竞争相对分散，前三名申请人占比58%"
            ],
            recommendations=[
                "建议加大AI技术研发投入",
                "关注G06F和H04L技术领域机会",
                "考虑与领先企业建立合作关系"
            ],
            data_quality_score=0.85,
            confidence_level=0.88,
            total_patents_analyzed=328,
            data_sources_used=["google_patents", "patent_public_api"],
            processing_time=5.2
        )
    
    async def _generate_comprehensive_report(self, report_id: str, request: PatentAnalysisRequest, 
                                           analysis_result: PatentAnalysisResult) -> Report:
        """生成综合分析报告."""
        
        # 生成图表
        charts = await self._generate_charts(analysis_result)
        
        # 生成报告内容
        report_content = await self._generate_report_content(analysis_result)
        
        # 渲染HTML报告
        html_content = await self._render_html_report(report_content, charts, request)
        
        # 生成PDF（如果需要）
        pdf_content = None
        if request.report_format == 'pdf':
            pdf_content = await self._generate_pdf_report(html_content)
        
        report = Report(
            report_id=report_id,
            request_id=request.request_id,
            html_content=html_content,
            pdf_content=pdf_content,
            charts=charts,
            summary=report_content.summary,
            generation_date=datetime.now(),
            metadata={
                'template_used': 'comprehensive',
                'charts_count': len(charts),
                'sections_count': 5,
                'analysis_confidence': analysis_result.confidence_level
            }
        )
        
        return report
    
    async def _generate_charts(self, analysis_result: PatentAnalysisResult) -> Dict[str, str]:
        """生成报告图表."""
        charts = {}
        
        try:
            # 趋势图
            if analysis_result.trend_analysis:
                charts['trend_chart'] = await self._create_trend_chart(analysis_result.trend_analysis)
            
            # 技术分类饼图
            if analysis_result.tech_classification:
                charts['tech_pie_chart'] = await self._create_tech_pie_chart(analysis_result.tech_classification)
            
            # 竞争格局柱状图
            if analysis_result.competition_analysis:
                charts['competition_bar_chart'] = await self._create_competition_chart(analysis_result.competition_analysis)
            
            self.logger.info(f"Generated {len(charts)} charts")
            
        except Exception as e:
            self.logger.error(f"Chart generation failed: {str(e)}")
        
        return charts
    
    async def _create_trend_chart(self, trend_analysis) -> str:
        """创建趋势图表."""
        # 模拟图表生成 - 实际实现中会使用matplotlib或plotly
        chart_data = {
            'type': 'line',
            'title': '专利申请趋势',
            'data': trend_analysis.yearly_counts,
            'x_label': '年份',
            'y_label': '申请量'
        }
        
        # 返回图表的base64编码或HTML
        return f"<div class='chart' data-chart='{chart_data}'>趋势图表占位符</div>"
    
    async def _create_tech_pie_chart(self, tech_classification) -> str:
        """创建技术分类饼图."""
        chart_data = {
            'type': 'pie',
            'title': '技术分类分布',
            'data': tech_classification.ipc_distribution
        }
        
        return f"<div class='chart' data-chart='{chart_data}'>技术分类饼图占位符</div>"
    
    async def _create_competition_chart(self, competition_analysis) -> str:
        """创建竞争格局图表."""
        chart_data = {
            'type': 'bar',
            'title': '主要申请人专利数量',
            'data': dict(competition_analysis.top_applicants[:5]),
            'x_label': '申请人',
            'y_label': '专利数量'
        }
        
        return f"<div class='chart' data-chart='{chart_data}'>竞争格局柱状图占位符</div>"
    
    async def _generate_report_content(self, analysis_result: PatentAnalysisResult) -> ReportContent:
        """生成报告内容."""
        
        # 生成摘要
        summary = await self._generate_summary(analysis_result)
        
        # 生成各部分内容
        trend_section = await self._generate_trend_section(analysis_result.trend_analysis)
        tech_section = await self._generate_tech_section(analysis_result.tech_classification)
        competition_section = await self._generate_competition_section(analysis_result.competition_analysis)
        conclusions = await self._generate_conclusions(analysis_result)
        
        return ReportContent(
            summary=summary,
            trend_section=trend_section,
            tech_section=tech_section,
            competition_section=competition_section,
            conclusions=conclusions,
            methodology="本报告基于专利数据库检索和多维度分析方法生成",
            limitations="分析结果基于公开专利数据，可能存在数据延迟和不完整性"
        )
    
    async def _generate_summary(self, analysis_result: PatentAnalysisResult) -> str:
        """生成报告摘要."""
        total_patents = analysis_result.total_patents_analyzed
        confidence = analysis_result.confidence_level
        
        summary = f"""
本报告基于 {total_patents} 件专利数据进行分析，置信度为 {confidence:.1%}。

主要发现：
"""
        
        for insight in analysis_result.insights[:3]:
            summary += f"• {insight}\n"
        
        return summary.strip()
    
    async def _generate_trend_section(self, trend_analysis) -> str:
        """生成趋势分析部分."""
        if not trend_analysis:
            return "趋势分析数据不可用。"
        
        section = f"""
## 专利申请趋势分析

### 总体趋势
专利申请总量为 {trend_analysis.total_patents} 件，呈现{trend_analysis.trend_direction}趋势。
平均年增长率为 {trend_analysis.average_annual_growth:.1%}。

### 年度分布
"""
        
        for year, count in sorted(trend_analysis.yearly_counts.items()):
            section += f"• {year}年: {count} 件\n"
        
        if trend_analysis.peak_year:
            section += f"\n{trend_analysis.peak_year}年为专利申请峰值年份。"
        
        return section.strip()
    
    async def _generate_tech_section(self, tech_classification) -> str:
        """生成技术分析部分."""
        if not tech_classification:
            return "技术分类分析数据不可用。"
        
        section = """
## 技术分类分析

### IPC分类分布
"""
        
        for ipc, count in sorted(tech_classification.ipc_distribution.items(), 
                                key=lambda x: x[1], reverse=True)[:5]:
            section += f"• {ipc}: {count} 件\n"
        
        section += "\n### 主要技术领域\n"
        for tech in tech_classification.main_technologies[:3]:
            section += f"• {tech}\n"
        
        return section.strip()
    
    async def _generate_competition_section(self, competition_analysis) -> str:
        """生成竞争分析部分."""
        if not competition_analysis:
            return "竞争分析数据不可用。"
        
        section = f"""
## 竞争格局分析

### 市场集中度
市场集中度为 {competition_analysis.market_concentration:.2f}，
HHI指数为 {competition_analysis.hhi_index:.3f}。

### 主要申请人
"""
        
        for applicant, count in competition_analysis.top_applicants[:5]:
            section += f"• {applicant}: {count} 件\n"
        
        return section.strip()
    
    async def _generate_conclusions(self, analysis_result: PatentAnalysisResult) -> str:
        """生成结论部分."""
        conclusions = """
## 结论与建议

### 主要结论
"""
        
        for insight in analysis_result.insights:
            conclusions += f"• {insight}\n"
        
        conclusions += "\n### 建议\n"
        for recommendation in analysis_result.recommendations:
            conclusions += f"• {recommendation}\n"
        
        return conclusions.strip()
    
    async def _render_html_report(self, content: ReportContent, charts: Dict[str, str], 
                                 request: PatentAnalysisRequest) -> str:
        """渲染HTML报告."""
        
        # 简化的HTML模板
        html_template = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>专利分析报告 - {' '.join(request.keywords)}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        h1, h2 {{ color: #333; }}
        .chart {{ margin: 20px 0; padding: 20px; border: 1px solid #ddd; }}
        .summary {{ background: #f9f9f9; padding: 20px; margin: 20px 0; }}
    </style>
</head>
<body>
    <h1>专利分析报告</h1>
    <p><strong>关键词:</strong> {', '.join(request.keywords)}</p>
    <p><strong>生成时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <div class="summary">
        <h2>执行摘要</h2>
        {content.summary}
    </div>
    
    {charts.get('trend_chart', '')}
    {content.trend_section}
    
    {charts.get('tech_pie_chart', '')}
    {content.tech_section}
    
    {charts.get('competition_bar_chart', '')}
    {content.competition_section}
    
    {content.conclusions}
    
    <hr>
    <p><small>{content.methodology}</small></p>
    <p><small>局限性: {content.limitations}</small></p>
</body>
</html>
"""
        
        return html_template
    
    async def _generate_pdf_report(self, html_content: str) -> Optional[bytes]:
        """生成PDF报告."""
        try:
            # 模拟PDF生成 - 实际实现中会使用weasyprint或类似库
            self.logger.info("Generating PDF report...")
            
            # 这里应该使用真实的PDF生成库
            # import weasyprint
            # pdf_bytes = weasyprint.HTML(string=html_content).write_pdf()
            
            # 模拟PDF内容
            pdf_content = f"PDF Report Content - Generated at {datetime.now()}".encode('utf-8')
            
            return pdf_content
            
        except Exception as e:
            self.logger.error(f"PDF generation failed: {str(e)}")
            return None
    
    async def _validate_report_quality(self, report: Report) -> float:
        """验证报告质量."""
        quality_score = 0.0
        
        # 检查内容完整性
        if report.html_content and len(report.html_content) > 1000:
            quality_score += 0.3
        
        # 检查图表数量
        if report.charts and len(report.charts) >= 2:
            quality_score += 0.2
        
        # 检查摘要质量
        if report.summary and len(report.summary) > 100:
            quality_score += 0.2
        
        # 检查格式支持
        if report.html_content:
            quality_score += 0.15
        if report.pdf_content:
            quality_score += 0.15
        
        return min(quality_score, 1.0)
    
    async def _generate_response_content(self, result: Dict[str, Any]) -> str:
        """生成报告生成响应内容."""
        if result.get("status") == "completed":
            report_id = result.get("report_id", "unknown")
            quality_score = result.get("quality_score", 0.0)
            processing_time = result.get("processing_time", 0.0)
            file_size = result.get("file_size", 0)
            formats = result.get("formats_generated", [])
            
            return f"""专利分析报告生成完成！

📄 报告信息:
• 报告ID: {report_id}
• 生成格式: {', '.join(formats)}
• 文件大小: {file_size / 1024:.1f} KB
• 质量评分: {quality_score:.2f}/1.0
• 生成时间: {processing_time:.1f}秒

报告已生成完毕，包含趋势分析、技术分类、竞争格局等完整内容，可供下载和分享。"""
        
        elif result.get("status") == "failed":
            report_id = result.get("report_id", "unknown")
            error = result.get("error", "未知错误")
            return f"报告生成失败 (ID: {report_id}): {error}"
        
        else:
            return f"报告生成状态: {result.get('status', 'unknown')}"