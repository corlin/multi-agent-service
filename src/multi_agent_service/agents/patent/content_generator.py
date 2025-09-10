"""Patent report content generation system implementation."""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import re

from ...services.model_client import BaseModelClient


logger = logging.getLogger(__name__)


class ReportContentGenerator:
    """专利报告内容生成器，利用LLM模型路由生成智能报告文本."""
    
    def __init__(self, model_client: Optional[BaseModelClient] = None, config: Optional[Dict[str, Any]] = None):
        """初始化内容生成器."""
        self.model_client = model_client
        self.config = config or {}
        
        # 内容生成配置
        self.content_config = {
            "max_summary_length": self.config.get("max_summary_length", 500),
            "max_section_length": self.config.get("max_section_length", 1000),
            "language": self.config.get("language", "zh"),
            "tone": self.config.get("tone", "professional"),
            "include_recommendations": self.config.get("include_recommendations", True),
            "include_insights": self.config.get("include_insights", True),
            "quality_threshold": self.config.get("quality_threshold", 0.7)
        }
        
        # 内容模板
        self.content_templates = self._load_content_templates()
        
        # 质量控制器
        self.quality_controller = ContentQualityController()
        
        self.logger = logging.getLogger(f"{__name__}.ReportContentGenerator")
    
    def _load_content_templates(self) -> Dict[str, Dict[str, str]]:
        """加载内容模板."""
        return {
            "zh": {
                "executive_summary": """
基于对{keywords}领域的专利分析，本报告涵盖了{time_range}期间的{total_patents}件相关专利。
分析显示该技术领域{trend_description}，主要申请人包括{top_applicants}。
技术发展主要集中在{main_technologies}等方向。
{key_insights}
""",
                "trend_section": """
### 趋势分析

在{time_range}期间，{keywords}领域的专利申请呈现{trend_direction}趋势。
{yearly_analysis}

**关键发现：**
{trend_insights}

**发展预测：**
{trend_predictions}
""",
                "competition_section": """
### 竞争分析

市场竞争格局分析显示，{market_concentration_desc}。
主要竞争者及其专利布局如下：

{competitor_analysis}

**竞争态势：**
{competition_insights}
""",
                "technology_section": """
### 技术分析

技术分类分析表明，{keywords}领域的创新主要集中在以下技术方向：

{technology_breakdown}

**技术发展特点：**
{technology_insights}

**技术趋势：**
{technology_trends}
""",
                "geographic_section": """
### 地域分析

从地域分布来看，{keywords}领域的专利申请主要集中在{top_countries}。

{geographic_analysis}

**地域特点：**
{geographic_insights}
""",
                "insights_section": """
### 关键洞察

通过综合分析，我们发现以下关键洞察：

{key_findings}

**市场机会：**
{market_opportunities}

**风险因素：**
{risk_factors}
""",
                "recommendations_section": """
### 建议和结论

基于以上分析，我们提出以下建议：

**战略建议：**
{strategic_recommendations}

**技术建议：**
{technical_recommendations}

**市场建议：**
{market_recommendations}

**结论：**
{conclusions}
"""
            },
            "en": {
                "executive_summary": """
Based on patent analysis in the {keywords} field, this report covers {total_patents} relevant patents during {time_range}.
The analysis shows that this technology field {trend_description}, with major applicants including {top_applicants}.
Technology development is mainly concentrated in {main_technologies} and other directions.
{key_insights}
""",
                "trend_section": """
### Trend Analysis

During {time_range}, patent applications in the {keywords} field showed a {trend_direction} trend.
{yearly_analysis}

**Key Findings:**
{trend_insights}

**Development Predictions:**
{trend_predictions}
""",
                "competition_section": """
### Competition Analysis

Market competition landscape analysis shows {market_concentration_desc}.
Major competitors and their patent layouts are as follows:

{competitor_analysis}

**Competitive Situation:**
{competition_insights}
""",
                "technology_section": """
### Technology Analysis

Technology classification analysis indicates that innovation in the {keywords} field is mainly concentrated in the following technical directions:

{technology_breakdown}

**Technology Development Characteristics:**
{technology_insights}

**Technology Trends:**
{technology_trends}
""",
                "geographic_section": """
### Geographic Analysis

From a geographic distribution perspective, patent applications in the {keywords} field are mainly concentrated in {top_countries}.

{geographic_analysis}

**Geographic Characteristics:**
{geographic_insights}
""",
                "insights_section": """
### Key Insights

Through comprehensive analysis, we found the following key insights:

{key_findings}

**Market Opportunities:**
{market_opportunities}

**Risk Factors:**
{risk_factors}
""",
                "recommendations_section": """
### Recommendations and Conclusions

Based on the above analysis, we propose the following recommendations:

**Strategic Recommendations:**
{strategic_recommendations}

**Technical Recommendations:**
{technical_recommendations}

**Market Recommendations:**
{market_recommendations}

**Conclusions:**
{conclusions}
"""
            }
        }
    
    async def generate_content(self, analysis_data: Dict[str, Any], 
                             report_params: Dict[str, Any]) -> Dict[str, Any]:
        """生成报告内容."""
        try:
            content = {}
            language = report_params.get("language", self.content_config["language"])
            
            # 生成执行摘要
            if "summary" in report_params.get("sections", []):
                content["summary"] = await self._generate_executive_summary(
                    analysis_data, report_params, language
                )
            
            # 生成各个分析章节
            sections = {}
            
            if "trend" in report_params.get("sections", []) and "trend_analysis" in analysis_data:
                sections["trend"] = await self._generate_trend_section(
                    analysis_data["trend_analysis"], report_params, language
                )
            
            if "competition" in report_params.get("sections", []) and "competition_analysis" in analysis_data:
                sections["competition"] = await self._generate_competition_section(
                    analysis_data["competition_analysis"], report_params, language
                )
            
            if "technology" in report_params.get("sections", []) and "technology_analysis" in analysis_data:
                sections["technology"] = await self._generate_technology_section(
                    analysis_data["technology_analysis"], report_params, language
                )
            
            if "geographic" in report_params.get("sections", []) and "geographic_analysis" in analysis_data:
                sections["geographic"] = await self._generate_geographic_section(
                    analysis_data["geographic_analysis"], report_params, language
                )
            
            content["sections"] = sections
            
            # 生成洞察和建议
            if self.content_config["include_insights"] and "insights" in analysis_data:
                content["insights"] = await self._generate_insights_section(
                    analysis_data["insights"], report_params, language
                )
            
            if self.content_config["include_recommendations"]:
                content["recommendations"] = await self._generate_recommendations_section(
                    analysis_data, report_params, language
                )
            
            # 质量检查
            quality_report = await self.quality_controller.validate_content(content)
            
            if quality_report["overall_quality"] < self.content_config["quality_threshold"]:
                self.logger.warning(f"Content quality below threshold: {quality_report['overall_quality']}")
                content = await self._improve_content_quality(content, quality_report, analysis_data, report_params)
            
            # 添加元数据
            content["metadata"] = {
                "generation_time": datetime.now().isoformat(),
                "language": language,
                "sections_count": len(sections),
                "quality_score": quality_report["overall_quality"],
                "word_count": self._count_words(content)
            }
            
            self.logger.info(f"Generated content with {len(sections)} sections")
            return content
            
        except Exception as e:
            self.logger.error(f"Error generating content: {str(e)}")
            return {"error": str(e)}
    
    async def _generate_executive_summary(self, analysis_data: Dict[str, Any], 
                                        report_params: Dict[str, Any], language: str) -> str:
        """生成执行摘要."""
        try:
            # 提取关键信息
            keywords = report_params.get("keywords", ["相关技术"])
            total_patents = analysis_data.get("metadata", {}).get("total_patents", 0)
            
            # 时间范围
            time_range = self._format_time_range(report_params.get("time_range", {}), language)
            
            # 趋势描述
            trend_direction = analysis_data.get("trend_analysis", {}).get("trend_direction", "稳定")
            trend_description = self._describe_trend(trend_direction, language)
            
            # 主要申请人
            top_applicants = analysis_data.get("competition_analysis", {}).get("top_applicants", [])
            top_applicants_str = self._format_top_applicants(top_applicants[:3], language)
            
            # 主要技术
            main_technologies = analysis_data.get("technology_analysis", {}).get("main_technologies", [])
            main_technologies_str = "、".join(main_technologies[:3]) if language == "zh" else ", ".join(main_technologies[:3])
            
            # 关键洞察
            key_insights = analysis_data.get("insights", {}).get("key_findings", [])
            key_insights_str = self._format_insights(key_insights[:2], language)
            
            # 使用模板生成摘要
            template = self.content_templates[language]["executive_summary"]
            summary = template.format(
                keywords="、".join(keywords) if language == "zh" else ", ".join(keywords),
                time_range=time_range,
                total_patents=total_patents,
                trend_description=trend_description,
                top_applicants=top_applicants_str,
                main_technologies=main_technologies_str,
                key_insights=key_insights_str
            )
            
            # 如果有LLM模型，进一步优化摘要
            if self.model_client:
                summary = await self._enhance_with_llm(summary, "executive_summary", language)
            
            return summary.strip()
            
        except Exception as e:
            self.logger.error(f"Error generating executive summary: {str(e)}")
            return "执行摘要生成失败。" if language == "zh" else "Failed to generate executive summary."
    
    async def _generate_trend_section(self, trend_data: Dict[str, Any], 
                                    report_params: Dict[str, Any], language: str) -> str:
        """生成趋势分析章节."""
        try:
            keywords = report_params.get("keywords", ["相关技术"])
            time_range = self._format_time_range(report_params.get("time_range", {}), language)
            
            # 趋势方向
            trend_direction = trend_data.get("trend_direction", "稳定")
            trend_direction_desc = self._describe_trend(trend_direction, language)
            
            # 年度分析
            yearly_counts = trend_data.get("yearly_counts", {})
            yearly_analysis = self._analyze_yearly_data(yearly_counts, language)
            
            # 趋势洞察
            growth_rates = trend_data.get("growth_rates", {})
            trend_insights = self._generate_trend_insights(yearly_counts, growth_rates, language)
            
            # 趋势预测
            trend_predictions = self._generate_trend_predictions(trend_data, language)
            
            # 使用模板
            template = self.content_templates[language]["trend_section"]
            content = template.format(
                time_range=time_range,
                keywords="、".join(keywords) if language == "zh" else ", ".join(keywords),
                trend_direction=trend_direction_desc,
                yearly_analysis=yearly_analysis,
                trend_insights=trend_insights,
                trend_predictions=trend_predictions
            )
            
            # LLM增强
            if self.model_client:
                content = await self._enhance_with_llm(content, "trend_analysis", language)
            
            return content.strip()
            
        except Exception as e:
            self.logger.error(f"Error generating trend section: {str(e)}")
            return "趋势分析章节生成失败。" if language == "zh" else "Failed to generate trend section."
    
    async def _generate_competition_section(self, competition_data: Dict[str, Any], 
                                          report_params: Dict[str, Any], language: str) -> str:
        """生成竞争分析章节."""
        try:
            # 市场集中度描述
            market_concentration = competition_data.get("market_concentration", 0)
            market_concentration_desc = self._describe_market_concentration(market_concentration, language)
            
            # 竞争者分析
            top_applicants = competition_data.get("top_applicants", [])
            competitor_analysis = self._analyze_competitors(top_applicants, language)
            
            # 竞争洞察
            competition_insights = self._generate_competition_insights(competition_data, language)
            
            # 使用模板
            template = self.content_templates[language]["competition_section"]
            content = template.format(
                market_concentration_desc=market_concentration_desc,
                competitor_analysis=competitor_analysis,
                competition_insights=competition_insights
            )
            
            # LLM增强
            if self.model_client:
                content = await self._enhance_with_llm(content, "competition_analysis", language)
            
            return content.strip()
            
        except Exception as e:
            self.logger.error(f"Error generating competition section: {str(e)}")
            return "竞争分析章节生成失败。" if language == "zh" else "Failed to generate competition section."
    
    async def _generate_technology_section(self, technology_data: Dict[str, Any], 
                                         report_params: Dict[str, Any], language: str) -> str:
        """生成技术分析章节."""
        try:
            keywords = report_params.get("keywords", ["相关技术"])
            
            # 技术分解
            ipc_distribution = technology_data.get("ipc_distribution", {})
            main_technologies = technology_data.get("main_technologies", [])
            technology_breakdown = self._analyze_technology_breakdown(ipc_distribution, main_technologies, language)
            
            # 技术洞察
            technology_insights = self._generate_technology_insights(technology_data, language)
            
            # 技术趋势
            technology_trends = self._generate_technology_trends(technology_data, language)
            
            # 使用模板
            template = self.content_templates[language]["technology_section"]
            content = template.format(
                keywords="、".join(keywords) if language == "zh" else ", ".join(keywords),
                technology_breakdown=technology_breakdown,
                technology_insights=technology_insights,
                technology_trends=technology_trends
            )
            
            # LLM增强
            if self.model_client:
                content = await self._enhance_with_llm(content, "technology_analysis", language)
            
            return content.strip()
            
        except Exception as e:
            self.logger.error(f"Error generating technology section: {str(e)}")
            return "技术分析章节生成失败。" if language == "zh" else "Failed to generate technology section."
    
    async def _generate_geographic_section(self, geographic_data: Dict[str, Any], 
                                         report_params: Dict[str, Any], language: str) -> str:
        """生成地域分析章节."""
        try:
            keywords = report_params.get("keywords", ["相关技术"])
            
            # 主要国家
            top_countries = geographic_data.get("top_countries", [])
            top_countries_str = self._format_top_countries(top_countries[:3], language)
            
            # 地域分析
            geographic_analysis = self._analyze_geographic_distribution(geographic_data, language)
            
            # 地域洞察
            geographic_insights = self._generate_geographic_insights(geographic_data, language)
            
            # 使用模板
            template = self.content_templates[language]["geographic_section"]
            content = template.format(
                keywords="、".join(keywords) if language == "zh" else ", ".join(keywords),
                top_countries=top_countries_str,
                geographic_analysis=geographic_analysis,
                geographic_insights=geographic_insights
            )
            
            return content.strip()
            
        except Exception as e:
            self.logger.error(f"Error generating geographic section: {str(e)}")
            return "地域分析章节生成失败。" if language == "zh" else "Failed to generate geographic section."
    
    async def _generate_insights_section(self, insights_data: Dict[str, Any], 
                                       report_params: Dict[str, Any], language: str) -> str:
        """生成洞察章节."""
        try:
            # 关键发现
            key_findings = insights_data.get("key_findings", [])
            key_findings_str = self._format_list_items(key_findings, language)
            
            # 市场机会
            market_opportunities = self._generate_market_opportunities(insights_data, language)
            
            # 风险因素
            risk_factors = insights_data.get("risk_factors", [])
            risk_factors_str = self._format_list_items(risk_factors, language)
            
            # 使用模板
            template = self.content_templates[language]["insights_section"]
            content = template.format(
                key_findings=key_findings_str,
                market_opportunities=market_opportunities,
                risk_factors=risk_factors_str
            )
            
            return content.strip()
            
        except Exception as e:
            self.logger.error(f"Error generating insights section: {str(e)}")
            return "洞察章节生成失败。" if language == "zh" else "Failed to generate insights section."
    
    async def _generate_recommendations_section(self, analysis_data: Dict[str, Any], 
                                              report_params: Dict[str, Any], language: str) -> str:
        """生成建议章节."""
        try:
            # 战略建议
            strategic_recommendations = self._generate_strategic_recommendations(analysis_data, language)
            
            # 技术建议
            technical_recommendations = self._generate_technical_recommendations(analysis_data, language)
            
            # 市场建议
            market_recommendations = self._generate_market_recommendations(analysis_data, language)
            
            # 结论
            conclusions = self._generate_conclusions(analysis_data, language)
            
            # 使用模板
            template = self.content_templates[language]["recommendations_section"]
            content = template.format(
                strategic_recommendations=strategic_recommendations,
                technical_recommendations=technical_recommendations,
                market_recommendations=market_recommendations,
                conclusions=conclusions
            )
            
            # LLM增强
            if self.model_client:
                content = await self._enhance_with_llm(content, "recommendations", language)
            
            return content.strip()
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations section: {str(e)}")
            return "建议章节生成失败。" if language == "zh" else "Failed to generate recommendations section."
    
    async def _enhance_with_llm(self, content: str, section_type: str, language: str) -> str:
        """使用LLM增强内容."""
        try:
            if not self.model_client:
                return content
            
            # 构建提示词
            if language == "zh":
                prompt = f"""
请优化以下{section_type}内容，使其更加专业、准确和易读：

原始内容：
{content}

要求：
1. 保持原有信息的准确性
2. 提高语言的专业性和流畅性
3. 确保逻辑清晰，结构合理
4. 适当增加细节和洞察
5. 保持中文表达习惯

优化后的内容：
"""
            else:
                prompt = f"""
Please optimize the following {section_type} content to make it more professional, accurate and readable:

Original content:
{content}

Requirements:
1. Maintain the accuracy of original information
2. Improve language professionalism and fluency
3. Ensure clear logic and reasonable structure
4. Appropriately add details and insights
5. Maintain English expression habits

Optimized content:
"""
            
            # 调用LLM
            response = await self.model_client.generate_response(prompt)
            
            if response and len(response.strip()) > len(content) * 0.5:  # 基本质量检查
                return response.strip()
            else:
                return content
                
        except Exception as e:
            self.logger.error(f"Error enhancing content with LLM: {str(e)}")
            return content
    
    # 辅助方法
    def _format_time_range(self, time_range: Dict[str, Any], language: str) -> str:
        """格式化时间范围."""
        start_year = time_range.get("start_year", 2014)
        end_year = time_range.get("end_year", 2024)
        
        if language == "zh":
            return f"{start_year}年-{end_year}年"
        else:
            return f"{start_year}-{end_year}"
    
    def _describe_trend(self, trend_direction: str, language: str) -> str:
        """描述趋势方向."""
        descriptions = {
            "zh": {
                "increasing": "呈现上升趋势",
                "decreasing": "呈现下降趋势",
                "stable": "保持相对稳定",
                "fluctuating": "呈现波动态势"
            },
            "en": {
                "increasing": "shows an upward trend",
                "decreasing": "shows a downward trend", 
                "stable": "remains relatively stable",
                "fluctuating": "shows fluctuating patterns"
            }
        }
        
        return descriptions.get(language, descriptions["zh"]).get(trend_direction, "发展态势不明" if language == "zh" else "unclear development trend")
    
    def _format_top_applicants(self, top_applicants: List[tuple], language: str) -> str:
        """格式化主要申请人."""
        if not top_applicants:
            return "暂无数据" if language == "zh" else "No data available"
        
        names = [applicant[0] for applicant in top_applicants]
        
        if language == "zh":
            return "、".join(names)
        else:
            return ", ".join(names)
    
    def _format_insights(self, insights: List[str], language: str) -> str:
        """格式化洞察."""
        if not insights:
            return ""
        
        formatted = []
        for insight in insights:
            if language == "zh":
                formatted.append(f"• {insight}")
            else:
                formatted.append(f"• {insight}")
        
        return "\n".join(formatted)
    
    def _analyze_yearly_data(self, yearly_counts: Dict[str, int], language: str) -> str:
        """分析年度数据."""
        if not yearly_counts:
            return "暂无年度数据。" if language == "zh" else "No yearly data available."
        
        years = sorted(yearly_counts.keys())
        
        if len(years) < 2:
            return "数据年份不足，无法进行趋势分析。" if language == "zh" else "Insufficient data years for trend analysis."
        
        # 找出峰值年份
        max_year = max(yearly_counts.keys(), key=lambda x: yearly_counts[x])
        max_count = yearly_counts[max_year]
        
        # 计算总体变化
        first_year, last_year = years[0], years[-1]
        first_count, last_count = yearly_counts[first_year], yearly_counts[last_year]
        
        if language == "zh":
            analysis = f"从{first_year}年的{first_count}件增长到{last_year}年的{last_count}件，"
            analysis += f"其中{max_year}年达到峰值{max_count}件。"
        else:
            analysis = f"From {first_count} cases in {first_year} to {last_count} cases in {last_year}, "
            analysis += f"with a peak of {max_count} cases in {max_year}."
        
        return analysis
    
    def _generate_trend_insights(self, yearly_counts: Dict[str, int], 
                               growth_rates: Dict[str, float], language: str) -> str:
        """生成趋势洞察."""
        insights = []
        
        if not yearly_counts or not growth_rates:
            return "暂无足够数据生成趋势洞察。" if language == "zh" else "Insufficient data to generate trend insights."
        
        # 分析增长率
        recent_rates = list(growth_rates.values())[-3:] if len(growth_rates) >= 3 else list(growth_rates.values())
        avg_growth = sum(recent_rates) / len(recent_rates) if recent_rates else 0
        
        if language == "zh":
            if avg_growth > 10:
                insights.append("近年来保持较高增长率，显示出强劲的创新活力")
            elif avg_growth > 0:
                insights.append("保持稳定增长，技术发展持续推进")
            else:
                insights.append("增长放缓，可能进入技术成熟期")
        else:
            if avg_growth > 10:
                insights.append("Maintains high growth rate in recent years, showing strong innovation vitality")
            elif avg_growth > 0:
                insights.append("Maintains steady growth with continuous technology development")
            else:
                insights.append("Growth is slowing, possibly entering technology maturity phase")
        
        return "\n".join([f"• {insight}" for insight in insights])
    
    def _generate_trend_predictions(self, trend_data: Dict[str, Any], language: str) -> str:
        """生成趋势预测."""
        trend_direction = trend_data.get("trend_direction", "stable")
        
        predictions = {
            "zh": {
                "increasing": "预计未来2-3年将继续保持增长态势，但增长率可能逐步放缓。",
                "decreasing": "预计短期内申请量可能继续下降，需关注技术转型和新兴方向。",
                "stable": "预计将维持当前水平，技术发展进入稳定期。",
                "fluctuating": "预计将继续呈现波动特征，需密切关注市场变化。"
            },
            "en": {
                "increasing": "Expected to continue growing in the next 2-3 years, but growth rate may gradually slow down.",
                "decreasing": "Application volume may continue to decline in the short term, attention should be paid to technology transformation and emerging directions.",
                "stable": "Expected to maintain current levels as technology development enters a stable period.",
                "fluctuating": "Expected to continue showing fluctuating characteristics, requiring close attention to market changes."
            }
        }
        
        return predictions.get(language, predictions["zh"]).get(trend_direction, "发展趋势有待观察。" if language == "zh" else "Development trend remains to be observed.")
    
    def _describe_market_concentration(self, concentration: float, language: str) -> str:
        """描述市场集中度."""
        if language == "zh":
            if concentration > 0.7:
                return "市场集中度较高，少数企业占据主导地位"
            elif concentration > 0.4:
                return "市场集中度适中，存在明显的领先企业"
            else:
                return "市场相对分散，竞争格局较为开放"
        else:
            if concentration > 0.7:
                return "high market concentration with a few companies dominating"
            elif concentration > 0.4:
                return "moderate market concentration with clear leading companies"
            else:
                return "relatively dispersed market with open competitive landscape"
    
    def _analyze_competitors(self, top_applicants: List[tuple], language: str) -> str:
        """分析竞争者."""
        if not top_applicants:
            return "暂无竞争者数据。" if language == "zh" else "No competitor data available."
        
        analysis = []
        
        for i, (applicant, count) in enumerate(top_applicants[:5]):
            if language == "zh":
                analysis.append(f"{i+1}. **{applicant}**: {count}件专利，占据重要市场地位")
            else:
                analysis.append(f"{i+1}. **{applicant}**: {count} patents, occupying important market position")
        
        return "\n".join(analysis)
    
    def _generate_competition_insights(self, competition_data: Dict[str, Any], language: str) -> str:
        """生成竞争洞察."""
        insights = []
        
        market_concentration = competition_data.get("market_concentration", 0)
        top_applicants = competition_data.get("top_applicants", [])
        
        if language == "zh":
            if market_concentration > 0.6:
                insights.append("市场呈现寡头竞争格局，新进入者面临较高壁垒")
            
            if len(top_applicants) > 0:
                top_applicant = top_applicants[0]
                insights.append(f"{top_applicant[0]}在该领域处于领先地位，拥有{top_applicant[1]}件专利")
        else:
            if market_concentration > 0.6:
                insights.append("Market shows oligopolistic competition with high barriers for new entrants")
            
            if len(top_applicants) > 0:
                top_applicant = top_applicants[0]
                insights.append(f"{top_applicant[0]} leads the field with {top_applicant[1]} patents")
        
        return "\n".join([f"• {insight}" for insight in insights])
    
    def _analyze_technology_breakdown(self, ipc_distribution: Dict[str, int], 
                                   main_technologies: List[str], language: str) -> str:
        """分析技术分解."""
        breakdown = []
        
        # IPC分类分析
        if ipc_distribution:
            sorted_ipc = sorted(ipc_distribution.items(), key=lambda x: x[1], reverse=True)[:5]
            
            if language == "zh":
                breakdown.append("**主要IPC分类：**")
                for ipc, count in sorted_ipc:
                    percentage = (count / sum(ipc_distribution.values())) * 100
                    breakdown.append(f"- {ipc}: {count}件 ({percentage:.1f}%)")
            else:
                breakdown.append("**Main IPC Classifications:**")
                for ipc, count in sorted_ipc:
                    percentage = (count / sum(ipc_distribution.values())) * 100
                    breakdown.append(f"- {ipc}: {count} patents ({percentage:.1f}%)")
        
        # 主要技术方向
        if main_technologies:
            if language == "zh":
                breakdown.append("\n**主要技术方向：**")
                for i, tech in enumerate(main_technologies[:5], 1):
                    breakdown.append(f"{i}. {tech}")
            else:
                breakdown.append("\n**Main Technology Directions:**")
                for i, tech in enumerate(main_technologies[:5], 1):
                    breakdown.append(f"{i}. {tech}")
        
        return "\n".join(breakdown)
    
    def _generate_technology_insights(self, technology_data: Dict[str, Any], language: str) -> str:
        """生成技术洞察."""
        insights = []
        
        ipc_distribution = technology_data.get("ipc_distribution", {})
        main_technologies = technology_data.get("main_technologies", [])
        
        if language == "zh":
            if len(ipc_distribution) > 5:
                insights.append("技术分布较为分散，显示出多元化发展特征")
            elif len(ipc_distribution) <= 3:
                insights.append("技术集中度较高，主要聚焦在少数几个技术领域")
            
            if main_technologies:
                insights.append(f"核心技术方向包括{main_technologies[0]}等领域")
        else:
            if len(ipc_distribution) > 5:
                insights.append("Technology distribution is relatively dispersed, showing diversified development characteristics")
            elif len(ipc_distribution) <= 3:
                insights.append("High technology concentration, mainly focused on a few technical fields")
            
            if main_technologies:
                insights.append(f"Core technology directions include {main_technologies[0]} and other fields")
        
        return "\n".join([f"• {insight}" for insight in insights])
    
    def _generate_technology_trends(self, technology_data: Dict[str, Any], language: str) -> str:
        """生成技术趋势."""
        trends = []
        
        keyword_clusters = technology_data.get("keyword_clusters", [])
        
        if language == "zh":
            if keyword_clusters:
                top_cluster = keyword_clusters[0]
                trends.append(f"{top_cluster['cluster']}是当前最活跃的技术方向")
            
            trends.append("技术发展呈现智能化、集成化趋势")
            trends.append("跨领域技术融合成为重要发展方向")
        else:
            if keyword_clusters:
                top_cluster = keyword_clusters[0]
                trends.append(f"{top_cluster['cluster']} is currently the most active technology direction")
            
            trends.append("Technology development shows trends of intelligence and integration")
            trends.append("Cross-field technology integration becomes an important development direction")
        
        return "\n".join([f"• {trend}" for trend in trends])
    
    def _format_top_countries(self, top_countries: List[str], language: str) -> str:
        """格式化主要国家."""
        if not top_countries:
            return "暂无数据" if language == "zh" else "No data available"
        
        if language == "zh":
            return "、".join(top_countries)
        else:
            return ", ".join(top_countries)
    
    def _analyze_geographic_distribution(self, geographic_data: Dict[str, Any], language: str) -> str:
        """分析地域分布."""
        analysis = []
        
        country_distribution = geographic_data.get("country_distribution", {})
        country_percentages = geographic_data.get("country_percentages", {})
        
        if country_distribution:
            total_patents = sum(country_distribution.values())
            sorted_countries = sorted(country_distribution.items(), key=lambda x: x[1], reverse=True)
            
            if language == "zh":
                analysis.append("**各国/地区专利申请情况：**")
                for country, count in sorted_countries[:5]:
                    percentage = country_percentages.get(country, (count/total_patents)*100)
                    analysis.append(f"- {country}: {count}件 ({percentage:.1f}%)")
            else:
                analysis.append("**Patent Applications by Country/Region:**")
                for country, count in sorted_countries[:5]:
                    percentage = country_percentages.get(country, (count/total_patents)*100)
                    analysis.append(f"- {country}: {count} patents ({percentage:.1f}%)")
        
        return "\n".join(analysis)
    
    def _generate_geographic_insights(self, geographic_data: Dict[str, Any], language: str) -> str:
        """生成地域洞察."""
        insights = []
        
        country_distribution = geographic_data.get("country_distribution", {})
        
        if country_distribution:
            total_patents = sum(country_distribution.values())
            sorted_countries = sorted(country_distribution.items(), key=lambda x: x[1], reverse=True)
            
            if len(sorted_countries) > 0:
                top_country, top_count = sorted_countries[0]
                top_percentage = (top_count / total_patents) * 100
                
                if language == "zh":
                    insights.append(f"{top_country}是该技术领域的主要创新国家，占比{top_percentage:.1f}%")
                    
                    if top_percentage > 50:
                        insights.append("技术创新高度集中在单一国家")
                    elif len(sorted_countries) >= 3:
                        insights.append("技术创新呈现多国竞争格局")
                else:
                    insights.append(f"{top_country} is the main innovation country in this field, accounting for {top_percentage:.1f}%")
                    
                    if top_percentage > 50:
                        insights.append("Technology innovation is highly concentrated in a single country")
                    elif len(sorted_countries) >= 3:
                        insights.append("Technology innovation shows multi-country competition pattern")
        
        return "\n".join([f"• {insight}" for insight in insights])
    
    def _format_list_items(self, items: List[str], language: str) -> str:
        """格式化列表项."""
        if not items:
            return "暂无数据" if language == "zh" else "No data available"
        
        formatted = []
        for item in items:
            formatted.append(f"• {item}")
        
        return "\n".join(formatted)
    
    def _generate_market_opportunities(self, insights_data: Dict[str, Any], language: str) -> str:
        """生成市场机会."""
        opportunities = []
        
        trends = insights_data.get("trends", [])
        
        if language == "zh":
            opportunities.append("新兴技术领域存在较大发展空间")
            opportunities.append("跨领域技术整合带来新的商业机会")
            
            if trends:
                opportunities.append(f"基于{trends[0]}的应用创新具有市场潜力")
        else:
            opportunities.append("Emerging technology fields have significant development space")
            opportunities.append("Cross-field technology integration brings new business opportunities")
            
            if trends:
                opportunities.append(f"Application innovation based on {trends[0]} has market potential")
        
        return "\n".join([f"• {opportunity}" for opportunity in opportunities])
    
    def _generate_strategic_recommendations(self, analysis_data: Dict[str, Any], language: str) -> str:
        """生成战略建议."""
        recommendations = []
        
        if language == "zh":
            recommendations.append("加强核心技术研发投入，提升技术竞争力")
            recommendations.append("关注新兴技术趋势，及时调整技术布局")
            recommendations.append("建立专利预警机制，规避知识产权风险")
        else:
            recommendations.append("Strengthen core technology R&D investment to enhance technological competitiveness")
            recommendations.append("Pay attention to emerging technology trends and adjust technology layout in time")
            recommendations.append("Establish patent early warning mechanism to avoid intellectual property risks")
        
        return "\n".join([f"• {rec}" for rec in recommendations])
    
    def _generate_technical_recommendations(self, analysis_data: Dict[str, Any], language: str) -> str:
        """生成技术建议."""
        recommendations = []
        
        if language == "zh":
            recommendations.append("重点发展具有自主知识产权的核心技术")
            recommendations.append("加强产学研合作，促进技术成果转化")
            recommendations.append("建立技术标准体系，引领行业发展")
        else:
            recommendations.append("Focus on developing core technologies with independent intellectual property rights")
            recommendations.append("Strengthen industry-university-research cooperation to promote technology transfer")
            recommendations.append("Establish technical standard system to lead industry development")
        
        return "\n".join([f"• {rec}" for rec in recommendations])
    
    def _generate_market_recommendations(self, analysis_data: Dict[str, Any], language: str) -> str:
        """生成市场建议."""
        recommendations = []
        
        if language == "zh":
            recommendations.append("深入分析目标市场需求，制定差异化竞争策略")
            recommendations.append("加强品牌建设，提升市场影响力")
            recommendations.append("建立全球化布局，拓展国际市场")
        else:
            recommendations.append("Deeply analyze target market demand and formulate differentiated competitive strategies")
            recommendations.append("Strengthen brand building to enhance market influence")
            recommendations.append("Establish global layout and expand international markets")
        
        return "\n".join([f"• {rec}" for rec in recommendations])
    
    def _generate_conclusions(self, analysis_data: Dict[str, Any], language: str) -> str:
        """生成结论."""
        conclusions = []
        
        if language == "zh":
            conclusions.append("该技术领域具有良好的发展前景和市场潜力")
            conclusions.append("技术创新活跃，竞争格局日趋激烈")
            conclusions.append("需要持续关注技术发展动态，及时调整战略布局")
        else:
            conclusions.append("This technology field has good development prospects and market potential")
            conclusions.append("Technology innovation is active and competition is becoming increasingly fierce")
            conclusions.append("Need to continuously monitor technology development trends and adjust strategic layout in time")
        
        return "\n".join([f"• {conclusion}" for conclusion in conclusions])
    
    async def _improve_content_quality(self, content: Dict[str, Any], quality_report: Dict[str, Any], 
                                     analysis_data: Dict[str, Any], report_params: Dict[str, Any]) -> Dict[str, Any]:
        """改进内容质量."""
        try:
            improved_content = content.copy()
            
            # 根据质量报告改进内容
            issues = quality_report.get("issues", [])
            
            for issue in issues:
                if issue["type"] == "length":
                    # 扩展内容长度
                    section = issue["section"]
                    if section in improved_content.get("sections", {}):
                        original = improved_content["sections"][section]
                        enhanced = await self._expand_section_content(original, section, analysis_data, report_params)
                        improved_content["sections"][section] = enhanced
                
                elif issue["type"] == "detail":
                    # 增加详细信息
                    section = issue["section"]
                    if section in improved_content.get("sections", {}):
                        original = improved_content["sections"][section]
                        detailed = await self._add_section_details(original, section, analysis_data, report_params)
                        improved_content["sections"][section] = detailed
            
            return improved_content
            
        except Exception as e:
            self.logger.error(f"Error improving content quality: {str(e)}")
            return content
    
    async def _expand_section_content(self, original_content: str, section: str, 
                                    analysis_data: Dict[str, Any], report_params: Dict[str, Any]) -> str:
        """扩展章节内容."""
        try:
            language = report_params.get("language", "zh")
            
            # 根据章节类型添加更多内容
            if section == "trend":
                additional = self._generate_additional_trend_content(analysis_data, language)
            elif section == "competition":
                additional = self._generate_additional_competition_content(analysis_data, language)
            elif section == "technology":
                additional = self._generate_additional_technology_content(analysis_data, language)
            else:
                additional = ""
            
            return f"{original_content}\n\n{additional}" if additional else original_content
            
        except Exception as e:
            self.logger.error(f"Error expanding section content: {str(e)}")
            return original_content
    
    async def _add_section_details(self, original_content: str, section: str, 
                                 analysis_data: Dict[str, Any], report_params: Dict[str, Any]) -> str:
        """添加章节详细信息."""
        try:
            language = report_params.get("language", "zh")
            
            # 添加数据支撑和详细分析
            if section == "trend":
                details = self._generate_trend_details(analysis_data, language)
            elif section == "competition":
                details = self._generate_competition_details(analysis_data, language)
            elif section == "technology":
                details = self._generate_technology_details(analysis_data, language)
            else:
                details = ""
            
            return f"{original_content}\n\n**详细分析：**\n{details}" if details else original_content
            
        except Exception as e:
            self.logger.error(f"Error adding section details: {str(e)}")
            return original_content
    
    def _generate_additional_trend_content(self, analysis_data: Dict[str, Any], language: str) -> str:
        """生成额外的趋势内容."""
        trend_data = analysis_data.get("trend_analysis", {})
        yearly_counts = trend_data.get("yearly_counts", {})
        
        if not yearly_counts:
            return ""
        
        if language == "zh":
            content = "**趋势分析补充：**\n"
            content += f"数据覆盖{len(yearly_counts)}年时间跨度，"
            content += f"总计{sum(yearly_counts.values())}件专利申请。"
        else:
            content = "**Additional Trend Analysis:**\n"
            content += f"Data covers {len(yearly_counts)} years timespan, "
            content += f"totaling {sum(yearly_counts.values())} patent applications."
        
        return content
    
    def _generate_additional_competition_content(self, analysis_data: Dict[str, Any], language: str) -> str:
        """生成额外的竞争内容."""
        competition_data = analysis_data.get("competition_analysis", {})
        applicant_distribution = competition_data.get("applicant_distribution", {})
        
        if not applicant_distribution:
            return ""
        
        if language == "zh":
            content = "**竞争格局补充：**\n"
            content += f"共有{len(applicant_distribution)}个申请人参与竞争，"
            content += "市场参与者多样化程度较高。"
        else:
            content = "**Additional Competition Analysis:**\n"
            content += f"A total of {len(applicant_distribution)} applicants participate in competition, "
            content += "showing high market participant diversity."
        
        return content
    
    def _generate_additional_technology_content(self, analysis_data: Dict[str, Any], language: str) -> str:
        """生成额外的技术内容."""
        technology_data = analysis_data.get("technology_analysis", {})
        ipc_distribution = technology_data.get("ipc_distribution", {})
        
        if not ipc_distribution:
            return ""
        
        if language == "zh":
            content = "**技术分析补充：**\n"
            content += f"涉及{len(ipc_distribution)}个IPC技术分类，"
            content += "技术覆盖面较为广泛。"
        else:
            content = "**Additional Technology Analysis:**\n"
            content += f"Involves {len(ipc_distribution)} IPC technology classifications, "
            content += "showing broad technology coverage."
        
        return content
    
    def _generate_trend_details(self, analysis_data: Dict[str, Any], language: str) -> str:
        """生成趋势详细信息."""
        trend_data = analysis_data.get("trend_analysis", {})
        growth_rates = trend_data.get("growth_rates", {})
        
        if not growth_rates:
            return ""
        
        details = []
        avg_growth = sum(growth_rates.values()) / len(growth_rates) if growth_rates else 0
        
        if language == "zh":
            details.append(f"平均年增长率: {avg_growth:.1f}%")
            details.append(f"增长率标准差: {self._calculate_std_dev(list(growth_rates.values())):.1f}%")
        else:
            details.append(f"Average annual growth rate: {avg_growth:.1f}%")
            details.append(f"Growth rate standard deviation: {self._calculate_std_dev(list(growth_rates.values())):.1f}%")
        
        return "\n".join(details)
    
    def _generate_competition_details(self, analysis_data: Dict[str, Any], language: str) -> str:
        """生成竞争详细信息."""
        competition_data = analysis_data.get("competition_analysis", {})
        market_concentration = competition_data.get("market_concentration", 0)
        
        details = []
        
        if language == "zh":
            details.append(f"市场集中度指数: {market_concentration:.3f}")
            details.append(f"竞争强度: {'高' if market_concentration < 0.4 else '中' if market_concentration < 0.7 else '低'}")
        else:
            details.append(f"Market concentration index: {market_concentration:.3f}")
            details.append(f"Competition intensity: {'High' if market_concentration < 0.4 else 'Medium' if market_concentration < 0.7 else 'Low'}")
        
        return "\n".join(details)
    
    def _generate_technology_details(self, analysis_data: Dict[str, Any], language: str) -> str:
        """生成技术详细信息."""
        technology_data = analysis_data.get("technology_analysis", {})
        keyword_clusters = technology_data.get("keyword_clusters", [])
        
        if not keyword_clusters:
            return ""
        
        details = []
        
        if language == "zh":
            details.append(f"技术聚类数量: {len(keyword_clusters)}")
            if keyword_clusters:
                top_cluster = keyword_clusters[0]
                details.append(f"最大技术聚类: {top_cluster.get('cluster', '未知')} ({top_cluster.get('count', 0)}件)")
        else:
            details.append(f"Number of technology clusters: {len(keyword_clusters)}")
            if keyword_clusters:
                top_cluster = keyword_clusters[0]
                details.append(f"Largest technology cluster: {top_cluster.get('cluster', 'Unknown')} ({top_cluster.get('count', 0)} patents)")
        
        return "\n".join(details)
    
    def _calculate_std_dev(self, values: List[float]) -> float:
        """计算标准差."""
        if not values:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def _count_words(self, content: Dict[str, Any]) -> int:
        """统计内容字数."""
        total_words = 0
        
        try:
            # 统计摘要字数
            if "summary" in content:
                total_words += len(str(content["summary"]))
            
            # 统计章节字数
            if "sections" in content:
                for section_content in content["sections"].values():
                    total_words += len(str(section_content))
            
            # 统计洞察字数
            if "insights" in content:
                total_words += len(str(content["insights"]))
            
            # 统计建议字数
            if "recommendations" in content:
                total_words += len(str(content["recommendations"]))
            
            return total_words
            
        except Exception as e:
            self.logger.error(f"Error counting words: {str(e)}")
            return 0


