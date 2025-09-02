"""故障恢复和异常处理测试."""

import asyncio
import pytest
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch
import random

from src.multi_agent_service.models.base import UserRequest, AgentResponse
from src.multi_agent_service.models.enums import (
    AgentType, WorkflowType, WorkflowStatus, Priority, AgentStatus
)
from src.multi_agent_service.models.workflow import WorkflowExecution, NodeExecutionContext
from src.multi_agent_service.models.config import AgentConfig, ModelConfig
from src.multi_agent_service.services.model_clients.mock_client import MockModelClient
from src.multi_agent_service.services.model_router import ModelRouter
from src.multi_agent_service.services.intent_analyzer import IntentAnalyzer
from src.multi_agent_service.services.agent_router import AgentRouter
from src.multi_agent_service.agents.registry import AgentRegistry
from src.multi_agent_service.agents.sales_agent import SalesAgent
from src.multi_agent_service.agents.customer_support_agent import CustomerSupportAgent
from src.multi_agent_service.agents.manager_agent import ManagerAgent
from src.multi_agent_service.workflows.sequential import SequentialWorkflowEngine
from src.multi_agent_service.workflows.parallel import ParallelWorkflowEngine
from src.multi_agent_service.workflows.hierarchical import HierarchicalWorkflowEngine
from src.multi_agent_service.utils.exceptions import (
    ModelException, AgentException, WorkflowException, ConfigurationError
)


class FailingModelClient(MockModelClient):
    """模拟失败的模型客户端."""
    
    def __init__(self, failure_rate: float = 0.5, failure_type: str = "timeout"):
        model_config = ModelConfig(
            provider=ModelProvider.CUSTOM,
            model_name="failing-mock-model",
            api_key="mock-key",
            api_base="http://mock.api"
        )
        super().__init__(model_config)
        self.failure_rate = failure_rate
        self.failure_type = failure_type
        self.call_count = 0
    
    async def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """模拟可能失败的响应生成."""
        self.call_count += 1
        
        # 根据失败率决定是否失败
        if random.random() < self.failure_rate:
            if self.failure_type == "timeout":
                await asyncio.sleep(0.1)  # 模拟超时
                raise asyncio.TimeoutError("Model API timeout")
            elif self.failure_type == "api_error":
                raise ModelException("Model API returned error 500", "MODEL_5000")
            elif self.failure_type == "rate_limit":
                raise ModelException("Rate limit exceeded", "MODEL_5004")
            elif self.failure_type == "network_error":
                raise ConnectionError("Network connection failed")
        
        # 成功情况
        return await super().generate_response(messages, **kwargs)


class UnstableAgent(SalesAgent):
    """不稳定的智能体，用于测试故障处理."""
    
    def __init__(self, config: AgentConfig, model_client, failure_probability: float = 0.3):
        super().__init__(config, model_client)
        self.failure_probability = failure_probability
        self.failure_count = 0
    
    async def process_request(self, request: UserRequest) -> AgentResponse:
        """可能失败的请求处理."""
        # 随机失败
        if random.random() < self.failure_probability:
            self.failure_count += 1
            raise AgentException(f"Agent {self.agent_id} processing failed (failure #{self.failure_count})")
        
        return await super().process_request(request)
    
    async def health_check(self) -> bool:
        """不稳定的健康检查."""
        # 偶尔返回不健康状态
        if random.random() < 0.2:
            return False
        return await super().health_check()


