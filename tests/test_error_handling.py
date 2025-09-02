"""错误处理系统的单元测试."""

import pytest
from datetime import datetime
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from src.multi_agent_service.utils.exceptions import (
    ErrorCode,
    ErrorSeverity,
    ErrorCategory,
    BaseServiceException,
    APIException,
    BusinessException,
    AgentException,
    WorkflowException,
    ModelException,
    SystemException,
    BadRequestException,
    UnauthorizedException,
    NotFoundException,
    InternalServerErrorException
)
from src.multi_agent_service.utils.error_handler import (
    ErrorHandler,
    APIErrorStrategy,
    BusinessErrorStrategy,
    AgentErrorStrategy,
    WorkflowErrorStrategy,
    ModelErrorStrategy,
    SystemErrorStrategy,
    DefaultErrorStrategy
)


class TestExceptions:
    """测试异常类."""
    
    def test_base_service_exception(self):
        """测试基础服务异常."""
        exc = BaseServiceException(
            message="Test error",
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            category=ErrorCategory.API,
            severity=ErrorSeverity.HIGH,
            context={"test": "value"},
            user_message="User friendly message",
            suggestions=["Try again"]
        )
        
        assert exc.error_detail.error_message == "Test error"
        assert exc.error_detail.error_code == ErrorCode.INTERNAL_SERVER_ERROR
        assert exc.error_detail.error_category == ErrorCategory.API
        assert exc.error_detail.severity == ErrorSeverity.HIGH
        assert exc.error_detail.context == {"test": "value"}
        assert exc.error_detail.user_message == "User friendly message"
        assert exc.error_detail.suggestions == ["Try again"]
        assert isinstance(exc.error_detail.timestamp, datetime)
    
    def test_api_exception(self):
        """测试API异常."""
        exc = APIException(
            message="Bad request",
            error_code=ErrorCode.BAD_REQUEST,
            status_code=400
        )
        
        assert exc.status_code == 400
        assert exc.error_detail.error_category == ErrorCategory.API
        assert exc.error_detail.error_code == ErrorCode.BAD_REQUEST
    
    def test_agent_exception(self):
        """测试智能体异常."""
        exc = AgentException(
            message="Agent error",
            error_code=ErrorCode.AGENT_NOT_FOUND,
            agent_id="test-agent-123"
        )
        
        assert exc.agent_id == "test-agent-123"
        assert exc.error_detail.error_category == ErrorCategory.AGENT
        assert exc.error_detail.context["agent_id"] == "test-agent-123"
    
    def test_workflow_exception(self):
        """测试工作流异常."""
        exc = WorkflowException(
            message="Workflow error",
            error_code=ErrorCode.WORKFLOW_EXECUTION_FAILED,
            workflow_id="workflow-456"
        )
        
        assert exc.workflow_id == "workflow-456"
        assert exc.error_detail.error_category == ErrorCategory.WORKFLOW
        assert exc.error_detail.context["workflow_id"] == "workflow-456"
    
    def test_model_exception(self):
        """测试模型服务异常."""
        exc = ModelException(
            message="Model error",
            error_code=ErrorCode.MODEL_API_ERROR,
            provider="qwen"
        )
        
        assert exc.provider == "qwen"
        assert exc.error_detail.error_category == ErrorCategory.MODEL
        assert exc.error_detail.context["provider"] == "qwen"
    
    def test_system_exception(self):
        """测试系统级异常."""
        exc = SystemException(
            message="System error",
            error_code=ErrorCode.DATABASE_ERROR
        )
        
        assert exc.error_detail.error_category == ErrorCategory.SYSTEM
        assert exc.error_detail.severity == ErrorSeverity.HIGH
    
    def test_specific_api_exceptions(self):
        """测试具体的API异常类."""
        # BadRequestException
        bad_req = BadRequestException("Invalid input")
        assert bad_req.status_code == 400
        assert bad_req.error_detail.error_code == ErrorCode.BAD_REQUEST
        
        # UnauthorizedException
        unauth = UnauthorizedException("Not authenticated")
        assert unauth.status_code == 401
        assert unauth.error_detail.error_code == ErrorCode.UNAUTHORIZED
        
        # NotFoundException
        not_found = NotFoundException("Resource not found")
        assert not_found.status_code == 404
        assert not_found.error_detail.error_code == ErrorCode.NOT_FOUND
        
        # InternalServerErrorException
        internal = InternalServerErrorException("Server error")
        assert internal.status_code == 500
        assert internal.error_detail.error_code == ErrorCode.INTERNAL_SERVER_ERROR


