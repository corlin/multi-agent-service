"""Agent-specific exceptions - 兼容旧版本的异常类."""

# 导入新的统一异常系统
from ..utils.exceptions import (
    AgentException as BaseAgentException,
    ErrorCode,
    ErrorSeverity
)


# 为了向后兼容，保留旧的异常类名，但继承新的异常系统
class AgentException(BaseAgentException):
    """智能体基础异常类 - 兼容旧版本."""
    
    def __init__(self, message: str, agent_id: str = None, error_code: str = None):
        # 使用新的错误代码系统
        if error_code and not error_code.startswith("AGENT_"):
            error_code = f"AGENT_{error_code}"
        
        super().__init__(
            message=message,
            error_code=error_code or ErrorCode.AGENT_PROCESSING_ERROR,
            agent_id=agent_id,
            user_message="智能体处理请求时出现问题，请稍后重试"
        )
        
        # 保持向后兼容的属性
        self.message = message
        self.error_code = error_code


class AgentInitializationError(BaseAgentException):
    """智能体初始化异常."""
    
    def __init__(self, message: str, agent_id: str = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.AGENT_INITIALIZATION_FAILED,
            agent_id=agent_id,
            severity=ErrorSeverity.HIGH,
            user_message="智能体初始化失败，请联系系统管理员",
            suggestions=[
                "检查智能体配置是否正确",
                "重启智能体服务",
                "联系技术支持"
            ]
        )


class AgentConfigurationError(BaseAgentException):
    """智能体配置异常."""
    
    def __init__(self, message: str, agent_id: str = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.AGENT_VALIDATION_ERROR,
            agent_id=agent_id,
            user_message="智能体配置错误，请检查配置参数",
            suggestions=[
                "检查配置文件格式",
                "验证必需参数是否提供",
                "参考配置文档"
            ]
        )


class AgentProcessingError(BaseAgentException):
    """智能体处理异常."""
    
    def __init__(self, message: str, agent_id: str = None, request_id: str = None):
        context = {}
        if request_id:
            context["request_id"] = request_id
        
        super().__init__(
            message=message,
            error_code=ErrorCode.AGENT_PROCESSING_ERROR,
            agent_id=agent_id,
            context=context,
            user_message="智能体处理请求失败，请稍后重试",
            suggestions=[
                "请稍后重试",
                "检查请求内容是否合适",
                "联系技术支持"
            ]
        )
        self.request_id = request_id


class AgentOverloadError(BaseAgentException):
    """智能体过载异常."""
    
    def __init__(self, message: str, agent_id: str = None, current_load: int = None, max_load: int = None):
        context = {}
        if current_load is not None:
            context["current_load"] = current_load
        if max_load is not None:
            context["max_load"] = max_load
        
        super().__init__(
            message=message,
            error_code=ErrorCode.AGENT_OVERLOAD,
            agent_id=agent_id,
            context=context,
            user_message="智能体当前负载过高，请稍后重试",
            suggestions=[
                "请求已加入队列，请稍等",
                "系统将分配其他可用智能体",
                "稍后重试"
            ]
        )
        self.current_load = current_load
        self.max_load = max_load


class AgentCollaborationError(BaseAgentException):
    """智能体协作异常."""
    
    def __init__(self, message: str, agent_id: str = None, collaboration_id: str = None):
        context = {}
        if collaboration_id:
            context["collaboration_id"] = collaboration_id
        
        super().__init__(
            message=message,
            error_code=ErrorCode.AGENT_COLLABORATION_ERROR,
            agent_id=agent_id,
            context=context,
            user_message="智能体协作出现问题，系统将重新尝试",
            suggestions=[
                "系统将重新分配协作任务",
                "请稍后重试",
                "联系技术支持"
            ]
        )
        self.collaboration_id = collaboration_id


class AgentNotFoundError(BaseAgentException):
    """智能体未找到异常."""
    
    def __init__(self, agent_id: str):
        message = f"Agent not found: {agent_id}"
        super().__init__(
            message=message,
            error_code=ErrorCode.AGENT_NOT_FOUND,
            agent_id=agent_id,
            user_message="请求的智能体不存在，系统将使用默认智能体",
            suggestions=[
                "系统将使用备用智能体",
                "请联系系统管理员",
                "检查智能体ID是否正确"
            ]
        )


class AgentUnavailableError(BaseAgentException):
    """智能体不可用异常."""
    
    def __init__(self, message: str, agent_id: str = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.AGENT_UNAVAILABLE,
            agent_id=agent_id,
            user_message="智能体暂时不可用，请稍后重试",
            suggestions=[
                "请稍后重试",
                "系统将尝试使用其他智能体",
                "联系技术支持"
            ]
        )


class AgentTimeoutError(BaseAgentException):
    """智能体超时异常."""
    
    def __init__(self, message: str, agent_id: str = None, timeout_seconds: int = None):
        context = {}
        if timeout_seconds is not None:
            context["timeout_seconds"] = timeout_seconds
        
        super().__init__(
            message=message,
            error_code=ErrorCode.AGENT_TIMEOUT,
            agent_id=agent_id,
            context=context,
            user_message="智能体响应超时，系统将重新尝试",
            suggestions=[
                "系统将重新尝试处理",
                "请检查网络连接",
                "如问题持续，请联系技术支持"
            ]
        )
        self.timeout_seconds = timeout_seconds


class AgentModelError(BaseAgentException):
    """智能体模型服务异常."""
    
    def __init__(self, message: str, agent_id: str = None, model_provider: str = None):
        context = {}
        if model_provider:
            context["model_provider"] = model_provider
        
        super().__init__(
            message=message,
            error_code=ErrorCode.AGENT_MODEL_ERROR,
            agent_id=agent_id,
            context=context,
            user_message="AI模型服务出现问题，系统将尝试使用备用模型",
            suggestions=[
                "系统将切换到备用模型",
                "请稍后重试",
                "联系技术支持"
            ]
        )
        self.model_provider = model_provider


class AgentRegistryError(BaseAgentException):
    """智能体注册表异常."""
    
    def __init__(self, message: str, agent_id: str = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.AGENT_REGISTRY_ERROR,
            agent_id=agent_id,
            severity=ErrorSeverity.HIGH,
            user_message="智能体注册服务出现问题，请联系系统管理员",
            suggestions=[
                "重启智能体服务",
                "检查注册表配置",
                "联系系统管理员"
            ]
        )


class AgentValidationError(BaseAgentException):
    """智能体验证异常."""
    
    def __init__(self, message: str, agent_id: str = None, validation_field: str = None):
        context = {}
        if validation_field:
            context["validation_field"] = validation_field
        
        super().__init__(
            message=message,
            error_code=ErrorCode.AGENT_VALIDATION_ERROR,
            agent_id=agent_id,
            context=context,
            user_message="智能体参数验证失败，请检查输入参数",
            suggestions=[
                "检查输入参数格式",
                "确保必需参数已提供",
                "参考API文档"
            ]
        )
        self.validation_field = validation_field