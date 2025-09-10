"""性能监控和指标收集系统."""

import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from collections import defaultdict, deque
from dataclasses import dataclass, field
from contextlib import contextmanager

from pydantic import BaseModel, Field, field_serializer

from .logging import get_logger, LogCategory


logger = get_logger("multi_agent_service.monitoring")


@dataclass
class MetricPoint:
    """指标数据点."""
    timestamp: datetime
    value: Union[int, float]
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class MetricSummary:
    """指标摘要统计."""
    count: int = 0
    sum: float = 0.0
    min: float = float('inf')
    max: float = float('-inf')
    avg: float = 0.0
    
    def add_value(self, value: float):
        """添加新的值."""
        self.count += 1
        self.sum += value
        self.min = min(self.min, value)
        self.max = max(self.max, value)
        self.avg = self.sum / self.count


class PerformanceMetrics(BaseModel):
    """性能指标模型."""
    
    # API性能指标
    api_request_count: int = Field(default=0, description="API请求总数")
    api_request_duration_avg: float = Field(default=0.0, description="API请求平均响应时间(秒)")
    api_request_duration_p95: float = Field(default=0.0, description="API请求95%响应时间(秒)")
    api_error_rate: float = Field(default=0.0, description="API错误率")
    
    # 智能体性能指标
    agent_execution_count: int = Field(default=0, description="智能体执行总数")
    agent_execution_duration_avg: float = Field(default=0.0, description="智能体平均执行时间(秒)")
    agent_success_rate: float = Field(default=0.0, description="智能体执行成功率")
    active_agents: int = Field(default=0, description="活跃智能体数量")
    
    # 工作流性能指标
    workflow_execution_count: int = Field(default=0, description="工作流执行总数")
    workflow_execution_duration_avg: float = Field(default=0.0, description="工作流平均执行时间(秒)")
    workflow_success_rate: float = Field(default=0.0, description="工作流执行成功率")
    
    # 模型服务指标
    model_api_call_count: int = Field(default=0, description="模型API调用总数")
    model_api_duration_avg: float = Field(default=0.0, description="模型API平均响应时间(秒)")
    model_api_success_rate: float = Field(default=0.0, description="模型API成功率")
    model_token_usage: int = Field(default=0, description="模型Token使用总量")
    model_cost_total: float = Field(default=0.0, description="模型使用总成本")
    
    # 专利分析指标
    patent_analysis_count: int = Field(default=0, description="专利分析任务总数")
    patent_analysis_duration_avg: float = Field(default=0.0, description="专利分析平均执行时间(秒)")
    patent_analysis_success_rate: float = Field(default=0.0, description="专利分析成功率")
    patent_data_collection_count: int = Field(default=0, description="专利数据收集次数")
    patent_search_count: int = Field(default=0, description="专利搜索次数")
    patent_report_generation_count: int = Field(default=0, description="专利报告生成次数")
    patent_cache_hit_rate: float = Field(default=0.0, description="专利缓存命中率")
    patent_data_quality_avg: float = Field(default=0.0, description="专利数据质量平均分")
    active_patent_agents: int = Field(default=0, description="活跃专利Agent数量")
    patent_api_call_count: int = Field(default=0, description="专利API调用总数")
    patent_api_success_rate: float = Field(default=0.0, description="专利API成功率")
    
    # 系统资源指标
    cpu_usage_percent: float = Field(default=0.0, description="CPU使用率")
    memory_usage_percent: float = Field(default=0.0, description="内存使用率")
    memory_usage_mb: float = Field(default=0.0, description="内存使用量(MB)")
    disk_usage_percent: float = Field(default=0.0, description="磁盘使用率")
    
    # 时间戳
    timestamp: datetime = Field(default_factory=datetime.now, description="指标收集时间")
    
    @field_serializer('timestamp')
    def serialize_timestamp(self, value: datetime) -> str:
        return value.isoformat()


