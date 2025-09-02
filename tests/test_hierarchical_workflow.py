"""测试分层执行模式实现."""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from src.multi_agent_service.workflows.hierarchical import (
    TaskPriority,
    TaskStatus,
    SubTask,
    CoordinatorAgent,
    HierarchicalGraphBuilder,
    HierarchicalExecutor,
    HierarchicalWorkflowEngine,
    HierarchicalWorkflowFactory,
    ConflictResolver
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


class TestSubTask:
    """测试SubTask子任务模型."""
    
    def test_subtask_creation(self):
        """测试子任务创建."""
        subtask = SubTask(
            task_id="test_task",
            name="Test Task",
            agent_type=AgentType.SALES,
            input_data={"key": "value"},
            priority=TaskPriority.HIGH,
            dependencies=["dep1", "dep2"]
        )
        
        assert subtask.task_id == "test_task"
        assert subtask.name == "Test Task"
        assert subtask.agent_type == AgentType.SALES
        assert subtask.input_data["key"] == "value"
        assert subtask.priority == TaskPriority.HIGH
        assert subtask.dependencies == ["dep1", "dep2"]
        assert subtask.status == TaskStatus.PENDING
        assert subtask.assigned_agent is None
        assert subtask.result is None
    
    def test_subtask_to_dict(self):
        """测试子任务转换为字典."""
        subtask = SubTask(
            task_id="test_task",
            name="Test Task",
            agent_type=AgentType.SALES,
            input_data={"key": "value"}
        )
        
        task_dict = subtask.to_dict()
        
        assert task_dict["task_id"] == "test_task"
        assert task_dict["name"] == "Test Task"
        assert task_dict["agent_type"] == "sales"
        assert task_dict["input_data"]["key"] == "value"
        assert task_dict["status"] == "pending"


class TestCoordinatorAgent:
    """测试CoordinatorAgent协调员智能体."""
    
    def test_coordinator_creation(self):
        """测试协调员创建."""
        coordinator = CoordinatorAgent("test_coordinator")
        
        assert coordinator.coordinator_id == "test_coordinator"
        assert len(coordinator.subtasks) == 0
        assert len(coordinator.agent_workload) == 0
        assert len(coordinator.task_queue) == 0
        assert len(coordinator.completed_tasks) == 0
        assert len(coordinator.failed_tasks) == 0
    
    @pytest.mark.asyncio
    async def test_decompose_customer_inquiry(self):
        """测试客户咨询任务分解."""
        coordinator = CoordinatorAgent()
        context = NodeExecutionContext(
            node_id="coordinator",
            execution_id="test_exec",
            input_data={}
        )
        
        main_task = {
            "type": "customer_inquiry",
            "query": "I have a problem with my order",
            "customer_id": "12345"
        }
        
        subtasks = await coordinator.decompose_task(main_task, context)
        
        assert len(subtasks) == 3
        assert subtasks[0].task_id == "intent_analysis"
        assert subtasks[1].task_id == "info_gathering"
        assert subtasks[2].task_id == "solution_provision"
        
        # 检查依赖关系
        assert "intent_analysis" in subtasks[1].dependencies
        assert "info_gathering" in subtasks[2].dependencies
    
    @pytest.mark.asyncio
    async def test_decompose_sales_process(self):
        """测试销售流程任务分解."""
        coordinator = CoordinatorAgent()
        context = NodeExecutionContext(
            node_id="coordinator",
            execution_id="test_exec",
            input_data={}
        )
        
        main_task = {
            "type": "sales_process",
            "customer_profile": {"name": "John Doe"},
            "requirements": {"budget": 10000}
        }
        
        subtasks = await coordinator.decompose_task(main_task, context)
        
        assert len(subtasks) == 4
        task_ids = [task.task_id for task in subtasks]
        assert "needs_analysis" in task_ids
        assert "product_recommendation" in task_ids
        assert "quote_generation" in task_ids
        assert "management_approval" in task_ids
        
        # 检查管理审批任务的优先级
        approval_task = next(task for task in subtasks if task.task_id == "management_approval")
        assert approval_task.priority == TaskPriority.HIGH
    
    @pytest.mark.asyncio
    async def test_decompose_technical_support(self):
        """测试技术支持任务分解."""
        coordinator = CoordinatorAgent()
        context = NodeExecutionContext(
            node_id="coordinator",
            execution_id="test_exec",
            input_data={}
        )
        
        main_task = {
            "type": "technical_support",
            "symptoms": ["system crash", "data loss"]
        }
        
        subtasks = await coordinator.decompose_task(main_task, context)
        
        assert len(subtasks) == 3
        task_ids = [task.task_id for task in subtasks]
        assert "problem_diagnosis" in task_ids
        assert "solution_planning" in task_ids
        assert "resource_scheduling" in task_ids
        
        # 检查问题诊断任务的优先级
        diagnosis_task = next(task for task in subtasks if task.task_id == "problem_diagnosis")
        assert diagnosis_task.priority == TaskPriority.URGENT
    
    @pytest.mark.asyncio
    async def test_schedule_tasks(self):
        """测试任务调度."""
        coordinator = CoordinatorAgent()
        
        # 创建测试任务
        task1 = SubTask("task1", "Task 1", AgentType.SALES, {}, TaskPriority.HIGH)
        task2 = SubTask("task2", "Task 2", AgentType.SALES, {}, TaskPriority.NORMAL, ["task1"])
        task3 = SubTask("task3", "Task 3", AgentType.SALES, {}, TaskPriority.URGENT)
        
        coordinator.subtasks = {
            "task1": task1,
            "task2": task2,
            "task3": task3
        }
        coordinator.task_queue = ["task1", "task2", "task3"]
        
        # 调度任务
        ready_tasks = await coordinator.schedule_tasks()
        
        # task1和task3应该就绪（没有依赖），task2有依赖不就绪
        assert len(ready_tasks) == 2
        assert "task1" in ready_tasks
        assert "task3" in ready_tasks
        assert "task2" not in ready_tasks
        
        # 检查优先级排序（URGENT > HIGH）
        assert ready_tasks[0] == "task3"  # URGENT优先级最高
    
    @pytest.mark.asyncio
    async def test_task_lifecycle(self):
        """测试任务生命周期管理."""
        coordinator = CoordinatorAgent()
        
        # 创建任务
        task = SubTask("test_task", "Test Task", AgentType.SALES, {})
        coordinator.subtasks["test_task"] = task
        
        # 分配任务
        success = await coordinator.assign_task("test_task", "agent_1")
        assert success is True
        assert task.status == TaskStatus.ASSIGNED
        assert task.assigned_agent == "agent_1"
        assert coordinator.agent_workload["agent_1"] == 1
        
        # 开始任务
        success = await coordinator.start_task("test_task")
        assert success is True
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.start_time is not None
        
        # 完成任务
        result = {"output": "task completed"}
        success = await coordinator.complete_task("test_task", result)
        assert success is True
        assert task.status == TaskStatus.COMPLETED
        assert task.result == result
        assert task.end_time is not None
        assert "test_task" in coordinator.completed_tasks
        assert coordinator.agent_workload["agent_1"] == 0
    
    @pytest.mark.asyncio
    async def test_task_failure(self):
        """测试任务失败处理."""
        coordinator = CoordinatorAgent()
        
        # 创建和分配任务
        task = SubTask("failing_task", "Failing Task", AgentType.SALES, {})
        coordinator.subtasks["failing_task"] = task
        await coordinator.assign_task("failing_task", "agent_1")
        await coordinator.start_task("failing_task")
        
        # 任务失败
        error_message = "Task execution failed"
        success = await coordinator.fail_task("failing_task", error_message)
        
        assert success is True
        assert task.status == TaskStatus.FAILED
        assert task.error_message == error_message
        assert task.end_time is not None
        assert "failing_task" in coordinator.failed_tasks
        assert coordinator.agent_workload["agent_1"] == 0
    
    @pytest.mark.asyncio
    async def test_execution_summary(self):
        """测试执行摘要生成."""
        coordinator = CoordinatorAgent("test_coordinator")
        
        # 创建多个任务
        tasks = [
            SubTask("task1", "Task 1", AgentType.SALES, {}),
            SubTask("task2", "Task 2", AgentType.CUSTOMER_SUPPORT, {}),
            SubTask("task3", "Task 3", AgentType.MANAGER, {})
        ]
        
        for task in tasks:
            coordinator.subtasks[task.task_id] = task
        
        # 模拟任务执行状态
        coordinator.completed_tasks.add("task1")
        coordinator.failed_tasks.add("task2")
        coordinator.subtasks["task3"].status = TaskStatus.IN_PROGRESS
        
        summary = await coordinator.get_execution_summary()
        
        assert summary["coordinator_id"] == "test_coordinator"
        assert summary["total_tasks"] == 3
        assert summary["completed_tasks"] == 1
        assert summary["failed_tasks"] == 1
        assert summary["in_progress_tasks"] == 1
        assert summary["success_rate"] == 1/3


class TestHierarchicalGraphBuilder:
    """测试分层执行图构建器."""
    
    def test_hierarchical_builder_creation(self):
        """测试分层构建器创建."""
        builder = HierarchicalGraphBuilder()
        
        assert len(builder.nodes) == 0
        assert len(builder.edges) == 0
        assert builder.coordinator_node is None
        assert len(builder.worker_nodes) == 0
        assert len(builder.task_flow) == 0
    
    def test_set_coordinator(self):
        """测试设置协调员节点."""
        builder = HierarchicalGraphBuilder()
        
        result = builder.set_coordinator("coordinator_1")
        
        assert result is builder  # 支持链式调用
        assert builder.coordinator_node == "coordinator_1"
    
    def test_add_worker_nodes(self):
        """测试添加工作节点."""
        builder = HierarchicalGraphBuilder()
        
        result = builder.add_worker_nodes(["worker1", "worker2", "worker3"])
        
        assert result is builder  # 支持链式调用
        assert len(builder.worker_nodes) == 3
        assert "worker1" in builder.worker_nodes
        assert "worker2" in builder.worker_nodes
        assert "worker3" in builder.worker_nodes
    
    def test_set_task_flow(self):
        """测试设置任务流程."""
        builder = HierarchicalGraphBuilder()
        flow = {"coordinator": ["worker1", "worker2"], "worker1": ["worker3"]}
        
        result = builder.set_task_flow(flow)
        
        assert result is builder  # 支持链式调用
        assert builder.task_flow == flow


class TestHierarchicalExecutor:
    """测试分层执行器."""
    
    def test_executor_creation(self):
        """测试执行器创建."""
        executor = HierarchicalExecutor()
        
        assert isinstance(executor.coordinator, CoordinatorAgent)
        assert len(executor.execution_history) == 0
        assert len(executor.active_tasks) == 0
    
    @pytest.mark.asyncio
    async def test_execute_node(self):
        """测试执行单个节点."""
        executor = HierarchicalExecutor()
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
        assert len(executor.execution_history) == 1
    
    @pytest.mark.asyncio
    async def test_execute_hierarchical_simple(self):
        """测试简单分层执行."""
        executor = HierarchicalExecutor()
        context = NodeExecutionContext(
            node_id="coordinator",
            execution_id="test_exec",
            input_data={}
        )
        
        main_task = {
            "type": "general",
            "input_data": {"message": "test task"}
        }
        
        result = await executor.execute_hierarchical(main_task, context)
        
        assert "main_task" in result
        assert "subtasks" in result
        assert "execution_log" in result
        assert "final_result" in result
        assert len(result["subtasks"]) > 0
        assert len(result["execution_log"]) > 0
    
    @pytest.mark.asyncio
    async def test_execute_hierarchical_customer_inquiry(self):
        """测试客户咨询分层执行."""
        executor = HierarchicalExecutor()
        context = NodeExecutionContext(
            node_id="coordinator",
            execution_id="test_exec",
            input_data={}
        )
        
        main_task = {
            "type": "customer_inquiry",
            "query": "I need help with my order",
            "customer_id": "12345"
        }
        
        result = await executor.execute_hierarchical(main_task, context)
        
        # 检查客户咨询特定的子任务
        subtask_ids = [task["task_id"] for task in result["subtasks"]]
        assert "intent_analysis" in subtask_ids
        assert "info_gathering" in subtask_ids
        assert "solution_provision" in subtask_ids
        
        # 检查执行日志
        assert len(result["execution_log"]) >= 3
        
        # 检查最终结果
        final_result = result["final_result"]
        assert "total_tasks" in final_result
        assert "completed_tasks" in final_result
        assert "success_rate" in final_result


class TestHierarchicalWorkflowEngine:
    """测试分层工作流引擎."""
    
    def test_engine_creation(self):
        """测试引擎创建."""
        engine = HierarchicalWorkflowEngine()
        
        assert isinstance(engine.executor, HierarchicalExecutor)
        assert len(engine.active_executions) == 0
    
    @pytest.mark.asyncio
    async def test_execute_workflow_success(self):
        """测试工作流执行成功."""
        engine = HierarchicalWorkflowEngine()
        
        execution = WorkflowExecution(
            execution_id="test_exec",
            graph_id="test_graph",
            input_data={
                "task_type": "customer_inquiry",
                "query": "I need help",
                "customer_id": "12345"
            }
        )
        
        result = await engine.execute_workflow(execution)
        
        assert result.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]
        assert result.start_time is not None
        assert result.end_time is not None
        assert len(result.node_results) > 0
        assert "coordinator" in result.node_results
    
    @pytest.mark.asyncio
    async def test_cancel_workflow(self):
        """测试取消工作流."""
        engine = HierarchicalWorkflowEngine()
        
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
    async def test_pause_resume_workflow(self):
        """测试暂停和恢复工作流."""
        engine = HierarchicalWorkflowEngine()
        
        execution = WorkflowExecution(
            execution_id="test_exec",
            graph_id="test_graph"
        )
        
        engine.active_executions["test_exec"] = execution
        
        # 测试暂停
        pause_result = await engine.pause_workflow("test_exec")
        assert pause_result is True
        
        # 测试恢复
        resume_result = await engine.resume_workflow("test_exec")
        assert resume_result is True


