"""Patent workflow quality control system."""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from uuid import uuid4
from enum import Enum
from dataclasses import dataclass
from collections import defaultdict

from ...models.base import AgentResponse
from ...models.enums import WorkflowStatus
from ...workflows.state_management import WorkflowStateManager
from ...utils.monitoring import MonitoringSystem


logger = logging.getLogger(__name__)


class QualityCheckType(Enum):
    """质量检查类型."""
    DATA_VALIDATION = "data_validation"
    RESULT_CONSISTENCY = "result_consistency"
    PERFORMANCE_CHECK = "performance_check"
    COMPLETENESS_CHECK = "completeness_check"
    ACCURACY_VALIDATION = "accuracy_validation"
    CROSS_VALIDATION = "cross_validation"


class QualityLevel(Enum):
    """质量等级."""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    FAILED = "failed"


@dataclass
class QualityMetric:
    """质量指标."""
    metric_name: str
    value: float
    threshold: float
    weight: float
    passed: bool
    description: str


@dataclass
class QualityCheckResult:
    """质量检查结果."""
    check_id: str
    check_type: QualityCheckType
    target_id: str  # 被检查的对象ID（任务、工作流等）
    overall_score: float
    quality_level: QualityLevel
    metrics: List[QualityMetric]
    issues: List[str]
    recommendations: List[str]
    timestamp: datetime
    passed: bool


