"""Advanced trend analysis algorithms for patent data."""

import asyncio
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """高级趋势分析器，实现时间序列分析、预测算法和方向判断."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.TrendAnalyzer")
        
        # 趋势分析配置
        self.config = {
            "min_data_points": 3,
            "prediction_years": 3,
            "smoothing_window": 3,
            "trend_threshold": 0.1,
            "seasonality_detection": True,
            "outlier_detection": True
        }
        
        # 性能监控
        self.performance_metrics = {
            "analysis_count": 0,
            "average_processing_time": 0.0,
            "success_rate": 0.0
        }
    
    async def analyze_trends(self, patent_data: List[Dict[str, Any]], analysis_params: Dict[str, Any]) -> Dict[str, Any]:
        """执行综合趋势分析."""
        start_time = datetime.now()
        
        try:
            self.logger.info("Starting comprehensive trend analysis")
            
            # 数据预处理和验证
            processed_data = await self._preprocess_patent_data(patent_data)
            
            if not self._validate_data_quality(processed_data):
                return {
                    "error": "数据质量不足，无法进行可靠的趋势分析",
                    "data_quality_issues": self._get_data_quality_issues(processed_data)
                }
            
            # 执行多维度趋势分析
            analysis_results = {}
            
            # 1. 基础时间序列分析
            time_series_result = await self._time_series_analysis(processed_data, analysis_params)
            analysis_results["time_series"] = time_series_result
            
            # 2. 年度申请量统计和增长率计算
            yearly_analysis = await self._yearly_growth_analysis(processed_data)
            analysis_results["yearly_analysis"] = yearly_analysis
            
            # 3. 趋势预测算法
            prediction_result = await self._advanced_trend_prediction(processed_data, analysis_params)
            analysis_results["prediction"] = prediction_result
            
            # 4. 趋势方向判断
            direction_analysis = await self._trend_direction_analysis(processed_data, yearly_analysis)
            analysis_results["direction"] = direction_analysis
            
            # 5. 季节性和周期性分析
            if self.config["seasonality_detection"]:
                seasonality_result = await self._seasonality_analysis(processed_data)
                analysis_results["seasonality"] = seasonality_result
            
            # 6. 异常值检测和处理
            if self.config["outlier_detection"]:
                outlier_result = await self._outlier_detection(processed_data)
                analysis_results["outliers"] = outlier_result
            
            # 7. 综合趋势评估
            comprehensive_assessment = await self._comprehensive_trend_assessment(analysis_results)
            analysis_results["assessment"] = comprehensive_assessment
            
            # 记录性能指标
            processing_time = (datetime.now() - start_time).total_seconds()
            await self._update_performance_metrics(processing_time, True)
            
            self.logger.info(f"Trend analysis completed in {processing_time:.2f}s")
            
            return {
                "success": True,
                "results": analysis_results,
                "metadata": {
                    "processing_time": processing_time,
                    "data_points": len(processed_data),
                    "analysis_timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in trend analysis: {str(e)}")
            
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
    
    async def _preprocess_patent_data(self, patent_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """预处理专利数据，提取时间序列信息."""
        processed_data = []
        
        for patent in patent_data:
            try:
                # 提取申请日期
                app_date_str = patent.get("application_date", "")
                if not app_date_str:
                    continue
                
                # 解析日期
                app_date = self._parse_date(app_date_str)
                if not app_date:
                    continue
                
                processed_patent = {
                    "application_date": app_date,
                    "year": app_date.year,
                    "month": app_date.month,
                    "quarter": (app_date.month - 1) // 3 + 1,
                    "applicant": patent.get("applicants", ["Unknown"])[0] if patent.get("applicants") else "Unknown",
                    "ipc_class": patent.get("ipc_classes", ["Unknown"])[0] if patent.get("ipc_classes") else "Unknown",
                    "country": patent.get("country", "Unknown"),
                    "title": patent.get("title", ""),
                    "original_data": patent
                }
                
                processed_data.append(processed_patent)
                
            except Exception as e:
                self.logger.warning(f"Error processing patent data: {str(e)}")
                continue
        
        # 按日期排序
        processed_data.sort(key=lambda x: x["application_date"])
        
        self.logger.info(f"Processed {len(processed_data)} patents from {len(patent_data)} total")
        return processed_data
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """解析日期字符串."""
        date_formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%Y.%m.%d",
            "%Y-%m",
            "%Y/%m",
            "%Y.%m",
            "%Y"
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def _validate_data_quality(self, processed_data: List[Dict[str, Any]]) -> bool:
        """验证数据质量."""
        if len(processed_data) < self.config["min_data_points"]:
            return False
        
        # 检查时间跨度
        if len(processed_data) > 0:
            date_range = processed_data[-1]["application_date"] - processed_data[0]["application_date"]
            if date_range.days < 365:  # 至少需要1年的数据
                return False
        
        # 检查数据分布
        yearly_counts = defaultdict(int)
        for patent in processed_data:
            yearly_counts[patent["year"]] += 1
        
        # 至少需要3个不同年份的数据
        if len(yearly_counts) < 3:
            return False
        
        return True
    
    def _get_data_quality_issues(self, processed_data: List[Dict[str, Any]]) -> List[str]:
        """获取数据质量问题列表."""
        issues = []
        
        if len(processed_data) < self.config["min_data_points"]:
            issues.append(f"数据点不足，需要至少{self.config['min_data_points']}个数据点")
        
        if len(processed_data) > 0:
            date_range = processed_data[-1]["application_date"] - processed_data[0]["application_date"]
            if date_range.days < 365:
                issues.append("时间跨度不足，需要至少1年的数据")
        
        yearly_counts = defaultdict(int)
        for patent in processed_data:
            yearly_counts[patent["year"]] += 1
        
        if len(yearly_counts) < 3:
            issues.append("年份覆盖不足，需要至少3个不同年份的数据")
        
        return issues
    
    async def _time_series_analysis(self, processed_data: List[Dict[str, Any]], analysis_params: Dict[str, Any]) -> Dict[str, Any]:
        """时间序列分析."""
        try:
            # 按不同时间粒度统计
            yearly_counts = defaultdict(int)
            monthly_counts = defaultdict(int)
            quarterly_counts = defaultdict(int)
            
            for patent in processed_data:
                yearly_counts[patent["year"]] += 1
                month_key = f"{patent['year']}-{patent['month']:02d}"
                monthly_counts[month_key] += 1
                quarter_key = f"{patent['year']}-Q{patent['quarter']}"
                quarterly_counts[quarter_key] += 1
            
            # 计算移动平均
            yearly_ma = self._calculate_moving_average(yearly_counts, window=self.config["smoothing_window"])
            
            # 计算变化率
            yearly_changes = self._calculate_change_rates(yearly_counts)
            
            # 趋势强度分析
            trend_strength = self._calculate_trend_strength(yearly_counts)
            
            return {
                "yearly_counts": dict(yearly_counts),
                "monthly_counts": dict(monthly_counts),
                "quarterly_counts": dict(quarterly_counts),
                "yearly_moving_average": yearly_ma,
                "yearly_change_rates": yearly_changes,
                "trend_strength": trend_strength,
                "data_span_years": len(yearly_counts),
                "total_patents": len(processed_data)
            }
            
        except Exception as e:
            self.logger.error(f"Error in time series analysis: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_moving_average(self, data_dict: Dict[int, int], window: int = 3) -> Dict[int, float]:
        """计算移动平均."""
        if len(data_dict) < window:
            return {}
        
        sorted_years = sorted(data_dict.keys())
        moving_averages = {}
        
        for i in range(window - 1, len(sorted_years)):
            window_years = sorted_years[i - window + 1:i + 1]
            window_values = [data_dict[year] for year in window_years]
            moving_averages[sorted_years[i]] = sum(window_values) / len(window_values)
        
        return moving_averages
    
    def _calculate_change_rates(self, yearly_counts: Dict[int, int]) -> Dict[int, float]:
        """计算年度变化率."""
        change_rates = {}
        sorted_years = sorted(yearly_counts.keys())
        
        for i in range(1, len(sorted_years)):
            prev_year = sorted_years[i - 1]
            curr_year = sorted_years[i]
            
            prev_count = yearly_counts[prev_year]
            curr_count = yearly_counts[curr_year]
            
            if prev_count > 0:
                change_rate = ((curr_count - prev_count) / prev_count) * 100
                change_rates[curr_year] = change_rate
            else:
                change_rates[curr_year] = 0.0
        
        return change_rates
    
    def _calculate_trend_strength(self, yearly_counts: Dict[int, int]) -> Dict[str, float]:
        """计算趋势强度."""
        if len(yearly_counts) < 3:
            return {"strength": 0.0, "confidence": 0.0}
        
        years = sorted(yearly_counts.keys())
        counts = [yearly_counts[year] for year in years]
        
        # 使用线性回归计算趋势
        n = len(years)
        sum_x = sum(range(n))
        sum_y = sum(counts)
        sum_xy = sum(i * counts[i] for i in range(n))
        sum_x2 = sum(i * i for i in range(n))
        
        # 计算斜率
        if n * sum_x2 - sum_x * sum_x != 0:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            
            # 计算相关系数
            mean_x = sum_x / n
            mean_y = sum_y / n
            
            numerator = sum((i - mean_x) * (counts[i] - mean_y) for i in range(n))
            denominator_x = sum((i - mean_x) ** 2 for i in range(n))
            denominator_y = sum((counts[i] - mean_y) ** 2 for i in range(n))
            
            if denominator_x > 0 and denominator_y > 0:
                correlation = numerator / (denominator_x * denominator_y) ** 0.5
            else:
                correlation = 0.0
            
            return {
                "strength": abs(slope),
                "confidence": abs(correlation),
                "direction": "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable"
            }
        
        return {"strength": 0.0, "confidence": 0.0, "direction": "stable"}
    
    async def _yearly_growth_analysis(self, processed_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """年度申请量统计和增长率计算."""
        try:
            yearly_stats = defaultdict(lambda: {
                "count": 0,
                "applicants": set(),
                "countries": set(),
                "ipc_classes": set()
            })
            
            # 统计各年度数据
            for patent in processed_data:
                year = patent["year"]
                yearly_stats[year]["count"] += 1
                yearly_stats[year]["applicants"].add(patent["applicant"])
                yearly_stats[year]["countries"].add(patent["country"])
                yearly_stats[year]["ipc_classes"].add(patent["ipc_class"])
            
            # 转换为可序列化的格式
            yearly_summary = {}
            for year, stats in yearly_stats.items():
                yearly_summary[year] = {
                    "patent_count": stats["count"],
                    "unique_applicants": len(stats["applicants"]),
                    "unique_countries": len(stats["countries"]),
                    "unique_ipc_classes": len(stats["ipc_classes"])
                }
            
            # 计算增长率
            growth_analysis = self._calculate_detailed_growth_rates(yearly_summary)
            
            # 计算复合年增长率 (CAGR)
            cagr = self._calculate_cagr(yearly_summary)
            
            # 增长趋势分类
            growth_pattern = self._classify_growth_pattern(growth_analysis["growth_rates"])
            
            return {
                "yearly_summary": yearly_summary,
                "growth_rates": growth_analysis["growth_rates"],
                "average_growth_rate": growth_analysis["average_growth_rate"],
                "growth_volatility": growth_analysis["growth_volatility"],
                "cagr": cagr,
                "growth_pattern": growth_pattern,
                "peak_year": max(yearly_summary.keys(), key=lambda y: yearly_summary[y]["patent_count"]),
                "total_years": len(yearly_summary)
            }
            
        except Exception as e:
            self.logger.error(f"Error in yearly growth analysis: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_detailed_growth_rates(self, yearly_summary: Dict[int, Dict[str, int]]) -> Dict[str, Any]:
        """计算详细的增长率分析."""
        growth_rates = {}
        sorted_years = sorted(yearly_summary.keys())
        
        for i in range(1, len(sorted_years)):
            prev_year = sorted_years[i - 1]
            curr_year = sorted_years[i]
            
            prev_count = yearly_summary[prev_year]["patent_count"]
            curr_count = yearly_summary[curr_year]["patent_count"]
            
            if prev_count > 0:
                growth_rate = ((curr_count - prev_count) / prev_count) * 100
                growth_rates[curr_year] = growth_rate
        
        # 计算平均增长率
        if growth_rates:
            average_growth = sum(growth_rates.values()) / len(growth_rates)
            
            # 计算增长率的标准差（波动性）
            variance = sum((rate - average_growth) ** 2 for rate in growth_rates.values()) / len(growth_rates)
            volatility = variance ** 0.5
        else:
            average_growth = 0.0
            volatility = 0.0
        
        return {
            "growth_rates": growth_rates,
            "average_growth_rate": average_growth,
            "growth_volatility": volatility
        }
    
    def _calculate_cagr(self, yearly_summary: Dict[int, Dict[str, int]]) -> float:
        """计算复合年增长率."""
        if len(yearly_summary) < 2:
            return 0.0
        
        sorted_years = sorted(yearly_summary.keys())
        start_year = sorted_years[0]
        end_year = sorted_years[-1]
        
        start_count = yearly_summary[start_year]["patent_count"]
        end_count = yearly_summary[end_year]["patent_count"]
        
        if start_count > 0 and end_year > start_year:
            years_span = end_year - start_year
            cagr = ((end_count / start_count) ** (1 / years_span) - 1) * 100
            return cagr
        
        return 0.0
    
    def _classify_growth_pattern(self, growth_rates: Dict[int, float]) -> str:
        """分类增长模式."""
        if not growth_rates:
            return "insufficient_data"
        
        rates = list(growth_rates.values())
        avg_rate = sum(rates) / len(rates)
        
        # 计算增长率的变化趋势
        positive_rates = sum(1 for rate in rates if rate > 0)
        negative_rates = sum(1 for rate in rates if rate < 0)
        
        if avg_rate > 20:
            return "rapid_growth"
        elif avg_rate > 5:
            return "steady_growth"
        elif avg_rate > -5:
            if positive_rates > negative_rates:
                return "moderate_growth"
            else:
                return "fluctuating"
        elif avg_rate > -20:
            return "declining"
        else:
            return "rapid_decline"
    
    async def _advanced_trend_prediction(self, processed_data: List[Dict[str, Any]], analysis_params: Dict[str, Any]) -> Dict[str, Any]:
        """高级趋势预测算法."""
        try:
            # 准备历史数据
            yearly_counts = defaultdict(int)
            for patent in processed_data:
                yearly_counts[patent["year"]] += 1
            
            if len(yearly_counts) < 3:
                return {"error": "历史数据不足，无法进行可靠预测"}
            
            # 多种预测方法
            predictions = {}
            
            # 1. 线性趋势预测
            linear_prediction = self._linear_trend_prediction(yearly_counts)
            predictions["linear"] = linear_prediction
            
            # 2. 移动平均预测
            ma_prediction = self._moving_average_prediction(yearly_counts)
            predictions["moving_average"] = ma_prediction
            
            # 3. 指数平滑预测
            exp_smoothing_prediction = self._exponential_smoothing_prediction(yearly_counts)
            predictions["exponential_smoothing"] = exp_smoothing_prediction
            
            # 4. 季节性调整预测（如果有足够数据）
            if len(yearly_counts) >= 5:
                seasonal_prediction = self._seasonal_adjusted_prediction(yearly_counts)
                predictions["seasonal_adjusted"] = seasonal_prediction
            
            # 5. 集成预测（综合多种方法）
            ensemble_prediction = self._ensemble_prediction(predictions)
            
            # 预测置信度评估
            confidence_assessment = self._assess_prediction_confidence(yearly_counts, predictions)
            
            return {
                "individual_predictions": predictions,
                "ensemble_prediction": ensemble_prediction,
                "confidence_assessment": confidence_assessment,
                "prediction_horizon": self.config["prediction_years"],
                "base_data_years": len(yearly_counts)
            }
            
        except Exception as e:
            self.logger.error(f"Error in trend prediction: {str(e)}")
            return {"error": str(e)}
    
    def _linear_trend_prediction(self, yearly_counts: Dict[int, int]) -> Dict[str, Any]:
        """线性趋势预测."""
        years = sorted(yearly_counts.keys())
        counts = [yearly_counts[year] for year in years]
        
        # 线性回归
        n = len(years)
        sum_x = sum(range(n))
        sum_y = sum(counts)
        sum_xy = sum(i * counts[i] for i in range(n))
        sum_x2 = sum(i * i for i in range(n))
        
        if n * sum_x2 - sum_x * sum_x != 0:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            intercept = (sum_y - slope * sum_x) / n
            
            # 预测未来几年
            predictions = {}
            last_year = max(years)
            
            for i in range(1, self.config["prediction_years"] + 1):
                future_year = last_year + i
                predicted_value = slope * (n + i - 1) + intercept
                predictions[future_year] = max(0, int(predicted_value))
            
            return {
                "method": "linear_regression",
                "slope": slope,
                "intercept": intercept,
                "predictions": predictions,
                "trend": "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable"
            }
        
        return {"method": "linear_regression", "error": "无法计算线性趋势"}
    
    def _moving_average_prediction(self, yearly_counts: Dict[int, int], window: int = 3) -> Dict[str, Any]:
        """移动平均预测."""
        years = sorted(yearly_counts.keys())
        counts = [yearly_counts[year] for year in years]
        
        if len(counts) < window:
            window = len(counts)
        
        # 计算最近几年的移动平均
        recent_average = sum(counts[-window:]) / window
        
        # 预测未来几年（假设保持当前平均水平）
        predictions = {}
        last_year = max(years)
        
        for i in range(1, self.config["prediction_years"] + 1):
            future_year = last_year + i
            predictions[future_year] = int(recent_average)
        
        return {
            "method": "moving_average",
            "window_size": window,
            "recent_average": recent_average,
            "predictions": predictions
        }
    
    def _exponential_smoothing_prediction(self, yearly_counts: Dict[int, int], alpha: float = 0.3) -> Dict[str, Any]:
        """指数平滑预测."""
        years = sorted(yearly_counts.keys())
        counts = [yearly_counts[year] for year in years]
        
        # 指数平滑
        smoothed_values = [counts[0]]
        
        for i in range(1, len(counts)):
            smoothed_value = alpha * counts[i] + (1 - alpha) * smoothed_values[-1]
            smoothed_values.append(smoothed_value)
        
        # 预测未来几年
        predictions = {}
        last_year = max(years)
        last_smoothed = smoothed_values[-1]
        
        for i in range(1, self.config["prediction_years"] + 1):
            future_year = last_year + i
            predictions[future_year] = int(last_smoothed)
        
        return {
            "method": "exponential_smoothing",
            "alpha": alpha,
            "last_smoothed_value": last_smoothed,
            "predictions": predictions
        }
    
    def _seasonal_adjusted_prediction(self, yearly_counts: Dict[int, int]) -> Dict[str, Any]:
        """季节性调整预测."""
        # 简化的季节性分析（基于年度数据的周期性）
        years = sorted(yearly_counts.keys())
        counts = [yearly_counts[year] for year in years]
        
        # 检测是否有周期性模式
        if len(counts) >= 6:
            # 简单的周期检测（检查是否有2-3年的周期）
            cycle_length = 3  # 假设3年周期
            
            if len(counts) >= cycle_length * 2:
                # 计算周期性调整因子
                cycle_averages = []
                for i in range(cycle_length):
                    cycle_values = [counts[j] for j in range(i, len(counts), cycle_length)]
                    if cycle_values:
                        cycle_averages.append(sum(cycle_values) / len(cycle_values))
                
                # 预测未来几年
                predictions = {}
                last_year = max(years)
                
                for i in range(1, self.config["prediction_years"] + 1):
                    future_year = last_year + i
                    cycle_position = (i - 1) % cycle_length
                    if cycle_position < len(cycle_averages):
                        predictions[future_year] = int(cycle_averages[cycle_position])
                    else:
                        predictions[future_year] = int(sum(cycle_averages) / len(cycle_averages))
                
                return {
                    "method": "seasonal_adjusted",
                    "cycle_length": cycle_length,
                    "cycle_averages": cycle_averages,
                    "predictions": predictions
                }
        
        # 如果无法检测到季节性，回退到简单平均
        avg_count = sum(counts) / len(counts)
        predictions = {}
        last_year = max(years)
        
        for i in range(1, self.config["prediction_years"] + 1):
            future_year = last_year + i
            predictions[future_year] = int(avg_count)
        
        return {
            "method": "seasonal_adjusted_fallback",
            "average_count": avg_count,
            "predictions": predictions
        }
    
    def _ensemble_prediction(self, individual_predictions: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """集成预测（综合多种方法）."""
        if not individual_predictions:
            return {"error": "没有可用的预测方法"}
        
        # 收集所有预测结果
        all_predictions = defaultdict(list)
        
        for method, prediction_data in individual_predictions.items():
            if "predictions" in prediction_data:
                for year, value in prediction_data["predictions"].items():
                    all_predictions[year].append(value)
        
        # 计算集成预测（简单平均）
        ensemble_predictions = {}
        prediction_ranges = {}
        
        for year, values in all_predictions.items():
            if values:
                ensemble_predictions[year] = int(sum(values) / len(values))
                prediction_ranges[year] = {
                    "min": min(values),
                    "max": max(values),
                    "std": (sum((v - ensemble_predictions[year]) ** 2 for v in values) / len(values)) ** 0.5
                }
        
        return {
            "method": "ensemble",
            "predictions": ensemble_predictions,
            "prediction_ranges": prediction_ranges,
            "contributing_methods": list(individual_predictions.keys())
        }
    
    def _assess_prediction_confidence(self, yearly_counts: Dict[int, int], predictions: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """评估预测置信度."""
        confidence_factors = {
            "data_quality": 0.0,
            "trend_consistency": 0.0,
            "method_agreement": 0.0,
            "historical_stability": 0.0
        }
        
        # 1. 数据质量评估
        data_span = len(yearly_counts)
        if data_span >= 10:
            confidence_factors["data_quality"] = 0.9
        elif data_span >= 5:
            confidence_factors["data_quality"] = 0.7
        elif data_span >= 3:
            confidence_factors["data_quality"] = 0.5
        else:
            confidence_factors["data_quality"] = 0.3
        
        # 2. 趋势一致性评估
        counts = [yearly_counts[year] for year in sorted(yearly_counts.keys())]
        if len(counts) >= 3:
            # 计算趋势的一致性
            changes = [counts[i] - counts[i-1] for i in range(1, len(counts))]
            positive_changes = sum(1 for c in changes if c > 0)
            negative_changes = sum(1 for c in changes if c < 0)
            
            consistency = abs(positive_changes - negative_changes) / len(changes)
            confidence_factors["trend_consistency"] = consistency
        
        # 3. 方法一致性评估
        if len(predictions) > 1:
            # 检查不同预测方法的一致性
            first_year_predictions = []
            for method_data in predictions.values():
                if "predictions" in method_data:
                    pred_years = sorted(method_data["predictions"].keys())
                    if pred_years:
                        first_year_predictions.append(method_data["predictions"][pred_years[0]])
            
            if len(first_year_predictions) > 1:
                avg_pred = sum(first_year_predictions) / len(first_year_predictions)
                variance = sum((p - avg_pred) ** 2 for p in first_year_predictions) / len(first_year_predictions)
                # 方差越小，一致性越高
                confidence_factors["method_agreement"] = max(0, 1 - (variance ** 0.5) / avg_pred) if avg_pred > 0 else 0
        
        # 4. 历史稳定性评估
        if len(counts) >= 3:
            # 计算历史数据的稳定性
            mean_count = sum(counts) / len(counts)
            variance = sum((c - mean_count) ** 2 for c in counts) / len(counts)
            cv = (variance ** 0.5) / mean_count if mean_count > 0 else 1  # 变异系数
            
            # 变异系数越小，稳定性越高
            confidence_factors["historical_stability"] = max(0, 1 - cv)
        
        # 计算总体置信度
        overall_confidence = sum(confidence_factors.values()) / len(confidence_factors)
        
        # 置信度等级
        if overall_confidence >= 0.8:
            confidence_level = "high"
        elif overall_confidence >= 0.6:
            confidence_level = "medium"
        elif overall_confidence >= 0.4:
            confidence_level = "low"
        else:
            confidence_level = "very_low"
        
        return {
            "overall_confidence": overall_confidence,
            "confidence_level": confidence_level,
            "confidence_factors": confidence_factors,
            "recommendations": self._generate_confidence_recommendations(confidence_factors)
        }
    
    def _generate_confidence_recommendations(self, confidence_factors: Dict[str, float]) -> List[str]:
        """生成置信度改进建议."""
        recommendations = []
        
        if confidence_factors["data_quality"] < 0.6:
            recommendations.append("建议收集更多历史数据以提高预测准确性")
        
        if confidence_factors["trend_consistency"] < 0.5:
            recommendations.append("历史趋势不够一致，预测结果存在较大不确定性")
        
        if confidence_factors["method_agreement"] < 0.6:
            recommendations.append("不同预测方法结果差异较大，建议谨慎使用预测结果")
        
        if confidence_factors["historical_stability"] < 0.5:
            recommendations.append("历史数据波动较大，建议结合外部因素分析")
        
        return recommendations
    
    async def _trend_direction_analysis(self, processed_data: List[Dict[str, Any]], yearly_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """趋势方向判断逻辑."""
        try:
            yearly_summary = yearly_analysis.get("yearly_summary", {})
            growth_rates = yearly_analysis.get("growth_rates", {})
            
            if not yearly_summary or not growth_rates:
                return {"error": "缺少年度分析数据"}
            
            # 多维度方向分析
            direction_analysis = {}
            
            # 1. 基于增长率的方向判断
            recent_growth_rates = list(growth_rates.values())[-3:]  # 最近3年
            avg_recent_growth = sum(recent_growth_rates) / len(recent_growth_rates) if recent_growth_rates else 0
            
            if avg_recent_growth > 10:
                growth_direction = "strong_upward"
            elif avg_recent_growth > 0:
                growth_direction = "upward"
            elif avg_recent_growth > -10:
                growth_direction = "stable"
            else:
                growth_direction = "downward"
            
            direction_analysis["growth_based"] = {
                "direction": growth_direction,
                "average_recent_growth": avg_recent_growth,
                "confidence": min(abs(avg_recent_growth) / 20, 1.0)
            }
            
            # 2. 基于趋势强度的方向判断
            trend_strength = yearly_analysis.get("growth_pattern", "insufficient_data")
            direction_analysis["pattern_based"] = {
                "pattern": trend_strength,
                "direction_confidence": self._pattern_to_confidence(trend_strength)
            }
            
            # 3. 基于CAGR的长期方向判断
            cagr = yearly_analysis.get("cagr", 0)
            if cagr > 5:
                long_term_direction = "positive"
            elif cagr > -5:
                long_term_direction = "neutral"
            else:
                long_term_direction = "negative"
            
            direction_analysis["long_term"] = {
                "direction": long_term_direction,
                "cagr": cagr,
                "confidence": min(abs(cagr) / 20, 1.0)
            }
            
            # 4. 综合方向判断
            overall_direction = self._determine_overall_direction(direction_analysis)
            
            # 5. 方向变化点检测
            change_points = self._detect_direction_changes(yearly_summary)
            
            return {
                "individual_analyses": direction_analysis,
                "overall_direction": overall_direction,
                "change_points": change_points,
                "direction_stability": self._assess_direction_stability(growth_rates),
                "future_direction_probability": self._predict_direction_probability(direction_analysis)
            }
            
        except Exception as e:
            self.logger.error(f"Error in trend direction analysis: {str(e)}")
            return {"error": str(e)}
    
    def _pattern_to_confidence(self, pattern: str) -> float:
        """将增长模式转换为置信度."""
        pattern_confidence = {
            "rapid_growth": 0.9,
            "steady_growth": 0.8,
            "moderate_growth": 0.6,
            "fluctuating": 0.4,
            "declining": 0.7,
            "rapid_decline": 0.8,
            "insufficient_data": 0.1
        }
        return pattern_confidence.get(pattern, 0.5)
    
    def _determine_overall_direction(self, direction_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """确定总体方向."""
        # 权重分配
        weights = {
            "growth_based": 0.4,
            "pattern_based": 0.3,
            "long_term": 0.3
        }
        
        # 方向评分
        direction_scores = {
            "upward": 1.0,
            "strong_upward": 1.5,
            "positive": 1.0,
            "stable": 0.0,
            "neutral": 0.0,
            "downward": -1.0,
            "negative": -1.0
        }
        
        weighted_score = 0.0
        total_confidence = 0.0
        
        for analysis_type, weight in weights.items():
            if analysis_type in direction_analysis:
                analysis = direction_analysis[analysis_type]
                direction = analysis.get("direction", "stable")
                confidence = analysis.get("confidence", 0.5)
                
                score = direction_scores.get(direction, 0.0)
                weighted_score += score * weight * confidence
                total_confidence += weight * confidence
        
        # 确定最终方向
        if weighted_score > 0.3:
            final_direction = "increasing"
        elif weighted_score < -0.3:
            final_direction = "decreasing"
        else:
            final_direction = "stable"
        
        return {
            "direction": final_direction,
            "confidence": total_confidence / sum(weights.values()) if sum(weights.values()) > 0 else 0.0,
            "weighted_score": weighted_score,
            "strength": abs(weighted_score)
        }
    
    def _detect_direction_changes(self, yearly_summary: Dict[int, Dict[str, int]]) -> List[Dict[str, Any]]:
        """检测方向变化点."""
        change_points = []
        
        years = sorted(yearly_summary.keys())
        counts = [yearly_summary[year]["patent_count"] for year in years]
        
        if len(counts) < 3:
            return change_points
        
        # 检测显著的方向变化
        for i in range(2, len(counts)):
            prev_trend = counts[i-1] - counts[i-2]
            curr_trend = counts[i] - counts[i-1]
            
            # 检测趋势反转
            if (prev_trend > 0 and curr_trend < 0) or (prev_trend < 0 and curr_trend > 0):
                change_magnitude = abs(curr_trend - prev_trend)
                if change_magnitude > counts[i-1] * 0.2:  # 变化幅度超过20%
                    change_points.append({
                        "year": years[i],
                        "type": "trend_reversal",
                        "magnitude": change_magnitude,
                        "from_trend": "increasing" if prev_trend > 0 else "decreasing",
                        "to_trend": "increasing" if curr_trend > 0 else "decreasing"
                    })
        
        return change_points
    
    def _assess_direction_stability(self, growth_rates: Dict[int, float]) -> Dict[str, Any]:
        """评估方向稳定性."""
        if not growth_rates:
            return {"stability": "unknown", "score": 0.0}
        
        rates = list(growth_rates.values())
        
        # 计算增长率的标准差
        mean_rate = sum(rates) / len(rates)
        variance = sum((rate - mean_rate) ** 2 for rate in rates) / len(rates)
        std_dev = variance ** 0.5
        
        # 计算方向一致性
        positive_rates = sum(1 for rate in rates if rate > 0)
        negative_rates = sum(1 for rate in rates if rate < 0)
        
        direction_consistency = abs(positive_rates - negative_rates) / len(rates)
        
        # 综合稳定性评分
        volatility_score = max(0, 1 - std_dev / 50)  # 标准差越小越稳定
        consistency_score = direction_consistency
        
        stability_score = (volatility_score + consistency_score) / 2
        
        if stability_score > 0.8:
            stability_level = "high"
        elif stability_score > 0.6:
            stability_level = "medium"
        elif stability_score > 0.4:
            stability_level = "low"
        else:
            stability_level = "very_low"
        
        return {
            "stability": stability_level,
            "score": stability_score,
            "volatility": std_dev,
            "direction_consistency": direction_consistency
        }
    
    def _predict_direction_probability(self, direction_analysis: Dict[str, Any]) -> Dict[str, float]:
        """预测未来方向概率."""
        # 基于历史分析预测未来方向的概率
        probabilities = {
            "increasing": 0.33,
            "stable": 0.34,
            "decreasing": 0.33
        }
        
        # 根据各种分析调整概率
        for analysis_type, analysis in direction_analysis.items():
            direction = analysis.get("direction", "stable")
            confidence = analysis.get("confidence", 0.5)
            
            adjustment = confidence * 0.2  # 最大调整20%
            
            if direction in ["upward", "strong_upward", "positive"]:
                probabilities["increasing"] += adjustment
                probabilities["decreasing"] -= adjustment / 2
                probabilities["stable"] -= adjustment / 2
            elif direction in ["downward", "negative"]:
                probabilities["decreasing"] += adjustment
                probabilities["increasing"] -= adjustment / 2
                probabilities["stable"] -= adjustment / 2
        
        # 确保概率和为1
        total_prob = sum(probabilities.values())
        if total_prob > 0:
            probabilities = {k: v / total_prob for k, v in probabilities.items()}
        
        return probabilities
    
    async def _seasonality_analysis(self, processed_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """季节性和周期性分析."""
        try:
            # 按月份统计
            monthly_counts = defaultdict(int)
            quarterly_counts = defaultdict(int)
            
            for patent in processed_data:
                month = patent["month"]
                quarter = patent["quarter"]
                
                monthly_counts[month] += 1
                quarterly_counts[quarter] += 1
            
            # 检测季节性模式
            seasonality_strength = self._calculate_seasonality_strength(monthly_counts)
            
            # 识别峰值和低谷
            peak_months = self._identify_seasonal_peaks(monthly_counts)
            
            # 季度分析
            quarterly_analysis = self._analyze_quarterly_patterns(quarterly_counts)
            
            return {
                "monthly_distribution": dict(monthly_counts),
                "quarterly_distribution": dict(quarterly_counts),
                "seasonality_strength": seasonality_strength,
                "peak_months": peak_months,
                "quarterly_analysis": quarterly_analysis,
                "has_seasonality": seasonality_strength > 0.3
            }
            
        except Exception as e:
            self.logger.error(f"Error in seasonality analysis: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_seasonality_strength(self, monthly_counts: Dict[int, int]) -> float:
        """计算季节性强度."""
        if len(monthly_counts) < 12:
            return 0.0
        
        counts = [monthly_counts.get(i, 0) for i in range(1, 13)]
        mean_count = sum(counts) / len(counts)
        
        if mean_count == 0:
            return 0.0
        
        # 计算变异系数
        variance = sum((count - mean_count) ** 2 for count in counts) / len(counts)
        cv = (variance ** 0.5) / mean_count
        
        # 季节性强度基于变异系数
        return min(cv, 1.0)
    
    def _identify_seasonal_peaks(self, monthly_counts: Dict[int, int]) -> Dict[str, Any]:
        """识别季节性峰值和低谷."""
        if not monthly_counts:
            return {}
        
        counts = [(month, count) for month, count in monthly_counts.items()]
        counts.sort(key=lambda x: x[1], reverse=True)
        
        month_names = {
            1: "一月", 2: "二月", 3: "三月", 4: "四月", 5: "五月", 6: "六月",
            7: "七月", 8: "八月", 9: "九月", 10: "十月", 11: "十一月", 12: "十二月"
        }
        
        peak_months = counts[:3]  # 前3个峰值月份
        low_months = counts[-3:]  # 后3个低谷月份
        
        return {
            "peak_months": [(month_names.get(month, str(month)), count) for month, count in peak_months],
            "low_months": [(month_names.get(month, str(month)), count) for month, count in low_months]
        }
    
    def _analyze_quarterly_patterns(self, quarterly_counts: Dict[int, int]) -> Dict[str, Any]:
        """分析季度模式."""
        quarter_names = {1: "Q1", 2: "Q2", 3: "Q3", 4: "Q4"}
        
        if not quarterly_counts:
            return {}
        
        total_count = sum(quarterly_counts.values())
        quarterly_percentages = {
            quarter_names.get(q, f"Q{q}"): (count / total_count) * 100
            for q, count in quarterly_counts.items()
        }
        
        # 找出最活跃的季度
        max_quarter = max(quarterly_counts.items(), key=lambda x: x[1])
        min_quarter = min(quarterly_counts.items(), key=lambda x: x[1])
        
        return {
            "quarterly_percentages": quarterly_percentages,
            "most_active_quarter": quarter_names.get(max_quarter[0], f"Q{max_quarter[0]}"),
            "least_active_quarter": quarter_names.get(min_quarter[0], f"Q{min_quarter[0]}"),
            "quarterly_variation": max_quarter[1] - min_quarter[1]
        }
    
    async def _outlier_detection(self, processed_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """异常值检测和处理."""
        try:
            yearly_counts = defaultdict(int)
            for patent in processed_data:
                yearly_counts[patent["year"]] += 1
            
            if len(yearly_counts) < 3:
                return {"outliers": [], "method": "insufficient_data"}
            
            counts = list(yearly_counts.values())
            years = list(yearly_counts.keys())
            
            # 使用IQR方法检测异常值
            outliers = self._detect_outliers_iqr(counts, years)
            
            # 使用Z-score方法检测异常值
            z_score_outliers = self._detect_outliers_zscore(counts, years)
            
            # 合并结果
            all_outliers = list(set(outliers + z_score_outliers))
            
            # 分析异常值的可能原因
            outlier_analysis = self._analyze_outlier_causes(all_outliers, yearly_counts)
            
            return {
                "outliers": all_outliers,
                "iqr_outliers": outliers,
                "zscore_outliers": z_score_outliers,
                "outlier_analysis": outlier_analysis,
                "method": "combined_iqr_zscore"
            }
            
        except Exception as e:
            self.logger.error(f"Error in outlier detection: {str(e)}")
            return {"error": str(e)}
    
    def _detect_outliers_iqr(self, counts: List[int], years: List[int]) -> List[int]:
        """使用IQR方法检测异常值."""
        if len(counts) < 4:
            return []
        
        sorted_counts = sorted(counts)
        n = len(sorted_counts)
        
        q1_index = n // 4
        q3_index = 3 * n // 4
        
        q1 = sorted_counts[q1_index]
        q3 = sorted_counts[q3_index]
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outliers = []
        for i, count in enumerate(counts):
            if count < lower_bound or count > upper_bound:
                outliers.append(years[i])
        
        return outliers
    
    def _detect_outliers_zscore(self, counts: List[int], years: List[int], threshold: float = 2.0) -> List[int]:
        """使用Z-score方法检测异常值."""
        if len(counts) < 3:
            return []
        
        mean_count = sum(counts) / len(counts)
        variance = sum((count - mean_count) ** 2 for count in counts) / len(counts)
        std_dev = variance ** 0.5
        
        if std_dev == 0:
            return []
        
        outliers = []
        for i, count in enumerate(counts):
            z_score = abs(count - mean_count) / std_dev
            if z_score > threshold:
                outliers.append(years[i])
        
        return outliers
    
    def _analyze_outlier_causes(self, outliers: List[int], yearly_counts: Dict[int, int]) -> List[Dict[str, Any]]:
        """分析异常值的可能原因."""
        outlier_analysis = []
        
        for year in outliers:
            count = yearly_counts.get(year, 0)
            
            # 判断是高异常还是低异常
            all_counts = list(yearly_counts.values())
            mean_count = sum(all_counts) / len(all_counts)
            
            if count > mean_count:
                anomaly_type = "high"
                possible_causes = [
                    "政策推动或法规变化",
                    "技术突破或创新热潮",
                    "市场需求激增",
                    "竞争加剧导致专利布局"
                ]
            else:
                anomaly_type = "low"
                possible_causes = [
                    "经济衰退或市场萎缩",
                    "技术成熟度提高",
                    "政策限制或监管加强",
                    "数据收集问题"
                ]
            
            outlier_analysis.append({
                "year": year,
                "count": count,
                "anomaly_type": anomaly_type,
                "deviation_from_mean": count - mean_count,
                "possible_causes": possible_causes
            })
        
        return outlier_analysis
    
    async def _comprehensive_trend_assessment(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """综合趋势评估."""
        try:
            assessment = {
                "overall_trend": "unknown",
                "trend_strength": 0.0,
                "confidence_level": 0.0,
                "key_insights": [],
                "risk_factors": [],
                "opportunities": []
            }
            
            # 基于各项分析结果进行综合评估
            
            # 1. 整体趋势判断
            if "direction" in analysis_results:
                direction_data = analysis_results["direction"]
                overall_direction = direction_data.get("overall_direction", {})
                assessment["overall_trend"] = overall_direction.get("direction", "unknown")
                assessment["trend_strength"] = overall_direction.get("strength", 0.0)
                assessment["confidence_level"] = overall_direction.get("confidence", 0.0)
            
            # 2. 关键洞察提取
            insights = []
            
            # 基于时间序列分析的洞察
            if "time_series" in analysis_results:
                ts_data = analysis_results["time_series"]
                total_patents = ts_data.get("total_patents", 0)
                data_span = ts_data.get("data_span_years", 0)
                
                insights.append(f"在{data_span}年期间共有{total_patents}件专利申请")
                
                trend_strength = ts_data.get("trend_strength", {})
                if trend_strength.get("confidence", 0) > 0.7:
                    direction = trend_strength.get("direction", "stable")
                    insights.append(f"专利申请呈现{direction}趋势，趋势强度较高")
            
            # 基于年度增长分析的洞察
            if "yearly_analysis" in analysis_results:
                yearly_data = analysis_results["yearly_analysis"]
                cagr = yearly_data.get("cagr", 0)
                growth_pattern = yearly_data.get("growth_pattern", "unknown")
                
                if abs(cagr) > 5:
                    insights.append(f"复合年增长率为{cagr:.1f}%，显示{growth_pattern}模式")
            
            # 基于预测分析的洞察
            if "prediction" in analysis_results:
                pred_data = analysis_results["prediction"]
                confidence_assessment = pred_data.get("confidence_assessment", {})
                confidence_level = confidence_assessment.get("confidence_level", "unknown")
                
                insights.append(f"未来趋势预测置信度为{confidence_level}")
            
            assessment["key_insights"] = insights
            
            # 3. 风险因素识别
            risks = []
            
            # 基于异常值检测的风险
            if "outliers" in analysis_results:
                outlier_data = analysis_results["outliers"]
                outliers = outlier_data.get("outliers", [])
                if outliers:
                    risks.append(f"检测到{len(outliers)}个异常年份，可能存在外部干扰因素")
            
            # 基于趋势稳定性的风险
            if "direction" in analysis_results:
                direction_data = analysis_results["direction"]
                stability = direction_data.get("direction_stability", {})
                if stability.get("stability") in ["low", "very_low"]:
                    risks.append("趋势稳定性较低，未来发展存在不确定性")
            
            # 基于季节性的风险
            if "seasonality" in analysis_results:
                seasonal_data = analysis_results["seasonality"]
                if seasonal_data.get("has_seasonality", False):
                    risks.append("存在明显的季节性波动，需要考虑周期性因素")
            
            assessment["risk_factors"] = risks
            
            # 4. 机会识别
            opportunities = []
            
            if assessment["overall_trend"] == "increasing":
                opportunities.append("市场呈增长趋势，适合加大投入和布局")
            
            if assessment["trend_strength"] > 0.7:
                opportunities.append("趋势强度较高，发展方向明确")
            
            if assessment["confidence_level"] > 0.7:
                opportunities.append("预测置信度较高，可以制定中长期战略")
            
            assessment["opportunities"] = opportunities
            
            return assessment
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive trend assessment: {str(e)}")
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
            
            # 集成现有性能监控和错误处理机制
            self.logger.info(f"Performance metrics updated: {json.dumps(self.performance_metrics, ensure_ascii=False)}")
            
        except Exception as e:
            self.logger.error(f"Error updating performance metrics: {str(e)}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标."""
        return self.performance_metrics.copy()