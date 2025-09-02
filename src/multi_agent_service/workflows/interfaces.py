"""抽象接口定义，用于节点、边和状态管理."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from ..models.workflow import (
    NodeExecutionContext, 
    WorkflowMessage, 
    WorkflowExecution
)
from ..models.enums import WorkflowStatus


@runtime_checkable
class NodeInterface(Protocol):
    """节点接口协议."""
    
    node_id: str
    name: str
    config: Dict[str, Any]
    
    async def execute(self, context: NodeExecutionContext) -> Dict[str, Any]:
        """执行节点逻辑."""
        ...
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入数据."""
        ...
    
    def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """验证输出数据."""
        ...


@runtime_checkable
class EdgeInterface(Protocol):
    """边接口协议."""
    
    edge_id: str
    source_node: str
    target_node: str
    condition: Optional[str]
    
    def evaluate_condition(self, context: Dict[str, Any]) -> bool:
        """评估边的条件."""
        ...


class StateManagerInterface(ABC):
    """状态管理器接口."""
    
    @abstractmethod
    async def get_state(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """获取执行状态."""
        pass
    
    @abstractmethod
    async def update_state(self, execution_id: str, state_data: Dict[str, Any]) -> bool:
        """更新执行状态."""
        pass
    
    @abstractmethod
    async def delete_state(self, execution_id: str) -> bool:
        """删除执行状态."""
        pass
    
    @abstractmethod
    async def persist_state(self, execution_id: str) -> bool:
        """持久化状态."""
        pass


class MessageBusInterface(ABC):
    """消息总线接口."""
    
    @abstractmethod
    async def send_message(self, message: WorkflowMessage) -> bool:
        """发送消息."""
        pass
    
    @abstractmethod
    async def receive_message(self, node_id: str) -> Optional[WorkflowMessage]:
        """接收消息."""
        pass
    
    @abstractmethod
    async def broadcast_message(self, message: WorkflowMessage, target_nodes: List[str]) -> bool:
        """广播消息."""
        pass
    
    @abstractmethod
    async def subscribe(self, node_id: str, message_types: List[str]) -> bool:
        """订阅消息类型."""
        pass


class WorkflowEngineInterface(ABC):
    """工作流引擎接口."""
    
    @abstractmethod
    async def execute_workflow(self, execution: WorkflowExecution) -> WorkflowExecution:
        """执行工作流."""
        pass
    
    @abstractmethod
    async def pause_workflow(self, execution_id: str) -> bool:
        """暂停工作流."""
        pass
    
    @abstractmethod
    async def resume_workflow(self, execution_id: str) -> bool:
        """恢复工作流."""
        pass
    
    @abstractmethod
    async def cancel_workflow(self, execution_id: str) -> bool:
        """取消工作流."""
        pass
    
    @abstractmethod
    async def get_workflow_status(self, execution_id: str) -> Optional[WorkflowStatus]:
        """获取工作流状态."""
        pass


class GraphExecutorInterface(ABC):
    """图执行器接口."""
    
    @abstractmethod
    async def execute_node(self, node_id: str, context: NodeExecutionContext) -> Dict[str, Any]:
        """执行单个节点."""
        pass
    
    @abstractmethod
    async def execute_sequential(self, node_ids: List[str], context: NodeExecutionContext) -> List[Dict[str, Any]]:
        """顺序执行多个节点."""
        pass
    
    @abstractmethod
    async def execute_parallel(self, node_ids: List[str], context: NodeExecutionContext) -> List[Dict[str, Any]]:
        """并行执行多个节点."""
        pass
    
    @abstractmethod
    async def execute_conditional(self, condition: str, context: NodeExecutionContext) -> str:
        """执行条件判断."""
        pass


class GraphBuilderInterface(ABC):
    """图构建器接口."""
    
    @abstractmethod
    def add_node(self, node: NodeInterface) -> 'GraphBuilderInterface':
        """添加节点."""
        pass
    
    @abstractmethod
    def add_edge(self, edge: EdgeInterface) -> 'GraphBuilderInterface':
        """添加边."""
        pass
    
    @abstractmethod
    def build(self) -> Any:
        """构建图."""
        pass
    
    @abstractmethod
    def validate(self) -> List[str]:
        """验证图的有效性."""
        pass


class SerializerInterface(ABC):
    """序列化器接口."""
    
    @abstractmethod
    def serialize(self, obj: Any) -> str:
        """序列化对象."""
        pass
    
    @abstractmethod
    def deserialize(self, data: str) -> Any:
        """反序列化对象."""
        pass


class ValidatorInterface(ABC):
    """验证器接口."""
    
    @abstractmethod
    def validate(self, obj: Any) -> List[str]:
        """验证对象，返回错误列表."""
        pass
    
    @abstractmethod
    def is_valid(self, obj: Any) -> bool:
        """检查对象是否有效."""
        pass


# 回调接口
class NodeExecutionCallback(Protocol):
    """节点执行回调接口."""
    
    async def on_node_start(self, node_id: str, context: NodeExecutionContext) -> None:
        """节点开始执行时的回调."""
        ...
    
    async def on_node_complete(self, node_id: str, result: Dict[str, Any]) -> None:
        """节点执行完成时的回调."""
        ...
    
    async def on_node_error(self, node_id: str, error: Exception) -> None:
        """节点执行出错时的回调."""
        ...


class WorkflowExecutionCallback(Protocol):
    """工作流执行回调接口."""
    
    async def on_workflow_start(self, execution_id: str) -> None:
        """工作流开始执行时的回调."""
        ...
    
    async def on_workflow_complete(self, execution_id: str, result: Dict[str, Any]) -> None:
        """工作流执行完成时的回调."""
        ...
    
    async def on_workflow_error(self, execution_id: str, error: Exception) -> None:
        """工作流执行出错时的回调."""
        ...
    
    async def on_workflow_pause(self, execution_id: str) -> None:
        """工作流暂停时的回调."""
        ...
    
    async def on_workflow_resume(self, execution_id: str) -> None:
        """工作流恢复时的回调."""
        ...


# 扩展接口
class PluginInterface(ABC):
    """插件接口."""
    
    @abstractmethod
    def get_name(self) -> str:
        """获取插件名称."""
        pass
    
    @abstractmethod
    def get_version(self) -> str:
        """获取插件版本."""
        pass
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化插件."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> bool:
        """清理插件资源."""
        pass


class MonitoringInterface(ABC):
    """监控接口."""
    
    @abstractmethod
    async def record_metric(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """记录指标."""
        pass
    
    @abstractmethod
    async def record_event(self, event_name: str, data: Dict[str, Any]) -> None:
        """记录事件."""
        pass
    
    @abstractmethod
    async def get_metrics(self, metric_name: str, time_range: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """获取指标数据."""
        pass