class PatentDataValidator:
    """专利数据验证器."""
    
    def __init__(self):
        self.validation_rules = {
            "patent_data": {
                "required_fields": ["title", "application_number", "applicants"],
                "field_types": {
                    "title": str,
                    "application_number": str,
                    "applicants": list,
                    "application_date": str,
                    "ipc_classes": list
                },
                "field_constraints": {
                    "title": {"min_length": 5, "max_length": 500},
                    "application_number": {"pattern": r"^[A-Z]{2}\d+"},
                    "applicants": {"min_items": 1}
                }
            },
            "search_results": {
                "required_fields": ["query", "results", "total_count"],
                "field_types": {
                    "query": str,
                    "results": list,
                    "total_count": int
                },
                "field_constraints": {
                    "query": {"min_length": 1},
                    "total_count": {"min_value": 0}
                }
            },
            "analysis_results": {
                "required_fields": ["analysis_type", "results", "confidence"],
                "field_types": {
                    "analysis_type": str,
                    "results": dict,
                    "confidence": float
                },
                "field_constraints": {
                    "confidence": {"min_value": 0.0, "max_value": 1.0}
                }
            }
        }
    
    async def validate_data(self, data_type: str, data: Dict[str, Any]) -> QualityCheckResult:
        """验证数据质量."""
        check_id = str(uuid4())
        metrics = []
        issues = []
        
        if data_type not in self.validation_rules:
            return QualityCheckResult(
                check_id=check_id,
                check_type=QualityCheckType.DATA_VALIDATION,
                target_id=data_type,
                overall_score=0.0,
                quality_level=QualityLevel.FAILED,
                metrics=[],
                issues=[f"Unknown data type: {data_type}"],
                recommendations=["Use supported data types"],
                timestamp=datetime.now(),
                passed=False
            )
        
        rules = self.validation_rules[data_type]
        
        # 检查必需字段
        required_score = self._check_required_fields(data, rules["required_fields"], issues)
        metrics.append(QualityMetric(
            metric_name="required_fields",
            value=required_score,
            threshold=1.0,
            weight=0.3,
            passed=required_score >= 1.0,
            description="All required fields present"
        ))
        
        # 检查字段类型
        type_score = self._check_field_types(data, rules["field_types"], issues)
        metrics.append(QualityMetric(
            metric_name="field_types",
            value=type_score,
            threshold=0.9,
            weight=0.2,
            passed=type_score >= 0.9,
            description="Field types are correct"
        ))
        
        # 检查字段约束
        constraint_score = self._check_field_constraints(data, rules["field_constraints"], issues)
        metrics.append(QualityMetric(
            metric_name="field_constraints",
            value=constraint_score,
            threshold=0.8,
            weight=0.3,
            passed=constraint_score >= 0.8,
            description="Field constraints satisfied"
        ))
        
        # 检查数据完整性
        completeness_score = self._check_data_completeness(data, issues)
        metrics.append(QualityMetric(
            metric_name="data_completeness",
            value=completeness_score,
            threshold=0.7,
            weight=0.2,
            passed=completeness_score >= 0.7,
            description="Data is reasonably complete"
        ))
        
        # 计算总分
        overall_score = sum(metric.value * metric.weight for metric in metrics)
        quality_level = self._determine_quality_level(overall_score)
        passed = all(metric.passed for metric in metrics)
        
        # 生成建议
        recommendations = self._generate_data_recommendations(metrics, issues)
        
        return QualityCheckResult(
            check_id=check_id,
            check_type=QualityCheckType.DATA_VALIDATION,
            target_id=data_type,
            overall_score=overall_score,
            quality_level=quality_level,
            metrics=metrics,
            issues=issues,
            recommendations=recommendations,
            timestamp=datetime.now(),
            passed=passed
        )
    
    def _check_required_fields(self, data: Dict[str, Any], required_fields: List[str], 
                              issues: List[str]) -> float:
        """检查必需字段."""
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            issues.extend([f"Missing required field: {field}" for field in missing_fields])
        
        return (len(required_fields) - len(missing_fields)) / len(required_fields)
    
    def _check_field_types(self, data: Dict[str, Any], field_types: Dict[str, type], 
                          issues: List[str]) -> float:
        """检查字段类型."""
        correct_types = 0
        total_fields = 0
        
        for field, expected_type in field_types.items():
            if field in data:
                total_fields += 1
                if isinstance(data[field], expected_type):
                    correct_types += 1
                else:
                    issues.append(f"Field '{field}' has incorrect type: expected {expected_type.__name__}, got {type(data[field]).__name__}")
        
        return correct_types / total_fields if total_fields > 0 else 1.0
    
    def _check_field_constraints(self, data: Dict[str, Any], constraints: Dict[str, Dict[str, Any]], 
                                issues: List[str]) -> float:
        """检查字段约束."""
        satisfied_constraints = 0
        total_constraints = 0
        
        for field, field_constraints in constraints.items():
            if field not in data:
                continue
            
            value = data[field]
            
            for constraint_name, constraint_value in field_constraints.items():
                total_constraints += 1
                
                if constraint_name == "min_length" and isinstance(value, str):
                    if len(value) >= constraint_value:
                        satisfied_constraints += 1
                    else:
                        issues.append(f"Field '{field}' too short: {len(value)} < {constraint_value}")
                
                elif constraint_name == "max_length" and isinstance(value, str):
                    if len(value) <= constraint_value:
                        satisfied_constraints += 1
                    else:
                        issues.append(f"Field '{field}' too long: {len(value)} > {constraint_value}")
                
                elif constraint_name == "min_items" and isinstance(value, list):
                    if len(value) >= constraint_value:
                        satisfied_constraints += 1
                    else:
                        issues.append(f"Field '{field}' has too few items: {len(value)} < {constraint_value}")
                
                elif constraint_name == "min_value" and isinstance(value, (int, float)):
                    if value >= constraint_value:
                        satisfied_constraints += 1
                    else:
                        issues.append(f"Field '{field}' value too small: {value} < {constraint_value}")
                
                elif constraint_name == "max_value" and isinstance(value, (int, float)):
                    if value <= constraint_value:
                        satisfied_constraints += 1
                    else:
                        issues.append(f"Field '{field}' value too large: {value} > {constraint_value}")
                
                elif constraint_name == "pattern" and isinstance(value, str):
                    import re
                    if re.match(constraint_value, value):
                        satisfied_constraints += 1
                    else:
                        issues.append(f"Field '{field}' doesn't match pattern: {constraint_value}")
        
        return satisfied_constraints / total_constraints if total_constraints > 0 else 1.0
    
    def _check_data_completeness(self, data: Dict[str, Any], issues: List[str]) -> float:
        """检查数据完整性."""
        total_fields = len(data)
        complete_fields = 0
        
        for key, value in data.items():
            if value is not None and value != "" and value != []:
                complete_fields += 1
            else:
                issues.append(f"Field '{key}' is empty or null")
        
        return complete_fields / total_fields if total_fields > 0 else 1.0
    
    def _determine_quality_level(self, score: float) -> QualityLevel:
        """确定质量等级."""
        if score >= 0.9:
            return QualityLevel.EXCELLENT
        elif score >= 0.8:
            return QualityLevel.GOOD
        elif score >= 0.7:
            return QualityLevel.ACCEPTABLE
        elif score >= 0.5:
            return QualityLevel.POOR
        else:
            return QualityLevel.FAILED
    
    def _generate_data_recommendations(self, metrics: List[QualityMetric], 
                                     issues: List[str]) -> List[str]:
        """生成数据改进建议."""
        recommendations = []
        
        for metric in metrics:
            if not metric.passed:
                if metric.metric_name == "required_fields":
                    recommendations.append("Ensure all required fields are provided")
                elif metric.metric_name == "field_types":
                    recommendations.append("Verify field types match expected schema")
                elif metric.metric_name == "field_constraints":
                    recommendations.append("Check field values meet constraints")
                elif metric.metric_name == "data_completeness":
                    recommendations.append("Fill in missing or empty fields")
        
        if len(issues) > 5:
            recommendations.append("Consider data preprocessing to improve quality")
        
        return recommendations