class MetricsCollector:
    """指标收集器."""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self._metrics_history: deque = deque(maxlen=max_history)
        self._raw_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self._summaries: Dict[str, MetricSummary] = defaultdict(MetricSummary)
        self._lock = threading.Lock()
        
        # 启动系统资源监控
        self._start_system_monitoring()
    
    def _start_system_monitoring(self):
        """启动系统资源监控线程."""
        def monitor_system_resources():
            while True:
                try:
                    # 收集系统资源指标
                    cpu_percent = psutil.cpu_percent(interval=1)
                    memory = psutil.virtual_memory()
                    disk = psutil.disk_usage('/')
                    
                    self.record_metric("system.cpu_usage", cpu_percent, tags={"unit": "percent"})
                    self.record_metric("system.memory_usage_percent", memory.percent, tags={"unit": "percent"})
                    self.record_metric("system.memory_usage_mb", memory.used / 1024 / 1024, tags={"unit": "mb"})
                    self.record_metric("system.disk_usage_percent", disk.percent, tags={"unit": "percent"})
                    
                    time.sleep(30)  # 每30秒收集一次系统指标
                except Exception as e:
                    logger.error(f"System monitoring error: {e}", category=LogCategory.SYSTEM)
                    time.sleep(60)  # 出错时等待更长时间
        
        monitor_thread = threading.Thread(target=monitor_system_resources, daemon=True)
        monitor_thread.start()
    
    def record_metric(
        self,
        metric_name: str,
        value: Union[int, float],
        tags: Optional[Dict[str, str]] = None
    ):
        """记录指标数据点."""
        with self._lock:
            point = MetricPoint(
                timestamp=datetime.now(),
                value=float(value),
                tags=tags or {}
            )
            
            self._raw_metrics[metric_name].append(point)
            self._summaries[metric_name].add_value(float(value))
            
            # 记录到日志
            logger.log_performance_metric(
                metric_name=metric_name,
                metric_value=value,
                metric_unit=tags.get("unit", "count") if tags else "count",
                component="metrics_collector",
                tags=tags
            )
    
    def get_metric_summary(self, metric_name: str) -> Optional[MetricSummary]:
        """获取指标摘要统计."""
        with self._lock:
            return self._summaries.get(metric_name)
    
    def get_metric_history(
        self,
        metric_name: str,
        since: Optional[datetime] = None
    ) -> List[MetricPoint]:
        """获取指标历史数据."""
        with self._lock:
            points = list(self._raw_metrics.get(metric_name, []))
            
            if since:
                points = [p for p in points if p.timestamp >= since]
            
            return points
    
    def get_current_metrics(self) -> PerformanceMetrics:
        """获取当前性能指标快照."""
        with self._lock:
            metrics = PerformanceMetrics()
            
            # API指标
            api_duration_summary = self._summaries.get("api.request_duration")
            if api_duration_summary and api_duration_summary.count > 0:
                metrics.api_request_count = api_duration_summary.count
                metrics.api_request_duration_avg = api_duration_summary.avg
                
                # 计算P95
                durations = [p.value for p in self._raw_metrics.get("api.request_duration", [])]
                if durations:
                    durations.sort()
                    p95_index = int(len(durations) * 0.95)
                    metrics.api_request_duration_p95 = durations[p95_index] if p95_index < len(durations) else durations[-1]
            
            # 错误率计算
            error_count = self._summaries.get("api.error_count", MetricSummary()).count
            total_requests = self._summaries.get("api.request_count", MetricSummary()).count
            if total_requests > 0:
                metrics.api_error_rate = error_count / total_requests
            
            # 智能体指标
            agent_duration_summary = self._summaries.get("agent.execution_duration")
            if agent_duration_summary and agent_duration_summary.count > 0:
                metrics.agent_execution_count = agent_duration_summary.count
                metrics.agent_execution_duration_avg = agent_duration_summary.avg
            
            agent_success_count = self._summaries.get("agent.success_count", MetricSummary()).count
            agent_total_count = self._summaries.get("agent.execution_count", MetricSummary()).count
            if agent_total_count > 0:
                metrics.agent_success_rate = agent_success_count / agent_total_count
            
            metrics.active_agents = self._summaries.get("agent.active_count", MetricSummary()).count
            
            # 工作流指标
            workflow_duration_summary = self._summaries.get("workflow.execution_duration")
            if workflow_duration_summary and workflow_duration_summary.count > 0:
                metrics.workflow_execution_count = workflow_duration_summary.count
                metrics.workflow_execution_duration_avg = workflow_duration_summary.avg
            
            workflow_success_count = self._summaries.get("workflow.success_count", MetricSummary()).count
            workflow_total_count = self._summaries.get("workflow.execution_count", MetricSummary()).count
            if workflow_total_count > 0:
                metrics.workflow_success_rate = workflow_success_count / workflow_total_count
            
            # 模型服务指标
            model_duration_summary = self._summaries.get("model.api_duration")
            if model_duration_summary and model_duration_summary.count > 0:
                metrics.model_api_call_count = model_duration_summary.count
                metrics.model_api_duration_avg = model_duration_summary.avg
            
            model_success_count = self._summaries.get("model.success_count", MetricSummary()).count
            model_total_count = self._summaries.get("model.api_call_count", MetricSummary()).count
            if model_total_count > 0:
                metrics.model_api_success_rate = model_success_count / model_total_count
            
            metrics.model_token_usage = int(self._summaries.get("model.token_usage", MetricSummary()).sum)
            metrics.model_cost_total = self._summaries.get("model.cost", MetricSummary()).sum
            
            # 系统资源指标
            cpu_summary = self._summaries.get("system.cpu_usage")
            if cpu_summary and cpu_summary.count > 0:
                metrics.cpu_usage_percent = cpu_summary.avg
            
            memory_percent_summary = self._summaries.get("system.memory_usage_percent")
            if memory_percent_summary and memory_percent_summary.count > 0:
                metrics.memory_usage_percent = memory_percent_summary.avg
            
            memory_mb_summary = self._summaries.get("system.memory_usage_mb")
            if memory_mb_summary and memory_mb_summary.count > 0:
                metrics.memory_usage_mb = memory_mb_summary.avg
            
            disk_summary = self._summaries.get("system.disk_usage_percent")
            if disk_summary and disk_summary.count > 0:
                metrics.disk_usage_percent = disk_summary.avg
            
            # 专利分析指标
            patent_analysis_duration_summary = self._summaries.get("patent.analysis_duration")
            if patent_analysis_duration_summary and patent_analysis_duration_summary.count > 0:
                metrics.patent_analysis_count = patent_analysis_duration_summary.count
                metrics.patent_analysis_duration_avg = patent_analysis_duration_summary.avg
            
            patent_analysis_success_count = self._summaries.get("patent.analysis_success_count", MetricSummary()).count
            patent_analysis_total_count = self._summaries.get("patent.analysis_count", MetricSummary()).count
            if patent_analysis_total_count > 0:
                metrics.patent_analysis_success_rate = patent_analysis_success_count / patent_analysis_total_count
            
            # 专利数据收集指标
            metrics.patent_data_collection_count = self._summaries.get("patent.data_collection_count", MetricSummary()).count
            
            # 专利搜索指标
            metrics.patent_search_count = self._summaries.get("patent.search_count", MetricSummary()).count
            
            # 专利报告生成指标
            metrics.patent_report_generation_count = self._summaries.get("patent.report_generation_count", MetricSummary()).count
            
            # 专利缓存命中率
            cache_hits = self._summaries.get("patent.cache_hit", MetricSummary()).count
            cache_misses = self._summaries.get("patent.cache_miss", MetricSummary()).count
            total_cache_requests = cache_hits + cache_misses
            if total_cache_requests > 0:
                metrics.patent_cache_hit_rate = cache_hits / total_cache_requests
            
            # 专利数据质量平均分
            quality_summary = self._summaries.get("patent.data_quality_score")
            if quality_summary and quality_summary.count > 0:
                metrics.patent_data_quality_avg = quality_summary.avg
            
            # 专利API调用指标
            patent_api_call_count = self._summaries.get("patent.api_call_count", MetricSummary()).count
            patent_api_success_count = self._summaries.get("patent.api_call_success_count", MetricSummary()).count
            metrics.patent_api_call_count = patent_api_call_count
            if patent_api_call_count > 0:
                metrics.patent_api_success_rate = patent_api_success_count / patent_api_call_count
            
            return metrics
    
    def reset_metrics(self):
        """重置所有指标."""
        with self._lock:
            self._raw_metrics.clear()
            self._summaries.clear()
            logger.info("Metrics reset", category=LogCategory.SYSTEM)


