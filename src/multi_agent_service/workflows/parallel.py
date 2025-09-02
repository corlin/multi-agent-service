"""并行执行模式实现."""

import asyncio
from typing import Any, Dict, List, Optional, Set, Tuple
from datetime import datetime
from collections import defaultdict

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


class ParallelGraphBuilder(GraphBuilder):
    """并行执行图构建器."""
    
    def __init__(self):
        super().__init__()
        self.parallel_groups: List[List[str]] = []
        self.start_node: Optional[str] = None
        self.end_node: Optional[str] = None
    
    def set_parallel_groups(self, groups: List[List[str]]) -> 'ParallelGraphBuilder':
        """设置并行执行组."""
        self.parallel_groups = groups
        return self
    
    def set_start_end_nodes(self, start_node: str, end_node: str) -> 'ParallelGraphBuilder':
        """设置开始和结束节点."""
        self.start_node = start_node
        self.end_node = end_node
        return self
    
    def build_parallel_graph(self) -> CompiledStateGraph:
        """构建并行执行图."""
        # 创建StateGraph
        graph = StateGraph(GraphState)
        
        # 添加所有节点
        for node_id, node_func in self.node_functions.items():
            graph.add_node(node_id, node_func)
        
        # 设置入口点
        if self.start_node:
            graph.set_entry_point(self.start_node)
            
            # 从开始节点连接到所有并行组的第一个节点
            for group in self.parallel_groups:
                if group:
                    graph.add_edge(self.start_node, group[0])
            
            # 在每个并行组内部按顺序连接
            for group in self.parallel_groups:
                for i in range(len(group) - 1):
                    graph.add_edge(group[i], group[i + 1])
            
            # 从所有并行组的最后一个节点连接到结束节点
            if self.end_node:
                for group in self.parallel_groups:
                    if group:
                        graph.add_edge(group[-1], self.end_node)
                
                # 从结束节点连接到END
                graph.add_edge(self.end_node, END)
        
        return graph.compile()
    
    def auto_detect_parallel_structure(self) -> 'ParallelGraphBuilder':
        """自动检测并行结构."""
        if not self.edges:
            return self
        
        # 构建邻接表
        graph = defaultdict(list)
        reverse_graph = defaultdict(list)
        in_degree = defaultdict(int)
        out_degree = defaultdict(int)
        
        for edge in self.edges:
            graph[edge.source_node].append(edge.target_node)
            reverse_graph[edge.target_node].append(edge.source_node)
            out_degree[edge.source_node] += 1
            in_degree[edge.target_node] += 1
        
        # 找到开始节点（入度为0）
        start_nodes = [node for node in self.nodes.keys() if in_degree[node] == 0]
        if len(start_nodes) == 1:
            self.start_node = start_nodes[0]
        
        # 找到结束节点（出度为0）
        end_nodes = [node for node in self.nodes.keys() if out_degree[node] == 0]
        if len(end_nodes) == 1:
            self.end_node = end_nodes[0]
        
        # 检测并行分支
        if self.start_node and self.end_node:
            parallel_paths = self._find_parallel_paths(graph, self.start_node, self.end_node)
            self.parallel_groups = parallel_paths
        
        return self
    
    def _find_parallel_paths(self, graph: Dict[str, List[str]], start: str, end: str) -> List[List[str]]:
        """查找从开始到结束的所有并行路径."""
        all_paths = []
        
        def dfs(current: str, path: List[str], visited: Set[str]):
            if current == end:
                all_paths.append(path + [current])
                return
            
            if current in visited:
                return
            
            visited.add(current)
            for neighbor in graph.get(current, []):
                dfs(neighbor, path + [current], visited.copy())
        
        # 从开始节点的直接邻居开始查找路径
        for neighbor in graph.get(start, []):
            dfs(neighbor, [], set())
        
        return all_paths