class PatentResultConsistencyChecker:
    """专利结果一致性检查器."""
    
    def __init__(self):
        self.consistency_thresholds = {
            "trend_analysis": 0.8,
            "competition_analysis": 0.75,
            "classification_analysis": 0.85,
            "search_results": 0.7
        }
    
    async def check_result_consistency(self, results: List[Dict[str, Any]], 
                                     analysis_type: str) -> QualityCheckResult:
        """检查结果一致性."""
        check_id = str(uuid4())
        metrics = []
        issues = []
        
        if len(results) < 2:
            return QualityCheckResult(
                check_id=check_id,
                check_type=QualityCheckType.RESULT_CONSISTENCY,
                target_id=analysis_type,
                overall_score=1.0,
                quality_level=QualityLevel.EXCELLENT,
                metrics=[],
                issues=[],
                recommendations=[],
                timestamp=datetime.now(),
                passed=True
            )
        
        # 检查数值一致性
        numerical_consistency = self._check_numerical_consistency(results, issues)
        metrics.append(QualityMetric(
            metric_name="numerical_consistency",
            value=numerical_consistency,
            threshold=0.8,
            weight=0.4,
            passed=numerical_consistency >= 0.8,
            description="Numerical results are consistent"
        ))
        
        # 检查分类一致性
        categorical_consistency = self._check_categorical_consistency(results, issues)
        metrics.append(QualityMetric(
            metric_name="categorical_consistency",
            value=categorical_consistency,
            threshold=0.7,
            weight=0.3,
            passed=categorical_consistency >= 0.7,
            description="Categorical results are consistent"
        ))
        
        # 检查趋势一致性
        trend_consistency = self._check_trend_consistency(results, issues)
        metrics.append(QualityMetric(
            metric_name="trend_consistency",
            value=trend_consistency,
            threshold=0.75,
            weight=0.3,
            passed=trend_consistency >= 0.75,
            description="Trend directions are consistent"
        ))
        
        # 计算总分
        overall_score = sum(metric.value * metric.weight for metric in metrics)
        quality_level = self._determine_quality_level(overall_score)
        
        threshold = self.consistency_thresholds.get(analysis_type, 0.75)
        passed = overall_score >= threshold
        
        recommendations = self._generate_consistency_recommendations(metrics, issues)
        
        return QualityCheckResult(
            check_id=check_id,
            check_type=QualityCheckType.RESULT_CONSISTENCY,
            target_id=analysis_type,
            overall_score=overall_score,
            quality_level=quality_level,
            metrics=metrics,
            issues=issues,
            recommendations=recommendations,
            timestamp=datetime.now(),
            passed=passed
        )
    
    def _check_numerical_consistency(self, results: List[Dict[str, Any]], 
                                   issues: List[str]) -> float:
        """检查数值一致性."""
        numerical_fields = []
        
        # 提取所有数值字段
        for result in results:
            for key, value in result.items():
                if isinstance(value, (int, float)) and key not in [field[0] for field in numerical_fields]:
                    numerical_fields.append((key, []))
        
        # 收集每个字段的值
        for field_name, values in numerical_fields:
            for result in results:
                if field_name in result and isinstance(result[field_name], (int, float)):
                    values.append(result[field_name])
        
        # 计算一致性
        consistent_fields = 0
        total_fields = len(numerical_fields)
        
        for field_name, values in numerical_fields:
            if len(values) < 2:
                consistent_fields += 1
                continue
            
            # 计算变异系数
            mean_val = sum(values) / len(values)
            if mean_val == 0:
                consistent_fields += 1
                continue
            
            variance = sum((x - mean_val) ** 2 for x in values) / len(values)
            std_dev = variance ** 0.5
            cv = std_dev / abs(mean_val)  # 变异系数
            
            if cv <= 0.2:  # 变异系数小于20%认为一致
                consistent_fields += 1
            else:
                issues.append(f"High variance in field '{field_name}': CV = {cv:.2f}")
        
        return consistent_fields / total_fields if total_fields > 0 else 1.0
    
    def _check_categorical_consistency(self, results: List[Dict[str, Any]], 
                                     issues: List[str]) -> float:
        """检查分类一致性."""
        categorical_fields = []
        
        # 提取分类字段
        for result in results:
            for key, value in result.items():
                if isinstance(value, (str, list)) and key not in [field[0] for field in categorical_fields]:
                    categorical_fields.append((key, []))
        
        # 收集每个字段的值
        for field_name, values in categorical_fields:
            for result in results:
                if field_name in result:
                    value = result[field_name]
                    if isinstance(value, list):
                        values.extend(value)
                    else:
                        values.append(value)
        
        # 计算一致性
        consistent_fields = 0
        total_fields = len(categorical_fields)
        
        for field_name, values in categorical_fields:
            if len(values) < 2:
                consistent_fields += 1
                continue
            
            # 计算最频繁值的比例
            value_counts = {}
            for value in values:
                value_counts[value] = value_counts.get(value, 0) + 1
            
            max_count = max(value_counts.values())
            consistency_ratio = max_count / len(values)
            
            if consistency_ratio >= 0.6:  # 60%以上一致认为合格
                consistent_fields += 1
            else:
                issues.append(f"Low consistency in field '{field_name}': {consistency_ratio:.2f}")
        
        return consistent_fields / total_fields if total_fields > 0 else 1.0
    
    def _check_trend_consistency(self, results: List[Dict[str, Any]], 
                               issues: List[str]) -> float:
        """检查趋势一致性."""
        trend_indicators = ["trend", "direction", "growth", "change"]
        trend_data = []
        
        for result in results:
            for key, value in result.items():
                if any(indicator in key.lower() for indicator in trend_indicators):
                    if isinstance(value, str):
                        trend_data.append(value.lower())
                    elif isinstance(value, (int, float)):
                        trend_data.append("positive" if value > 0 else "negative" if value < 0 else "stable")
        
        if len(trend_data) < 2:
            return 1.0
        
        # 计算趋势一致性
        trend_counts = {}
        for trend in trend_data:
            trend_counts[trend] = trend_counts.get(trend, 0) + 1
        
        max_count = max(trend_counts.values())
        consistency_ratio = max_count / len(trend_data)
        
        if consistency_ratio < 0.6:
            issues.append(f"Inconsistent trend directions: {trend_counts}")
        
        return consistency_ratio
    
    def _determine_quality_level(self, score: float) -> QualityLevel:
        """确定质量等级."""
        if score >= 0.9:
            return QualityLevel.EXCELLENT
        elif score >= 0.8:
            return QualityLevel.GOOD
        elif score >= 0.7:
            return QualityLevel.ACCEPTABLE
        elif score >= 0.5:
            return QualityLevel.POOR
        else:
            return QualityLevel.FAILED
    
    def _generate_consistency_recommendations(self, metrics: List[QualityMetric], 
                                           issues: List[str]) -> List[str]:
        """生成一致性改进建议."""
        recommendations = []
        
        for metric in metrics:
            if not metric.passed:
                if metric.metric_name == "numerical_consistency":
                    recommendations.append("Review numerical calculation methods for consistency")
                elif metric.metric_name == "categorical_consistency":
                    recommendations.append("Standardize categorical classification criteria")
                elif metric.metric_name == "trend_consistency":
                    recommendations.append("Verify trend analysis methodology")
        
        if len(issues) > 3:
            recommendations.append("Consider cross-validation with additional data sources")
        
        return recommendations


