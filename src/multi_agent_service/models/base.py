"""Base data models for the multi-agent service."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict, field_serializer

from .enums import AgentType, IntentType, Priority, WorkflowStatus, AgentStatus


class Entity(BaseModel):
    """实体模型，用于意图识别中的实体提取."""
    
    name: str = Field(..., description="实体名称")
    value: str = Field(..., description="实体值")
    confidence: float = Field(..., ge=0.0, le=1.0, description="置信度")
    entity_type: str = Field(..., description="实体类型")


class Action(BaseModel):
    """动作模型，表示智能体可以执行的动作."""
    
    action_type: str = Field(..., description="动作类型")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="动作参数")
    description: Optional[str] = Field(None, description="动作描述")


class UserRequest(BaseModel):
    """用户请求模型."""
    
    request_id: str = Field(default_factory=lambda: str(uuid4()), description="请求ID")
    user_id: Optional[str] = Field(None, description="用户ID")
    content: str = Field(..., description="请求内容")
    context: Dict[str, Any] = Field(default_factory=dict, description="请求上下文")
    timestamp: datetime = Field(default_factory=datetime.now, description="请求时间戳")
    priority: Priority = Field(default=Priority.NORMAL, description="优先级")
    
    @field_serializer('timestamp')
    def serialize_timestamp(self, value: datetime) -> str:
        return value.isoformat()


class IntentResult(BaseModel):
    """意图识别结果模型."""
    
    intent_type: IntentType = Field(..., description="意图类型")
    confidence: float = Field(..., ge=0.0, le=1.0, description="置信度")
    entities: List[Entity] = Field(default_factory=list, description="提取的实体列表")
    suggested_agents: List[AgentType] = Field(default_factory=list, description="建议的智能体列表")
    requires_collaboration: bool = Field(default=False, description="是否需要协作")
    reasoning: Optional[str] = Field(None, description="推理过程")


class AgentResponse(BaseModel):
    """智能体响应模型."""
    
    agent_id: str = Field(..., description="智能体ID")
    agent_type: AgentType = Field(..., description="智能体类型")
    response_content: str = Field(..., description="响应内容")
    confidence: float = Field(..., ge=0.0, le=1.0, description="置信度")
    next_actions: List[Action] = Field(default_factory=list, description="下一步动作")
    collaboration_needed: bool = Field(default=False, description="是否需要协作")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间戳")
    
    @field_serializer('timestamp')
    def serialize_timestamp(self, value: datetime) -> str:
        return value.isoformat()


class ExecutionStep(BaseModel):
    """执行步骤模型."""
    
    step_id: str = Field(default_factory=lambda: str(uuid4()), description="步骤ID")
    agent_id: str = Field(..., description="执行智能体ID")
    action: Action = Field(..., description="执行的动作")
    result: Dict[str, Any] = Field(default_factory=dict, description="执行结果")
    status: str = Field(..., description="执行状态")
    start_time: datetime = Field(default_factory=datetime.now, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    error_message: Optional[str] = Field(None, description="错误信息")
    
    @field_serializer('start_time', 'end_time')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        return value.isoformat() if value else None


class WorkflowState(BaseModel):
    """工作流状态模型."""
    
    workflow_id: str = Field(default_factory=lambda: str(uuid4()), description="工作流ID")
    status: WorkflowStatus = Field(default=WorkflowStatus.PENDING, description="工作流状态")
    current_step: int = Field(default=0, description="当前步骤")
    total_steps: int = Field(default=0, description="总步骤数")
    participating_agents: List[str] = Field(default_factory=list, description="参与的智能体ID列表")
    execution_history: List[ExecutionStep] = Field(default_factory=list, description="执行历史")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    
    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, value: datetime) -> str:
        return value.isoformat()


class AgentInfo(BaseModel):
    """智能体信息模型."""
    
    agent_id: str = Field(..., description="智能体ID")
    agent_type: AgentType = Field(..., description="智能体类型")
    name: str = Field(..., description="智能体名称")
    description: str = Field(..., description="智能体描述")
    status: AgentStatus = Field(default=AgentStatus.IDLE, description="智能体状态")
    capabilities: List[str] = Field(default_factory=list, description="能力列表")
    current_load: int = Field(default=0, description="当前负载")
    max_load: int = Field(default=10, description="最大负载")
    last_active: datetime = Field(default_factory=datetime.now, description="最后活跃时间")
    
    @field_serializer('last_active')
    def serialize_last_active(self, value: datetime) -> str:
        return value.isoformat()


class CollaborationResult(BaseModel):
    """协作结果模型."""
    
    collaboration_id: str = Field(default_factory=lambda: str(uuid4()), description="协作ID")
    participating_agents: List[str] = Field(..., description="参与协作的智能体ID列表")
    final_result: str = Field(..., description="最终结果")
    individual_responses: List[AgentResponse] = Field(default_factory=list, description="各智能体的响应")
    consensus_reached: bool = Field(default=False, description="是否达成共识")
    resolution_method: Optional[str] = Field(None, description="解决方法")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    
    @field_serializer('timestamp')
    def serialize_timestamp(self, value: datetime) -> str:
        return value.isoformat()


class Conflict(BaseModel):
    """冲突模型."""
    
    conflict_id: str = Field(default_factory=lambda: str(uuid4()), description="冲突ID")
    conflicting_agents: List[str] = Field(..., description="冲突的智能体ID列表")
    conflict_type: str = Field(..., description="冲突类型")
    description: str = Field(..., description="冲突描述")
    proposed_solutions: List[str] = Field(default_factory=list, description="提议的解决方案")
    resolution: Optional[str] = Field(None, description="解决方案")
    resolved: bool = Field(default=False, description="是否已解决")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    
    @field_serializer('timestamp')
    def serialize_timestamp(self, value: datetime) -> str:
        return value.isoformat()