class TestErrorStrategies:
    """测试错误处理策略."""
    
    def test_api_error_strategy(self):
        """测试API错误处理策略."""
        strategy = APIErrorStrategy()
        
        # 测试API异常处理
        api_exc = BadRequestException("Invalid request")
        assert strategy.can_handle(api_exc)
        
        result = strategy.handle(api_exc)
        assert "error" in result
        assert result["error"]["error_code"] == ErrorCode.BAD_REQUEST
        assert result["error"]["category"] == ErrorCategory.API
        
        # 测试HTTP异常处理
        http_exc = HTTPException(status_code=404, detail="Not found")
        assert strategy.can_handle(http_exc)
        
        result = strategy.handle(http_exc)
        assert "error" in result
        assert result["error"]["error_code"] == "HTTP_404"
    
    def test_business_error_strategy(self):
        """测试业务错误处理策略."""
        strategy = BusinessErrorStrategy()
        
        business_exc = BusinessException(
            message="Intent recognition failed",
            error_code=ErrorCode.INTENT_RECOGNITION_FAILED
        )
        
        assert strategy.can_handle(business_exc)
        
        result = strategy.handle(business_exc)
        assert "error" in result
        assert result["error"]["error_code"] == ErrorCode.INTENT_RECOGNITION_FAILED
        assert result["error"]["category"] == ErrorCategory.BUSINESS
        assert "recovery_actions" in result["error"]
    
    def test_agent_error_strategy(self):
        """测试智能体错误处理策略."""
        strategy = AgentErrorStrategy()
        
        agent_exc = AgentException(
            message="Agent not found",
            error_code=ErrorCode.AGENT_NOT_FOUND,
            agent_id="test-agent"
        )
        
        assert strategy.can_handle(agent_exc)
        
        result = strategy.handle(agent_exc)
        assert "error" in result
        assert result["error"]["error_code"] == ErrorCode.AGENT_NOT_FOUND
        assert result["error"]["agent_id"] == "test-agent"
        assert "recovery_actions" in result["error"]
    
    def test_workflow_error_strategy(self):
        """测试工作流错误处理策略."""
        strategy = WorkflowErrorStrategy()
        
        workflow_exc = WorkflowException(
            message="Workflow execution failed",
            error_code=ErrorCode.WORKFLOW_EXECUTION_FAILED,
            workflow_id="test-workflow"
        )
        
        assert strategy.can_handle(workflow_exc)
        
        result = strategy.handle(workflow_exc)
        assert "error" in result
        assert result["error"]["error_code"] == ErrorCode.WORKFLOW_EXECUTION_FAILED
        assert result["error"]["workflow_id"] == "test-workflow"
        assert "recovery_actions" in result["error"]
    
    def test_model_error_strategy(self):
        """测试模型服务错误处理策略."""
        strategy = ModelErrorStrategy()
        
        model_exc = ModelException(
            message="Model API error",
            error_code=ErrorCode.MODEL_API_ERROR,
            provider="qwen"
        )
        
        assert strategy.can_handle(model_exc)
        
        result = strategy.handle(model_exc)
        assert "error" in result
        assert result["error"]["error_code"] == ErrorCode.MODEL_API_ERROR
        assert result["error"]["provider"] == "qwen"
        assert "recovery_actions" in result["error"]
    
    def test_system_error_strategy(self):
        """测试系统错误处理策略."""
        strategy = SystemErrorStrategy()
        
        system_exc = SystemException(
            message="Database error",
            error_code=ErrorCode.DATABASE_ERROR
        )
        
        assert strategy.can_handle(system_exc)
        
        result = strategy.handle(system_exc)
        assert "error" in result
        assert result["error"]["error_code"] == ErrorCode.DATABASE_ERROR
        assert result["error"]["category"] == ErrorCategory.SYSTEM
        assert "recovery_actions" in result["error"]
    
    def test_default_error_strategy(self):
        """测试默认错误处理策略."""
        strategy = DefaultErrorStrategy()
        
        # 测试处理未知异常
        unknown_exc = ValueError("Unknown error")
        assert strategy.can_handle(unknown_exc)
        
        result = strategy.handle(unknown_exc)
        assert "error" in result
        assert result["error"]["error_code"] == ErrorCode.INTERNAL_SERVER_ERROR
        assert result["error"]["category"] == ErrorCategory.API