class ParallelExecutor(GraphExecutorInterface):
    """并行执行器."""
    
    def __init__(self, max_concurrent_tasks: int = 10):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.execution_history: List[Dict[str, Any]] = []
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)
    
    async def execute_node(self, node_id: str, context: NodeExecutionContext) -> Dict[str, Any]:
        """执行单个节点."""
        async with self.semaphore:
            start_time = datetime.now()
            
            try:
                # 模拟节点执行时间
                await asyncio.sleep(0.1)
                
                result = {
                    "node_id": node_id,
                    "status": "completed",
                    "start_time": start_time.isoformat(),
                    "end_time": datetime.now().isoformat(),
                    "output": f"Node {node_id} executed successfully",
                    "thread_id": id(asyncio.current_task())
                }
                
                self.execution_history.append(result)
                return result
                
            except Exception as e:
                error_result = {
                    "node_id": node_id,
                    "status": "failed",
                    "start_time": start_time.isoformat(),
                    "end_time": datetime.now().isoformat(),
                    "error": str(e),
                    "thread_id": id(asyncio.current_task())
                }
                
                self.execution_history.append(error_result)
                raise
    
    async def execute_sequential(self, node_ids: List[str], context: NodeExecutionContext) -> List[Dict[str, Any]]:
        """顺序执行多个节点（在并行组内使用）."""
        results = []
        
        for i, node_id in enumerate(node_ids):
            step_context = NodeExecutionContext(
                node_id=node_id,
                execution_id=context.execution_id,
                input_data=context.input_data,
                shared_state=context.shared_state,
                metadata={
                    **context.metadata,
                    "step": i + 1,
                    "total_steps": len(node_ids),
                    "group_results": results
                }
            )
            
            try:
                result = await self.execute_node(node_id, step_context)
                results.append(result)
                
                # 更新共享状态
                if "shared_data" in result:
                    context.shared_state.update(result["shared_data"])
                
            except Exception as e:
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
        """并行执行多个节点."""
        tasks = []
        
        for node_id in node_ids:
            node_context = NodeExecutionContext(
                node_id=node_id,
                execution_id=context.execution_id,
                input_data=context.input_data.copy(),
                shared_state=context.shared_state.copy(),
                metadata={**context.metadata, "parallel_execution": True}
            )
            
            task = asyncio.create_task(
                self.execute_node(node_id, node_context),
                name=f"execute_{node_id}"
            )
            tasks.append(task)
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果和异常
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_result = {
                    "node_id": node_ids[i],
                    "status": "failed",
                    "error": str(result),
                    "timestamp": datetime.now().isoformat()
                }
                processed_results.append(error_result)
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def execute_parallel_groups(
        self, 
        parallel_groups: List[List[str]], 
        context: NodeExecutionContext
    ) -> List[List[Dict[str, Any]]]:
        """执行并行组."""
        group_tasks = []
        
        for group_index, group in enumerate(parallel_groups):
            group_context = NodeExecutionContext(
                node_id="",
                execution_id=context.execution_id,
                input_data=context.input_data.copy(),
                shared_state=context.shared_state.copy(),
                metadata={
                    **context.metadata,
                    "group_index": group_index,
                    "total_groups": len(parallel_groups)
                }
            )
            
            # 每个组内部是顺序执行
            task = asyncio.create_task(
                self.execute_sequential(group, group_context),
                name=f"group_{group_index}"
            )
            group_tasks.append(task)
        
        # 等待所有组完成
        group_results = await asyncio.gather(*group_tasks, return_exceptions=True)
        
        # 处理组结果
        processed_group_results = []
        for i, result in enumerate(group_results):
            if isinstance(result, Exception):
                error_result = [{
                    "group_index": i,
                    "status": "failed",
                    "error": str(result),
                    "timestamp": datetime.now().isoformat()
                }]
                processed_group_results.append(error_result)
            else:
                processed_group_results.append(result)
        
        return processed_group_results
    
    async def execute_conditional(self, condition: str, context: NodeExecutionContext) -> str:
        """执行条件判断."""
        # 并行执行中的条件判断
        if condition == "all_success":
            # 检查所有并行任务是否成功
            return "all_success"
        elif condition == "any_success":
            # 检查是否有任务成功
            return "any_success"
        else:
            return "default"


