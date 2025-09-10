"""Patent analysis agent."""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from collections import defaultdict

from .base import PatentBaseAgent
from ...models.enums import AgentType
from ...models.config import AgentConfig
from ...services.model_client import BaseModelClient

from ..models.requests import PatentAnalysisRequest
from ..models.results import PatentAnalysisResult, TrendAnalysis, TechClassification, CompetitionAnalysis
from ..models.patent_data import PatentDataset
from ..models.external_data import EnhancedData


logger = logging.getLogger(__name__)


class PatentAnalysisAgent(PatentBaseAgent):
    """专利分析处理智能体，负责专利数据分析."""
    
    agent_type = AgentType.PATENT_ANALYSIS
    
    def __init__(self, config: AgentConfig, model_client: BaseModelClient):
        """初始化专利分析智能体."""
        super().__init__(config, model_client)
        
        # 分析专用配置
        self.analysis_config = {
            'enable_trend_analysis': True,
            'enable_tech_classification': True,
            'enable_competition_analysis': True,
            'enable_geographic_analysis': True,
            'min_patents_for_analysis': 10,
            'confidence_threshold': 0.7
        }
        
        self.logger = logging.getLogger(f"{__name__}.PatentAnalysisAgent")
    
    async def _get_specific_capabilities(self) -> List[str]:
        """获取分析智能体的特定能力."""
        return [
            "专利趋势分析",
            "技术分类统计",
            "竞争格局分析",
            "地域分布分析",
            "IPC分类分析",
            "申请人统计分析",
            "时间序列分析",
            "技术演进预测"
        ]
    
    async def _process_patent_request(self, request: PatentAnalysisRequest) -> Dict[str, Any]:
        """处理专利分析请求."""
        start_time = datetime.now()
        
        try:
            self.logger.info(f"Starting patent analysis for request {request.request_id}")
            
            # 检查缓存
            cache_key = f"patent_analysis_{hash(str(request.keywords))}_{hash(str(request.analysis_types))}"
            cached_result = await self._get_from_cache(cache_key)
            if cached_result:
                self.logger.info(f"Using cached analysis results for request {request.request_id}")
                return cached_result
            
            # 模拟获取专利数据和增强数据（实际实现中会从其他Agent获取）
            patent_dataset = await self._get_patent_dataset(request)
            enhanced_data = await self._get_enhanced_data(request)
            
            if not patent_dataset or len(patent_dataset.patents) < self.analysis_config['min_patents_for_analysis']:
                raise Exception(f"Insufficient patent data for analysis (minimum {self.analysis_config['min_patents_for_analysis']} required)")
            
            # 执行各种分析
            analysis_result = await self._perform_comprehensive_analysis(
                patent_dataset, enhanced_data, request
            )
            
            # 生成洞察和建议
            insights = await self._generate_insights(analysis_result, enhanced_data)
            recommendations = await self._generate_recommendations(analysis_result, enhanced_data)
            
            # 评估分析质量
            quality_score = await self._evaluate_analysis_quality(analysis_result, patent_dataset)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                "status": "completed",
                "analysis_result": analysis_result,
                "insights": insights,
                "recommendations": recommendations,
                "quality_score": quality_score,
                "processing_time": processing_time,
                "total_patents_analyzed": len(patent_dataset.patents),
                "analysis_types": [at.value for at in request.analysis_types]
            }
            
            # 保存到缓存
            await self._save_to_cache(cache_key, result)
            
            self.logger.info(f"Patent analysis completed for request {request.request_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Patent analysis failed for request {request.request_id}: {str(e)}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "status": "failed",
                "error": str(e),
                "processing_time": processing_time,
                "total_patents_analyzed": 0
            }
    
    async def _get_patent_dataset(self, request: PatentAnalysisRequest) -> Optional[PatentDataset]:
        """获取专利数据集（模拟实现）."""
        # 实际实现中会从PatentDataCollectionAgent获取数据
        from ..models.patent_data import PatentData
        
        # 生成模拟专利数据用于分析
        patents = []
        for i in range(100):  # 模拟100个专利
            year = 2020 + (i % 5)  # 2020-2024年的数据
            patent = PatentData(
                application_number=f"US{year}{1000 + i}",
                title=f"Patent for {' '.join(request.keywords)} technology - {i}",
                abstract=f"This patent describes {' '.join(request.keywords)} implementation...",
                applicants=[f"Company {chr(65 + i % 10)}", f"Corp {i % 5}"][:(i % 2 + 1)],
                inventors=[f"Inventor {i % 20}"],
                application_date=datetime(year, 1 + i % 12, 1 + i % 28),
                country=["US", "CN", "JP", "DE", "KR"][i % 5],
                status=["Published", "Granted", "Pending"][i % 3],
                ipc_classes=[f"G06F{i % 20}/00", f"H04L{i % 15}/00"][:(i % 2 + 1)]
            )
            patents.append(patent)
        
        return PatentDataset(
            patents=patents,
            total_count=len(patents),
            search_keywords=request.keywords,
            collection_date=datetime.now(),
            data_sources=["google_patents", "patent_public_api"]
        )
    
    async def _get_enhanced_data(self, request: PatentAnalysisRequest) -> Optional[EnhancedData]:
        """获取增强数据（模拟实现）."""
        # 实际实现中会从PatentSearchAgent获取数据
        return EnhancedData(
            academic_data=None,  # 简化模拟
            web_intelligence=None,
            collection_date=datetime.now()
        )
    
    async def _perform_comprehensive_analysis(
        self, 
        patent_dataset: PatentDataset, 
        enhanced_data: Optional[EnhancedData],
        request: PatentAnalysisRequest
    ) -> PatentAnalysisResult:
        """执行综合专利分析."""
        
        analysis_result = PatentAnalysisResult(
            request_id=request.request_id,
            analysis_date=datetime.now(),
            total_patents_analyzed=len(patent_dataset.patents),
            data_sources_used=patent_dataset.data_sources
        )
        
        # 趋势分析
        if any(at.value == "trend_analysis" or at.value == "comprehensive" for at in request.analysis_types):
            analysis_result.trend_analysis = await self._analyze_trends(patent_dataset)
        
        # 技术分类分析
        if any(at.value == "tech_classification" or at.value == "comprehensive" for at in request.analysis_types):
            analysis_result.tech_classification = await self._classify_technologies(patent_dataset)
        
        # 竞争分析
        if any(at.value == "competition_analysis" or at.value == "comprehensive" for at in request.analysis_types):
            analysis_result.competition_analysis = await self._analyze_competition(patent_dataset)
        
        # 地域分析
        if any(at.value == "geographic_analysis" or at.value == "comprehensive" for at in request.analysis_types):
            from ..models.results import GeographicAnalysisModel
            analysis_result.geographic_analysis = await self._analyze_geography(patent_dataset)
        
        return analysis_result
    
    async def _analyze_trends(self, patent_dataset: PatentDataset) -> TrendAnalysis:
        """执行趋势分析."""
        from ..models.results import TrendAnalysisModel
        
        # 按年份统计专利申请量
        yearly_counts = defaultdict(int)
        for patent in patent_dataset.patents:
            if patent.application_date:
                year = patent.application_date.year
                yearly_counts[year] += 1
        
        # 计算增长率
        growth_rates = {}
        years = sorted(yearly_counts.keys())
        for i in range(1, len(years)):
            prev_year = years[i-1]
            curr_year = years[i]
            if yearly_counts[prev_year] > 0:
                growth_rate = (yearly_counts[curr_year] - yearly_counts[prev_year]) / yearly_counts[prev_year]
                growth_rates[curr_year] = growth_rate
        
        # 确定趋势方向
        if len(growth_rates) > 0:
            avg_growth = sum(growth_rates.values()) / len(growth_rates)
            if avg_growth > 0.1:
                trend_direction = "increasing"
            elif avg_growth < -0.1:
                trend_direction = "decreasing"
            else:
                trend_direction = "stable"
        else:
            trend_direction = "stable"
        
        # 找到峰值年份
        peak_year = max(yearly_counts.keys(), key=lambda y: yearly_counts[y]) if yearly_counts else None
        
        return TrendAnalysisModel(
            yearly_counts=dict(yearly_counts),
            growth_rates=growth_rates,
            trend_direction=trend_direction,
            peak_year=peak_year,
            total_patents=sum(yearly_counts.values()),
            average_annual_growth=sum(growth_rates.values()) / len(growth_rates) if growth_rates else 0.0
        )
    
    async def _classify_technologies(self, patent_dataset: PatentDataset) -> TechClassification:
        """执行技术分类分析."""
        from ..models.results import TechClassificationModel
        
        # IPC分类统计
        ipc_counts = defaultdict(int)
        for patent in patent_dataset.patents:
            for ipc in patent.ipc_classes or []:
                # 提取主分类（前4位）
                main_ipc = ipc[:4] if len(ipc) >= 4 else ipc
                ipc_counts[main_ipc] += 1
        
        # 关键词聚类（简化实现）
        keyword_clusters = []
        main_keywords = set()
        for patent in patent_dataset.patents:
            # 从标题中提取关键词
            title_words = patent.title.lower().split()
            for word in title_words:
                if len(word) > 4:  # 过滤短词
                    main_keywords.add(word)
        
        # 创建关键词聚类
        keyword_list = list(main_keywords)[:10]  # 取前10个关键词
        for i, keyword in enumerate(keyword_list):
            cluster = {
                "cluster_id": i,
                "main_keyword": keyword,
                "related_keywords": keyword_list[max(0, i-2):i+3],
                "patent_count": sum(1 for p in patent_dataset.patents if keyword in p.title.lower())
            }
            keyword_clusters.append(cluster)
        
        # 识别主要技术
        main_technologies = []
        sorted_ipc = sorted(ipc_counts.items(), key=lambda x: x[1], reverse=True)
        for ipc, count in sorted_ipc[:5]:  # 取前5个IPC分类
            main_technologies.append(f"{ipc} ({count} patents)")
        
        return TechClassificationModel(
            ipc_distribution=dict(ipc_counts),
            keyword_clusters=keyword_clusters,
            main_technologies=main_technologies
        )
    
    async def _analyze_competition(self, patent_dataset: PatentDataset) -> CompetitionAnalysis:
        """执行竞争分析."""
        from ..models.results import CompetitionAnalysisModel
        
        # 申请人统计
        applicant_counts = defaultdict(int)
        for patent in patent_dataset.patents:
            for applicant in patent.applicants or []:
                applicant_counts[applicant] += 1
        
        # 排序获取顶级申请人
        top_applicants = sorted(applicant_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # 计算市场集中度（HHI指数）
        total_patents = sum(applicant_counts.values())
        if total_patents > 0:
            hhi_index = sum((count / total_patents) ** 2 for count in applicant_counts.values())
            market_concentration = hhi_index
        else:
            hhi_index = 0.0
            market_concentration = 0.0
        
        return CompetitionAnalysisModel(
            applicant_distribution=dict(applicant_counts),
            top_applicants=top_applicants,
            market_concentration=market_concentration,
            hhi_index=hhi_index
        )
    
    async def _analyze_geography(self, patent_dataset: PatentDataset) -> Dict[str, Any]:
        """执行地域分析."""
        # 国家分布统计
        country_counts = defaultdict(int)
        for patent in patent_dataset.patents:
            if patent.country:
                country_counts[patent.country] += 1
        
        # 排序获取顶级国家
        top_countries = sorted(country_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # 计算全球化指数（简化版）
        total_patents = sum(country_counts.values())
        if total_patents > 0 and len(country_counts) > 1:
            # 基于国家数量和分布均匀度计算
            globalization_index = len(country_counts) / 10  # 假设最多10个主要国家
            globalization_index = min(globalization_index, 1.0)
        else:
            globalization_index = 0.0
        
        return {
            "country_distribution": dict(country_counts),
            "top_countries": top_countries,
            "globalization_index": globalization_index,
            "regional_trends": {}  # 简化实现
        }
    
    async def _generate_insights(self, analysis_result: PatentAnalysisResult, enhanced_data: Optional[EnhancedData]) -> List[str]:
        """生成分析洞察."""
        insights = []
        
        # 趋势洞察
        if analysis_result.trend_analysis:
            trend = analysis_result.trend_analysis
            if trend.trend_direction == "increasing":
                insights.append(f"专利申请呈上升趋势，平均年增长率为 {trend.average_annual_growth:.1%}")
            elif trend.trend_direction == "decreasing":
                insights.append(f"专利申请呈下降趋势，需要关注技术发展放缓")
            else:
                insights.append("专利申请量保持相对稳定")
            
            if trend.peak_year:
                insights.append(f"{trend.peak_year}年是专利申请的峰值年份")
        
        # 技术洞察
        if analysis_result.tech_classification:
            tech = analysis_result.tech_classification
            if tech.main_technologies:
                main_tech = tech.main_technologies[0].split('(')[0].strip()
                insights.append(f"主要技术领域集中在 {main_tech}")
        
        # 竞争洞察
        if analysis_result.competition_analysis:
            comp = analysis_result.competition_analysis
            if comp.top_applicants:
                top_applicant = comp.top_applicants[0][0]
                insights.append(f"{top_applicant} 是该领域的主要专利申请人")
            
            if comp.market_concentration > 0.5:
                insights.append("市场集中度较高，存在明显的技术领导者")
            else:
                insights.append("市场竞争相对分散，技术发展多元化")
        
        return insights
    
    async def _generate_recommendations(self, analysis_result: PatentAnalysisResult, enhanced_data: Optional[EnhancedData]) -> List[str]:
        """生成建议."""
        recommendations = []
        
        # 基于趋势的建议
        if analysis_result.trend_analysis:
            if analysis_result.trend_analysis.trend_direction == "increasing":
                recommendations.append("建议加大研发投入，抓住技术发展机遇")
            elif analysis_result.trend_analysis.trend_direction == "decreasing":
                recommendations.append("建议关注新兴技术方向，寻找突破点")
        
        # 基于竞争的建议
        if analysis_result.competition_analysis:
            if analysis_result.competition_analysis.market_concentration > 0.6:
                recommendations.append("市场集中度高，建议寻找细分领域机会")
            else:
                recommendations.append("市场竞争激烈，建议加强技术差异化")
        
        # 通用建议
        recommendations.extend([
            "建议持续监控专利动态，及时调整技术策略",
            "考虑建立专利预警机制，防范侵权风险",
            "加强国际专利布局，提升全球竞争力"
        ])
        
        return recommendations
    
    async def _evaluate_analysis_quality(self, analysis_result: PatentAnalysisResult, patent_dataset: PatentDataset) -> float:
        """评估分析质量."""
        quality_factors = []
        
        # 数据完整性
        complete_patents = sum(1 for p in patent_dataset.patents 
                             if p.application_number and p.title and p.applicants)
        data_completeness = complete_patents / len(patent_dataset.patents)
        quality_factors.append(data_completeness * 0.3)
        
        # 分析覆盖度
        analysis_coverage = 0
        if analysis_result.trend_analysis:
            analysis_coverage += 0.25
        if analysis_result.tech_classification:
            analysis_coverage += 0.25
        if analysis_result.competition_analysis:
            analysis_coverage += 0.25
        if analysis_result.geographic_analysis:
            analysis_coverage += 0.25
        quality_factors.append(analysis_coverage * 0.4)
        
        # 数据量充足性
        data_sufficiency = min(len(patent_dataset.patents) / 100, 1.0)  # 100个专利为满分
        quality_factors.append(data_sufficiency * 0.3)
        
        return sum(quality_factors)
    
    async def _generate_response_content(self, result: Dict[str, Any]) -> str:
        """生成分析响应内容."""
        if result.get("status") == "completed":
            total_patents = result.get("total_patents_analyzed", 0)
            quality_score = result.get("quality_score", 0.0)
            processing_time = result.get("processing_time", 0.0)
            insights = result.get("insights", [])
            recommendations = result.get("recommendations", [])
            
            content = f"""专利分析已完成！

📊 分析概况:
• 分析专利数量: {total_patents}
• 分析质量评分: {quality_score:.2f}/1.0
• 处理时间: {processing_time:.1f}秒

🔍 关键洞察:
"""
            for i, insight in enumerate(insights[:3], 1):
                content += f"{i}. {insight}\n"
            
            content += f"""
💡 建议:
"""
            for i, rec in enumerate(recommendations[:3], 1):
                content += f"{i}. {rec}\n"
            
            content += "\n详细分析报告已生成，可进行进一步的报告生成和可视化。"
            
            return content
        
        elif result.get("status") == "failed":
            error = result.get("error", "未知错误")
            return f"专利分析失败: {error}"
        
        else:
            return f"专利分析状态: {result.get('status', 'unknown')}"