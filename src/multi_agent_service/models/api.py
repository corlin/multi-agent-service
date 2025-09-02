"""API request and response models."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict, field_serializer

from .enums import AgentType, IntentType, Priority, WorkflowType
from .base import AgentResponse, IntentResult, WorkflowState


class ChatCompletionRequest(BaseModel):
    """聊天完成请求模型 - OpenAI兼容格式."""
    
    messages: List[Dict[str, str]] = Field(..., description="消息列表")
    model: Optional[str] = Field(None, description="模型名称")
    max_tokens: Optional[int] = Field(None, description="最大token数")
    temperature: Optional[float] = Field(None, description="温度参数")
    stream: bool = Field(default=False, description="是否流式响应")
    user_id: Optional[str] = Field(None, description="用户ID")
    context: Dict[str, Any] = Field(default_factory=dict, description="上下文信息")


class ChatCompletionResponse(BaseModel):
    """聊天完成响应模型 - OpenAI兼容格式."""
    
    id: str = Field(..., description="响应ID")
    object: str = Field(default="chat.completion", description="对象类型")
    created: int = Field(..., description="创建时间戳")
    model: str = Field(..., description="使用的模型")
    choices: List[Dict[str, Any]] = Field(..., description="选择列表")
    usage: Dict[str, int] = Field(..., description="使用统计")
    agent_info: Optional[Dict[str, Any]] = Field(None, description="智能体信息")


class RouteRequest(BaseModel):
    """路由请求模型."""
    
    content: str = Field(..., description="请求内容")
    user_id: Optional[str] = Field(None, description="用户ID")
    context: Dict[str, Any] = Field(default_factory=dict, description="上下文信息")
    priority: Priority = Field(default=Priority.NORMAL, description="优先级")
    preferred_agents: Optional[List[AgentType]] = Field(None, description="首选智能体列表")


class RouteResponse(BaseModel):
    """路由响应模型."""
    
    intent_result: IntentResult = Field(..., description="意图识别结果")
    selected_agent: AgentType = Field(..., description="选择的智能体")
    routing_confidence: float = Field(..., description="路由置信度")
    alternative_agents: List[AgentType] = Field(default_factory=list, description="备选智能体")
    requires_collaboration: bool = Field(default=False, description="是否需要协作")
    estimated_processing_time: Optional[int] = Field(None, description="预估处理时间(秒)")


class WorkflowExecuteRequest(BaseModel):
    """工作流执行请求模型."""
    
    workflow_type: WorkflowType = Field(..., description="工作流类型")
    tasks: List[Dict[str, Any]] = Field(..., description="任务列表")
    participating_agents: List[AgentType] = Field(..., description="参与的智能体")
    context: Dict[str, Any] = Field(default_factory=dict, description="执行上下文")
    priority: Priority = Field(default=Priority.NORMAL, description="优先级")
    timeout: Optional[int] = Field(None, description="超时时间(秒)")


class WorkflowExecuteResponse(BaseModel):
    """工作流执行响应模型."""
    
    workflow_id: str = Field(..., description="工作流ID")
    status: str = Field(..., description="执行状态")
    message: str = Field(..., description="状态消息")
    estimated_completion_time: Optional[datetime] = Field(None, description="预估完成时间")
    
    @field_serializer('estimated_completion_time')
    def serialize_estimated_completion_time(self, value: Optional[datetime]) -> Optional[str]:
        return value.isoformat() if value else None


class AgentStatusRequest(BaseModel):
    """智能体状态查询请求模型."""
    
    agent_ids: Optional[List[str]] = Field(None, description="智能体ID列表，为空则查询所有")
    agent_types: Optional[List[AgentType]] = Field(None, description="智能体类型列表")
    include_metrics: bool = Field(default=False, description="是否包含性能指标")


class AgentStatusResponse(BaseModel):
    """智能体状态查询响应模型."""
    
    agents: List[Dict[str, Any]] = Field(..., description="智能体状态列表")
    total_count: int = Field(..., description="总数量")
    active_count: int = Field(..., description="活跃数量")
    timestamp: datetime = Field(default_factory=datetime.now, description="查询时间戳")
    
    @field_serializer('timestamp')
    def serialize_timestamp(self, value: datetime) -> str:
        return value.isoformat()


class WorkflowStatusRequest(BaseModel):
    """工作流状态查询请求模型."""
    
    workflow_id: str = Field(..., description="工作流ID")
    include_history: bool = Field(default=False, description="是否包含执行历史")
    include_agent_details: bool = Field(default=False, description="是否包含智能体详情")


class WorkflowStatusResponse(BaseModel):
    """工作流状态查询响应模型."""
    
    workflow_state: WorkflowState = Field(..., description="工作流状态")
    agent_responses: Optional[List[AgentResponse]] = Field(None, description="智能体响应列表")
    progress_percentage: float = Field(..., description="进度百分比")
    estimated_remaining_time: Optional[int] = Field(None, description="预估剩余时间(秒)")


class HealthCheckResponse(BaseModel):
    """健康检查响应模型."""
    
    status: str = Field(..., description="服务状态")
    timestamp: datetime = Field(default_factory=datetime.now, description="检查时间戳")
    version: str = Field(..., description="服务版本")
    uptime: int = Field(..., description="运行时间(秒)")
    agents_status: Dict[str, Any] = Field(..., description="智能体状态摘要")
    system_metrics: Dict[str, Any] = Field(default_factory=dict, description="系统指标")
    
    @field_serializer('timestamp')
    def serialize_timestamp(self, value: datetime) -> str:
        return value.isoformat()


class ErrorResponse(BaseModel):
    """错误响应模型."""
    
    error_code: str = Field(..., description="错误代码")
    error_message: str = Field(..., description="错误消息")
    error_details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    timestamp: datetime = Field(default_factory=datetime.now, description="错误时间戳")
    request_id: Optional[str] = Field(None, description="请求ID")
    
    @field_serializer('timestamp')
    def serialize_timestamp(self, value: datetime) -> str:
        return value.isoformat()