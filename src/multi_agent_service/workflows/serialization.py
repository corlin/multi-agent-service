"""图序列化和反序列化工具."""

import json
import pickle
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from pydantic import BaseModel

from .interfaces import SerializerInterface
from ..models.workflow import WorkflowGraph, WorkflowNode, WorkflowEdge, WorkflowExecution


class JSONSerializer(SerializerInterface):
    """JSON序列化器."""
    
    def serialize(self, obj: Any) -> str:
        """序列化对象为JSON字符串."""
        if isinstance(obj, BaseModel):
            return obj.model_dump_json(indent=2)
        elif isinstance(obj, dict):
            return json.dumps(obj, indent=2, default=self._json_serializer)
        else:
            return json.dumps(obj, indent=2, default=self._json_serializer)
    
    def deserialize(self, data: str) -> Any:
        """从JSON字符串反序列化对象."""
        return json.loads(data)
    
    def _json_serializer(self, obj: Any) -> Any:
        """自定义JSON序列化器，处理特殊类型."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return str(obj)


class PickleSerializer(SerializerInterface):
    """Pickle序列化器，用于Python对象的二进制序列化."""
    
    def serialize(self, obj: Any) -> str:
        """序列化对象为base64编码的字符串."""
        import base64
        pickled_data = pickle.dumps(obj)
        return base64.b64encode(pickled_data).decode('utf-8')
    
    def deserialize(self, data: str) -> Any:
        """从base64编码的字符串反序列化对象."""
        import base64
        pickled_data = base64.b64decode(data.encode('utf-8'))
        return pickle.loads(pickled_data)


class WorkflowGraphSerializer:
    """工作流图专用序列化器."""
    
    def __init__(self, serializer: SerializerInterface = None):
        self.serializer = serializer or JSONSerializer()
    
    def serialize_graph(self, workflow_graph: WorkflowGraph) -> str:
        """序列化工作流图."""
        return self.serializer.serialize(workflow_graph)
    
    def deserialize_graph(self, data: str) -> WorkflowGraph:
        """反序列化工作流图."""
        graph_data = self.serializer.deserialize(data)
        return WorkflowGraph(**graph_data)
    
    def serialize_to_dict(self, workflow_graph: WorkflowGraph) -> Dict[str, Any]:
        """序列化工作流图为字典."""
        return workflow_graph.model_dump()
    
    def deserialize_from_dict(self, data: Dict[str, Any]) -> WorkflowGraph:
        """从字典反序列化工作流图."""
        return WorkflowGraph(**data)
    
    def export_to_file(self, workflow_graph: WorkflowGraph, file_path: str) -> bool:
        """导出工作流图到文件."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.serialize_graph(workflow_graph))
            return True
        except Exception:
            return False
    
    def import_from_file(self, file_path: str) -> Optional[WorkflowGraph]:
        """从文件导入工作流图."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = f.read()
            return self.deserialize_graph(data)
        except Exception:
            return None


class WorkflowExecutionSerializer:
    """工作流执行序列化器."""
    
    def __init__(self, serializer: SerializerInterface = None):
        self.serializer = serializer or JSONSerializer()
    
    def serialize_execution(self, execution: WorkflowExecution) -> str:
        """序列化工作流执行."""
        return self.serializer.serialize(execution)
    
    def deserialize_execution(self, data: str) -> WorkflowExecution:
        """反序列化工作流执行."""
        execution_data = self.serializer.deserialize(data)
        return WorkflowExecution(**execution_data)
    
    def serialize_execution_state(self, execution: WorkflowExecution) -> Dict[str, Any]:
        """序列化执行状态为字典."""
        return {
            "execution_id": execution.execution_id,
            "graph_id": execution.graph_id,
            "status": execution.status.value,
            "current_node": execution.current_node,
            "node_results": execution.node_results,
            "input_data": execution.input_data,
            "output_data": execution.output_data,
            "error_message": execution.error_message,
            "start_time": execution.start_time.isoformat() if execution.start_time else None,
            "end_time": execution.end_time.isoformat() if execution.end_time else None
        }
    
    def deserialize_execution_state(self, data: Dict[str, Any]) -> WorkflowExecution:
        """从字典反序列化执行状态."""
        # 处理时间字段
        if data.get("start_time"):
            data["start_time"] = datetime.fromisoformat(data["start_time"])
        if data.get("end_time"):
            data["end_time"] = datetime.fromisoformat(data["end_time"])
        
        return WorkflowExecution(**data)


class GraphSchemaSerializer:
    """图模式序列化器，用于生成图的结构描述."""
    
    def serialize_schema(self, workflow_graph: WorkflowGraph) -> Dict[str, Any]:
        """序列化图模式."""
        schema = {
            "graph_id": workflow_graph.graph_id,
            "name": workflow_graph.name,
            "workflow_type": workflow_graph.workflow_type.value,
            "nodes": [],
            "edges": [],
            "metadata": {
                "node_count": len(workflow_graph.nodes),
                "edge_count": len(workflow_graph.edges),
                "entry_point": workflow_graph.entry_point,
                "exit_points": workflow_graph.exit_points,
                "created_at": workflow_graph.created_at.isoformat()
            }
        }
        
        # 序列化节点
        for node in workflow_graph.nodes:
            node_schema = {
                "node_id": node.node_id,
                "name": node.name,
                "node_type": node.node_type,
                "agent_type": node.agent_type.value if node.agent_type else None,
                "description": node.description,
                "input_schema": node.input_schema,
                "output_schema": node.output_schema
            }
            schema["nodes"].append(node_schema)
        
        # 序列化边
        for edge in workflow_graph.edges:
            edge_schema = {
                "edge_id": edge.edge_id,
                "source_node": edge.source_node,
                "target_node": edge.target_node,
                "condition": edge.condition,
                "weight": edge.weight
            }
            schema["edges"].append(edge_schema)
        
        return schema
    
    def generate_mermaid_diagram(self, workflow_graph: WorkflowGraph) -> str:
        """生成Mermaid流程图代码."""
        lines = ["graph TD"]
        
        # 添加节点
        for node in workflow_graph.nodes:
            node_label = f"{node.name}"
            if node.agent_type:
                node_label += f"\\n({node.agent_type.value})"
            lines.append(f"    {node.node_id}[\"{node_label}\"]")
        
        # 添加边
        for edge in workflow_graph.edges:
            if edge.condition:
                lines.append(f"    {edge.source_node} -->|{edge.condition}| {edge.target_node}")
            else:
                lines.append(f"    {edge.source_node} --> {edge.target_node}")
        
        return "\n".join(lines)
    
    def generate_dot_diagram(self, workflow_graph: WorkflowGraph) -> str:
        """生成Graphviz DOT格式的图描述."""
        lines = ["digraph workflow {"]
        lines.append("    rankdir=TB;")
        lines.append("    node [shape=box];")
        
        # 添加节点
        for node in workflow_graph.nodes:
            label = node.name
            if node.agent_type:
                label += f"\\n({node.agent_type.value})"
            lines.append(f'    {node.node_id} [label="{label}"];')
        
        # 添加边
        for edge in workflow_graph.edges:
            if edge.condition:
                lines.append(f'    {edge.source_node} -> {edge.target_node} [label="{edge.condition}"];')
            else:
                lines.append(f'    {edge.source_node} -> {edge.target_node};')
        
        lines.append("}")
        return "\n".join(lines)


class SerializationManager:
    """序列化管理器，统一管理各种序列化器."""
    
    def __init__(self):
        self.serializers: Dict[str, SerializerInterface] = {
            "json": JSONSerializer(),
            "pickle": PickleSerializer()
        }
        self.graph_serializer = WorkflowGraphSerializer()
        self.execution_serializer = WorkflowExecutionSerializer()
        self.schema_serializer = GraphSchemaSerializer()
    
    def register_serializer(self, name: str, serializer: SerializerInterface) -> None:
        """注册新的序列化器."""
        self.serializers[name] = serializer
    
    def get_serializer(self, name: str) -> Optional[SerializerInterface]:
        """获取序列化器."""
        return self.serializers.get(name)
    
    def serialize_with(self, serializer_name: str, obj: Any) -> Optional[str]:
        """使用指定序列化器序列化对象."""
        serializer = self.get_serializer(serializer_name)
        if serializer:
            return serializer.serialize(obj)
        return None
    
    def deserialize_with(self, serializer_name: str, data: str) -> Any:
        """使用指定序列化器反序列化对象."""
        serializer = self.get_serializer(serializer_name)
        if serializer:
            return serializer.deserialize(data)
        return None