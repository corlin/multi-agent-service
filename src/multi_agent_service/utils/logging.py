"""结构化日志记录系统."""

import json
import logging
import sys
import time
from datetime import datetime
from typing import Any, Dict, Optional, Union
from uuid import uuid4
from pathlib import Path

from pydantic import BaseModel, Field, field_serializer


class LogLevel:
    """日志级别常量."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory:
    """日志分类常量."""
    API = "api"                    # API请求日志
    AGENT = "agent"               # 智能体日志
    WORKFLOW = "workflow"         # 工作流日志
    MODEL = "model"               # 模型服务日志
    SYSTEM = "system"             # 系统日志
    SECURITY = "security"         # 安全日志
    PERFORMANCE = "performance"   # 性能日志
    BUSINESS = "business"         # 业务日志


class LogEntry(BaseModel):
    """结构化日志条目模型."""
    
    log_id: str = Field(default_factory=lambda: str(uuid4()), description="日志ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    level: str = Field(..., description="日志级别")
    category: str = Field(..., description="日志分类")
    message: str = Field(..., description="日志消息")
    logger_name: str = Field(..., description="记录器名称")
    module: Optional[str] = Field(None, description="模块名称")
    function: Optional[str] = Field(None, description="函数名称")
    line_number: Optional[int] = Field(None, description="行号")
    context: Dict[str, Any] = Field(default_factory=dict, description="上下文信息")
    tags: list[str] = Field(default_factory=list, description="标签")
    correlation_id: Optional[str] = Field(None, description="关联ID")
    user_id: Optional[str] = Field(None, description="用户ID")
    request_id: Optional[str] = Field(None, description="请求ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    
    @field_serializer('timestamp')
    def serialize_timestamp(self, value: datetime) -> str:
        return value.isoformat()


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器."""
    
    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录."""
        # 获取基础信息
        log_entry = LogEntry(
            level=record.levelname,
            category=getattr(record, 'category', LogCategory.SYSTEM),
            message=record.getMessage(),
            logger_name=record.name,
            module=record.module if hasattr(record, 'module') else None,
            function=record.funcName if record.funcName != '<module>' else None,
            line_number=record.lineno
        )
        
        # 添加异常信息
        if record.exc_info:
            log_entry.context['exception'] = self.formatException(record.exc_info)
        
        # 添加额外的上下文信息
        if self.include_extra:
            extra_fields = [
                'correlation_id', 'user_id', 'request_id', 'session_id',
                'agent_id', 'workflow_id', 'model_provider', 'execution_time',
                'status_code', 'method', 'url', 'ip_address', 'user_agent'
            ]
            
            for field in extra_fields:
                if hasattr(record, field):
                    value = getattr(record, field)
                    if field in ['correlation_id', 'user_id', 'request_id', 'session_id']:
                        setattr(log_entry, field, value)
                    else:
                        log_entry.context[field] = value
            
            # 添加标签
            if hasattr(record, 'tags'):
                log_entry.tags = record.tags
        
        # 使用Pydantic的JSON序列化，它会处理datetime对象
        return log_entry.model_dump_json()


class MultiAgentLogger:
    """多智能体服务专用日志记录器."""
    
    def __init__(self, name: str, level: str = LogLevel.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level))
        self._setup_handlers()
    
    def _setup_handlers(self):
        """设置日志处理器."""
        # 清除现有处理器
        self.logger.handlers.clear()
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(console_handler)
        
        # 文件处理器（如果配置了日志目录）
        try:
            from ..config.settings import settings
            if hasattr(settings, 'log_dir') and settings.log_dir:
                log_dir = Path(settings.log_dir)
                log_dir.mkdir(parents=True, exist_ok=True)
                
                file_handler = logging.FileHandler(
                    log_dir / f"{self.logger.name}.log",
                    encoding='utf-8'
                )
                file_handler.setFormatter(StructuredFormatter())
                self.logger.addHandler(file_handler)
        except ImportError:
            pass  # 如果settings不可用，只使用控制台输出
    
    def _log(
        self,
        level: str,
        message: str,
        category: str = LogCategory.SYSTEM,
        **kwargs
    ):
        """内部日志记录方法."""
        extra = {
            'category': category,
            **kwargs
        }
        
        self.logger.log(getattr(logging, level), message, extra=extra)
    
    def debug(self, message: str, category: str = LogCategory.SYSTEM, **kwargs):
        """记录调试日志."""
        self._log(LogLevel.DEBUG, message, category, **kwargs)
    
    def info(self, message: str, category: str = LogCategory.SYSTEM, **kwargs):
        """记录信息日志."""
        self._log(LogLevel.INFO, message, category, **kwargs)
    
    def warning(self, message: str, category: str = LogCategory.SYSTEM, **kwargs):
        """记录警告日志."""
        self._log(LogLevel.WARNING, message, category, **kwargs)
    
    def error(self, message: str, category: str = LogCategory.SYSTEM, **kwargs):
        """记录错误日志."""
        self._log(LogLevel.ERROR, message, category, **kwargs)
    
    def critical(self, message: str, category: str = LogCategory.SYSTEM, **kwargs):
        """记录严重错误日志."""
        self._log(LogLevel.CRITICAL, message, category, **kwargs)
    
    # 专用日志方法
    def log_api_request(
        self,
        method: str,
        url: str,
        status_code: int,
        execution_time: float,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        **kwargs
    ):
        """记录API请求日志."""
        message = f"{method} {url} - {status_code} ({execution_time:.3f}s)"
        
        self._log(
            LogLevel.INFO,
            message,
            LogCategory.API,
            method=method,
            url=url,
            status_code=status_code,
            execution_time=execution_time,
            user_id=user_id,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            tags=["api_request"],
            **kwargs
        )
    
    def log_agent_execution(
        self,
        agent_id: str,
        agent_type: str,
        action: str,
        status: str,
        execution_time: float,
        request_id: Optional[str] = None,
        error_message: Optional[str] = None,
        **kwargs
    ):
        """记录智能体执行日志."""
        if status == "success":
            level = LogLevel.INFO
            message = f"Agent {agent_id} ({agent_type}) completed {action} in {execution_time:.3f}s"
        elif status == "error":
            level = LogLevel.ERROR
            message = f"Agent {agent_id} ({agent_type}) failed {action}: {error_message}"
        else:
            level = LogLevel.INFO
            message = f"Agent {agent_id} ({agent_type}) {status} {action}"
        
        self._log(
            level,
            message,
            LogCategory.AGENT,
            agent_id=agent_id,
            agent_type=agent_type,
            action=action,
            status=status,
            execution_time=execution_time,
            request_id=request_id,
            error_message=error_message,
            tags=["agent_execution"],
            **kwargs
        )
    
    def log_workflow_execution(
        self,
        workflow_id: str,
        workflow_type: str,
        step: str,
        status: str,
        execution_time: Optional[float] = None,
        participating_agents: Optional[list] = None,
        error_message: Optional[str] = None,
        **kwargs
    ):
        """记录工作流执行日志."""
        if status == "started":
            level = LogLevel.INFO
            message = f"Workflow {workflow_id} ({workflow_type}) started"
        elif status == "completed":
            level = LogLevel.INFO
            message = f"Workflow {workflow_id} ({workflow_type}) completed in {execution_time:.3f}s"
        elif status == "failed":
            level = LogLevel.ERROR
            message = f"Workflow {workflow_id} ({workflow_type}) failed at step {step}: {error_message}"
        else:
            level = LogLevel.INFO
            message = f"Workflow {workflow_id} ({workflow_type}) {status} at step {step}"
        
        self._log(
            level,
            message,
            LogCategory.WORKFLOW,
            workflow_id=workflow_id,
            workflow_type=workflow_type,
            step=step,
            status=status,
            execution_time=execution_time,
            participating_agents=participating_agents,
            error_message=error_message,
            tags=["workflow_execution"],
            **kwargs
        )
    
    def log_model_api_call(
        self,
        provider: str,
        model: str,
        status: str,
        execution_time: float,
        token_count: Optional[int] = None,
        cost: Optional[float] = None,
        error_message: Optional[str] = None,
        **kwargs
    ):
        """记录模型API调用日志."""
        if status == "success":
            level = LogLevel.INFO
            message = f"Model API call to {provider}/{model} completed in {execution_time:.3f}s"
            if token_count:
                message += f" ({token_count} tokens)"
            if cost:
                message += f" (${cost:.4f})"
        else:
            level = LogLevel.ERROR
            message = f"Model API call to {provider}/{model} failed: {error_message}"
        
        self._log(
            level,
            message,
            LogCategory.MODEL,
            provider=provider,
            model=model,
            status=status,
            execution_time=execution_time,
            token_count=token_count,
            cost=cost,
            error_message=error_message,
            tags=["model_api_call"],
            **kwargs
        )
    
    def log_performance_metric(
        self,
        metric_name: str,
        metric_value: Union[int, float],
        metric_unit: str,
        component: str,
        **kwargs
    ):
        """记录性能指标日志."""
        message = f"Performance metric: {metric_name} = {metric_value} {metric_unit} ({component})"
        
        # Extract tags from kwargs to avoid conflicts
        tags = kwargs.pop('tags', [])
        if not isinstance(tags, list):
            tags = []
        tags.append("performance_metric")
        
        self._log(
            LogLevel.INFO,
            message,
            LogCategory.PERFORMANCE,
            metric_name=metric_name,
            metric_value=metric_value,
            metric_unit=metric_unit,
            component=component,
            tags=tags,
            **kwargs
        )
    
    def log_security_event(
        self,
        event_type: str,
        severity: str,
        description: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        **kwargs
    ):
        """记录安全事件日志."""
        level = LogLevel.WARNING if severity == "medium" else LogLevel.ERROR
        message = f"Security event ({event_type}): {description}"
        
        self._log(
            level,
            message,
            LogCategory.SECURITY,
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            ip_address=ip_address,
            tags=["security_event"],
            **kwargs
        )


# 全局日志记录器实例
def get_logger(name: str, level: str = LogLevel.INFO) -> MultiAgentLogger:
    """获取日志记录器实例."""
    return MultiAgentLogger(name, level)


# 预定义的日志记录器
api_logger = get_logger("multi_agent_service.api")
agent_logger = get_logger("multi_agent_service.agent")
workflow_logger = get_logger("multi_agent_service.workflow")
model_logger = get_logger("multi_agent_service.model")
system_logger = get_logger("multi_agent_service.system")


class LogContext:
    """日志上下文管理器，用于在代码块中自动添加上下文信息."""
    
    def __init__(self, logger: MultiAgentLogger, **context):
        self.logger = logger
        self.context = context
        self.original_log = None
    
    def __enter__(self):
        # 保存原始的_log方法
        self.original_log = self.logger._log
        
        # 创建新的_log方法，自动添加上下文
        def _log_with_context(level, message, category=LogCategory.SYSTEM, **kwargs):
            merged_kwargs = {**self.context, **kwargs}
            return self.original_log(level, message, category, **merged_kwargs)
        
        # 替换_log方法
        self.logger._log = _log_with_context
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # 恢复原始的_log方法
        self.logger._log = self.original_log


class LoggingSystem:
    """日志系统，管理所有日志记录器."""
    
    def __init__(self):
        self.loggers: Dict[str, MultiAgentLogger] = {}
        self.is_initialized = False
        self.system_logger = get_logger("multi_agent_service.logging_system")
    
    async def initialize(self):
        """初始化日志系统."""
        self.is_initialized = True
        self.system_logger.info("Logging system initialized", category=LogCategory.SYSTEM)
        return True
    
    def get_logger(self, name: str, level: str = LogLevel.INFO) -> MultiAgentLogger:
        """获取或创建日志记录器."""
        if name not in self.loggers:
            self.loggers[name] = MultiAgentLogger(name, level)
        return self.loggers[name]
    
    def set_log_level(self, logger_name: str, level: str):
        """设置日志级别."""
        if logger_name in self.loggers:
            self.loggers[logger_name].logger.setLevel(getattr(logging, level))
    
    def set_global_log_level(self, level: str):
        """设置全局日志级别."""
        for logger in self.loggers.values():
            logger.logger.setLevel(getattr(logging, level))
    
    async def health_check(self) -> bool:
        """健康检查."""
        return self.is_initialized
    
    async def shutdown(self):
        """关闭日志系统."""
        for logger in self.loggers.values():
            for handler in logger.logger.handlers:
                handler.close()
        self.loggers.clear()
        self.is_initialized = False
        self.system_logger.info("Logging system shutdown", category=LogCategory.SYSTEM)