class ParallelWorkflowEngine(WorkflowEngineInterface):
    """并行执行工作流引擎."""
    
    def __init__(self, max_concurrent_tasks: int = 10):
        self.executor = ParallelExecutor(max_concurrent_tasks)
        self.active_executions: Dict[str, WorkflowExecution] = {}
    
    async def execute_workflow(self, execution: WorkflowExecution) -> WorkflowExecution:
        """执行并行工作流."""
        execution.status = WorkflowStatus.RUNNING
        execution.start_time = datetime.now()
        
        self.active_executions[execution.execution_id] = execution
        
        try:
            # 获取工作流图
            workflow_graph = await self._get_workflow_graph(execution.graph_id)
            
            if not workflow_graph:
                raise ValueError(f"Workflow graph {execution.graph_id} not found")
            
            # 分析并行结构
            parallel_structure = self._analyze_parallel_structure(workflow_graph)
            
            # 创建执行上下文
            context = NodeExecutionContext(
                node_id="",
                execution_id=execution.execution_id,
                input_data=execution.input_data,
                shared_state={}
            )
            
            # 执行开始节点
            if parallel_structure["start_node"]:
                start_result = await self.executor.execute_node(
                    parallel_structure["start_node"], context
                )
                execution.node_results[parallel_structure["start_node"]] = start_result
            
            # 执行并行组
            if parallel_structure["parallel_groups"]:
                group_results = await self.executor.execute_parallel_groups(
                    parallel_structure["parallel_groups"], context
                )
                
                # 合并组结果
                for group_index, group_result in enumerate(group_results):
                    for node_result in group_result:
                        if "node_id" in node_result:
                            execution.node_results[node_result["node_id"]] = node_result
            
            # 执行结束节点
            if parallel_structure["end_node"]:
                # 聚合所有并行结果
                aggregated_data = self._aggregate_parallel_results(execution.node_results)
                context.shared_state.update(aggregated_data)
                
                end_result = await self.executor.execute_node(
                    parallel_structure["end_node"], context
                )
                execution.node_results[parallel_structure["end_node"]] = end_result
            
            # 设置输出数据
            execution.output_data = context.shared_state
            
            # 检查执行结果
            failed_nodes = [
                node_id for node_id, result in execution.node_results.items()
                if result.get("status") == "failed"
            ]
            
            if failed_nodes:
                execution.status = WorkflowStatus.FAILED
                execution.error_message = f"Nodes failed: {failed_nodes}"
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
        """暂停工作流（并行执行不支持暂停）."""
        return False
    
    async def resume_workflow(self, execution_id: str) -> bool:
        """恢复工作流（并行执行不支持恢复）."""
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
        return WorkflowGraph(
            graph_id=graph_id,
            name="Parallel Workflow",
            workflow_type=WorkflowType.PARALLEL,
            nodes=[
                WorkflowNode(node_id="start", node_type="start", name="Start Node"),
                WorkflowNode(node_id="parallel1", node_type="agent", agent_type=AgentType.SALES, name="Sales Agent"),
                WorkflowNode(node_id="parallel2", node_type="agent", agent_type=AgentType.CUSTOMER_SUPPORT, name="Support Agent"),
                WorkflowNode(node_id="end", node_type="end", name="End Node")
            ],
            edges=[
                WorkflowEdge(source_node="start", target_node="parallel1"),
                WorkflowEdge(source_node="start", target_node="parallel2"),
                WorkflowEdge(source_node="parallel1", target_node="end"),
                WorkflowEdge(source_node="parallel2", target_node="end")
            ]
        )
    
    def _analyze_parallel_structure(self, workflow_graph: WorkflowGraph) -> Dict[str, Any]:
        """分析并行结构."""
        # 构建邻接表
        graph = defaultdict(list)
        reverse_graph = defaultdict(list)
        in_degree = defaultdict(int)
        out_degree = defaultdict(int)
        
        for edge in workflow_graph.edges:
            graph[edge.source_node].append(edge.target_node)
            reverse_graph[edge.target_node].append(edge.source_node)
            out_degree[edge.source_node] += 1
            in_degree[edge.target_node] += 1
        
        # 找到开始和结束节点
        start_nodes = [node.node_id for node in workflow_graph.nodes if in_degree[node.node_id] == 0]
        end_nodes = [node.node_id for node in workflow_graph.nodes if out_degree[node.node_id] == 0]
        
        start_node = start_nodes[0] if start_nodes else None
        end_node = end_nodes[0] if end_nodes else None
        
        # 找到并行分支
        parallel_groups = []
        if start_node and end_node:
            # 从开始节点的直接后继开始
            parallel_nodes = graph.get(start_node, [])
            
            # 每个并行节点形成一个组
            for node in parallel_nodes:
                if node != end_node:  # 排除直接连接到结束节点的情况
                    parallel_groups.append([node])
        
        return {
            "start_node": start_node,
            "end_node": end_node,
            "parallel_groups": parallel_groups
        }
    
    def _aggregate_parallel_results(self, node_results: Dict[str, Any]) -> Dict[str, Any]:
        """聚合并行执行结果."""
        aggregated = {
            "parallel_results": [],
            "success_count": 0,
            "failure_count": 0,
            "total_execution_time": 0
        }
        
        for node_id, result in node_results.items():
            if isinstance(result, dict):
                aggregated["parallel_results"].append({
                    "node_id": node_id,
                    "status": result.get("status"),
                    "output": result.get("output")
                })
                
                if result.get("status") == "completed":
                    aggregated["success_count"] += 1
                elif result.get("status") == "failed":
                    aggregated["failure_count"] += 1
        
        return aggregated


