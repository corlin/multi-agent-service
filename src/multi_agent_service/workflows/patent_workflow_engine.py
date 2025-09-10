"""Patent workflow engine integration with existing workflow infrastructure."""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from uuid import uuid4

from .graph_builder import GraphBuilder, GraphState, BaseNode, AgentNode, ControlNode
from .state_management import WorkflowStateManager
from .sequential import SequentialWorkflowEngine
from .parallel import ParallelWorkflowEngine
from .interfaces import WorkflowEngineInterface
from ..models.workflow import (
    WorkflowGraph, WorkflowExecution, WorkflowNode, WorkflowEdge,
    NodeExecutionContext, WorkflowTemplate
)
from ..models.enums import WorkflowType, WorkflowStatus, AgentType


logger = logging.getLogger(__name__)


class PatentWorkflowNode(BaseNode):
    """专利工作流节点，扩展基础节点以支持专利特定功能."""
    
    def __init__(self, node_id: str, name: str, agent_type: Optional[AgentType] = None,
                 config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, name, config)
        self.agent_type = agent_type
        self.patent_config = config or {}
        
    async def execute(self, context: NodeExecutionContext) -> Dict[str, Any]:
        """执行专利节点逻辑."""
        start_time = datetime.now()
        
        try:
            # 专利节点特定的执行逻辑
            if self.agent_type:
                result = await self._execute_patent_agent(context)
            else:
                result = await self._execute_patent_control(context)
            
            # 添加专利特定的元数据
            result.update({
                "node_type": "patent_node",
                "agent_type": self.agent_type.value if self.agent_type else None,
                "execution_time": (datetime.now() - start_time).total_seconds(),
                "patent_metadata": self.patent_config
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Patent node {self.node_id} execution failed: {str(e)}")
            return {
                "node_id": self.node_id,
                "status": "failed",
                "error": str(e),
                "execution_time": (datetime.now() - start_time).total_seconds()
            }
    
    async def _execute_patent_agent(self, context: NodeExecutionContext) -> Dict[str, Any]:
        """执行专利Agent节点."""
        # 模拟专利Agent执行
        await asyncio.sleep(0.2)  # 模拟处理时间
        
        agent_name = self.agent_type.value if self.agent_type else "unknown"
        
        return {
            "node_id": self.node_id,
            "status": "completed",
            "output": f"Patent agent {agent_name} processed successfully",
            "data": {
                "agent_type": agent_name,
                "processed_data": context.input_data,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    async def _execute_patent_control(self, context: NodeExecutionContext) -> Dict[str, Any]:
        """执行专利控制节点."""
        control_type = self.patent_config.get("control_type", "generic")
        
        if control_type == "data_aggregation":
            return await self._aggregate_patent_data(context)
        elif control_type == "quality_check":
            return await self._check_patent_quality(context)
        elif control_type == "result_merge":
            return await self._merge_patent_results(context)
        else:
            return {
                "node_id": self.node_id,
                "status": "completed",
                "output": f"Control node {control_type} executed"
            }
    
    async def _aggregate_patent_data(self, context: NodeExecutionContext) -> Dict[str, Any]:
        """聚合专利数据."""
        aggregated_data = {}
        
        # 从共享状态中聚合数据
        for key, value in context.shared_state.items():
            if "patent" in key.lower() or "data" in key.lower():
                aggregated_data[key] = value
        
        return {
            "node_id": self.node_id,
            "status": "completed",
            "output": "Patent data aggregated successfully",
            "aggregated_data": aggregated_data
        }
    
    async def _check_patent_quality(self, context: NodeExecutionContext) -> Dict[str, Any]:
        """检查专利数据质量."""
        quality_score = 0.85  # 模拟质量分数
        
        return {
            "node_id": self.node_id,
            "status": "completed",
            "output": f"Patent data quality check completed (score: {quality_score})",
            "quality_score": quality_score,
            "quality_passed": quality_score > 0.7
        }
    
    async def _merge_patent_results(self, context: NodeExecutionContext) -> Dict[str, Any]:
        """合并专利结果."""
        merged_results = {
            "data_collection": context.shared_state.get("data_collection_result"),
            "search_enhancement": context.shared_state.get("search_result"),
            "analysis": context.shared_state.get("analysis_result"),
            "report": context.shared_state.get("report_result")
        }
        
        return {
            "node_id": self.node_id,
            "status": "completed",
            "output": "Patent results merged successfully",
            "merged_results": merged_results
        }


class PatentGraphBuilder(GraphBuilder):
    """专利工作流图构建器."""
    
    def __init__(self):
        super().__init__()
        self.patent_templates = {}
        
    def add_patent_node(self, node_id: str, name: str, agent_type: Optional[AgentType] = None,
                       config: Optional[Dict[str, Any]] = None) -> 'PatentGraphBuilder':
        """添加专利节点."""
        node = PatentWorkflowNode(node_id, name, agent_type, config)
        return self.add_node(node)
    
    def create_patent_workflow_from_template(self, template_name: str, 
                                           parameters: Dict[str, Any]) -> 'PatentGraphBuilder':
        """从模板创建专利工作流."""
        if template_name not in self.patent_templates:
            raise ValueError(f"Patent workflow template '{template_name}' not found")
        
        template = self.patent_templates[template_name]
        
        # 根据模板创建节点和边
        for node_config in template["nodes"]:
            self.add_patent_node(
                node_id=node_config["node_id"],
                name=node_config["name"],
                agent_type=node_config.get("agent_type"),
                config=node_config.get("config", {})
            )
        
        for edge_config in template["edges"]:
            edge = WorkflowEdge(
                source_node=edge_config["source_node"],
                target_node=edge_config["target_node"],
                condition=edge_config.get("condition")
            )
            self.add_edge(edge)
        
        return self
    
    def register_patent_template(self, template_name: str, template_config: Dict[str, Any]):
        """注册专利工作流模板."""
        self.patent_templates[template_name] = template_config
    
    def build_patent_workflow(self, workflow_type: WorkflowType) -> 'CompiledStateGraph':
        """构建专利工作流图."""
        return self.build(workflow_type)


class PatentWorkflowEngine(WorkflowEngineInterface):
    """专利工作流引擎，整合Sequential和Parallel引擎."""
    
    def __init__(self, state_manager: Optional[WorkflowStateManager] = None):
        self.state_manager = state_manager or WorkflowStateManager()
        self.sequential_engine = SequentialWorkflowEngine()
        self.parallel_engine = ParallelWorkflowEngine()
        
        # 专利工作流模板
        self.workflow_templates = {}
        self._initialize_patent_templates()
        
        # 活跃的专利工作流执行
        self.active_executions: Dict[str, WorkflowExecution] = {}
        
    def _initialize_patent_templates(self):
        """初始化专利工作流模板."""
        # 全面专利分析工作流模板
        self.workflow_templates["comprehensive_patent_analysis"] = WorkflowTemplate(
            name="全面专利分析工作流",
            description="包含数据收集、搜索增强、深度分析和报告生成的完整流程",
            workflow_type=WorkflowType.HIERARCHICAL,
            node_templates=[
                {
                    "node_id": "start",
                    "node_type": "start",
                    "name": "开始节点",
                    "config": {"control_type": "start"}
                },
                {
                    "node_id": "data_collection",
                    "node_type": "agent",
                    "agent_type": AgentType.PATENT_DATA_COLLECTION,
                    "name": "专利数据收集",
                    "config": {"agent_class": "PatentDataCollectionAgent"}
                },
                {
                    "node_id": "search_enhancement",
                    "node_type": "agent", 
                    "agent_type": AgentType.PATENT_SEARCH,
                    "name": "搜索增强",
                    "config": {"agent_class": "PatentSearchAgent"}
                },
                {
                    "node_id": "data_aggregation",
                    "node_type": "control",
                    "name": "数据聚合",
                    "config": {"control_type": "data_aggregation"}
                },
                {
                    "node_id": "patent_analysis",
                    "node_type": "agent",
                    "agent_type": AgentType.PATENT_ANALYSIS,
                    "name": "专利分析",
                    "config": {"agent_class": "PatentAnalysisAgent"}
                },
                {
                    "node_id": "quality_check",
                    "node_type": "control",
                    "name": "质量检查",
                    "config": {"control_type": "quality_check"}
                },
                {
                    "node_id": "report_generation",
                    "node_type": "agent",
                    "agent_type": AgentType.PATENT_REPORT,
                    "name": "报告生成",
                    "config": {"agent_class": "PatentReportAgent"}
                },
                {
                    "node_id": "end",
                    "node_type": "end",
                    "name": "结束节点",
                    "config": {"control_type": "end"}
                }
            ],
            edge_templates=[
                {"source_node": "start", "target_node": "data_collection"},
                {"source_node": "start", "target_node": "search_enhancement"},
                {"source_node": "data_collection", "target_node": "data_aggregation"},
                {"source_node": "search_enhancement", "target_node": "data_aggregation"},
                {"source_node": "data_aggregation", "target_node": "patent_analysis"},
                {"source_node": "patent_analysis", "target_node": "quality_check"},
                {"source_node": "quality_check", "target_node": "report_generation"},
                {"source_node": "report_generation", "target_node": "end"}
            ]
        )
        
        # 快速专利检索工作流模板
        self.workflow_templates["quick_patent_search"] = WorkflowTemplate(
            name="快速专利检索工作流",
            description="快速专利检索和基础分析流程",
            workflow_type=WorkflowType.SEQUENTIAL,
            node_templates=[
                {
                    "node_id": "start",
                    "node_type": "start",
                    "name": "开始节点"
                },
                {
                    "node_id": "patent_search",
                    "node_type": "agent",
                    "agent_type": AgentType.PATENT_SEARCH,
                    "name": "专利检索",
                    "config": {"agent_class": "PatentSearchAgent"}
                },
                {
                    "node_id": "basic_analysis",
                    "node_type": "agent",
                    "agent_type": AgentType.PATENT_ANALYSIS,
                    "name": "基础分析",
                    "config": {"agent_class": "PatentAnalysisAgent", "analysis_type": "basic"}
                },
                {
                    "node_id": "end",
                    "node_type": "end",
                    "name": "结束节点"
                }
            ],
            edge_templates=[
                {"source_node": "start", "target_node": "patent_search"},
                {"source_node": "patent_search", "target_node": "basic_analysis"},
                {"source_node": "basic_analysis", "target_node": "end"}
            ]
        )
        
        # 专利趋势分析工作流模板
        self.workflow_templates["patent_trend_analysis"] = WorkflowTemplate(
            name="专利趋势分析工作流",
            description="专注于专利趋势分析的专门流程",
            workflow_type=WorkflowType.PARALLEL,
            node_templates=[
                {
                    "node_id": "start",
                    "node_type": "start",
                    "name": "开始节点"
                },
                {
                    "node_id": "historical_data",
                    "node_type": "agent",
                    "agent_type": AgentType.PATENT_DATA_COLLECTION,
                    "name": "历史数据收集",
                    "config": {"agent_class": "PatentDataCollectionAgent", "data_type": "historical"}
                },
                {
                    "node_id": "current_data",
                    "node_type": "agent",
                    "agent_type": AgentType.PATENT_DATA_COLLECTION,
                    "name": "当前数据收集",
                    "config": {"agent_class": "PatentDataCollectionAgent", "data_type": "current"}
                },
                {
                    "node_id": "trend_analysis",
                    "node_type": "agent",
                    "agent_type": AgentType.PATENT_ANALYSIS,
                    "name": "趋势分析",
                    "config": {"agent_class": "PatentAnalysisAgent", "analysis_type": "trend"}
                },
                {
                    "node_id": "end",
                    "node_type": "end",
                    "name": "结束节点"
                }
            ],
            edge_templates=[
                {"source_node": "start", "target_node": "historical_data"},
                {"source_node": "start", "target_node": "current_data"},
                {"source_node": "historical_data", "target_node": "trend_analysis"},
                {"source_node": "current_data", "target_node": "trend_analysis"},
                {"source_node": "trend_analysis", "target_node": "end"}
            ]
        )
    
    async def execute_workflow(self, execution: WorkflowExecution) -> WorkflowExecution:
        """执行专利工作流."""
        try:
            # 记录执行开始
            await self.state_manager.start_execution(execution)
            self.active_executions[execution.execution_id] = execution
            
            # 获取工作流图
            workflow_graph = await self._get_workflow_graph(execution.graph_id)
            if not workflow_graph:
                raise ValueError(f"Workflow graph {execution.graph_id} not found")
            
            # 根据工作流类型选择执行引擎
            if workflow_graph.workflow_type == WorkflowType.SEQUENTIAL:
                result = await self.sequential_engine.execute_workflow(execution)
            elif workflow_graph.workflow_type == WorkflowType.PARALLEL:
                result = await self.parallel_engine.execute_workflow(execution)
            elif workflow_graph.workflow_type == WorkflowType.HIERARCHICAL:
                result = await self._execute_hierarchical_workflow(execution, workflow_graph)
            else:
                result = await self.sequential_engine.execute_workflow(execution)
            
            # 更新执行状态
            await self.state_manager.complete_execution(
                execution.execution_id, 
                result.output_data or {}
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Patent workflow execution failed: {str(e)}")
            execution.status = WorkflowStatus.FAILED
            execution.error_message = str(e)
            execution.end_time = datetime.now()
            
            await self.state_manager.fail_execution(execution.execution_id, str(e))
            
            return execution
        
        finally:
            # 清理活跃执行记录
            if execution.execution_id in self.active_executions:
                del self.active_executions[execution.execution_id]
    
    async def _execute_hierarchical_workflow(self, execution: WorkflowExecution, 
                                           workflow_graph: WorkflowGraph) -> WorkflowExecution:
        """执行分层专利工作流."""
        execution.status = WorkflowStatus.RUNNING
        execution.start_time = datetime.now()
        
        try:
            # 分析工作流结构
            layers = self._analyze_workflow_layers(workflow_graph)
            
            # 逐层执行
            for layer_index, layer_nodes in enumerate(layers):
                logger.info(f"Executing layer {layer_index + 1}/{len(layers)} with nodes: {layer_nodes}")
                
                # 创建层执行上下文
                layer_context = NodeExecutionContext(
                    node_id="",
                    execution_id=execution.execution_id,
                    input_data=execution.input_data,
                    shared_state=execution.output_data or {}
                )
                
                # 并行执行当前层的节点
                layer_results = await self._execute_layer_nodes(layer_nodes, layer_context, workflow_graph)
                
                # 更新执行结果
                for node_id, result in layer_results.items():
                    execution.node_results[node_id] = result
                    
                    # 更新共享状态
                    if isinstance(result, dict) and "data" in result:
                        execution.output_data = execution.output_data or {}
                        execution.output_data.update(result["data"])
            
            execution.status = WorkflowStatus.COMPLETED
            execution.end_time = datetime.now()
            
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.error_message = str(e)
            execution.end_time = datetime.now()
            logger.error(f"Hierarchical workflow execution failed: {str(e)}")
        
        return execution
    
    def _analyze_workflow_layers(self, workflow_graph: WorkflowGraph) -> List[List[str]]:
        """分析工作流的层次结构."""
        # 构建邻接表和入度
        graph = {}
        in_degree = {}
        
        for node in workflow_graph.nodes:
            graph[node.node_id] = []
            in_degree[node.node_id] = 0
        
        for edge in workflow_graph.edges:
            if edge.source_node in graph and edge.target_node in in_degree:
                graph[edge.source_node].append(edge.target_node)
                in_degree[edge.target_node] += 1
        
        # 拓扑排序分层
        layers = []
        remaining_nodes = set(in_degree.keys())
        
        while remaining_nodes:
            # 找到当前层的节点（入度为0的节点）
            current_layer = [node for node in remaining_nodes if in_degree[node] == 0]
            
            if not current_layer:
                # 如果没有入度为0的节点，说明有循环依赖，取剩余节点作为一层
                current_layer = list(remaining_nodes)
            
            layers.append(current_layer)
            
            # 更新入度和剩余节点
            for node in current_layer:
                remaining_nodes.remove(node)
                for neighbor in graph[node]:
                    if neighbor in remaining_nodes:
                        in_degree[neighbor] -= 1
        
        return layers
    
    async def _execute_layer_nodes(self, node_ids: List[str], context: NodeExecutionContext,
                                 workflow_graph: WorkflowGraph) -> Dict[str, Any]:
        """执行层中的节点."""
        # 获取节点配置
        node_configs = {node.node_id: node for node in workflow_graph.nodes}
        
        # 创建并行任务
        tasks = []
        for node_id in node_ids:
            if node_id in node_configs:
                node_config = node_configs[node_id]
                task = self._execute_single_node(node_id, node_config, context)
                tasks.append((node_id, task))
        
        # 等待所有任务完成
        results = {}
        for node_id, task in tasks:
            try:
                result = await task
                results[node_id] = result
            except Exception as e:
                logger.error(f"Node {node_id} execution failed: {str(e)}")
                results[node_id] = {
                    "node_id": node_id,
                    "status": "failed",
                    "error": str(e)
                }
        
        return results
    
    async def _execute_single_node(self, node_id: str, node_config: WorkflowNode,
                                 context: NodeExecutionContext) -> Dict[str, Any]:
        """执行单个节点."""
        # 创建专利工作流节点
        patent_node = PatentWorkflowNode(
            node_id=node_id,
            name=node_config.name,
            agent_type=node_config.agent_type,
            config=node_config.config
        )
        
        # 更新上下文
        node_context = NodeExecutionContext(
            node_id=node_id,
            execution_id=context.execution_id,
            input_data=context.input_data,
            shared_state=context.shared_state,
            metadata=context.metadata
        )
        
        # 执行节点
        return await patent_node.execute(node_context)
    
    async def pause_workflow(self, execution_id: str) -> bool:
        """暂停专利工作流."""
        if execution_id in self.active_executions:
            execution = self.active_executions[execution_id]
            execution.status = WorkflowStatus.PAUSED
            
            await self.state_manager.update_execution_state(
                execution_id, 
                {"status": WorkflowStatus.PAUSED.value}
            )
            return True
        return False
    
    async def resume_workflow(self, execution_id: str) -> bool:
        """恢复专利工作流."""
        if execution_id in self.active_executions:
            execution = self.active_executions[execution_id]
            execution.status = WorkflowStatus.RUNNING
            
            await self.state_manager.update_execution_state(
                execution_id,
                {"status": WorkflowStatus.RUNNING.value}
            )
            return True
        return False
    
    async def cancel_workflow(self, execution_id: str) -> bool:
        """取消专利工作流."""
        if execution_id in self.active_executions:
            execution = self.active_executions[execution_id]
            execution.status = WorkflowStatus.CANCELLED
            execution.end_time = datetime.now()
            
            await self.state_manager.update_execution_state(
                execution_id,
                {
                    "status": WorkflowStatus.CANCELLED.value,
                    "end_time": datetime.now().isoformat()
                }
            )
            
            del self.active_executions[execution_id]
            return True
        return False
    
    async def get_workflow_status(self, execution_id: str) -> Optional[WorkflowStatus]:
        """获取专利工作流状态."""
        if execution_id in self.active_executions:
            return self.active_executions[execution_id].status
        
        # 从状态管理器获取
        state = await self.state_manager.get_execution_state(execution_id)
        if state:
            return WorkflowStatus(state.get("status", "unknown"))
        
        return None
    
    async def _get_workflow_graph(self, graph_id: str) -> Optional[WorkflowGraph]:
        """获取工作流图（从模板或存储中）."""
        # 如果graph_id是模板名称，从模板创建图
        if graph_id in self.workflow_templates:
            template = self.workflow_templates[graph_id]
            return self._create_graph_from_template(template)
        
        # 否则从存储中获取（这里是模拟实现）
        return None
    
    def _create_graph_from_template(self, template: WorkflowTemplate) -> WorkflowGraph:
        """从模板创建工作流图."""
        nodes = []
        for node_template in template.node_templates:
            node = WorkflowNode(
                node_id=node_template["node_id"],
                node_type=node_template["node_type"],
                agent_type=node_template.get("agent_type"),
                name=node_template["name"],
                config=node_template.get("config", {})
            )
            nodes.append(node)
        
        edges = []
        for edge_template in template.edge_templates:
            edge = WorkflowEdge(
                source_node=edge_template["source_node"],
                target_node=edge_template["target_node"],
                condition=edge_template.get("condition")
            )
            edges.append(edge)
        
        return WorkflowGraph(
            graph_id=template.template_id,
            name=template.name,
            workflow_type=template.workflow_type,
            nodes=nodes,
            edges=edges,
            entry_point=nodes[0].node_id if nodes else None,
            exit_points=[nodes[-1].node_id] if nodes else []
        )
    
    # 专利工作流引擎特有的方法
    def get_available_templates(self) -> List[str]:
        """获取可用的专利工作流模板."""
        return list(self.workflow_templates.keys())
    
    def get_template_info(self, template_name: str) -> Optional[Dict[str, Any]]:
        """获取模板信息."""
        if template_name in self.workflow_templates:
            template = self.workflow_templates[template_name]
            return {
                "name": template.name,
                "description": template.description,
                "workflow_type": template.workflow_type.value,
                "node_count": len(template.node_templates),
                "edge_count": len(template.edge_templates)
            }
        return None
    
    async def create_execution_from_template(self, template_name: str, 
                                           input_data: Dict[str, Any]) -> WorkflowExecution:
        """从模板创建工作流执行."""
        if template_name not in self.workflow_templates:
            raise ValueError(f"Template '{template_name}' not found")
        
        execution = WorkflowExecution(
            graph_id=template_name,  # 使用模板名称作为图ID
            input_data=input_data,
            status=WorkflowStatus.PENDING
        )
        
        return execution
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """获取执行统计信息."""
        return {
            "active_executions": len(self.active_executions),
            "available_templates": len(self.workflow_templates),
            "supported_workflow_types": [wt.value for wt in WorkflowType],
            "last_updated": datetime.now().isoformat()
        }


class PatentWorkflowFactory:
    """专利工作流工厂类."""
    
    @staticmethod
    def create_comprehensive_analysis_workflow(keywords: List[str]) -> WorkflowExecution:
        """创建全面专利分析工作流执行."""
        return WorkflowExecution(
            graph_id="comprehensive_patent_analysis",
            input_data={
                "keywords": keywords,
                "analysis_type": "comprehensive",
                "output_format": ["html", "pdf"]
            }
        )
    
    @staticmethod
    def create_quick_search_workflow(query: str) -> WorkflowExecution:
        """创建快速专利检索工作流执行."""
        return WorkflowExecution(
            graph_id="quick_patent_search",
            input_data={
                "query": query,
                "search_type": "quick",
                "max_results": 100
            }
        )
    
    @staticmethod
    def create_trend_analysis_workflow(technology_area: str, time_range: str) -> WorkflowExecution:
        """创建专利趋势分析工作流执行."""
        return WorkflowExecution(
            graph_id="patent_trend_analysis",
            input_data={
                "technology_area": technology_area,
                "time_range": time_range,
                "analysis_depth": "detailed"
            }
        )