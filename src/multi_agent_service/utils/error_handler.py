"""错误处理策略和处理器."""

import logging
import traceback
from typing import Any, Dict, List, Optional, Type, Union

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

from .exceptions import (
    BaseServiceException,
    APIException,
    BusinessException,
    AgentException,
    WorkflowException,
    ModelException,
    SystemException,
    ErrorCode,
    ErrorSeverity,
    ErrorCategory,
    InternalServerErrorException
)


logger = logging.getLogger(__name__)


class ErrorHandlingStrategy:
    """错误处理策略基类."""
    
    def can_handle(self, exception: Exception) -> bool:
        """判断是否可以处理该异常."""
        raise NotImplementedError
    
    def handle(self, exception: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """处理异常并返回错误响应."""
        raise NotImplementedError
    
    def get_recovery_actions(self, exception: Exception) -> List[str]:
        """获取恢复操作建议."""
        return []


class APIErrorStrategy(ErrorHandlingStrategy):
    """API错误处理策略."""
    
    def can_handle(self, exception: Exception) -> bool:
        return isinstance(exception, (APIException, HTTPException))
    
    def handle(self, exception: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if isinstance(exception, APIException):
            return self._handle_api_exception(exception, context)
        elif isinstance(exception, HTTPException):
            return self._handle_http_exception(exception, context)
        
        return self._handle_unknown_api_error(exception, context)
    
    def _handle_api_exception(self, exception: APIException, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """处理API异常."""
        error_detail = exception.error_detail
        
        # 记录日志
        logger.error(
            f"API Error: {error_detail.error_code} - {error_detail.error_message}",
            extra={
                "error_id": error_detail.error_id,
                "error_code": error_detail.error_code,
                "category": error_detail.error_category,
                "severity": error_detail.severity,
                "context": error_detail.context
            }
        )
        
        return {
            "error": {
                "error_id": error_detail.error_id,
                "error_code": error_detail.error_code,
                "message": error_detail.user_message or error_detail.error_message,
                "category": error_detail.error_category,
                "severity": error_detail.severity,
                "timestamp": error_detail.timestamp.isoformat(),
                "suggestions": error_detail.suggestions
            }
        }
    
    def _handle_http_exception(self, exception: HTTPException, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """处理FastAPI HTTPException."""
        logger.error(f"HTTP Exception: {exception.status_code} - {exception.detail}")
        
        return {
            "error": {
                "error_code": f"HTTP_{exception.status_code}",
                "message": str(exception.detail),
                "category": ErrorCategory.API,
                "severity": ErrorSeverity.MEDIUM
            }
        }
    
    def _handle_unknown_api_error(self, exception: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """处理未知API错误."""
        logger.error(f"Unknown API Error: {str(exception)}", exc_info=True)
        
        return {
            "error": {
                "error_code": ErrorCode.INTERNAL_SERVER_ERROR,
                "message": "An unexpected API error occurred",
                "category": ErrorCategory.API,
                "severity": ErrorSeverity.HIGH
            }
        }


class BusinessErrorStrategy(ErrorHandlingStrategy):
    """业务逻辑错误处理策略."""
    
    def can_handle(self, exception: Exception) -> bool:
        return isinstance(exception, BusinessException)
    
    def handle(self, exception: BusinessException, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        error_detail = exception.error_detail
        
        # 记录业务错误日志
        logger.warning(
            f"Business Error: {error_detail.error_code} - {error_detail.error_message}",
            extra={
                "error_id": error_detail.error_id,
                "error_code": error_detail.error_code,
                "context": error_detail.context
            }
        )
        
        return {
            "error": {
                "error_id": error_detail.error_id,
                "error_code": error_detail.error_code,
                "message": error_detail.user_message or error_detail.error_message,
                "category": error_detail.error_category,
                "severity": error_detail.severity,
                "timestamp": error_detail.timestamp.isoformat(),
                "suggestions": error_detail.suggestions,
                "recovery_actions": self.get_recovery_actions(exception)
            }
        }
    
    def get_recovery_actions(self, exception: BusinessException) -> List[str]:
        """获取业务错误的恢复操作."""
        recovery_actions = []
        
        if exception.error_detail.error_code == ErrorCode.INTENT_RECOGNITION_FAILED:
            recovery_actions = [
                "请尝试重新表述您的问题",
                "提供更多上下文信息",
                "联系人工客服"
            ]
        elif exception.error_detail.error_code == ErrorCode.AGENT_ROUTING_FAILED:
            recovery_actions = [
                "系统将使用默认智能体处理",
                "请稍后重试",
                "联系技术支持"
            ]
        elif exception.error_detail.error_code == ErrorCode.WORKFLOW_EXECUTION_FAILED:
            recovery_actions = [
                "系统将重新执行工作流",
                "检查输入参数是否正确",
                "联系系统管理员"
            ]
        
        return recovery_actions


class AgentErrorStrategy(ErrorHandlingStrategy):
    """智能体错误处理策略."""
    
    def can_handle(self, exception: Exception) -> bool:
        return isinstance(exception, AgentException)
    
    def handle(self, exception: AgentException, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        error_detail = exception.error_detail
        
        # 记录智能体错误日志
        logger.error(
            f"Agent Error: {error_detail.error_code} - {error_detail.error_message}",
            extra={
                "error_id": error_detail.error_id,
                "error_code": error_detail.error_code,
                "agent_id": exception.agent_id,
                "context": error_detail.context
            }
        )
        
        return {
            "error": {
                "error_id": error_detail.error_id,
                "error_code": error_detail.error_code,
                "message": error_detail.user_message or "智能体服务暂时不可用，请稍后重试",
                "category": error_detail.error_category,
                "severity": error_detail.severity,
                "timestamp": error_detail.timestamp.isoformat(),
                "agent_id": exception.agent_id,
                "suggestions": error_detail.suggestions,
                "recovery_actions": self.get_recovery_actions(exception)
            }
        }
    
    def get_recovery_actions(self, exception: AgentException) -> List[str]:
        """获取智能体错误的恢复操作."""
        recovery_actions = []
        
        if exception.error_detail.error_code == ErrorCode.AGENT_NOT_FOUND:
            recovery_actions = [
                "系统将使用备用智能体",
                "请联系系统管理员"
            ]
        elif exception.error_detail.error_code == ErrorCode.AGENT_OVERLOAD:
            recovery_actions = [
                "请求已加入队列，请稍等",
                "系统将分配其他可用智能体"
            ]
        elif exception.error_detail.error_code == ErrorCode.AGENT_TIMEOUT:
            recovery_actions = [
                "系统将重新尝试处理",
                "请检查网络连接",
                "如问题持续，请联系技术支持"
            ]
        
        return recovery_actions


class WorkflowErrorStrategy(ErrorHandlingStrategy):
    """工作流错误处理策略."""
    
    def can_handle(self, exception: Exception) -> bool:
        return isinstance(exception, WorkflowException)
    
    def handle(self, exception: WorkflowException, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        error_detail = exception.error_detail
        
        # 记录工作流错误日志
        logger.error(
            f"Workflow Error: {error_detail.error_code} - {error_detail.error_message}",
            extra={
                "error_id": error_detail.error_id,
                "error_code": error_detail.error_code,
                "workflow_id": exception.workflow_id,
                "context": error_detail.context
            }
        )
        
        return {
            "error": {
                "error_id": error_detail.error_id,
                "error_code": error_detail.error_code,
                "message": error_detail.user_message or "工作流执行出现问题，请稍后重试",
                "category": error_detail.error_category,
                "severity": error_detail.severity,
                "timestamp": error_detail.timestamp.isoformat(),
                "workflow_id": exception.workflow_id,
                "suggestions": error_detail.suggestions,
                "recovery_actions": self.get_recovery_actions(exception)
            }
        }
    
    def get_recovery_actions(self, exception: WorkflowException) -> List[str]:
        """获取工作流错误的恢复操作."""
        recovery_actions = []
        
        if exception.error_detail.error_code == ErrorCode.WORKFLOW_EXECUTION_TIMEOUT:
            recovery_actions = [
                "系统将重新执行工作流",
                "请检查输入数据的复杂度",
                "联系系统管理员调整超时设置"
            ]
        elif exception.error_detail.error_code == ErrorCode.WORKFLOW_STEP_FAILED:
            recovery_actions = [
                "系统将从失败步骤重新开始",
                "检查步骤输入参数",
                "查看详细错误日志"
            ]
        
        return recovery_actions


class ModelErrorStrategy(ErrorHandlingStrategy):
    """模型服务错误处理策略."""
    
    def can_handle(self, exception: Exception) -> bool:
        return isinstance(exception, ModelException)
    
    def handle(self, exception: ModelException, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        error_detail = exception.error_detail
        
        # 记录模型服务错误日志
        logger.error(
            f"Model Error: {error_detail.error_code} - {error_detail.error_message}",
            extra={
                "error_id": error_detail.error_id,
                "error_code": error_detail.error_code,
                "provider": exception.provider,
                "context": error_detail.context
            }
        )
        
        return {
            "error": {
                "error_id": error_detail.error_id,
                "error_code": error_detail.error_code,
                "message": error_detail.user_message or "AI模型服务暂时不可用，请稍后重试",
                "category": error_detail.error_category,
                "severity": error_detail.severity,
                "timestamp": error_detail.timestamp.isoformat(),
                "provider": exception.provider,
                "suggestions": error_detail.suggestions,
                "recovery_actions": self.get_recovery_actions(exception)
            }
        }
    
    def get_recovery_actions(self, exception: ModelException) -> List[str]:
        """获取模型服务错误的恢复操作."""
        recovery_actions = []
        
        if exception.error_detail.error_code == ErrorCode.MODEL_QUOTA_EXCEEDED:
            recovery_actions = [
                "系统将切换到备用模型",
                "请稍后重试",
                "联系管理员增加配额"
            ]
        elif exception.error_detail.error_code == ErrorCode.MODEL_TIMEOUT:
            recovery_actions = [
                "系统将重新尝试调用",
                "使用更简洁的输入",
                "切换到更快的模型"
            ]
        elif exception.error_detail.error_code == ErrorCode.MODEL_RATE_LIMITED:
            recovery_actions = [
                "请求已加入队列",
                "请稍后重试",
                "升级服务计划"
            ]
        
        return recovery_actions


class SystemErrorStrategy(ErrorHandlingStrategy):
    """系统级错误处理策略."""
    
    def can_handle(self, exception: Exception) -> bool:
        return isinstance(exception, SystemException)
    
    def handle(self, exception: SystemException, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        error_detail = exception.error_detail
        
        # 记录系统错误日志
        logger.critical(
            f"System Error: {error_detail.error_code} - {error_detail.error_message}",
            extra={
                "error_id": error_detail.error_id,
                "error_code": error_detail.error_code,
                "context": error_detail.context
            }
        )
        
        return {
            "error": {
                "error_id": error_detail.error_id,
                "error_code": error_detail.error_code,
                "message": error_detail.user_message or "系统暂时不可用，我们正在紧急修复",
                "category": error_detail.error_category,
                "severity": error_detail.severity,
                "timestamp": error_detail.timestamp.isoformat(),
                "suggestions": error_detail.suggestions,
                "recovery_actions": self.get_recovery_actions(exception)
            }
        }
    
    def get_recovery_actions(self, exception: SystemException) -> List[str]:
        """获取系统错误的恢复操作."""
        return [
            "系统正在自动恢复",
            "请稍后重试",
            "如问题持续，请联系技术支持",
            "查看系统状态页面获取更新"
        ]


class DefaultErrorStrategy(ErrorHandlingStrategy):
    """默认错误处理策略."""
    
    def can_handle(self, exception: Exception) -> bool:
        return True  # 处理所有未被其他策略处理的异常
    
    def handle(self, exception: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # 记录未知错误
        logger.error(f"Unhandled Exception: {str(exception)}", exc_info=True)
        
        # 创建内部服务器错误
        internal_error = InternalServerErrorException(
            message=f"Unhandled exception: {type(exception).__name__}",
            context={"original_exception": str(exception)},
            user_message="系统出现未知错误，请稍后重试"
        )
        
        return APIErrorStrategy().handle(internal_error, context)


class ErrorHandler:
    """统一错误处理器."""
    
    def __init__(self):
        self.strategies: List[ErrorHandlingStrategy] = [
            APIErrorStrategy(),
            BusinessErrorStrategy(),
            AgentErrorStrategy(),
            WorkflowErrorStrategy(),
            ModelErrorStrategy(),
            SystemErrorStrategy(),
            DefaultErrorStrategy()  # 必须放在最后
        ]
    
    def handle_error(self, exception: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """处理错误并返回标准化的错误响应."""
        for strategy in self.strategies:
            if strategy.can_handle(exception):
                return strategy.handle(exception, context)
        
        # 这里不应该到达，因为DefaultErrorStrategy会处理所有异常
        logger.critical(f"No strategy found for exception: {type(exception).__name__}")
        return DefaultErrorStrategy().handle(exception, context)
    
    def create_error_response(self, exception: Exception, context: Optional[Dict[str, Any]] = None) -> JSONResponse:
        """创建错误响应."""
        error_data = self.handle_error(exception, context)
        
        # 确定HTTP状态码
        status_code = 500  # 默认状态码
        if isinstance(exception, APIException):
            status_code = exception.status_code
        elif isinstance(exception, HTTPException):
            status_code = exception.status_code
        elif isinstance(exception, (BusinessException, AgentException, WorkflowException)):
            status_code = 422  # Unprocessable Entity
        elif isinstance(exception, ModelException):
            status_code = 503  # Service Unavailable
        elif isinstance(exception, SystemException):
            status_code = 500  # Internal Server Error
        
        return JSONResponse(
            status_code=status_code,
            content=error_data
        )


# 全局错误处理器实例
error_handler = ErrorHandler()