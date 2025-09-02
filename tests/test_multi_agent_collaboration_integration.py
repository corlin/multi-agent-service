"""多智能体协作集成测试."""

import asyncio
import pytest
from datetime import datetime
from typing import Dict, List, Any
from unittest.mock import AsyncMock, MagicMock, patch

from src.multi_agent_service.models.base import UserRequest, AgentResponse, CollaborationResult
from src.multi_agent_service.models.enums import (
    AgentType, WorkflowType, WorkflowStatus, IntentType, Priority, AgentStatus
)
from src.multi_agent_service.models.workflow import (
    WorkflowExecution, WorkflowGraph, WorkflowNode, WorkflowEdge, NodeExecutionContext
)
from src.multi_agent_service.workflows.sequential import SequentialWorkflowEngine
from src.multi_agent_service.workflows.parallel import ParallelWorkflowEngine
from src.multi_agent_service.workflows.hierarchical import HierarchicalWorkflowEngine
from src.multi_agent_service.agents.base import BaseAgent
from src.multi_agent_service.agents.sales_agent import SalesAgent
from src.multi_agent_service.agents.customer_support_agent import CustomerSupportAgent
from src.multi_agent_service.agents.manager_agent import ManagerAgent
from src.multi_agent_service.agents.field_service_agent import FieldServiceAgent
from src.multi_agent_service.agents.coordinator_agent import CoordinatorAgent
from src.multi_agent_service.services.agent_router import AgentRouter
from src.multi_agent_service.services.intent_analyzer import IntentAnalyzer
from src.multi_agent_service.agents.registry import AgentRegistry
from src.multi_agent_service.models.config import AgentConfig
from src.multi_agent_service.models.config import ModelConfig as ConfigModelConfig
from src.multi_agent_service.models.model_service import ModelConfig as ServiceModelConfig
from src.multi_agent_service.services.model_clients.mock_client import MockModelClient