class PatentPerformanceMonitor:
    """专利性能监控器."""
    
    def __init__(self):
        self.performance_thresholds = {
            "response_time": 30.0,  # 秒
            "throughput": 10.0,     # 任务/分钟
            "error_rate": 0.05,     # 5%
            "resource_usage": 0.8   # 80%
        }
        
        self.performance_history = defaultdict(list)
    
    async def check_performance(self, execution_data: Dict[str, Any]) -> QualityCheckResult:
        """检查性能指标."""
        check_id = str(uuid4())
        metrics = []
        issues = []
        
        # 检查响应时间
        response_time_score = self._check_response_time(execution_data, issues)
        metrics.append(QualityMetric(
            metric_name="response_time",
            value=response_time_score,
            threshold=0.8,
            weight=0.3,
            passed=response_time_score >= 0.8,
            description="Response time within acceptable limits"
        ))
        
        # 检查吞吐量
        throughput_score = self._check_throughput(execution_data, issues)
        metrics.append(QualityMetric(
            metric_name="throughput",
            value=throughput_score,
            threshold=0.7,
            weight=0.25,
            passed=throughput_score >= 0.7,
            description="Processing throughput meets requirements"
        ))
        
        # 检查错误率
        error_rate_score = self._check_error_rate(execution_data, issues)
        metrics.append(QualityMetric(
            metric_name="error_rate",
            value=error_rate_score,
            threshold=0.9,
            weight=0.25,
            passed=error_rate_score >= 0.9,
            description="Error rate within acceptable limits"
        ))
        
        # 检查资源使用
        resource_score = self._check_resource_usage(execution_data, issues)
        metrics.append(QualityMetric(
            metric_name="resource_usage",
            value=resource_score,
            threshold=0.8,
            weight=0.2,
            passed=resource_score >= 0.8,
            description="Resource usage is efficient"
        ))
        
        # 计算总分
        overall_score = sum(metric.value * metric.weight for metric in metrics)
        quality_level = self._determine_quality_level(overall_score)
        passed = all(metric.passed for metric in metrics)
        
        recommendations = self._generate_performance_recommendations(metrics, issues)
        
        return QualityCheckResult(
            check_id=check_id,
            check_type=QualityCheckType.PERFORMANCE_CHECK,
            target_id=execution_data.get("execution_id", "unknown"),
            overall_score=overall_score,
            quality_level=quality_level,
            metrics=metrics,
            issues=issues,
            recommendations=recommendations,
            timestamp=datetime.now(),
            passed=passed
        )
    
    def _check_response_time(self, execution_data: Dict[str, Any], issues: List[str]) -> float:
        """检查响应时间."""
        execution_time = execution_data.get("execution_time", 0)
        threshold = self.performance_thresholds["response_time"]
        
        if execution_time <= threshold:
            score = 1.0
        elif execution_time <= threshold * 2:
            score = 1.0 - (execution_time - threshold) / threshold
        else:
            score = 0.0
            issues.append(f"Response time too high: {execution_time:.2f}s > {threshold}s")
        
        return max(0.0, score)
    
    def _check_throughput(self, execution_data: Dict[str, Any], issues: List[str]) -> float:
        """检查吞吐量."""
        tasks_completed = execution_data.get("tasks_completed", 0)
        execution_time = execution_data.get("execution_time", 1)
        
        throughput = (tasks_completed * 60) / execution_time  # 任务/分钟
        threshold = self.performance_thresholds["throughput"]
        
        if throughput >= threshold:
            score = 1.0
        elif throughput >= threshold * 0.5:
            score = throughput / threshold
        else:
            score = 0.0
            issues.append(f"Throughput too low: {throughput:.2f} < {threshold}")
        
        return min(1.0, score)
    
    def _check_error_rate(self, execution_data: Dict[str, Any], issues: List[str]) -> float:
        """检查错误率."""
        total_tasks = execution_data.get("total_tasks", 1)
        failed_tasks = execution_data.get("failed_tasks", 0)
        
        error_rate = failed_tasks / total_tasks
        threshold = self.performance_thresholds["error_rate"]
        
        if error_rate <= threshold:
            score = 1.0
        else:
            score = max(0.0, 1.0 - (error_rate - threshold) / (1.0 - threshold))
            issues.append(f"Error rate too high: {error_rate:.2%} > {threshold:.2%}")
        
        return score
    
    def _check_resource_usage(self, execution_data: Dict[str, Any], issues: List[str]) -> float:
        """检查资源使用."""
        cpu_usage = execution_data.get("cpu_usage", 0.5)
        memory_usage = execution_data.get("memory_usage", 0.5)
        
        threshold = self.performance_thresholds["resource_usage"]
        
        # 资源使用应该适中（不太高也不太低）
        cpu_score = 1.0 if cpu_usage <= threshold else max(0.0, 2.0 - cpu_usage / threshold)
        memory_score = 1.0 if memory_usage <= threshold else max(0.0, 2.0 - memory_usage / threshold)
        
        if cpu_usage > threshold:
            issues.append(f"High CPU usage: {cpu_usage:.2%}")
        if memory_usage > threshold:
            issues.append(f"High memory usage: {memory_usage:.2%}")
        
        return (cpu_score + memory_score) / 2
    
    def _determine_quality_level(self, score: float) -> QualityLevel:
        """确定质量等级."""
        if score >= 0.9:
            return QualityLevel.EXCELLENT
        elif score >= 0.8:
            return QualityLevel.GOOD
        elif score >= 0.7:
            return QualityLevel.ACCEPTABLE
        elif score >= 0.5:
            return QualityLevel.POOR
        else:
            return QualityLevel.FAILED
    
    def _generate_performance_recommendations(self, metrics: List[QualityMetric], 
                                           issues: List[str]) -> List[str]:
        """生成性能改进建议."""
        recommendations = []
        
        for metric in metrics:
            if not metric.passed:
                if metric.metric_name == "response_time":
                    recommendations.append("Optimize processing algorithms or increase resources")
                elif metric.metric_name == "throughput":
                    recommendations.append("Consider parallel processing or load balancing")
                elif metric.metric_name == "error_rate":
                    recommendations.append("Improve error handling and input validation")
                elif metric.metric_name == "resource_usage":
                    recommendations.append("Optimize resource allocation and usage patterns")
        
        return recommendations