class TestHierarchicalWorkflowFactory:
    """测试分层工作流工厂."""
    
    def test_create_hierarchical_workflow(self):
        """测试创建分层工作流."""
        coordinator_config = {
            "node_id": "coordinator",
            "name": "Main Coordinator"
        }
        
        worker_configs = [
            {"node_id": "sales_worker", "agent_type": AgentType.SALES, "name": "Sales Worker"},
            {"node_id": "support_worker", "agent_type": AgentType.CUSTOMER_SUPPORT, "name": "Support Worker"},
            {"node_id": "manager_worker", "agent_type": AgentType.MANAGER, "name": "Manager Worker"}
        ]
        
        workflow = HierarchicalWorkflowFactory.create_hierarchical_workflow(
            coordinator_config, worker_configs, "Test Hierarchical Workflow"
        )
        
        assert workflow.name == "Test Hierarchical Workflow"
        assert workflow.workflow_type == WorkflowType.HIERARCHICAL
        assert len(workflow.nodes) == 4  # 1 coordinator + 3 workers
        assert len(workflow.edges) == 6  # coordinator->workers + workers->coordinator
        assert workflow.entry_point == "coordinator"
        assert workflow.exit_points == ["coordinator"]
        
        # 检查协调员节点
        coordinator_node = next(node for node in workflow.nodes if node.node_id == "coordinator")
        assert coordinator_node.agent_type == AgentType.COORDINATOR
        
        # 检查工作节点
        worker_nodes = [node for node in workflow.nodes if node.node_type == "worker"]
        assert len(worker_nodes) == 3
        
        worker_agent_types = {node.agent_type for node in worker_nodes}
        assert AgentType.SALES in worker_agent_types
        assert AgentType.CUSTOMER_SUPPORT in worker_agent_types
        assert AgentType.MANAGER in worker_agent_types
    
    def test_create_multi_level_hierarchy(self):
        """测试创建多层级分层工作流."""
        levels = [
            [{"node_id": "top_manager", "agent_type": AgentType.MANAGER, "name": "Top Manager"}],
            [
                {"node_id": "sales_manager", "agent_type": AgentType.SALES, "name": "Sales Manager"},
                {"node_id": "support_manager", "agent_type": AgentType.CUSTOMER_SUPPORT, "name": "Support Manager"}
            ],
            [
                {"node_id": "sales_agent1", "agent_type": AgentType.SALES, "name": "Sales Agent 1"},
                {"node_id": "sales_agent2", "agent_type": AgentType.SALES, "name": "Sales Agent 2"},
                {"node_id": "support_agent", "agent_type": AgentType.CUSTOMER_SUPPORT, "name": "Support Agent"}
            ]
        ]
        
        workflow = HierarchicalWorkflowFactory.create_multi_level_hierarchy(
            levels, "Multi-Level Hierarchy"
        )
        
        assert workflow.name == "Multi-Level Hierarchy"
        assert workflow.workflow_type == WorkflowType.HIERARCHICAL
        assert len(workflow.nodes) == 6  # 1 + 2 + 3 nodes
        assert workflow.entry_point == "top_manager"
        
        # 检查层级连接
        # 第一层到第二层：1 * 2 = 2 条边
        # 第二层到第三层：2 * 3 = 6 条边
        # 总共 8 条边
        assert len(workflow.edges) == 8


