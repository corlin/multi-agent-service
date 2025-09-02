"""图验证工具和规则."""

from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict, deque

from .interfaces import ValidatorInterface
from ..models.workflow import WorkflowGraph, WorkflowNode, WorkflowEdge, WorkflowExecution
from ..models.enums import WorkflowType, AgentType, WorkflowStatus


class GraphStructureValidator(ValidatorInterface):
    """图结构验证器."""
    
    def validate(self, workflow_graph: WorkflowGraph) -> List[str]:
        """验证工作流图的结构有效性."""
        errors = []
        
        # 基本结构检查
        errors.extend(self._validate_basic_structure(workflow_graph))
        
        # 节点检查
        errors.extend(self._validate_nodes(workflow_graph))
        
        # 边检查
        errors.extend(self._validate_edges(workflow_graph))
        
        # 连通性检查
        errors.extend(self._validate_connectivity(workflow_graph))
        
        # 循环检查
        errors.extend(self._validate_cycles(workflow_graph))
        
        return errors
    
    def is_valid(self, workflow_graph: WorkflowGraph) -> bool:
        """检查工作流图是否有效."""
        return len(self.validate(workflow_graph)) == 0
    
    def _validate_basic_structure(self, workflow_graph: WorkflowGraph) -> List[str]:
        """验证基本结构."""
        errors = []
        
        if not workflow_graph.name:
            errors.append("工作流图名称不能为空")
        
        if not workflow_graph.nodes:
            errors.append("工作流图必须包含至少一个节点")
        
        return errors
    
    def _validate_nodes(self, workflow_graph: WorkflowGraph) -> List[str]:
        """验证节点."""
        errors = []
        node_ids = set()
        
        for node in workflow_graph.nodes:
            # 检查节点ID唯一性
            if node.node_id in node_ids:
                errors.append(f"节点ID重复: {node.node_id}")
            node_ids.add(node.node_id)
            
            # 检查节点名称
            if not node.name:
                errors.append(f"节点 {node.node_id} 名称不能为空")
            
            # 检查节点类型
            if not node.node_type:
                errors.append(f"节点 {node.node_id} 类型不能为空")
        
        return errors
    
    def _validate_edges(self, workflow_graph: WorkflowGraph) -> List[str]:
        """验证边."""
        errors = []
        node_ids = {node.node_id for node in workflow_graph.nodes}
        edge_ids = set()
        
        for edge in workflow_graph.edges:
            # 检查边ID唯一性
            if edge.edge_id in edge_ids:
                errors.append(f"边ID重复: {edge.edge_id}")
            edge_ids.add(edge.edge_id)
            
            # 检查源节点存在性
            if edge.source_node not in node_ids:
                errors.append(f"边 {edge.edge_id} 的源节点 {edge.source_node} 不存在")
            
            # 检查目标节点存在性
            if edge.target_node not in node_ids:
                errors.append(f"边 {edge.edge_id} 的目标节点 {edge.target_node} 不存在")
            
            # 检查自环
            if edge.source_node == edge.target_node:
                errors.append(f"边 {edge.edge_id} 形成自环")
        
        return errors
    
    def _validate_connectivity(self, workflow_graph: WorkflowGraph) -> List[str]:
        """验证连通性."""
        errors = []
        
        if len(workflow_graph.nodes) <= 1:
            return errors
        
        # 构建邻接表
        graph = defaultdict(list)
        for edge in workflow_graph.edges:
            graph[edge.source_node].append(edge.target_node)
        
        # 检查是否所有节点都可达
        node_ids = {node.node_id for node in workflow_graph.nodes}
        
        if workflow_graph.entry_point:
            reachable = self._get_reachable_nodes(graph, workflow_graph.entry_point)
            unreachable = node_ids - reachable
            if unreachable:
                errors.append(f"从入口点无法到达的节点: {', '.join(unreachable)}")
        
        return errors
    
    def _validate_cycles(self, workflow_graph: WorkflowGraph) -> List[str]:
        """验证是否存在循环."""
        errors = []
        
        # 构建邻接表
        graph = defaultdict(list)
        for edge in workflow_graph.edges:
            graph[edge.source_node].append(edge.target_node)
        
        # 检测循环
        cycles = self._detect_cycles(graph)
        if cycles:
            for cycle in cycles:
                errors.append(f"检测到循环: {' -> '.join(cycle)}")
        
        return errors
    
    def _get_reachable_nodes(self, graph: Dict[str, List[str]], start_node: str) -> Set[str]:
        """获取从起始节点可达的所有节点."""
        visited = set()
        queue = deque([start_node])
        
        while queue:
            node = queue.popleft()
            if node not in visited:
                visited.add(node)
                queue.extend(graph.get(node, []))
        
        return visited
    
    def _detect_cycles(self, graph: Dict[str, List[str]]) -> List[List[str]]:
        """检测图中的循环."""
        cycles = []
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    # 找到循环
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
                    return True
            
            rec_stack.remove(node)
            path.pop()
            return False
        
        for node in graph:
            if node not in visited:
                dfs(node)
        
        return cycles


