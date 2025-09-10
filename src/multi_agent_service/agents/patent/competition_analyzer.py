"""Advanced competition analysis algorithms for patent data."""

import asyncio
import logging
import re
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime
from collections import defaultdict, Counter
import json

logger = logging.getLogger(__name__)


class CompetitionAnalyzer:
    """高级竞争分析器，进行申请人分析和市场集中度计算."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.CompetitionAnalyzer")
        
        # 申请人类型分类规则
        self.applicant_type_rules = {
            "大学": ["大学", "学院", "university", "college", "institute of technology"],
            "研究机构": ["研究院", "研究所", "科学院", "实验室", "institute", "laboratory", "research"],
            "大型企业": ["集团", "控股", "group", "holdings", "corporation", "corp", "inc"],
            "科技公司": ["科技", "技术", "软件", "信息", "technology", "tech", "software", "information"],
            "制造企业": ["制造", "工业", "机械", "manufacturing", "industrial", "machinery"],
            "外资企业": ["ltd", "llc", "gmbh", "co.", "company", "limited"]
        }
        
        # 国家/地区代码映射
        self.country_mapping = {
            "CN": "中国", "US": "美国", "JP": "日本", "KR": "韩国", 
            "DE": "德国", "GB": "英国", "FR": "法国", "IT": "意大利"
        }
        
        # 性能监控
        self.performance_metrics = {
            "analysis_count": 0,
            "average_processing_time": 0.0,
            "success_rate": 0.0
        }
    
    async def analyze_competition(self, patent_data: List[Dict[str, Any]], analysis_params: Dict[str, Any]) -> Dict[str, Any]:
        """执行竞争分析."""
        start_time = datetime.now()
        
        try:
            self.logger.info("Starting competition analysis")
            
            # 数据预处理
            processed_data = await self._preprocess_competition_data(patent_data)
            
            if not processed_data:
                return {
                    "error": "没有可用于竞争分析的数据",
                    "success": False
                }
            
            # 执行多维度竞争分析
            competition_results = {}
            
            # 1. 申请人分析
            applicant_analysis = await self._applicant_analysis(processed_data)
            competition_results["applicant_analysis"] = applicant_analysis
            
            # 2. 市场集中度计算
            market_concentration = await self._market_concentration_analysis(processed_data)
            competition_results["market_concentration"] = market_concentration
            
            # 3. 竞争格局分析
            competition_landscape = await self._competition_landscape_analysis(processed_data)
            competition_results["competition_landscape"] = competition_landscape
            
            # 4. 地域竞争分析
            geographic_competition = await self._geographic_competition_analysis(processed_data)
            competition_results["geographic_competition"] = geographic_competition
            
            # 5. 时间序列竞争分析
            temporal_competition = await self._temporal_competition_analysis(processed_data)
            competition_results["temporal_competition"] = temporal_competition
            
            # 6. 竞争强度评估
            competition_intensity = await self._competition_intensity_assessment(competition_results)
            competition_results["competition_intensity"] = competition_intensity
            
            # 记录性能指标
            processing_time = (datetime.now() - start_time).total_seconds()
            await self._update_performance_metrics(processing_time, True)
            
            self.logger.info(f"Competition analysis completed in {processing_time:.2f}s")
            
            return {
                "success": True,
                "results": competition_results,
                "metadata": {
                    "processing_time": processing_time,
                    "patents_analyzed": len(processed_data),
                    "analysis_timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in competition analysis: {str(e)}")
            
            # 记录失败指标
            processing_time = (datetime.now() - start_time).total_seconds()
            await self._update_performance_metrics(processing_time, False)
            
            return {
                "success": False,
                "error": str(e),
                "metadata": {
                    "processing_time": processing_time,
                    "error_timestamp": datetime.now().isoformat()
                }
            } 
   
    async def _preprocess_competition_data(self, patent_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """预处理竞争分析数据."""
        processed_data = []
        
        for patent in patent_data:
            try:
                # 清理和标准化申请人信息
                applicants = patent.get("applicants", [])
                cleaned_applicants = [self._clean_applicant_name(app) for app in applicants if app]
                
                if not cleaned_applicants:
                    continue
                
                processed_patent = {
                    "applicants": cleaned_applicants,
                    "primary_applicant": cleaned_applicants[0],
                    "year": self._extract_year(patent.get("application_date", "")),
                    "country": patent.get("country", "Unknown"),
                    "ipc_classes": patent.get("ipc_classes", []),
                    "title": patent.get("title", ""),
                    "application_number": patent.get("application_number", ""),
                    "original_data": patent
                }
                
                processed_data.append(processed_patent)
                
            except Exception as e:
                self.logger.warning(f"Error processing patent for competition analysis: {str(e)}")
                continue
        
        self.logger.info(f"Processed {len(processed_data)} patents for competition analysis")
        return processed_data
    
    def _clean_applicant_name(self, applicant: str) -> str:
        """清理申请人名称."""
        if not applicant:
            return ""
        
        # 移除常见的公司后缀
        suffixes_to_remove = [
            "有限公司", "股份有限公司", "科技有限公司", "技术有限公司",
            "有限责任公司", "集团有限公司", "控股有限公司",
            "Inc.", "LLC", "Corporation", "Corp.", "Ltd.", "Co.", 
            "Company", "Limited", "GmbH", "S.A.", "N.V."
        ]
        
        cleaned = applicant.strip()
        
        for suffix in suffixes_to_remove:
            if cleaned.endswith(suffix):
                cleaned = cleaned[:-len(suffix)].strip()
        
        # 移除多余的空格和特殊字符
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = re.sub(r'[^\w\s\u4e00-\u9fff]', '', cleaned)  # 保留中文、英文、数字和空格
        
        return cleaned.strip()
    
    def _extract_year(self, date_str: str) -> Optional[int]:
        """提取年份."""
        try:
            if date_str:
                return int(date_str.split("-")[0])
        except (ValueError, IndexError):
            pass
        return None
    
    async def _applicant_analysis(self, processed_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """申请人分析."""
        try:
            # 统计申请人
            applicant_counts = defaultdict(int)
            applicant_years = defaultdict(set)
            applicant_countries = defaultdict(set)
            applicant_ipc_classes = defaultdict(set)
            
            for patent in processed_data:
                primary_applicant = patent["primary_applicant"]
                year = patent.get("year")
                country = patent.get("country", "Unknown")
                ipc_classes = patent.get("ipc_classes", [])
                
                applicant_counts[primary_applicant] += 1
                
                if year:
                    applicant_years[primary_applicant].add(year)
                
                applicant_countries[primary_applicant].add(country)
                
                for ipc in ipc_classes:
                    if ipc:
                        main_ipc = ipc[:4] if len(ipc) >= 4 else ipc
                        applicant_ipc_classes[primary_applicant].add(main_ipc)
            
            # 排序获取主要申请人
            top_applicants = sorted(applicant_counts.items(), key=lambda x: x[1], reverse=True)
            
            # 申请人类型分类
            applicant_types = self._classify_applicant_types(top_applicants)
            
            # 申请人活跃度分析
            applicant_activity = self._analyze_applicant_activity(
                applicant_counts, applicant_years, applicant_countries, applicant_ipc_classes
            )
            
            # 新兴申请人识别
            emerging_applicants = self._identify_emerging_applicants(processed_data)
            
            return {
                "total_unique_applicants": len(applicant_counts),
                "top_applicants": top_applicants[:20],
                "applicant_types": applicant_types,
                "applicant_activity": applicant_activity,
                "emerging_applicants": emerging_applicants
            }
            
        except Exception as e:
            self.logger.error(f"Error in applicant analysis: {str(e)}")
            return {"error": str(e)}
    
    def _classify_applicant_types(self, top_applicants: List[Tuple[str, int]]) -> Dict[str, List[Dict[str, Any]]]:
        """分类申请人类型."""
        classified_types = {
            "大学": [],
            "研究机构": [],
            "大型企业": [],
            "科技公司": [],
            "制造企业": [],
            "外资企业": [],
            "其他": []
        }
        
        for applicant, count in top_applicants[:50]:  # 分析前50名申请人
            applicant_lower = applicant.lower()
            classified = False
            
            for type_name, keywords in self.applicant_type_rules.items():
                if any(keyword.lower() in applicant_lower for keyword in keywords):
                    classified_types[type_name].append({
                        "name": applicant,
                        "patent_count": count
                    })
                    classified = True
                    break
            
            if not classified:
                classified_types["其他"].append({
                    "name": applicant,
                    "patent_count": count
                })
        
        # 计算各类型的统计信息
        type_statistics = {}
        for type_name, applicants in classified_types.items():
            if applicants:
                total_patents = sum(app["patent_count"] for app in applicants)
                type_statistics[type_name] = {
                    "count": len(applicants),
                    "total_patents": total_patents,
                    "average_patents": total_patents / len(applicants),
                    "top_applicants": applicants[:5]
                }
        
        return type_statistics
    
    def _analyze_applicant_activity(self, applicant_counts: Dict[str, int], 
                                  applicant_years: Dict[str, Set[int]], 
                                  applicant_countries: Dict[str, Set[str]], 
                                  applicant_ipc_classes: Dict[str, Set[str]]) -> Dict[str, Any]:
        """分析申请人活跃度."""
        activity_analysis = {}
        
        for applicant in list(applicant_counts.keys())[:20]:  # 分析前20名申请人
            patent_count = applicant_counts[applicant]
            active_years = len(applicant_years.get(applicant, set()))
            countries = len(applicant_countries.get(applicant, set()))
            tech_areas = len(applicant_ipc_classes.get(applicant, set()))
            
            # 计算活跃度评分
            activity_score = self._calculate_activity_score(patent_count, active_years, countries, tech_areas)
            
            # 判断申请人特征
            characteristics = []
            if patent_count > 50:
                characteristics.append("高产申请人")
            if active_years > 5:
                characteristics.append("长期活跃")
            if countries > 1:
                characteristics.append("国际化布局")
            if tech_areas > 5:
                characteristics.append("技术多元化")
            
            activity_analysis[applicant] = {
                "patent_count": patent_count,
                "active_years": active_years,
                "countries_count": countries,
                "tech_areas_count": tech_areas,
                "activity_score": activity_score,
                "characteristics": characteristics
            }
        
        return activity_analysis
    
    def _calculate_activity_score(self, patent_count: int, active_years: int, countries: int, tech_areas: int) -> float:
        """计算申请人活跃度评分."""
        # 归一化各项指标
        patent_score = min(patent_count / 100, 1.0)  # 专利数量，最高100分
        years_score = min(active_years / 10, 1.0)    # 活跃年数，最高10年
        country_score = min(countries / 5, 1.0)      # 国家数量，最高5个国家
        tech_score = min(tech_areas / 10, 1.0)       # 技术领域，最高10个领域
        
        # 加权计算总分
        activity_score = (
            patent_score * 0.4 +      # 专利数量权重40%
            years_score * 0.3 +       # 活跃年数权重30%
            country_score * 0.15 +    # 国际化权重15%
            tech_score * 0.15         # 技术多样性权重15%
        )
        
        return round(activity_score * 100, 2)  # 转换为百分制
    
    def _identify_emerging_applicants(self, processed_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """识别新兴申请人."""
        try:
            # 按年份统计申请人
            yearly_applicants = defaultdict(lambda: defaultdict(int))
            
            for patent in processed_data:
                year = patent.get("year")
                applicant = patent["primary_applicant"]
                
                if year:
                    yearly_applicants[year][applicant] += 1
            
            years = sorted(yearly_applicants.keys())
            if len(years) < 3:
                return {"insufficient_data": True}
            
            # 识别新兴申请人（最近几年快速增长的申请人）
            recent_years = years[-3:]  # 最近3年
            early_years = years[:3] if len(years) >= 6 else years[:-3]
            
            emerging_applicants = []
            
            for applicant in set().union(*[yearly_applicants[year].keys() for year in years]):
                recent_count = sum(yearly_applicants[year].get(applicant, 0) for year in recent_years)
                early_count = sum(yearly_applicants[year].get(applicant, 0) for year in early_years) if early_years else 0
                
                # 计算增长率
                if recent_count >= 3 and (early_count == 0 or recent_count > early_count * 2):
                    growth_rate = ((recent_count - early_count) / max(early_count, 1)) * 100
                    
                    emerging_applicants.append({
                        "applicant": applicant,
                        "recent_patents": recent_count,
                        "early_patents": early_count,
                        "growth_rate": growth_rate,
                        "emergence_type": "new_entrant" if early_count == 0 else "rapid_growth"
                    })
            
            # 按增长率排序
            emerging_applicants.sort(key=lambda x: x["growth_rate"], reverse=True)
            
            return {
                "emerging_applicants": emerging_applicants[:10],
                "total_emerging_count": len(emerging_applicants),
                "analysis_period": f"{min(years)}-{max(years)}"
            }
            
        except Exception as e:
            self.logger.error(f"Error identifying emerging applicants: {str(e)}")
            return {"error": str(e)}
    
    async def _market_concentration_analysis(self, processed_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """市场集中度分析."""
        try:
            # 统计申请人专利数量
            applicant_counts = defaultdict(int)
            for patent in processed_data:
                applicant_counts[patent["primary_applicant"]] += 1
            
            total_patents = len(processed_data)
            sorted_applicants = sorted(applicant_counts.items(), key=lambda x: x[1], reverse=True)
            
            # 计算各种集中度指标
            concentration_metrics = {}
            
            # 1. HHI指数 (Herfindahl-Hirschman Index)
            hhi = sum((count / total_patents) ** 2 for count in applicant_counts.values())
            concentration_metrics["hhi"] = hhi
            
            # 2. CR4 (前4名集中度)
            cr4 = sum(count for _, count in sorted_applicants[:4]) / total_patents if total_patents > 0 else 0
            concentration_metrics["cr4"] = cr4
            
            # 3. CR8 (前8名集中度)
            cr8 = sum(count for _, count in sorted_applicants[:8]) / total_patents if total_patents > 0 else 0
            concentration_metrics["cr8"] = cr8
            
            # 4. 基尼系数
            gini = self._calculate_gini_coefficient([count for _, count in sorted_applicants])
            concentration_metrics["gini"] = gini
            
            # 集中度等级判断
            concentration_level = self._determine_concentration_level(hhi, cr4)
            
            # 市场结构分析
            market_structure = self._analyze_market_structure(concentration_metrics, sorted_applicants)
            
            return {
                "concentration_metrics": concentration_metrics,
                "concentration_level": concentration_level,
                "market_structure": market_structure,
                "top_players_share": {
                    "top_1": (sorted_applicants[0][1] / total_patents) * 100 if sorted_applicants else 0,
                    "top_5": sum(count for _, count in sorted_applicants[:5]) / total_patents * 100 if total_patents > 0 else 0,
                    "top_10": sum(count for _, count in sorted_applicants[:10]) / total_patents * 100 if total_patents > 0 else 0
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in market concentration analysis: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_gini_coefficient(self, values: List[int]) -> float:
        """计算基尼系数."""
        if not values or len(values) == 1:
            return 0.0
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        cumsum = sum(sorted_values)
        
        if cumsum == 0:
            return 0.0
        
        # 基尼系数计算公式
        gini = (2 * sum((i + 1) * val for i, val in enumerate(sorted_values))) / (n * cumsum) - (n + 1) / n
        
        return max(0.0, min(1.0, gini))
    
    def _determine_concentration_level(self, hhi: float, cr4: float) -> str:
        """判断市场集中度等级."""
        if hhi > 0.25 or cr4 > 0.6:
            return "高度集中"
        elif hhi > 0.15 or cr4 > 0.4:
            return "中度集中"
        elif hhi > 0.1 or cr4 > 0.25:
            return "适度集中"
        else:
            return "竞争充分"
    
    def _analyze_market_structure(self, concentration_metrics: Dict[str, float], 
                                sorted_applicants: List[Tuple[str, int]]) -> Dict[str, Any]:
        """分析市场结构."""
        total_applicants = len(sorted_applicants)
        total_patents = sum(count for _, count in sorted_applicants)
        
        # 市场参与者分层
        if total_applicants == 0:
            return {"error": "No applicants data"}
        
        # 领导者（前10%或前5名）
        leaders_count = max(1, min(5, total_applicants // 10))
        leaders = sorted_applicants[:leaders_count]
        leaders_share = sum(count for _, count in leaders) / total_patents * 100 if total_patents > 0 else 0
        
        # 挑战者（接下来的20%）
        challengers_start = leaders_count
        challengers_end = min(total_applicants, leaders_count + max(1, total_applicants // 5))
        challengers = sorted_applicants[challengers_start:challengers_end]
        challengers_share = sum(count for _, count in challengers) / total_patents * 100 if total_patents > 0 else 0
        
        # 跟随者（其余参与者）
        followers = sorted_applicants[challengers_end:]
        followers_share = sum(count for _, count in followers) / total_patents * 100 if total_patents > 0 else 0
        
        # 竞争激烈程度评估
        competition_intensity = self._assess_competition_intensity_from_structure(
            concentration_metrics, leaders_share, total_applicants
        )
        
        return {
            "market_leaders": {
                "count": len(leaders),
                "applicants": [(name, count) for name, count in leaders],
                "market_share": leaders_share
            },
            "market_challengers": {
                "count": len(challengers),
                "market_share": challengers_share
            },
            "market_followers": {
                "count": len(followers),
                "market_share": followers_share
            },
            "competition_intensity": competition_intensity,
            "market_fragmentation": total_applicants / total_patents if total_patents > 0 else 0
        }
    
    def _assess_competition_intensity_from_structure(self, concentration_metrics: Dict[str, float], 
                                                   leaders_share: float, total_applicants: int) -> str:
        """基于市场结构评估竞争激烈程度."""
        hhi = concentration_metrics.get("hhi", 0)
        
        if hhi > 0.25 and leaders_share > 70:
            return "低"  # 高度集中，竞争不激烈
        elif hhi > 0.15 and leaders_share > 50:
            return "中等"  # 中度集中
        elif total_applicants > 50 and leaders_share < 40:
            return "激烈"  # 参与者众多，集中度低
        else:
            return "中等"
    
    async def _competition_landscape_analysis(self, processed_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """竞争格局分析."""
        try:
            # 竞争对手关系分析
            competitor_relationships = self._analyze_competitor_relationships(processed_data)
            
            # 技术竞争分析
            tech_competition = self._analyze_technology_competition(processed_data)
            
            # 竞争态势演变
            competition_evolution = self._analyze_competition_evolution(processed_data)
            
            # 竞争优势分析
            competitive_advantages = self._analyze_competitive_advantages(processed_data)
            
            return {
                "competitor_relationships": competitor_relationships,
                "technology_competition": tech_competition,
                "competition_evolution": competition_evolution,
                "competitive_advantages": competitive_advantages
            }
            
        except Exception as e:
            self.logger.error(f"Error in competition landscape analysis: {str(e)}")
            return {"error": str(e)}
    
    def _analyze_competitor_relationships(self, processed_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析竞争对手关系."""
        # 技术领域重叠分析
        applicant_tech_areas = defaultdict(set)
        
        for patent in processed_data:
            applicant = patent["primary_applicant"]
            ipc_classes = patent.get("ipc_classes", [])
            
            for ipc in ipc_classes:
                if ipc:
                    main_ipc = ipc[:4] if len(ipc) >= 4 else ipc
                    applicant_tech_areas[applicant].add(main_ipc)
        
        # 计算申请人间的技术重叠度
        top_applicants = sorted(applicant_tech_areas.items(), 
                              key=lambda x: len(x[1]), reverse=True)[:10]
        
        competitor_pairs = []
        for i, (app1, tech1) in enumerate(top_applicants):
            for app2, tech2 in top_applicants[i+1:]:
                overlap = len(tech1 & tech2)
                total_tech = len(tech1 | tech2)
                
                if overlap > 0 and total_tech > 0:
                    similarity = overlap / total_tech
                    if similarity > 0.3:  # 技术重叠度超过30%
                        competitor_pairs.append({
                            "applicant_1": app1,
                            "applicant_2": app2,
                            "tech_overlap": overlap,
                            "similarity_score": similarity,
                            "shared_technologies": list(tech1 & tech2)
                        })
        
        # 按相似度排序
        competitor_pairs.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        return {
            "direct_competitors": competitor_pairs[:10],
            "total_competitor_pairs": len(competitor_pairs)
        }
    
    def _analyze_technology_competition(self, processed_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析技术竞争."""
        # 按技术领域统计竞争者
        tech_competitors = defaultdict(lambda: defaultdict(int))
        
        for patent in processed_data:
            applicant = patent["primary_applicant"]
            ipc_classes = patent.get("ipc_classes", [])
            
            for ipc in ipc_classes:
                if ipc:
                    main_ipc = ipc[:4] if len(ipc) >= 4 else ipc
                    tech_competitors[main_ipc][applicant] += 1
        
        # 分析各技术领域的竞争激烈程度
        tech_competition_analysis = {}
        
        for tech, competitors in tech_competitors.items():
            if len(competitors) >= 3:  # 至少3个竞争者
                total_patents = sum(competitors.values())
                sorted_competitors = sorted(competitors.items(), key=lambda x: x[1], reverse=True)
                
                # 计算该技术领域的集中度
                top3_share = sum(count for _, count in sorted_competitors[:3]) / total_patents
                
                tech_competition_analysis[tech] = {
                    "total_competitors": len(competitors),
                    "total_patents": total_patents,
                    "top_competitors": sorted_competitors[:5],
                    "concentration_level": "高" if top3_share > 0.7 else "中" if top3_share > 0.5 else "低",
                    "competition_intensity": "激烈" if len(competitors) > 10 and top3_share < 0.5 else "中等"
                }
        
        # 按专利数量排序技术领域
        sorted_tech_areas = sorted(tech_competition_analysis.items(), 
                                 key=lambda x: x[1]["total_patents"], reverse=True)
        
        return {
            "technology_areas": dict(sorted_tech_areas[:10]),
            "most_competitive_areas": [
                (tech, data) for tech, data in sorted_tech_areas 
                if data["competition_intensity"] == "激烈"
            ][:5]
        }
    
    def _analyze_competition_evolution(self, processed_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析竞争态势演变."""
        # 按年份统计申请人排名变化
        yearly_rankings = defaultdict(lambda: defaultdict(int))
        
        for patent in processed_data:
            year = patent.get("year")
            applicant = patent["primary_applicant"]
            
            if year:
                yearly_rankings[year][applicant] += 1
        
        years = sorted(yearly_rankings.keys())
        if len(years) < 3:
            return {"insufficient_data": True}
        
        # 分析排名变化
        ranking_changes = []
        
        for i in range(1, len(years)):
            prev_year = years[i-1]
            curr_year = years[i]
            
            prev_ranking = sorted(yearly_rankings[prev_year].items(), key=lambda x: x[1], reverse=True)
            curr_ranking = sorted(yearly_rankings[curr_year].items(), key=lambda x: x[1], reverse=True)
            
            # 创建排名映射
            prev_rank_map = {app: rank+1 for rank, (app, _) in enumerate(prev_ranking)}
            curr_rank_map = {app: rank+1 for rank, (app, _) in enumerate(curr_ranking)}
            
            # 分析排名变化
            for app in set(prev_rank_map.keys()) | set(curr_rank_map.keys()):
                prev_rank = prev_rank_map.get(app, 999)  # 999表示未上榜
                curr_rank = curr_rank_map.get(app, 999)
                
                if prev_rank != curr_rank and min(prev_rank, curr_rank) <= 10:  # 只关注前10名的变化
                    ranking_changes.append({
                        "applicant": app,
                        "year_from": prev_year,
                        "year_to": curr_year,
                        "rank_from": prev_rank if prev_rank != 999 else "未上榜",
                        "rank_to": curr_rank if curr_rank != 999 else "未上榜",
                        "change_type": self._classify_ranking_change(prev_rank, curr_rank)
                    })
        
        # 识别持续领先者和新兴挑战者
        consistent_leaders = self._identify_consistent_leaders(yearly_rankings)
        emerging_challengers = self._identify_emerging_challengers(yearly_rankings)
        
        return {
            "ranking_changes": ranking_changes[-20:],  # 最近20个变化
            "consistent_leaders": consistent_leaders,
            "emerging_challengers": emerging_challengers,
            "analysis_period": f"{min(years)}-{max(years)}"
        }
    
    def _classify_ranking_change(self, prev_rank: int, curr_rank: int) -> str:
        """分类排名变化类型."""
        if prev_rank == 999 and curr_rank <= 10:
            return "新进入者"
        elif prev_rank <= 10 and curr_rank == 999:
            return "退出前十"
        elif prev_rank > curr_rank:
            return "排名上升"
        elif prev_rank < curr_rank:
            return "排名下降"
        else:
            return "排名不变"
    
    def _identify_consistent_leaders(self, yearly_rankings: Dict[int, Dict[str, int]]) -> List[Dict[str, Any]]:
        """识别持续领先者."""
        years = sorted(yearly_rankings.keys())
        if len(years) < 3:
            return []
        
        # 统计每个申请人在前5名的出现次数
        top5_appearances = defaultdict(int)
        
        for year in years:
            top5 = sorted(yearly_rankings[year].items(), key=lambda x: x[1], reverse=True)[:5]
            for app, _ in top5:
                top5_appearances[app] += 1
        
        # 识别持续领先者（在大部分年份都在前5名）
        min_appearances = max(1, len(years) * 0.6)  # 至少60%的年份在前5名
        consistent_leaders = [
            {
                "applicant": app,
                "appearances": count,
                "consistency_rate": count / len(years)
            }
            for app, count in top5_appearances.items()
            if count >= min_appearances
        ]
        
        consistent_leaders.sort(key=lambda x: x["consistency_rate"], reverse=True)
        return consistent_leaders[:5]
    
    def _identify_emerging_challengers(self, yearly_rankings: Dict[int, Dict[str, int]]) -> List[Dict[str, Any]]:
        """识别新兴挑战者."""
        years = sorted(yearly_rankings.keys())
        if len(years) < 3:
            return []
        
        recent_years = years[-3:]  # 最近3年
        early_years = years[:3] if len(years) >= 6 else years[:-3]
        
        emerging_challengers = []
        
        # 计算最近几年的平均排名
        for year in recent_years:
            top10 = sorted(yearly_rankings[year].items(), key=lambda x: x[1], reverse=True)[:10]
            
            for rank, (app, count) in enumerate(top10):
                # 检查是否为新兴挑战者
                early_presence = any(app in yearly_rankings[year] for year in early_years)
                
                if not early_presence or rank <= 5:  # 新进入者或排名靠前
                    emerging_challengers.append({
                        "applicant": app,
                        "recent_rank": rank + 1,
                        "recent_patents": count,
                        "emergence_type": "新进入者" if not early_presence else "快速上升"
                    })
        
        # 去重并排序
        unique_challengers = {}
        for challenger in emerging_challengers:
            app = challenger["applicant"]
            if app not in unique_challengers or challenger["recent_rank"] < unique_challengers[app]["recent_rank"]:
                unique_challengers[app] = challenger
        
        result = list(unique_challengers.values())
        result.sort(key=lambda x: x["recent_rank"])
        return result[:5]
    
    def _analyze_competitive_advantages(self, processed_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析竞争优势."""
        # 统计各申请人的竞争优势指标
        applicant_metrics = defaultdict(lambda: {
            "patent_count": 0,
            "tech_diversity": set(),
            "geographic_presence": set(),
            "active_years": set(),
            "recent_activity": 0
        })
        
        current_year = datetime.now().year
        
        for patent in processed_data:
            applicant = patent["primary_applicant"]
            year = patent.get("year")
            country = patent.get("country", "Unknown")
            ipc_classes = patent.get("ipc_classes", [])
            
            metrics = applicant_metrics[applicant]
            metrics["patent_count"] += 1
            metrics["geographic_presence"].add(country)
            
            if year:
                metrics["active_years"].add(year)
                if year >= current_year - 3:  # 最近3年
                    metrics["recent_activity"] += 1
            
            for ipc in ipc_classes:
                if ipc:
                    main_ipc = ipc[:4] if len(ipc) >= 4 else ipc
                    metrics["tech_diversity"].add(main_ipc)
        
        # 计算竞争优势评分
        competitive_analysis = {}
        
        for applicant, metrics in applicant_metrics.items():
            if metrics["patent_count"] >= 5:  # 至少5件专利
                advantages = []
                
                # 专利数量优势
                if metrics["patent_count"] > 50:
                    advantages.append("专利数量优势")
                
                # 技术多样性优势
                if len(metrics["tech_diversity"]) > 5:
                    advantages.append("技术多样性")
                
                # 地域布局优势
                if len(metrics["geographic_presence"]) > 2:
                    advantages.append("国际化布局")
                
                # 持续创新优势
                if len(metrics["active_years"]) > 5:
                    advantages.append("持续创新能力")
                
                # 近期活跃度优势
                if metrics["recent_activity"] > 10:
                    advantages.append("近期高活跃度")
                
                competitive_analysis[applicant] = {
                    "patent_count": metrics["patent_count"],
                    "tech_diversity_score": len(metrics["tech_diversity"]),
                    "geographic_score": len(metrics["geographic_presence"]),
                    "longevity_score": len(metrics["active_years"]),
                    "recent_activity_score": metrics["recent_activity"],
                    "competitive_advantages": advantages,
                    "overall_strength": len(advantages)
                }
        
        # 按综合实力排序
        sorted_analysis = sorted(competitive_analysis.items(), 
                               key=lambda x: x[1]["overall_strength"], reverse=True)
        
        return {
            "top_competitors": dict(sorted_analysis[:10]),
            "advantage_distribution": self._analyze_advantage_distribution(competitive_analysis)
        }
    
    def _analyze_advantage_distribution(self, competitive_analysis: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """分析竞争优势分布."""
        advantage_counts = defaultdict(int)
        
        for _, analysis in competitive_analysis.items():
            for advantage in analysis["competitive_advantages"]:
                advantage_counts[advantage] += 1
        
        return {
            "advantage_frequency": dict(advantage_counts),
            "most_common_advantages": sorted(advantage_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        }
    
    async def _geographic_competition_analysis(self, processed_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """地域竞争分析."""
        try:
            # 按国家统计申请人和专利
            country_stats = defaultdict(lambda: {
                "applicants": set(),
                "patent_count": 0,
                "top_applicants": defaultdict(int)
            })
            
            for patent in processed_data:
                country = patent.get("country", "Unknown")
                applicant = patent["primary_applicant"]
                
                country_stats[country]["applicants"].add(applicant)
                country_stats[country]["patent_count"] += 1
                country_stats[country]["top_applicants"][applicant] += 1
            
            # 转换为可序列化格式并分析
            geographic_analysis = {}
            
            for country, stats in country_stats.items():
                country_name = self.country_mapping.get(country, country)
                
                top_applicants = sorted(stats["top_applicants"].items(), 
                                      key=lambda x: x[1], reverse=True)[:5]
                
                geographic_analysis[country_name] = {
                    "unique_applicants": len(stats["applicants"]),
                    "total_patents": stats["patent_count"],
                    "top_applicants": top_applicants,
                    "market_concentration": self._calculate_country_concentration(stats["top_applicants"])
                }
            
            # 按专利数量排序
            sorted_countries = sorted(geographic_analysis.items(), 
                                    key=lambda x: x[1]["total_patents"], reverse=True)
            
            # 跨国竞争分析
            cross_border_competition = self._analyze_cross_border_competition(processed_data)
            
            return {
                "country_rankings": dict(sorted_countries[:10]),
                "cross_border_competition": cross_border_competition,
                "geographic_diversity": len(geographic_analysis)
            }
            
        except Exception as e:
            self.logger.error(f"Error in geographic competition analysis: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_country_concentration(self, applicant_counts: Dict[str, int]) -> float:
        """计算国家内的市场集中度."""
        if not applicant_counts:
            return 0.0
        
        total = sum(applicant_counts.values())
        hhi = sum((count / total) ** 2 for count in applicant_counts.values())
        return hhi
    
    def _analyze_cross_border_competition(self, processed_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析跨国竞争."""
        # 识别在多个国家有专利申请的申请人
        applicant_countries = defaultdict(set)
        
        for patent in processed_data:
            applicant = patent["primary_applicant"]
            country = patent.get("country", "Unknown")
            applicant_countries[applicant].add(country)
        
        # 找出跨国申请人
        multinational_applicants = {
            app: list(countries) for app, countries in applicant_countries.items()
            if len(countries) > 1
        }
        
        # 分析国家间的竞争关系
        country_pairs = defaultdict(set)
        
        for app, countries in multinational_applicants.items():
            for i, country1 in enumerate(countries):
                for country2 in countries[i+1:]:
                    pair = tuple(sorted([country1, country2]))
                    country_pairs[pair].add(app)
        
        # 按竞争者数量排序国家对
        sorted_pairs = sorted(country_pairs.items(), 
                            key=lambda x: len(x[1]), reverse=True)
        
        return {
            "multinational_applicants": dict(list(multinational_applicants.items())[:10]),
            "competitive_country_pairs": [
                {
                    "countries": list(pair),
                    "competing_applicants": len(competitors),
                    "applicant_examples": list(competitors)[:3]
                }
                for pair, competitors in sorted_pairs[:5]
            ],
            "total_multinational_count": len(multinational_applicants)
        }
    
    async def _temporal_competition_analysis(self, processed_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """时间序列竞争分析."""
        try:
            # 按年份分析竞争态势
            yearly_competition = defaultdict(lambda: {
                "total_patents": 0,
                "applicant_counts": defaultdict(int),
                "new_entrants": set(),
                "active_applicants": set()
            })
            
            all_applicants = set()
            
            for patent in processed_data:
                year = patent.get("year")
                applicant = patent["primary_applicant"]
                
                if year:
                    yearly_competition[year]["total_patents"] += 1
                    yearly_competition[year]["applicant_counts"][applicant] += 1
                    yearly_competition[year]["active_applicants"].add(applicant)
                    all_applicants.add(applicant)
            
            years = sorted(yearly_competition.keys())
            
            # 识别每年的新进入者
            seen_applicants = set()
            for year in years:
                current_applicants = yearly_competition[year]["active_applicants"]
                new_entrants = current_applicants - seen_applicants
                yearly_competition[year]["new_entrants"] = new_entrants
                seen_applicants.update(current_applicants)
            
            # 分析竞争强度变化
            competition_intensity_trend = []
            
            for year in years:
                year_data = yearly_competition[year]
                
                # 计算该年的竞争强度指标
                total_patents = year_data["total_patents"]
                unique_applicants = len(year_data["active_applicants"])
                new_entrants_count = len(year_data["new_entrants"])
                
                # HHI指数
                applicant_counts = year_data["applicant_counts"]
                hhi = sum((count / total_patents) ** 2 for count in applicant_counts.values()) if total_patents > 0 else 0
                
                competition_intensity_trend.append({
                    "year": year,
                    "total_patents": total_patents,
                    "unique_applicants": unique_applicants,
                    "new_entrants": new_entrants_count,
                    "hhi": hhi,
                    "competition_score": self._calculate_yearly_competition_score(
                        unique_applicants, new_entrants_count, hhi, total_patents
                    )
                })
            
            # 分析趋势
            trend_analysis = self._analyze_competition_trends(competition_intensity_trend)
            
            return {
                "yearly_competition_data": competition_intensity_trend,
                "trend_analysis": trend_analysis,
                "analysis_period": f"{min(years)}-{max(years)}" if years else "无数据"
            }
            
        except Exception as e:
            self.logger.error(f"Error in temporal competition analysis: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_yearly_competition_score(self, unique_applicants: int, new_entrants: int, 
                                          hhi: float, total_patents: int) -> float:
        """计算年度竞争评分."""
        # 归一化各项指标
        applicant_score = min(unique_applicants / 50, 1.0)  # 申请人数量，最高50个
        new_entrant_score = min(new_entrants / 10, 1.0)     # 新进入者，最高10个
        concentration_score = 1 - hhi                        # 集中度越低，竞争越激烈
        activity_score = min(total_patents / 100, 1.0)      # 活跃度，最高100件专利
        
        # 加权计算竞争评分
        competition_score = (
            applicant_score * 0.3 +      # 参与者数量权重30%
            new_entrant_score * 0.2 +    # 新进入者权重20%
            concentration_score * 0.3 +  # 市场分散度权重30%
            activity_score * 0.2         # 市场活跃度权重20%
        )
        
        return round(competition_score * 100, 2)  # 转换为百分制
    
    def _analyze_competition_trends(self, competition_intensity_trend: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析竞争趋势."""
        if len(competition_intensity_trend) < 3:
            return {"insufficient_data": True}
        
        # 提取竞争评分序列
        scores = [data["competition_score"] for data in competition_intensity_trend]
        years = [data["year"] for data in competition_intensity_trend]
        
        # 计算趋势
        recent_scores = scores[-3:]  # 最近3年
        early_scores = scores[:3]    # 前3年
        
        recent_avg = sum(recent_scores) / len(recent_scores)
        early_avg = sum(early_scores) / len(early_scores)
        
        # 趋势判断
        if recent_avg > early_avg * 1.1:
            trend_direction = "竞争加剧"
        elif recent_avg < early_avg * 0.9:
            trend_direction = "竞争缓解"
        else:
            trend_direction = "竞争稳定"
        
        # 波动性分析
        score_variance = sum((score - sum(scores)/len(scores)) ** 2 for score in scores) / len(scores)
        volatility = score_variance ** 0.5
        
        return {
            "trend_direction": trend_direction,
            "recent_average_score": recent_avg,
            "early_average_score": early_avg,
            "volatility": volatility,
            "peak_competition_year": years[scores.index(max(scores))],
            "lowest_competition_year": years[scores.index(min(scores))]
        }
    
    async def _competition_intensity_assessment(self, competition_results: Dict[str, Any]) -> Dict[str, Any]:
        """竞争强度综合评估."""
        try:
            assessment = {
                "overall_intensity": "中等",
                "intensity_score": 0.0,
                "key_factors": [],
                "competitive_threats": [],
                "market_opportunities": []
            }
            
            # 收集各项指标
            intensity_factors = []
            
            # 市场集中度因素
            if "market_concentration" in competition_results:
                conc_data = competition_results["market_concentration"]
                concentration_level = conc_data.get("concentration_level", "未知")
                
                if concentration_level == "竞争充分":
                    intensity_factors.append(("市场分散", 0.8))
                elif concentration_level == "适度集中":
                    intensity_factors.append(("适度集中", 0.6))
                elif concentration_level == "中度集中":
                    intensity_factors.append(("中度集中", 0.4))
                else:
                    intensity_factors.append(("高度集中", 0.2))
            
            # 申请人数量因素
            if "applicant_analysis" in competition_results:
                app_data = competition_results["applicant_analysis"]
                total_applicants = app_data.get("total_unique_applicants", 0)
                
                if total_applicants > 100:
                    intensity_factors.append(("参与者众多", 0.8))
                elif total_applicants > 50:
                    intensity_factors.append(("参与者较多", 0.6))
                elif total_applicants > 20:
                    intensity_factors.append(("参与者适中", 0.4))
                else:
                    intensity_factors.append(("参与者较少", 0.2))
            
            # 新兴竞争者因素
            if "applicant_analysis" in competition_results:
                app_data = competition_results["applicant_analysis"]
                emerging_data = app_data.get("emerging_applicants", {})
                emerging_count = emerging_data.get("total_emerging_count", 0)
                
                if emerging_count > 10:
                    intensity_factors.append(("新兴竞争者活跃", 0.7))
                elif emerging_count > 5:
                    intensity_factors.append(("新兴竞争者较多", 0.5))
                else:
                    intensity_factors.append(("新兴竞争者较少", 0.3))
            
            # 计算综合强度评分
            if intensity_factors:
                total_score = sum(score for _, score in intensity_factors)
                assessment["intensity_score"] = total_score / len(intensity_factors)
                
                # 确定强度等级
                if assessment["intensity_score"] > 0.7:
                    assessment["overall_intensity"] = "激烈"
                elif assessment["intensity_score"] > 0.5:
                    assessment["overall_intensity"] = "中等偏高"
                elif assessment["intensity_score"] > 0.3:
                    assessment["overall_intensity"] = "中等"
                else:
                    assessment["overall_intensity"] = "较低"
                
                assessment["key_factors"] = [factor for factor, _ in intensity_factors]
            
            # 识别竞争威胁
            threats = []
            if assessment["intensity_score"] > 0.6:
                threats.append("市场竞争激烈，新进入者面临较高壁垒")
            
            if "competition_landscape" in competition_results:
                landscape_data = competition_results["competition_landscape"]
                tech_competition = landscape_data.get("technology_competition", {})
                competitive_areas = tech_competition.get("most_competitive_areas", [])
                
                if competitive_areas:
                    threats.append(f"技术领域{competitive_areas[0][0]}等存在激烈竞争")
            
            assessment["competitive_threats"] = threats
            
            # 识别市场机会
            opportunities = []
            if assessment["intensity_score"] < 0.4:
                opportunities.append("市场集中度较低，存在发展空间")
            
            if "applicant_analysis" in competition_results:
                app_data = competition_results["applicant_analysis"]
                emerging_data = app_data.get("emerging_applicants", {})
                
                if emerging_data.get("total_emerging_count", 0) > 5:
                    opportunities.append("新兴技术领域活跃，创新机会较多")
            
            assessment["market_opportunities"] = opportunities
            
            return assessment
            
        except Exception as e:
            self.logger.error(f"Error in competition intensity assessment: {str(e)}")
            return {"error": str(e)}
    
    async def _update_performance_metrics(self, processing_time: float, success: bool):
        """更新性能指标."""
        try:
            self.performance_metrics["analysis_count"] += 1
            
            # 更新平均处理时间
            current_avg = self.performance_metrics["average_processing_time"]
            count = self.performance_metrics["analysis_count"]
            
            new_avg = ((current_avg * (count - 1)) + processing_time) / count
            self.performance_metrics["average_processing_time"] = new_avg
            
            # 更新成功率
            if success:
                success_count = self.performance_metrics["success_rate"] * (count - 1) + 1
            else:
                success_count = self.performance_metrics["success_rate"] * (count - 1)
            
            self.performance_metrics["success_rate"] = success_count / count
            
            self.logger.info(f"Competition analysis metrics updated: {json.dumps(self.performance_metrics, ensure_ascii=False)}")
            
        except Exception as e:
            self.logger.error(f"Error updating performance metrics: {str(e)}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标."""
        return self.performance_metrics.copy()