# 全局指标收集器实例
metrics_collector = MetricsCollector()


class PerformanceTimer:
    """性能计时器上下文管理器."""
    
    def __init__(
        self,
        metric_name: str,
        tags: Optional[Dict[str, str]] = None,
        log_result: bool = True
    ):
        self.metric_name = metric_name
        self.tags = tags or {}
        self.log_result = log_result
        self.start_time = None
        self.end_time = None
        self.duration = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        
        # 记录指标
        metrics_collector.record_metric(
            self.metric_name,
            self.duration,
            tags={**self.tags, "unit": "seconds"}
        )
        
        # 记录到日志
        if self.log_result:
            status = "error" if exc_type else "success"
            logger.info(
                f"Performance timer: {self.metric_name} completed in {self.duration:.3f}s",
                category=LogCategory.PERFORMANCE,
                metric_name=self.metric_name,
                duration=self.duration,
                status=status,
                tags=self.tags
            )


@contextmanager
def measure_performance(metric_name: str, tags: Optional[Dict[str, str]] = None):
    """性能测量上下文管理器."""
    with PerformanceTimer(metric_name, tags) as timer:
        yield timer


def track_api_request(
    method: str,
    endpoint: str,
    status_code: int,
    duration: float,
    user_id: Optional[str] = None
):
    """跟踪API请求指标."""
    tags = {
        "method": method,
        "endpoint": endpoint,
        "status_code": str(status_code),
        "unit": "seconds"
    }
    
    if user_id:
        tags["user_id"] = user_id
    
    # 记录请求持续时间
    metrics_collector.record_metric("api.request_duration", duration, tags)
    
    # 记录请求计数
    metrics_collector.record_metric("api.request_count", 1, tags)
    
    # 记录错误计数
    if status_code >= 400:
        metrics_collector.record_metric("api.error_count", 1, tags)