class WorkflowQualityController:
    """工作流质量控制器."""
    
    def __init__(self, state_manager: Optional[WorkflowStateManager] = None,
                 monitoring_system: Optional[MonitoringSystem] = None):
        self.state_manager = state_manager or WorkflowStateManager()
        self.monitoring_system = monitoring_system
        
        # 质量检查器
        self.data_validator = PatentDataValidator()
        self.consistency_checker = PatentResultConsistencyChecker()
        self.performance_monitor = PatentPerformanceMonitor()
        
        # 质量检查历史
        self.quality_history: Dict[str, List[QualityCheckResult]] = defaultdict(list)
        
        # 质量阈值配置
        self.quality_thresholds = {
            "overall_quality": 0.8,
            "data_quality": 0.85,
            "consistency_quality": 0.75,
            "performance_quality": 0.8
        }
        
        # 告警配置
        self.alert_thresholds = {
            "quality_degradation": 0.6,
            "consecutive_failures": 3,
            "performance_degradation": 0.5
        }
        
        # 实时监控状态
        self.monitoring_active = True
        self.quality_alerts: List[Dict[str, Any]] = []
    
    async def validate_workflow_input(self, workflow_id: str, input_data: Dict[str, Any]) -> QualityCheckResult:
        """验证工作流输入数据质量."""
        try:
            # 确定数据类型
            data_type = self._determine_data_type(input_data)
            
            # 执行数据验证
            result = await self.data_validator.validate_data(data_type, input_data)
            
            # 记录质量检查结果
            self.quality_history[workflow_id].append(result)
            
            # 检查是否需要告警
            await self._check_quality_alerts(workflow_id, result)
            
            logger.info(f"Input validation for workflow {workflow_id}: {result.quality_level.value}")
            return result
            
        except Exception as e:
            logger.error(f"Input validation failed for workflow {workflow_id}: {str(e)}")
            return QualityCheckResult(
                check_id=str(uuid4()),
                check_type=QualityCheckType.DATA_VALIDATION,
                target_id=workflow_id,
                overall_score=0.0,
                quality_level=QualityLevel.FAILED,
                metrics=[],
                issues=[f"Validation error: {str(e)}"],
                recommendations=["Check input data format and content"],
                timestamp=datetime.now(),
                passed=False
            )
    
    async def validate_agent_results(self, workflow_id: str, agent_results: List[AgentResponse]) -> QualityCheckResult:
        """验证Agent结果的一致性."""
        try:
            # 提取结果数据
            results_data = []
            for response in agent_results:
                if hasattr(response, 'metadata') and response.metadata:
                    results_data.append(response.metadata)
                else:
                    results_data.append({"response": response.response_content})
            
            # 执行一致性检查
            result = await self.consistency_checker.check_result_consistency(
                results_data, "agent_results"
            )
            
            # 记录质量检查结果
            self.quality_history[workflow_id].append(result)
            
            # 检查是否需要告警
            await self._check_quality_alerts(workflow_id, result)
            
            logger.info(f"Result validation for workflow {workflow_id}: {result.quality_level.value}")
            return result
            
        except Exception as e:
            logger.error(f"Result validation failed for workflow {workflow_id}: {str(e)}")
            return QualityCheckResult(
                check_id=str(uuid4()),
                check_type=QualityCheckType.RESULT_CONSISTENCY,
                target_id=workflow_id,
                overall_score=0.0,
                quality_level=QualityLevel.FAILED,
                metrics=[],
                issues=[f"Validation error: {str(e)}"],
                recommendations=["Check agent result format and consistency"],
                timestamp=datetime.now(),
                passed=False
            )
    
    async def monitor_workflow_performance(self, workflow_id: str, 
                                         execution_data: Dict[str, Any]) -> QualityCheckResult:
        """监控工作流性能."""
        try:
            # 执行性能检查
            result = await self.performance_monitor.check_performance(execution_data)
            
            # 记录质量检查结果
            self.quality_history[workflow_id].append(result)
            
            # 检查是否需要告警
            await self._check_quality_alerts(workflow_id, result)
            
            # 发送监控数据到监控系统
            if self.monitoring_system:
                await self._send_performance_metrics(workflow_id, result)
            
            logger.info(f"Performance monitoring for workflow {workflow_id}: {result.quality_level.value}")
            return result
            
        except Exception as e:
            logger.error(f"Performance monitoring failed for workflow {workflow_id}: {str(e)}")
            return QualityCheckResult(
                check_id=str(uuid4()),
                check_type=QualityCheckType.PERFORMANCE_CHECK,
                target_id=workflow_id,
                overall_score=0.0,
                quality_level=QualityLevel.FAILED,
                metrics=[],
                issues=[f"Monitoring error: {str(e)}"],
                recommendations=["Check monitoring system configuration"],
                timestamp=datetime.now(),
                passed=False
            )
    
    async def cross_validate_results(self, workflow_id: str, 
                                   primary_results: Dict[str, Any],
                                   validation_results: List[Dict[str, Any]]) -> QualityCheckResult:
        """交叉验证结果."""
        try:
            all_results = [primary_results] + validation_results
            
            # 执行交叉验证
            result = await self.consistency_checker.check_result_consistency(
                all_results, "cross_validation"
            )
            
            # 记录质量检查结果
            self.quality_history[workflow_id].append(result)
            
            logger.info(f"Cross validation for workflow {workflow_id}: {result.quality_level.value}")
            return result
            
        except Exception as e:
            logger.error(f"Cross validation failed for workflow {workflow_id}: {str(e)}")
            return QualityCheckResult(
                check_id=str(uuid4()),
                check_type=QualityCheckType.CROSS_VALIDATION,
                target_id=workflow_id,
                overall_score=0.0,
                quality_level=QualityLevel.FAILED,
                metrics=[],
                issues=[f"Cross validation error: {str(e)}"],
                recommendations=["Check validation data and methodology"],
                timestamp=datetime.now(),
                passed=False
            )
    
    async def generate_quality_report(self, workflow_id: str) -> Dict[str, Any]:
        """生成质量报告."""
        try:
            history = self.quality_history.get(workflow_id, [])
            
            if not history:
                return {
                    "workflow_id": workflow_id,
                    "status": "no_data",
                    "message": "No quality check data available"
                }
            
            # 计算总体质量指标
            overall_scores = [check.overall_score for check in history]
            avg_score = sum(overall_scores) / len(overall_scores)
            
            # 按检查类型分组
            checks_by_type = defaultdict(list)
            for check in history:
                checks_by_type[check.check_type].append(check)
            
            # 生成报告
            report = {
                "workflow_id": workflow_id,
                "generated_at": datetime.now().isoformat(),
                "overall_quality": {
                    "average_score": avg_score,
                    "quality_level": self._determine_overall_quality_level(avg_score),
                    "total_checks": len(history),
                    "passed_checks": len([c for c in history if c.passed]),
                    "failed_checks": len([c for c in history if not c.passed])
                },
                "quality_by_type": {},
                "quality_trends": self._analyze_quality_trends(history),
                "recommendations": self._generate_overall_recommendations(history),
                "alerts": [alert for alert in self.quality_alerts 
                          if alert.get("workflow_id") == workflow_id]
            }
            
            # 按类型统计
            for check_type, type_checks in checks_by_type.items():
                type_scores = [check.overall_score for check in type_checks]
                report["quality_by_type"][check_type.value] = {
                    "average_score": sum(type_scores) / len(type_scores),
                    "check_count": len(type_checks),
                    "latest_check": type_checks[-1].timestamp.isoformat(),
                    "passed_rate": len([c for c in type_checks if c.passed]) / len(type_checks)
                }
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate quality report for workflow {workflow_id}: {str(e)}")
            return {
                "workflow_id": workflow_id,
                "status": "error",
                "error": str(e)
            }
    
    def _determine_data_type(self, data: Dict[str, Any]) -> str:
        """确定数据类型."""
        if "query" in data and "results" in data:
            return "search_results"
        elif "analysis_type" in data and "results" in data:
            return "analysis_results"
        elif "title" in data or "application_number" in data:
            return "patent_data"
        else:
            return "generic_data"
    
    def _determine_overall_quality_level(self, score: float) -> str:
        """确定总体质量等级."""
        if score >= 0.9:
            return "excellent"
        elif score >= 0.8:
            return "good"
        elif score >= 0.7:
            return "acceptable"
        elif score >= 0.5:
            return "poor"
        else:
            return "failed"
    
    def _analyze_quality_trends(self, history: List[QualityCheckResult]) -> Dict[str, Any]:
        """分析质量趋势."""
        if len(history) < 2:
            return {"trend": "insufficient_data"}
        
        # 计算最近的趋势
        recent_scores = [check.overall_score for check in history[-5:]]
        
        if len(recent_scores) >= 2:
            trend_slope = (recent_scores[-1] - recent_scores[0]) / (len(recent_scores) - 1)
            
            if trend_slope > 0.05:
                trend = "improving"
            elif trend_slope < -0.05:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "recent_average": sum(recent_scores) / len(recent_scores),
            "trend_slope": trend_slope if 'trend_slope' in locals() else 0
        }
    
    def _generate_overall_recommendations(self, history: List[QualityCheckResult]) -> List[str]:
        """生成总体建议."""
        recommendations = set()
        
        # 收集所有建议
        for check in history:
            recommendations.update(check.recommendations)
        
        # 添加基于趋势的建议
        trends = self._analyze_quality_trends(history)
        if trends["trend"] == "declining":
            recommendations.add("Quality is declining - review and improve processes")
        
        # 添加基于失败率的建议
        failed_checks = [check for check in history if not check.passed]
        if len(failed_checks) / len(history) > 0.3:
            recommendations.add("High failure rate - consider process redesign")
        
        return list(recommendations)
    
    async def _check_quality_alerts(self, workflow_id: str, result: QualityCheckResult):
        """检查是否需要发出质量告警."""
        # 质量降级告警
        if result.overall_score < self.alert_thresholds["quality_degradation"]:
            alert = {
                "alert_id": str(uuid4()),
                "workflow_id": workflow_id,
                "alert_type": "quality_degradation",
                "severity": "high" if result.overall_score < 0.3 else "medium",
                "message": f"Quality score dropped to {result.overall_score:.2f}",
                "timestamp": datetime.now().isoformat(),
                "check_result": result
            }
            self.quality_alerts.append(alert)
            
            # 发送到监控系统
            if self.monitoring_system:
                await self.monitoring_system.send_alert(alert)
        
        # 连续失败告警
        recent_checks = self.quality_history[workflow_id][-self.alert_thresholds["consecutive_failures"]:]
        if (len(recent_checks) >= self.alert_thresholds["consecutive_failures"] and
            all(not check.passed for check in recent_checks)):
            
            alert = {
                "alert_id": str(uuid4()),
                "workflow_id": workflow_id,
                "alert_type": "consecutive_failures",
                "severity": "critical",
                "message": f"Consecutive quality check failures: {len(recent_checks)}",
                "timestamp": datetime.now().isoformat()
            }
            self.quality_alerts.append(alert)
            
            if self.monitoring_system:
                await self.monitoring_system.send_alert(alert)
    
    async def _send_performance_metrics(self, workflow_id: str, result: QualityCheckResult):
        """发送性能指标到监控系统."""
        if not self.monitoring_system:
            return
        
        metrics = {
            "workflow_id": workflow_id,
            "quality_score": result.overall_score,
            "quality_level": result.quality_level.value,
            "check_type": result.check_type.value,
            "passed": result.passed,
            "timestamp": result.timestamp.isoformat()
        }
        
        # 添加具体指标
        for metric in result.metrics:
            metrics[f"metric_{metric.metric_name}"] = metric.value
        
        await self.monitoring_system.record_metrics("patent_quality", metrics)
    
    # 管理方法
    def get_quality_statistics(self) -> Dict[str, Any]:
        """获取质量统计信息."""
        total_checks = sum(len(history) for history in self.quality_history.values())
        
        if total_checks == 0:
            return {"status": "no_data"}
        
        all_checks = []
        for history in self.quality_history.values():
            all_checks.extend(history)
        
        passed_checks = len([check for check in all_checks if check.passed])
        
        return {
            "total_workflows": len(self.quality_history),
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "pass_rate": passed_checks / total_checks,
            "average_quality_score": sum(check.overall_score for check in all_checks) / total_checks,
            "active_alerts": len(self.quality_alerts),
            "monitoring_active": self.monitoring_active
        }
    
    async def cleanup_old_data(self, days: int = 7):
        """清理旧的质量数据."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        cleaned_count = 0
        for workflow_id, history in list(self.quality_history.items()):
            # 保留最近的检查结果
            recent_checks = [
                check for check in history
                if check.timestamp > cutoff_date
            ]
            
            if recent_checks:
                self.quality_history[workflow_id] = recent_checks
            else:
                del self.quality_history[workflow_id]
            
            cleaned_count += len(history) - len(recent_checks)
        
        # 清理旧告警
        recent_alerts = [
            alert for alert in self.quality_alerts
            if datetime.fromisoformat(alert["timestamp"]) > cutoff_date
        ]
        
        cleaned_count += len(self.quality_alerts) - len(recent_alerts)
        self.quality_alerts = recent_alerts
        
        logger.info(f"Cleaned up {cleaned_count} old quality records")
        return cleaned_count