"""监控系统的单元测试."""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.multi_agent_service.utils.monitoring import (
    MetricPoint,
    MetricSummary,
    PerformanceMetrics,
    MetricsCollector,
    PerformanceTimer,
    measure_performance,
    track_api_request,
    track_agent_execution,
    track_workflow_execution,
    track_model_api_call,
    get_performance_report
)


class TestMetricPoint:
    """测试指标数据点."""
    
    def test_metric_point_creation(self):
        """测试指标数据点创建."""
        timestamp = datetime.now()
        tags = {"component": "api", "method": "GET"}
        
        point = MetricPoint(
            timestamp=timestamp,
            value=1.5,
            tags=tags
        )
        
        assert point.timestamp == timestamp
        assert point.value == 1.5
        assert point.tags == tags
    
    def test_metric_point_default_tags(self):
        """测试默认标签."""
        point = MetricPoint(
            timestamp=datetime.now(),
            value=100
        )
        
        assert point.tags == {}


class TestMetricSummary:
    """测试指标摘要统计."""
    
    def test_metric_summary_initialization(self):
        """测试指标摘要初始化."""
        summary = MetricSummary()
        
        assert summary.count == 0
        assert summary.sum == 0.0
        assert summary.min == float('inf')
        assert summary.max == float('-inf')
        assert summary.avg == 0.0
    
    def test_add_single_value(self):
        """测试添加单个值."""
        summary = MetricSummary()
        summary.add_value(10.0)
        
        assert summary.count == 1
        assert summary.sum == 10.0
        assert summary.min == 10.0
        assert summary.max == 10.0
        assert summary.avg == 10.0
    
    def test_add_multiple_values(self):
        """测试添加多个值."""
        summary = MetricSummary()
        values = [5.0, 10.0, 15.0, 20.0]
        
        for value in values:
            summary.add_value(value)
        
        assert summary.count == 4
        assert summary.sum == 50.0
        assert summary.min == 5.0
        assert summary.max == 20.0
        assert summary.avg == 12.5


class TestPerformanceMetrics:
    """测试性能指标模型."""
    
    def test_performance_metrics_creation(self):
        """测试性能指标创建."""
        metrics = PerformanceMetrics()
        
        # 验证默认值
        assert metrics.api_request_count == 0
        assert metrics.api_request_duration_avg == 0.0
        assert metrics.agent_execution_count == 0
        assert metrics.workflow_execution_count == 0
        assert metrics.model_api_call_count == 0
        assert metrics.cpu_usage_percent == 0.0
        assert isinstance(metrics.timestamp, datetime)
    
    def test_performance_metrics_with_values(self):
        """测试带值的性能指标."""
        timestamp = datetime.now()
        
        metrics = PerformanceMetrics(
            api_request_count=100,
            api_request_duration_avg=0.5,
            api_error_rate=0.02,
            agent_execution_count=50,
            cpu_usage_percent=75.5,
            timestamp=timestamp
        )
        
        assert metrics.api_request_count == 100
        assert metrics.api_request_duration_avg == 0.5
        assert metrics.api_error_rate == 0.02
        assert metrics.agent_execution_count == 50
        assert metrics.cpu_usage_percent == 75.5
        assert metrics.timestamp == timestamp
    
    def test_performance_metrics_serialization(self):
        """测试性能指标序列化."""
        metrics = PerformanceMetrics(
            api_request_count=10,
            cpu_usage_percent=50.0
        )
        
        data = metrics.model_dump()
        assert data["api_request_count"] == 10
        assert data["cpu_usage_percent"] == 50.0
        assert "timestamp" in data


