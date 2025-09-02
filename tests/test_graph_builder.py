"""测试LangGraph图构建器基础框架."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from src.multi_agent_service.workflows.graph_builder import (
    GraphBuilder,
    GraphBuilderFactory,
    BaseNode,
    AgentNode,
    ControlNode,
    GraphState,
    GraphSerializer,
    GraphValidator
)
from src.multi_agent_service.workflows.serialization import (
    WorkflowGraphSerializer,
    JSONSerializer
)
from src.multi_agent_service.workflows.validation import (
    GraphStructureValidator,
    ValidationManager
)
from src.multi_agent_service.models.workflow import (
    WorkflowGraph,
    WorkflowNode,
    WorkflowEdge,
    NodeExecutionContext
)
from src.multi_agent_service.models.enums import (
    WorkflowType,
    AgentType
)


class TestGraphState:
    """测试GraphState模型."""
    
    def test_graph_state_creation(self):
        """测试GraphState创建."""
        state = GraphState(execution_id="test-123")
        
        assert state.execution_id == "test-123"
        assert state.current_step == 0
        assert state.total_steps == 0
        assert state.shared_data == {}
        assert state.node_results == {}
        assert state.messages == []
        assert state.error is None
    
    def test_graph_state_with_data(self):
        """测试带数据的GraphState."""
        state = GraphState(
            execution_id="test-123",
            current_step=2,
            total_steps=5,
            shared_data={"key": "value"},
            node_results={"node1": {"result": "success"}},
            messages=[{"type": "info", "content": "test"}],
            error="test error"
        )
        
        assert state.execution_id == "test-123"
        assert state.current_step == 2
        assert state.total_steps == 5
        assert state.shared_data["key"] == "value"
        assert state.node_results["node1"]["result"] == "success"
        assert len(state.messages) == 1
        assert state.error == "test error"


class TestBaseNode:
    """测试BaseNode基类."""
    
    def test_base_node_creation(self):
        """测试BaseNode创建."""
        
        class TestNode(BaseNode):
            async def execute(self, context: NodeExecutionContext):
                return {"result": "test"}
        
        node = TestNode("node1", "Test Node", {"param": "value"})
        
        assert node.node_id == "node1"
        assert node.name == "Test Node"
        assert node.config["param"] == "value"
    
    def test_base_node_validation(self):
        """测试BaseNode验证方法."""
        
        class TestNode(BaseNode):
            async def execute(self, context: NodeExecutionContext):
                return {"result": "test"}
        
        node = TestNode("node1", "Test Node")
        
        # 默认验证应该返回True
        assert node.validate_input({"input": "data"}) is True
        assert node.validate_output({"output": "data"}) is True


class TestAgentNode:
    """测试AgentNode智能体节点."""
    
    @pytest.mark.asyncio
    async def test_agent_node_creation(self):
        """测试AgentNode创建."""
        node = AgentNode("agent1", "Sales Agent", AgentType.SALES)
        
        assert node.node_id == "agent1"
        assert node.name == "Sales Agent"
        assert node.agent_type == AgentType.SALES
    
    @pytest.mark.asyncio
    async def test_agent_node_execution(self):
        """测试AgentNode执行."""
        node = AgentNode("agent1", "Sales Agent", AgentType.SALES)
        context = NodeExecutionContext(
            node_id="agent1",
            execution_id="exec1",
            input_data={"query": "test"}
        )
        
        result = await node.execute(context)
        
        assert result["node_id"] == "agent1"
        assert result["agent_type"] == "sales"
        assert "result" in result
        assert result["context"]["query"] == "test"


class TestControlNode:
    """测试ControlNode控制节点."""
    
    @pytest.mark.asyncio
    async def test_control_node_start(self):
        """测试开始控制节点."""
        node = ControlNode("start1", "Start Node", "start")
        context = NodeExecutionContext(
            node_id="start1",
            execution_id="exec1"
        )
        
        result = await node.execute(context)
        
        assert result["status"] == "started"
        assert "timestamp" in result
    
    @pytest.mark.asyncio
    async def test_control_node_end(self):
        """测试结束控制节点."""
        node = ControlNode("end1", "End Node", "end")
        context = NodeExecutionContext(
            node_id="end1",
            execution_id="exec1"
        )
        
        result = await node.execute(context)
        
        assert result["status"] == "completed"
        assert "timestamp" in result
    
    @pytest.mark.asyncio
    async def test_control_node_decision(self):
        """测试决策控制节点."""
        node = ControlNode(
            "decision1", 
            "Decision Node", 
            "decision",
            {"condition": "true", "next_node": "node2"}
        )
        context = NodeExecutionContext(
            node_id="decision1",
            execution_id="exec1"
        )
        
        result = await node.execute(context)
        
        assert result["decision"] == "true"
        assert result["next_node"] == "node2"


class TestGraphBuilder:
    """测试GraphBuilder图构建器."""
    
    def test_graph_builder_creation(self):
        """测试GraphBuilder创建."""
        builder = GraphBuilder()
        
        assert len(builder.nodes) == 0
        assert len(builder.edges) == 0
        assert len(builder.node_functions) == 0
    
    def test_add_node(self):
        """测试添加节点."""
        builder = GraphBuilder()
        node = AgentNode("agent1", "Sales Agent", AgentType.SALES)
        
        result = builder.add_node(node)
        
        assert result is builder  # 支持链式调用
        assert "agent1" in builder.nodes
        assert "agent1" in builder.node_functions
        assert builder.nodes["agent1"] is node
    
    def test_add_edge(self):
        """测试添加边."""
        builder = GraphBuilder()
        edge = WorkflowEdge(
            source_node="node1",
            target_node="node2"
        )
        
        result = builder.add_edge(edge)
        
        assert result is builder  # 支持链式调用
        assert len(builder.edges) == 1
        assert builder.edges[0] is edge
    
    def test_from_workflow_graph(self):
        """测试从WorkflowGraph创建构建器."""
        # 创建测试用的WorkflowGraph
        nodes = [
            WorkflowNode(
                node_id="agent1",
                node_type="agent",
                agent_type=AgentType.SALES,
                name="Sales Agent"
            ),
            WorkflowNode(
                node_id="start1",
                node_type="start",
                name="Start Node"
            )
        ]
        edges = [
            WorkflowEdge(
                source_node="start1",
                target_node="agent1"
            )
        ]
        workflow_graph = WorkflowGraph(
            name="Test Workflow",
            workflow_type=WorkflowType.SEQUENTIAL,
            nodes=nodes,
            edges=edges
        )
        
        builder = GraphBuilder()
        result = builder.from_workflow_graph(workflow_graph)
        
        assert result is builder
        assert len(builder.nodes) == 2
        assert len(builder.edges) == 1
        assert "agent1" in builder.nodes
        assert "start1" in builder.nodes
        assert isinstance(builder.nodes["agent1"], AgentNode)
        assert isinstance(builder.nodes["start1"], ControlNode)
    
    def test_to_workflow_graph(self):
        """测试转换为WorkflowGraph."""
        builder = GraphBuilder()
        
        # 添加节点
        agent_node = AgentNode("agent1", "Sales Agent", AgentType.SALES)
        start_node = ControlNode("start1", "Start Node", "start")
        builder.add_node(agent_node)
        builder.add_node(start_node)
        
        # 添加边
        edge = WorkflowEdge(source_node="start1", target_node="agent1")
        builder.add_edge(edge)
        
        # 转换为WorkflowGraph
        workflow_graph = builder.to_workflow_graph("Test Workflow", WorkflowType.SEQUENTIAL)
        
        assert workflow_graph.name == "Test Workflow"
        assert workflow_graph.workflow_type == WorkflowType.SEQUENTIAL
        assert len(workflow_graph.nodes) == 2
        assert len(workflow_graph.edges) == 1
        
        # 检查节点
        node_ids = {node.node_id for node in workflow_graph.nodes}
        assert "agent1" in node_ids
        assert "start1" in node_ids
        
        # 检查边
        assert workflow_graph.edges[0].source_node == "start1"
        assert workflow_graph.edges[0].target_node == "agent1"


class TestGraphBuilderFactory:
    """测试GraphBuilderFactory工厂类."""
    
    def test_create_sequential_builder(self):
        """测试创建顺序执行构建器."""
        builder = GraphBuilderFactory.create_builder(WorkflowType.SEQUENTIAL)
        
        assert isinstance(builder, GraphBuilder)
        assert len(builder.nodes) == 0
        assert len(builder.edges) == 0
    
    def test_create_parallel_builder(self):
        """测试创建并行执行构建器."""
        builder = GraphBuilderFactory.create_builder(WorkflowType.PARALLEL)
        
        assert isinstance(builder, GraphBuilder)
        assert len(builder.nodes) == 0
        assert len(builder.edges) == 0
    
    def test_create_hierarchical_builder(self):
        """测试创建分层执行构建器."""
        builder = GraphBuilderFactory.create_builder(WorkflowType.HIERARCHICAL)
        
        assert isinstance(builder, GraphBuilder)
        assert len(builder.nodes) == 0
        assert len(builder.edges) == 0


class TestGraphSerializer:
    """测试GraphSerializer序列化器."""
    
    def test_serialize_graph(self):
        """测试序列化工作流图."""
        workflow_graph = WorkflowGraph(
            name="Test Workflow",
            workflow_type=WorkflowType.SEQUENTIAL,
            nodes=[
                WorkflowNode(
                    node_id="node1",
                    node_type="agent",
                    agent_type=AgentType.SALES,
                    name="Sales Agent"
                )
            ],
            edges=[]
        )
        
        json_str = GraphSerializer.serialize_graph(workflow_graph)
        
        assert isinstance(json_str, str)
        assert "Test Workflow" in json_str
        assert "sequential" in json_str
        assert "Sales Agent" in json_str
    
    def test_deserialize_graph(self):
        """测试反序列化工作流图."""
        # 先序列化一个图
        original_graph = WorkflowGraph(
            name="Test Workflow",
            workflow_type=WorkflowType.SEQUENTIAL,
            nodes=[
                WorkflowNode(
                    node_id="node1",
                    node_type="agent",
                    agent_type=AgentType.SALES,
                    name="Sales Agent"
                )
            ],
            edges=[]
        )
        
        json_str = GraphSerializer.serialize_graph(original_graph)
        
        # 反序列化
        deserialized_graph = GraphSerializer.deserialize_graph(json_str)
        
        assert deserialized_graph.name == original_graph.name
        assert deserialized_graph.workflow_type == original_graph.workflow_type
        assert len(deserialized_graph.nodes) == len(original_graph.nodes)
        assert deserialized_graph.nodes[0].name == original_graph.nodes[0].name
    
    def test_serialize_to_dict(self):
        """测试序列化为字典."""
        workflow_graph = WorkflowGraph(
            name="Test Workflow",
            workflow_type=WorkflowType.SEQUENTIAL,
            nodes=[],
            edges=[]
        )
        
        data_dict = GraphSerializer.serialize_to_dict(workflow_graph)
        
        assert isinstance(data_dict, dict)
        assert data_dict["name"] == "Test Workflow"
        assert data_dict["workflow_type"] == "sequential"
    
    def test_deserialize_from_dict(self):
        """测试从字典反序列化."""
        data_dict = {
            "graph_id": "test-graph-123",
            "name": "Test Workflow",
            "workflow_type": "sequential",
            "nodes": [],
            "edges": [],
            "entry_point": None,
            "exit_points": [],
            "config": {},
            "created_at": datetime.now().isoformat()
        }
        
        workflow_graph = GraphSerializer.deserialize_from_dict(data_dict)
        
        assert workflow_graph.name == "Test Workflow"
        assert workflow_graph.workflow_type == WorkflowType.SEQUENTIAL
        assert len(workflow_graph.nodes) == 0
        assert len(workflow_graph.edges) == 0


class TestGraphValidator:
    """测试GraphValidator验证器."""
    
    def test_validate_valid_graph(self):
        """测试验证有效图."""
        workflow_graph = WorkflowGraph(
            name="Valid Workflow",
            workflow_type=WorkflowType.SEQUENTIAL,
            nodes=[
                WorkflowNode(
                    node_id="node1",
                    node_type="start",
                    name="Start Node"
                ),
                WorkflowNode(
                    node_id="node2",
                    node_type="agent",
                    agent_type=AgentType.SALES,
                    name="Sales Agent"
                )
            ],
            edges=[
                WorkflowEdge(
                    source_node="node1",
                    target_node="node2"
                )
            ]
        )
        
        errors = GraphValidator.validate_graph(workflow_graph)
        
        assert len(errors) == 0
        assert GraphValidator.is_valid_graph(workflow_graph) is True
    
    def test_validate_empty_graph(self):
        """测试验证空图."""
        workflow_graph = WorkflowGraph(
            name="Empty Workflow",
            workflow_type=WorkflowType.SEQUENTIAL,
            nodes=[],
            edges=[]
        )
        
        errors = GraphValidator.validate_graph(workflow_graph)
        
        assert len(errors) > 0
        assert any("没有节点" in error for error in errors)
        assert GraphValidator.is_valid_graph(workflow_graph) is False
    
    def test_validate_invalid_edge(self):
        """测试验证无效边."""
        workflow_graph = WorkflowGraph(
            name="Invalid Workflow",
            workflow_type=WorkflowType.SEQUENTIAL,
            nodes=[
                WorkflowNode(
                    node_id="node1",
                    node_type="start",
                    name="Start Node"
                )
            ],
            edges=[
                WorkflowEdge(
                    source_node="node1",
                    target_node="nonexistent"  # 不存在的节点
                )
            ]
        )
        
        errors = GraphValidator.validate_graph(workflow_graph)
        
        assert len(errors) > 0
        assert any("不存在" in error for error in errors)
        assert GraphValidator.is_valid_graph(workflow_graph) is False


class TestIntegration:
    """集成测试."""
    
    def test_complete_workflow_creation(self):
        """测试完整的工作流创建流程."""
        # 1. 创建构建器
        builder = GraphBuilderFactory.create_builder(WorkflowType.SEQUENTIAL)
        
        # 2. 添加节点
        start_node = ControlNode("start", "Start", "start")
        agent_node = AgentNode("sales", "Sales Agent", AgentType.SALES)
        end_node = ControlNode("end", "End", "end")
        
        builder.add_node(start_node)
        builder.add_node(agent_node)
        builder.add_node(end_node)
        
        # 3. 添加边
        edge1 = WorkflowEdge(source_node="start", target_node="sales")
        edge2 = WorkflowEdge(source_node="sales", target_node="end")
        
        builder.add_edge(edge1)
        builder.add_edge(edge2)
        
        # 4. 转换为WorkflowGraph
        workflow_graph = builder.to_workflow_graph("Sales Workflow", WorkflowType.SEQUENTIAL)
        
        # 5. 验证图
        is_valid = GraphValidator.is_valid_graph(workflow_graph)
        assert is_valid is True
        
        # 6. 序列化图
        json_str = GraphSerializer.serialize_graph(workflow_graph)
        assert isinstance(json_str, str)
        
        # 7. 反序列化图
        deserialized_graph = GraphSerializer.deserialize_graph(json_str)
        assert deserialized_graph.name == workflow_graph.name
        assert len(deserialized_graph.nodes) == len(workflow_graph.nodes)
        assert len(deserialized_graph.edges) == len(workflow_graph.edges)
    
    @pytest.mark.asyncio
    async def test_node_execution_flow(self):
        """测试节点执行流程."""
        # 创建执行上下文
        context = NodeExecutionContext(
            node_id="test_node",
            execution_id="test_exec",
            input_data={"message": "Hello"},
            shared_state={"step": 1}
        )
        
        # 测试智能体节点执行
        agent_node = AgentNode("agent1", "Test Agent", AgentType.SALES)
        result = await agent_node.execute(context)
        
        assert result["node_id"] == "agent1"
        assert result["agent_type"] == "sales"
        assert "result" in result
        
        # 测试控制节点执行
        control_node = ControlNode("control1", "Test Control", "start")
        result = await control_node.execute(context)
        
        assert result["status"] == "started"
        assert "timestamp" in result