class TestConflictResolver:
    """测试冲突解决器."""
    
    def test_resolver_creation(self):
        """测试解决器创建."""
        resolver = ConflictResolver()
        
        assert len(resolver.resolution_strategies) == 4
        assert "priority_based" in resolver.resolution_strategies
        assert "resource_based" in resolver.resolution_strategies
        assert "consensus" in resolver.resolution_strategies
        assert "escalation" in resolver.resolution_strategies
    
    @pytest.mark.asyncio
    async def test_resolve_by_priority(self):
        """测试基于优先级的冲突解决."""
        resolver = ConflictResolver()
        
        tasks = [
            SubTask("task1", "Task 1", AgentType.SALES, {}, TaskPriority.NORMAL),
            SubTask("task2", "Task 2", AgentType.SALES, {}, TaskPriority.URGENT),
            SubTask("task3", "Task 3", AgentType.SALES, {}, TaskPriority.HIGH)
        ]
        
        resolution = await resolver.resolve_conflict(tasks, "priority_based")
        
        assert resolution["strategy"] == "priority_based"
        assert resolution["winner"] == "task2"  # URGENT优先级最高
        assert resolution["execution_order"][0] == "task2"
        assert resolution["execution_order"][1] == "task3"  # HIGH第二
        assert resolution["execution_order"][2] == "task1"  # NORMAL最后
    
    @pytest.mark.asyncio
    async def test_resolve_by_resource(self):
        """测试基于资源的冲突解决."""
        resolver = ConflictResolver()
        
        tasks = [
            SubTask("task1", "Task 1", AgentType.SALES, {"data": "large_dataset", "params": [1, 2, 3]}),
            SubTask("task2", "Task 2", AgentType.SALES, {"simple": "task"}),
            SubTask("task3", "Task 3", AgentType.SALES, {"medium": "complexity", "config": {}})
        ]
        
        resolution = await resolver.resolve_conflict(tasks, "resource_based")
        
        assert resolution["strategy"] == "resource_based"
        assert resolution["winner"] == "task2"  # 资源需求最少
        assert "resource_scores" in resolution
    
    @pytest.mark.asyncio
    async def test_resolve_by_consensus(self):
        """测试基于共识的冲突解决."""
        resolver = ConflictResolver()
        
        tasks = [
            SubTask("task1", "Task 1", AgentType.SALES, {}),
            SubTask("task2", "Task 2", AgentType.SALES, {})
        ]
        
        resolution = await resolver.resolve_conflict(tasks, "consensus")
        
        assert resolution["strategy"] == "consensus"
        assert resolution["winner"] == "task1"  # 简化实现选择第一个
    
    @pytest.mark.asyncio
    async def test_resolve_by_escalation(self):
        """测试通过升级解决冲突."""
        resolver = ConflictResolver()
        
        tasks = [
            SubTask("task1", "Task 1", AgentType.SALES, {}),
            SubTask("task2", "Task 2", AgentType.SALES, {})
        ]
        
        resolution = await resolver.resolve_conflict(tasks, "escalation")
        
        assert resolution["strategy"] == "escalation"
        assert resolution["escalated_to"] == "management"
        assert len(resolution["pending_tasks"]) == 2
    
    @pytest.mark.asyncio
    async def test_resolve_unknown_strategy(self):
        """测试未知策略回退到默认策略."""
        resolver = ConflictResolver()
        
        tasks = [
            SubTask("task1", "Task 1", AgentType.SALES, {}, TaskPriority.HIGH),
            SubTask("task2", "Task 2", AgentType.SALES, {}, TaskPriority.LOW)
        ]
        
        resolution = await resolver.resolve_conflict(tasks, "unknown_strategy")
        
        # 应该回退到priority_based策略
        assert resolution["strategy"] == "priority_based"
        assert resolution["winner"] == "task1"  # HIGH优先级