class ParallelWorkflowFactory:
    """并行工作流工厂类."""
    
    @staticmethod
    def create_parallel_workflow(
        start_config: Dict[str, Any],
        parallel_configs: List[Dict[str, Any]],
        end_config: Dict[str, Any],
        workflow_name: str = "Parallel Workflow"
    ) -> WorkflowGraph:
        """创建并行工作流."""
        nodes = []
        edges = []
        
        # 创建开始节点
        start_node = WorkflowNode(
            node_id=start_config.get("node_id", "start"),
            node_type=start_config.get("node_type", "start"),
            name=start_config.get("name", "Start"),
            config=start_config.get("config", {})
        )
        nodes.append(start_node)
        
        # 创建并行节点
        parallel_node_ids = []
        for i, config in enumerate(parallel_configs):
            node = WorkflowNode(
                node_id=config.get("node_id", f"parallel_{i}"),
                node_type=config.get("node_type", "agent"),
                agent_type=config.get("agent_type"),
                name=config.get("name", f"Parallel Node {i}"),
                config=config.get("config", {})
            )
            nodes.append(node)
            parallel_node_ids.append(node.node_id)
            
            # 从开始节点连接到并行节点
            edges.append(WorkflowEdge(
                source_node=start_node.node_id,
                target_node=node.node_id
            ))
        
        # 创建结束节点
        end_node = WorkflowNode(
            node_id=end_config.get("node_id", "end"),
            node_type=end_config.get("node_type", "end"),
            name=end_config.get("name", "End"),
            config=end_config.get("config", {})
        )
        nodes.append(end_node)
        
        # 从所有并行节点连接到结束节点
        for parallel_node_id in parallel_node_ids:
            edges.append(WorkflowEdge(
                source_node=parallel_node_id,
                target_node=end_node.node_id
            ))
        
        return WorkflowGraph(
            name=workflow_name,
            workflow_type=WorkflowType.PARALLEL,
            nodes=nodes,
            edges=edges,
            entry_point=start_node.node_id,
            exit_points=[end_node.node_id]
        )
    
    @staticmethod
    def create_multi_agent_parallel_workflow(
        agent_types: List[AgentType],
        workflow_name: str = "Multi-Agent Parallel Workflow"
    ) -> WorkflowGraph:
        """创建多智能体并行工作流."""
        start_config = {"node_id": "start", "node_type": "start", "name": "Start"}
        
        parallel_configs = []
        for i, agent_type in enumerate(agent_types):
            parallel_configs.append({
                "node_id": f"agent_{agent_type.value}",
                "node_type": "agent",
                "agent_type": agent_type,
                "name": f"{agent_type.value.title()} Agent"
            })
        
        end_config = {"node_id": "end", "node_type": "end", "name": "End"}
        
        return ParallelWorkflowFactory.create_parallel_workflow(
            start_config, parallel_configs, end_config, workflow_name
        )


