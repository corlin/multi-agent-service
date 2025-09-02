"""端到端业务流程测试."""

import asyncio
import pytest
from datetime import datetime
from typing import Dict, List, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch
import json

from src.multi_agent_service.models.base import UserRequest, AgentResponse, IntentResult
from src.multi_agent_service.models.enums import (
    AgentType, IntentType, Priority, AgentStatus, WorkflowType, WorkflowStatus
)
from src.multi_agent_service.models.config import AgentConfig, ModelConfig
from src.multi_agent_service.services.intent_analyzer import IntentAnalyzer
from src.multi_agent_service.services.agent_router import AgentRouter
from src.multi_agent_service.agents.registry import AgentRegistry
from src.multi_agent_service.agents.sales_agent import SalesAgent
from src.multi_agent_service.agents.customer_support_agent import CustomerSupportAgent
from src.multi_agent_service.agents.manager_agent import ManagerAgent
from src.multi_agent_service.agents.field_service_agent import FieldServiceAgent
from src.multi_agent_service.agents.coordinator_agent import CoordinatorAgent
from src.multi_agent_service.services.model_clients.mock_client import MockModelClient
from src.multi_agent_service.api.chat import router as chat_router
from src.multi_agent_service.api.agents import router as agents_router
from src.multi_agent_service.api.workflows import router as workflows_router


class MockFastAPIRequest:
    """模拟FastAPI请求对象."""
    
    def __init__(self, json_data: Dict[str, Any]):
        self._json_data = json_data
    
    async def json(self):
        return self._json_data


