"""Patent analysis agent implementation."""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import re

from .base import PatentBaseAgent
from .trend_analyzer import TrendAnalyzer
from .tech_classifier import TechClassifier
from .competition_analyzer import CompetitionAnalyzer
from .quality_controller import AnalysisQualityController
from ...models.base import UserRequest, AgentResponse, Action
from ...models.config import AgentConfig
from ...models.enums import AgentType
from ...services.model_client import BaseModelClient


logger = logging.getLogger(__name__)


class PatentAnalysisAgent(PatentBaseAgent):
    """专利分析处理Agent，负责深度分析专利数据并生成洞察."""
    
    def __init__(self, config: AgentConfig, model_client: BaseModelClient):
        """初始化专利分析Agent."""
        super().__init__(config, model_client)
        
        # 分析相关关键词
        self.analysis_keywords = [
            "分析", "趋势", "竞争", "技术", "发展", "预测", "洞察", "报告",
            "统计", "对比", "评估", "研究", "调研", "市场", "行业",
            "analysis", "trend", "competition", "technology", "development",
            "prediction", "insight", "report", "statistics", "comparison"
        ]
        
        # 初始化分析组件
        self.trend_analyzer = TrendAnalyzer()
        self.tech_classifier = TechClassifier()
        self.competition_analyzer = CompetitionAnalyzer()
        self.quality_controller = AnalysisQualityController()
        
        # 分析配置
        self.analysis_config = {
            "min_patents_for_trend": 5,
            "trend_analysis_years": 10,
            "top_applicants_limit": 20,
            "tech_clusters_limit": 15,
            "quality_threshold": 0.7
        }
    
    async def can_handle_request(self, request: UserRequest) -> float:
        """判断是否能处理分析相关请求."""
        # 先调用父类的专利相关判断
        base_confidence = await super().can_handle_request(request)
        
        content = request.content.lower()
        
        # 检查分析关键词
        analysis_matches = sum(1 for keyword in self.analysis_keywords if keyword in content)
        analysis_score = min(analysis_matches * 0.25, 0.7)
        
        # 检查分析特定模式
        analysis_patterns = [
            r"(分析|研究).*?(专利|技术|趋势)",
            r"(统计|对比).*?(申请|发明|专利)",
            r"(竞争|市场).*?(分析|格局|态势)",
            r"(技术|行业).*?(发展|趋势|方向)",
            r"(analysis|research).*?(patent|technology|trend)",
            r"(statistics|comparison).*?(application|invention|patent)",
            r"(competition|market).*?(analysis|landscape|situation)"
        ]
        
        pattern_score = 0
        for pattern in analysis_patterns:
            if re.search(pattern, content):
                pattern_score += 0.2
        
        # 综合评分
        total_score = min(base_confidence + analysis_score + pattern_score, 1.0)
        
        return max(total_score, 0.0)
    
    async def get_capabilities(self) -> List[str]:
        """获取分析Agent的能力列表."""
        base_capabilities = await super().get_capabilities()
        analysis_capabilities = [
            "专利趋势分析",
            "技术分类统计",
            "竞争格局分析",
            "申请人分析",
            "地域分布分析",
            "时间序列分析",
            "技术聚类分析",
            "市场集中度计算",
            "分析结果质量控制"
        ]
        return base_capabilities + analysis_capabilities
    
    async def estimate_processing_time(self, request: UserRequest) -> int:
        """估算分析处理时间."""
        content = request.content.lower()
        
        # 简单分析：30-45秒
        if any(word in content for word in ["简单", "基础", "概览"]):
            return 35
        
        # 深度分析：60-90秒
        if any(word in content for word in ["深度", "详细", "全面", "完整"]):
            return 75
        
        # 复杂分析：90-120秒
        if any(word in content for word in ["复杂", "多维", "综合", "系统"]):
            return 105
        
        # 默认分析时间
        return 60
    
    async def _process_request_specific(self, request: UserRequest) -> AgentResponse:
        """处理分析相关的具体请求."""
        start_time = datetime.now()
        
        try:
            # 解析分析请求
            analysis_params = self._parse_analysis_request(request.content)
            
            # 检查缓存
            cache_key = self._generate_analysis_cache_key(analysis_params)
            cached_result = await self.get_from_cache(cache_key)
            
            if cached_result:
                self.logger.info("Returning cached analysis results")
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
            
            # 获取专利数据（模拟从数据收集Agent获取）
            patent_data = await self._get_patent_data_for_analysis(analysis_params)
            
            if not patent_data or len(patent_data) < self.analysis_config["min_patents_for_trend"]:
                return AgentResponse(
                    agent_id=self.agent_id,
                    agent_type=self.agent_type,
                    response_content="数据量不足，无法进行有效分析。建议扩大搜索范围或调整关键词。",
                    confidence=0.3,
                    collaboration_needed=True,
                    metadata={"insufficient_data": True, "data_count": len(patent_data) if patent_data else 0}
                )
            
            # 执行分析
            analysis_results = await self._execute_comprehensive_analysis(patent_data, analysis_params)
            
            # 质量控制
            quality_report = await self.quality_controller.validate_analysis_results(analysis_results)
            
            if quality_report["overall_quality"] < self.analysis_config["quality_threshold"]:
                self.logger.warning(f"Analysis quality below threshold: {quality_report['overall_quality']}")
                # 尝试改进分析
                analysis_results = await self._improve_analysis_quality(analysis_results, quality_report)
            
            # 生成响应内容
            response_content = await self._generate_analysis_response(analysis_results, analysis_params)
            
            # 生成后续动作
            next_actions = self._generate_analysis_actions(analysis_results)
            
            # 缓存结果
            result_data = {
                "response_content": response_content,
                "metadata": {
                    "analysis_params": analysis_params,
                    "data_count": len(patent_data),
                    "processing_time": (datetime.now() - start_time).total_seconds(),
                    "quality_score": quality_report["overall_quality"],
                    "analysis_types": list(analysis_results.keys())
                }
            }
            await self.save_to_cache(cache_key, result_data)
            
            # 记录性能指标
            duration = (datetime.now() - start_time).total_seconds()
            self.log_performance_metrics("analysis", duration, True)
            
            # 集成现有监控系统记录分析指标
            await self._log_analysis_metrics(analysis_params, analysis_results, duration)
            
            return AgentResponse(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                response_content=response_content,
                confidence=0.85,
                next_actions=next_actions,
                collaboration_needed=False,
                metadata=result_data["metadata"]
            )
            
        except Exception as e:
            self.logger.error(f"Error processing analysis request: {str(e)}")
            
            # 记录失败指标
            duration = (datetime.now() - start_time).total_seconds()
            self.log_performance_metrics("analysis", duration, False)
            
            return AgentResponse(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                response_content=f"分析过程中发生错误: {str(e)}。请稍后重试或联系技术支持。",
                confidence=0.0,
                collaboration_needed=True,
                metadata={
                    "error": str(e),
                    "processing_time": duration
                }
            )
    
    def _parse_analysis_request(self, content: str) -> Dict[str, Any]:
        """解析分析请求参数."""
        params = {
            "analysis_types": ["trend", "competition", "technology"],
            "keywords": [],
            "time_range": {"start_year": 2014, "end_year": 2024},
            "focus_areas": [],
            "depth": "standard"
        }
        
        content_lower = content.lower()
        
        # 提取关键词
        keywords = []
        quoted_keywords = re.findall(r'["""\'](.*?)["""\']', content)
        keywords.extend(quoted_keywords)
        
        # 技术领域关键词
        tech_patterns = [
            r'(人工智能|AI|机器学习|深度学习)',
            r'(区块链|blockchain)',
            r'(物联网|IoT)',
            r'(5G|通信技术)',
            r'(新能源|电池技术)',
            r'(生物技术|基因)',
            r'(芯片|半导体)',
        ]
        
        for pattern in tech_patterns:
            matches = re.findall(pattern, content)
            keywords.extend(matches)
        
        if not keywords:
            stop_words = {"的", "了", "在", "是", "有", "和", "与", "或", "但", "等", "分析", "专利"}
            words = content.split()
            keywords = [word for word in words if len(word) > 1 and word not in stop_words]
        
        params["keywords"] = keywords[:5]
        
        # 判断分析类型
        if any(word in content_lower for word in ["趋势", "发展", "变化", "trend"]):
            if "trend" not in params["analysis_types"]:
                params["analysis_types"].append("trend")
        
        if any(word in content_lower for word in ["竞争", "申请人", "公司", "competition"]):
            if "competition" not in params["analysis_types"]:
                params["analysis_types"].append("competition")
        
        if any(word in content_lower for word in ["技术", "分类", "ipc", "technology"]):
            if "technology" not in params["analysis_types"]:
                params["analysis_types"].append("technology")
        
        if any(word in content_lower for word in ["地域", "国家", "地区", "geographic"]):
            params["analysis_types"].append("geographic")
        
        # 判断分析深度
        if any(word in content_lower for word in ["深度", "详细", "全面", "comprehensive"]):
            params["depth"] = "deep"
        elif any(word in content_lower for word in ["简单", "概览", "基础", "basic"]):
            params["depth"] = "basic"
        
        # 提取时间范围
        year_matches = re.findall(r'(\d{4})', content)
        if len(year_matches) >= 2:
            years = [int(y) for y in year_matches if 2000 <= int(y) <= 2024]
            if len(years) >= 2:
                params["time_range"]["start_year"] = min(years)
                params["time_range"]["end_year"] = max(years)
        
        return params
    
    def _generate_analysis_cache_key(self, analysis_params: Dict[str, Any]) -> str:
        """生成分析缓存键."""
        key_parts = [
            "analysis",
            "_".join(sorted(analysis_params["keywords"])),
            "_".join(sorted(analysis_params["analysis_types"])),
            f"{analysis_params['time_range']['start_year']}-{analysis_params['time_range']['end_year']}",
            analysis_params["depth"]
        ]
        return "_".join(key_parts).replace(" ", "_")
    
    async def _get_patent_data_for_analysis(self, analysis_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """获取用于分析的专利数据（模拟从数据收集Agent获取）."""
        # 这里应该调用专利数据收集Agent或从缓存/数据库获取数据
        # 现在提供模拟数据用于演示
        
        keywords = analysis_params.get("keywords", ["技术"])
        start_year = analysis_params["time_range"]["start_year"]
        end_year = analysis_params["time_range"]["end_year"]
        
        # 模拟专利数据
        mock_patents = []
        
        # 生成模拟的专利数据
        applicants = [
            "华为技术有限公司", "腾讯科技", "阿里巴巴", "百度", "字节跳动",
            "Apple Inc.", "Google LLC", "Microsoft Corporation", "Samsung Electronics",
            "IBM Corporation", "Intel Corporation", "NVIDIA Corporation"
        ]
        
        ipc_classes = [
            "G06F", "H04L", "G06N", "H04W", "G06Q", "H01L", "G06K", "H04N", "G06T", "G01S"
        ]
        
        countries = ["CN", "US", "JP", "KR", "DE", "GB", "FR"]
        
        import random
        random.seed(42)  # 确保结果可重现
        
        for i in range(100):  # 生成100个模拟专利
            year = random.randint(start_year, end_year)
            month = random.randint(1, 12)
            day = random.randint(1, 28)
            
            patent = {
                "application_number": f"CN{year}{i:06d}",
                "title": f"关于{keywords[0] if keywords else '技术'}的{random.choice(['方法', '系统', '装置', '算法'])} {i+1}",
                "abstract": f"本发明涉及{keywords[0] if keywords else '技术'}领域，提供了一种新的解决方案...",
                "applicants": [random.choice(applicants)],
                "inventors": [f"发明人{i+1}", f"发明人{i+2}"],
                "application_date": f"{year}-{month:02d}-{day:02d}",
                "publication_date": f"{year}-{month+6 if month <= 6 else month-6:02d}-{day:02d}",
                "ipc_classes": [random.choice(ipc_classes)],
                "country": random.choice(countries),
                "status": random.choice(["已授权", "审查中", "已公开"])
            }
            mock_patents.append(patent)
        
        self.logger.info(f"Generated {len(mock_patents)} mock patents for analysis")
        return mock_patents
    
    async def _execute_comprehensive_analysis(self, patent_data: List[Dict[str, Any]], analysis_params: Dict[str, Any]) -> Dict[str, Any]:
        """执行综合分析."""
        results = {}
        
        try:
            # 并行执行不同类型的分析
            analysis_tasks = []
            
            if "trend" in analysis_params["analysis_types"]:
                analysis_tasks.append(("trend", self.trend_analyzer.analyze_trends(patent_data, analysis_params)))
            
            if "technology" in analysis_params["analysis_types"]:
                analysis_tasks.append(("technology", self.tech_classifier.classify_technologies(patent_data, analysis_params)))
            
            if "competition" in analysis_params["analysis_types"]:
                analysis_tasks.append(("competition", self.competition_analyzer.analyze_competition(patent_data, analysis_params)))
            
            if "geographic" in analysis_params["analysis_types"]:
                analysis_tasks.append(("geographic", self._analyze_geographic_distribution(patent_data)))
            
            # 等待所有分析完成
            completed_analyses = await asyncio.gather(
                *[task for _, task in analysis_tasks],
                return_exceptions=True
            )
            
            # 处理分析结果
            for i, (analysis_type, _) in enumerate(analysis_tasks):
                result = completed_analyses[i]
                if isinstance(result, Exception):
                    self.logger.error(f"Analysis {analysis_type} failed: {str(result)}")
                    results[analysis_type] = {"error": str(result), "success": False}
                else:
                    results[analysis_type] = result
                    results[analysis_type]["success"] = True
            
            # 生成综合洞察
            if len([r for r in results.values() if r.get("success", False)]) >= 2:
                results["insights"] = await self._generate_comprehensive_insights(results, patent_data)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive analysis: {str(e)}")
            return {"error": str(e), "success": False}
    
    async def _analyze_geographic_distribution(self, patent_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析地域分布."""
        try:
            country_counts = defaultdict(int)
            
            for patent in patent_data:
                country = patent.get("country", "Unknown")
                country_counts[country] += 1
            
            # 计算百分比
            total_patents = len(patent_data)
            country_percentages = {
                country: (count / total_patents) * 100
                for country, count in country_counts.items()
            }
            
            # 排序
            sorted_countries = sorted(
                country_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            return {
                "country_distribution": dict(country_counts),
                "country_percentages": country_percentages,
                "top_countries": sorted_countries[:10],
                "total_countries": len(country_counts),
                "analysis_summary": f"专利申请主要集中在{sorted_countries[0][0]}等{len(country_counts)}个国家/地区"
            }
            
        except Exception as e:
            self.logger.error(f"Error in geographic analysis: {str(e)}")
            return {"error": str(e)}
    
    async def _generate_comprehensive_insights(self, analysis_results: Dict[str, Any], patent_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成综合洞察."""
        insights = {
            "key_findings": [],
            "trends": [],
            "recommendations": [],
            "risk_factors": []
        }
        
        try:
            # 基于趋势分析的洞察
            if "trend" in analysis_results and analysis_results["trend"].get("success"):
                trend_data = analysis_results["trend"]
                if trend_data.get("trend_direction") == "increasing":
                    insights["key_findings"].append("该技术领域专利申请量呈上升趋势，显示出强劲的创新活力")
                    insights["trends"].append("技术发展处于快速增长期")
                elif trend_data.get("trend_direction") == "decreasing":
                    insights["key_findings"].append("专利申请量呈下降趋势，可能表明技术成熟或市场饱和")
                    insights["risk_factors"].append("技术发展可能进入平台期或衰退期")
            
            # 基于竞争分析的洞察
            if "competition" in analysis_results and analysis_results["competition"].get("success"):
                comp_data = analysis_results["competition"]
                market_concentration = comp_data.get("market_concentration", 0)
                
                if market_concentration > 0.7:
                    insights["key_findings"].append("市场集中度较高，少数企业占据主导地位")
                    insights["risk_factors"].append("市场竞争激烈，新进入者面临较高壁垒")
                elif market_concentration < 0.3:
                    insights["key_findings"].append("市场相对分散，竞争格局较为开放")
                    insights["recommendations"].append("适合新技术企业进入和发展")
            
            # 基于技术分析的洞察
            if "technology" in analysis_results and analysis_results["technology"].get("success"):
                tech_data = analysis_results["technology"]
                main_techs = tech_data.get("main_technologies", [])
                
                if main_techs:
                    insights["trends"].append(f"主要技术方向集中在{', '.join(main_techs[:3])}等领域")
                    insights["recommendations"].append("建议重点关注主流技术方向的发展机会")
            
            # 综合建议
            insights["recommendations"].extend([
                "持续监控技术发展趋势和竞争动态",
                "关注主要竞争对手的专利布局策略",
                "结合市场需求制定差异化技术路线"
            ])
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating insights: {str(e)}")
            return {"error": str(e)}
    
    async def _improve_analysis_quality(self, analysis_results: Dict[str, Any], quality_report: Dict[str, Any]) -> Dict[str, Any]:
        """改进分析质量."""
        try:
            # 根据质量报告改进分析结果
            improved_results = analysis_results.copy()
            
            # 如果数据完整性不足，添加数据质量说明
            if quality_report.get("data_completeness", 1.0) < 0.8:
                for analysis_type in improved_results:
                    if isinstance(improved_results[analysis_type], dict):
                        improved_results[analysis_type]["data_quality_note"] = "部分数据可能不完整，分析结果仅供参考"
            
            # 如果置信度较低，添加不确定性说明
            if quality_report.get("confidence_level", 1.0) < 0.7:
                for analysis_type in improved_results:
                    if isinstance(improved_results[analysis_type], dict):
                        improved_results[analysis_type]["uncertainty_note"] = "分析结果存在一定不确定性，建议结合其他信息源"
            
            return improved_results
            
        except Exception as e:
            self.logger.error(f"Error improving analysis quality: {str(e)}")
            return analysis_results
    
    async def _generate_analysis_response(self, analysis_results: Dict[str, Any], analysis_params: Dict[str, Any]) -> str:
        """生成分析响应内容."""
        try:
            response_parts = []
            
            # 添加分析概述
            keywords_str = "、".join(analysis_params.get("keywords", ["相关技术"]))
            time_range = analysis_params.get("time_range", {})
            start_year = time_range.get("start_year", 2014)
            end_year = time_range.get("end_year", 2024)
            
            response_parts.append(f"## 专利分析报告")
            response_parts.append(f"**分析主题**: {keywords_str}")
            response_parts.append(f"**时间范围**: {start_year}年-{end_year}年")
            response_parts.append("")
            
            # 添加各项分析结果
            if "trend" in analysis_results and analysis_results["trend"].get("success"):
                trend_data = analysis_results["trend"]
                response_parts.append("### 📈 趋势分析")
                response_parts.append(f"- **总体趋势**: {trend_data.get('trend_direction', '稳定')}")
                
                yearly_counts = trend_data.get("yearly_counts", {})
                if yearly_counts:
                    max_year = max(yearly_counts.keys(), key=lambda x: yearly_counts[x])
                    response_parts.append(f"- **峰值年份**: {max_year}年（{yearly_counts[max_year]}件）")
                
                growth_rates = trend_data.get("growth_rates", {})
                if growth_rates:
                    recent_years = sorted(growth_rates.keys())[-3:]
                    avg_growth = sum(growth_rates[year] for year in recent_years) / len(recent_years)
                    response_parts.append(f"- **近期增长率**: {avg_growth:.1f}%")
                
                response_parts.append("")
            
            if "competition" in analysis_results and analysis_results["competition"].get("success"):
                comp_data = analysis_results["competition"]
                response_parts.append("### 🏢 竞争分析")
                
                top_applicants = comp_data.get("top_applicants", [])
                if top_applicants:
                    response_parts.append("- **主要申请人**:")
                    for i, (applicant, count) in enumerate(top_applicants[:5]):
                        response_parts.append(f"  {i+1}. {applicant}: {count}件")
                
                market_concentration = comp_data.get("market_concentration", 0)
                response_parts.append(f"- **市场集中度**: {market_concentration:.2f}")
                
                response_parts.append("")
            
            if "technology" in analysis_results and analysis_results["technology"].get("success"):
                tech_data = analysis_results["technology"]
                response_parts.append("### 🔬 技术分析")
                
                main_technologies = tech_data.get("main_technologies", [])
                if main_technologies:
                    response_parts.append("- **主要技术领域**:")
                    for tech in main_technologies[:5]:
                        response_parts.append(f"  • {tech}")
                
                ipc_distribution = tech_data.get("ipc_distribution", {})
                if ipc_distribution:
                    top_ipc = sorted(ipc_distribution.items(), key=lambda x: x[1], reverse=True)[:3]
                    response_parts.append("- **主要IPC分类**:")
                    for ipc, count in top_ipc:
                        response_parts.append(f"  • {ipc}: {count}件")
                
                response_parts.append("")
            
            if "geographic" in analysis_results and analysis_results["geographic"].get("success"):
                geo_data = analysis_results["geographic"]
                response_parts.append("### 🌍 地域分析")
                
                top_countries = geo_data.get("top_countries", [])
                if top_countries:
                    response_parts.append("- **主要申请国家/地区**:")
                    for country, count in top_countries[:5]:
                        percentage = geo_data.get("country_percentages", {}).get(country, 0)
                        response_parts.append(f"  • {country}: {count}件 ({percentage:.1f}%)")
                
                response_parts.append("")
            
            # 添加综合洞察
            if "insights" in analysis_results:
                insights = analysis_results["insights"]
                response_parts.append("### 💡 关键洞察")
                
                key_findings = insights.get("key_findings", [])
                for finding in key_findings:
                    response_parts.append(f"- {finding}")
                
                if insights.get("recommendations"):
                    response_parts.append("\n### 📋 建议")
                    for rec in insights["recommendations"]:
                        response_parts.append(f"- {rec}")
                
                if insights.get("risk_factors"):
                    response_parts.append("\n### ⚠️ 风险因素")
                    for risk in insights["risk_factors"]:
                        response_parts.append(f"- {risk}")
            
            # 添加数据质量说明
            response_parts.append("\n---")
            response_parts.append("*本分析基于专利数据库信息，结果仅供参考。建议结合市场调研等其他信息源进行综合判断。*")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            self.logger.error(f"Error generating analysis response: {str(e)}")
            return f"分析报告生成过程中发生错误: {str(e)}"
    
    def _generate_analysis_actions(self, analysis_results: Dict[str, Any]) -> List[Action]:
        """生成分析后续动作."""
        actions = []
        
        try:
            # 基础后续动作
            actions.append(Action(
                action_type="generate_detailed_report",
                parameters={"format": "pdf", "include_charts": True},
                description="生成详细的PDF分析报告"
            ))
            
            actions.append(Action(
                action_type="export_data",
                parameters={"format": "excel", "include_raw_data": True},
                description="导出分析数据到Excel"
            ))
            
            # 基于分析结果的特定动作
            if "trend" in analysis_results and analysis_results["trend"].get("success"):
                actions.append(Action(
                    action_type="trend_monitoring",
                    parameters={"frequency": "monthly", "alert_threshold": 0.2},
                    description="设置趋势监控和预警"
                ))
            
            if "competition" in analysis_results and analysis_results["competition"].get("success"):
                actions.append(Action(
                    action_type="competitor_tracking",
                    parameters={"top_competitors": 5, "update_frequency": "weekly"},
                    description="跟踪主要竞争对手动态"
                ))
            
            return actions
            
        except Exception as e:
            self.logger.error(f"Error generating analysis actions: {str(e)}")
            return []
    
    async def _log_analysis_metrics(self, analysis_params: Dict[str, Any], analysis_results: Dict[str, Any], duration: float):
        """记录分析指标到监控系统."""
        try:
            # 这里应该集成到现有的MonitoringSystem
            metrics = {
                "analysis_duration": duration,
                "analysis_types": len(analysis_params.get("analysis_types", [])),
                "keywords_count": len(analysis_params.get("keywords", [])),
                "successful_analyses": len([r for r in analysis_results.values() if isinstance(r, dict) and r.get("success", False)]),
                "failed_analyses": len([r for r in analysis_results.values() if isinstance(r, dict) and not r.get("success", True)]),
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"Analysis metrics: {json.dumps(metrics, ensure_ascii=False)}")
            
        except Exception as e:
            self.logger.error(f"Error logging analysis metrics: {str(e)}")


class TrendAnalyzer:
    """趋势分析器，实现时间序列分析."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.TrendAnalyzer")
    
    async def analyze_trends(self, patent_data: List[Dict[str, Any]], analysis_params: Dict[str, Any]) -> Dict[str, Any]:
        """分析专利申请趋势."""
        try:
            # 按年份统计申请量
            yearly_counts = defaultdict(int)
            
            for patent in patent_data:
                app_date = patent.get("application_date", "")
                if app_date:
                    try:
                        year = int(app_date.split("-")[0])
                        yearly_counts[year] += 1
                    except (ValueError, IndexError):
                        continue
            
            if not yearly_counts:
                return {"error": "无法提取有效的申请日期信息"}
            
            # 计算增长率
            growth_rates = self._calculate_growth_rates(yearly_counts)
            
            # 判断趋势方向
            trend_direction = self._determine_trend_direction(growth_rates)
            
            # 预测未来趋势
            future_prediction = self._predict_future_trend(yearly_counts, growth_rates)
            
            return {
                "yearly_counts": dict(yearly_counts),
                "growth_rates": growth_rates,
                "trend_direction": trend_direction,
                "future_prediction": future_prediction,
                "analysis_summary": self._generate_trend_summary(yearly_counts, growth_rates, trend_direction)
            }
            
        except Exception as e:
            self.logger.error(f"Error in trend analysis: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_growth_rates(self, yearly_counts: Dict[int, int]) -> Dict[int, float]:
        """计算年度增长率."""
        growth_rates = {}
        sorted_years = sorted(yearly_counts.keys())
        
        for i in range(1, len(sorted_years)):
            prev_year = sorted_years[i-1]
            curr_year = sorted_years[i]
            
            prev_count = yearly_counts[prev_year]
            curr_count = yearly_counts[curr_year]
            
            if prev_count > 0:
                growth_rate = ((curr_count - prev_count) / prev_count) * 100
                growth_rates[curr_year] = growth_rate
            else:
                growth_rates[curr_year] = 0.0
        
        return growth_rates
    
    def _determine_trend_direction(self, growth_rates: Dict[int, float]) -> str:
        """判断趋势方向."""
        if not growth_rates:
            return "stable"
        
        recent_rates = list(growth_rates.values())[-3:]  # 最近3年的增长率
        avg_growth = sum(recent_rates) / len(recent_rates)
        
        if avg_growth > 10:
            return "rapidly_increasing"
        elif avg_growth > 0:
            return "increasing"
        elif avg_growth > -10:
            return "stable"
        else:
            return "decreasing"
    
    def _predict_future_trend(self, yearly_counts: Dict[int, int], growth_rates: Dict[int, float]) -> Dict[str, Any]:
        """预测未来趋势."""
        try:
            if not yearly_counts or not growth_rates:
                return {"prediction": "insufficient_data"}
            
            # 简单的线性预测
            recent_years = sorted(yearly_counts.keys())[-3:]
            recent_counts = [yearly_counts[year] for year in recent_years]
            
            if len(recent_counts) >= 2:
                # 计算平均增长
                avg_change = (recent_counts[-1] - recent_counts[0]) / (len(recent_counts) - 1)
                
                # 预测下一年
                next_year = max(yearly_counts.keys()) + 1
                predicted_count = max(0, int(recent_counts[-1] + avg_change))
                
                return {
                    "next_year": next_year,
                    "predicted_count": predicted_count,
                    "confidence": "medium",
                    "method": "linear_trend"
                }
            
            return {"prediction": "insufficient_data"}
            
        except Exception as e:
            self.logger.error(f"Error in trend prediction: {str(e)}")
            return {"prediction": "error", "error": str(e)}
    
    def _generate_trend_summary(self, yearly_counts: Dict[int, int], growth_rates: Dict[int, float], trend_direction: str) -> str:
        """生成趋势分析摘要."""
        try:
            total_patents = sum(yearly_counts.values())
            years_span = max(yearly_counts.keys()) - min(yearly_counts.keys()) + 1
            
            direction_desc = {
                "rapidly_increasing": "快速增长",
                "increasing": "稳步增长", 
                "stable": "相对稳定",
                "decreasing": "下降趋势"
            }
            
            return f"在{years_span}年期间共有{total_patents}件专利申请，整体呈{direction_desc.get(trend_direction, '未知')}态势。"
            
        except Exception as e:
            return f"趋势分析摘要生成失败: {str(e)}"


class TechClassifier:
    """技术分类器，实现IPC分类统计和技术聚类."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.TechClassifier")
    
    async def classify_technologies(self, patent_data: List[Dict[str, Any]], analysis_params: Dict[str, Any]) -> Dict[str, Any]:
        """分析技术分类分布."""
        try:
            # IPC分类统计
            ipc_counts = defaultdict(int)
            
            for patent in patent_data:
                ipc_classes = patent.get("ipc_classes", [])
                for ipc in ipc_classes:
                    # 提取主分类（前4位）
                    main_ipc = ipc[:4] if len(ipc) >= 4 else ipc
                    ipc_counts[main_ipc] += 1
            
            # 关键词提取和聚类
            keywords = self._extract_technology_keywords(patent_data)
            tech_clusters = self._cluster_technologies(keywords)
            
            # 识别主要技术领域
            main_technologies = self._identify_main_technologies(ipc_counts, tech_clusters)
            
            return {
                "ipc_distribution": dict(ipc_counts),
                "keyword_clusters": tech_clusters,
                "main_technologies": main_technologies,
                "technology_diversity": len(ipc_counts),
                "analysis_summary": self._generate_tech_summary(ipc_counts, main_technologies)
            }
            
        except Exception as e:
            self.logger.error(f"Error in technology classification: {str(e)}")
            return {"error": str(e)}
    
    def _extract_technology_keywords(self, patent_data: List[Dict[str, Any]]) -> List[str]:
        """提取技术关键词."""
        keywords = []
        
        # 技术相关的关键词模式
        tech_patterns = [
            r'(人工智能|机器学习|深度学习|神经网络)',
            r'(区块链|分布式|加密|哈希)',
            r'(物联网|传感器|无线|通信)',
            r'(大数据|数据挖掘|数据分析)',
            r'(云计算|边缘计算|分布式计算)',
            r'(5G|通信|网络|协议)',
            r'(芯片|半导体|集成电路)',
            r'(新能源|电池|太阳能|风能)',
            r'(生物技术|基因|蛋白质|医疗)',
            r'(自动驾驶|智能汽车|导航)'
        ]
        
        for patent in patent_data:
            title = patent.get("title", "")
            abstract = patent.get("abstract", "")
            text = f"{title} {abstract}"
            
            for pattern in tech_patterns:
                matches = re.findall(pattern, text)
                keywords.extend(matches)
        
        return keywords
    
    def _cluster_technologies(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """技术聚类分析."""
        try:
            # 简单的关键词频次聚类
            keyword_counts = defaultdict(int)
            for keyword in keywords:
                keyword_counts[keyword] += 1
            
            # 按频次分组
            clusters = []
            
            # 高频技术（出现5次以上）
            high_freq = {k: v for k, v in keyword_counts.items() if v >= 5}
            if high_freq:
                clusters.append({
                    "cluster_name": "核心技术",
                    "keywords": list(high_freq.keys()),
                    "frequency": sum(high_freq.values()),
                    "importance": "high"
                })
            
            # 中频技术（出现2-4次）
            mid_freq = {k: v for k, v in keyword_counts.items() if 2 <= v < 5}
            if mid_freq:
                clusters.append({
                    "cluster_name": "重要技术",
                    "keywords": list(mid_freq.keys()),
                    "frequency": sum(mid_freq.values()),
                    "importance": "medium"
                })
            
            # 新兴技术（出现1次）
            low_freq = {k: v for k, v in keyword_counts.items() if v == 1}
            if low_freq:
                clusters.append({
                    "cluster_name": "新兴技术",
                    "keywords": list(low_freq.keys())[:10],  # 限制数量
                    "frequency": sum(low_freq.values()),
                    "importance": "low"
                })
            
            return clusters
            
        except Exception as e:
            self.logger.error(f"Error in technology clustering: {str(e)}")
            return []
    
    def _identify_main_technologies(self, ipc_counts: Dict[str, int], tech_clusters: List[Dict[str, Any]]) -> List[str]:
        """识别主要技术领域."""
        main_techs = []
        
        # 基于IPC分类识别
        ipc_mapping = {
            "G06F": "计算机技术",
            "H04L": "通信技术", 
            "G06N": "人工智能",
            "H04W": "无线通信",
            "G06Q": "商业方法",
            "H01L": "半导体技术",
            "G06K": "图像识别",
            "H04N": "图像通信",
            "G06T": "图像处理",
            "G01S": "定位技术"
        }
        
        # 获取前5个IPC分类
        top_ipcs = sorted(ipc_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        for ipc, count in top_ipcs:
            tech_name = ipc_mapping.get(ipc, f"技术领域{ipc}")
            main_techs.append(tech_name)
        
        # 基于技术聚类补充
        for cluster in tech_clusters:
            if cluster.get("importance") == "high":
                main_techs.extend(cluster.get("keywords", [])[:2])
        
        return list(set(main_techs))[:10]  # 去重并限制数量
    
    def _generate_tech_summary(self, ipc_counts: Dict[str, int], main_technologies: List[str]) -> str:
        """生成技术分析摘要."""
        try:
            total_classes = len(ipc_counts)
            main_tech_str = "、".join(main_technologies[:3])
            
            return f"涉及{total_classes}个主要技术分类，主要集中在{main_tech_str}等领域。"
            
        except Exception as e:
            return f"技术分析摘要生成失败: {str(e)}"


class CompetitionAnalyzer:
    """竞争分析器，进行申请人分析和市场集中度计算."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.CompetitionAnalyzer")
    
    async def analyze_competition(self, patent_data: List[Dict[str, Any]], analysis_params: Dict[str, Any]) -> Dict[str, Any]:
        """分析竞争格局."""
        try:
            # 申请人统计
            applicant_counts = defaultdict(int)
            
            for patent in patent_data:
                applicants = patent.get("applicants", [])
                for applicant in applicants:
                    # 清理申请人名称
                    clean_name = self._clean_applicant_name(applicant)
                    applicant_counts[clean_name] += 1
            
            # 排序获取主要申请人
            top_applicants = sorted(
                applicant_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:20]
            
            # 计算市场集中度
            market_concentration = self._calculate_market_concentration(applicant_counts)
            
            # 分析竞争格局
            competition_landscape = self._analyze_competition_landscape(applicant_counts, top_applicants)
            
            return {
                "applicant_distribution": dict(applicant_counts),
                "top_applicants": top_applicants,
                "market_concentration": market_concentration,
                "competition_landscape": competition_landscape,
                "total_applicants": len(applicant_counts),
                "analysis_summary": self._generate_competition_summary(top_applicants, market_concentration)
            }
            
        except Exception as e:
            self.logger.error(f"Error in competition analysis: {str(e)}")
            return {"error": str(e)}
    
    def _clean_applicant_name(self, applicant: str) -> str:
        """清理申请人名称."""
        # 移除常见的公司后缀变体
        suffixes = [
            "有限公司", "股份有限公司", "科技有限公司", "技术有限公司",
            "Inc.", "LLC", "Corporation", "Corp.", "Ltd.", "Co.", "Company"
        ]
        
        clean_name = applicant.strip()
        for suffix in suffixes:
            if clean_name.endswith(suffix):
                clean_name = clean_name[:-len(suffix)].strip()
        
        return clean_name
    
    def _calculate_market_concentration(self, applicant_counts: Dict[str, int]) -> float:
        """计算市场集中度（HHI指数）."""
        try:
            total_patents = sum(applicant_counts.values())
            if total_patents == 0:
                return 0.0
            
            # 计算HHI指数
            hhi = sum((count / total_patents) ** 2 for count in applicant_counts.values())
            
            return hhi
            
        except Exception as e:
            self.logger.error(f"Error calculating market concentration: {str(e)}")
            return 0.0
    
    def _analyze_competition_landscape(self, applicant_counts: Dict[str, int], top_applicants: List[tuple]) -> Dict[str, Any]:
        """分析竞争格局."""
        try:
            total_patents = sum(applicant_counts.values())
            
            # 计算前N名申请人的市场份额
            top5_share = sum(count for _, count in top_applicants[:5]) / total_patents if total_patents > 0 else 0
            top10_share = sum(count for _, count in top_applicants[:10]) / total_patents if total_patents > 0 else 0
            
            # 判断竞争格局类型
            if top5_share > 0.8:
                landscape_type = "高度集中"
            elif top5_share > 0.6:
                landscape_type = "中度集中"
            elif top5_share > 0.4:
                landscape_type = "适度竞争"
            else:
                landscape_type = "充分竞争"
            
            # 识别主要竞争者类型
            competitor_types = self._classify_competitors(top_applicants[:10])
            
            return {
                "landscape_type": landscape_type,
                "top5_market_share": top5_share,
                "top10_market_share": top10_share,
                "competitor_types": competitor_types,
                "competition_intensity": self._assess_competition_intensity(top5_share, len(applicant_counts))
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing competition landscape: {str(e)}")
            return {}
    
    def _classify_competitors(self, top_applicants: List[tuple]) -> Dict[str, List[str]]:
        """分类竞争者类型."""
        competitor_types = {
            "大型企业": [],
            "科技公司": [],
            "研究机构": [],
            "其他": []
        }
        
        # 简单的分类规则
        for applicant, count in top_applicants:
            applicant_lower = applicant.lower()
            
            if any(keyword in applicant_lower for keyword in ["大学", "学院", "研究院", "科学院", "university", "institute"]):
                competitor_types["研究机构"].append(applicant)
            elif any(keyword in applicant_lower for keyword in ["科技", "技术", "technology", "tech"]):
                competitor_types["科技公司"].append(applicant)
            elif any(keyword in applicant_lower for keyword in ["集团", "控股", "group", "holdings"]):
                competitor_types["大型企业"].append(applicant)
            else:
                competitor_types["其他"].append(applicant)
        
        return competitor_types
    
    def _assess_competition_intensity(self, top5_share: float, total_competitors: int) -> str:
        """评估竞争激烈程度."""
        if top5_share > 0.7 and total_competitors < 20:
            return "低"
        elif top5_share > 0.5 and total_competitors < 50:
            return "中等"
        elif top5_share < 0.3 and total_competitors > 100:
            return "激烈"
        else:
            return "中等"
    
    def _generate_competition_summary(self, top_applicants: List[tuple], market_concentration: float) -> str:
        """生成竞争分析摘要."""
        try:
            if not top_applicants:
                return "竞争分析数据不足"
            
            top_applicant = top_applicants[0][0]
            top_count = top_applicants[0][1]
            
            concentration_desc = "高" if market_concentration > 0.5 else "中" if market_concentration > 0.2 else "低"
            
            return f"市场集中度{concentration_desc}，{top_applicant}以{top_count}件专利领先，共有{len(top_applicants)}个主要竞争者。"
            
        except Exception as e:
            return f"竞争分析摘要生成失败: {str(e)}"


class AnalysisQualityController:
    """分析结果质量控制系统."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.AnalysisQualityController")
    
    async def validate_analysis_results(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """验证分析结果质量."""
        try:
            quality_report = {
                "overall_quality": 0.0,
                "data_completeness": 0.0,
                "confidence_level": 0.0,
                "consistency_score": 0.0,
                "issues": [],
                "recommendations": []
            }
            
            # 检查数据完整性
            completeness_score = self._check_data_completeness(analysis_results)
            quality_report["data_completeness"] = completeness_score
            
            # 检查置信度
            confidence_score = self._check_confidence_level(analysis_results)
            quality_report["confidence_level"] = confidence_score
            
            # 检查一致性
            consistency_score = self._check_consistency(analysis_results)
            quality_report["consistency_score"] = consistency_score
            
            # 计算总体质量分数
            quality_report["overall_quality"] = (
                completeness_score * 0.4 +
                confidence_score * 0.3 +
                consistency_score * 0.3
            )
            
            # 生成问题和建议
            quality_report["issues"] = self._identify_quality_issues(analysis_results, quality_report)
            quality_report["recommendations"] = self._generate_quality_recommendations(quality_report)
            
            return quality_report
            
        except Exception as e:
            self.logger.error(f"Error validating analysis results: {str(e)}")
            return {
                "overall_quality": 0.0,
                "error": str(e)
            }
    
    def _check_data_completeness(self, analysis_results: Dict[str, Any]) -> float:
        """检查数据完整性."""
        try:
            required_analyses = ["trend", "competition", "technology"]
            completed_analyses = 0
            
            for analysis_type in required_analyses:
                if analysis_type in analysis_results and analysis_results[analysis_type].get("success", False):
                    completed_analyses += 1
            
            return completed_analyses / len(required_analyses)
            
        except Exception:
            return 0.0
    
    def _check_confidence_level(self, analysis_results: Dict[str, Any]) -> float:
        """检查置信度水平."""
        try:
            confidence_scores = []
            
            for analysis_type, result in analysis_results.items():
                if isinstance(result, dict) and result.get("success", False):
                    # 基于数据量和结果完整性评估置信度
                    if analysis_type == "trend":
                        yearly_data = result.get("yearly_counts", {})
                        if len(yearly_data) >= 5:
                            confidence_scores.append(0.8)
                        elif len(yearly_data) >= 3:
                            confidence_scores.append(0.6)
                        else:
                            confidence_scores.append(0.4)
                    
                    elif analysis_type == "competition":
                        top_applicants = result.get("top_applicants", [])
                        if len(top_applicants) >= 10:
                            confidence_scores.append(0.8)
                        elif len(top_applicants) >= 5:
                            confidence_scores.append(0.6)
                        else:
                            confidence_scores.append(0.4)
                    
                    else:
                        confidence_scores.append(0.7)  # 默认置信度
            
            return sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
            
        except Exception:
            return 0.0
    
    def _check_consistency(self, analysis_results: Dict[str, Any]) -> float:
        """检查结果一致性."""
        try:
            # 简单的一致性检查
            consistency_score = 0.8  # 基础分数
            
            # 检查是否有明显的数据冲突
            # 这里可以实现更复杂的一致性检查逻辑
            
            return consistency_score
            
        except Exception:
            return 0.0
    
    def _identify_quality_issues(self, analysis_results: Dict[str, Any], quality_report: Dict[str, Any]) -> List[str]:
        """识别质量问题."""
        issues = []
        
        if quality_report["data_completeness"] < 0.7:
            issues.append("部分分析模块数据不完整")
        
        if quality_report["confidence_level"] < 0.6:
            issues.append("分析结果置信度较低")
        
        if quality_report["consistency_score"] < 0.7:
            issues.append("分析结果存在一致性问题")
        
        return issues
    
    def _generate_quality_recommendations(self, quality_report: Dict[str, Any]) -> List[str]:
        """生成质量改进建议."""
        recommendations = []
        
        if quality_report["data_completeness"] < 0.8:
            recommendations.append("建议增加数据源或扩大数据收集范围")
        
        if quality_report["confidence_level"] < 0.7:
            recommendations.append("建议结合其他分析方法提高结果可信度")
        
        if quality_report["overall_quality"] < 0.7:
            recommendations.append("建议进行人工审核和验证")
        
        return recommendations