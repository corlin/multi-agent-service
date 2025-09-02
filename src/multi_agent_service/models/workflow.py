"""Workflow-specific data models for LangGraph integration."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field, field_serializer

from .enums import WorkflowType, WorkflowStatus, AgentType


class WorkflowNode(BaseModel):
    """工作流节点模型."""
    
    node_id: str = Field(default_factory=lambda: str(uuid4()), description="节点ID")
    node_type: str = Field(..., description="节点类型")
    agent_type: Optional[AgentType] = Field(None, description="关联的智能体类型")
    name: str = Field(..., description="节点名称")
    description: Optional[str] = Field(None, description="节点描述")
    config: Dict[str, Any] = Field(default_factory=dict, description="节点配置")
    input_schema: Dict[str, Any] = Field(default_factory=dict, description="输入模式")
    output_schema: Dict[str, Any] = Field(default_factory=dict, description="输出模式")


class WorkflowEdge(BaseModel):
    """工作流边模型."""
    
    edge_id: str = Field(default_factory=lambda: str(uuid4()), description="边ID")
    source_node: str = Field(..., description="源节点ID")
    target_node: str = Field(..., description="目标节点ID")
    condition: Optional[str] = Field(None, description="条件表达式")
    weight: float = Field(default=1.0, description="权重")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class WorkflowGraph(BaseModel):
    """工作流图模型."""
    
    graph_id: str = Field(default_factory=lambda: str(uuid4()), description="图ID")
    name: str = Field(..., description="图名称")
    workflow_type: WorkflowType = Field(..., description="工作流类型")
    nodes: List[WorkflowNode] = Field(default_factory=list, description="节点列表")
    edges: List[WorkflowEdge] = Field(default_factory=list, description="边列表")
    entry_point: Optional[str] = Field(None, description="入口节点ID")
    exit_points: List[str] = Field(default_factory=list, description="出口节点ID列表")
    config: Dict[str, Any] = Field(default_factory=dict, description="图配置")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    
    @field_serializer('created_at')
    def serialize_created_at(self, value: datetime) -> str:
        return value.isoformat()


class WorkflowExecution(BaseModel):
    """工作流执行模型."""
    
    execution_id: str = Field(default_factory=lambda: str(uuid4()), description="执行ID")
    graph_id: str = Field(..., description="图ID")
    status: WorkflowStatus = Field(default=WorkflowStatus.PENDING, description="执行状态")
    current_node: Optional[str] = Field(None, description="当前节点ID")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="输入数据")
    output_data: Dict[str, Any] = Field(default_factory=dict, description="输出数据")
    node_results: Dict[str, Any] = Field(default_factory=dict, description="节点执行结果")
    error_message: Optional[str] = Field(None, description="错误信息")
    start_time: datetime = Field(default_factory=datetime.now, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    
    @field_serializer('start_time', 'end_time')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        return value.isoformat() if value else None


class NodeExecutionContext(BaseModel):
    """节点执行上下文模型."""
    
    node_id: str = Field(..., description="节点ID")
    execution_id: str = Field(..., description="执行ID")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="输入数据")
    shared_state: Dict[str, Any] = Field(default_factory=dict, description="共享状态")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    
    @field_serializer('timestamp')
    def serialize_timestamp(self, value: datetime) -> str:
        return value.isoformat()


class WorkflowMessage(BaseModel):
    """工作流消息模型."""
    
    message_id: str = Field(default_factory=lambda: str(uuid4()), description="消息ID")
    sender_node: str = Field(..., description="发送节点ID")
    receiver_node: Optional[str] = Field(None, description="接收节点ID")
    message_type: str = Field(..., description="消息类型")
    content: Dict[str, Any] = Field(default_factory=dict, description="消息内容")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    
    @field_serializer('timestamp')
    def serialize_timestamp(self, value: datetime) -> str:
        return value.isoformat()


class WorkflowTemplate(BaseModel):
    """工作流模板模型."""
    
    template_id: str = Field(default_factory=lambda: str(uuid4()), description="模板ID")
    name: str = Field(..., description="模板名称")
    description: str = Field(..., description="模板描述")
    workflow_type: WorkflowType = Field(..., description="工作流类型")
    template_config: Dict[str, Any] = Field(default_factory=dict, description="模板配置")
    node_templates: List[Dict[str, Any]] = Field(default_factory=list, description="节点模板")
    edge_templates: List[Dict[str, Any]] = Field(default_factory=list, description="边模板")
    version: str = Field(default="1.0.0", description="版本号")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    
    @field_serializer('created_at')
    def serialize_created_at(self, value: datetime) -> str:
        return value.isoformat()