class ParallelResultAggregator:
    """并行结果聚合器."""
    
    @staticmethod
    def aggregate_by_strategy(
        results: List[Dict[str, Any]], 
        strategy: str = "merge"
    ) -> Dict[str, Any]:
        """根据策略聚合结果."""
        if strategy == "merge":
            return ParallelResultAggregator._merge_results(results)
        elif strategy == "vote":
            return ParallelResultAggregator._vote_results(results)
        elif strategy == "best":
            return ParallelResultAggregator._select_best_result(results)
        else:
            return ParallelResultAggregator._merge_results(results)
    
    @staticmethod
    def _merge_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并所有结果."""
        merged = {
            "aggregation_strategy": "merge",
            "individual_results": results,
            "combined_output": {},
            "success_rate": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        successful_results = [r for r in results if r.get("status") == "completed"]
        merged["success_rate"] = len(successful_results) / len(results) if results else 0
        
        # 合并输出数据
        for result in successful_results:
            if "output" in result and isinstance(result["output"], dict):
                merged["combined_output"].update(result["output"])
        
        return merged
    
    @staticmethod
    def _vote_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """投票选择结果."""
        vote_counts = defaultdict(int)
        
        for result in results:
            if result.get("status") == "completed":
                output = result.get("output", "")
                vote_counts[str(output)] += 1
        
        # 选择得票最多的结果
        if vote_counts:
            winning_output = max(vote_counts.keys(), key=lambda k: vote_counts[k])
            confidence = vote_counts[winning_output] / len(results)
        else:
            winning_output = ""
            confidence = 0
        
        return {
            "aggregation_strategy": "vote",
            "winning_output": winning_output,
            "confidence": confidence,
            "vote_counts": dict(vote_counts),
            "individual_results": results,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def _select_best_result(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """选择最佳结果."""
        successful_results = [r for r in results if r.get("status") == "completed"]
        
        if not successful_results:
            return {
                "aggregation_strategy": "best",
                "selected_result": None,
                "reason": "No successful results",
                "individual_results": results,
                "timestamp": datetime.now().isoformat()
            }
        
        # 简单选择第一个成功的结果（可以扩展更复杂的选择逻辑）
        best_result = successful_results[0]
        
        return {
            "aggregation_strategy": "best",
            "selected_result": best_result,
            "reason": "First successful result",
            "individual_results": results,
            "timestamp": datetime.now().isoformat()
        }


class ParallelSynchronizer:
    """并行同步器，用于协调并行任务."""
    
    def __init__(self):
        self.barriers: Dict[str, asyncio.Barrier] = {}
        self.events: Dict[str, asyncio.Event] = {}
        self.locks: Dict[str, asyncio.Lock] = {}
    
    async def create_barrier(self, barrier_id: str, parties: int) -> asyncio.Barrier:
        """创建屏障."""
        barrier = asyncio.Barrier(parties)
        self.barriers[barrier_id] = barrier
        return barrier
    
    async def wait_barrier(self, barrier_id: str) -> None:
        """等待屏障."""
        if barrier_id in self.barriers:
            await self.barriers[barrier_id].wait()
    
    async def create_event(self, event_id: str) -> asyncio.Event:
        """创建事件."""
        event = asyncio.Event()
        self.events[event_id] = event
        return event
    
    async def set_event(self, event_id: str) -> None:
        """设置事件."""
        if event_id in self.events:
            self.events[event_id].set()
    
    async def wait_event(self, event_id: str) -> None:
        """等待事件."""
        if event_id in self.events:
            await self.events[event_id].wait()
    
    async def acquire_lock(self, lock_id: str) -> asyncio.Lock:
        """获取锁."""
        if lock_id not in self.locks:
            self.locks[lock_id] = asyncio.Lock()
        return self.locks[lock_id]
    
    def cleanup(self) -> None:
        """清理资源."""
        self.barriers.clear()
        self.events.clear()
        self.locks.clear()