class WorkflowTypeValidator(ValidatorInterface):
    """工作流类型验证器."""
    
    def validate(self, workflow_graph: WorkflowGraph) -> List[str]:
        """根据工作流类型验证图结构."""
        errors = []
        
        if workflow_graph.workflow_type == WorkflowType.SEQUENTIAL:
            errors.extend(self._validate_sequential(workflow_graph))
        elif workflow_graph.workflow_type == WorkflowType.PARALLEL:
            errors.extend(self._validate_parallel(workflow_graph))
        elif workflow_graph.workflow_type == WorkflowType.HIERARCHICAL:
            errors.extend(self._validate_hierarchical(workflow_graph))
        
        return errors
    
    def is_valid(self, workflow_graph: WorkflowGraph) -> bool:
        """检查工作流图是否符合类型要求."""
        return len(self.validate(workflow_graph)) == 0
    
    def _validate_sequential(self, workflow_graph: WorkflowGraph) -> List[str]:
        """验证顺序执行工作流."""
        errors = []
        
        # 顺序执行应该是线性结构
        node_count = len(workflow_graph.nodes)
        edge_count = len(workflow_graph.edges)
        
        if node_count > 1 and edge_count != node_count - 1:
            errors.append("顺序执行工作流应该是线性结构")
        
        # 检查是否有分支
        out_degrees = defaultdict(int)
        in_degrees = defaultdict(int)
        
        for edge in workflow_graph.edges:
            out_degrees[edge.source_node] += 1
            in_degrees[edge.target_node] += 1
        
        for node_id, out_degree in out_degrees.items():
            if out_degree > 1:
                errors.append(f"顺序执行工作流中节点 {node_id} 不应有多个出边")
        
        for node_id, in_degree in in_degrees.items():
            if in_degree > 1:
                errors.append(f"顺序执行工作流中节点 {node_id} 不应有多个入边")
        
        return errors
    
    def _validate_parallel(self, workflow_graph: WorkflowGraph) -> List[str]:
        """验证并行执行工作流."""
        errors = []
        
        # 并行执行应该有明确的开始和结束节点
        in_degrees = defaultdict(int)
        out_degrees = defaultdict(int)
        
        for edge in workflow_graph.edges:
            out_degrees[edge.source_node] += 1
            in_degrees[edge.target_node] += 1
        
        # 应该有一个开始节点（入度为0）
        start_nodes = [node.node_id for node in workflow_graph.nodes if in_degrees[node.node_id] == 0]
        if len(start_nodes) != 1:
            errors.append("并行执行工作流应该有且仅有一个开始节点")
        
        # 应该有一个结束节点（出度为0）
        end_nodes = [node.node_id for node in workflow_graph.nodes if out_degrees[node.node_id] == 0]
        if len(end_nodes) != 1:
            errors.append("并行执行工作流应该有且仅有一个结束节点")
        
        return errors
    
    def _validate_hierarchical(self, workflow_graph: WorkflowGraph) -> List[str]:
        """验证分层执行工作流."""
        errors = []
        
        # 分层执行应该有协调员节点
        coordinator_nodes = [
            node for node in workflow_graph.nodes 
            if node.agent_type == AgentType.COORDINATOR
        ]
        
        if not coordinator_nodes:
            errors.append("分层执行工作流必须包含协调员智能体节点")
        elif len(coordinator_nodes) > 1:
            errors.append("分层执行工作流应该只有一个协调员智能体节点")
        
        return errors


