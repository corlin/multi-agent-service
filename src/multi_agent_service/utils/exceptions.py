"""统一异常处理模块."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_serializer


class ErrorCode:
    """错误代码常量."""
    
    # API层错误 (1000-1999)
    BAD_REQUEST = "API_1000"
    UNAUTHORIZED = "API_1001"
    FORBIDDEN = "API_1002"
    NOT_FOUND = "API_1003"
    METHOD_NOT_ALLOWED = "API_1004"
    CONFLICT = "API_1005"
    UNPROCESSABLE_ENTITY = "API_1006"
    TOO_MANY_REQUESTS = "API_1007"
    INTERNAL_SERVER_ERROR = "API_1008"
    SERVICE_UNAVAILABLE = "API_1009"
    GATEWAY_TIMEOUT = "API_1010"
    
    # 业务逻辑错误 (2000-2999)
    INTENT_RECOGNITION_FAILED = "BIZ_2000"
    AGENT_ROUTING_FAILED = "BIZ_2001"
    WORKFLOW_EXECUTION_FAILED = "BIZ_2002"
    COLLABORATION_FAILED = "BIZ_2003"
    TASK_DECOMPOSITION_FAILED = "BIZ_2004"
    CONFLICT_RESOLUTION_FAILED = "BIZ_2005"
    VALIDATION_FAILED = "BIZ_2006"
    CONFIGURATION_ERROR = "BIZ_2007"
    
    # 智能体错误 (3000-3999)
    AGENT_NOT_FOUND = "AGENT_3000"
    AGENT_UNAVAILABLE = "AGENT_3001"
    AGENT_OVERLOAD = "AGENT_3002"
    AGENT_TIMEOUT = "AGENT_3003"
    AGENT_INITIALIZATION_FAILED = "AGENT_3004"
    AGENT_PROCESSING_ERROR = "AGENT_3005"
    AGENT_COLLABORATION_ERROR = "AGENT_3006"
    AGENT_MODEL_ERROR = "AGENT_3007"
    AGENT_REGISTRY_ERROR = "AGENT_3008"
    AGENT_VALIDATION_ERROR = "AGENT_3009"
    
    # 工作流错误 (4000-4999)
    WORKFLOW_NOT_FOUND = "WORKFLOW_4000"
    WORKFLOW_INVALID_STATE = "WORKFLOW_4001"
    WORKFLOW_EXECUTION_TIMEOUT = "WORKFLOW_4002"
    WORKFLOW_STEP_FAILED = "WORKFLOW_4003"
    WORKFLOW_GRAPH_ERROR = "WORKFLOW_4004"
    WORKFLOW_STATE_ERROR = "WORKFLOW_4005"
    WORKFLOW_SERIALIZATION_ERROR = "WORKFLOW_4006"
    WORKFLOW_VALIDATION_ERROR = "WORKFLOW_4007"
    
    # 模型服务错误 (5000-5999)
    MODEL_API_ERROR = "MODEL_5000"
    MODEL_TIMEOUT = "MODEL_5001"
    MODEL_QUOTA_EXCEEDED = "MODEL_5002"
    MODEL_AUTHENTICATION_FAILED = "MODEL_5003"
    MODEL_RATE_LIMITED = "MODEL_5004"
    MODEL_UNAVAILABLE = "MODEL_5005"
    MODEL_RESPONSE_INVALID = "MODEL_5006"
    MODEL_PROVIDER_ERROR = "MODEL_5007"
    
    # 系统级错误 (6000-6999)
    DATABASE_ERROR = "SYS_6000"
    NETWORK_ERROR = "SYS_6001"
    MEMORY_ERROR = "SYS_6002"
    DISK_ERROR = "SYS_6003"
    PERMISSION_ERROR = "SYS_6004"
    RESOURCE_EXHAUSTED = "SYS_6005"
    EXTERNAL_SERVICE_ERROR = "SYS_6006"
    CONFIGURATION_LOAD_ERROR = "SYS_6007"


class ErrorSeverity:
    """错误严重程度."""
    
    LOW = "low"          # 低级错误，不影响核心功能
    MEDIUM = "medium"    # 中级错误，影响部分功能
    HIGH = "high"        # 高级错误，影响核心功能
    CRITICAL = "critical"  # 严重错误，系统不可用


class ErrorCategory:
    """错误分类."""
    
    API = "api"                    # API层错误
    BUSINESS = "business"          # 业务逻辑错误
    AGENT = "agent"               # 智能体错误
    WORKFLOW = "workflow"         # 工作流错误
    MODEL = "model"               # 模型服务错误
    SYSTEM = "system"             # 系统级错误


class ErrorDetail(BaseModel):
    """错误详情模型."""
    
    error_id: str = Field(default_factory=lambda: str(uuid4()), description="错误ID")
    error_code: str = Field(..., description="错误代码")
    error_message: str = Field(..., description="错误消息")
    error_category: str = Field(..., description="错误分类")
    severity: str = Field(..., description="严重程度")
    timestamp: datetime = Field(default_factory=datetime.now, description="错误时间")
    context: Dict[str, Any] = Field(default_factory=dict, description="错误上下文")
    stack_trace: Optional[str] = Field(None, description="堆栈跟踪")
    user_message: Optional[str] = Field(None, description="用户友好的错误消息")
    suggestions: List[str] = Field(default_factory=list, description="解决建议")
    
    @field_serializer('timestamp')
    def serialize_timestamp(self, value: datetime) -> str:
        return value.isoformat()


class BaseServiceException(Exception):
    """服务基础异常类."""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        category: str,
        severity: str = ErrorSeverity.MEDIUM,
        context: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ):
        super().__init__(message)
        self.error_detail = ErrorDetail(
            error_code=error_code,
            error_message=message,
            error_category=category,
            severity=severity,
            context=context or {},
            user_message=user_message,
            suggestions=suggestions or []
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式."""
        return self.error_detail.model_dump()


