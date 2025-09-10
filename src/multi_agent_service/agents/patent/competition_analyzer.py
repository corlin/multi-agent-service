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
        try:
            years = sorted(yearly_rankings.keys())
            if len(years) < 3:
                return []
            
            # 统计每个申请人在前5名的出现次数
            top5_appearances = defaultdict(int)
            top1_appearances = defaultdict(int)
            
            for year in years:
                year_ranking = sorted(yearly_rankings[year].items(), key=lambda x: x[1], reverse=True)
                
                # 前5名
                for i, (applicant, _) in enumerate(year_ranking[:5]):
                    top5_appearances[applicant] += 1
                    
                    # 第1名
                    if i == 0:
                        top1_appearances[applicant] += 1
            
            # 识别持续领先者（至少在70%的年份中排名前5）
            min_appearances = len(years) * 0.7
            consistent_leaders = []
            
            for applicant, appearances in top5_appearances.items():
                if appearances >= min_appearances:
                    consistency_rate = appearances / len(years)
                    leadership_rate = top1_appearances[applicant] / len(years)
                    
                    consistent_leaders.append({
                        "applicant": applicant,
                        "consistency_rate": consistency_rate,
                        "leadership_rate": leadership_rate,
                        "top5_years": appearances,
                        "top1_years": top1_appearances[applicant],
                        "leadership_type": "dominant" if leadership_rate > 0.5 else "consistent"
                    })
            
            # 按一致性排序
            consistent_leaders.sort(key=lambda x: x["consistency_rate"], reverse=True)
            
            return consistent_leaders[:10]
            
        except Exception as e:
            self.logger.error(f"Error identifying consistent leaders: {str(e)}")
            return []
    
    def _identify_emerging_challengers(self, yearly_rankings: Dict[int, Dict[str, int]]) -> List[Dict[str, Any]]:
        """识别新兴挑战者."""
        try:
            years = sorted(yearly_rankings.keys())
            if len(years) < 4:
                return []
            
            # 分析最近几年vs早期几年的排名变化
            early_years = years[:len(years)//2]
            recent_years = years[len(years)//2:]
            
            # 计算早期和近期的平均排名
            applicant_early_avg = defaultdict(list)
            applicant_recent_avg = defaultdict(list)
            
            for year in early_years:
                year_ranking = sorted(yearly_rankings[year].items(), key=lambda x: x[1], reverse=True)
                for rank, (applicant, _) in enumerate(year_ranking[:20], 1):
                    applicant_early_avg[applicant].append(rank)
            
            for year in recent_years:
                year_ranking = sorted(yearly_rankings[year].items(), key=lambda x: x[1], reverse=True)
                for rank, (applicant, _) in enumerate(year_ranking[:20], 1):
                    applicant_recent_avg[applicant].append(rank)
            
            # 识别新兴挑战者
            emerging_challengers = []
            
            for applicant in set(applicant_recent_avg.keys()):
                recent_ranks = applicant_recent_avg[applicant]
                early_ranks = applicant_early_avg.get(applicant, [])
                
                if len(recent_ranks) >= 2:  # 至少在最近2年有排名
                    recent_avg_rank = sum(recent_ranks) / len(recent_ranks)
                    
                    if early_ranks:
                        early_avg_rank = sum(early_ranks) / len(early_ranks)
                        rank_improvement = early_avg_rank - recent_avg_rank
                        
                        # 排名显著提升的申请人
                        if rank_improvement > 3 and recent_avg_rank <= 10:
                            emerging_challengers.append({
                                "applicant": applicant,
                                "early_avg_rank": early_avg_rank,
                                "recent_avg_rank": recent_avg_rank,
                                "rank_improvement": rank_improvement,
                                "emergence_type": "rising_star",
                                "recent_appearances": len(recent_ranks)
                            })
                    else:
                        # 新进入者
                        if recent_avg_rank <= 15:
                            emerging_challengers.append({
                                "applicant": applicant,
                                "early_avg_rank": None,
                                "recent_avg_rank": recent_avg_rank,
                                "rank_improvement": None,
                                "emergence_type": "new_entrant",
                                "recent_appearances": len(recent_ranks)
                            })
            
            # 按排名改进程度排序
            emerging_challengers.sort(key=lambda x: x.get("rank_improvement", 0) or (20 - x["recent_avg_rank"]), reverse=True)
            
            return emerging_challengers[:10]
            
        except Exception as e:
            self.logger.error(f"Error identifying emerging challengers: {str(e)}")
            return []
    
    def _analyze_competitive_advantages(self, processed_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析竞争优势."""
        try:
            # 统计各申请人的多维度指标
            applicant_metrics = defaultdict(lambda: {
                "patent_count": 0,
                "active_years": set(),
                "tech_areas": set(),
                "countries": set(),
                "recent_activity": 0,
                "tech_diversity": 0,
                "geographic_reach": 0,
                "innovation_consistency": 0
            })
            
            current_year = datetime.now().year
            recent_years = {current_year - i for i in range(3)}  # 最近3年
            
            for patent in processed_data:
                applicant = patent["primary_applicant"]
                year = patent.get("year")
                country = patent.get("country", "Unknown")
                ipc_classes = patent.get("ipc_classes", [])
                
                metrics = applicant_metrics[applicant]
                metrics["patent_count"] += 1
                
                if year:
                    metrics["active_years"].add(year)
                    if year in recent_years:
                        metrics["recent_activity"] += 1
                
                metrics["countries"].add(country)
                
                for ipc in ipc_classes:
                    if ipc:
                        main_ipc = ipc[:4] if len(ipc) >= 4 else ipc
                        metrics["tech_areas"].add(main_ipc)
            
            # 计算竞争优势指标
            competitive_advantages = {}
            
            for applicant, metrics in applicant_metrics.items():
                if metrics["patent_count"] >= 5:  # 只分析有一定规模的申请人
                    
                    # 技术多样性
                    tech_diversity = len(metrics["tech_areas"])
                    
                    # 地理覆盖
                    geographic_reach = len(metrics["countries"])
                    
                    # 创新一致性（活跃年数/总年数）
                    total_years = len(metrics["active_years"])
                    innovation_consistency = total_years / 10 if total_years > 0 else 0  # 假设10年为满分
                    
                    # 近期活跃度
                    recent_activity_rate = metrics["recent_activity"] / metrics["patent_count"]
                    
                    # 综合竞争力评分
                    competitiveness_score = (
                        min(metrics["patent_count"] / 50, 1.0) * 0.3 +  # 专利数量权重30%
                        min(tech_diversity / 10, 1.0) * 0.25 +          # 技术多样性权重25%
                        min(geographic_reach / 5, 1.0) * 0.15 +         # 地理覆盖权重15%
                        min(innovation_consistency, 1.0) * 0.15 +       # 创新一致性权重15%
                        min(recent_activity_rate * 2, 1.0) * 0.15       # 近期活跃度权重15%
                    )
                    
                    # 识别核心优势
                    core_advantages = []
                    if metrics["patent_count"] > 30:
                        core_advantages.append("专利数量优势")
                    if tech_diversity > 5:
                        core_advantages.append("技术多元化")
                    if geographic_reach > 2:
                        core_advantages.append("国际化布局")
                    if recent_activity_rate > 0.5:
                        core_advantages.append("持续创新能力")
                    if innovation_consistency > 0.7:
                        core_advantages.append("长期稳定发展")
                    
                    competitive_advantages[applicant] = {
                        "competitiveness_score": competitiveness_score,
                        "patent_count": metrics["patent_count"],
                        "tech_diversity": tech_diversity,
                        "geographic_reach": geographic_reach,
                        "innovation_consistency": innovation_consistency,
                        "recent_activity_rate": recent_activity_rate,
                        "core_advantages": core_advantages,
                        "competitive_tier": self._determine_competitive_tier(competitiveness_score)
                    }
            
            # 排序并返回前20名
            sorted_competitors = sorted(
                competitive_advantages.items(),
                key=lambda x: x[1]["competitiveness_score"],
                reverse=True
            )[:20]
            
            return {
                "competitive_rankings": sorted_competitors,
                "tier_distribution": self._analyze_tier_distribution(competitive_advantages),
                "advantage_patterns": self._analyze_advantage_patterns(competitive_advantages)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing competitive advantages: {str(e)}")
            return {"error": str(e)}
    
    def _determine_competitive_tier(self, score: float) -> str:
        """确定竞争层级."""
        if score >= 0.8:
            return "领导者"
        elif score >= 0.6:
            return "挑战者"
        elif score >= 0.4:
            return "跟随者"
        else:
            return "补缺者"
    
    def _analyze_tier_distribution(self, competitive_advantages: Dict[str, Dict[str, Any]]) -> Dict[str, int]:
        """分析竞争层级分布."""
        tier_counts = defaultdict(int)
        
        for advantages in competitive_advantages.values():
            tier = advantages["competitive_tier"]
            tier_counts[tier] += 1
        
        return dict(tier_counts)
    
    def _analyze_advantage_patterns(self, competitive_advantages: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """分析优势模式."""
        try:
            patterns = {
                "most_common_advantages": defaultdict(int),
                "advantage_combinations": defaultdict(int),
                "success_factors": []
            }
            
            # 统计最常见的优势
            for advantages in competitive_advantages.values():
                for advantage in advantages["core_advantages"]:
                    patterns["most_common_advantages"][advantage] += 1
            
            # 分析优势组合
            for advantages in competitive_advantages.values():
                if len(advantages["core_advantages"]) > 1:
                    combo = tuple(sorted(advantages["core_advantages"]))
                    patterns["advantage_combinations"][combo] += 1
            
            # 识别成功因素
            top_performers = [
                adv for adv in competitive_advantages.values()
                if adv["competitiveness_score"] > 0.7
            ]
            
            if top_performers:
                avg_patent_count = sum(p["patent_count"] for p in top_performers) / len(top_performers)
                avg_tech_diversity = sum(p["tech_diversity"] for p in top_performers) / len(top_performers)
                
                if avg_patent_count > 25:
                    patterns["success_factors"].append("高专利产出是成功的关键因素")
                if avg_tech_diversity > 4:
                    patterns["success_factors"].append("技术多元化有助于提升竞争力")
            
            return {
                "most_common_advantages": dict(patterns["most_common_advantages"]),
                "top_advantage_combinations": sorted(
                    patterns["advantage_combinations"].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5],
                "success_factors": patterns["success_factors"]
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing advantage patterns: {str(e)}")
            return {}
    
    async def _geographic_competition_analysis(self, processed_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """地域竞争分析."""
        try:
            # 按国家统计申请人和专利
            country_competition = defaultdict(lambda: {
                "applicants": set(),
                "patent_count": 0,
                "top_applicants": defaultdict(int)
            })
            
            for patent in processed_data:
                country = patent.get("country", "Unknown")
                applicant = patent["primary_applicant"]
                
                country_competition[country]["applicants"].add(applicant)
                country_competition[country]["patent_count"] += 1
                country_competition[country]["top_applicants"][applicant] += 1
            
            # 分析各国竞争格局
            country_analysis = {}
            
            for country, data in country_competition.items():
                if data["patent_count"] >= 5:  # 只分析有一定规模的国家
                    
                    # 计算该国的市场集中度
                    applicant_counts = list(data["top_applicants"].values())
                    total_patents = sum(applicant_counts)
                    
                    # HHI指数
                    hhi = sum((count / total_patents) ** 2 for count in applicant_counts)
                    
                    # 前3名集中度
                    sorted_applicants = sorted(data["top_applicants"].items(), key=lambda x: x[1], reverse=True)
                    cr3 = sum(count for _, count in sorted_applicants[:3]) / total_patents if total_patents > 0 else 0
                    
                    country_analysis[country] = {
                        "patent_count": data["patent_count"],
                        "unique_applicants": len(data["applicants"]),
                        "market_concentration_hhi": hhi,
                        "cr3_concentration": cr3,
                        "top_applicants": sorted_applicants[:5],
                        "competition_level": self._assess_country_competition_level(hhi, len(data["applicants"]))
                    }
            
            # 跨国竞争分析
            cross_border_analysis = self._analyze_cross_border_competition(processed_data)
            
            # 地域竞争强度排名
            competition_intensity_ranking = sorted(
                country_analysis.items(),
                key=lambda x: (1 - x[1]["market_concentration_hhi"]) * x[1]["unique_applicants"],
                reverse=True
            )
            
            return {
                "country_competition": country_analysis,
                "cross_border_competition": cross_border_analysis,
                "competition_intensity_ranking": competition_intensity_ranking[:10],
                "global_competition_summary": self._generate_global_competition_summary(country_analysis)
            }
            
        except Exception as e:
            self.logger.error(f"Error in geographic competition analysis: {str(e)}")
            return {"error": str(e)}
    
    def _assess_country_competition_level(self, hhi: float, applicant_count: int) -> str:
        """评估国家竞争水平."""
        if hhi > 0.25 or applicant_count < 5:
            return "低竞争"
        elif hhi > 0.15 or applicant_count < 15:
            return "中等竞争"
        else:
            return "激烈竞争"
    
    def _analyze_cross_border_competition(self, processed_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析跨国竞争."""
        try:
            # 识别在多个国家有专利申请的申请人
            applicant_countries = defaultdict(set)
            
            for patent in processed_data:
                applicant = patent["primary_applicant"]
                country = patent.get("country", "Unknown")
                applicant_countries[applicant].add(country)
            
            # 跨国申请人分析
            multinational_applicants = []
            
            for applicant, countries in applicant_countries.items():
                if len(countries) > 1:
                    multinational_applicants.append({
                        "applicant": applicant,
                        "countries": list(countries),
                        "country_count": len(countries),
                        "globalization_score": min(len(countries) / 5, 1.0)  # 5个国家为满分
                    })
            
            # 按国际化程度排序
            multinational_applicants.sort(key=lambda x: x["country_count"], reverse=True)
            
            # 国际竞争热点分析
            country_pairs = defaultdict(set)
            
            for applicant, countries in applicant_countries.items():
                if len(countries) > 1:
                    countries_list = sorted(list(countries))
                    for i in range(len(countries_list)):
                        for j in range(i + 1, len(countries_list)):
                            pair = (countries_list[i], countries_list[j])
                            country_pairs[pair].add(applicant)
            
            # 找出竞争最激烈的国家对
            competitive_pairs = [
                {
                    "country_pair": pair,
                    "competing_applicants": len(applicants),
                    "applicants": list(applicants)[:5]  # 只显示前5个
                }
                for pair, applicants in country_pairs.items()
                if len(applicants) >= 3
            ]
            
            competitive_pairs.sort(key=lambda x: x["competing_applicants"], reverse=True)
            
            return {
                "multinational_applicants": multinational_applicants[:15],
                "competitive_country_pairs": competitive_pairs[:10],
                "globalization_trends": {
                    "total_multinational_count": len(multinational_applicants),
                    "avg_countries_per_applicant": sum(len(countries) for countries in applicant_countries.values()) / len(applicant_countries),
                    "most_globalized": multinational_applicants[0] if multinational_applicants else None
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing cross-border competition: {str(e)}")
            return {}
    
    def _generate_global_competition_summary(self, country_analysis: Dict[str, Dict[str, Any]]) -> str:
        """生成全球竞争格局总结."""
        try:
            if not country_analysis:
                return "数据不足，无法生成竞争格局总结"
            
            # 统计各竞争水平的国家数量
            competition_levels = defaultdict(int)
            for data in country_analysis.values():
                level = data["competition_level"]
                competition_levels[level] += 1
            
            # 找出专利数量最多的国家
            top_country = max(country_analysis.items(), key=lambda x: x[1]["patent_count"])
            
            # 找出竞争最激烈的国家
            most_competitive = min(country_analysis.items(), key=lambda x: x[1]["market_concentration_hhi"])
            
            summary_parts = [
                f"全球共有{len(country_analysis)}个主要国家/地区参与竞争",
                f"其中{competition_levels.get('激烈竞争', 0)}个地区竞争激烈，{competition_levels.get('中等竞争', 0)}个地区竞争适中",
                f"{top_country[0]}是专利申请最活跃的地区（{top_country[1]['patent_count']}件）",
                f"{most_competitive[0]}的市场竞争最为激烈"
            ]
            
            return "，".join(summary_parts)
            
        except Exception as e:
            self.logger.error(f"Error generating global competition summary: {str(e)}")
            return "竞争格局总结生成失败"
    
    async def _temporal_competition_analysis(self, processed_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """时间序列竞争分析."""
        try:
            # 按年份分析竞争格局变化
            yearly_competition = defaultdict(lambda: defaultdict(int))
            
            for patent in processed_data:
                year = patent.get("year")
                applicant = patent["primary_applicant"]
                
                if year:
                    yearly_competition[year][applicant] += 1
            
            years = sorted(yearly_competition.keys())
            if len(years) < 3:
                return {"insufficient_data": True}
            
            # 分析竞争格局演变
            competition_evolution = {}
            
            for year in years:
                year_data = yearly_competition[year]
                total_patents = sum(year_data.values())
                
                if total_patents > 0:
                    # 计算年度HHI
                    hhi = sum((count / total_patents) ** 2 for count in year_data.values())
                    
                    # 前5名集中度
                    sorted_applicants = sorted(year_data.items(), key=lambda x: x[1], reverse=True)
                    cr5 = sum(count for _, count in sorted_applicants[:5]) / total_patents
                    
                    competition_evolution[year] = {
                        "total_patents": total_patents,
                        "unique_applicants": len(year_data),
                        "hhi": hhi,
                        "cr5": cr5,
                        "top_applicant": sorted_applicants[0] if sorted_applicants else None,
                        "competition_intensity": self._calculate_competition_intensity(hhi, len(year_data))
                    }
            
            # 分析竞争趋势
            competition_trends = self._analyze_competition_trends(competition_evolution)
            
            # 市场进入和退出分析
            entry_exit_analysis = self._analyze_market_entry_exit(yearly_competition)
            
            return {
                "yearly_competition_evolution": competition_evolution,
                "competition_trends": competition_trends,
                "market_dynamics": entry_exit_analysis,
                "temporal_summary": self._generate_temporal_summary(competition_trends)
            }
            
        except Exception as e:
            self.logger.error(f"Error in temporal competition analysis: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_competition_intensity(self, hhi: float, applicant_count: int) -> float:
        """计算竞争强度."""
        # 竞争强度 = (1 - HHI) * log(申请人数量)
        import math
        
        if applicant_count <= 1:
            return 0.0
        
        intensity = (1 - hhi) * math.log(applicant_count)
        return min(intensity, 1.0)  # 标准化到0-1
    
    def _analyze_competition_trends(self, competition_evolution: Dict[int, Dict[str, Any]]) -> Dict[str, Any]:
        """分析竞争趋势."""
        try:
            years = sorted(competition_evolution.keys())
            
            if len(years) < 3:
                return {"insufficient_data": True}
            
            # 提取时间序列数据
            hhi_series = [competition_evolution[year]["hhi"] for year in years]
            applicant_count_series = [competition_evolution[year]["unique_applicants"] for year in years]
            intensity_series = [competition_evolution[year]["competition_intensity"] for year in years]
            
            # 计算趋势
            trends = {
                "concentration_trend": self._calculate_trend_direction(hhi_series),
                "participation_trend": self._calculate_trend_direction(applicant_count_series),
                "intensity_trend": self._calculate_trend_direction(intensity_series)
            }
            
            # 趋势强度
            trends["concentration_trend_strength"] = self._calculate_trend_strength(hhi_series)
            trends["participation_trend_strength"] = self._calculate_trend_strength(applicant_count_series)
            trends["intensity_trend_strength"] = self._calculate_trend_strength(intensity_series)
            
            # 综合趋势评估
            trends["overall_trend"] = self._assess_overall_competition_trend(trends)
            
            return trends
            
        except Exception as e:
            self.logger.error(f"Error analyzing competition trends: {str(e)}")
            return {}
    
    def _calculate_trend_direction(self, series: List[float]) -> str:
        """计算趋势方向."""
        if len(series) < 2:
            return "stable"
        
        # 简单线性回归计算斜率
        n = len(series)
        x_sum = sum(range(n))
        y_sum = sum(series)
        xy_sum = sum(i * series[i] for i in range(n))
        x2_sum = sum(i * i for i in range(n))
        
        if n * x2_sum - x_sum * x_sum != 0:
            slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
            
            if slope > 0.01:
                return "increasing"
            elif slope < -0.01:
                return "decreasing"
            else:
                return "stable"
        
        return "stable"
    
    def _calculate_trend_strength(self, series: List[float]) -> float:
        """计算趋势强度."""
        if len(series) < 3:
            return 0.0
        
        # 计算相关系数作为趋势强度
        n = len(series)
        x = list(range(n))
        
        mean_x = sum(x) / n
        mean_y = sum(series) / n
        
        numerator = sum((x[i] - mean_x) * (series[i] - mean_y) for i in range(n))
        denominator_x = sum((x[i] - mean_x) ** 2 for i in range(n))
        denominator_y = sum((series[i] - mean_y) ** 2 for i in range(n))
        
        if denominator_x > 0 and denominator_y > 0:
            correlation = numerator / (denominator_x * denominator_y) ** 0.5
            return abs(correlation)
        
        return 0.0
    
    def _assess_overall_competition_trend(self, trends: Dict[str, Any]) -> str:
        """评估整体竞争趋势."""
        concentration_trend = trends.get("concentration_trend", "stable")
        participation_trend = trends.get("participation_trend", "stable")
        intensity_trend = trends.get("intensity_trend", "stable")
        
        # 竞争加剧：集中度下降，参与者增加，强度上升
        if (concentration_trend == "decreasing" and 
            participation_trend == "increasing" and 
            intensity_trend == "increasing"):
            return "竞争加剧"
        
        # 竞争缓解：集中度上升，参与者减少，强度下降
        elif (concentration_trend == "increasing" and 
              participation_trend == "decreasing" and 
              intensity_trend == "decreasing"):
            return "竞争缓解"
        
        # 市场整合：集中度上升，但强度可能仍然较高
        elif concentration_trend == "increasing" and participation_trend == "decreasing":
            return "市场整合"
        
        # 市场扩张：参与者增加，但集中度变化不明显
        elif participation_trend == "increasing":
            return "市场扩张"
        
        else:
            return "竞争稳定"
    
    def _analyze_market_entry_exit(self, yearly_competition: Dict[int, Dict[str, int]]) -> Dict[str, Any]:
        """分析市场进入和退出."""
        try:
            years = sorted(yearly_competition.keys())
            
            if len(years) < 2:
                return {"insufficient_data": True}
            
            entry_exit_data = {}
            
            for i in range(1, len(years)):
                prev_year = years[i - 1]
                curr_year = years[i]
                
                prev_applicants = set(yearly_competition[prev_year].keys())
                curr_applicants = set(yearly_competition[curr_year].keys())
                
                # 新进入者
                new_entrants = curr_applicants - prev_applicants
                
                # 退出者
                exiters = prev_applicants - curr_applicants
                
                # 持续参与者
                continuing = prev_applicants & curr_applicants
                
                entry_exit_data[curr_year] = {
                    "new_entrants": len(new_entrants),
                    "exiters": len(exiters),
                    "continuing_participants": len(continuing),
                    "net_entry": len(new_entrants) - len(exiters),
                    "turnover_rate": (len(new_entrants) + len(exiters)) / len(prev_applicants | curr_applicants)
                }
            
            # 计算平均指标
            avg_metrics = {
                "avg_new_entrants": sum(data["new_entrants"] for data in entry_exit_data.values()) / len(entry_exit_data),
                "avg_exiters": sum(data["exiters"] for data in entry_exit_data.values()) / len(entry_exit_data),
                "avg_turnover_rate": sum(data["turnover_rate"] for data in entry_exit_data.values()) / len(entry_exit_data)
            }
            
            # 市场动态评估
            market_dynamism = self._assess_market_dynamism(avg_metrics)
            
            return {
                "yearly_entry_exit": entry_exit_data,
                "average_metrics": avg_metrics,
                "market_dynamism": market_dynamism
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing market entry/exit: {str(e)}")
            return {}
    
    def _assess_market_dynamism(self, avg_metrics: Dict[str, float]) -> str:
        """评估市场动态性."""
        turnover_rate = avg_metrics.get("avg_turnover_rate", 0)
        
        if turnover_rate > 0.3:
            return "高度动态"
        elif turnover_rate > 0.15:
            return "中等动态"
        else:
            return "相对稳定"
    
    def _generate_temporal_summary(self, competition_trends: Dict[str, Any]) -> str:
        """生成时间序列竞争总结."""
        try:
            overall_trend = competition_trends.get("overall_trend", "竞争稳定")
            concentration_trend = competition_trends.get("concentration_trend", "stable")
            participation_trend = competition_trends.get("participation_trend", "stable")
            
            summary_parts = [f"整体竞争态势呈现{overall_trend}的特征"]
            
            if concentration_trend == "decreasing":
                summary_parts.append("市场集中度逐步下降")
            elif concentration_trend == "increasing":
                summary_parts.append("市场集中度有所提升")
            
            if participation_trend == "increasing":
                summary_parts.append("参与竞争的主体数量增加")
            elif participation_trend == "decreasing":
                summary_parts.append("市场参与者数量减少")
            
            return "，".join(summary_parts)
            
        except Exception as e:
            self.logger.error(f"Error generating temporal summary: {str(e)}")
            return "时间序列竞争分析总结生成失败"
    
    async def _competition_intensity_assessment(self, competition_results: Dict[str, Any]) -> Dict[str, Any]:
        """竞争强度评估."""
        try:
            intensity_factors = {}
            
            # 基于市场集中度的评估
            if "market_concentration" in competition_results:
                concentration_data = competition_results["market_concentration"]
                hhi = concentration_data.get("concentration_metrics", {}).get("hhi", 0.5)
                
                if hhi < 0.15:
                    intensity_factors["concentration_intensity"] = "高"
                elif hhi < 0.25:
                    intensity_factors["concentration_intensity"] = "中"
                else:
                    intensity_factors["concentration_intensity"] = "低"
            
            # 基于申请人分析的评估
            if "applicant_analysis" in competition_results:
                applicant_data = competition_results["applicant_analysis"]
                total_applicants = applicant_data.get("total_unique_applicants", 0)
                
                if total_applicants > 50:
                    intensity_factors["participation_intensity"] = "高"
                elif total_applicants > 20:
                    intensity_factors["participation_intensity"] = "中"
                else:
                    intensity_factors["participation_intensity"] = "低"
            
            # 基于时间序列分析的评估
            if "temporal_competition" in competition_results:
                temporal_data = competition_results["temporal_competition"]
                overall_trend = temporal_data.get("competition_trends", {}).get("overall_trend", "竞争稳定")
                
                if "加剧" in overall_trend:
                    intensity_factors["temporal_intensity"] = "高"
                elif "缓解" in overall_trend:
                    intensity_factors["temporal_intensity"] = "低"
                else:
                    intensity_factors["temporal_intensity"] = "中"
            
            # 综合竞争强度评估
            overall_intensity = self._calculate_overall_intensity(intensity_factors)
            
            # 竞争风险评估
            competition_risks = self._assess_competition_risks(competition_results, overall_intensity)
            
            # 竞争机会识别
            competition_opportunities = self._identify_competition_opportunities(competition_results, overall_intensity)
            
            return {
                "intensity_factors": intensity_factors,
                "overall_intensity": overall_intensity,
                "intensity_score": self._calculate_intensity_score(intensity_factors),
                "competition_risks": competition_risks,
                "competition_opportunities": competition_opportunities,
                "strategic_recommendations": self._generate_strategic_recommendations(overall_intensity, competition_risks, competition_opportunities)
            }
            
        except Exception as e:
            self.logger.error(f"Error in competition intensity assessment: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_overall_intensity(self, intensity_factors: Dict[str, str]) -> str:
        """计算整体竞争强度."""
        intensity_scores = {"高": 3, "中": 2, "低": 1}
        
        total_score = sum(intensity_scores.get(level, 2) for level in intensity_factors.values())
        avg_score = total_score / len(intensity_factors) if intensity_factors else 2
        
        if avg_score >= 2.5:
            return "激烈"
        elif avg_score >= 1.5:
            return "适中"
        else:
            return "温和"
    
    def _calculate_intensity_score(self, intensity_factors: Dict[str, str]) -> float:
        """计算竞争强度评分."""
        intensity_scores = {"高": 1.0, "中": 0.6, "低": 0.3}
        
        if not intensity_factors:
            return 0.5
        
        total_score = sum(intensity_scores.get(level, 0.5) for level in intensity_factors.values())
        return total_score / len(intensity_factors)
    
    def _assess_competition_risks(self, competition_results: Dict[str, Any], overall_intensity: str) -> List[str]:
        """评估竞争风险."""
        risks = []
        
        if overall_intensity == "激烈":
            risks.append("市场竞争激烈，新进入者面临较高壁垒")
            risks.append("价格竞争可能加剧，影响盈利能力")
        
        # 基于市场集中度的风险
        if "market_concentration" in competition_results:
            concentration_data = competition_results["market_concentration"]
            concentration_level = concentration_data.get("concentration_level", "")
            
            if concentration_level == "高度集中":
                risks.append("市场被少数企业垄断，竞争地位难以撼动")
            elif concentration_level == "竞争充分":
                risks.append("市场过度分散，难以形成规模优势")
        
        # 基于新兴申请人的风险
        if "applicant_analysis" in competition_results:
            applicant_data = competition_results["applicant_analysis"]
            emerging_applicants = applicant_data.get("emerging_applicants", {})
            
            if emerging_applicants.get("total_emerging_count", 0) > 5:
                risks.append("新兴竞争者快速崛起，可能改变竞争格局")
        
        return risks
    
    def _identify_competition_opportunities(self, competition_results: Dict[str, Any], overall_intensity: str) -> List[str]:
        """识别竞争机会."""
        opportunities = []
        
        if overall_intensity == "温和":
            opportunities.append("竞争相对温和，适合新进入者布局")
        
        # 基于地域竞争的机会
        if "geographic_competition" in competition_results:
            geo_data = competition_results["geographic_competition"]
            country_competition = geo_data.get("country_competition", {})
            
            low_competition_countries = [
                country for country, data in country_competition.items()
                if data.get("competition_level") == "低竞争"
            ]
            
            if low_competition_countries:
                opportunities.append(f"可考虑在{low_competition_countries[:3]}等竞争较弱的地区加强布局")
        
        # 基于技术竞争的机会
        if "competition_landscape" in competition_results:
            landscape_data = competition_results["competition_landscape"]
            tech_competition = landscape_data.get("technology_competition", {})
            
            moderate_competition_areas = [
                tech for tech, data in tech_competition.get("technology_areas", {}).items()
                if data.get("competition_intensity") == "中等"
            ]
            
            if moderate_competition_areas:
                opportunities.append(f"在{moderate_competition_areas[:2]}等技术领域存在发展机会")
        
        return opportunities
    
    def _generate_strategic_recommendations(self, overall_intensity: str, risks: List[str], opportunities: List[str]) -> List[str]:
        """生成战略建议."""
        recommendations = []
        
        if overall_intensity == "激烈":
            recommendations.extend([
                "加强技术创新，形成差异化竞争优势",
                "考虑战略联盟或并购，提升市场地位",
                "重点关注细分市场，避免正面竞争"
            ])
        elif overall_intensity == "适中":
            recommendations.extend([
                "保持技术领先，巩固现有市场地位",
                "适度扩张，抢占市场份额",
                "建立品牌优势，提升客户忠诚度"
            ])
        else:  # 温和
            recommendations.extend([
                "积极扩张市场份额，建立先发优势",
                "加大研发投入，构建技术壁垒",
                "快速占领关键市场和客户资源"
            ])
        
        # 基于风险的建议
        if len(risks) > 3:
            recommendations.append("制定风险应对预案，提升抗风险能力")
        
        # 基于机会的建议
        if len(opportunities) > 2:
            recommendations.append("积极把握市场机会，制定针对性发展策略")
        
        return recommendations[:5]  # 返回前5个建议
    
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
            
        except Exception as e:
            self.logger.error(f"Error updating performance metrics: {str(e)}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标."""
        return self.performance_metrics.copy()