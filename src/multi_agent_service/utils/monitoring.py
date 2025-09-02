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
            "memory_usage": f"{current_metrics.memory_usage_percent:.1f}%"
        }
    }


class MonitoringSystem:
    """监控系统，整合所有监控功能."""
    
    def __init__(self):
        self.metrics_collector = metrics_collector
        self.is_monitoring = False
        self.logger = get_logger("multi_agent_service.monitoring_system")
    
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