class TestErrorHandler:
    """测试错误处理器."""
    
    def test_error_handler_initialization(self):
        """测试错误处理器初始化."""
        handler = ErrorHandler()
        assert len(handler.strategies) > 0
        
        # 确保DefaultErrorStrategy在最后
        assert isinstance(handler.strategies[-1], DefaultErrorStrategy)
    
    def test_handle_api_error(self):
        """测试处理API错误."""
        handler = ErrorHandler()
        
        api_exc = BadRequestException("Invalid request")
        result = handler.handle_error(api_exc)
        
        assert "error" in result
        assert result["error"]["error_code"] == ErrorCode.BAD_REQUEST
        assert result["error"]["category"] == ErrorCategory.API
    
    def test_handle_business_error(self):
        """测试处理业务错误."""
        handler = ErrorHandler()
        
        business_exc = BusinessException(
            message="Validation failed",
            error_code=ErrorCode.VALIDATION_FAILED
        )
        result = handler.handle_error(business_exc)
        
        assert "error" in result
        assert result["error"]["error_code"] == ErrorCode.VALIDATION_FAILED
        assert result["error"]["category"] == ErrorCategory.BUSINESS
    
    def test_handle_agent_error(self):
        """测试处理智能体错误."""
        handler = ErrorHandler()
        
        agent_exc = AgentException(
            message="Agent timeout",
            error_code=ErrorCode.AGENT_TIMEOUT,
            agent_id="test-agent"
        )
        result = handler.handle_error(agent_exc)
        
        assert "error" in result
        assert result["error"]["error_code"] == ErrorCode.AGENT_TIMEOUT
        assert result["error"]["agent_id"] == "test-agent"
    
    def test_handle_workflow_error(self):
        """测试处理工作流错误."""
        handler = ErrorHandler()
        
        workflow_exc = WorkflowException(
            message="Step failed",
            error_code=ErrorCode.WORKFLOW_STEP_FAILED,
            workflow_id="test-workflow"
        )
        result = handler.handle_error(workflow_exc)
        
        assert "error" in result
        assert result["error"]["error_code"] == ErrorCode.WORKFLOW_STEP_FAILED
        assert result["error"]["workflow_id"] == "test-workflow"
    
    def test_handle_model_error(self):
        """测试处理模型服务错误."""
        handler = ErrorHandler()
        
        model_exc = ModelException(
            message="Quota exceeded",
            error_code=ErrorCode.MODEL_QUOTA_EXCEEDED,
            provider="deepseek"
        )
        result = handler.handle_error(model_exc)
        
        assert "error" in result
        assert result["error"]["error_code"] == ErrorCode.MODEL_QUOTA_EXCEEDED
        assert result["error"]["provider"] == "deepseek"
    
    def test_handle_system_error(self):
        """测试处理系统错误."""
        handler = ErrorHandler()
        
        system_exc = SystemException(
            message="Network error",
            error_code=ErrorCode.NETWORK_ERROR
        )
        result = handler.handle_error(system_exc)
        
        assert "error" in result
        assert result["error"]["error_code"] == ErrorCode.NETWORK_ERROR
        assert result["error"]["category"] == ErrorCategory.SYSTEM
    
    def test_handle_unknown_error(self):
        """测试处理未知错误."""
        handler = ErrorHandler()
        
        unknown_exc = RuntimeError("Unknown runtime error")
        result = handler.handle_error(unknown_exc)
        
        assert "error" in result
        assert result["error"]["error_code"] == ErrorCode.INTERNAL_SERVER_ERROR
        assert result["error"]["category"] == ErrorCategory.API
    
    def test_create_error_response(self):
        """测试创建错误响应."""
        handler = ErrorHandler()
        
        api_exc = BadRequestException("Invalid input")
        response = handler.create_error_response(api_exc)
        
        assert response.status_code == 400
        assert "error" in response.body.decode()
    
    def test_error_context(self):
        """测试错误上下文传递."""
        handler = ErrorHandler()
        
        context = {
            "request_id": "test-123",
            "user_id": "user-456"
        }
        
        api_exc = BadRequestException("Invalid request")
        result = handler.handle_error(api_exc, context)
        
        # 上下文信息应该被包含在错误详情中
        assert "error" in result