class TestIntegration:
    """集成测试."""
    
    @pytest.mark.asyncio
    async def test_complete_hierarchical_workflow(self):
        """测试完整的分层工作流执行."""
        # 1. 创建分层工作流
        coordinator_config = {"node_id": "coordinator", "name": "Main Coordinator"}
        worker_configs = [
            {"node_id": "sales_worker", "agent_type": AgentType.SALES, "name": "Sales Worker"},
            {"node_id": "support_worker", "agent_type": AgentType.CUSTOMER_SUPPORT, "name": "Support Worker"}
        ]
        
        workflow = HierarchicalWorkflowFactory.create_hierarchical_workflow(
            coordinator_config, worker_configs, "Complete Hierarchical Test"
        )
        
        # 2. 创建执行
        execution = WorkflowExecution(
            execution_id="hierarchical_integration_test",
            graph_id=workflow.graph_id,
            input_data={
                "task_type": "sales_process",
                "customer_profile": {"name": "John Doe", "budget": 50000},
                "requirements": {"product_type": "enterprise"}
            }
        )
        
        # 3. 执行工作流
        engine = HierarchicalWorkflowEngine()
        result = await engine.execute_workflow(execution)
        
        # 4. 验证结果
        assert result.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]
        assert result.start_time is not None
        assert result.end_time is not None
        assert len(result.node_results) > 0
        
        # 5. 验证分层执行特性
        coordinator_result = result.node_results.get("coordinator")
        assert coordinator_result is not None
        assert "subtasks" in coordinator_result
        assert "execution_log" in coordinator_result
        assert "final_result" in coordinator_result
        
        # 6. 验证子任务执行
        subtasks = coordinator_result["subtasks"]
        assert len(subtasks) > 0
        
        # 销售流程应该包含特定的子任务
        subtask_ids = [task["task_id"] for task in subtasks]
        assert "needs_analysis" in subtask_ids
        assert "product_recommendation" in subtask_ids
        assert "quote_generation" in subtask_ids
        assert "management_approval" in subtask_ids
    
    def test_hierarchical_workflow_builder_integration(self):
        """测试分层工作流构建器集成."""
        # 1. 使用工厂创建工作流
        workflow = HierarchicalWorkflowFactory.create_hierarchical_workflow(
            {"node_id": "coordinator", "name": "Coordinator"},
            [
                {"node_id": "worker1", "agent_type": AgentType.SALES, "name": "Sales Worker"},
                {"node_id": "worker2", "agent_type": AgentType.CUSTOMER_SUPPORT, "name": "Support Worker"}
            ]
        )
        
        # 2. 使用构建器重建
        builder = HierarchicalGraphBuilder()
        builder.from_workflow_graph(workflow)
        
        # 3. 设置分层结构
        builder.set_coordinator("coordinator")
        builder.add_worker_nodes(["worker1", "worker2"])
        
        # 4. 验证构建器状态
        assert len(builder.nodes) == 3
        assert len(builder.edges) == 4
        assert builder.coordinator_node == "coordinator"
        assert len(builder.worker_nodes) == 2
        
        # 5. 重新生成工作流图
        rebuilt_workflow = builder.to_workflow_graph("Rebuilt Hierarchical Workflow", WorkflowType.HIERARCHICAL)
        
        assert rebuilt_workflow.workflow_type == WorkflowType.HIERARCHICAL
        assert len(rebuilt_workflow.nodes) == len(workflow.nodes)
        assert len(rebuilt_workflow.edges) == len(workflow.edges)
    
    @pytest.mark.asyncio
    async def test_task_dependency_execution(self):
        """测试任务依赖执行."""
        coordinator = CoordinatorAgent()
        
        # 创建有依赖关系的任务
        context = NodeExecutionContext(
            node_id="coordinator",
            execution_id="dependency_test",
            input_data={}
        )
        
        main_task = {
            "type": "sales_process",
            "customer_profile": {"name": "Test Customer"}
        }
        
        # 分解任务
        subtasks = await coordinator.decompose_task(main_task, context)
        
        # 验证依赖关系
        needs_analysis = next(task for task in subtasks if task.task_id == "needs_analysis")
        product_recommendation = next(task for task in subtasks if task.task_id == "product_recommendation")
        quote_generation = next(task for task in subtasks if task.task_id == "quote_generation")
        management_approval = next(task for task in subtasks if task.task_id == "management_approval")
        
        # 检查依赖链
        assert len(needs_analysis.dependencies) == 0  # 第一个任务无依赖
        assert "needs_analysis" in product_recommendation.dependencies
        assert "product_recommendation" in quote_generation.dependencies
        assert "quote_generation" in management_approval.dependencies
        
        # 模拟按依赖顺序执行
        # 1. 只有needs_analysis就绪
        ready_tasks = await coordinator.schedule_tasks()
        assert "needs_analysis" in ready_tasks
        assert len(ready_tasks) == 1
        
        # 2. 完成needs_analysis后，product_recommendation就绪
        await coordinator.complete_task("needs_analysis", {"analysis": "completed"})
        ready_tasks = await coordinator.schedule_tasks()
        assert "product_recommendation" in ready_tasks
        
        # 3. 完成product_recommendation后，quote_generation就绪
        await coordinator.complete_task("product_recommendation", {"products": ["product1"]})
        ready_tasks = await coordinator.schedule_tasks()
        assert "quote_generation" in ready_tasks
        
        # 4. 完成quote_generation后，management_approval就绪
        await coordinator.complete_task("quote_generation", {"quote": 10000})
        ready_tasks = await coordinator.schedule_tasks()
        assert "management_approval" in ready_tasks
    
    @pytest.mark.asyncio
    async def test_conflict_resolution_integration(self):
        """测试冲突解决集成."""
        resolver = ConflictResolver()
        
        # 创建冲突任务（相同资源需求）
        conflicting_tasks = [
            SubTask("urgent_task", "Urgent Task", AgentType.SALES, {}, TaskPriority.URGENT),
            SubTask("high_task", "High Task", AgentType.SALES, {}, TaskPriority.HIGH),
            SubTask("normal_task", "Normal Task", AgentType.SALES, {}, TaskPriority.NORMAL)
        ]
        
        # 使用不同策略解决冲突
        priority_resolution = await resolver.resolve_conflict(conflicting_tasks, "priority_based")
        resource_resolution = await resolver.resolve_conflict(conflicting_tasks, "resource_based")
        escalation_resolution = await resolver.resolve_conflict(conflicting_tasks, "escalation")
        
        # 验证不同策略的结果
        assert priority_resolution["winner"] == "urgent_task"
        assert resource_resolution["strategy"] == "resource_based"
        assert escalation_resolution["escalated_to"] == "management"
        
        # 验证优先级策略的执行顺序
        expected_order = ["urgent_task", "high_task", "normal_task"]
        assert priority_resolution["execution_order"] == expected_order