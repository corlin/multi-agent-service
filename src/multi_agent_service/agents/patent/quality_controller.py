"""Analysis quality control system for patent analysis results."""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)


class AnalysisQualityController:
    """分析结果质量控制系统，实现结果验证、异常检测、缓存和版本管理."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.AnalysisQualityController")
        
        # 质量控制配置
        self.quality_config = {
            "min_data_threshold": 10,           # 最小数据量阈值
            "confidence_threshold": 0.7,        # 置信度阈值
            "consistency_threshold": 0.8,       # 一致性阈值
            "completeness_threshold": 0.9,      # 完整性阈值
            "anomaly_detection_enabled": True,  # 异常检测开关
            "version_retention_days": 30        # 版本保留天数
        }
        
        # 质量评估权重
        self.quality_weights = {
            "data_completeness": 0.25,    # 数据完整性权重
            "result_consistency": 0.25,   # 结果一致性权重
            "statistical_validity": 0.20, # 统计有效性权重
            "logical_coherence": 0.15,    # 逻辑连贯性权重
            "temporal_stability": 0.15    # 时间稳定性权重
        }
        
        # 缓存和版本管理
        self.result_cache = {}
        self.version_history = defaultdict(list)
        
        # 性能监控
        self.performance_metrics = {
            "validation_count": 0,
            "average_validation_time": 0.0,
            "quality_pass_rate": 0.0,
            "anomaly_detection_rate": 0.0
        }
    
    async def validate_analysis_results(self, analysis_results: Dict[str, Any], 
                                      analysis_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """验证分析结果质量."""
        start_time = datetime.now()
        
        try:
            self.logger.info("Starting analysis results validation")
            
            # 生成结果ID用于缓存和版本管理
            result_id = self._generate_result_id(analysis_results)
            
            # 检查缓存
            cached_validation = await self._get_cached_validation(result_id)
            if cached_validation:
                self.logger.info("Returning cached validation results")
                return cached_validation
            
            # 执行多维度质量验证
            validation_results = {}
            
            # 1. 数据完整性检查
            completeness_check = await self._check_data_completeness(analysis_results)
            validation_results["completeness"] = completeness_check
            
            # 2. 结果一致性验证
            consistency_check = await self._check_result_consistency(analysis_results)
            validation_results["consistency"] = consistency_check
            
            # 3. 统计有效性验证
            statistical_validity = await self._check_statistical_validity(analysis_results)
            validation_results["statistical_validity"] = statistical_validity
            
            # 4. 逻辑连贯性检查
            logical_coherence = await self._check_logical_coherence(analysis_results)
            validation_results["logical_coherence"] = logical_coherence
            
            # 5. 时间稳定性检查
            temporal_stability = await self._check_temporal_stability(analysis_results, result_id)
            validation_results["temporal_stability"] = temporal_stability
            
            # 6. 异常检测
            if self.quality_config["anomaly_detection_enabled"]:
                anomaly_detection = await self._detect_anomalies(analysis_results)
                validation_results["anomaly_detection"] = anomaly_detection
            
            # 7. 综合质量评估
            overall_quality = await self._calculate_overall_quality(validation_results)
            
            # 8. 生成质量报告
            quality_report = await self._generate_quality_report(validation_results, overall_quality)
            
            # 9. 版本管理和缓存
            await self._manage_result_version(result_id, analysis_results, quality_report)
            await self._cache_validation_results(result_id, quality_report)
            
            # 记录性能指标
            processing_time = (datetime.now() - start_time).total_seconds()
            await self._update_performance_metrics(processing_time, quality_report["overall_quality"])
            
            self.logger.info(f"Analysis validation completed in {processing_time:.2f}s")
            
            return quality_report
            
        except Exception as e:
            self.logger.error(f"Error in analysis results validation: {str(e)}")
            
            # 记录失败指标
            processing_time = (datetime.now() - start_time).total_seconds()
            await self._update_performance_metrics(processing_time, 0.0)
            
            return {
                "overall_quality": 0.0,
                "validation_status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _generate_result_id(self, analysis_results: Dict[str, Any]) -> str:
        """生成分析结果ID."""
        try:
            # 创建结果的哈希值作为ID
            result_str = json.dumps(analysis_results, sort_keys=True, ensure_ascii=False)
            result_hash = hashlib.md5(result_str.encode('utf-8')).hexdigest()
            return f"analysis_{result_hash[:16]}"
        except Exception as e:
            self.logger.warning(f"Error generating result ID: {str(e)}")
            return f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    async def _get_cached_validation(self, result_id: str) -> Optional[Dict[str, Any]]:
        """获取缓存的验证结果."""
        try:
            cached_result = self.result_cache.get(result_id)
            if cached_result:
                # 检查缓存是否过期
                cache_time = cached_result.get("cache_timestamp", 0)
                current_time = datetime.now().timestamp()
                
                if current_time - cache_time < 3600:  # 1小时缓存
                    return cached_result.get("validation_result")
                else:
                    # 清理过期缓存
                    del self.result_cache[result_id]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting cached validation: {str(e)}")
            return None
    
    async def _check_data_completeness(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """检查数据完整性."""
        try:
            completeness_scores = {}
            
            # 检查必需的分析模块
            required_modules = ["trend", "competition", "technology"]
            present_modules = []
            
            for module in required_modules:
                if module in analysis_results and analysis_results[module].get("success", False):
                    present_modules.append(module)
            
            module_completeness = len(present_modules) / len(required_modules)
            completeness_scores["module_completeness"] = module_completeness
            
            # 检查每个模块的数据完整性
            module_data_completeness = {}
            
            for module in present_modules:
                module_data = analysis_results[module]
                data_completeness = self._assess_module_data_completeness(module, module_data)
                module_data_completeness[module] = data_completeness
            
            # 计算平均数据完整性
            avg_data_completeness = (
                sum(module_data_completeness.values()) / len(module_data_completeness)
                if module_data_completeness else 0.0
            )
            
            completeness_scores["data_completeness"] = avg_data_completeness
            
            # 综合完整性评分
            overall_completeness = (module_completeness + avg_data_completeness) / 2
            
            return {
                "overall_completeness": overall_completeness,
                "module_completeness": module_completeness,
                "data_completeness": avg_data_completeness,
                "present_modules": present_modules,
                "module_scores": module_data_completeness,
                "pass_threshold": self.quality_config["completeness_threshold"],
                "status": "pass" if overall_completeness >= self.quality_config["completeness_threshold"] else "fail"
            }
            
        except Exception as e:
            self.logger.error(f"Error checking data completeness: {str(e)}")
            return {"overall_completeness": 0.0, "error": str(e)}
    
    def _assess_module_data_completeness(self, module_name: str, module_data: Dict[str, Any]) -> float:
        """评估模块数据完整性."""
        try:
            if module_name == "trend":
                required_fields = ["yearly_counts", "growth_rates", "trend_direction"]
                present_fields = sum(1 for field in required_fields if field in module_data)
                return present_fields / len(required_fields)
            
            elif module_name == "competition":
                required_fields = ["top_applicants", "market_concentration", "applicant_distribution"]
                present_fields = sum(1 for field in required_fields if field in module_data)
                return present_fields / len(required_fields)
            
            elif module_name == "technology":
                required_fields = ["ipc_distribution", "main_technologies", "keyword_clusters"]
                present_fields = sum(1 for field in required_fields if field in module_data)
                return present_fields / len(required_fields)
            
            else:
                # 通用完整性检查
                return 0.8 if module_data else 0.0
                
        except Exception as e:
            self.logger.error(f"Error assessing module data completeness: {str(e)}")
            return 0.0
    
    async def _check_result_consistency(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """检查结果一致性."""
        try:
            consistency_checks = []
            
            # 1. 数据量一致性检查
            data_counts = {}
            for module_name, module_data in analysis_results.items():
                if isinstance(module_data, dict) and module_data.get("success", False):
                    # 提取数据量信息
                    if "total_patents" in module_data:
                        data_counts[module_name] = module_data["total_patents"]
                    elif "data_count" in module_data:
                        data_counts[module_name] = module_data["data_count"]
            
            # 检查数据量是否一致
            if len(set(data_counts.values())) <= 1:
                consistency_checks.append(("data_count_consistency", 1.0))
            else:
                # 计算数据量差异
                max_count = max(data_counts.values()) if data_counts else 0
                min_count = min(data_counts.values()) if data_counts else 0
                consistency_score = min_count / max_count if max_count > 0 else 0
                consistency_checks.append(("data_count_consistency", consistency_score))
            
            # 2. 时间范围一致性检查
            time_ranges = {}
            for module_name, module_data in analysis_results.items():
                if isinstance(module_data, dict) and "yearly_counts" in module_data:
                    years = list(module_data["yearly_counts"].keys())
                    if years:
                        time_ranges[module_name] = (min(years), max(years))
            
            if len(set(time_ranges.values())) <= 1:
                consistency_checks.append(("time_range_consistency", 1.0))
            else:
                # 计算时间范围重叠度
                if time_ranges:
                    all_ranges = list(time_ranges.values())
                    overlap_score = self._calculate_time_range_overlap(all_ranges)
                    consistency_checks.append(("time_range_consistency", overlap_score))
            
            # 3. 逻辑一致性检查
            logical_consistency = self._check_logical_consistency(analysis_results)
            consistency_checks.append(("logical_consistency", logical_consistency))
            
            # 计算总体一致性
            overall_consistency = sum(score for _, score in consistency_checks) / len(consistency_checks)
            
            return {
                "overall_consistency": overall_consistency,
                "consistency_checks": dict(consistency_checks),
                "pass_threshold": self.quality_config["consistency_threshold"],
                "status": "pass" if overall_consistency >= self.quality_config["consistency_threshold"] else "fail"
            }
            
        except Exception as e:
            self.logger.error(f"Error checking result consistency: {str(e)}")
            return {"overall_consistency": 0.0, "error": str(e)}
    
    def _calculate_time_range_overlap(self, time_ranges: List[Tuple[int, int]]) -> float:
        """计算时间范围重叠度."""
        try:
            if not time_ranges:
                return 0.0
            
            # 找到所有范围的交集
            max_start = max(start for start, _ in time_ranges)
            min_end = min(end for _, end in time_ranges)
            
            if max_start <= min_end:
                overlap_years = min_end - max_start + 1
                
                # 计算平均范围长度
                avg_range_length = sum(end - start + 1 for start, end in time_ranges) / len(time_ranges)
                
                return min(overlap_years / avg_range_length, 1.0)
            else:
                return 0.0
                
        except Exception as e:
            self.logger.error(f"Error calculating time range overlap: {str(e)}")
            return 0.0
    
    def _check_logical_consistency(self, analysis_results: Dict[str, Any]) -> float:
        """检查逻辑一致性."""
        try:
            consistency_score = 1.0
            
            # 检查趋势分析和竞争分析的逻辑一致性
            if "trend" in analysis_results and "competition" in analysis_results:
                trend_data = analysis_results["trend"]
                competition_data = analysis_results["competition"]
                
                # 如果趋势是增长的，竞争应该相对激烈
                trend_direction = trend_data.get("trend_direction", "stable")
                market_concentration = competition_data.get("market_concentration", 0.5)
                
                if trend_direction == "increasing" and market_concentration > 0.8:
                    consistency_score -= 0.2  # 增长趋势但高度集中，逻辑上有些矛盾
                
                if trend_direction == "decreasing" and market_concentration < 0.2:
                    consistency_score -= 0.2  # 下降趋势但竞争激烈，逻辑上有些矛盾
            
            return max(0.0, consistency_score)
            
        except Exception as e:
            self.logger.error(f"Error checking logical consistency: {str(e)}")
            return 0.5
    
    async def _check_statistical_validity(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """检查统计有效性."""
        try:
            validity_checks = []
            
            # 1. 样本量充足性检查
            sample_size_validity = self._check_sample_size_validity(analysis_results)
            validity_checks.append(("sample_size", sample_size_validity))
            
            # 2. 统计显著性检查
            statistical_significance = self._check_statistical_significance(analysis_results)
            validity_checks.append(("statistical_significance", statistical_significance))
            
            # 3. 数据分布合理性检查
            distribution_validity = self._check_distribution_validity(analysis_results)
            validity_checks.append(("distribution_validity", distribution_validity))
            
            # 4. 置信区间检查
            confidence_interval_validity = self._check_confidence_intervals(analysis_results)
            validity_checks.append(("confidence_intervals", confidence_interval_validity))
            
            # 计算总体统计有效性
            overall_validity = sum(score for _, score in validity_checks) / len(validity_checks)
            
            return {
                "overall_validity": overall_validity,
                "validity_checks": dict(validity_checks),
                "status": "pass" if overall_validity >= 0.7 else "fail"
            }
            
        except Exception as e:
            self.logger.error(f"Error checking statistical validity: {str(e)}")
            return {"overall_validity": 0.0, "error": str(e)}
    
    def _check_sample_size_validity(self, analysis_results: Dict[str, Any]) -> float:
        """检查样本量充足性."""
        try:
            min_sample_sizes = {
                "trend": 20,      # 趋势分析至少需要20个数据点
                "competition": 15, # 竞争分析至少需要15个申请人
                "technology": 10   # 技术分析至少需要10个技术分类
            }
            
            validity_scores = []
            
            for module_name, min_size in min_sample_sizes.items():
                if module_name in analysis_results:
                    module_data = analysis_results[module_name]
                    
                    # 获取实际样本量
                    actual_size = self._extract_sample_size(module_name, module_data)
                    
                    # 计算充足性评分
                    if actual_size >= min_size:
                        validity_scores.append(1.0)
                    elif actual_size >= min_size * 0.7:  # 70%的最小要求
                        validity_scores.append(0.8)
                    elif actual_size >= min_size * 0.5:  # 50%的最小要求
                        validity_scores.append(0.6)
                    else:
                        validity_scores.append(0.3)
            
            return sum(validity_scores) / len(validity_scores) if validity_scores else 0.0
            
        except Exception as e:
            self.logger.error(f"Error checking sample size validity: {str(e)}")
            return 0.0
    
    def _extract_sample_size(self, module_name: str, module_data: Dict[str, Any]) -> int:
        """提取模块的样本量."""
        try:
            if module_name == "trend":
                yearly_counts = module_data.get("yearly_counts", {})
                return sum(yearly_counts.values())
            
            elif module_name == "competition":
                applicant_distribution = module_data.get("applicant_distribution", {})
                return len(applicant_distribution)
            
            elif module_name == "technology":
                ipc_distribution = module_data.get("ipc_distribution", {})
                return len(ipc_distribution)
            
            else:
                return module_data.get("total_count", 0)
                
        except Exception as e:
            self.logger.error(f"Error extracting sample size: {str(e)}")
            return 0
    
    def _check_statistical_significance(self, analysis_results: Dict[str, Any]) -> float:
        """检查统计显著性."""
        try:
            # 简化的显著性检查
            significance_scores = []
            
            # 检查趋势分析的显著性
            if "trend" in analysis_results:
                trend_data = analysis_results["trend"]
                growth_rates = trend_data.get("growth_rates", {})
                
                if growth_rates:
                    # 检查增长率的变异性
                    rates = list(growth_rates.values())
                    if len(rates) > 1:
                        mean_rate = sum(rates) / len(rates)
                        variance = sum((rate - mean_rate) ** 2 for rate in rates) / len(rates)
                        
                        # 如果变异性适中，认为有统计显著性
                        if 5 < variance < 100:  # 合理的变异范围
                            significance_scores.append(0.8)
                        else:
                            significance_scores.append(0.5)
            
            # 检查竞争分析的显著性
            if "competition" in analysis_results:
                competition_data = analysis_results["competition"]
                market_concentration = competition_data.get("market_concentration", 0)
                
                # 市场集中度在合理范围内认为有显著性
                if 0.1 < market_concentration < 0.9:
                    significance_scores.append(0.8)
                else:
                    significance_scores.append(0.6)
            
            return sum(significance_scores) / len(significance_scores) if significance_scores else 0.7
            
        except Exception as e:
            self.logger.error(f"Error checking statistical significance: {str(e)}")
            return 0.5
    
    def _check_distribution_validity(self, analysis_results: Dict[str, Any]) -> float:
        """检查数据分布合理性."""
        try:
            distribution_scores = []
            
            # 检查年度分布的合理性
            for module_name, module_data in analysis_results.items():
                if isinstance(module_data, dict) and "yearly_counts" in module_data:
                    yearly_counts = module_data["yearly_counts"]
                    
                    if yearly_counts:
                        counts = list(yearly_counts.values())
                        
                        # 检查是否有极端异常值
                        mean_count = sum(counts) / len(counts)
                        max_count = max(counts)
                        min_count = min(counts)
                        
                        # 合理的分布应该没有过于极端的值
                        if max_count <= mean_count * 5 and min_count >= mean_count * 0.1:
                            distribution_scores.append(0.9)
                        elif max_count <= mean_count * 10 and min_count >= mean_count * 0.05:
                            distribution_scores.append(0.7)
                        else:
                            distribution_scores.append(0.5)
            
            return sum(distribution_scores) / len(distribution_scores) if distribution_scores else 0.8
            
        except Exception as e:
            self.logger.error(f"Error checking distribution validity: {str(e)}")
            return 0.5
    
    def _check_confidence_intervals(self, analysis_results: Dict[str, Any]) -> float:
        """检查置信区间."""
        try:
            # 简化的置信区间检查
            # 在实际应用中，这里应该计算具体的置信区间
            
            confidence_scores = []
            
            # 检查预测结果的置信区间
            if "trend" in analysis_results:
                trend_data = analysis_results["trend"]
                
                # 如果有预测数据，检查其合理性
                if "future_prediction" in trend_data:
                    prediction = trend_data["future_prediction"]
                    confidence = prediction.get("confidence", "medium")
                    
                    if confidence == "high":
                        confidence_scores.append(0.9)
                    elif confidence == "medium":
                        confidence_scores.append(0.7)
                    else:
                        confidence_scores.append(0.5)
            
            return sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.7
            
        except Exception as e:
            self.logger.error(f"Error checking confidence intervals: {str(e)}")
            return 0.5
    
    async def _check_logical_coherence(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """检查逻辑连贯性."""
        try:
            coherence_checks = []
            
            # 1. 内部逻辑一致性
            internal_consistency = self._check_internal_logic_consistency(analysis_results)
            coherence_checks.append(("internal_consistency", internal_consistency))
            
            # 2. 跨模块逻辑连贯性
            cross_module_coherence = self._check_cross_module_coherence(analysis_results)
            coherence_checks.append(("cross_module_coherence", cross_module_coherence))
            
            # 3. 因果关系合理性
            causal_relationship_validity = self._check_causal_relationships(analysis_results)
            coherence_checks.append(("causal_relationships", causal_relationship_validity))
            
            # 4. 结论与数据的一致性
            conclusion_data_consistency = self._check_conclusion_data_consistency(analysis_results)
            coherence_checks.append(("conclusion_consistency", conclusion_data_consistency))
            
            # 计算总体逻辑连贯性
            overall_coherence = sum(score for _, score in coherence_checks) / len(coherence_checks)
            
            return {
                "overall_coherence": overall_coherence,
                "coherence_checks": dict(coherence_checks),
                "status": "pass" if overall_coherence >= 0.7 else "fail"
            }
            
        except Exception as e:
            self.logger.error(f"Error checking logical coherence: {str(e)}")
            return {"overall_coherence": 0.0, "error": str(e)}
    
    def _check_internal_logic_consistency(self, analysis_results: Dict[str, Any]) -> float:
        """检查内部逻辑一致性."""
        try:
            consistency_score = 1.0
            
            # 检查趋势分析内部一致性
            if "trend" in analysis_results:
                trend_data = analysis_results["trend"]
                
                trend_direction = trend_data.get("trend_direction", "stable")
                growth_rates = trend_data.get("growth_rates", {})
                
                if growth_rates:
                    recent_rates = list(growth_rates.values())[-3:]  # 最近3年
                    avg_recent_growth = sum(recent_rates) / len(recent_rates)
                    
                    # 检查趋势方向与增长率的一致性
                    if trend_direction == "increasing" and avg_recent_growth < -5:
                        consistency_score -= 0.3
                    elif trend_direction == "decreasing" and avg_recent_growth > 5:
                        consistency_score -= 0.3
            
            return max(0.0, consistency_score)
            
        except Exception as e:
            self.logger.error(f"Error checking internal logic consistency: {str(e)}")
            return 0.7
    
    def _check_cross_module_coherence(self, analysis_results: Dict[str, Any]) -> float:
        """检查跨模块逻辑连贯性."""
        try:
            coherence_score = 1.0
            
            # 检查趋势与竞争的连贯性
            if "trend" in analysis_results and "competition" in analysis_results:
                trend_data = analysis_results["trend"]
                competition_data = analysis_results["competition"]
                
                trend_direction = trend_data.get("trend_direction", "stable")
                market_concentration = competition_data.get("market_concentration", 0.5)
                
                # 逻辑检查：快速增长通常伴随着竞争加剧（集中度降低）
                if trend_direction == "rapidly_increasing" and market_concentration > 0.8:
                    coherence_score -= 0.2
                
                # 逻辑检查：市场衰退通常伴随着集中度提高
                if trend_direction == "decreasing" and market_concentration < 0.3:
                    coherence_score -= 0.2
            
            return max(0.0, coherence_score)
            
        except Exception as e:
            self.logger.error(f"Error checking cross module coherence: {str(e)}")
            return 0.7
    
    def _check_causal_relationships(self, analysis_results: Dict[str, Any]) -> float:
        """检查因果关系合理性."""
        try:
            # 简化的因果关系检查
            causal_score = 0.8  # 默认评分
            
            # 检查技术发展与专利申请的因果关系
            if "technology" in analysis_results and "trend" in analysis_results:
                tech_data = analysis_results["technology"]
                trend_data = analysis_results["trend"]
                
                # 新兴技术应该与专利增长有正相关
                emerging_tech = tech_data.get("emerging_technologies", {})
                trend_direction = trend_data.get("trend_direction", "stable")
                
                if emerging_tech.get("total_emerging_count", 0) > 5 and trend_direction == "increasing":
                    causal_score = 0.9  # 因果关系合理
                elif emerging_tech.get("total_emerging_count", 0) == 0 and trend_direction == "rapidly_increasing":
                    causal_score = 0.6  # 因果关系存疑
            
            return causal_score
            
        except Exception as e:
            self.logger.error(f"Error checking causal relationships: {str(e)}")
            return 0.7
    
    def _check_conclusion_data_consistency(self, analysis_results: Dict[str, Any]) -> float:
        """检查结论与数据的一致性."""
        try:
            consistency_score = 0.8  # 默认评分
            
            # 检查洞察与数据的一致性
            if "insights" in analysis_results:
                insights = analysis_results["insights"]
                key_findings = insights.get("key_findings", [])
                
                # 简单检查：如果有关键发现，应该有支撑数据
                if key_findings:
                    # 检查是否有足够的数据支撑这些发现
                    supporting_modules = sum(1 for module in ["trend", "competition", "technology"] 
                                           if module in analysis_results and analysis_results[module].get("success", False))
                    
                    if supporting_modules >= 2:
                        consistency_score = 0.9
                    elif supporting_modules == 1:
                        consistency_score = 0.7
                    else:
                        consistency_score = 0.5
            
            return consistency_score
            
        except Exception as e:
            self.logger.error(f"Error checking conclusion data consistency: {str(e)}")
            return 0.7
    
    async def _check_temporal_stability(self, analysis_results: Dict[str, Any], result_id: str) -> Dict[str, Any]:
        """检查时间稳定性."""
        try:
            # 获取历史版本进行比较
            historical_versions = self.version_history.get(result_id, [])
            
            if len(historical_versions) < 2:
                return {
                    "stability_score": 0.8,  # 默认稳定性
                    "status": "insufficient_history",
                    "message": "历史数据不足，无法评估时间稳定性"
                }
            
            # 比较最近两个版本
            current_version = analysis_results
            previous_version = historical_versions[-1]["results"]
            
            # 计算关键指标的变化
            stability_checks = []
            
            # 1. 趋势方向稳定性
            if "trend" in current_version and "trend" in previous_version:
                current_trend = current_version["trend"].get("trend_direction", "unknown")
                previous_trend = previous_version["trend"].get("trend_direction", "unknown")
                
                if current_trend == previous_trend:
                    stability_checks.append(("trend_direction", 1.0))
                else:
                    stability_checks.append(("trend_direction", 0.5))
            
            # 2. 主要竞争者稳定性
            if "competition" in current_version and "competition" in previous_version:
                current_top = set(app for app, _ in current_version["competition"].get("top_applicants", [])[:5])
                previous_top = set(app for app, _ in previous_version["competition"].get("top_applicants", [])[:5])
                
                overlap = len(current_top & previous_top)
                stability_score = overlap / max(len(current_top), len(previous_top)) if current_top or previous_top else 0
                stability_checks.append(("top_competitors", stability_score))
            
            # 3. 技术领域稳定性
            if "technology" in current_version and "technology" in previous_version:
                current_tech = set(current_version["technology"].get("main_technologies", [])[:5])
                previous_tech = set(previous_version["technology"].get("main_technologies", [])[:5])
                
                overlap = len(current_tech & previous_tech)
                stability_score = overlap / max(len(current_tech), len(previous_tech)) if current_tech or previous_tech else 0
                stability_checks.append(("main_technologies", stability_score))
            
            # 计算总体稳定性
            overall_stability = sum(score for _, score in stability_checks) / len(stability_checks) if stability_checks else 0.8
            
            return {
                "stability_score": overall_stability,
                "stability_checks": dict(stability_checks),
                "versions_compared": 2,
                "status": "pass" if overall_stability >= 0.7 else "unstable"
            }
            
        except Exception as e:
            self.logger.error(f"Error checking temporal stability: {str(e)}")
            return {"stability_score": 0.0, "error": str(e)}
    
    async def _detect_anomalies(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """检测异常."""
        try:
            anomalies = []
            
            # 1. 数值异常检测
            numerical_anomalies = self._detect_numerical_anomalies(analysis_results)
            anomalies.extend(numerical_anomalies)
            
            # 2. 逻辑异常检测
            logical_anomalies = self._detect_logical_anomalies(analysis_results)
            anomalies.extend(logical_anomalies)
            
            # 3. 统计异常检测
            statistical_anomalies = self._detect_statistical_anomalies(analysis_results)
            anomalies.extend(statistical_anomalies)
            
            # 异常严重程度分类
            critical_anomalies = [a for a in anomalies if a.get("severity") == "critical"]
            warning_anomalies = [a for a in anomalies if a.get("severity") == "warning"]
            
            return {
                "total_anomalies": len(anomalies),
                "critical_anomalies": len(critical_anomalies),
                "warning_anomalies": len(warning_anomalies),
                "anomaly_details": anomalies[:10],  # 只返回前10个异常
                "anomaly_rate": len(anomalies) / 10,  # 假设总共检查10个方面
                "status": "critical" if critical_anomalies else "warning" if warning_anomalies else "normal"
            }
            
        except Exception as e:
            self.logger.error(f"Error detecting anomalies: {str(e)}")
            return {"total_anomalies": 0, "error": str(e)}
    
    def _detect_numerical_anomalies(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检测数值异常."""
        anomalies = []
        
        try:
            # 检查增长率异常
            if "trend" in analysis_results:
                trend_data = analysis_results["trend"]
                growth_rates = trend_data.get("growth_rates", {})
                
                for year, rate in growth_rates.items():
                    if abs(rate) > 500:  # 增长率超过500%
                        anomalies.append({
                            "type": "numerical",
                            "severity": "critical",
                            "description": f"{year}年增长率异常: {rate}%",
                            "module": "trend",
                            "value": rate
                        })
                    elif abs(rate) > 200:  # 增长率超过200%
                        anomalies.append({
                            "type": "numerical",
                            "severity": "warning",
                            "description": f"{year}年增长率较高: {rate}%",
                            "module": "trend",
                            "value": rate
                        })
            
            # 检查市场集中度异常
            if "competition" in analysis_results:
                competition_data = analysis_results["competition"]
                market_concentration = competition_data.get("market_concentration", 0)
                
                if market_concentration > 0.95:
                    anomalies.append({
                        "type": "numerical",
                        "severity": "warning",
                        "description": f"市场集中度极高: {market_concentration:.3f}",
                        "module": "competition",
                        "value": market_concentration
                    })
                elif market_concentration < 0.01:
                    anomalies.append({
                        "type": "numerical",
                        "severity": "warning",
                        "description": f"市场集中度极低: {market_concentration:.3f}",
                        "module": "competition",
                        "value": market_concentration
                    })
            
        except Exception as e:
            self.logger.error(f"Error detecting numerical anomalies: {str(e)}")
        
        return anomalies
    
    def _detect_logical_anomalies(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检测逻辑异常."""
        anomalies = []
        
        try:
            # 检查趋势与竞争的逻辑异常
            if "trend" in analysis_results and "competition" in analysis_results:
                trend_data = analysis_results["trend"]
                competition_data = analysis_results["competition"]
                
                trend_direction = trend_data.get("trend_direction", "stable")
                market_concentration = competition_data.get("market_concentration", 0.5)
                
                # 逻辑异常：快速增长但市场高度集中
                if trend_direction == "rapidly_increasing" and market_concentration > 0.9:
                    anomalies.append({
                        "type": "logical",
                        "severity": "warning",
                        "description": "快速增长趋势与高市场集中度存在逻辑矛盾",
                        "modules": ["trend", "competition"]
                    })
                
                # 逻辑异常：市场衰退但竞争激烈
                if trend_direction == "decreasing" and market_concentration < 0.2:
                    anomalies.append({
                        "type": "logical",
                        "severity": "warning",
                        "description": "下降趋势与低市场集中度存在逻辑矛盾",
                        "modules": ["trend", "competition"]
                    })
            
        except Exception as e:
            self.logger.error(f"Error detecting logical anomalies: {str(e)}")
        
        return anomalies
    
    def _detect_statistical_anomalies(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检测统计异常."""
        anomalies = []
        
        try:
            # 检查数据分布异常
            for module_name, module_data in analysis_results.items():
                if isinstance(module_data, dict) and "yearly_counts" in module_data:
                    yearly_counts = module_data["yearly_counts"]
                    
                    if yearly_counts:
                        counts = list(yearly_counts.values())
                        mean_count = sum(counts) / len(counts)
                        
                        # 检查极端值
                        for year, count in yearly_counts.items():
                            if count > mean_count * 10:  # 超过平均值10倍
                                anomalies.append({
                                    "type": "statistical",
                                    "severity": "critical",
                                    "description": f"{module_name}模块{year}年数据异常高: {count}",
                                    "module": module_name,
                                    "year": year,
                                    "value": count
                                })
                            elif count == 0 and mean_count > 5:  # 零值异常
                                anomalies.append({
                                    "type": "statistical",
                                    "severity": "warning",
                                    "description": f"{module_name}模块{year}年数据为零",
                                    "module": module_name,
                                    "year": year,
                                    "value": count
                                })
            
        except Exception as e:
            self.logger.error(f"Error detecting statistical anomalies: {str(e)}")
        
        return anomalies    

    async def _calculate_overall_quality(self, validation_results: Dict[str, Any]) -> float:
        """计算总体质量评分."""
        try:
            quality_scores = {}
            
            # 提取各维度评分
            if "completeness" in validation_results:
                quality_scores["data_completeness"] = validation_results["completeness"].get("overall_completeness", 0.0)
            
            if "consistency" in validation_results:
                quality_scores["result_consistency"] = validation_results["consistency"].get("overall_consistency", 0.0)
            
            if "statistical_validity" in validation_results:
                quality_scores["statistical_validity"] = validation_results["statistical_validity"].get("overall_validity", 0.0)
            
            if "logical_coherence" in validation_results:
                quality_scores["logical_coherence"] = validation_results["logical_coherence"].get("overall_coherence", 0.0)
            
            if "temporal_stability" in validation_results:
                quality_scores["temporal_stability"] = validation_results["temporal_stability"].get("stability_score", 0.0)
            
            # 加权计算总体质量
            overall_quality = 0.0
            total_weight = 0.0
            
            for dimension, weight in self.quality_weights.items():
                if dimension in quality_scores:
                    overall_quality += quality_scores[dimension] * weight
                    total_weight += weight
            
            # 归一化
            if total_weight > 0:
                overall_quality = overall_quality / total_weight
            
            return min(1.0, max(0.0, overall_quality))
            
        except Exception as e:
            self.logger.error(f"Error calculating overall quality: {str(e)}")
            return 0.0
    
    async def _generate_quality_report(self, validation_results: Dict[str, Any], overall_quality: float) -> Dict[str, Any]:
        """生成质量报告."""
        try:
            # 确定质量等级
            if overall_quality >= 0.9:
                quality_grade = "优秀"
            elif overall_quality >= 0.8:
                quality_grade = "良好"
            elif overall_quality >= 0.7:
                quality_grade = "合格"
            elif overall_quality >= 0.6:
                quality_grade = "需改进"
            else:
                quality_grade = "不合格"
            
            # 生成改进建议
            improvement_suggestions = self._generate_improvement_suggestions(validation_results, overall_quality)
            
            # 生成质量摘要
            quality_summary = self._generate_quality_summary(validation_results)
            
            # 风险评估
            risk_assessment = self._assess_quality_risks(validation_results)
            
            quality_report = {
                "overall_quality": overall_quality,
                "quality_grade": quality_grade,
                "validation_status": "pass" if overall_quality >= self.quality_config["confidence_threshold"] else "fail",
                "validation_timestamp": datetime.now().isoformat(),
                "detailed_results": validation_results,
                "quality_summary": quality_summary,
                "improvement_suggestions": improvement_suggestions,
                "risk_assessment": risk_assessment,
                "quality_metrics": {
                    "completeness_score": validation_results.get("completeness", {}).get("overall_completeness", 0.0),
                    "consistency_score": validation_results.get("consistency", {}).get("overall_consistency", 0.0),
                    "validity_score": validation_results.get("statistical_validity", {}).get("overall_validity", 0.0),
                    "coherence_score": validation_results.get("logical_coherence", {}).get("overall_coherence", 0.0),
                    "stability_score": validation_results.get("temporal_stability", {}).get("stability_score", 0.0)
                }
            }
            
            return quality_report
            
        except Exception as e:
            self.logger.error(f"Error generating quality report: {str(e)}")
            return {
                "overall_quality": 0.0,
                "quality_grade": "错误",
                "validation_status": "error",
                "error": str(e)
            }
    
    def _generate_improvement_suggestions(self, validation_results: Dict[str, Any], overall_quality: float) -> List[str]:
        """生成改进建议."""
        suggestions = []
        
        try:
            # 基于完整性的建议
            completeness = validation_results.get("completeness", {})
            if completeness.get("overall_completeness", 1.0) < 0.8:
                missing_modules = set(["trend", "competition", "technology"]) - set(completeness.get("present_modules", []))
                if missing_modules:
                    suggestions.append(f"建议补充{', '.join(missing_modules)}分析模块以提高数据完整性")
            
            # 基于一致性的建议
            consistency = validation_results.get("consistency", {})
            if consistency.get("overall_consistency", 1.0) < 0.7:
                suggestions.append("建议检查各分析模块间的数据一致性，确保使用相同的数据源和时间范围")
            
            # 基于统计有效性的建议
            validity = validation_results.get("statistical_validity", {})
            if validity.get("overall_validity", 1.0) < 0.7:
                suggestions.append("建议增加样本量或改进统计方法以提高分析结果的统计有效性")
            
            # 基于逻辑连贯性的建议
            coherence = validation_results.get("logical_coherence", {})
            if coherence.get("overall_coherence", 1.0) < 0.7:
                suggestions.append("建议检查分析逻辑，确保各模块结论之间的逻辑一致性")
            
            # 基于异常检测的建议
            anomalies = validation_results.get("anomaly_detection", {})
            if anomalies.get("critical_anomalies", 0) > 0:
                suggestions.append("检测到关键异常，建议仔细检查数据质量和分析方法")
            elif anomalies.get("warning_anomalies", 0) > 2:
                suggestions.append("检测到多个警告级异常，建议进行数据清洗和验证")
            
            # 通用建议
            if overall_quality < 0.7:
                suggestions.append("建议扩大数据收集范围，使用多个数据源进行交叉验证")
                suggestions.append("建议增加人工审核环节，确保分析结果的准确性")
            
        except Exception as e:
            self.logger.error(f"Error generating improvement suggestions: {str(e)}")
            suggestions.append("质量评估过程中出现错误，建议重新进行分析")
        
        return suggestions
    
    def _generate_quality_summary(self, validation_results: Dict[str, Any]) -> str:
        """生成质量摘要."""
        try:
            summary_parts = []
            
            # 完整性摘要
            completeness = validation_results.get("completeness", {})
            completeness_score = completeness.get("overall_completeness", 0.0)
            present_modules = completeness.get("present_modules", [])
            
            summary_parts.append(f"数据完整性: {completeness_score:.1%}，包含{len(present_modules)}个分析模块")
            
            # 一致性摘要
            consistency = validation_results.get("consistency", {})
            consistency_score = consistency.get("overall_consistency", 0.0)
            summary_parts.append(f"结果一致性: {consistency_score:.1%}")
            
            # 有效性摘要
            validity = validation_results.get("statistical_validity", {})
            validity_score = validity.get("overall_validity", 0.0)
            summary_parts.append(f"统计有效性: {validity_score:.1%}")
            
            # 异常摘要
            anomalies = validation_results.get("anomaly_detection", {})
            total_anomalies = anomalies.get("total_anomalies", 0)
            if total_anomalies > 0:
                summary_parts.append(f"检测到{total_anomalies}个异常")
            else:
                summary_parts.append("未检测到异常")
            
            return "；".join(summary_parts) + "。"
            
        except Exception as e:
            self.logger.error(f"Error generating quality summary: {str(e)}")
            return "质量摘要生成失败。"
    
    def _assess_quality_risks(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """评估质量风险."""
        try:
            risks = {
                "high_risk_factors": [],
                "medium_risk_factors": [],
                "low_risk_factors": [],
                "overall_risk_level": "low"
            }
            
            # 评估各种风险因素
            
            # 数据完整性风险
            completeness = validation_results.get("completeness", {})
            completeness_score = completeness.get("overall_completeness", 1.0)
            
            if completeness_score < 0.6:
                risks["high_risk_factors"].append("数据完整性严重不足")
            elif completeness_score < 0.8:
                risks["medium_risk_factors"].append("数据完整性有待提高")
            
            # 一致性风险
            consistency = validation_results.get("consistency", {})
            consistency_score = consistency.get("overall_consistency", 1.0)
            
            if consistency_score < 0.6:
                risks["high_risk_factors"].append("结果一致性存在严重问题")
            elif consistency_score < 0.8:
                risks["medium_risk_factors"].append("结果一致性需要改进")
            
            # 异常风险
            anomalies = validation_results.get("anomaly_detection", {})
            critical_anomalies = anomalies.get("critical_anomalies", 0)
            warning_anomalies = anomalies.get("warning_anomalies", 0)
            
            if critical_anomalies > 0:
                risks["high_risk_factors"].append(f"存在{critical_anomalies}个关键异常")
            elif warning_anomalies > 3:
                risks["medium_risk_factors"].append(f"存在{warning_anomalies}个警告级异常")
            elif warning_anomalies > 0:
                risks["low_risk_factors"].append(f"存在{warning_anomalies}个轻微异常")
            
            # 统计有效性风险
            validity = validation_results.get("statistical_validity", {})
            validity_score = validity.get("overall_validity", 1.0)
            
            if validity_score < 0.6:
                risks["high_risk_factors"].append("统计有效性不足")
            elif validity_score < 0.8:
                risks["medium_risk_factors"].append("统计有效性有待提高")
            
            # 确定总体风险等级
            if risks["high_risk_factors"]:
                risks["overall_risk_level"] = "high"
            elif len(risks["medium_risk_factors"]) > 2:
                risks["overall_risk_level"] = "high"
            elif risks["medium_risk_factors"]:
                risks["overall_risk_level"] = "medium"
            else:
                risks["overall_risk_level"] = "low"
            
            return risks
            
        except Exception as e:
            self.logger.error(f"Error assessing quality risks: {str(e)}")
            return {
                "high_risk_factors": ["质量风险评估失败"],
                "overall_risk_level": "unknown"
            }
    
    async def _manage_result_version(self, result_id: str, analysis_results: Dict[str, Any], quality_report: Dict[str, Any]):
        """管理结果版本."""
        try:
            # 创建版本记录
            version_record = {
                "version_id": f"{result_id}_v{len(self.version_history[result_id]) + 1}",
                "timestamp": datetime.now().isoformat(),
                "results": analysis_results,
                "quality_score": quality_report.get("overall_quality", 0.0),
                "quality_grade": quality_report.get("quality_grade", "未知")
            }
            
            # 添加到版本历史
            self.version_history[result_id].append(version_record)
            
            # 清理过期版本
            await self._cleanup_expired_versions(result_id)
            
            self.logger.info(f"Version managed for result {result_id}: {version_record['version_id']}")
            
        except Exception as e:
            self.logger.error(f"Error managing result version: {str(e)}")
    
    async def _cleanup_expired_versions(self, result_id: str):
        """清理过期版本."""
        try:
            if result_id not in self.version_history:
                return
            
            current_time = datetime.now()
            retention_days = self.quality_config["version_retention_days"]
            
            # 过滤出未过期的版本
            valid_versions = []
            for version in self.version_history[result_id]:
                version_time = datetime.fromisoformat(version["timestamp"])
                if (current_time - version_time).days <= retention_days:
                    valid_versions.append(version)
            
            # 至少保留最新的3个版本
            if len(valid_versions) < 3 and len(self.version_history[result_id]) >= 3:
                valid_versions = self.version_history[result_id][-3:]
            
            self.version_history[result_id] = valid_versions
            
        except Exception as e:
            self.logger.error(f"Error cleaning up expired versions: {str(e)}")
    
    async def _cache_validation_results(self, result_id: str, quality_report: Dict[str, Any]):
        """缓存验证结果."""
        try:
            cache_entry = {
                "validation_result": quality_report,
                "cache_timestamp": datetime.now().timestamp()
            }
            
            self.result_cache[result_id] = cache_entry
            
            # 限制缓存大小
            if len(self.result_cache) > 1000:
                # 删除最旧的缓存项
                oldest_key = min(self.result_cache.keys(), 
                               key=lambda k: self.result_cache[k]["cache_timestamp"])
                del self.result_cache[oldest_key]
            
        except Exception as e:
            self.logger.error(f"Error caching validation results: {str(e)}")
    
    async def _update_performance_metrics(self, processing_time: float, quality_score: float):
        """更新性能指标."""
        try:
            self.performance_metrics["validation_count"] += 1
            
            # 更新平均验证时间
            current_avg = self.performance_metrics["average_validation_time"]
            count = self.performance_metrics["validation_count"]
            
            new_avg = ((current_avg * (count - 1)) + processing_time) / count
            self.performance_metrics["average_validation_time"] = new_avg
            
            # 更新质量通过率
            if quality_score >= self.quality_config["confidence_threshold"]:
                pass_count = self.performance_metrics["quality_pass_rate"] * (count - 1) + 1
            else:
                pass_count = self.performance_metrics["quality_pass_rate"] * (count - 1)
            
            self.performance_metrics["quality_pass_rate"] = pass_count / count
            
            # 集成现有健康检查和监控系统
            self.logger.info(f"Quality control metrics updated: {json.dumps(self.performance_metrics, ensure_ascii=False)}")
            
        except Exception as e:
            self.logger.error(f"Error updating performance metrics: {str(e)}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标."""
        return self.performance_metrics.copy()
    
    def get_version_history(self, result_id: str) -> List[Dict[str, Any]]:
        """获取版本历史."""
        return self.version_history.get(result_id, [])
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """获取缓存统计信息."""
        return {
            "cache_size": len(self.result_cache),
            "version_histories": len(self.version_history),
            "total_versions": sum(len(versions) for versions in self.version_history.values())
        }
    
    async def clear_cache(self):
        """清理缓存."""
        try:
            self.result_cache.clear()
            self.logger.info("Quality control cache cleared")
        except Exception as e:
            self.logger.error(f"Error clearing cache: {str(e)}")
    
    async def clear_version_history(self, result_id: Optional[str] = None):
        """清理版本历史."""
        try:
            if result_id:
                if result_id in self.version_history:
                    del self.version_history[result_id]
                    self.logger.info(f"Version history cleared for result {result_id}")
            else:
                self.version_history.clear()
                self.logger.info("All version history cleared")
        except Exception as e:
            self.logger.error(f"Error clearing version history: {str(e)}")
    
    def update_quality_config(self, new_config: Dict[str, Any]):
        """更新质量控制配置."""
        try:
            self.quality_config.update(new_config)
            self.logger.info(f"Quality control config updated: {json.dumps(new_config, ensure_ascii=False)}")
        except Exception as e:
            self.logger.error(f"Error updating quality config: {str(e)}")
    
    def get_quality_config(self) -> Dict[str, Any]:
        """获取质量控制配置."""
        return self.quality_config.copy()