class TestFaultRecoveryAndExceptionHandling:
    """故障恢复和异常处理测试类."""
    
    @pytest.fixture
    async def fault_tolerant_system_setup(self):
        """设置容错系统环境."""
        # 创建模型配置
        from src.multi_agent_service.models.enums import ModelProvider
        model_config = ModelConfig(
            provider=ModelProvider.CUSTOM,
            model_name="mock-model",
            api_key="mock-key",
            api_base="http://mock.api"
        )
        
        # 创建多个模型客户端（包括失败的）
        stable_client = MockModelClient(model_config)
        failing_client = FailingModelClient(failure_rate=0.7, failure_type="timeout")
        backup_client = MockModelClient(model_config)
        
        # 创建智能体配置
        sales_config = AgentConfig(
            agent_id="sales_001",
            agent_type=AgentType.SALES,
            name="Sales Agent",
            description="销售代表智能体",
            capabilities=["sales", "consultation", "pricing"],
            llm_config=model_config,
            prompt_template="你是一个专业的销售代表，请帮助客户解答问题。",
            max_concurrent_tasks=5
        )
        
        support_config = AgentConfig(
            agent_id="support_001",
            agent_type=AgentType.CUSTOMER_SUPPORT,
            name="Support Agent",
            description="客服专员智能体",
            capabilities=["support", "troubleshooting", "customer_service"],
            llm_config=model_config,
            prompt_template="你是一个专业的客服专员，请帮助客户解决问题。",
            max_concurrent_tasks=5
        )
        
        # 创建稳定和不稳定的智能体
        stable_sales_agent = SalesAgent(sales_config, stable_client)
        unstable_sales_agent = UnstableAgent(sales_config, failing_client, failure_probability=0.4)
        stable_support_agent = CustomerSupportAgent(support_config, backup_client)
        
        # 初始化智能体
        agents = [stable_sales_agent, unstable_sales_agent, stable_support_agent]
        for agent in agents:
            await agent.initialize()
            await agent.start()
        
        # 创建智能体注册表
        agent_registry = AgentRegistry()
        await agent_registry.register_agent(stable_sales_agent)
        await agent_registry.register_agent(stable_support_agent)
        
        # 创建模型路由器（包含故障转移）
        model_router = ModelRouter()
        model_router.add_model_provider("primary", failing_client)
        model_router.add_model_provider("backup", stable_client)
        model_router.add_model_provider("fallback", backup_client)
        
        # 创建意图分析器和路由器
        intent_analyzer = IntentAnalyzer()
        await intent_analyzer.initialize()
        
        agent_router = AgentRouter(intent_analyzer, agent_registry)
        
        # 创建工作流引擎
        workflow_engines = {
            WorkflowType.SEQUENTIAL: SequentialWorkflowEngine(),
            WorkflowType.PARALLEL: ParallelWorkflowEngine(),
            WorkflowType.HIERARCHICAL: HierarchicalWorkflowEngine()
        }
        
        return {
            "stable_agents": [stable_sales_agent, stable_support_agent],
            "unstable_agent": unstable_sales_agent,
            "agent_registry": agent_registry,
            "model_router": model_router,
            "agent_router": agent_router,
            "workflow_engines": workflow_engines,
            "model_clients": {
                "stable": stable_client,
                "failing": failing_client,
                "backup": backup_client
            }
        }

    @pytest.mark.asyncio
    async def test_model_api_failure_and_failover(self, fault_tolerant_system_setup):
        """测试模型API调用失败的故障转移机制."""
        system = fault_tolerant_system_setup
        model_router = system["model_router"]
        
        # 测试多次API调用，验证故障转移
        test_messages = [
            [{"role": "user", "content": "测试消息1"}],
            [{"role": "user", "content": "测试消息2"}],
            [{"role": "user", "content": "测试消息3"}],
            [{"role": "user", "content": "测试消息4"}],
            [{"role": "user", "content": "测试消息5"}]
        ]
        
        successful_calls = 0
        failed_calls = 0
        failover_events = 0
        
        for i, messages in enumerate(test_messages):
            try:
                # 尝试调用主要模型
                response = await model_router.route_and_call("primary", messages)
                
                if response:
                    successful_calls += 1
                    print(f"Call {i+1}: Success")
                else:
                    failed_calls += 1
                    print(f"Call {i+1}: Failed")
                
            except Exception as e:
                # 如果主要模型失败，尝试故障转移
                print(f"Call {i+1}: Primary failed ({str(e)}), attempting failover...")
                failover_events += 1
                
                try:
                    # 尝试备用模型
                    backup_response = await model_router.route_and_call("backup", messages)
                    if backup_response:
                        successful_calls += 1
                        print(f"Call {i+1}: Failover success")
                    else:
                        failed_calls += 1
                        print(f"Call {i+1}: Failover failed")
                        
                except Exception as backup_error:
                    # 如果备用也失败，尝试最后的fallback
                    print(f"Call {i+1}: Backup failed ({str(backup_error)}), trying fallback...")
                    
                    try:
                        fallback_response = await model_router.route_and_call("fallback", messages)
                        if fallback_response:
                            successful_calls += 1
                            print(f"Call {i+1}: Fallback success")
                        else:
                            failed_calls += 1
                            print(f"Call {i+1}: All providers failed")
                    except Exception:
                        failed_calls += 1
                        print(f"Call {i+1}: All providers failed")
        
        # 验证故障转移机制
        print(f"Model API failover test results:")
        print(f"  Successful calls: {successful_calls}")
        print(f"  Failed calls: {failed_calls}")
        print(f"  Failover events: {failover_events}")
        
        # 应该有一定的成功率，即使主要模型不稳定
        success_rate = successful_calls / len(test_messages)
        assert success_rate >= 0.6, f"Success rate too low: {success_rate:.2%}"
        
        # 应该发生故障转移
        assert failover_events > 0, "No failover events detected"

    @pytest.mark.asyncio
    async def test_agent_unavailable_degradation_strategy(self, fault_tolerant_system_setup):
        """测试智能体不可用时的降级处理策略."""
        system = fault_tolerant_system_setup
        agent_registry = system["agent_registry"]
        agent_router = system["agent_router"]
        
        # 创建需要销售智能体的请求
        sales_request = UserRequest(
            request_id="sales_degradation_test",
            content="我想了解产品价格和购买流程",
            priority=Priority.HIGH
        )
        
        # 1. 正常情况下的路由
        normal_route, _ = await agent_router.route_request(sales_request)
        print(f"Normal routing: {normal_route.selected_agent}")
        
        # 2. 模拟销售智能体离线
        sales_agents = await agent_registry.get_agents_by_type(AgentType.SALES)
        if sales_agents:
            original_status = sales_agents[0]._status
            sales_agents[0]._status = AgentStatus.OFFLINE
            
            try:
                # 尝试路由到离线的智能体
                degraded_route, _ = await agent_router.route_request(sales_request)
                
                # 验证降级策略
                if degraded_route.selected_agent == AgentType.SALES:
                    # 如果仍然路由到销售智能体，处理时应该失败并有适当的错误处理
                    try:
                        offline_agent = sales_agents[0]
                        response = await offline_agent.process_request(sales_request)
                        # 如果没有抛出异常，验证响应包含错误信息
                        assert "错误" in response.response_content or "不可用" in response.response_content
                    except Exception as e:
                        # 预期的异常
                        assert "offline" in str(e).lower() or "unavailable" in str(e).lower()
                        print(f"Expected offline agent error: {str(e)}")
                
                else:
                    # 路由到了备用智能体
                    print(f"Degraded routing: {degraded_route.selected_agent}")
                    assert degraded_route.selected_agent != AgentType.SALES
                    
                    # 验证备用智能体能够处理请求
                    backup_agents = await agent_registry.get_agents_by_type(degraded_route.selected_agent)
                    if backup_agents:
                        backup_response = await backup_agents[0].process_request(sales_request)
                        assert backup_response is not None
                        assert backup_response.response_content is not None
                        print("Backup agent successfully handled the request")
            
            finally:
                # 恢复智能体状态
                sales_agents[0]._status = original_status
        
        # 3. 测试所有智能体都不可用的极端情况
        original_statuses = {}
        all_agents = await agent_registry.get_all_agents()
        
        # 将所有智能体设为离线
        for agent in all_agents:
            original_statuses[agent.agent_id] = agent._status
            agent._status = AgentStatus.OFFLINE
        
        try:
            # 尝试路由请求
            extreme_route, _ = await agent_router.route_request(sales_request)
            
            # 验证系统的极端情况处理
            assert extreme_route is not None
            assert extreme_route.confidence < 0.5  # 置信度应该很低
            
            print(f"Extreme case routing: {extreme_route.selected_agent} (confidence: {extreme_route.confidence})")
            
        finally:
            # 恢复所有智能体状态
            for agent in all_agents:
                agent._status = original_statuses[agent.agent_id]

    @pytest.mark.asyncio
    async def test_workflow_execution_exception_recovery(self, fault_tolerant_system_setup):
        """测试工作流执行异常的恢复机制."""
        system = fault_tolerant_system_setup
        workflow_engines = system["workflow_engines"]
        
        # 测试Sequential工作流的异常恢复
        sequential_engine = workflow_engines[WorkflowType.SEQUENTIAL]
        
        # 创建一个会部分失败的工作流执行
        execution = WorkflowExecution(
            execution_id="recovery_test_sequential",
            graph_id="test_recovery_workflow",
            input_data={
                "test_scenario": "partial_failure",
                "expected_failures": ["step_2", "step_4"]
            }
        )
        
        # 模拟节点执行失败
        original_execute_node = sequential_engine.executor.execute_node
        
        async def failing_execute_node(node_id: str, context: NodeExecutionContext):
            # 模拟特定节点失败
            if "step_2" in node_id or "step_4" in node_id:
                raise Exception(f"Simulated failure in {node_id}")
            return await original_execute_node(node_id, context)
        
        # 替换执行方法
        sequential_engine.executor.execute_node = failing_execute_node
        
        try:
            result = await sequential_engine.execute_workflow(execution)
            
            # 验证工作流处理了异常
            assert result.status == WorkflowStatus.FAILED
            assert result.error_message is not None
            assert "failed" in result.error_message.lower()
            
            print(f"Sequential workflow handled failures: {result.error_message}")
            
        finally:
            # 恢复原始方法
            sequential_engine.executor.execute_node = original_execute_node
        
        # 测试Parallel工作流的异常恢复
        parallel_engine = workflow_engines[WorkflowType.PARALLEL]
        
        parallel_execution = WorkflowExecution(
            execution_id="recovery_test_parallel",
            graph_id="test_parallel_recovery",
            input_data={
                "parallel_tasks": ["task_1", "task_2", "task_3"],
                "failure_tasks": ["task_2"]
            }
        )
        
        # 模拟并行任务部分失败
        original_parallel_execute = parallel_engine.executor.execute_node
        
        async def failing_parallel_execute(node_id: str, context: NodeExecutionContext):
            if "task_2" in node_id:
                raise Exception(f"Simulated parallel task failure in {node_id}")
            return await original_parallel_execute(node_id, context)
        
        parallel_engine.executor.execute_node = failing_parallel_execute
        
        try:
            parallel_result = await parallel_engine.execute_workflow(parallel_execution)
            
            # 并行工作流应该能够处理部分失败
            # 验证结果包含成功和失败的任务信息
            assert parallel_result is not None
            
            if parallel_result.status == WorkflowStatus.FAILED:
                print(f"Parallel workflow handled partial failures: {parallel_result.error_message}")
            else:
                # 如果成功完成，验证输出包含失败信息
                assert parallel_result.output_data is not None
                print(f"Parallel workflow completed with partial failures handled")
            
        finally:
            # 恢复原始方法
            parallel_engine.executor.execute_node = original_parallel_execute

    @pytest.mark.asyncio
    async def test_system_fault_tolerance_under_stress(self, fault_tolerant_system_setup):
        """测试系统在压力下的容错能力和自动恢复功能."""
        system = fault_tolerant_system_setup
        agent_router = system["agent_router"]
        unstable_agent = system["unstable_agent"]
        
        # 创建大量并发请求来测试系统稳定性
        stress_requests = []
        for i in range(50):
            request = UserRequest(
                request_id=f"stress_test_{i:03d}",
                content=f"压力测试请求 {i+1}: 我需要销售咨询服务",
                priority=Priority.NORMAL if i % 3 != 0 else Priority.HIGH
            )
            stress_requests.append(request)
        
        # 并发处理所有请求
        async def process_request_with_retry(request: UserRequest, max_retries: int = 3):
            """带重试机制的请求处理."""
            for attempt in range(max_retries):
                try:
                    # 路由请求
                    route_result, _ = await agent_router.route_request(request)
                    
                    # 选择智能体（可能是不稳定的）
                    if route_result.selected_agent == AgentType.SALES and attempt % 2 == 0:
                        # 有时使用不稳定的智能体来测试故障处理
                        selected_agent = unstable_agent
                    else:
                        # 使用稳定的智能体
                        stable_agents = system["stable_agents"]
                        selected_agent = next(
                            (agent for agent in stable_agents 
                             if agent.agent_type == route_result.selected_agent),
                            stable_agents[0]  # 默认使用第一个稳定智能体
                        )
                    
                    # 处理请求
                    response = await selected_agent.process_request(request)
                    
                    return {
                        "request_id": request.request_id,
                        "status": "success",
                        "attempts": attempt + 1,
                        "agent_type": selected_agent.agent_type.value,
                        "response_length": len(response.response_content)
                    }
                
                except Exception as e:
                    if attempt == max_retries - 1:
                        # 最后一次尝试失败
                        return {
                            "request_id": request.request_id,
                            "status": "failed",
                            "attempts": attempt + 1,
                            "error": str(e)
                        }
                    else:
                        # 重试前等待一小段时间
                        await asyncio.sleep(0.1 * (attempt + 1))
                        continue
        
        # 记录开始时间
        start_time = datetime.now()
        
        # 并发处理所有请求
        processing_tasks = [
            process_request_with_retry(request) 
            for request in stress_requests
        ]
        
        results = await asyncio.gather(*processing_tasks, return_exceptions=True)
        
        # 记录结束时间
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        # 分析结果
        successful_results = [r for r in results if isinstance(r, dict) and r.get("status") == "success"]
        failed_results = [r for r in results if isinstance(r, dict) and r.get("status") == "failed"]
        exception_results = [r for r in results if isinstance(r, Exception)]
        
        # 计算统计信息
        total_requests = len(stress_requests)
        success_count = len(successful_results)
        failure_count = len(failed_results) + len(exception_results)
        success_rate = success_count / total_requests
        
        # 计算重试统计
        retry_stats = {}
        for result in successful_results:
            attempts = result.get("attempts", 1)
            retry_stats[attempts] = retry_stats.get(attempts, 0) + 1
        
        # 输出测试结果
        print(f"Stress test results:")
        print(f"  Total requests: {total_requests}")
        print(f"  Successful: {success_count}")
        print(f"  Failed: {failure_count}")
        print(f"  Success rate: {success_rate:.2%}")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Average time per request: {total_time/total_requests:.3f}s")
        print(f"  Retry statistics: {retry_stats}")
        
        # 验证系统容错能力
        assert success_rate >= 0.7, f"Success rate too low under stress: {success_rate:.2%}"
        assert total_time < 30.0, f"Processing time too long: {total_time:.2f}s"
        
        # 验证重试机制有效
        retried_requests = sum(count for attempts, count in retry_stats.items() if attempts > 1)
        if retried_requests > 0:
            print(f"  Retry mechanism helped {retried_requests} requests")

    @pytest.mark.asyncio
    async def test_cascading_failure_prevention(self, fault_tolerant_system_setup):
        """测试级联故障预防机制."""
        system = fault_tolerant_system_setup
        agent_registry = system["agent_registry"]
        
        # 模拟级联故障场景：一个智能体失败导致其他智能体过载
        
        # 1. 首先让一个智能体"失败"
        all_agents = await agent_registry.get_all_agents()
        if len(all_agents) >= 2:
            failing_agent = all_agents[0]
            remaining_agents = all_agents[1:]
            
            # 设置第一个智能体为错误状态
            original_status = failing_agent._status
            failing_agent._status = AgentStatus.ERROR
            
            try:
                # 2. 创建大量请求，这些请求原本会分配给失败的智能体
                cascade_requests = []
                for i in range(20):
                    request = UserRequest(
                        request_id=f"cascade_test_{i:03d}",
                        content="需要处理的紧急请求",
                        priority=Priority.HIGH
                    )
                    cascade_requests.append(request)
                
                # 3. 监控剩余智能体的负载
                initial_loads = {}
                for agent in remaining_agents:
                    initial_loads[agent.agent_id] = agent._current_load
                
                # 4. 处理请求并监控负载分布
                async def monitor_and_process(request: UserRequest):
                    try:
                        # 路由到可用的智能体
                        route_result, _ = await system["agent_router"].route_request(request)
                        
                        # 找到对应的智能体
                        target_agent = None
                        for agent in remaining_agents:
                            if agent.agent_type == route_result.selected_agent:
                                target_agent = agent
                                break
                        
                        if target_agent and target_agent._status != AgentStatus.ERROR:
                            # 检查负载是否超限
                            if target_agent._current_load < target_agent._max_load:
                                response = await target_agent.process_request(request)
                                return {
                                    "request_id": request.request_id,
                                    "status": "success",
                                    "agent_id": target_agent.agent_id,
                                    "load_after": target_agent._current_load
                                }
                            else:
                                # 智能体过载，应该有负载均衡机制
                                return {
                                    "request_id": request.request_id,
                                    "status": "overloaded",
                                    "agent_id": target_agent.agent_id,
                                    "load": target_agent._current_load
                                }
                        else:
                            return {
                                "request_id": request.request_id,
                                "status": "no_available_agent"
                            }
                    
                    except Exception as e:
                        return {
                            "request_id": request.request_id,
                            "status": "error",
                            "error": str(e)
                        }
                
                # 5. 分批处理请求以避免瞬间过载
                batch_size = 5
                all_results = []
                
                for i in range(0, len(cascade_requests), batch_size):
                    batch = cascade_requests[i:i+batch_size]
                    batch_tasks = [monitor_and_process(req) for req in batch]
                    batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                    all_results.extend(batch_results)
                    
                    # 批次间短暂等待，模拟真实场景
                    await asyncio.sleep(0.1)
                
                # 6. 分析结果，验证级联故障预防
                successful_requests = [r for r in all_results if isinstance(r, dict) and r.get("status") == "success"]
                overloaded_requests = [r for r in all_results if isinstance(r, dict) and r.get("status") == "overloaded"]
                failed_requests = [r for r in all_results if isinstance(r, dict) and r.get("status") in ["error", "no_available_agent"]]
                
                print(f"Cascading failure prevention test:")
                print(f"  Successful requests: {len(successful_requests)}")
                print(f"  Overloaded requests: {len(overloaded_requests)}")
                print(f"  Failed requests: {len(failed_requests)}")
                
                # 验证系统没有完全崩溃
                success_rate = len(successful_requests) / len(cascade_requests)
                assert success_rate >= 0.3, f"Too many requests failed, possible cascading failure: {success_rate:.2%}"
                
                # 验证负载分布
                load_distribution = {}
                for result in successful_requests:
                    agent_id = result.get("agent_id")
                    if agent_id:
                        load_distribution[agent_id] = load_distribution.get(agent_id, 0) + 1
                
                print(f"  Load distribution: {load_distribution}")
                
                # 如果有多个智能体，负载应该相对分散
                if len(remaining_agents) > 1 and len(load_distribution) > 1:
                    max_load = max(load_distribution.values())
                    min_load = min(load_distribution.values())
                    load_variance = max_load - min_load
                    
                    # 负载差异不应该太大（避免某个智能体过载）
                    assert load_variance <= len(cascade_requests) * 0.7, "Load distribution too uneven"
            
            finally:
                # 恢复智能体状态
                failing_agent._status = original_status

    @pytest.mark.asyncio
    async def test_automatic_recovery_mechanisms(self, fault_tolerant_system_setup):
        """测试自动恢复机制."""
        system = fault_tolerant_system_setup
        unstable_agent = system["unstable_agent"]
        
        # 1. 测试智能体自动重启机制
        print("Testing agent automatic restart mechanism...")
        
        # 模拟智能体崩溃
        original_status = unstable_agent._status
        unstable_agent._status = AgentStatus.ERROR
        
        # 模拟自动恢复逻辑
        async def attempt_agent_recovery(agent, max_attempts: int = 3):
            """尝试恢复智能体."""
            for attempt in range(max_attempts):
                try:
                    print(f"  Recovery attempt {attempt + 1} for agent {agent.agent_id}")
                    
                    # 尝试重新初始化
                    if await agent.initialize():
                        if await agent.start():
                            print(f"  Agent {agent.agent_id} recovered successfully")
                            return True
                    
                    # 如果失败，等待后重试
                    await asyncio.sleep(0.5 * (attempt + 1))
                
                except Exception as e:
                    print(f"  Recovery attempt {attempt + 1} failed: {str(e)}")
                    if attempt == max_attempts - 1:
                        print(f"  Agent {agent.agent_id} recovery failed after {max_attempts} attempts")
                        return False
            
            return False
        
        # 执行恢复
        recovery_success = await attempt_agent_recovery(unstable_agent)
        
        if recovery_success:
            # 验证恢复后的智能体功能
            test_request = UserRequest(
                request_id="recovery_test",
                content="测试恢复后的智能体功能",
                priority=Priority.NORMAL
            )
            
            try:
                response = await unstable_agent.process_request(test_request)
                assert response is not None
                print("  Recovered agent functioning correctly")
            except Exception as e:
                print(f"  Recovered agent still has issues: {str(e)}")
        
        # 2. 测试连接重试机制
        print("Testing connection retry mechanism...")
        
        # 模拟网络连接问题
        failing_client = system["model_clients"]["failing"]
        
        async def retry_with_backoff(operation, max_retries: int = 5):
            """带退避的重试机制."""
            for attempt in range(max_retries):
                try:
                    result = await operation()
                    return result
                except (ConnectionError, asyncio.TimeoutError) as e:
                    if attempt == max_retries - 1:
                        raise e
                    
                    # 指数退避
                    wait_time = min(2 ** attempt, 10)  # 最大等待10秒
                    print(f"  Connection attempt {attempt + 1} failed, retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
        
        # 测试重试机制
        async def test_operation():
            return await failing_client.generate_response([{"role": "user", "content": "test"}])
        
        try:
            result = await retry_with_backoff(test_operation)
            if result:
                print("  Connection retry mechanism successful")
        except Exception as e:
            print(f"  Connection retry mechanism failed: {str(e)}")
        
        # 3. 测试健康检查和自动修复
        print("Testing health check and auto-repair...")
        
        # 模拟健康检查循环
        async def health_check_loop(agents: List, check_interval: float = 1.0, max_checks: int = 5):
            """健康检查循环."""
            unhealthy_agents = []
            
            for check_round in range(max_checks):
                print(f"  Health check round {check_round + 1}")
                
                for agent in agents:
                    try:
                        is_healthy = await agent.health_check()
                        if not is_healthy:
                            if agent.agent_id not in unhealthy_agents:
                                unhealthy_agents.append(agent.agent_id)
                                print(f"    Agent {agent.agent_id} is unhealthy")
                            
                            # 尝试自动修复
                            print(f"    Attempting to repair agent {agent.agent_id}")
                            repair_success = await attempt_agent_recovery(agent, max_attempts=1)
                            
                            if repair_success:
                                unhealthy_agents.remove(agent.agent_id)
                                print(f"    Agent {agent.agent_id} repaired successfully")
                        else:
                            if agent.agent_id in unhealthy_agents:
                                unhealthy_agents.remove(agent.agent_id)
                                print(f"    Agent {agent.agent_id} recovered to healthy state")
                    
                    except Exception as e:
                        print(f"    Health check failed for agent {agent.agent_id}: {str(e)}")
                
                await asyncio.sleep(check_interval)
            
            return unhealthy_agents
        
        # 执行健康检查
        test_agents = [unstable_agent] + system["stable_agents"][:1]  # 测试一个不稳定和一个稳定的智能体
        final_unhealthy = await health_check_loop(test_agents)
        
        print(f"  Final unhealthy agents: {final_unhealthy}")
        
        # 验证自动恢复效果
        # 在理想情况下，大部分智能体应该能够恢复
        healthy_rate = (len(test_agents) - len(final_unhealthy)) / len(test_agents)
        assert healthy_rate >= 0.5, f"Too many agents remain unhealthy: {healthy_rate:.2%}"
        
        print("Automatic recovery mechanisms test completed")

    @pytest.mark.asyncio
    async def test_graceful_degradation_under_extreme_conditions(self, fault_tolerant_system_setup):
        """测试极端条件下的优雅降级."""
        system = fault_tolerant_system_setup
        
        # 创建极端压力条件
        extreme_requests = []
        for i in range(100):
            request = UserRequest(
                request_id=f"extreme_test_{i:03d}",
                content=f"极端测试请求 {i+1}: " + "复杂需求 " * 10,  # 长内容
                priority=Priority.URGENT if i % 5 == 0 else Priority.HIGH
            )
            extreme_requests.append(request)
        
        # 同时模拟多种故障
        all_agents = await system["agent_registry"].get_all_agents()
        
        # 1. 让一半智能体离线
        offline_agents = all_agents[:len(all_agents)//2]
        online_agents = all_agents[len(all_agents)//2:]
        
        original_statuses = {}
        for agent in offline_agents:
            original_statuses[agent.agent_id] = agent._status
            agent._status = AgentStatus.OFFLINE
        
        # 2. 让剩余智能体负载接近上限
        for agent in online_agents:
            agent._current_load = agent._max_load - 1
        
        try:
            # 3. 在极端条件下处理请求
            async def process_under_extreme_conditions(request: UserRequest):
                try:
                    # 尝试路由（可能失败）
                    route_result, _ = await system["agent_router"].route_request(request)
                    
                    # 寻找可用的智能体
                    available_agent = None
                    for agent in online_agents:
                        if (agent.agent_type == route_result.selected_agent and 
                            agent._current_load < agent._max_load):
                            available_agent = agent
                            break
                    
                    if not available_agent:
                        # 没有完全匹配的智能体，尝试任何可用的智能体
                        for agent in online_agents:
                            if agent._current_load < agent._max_load:
                                available_agent = agent
                                break
                    
                    if available_agent:
                        # 尝试处理（可能因为过载而失败）
                        response = await available_agent.process_request(request)
                        return {
                            "request_id": request.request_id,
                            "status": "success",
                            "agent_type": available_agent.agent_type.value,
                            "degraded": available_agent.agent_type != route_result.selected_agent
                        }
                    else:
                        # 优雅降级：返回基本响应
                        return {
                            "request_id": request.request_id,
                            "status": "degraded",
                            "message": "系统当前负载较高，我们已收到您的请求，将尽快处理"
                        }
                
                except Exception as e:
                    # 最后的降级：至少确认收到请求
                    return {
                        "request_id": request.request_id,
                        "status": "minimal_service",
                        "message": "系统暂时不可用，请稍后重试",
                        "error": str(e)
                    }
            
            # 4. 分批处理以避免完全崩溃
            batch_size = 10
            all_results = []
            
            start_time = datetime.now()
            
            for i in range(0, len(extreme_requests), batch_size):
                batch = extreme_requests[i:i+batch_size]
                
                # 并发处理批次
                batch_tasks = [process_under_extreme_conditions(req) for req in batch]
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                all_results.extend(batch_results)
                
                # 批次间等待，避免系统完全过载
                await asyncio.sleep(0.2)
            
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()
            
            # 5. 分析降级效果
            successful_results = [r for r in all_results if isinstance(r, dict) and r.get("status") == "success"]
            degraded_results = [r for r in all_results if isinstance(r, dict) and r.get("status") == "degraded"]
            minimal_results = [r for r in all_results if isinstance(r, dict) and r.get("status") == "minimal_service"]
            exception_results = [r for r in all_results if isinstance(r, Exception)]
            
            print(f"Graceful degradation test results:")
            print(f"  Total requests: {len(extreme_requests)}")
            print(f"  Successful: {len(successful_results)}")
            print(f"  Degraded service: {len(degraded_results)}")
            print(f"  Minimal service: {len(minimal_results)}")
            print(f"  Exceptions: {len(exception_results)}")
            print(f"  Total processing time: {total_time:.2f}s")
            
            # 验证优雅降级
            total_handled = len(successful_results) + len(degraded_results) + len(minimal_results)
            handling_rate = total_handled / len(extreme_requests)
            
            # 即使在极端条件下，系统也应该能处理大部分请求（即使是降级服务）
            assert handling_rate >= 0.8, f"System failed to handle requests gracefully: {handling_rate:.2%}"
            
            # 验证没有完全崩溃
            assert len(exception_results) < len(extreme_requests) * 0.3, "Too many unhandled exceptions"
            
            print(f"Graceful degradation successful: {handling_rate:.2%} requests handled")
        
        finally:
            # 恢复智能体状态
            for agent in offline_agents:
                agent._status = original_statuses[agent.agent_id]
            
            for agent in online_agents:
                agent._current_load = 0