def track_agent_execution(
    agent_id: str,
    agent_type: str,
    action: str,
    duration: float,
    success: bool
):
    """跟踪智能体执行指标."""
    tags = {
        "agent_id": agent_id,
        "agent_type": agent_type,
        "action": action,
        "unit": "seconds"
    }
    
    # 记录执行持续时间
    metrics_collector.record_metric("agent.execution_duration", duration, tags)
    
    # 记录执行计数
    metrics_collector.record_metric("agent.execution_count", 1, tags)
    
    # 记录成功计数
    if success:
        metrics_collector.record_metric("agent.success_count", 1, tags)


def track_workflow_execution(
    workflow_id: str,
    workflow_type: str,
    duration: float,
    success: bool,
    participating_agents: Optional[List[str]] = None
):
    """跟踪工作流执行指标."""
    tags = {
        "workflow_id": workflow_id,
        "workflow_type": workflow_type,
        "unit": "seconds"
    }
    
    if participating_agents:
        tags["agent_count"] = str(len(participating_agents))
    
    # 记录执行持续时间
    metrics_collector.record_metric("workflow.execution_duration", duration, tags)
    
    # 记录执行计数
    metrics_collector.record_metric("workflow.execution_count", 1, tags)
    
    # 记录成功计数
    if success:
        metrics_collector.record_metric("workflow.success_count", 1, tags)