class TestRecoveryActions:
    """测试恢复操作建议."""
    
    def test_business_error_recovery_actions(self):
        """测试业务错误的恢复操作."""
        strategy = BusinessErrorStrategy()
        
        # 意图识别失败
        intent_exc = BusinessException(
            message="Intent recognition failed",
            error_code=ErrorCode.INTENT_RECOGNITION_FAILED
        )
        actions = strategy.get_recovery_actions(intent_exc)
        assert len(actions) > 0
        assert any("重新表述" in action for action in actions)
        
        # 智能体路由失败
        routing_exc = BusinessException(
            message="Agent routing failed",
            error_code=ErrorCode.AGENT_ROUTING_FAILED
        )
        actions = strategy.get_recovery_actions(routing_exc)
        assert len(actions) > 0
        assert any("默认智能体" in action for action in actions)
    
    def test_agent_error_recovery_actions(self):
        """测试智能体错误的恢复操作."""
        strategy = AgentErrorStrategy()
        
        # 智能体未找到
        not_found_exc = AgentException(
            message="Agent not found",
            error_code=ErrorCode.AGENT_NOT_FOUND,
            agent_id="test-agent"
        )
        actions = strategy.get_recovery_actions(not_found_exc)
        assert len(actions) > 0
        assert any("备用智能体" in action for action in actions)
        
        # 智能体过载
        overload_exc = AgentException(
            message="Agent overload",
            error_code=ErrorCode.AGENT_OVERLOAD,
            agent_id="test-agent"
        )
        actions = strategy.get_recovery_actions(overload_exc)
        assert len(actions) > 0
        assert any("队列" in action for action in actions)
    
    def test_model_error_recovery_actions(self):
        """测试模型服务错误的恢复操作."""
        strategy = ModelErrorStrategy()
        
        # 配额超限
        quota_exc = ModelException(
            message="Quota exceeded",
            error_code=ErrorCode.MODEL_QUOTA_EXCEEDED,
            provider="qwen"
        )
        actions = strategy.get_recovery_actions(quota_exc)
        assert len(actions) > 0
        assert any("备用模型" in action for action in actions)
        
        # 请求超时
        timeout_exc = ModelException(
            message="Request timeout",
            error_code=ErrorCode.MODEL_TIMEOUT,
            provider="deepseek"
        )
        actions = strategy.get_recovery_actions(timeout_exc)
        assert len(actions) > 0
        assert any("重新尝试" in action for action in actions)


if __name__ == "__main__":
    pytest.main([__file__])