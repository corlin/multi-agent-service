"""日志记录系统的单元测试."""

import json
import logging
import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from io import StringIO

from src.multi_agent_service.utils.logging import (
    LogLevel,
    LogCategory,
    LogEntry,
    StructuredFormatter,
    MultiAgentLogger,
    LogContext,
    get_logger
)


class TestLogEntry:
    """测试日志条目模型."""
    
    def test_log_entry_creation(self):
        """测试日志条目创建."""
        entry = LogEntry(
            level=LogLevel.INFO,
            category=LogCategory.API,
            message="Test message",
            logger_name="test_logger"
        )
        
        assert entry.level == LogLevel.INFO
        assert entry.category == LogCategory.API
        assert entry.message == "Test message"
        assert entry.logger_name == "test_logger"
        assert isinstance(entry.timestamp, datetime)
        assert isinstance(entry.log_id, str)
        assert len(entry.log_id) > 0
    
    def test_log_entry_with_context(self):
        """测试带上下文的日志条目."""
        context = {"user_id": "123", "request_id": "abc"}
        tags = ["api", "request"]
        
        entry = LogEntry(
            level=LogLevel.ERROR,
            category=LogCategory.AGENT,
            message="Agent error",
            logger_name="agent_logger",
            context=context,
            tags=tags,
            correlation_id="corr-123"
        )
        
        assert entry.context == context
        assert entry.tags == tags
        assert entry.correlation_id == "corr-123"
    
    def test_log_entry_serialization(self):
        """测试日志条目序列化."""
        entry = LogEntry(
            level=LogLevel.WARNING,
            category=LogCategory.WORKFLOW,
            message="Workflow warning",
            logger_name="workflow_logger"
        )
        
        data = entry.model_dump()
        assert "log_id" in data
        assert "timestamp" in data
        assert data["level"] == LogLevel.WARNING
        assert data["category"] == LogCategory.WORKFLOW
        assert data["message"] == "Workflow warning"


class TestStructuredFormatter:
    """测试结构化格式化器."""
    
    def test_basic_formatting(self):
        """测试基础格式化."""
        formatter = StructuredFormatter()
        
        # 创建日志记录
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.category = LogCategory.API
        
        formatted = formatter.format(record)
        data = json.loads(formatted)
        
        assert data["level"] == "INFO"
        assert data["category"] == LogCategory.API
        assert data["message"] == "Test message"
        assert data["logger_name"] == "test_logger"
        assert data["line_number"] == 10
    
    def test_formatting_with_extra_fields(self):
        """测试带额外字段的格式化."""
        formatter = StructuredFormatter(include_extra=True)
        
        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=20,
            msg="Error message",
            args=(),
            exc_info=None
        )
        record.category = LogCategory.AGENT
        record.agent_id = "agent-123"
        record.request_id = "req-456"
        record.execution_time = 1.5
        
        formatted = formatter.format(record)
        data = json.loads(formatted)
        
        assert data["request_id"] == "req-456"
        assert data["context"]["agent_id"] == "agent-123"
        assert data["context"]["execution_time"] == 1.5
    
    def test_formatting_with_exception(self):
        """测试异常信息格式化."""
        formatter = StructuredFormatter()
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
        
        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=30,
            msg="Exception occurred",
            args=(),
            exc_info=exc_info
        )
        record.category = LogCategory.SYSTEM
        
        formatted = formatter.format(record)
        data = json.loads(formatted)
        
        assert "exception" in data["context"]
        assert "ValueError: Test exception" in data["context"]["exception"]