class APIException(BaseServiceException):
    """API层异常."""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 500,
        severity: str = ErrorSeverity.MEDIUM,
        context: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            category=ErrorCategory.API,
            severity=severity,
            context=context,
            user_message=user_message,
            suggestions=suggestions
        )
        self.status_code = status_code


class BusinessException(BaseServiceException):
    """业务逻辑异常."""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        severity: str = ErrorSeverity.MEDIUM,
        context: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            category=ErrorCategory.BUSINESS,
            severity=severity,
            context=context,
            user_message=user_message,
            suggestions=suggestions
        )


class AgentException(BaseServiceException):
    """智能体异常."""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        agent_id: Optional[str] = None,
        severity: str = ErrorSeverity.MEDIUM,
        context: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ):
        context = context or {}
        if agent_id:
            context["agent_id"] = agent_id
        
        super().__init__(
            message=message,
            error_code=error_code,
            category=ErrorCategory.AGENT,
            severity=severity,
            context=context,
            user_message=user_message,
            suggestions=suggestions
        )
        self.agent_id = agent_id


class WorkflowException(BaseServiceException):
    """工作流异常."""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        workflow_id: Optional[str] = None,
        severity: str = ErrorSeverity.MEDIUM,
        context: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ):
        context = context or {}
        if workflow_id:
            context["workflow_id"] = workflow_id
        
        super().__init__(
            message=message,
            error_code=error_code,
            category=ErrorCategory.WORKFLOW,
            severity=severity,
            context=context,
            user_message=user_message,
            suggestions=suggestions
        )
        self.workflow_id = workflow_id


class ModelException(BaseServiceException):
    """模型服务异常."""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        provider: Optional[str] = None,
        severity: str = ErrorSeverity.MEDIUM,
        context: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ):
        context = context or {}
        if provider:
            context["provider"] = provider
        
        super().__init__(
            message=message,
            error_code=error_code,
            category=ErrorCategory.MODEL,
            severity=severity,
            context=context,
            user_message=user_message,
            suggestions=suggestions
        )
        self.provider = provider


class SystemException(BaseServiceException):
    """系统级异常."""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        severity: str = ErrorSeverity.HIGH,
        context: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            category=ErrorCategory.SYSTEM,
            severity=severity,
            context=context,
            user_message=user_message,
            suggestions=suggestions
        )


# 具体异常类定义
class BadRequestException(APIException):
    """400 Bad Request异常."""
    
    def __init__(self, message: str = "Bad Request", **kwargs):
        super().__init__(
            message=message,
            error_code=ErrorCode.BAD_REQUEST,
            status_code=400,
            **kwargs
        )


class UnauthorizedException(APIException):
    """401 Unauthorized异常."""
    
    def __init__(self, message: str = "Unauthorized", **kwargs):
        super().__init__(
            message=message,
            error_code=ErrorCode.UNAUTHORIZED,
            status_code=401,
            **kwargs
        )


class ForbiddenException(APIException):
    """403 Forbidden异常."""
    
    def __init__(self, message: str = "Forbidden", **kwargs):
        super().__init__(
            message=message,
            error_code=ErrorCode.FORBIDDEN,
            status_code=403,
            **kwargs
        )


class NotFoundException(APIException):
    """404 Not Found异常."""
    
    def __init__(self, message: str = "Not Found", **kwargs):
        super().__init__(
            message=message,
            error_code=ErrorCode.NOT_FOUND,
            status_code=404,
            **kwargs
        )


class ConflictException(APIException):
    """409 Conflict异常."""
    
    def __init__(self, message: str = "Conflict", **kwargs):
        super().__init__(
            message=message,
            error_code=ErrorCode.CONFLICT,
            status_code=409,
            **kwargs
        )


class UnprocessableEntityException(APIException):
    """422 Unprocessable Entity异常."""
    
    def __init__(self, message: str = "Unprocessable Entity", **kwargs):
        super().__init__(
            message=message,
            error_code=ErrorCode.UNPROCESSABLE_ENTITY,
            status_code=422,
            **kwargs
        )


class TooManyRequestsException(APIException):
    """429 Too Many Requests异常."""
    
    def __init__(self, message: str = "Too Many Requests", **kwargs):
        super().__init__(
            message=message,
            error_code=ErrorCode.TOO_MANY_REQUESTS,
            status_code=429,
            **kwargs
        )


class InternalServerErrorException(APIException):
    """500 Internal Server Error异常."""
    
    def __init__(self, message: str = "Internal Server Error", **kwargs):
        super().__init__(
            message=message,
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            status_code=500,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )


class ServiceUnavailableException(APIException):
    """503 Service Unavailable异常."""
    
    def __init__(self, message: str = "Service Unavailable", **kwargs):
        super().__init__(
            message=message,
            error_code=ErrorCode.SERVICE_UNAVAILABLE,
            status_code=503,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )


class GatewayTimeoutException(APIException):
    """504 Gateway Timeout异常."""
    
    def __init__(self, message: str = "Gateway Timeout", **kwargs):
        super().__init__(
            message=message,
            error_code=ErrorCode.GATEWAY_TIMEOUT,
            status_code=504,
            **kwargs
        )


class ValidationError(BusinessException):
    """验证错误异常."""
    
    def __init__(self, message: str = "Validation Error", **kwargs):
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_FAILED,
            **kwargs
        )


class ConfigurationError(BusinessException):
    """配置错误异常."""
    
    def __init__(self, message: str = "Configuration Error", **kwargs):
        super().__init__(
            message=message,
            error_code=ErrorCode.CONFIGURATION_ERROR,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )