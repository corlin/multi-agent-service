"""顺序执行模式实现."""

import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime

from langgraph.graph import StateGraph, END, START
from langgraph.graph.state import CompiledStateGraph

from .graph_builder import GraphBuilder, GraphState, BaseNode
from .interfaces import WorkflowEngineInterface, GraphExecutorInterface
from ..models.workflow import (
    WorkflowGraph,
    WorkflowExecution,
    NodeExecutionContext,
    WorkflowNode,
    WorkflowEdge
)
from ..models.enums import WorkflowType, WorkflowStatus, AgentType


class SequentialGraphBuilder(GraphBuilder):
    """顺序执行图构建器."""
    
    def __init__(self):
        super().__init__()
        self.execution_order: List[str] = []
    
    def set_execution_order(self, node_ids: List[str]) -> 'SequentialGraphBuilder':
        """设置节点执行顺序."""
        self.execution_order = node_ids
        return self
    
    def build_sequential_graph(self) -> CompiledStateGraph:
        """构建顺序执行图."""
        if not self.execution_order:
            # 如果没有设置执行顺序，尝试从边推导
            self.execution_order = self._derive_execution_order()
        
        # 创建StateGraph
        graph = StateGraph(GraphState)
        
        # 添加所有节点
        for node_id, node_func in self.node_functions.items():
            graph.add_node(node_id, node_func)
        
        # 设置入口点
        if self.execution_order:
            graph.set_entry_point(self.execution_order[0])
            
            # 按顺序连接节点
            for i in range(len(self.execution_order) - 1):
                current_node = self.execution_order[i]
                next_node = self.execution_order[i + 1]
                graph.add_edge(current_node, next_node)
            
            # 最后一个节点连接到END
            graph.add_edge(self.execution_order[-1], END)
        
        return graph.compile()
    
    def _derive_execution_order(self) -> List[str]:
        """从边推导执行顺序."""
        if not self.edges:
            return list(self.nodes.keys())
        
        # 构建邻接表
        graph = {}
        in_degree = {}
        
        # 初始化
        for node_id in self.nodes.keys():
            graph[node_id] = []
            in_degree[node_id] = 0
        
        # 构建图
        for edge in self.edges:
            if edge.source_node in graph and edge.target_node in in_degree:
                graph[edge.source_node].append(edge.target_node)
                in_degree[edge.target_node] += 1
        
        # 拓扑排序
        queue = [node for node, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            node = queue.pop(0)
            result.append(node)
            
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return result if len(result) == len(self.nodes) else list(self.nodes.keys())


class SequentialExecutor(GraphExecutorInterface):
    """顺序执行器."""
    
    def __init__(self):
        self.execution_history: List[Dict[str, Any]] = []
    
    async def execute_node(self, node_id: str, context: NodeExecutionContext) -> Dict[str, Any]:
        """执行单个节点."""
        start_time = datetime.now()
        
        try:
            # 这里应该调用实际的节点执行逻辑
            # 暂时返回模拟结果
            result = {
                "node_id": node_id,
                "status": "completed",
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "output": f"Node {node_id} executed successfully"
            }
            
            self.execution_history.append(result)
            return result
            
        except Exception as e:
            error_result = {
                "node_id": node_id,
                "status": "failed",
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "error": str(e)
            }
            
            self.execution_history.append(error_result)
            raise
    
    async def execute_sequential(self, node_ids: List[str], context: NodeExecutionContext) -> List[Dict[str, Any]]:
        """顺序执行多个节点."""
        results = []
        
        for i, node_id in enumerate(node_ids):
            # 更新上下文
            step_context = NodeExecutionContext(
                node_id=node_id,
                execution_id=context.execution_id,
                input_data=context.input_data,
                shared_state=context.shared_state,
                metadata={
                    **context.metadata,
                    "step": i + 1,
                    "total_steps": len(node_ids),
                    "previous_results": results
                }
            )
            
            try:
                result = await self.execute_node(node_id, step_context)
                results.append(result)
                
                # 更新共享状态
                if "shared_data" in result:
                    context.shared_state.update(result["shared_data"])
                
            except Exception as e:
                # 顺序执行中如果某个节点失败，停止执行
                error_result = {
                    "node_id": node_id,
                    "status": "failed",
                    "error": str(e),
                    "step": i + 1
                }
                results.append(error_result)
                break
        
        return results
    
    async def execute_parallel(self, node_ids: List[str], context: NodeExecutionContext) -> List[Dict[str, Any]]:
        """并行执行多个节点（在顺序执行器中不使用）."""
        raise NotImplementedError("Sequential executor does not support parallel execution")
    
    async def execute_conditional(self, condition: str, context: NodeExecutionContext) -> str:
        """执行条件判断."""
        # 简单的条件判断逻辑
        if condition == "true":
            return "true"
        elif condition == "false":
            return "false"
        else:
            # 可以扩展更复杂的条件判断逻辑
            return "default"


class SequentialWorkflowEngine(WorkflowEngineInterface):
    """顺序执行工作流引擎."""
    
    def __init__(self):
        self.executor = SequentialExecutor()
        self.active_executions: Dict[str, WorkflowExecution] = {}
    
    async def execute_workflow(self, execution: WorkflowExecution) -> WorkflowExecution:
        """执行顺序工作流."""
        execution.status = WorkflowStatus.RUNNING
        execution.start_time = datetime.now()
        
        self.active_executions[execution.execution_id] = execution
        
        try:
            # 获取工作流图（这里需要从存储中获取，暂时模拟）
            workflow_graph = await self._get_workflow_graph(execution.graph_id)
            
            if not workflow_graph:
                raise ValueError(f"Workflow graph {execution.graph_id} not found")
            
            # 构建执行顺序
            node_order = self._build_execution_order(workflow_graph)
            
            # 创建执行上下文
            context = NodeExecutionContext(
                node_id="",  # 将在执行时设置
                execution_id=execution.execution_id,
                input_data=execution.input_data,
                shared_state={}
            )
            
            # 顺序执行节点
            results = await self.executor.execute_sequential(node_order, context)
            
            # 更新执行结果
            execution.node_results = {result["node_id"]: result for result in results}
            execution.output_data = context.shared_state
            
            # 检查是否所有节点都成功执行
            failed_nodes = [r for r in results if r.get("status") == "failed"]
            if failed_nodes:
                execution.status = WorkflowStatus.FAILED
                execution.error_message = f"Nodes failed: {[n['node_id'] for n in failed_nodes]}"
            else:
                execution.status = WorkflowStatus.COMPLETED
            
            execution.end_time = datetime.now()
            
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.error_message = str(e)
            execution.end_time = datetime.now()
        
        finally:
            # 清理活跃执行记录
            if execution.execution_id in self.active_executions:
                del self.active_executions[execution.execution_id]
        
        return execution
    
    async def pause_workflow(self, execution_id: str) -> bool:
        """暂停工作流（顺序执行不支持暂停）."""
        return False
    
    async def resume_workflow(self, execution_id: str) -> bool:
        """恢复工作流（顺序执行不支持恢复）."""
        return False
    
    async def cancel_workflow(self, execution_id: str) -> bool:
        """取消工作流."""
        if execution_id in self.active_executions:
            execution = self.active_executions[execution_id]
            execution.status = WorkflowStatus.CANCELLED
            execution.end_time = datetime.now()
            del self.active_executions[execution_id]
            return True
        return False
    
    async def get_workflow_status(self, execution_id: str) -> Optional[WorkflowStatus]:
        """获取工作流状态."""
        if execution_id in self.active_executions:
            return self.active_executions[execution_id].status
        return None
    
    async def _get_workflow_graph(self, graph_id: str) -> Optional[WorkflowGraph]:
        """获取工作流图（模拟实现）."""
        # 这里应该从实际的存储中获取图定义
        # 暂时返回一个示例图
        return WorkflowGraph(
            graph_id=graph_id,
            name="Sequential Workflow",
            workflow_type=WorkflowType.SEQUENTIAL,
            nodes=[
                WorkflowNode(
                    node_id="start",
                    node_type="start",
                    name="Start Node"
                ),
                WorkflowNode(
                    node_id="process",
                    node_type="agent",
                    agent_type=AgentType.SALES,
                    name="Process Node"
                ),
                WorkflowNode(
                    node_id="end",
                    node_type="end",
                    name="End Node"
                )
            ],
            edges=[
                WorkflowEdge(source_node="start", target_node="process"),
                WorkflowEdge(source_node="process", target_node="end")
            ]
        )
    
    def _build_execution_order(self, workflow_graph: WorkflowGraph) -> List[str]:
        """构建执行顺序."""
        # 简单的拓扑排序
        in_degree = {node.node_id: 0 for node in workflow_graph.nodes}
        graph = {node.node_id: [] for node in workflow_graph.nodes}
        
        # 构建邻接表和入度
        for edge in workflow_graph.edges:
            graph[edge.source_node].append(edge.target_node)
            in_degree[edge.target_node] += 1
        
        # 拓扑排序
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            node_id = queue.pop(0)
            result.append(node_id)
            
            for neighbor in graph[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return result


class SequentialWorkflowFactory:
    """顺序工作流工厂类."""
    
    @staticmethod
    def create_simple_sequential_workflow(
        node_configs: List[Dict[str, Any]],
        workflow_name: str = "Sequential Workflow"
    ) -> WorkflowGraph:
        """创建简单的顺序工作流."""
        nodes = []
        edges = []
        
        # 创建节点
        for i, config in enumerate(node_configs):
            node = WorkflowNode(
                node_id=config.get("node_id", f"node_{i}"),
                node_type=config.get("node_type", "agent"),
                agent_type=config.get("agent_type"),
                name=config.get("name", f"Node {i}"),
                description=config.get("description"),
                config=config.get("config", {})
            )
            nodes.append(node)
        
        # 创建顺序边
        for i in range(len(nodes) - 1):
            edge = WorkflowEdge(
                source_node=nodes[i].node_id,
                target_node=nodes[i + 1].node_id
            )
            edges.append(edge)
        
        return WorkflowGraph(
            name=workflow_name,
            workflow_type=WorkflowType.SEQUENTIAL,
            nodes=nodes,
            edges=edges,
            entry_point=nodes[0].node_id if nodes else None,
            exit_points=[nodes[-1].node_id] if nodes else []
        )
    
    @staticmethod
    def create_agent_pipeline(
        agent_types: List[AgentType],
        workflow_name: str = "Agent Pipeline"
    ) -> WorkflowGraph:
        """创建智能体流水线."""
        node_configs = []
        
        # 添加开始节点
        node_configs.append({
            "node_id": "start",
            "node_type": "start",
            "name": "Start"
        })
        
        # 添加智能体节点
        for i, agent_type in enumerate(agent_types):
            node_configs.append({
                "node_id": f"agent_{i}",
                "node_type": "agent",
                "agent_type": agent_type,
                "name": f"{agent_type.value.title()} Agent"
            })
        
        # 添加结束节点
        node_configs.append({
            "node_id": "end",
            "node_type": "end",
            "name": "End"
        })
        
        return SequentialWorkflowFactory.create_simple_sequential_workflow(
            node_configs, workflow_name
        )


# 状态管理和数据传递工具
class SequentialStateManager:
    """顺序执行状态管理器."""
    
    def __init__(self):
        self.state_store: Dict[str, Dict[str, Any]] = {}
    
    async def save_step_state(
        self, 
        execution_id: str, 
        step: int, 
        node_id: str, 
        state_data: Dict[str, Any]
    ) -> None:
        """保存步骤状态."""
        if execution_id not in self.state_store:
            self.state_store[execution_id] = {}
        
        self.state_store[execution_id][f"step_{step}"] = {
            "node_id": node_id,
            "state_data": state_data,
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_step_state(
        self, 
        execution_id: str, 
        step: int
    ) -> Optional[Dict[str, Any]]:
        """获取步骤状态."""
        if execution_id in self.state_store:
            return self.state_store[execution_id].get(f"step_{step}")
        return None
    
    async def get_execution_state(self, execution_id: str) -> Dict[str, Any]:
        """获取整个执行的状态."""
        return self.state_store.get(execution_id, {})
    
    async def clear_execution_state(self, execution_id: str) -> None:
        """清理执行状态."""
        if execution_id in self.state_store:
            del self.state_store[execution_id]


class DataPassingManager:
    """数据传递管理器."""
    
    @staticmethod
    def prepare_next_step_input(
        current_result: Dict[str, Any],
        shared_state: Dict[str, Any],
        next_node_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """准备下一步的输入数据."""
        next_input = {}
        
        # 从当前结果中提取输出数据
        if "output" in current_result:
            next_input.update(current_result["output"])
        
        # 从共享状态中获取数据
        next_input.update(shared_state)
        
        # 应用节点特定的数据映射
        if "input_mapping" in next_node_config:
            mapping = next_node_config["input_mapping"]
            mapped_input = {}
            for target_key, source_key in mapping.items():
                if source_key in next_input:
                    mapped_input[target_key] = next_input[source_key]
            next_input.update(mapped_input)
        
        return next_input
    
    @staticmethod
    def extract_shared_data(
        node_result: Dict[str, Any],
        extraction_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """从节点结果中提取共享数据."""
        if not extraction_config:
            # 默认提取所有输出数据
            return node_result.get("output", {})
        
        shared_data = {}
        for shared_key, result_key in extraction_config.items():
            if result_key in node_result:
                shared_data[shared_key] = node_result[result_key]
        
        return shared_data