def track_model_api_call(
    provider: str,
    model: str,
    duration: float,
    success: bool,
    token_count: Optional[int] = None,
    cost: Optional[float] = None
):
    """跟踪模型API调用指标."""
    tags = {
        "provider": provider,
        "model": model,
        "unit": "seconds"
    }
    
    # 记录API调用持续时间
    metrics_collector.record_metric("model.api_duration", duration, tags)
    
    # 记录API调用计数
    metrics_collector.record_metric("model.api_call_count", 1, tags)
    
    # 记录成功计数
    if success:
        metrics_collector.record_metric("model.success_count", 1, tags)
    
    # 记录Token使用量
    if token_count:
        metrics_collector.record_metric("model.token_usage", token_count, {**tags, "unit": "tokens"})
    
    # 记录成本
    if cost:
        metrics_collector.record_metric("model.cost", cost, {**tags, "unit": "usd"})


def track_patent_analysis(
    agent_id: str,
    agent_type: str,
    analysis_type: str,
    duration: float,
    success: bool,
    data_quality_score: Optional[float] = None,
    patents_processed: Optional[int] = None
):
    """跟踪专利分析指标."""
    tags = {
        "agent_id": agent_id,
        "agent_type": agent_type,
        "analysis_type": analysis_type,
        "unit": "seconds"
    }
    
    # 记录分析持续时间
    metrics_collector.record_metric("patent.analysis_duration", duration, tags)
    
    # 记录分析计数
    metrics_collector.record_metric("patent.analysis_count", 1, tags)
    
    # 记录成功计数
    if success:
        metrics_collector.record_metric("patent.analysis_success_count", 1, tags)
    
    # 记录数据质量评分
    if data_quality_score is not None:
        metrics_collector.record_metric("patent.data_quality_score", data_quality_score, {**tags, "unit": "score"})
    
    # 记录处理的专利数量
    if patents_processed is not None:
        metrics_collector.record_metric("patent.patents_processed", patents_processed, {**tags, "unit": "count"})


def track_patent_data_collection(
    agent_id: str,
    data_source: str,
    duration: float,
    success: bool,
    patents_collected: Optional[int] = None,
    cache_hit: bool = False
):
    """跟踪专利数据收集指标."""
    tags = {
        "agent_id": agent_id,
        "data_source": data_source,
        "unit": "seconds"
    }
    
    # 记录收集持续时间
    metrics_collector.record_metric("patent.data_collection_duration", duration, tags)
    
    # 记录收集计数
    metrics_collector.record_metric("patent.data_collection_count", 1, tags)
    
    # 记录成功计数
    if success:
        metrics_collector.record_metric("patent.data_collection_success_count", 1, tags)
    
    # 记录收集的专利数量
    if patents_collected is not None:
        metrics_collector.record_metric("patent.patents_collected", patents_collected, {**tags, "unit": "count"})
    
    # 记录缓存命中
    if cache_hit:
        metrics_collector.record_metric("patent.cache_hit", 1, {**tags, "unit": "count"})
    else:
        metrics_collector.record_metric("patent.cache_miss", 1, {**tags, "unit": "count"})


def track_patent_search(
    agent_id: str,
    search_engine: str,
    duration: float,
    success: bool,
    results_count: Optional[int] = None,
    search_type: str = "general"
):
    """跟踪专利搜索指标."""
    tags = {
        "agent_id": agent_id,
        "search_engine": search_engine,
        "search_type": search_type,
        "unit": "seconds"
    }
    
    # 记录搜索持续时间
    metrics_collector.record_metric("patent.search_duration", duration, tags)
    
    # 记录搜索计数
    metrics_collector.record_metric("patent.search_count", 1, tags)
    
    # 记录成功计数
    if success:
        metrics_collector.record_metric("patent.search_success_count", 1, tags)
    
    # 记录搜索结果数量
    if results_count is not None:
        metrics_collector.record_metric("patent.search_results", results_count, {**tags, "unit": "count"})