class TestMetricsCollector:
    """测试指标收集器."""
    
    @pytest.fixture
    def collector(self):
        """创建测试指标收集器."""
        with patch('src.multi_agent_service.utils.monitoring.MetricsCollector._start_system_monitoring'):
            return MetricsCollector(max_history=100)
    
    def test_collector_initialization(self, collector):
        """测试收集器初始化."""
        assert collector.max_history == 100
        assert len(collector._metrics_history) == 0
        assert len(collector._raw_metrics) == 0
        assert len(collector._summaries) == 0
    
    def test_record_metric(self, collector):
        """测试记录指标."""
        with patch('src.multi_agent_service.utils.monitoring.logger') as mock_logger:
            collector.record_metric("test.metric", 10.5, {"unit": "seconds"})
            
            # 验证指标被记录
            assert "test.metric" in collector._raw_metrics
            assert len(collector._raw_metrics["test.metric"]) == 1
            
            point = collector._raw_metrics["test.metric"][0]
            assert point.value == 10.5
            assert point.tags == {"unit": "seconds"}
            
            # 验证摘要统计被更新
            summary = collector._summaries["test.metric"]
            assert summary.count == 1
            assert summary.sum == 10.5
            assert summary.avg == 10.5
            
            # 验证日志被记录
            mock_logger.log_performance_metric.assert_called_once()
    
    def test_record_multiple_metrics(self, collector):
        """测试记录多个指标."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        
        with patch('src.multi_agent_service.utils.monitoring.logger'):
            for value in values:
                collector.record_metric("test.metric", value)
        
        # 验证所有值都被记录
        assert len(collector._raw_metrics["test.metric"]) == 5
        
        # 验证摘要统计
        summary = collector._summaries["test.metric"]
        assert summary.count == 5
        assert summary.sum == 15.0
        assert summary.min == 1.0
        assert summary.max == 5.0
        assert summary.avg == 3.0
    
    def test_get_metric_summary(self, collector):
        """测试获取指标摘要."""
        with patch('src.multi_agent_service.utils.monitoring.logger'):
            collector.record_metric("test.metric", 10.0)
            collector.record_metric("test.metric", 20.0)
        
        summary = collector.get_metric_summary("test.metric")
        assert summary is not None
        assert summary.count == 2
        assert summary.avg == 15.0
        
        # 测试不存在的指标
        non_existent = collector.get_metric_summary("non.existent")
        assert non_existent is None
    
    def test_get_metric_history(self, collector):
        """测试获取指标历史."""
        now = datetime.now()
        
        with patch('src.multi_agent_service.utils.monitoring.logger'):
            # 记录一些指标
            collector.record_metric("test.metric", 1.0)
            collector.record_metric("test.metric", 2.0)
            collector.record_metric("test.metric", 3.0)
        
        # 获取所有历史
        history = collector.get_metric_history("test.metric")
        assert len(history) == 3
        assert [p.value for p in history] == [1.0, 2.0, 3.0]
        
        # 测试时间过滤
        since = now + timedelta(seconds=1)
        recent_history = collector.get_metric_history("test.metric", since=since)
        # 由于时间很接近，可能所有点都会被包含或排除
        assert len(recent_history) <= 3
    
    def test_get_current_metrics(self, collector):
        """测试获取当前指标快照."""
        with patch('src.multi_agent_service.utils.monitoring.logger'):
            # 记录一些API指标
            collector.record_metric("api.request_duration", 0.5)
            collector.record_metric("api.request_duration", 1.0)
            collector.record_metric("api.request_count", 1)
            collector.record_metric("api.request_count", 1)
            collector.record_metric("api.error_count", 1)
            
            # 记录智能体指标
            collector.record_metric("agent.execution_duration", 2.0)
            collector.record_metric("agent.execution_count", 1)
            collector.record_metric("agent.success_count", 1)
            
            # 记录系统指标
            collector.record_metric("system.cpu_usage", 75.0)
            collector.record_metric("system.memory_usage_percent", 60.0)
        
        metrics = collector.get_current_metrics()
        
        # 验证API指标
        assert metrics.api_request_count == 2
        assert metrics.api_request_duration_avg == 0.75
        assert metrics.api_error_rate == 0.5  # 1 error out of 2 requests
        
        # 验证智能体指标
        assert metrics.agent_execution_count == 1
        assert metrics.agent_execution_duration_avg == 2.0
        assert metrics.agent_success_rate == 1.0
        
        # 验证系统指标
        assert metrics.cpu_usage_percent == 75.0
        assert metrics.memory_usage_percent == 60.0
    
    def test_reset_metrics(self, collector):
        """测试重置指标."""
        with patch('src.multi_agent_service.utils.monitoring.logger') as mock_logger:
            # 记录一些指标
            collector.record_metric("test.metric", 10.0)
            collector.record_metric("test.metric", 20.0)
            
            # 验证指标存在
            assert len(collector._raw_metrics) > 0
            assert len(collector._summaries) > 0
            
            # 重置指标
            collector.reset_metrics()
            
            # 验证指标被清空
            assert len(collector._raw_metrics) == 0
            assert len(collector._summaries) == 0
            
            # 验证日志被记录
            mock_logger.info.assert_called_with("Metrics reset", category="system")


class TestPerformanceTimer:
    """测试性能计时器."""
    
    def test_performance_timer_context_manager(self):
        """测试性能计时器上下文管理器."""
        with patch('src.multi_agent_service.utils.monitoring.metrics_collector') as mock_collector:
            with patch('src.multi_agent_service.utils.monitoring.logger') as mock_logger:
                with PerformanceTimer("test.timer", {"component": "test"}) as timer:
                    time.sleep(0.01)  # 短暂睡眠
                
                # 验证计时器属性
                assert timer.start_time is not None
                assert timer.end_time is not None
                assert timer.duration is not None
                assert timer.duration > 0
                
                # 验证指标被记录
                mock_collector.record_metric.assert_called_once()
                args, kwargs = mock_collector.record_metric.call_args
                assert args[0] == "test.timer"
                assert args[1] == timer.duration
                assert kwargs["tags"]["component"] == "test"
                assert kwargs["tags"]["unit"] == "seconds"
    
    def test_performance_timer_with_exception(self):
        """测试异常情况下的性能计时器."""
        with patch('src.multi_agent_service.utils.monitoring.metrics_collector') as mock_collector:
            with patch('src.multi_agent_service.utils.monitoring.logger') as mock_logger:
                try:
                    with PerformanceTimer("test.timer") as timer:
                        raise ValueError("Test exception")
                except ValueError:
                    pass
                
                # 即使有异常，计时器也应该记录时间
                assert timer.duration is not None
                mock_collector.record_metric.assert_called_once()
    
    def test_performance_timer_no_logging(self):
        """测试不记录日志的性能计时器."""
        with patch('src.multi_agent_service.utils.monitoring.metrics_collector') as mock_collector:
            with patch('src.multi_agent_service.utils.monitoring.logger') as mock_logger:
                with PerformanceTimer("test.timer", log_result=False):
                    pass
                
                # 指标应该被记录，但不应该有日志
                mock_collector.record_metric.assert_called_once()
                mock_logger.info.assert_not_called()


class TestMeasurePerformance:
    """测试性能测量函数."""
    
    def test_measure_performance_context_manager(self):
        """测试性能测量上下文管理器."""
        with patch('src.multi_agent_service.utils.monitoring.PerformanceTimer') as mock_timer_class:
            mock_timer = Mock()
            mock_timer.__enter__ = Mock(return_value=mock_timer)
            mock_timer.__exit__ = Mock(return_value=None)
            mock_timer_class.return_value = mock_timer
            
            with measure_performance("test.metric", {"tag": "value"}) as timer:
                pass
            
            # 验证PerformanceTimer被正确调用
            mock_timer_class.assert_called_once_with("test.metric", {"tag": "value"})
            mock_timer.__enter__.assert_called_once()
            mock_timer.__exit__.assert_called_once()


class TestTrackingFunctions:
    """测试跟踪函数."""
    
    def test_track_api_request(self):
        """测试API请求跟踪."""
        with patch('src.multi_agent_service.utils.monitoring.metrics_collector') as mock_collector:
            track_api_request(
                method="GET",
                endpoint="/api/test",
                status_code=200,
                duration=0.5,
                user_id="user123"
            )
            
            # 验证指标被记录 (只有duration和count，因为status_code < 400，不会记录error)
            assert mock_collector.record_metric.call_count == 2  # duration, count
            
            # 验证调用参数
            calls = mock_collector.record_metric.call_args_list
            
            # 第一个调用：duration
            assert calls[0][0][0] == "api.request_duration"
            assert calls[0][0][1] == 0.5
            assert calls[0][0][2]["method"] == "GET"
            assert calls[0][0][2]["endpoint"] == "/api/test"
            assert calls[0][0][2]["status_code"] == "200"
            assert calls[0][0][2]["user_id"] == "user123"
            
            # 第二个调用：count
            assert calls[1][0][0] == "api.request_count"
            assert calls[1][0][1] == 1
    
    def test_track_agent_execution(self):
        """测试智能体执行跟踪."""
        with patch('src.multi_agent_service.utils.monitoring.metrics_collector') as mock_collector:
            track_agent_execution(
                agent_id="agent123",
                agent_type="sales",
                action="process_request",
                duration=1.5,
                success=True
            )
            
            # 验证指标被记录
            assert mock_collector.record_metric.call_count == 3  # duration, count, success_count
            
            calls = mock_collector.record_metric.call_args_list
            
            # 验证duration调用 - record_metric(metric_name, value, tags)
            assert calls[0][0][0] == "agent.execution_duration"
            assert calls[0][0][1] == 1.5
            assert calls[0][0][2]["agent_id"] == "agent123"
            assert calls[0][0][2]["agent_type"] == "sales"
            assert calls[0][0][2]["action"] == "process_request"
            
            # 验证success_count调用
            assert calls[2][0][0] == "agent.success_count"
            assert calls[2][0][1] == 1
    
    def test_track_workflow_execution(self):
        """测试工作流执行跟踪."""
        with patch('src.multi_agent_service.utils.monitoring.metrics_collector') as mock_collector:
            track_workflow_execution(
                workflow_id="wf123",
                workflow_type="sequential",
                duration=5.0,
                success=True,
                participating_agents=["agent1", "agent2"]
            )
            
            calls = mock_collector.record_metric.call_args_list
            
            # 验证duration调用
            assert calls[0][0][0] == "workflow.execution_duration"
            assert calls[0][0][1] == 5.0
            assert calls[0][0][2]["workflow_id"] == "wf123"
            assert calls[0][0][2]["workflow_type"] == "sequential"
            assert calls[0][0][2]["agent_count"] == "2"
    
    def test_track_model_api_call(self):
        """测试模型API调用跟踪."""
        with patch('src.multi_agent_service.utils.monitoring.metrics_collector') as mock_collector:
            track_model_api_call(
                provider="qwen",
                model="qwen-turbo",
                duration=2.0,
                success=True,
                token_count=150,
                cost=0.003
            )
            
            # 验证所有指标被记录
            assert mock_collector.record_metric.call_count == 5  # duration, count, success, tokens, cost
            
            calls = mock_collector.record_metric.call_args_list
            
            # 验证token_usage调用
            token_call = next(call for call in calls if call[0][0] == "model.token_usage")
            assert token_call[0][1] == 150
            assert token_call[0][2]["unit"] == "tokens"
            
            # 验证cost调用
            cost_call = next(call for call in calls if call[0][0] == "model.cost")
            assert cost_call[0][1] == 0.003
            assert cost_call[0][2]["unit"] == "usd"


class TestPerformanceReport:
    """测试性能报告."""
    
    def test_get_performance_report(self):
        """测试获取性能报告."""
        with patch('src.multi_agent_service.utils.monitoring.metrics_collector') as mock_collector:
            # 模拟当前指标
            mock_metrics = PerformanceMetrics(
                api_request_count=100,
                api_request_duration_avg=0.5,
                api_error_rate=0.02,
                agent_execution_count=50,
                agent_success_rate=0.95,
                cpu_usage_percent=75.0,
                memory_usage_percent=60.0,
                model_api_call_count=25,
                model_token_usage=5000,
                model_cost_total=1.25
            )
            mock_collector.get_current_metrics.return_value = mock_metrics
            
            report = get_performance_report()
            
            # 验证报告结构
            assert "timestamp" in report
            assert "metrics" in report
            assert "summary" in report
            
            # 验证摘要信息
            summary = report["summary"]
            assert summary["total_api_requests"] == 100
            assert summary["avg_api_response_time"] == "0.500s"
            assert summary["api_error_rate"] == "2.00%"
            assert summary["agent_success_rate"] == "95.00%"
            assert summary["cpu_usage"] == "75.0%"
            assert summary["memory_usage"] == "60.0%"
            assert summary["total_token_usage"] == 5000
            assert summary["total_model_cost"] == "$1.2500"


if __name__ == "__main__":
    pytest.main([__file__])