"""LangGraph图构建器基础框架."""

import json
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Type, Union

from langgraph.graph import StateGraph, END, START
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel

from ..models.workflow import (
    WorkflowGraph, 
    WorkflowNode, 
    WorkflowEdge, 
    NodeExecutionContext,
    WorkflowExecution
)
from ..models.enums import WorkflowType, AgentType


class GraphState(BaseModel):
    """图状态模型，用于在节点间传递数据."""
    
    execution_id: str
    current_step: int = 0
    total_steps: int = 0
    shared_data: Dict[str, Any] = {}
    node_results: Dict[str, Any] = {}
    messages: List[Dict[str, Any]] = []
    error: Optional[str] = None
    
    model_config = {"arbitrary_types_allowed": True}


class BaseNode(ABC):
    """节点基类，定义节点的基本接口."""
    
    def __init__(self, node_id: str, name: str, config: Optional[Dict[str, Any]] = None):
        self.node_id = node_id
        self.name = name
        self.config = config or {}
    
    @abstractmethod
    async def execute(self, context: NodeExecutionContext) -> Dict[str, Any]:
        """执行节点逻辑."""
        pass
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入数据."""
        return True
    
    def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """验证输出数据."""
        return True


class AgentNode(BaseNode):
    """智能体节点，封装智能体执行逻辑."""
    
    def __init__(
        self, 
        node_id: str, 
        name: str, 
        agent_type: AgentType,
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(node_id, name, config)
        self.agent_type = agent_type
    
    async def execute(self, context: NodeExecutionContext) -> Dict[str, Any]:
        """执行智能体节点."""
        # 这里将在后续任务中集成具体的智能体执行逻辑
        return {
            "node_id": self.node_id,
            "agent_type": self.agent_type.value,
            "result": f"Agent {self.agent_type.value} executed successfully",
            "context": context.input_data
        }


class ControlNode(BaseNode):
    """控制节点，用于流程控制."""
    
    def __init__(
        self, 
        node_id: str, 
        name: str, 
        control_type: str,
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(node_id, name, config)
        self.control_type = control_type
    
    async def execute(self, context: NodeExecutionContext) -> Dict[str, Any]:
        """执行控制节点."""
        if self.control_type == "start":
            return {"status": "started", "timestamp": context.timestamp.isoformat()}
        elif self.control_type == "end":
            return {"status": "completed", "timestamp": context.timestamp.isoformat()}
        elif self.control_type == "decision":
            # 决策逻辑
            condition = self.config.get("condition", "true")
            return {"decision": condition, "next_node": self.config.get("next_node")}
        else:
            return {"status": "unknown_control_type"}


class GraphBuilder:
    """LangGraph图构建器."""
    
    def __init__(self):
        self.nodes: Dict[str, BaseNode] = {}
        self.edges: List[WorkflowEdge] = []
        self.node_functions: Dict[str, Callable] = {}
        
    def add_node(self, node: BaseNode) -> 'GraphBuilder':
        """添加节点."""
        self.nodes[node.node_id] = node
        
        # 创建节点执行函数
        async def node_function(state: GraphState) -> GraphState:
            context = NodeExecutionContext(
                node_id=node.node_id,
                execution_id=state.execution_id,
                input_data=state.shared_data,
                shared_state=state.shared_data
            )
            
            try:
                result = await node.execute(context)
                state.node_results[node.node_id] = result
                state.shared_data.update(result.get("shared_data", {}))
                state.current_step += 1
            except Exception as e:
                state.error = str(e)
                state.node_results[node.node_id] = {"error": str(e)}
            
            return state
        
        self.node_functions[node.node_id] = node_function
        return self
    
    def add_edge(self, edge: WorkflowEdge) -> 'GraphBuilder':
        """添加边."""
        self.edges.append(edge)
        return self
    
    def add_conditional_edge(
        self, 
        source_node: str, 
        condition_func: Callable[[GraphState], str],
        edge_mapping: Dict[str, str]
    ) -> 'GraphBuilder':
        """添加条件边."""
        # 创建条件边
        for condition_value, target_node in edge_mapping.items():
            edge = WorkflowEdge(
                source_node=source_node,
                target_node=target_node,
                condition=condition_value
            )
            self.edges.append(edge)
        
        return self
    
    def build(self, workflow_type: WorkflowType) -> CompiledStateGraph:
        """构建LangGraph图."""
        # 创建StateGraph
        graph = StateGraph(GraphState)
        
        # 添加节点
        for node_id, node_func in self.node_functions.items():
            graph.add_node(node_id, node_func)
        
        # 添加边
        for edge in self.edges:
            if edge.condition:
                # 条件边需要特殊处理
                continue
            else:
                graph.add_edge(edge.source_node, edge.target_node)
        
        # 处理条件边
        conditional_edges = {}
        for edge in self.edges:
            if edge.condition:
                source = edge.source_node
                if source not in conditional_edges:
                    conditional_edges[source] = {}
                conditional_edges[source][edge.condition] = edge.target_node
        
        for source_node, conditions in conditional_edges.items():
            def condition_func(state: GraphState) -> str:
                # 简单的条件判断逻辑
                node_result = state.node_results.get(source_node, {})
                return node_result.get("decision", "default")
            
            graph.add_conditional_edges(source_node, condition_func, conditions)
        
        # 编译图
        return graph.compile()
    
    def from_workflow_graph(self, workflow_graph: WorkflowGraph) -> 'GraphBuilder':
        """从WorkflowGraph模型创建图构建器."""
        # 添加节点
        for node_model in workflow_graph.nodes:
            if node_model.agent_type:
                node = AgentNode(
                    node_id=node_model.node_id,
                    name=node_model.name,
                    agent_type=node_model.agent_type,
                    config=node_model.config
                )
            else:
                node = ControlNode(
                    node_id=node_model.node_id,
                    name=node_model.name,
                    control_type=node_model.node_type,
                    config=node_model.config
                )
            self.add_node(node)
        
        # 添加边
        for edge_model in workflow_graph.edges:
            self.add_edge(edge_model)
        
        return self
    
    def to_workflow_graph(self, name: str, workflow_type: WorkflowType) -> WorkflowGraph:
        """将图构建器转换为WorkflowGraph模型."""
        nodes = []
        for node_id, node in self.nodes.items():
            node_model = WorkflowNode(
                node_id=node_id,
                node_type=getattr(node, 'control_type', 'agent'),
                agent_type=getattr(node, 'agent_type', None),
                name=node.name,
                config=node.config
            )
            nodes.append(node_model)
        
        return WorkflowGraph(
            name=name,
            workflow_type=workflow_type,
            nodes=nodes,
            edges=self.edges
        )


class GraphSerializer:
    """图序列化器，用于图的序列化和反序列化."""
    
    @staticmethod
    def serialize_graph(workflow_graph: WorkflowGraph) -> str:
        """序列化工作流图为JSON字符串."""
        return workflow_graph.model_dump_json(indent=2)
    
    @staticmethod
    def deserialize_graph(json_str: str) -> WorkflowGraph:
        """从JSON字符串反序列化工作流图."""
        data = json.loads(json_str)
        return WorkflowGraph(**data)
    
    @staticmethod
    def serialize_to_dict(workflow_graph: WorkflowGraph) -> Dict[str, Any]:
        """序列化工作流图为字典."""
        return workflow_graph.model_dump()
    
    @staticmethod
    def deserialize_from_dict(data: Dict[str, Any]) -> WorkflowGraph:
        """从字典反序列化工作流图."""
        return WorkflowGraph(**data)


class GraphValidator:
    """图验证器，用于验证图的有效性."""
    
    @staticmethod
    def validate_graph(workflow_graph: WorkflowGraph) -> List[str]:
        """验证工作流图的有效性，返回错误列表."""
        errors = []
        
        # 检查节点
        if not workflow_graph.nodes:
            errors.append("图中没有节点")
        
        node_ids = {node.node_id for node in workflow_graph.nodes}
        
        # 检查边
        for edge in workflow_graph.edges:
            if edge.source_node not in node_ids:
                errors.append(f"边的源节点 {edge.source_node} 不存在")
            if edge.target_node not in node_ids:
                errors.append(f"边的目标节点 {edge.target_node} 不存在")
        
        # 检查入口点
        if workflow_graph.entry_point and workflow_graph.entry_point not in node_ids:
            errors.append(f"入口点 {workflow_graph.entry_point} 不存在")
        
        # 检查出口点
        for exit_point in workflow_graph.exit_points:
            if exit_point not in node_ids:
                errors.append(f"出口点 {exit_point} 不存在")
        
        # 检查图的连通性
        if len(workflow_graph.nodes) > 1 and not workflow_graph.edges:
            errors.append("图中有多个节点但没有边连接")
        
        return errors
    
    @staticmethod
    def is_valid_graph(workflow_graph: WorkflowGraph) -> bool:
        """检查工作流图是否有效."""
        return len(GraphValidator.validate_graph(workflow_graph)) == 0


# 工厂类用于创建不同类型的图构建器
class GraphBuilderFactory:
    """图构建器工厂."""
    
    @staticmethod
    def create_builder(workflow_type: WorkflowType) -> GraphBuilder:
        """根据工作流类型创建图构建器."""
        builder = GraphBuilder()
        
        # 根据不同的工作流类型进行初始化配置
        if workflow_type == WorkflowType.SEQUENTIAL:
            # 顺序执行模式的特殊配置
            pass
        elif workflow_type == WorkflowType.PARALLEL:
            # 并行执行模式的特殊配置
            pass
        elif workflow_type == WorkflowType.HIERARCHICAL:
            # 分层执行模式的特殊配置
            pass
        
        return builder