class TestMultiAgentCollaborationIntegration:
    """多智能体协作集成测试类."""
    
    @pytest.fixture
    async def mock_agents(self):
        """创建模拟智能体实例."""
        # 创建模型配置
        from src.multi_agent_service.models.enums import ModelProvider
        
        # 为MockModelClient创建ServiceModelConfig
        service_model_config = ServiceModelConfig(
            provider=ModelProvider.CUSTOM,
            model_name="mock-model",
            api_key="mock-key",
            base_url="http://mock.api"
        )
        mock_client = MockModelClient(service_model_config)
        
        # 为AgentConfig创建ConfigModelConfig
        config_model_config = ConfigModelConfig(
            provider=ModelProvider.CUSTOM,
            model_name="mock-model",
            api_key="mock-key",
            api_base="http://mock.api"
        )
        
        # 创建智能体配置
        sales_config = AgentConfig(
            agent_id="sales_001",
            agent_type=AgentType.SALES,
            name="Sales Agent",
            description="销售代表智能体",
            capabilities=["sales", "consultation", "pricing"],
            llm_config=config_model_config,
            prompt_template="你是一个专业的销售代表，请帮助客户解答问题。",
            max_concurrent_tasks=5
        )
        
        support_config = AgentConfig(
            agent_id="support_001",
            agent_type=AgentType.CUSTOMER_SUPPORT,
            name="Support Agent",
            description="客服专员智能体",
            capabilities=["support", "troubleshooting", "customer_service"],
            llm_config=config_model_config,
            prompt_template="你是一个专业的客服专员，请帮助客户解决问题。",
            max_concurrent_tasks=5
        )
        
        manager_config = AgentConfig(
            agent_id="manager_001",
            agent_type=AgentType.MANAGER,
            name="Manager Agent",
            description="管理者智能体",
            capabilities=["management", "decision_making", "strategy"],
            llm_config=config_model_config,
            prompt_template="你是一个公司管理者，请提供管理决策和战略建议。",
            max_concurrent_tasks=3
        )
        
        field_config = AgentConfig(
            agent_id="field_001",
            agent_type=AgentType.FIELD_SERVICE,
            name="Field Service Agent",
            description="现场服务人员智能体",
            capabilities=["technical_service", "field_work", "maintenance"],
            llm_config=config_model_config,
            prompt_template="你是一个现场服务技术人员，请提供技术支持和维修指导。",
            max_concurrent_tasks=3
        )
        
        coordinator_config = AgentConfig(
            agent_id="coordinator_001",
            agent_type=AgentType.COORDINATOR,
            name="Coordinator Agent",
            description="协调员智能体",
            capabilities=["coordination", "task_management", "conflict_resolution"],
            llm_config=config_model_config,
            prompt_template="你是一个智能体协调员，负责任务分配和协调管理。",
            max_concurrent_tasks=10
        )
        
        # 创建智能体实例
        agents = {
            AgentType.SALES: SalesAgent(sales_config, mock_client),
            AgentType.CUSTOMER_SUPPORT: CustomerSupportAgent(support_config, mock_client),
            AgentType.MANAGER: ManagerAgent(manager_config, mock_client),
            AgentType.FIELD_SERVICE: FieldServiceAgent(field_config, mock_client),
            AgentType.COORDINATOR: CoordinatorAgent(coordinator_config, mock_client)
        }
        
        # 初始化所有智能体
        for agent in agents.values():
            await agent.initialize()
            await agent.start()
        
        return agents
    
    @pytest.fixture
    async def agent_registry(self, mock_agents):
        """创建智能体注册表."""
        registry = AgentRegistry()
        
        # 注册所有智能体
        for agent_type, agent in mock_agents.items():
            await registry.register_agent(agent)
        
        return registry
    
    @pytest.fixture
    async def intent_analyzer(self):
        """创建意图分析器."""
        analyzer = IntentAnalyzer()
        await analyzer.initialize()
        return analyzer
    
    @pytest.fixture
    async def agent_router(self, intent_analyzer, agent_registry):
        """创建智能体路由器."""
        return AgentRouter(intent_analyzer, agent_registry)
    
    @pytest.fixture
    async def workflow_engines(self):
        """创建工作流引擎."""
        return {
            WorkflowType.SEQUENTIAL: SequentialWorkflowEngine(),
            WorkflowType.PARALLEL: ParallelWorkflowEngine(),
            WorkflowType.HIERARCHICAL: HierarchicalWorkflowEngine()
        }

    @pytest.mark.asyncio
    async def test_sequential_workflow_collaboration(self, mock_agents, workflow_engines):
        """测试Sequential协作模式下的智能体协同工作."""
        # 创建顺序工作流执行
        execution = WorkflowExecution(
            execution_id="seq_test_001",
            graph_id="sequential_sales_process",
            input_data={
                "customer_inquiry": "我想了解你们的产品价格和技术支持服务",
                "customer_id": "cust_001",
                "priority": "high"
            }
        )
        
        # 执行顺序工作流
        engine = workflow_engines[WorkflowType.SEQUENTIAL]
        result = await engine.execute_workflow(execution)
        
        # 验证执行结果
        assert result.status == WorkflowStatus.COMPLETED
        assert result.execution_id == "seq_test_001"
        assert result.node_results is not None
        assert len(result.node_results) > 0
        
        # 验证智能体间的信息传递
        # 在顺序执行中，每个步骤的输出应该传递给下一个步骤
        node_ids = list(result.node_results.keys())
        for i in range(len(node_ids) - 1):
            current_result = result.node_results[node_ids[i]]
            assert current_result.get("status") == "completed"
        
        # 验证最终输出包含所有步骤的信息
        assert result.output_data is not None
        
        print(f"Sequential workflow completed with {len(result.node_results)} steps")

    @pytest.mark.asyncio
    async def test_parallel_workflow_collaboration(self, mock_agents, workflow_engines):
        """测试Parallel协作模式下的智能体并行处理."""
        # 创建并行工作流执行
        execution = WorkflowExecution(
            execution_id="par_test_001",
            graph_id="parallel_multi_inquiry",
            input_data={
                "inquiries": [
                    {"type": "sales", "content": "产品价格咨询"},
                    {"type": "support", "content": "技术问题求助"},
                    {"type": "service", "content": "现场服务预约"}
                ]
            }
        )
        
        # 执行并行工作流
        engine = workflow_engines[WorkflowType.PARALLEL]
        result = await engine.execute_workflow(execution)
        
        # 验证执行结果
        assert result.status == WorkflowStatus.COMPLETED
        assert result.execution_id == "par_test_001"
        assert result.node_results is not None
        
        # 验证并行执行特性
        # 所有并行任务应该同时执行
        parallel_results = [
            res for res in result.node_results.values() 
            if isinstance(res, dict) and res.get("node_id") not in ["start", "end"]
        ]
        
        # 验证并行任务都成功完成
        for parallel_result in parallel_results:
            assert parallel_result.get("status") == "completed"
        
        # 验证结果聚合
        assert result.output_data is not None
        assert "parallel_results" in result.output_data or "success_count" in result.output_data
        
        print(f"Parallel workflow completed with {len(parallel_results)} parallel tasks")

    @pytest.mark.asyncio
    async def test_hierarchical_workflow_collaboration(self, mock_agents, workflow_engines):
        """测试Hierarchical协作模式下的分层管理和任务分配."""
        # 创建分层工作流执行
        execution = WorkflowExecution(
            execution_id="hier_test_001",
            graph_id="hierarchical_complex_task",
            input_data={
                "task_type": "customer_inquiry",
                "query": "我需要一个综合解决方案，包括产品购买、技术支持和现场服务",
                "customer_id": "cust_002",
                "urgency": "high"
            }
        )
        
        # 执行分层工作流
        engine = workflow_engines[WorkflowType.HIERARCHICAL]
        result = await engine.execute_workflow(execution)
        
        # 验证执行结果
        assert result.status == WorkflowStatus.COMPLETED
        assert result.execution_id == "hier_test_001"
        assert result.node_results is not None
        
        # 验证协调员的任务分解
        coordinator_result = result.node_results.get("coordinator")
        assert coordinator_result is not None
        assert "subtasks" in coordinator_result
        assert len(coordinator_result["subtasks"]) > 0
        
        # 验证子任务执行
        subtasks = coordinator_result["subtasks"]
        execution_log = coordinator_result.get("execution_log", [])
        
        # 至少应该有一些子任务被执行
        assert len(execution_log) > 0
        
        # 验证最终结果包含执行摘要
        final_result = coordinator_result.get("final_result", {})
        assert "total_tasks" in final_result
        assert "completed_tasks" in final_result
        assert "success_rate" in final_result
        
        print(f"Hierarchical workflow completed with {final_result.get('total_tasks', 0)} subtasks")

    @pytest.mark.asyncio
    async def test_agent_information_sharing(self, mock_agents):
        """测试智能体间的信息共享和状态同步机制."""
        sales_agent = mock_agents[AgentType.SALES]
        support_agent = mock_agents[AgentType.CUSTOMER_SUPPORT]
        manager_agent = mock_agents[AgentType.MANAGER]
        
        # 测试信息共享
        shared_info = {
            "customer_id": "cust_003",
            "issue_type": "complex_inquiry",
            "priority": "high",
            "context": "客户需要综合解决方案"
        }
        
        # 销售智能体分享信息给支持和管理智能体
        share_result = await sales_agent.share_information(
            shared_info, 
            [support_agent.agent_id, manager_agent.agent_id]
        )
        assert share_result is True
        
        # 验证信息被正确存储
        assert len(sales_agent._shared_memory) > 0
        
        # 支持智能体接收信息
        receive_result = await support_agent.receive_information(
            shared_info, 
            sales_agent.agent_id
        )
        assert receive_result is True
        
        # 管理智能体接收信息
        receive_result = await manager_agent.receive_information(
            shared_info, 
            sales_agent.agent_id
        )
        assert receive_result is True
        
        # 验证信息同步
        assert len(support_agent._shared_memory) > 0
        assert len(manager_agent._shared_memory) > 0
        
        print("Information sharing test completed successfully")

    @pytest.mark.asyncio
    async def test_coordinator_task_assignment_and_conflict_resolution(self, mock_agents):
        """测试协调员智能体的任务分配和冲突解决."""
        coordinator = mock_agents[AgentType.COORDINATOR]
        sales_agent = mock_agents[AgentType.SALES]
        support_agent = mock_agents[AgentType.CUSTOMER_SUPPORT]
        
        # 创建需要协调的任务
        main_task = {
            "type": "sales_process",
            "customer_profile": {"size": "large", "budget": "high"},
            "requirements": ["product_demo", "custom_solution", "priority_support"],
            "quote_amount": 50000
        }
        
        # 创建执行上下文
        context = NodeExecutionContext(
            node_id="coordination_test",
            execution_id="coord_test_001",
            input_data=main_task,
            shared_state={}
        )
        
        # 协调员分解任务
        subtasks = await coordinator.coordinator.decompose_task(main_task, context)
        
        # 验证任务分解
        assert len(subtasks) > 0
        assert all(hasattr(task, 'task_id') for task in subtasks)
        assert all(hasattr(task, 'agent_type') for task in subtasks)
        
        # 验证任务调度
        ready_tasks = await coordinator.coordinator.schedule_tasks()
        assert len(ready_tasks) > 0
        
        # 测试任务分配
        for task_id in ready_tasks[:2]:  # 分配前两个任务
            subtask = coordinator.coordinator.subtasks[task_id]
            agent_id = f"agent_{subtask.agent_type.value}"
            
            assign_result = await coordinator.coordinator.assign_task(task_id, agent_id)
            assert assign_result is True
            
            # 验证任务状态更新
            assert subtask.status.value == "assigned"
            assert subtask.assigned_agent == agent_id
        
        # 测试冲突解决（模拟冲突场景）
        from src.multi_agent_service.models.base import Conflict
        
        conflict = Conflict(
            conflict_id="conflict_001",
            conflicting_agents=[sales_agent.agent_id, support_agent.agent_id],
            conflict_type="resource_allocation",
            description="两个智能体都需要同一个资源",
            proposed_solutions=["轮流使用", "优先级分配", "资源复制"]
        )
        
        resolution = await coordinator.handle_conflict(conflict)
        assert resolution is not None
        assert isinstance(resolution, str)
        
        print(f"Coordinator assigned {len(ready_tasks)} tasks and resolved conflict")

    @pytest.mark.asyncio
    async def test_cross_workflow_collaboration(self, mock_agents, workflow_engines, agent_router):
        """测试跨工作流的智能体协作."""
        # 创建复杂场景：需要多种协作模式的综合任务
        user_request = UserRequest(
            request_id="cross_collab_001",
            content="我需要购买企业版产品，同时需要技术支持团队协助部署，还需要管理层审批预算",
            priority=Priority.HIGH
        )
        
        # 1. 首先通过路由器分析意图
        route_result, intent_result = await agent_router.route_request(user_request)
        
        # 验证路由结果
        assert route_result.selected_agent is not None
        assert route_result.confidence > 0.0
        
        # 2. 如果需要协作，启动相应的工作流
        if route_result.requires_collaboration:
            # 根据协作需求选择工作流类型
            if intent_result.intent_type == IntentType.MANAGEMENT_DECISION:
                workflow_type = WorkflowType.HIERARCHICAL
            elif len(intent_result.suggested_agents) > 2:
                workflow_type = WorkflowType.PARALLEL
            else:
                workflow_type = WorkflowType.SEQUENTIAL
            
            # 创建工作流执行
            execution = WorkflowExecution(
                execution_id="cross_collab_workflow_001",
                graph_id=f"{workflow_type.value}_cross_collaboration",
                input_data={
                    "original_request": user_request.content,
                    "intent_type": intent_result.intent_type.value,
                    "suggested_agents": [agent.value for agent in intent_result.suggested_agents],
                    "priority": user_request.priority.value
                }
            )
            
            # 执行工作流
            engine = workflow_engines[workflow_type]
            result = await engine.execute_workflow(execution)
            
            # 验证跨工作流协作结果
            assert result.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]
            assert result.node_results is not None
            
            if result.status == WorkflowStatus.COMPLETED:
                # 验证所有参与的智能体都有贡献
                participating_agents = set()
                for node_result in result.node_results.values():
                    if isinstance(node_result, dict) and "agent_type" in node_result:
                        participating_agents.add(node_result["agent_type"])
                
                # 应该有多个智能体参与
                assert len(participating_agents) >= 2
                
                print(f"Cross-workflow collaboration completed with {len(participating_agents)} agents")
        
        else:
            # 单智能体处理
            selected_agent = mock_agents[route_result.selected_agent]
            response = await selected_agent.process_request(user_request)
            
            # 验证单智能体响应
            assert response.agent_id == selected_agent.agent_id
            assert response.response_content is not None
            
            print("Single agent processing completed")

    @pytest.mark.asyncio
    async def test_agent_collaboration_with_state_synchronization(self, mock_agents):
        """测试智能体协作过程中的状态同步."""
        sales_agent = mock_agents[AgentType.SALES]
        support_agent = mock_agents[AgentType.CUSTOMER_SUPPORT]
        manager_agent = mock_agents[AgentType.MANAGER]
        
        # 创建协作上下文
        collaboration_context = {
            "customer_id": "cust_004",
            "case_id": "case_001",
            "collaboration_type": "complex_inquiry",
            "shared_state": {
                "customer_profile": {"tier": "premium", "history": "long_term"},
                "current_issue": "product_upgrade_with_support",
                "timeline": "urgent"
            }
        }
        
        # 启动协作
        other_agents = [support_agent, manager_agent]
        collaboration_result = await sales_agent.collaborate(other_agents, collaboration_context)
        
        # 验证协作结果
        assert collaboration_result is not None
        assert hasattr(collaboration_result, 'collaboration_id')
        assert hasattr(collaboration_result, 'participating_agents')
        assert hasattr(collaboration_result, 'final_result')
        
        # 验证所有智能体都参与了协作
        expected_agents = {sales_agent.agent_id, support_agent.agent_id, manager_agent.agent_id}
        actual_agents = set(collaboration_result.participating_agents)
        assert expected_agents.issubset(actual_agents)
        
        # 验证协作伙伴关系建立
        assert support_agent.agent_id in sales_agent._collaboration_partners
        assert manager_agent.agent_id in sales_agent._collaboration_partners
        
        # 验证状态同步 - 检查共享状态是否在智能体间传播
        # 这里可以通过检查智能体的内部状态来验证同步
        assert len(sales_agent._shared_memory) > 0
        
        print(f"Collaboration completed with {len(collaboration_result.participating_agents)} agents")

    @pytest.mark.asyncio
    async def test_workflow_failure_and_recovery(self, mock_agents, workflow_engines):
        """测试工作流执行失败和恢复机制."""
        # 创建一个可能失败的工作流执行
        execution = WorkflowExecution(
            execution_id="failure_test_001",
            graph_id="test_failure_recovery",
            input_data={
                "simulate_failure": True,  # 模拟失败场景
                "failure_point": "middle_step",
                "recovery_strategy": "retry"
            }
        )
        
        # 使用Sequential引擎测试失败处理
        engine = workflow_engines[WorkflowType.SEQUENTIAL]
        
        # 模拟部分节点失败
        with patch.object(engine.executor, 'execute_node') as mock_execute:
            # 设置模拟：第一个节点成功，第二个节点失败，第三个节点成功
            mock_execute.side_effect = [
                {"node_id": "step1", "status": "completed", "output": "success"},
                Exception("Simulated node failure"),
                {"node_id": "step3", "status": "completed", "output": "success"}
            ]
            
            result = await engine.execute_workflow(execution)
            
            # 验证失败处理
            assert result.status == WorkflowStatus.FAILED
            assert result.error_message is not None
            assert "failed" in result.error_message.lower()
        
        # 测试工作流取消
        cancel_result = await engine.cancel_workflow("failure_test_001")
        # 由于工作流已经完成（失败），取消操作应该返回False
        assert cancel_result is False
        
        print("Workflow failure and recovery test completed")

    @pytest.mark.asyncio
    async def test_agent_load_balancing_in_collaboration(self, mock_agents, agent_router):
        """测试协作过程中的智能体负载均衡."""
        # 创建多个并发请求来测试负载均衡
        requests = []
        for i in range(5):
            request = UserRequest(
                request_id=f"load_test_{i:03d}",
                content=f"销售咨询请求 {i+1}：我想了解产品价格和服务",
                priority=Priority.NORMAL
            )
            requests.append(request)
        
        # 并发处理所有请求
        routing_tasks = [
            agent_router.route_request(request, strategy="load_balanced")
            for request in requests
        ]
        
        routing_results = await asyncio.gather(*routing_tasks, return_exceptions=True)
        
        # 验证路由结果
        successful_routes = [
            result for result in routing_results 
            if not isinstance(result, Exception)
        ]
        
        assert len(successful_routes) > 0
        
        # 统计智能体分配情况
        agent_assignments = {}
        for route_result, intent_result in successful_routes:
            agent_type = route_result.selected_agent
            agent_assignments[agent_type] = agent_assignments.get(agent_type, 0) + 1
        
        # 验证负载分布（在理想情况下应该相对均匀）
        print(f"Agent assignments: {agent_assignments}")
        
        # 验证所有请求都得到了处理
        assert len(successful_routes) == len(requests)
        
        print(f"Load balancing test completed with {len(successful_routes)} successful routes")

    @pytest.mark.asyncio
    async def test_end_to_end_collaboration_scenario(self, mock_agents, workflow_engines, agent_router):
        """端到端协作场景测试：从用户请求到最终响应的完整流程."""
        # 创建复杂的用户请求
        user_request = UserRequest(
            request_id="e2e_test_001",
            content="我是一家大型企业的IT主管，需要购买你们的企业版产品，包括定制开发、现场部署和长期技术支持。预算在10万以上，希望能安排管理层会议讨论合作细节。",
            priority=Priority.HIGH,
            context={
                "user_role": "IT_Manager",
                "company_size": "large",
                "budget_range": "100k+",
                "requirements": ["custom_development", "on_site_deployment", "long_term_support"]
            }
        )
        
        # 1. 意图识别和路由
        route_result, intent_result = await agent_router.route_request(user_request)
        
        assert route_result.selected_agent is not None
        assert intent_result.intent_type is not None
        
        # 2. 根据路由结果决定处理方式
        if route_result.requires_collaboration:
            # 需要协作 - 启动分层工作流
            execution = WorkflowExecution(
                execution_id="e2e_collaboration_001",
                graph_id="enterprise_sales_process",
                input_data={
                    "user_request": user_request.content,
                    "user_context": user_request.context,
                    "intent_analysis": {
                        "type": intent_result.intent_type.value,
                        "confidence": intent_result.confidence,
                        "entities": [entity.dict() for entity in intent_result.entities]
                    },
                    "routing_info": {
                        "primary_agent": route_result.selected_agent.value,
                        "alternatives": [agent.value for agent in route_result.alternative_agents],
                        "confidence": route_result.confidence
                    }
                }
            )
            
            # 执行分层工作流（最适合复杂企业销售流程）
            engine = workflow_engines[WorkflowType.HIERARCHICAL]
            workflow_result = await engine.execute_workflow(execution)
            
            # 验证端到端执行结果
            assert workflow_result.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]
            
            if workflow_result.status == WorkflowStatus.COMPLETED:
                # 验证协作结果的完整性
                assert workflow_result.node_results is not None
                assert workflow_result.output_data is not None
                
                # 验证涉及的智能体类型
                coordinator_result = workflow_result.node_results.get("coordinator")
                if coordinator_result:
                    subtasks = coordinator_result.get("subtasks", [])
                    involved_agent_types = set()
                    for subtask in subtasks:
                        if isinstance(subtask, dict) and "agent_type" in subtask:
                            involved_agent_types.add(subtask["agent_type"])
                    
                    # 对于企业级销售，应该涉及多个智能体类型
                    expected_types = {"sales", "manager"}  # 至少应该有销售和管理
                    assert len(involved_agent_types.intersection(expected_types)) > 0
                
                final_response = {
                    "status": "success",
                    "workflow_id": workflow_result.execution_id,
                    "processing_time": (workflow_result.end_time - workflow_result.start_time).total_seconds() if workflow_result.end_time and workflow_result.start_time else None,
                    "involved_agents": list(workflow_result.node_results.keys()),
                    "final_result": workflow_result.output_data
                }
                
                print(f"E2E collaboration completed successfully: {final_response}")
                
            else:
                # 处理失败情况
                print(f"E2E collaboration failed: {workflow_result.error_message}")
                
        else:
            # 单智能体处理
            selected_agent = mock_agents[route_result.selected_agent]
            agent_response = await selected_agent.process_request(user_request)
            
            # 验证单智能体响应
            assert agent_response.response_content is not None
            assert agent_response.agent_id == selected_agent.agent_id
            
            final_response = {
                "status": "success",
                "agent_id": agent_response.agent_id,
                "agent_type": agent_response.agent_type.value,
                "response": agent_response.response_content,
                "confidence": agent_response.confidence
            }
            
            print(f"E2E single agent processing completed: {final_response}")
        
        # 3. 验证整个流程的完整性
        # 确保从用户请求到最终响应的链路是完整的
        assert user_request.request_id == "e2e_test_001"
        assert route_result is not None
        assert intent_result is not None
        
        print("End-to-end collaboration scenario test completed successfully")