def track_patent_report_generation(
    agent_id: str,
    report_type: str,
    duration: float,
    success: bool,
    report_size_kb: Optional[float] = None,
    charts_generated: Optional[int] = None
):
    """跟踪专利报告生成指标."""
    tags = {
        "agent_id": agent_id,
        "report_type": report_type,
        "unit": "seconds"
    }
    
    # 记录报告生成持续时间
    metrics_collector.record_metric("patent.report_generation_duration", duration, tags)
    
    # 记录报告生成计数
    metrics_collector.record_metric("patent.report_generation_count", 1, tags)
    
    # 记录成功计数
    if success:
        metrics_collector.record_metric("patent.report_generation_success_count", 1, tags)
    
    # 记录报告大小
    if report_size_kb is not None:
        metrics_collector.record_metric("patent.report_size", report_size_kb, {**tags, "unit": "kb"})
    
    # 记录生成的图表数量
    if charts_generated is not None:
        metrics_collector.record_metric("patent.charts_generated", charts_generated, {**tags, "unit": "count"})


def track_patent_api_call(
    api_name: str,
    endpoint: str,
    duration: float,
    success: bool,
    response_size_kb: Optional[float] = None,
    rate_limited: bool = False
):
    """跟踪专利API调用指标."""
    tags = {
        "api_name": api_name,
        "endpoint": endpoint,
        "unit": "seconds"
    }
    
    # 记录API调用持续时间
    metrics_collector.record_metric("patent.api_call_duration", duration, tags)
    
    # 记录API调用计数
    metrics_collector.record_metric("patent.api_call_count", 1, tags)
    
    # 记录成功计数
    if success:
        metrics_collector.record_metric("patent.api_call_success_count", 1, tags)
    
    # 记录响应大小
    if response_size_kb is not None:
        metrics_collector.record_metric("patent.api_response_size", response_size_kb, {**tags, "unit": "kb"})
    
    # 记录限流情况
    if rate_limited:
        metrics_collector.record_metric("patent.api_rate_limited", 1, {**tags, "unit": "count"})


def get_performance_report() -> Dict[str, Any]:
    """获取性能报告."""
    current_metrics = metrics_collector.get_current_metrics()
    
    return {
        "timestamp": datetime.now().isoformat(),
        "metrics": current_metrics.model_dump(),
        "summary": {
            "total_api_requests": current_metrics.api_request_count,
            "avg_api_response_time": f"{current_metrics.api_request_duration_avg:.3f}s",
            "api_error_rate": f"{current_metrics.api_error_rate:.2%}",
            "total_agent_executions": current_metrics.agent_execution_count,
            "agent_success_rate": f"{current_metrics.agent_success_rate:.2%}",
            "total_workflow_executions": current_metrics.workflow_execution_count,
            "workflow_success_rate": f"{current_metrics.workflow_success_rate:.2%}",
            "total_model_api_calls": current_metrics.model_api_call_count,
            "model_api_success_rate": f"{current_metrics.model_api_success_rate:.2%}",
            "total_token_usage": current_metrics.model_token_usage,
            "total_model_cost": f"${current_metrics.model_cost_total:.4f}",
            "cpu_usage": f"{current_metrics.cpu_usage_percent:.1f}%",
            "memory_usage": f"{current_metrics.memory_usage_percent:.1f}%",
            # 专利分析指标摘要
            "patent_analysis_count": current_metrics.patent_analysis_count,
            "patent_analysis_success_rate": f"{current_metrics.patent_analysis_success_rate:.2%}",
            "patent_data_collection_count": current_metrics.patent_data_collection_count,
            "patent_search_count": current_metrics.patent_search_count,
            "patent_report_generation_count": current_metrics.patent_report_generation_count,
            "patent_cache_hit_rate": f"{current_metrics.patent_cache_hit_rate:.2%}",
            "patent_data_quality_avg": f"{current_metrics.patent_data_quality_avg:.2f}",
            "patent_api_call_count": current_metrics.patent_api_call_count,
            "patent_api_success_rate": f"{current_metrics.patent_api_success_rate:.2%}"
        }
    }


