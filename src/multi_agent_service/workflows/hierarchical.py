"""分层执行模式实现."""

import asyncio
from typing import Any, Dict, List, Optional, Set, Tuple
from datetime import datetime
from collections import defaultdict
from enum import Enum

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


class TaskPriority(str, Enum):
    """任务优先级枚举."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(str, Enum):
    """任务状态枚举."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SubTask:
    """子任务模型."""
    
    def __init__(
        self,
        task_id: str,
        name: str,
        agent_type: AgentType,
        input_data: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
        dependencies: Optional[List[str]] = None
    ):
        self.task_id = task_id
        self.name = name
        self.agent_type = agent_type
        self.input_data = input_data
        self.priority = priority
        self.dependencies = dependencies or []
        self.status = TaskStatus.PENDING
        self.assigned_agent: Optional[str] = None
        self.result: Optional[Dict[str, Any]] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典."""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "agent_type": self.agent_type.value,
            "input_data": self.input_data,
            "priority": self.priority.value,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "assigned_agent": self.assigned_agent,
            "result": self.result,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "error_message": self.error_message
        }


class CoordinatorAgent:
    """协调员智能体，负责任务分解和调度."""
    
    def __init__(self, coordinator_id: str = "coordinator"):
        self.coordinator_id = coordinator_id
        self.subtasks: Dict[str, SubTask] = {}
        self.agent_workload: Dict[str, int] = defaultdict(int)
        self.task_queue: List[str] = []
        self.completed_tasks: Set[str] = set()
        self.failed_tasks: Set[str] = set()
    
    async def decompose_task(
        self, 
        main_task: Dict[str, Any], 
        context: NodeExecutionContext
    ) -> List[SubTask]:
        """将主任务分解为子任务."""
        subtasks = []
        
        # 基于任务类型进行分解（这里是简化的示例）
        task_type = main_task.get("type", "general")
        
        if task_type == "customer_inquiry":
            # 客户咨询任务分解
            subtasks.extend(self._decompose_customer_inquiry(main_task))
        elif task_type == "sales_process":
            # 销售流程任务分解
            subtasks.extend(self._decompose_sales_process(main_task))
        elif task_type == "technical_support":
            # 技术支持任务分解
            subtasks.extend(self._decompose_technical_support(main_task))
        else:
            # 通用任务分解
            subtasks.extend(self._decompose_general_task(main_task))
        
        # 注册子任务
        for subtask in subtasks:
            self.subtasks[subtask.task_id] = subtask
            self.task_queue.append(subtask.task_id)
        
        return subtasks
    
    def _decompose_customer_inquiry(self, task: Dict[str, Any]) -> List[SubTask]:
        """分解客户咨询任务."""
        subtasks = []
        
        # 1. 意图分析
        subtasks.append(SubTask(
            task_id="intent_analysis",
            name="Intent Analysis",
            agent_type=AgentType.CUSTOMER_SUPPORT,
            input_data={"query": task.get("query", "")},
            priority=TaskPriority.HIGH
        ))
        
        # 2. 信息收集
        subtasks.append(SubTask(
            task_id="info_gathering",
            name="Information Gathering",
            agent_type=AgentType.CUSTOMER_SUPPORT,
            input_data={"customer_id": task.get("customer_id")},
            dependencies=["intent_analysis"]
        ))
        
        # 3. 解决方案提供
        subtasks.append(SubTask(
            task_id="solution_provision",
            name="Solution Provision",
            agent_type=AgentType.CUSTOMER_SUPPORT,
            input_data={"issue_type": task.get("issue_type")},
            dependencies=["info_gathering"]
        ))
        
        return subtasks
    
    def _decompose_sales_process(self, task: Dict[str, Any]) -> List[SubTask]:
        """分解销售流程任务."""
        subtasks = []
        
        # 1. 需求分析
        subtasks.append(SubTask(
            task_id="needs_analysis",
            name="Needs Analysis",
            agent_type=AgentType.SALES,
            input_data={"customer_profile": task.get("customer_profile", {})},
            priority=TaskPriority.HIGH
        ))
        
        # 2. 产品推荐
        subtasks.append(SubTask(
            task_id="product_recommendation",
            name="Product Recommendation",
            agent_type=AgentType.SALES,
            input_data={"requirements": task.get("requirements", {})},
            dependencies=["needs_analysis"]
        ))
        
        # 3. 报价生成
        subtasks.append(SubTask(
            task_id="quote_generation",
            name="Quote Generation",
            agent_type=AgentType.SALES,
            input_data={"products": task.get("products", [])},
            dependencies=["product_recommendation"]
        ))
        
        # 4. 管理审批
        subtasks.append(SubTask(
            task_id="management_approval",
            name="Management Approval",
            agent_type=AgentType.MANAGER,
            input_data={"quote_amount": task.get("quote_amount", 0)},
            dependencies=["quote_generation"],
            priority=TaskPriority.HIGH
        ))
        
        return subtasks
    
    def _decompose_technical_support(self, task: Dict[str, Any]) -> List[SubTask]:
        """分解技术支持任务."""
        subtasks = []
        
        # 1. 问题诊断
        subtasks.append(SubTask(
            task_id="problem_diagnosis",
            name="Problem Diagnosis",
            agent_type=AgentType.FIELD_SERVICE,
            input_data={"symptoms": task.get("symptoms", [])},
            priority=TaskPriority.URGENT
        ))
        
        # 2. 解决方案制定
        subtasks.append(SubTask(
            task_id="solution_planning",
            name="Solution Planning",
            agent_type=AgentType.FIELD_SERVICE,
            input_data={"diagnosis": task.get("diagnosis", {})},
            dependencies=["problem_diagnosis"]
        ))
        
        # 3. 资源调度
        subtasks.append(SubTask(
            task_id="resource_scheduling",
            name="Resource Scheduling",
            agent_type=AgentType.MANAGER,
            input_data={"required_resources": task.get("resources", [])},
            dependencies=["solution_planning"]
        ))
        
        return subtasks
    
    def _decompose_general_task(self, task: Dict[str, Any]) -> List[SubTask]:
        """分解通用任务."""
        subtasks = []
        
        # 简单的通用分解：分析 -> 处理 -> 总结
        subtasks.append(SubTask(
            task_id="analysis",
            name="Analysis",
            agent_type=AgentType.CUSTOMER_SUPPORT,
            input_data=task.get("input_data", {}),
            priority=TaskPriority.NORMAL
        ))
        
        subtasks.append(SubTask(
            task_id="processing",
            name="Processing",
            agent_type=AgentType.SALES,
            input_data={},
            dependencies=["analysis"]
        ))
        
        subtasks.append(SubTask(
            task_id="summary",
            name="Summary",
            agent_type=AgentType.MANAGER,
            input_data={},
            dependencies=["processing"]
        ))
        
        return subtasks
    
    async def schedule_tasks(self) -> List[str]:
        """调度任务，返回可执行的任务ID列表."""
        ready_tasks = []
        
        for task_id in self.task_queue:
            if task_id in self.completed_tasks or task_id in self.failed_tasks:
                continue
            
            subtask = self.subtasks[task_id]
            if subtask.status != TaskStatus.PENDING:
                continue
            
            # 检查依赖是否完成
            dependencies_met = all(
                dep_id in self.completed_tasks 
                for dep_id in subtask.dependencies
            )
            
            if dependencies_met:
                ready_tasks.append(task_id)
        
        # 按优先级排序（降序，优先级高的在前）
        ready_tasks.sort(key=lambda tid: self._get_priority_value(self.subtasks[tid].priority), reverse=True)
        
        return ready_tasks
    
    def _get_priority_value(self, priority: TaskPriority) -> int:
        """获取优先级数值（用于排序）."""
        priority_values = {
            TaskPriority.LOW: 1,
            TaskPriority.NORMAL: 2,
            TaskPriority.HIGH: 3,
            TaskPriority.URGENT: 4
        }
        return priority_values.get(priority, 2)
    
    async def assign_task(self, task_id: str, agent_id: str) -> bool:
        """分配任务给智能体."""
        if task_id not in self.subtasks:
            return False
        
        subtask = self.subtasks[task_id]
        subtask.status = TaskStatus.ASSIGNED
        subtask.assigned_agent = agent_id
        self.agent_workload[agent_id] += 1
        
        return True
    
    async def start_task(self, task_id: str) -> bool:
        """开始执行任务."""
        if task_id not in self.subtasks:
            return False
        
        subtask = self.subtasks[task_id]
        subtask.status = TaskStatus.IN_PROGRESS
        subtask.start_time = datetime.now()
        
        return True
    
    async def complete_task(self, task_id: str, result: Dict[str, Any]) -> bool:
        """完成任务."""
        if task_id not in self.subtasks:
            return False
        
        subtask = self.subtasks[task_id]
        subtask.status = TaskStatus.COMPLETED
        subtask.result = result
        subtask.end_time = datetime.now()
        
        self.completed_tasks.add(task_id)
        
        # 减少智能体工作负载
        if subtask.assigned_agent:
            self.agent_workload[subtask.assigned_agent] -= 1
        
        return True
    
    async def fail_task(self, task_id: str, error_message: str) -> bool:
        """标记任务失败."""
        if task_id not in self.subtasks:
            return False
        
        subtask = self.subtasks[task_id]
        subtask.status = TaskStatus.FAILED
        subtask.error_message = error_message
        subtask.end_time = datetime.now()
        
        self.failed_tasks.add(task_id)
        
        # 减少智能体工作负载
        if subtask.assigned_agent:
            self.agent_workload[subtask.assigned_agent] -= 1
        
        return True
    
    async def get_execution_summary(self) -> Dict[str, Any]:
        """获取执行摘要."""
        total_tasks = len(self.subtasks)
        completed_count = len(self.completed_tasks)
        failed_count = len(self.failed_tasks)
        in_progress_count = sum(
            1 for task in self.subtasks.values() 
            if task.status == TaskStatus.IN_PROGRESS
        )
        
        return {
            "coordinator_id": self.coordinator_id,
            "total_tasks": total_tasks,
            "completed_tasks": completed_count,
            "failed_tasks": failed_count,
            "in_progress_tasks": in_progress_count,
            "success_rate": completed_count / total_tasks if total_tasks > 0 else 0,
            "agent_workload": dict(self.agent_workload),
            "task_details": {tid: task.to_dict() for tid, task in self.subtasks.items()}
        }


class HierarchicalGraphBuilder(GraphBuilder):
    """分层执行图构建器."""
    
    def __init__(self):
        super().__init__()
        self.coordinator_node: Optional[str] = None
        self.worker_nodes: List[str] = []
        self.task_flow: Dict[str, List[str]] = {}
    
    def set_coordinator(self, coordinator_node_id: str) -> 'HierarchicalGraphBuilder':
        """设置协调员节点."""
        self.coordinator_node = coordinator_node_id
        return self
    
    def add_worker_nodes(self, worker_node_ids: List[str]) -> 'HierarchicalGraphBuilder':
        """添加工作节点."""
        self.worker_nodes.extend(worker_node_ids)
        return self
    
    def set_task_flow(self, flow: Dict[str, List[str]]) -> 'HierarchicalGraphBuilder':
        """设置任务流程."""
        self.task_flow = flow
        return self
    
    def build_hierarchical_graph(self) -> CompiledStateGraph:
        """构建分层执行图."""
        # 创建StateGraph
        graph = StateGraph(GraphState)
        
        # 添加所有节点
        for node_id, node_func in self.node_functions.items():
            graph.add_node(node_id, node_func)
        
        # 设置协调员为入口点
        if self.coordinator_node:
            graph.set_entry_point(self.coordinator_node)
            
            # 协调员连接到所有工作节点
            for worker_node in self.worker_nodes:
                graph.add_edge(self.coordinator_node, worker_node)
            
            # 工作节点完成后回到协调员
            for worker_node in self.worker_nodes:
                graph.add_edge(worker_node, self.coordinator_node)
        
        # 添加其他边
        for edge in self.edges:
            if not self._is_coordinator_edge(edge):
                graph.add_edge(edge.source_node, edge.target_node)
        
        return graph.compile()
    
    def _is_coordinator_edge(self, edge: WorkflowEdge) -> bool:
        """检查是否是协调员相关的边."""
        return (edge.source_node == self.coordinator_node or 
                edge.target_node == self.coordinator_node)


class HierarchicalExecutor(GraphExecutorInterface):
    """分层执行器."""
    
    def __init__(self):
        self.coordinator = CoordinatorAgent()
        self.execution_history: List[Dict[str, Any]] = []
        self.active_tasks: Dict[str, asyncio.Task] = {}
    
    async def execute_node(self, node_id: str, context: NodeExecutionContext) -> Dict[str, Any]:
        """执行单个节点."""
        start_time = datetime.now()
        
        try:
            # 模拟节点执行
            await asyncio.sleep(0.1)
            
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
        
        for node_id in node_ids:
            try:
                result = await self.execute_node(node_id, context)
                results.append(result)
            except Exception as e:
                error_result = {
                    "node_id": node_id,
                    "status": "failed",
                    "error": str(e)
                }
                results.append(error_result)
                break
        
        return results
    
    async def execute_parallel(self, node_ids: List[str], context: NodeExecutionContext) -> List[Dict[str, Any]]:
        """并行执行多个节点."""
        tasks = []
        
        for node_id in node_ids:
            task = asyncio.create_task(
                self.execute_node(node_id, context),
                name=f"execute_{node_id}"
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_result = {
                    "node_id": node_ids[i],
                    "status": "failed",
                    "error": str(result)
                }
                processed_results.append(error_result)
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def execute_hierarchical(
        self, 
        main_task: Dict[str, Any], 
        context: NodeExecutionContext
    ) -> Dict[str, Any]:
        """执行分层任务."""
        # 1. 任务分解
        subtasks = await self.coordinator.decompose_task(main_task, context)
        
        execution_result = {
            "main_task": main_task,
            "subtasks": [task.to_dict() for task in subtasks],
            "execution_log": [],
            "final_result": {},
            "start_time": datetime.now().isoformat()
        }
        
        # 如果没有子任务，直接返回
        if not subtasks:
            execution_summary = await self.coordinator.get_execution_summary()
            execution_result["final_result"] = execution_summary
            execution_result["end_time"] = datetime.now().isoformat()
            return execution_result
        
        # 2. 任务执行循环（添加超时保护）
        max_iterations = 100  # 防止无限循环
        iteration_count = 0
        
        while iteration_count < max_iterations:
            iteration_count += 1
            
            # 获取可执行的任务
            ready_tasks = await self.coordinator.schedule_tasks()
            
            # 检查是否所有任务都完成
            total_finished = len(self.coordinator.completed_tasks) + len(self.coordinator.failed_tasks)
            if total_finished >= len(self.coordinator.subtasks):
                break
            
            # 如果没有就绪任务且没有活跃任务，可能存在死锁
            if not ready_tasks and not self.active_tasks:
                # 检查是否有待处理的任务
                pending_tasks = [
                    task_id for task_id, task in self.coordinator.subtasks.items()
                    if task.status == TaskStatus.PENDING and task_id not in self.coordinator.completed_tasks and task_id not in self.coordinator.failed_tasks
                ]
                if pending_tasks:
                    # 强制执行第一个待处理任务以打破死锁
                    task_id = pending_tasks[0]
                    task = asyncio.create_task(
                        self._execute_subtask(task_id, context),
                        name=f"subtask_{task_id}"
                    )
                    self.active_tasks[task_id] = task
                else:
                    break
            
            # 3. 执行就绪的任务
            for task_id in ready_tasks:
                if task_id not in self.active_tasks:
                    task = asyncio.create_task(
                        self._execute_subtask(task_id, context),
                        name=f"subtask_{task_id}"
                    )
                    self.active_tasks[task_id] = task
            
            # 4. 检查完成的任务
            completed_task_ids = []
            for task_id, task in list(self.active_tasks.items()):
                if task.done():
                    completed_task_ids.append(task_id)
                    try:
                        result = await task
                        await self.coordinator.complete_task(task_id, result)
                        execution_result["execution_log"].append({
                            "task_id": task_id,
                            "status": "completed",
                            "result": result,
                            "timestamp": datetime.now().isoformat()
                        })
                    except Exception as e:
                        await self.coordinator.fail_task(task_id, str(e))
                        execution_result["execution_log"].append({
                            "task_id": task_id,
                            "status": "failed",
                            "error": str(e),
                            "timestamp": datetime.now().isoformat()
                        })
            
            # 清理完成的任务
            for task_id in completed_task_ids:
                del self.active_tasks[task_id]
            
            # 短暂等待，但只在有活跃任务时
            if self.active_tasks:
                await asyncio.sleep(0.01)
        
        # 5. 生成最终结果
        execution_summary = await self.coordinator.get_execution_summary()
        execution_result["final_result"] = execution_summary
        execution_result["end_time"] = datetime.now().isoformat()
        
        return execution_result
    
    async def _execute_subtask(self, task_id: str, context: NodeExecutionContext) -> Dict[str, Any]:
        """执行子任务."""
        subtask = self.coordinator.subtasks[task_id]
        
        # 分配和开始任务
        await self.coordinator.assign_task(task_id, f"agent_{subtask.agent_type.value}")
        await self.coordinator.start_task(task_id)
        
        # 创建子任务执行上下文
        subtask_context = NodeExecutionContext(
            node_id=task_id,
            execution_id=context.execution_id,
            input_data=subtask.input_data,
            shared_state=context.shared_state,
            metadata={
                **context.metadata,
                "subtask_id": task_id,
                "agent_type": subtask.agent_type.value,
                "priority": subtask.priority.value
            }
        )
        
        # 执行子任务
        result = await self.execute_node(task_id, subtask_context)
        
        return result
    
    async def execute_conditional(self, condition: str, context: NodeExecutionContext) -> str:
        """执行条件判断."""
        if condition == "all_subtasks_completed":
            return "all_completed" if len(self.coordinator.failed_tasks) == 0 else "some_failed"
        elif condition == "critical_task_failed":
            # 检查是否有关键任务失败
            return "critical_failed" if self.coordinator.failed_tasks else "no_critical_failure"
        else:
            return "default"


class HierarchicalWorkflowEngine(WorkflowEngineInterface):
    """分层执行工作流引擎."""
    
    def __init__(self):
        self.executor = HierarchicalExecutor()
        self.active_executions: Dict[str, WorkflowExecution] = {}
    
    async def execute_workflow(self, execution: WorkflowExecution) -> WorkflowExecution:
        """执行分层工作流."""
        execution.status = WorkflowStatus.RUNNING
        execution.start_time = datetime.now()
        
        self.active_executions[execution.execution_id] = execution
        
        try:
            # 获取工作流图
            workflow_graph = await self._get_workflow_graph(execution.graph_id)
            
            if not workflow_graph:
                raise ValueError(f"Workflow graph {execution.graph_id} not found")
            
            # 创建执行上下文
            context = NodeExecutionContext(
                node_id="coordinator",
                execution_id=execution.execution_id,
                input_data=execution.input_data,
                shared_state={}
            )
            
            # 执行分层任务
            main_task = {
                "type": execution.input_data.get("task_type", "general"),
                **execution.input_data
            }
            
            hierarchical_result = await self.executor.execute_hierarchical(main_task, context)
            
            # 设置执行结果
            execution.node_results = {
                "coordinator": hierarchical_result,
                **{
                    log_entry["task_id"]: log_entry.get("result", {})
                    for log_entry in hierarchical_result["execution_log"]
                    if log_entry.get("result")
                }
            }
            
            execution.output_data = hierarchical_result["final_result"]
            
            # 检查执行状态
            if hierarchical_result["final_result"]["failed_tasks"] > 0:
                execution.status = WorkflowStatus.FAILED
                execution.error_message = f"Failed subtasks: {hierarchical_result['final_result']['failed_tasks']}"
            else:
                execution.status = WorkflowStatus.COMPLETED
            
            execution.end_time = datetime.now()
            
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.error_message = str(e)
            execution.end_time = datetime.now()
        
        finally:
            if execution.execution_id in self.active_executions:
                del self.active_executions[execution.execution_id]
        
        return execution
    
    async def pause_workflow(self, execution_id: str) -> bool:
        """暂停工作流（分层执行支持暂停）."""
        if execution_id in self.active_executions:
            # 可以实现暂停逻辑，比如停止新任务的调度
            return True
        return False
    
    async def resume_workflow(self, execution_id: str) -> bool:
        """恢复工作流（分层执行支持恢复）."""
        if execution_id in self.active_executions:
            # 可以实现恢复逻辑，比如重新开始任务调度
            return True
        return False
    
    async def cancel_workflow(self, execution_id: str) -> bool:
        """取消工作流."""
        if execution_id in self.active_executions:
            execution = self.active_executions[execution_id]
            execution.status = WorkflowStatus.CANCELLED
            execution.end_time = datetime.now()
            
            # 取消所有活跃的子任务
            for task in self.executor.active_tasks.values():
                task.cancel()
            
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
        return WorkflowGraph(
            graph_id=graph_id,
            name="Hierarchical Workflow",
            workflow_type=WorkflowType.HIERARCHICAL,
            nodes=[
                WorkflowNode(
                    node_id="coordinator",
                    node_type="coordinator",
                    agent_type=AgentType.COORDINATOR,
                    name="Coordinator Agent"
                ),
                WorkflowNode(
                    node_id="sales_worker",
                    node_type="worker",
                    agent_type=AgentType.SALES,
                    name="Sales Worker"
                ),
                WorkflowNode(
                    node_id="support_worker",
                    node_type="worker",
                    agent_type=AgentType.CUSTOMER_SUPPORT,
                    name="Support Worker"
                ),
                WorkflowNode(
                    node_id="manager_worker",
                    node_type="worker",
                    agent_type=AgentType.MANAGER,
                    name="Manager Worker"
                )
            ],
            edges=[
                WorkflowEdge(source_node="coordinator", target_node="sales_worker"),
                WorkflowEdge(source_node="coordinator", target_node="support_worker"),
                WorkflowEdge(source_node="coordinator", target_node="manager_worker"),
                WorkflowEdge(source_node="sales_worker", target_node="coordinator"),
                WorkflowEdge(source_node="support_worker", target_node="coordinator"),
                WorkflowEdge(source_node="manager_worker", target_node="coordinator")
            ]
        )


class HierarchicalWorkflowFactory:
    """分层工作流工厂类."""
    
    @staticmethod
    def create_hierarchical_workflow(
        coordinator_config: Dict[str, Any],
        worker_configs: List[Dict[str, Any]],
        workflow_name: str = "Hierarchical Workflow"
    ) -> WorkflowGraph:
        """创建分层工作流."""
        nodes = []
        edges = []
        
        # 创建协调员节点
        coordinator_node = WorkflowNode(
            node_id=coordinator_config.get("node_id", "coordinator"),
            node_type="coordinator",
            agent_type=AgentType.COORDINATOR,
            name=coordinator_config.get("name", "Coordinator"),
            config=coordinator_config.get("config", {})
        )
        nodes.append(coordinator_node)
        
        # 创建工作节点
        for i, config in enumerate(worker_configs):
            worker_node = WorkflowNode(
                node_id=config.get("node_id", f"worker_{i}"),
                node_type="worker",
                agent_type=config.get("agent_type", AgentType.CUSTOMER_SUPPORT),
                name=config.get("name", f"Worker {i}"),
                config=config.get("config", {})
            )
            nodes.append(worker_node)
            
            # 协调员到工作节点的边
            edges.append(WorkflowEdge(
                source_node=coordinator_node.node_id,
                target_node=worker_node.node_id
            ))
            
            # 工作节点到协调员的边
            edges.append(WorkflowEdge(
                source_node=worker_node.node_id,
                target_node=coordinator_node.node_id
            ))
        
        return WorkflowGraph(
            name=workflow_name,
            workflow_type=WorkflowType.HIERARCHICAL,
            nodes=nodes,
            edges=edges,
            entry_point=coordinator_node.node_id,
            exit_points=[coordinator_node.node_id]
        )
    
    @staticmethod
    def create_multi_level_hierarchy(
        levels: List[List[Dict[str, Any]]],
        workflow_name: str = "Multi-Level Hierarchy"
    ) -> WorkflowGraph:
        """创建多层级分层工作流."""
        nodes = []
        edges = []
        
        # 为每一层创建节点
        level_nodes = []
        for level_index, level_configs in enumerate(levels):
            level_node_ids = []
            for node_index, config in enumerate(level_configs):
                node_id = config.get("node_id", f"level_{level_index}_node_{node_index}")
                node = WorkflowNode(
                    node_id=node_id,
                    node_type=config.get("node_type", "worker"),
                    agent_type=config.get("agent_type", AgentType.CUSTOMER_SUPPORT),
                    name=config.get("name", f"Level {level_index} Node {node_index}"),
                    config=config.get("config", {})
                )
                nodes.append(node)
                level_node_ids.append(node_id)
            level_nodes.append(level_node_ids)
        
        # 创建层级间的连接
        for level_index in range(len(level_nodes) - 1):
            current_level = level_nodes[level_index]
            next_level = level_nodes[level_index + 1]
            
            # 当前层的每个节点连接到下一层的所有节点
            for current_node in current_level:
                for next_node in next_level:
                    edges.append(WorkflowEdge(
                        source_node=current_node,
                        target_node=next_node
                    ))
        
        return WorkflowGraph(
            name=workflow_name,
            workflow_type=WorkflowType.HIERARCHICAL,
            nodes=nodes,
            edges=edges,
            entry_point=level_nodes[0][0] if level_nodes and level_nodes[0] else None,
            exit_points=level_nodes[-1] if level_nodes else []
        )


class ConflictResolver:
    """冲突解决器，用于处理分层执行中的冲突."""
    
    def __init__(self):
        self.resolution_strategies = {
            "priority_based": self._resolve_by_priority,
            "resource_based": self._resolve_by_resource,
            "consensus": self._resolve_by_consensus,
            "escalation": self._resolve_by_escalation
        }
    
    async def resolve_conflict(
        self,
        conflicting_tasks: List[SubTask],
        strategy: str = "priority_based"
    ) -> Dict[str, Any]:
        """解决任务冲突."""
        if strategy not in self.resolution_strategies:
            strategy = "priority_based"
        
        resolution_func = self.resolution_strategies[strategy]
        return await resolution_func(conflicting_tasks)
    
    async def _resolve_by_priority(self, tasks: List[SubTask]) -> Dict[str, Any]:
        """基于优先级解决冲突."""
        # 按优先级排序
        sorted_tasks = sorted(tasks, key=lambda t: self._get_priority_value(t.priority), reverse=True)
        
        return {
            "strategy": "priority_based",
            "winner": sorted_tasks[0].task_id,
            "execution_order": [task.task_id for task in sorted_tasks],
            "reason": "Resolved based on task priority"
        }
    
    async def _resolve_by_resource(self, tasks: List[SubTask]) -> Dict[str, Any]:
        """基于资源可用性解决冲突."""
        # 简化实现：选择资源需求最少的任务
        resource_scores = {}
        for task in tasks:
            # 模拟资源评分
            resource_scores[task.task_id] = len(task.input_data)
        
        winner = min(resource_scores.keys(), key=lambda k: resource_scores[k])
        
        return {
            "strategy": "resource_based",
            "winner": winner,
            "resource_scores": resource_scores,
            "reason": "Resolved based on resource availability"
        }
    
    async def _resolve_by_consensus(self, tasks: List[SubTask]) -> Dict[str, Any]:
        """基于共识解决冲突."""
        # 简化实现：选择第一个任务
        return {
            "strategy": "consensus",
            "winner": tasks[0].task_id if tasks else None,
            "reason": "Resolved by consensus (simplified)"
        }
    
    async def _resolve_by_escalation(self, tasks: List[SubTask]) -> Dict[str, Any]:
        """通过升级解决冲突."""
        # 升级到管理层决策
        return {
            "strategy": "escalation",
            "escalated_to": "management",
            "pending_tasks": [task.task_id for task in tasks],
            "reason": "Conflict escalated to management level"
        }
    
    def _get_priority_value(self, priority: TaskPriority) -> int:
        """获取优先级数值."""
        priority_values = {
            TaskPriority.LOW: 1,
            TaskPriority.NORMAL: 2,
            TaskPriority.HIGH: 3,
            TaskPriority.URGENT: 4
        }
        return priority_values.get(priority, 2)