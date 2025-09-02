"""测试顺序执行模式实现."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from src.multi_agent_service.workflows.sequential import (
    SequentialGraphBuilder,
    SequentialExecutor,
    SequentialWorkflowEngine,
    SequentialWorkflowFactory,
    SequentialStateManager,
    DataPassingManager
)
from src.multi_agent_service.workflows.graph_builder import (
    AgentNode,
    ControlNode
)
from src.multi_agent_service.models.workflow import (
    WorkflowGraph,
    WorkflowNode,
    WorkflowEdge,
    WorkflowExecution,
    NodeExecutionContext
)
from src.multi_agent_service.models.enums import (
    WorkflowType,
    WorkflowStatus,
    AgentType
)


class TestSequentialGraphBuilder:
    """测试顺序执行图构建器."""
    
    def test_sequential_builder_creation(self):
        """测试顺序构建器创建."""
        builder = SequentialGraphBuilder()
        
        assert len(builder.nodes) == 0
        assert len(builder.edges) == 0
        assert len(builder.execution_order) == 0
    
    def test_set_execution_order(self):
        """测试设置执行顺序."""
        builder = SequentialGraphBuilder()
        order = ["node1", "node2", "node3"]
        
        result = builder.set_execution_order(order)
        
        assert result is builder  # 支持链式调用
        assert builder.execution_order == order
    
    def test_derive_execution_order_from_edges(self):
        """测试从边推导执行顺序."""
        builder = SequentialGraphBuilder()
        
        # 添加节点
        node1 = ControlNode("node1", "Start", "start")
        node2 = AgentNode("node2", "Agent", AgentType.SALES)
        node3 = ControlNode("node3", "End", "end")
        
        builder.add_node(node1)
        builder.add_node(node2)
        builder.add_node(node3)
        
        # 添加边
        edge1 = WorkflowEdge(source_node="node1", target_node="node2")
        edge2 = WorkflowEdge(source_node="node2", target_node="node3")
        
        builder.add_edge(edge1)
        builder.add_edge(edge2)
        
        # 推导执行顺序
        order = builder._derive_execution_order()
        
        assert order == ["node1", "node2", "node3"]
    
    def test_derive_execution_order_no_edges(self):
        """测试没有边时的执行顺序推导."""
        builder = SequentialGraphBuilder()
        
        # 添加节点但不添加边
        node1 = ControlNode("node1", "Node1", "start")
        node2 = ControlNode("node2", "Node2", "end")
        
        builder.add_node(node1)
        builder.add_node(node2)
        
        # 推导执行顺序
        order = builder._derive_execution_order()
        
        # 应该返回所有节点ID
        assert len(order) == 2
        assert "node1" in order
        assert "node2" in order


class TestSequentialExecutor:
    """测试顺序执行器."""
    
    def test_executor_creation(self):
        """测试执行器创建."""
        executor = SequentialExecutor()
        
        assert len(executor.execution_history) == 0
    
    @pytest.mark.asyncio
    async def test_execute_node(self):
        """测试执行单个节点."""
        executor = SequentialExecutor()
        context = NodeExecutionContext(
            node_id="test_node",
            execution_id="test_exec",
            input_data={"input": "test"}
        )
        
        result = await executor.execute_node("test_node", context)
        
        assert result["node_id"] == "test_node"
        assert result["status"] == "completed"
        assert "start_time" in result
        assert "end_time" in result
        assert "output" in result
        assert len(executor.execution_history) == 1
    
    @pytest.mark.asyncio
    async def test_execute_sequential_success(self):
        """测试顺序执行成功场景."""
        executor = SequentialExecutor()
        context = NodeExecutionContext(
            node_id="",
            execution_id="test_exec",
            input_data={"input": "test"},
            shared_state={}
        )
        
        node_ids = ["node1", "node2", "node3"]
        results = await executor.execute_sequential(node_ids, context)
        
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result["node_id"] == node_ids[i]
            assert result["status"] == "completed"
        
        assert len(executor.execution_history) == 3
    
    @pytest.mark.asyncio
    async def test_execute_sequential_with_failure(self):
        """测试顺序执行失败场景."""
        executor = SequentialExecutor()
        
        # 模拟节点执行失败
        original_execute_node = executor.execute_node
        
        async def mock_execute_node(node_id: str, context: NodeExecutionContext):
            if node_id == "node2":
                raise Exception("Node execution failed")
            return await original_execute_node(node_id, context)
        
        executor.execute_node = mock_execute_node
        
        context = NodeExecutionContext(
            node_id="",
            execution_id="test_exec",
            input_data={"input": "test"},
            shared_state={}
        )
        
        node_ids = ["node1", "node2", "node3"]
        results = await executor.execute_sequential(node_ids, context)
        
        # 应该只执行到失败的节点
        assert len(results) == 2
        assert results[0]["status"] == "completed"
        assert results[1]["status"] == "failed"
        assert "error" in results[1]
    
    @pytest.mark.asyncio
    async def test_execute_parallel_not_supported(self):
        """测试并行执行不支持."""
        executor = SequentialExecutor()
        context = NodeExecutionContext(
            node_id="",
            execution_id="test_exec",
            input_data={}
        )
        
        with pytest.raises(NotImplementedError):
            await executor.execute_parallel(["node1", "node2"], context)
    
    @pytest.mark.asyncio
    async def test_execute_conditional(self):
        """测试条件执行."""
        executor = SequentialExecutor()
        context = NodeExecutionContext(
            node_id="",
            execution_id="test_exec",
            input_data={}
        )
        
        result_true = await executor.execute_conditional("true", context)
        result_false = await executor.execute_conditional("false", context)
        result_default = await executor.execute_conditional("unknown", context)
        
        assert result_true == "true"
        assert result_false == "false"
        assert result_default == "default"


class TestSequentialWorkflowEngine:
    """测试顺序工作流引擎."""
    
    def test_engine_creation(self):
        """测试引擎创建."""
        engine = SequentialWorkflowEngine()
        
        assert isinstance(engine.executor, SequentialExecutor)
        assert len(engine.active_executions) == 0
    
    @pytest.mark.asyncio
    async def test_execute_workflow_success(self):
        """测试工作流执行成功."""
        engine = SequentialWorkflowEngine()
        
        execution = WorkflowExecution(
            execution_id="test_exec",
            graph_id="test_graph",
            input_data={"input": "test"}
        )
        
        result = await engine.execute_workflow(execution)
        
        assert result.status == WorkflowStatus.COMPLETED
        assert result.start_time is not None
        assert result.end_time is not None
        assert len(result.node_results) > 0
    
    @pytest.mark.asyncio
    async def test_cancel_workflow(self):
        """测试取消工作流."""
        engine = SequentialWorkflowEngine()
        
        execution = WorkflowExecution(
            execution_id="test_exec",
            graph_id="test_graph"
        )
        
        # 添加到活跃执行中
        engine.active_executions["test_exec"] = execution
        
        result = await engine.cancel_workflow("test_exec")
        
        assert result is True
        assert execution.status == WorkflowStatus.CANCELLED
        assert execution.end_time is not None
        assert "test_exec" not in engine.active_executions
    
    @pytest.mark.asyncio
    async def test_cancel_nonexistent_workflow(self):
        """测试取消不存在的工作流."""
        engine = SequentialWorkflowEngine()
        
        result = await engine.cancel_workflow("nonexistent")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_workflow_status(self):
        """测试获取工作流状态."""
        engine = SequentialWorkflowEngine()
        
        execution = WorkflowExecution(
            execution_id="test_exec",
            graph_id="test_graph",
            status=WorkflowStatus.RUNNING
        )
        
        engine.active_executions["test_exec"] = execution
        
        status = await engine.get_workflow_status("test_exec")
        
        assert status == WorkflowStatus.RUNNING
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_workflow_status(self):
        """测试获取不存在工作流的状态."""
        engine = SequentialWorkflowEngine()
        
        status = await engine.get_workflow_status("nonexistent")
        
        assert status is None
    
    def test_build_execution_order(self):
        """测试构建执行顺序."""
        engine = SequentialWorkflowEngine()
        
        workflow_graph = WorkflowGraph(
            name="Test Workflow",
            workflow_type=WorkflowType.SEQUENTIAL,
            nodes=[
                WorkflowNode(node_id="start", node_type="start", name="Start"),
                WorkflowNode(node_id="middle", node_type="agent", name="Middle"),
                WorkflowNode(node_id="end", node_type="end", name="End")
            ],
            edges=[
                WorkflowEdge(source_node="start", target_node="middle"),
                WorkflowEdge(source_node="middle", target_node="end")
            ]
        )
        
        order = engine._build_execution_order(workflow_graph)
        
        assert order == ["start", "middle", "end"]


class TestSequentialWorkflowFactory:
    """测试顺序工作流工厂."""
    
    def test_create_simple_sequential_workflow(self):
        """测试创建简单顺序工作流."""
        node_configs = [
            {"node_id": "start", "node_type": "start", "name": "Start"},
            {"node_id": "process", "node_type": "agent", "agent_type": AgentType.SALES, "name": "Process"},
            {"node_id": "end", "node_type": "end", "name": "End"}
        ]
        
        workflow = SequentialWorkflowFactory.create_simple_sequential_workflow(
            node_configs, "Test Workflow"
        )
        
        assert workflow.name == "Test Workflow"
        assert workflow.workflow_type == WorkflowType.SEQUENTIAL
        assert len(workflow.nodes) == 3
        assert len(workflow.edges) == 2
        assert workflow.entry_point == "start"
        assert workflow.exit_points == ["end"]
        
        # 检查边的连接
        assert workflow.edges[0].source_node == "start"
        assert workflow.edges[0].target_node == "process"
        assert workflow.edges[1].source_node == "process"
        assert workflow.edges[1].target_node == "end"
    
    def test_create_agent_pipeline(self):
        """测试创建智能体流水线."""
        agent_types = [AgentType.SALES, AgentType.CUSTOMER_SUPPORT, AgentType.MANAGER]
        
        workflow = SequentialWorkflowFactory.create_agent_pipeline(
            agent_types, "Agent Pipeline"
        )
        
        assert workflow.name == "Agent Pipeline"
        assert workflow.workflow_type == WorkflowType.SEQUENTIAL
        assert len(workflow.nodes) == 5  # start + 3 agents + end
        assert len(workflow.edges) == 4
        
        # 检查智能体节点
        agent_nodes = [node for node in workflow.nodes if node.agent_type is not None]
        assert len(agent_nodes) == 3
        
        agent_types_in_workflow = [node.agent_type for node in agent_nodes]
        assert AgentType.SALES in agent_types_in_workflow
        assert AgentType.CUSTOMER_SUPPORT in agent_types_in_workflow
        assert AgentType.MANAGER in agent_types_in_workflow


class TestSequentialStateManager:
    """测试顺序执行状态管理器."""
    
    def test_state_manager_creation(self):
        """测试状态管理器创建."""
        manager = SequentialStateManager()
        
        assert len(manager.state_store) == 0
    
    @pytest.mark.asyncio
    async def test_save_and_get_step_state(self):
        """测试保存和获取步骤状态."""
        manager = SequentialStateManager()
        
        state_data = {"result": "success", "data": {"key": "value"}}
        
        await manager.save_step_state("exec1", 1, "node1", state_data)
        
        retrieved_state = await manager.get_step_state("exec1", 1)
        
        assert retrieved_state is not None
        assert retrieved_state["node_id"] == "node1"
        assert retrieved_state["state_data"] == state_data
        assert "timestamp" in retrieved_state
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_step_state(self):
        """测试获取不存在的步骤状态."""
        manager = SequentialStateManager()
        
        state = await manager.get_step_state("nonexistent", 1)
        
        assert state is None
    
    @pytest.mark.asyncio
    async def test_get_execution_state(self):
        """测试获取执行状态."""
        manager = SequentialStateManager()
        
        # 保存多个步骤状态
        await manager.save_step_state("exec1", 1, "node1", {"step": 1})
        await manager.save_step_state("exec1", 2, "node2", {"step": 2})
        
        execution_state = await manager.get_execution_state("exec1")
        
        assert len(execution_state) == 2
        assert "step_1" in execution_state
        assert "step_2" in execution_state
    
    @pytest.mark.asyncio
    async def test_clear_execution_state(self):
        """测试清理执行状态."""
        manager = SequentialStateManager()
        
        # 保存状态
        await manager.save_step_state("exec1", 1, "node1", {"step": 1})
        
        # 确认状态存在
        state = await manager.get_execution_state("exec1")
        assert len(state) == 1
        
        # 清理状态
        await manager.clear_execution_state("exec1")
        
        # 确认状态已清理
        state = await manager.get_execution_state("exec1")
        assert len(state) == 0


class TestDataPassingManager:
    """测试数据传递管理器."""
    
    def test_prepare_next_step_input_basic(self):
        """测试准备下一步输入数据（基本功能）."""
        current_result = {
            "output": {"processed_data": "result", "count": 5}
        }
        shared_state = {"global_var": "global_value"}
        next_node_config = {}
        
        next_input = DataPassingManager.prepare_next_step_input(
            current_result, shared_state, next_node_config
        )
        
        assert next_input["processed_data"] == "result"
        assert next_input["count"] == 5
        assert next_input["global_var"] == "global_value"
    
    def test_prepare_next_step_input_with_mapping(self):
        """测试带映射的下一步输入数据准备."""
        current_result = {
            "output": {"data": "result", "status": "success"}
        }
        shared_state = {"session_id": "123"}
        next_node_config = {
            "input_mapping": {
                "input_data": "data",
                "execution_status": "status"
            }
        }
        
        next_input = DataPassingManager.prepare_next_step_input(
            current_result, shared_state, next_node_config
        )
        
        assert next_input["input_data"] == "result"
        assert next_input["execution_status"] == "success"
        assert next_input["session_id"] == "123"
    
    def test_extract_shared_data_default(self):
        """测试提取共享数据（默认行为）."""
        node_result = {
            "node_id": "test_node",
            "status": "completed",
            "output": {"shared_var": "shared_value", "result": "success"}
        }
        
        shared_data = DataPassingManager.extract_shared_data(node_result)
        
        assert shared_data["shared_var"] == "shared_value"
        assert shared_data["result"] == "success"
    
    def test_extract_shared_data_with_config(self):
        """测试带配置的共享数据提取."""
        node_result = {
            "node_id": "test_node",
            "status": "completed",
            "output": {"data": "value"},
            "metadata": {"info": "meta"}
        }
        
        extraction_config = {
            "extracted_data": "output",
            "extracted_meta": "metadata"
        }
        
        shared_data = DataPassingManager.extract_shared_data(
            node_result, extraction_config
        )
        
        assert shared_data["extracted_data"] == {"data": "value"}
        assert shared_data["extracted_meta"] == {"info": "meta"}
    
    def test_extract_shared_data_missing_keys(self):
        """测试提取不存在的键."""
        node_result = {"status": "completed"}
        extraction_config = {"missing_key": "nonexistent"}
        
        shared_data = DataPassingManager.extract_shared_data(
            node_result, extraction_config
        )
        
        assert len(shared_data) == 0


class TestIntegration:
    """集成测试."""
    
    @pytest.mark.asyncio
    async def test_complete_sequential_workflow(self):
        """测试完整的顺序工作流执行."""
        # 1. 创建工作流
        agent_types = [AgentType.SALES, AgentType.CUSTOMER_SUPPORT]
        workflow = SequentialWorkflowFactory.create_agent_pipeline(
            agent_types, "Complete Test Workflow"
        )
        
        # 2. 创建执行
        execution = WorkflowExecution(
            execution_id="integration_test",
            graph_id=workflow.graph_id,
            input_data={"customer_query": "I need help with my order"}
        )
        
        # 3. 执行工作流
        engine = SequentialWorkflowEngine()
        result = await engine.execute_workflow(execution)
        
        # 4. 验证结果
        assert result.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]
        assert result.start_time is not None
        assert result.end_time is not None
        assert len(result.node_results) > 0
    
    def test_workflow_builder_integration(self):
        """测试工作流构建器集成."""
        # 1. 使用工厂创建工作流
        workflow = SequentialWorkflowFactory.create_simple_sequential_workflow([
            {"node_id": "start", "node_type": "start", "name": "Start"},
            {"node_id": "agent", "node_type": "agent", "agent_type": AgentType.SALES, "name": "Sales Agent"},
            {"node_id": "end", "node_type": "end", "name": "End"}
        ])
        
        # 2. 使用构建器重建
        builder = SequentialGraphBuilder()
        builder.from_workflow_graph(workflow)
        
        # 3. 验证构建器状态
        assert len(builder.nodes) == 3
        assert len(builder.edges) == 2
        
        # 4. 重新生成工作流图
        rebuilt_workflow = builder.to_workflow_graph("Rebuilt Workflow", WorkflowType.SEQUENTIAL)
        
        assert rebuilt_workflow.workflow_type == WorkflowType.SEQUENTIAL
        assert len(rebuilt_workflow.nodes) == len(workflow.nodes)
        assert len(rebuilt_workflow.edges) == len(workflow.edges)