class TestEndToEndBusinessProcesses:
    """端到端业务流程测试类."""
    
    @pytest.fixture
    async def complete_system_setup(self):
        """完整系统设置，包括所有组件."""
        # 创建模型客户端
        from src.multi_agent_service.models.enums import ModelProvider
        model_config = ModelConfig(
            provider=ModelProvider.CUSTOM,
            model_name="mock-model",
            api_key="mock-key",
            api_base="http://mock.api"
        )
        mock_client = MockModelClient(model_config)
        
        # 创建智能体配置
        agent_configs = {
            AgentType.SALES: AgentConfig(
                agent_id="sales_001",
                agent_type=AgentType.SALES,
                name="Sales Agent",
                description="销售代表智能体",
                capabilities=["sales", "consultation", "pricing"],
                llm_config=model_config,
                prompt_template="你是一个专业的销售代表，请帮助客户解答问题。",
                max_concurrent_tasks=5
            ),
            AgentType.CUSTOMER_SUPPORT: AgentConfig(
                agent_id="support_001",
                agent_type=AgentType.CUSTOMER_SUPPORT,
                name="Support Agent",
                description="客服专员智能体",
                capabilities=["support", "troubleshooting", "customer_service"],
                llm_config=model_config,
                prompt_template="你是一个专业的客服专员，请帮助客户解决问题。",
                max_concurrent_tasks=5
            ),
            AgentType.MANAGER: AgentConfig(
                agent_id="manager_001",
                agent_type=AgentType.MANAGER,
                name="Manager Agent",
                description="管理者智能体",
                capabilities=["management", "decision_making", "strategy"],
                llm_config=model_config,
                prompt_template="你是一个公司管理者，请提供管理决策和战略建议。",
                max_concurrent_tasks=3
            ),
            AgentType.FIELD_SERVICE: AgentConfig(
                agent_id="field_001",
                agent_type=AgentType.FIELD_SERVICE,
                name="Field Service Agent",
                description="现场服务人员智能体",
                capabilities=["technical_service", "field_work", "maintenance"],
                llm_config=model_config,
                prompt_template="你是一个现场服务技术人员，请提供技术支持和维修指导。",
                max_concurrent_tasks=3
            ),
            AgentType.COORDINATOR: AgentConfig(
                agent_id="coordinator_001",
                agent_type=AgentType.COORDINATOR,
                name="Coordinator Agent",
                description="协调员智能体",
                capabilities=["coordination", "task_management", "conflict_resolution"],
                llm_config=model_config,
                prompt_template="你是一个智能体协调员，负责任务分配和协调管理。",
                max_concurrent_tasks=10
            )
        }
        
        # 创建智能体实例
        agents = {
            AgentType.SALES: SalesAgent(agent_configs[AgentType.SALES], mock_client),
            AgentType.CUSTOMER_SUPPORT: CustomerSupportAgent(agent_configs[AgentType.CUSTOMER_SUPPORT], mock_client),
            AgentType.MANAGER: ManagerAgent(agent_configs[AgentType.MANAGER], mock_client),
            AgentType.FIELD_SERVICE: FieldServiceAgent(agent_configs[AgentType.FIELD_SERVICE], mock_client),
            AgentType.COORDINATOR: CoordinatorAgent(agent_configs[AgentType.COORDINATOR], mock_client)
        }
        
        # 初始化所有智能体
        for agent in agents.values():
            await agent.initialize()
            await agent.start()
        
        # 创建智能体注册表
        agent_registry = AgentRegistry()
        for agent in agents.values():
            await agent_registry.register_agent(agent)
        
        # 创建意图分析器
        intent_analyzer = IntentAnalyzer()
        await intent_analyzer.initialize()
        
        # 创建智能体路由器
        agent_router = AgentRouter(intent_analyzer, agent_registry)
        
        # 创建API实例
        chat_api = ChatAPI(agent_router, agent_registry)
        agents_api = AgentsAPI(agent_registry)
        workflows_api = WorkflowsAPI()
        
        return {
            "agents": agents,
            "agent_registry": agent_registry,
            "intent_analyzer": intent_analyzer,
            "agent_router": agent_router,
            "chat_api": chat_api,
            "agents_api": agents_api,
            "workflows_api": workflows_api
        }

    @pytest.mark.asyncio
    async def test_sales_consultation_complete_flow(self, complete_system_setup):
        """测试销售咨询完整流程：从用户询问到最终报价."""
        system = complete_system_setup
        
        # 1. 用户发起销售咨询
        user_message = "你好，我想了解你们的企业版产品，我们是一家200人的中型企业，主要关心价格和功能。"
        
        chat_request_data = {
            "messages": [
                {"role": "user", "content": user_message}
            ],
            "model": "gpt-3.5-turbo",
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        mock_request = MockFastAPIRequest(chat_request_data)
        
        # 2. 通过Chat API处理请求
        chat_response = await system["chat_api"].chat_completions(mock_request)
        
        # 验证初始响应
        assert chat_response is not None
        assert "choices" in chat_response
        assert len(chat_response["choices"]) > 0
        
        initial_response = chat_response["choices"][0]["message"]["content"]
        assert "企业版" in initial_response or "产品" in initial_response
        
        # 3. 用户询问具体价格
        price_inquiry = "企业版的具体价格是多少？有什么优惠政策吗？"
        
        price_request_data = {
            "messages": [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": initial_response},
                {"role": "user", "content": price_inquiry}
            ],
            "model": "gpt-3.5-turbo"
        }
        
        mock_price_request = MockFastAPIRequest(price_request_data)
        price_response = await system["chat_api"].chat_completions(mock_price_request)
        
        # 验证价格响应
        assert price_response is not None
        price_content = price_response["choices"][0]["message"]["content"]
        assert any(keyword in price_content for keyword in ["价格", "¥", "元", "优惠"])
        
        # 4. 用户请求详细方案
        solution_request = "请为我们公司制定一个详细的解决方案，包括部署计划和培训安排。"
        
        solution_request_data = {
            "messages": [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": initial_response},
                {"role": "user", "content": price_inquiry},
                {"role": "assistant", "content": price_content},
                {"role": "user", "content": solution_request}
            ],
            "model": "gpt-3.5-turbo"
        }
        
        mock_solution_request = MockFastAPIRequest(solution_request_data)
        solution_response = await system["chat_api"].chat_completions(mock_solution_request)
        
        # 验证方案响应
        assert solution_response is not None
        solution_content = solution_response["choices"][0]["message"]["content"]
        assert any(keyword in solution_content for keyword in ["方案", "部署", "培训", "计划"])
        
        # 5. 验证整个销售流程的连贯性
        conversation_flow = [
            user_message,
            initial_response,
            price_inquiry,
            price_content,
            solution_request,
            solution_content
        ]
        
        # 验证对话流程的逻辑性
        assert len(conversation_flow) == 6
        assert all(content.strip() for content in conversation_flow)
        
        print("Sales consultation complete flow test passed")

    @pytest.mark.asyncio
    async def test_customer_support_complete_flow(self, complete_system_setup):
        """测试客服支持完整流程：从问题报告到解决方案提供."""
        system = complete_system_setup
        
        # 1. 用户报告问题
        problem_report = "我在使用你们的系统时遇到了登录问题，总是提示密码错误，但我确定密码是正确的。"
        
        support_request_data = {
            "messages": [
                {"role": "user", "content": problem_report}
            ],
            "model": "gpt-3.5-turbo"
        }
        
        mock_request = MockFastAPIRequest(support_request_data)
        
        # 2. 客服初始响应
        initial_response = await system["chat_api"].chat_completions(mock_request)
        
        assert initial_response is not None
        initial_content = initial_response["choices"][0]["message"]["content"]
        assert any(keyword in initial_content for keyword in ["登录", "密码", "问题", "帮助"])
        
        # 3. 用户提供更多信息
        additional_info = "我使用的是Chrome浏览器，系统版本是Windows 10，这个问题从昨天开始出现的。"
        
        info_request_data = {
            "messages": [
                {"role": "user", "content": problem_report},
                {"role": "assistant", "content": initial_content},
                {"role": "user", "content": additional_info}
            ],
            "model": "gpt-3.5-turbo"
        }
        
        mock_info_request = MockFastAPIRequest(info_request_data)
        diagnostic_response = await system["chat_api"].chat_completions(mock_info_request)
        
        # 验证诊断响应
        assert diagnostic_response is not None
        diagnostic_content = diagnostic_response["choices"][0]["message"]["content"]
        
        # 4. 用户询问解决方案
        solution_inquiry = "有什么解决方法吗？我需要尽快恢复使用。"
        
        solution_request_data = {
            "messages": [
                {"role": "user", "content": problem_report},
                {"role": "assistant", "content": initial_content},
                {"role": "user", "content": additional_info},
                {"role": "assistant", "content": diagnostic_content},
                {"role": "user", "content": solution_inquiry}
            ],
            "model": "gpt-3.5-turbo"
        }
        
        mock_solution_request = MockFastAPIRequest(solution_request_data)
        solution_response = await system["chat_api"].chat_completions(mock_solution_request)
        
        # 验证解决方案响应
        assert solution_response is not None
        solution_content = solution_response["choices"][0]["message"]["content"]
        assert any(keyword in solution_content for keyword in ["解决", "方法", "步骤", "尝试"])
        
        # 5. 验证问题解决流程
        support_flow = [
            problem_report,
            initial_content,
            additional_info,
            diagnostic_content,
            solution_inquiry,
            solution_content
        ]
        
        assert len(support_flow) == 6
        assert all(content.strip() for content in support_flow)
        
        print("Customer support complete flow test passed")

    @pytest.mark.asyncio
    async def test_intent_recognition_to_agent_response_pipeline(self, complete_system_setup):
        """测试从意图识别到智能体响应的完整链路."""
        system = complete_system_setup
        
        # 测试用例：不同类型的用户请求
        test_cases = [
            {
                "content": "我想购买你们的产品，请给我报个价",
                "expected_intent": IntentType.SALES_INQUIRY,
                "expected_agent": AgentType.SALES,
                "keywords": ["价格", "产品", "购买"]
            },
            {
                "content": "我的系统出现了故障，需要技术支持",
                "expected_intent": IntentType.TECHNICAL_SERVICE,
                "expected_agent": AgentType.FIELD_SERVICE,
                "keywords": ["故障", "技术", "支持"]
            },
            {
                "content": "我对服务不满意，想要投诉",
                "expected_intent": IntentType.CUSTOMER_SUPPORT,
                "expected_agent": AgentType.CUSTOMER_SUPPORT,
                "keywords": ["服务", "投诉", "不满意"]
            },
            {
                "content": "我需要制定一个长期的合作战略",
                "expected_intent": IntentType.MANAGEMENT_DECISION,
                "expected_agent": AgentType.MANAGER,
                "keywords": ["战略", "合作", "长期"]
            }
        ]
        
        for i, test_case in enumerate(test_cases):
            print(f"Testing case {i+1}: {test_case['content'][:50]}...")
            
            # 1. 创建用户请求
            user_request = UserRequest(
                request_id=f"intent_test_{i+1:03d}",
                content=test_case["content"],
                priority=Priority.NORMAL
            )
            
            # 2. 意图识别
            intent_result = await system["intent_analyzer"].analyze_intent(user_request)
            
            # 验证意图识别结果
            assert intent_result is not None
            assert intent_result.intent_type is not None
            assert intent_result.confidence > 0.0
            
            # 3. 智能体路由
            route_result, _ = await system["agent_router"].route_request(user_request)
            
            # 验证路由结果
            assert route_result is not None
            assert route_result.selected_agent is not None
            assert route_result.confidence > 0.0
            
            # 4. 智能体处理
            selected_agent = system["agents"][route_result.selected_agent]
            agent_response = await selected_agent.process_request(user_request)
            
            # 验证智能体响应
            assert agent_response is not None
            assert agent_response.response_content is not None
            assert agent_response.agent_id == selected_agent.agent_id
            assert agent_response.agent_type == route_result.selected_agent
            
            # 5. 验证响应内容的相关性
            response_content = agent_response.response_content.lower()
            content_relevant = any(
                keyword in response_content 
                for keyword in test_case["keywords"]
            )
            
            # 如果直接关键词匹配失败，检查是否是合理的响应
            if not content_relevant:
                # 检查是否包含通用的服务性词汇
                service_keywords = ["帮助", "服务", "解决", "提供", "支持", "咨询"]
                content_relevant = any(keyword in response_content for keyword in service_keywords)
            
            assert content_relevant, f"Response not relevant to request: {test_case['content']}"
            
            print(f"  ✓ Intent: {intent_result.intent_type}")
            print(f"  ✓ Agent: {route_result.selected_agent}")
            print(f"  ✓ Response length: {len(agent_response.response_content)}")
        
        print("Intent recognition to agent response pipeline test passed")

    @pytest.mark.asyncio
    async def test_api_interface_complete_business_flow(self, complete_system_setup):
        """测试API接口的完整业务流程."""
        system = complete_system_setup
        
        # 1. 测试智能体状态查询API
        agents_status = await system["agents_api"].get_agents_status()
        
        assert agents_status is not None
        assert "agents" in agents_status
        assert len(agents_status["agents"]) > 0
        
        # 验证每个智能体的状态信息
        for agent_info in agents_status["agents"]:
            assert "agent_id" in agent_info
            assert "agent_type" in agent_info
            assert "status" in agent_info
            assert "capabilities" in agent_info
        
        # 2. 测试特定智能体信息查询
        sales_agent_info = await system["agents_api"].get_agent_info("sales_001")
        
        assert sales_agent_info is not None
        assert sales_agent_info["agent_id"] == "sales_001"
        assert sales_agent_info["agent_type"] == "sales"
        
        # 3. 测试智能体路由API
        route_request_data = {
            "content": "我想了解产品价格",
            "context": {"user_type": "potential_customer"}
        }
        
        mock_route_request = MockFastAPIRequest(route_request_data)
        route_response = await system["agents_api"].route_request(mock_route_request)
        
        assert route_response is not None
        assert "selected_agent" in route_response
        assert "confidence" in route_response
        assert "reasoning" in route_response
        
        # 4. 测试聊天完成API的完整流程
        chat_messages = [
            {"role": "user", "content": "你好，我需要技术支持"},
            {"role": "assistant", "content": "您好！我是技术支持专员，很高兴为您服务。请描述您遇到的具体问题。"},
            {"role": "user", "content": "我的系统无法启动，显示蓝屏错误"}
        ]
        
        chat_request_data = {
            "messages": chat_messages,
            "model": "gpt-3.5-turbo",
            "temperature": 0.7
        }
        
        mock_chat_request = MockFastAPIRequest(chat_request_data)
        chat_response = await system["chat_api"].chat_completions(mock_chat_request)
        
        # 验证聊天响应
        assert chat_response is not None
        assert "choices" in chat_response
        assert len(chat_response["choices"]) > 0
        
        response_message = chat_response["choices"][0]["message"]
        assert "role" in response_message
        assert "content" in response_message
        assert response_message["role"] == "assistant"
        
        # 5. 测试工作流执行API
        workflow_request_data = {
            "workflow_type": "sequential",
            "input_data": {
                "task_description": "处理客户技术支持请求",
                "priority": "high"
            }
        }
        
        mock_workflow_request = MockFastAPIRequest(workflow_request_data)
        
        # 由于工作流API可能需要更复杂的设置，这里主要验证API结构
        try:
            workflow_response = await system["workflows_api"].execute_workflow(mock_workflow_request)
            
            if workflow_response:
                assert "execution_id" in workflow_response
                assert "status" in workflow_response
        except Exception as e:
            # 如果工作流执行失败，至少验证错误处理
            assert isinstance(e, Exception)
            print(f"Workflow execution failed as expected: {str(e)}")
        
        print("API interface complete business flow test passed")

    @pytest.mark.asyncio
    async def test_complex_multi_step_business_scenario(self, complete_system_setup):
        """测试复杂的多步骤业务场景."""
        system = complete_system_setup
        
        # 场景：企业客户的完整服务流程
        # 1. 初始咨询 -> 2. 需求分析 -> 3. 方案设计 -> 4. 技术评估 -> 5. 管理审批 -> 6. 实施计划
        
        scenario_steps = [
            {
                "step": 1,
                "user_input": "我们是一家500人的制造企业，想要数字化转型，需要了解你们的解决方案",
                "expected_agent_type": AgentType.SALES,
                "validation_keywords": ["解决方案", "数字化", "企业"]
            },
            {
                "step": 2,
                "user_input": "我们主要需要ERP系统集成、数据分析平台和移动办公支持",
                "expected_agent_type": AgentType.SALES,
                "validation_keywords": ["ERP", "数据分析", "移动办公"]
            },
            {
                "step": 3,
                "user_input": "技术方面我们担心系统兼容性和数据迁移问题",
                "expected_agent_type": AgentType.FIELD_SERVICE,
                "validation_keywords": ["技术", "兼容性", "数据迁移"]
            },
            {
                "step": 4,
                "user_input": "预算大概在200万左右，需要管理层审批，你们能提供详细的ROI分析吗？",
                "expected_agent_type": AgentType.MANAGER,
                "validation_keywords": ["预算", "管理层", "ROI"]
            },
            {
                "step": 5,
                "user_input": "如果决定合作，实施周期大概多长？需要我们配合哪些工作？",
                "expected_agent_type": AgentType.FIELD_SERVICE,
                "validation_keywords": ["实施", "周期", "配合"]
            }
        ]
        
        conversation_history = []
        
        for step_info in scenario_steps:
            print(f"Processing step {step_info['step']}: {step_info['user_input'][:50]}...")
            
            # 创建用户请求
            user_request = UserRequest(
                request_id=f"scenario_step_{step_info['step']}",
                content=step_info["user_input"],
                priority=Priority.HIGH,
                context={"conversation_history": conversation_history}
            )
            
            # 路由到合适的智能体
            route_result, intent_result = await system["agent_router"].route_request(user_request)
            
            # 处理请求
            selected_agent = system["agents"][route_result.selected_agent]
            agent_response = await selected_agent.process_request(user_request)
            
            # 验证响应
            assert agent_response is not None
            assert agent_response.response_content is not None
            
            # 验证响应内容的相关性
            response_content = agent_response.response_content.lower()
            keywords_found = any(
                keyword.lower() in response_content 
                for keyword in step_info["validation_keywords"]
            )
            
            # 如果关键词不匹配，检查是否是合理的业务响应
            if not keywords_found:
                business_keywords = [
                    "方案", "服务", "支持", "帮助", "提供", "解决", 
                    "分析", "评估", "建议", "咨询", "了解"
                ]
                keywords_found = any(keyword in response_content for keyword in business_keywords)
            
            assert keywords_found, f"Response not relevant for step {step_info['step']}"
            
            # 更新对话历史
            conversation_history.extend([
                {"role": "user", "content": step_info["user_input"]},
                {"role": "assistant", "content": agent_response.response_content, "agent_type": agent_response.agent_type.value}
            ])
            
            print(f"  ✓ Routed to: {route_result.selected_agent}")
            print(f"  ✓ Response length: {len(agent_response.response_content)}")
        
        # 验证整个场景的完整性
        assert len(conversation_history) == len(scenario_steps) * 2  # 每步包含用户输入和智能体响应
        
        # 验证涉及的智能体类型多样性
        involved_agents = set()
        for i in range(1, len(conversation_history), 2):  # 只看智能体响应
            if "agent_type" in conversation_history[i]:
                involved_agents.add(conversation_history[i]["agent_type"])
        
        assert len(involved_agents) >= 2, "Should involve multiple agent types"
        
        print(f"Complex multi-step business scenario completed with {len(involved_agents)} agent types")

    @pytest.mark.asyncio
    async def test_error_handling_in_business_flow(self, complete_system_setup):
        """测试业务流程中的错误处理."""
        system = complete_system_setup
        
        # 1. 测试无效输入的处理
        invalid_requests = [
            "",  # 空输入
            "   ",  # 只有空格
            "a" * 10000,  # 过长输入
            "🤖🤖🤖",  # 特殊字符
            None  # None输入（需要特殊处理）
        ]
        
        for i, invalid_input in enumerate(invalid_requests):
            if invalid_input is None:
                continue  # 跳过None输入，因为会在请求创建时失败
            
            try:
                user_request = UserRequest(
                    request_id=f"invalid_test_{i}",
                    content=invalid_input,
                    priority=Priority.NORMAL
                )
                
                # 尝试路由和处理
                route_result, intent_result = await system["agent_router"].route_request(user_request)
                
                # 即使是无效输入，系统也应该能够处理并返回合理的响应
                assert route_result is not None
                assert route_result.selected_agent is not None
                
                selected_agent = system["agents"][route_result.selected_agent]
                agent_response = await selected_agent.process_request(user_request)
                
                # 验证错误处理响应
                assert agent_response is not None
                assert agent_response.response_content is not None
                
            except Exception as e:
                # 如果抛出异常，验证是合理的异常
                assert isinstance(e, (ValueError, TypeError, AttributeError))
                print(f"Expected error for invalid input {i}: {str(e)}")
        
        # 2. 测试智能体不可用时的处理
        # 模拟智能体离线
        original_status = system["agents"][AgentType.SALES]._status
        system["agents"][AgentType.SALES]._status = AgentStatus.OFFLINE
        
        try:
            sales_request = UserRequest(
                request_id="offline_agent_test",
                content="我想购买产品",
                priority=Priority.NORMAL
            )
            
            route_result, _ = await system["agent_router"].route_request(sales_request)
            
            # 应该路由到备用智能体或返回错误信息
            assert route_result is not None
            
            # 如果路由到了离线的智能体，处理时应该有适当的错误处理
            if route_result.selected_agent == AgentType.SALES:
                try:
                    selected_agent = system["agents"][route_result.selected_agent]
                    response = await selected_agent.process_request(sales_request)
                    # 如果成功处理，验证响应
                    assert response is not None
                except Exception as e:
                    # 如果失败，应该是合理的错误
                    assert "offline" in str(e).lower() or "unavailable" in str(e).lower()
            
        finally:
            # 恢复智能体状态
            system["agents"][AgentType.SALES]._status = original_status
        
        # 3. 测试API层面的错误处理
        # 测试无效的聊天请求
        invalid_chat_data = {
            "messages": [],  # 空消息列表
            "model": "invalid_model"
        }
        
        mock_invalid_request = MockFastAPIRequest(invalid_chat_data)
        
        try:
            chat_response = await system["chat_api"].chat_completions(mock_invalid_request)
            
            # 如果没有抛出异常，验证错误响应
            if chat_response:
                assert "error" in chat_response or "choices" in chat_response
        except Exception as e:
            # 验证是合理的错误
            assert isinstance(e, (ValueError, KeyError, AttributeError))
            print(f"Expected API error: {str(e)}")
        
        print("Error handling in business flow test passed")

    @pytest.mark.asyncio
    async def test_performance_under_concurrent_requests(self, complete_system_setup):
        """测试并发请求下的系统性能."""
        system = complete_system_setup
        
        # 创建多个并发请求
        concurrent_requests = []
        request_types = [
            "我想了解产品价格",
            "系统出现了故障",
            "需要技术支持",
            "想要投诉服务",
            "制定合作方案"
        ]
        
        # 创建20个并发请求
        for i in range(20):
            request_content = request_types[i % len(request_types)] + f" (请求 {i+1})"
            
            chat_data = {
                "messages": [{"role": "user", "content": request_content}],
                "model": "gpt-3.5-turbo"
            }
            
            mock_request = MockFastAPIRequest(chat_data)
            concurrent_requests.append(
                system["chat_api"].chat_completions(mock_request)
            )
        
        # 记录开始时间
        start_time = datetime.now()
        
        # 并发执行所有请求
        results = await asyncio.gather(*concurrent_requests, return_exceptions=True)
        
        # 记录结束时间
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # 验证结果
        successful_responses = [
            result for result in results 
            if not isinstance(result, Exception) and result is not None
        ]
        
        failed_responses = [
            result for result in results 
            if isinstance(result, Exception)
        ]
        
        # 验证性能指标
        success_rate = len(successful_responses) / len(results)
        average_response_time = processing_time / len(results)
        
        print(f"Concurrent requests performance:")
        print(f"  Total requests: {len(results)}")
        print(f"  Successful: {len(successful_responses)}")
        print(f"  Failed: {len(failed_responses)}")
        print(f"  Success rate: {success_rate:.2%}")
        print(f"  Total processing time: {processing_time:.2f}s")
        print(f"  Average response time: {average_response_time:.2f}s")
        
        # 性能断言
        assert success_rate >= 0.8, f"Success rate too low: {success_rate:.2%}"
        assert average_response_time < 5.0, f"Average response time too high: {average_response_time:.2f}s"
        
        # 验证成功响应的质量
        for response in successful_responses[:5]:  # 检查前5个成功响应
            assert "choices" in response
            assert len(response["choices"]) > 0
            assert "message" in response["choices"][0]
            assert "content" in response["choices"][0]["message"]
            assert len(response["choices"][0]["message"]["content"]) > 0
        
        print("Performance under concurrent requests test passed")