class TestMultiAgentLogger:
    """测试多智能体日志记录器."""
    
    @pytest.fixture
    def logger(self):
        """创建测试日志记录器."""
        return MultiAgentLogger("test_logger", LogLevel.DEBUG)
    
    def test_logger_creation(self, logger):
        """测试日志记录器创建."""
        assert logger.logger.name == "test_logger"
        assert logger.logger.level == logging.DEBUG
        assert len(logger.logger.handlers) > 0
    
    def test_basic_logging_methods(self, logger):
        """测试基础日志记录方法."""
        with patch.object(logger.logger, 'log') as mock_log:
            logger.debug("Debug message")
            mock_log.assert_called_with(logging.DEBUG, "Debug message", extra={'category': LogCategory.SYSTEM})
            
            logger.info("Info message", category=LogCategory.API)
            mock_log.assert_called_with(logging.INFO, "Info message", extra={'category': LogCategory.API})
            
            logger.warning("Warning message")
            mock_log.assert_called_with(logging.WARNING, "Warning message", extra={'category': LogCategory.SYSTEM})
            
            logger.error("Error message")
            mock_log.assert_called_with(logging.ERROR, "Error message", extra={'category': LogCategory.SYSTEM})
            
            logger.critical("Critical message")
            mock_log.assert_called_with(logging.CRITICAL, "Critical message", extra={'category': LogCategory.SYSTEM})
    
    def test_api_request_logging(self, logger):
        """测试API请求日志记录."""
        with patch.object(logger, '_log') as mock_log:
            logger.log_api_request(
                method="GET",
                url="/api/test",
                status_code=200,
                execution_time=0.5,
                user_id="user123",
                request_id="req456"
            )
            
            mock_log.assert_called_once()
            args, kwargs = mock_log.call_args
            
            assert args[0] == LogLevel.INFO
            assert "GET /api/test - 200 (0.500s)" in args[1]
            assert args[2] == LogCategory.API
            assert kwargs["method"] == "GET"
            assert kwargs["url"] == "/api/test"
            assert kwargs["status_code"] == 200
            assert kwargs["execution_time"] == 0.5
            assert kwargs["user_id"] == "user123"
            assert kwargs["request_id"] == "req456"
    
    def test_agent_execution_logging(self, logger):
        """测试智能体执行日志记录."""
        with patch.object(logger, '_log') as mock_log:
            # 成功执行
            logger.log_agent_execution(
                agent_id="agent123",
                agent_type="sales",
                action="process_request",
                status="success",
                execution_time=1.2,
                request_id="req789"
            )
            
            args, kwargs = mock_log.call_args
            assert args[0] == LogLevel.INFO
            assert "Agent agent123 (sales) completed process_request in 1.200s" in args[1]
            assert args[2] == LogCategory.AGENT
            
            # 失败执行
            logger.log_agent_execution(
                agent_id="agent456",
                agent_type="support",
                action="handle_query",
                status="error",
                execution_time=0.8,
                error_message="Processing failed"
            )
            
            args, kwargs = mock_log.call_args
            assert args[0] == LogLevel.ERROR
            assert "Agent agent456 (support) failed handle_query: Processing failed" in args[1]
    
    def test_workflow_execution_logging(self, logger):
        """测试工作流执行日志记录."""
        with patch.object(logger, '_log') as mock_log:
            # 工作流开始
            logger.log_workflow_execution(
                workflow_id="wf123",
                workflow_type="sequential",
                step="start",
                status="started"
            )
            
            args, kwargs = mock_log.call_args
            assert args[0] == LogLevel.INFO
            assert "Workflow wf123 (sequential) started" in args[1]
            assert args[2] == LogCategory.WORKFLOW
            
            # 工作流完成
            logger.log_workflow_execution(
                workflow_id="wf123",
                workflow_type="sequential",
                step="end",
                status="completed",
                execution_time=5.5,
                participating_agents=["agent1", "agent2"]
            )
            
            args, kwargs = mock_log.call_args
            assert args[0] == LogLevel.INFO
            assert "Workflow wf123 (sequential) completed in 5.500s" in args[1]
    
    def test_model_api_call_logging(self, logger):
        """测试模型API调用日志记录."""
        with patch.object(logger, '_log') as mock_log:
            # 成功调用
            logger.log_model_api_call(
                provider="qwen",
                model="qwen-turbo",
                status="success",
                execution_time=2.1,
                token_count=150,
                cost=0.003
            )
            
            args, kwargs = mock_log.call_args
            assert args[0] == LogLevel.INFO
            assert "Model API call to qwen/qwen-turbo completed in 2.100s (150 tokens) ($0.0030)" in args[1]
            assert args[2] == LogCategory.MODEL
            
            # 失败调用
            logger.log_model_api_call(
                provider="deepseek",
                model="deepseek-chat",
                status="error",
                execution_time=1.0,
                error_message="API quota exceeded"
            )
            
            args, kwargs = mock_log.call_args
            assert args[0] == LogLevel.ERROR
            assert "Model API call to deepseek/deepseek-chat failed: API quota exceeded" in args[1]
    
    def test_performance_metric_logging(self, logger):
        """测试性能指标日志记录."""
        with patch.object(logger, '_log') as mock_log:
            logger.log_performance_metric(
                metric_name="cpu_usage",
                metric_value=75.5,
                metric_unit="percent",
                component="system_monitor"
            )
            
            args, kwargs = mock_log.call_args
            assert args[0] == LogLevel.INFO
            assert "Performance metric: cpu_usage = 75.5 percent (system_monitor)" in args[1]
            assert args[2] == LogCategory.PERFORMANCE
    
    def test_security_event_logging(self, logger):
        """测试安全事件日志记录."""
        with patch.object(logger, '_log') as mock_log:
            # 中等严重程度
            logger.log_security_event(
                event_type="suspicious_request",
                severity="medium",
                description="SQL injection attempt detected",
                user_id="user123",
                ip_address="192.168.1.100"
            )
            
            args, kwargs = mock_log.call_args
            assert args[0] == LogLevel.WARNING
            assert "Security event (suspicious_request): SQL injection attempt detected" in args[1]
            assert args[2] == LogCategory.SECURITY
            
            # 高严重程度
            logger.log_security_event(
                event_type="authentication_bypass",
                severity="high",
                description="Authentication bypass attempt",
                ip_address="10.0.0.1"
            )
            
            args, kwargs = mock_log.call_args
            assert args[0] == LogLevel.ERROR