class MonitoringSystem:
    """监控系统，整合所有监控功能."""
    
    def __init__(self):
        self.metrics_collector = metrics_collector
        self.is_monitoring = False
        self.logger = get_logger("multi_agent_service.monitoring_system")
        
        # 专利Agent监控注册表
        self._patent_agents: Dict[str, Dict[str, Any]] = {}
        self._patent_alert_thresholds = {
            'analysis_failure_rate': 0.1,  # 10%失败率阈值
            'data_quality_threshold': 0.7,  # 数据质量阈值
            'api_response_time_threshold': 30.0,  # API响应时间阈值(秒)
            'cache_hit_rate_threshold': 0.5,  # 缓存命中率阈值
        }
    
    async def initialize(self):
        """初始化监控系统."""
        self.logger.info("Initializing monitoring system", category=LogCategory.SYSTEM)
        return True
    
    async def start_monitoring(self):
        """启动监控."""
        self.is_monitoring = True
        self.logger.info("Monitoring system started", category=LogCategory.SYSTEM)
    
    async def stop_monitoring(self):
        """停止监控."""
        self.is_monitoring = False
        self.logger.info("Monitoring system stopped", category=LogCategory.SYSTEM)
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统指标."""
        return get_performance_report()
    
    async def health_check(self) -> bool:
        """健康检查."""
        return self.is_monitoring
    
    async def shutdown(self):
        """关闭监控系统."""
        await self.stop_monitoring()
        self.logger.info("Monitoring system shutdown", category=LogCategory.SYSTEM)
    
    # 专利监控专用方法
    def register_patent_agent(self, agent_id: str, agent_type: str, agent_config: Dict[str, Any]):
        """注册专利Agent到监控系统."""
        self._patent_agents[agent_id] = {
            'agent_type': agent_type,
            'config': agent_config,
            'registered_at': datetime.now(),
            'last_health_check': None,
            'status': 'registered'
        }
        
        self.logger.info(
            f"Patent agent registered for monitoring: {agent_id} ({agent_type})",
            category=LogCategory.SYSTEM,
            agent_id=agent_id,
            agent_type=agent_type
        )
    
    def unregister_patent_agent(self, agent_id: str):
        """从监控系统注销专利Agent."""
        if agent_id in self._patent_agents:
            del self._patent_agents[agent_id]
            self.logger.info(
                f"Patent agent unregistered from monitoring: {agent_id}",
                category=LogCategory.SYSTEM,
                agent_id=agent_id
            )
    
    async def get_patent_metrics(self) -> Dict[str, Any]:
        """获取专利分析专用指标."""
        current_metrics = self.metrics_collector.get_current_metrics()
        
        patent_metrics = {
            'timestamp': datetime.now().isoformat(),
            'registered_patent_agents': len(self._patent_agents),
            'active_patent_agents': current_metrics.active_patent_agents,
            'patent_analysis': {
                'total_count': current_metrics.patent_analysis_count,
                'success_rate': current_metrics.patent_analysis_success_rate,
                'avg_duration': current_metrics.patent_analysis_duration_avg,
            },
            'patent_data_collection': {
                'total_count': current_metrics.patent_data_collection_count,
                'cache_hit_rate': current_metrics.patent_cache_hit_rate,
                'data_quality_avg': current_metrics.patent_data_quality_avg,
            },
            'patent_search': {
                'total_count': current_metrics.patent_search_count,
            },
            'patent_reports': {
                'total_count': current_metrics.patent_report_generation_count,
            },
            'patent_api_calls': {
                'total_count': current_metrics.patent_api_call_count,
                'success_rate': current_metrics.patent_api_success_rate,
            },
            'agent_status': {
                agent_id: info['status'] 
                for agent_id, info in self._patent_agents.items()
            }
        }
        
        return patent_metrics
    
    async def check_patent_alerts(self) -> List[Dict[str, Any]]:
        """检查专利分析相关告警."""
        alerts = []
        current_metrics = self.metrics_collector.get_current_metrics()
        
        # 检查分析失败率
        if (current_metrics.patent_analysis_count > 0 and 
            (1 - current_metrics.patent_analysis_success_rate) > self._patent_alert_thresholds['analysis_failure_rate']):
            alerts.append({
                'type': 'patent_analysis_failure_rate',
                'severity': 'warning',
                'message': f"专利分析失败率过高: {(1 - current_metrics.patent_analysis_success_rate):.2%}",
                'current_value': 1 - current_metrics.patent_analysis_success_rate,
                'threshold': self._patent_alert_thresholds['analysis_failure_rate'],
                'timestamp': datetime.now().isoformat()
            })
        
        # 检查数据质量
        if (current_metrics.patent_data_quality_avg > 0 and 
            current_metrics.patent_data_quality_avg < self._patent_alert_thresholds['data_quality_threshold']):
            alerts.append({
                'type': 'patent_data_quality_low',
                'severity': 'warning',
                'message': f"专利数据质量偏低: {current_metrics.patent_data_quality_avg:.2f}",
                'current_value': current_metrics.patent_data_quality_avg,
                'threshold': self._patent_alert_thresholds['data_quality_threshold'],
                'timestamp': datetime.now().isoformat()
            })
        
        # 检查API响应时间
        if (current_metrics.patent_analysis_duration_avg > 0 and 
            current_metrics.patent_analysis_duration_avg > self._patent_alert_thresholds['api_response_time_threshold']):
            alerts.append({
                'type': 'patent_api_slow_response',
                'severity': 'warning',
                'message': f"专利分析响应时间过长: {current_metrics.patent_analysis_duration_avg:.2f}s",
                'current_value': current_metrics.patent_analysis_duration_avg,
                'threshold': self._patent_alert_thresholds['api_response_time_threshold'],
                'timestamp': datetime.now().isoformat()
            })
        
        # 检查缓存命中率
        if (current_metrics.patent_cache_hit_rate > 0 and 
            current_metrics.patent_cache_hit_rate < self._patent_alert_thresholds['cache_hit_rate_threshold']):
            alerts.append({
                'type': 'patent_cache_hit_rate_low',
                'severity': 'info',
                'message': f"专利缓存命中率偏低: {current_metrics.patent_cache_hit_rate:.2%}",
                'current_value': current_metrics.patent_cache_hit_rate,
                'threshold': self._patent_alert_thresholds['cache_hit_rate_threshold'],
                'timestamp': datetime.now().isoformat()
            })
        
        # 记录告警到日志
        for alert in alerts:
            self.logger.warning(
                f"Patent monitoring alert: {alert['message']}",
                category=LogCategory.SYSTEM,
                alert_type=alert['type'],
                severity=alert['severity']
            )
        
        return alerts
    
    def update_patent_alert_thresholds(self, thresholds: Dict[str, float]):
        """更新专利告警阈值."""
        self._patent_alert_thresholds.update(thresholds)
        self.logger.info(
            "Patent alert thresholds updated",
            category=LogCategory.SYSTEM,
            thresholds=thresholds
        )
    
    async def get_patent_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """获取特定专利Agent的状态."""
        if agent_id not in self._patent_agents:
            return None
        
        agent_info = self._patent_agents[agent_id].copy()
        
        # 获取该Agent的指标
        agent_metrics = {}
        for metric_name, metric_summary in self.metrics_collector._summaries.items():
            if metric_name.startswith('patent.') and agent_id in str(metric_summary):
                agent_metrics[metric_name] = {
                    'count': metric_summary.count,
                    'avg': metric_summary.avg,
                    'min': metric_summary.min,
                    'max': metric_summary.max
                }
        
        agent_info['metrics'] = agent_metrics
        return agent_info
    
    async def reset_patent_metrics(self):
        """重置专利相关指标."""
        # 重置专利相关的指标
        patent_metric_keys = [key for key in self.metrics_collector._summaries.keys() if key.startswith('patent.')]
        for key in patent_metric_keys:
            if key in self.metrics_collector._summaries:
                del self.metrics_collector._summaries[key]
            if key in self.metrics_collector._raw_metrics:
                self.metrics_collector._raw_metrics[key].clear()
        
        self.logger.info("Patent metrics reset", category=LogCategory.SYSTEM)