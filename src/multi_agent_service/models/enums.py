"""Enums and constants for the multi-agent service."""

from enum import Enum


class AgentType(str, Enum):
    """智能体类型枚举."""
    COORDINATOR = "coordinator"  # 智能体总协调员
    SALES = "sales"  # 销售代表智能体
    MANAGER = "manager"  # 公司管理者智能体
    FIELD_SERVICE = "field_service"  # 现场服务人员智能体
    CUSTOMER_SUPPORT = "customer_support"  # 客服专员智能体


class IntentType(str, Enum):
    """意图类型枚举."""
    SALES_INQUIRY = "sales_inquiry"  # 销售咨询
    CUSTOMER_SUPPORT = "customer_support"  # 客户支持
    TECHNICAL_SERVICE = "technical_service"  # 技术服务
    MANAGEMENT_DECISION = "management_decision"  # 管理决策
    GENERAL_INQUIRY = "general_inquiry"  # 一般咨询
    COLLABORATION_REQUIRED = "collaboration_required"  # 需要协作


class WorkflowType(str, Enum):
    """工作流类型枚举."""
    SEQUENTIAL = "sequential"  # 顺序执行
    PARALLEL = "parallel"  # 并行执行
    HIERARCHICAL = "hierarchical"  # 分层执行


class WorkflowStatus(str, Enum):
    """工作流状态枚举."""
    PENDING = "pending"  # 等待中
    RUNNING = "running"  # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 执行失败
    CANCELLED = "cancelled"  # 已取消


class AgentStatus(str, Enum):
    """智能体状态枚举."""
    ACTIVE = "active"  # 活跃
    IDLE = "idle"  # 空闲
    BUSY = "busy"  # 忙碌
    ERROR = "error"  # 错误
    OFFLINE = "offline"  # 离线


class Priority(str, Enum):
    """优先级枚举."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ModelProvider(str, Enum):
    """模型服务提供商枚举."""
    QWEN = "qwen"  # 通义千问
    DEEPSEEK = "deepseek"  # DeepSeek
    GLM = "glm"  # 智谱AI
    OPENAI = "openai"  # OpenAI
    CUSTOM = "custom"  # 自定义兼容服务


# 常量定义
DEFAULT_MAX_TOKENS = 2048
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TIMEOUT = 30  # 秒
MAX_RETRY_ATTEMPTS = 3
DEFAULT_CONFIDENCE_THRESHOLD = 0.8