class TestLogContext:
    """测试日志上下文管理器."""
    
    def test_log_context(self):
        """测试日志上下文管理器."""
        logger = MultiAgentLogger("test_logger")
        
        with patch.object(logger, '_log') as mock_log:
            with LogContext(logger, user_id="user123", session_id="session456") as ctx_logger:
                ctx_logger.info("Test message", category=LogCategory.API)
            
            # 验证上下文信息被添加
            args, kwargs = mock_log.call_args
            assert kwargs["user_id"] == "user123"
            assert kwargs["session_id"] == "session456"
    
    def test_log_context_override(self):
        """测试日志上下文覆盖."""
        logger = MultiAgentLogger("test_logger")
        
        with patch.object(logger, '_log') as mock_log:
            with LogContext(logger, user_id="user123", request_id="req789") as ctx_logger:
                # 在调用时覆盖request_id
                ctx_logger.info("Test message", request_id="req999")
            
            args, kwargs = mock_log.call_args
            assert kwargs["user_id"] == "user123"
            assert kwargs["request_id"] == "req999"  # 应该被覆盖


class TestLoggerFactory:
    """测试日志记录器工厂函数."""
    
    def test_get_logger(self):
        """测试获取日志记录器."""
        logger1 = get_logger("test_logger_1")
        logger2 = get_logger("test_logger_2", LogLevel.DEBUG)
        
        assert isinstance(logger1, MultiAgentLogger)
        assert isinstance(logger2, MultiAgentLogger)
        assert logger1.logger.name == "test_logger_1"
        assert logger2.logger.name == "test_logger_2"
        assert logger2.logger.level == logging.DEBUG
    
    def test_logger_singleton_behavior(self):
        """测试日志记录器的单例行为."""
        # 注意：由于logging模块的特性，相同名称的logger会是同一个实例
        logger1 = get_logger("same_name")
        logger2 = get_logger("same_name")
        
        # 虽然MultiAgentLogger实例不同，但底层的logging.Logger是同一个
        assert logger1.logger is logger2.logger


if __name__ == "__main__":
    pytest.main([__file__])