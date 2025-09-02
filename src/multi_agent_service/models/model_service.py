"""Model service related data models."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict, field_serializer

from .enums import ModelProvider


class ModelRequest(BaseModel):
    """模型请求基础模型."""
    
    request_id: str = Field(default_factory=lambda: str(uuid4()), description="请求ID")
    messages: List[Dict[str, str]] = Field(..., description="消息列表")
    model: Optional[str] = Field(None, description="模型名称")
    max_tokens: Optional[int] = Field(None, description="最大token数")
    temperature: Optional[float] = Field(None, description="温度参数")
    top_p: Optional[float] = Field(None, description="top_p参数")
    frequency_penalty: Optional[float] = Field(None, description="频率惩罚")
    presence_penalty: Optional[float] = Field(None, description="存在惩罚")
    stop: Optional[Union[str, List[str]]] = Field(None, description="停止词")
    stream: bool = Field(default=False, description="是否流式响应")
    user: Optional[str] = Field(None, description="用户标识")
    timeout: Optional[int] = Field(None, description="超时时间(秒)")
    
    model_config = ConfigDict(
        extra="allow"  # 允许额外字段以支持不同提供商的特殊参数
    )


class ModelResponse(BaseModel):
    """模型响应基础模型."""
    
    id: str = Field(..., description="响应ID")
    object: str = Field(default="chat.completion", description="对象类型")
    created: int = Field(..., description="创建时间戳")
    model: str = Field(..., description="使用的模型")
    choices: List[Dict[str, Any]] = Field(..., description="选择列表")
    usage: Dict[str, Any] = Field(..., description="使用统计")  # 改为Any以支持复杂结构
    provider: ModelProvider = Field(..., description="模型提供商")
    response_time: float = Field(..., description="响应时间(秒)")
    
    model_config = ConfigDict(
        extra="allow"  # 允许额外字段以支持不同提供商的特殊响应字段
    )


class ModelConfig(BaseModel):
    """模型配置模型."""
    
    provider: ModelProvider = Field(..., description="模型提供商")
    model_name: str = Field(..., description="模型名称")
    api_key: str = Field(..., description="API密钥")
    base_url: str = Field(..., description="API基础URL")
    max_tokens: int = Field(default=2048, description="默认最大token数")
    temperature: float = Field(default=0.7, description="默认温度参数")
    timeout: int = Field(default=30, description="请求超时时间(秒)")
    max_retries: int = Field(default=3, description="最大重试次数")
    retry_delay: float = Field(default=1.0, description="重试延迟(秒)")
    enabled: bool = Field(default=True, description="是否启用")
    priority: int = Field(default=1, description="优先级，数字越小优先级越高")
    
    model_config = ConfigDict(
        # 不序列化敏感信息
        json_schema_extra={
            "examples": [
                {
                    "provider": "qwen",
                    "model_name": "qwen-turbo",
                    "api_key": "sk-xxx",
                    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                    "max_tokens": 2048,
                    "temperature": 0.7,
                    "timeout": 30,
                    "max_retries": 3,
                    "retry_delay": 1.0,
                    "enabled": True,
                    "priority": 1
                }
            ]
        }
    )


class ModelError(BaseModel):
    """模型错误信息模型."""
    
    error_code: str = Field(..., description="错误代码")
    error_message: str = Field(..., description="错误消息")
    error_type: str = Field(..., description="错误类型")
    provider: ModelProvider = Field(..., description="出错的模型提供商")
    model_name: Optional[str] = Field(None, description="出错的模型名称")
    request_id: Optional[str] = Field(None, description="请求ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="错误时间戳")
    retry_after: Optional[int] = Field(None, description="建议重试间隔(秒)")
    
    @field_serializer('timestamp')
    def serialize_timestamp(self, value: datetime) -> str:
        return value.isoformat()


class ModelMetrics(BaseModel):
    """模型性能指标模型."""
    
    provider: ModelProvider = Field(..., description="模型提供商")
    model_name: str = Field(..., description="模型名称")
    total_requests: int = Field(default=0, description="总请求数")
    successful_requests: int = Field(default=0, description="成功请求数")
    failed_requests: int = Field(default=0, description="失败请求数")
    average_response_time: float = Field(default=0.0, description="平均响应时间(秒)")
    total_tokens_used: int = Field(default=0, description="总使用token数")
    last_request_time: Optional[float] = Field(None, description="最后请求时间戳")
    error_rate: float = Field(default=0.0, description="错误率")
    availability: float = Field(default=1.0, description="可用性")
    
    model_config = ConfigDict(
        extra="allow"
    )


class FailoverEvent(BaseModel):
    """故障转移事件模型."""
    
    event_id: str = Field(default_factory=lambda: str(uuid4()), description="事件ID")
    original_provider: ModelProvider = Field(..., description="原始提供商")
    fallback_provider: ModelProvider = Field(..., description="故障转移提供商")
    reason: str = Field(..., description="故障转移原因")
    request_id: str = Field(..., description="触发故障转移的请求ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="事件时间戳")
    success: bool = Field(..., description="故障转移是否成功")
    
    @field_serializer('timestamp')
    def serialize_timestamp(self, value: datetime) -> str:
        return value.isoformat()


# 导入枚举类
from enum import Enum


class LoadBalancingStrategy(str, Enum):
    """负载均衡策略枚举."""
    ROUND_ROBIN = "round_robin"  # 轮询
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"  # 加权轮询
    LEAST_CONNECTIONS = "least_connections"  # 最少连接
    RESPONSE_TIME = "response_time"  # 响应时间优先
    PRIORITY = "priority"  # 优先级优先