class ContentQualityController:
    """内容质量控制器."""
    
    def __init__(self):
        self.quality_thresholds = {
            "min_summary_length": 100,
            "min_section_length": 200,
            "max_section_length": 2000,
            "min_insights_count": 3,
            "min_recommendations_count": 3
        }
    
    async def validate_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """验证内容质量."""
        try:
            quality_report = {
                "overall_quality": 0.0,
                "section_scores": {},
                "issues": [],
                "suggestions": []
            }
            
            scores = []
            
            # 检查摘要质量
            if "summary" in content:
                summary_score = self._validate_summary(content["summary"], quality_report)
                scores.append(summary_score)
                quality_report["section_scores"]["summary"] = summary_score
            
            # 检查章节质量
            if "sections" in content:
                for section_name, section_content in content["sections"].items():
                    section_score = self._validate_section(section_name, section_content, quality_report)
                    scores.append(section_score)
                    quality_report["section_scores"][section_name] = section_score
            
            # 检查洞察质量
            if "insights" in content:
                insights_score = self._validate_insights(content["insights"], quality_report)
                scores.append(insights_score)
                quality_report["section_scores"]["insights"] = insights_score
            
            # 检查建议质量
            if "recommendations" in content:
                recommendations_score = self._validate_recommendations(content["recommendations"], quality_report)
                scores.append(recommendations_score)
                quality_report["section_scores"]["recommendations"] = recommendations_score
            
            # 计算总体质量分数
            quality_report["overall_quality"] = sum(scores) / len(scores) if scores else 0.0
            
            return quality_report
            
        except Exception as e:
            return {
                "overall_quality": 0.0,
                "section_scores": {},
                "issues": [{"type": "error", "message": str(e)}],
                "suggestions": []
            }
    
    def _validate_summary(self, summary: str, quality_report: Dict[str, Any]) -> float:
        """验证摘要质量."""
        score = 1.0
        
        if len(summary) < self.quality_thresholds["min_summary_length"]:
            score -= 0.3
            quality_report["issues"].append({
                "type": "length",
                "section": "summary",
                "message": "Summary too short"
            })
        
        if not summary.strip():
            score -= 0.5
            quality_report["issues"].append({
                "type": "content",
                "section": "summary", 
                "message": "Summary is empty"
            })
        
        return max(score, 0.0)
    
    def _validate_section(self, section_name: str, section_content: str, quality_report: Dict[str, Any]) -> float:
        """验证章节质量."""
        score = 1.0
        
        content_length = len(str(section_content))
        
        if content_length < self.quality_thresholds["min_section_length"]:
            score -= 0.2
            quality_report["issues"].append({
                "type": "length",
                "section": section_name,
                "message": f"Section {section_name} too short"
            })
        
        if content_length > self.quality_thresholds["max_section_length"]:
            score -= 0.1
            quality_report["suggestions"].append({
                "type": "length",
                "section": section_name,
                "message": f"Section {section_name} might be too long"
            })
        
        if not str(section_content).strip():
            score -= 0.5
            quality_report["issues"].append({
                "type": "content",
                "section": section_name,
                "message": f"Section {section_name} is empty"
            })
        
        return max(score, 0.0)
    
    def _validate_insights(self, insights: Any, quality_report: Dict[str, Any]) -> float:
        """验证洞察质量."""
        score = 1.0
        
        if isinstance(insights, list):
            insights_count = len(insights)
        elif isinstance(insights, str):
            insights_count = len([line for line in insights.split('\n') if line.strip()])
        else:
            insights_count = 0
        
        if insights_count < self.quality_thresholds["min_insights_count"]:
            score -= 0.3
            quality_report["issues"].append({
                "type": "count",
                "section": "insights",
                "message": "Too few insights provided"
            })
        
        return max(score, 0.0)
    
    def _validate_recommendations(self, recommendations: Any, quality_report: Dict[str, Any]) -> float:
        """验证建议质量."""
        score = 1.0
        
        if isinstance(recommendations, list):
            rec_count = len(recommendations)
        elif isinstance(recommendations, str):
            rec_count = len([line for line in recommendations.split('\n') if line.strip()])
        else:
            rec_count = 0
        
        if rec_count < self.quality_thresholds["min_recommendations_count"]:
            score -= 0.3
            quality_report["issues"].append({
                "type": "count",
                "section": "recommendations",
                "message": "Too few recommendations provided"
            })
        
        return max(score, 0.0)
    
    def _analyze_technology_breakdown(self, ipc_distribution: Dict[str, int], 
                                    main_technologies: List[str], language: str) -> str:
        """分析技术分解."""
        breakdown = []
        
        # IPC分类分析
        if ipc_distribution:
            sorted_ipc = sorted(ipc_distribution.items(), key=lambda x: x[1], reverse=True)[:5]
            
            if language == "zh":
                breakdown.append("**主要IPC分类：**")
                for ipc, count in sorted_ipc:
                    breakdown.append(f"• {ipc}: {count}件")
            else:
                breakdown.append("**Main IPC Classifications:**")
                for ipc, count in sorted_ipc:
                    breakdown.append(f"• {ipc}: {count} patents")
        
        # 主要技术方向
        if main_technologies:
            if language == "zh":
                breakdown.append("\n**主要技术方向：**")
                for tech in main_technologies[:5]:
                    breakdown.append(f"• {tech}")
            else:
                breakdown.append("\n**Main Technology Directions:**")
                for tech in main_technologies[:5]:
                    breakdown.append(f"• {tech}")
        
        return "\n".join(breakdown)
    
    def _generate_technology_insights(self, technology_data: Dict[str, Any], language: str) -> str:
        """生成技术洞察."""
        insights = []
        
        main_technologies = technology_data.get("main_technologies", [])
        ipc_distribution = technology_data.get("ipc_distribution", {})
        
        if language == "zh":
            if main_technologies:
                insights.append(f"技术创新主要集中在{main_technologies[0]}等核心领域")
            
            if len(ipc_distribution) > 5:
                insights.append("技术分布较为广泛，显示出多元化发展特征")
            else:
                insights.append("技术相对集中，专业化程度较高")
        else:
            if main_technologies:
                insights.append(f"Technology innovation mainly focuses on core areas such as {main_technologies[0]}")
            
            if len(ipc_distribution) > 5:
                insights.append("Technology distribution is relatively broad, showing diversified development characteristics")
            else:
                insights.append("Technology is relatively concentrated with high specialization")
        
        return "\n".join([f"• {insight}" for insight in insights])
    
    def _generate_technology_trends(self, technology_data: Dict[str, Any], language: str) -> str:
        """生成技术趋势."""
        trends = []
        
        if language == "zh":
            trends.append("新兴技术方向值得重点关注")
            trends.append("传统技术领域仍有创新空间")
            trends.append("跨领域技术融合成为发展趋势")
        else:
            trends.append("Emerging technology directions deserve key attention")
            trends.append("Traditional technology fields still have innovation space")
            trends.append("Cross-field technology integration becomes development trend")
        
        return "\n".join([f"• {trend}" for trend in trends])
    
    def _format_top_countries(self, top_countries: List[tuple], language: str) -> str:
        """格式化主要国家."""
        if not top_countries:
            return "暂无数据" if language == "zh" else "No data available"
        
        countries = [country[0] for country in top_countries]
        
        if language == "zh":
            return "、".join(countries)
        else:
            return ", ".join(countries)
    
    def _analyze_geographic_distribution(self, geographic_data: Dict[str, Any], language: str) -> str:
        """分析地域分布."""
        country_distribution = geographic_data.get("country_distribution", {})
        
        if not country_distribution:
            return "暂无地域分布数据。" if language == "zh" else "No geographic distribution data available."
        
        total_patents = sum(country_distribution.values())
        sorted_countries = sorted(country_distribution.items(), key=lambda x: x[1], reverse=True)
        
        analysis = []
        
        for i, (country, count) in enumerate(sorted_countries[:5]):
            percentage = (count / total_patents) * 100 if total_patents > 0 else 0
            
            if language == "zh":
                analysis.append(f"{i+1}. {country}: {count}件 ({percentage:.1f}%)")
            else:
                analysis.append(f"{i+1}. {country}: {count} patents ({percentage:.1f}%)")
        
        return "\n".join(analysis)
    
    def _generate_geographic_insights(self, geographic_data: Dict[str, Any], language: str) -> str:
        """生成地域洞察."""
        insights = []
        
        country_distribution = geographic_data.get("country_distribution", {})
        
        if not country_distribution:
            return "暂无足够数据生成地域洞察。" if language == "zh" else "Insufficient data to generate geographic insights."
        
        # 分析地域集中度
        total_patents = sum(country_distribution.values())
        sorted_countries = sorted(country_distribution.items(), key=lambda x: x[1], reverse=True)
        
        if sorted_countries:
            top_country_ratio = sorted_countries[0][1] / total_patents if total_patents > 0 else 0
            
            if language == "zh":
                if top_country_ratio > 0.7:
                    insights.append("专利申请高度集中在单一国家/地区")
                elif top_country_ratio > 0.4:
                    insights.append("存在明显的地域集中趋势")
                else:
                    insights.append("地域分布相对均衡")
                
                insights.append("建议关注主要市场的政策变化和技术需求")
            else:
                if top_country_ratio > 0.7:
                    insights.append("Patent applications are highly concentrated in a single country/region")
                elif top_country_ratio > 0.4:
                    insights.append("There is a clear trend of geographic concentration")
                else:
                    insights.append("Geographic distribution is relatively balanced")
                
                insights.append("Recommend monitoring policy changes and technology demands in major markets")
        
        return "\n".join([f"• {insight}" for insight in insights])
    
    def _format_list_items(self, items: List[str], language: str) -> str:
        """格式化列表项."""
        if not items:
            return "暂无相关信息。" if language == "zh" else "No relevant information available."
        
        return "\n".join([f"• {item}" for item in items])
    
    def _generate_market_opportunities(self, insights_data: Dict[str, Any], language: str) -> str:
        """生成市场机会."""
        opportunities = []
        
        if language == "zh":
            opportunities.extend([
                "新兴技术领域存在发展机遇",
                "市场空白点值得重点关注",
                "技术转化应用前景广阔"
            ])
        else:
            opportunities.extend([
                "Development opportunities exist in emerging technology fields",
                "Market gaps deserve key attention", 
                "Technology transformation and application prospects are broad"
            ])
        
        return "\n".join([f"• {opp}" for opp in opportunities])
    
    def _generate_strategic_recommendations(self, analysis_data: Dict[str, Any], language: str) -> str:
        """生成战略建议."""
        recommendations = []
        
        if language == "zh":
            recommendations.extend([
                "制定长期技术发展战略规划",
                "加强核心技术领域的专利布局",
                "建立完善的知识产权保护体系"
            ])
        else:
            recommendations.extend([
                "Develop long-term technology development strategic planning",
                "Strengthen patent layout in core technology fields",
                "Establish comprehensive intellectual property protection system"
            ])
        
        return "\n".join([f"• {rec}" for rec in recommendations])
    
    def _generate_technical_recommendations(self, analysis_data: Dict[str, Any], language: str) -> str:
        """生成技术建议."""
        recommendations = []
        
        if language == "zh":
            recommendations.extend([
                "重点投入前沿技术研发",
                "加强产学研合作创新",
                "建立技术标准和规范"
            ])
        else:
            recommendations.extend([
                "Focus investment on cutting-edge technology R&D",
                "Strengthen industry-academia-research cooperation and innovation",
                "Establish technology standards and specifications"
            ])
        
        return "\n".join([f"• {rec}" for rec in recommendations])
    
    def _generate_market_recommendations(self, analysis_data: Dict[str, Any], language: str) -> str:
        """生成市场建议."""
        recommendations = []
        
        if language == "zh":
            recommendations.extend([
                "密切关注市场需求变化",
                "加快技术成果产业化进程",
                "拓展国际市场合作机会"
            ])
        else:
            recommendations.extend([
                "Closely monitor market demand changes",
                "Accelerate technology achievement industrialization process",
                "Expand international market cooperation opportunities"
            ])
        
        return "\n".join([f"• {rec}" for rec in recommendations])
    
    def _generate_conclusions(self, analysis_data: Dict[str, Any], language: str) -> str:
        """生成结论."""
        if language == "zh":
            return """
综合分析表明，该技术领域具有良好的发展前景和创新潜力。
建议相关企业和机构加强技术研发投入，完善专利布局策略，
积极参与市场竞争，把握技术发展机遇。
"""
        else:
            return """
Comprehensive analysis shows that this technology field has good development prospects and innovation potential.
It is recommended that relevant enterprises and institutions strengthen technology R&D investment, 
improve patent layout strategies, actively participate in market competition, and seize technology development opportunities.
"""
    
    def _count_words(self, content: Dict[str, Any]) -> int:
        """统计内容字数."""
        try:
            total_words = 0
            
            def count_text(text):
                if isinstance(text, str):
                    # 简单的中英文字数统计
                    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
                    english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
                    return chinese_chars + english_words
                return 0
            
            # 递归统计所有文本内容
            def recursive_count(obj):
                nonlocal total_words
                if isinstance(obj, str):
                    total_words += count_text(obj)
                elif isinstance(obj, dict):
                    for value in obj.values():
                        recursive_count(value)
                elif isinstance(obj, list):
                    for item in obj:
                        recursive_count(item)
            
            recursive_count(content)
            return total_words
            
        except Exception as e:
            self.logger.error(f"Error counting words: {str(e)}")
            return 0
    
    async def _improve_content_quality(self, content: Dict[str, Any], 
                                     quality_report: Dict[str, Any],
                                     analysis_data: Dict[str, Any], 
                                     report_params: Dict[str, Any]) -> Dict[str, Any]:
        """改进内容质量."""
        try:
            improved_content = content.copy()
            
            # 根据质量报告改进内容
            issues = quality_report.get("issues", [])
            
            for issue in issues:
                if issue == "insufficient_length":
                    # 扩展内容
                    improved_content = await self._expand_content(improved_content, analysis_data, report_params)
                elif issue == "poor_structure":
                    # 改进结构
                    improved_content = self._improve_structure(improved_content)
                elif issue == "unclear_language":
                    # 改进语言
                    improved_content = await self._improve_language(improved_content, report_params)
            
            return improved_content
            
        except Exception as e:
            self.logger.error(f"Error improving content quality: {str(e)}")
            return content
    
    async def _expand_content(self, content: Dict[str, Any], 
                            analysis_data: Dict[str, Any], 
                            report_params: Dict[str, Any]) -> Dict[str, Any]:
        """扩展内容."""
        # 简单的内容扩展逻辑
        expanded_content = content.copy()
        
        # 为每个章节添加更多细节
        if "sections" in expanded_content:
            for section_name, section_content in expanded_content["sections"].items():
                if len(section_content) < 200:  # 如果内容太短
                    # 添加更多分析细节
                    additional_content = f"\n\n通过深入分析，我们发现{section_name}方面还存在更多值得关注的细节和趋势。"
                    expanded_content["sections"][section_name] = section_content + additional_content
        
        return expanded_content
    
    def _improve_structure(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """改进结构."""
        # 简单的结构改进逻辑
        improved_content = content.copy()
        
        # 确保内容有清晰的层次结构
        if "sections" in improved_content:
            for section_name, section_content in improved_content["sections"].items():
                if not section_content.startswith("###"):
                    # 添加标题
                    improved_content["sections"][section_name] = f"### {section_name.title()}\n\n{section_content}"
        
        return improved_content
    
    async def _improve_language(self, content: Dict[str, Any], 
                              report_params: Dict[str, Any]) -> Dict[str, Any]:
        """改进语言."""
        # 如果有LLM，可以用来改进语言质量
        if self.model_client:
            improved_content = content.copy()
            
            # 对每个章节进行语言优化
            if "sections" in improved_content:
                for section_name, section_content in improved_content["sections"].items():
                    try:
                        improved_section = await self._enhance_with_llm(
                            section_content, section_name, 
                            report_params.get("language", "zh")
                        )
                        improved_content["sections"][section_name] = improved_section
                    except Exception as e:
                        self.logger.error(f"Error improving language for section {section_name}: {str(e)}")
            
            return improved_content
        
        return content


class ContentQualityController:
    """内容质量控制器."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ContentQualityController")
    
    async def validate_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """验证内容质量."""
        try:
            quality_report = {
                "overall_quality": 0.0,
                "issues": [],
                "scores": {}
            }
            
            # 检查内容完整性
            completeness_score = self._check_completeness(content)
            quality_report["scores"]["completeness"] = completeness_score
            
            # 检查内容长度
            length_score = self._check_length(content)
            quality_report["scores"]["length"] = length_score
            
            # 检查结构清晰度
            structure_score = self._check_structure(content)
            quality_report["scores"]["structure"] = structure_score
            
            # 检查语言质量
            language_score = self._check_language(content)
            quality_report["scores"]["language"] = language_score
            
            # 计算总体质量分数
            scores = list(quality_report["scores"].values())
            quality_report["overall_quality"] = sum(scores) / len(scores) if scores else 0.0
            
            # 识别问题
            if completeness_score < 0.7:
                quality_report["issues"].append("incomplete_content")
            if length_score < 0.6:
                quality_report["issues"].append("insufficient_length")
            if structure_score < 0.7:
                quality_report["issues"].append("poor_structure")
            if language_score < 0.7:
                quality_report["issues"].append("unclear_language")
            
            return quality_report
            
        except Exception as e:
            self.logger.error(f"Error validating content: {str(e)}")
            return {"overall_quality": 0.5, "issues": ["validation_error"], "scores": {}}
    
    def _check_completeness(self, content: Dict[str, Any]) -> float:
        """检查内容完整性."""
        required_sections = ["summary", "sections"]
        present_sections = [section for section in required_sections if section in content and content[section]]
        
        return len(present_sections) / len(required_sections)
    
    def _check_length(self, content: Dict[str, Any]) -> float:
        """检查内容长度."""
        total_length = 0
        
        if "summary" in content and isinstance(content["summary"], str):
            total_length += len(content["summary"])
        
        if "sections" in content and isinstance(content["sections"], dict):
            for section_content in content["sections"].values():
                if isinstance(section_content, str):
                    total_length += len(section_content)
        
        # 基于总长度评分
        if total_length > 2000:
            return 1.0
        elif total_length > 1000:
            return 0.8
        elif total_length > 500:
            return 0.6
        else:
            return 0.3
    
    def _check_structure(self, content: Dict[str, Any]) -> float:
        """检查结构清晰度."""
        structure_score = 0.0
        
        # 检查是否有摘要
        if "summary" in content and content["summary"]:
            structure_score += 0.3
        
        # 检查是否有章节
        if "sections" in content and isinstance(content["sections"], dict) and content["sections"]:
            structure_score += 0.4
            
            # 检查章节数量
            section_count = len(content["sections"])
            if 2 <= section_count <= 6:
                structure_score += 0.3
            elif section_count > 0:
                structure_score += 0.1
        
        return min(structure_score, 1.0)
    
    def _check_language(self, content: Dict[str, Any]) -> float:
        """检查语言质量."""
        # 简单的语言质量检查
        language_score = 0.8  # 默认分数
        
        # 检查是否有明显的错误模式
        all_text = ""
        
        if "summary" in content and isinstance(content["summary"], str):
            all_text += content["summary"]
        
        if "sections" in content and isinstance(content["sections"], dict):
            for section_content in content["sections"].values():
                if isinstance(section_content, str):
                    all_text += section_content
        
        # 简单的质量检查
        if len(all_text) > 0:
            # 检查重复内容
            words = all_text.split()
            unique_words = set(words)
            if len(unique_words) / len(words) < 0.3:  # 重复度过高
                language_score -= 0.2
            
            # 检查句子长度变化
            sentences = re.split(r'[。！？.!?]', all_text)
            if len(sentences) > 1:
                avg_length = sum(len(s) for s in sentences) / len(sentences)
                if avg_length < 10 or avg_length > 200:  # 句子过短或过长
                    language_score -= 0.1
        
        return max(language_score, 0.0)


class ContentQualityController:
    """内容质量控制器."""
    
    def __init__(self):
        self.quality_thresholds = {
            "min_summary_length": 100,
            "min_section_length": 200,
            "max_section_length": 2000,
            "min_insights_count": 3,
            "min_recommendations_count": 3
        }
    
    async def validate_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """验证内容质量."""
        try:
            quality_report = {
                "overall_quality": 0.0,
                "section_scores": {},
                "issues": [],
                "suggestions": []
            }
            
            scores = []
            
            # 检查摘要质量
            if "summary" in content:
                summary_score = self._validate_summary(content["summary"], quality_report)
                scores.append(summary_score)
                quality_report["section_scores"]["summary"] = summary_score
            
            # 检查章节质量
            if "sections" in content:
                for section_name, section_content in content["sections"].items():
                    section_score = self._validate_section(section_name, section_content, quality_report)
                    scores.append(section_score)
                    quality_report["section_scores"][section_name] = section_score
            
            # 检查洞察质量
            if "insights" in content:
                insights_score = self._validate_insights(content["insights"], quality_report)
                scores.append(insights_score)
                quality_report["section_scores"]["insights"] = insights_score
            
            # 检查建议质量
            if "recommendations" in content:
                recommendations_score = self._validate_recommendations(content["recommendations"], quality_report)
                scores.append(recommendations_score)
                quality_report["section_scores"]["recommendations"] = recommendations_score
            
            # 计算总体质量分数
            if scores:
                quality_report["overall_quality"] = sum(scores) / len(scores)
            
            return quality_report
            
        except Exception as e:
            logger.error(f"Error validating content quality: {str(e)}")
            return {
                "overall_quality": 0.5,
                "section_scores": {},
                "issues": [{"type": "validation_error", "message": str(e)}],
                "suggestions": []
            }
    
    def _validate_summary(self, summary: str, quality_report: Dict[str, Any]) -> float:
        """验证摘要质量."""
        score = 1.0
        
        # 检查长度
        if len(summary) < self.quality_thresholds["min_summary_length"]:
            score -= 0.3
            quality_report["issues"].append({
                "type": "length_too_short",
                "section": "summary",
                "message": f"摘要长度不足，当前{len(summary)}字符，建议至少{self.quality_thresholds['min_summary_length']}字符"
            })
        
        # 检查内容完整性
        required_elements = ["分析", "专利", "技术", "趋势"]
        missing_elements = [elem for elem in required_elements if elem not in summary]
        
        if missing_elements:
            score -= 0.2
            quality_report["suggestions"].append({
                "type": "content_completeness",
                "section": "summary", 
                "message": f"建议在摘要中包含以下要素：{', '.join(missing_elements)}"
            })
        
        return max(score, 0.0)
    
    def _validate_section(self, section_name: str, section_content: str, quality_report: Dict[str, Any]) -> float:
        """验证章节质量."""
        score = 1.0
        
        # 检查长度
        content_length = len(str(section_content))
        
        if content_length < self.quality_thresholds["min_section_length"]:
            score -= 0.4
            quality_report["issues"].append({
                "type": "length_too_short",
                "section": section_name,
                "message": f"{section_name}章节内容不足，当前{content_length}字符"
            })
        
        elif content_length > self.quality_thresholds["max_section_length"]:
            score -= 0.2
            quality_report["suggestions"].append({
                "type": "length_too_long",
                "section": section_name,
                "message": f"{section_name}章节内容过长，建议精简"
            })
        
        # 检查结构
        if "###" not in section_content and "**" not in section_content:
            score -= 0.2
            quality_report["suggestions"].append({
                "type": "structure_improvement",
                "section": section_name,
                "message": f"建议为{section_name}章节添加更清晰的结构标识"
            })
        
        return max(score, 0.0)
    
    def _validate_insights(self, insights: Any, quality_report: Dict[str, Any]) -> float:
        """验证洞察质量."""
        score = 1.0
        
        # 转换为列表格式进行检查
        if isinstance(insights, str):
            insights_list = [line.strip("• ") for line in insights.split("\n") if line.strip()]
        elif isinstance(insights, list):
            insights_list = insights
        else:
            insights_list = []
        
        # 检查数量
        if len(insights_list) < self.quality_thresholds["min_insights_count"]:
            score -= 0.3
            quality_report["issues"].append({
                "type": "insufficient_insights",
                "section": "insights",
                "message": f"洞察数量不足，当前{len(insights_list)}个，建议至少{self.quality_thresholds['min_insights_count']}个"
            })
        
        # 检查质量
        short_insights = [insight for insight in insights_list if len(insight) < 20]
        if len(short_insights) > len(insights_list) * 0.5:
            score -= 0.2
            quality_report["suggestions"].append({
                "type": "insight_depth",
                "section": "insights",
                "message": "建议提供更深入、详细的洞察分析"
            })
        
        return max(score, 0.0)
    
    def _validate_recommendations(self, recommendations: Any, quality_report: Dict[str, Any]) -> float:
        """验证建议质量."""
        score = 1.0
        
        # 转换为列表格式进行检查
        if isinstance(recommendations, str):
            recommendations_list = [line.strip("• ") for line in recommendations.split("\n") if line.strip()]
        elif isinstance(recommendations, list):
            recommendations_list = recommendations
        else:
            recommendations_list = []
        
        # 检查数量
        if len(recommendations_list) < self.quality_thresholds["min_recommendations_count"]:
            score -= 0.3
            quality_report["issues"].append({
                "type": "insufficient_recommendations",
                "section": "recommendations",
                "message": f"建议数量不足，当前{len(recommendations_list)}个，建议至少{self.quality_thresholds['min_recommendations_count']}个"
            })
        
        # 检查可操作性
        actionable_keywords = ["建议", "应当", "需要", "可以", "recommend", "should", "need", "can"]
        actionable_count = sum(1 for rec in recommendations_list 
                             if any(keyword in rec.lower() for keyword in actionable_keywords))
        
        if actionable_count < len(recommendations_list) * 0.7:
            score -= 0.2
            quality_report["suggestions"].append({
                "type": "actionability",
                "section": "recommendations",
                "message": "建议提供更具可操作性的建议"
            })
        
        return max(score, 0.0)