class ExecutionValidator(ValidatorInterface):
    """执行验证器."""
    
    def validate(self, execution: WorkflowExecution) -> List[str]:
        """验证工作流执行状态."""
        errors = []
        
        # 基本字段检查
        if not execution.execution_id:
            errors.append("执行ID不能为空")
        
        if not execution.graph_id:
            errors.append("图ID不能为空")
        
        # 状态一致性检查
        if execution.status == WorkflowStatus.COMPLETED and execution.end_time is None:
            errors.append("已完成的执行应该有结束时间")
        
        if execution.status == WorkflowStatus.RUNNING and execution.current_node is None:
            errors.append("运行中的执行应该有当前节点")
        
        if execution.status == WorkflowStatus.FAILED and not execution.error_message:
            errors.append("失败的执行应该有错误信息")
        
        return errors
    
    def is_valid(self, execution: WorkflowExecution) -> bool:
        """检查执行状态是否有效."""
        return len(self.validate(execution)) == 0


class CompositeValidator(ValidatorInterface):
    """组合验证器，组合多个验证器."""
    
    def __init__(self, validators: List[ValidatorInterface]):
        self.validators = validators
    
    def validate(self, obj: Any) -> List[str]:
        """使用所有验证器验证对象."""
        all_errors = []
        for validator in self.validators:
            errors = validator.validate(obj)
            all_errors.extend(errors)
        return all_errors
    
    def is_valid(self, obj: Any) -> bool:
        """检查对象是否通过所有验证器."""
        return len(self.validate(obj)) == 0


class ValidationManager:
    """验证管理器."""
    
    def __init__(self):
        self.structure_validator = GraphStructureValidator()
        self.type_validator = WorkflowTypeValidator()
        self.execution_validator = ExecutionValidator()
    
    def validate_workflow_graph(self, workflow_graph: WorkflowGraph) -> Tuple[bool, List[str]]:
        """验证工作流图."""
        validator = CompositeValidator([
            self.structure_validator,
            self.type_validator
        ])
        errors = validator.validate(workflow_graph)
        return len(errors) == 0, errors
    
    def validate_execution(self, execution: WorkflowExecution) -> Tuple[bool, List[str]]:
        """验证工作流执行."""
        errors = self.execution_validator.validate(execution)
        return len(errors) == 0, errors
    
    def get_validation_report(self, workflow_graph: WorkflowGraph) -> Dict[str, Any]:
        """获取详细的验证报告."""
        structure_errors = self.structure_validator.validate(workflow_graph)
        type_errors = self.type_validator.validate(workflow_graph)
        
        return {
            "is_valid": len(structure_errors) == 0 and len(type_errors) == 0,
            "structure_validation": {
                "is_valid": len(structure_errors) == 0,
                "errors": structure_errors
            },
            "type_validation": {
                "is_valid": len(type_errors) == 0,
                "errors": type_errors
            },
            "summary": {
                "total_errors": len(structure_errors) + len(type_errors),
                "node_count": len(workflow_graph.nodes),
                "edge_count": len(workflow_graph.edges),
                "workflow_type": workflow_graph.workflow_type.value
            }
        }