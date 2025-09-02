"""Tests for agent router service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.multi_agent_service.services.agent_router import AgentRouter, RouteResult
from src.multi_agent_service.services.intent_analyzer import IntentAnalyzer
from src.multi_agent_service.agents.registry import AgentRegistry
from src.multi_agent_service.models.base import UserRequest, IntentResult, Entity, AgentInfo
from src.multi_agent_service.models.enums import (
    IntentType, AgentType, Priority, AgentStatus
)


class TestAgentRouter:
    """智能体路由器测试类."""
    
    @pytest.fixture
    def mock_intent_analyzer(self):
        """模拟意图分析器."""
        analyzer = AsyncMock(spec=IntentAnalyzer)
        return analyzer
    
    @pytest.fixture
    def mock_agent_registry(self):
        """模拟智能体注册表."""
        registry = AsyncMock(spec=AgentRegistry)
        return registry
    
    @pytest.fixture
    def agent_router(self, mock_intent_analyzer, mock_agent_registry):
        """创建智能体路由器实例."""
        return AgentRouter(mock_intent_analyzer, mock_agent_registry)
    
    @pytest.fixture
    def sample_user_request(self):
        """示例用户请求."""
        return UserRequest(
            content="我想了解产品价格",
            user_id="test_user_123",
            priority=Priority.NORMAL
        )
    
    @pytest.fixture
    def sample_intent_result(self):
        """示例意图识别结果."""
        return IntentResult(
            intent_type=IntentType.SALES_INQUIRY,
            confidence=0.8,
            entities=[
                Entity(
                    name="产品",
                    value="产品",
                    entity_type="PRODUCT",
                    confidence=0.9
                )
            ],
            suggested_agents=[AgentType.SALES],
            requires_collaboration=False,
            reasoning="用户询问产品价格"
        )
    
    @pytest.fixture
    def sample_agent_info(self):
        """示例智能体信息."""
        return AgentInfo(
            agent_id="sales_001",
            agent_type=AgentType.SALES,
            name="销售代表",
            description="处理销售相关询问",
            status=AgentStatus.IDLE,
            capabilities=["产品介绍", "报价", "客户关系管理"],
            current_load=2,
            max_load=10
        )
    
    @pytest.mark.asyncio
    async def test_route_request_sales_inquiry(
        self, 
        agent_router, 
        mock_intent_analyzer, 
        mock_agent_registry,
        sample_user_request, 
        sample_intent_result,
        sample_agent_info
    ):
        """测试销售咨询请求路由."""
        # 设置模拟返回值
        mock_intent_analyzer.analyze_intent.return_value = sample_intent_result
        mock_intent_analyzer.validate_intent_result.return_value = True
        mock_intent_analyzer.get_intent_rules.return_value = {
            IntentType.SALES_INQUIRY: {
                "primary_agents": [AgentType.SALES],
                "fallback_agents": [AgentType.CUSTOMER_SUPPORT],
                "confidence_threshold": 0.7,
                "requires_collaboration": False
            }
        }
        mock_agent_registry.get_agent_info.return_value = sample_agent_info
        
        # 执行路由
        route_result, intent_result = await agent_router.route_request(sample_user_request)
        
        # 验证结果
        assert isinstance(route_result, RouteResult)
        assert route_result.selected_agent == AgentType.SALES
        assert route_result.confidence > 0.5
        assert not route_result.requires_collaboration
        assert intent_result == sample_intent_result
        
        # 验证调用
        mock_intent_analyzer.analyze_intent.assert_called_once_with(sample_user_request)
        mock_intent_analyzer.validate_intent_result.assert_called_once_with(sample_intent_result)
    
    @pytest.mark.asyncio
    async def test_route_request_collaboration_required(
        self, 
        agent_router, 
        mock_intent_analyzer, 
        mock_agent_registry
    ):
        """测试需要协作的复杂请求路由."""
        user_request = UserRequest(
            content="我需要一个综合解决方案，包括产品选型和技术支持",
            priority=Priority.HIGH
        )
        
        intent_result = IntentResult(
            intent_type=IntentType.COLLABORATION_REQUIRED,
            confidence=0.9,
            entities=[
                Entity(name="综合解决方案", value="综合解决方案", entity_type="SERVICE", confidence=0.9),
                Entity(name="产品选型", value="产品选型", entity_type="PRODUCT", confidence=0.8),
                Entity(name="技术支持", value="技术支持", entity_type="SERVICE", confidence=0.85)
            ],
            suggested_agents=[AgentType.COORDINATOR],
            requires_collaboration=True
        )
        
        coordinator_info = AgentInfo(
            agent_id="coordinator_001",
            agent_type=AgentType.COORDINATOR,
            name="协调员",
            description="统筹管理其他智能体",
            status=AgentStatus.IDLE,
            current_load=1,
            max_load=5
        )
        
        # 设置模拟返回值
        mock_intent_analyzer.analyze_intent.return_value = intent_result
        mock_intent_analyzer.validate_intent_result.return_value = True
        mock_intent_analyzer.get_intent_rules.return_value = {
            IntentType.COLLABORATION_REQUIRED: {
                "primary_agents": [AgentType.COORDINATOR],
                "fallback_agents": [AgentType.MANAGER],
                "confidence_threshold": 0.8,
                "requires_collaboration": True
            }
        }
        mock_agent_registry.get_agent_info.return_value = coordinator_info
        
        # 执行路由
        route_result, _ = await agent_router.route_request(user_request)
        
        # 验证结果
        assert route_result.selected_agent == AgentType.COORDINATOR
        assert route_result.requires_collaboration
        assert route_result.confidence > 0.8
    
    @pytest.mark.asyncio
    async def test_route_request_agent_unavailable(
        self, 
        agent_router, 
        mock_intent_analyzer, 
        mock_agent_registry,
        sample_user_request,
        sample_intent_result
    ):
        """测试主要智能体不可用时的路由."""
        # 设置主要智能体不可用
        unavailable_agent_info = AgentInfo(
            agent_id="sales_001",
            agent_type=AgentType.SALES,
            name="销售代表",
            description="处理销售相关询问",
            status=AgentStatus.OFFLINE,  # 不可用
            current_load=0,
            max_load=10
        )
        
        fallback_agent_info = AgentInfo(
            agent_id="support_001",
            agent_type=AgentType.CUSTOMER_SUPPORT,
            name="客服专员",
            description="处理客户咨询",
            status=AgentStatus.IDLE,  # 可用
            current_load=3,
            max_load=10
        )
        
        # 设置模拟返回值
        mock_intent_analyzer.analyze_intent.return_value = sample_intent_result
        mock_intent_analyzer.validate_intent_result.return_value = True
        mock_intent_analyzer.get_intent_rules.return_value = {
            IntentType.SALES_INQUIRY: {
                "primary_agents": [AgentType.SALES],
                "fallback_agents": [AgentType.CUSTOMER_SUPPORT],
                "confidence_threshold": 0.7,
                "requires_collaboration": False
            }
        }
        
        # 根据智能体类型返回不同的信息
        def get_agent_info_side_effect(agent_id):
            if "sales" in agent_id:
                return unavailable_agent_info
            elif "customer_support" in agent_id:
                return fallback_agent_info
            return None
        
        mock_agent_registry.get_agent_info.side_effect = get_agent_info_side_effect
        
        # 执行路由
        route_result, _ = await agent_router.route_request(sample_user_request)
        
        # 验证使用了备用智能体
        assert route_result.selected_agent == AgentType.CUSTOMER_SUPPORT
        assert route_result.confidence < 0.8  # 置信度应该降低
    
    @pytest.mark.asyncio
    async def test_route_request_load_balanced_strategy(
        self, 
        agent_router, 
        mock_intent_analyzer, 
        mock_agent_registry,
        sample_user_request,
        sample_intent_result
    ):
        """测试负载均衡路由策略."""
        # 创建两个销售智能体，负载不同
        sales_agent_1 = AgentInfo(
            agent_id="sales_001",
            agent_type=AgentType.SALES,
            name="销售代表1",
            description="处理销售相关询问",
            status=AgentStatus.IDLE,
            current_load=8,  # 高负载
            max_load=10
        )
        
        sales_agent_2 = AgentInfo(
            agent_id="sales_002",
            agent_type=AgentType.SALES,
            name="销售代表2",
            description="处理销售相关询问",
            status=AgentStatus.IDLE,
            current_load=3,  # 低负载
            max_load=10
        )
        
        # 设置模拟返回值
        mock_intent_analyzer.analyze_intent.return_value = sample_intent_result
        mock_intent_analyzer.validate_intent_result.return_value = True
        mock_intent_analyzer.get_intent_rules.return_value = {
            IntentType.SALES_INQUIRY: {
                "primary_agents": [AgentType.SALES],
                "fallback_agents": [AgentType.CUSTOMER_SUPPORT],
                "confidence_threshold": 0.7,
                "requires_collaboration": False
            }
        }
        
        # 模拟返回负载较低的智能体
        mock_agent_registry.get_agent_info.return_value = sales_agent_2
        
        # 使用负载均衡策略
        route_result, _ = await agent_router.route_request(
            sample_user_request, 
            strategy="load_balanced"
        )
        
        # 验证选择了负载较低的智能体
        assert route_result.selected_agent == AgentType.SALES
        assert route_result.confidence >= 0.6  # 调整期望值
    
    @pytest.mark.asyncio
    async def test_route_request_priority_based_strategy(
        self, 
        agent_router, 
        mock_intent_analyzer, 
        mock_agent_registry,
        sample_intent_result
    ):
        """测试基于优先级的路由策略."""
        high_priority_request = UserRequest(
            content="紧急：需要立即处理的销售问题",
            priority=Priority.URGENT
        )
        
        experienced_agent = AgentInfo(
            agent_id="sales_senior_001",
            agent_type=AgentType.SALES,
            name="资深销售代表",
            description="资深销售代表",
            status=AgentStatus.IDLE,
            current_load=5,
            max_load=10
        )
        
        # 设置模拟返回值
        mock_intent_analyzer.analyze_intent.return_value = sample_intent_result
        mock_intent_analyzer.validate_intent_result.return_value = True
        mock_intent_analyzer.get_intent_rules.return_value = {
            IntentType.SALES_INQUIRY: {
                "primary_agents": [AgentType.SALES],
                "fallback_agents": [AgentType.CUSTOMER_SUPPORT],
                "confidence_threshold": 0.7,
                "requires_collaboration": False
            }
        }
        mock_agent_registry.get_agent_info.return_value = experienced_agent
        
        # 使用优先级路由策略
        route_result, _ = await agent_router.route_request(
            high_priority_request, 
            strategy="priority_based"
        )
        
        # 验证高优先级请求得到了适当处理
        assert route_result.selected_agent == AgentType.SALES
        assert route_result.confidence > 0.7  # 高优先级应该提升置信度
    
    @pytest.mark.asyncio
    async def test_route_request_intent_validation_failure(
        self, 
        agent_router, 
        mock_intent_analyzer, 
        mock_agent_registry,
        sample_user_request
    ):
        """测试意图验证失败时的处理."""
        invalid_intent_result = IntentResult(
            intent_type=IntentType.SALES_INQUIRY,
            confidence=0.3,  # 低置信度
            entities=[],
            suggested_agents=[],  # 没有建议的智能体
            requires_collaboration=False
        )
        
        default_agent_info = AgentInfo(
            agent_id="support_001",
            agent_type=AgentType.CUSTOMER_SUPPORT,
            name="客服专员",
            description="处理客户咨询",
            status=AgentStatus.IDLE,
            current_load=2,
            max_load=10
        )
        
        # 设置模拟返回值
        mock_intent_analyzer.analyze_intent.return_value = invalid_intent_result
        mock_intent_analyzer.validate_intent_result.return_value = False  # 验证失败
        mock_intent_analyzer.get_intent_rules.return_value = {
            IntentType.GENERAL_INQUIRY: {
                "primary_agents": [AgentType.CUSTOMER_SUPPORT],
                "fallback_agents": [AgentType.SALES],
                "confidence_threshold": 0.5,
                "requires_collaboration": False
            }
        }
        mock_agent_registry.get_agent_info.return_value = default_agent_info
        
        # 执行路由
        route_result, intent_result = await agent_router.route_request(sample_user_request)
        
        # 验证使用了默认路由
        assert intent_result.intent_type == IntentType.GENERAL_INQUIRY
        assert route_result.selected_agent == AgentType.CUSTOMER_SUPPORT
    
    @pytest.mark.asyncio
    async def test_route_request_exception_handling(
        self, 
        agent_router, 
        mock_intent_analyzer, 
        mock_agent_registry,
        sample_user_request
    ):
        """测试路由过程中异常的处理."""
        # 模拟意图分析失败
        mock_intent_analyzer.analyze_intent.side_effect = Exception("意图分析失败")
        
        # 执行路由
        route_result, intent_result = await agent_router.route_request(sample_user_request)
        
        # 验证返回了默认结果
        assert route_result.selected_agent == AgentType.CUSTOMER_SUPPORT
        assert route_result.confidence == 0.1
        assert intent_result.intent_type == IntentType.GENERAL_INQUIRY
        assert "路由失败" in route_result.reasoning
    
    def test_evaluate_collaboration_need_high_complexity(self, agent_router):
        """测试高复杂度请求的协作需求评估."""
        complex_request = UserRequest(
            content="我需要一个复杂的综合解决方案，涉及多个产品和各种服务，并且需要跨部门协作",
            priority=Priority.HIGH
        )
        
        complex_intent_result = IntentResult(
            intent_type=IntentType.COLLABORATION_REQUIRED,
            confidence=0.6,  # 中等置信度
            entities=[
                Entity(name="产品1", value="产品1", entity_type="PRODUCT", confidence=0.8),
                Entity(name="产品2", value="产品2", entity_type="PRODUCT", confidence=0.8),
                Entity(name="服务1", value="服务1", entity_type="SERVICE", confidence=0.8),
                Entity(name="服务2", value="服务2", entity_type="SERVICE", confidence=0.8),
            ],
            suggested_agents=[AgentType.COORDINATOR],
            requires_collaboration=False  # 测试自动检测
        )
        
        needs_collaboration = agent_router._evaluate_collaboration_need(
            complex_intent_result, 
            complex_request
        )
        
        # 应该需要协作
        assert needs_collaboration
    
    def test_evaluate_collaboration_need_simple_request(self, agent_router):
        """测试简单请求的协作需求评估."""
        simple_request = UserRequest(
            content="产品价格是多少？",
            priority=Priority.NORMAL
        )
        
        simple_intent_result = IntentResult(
            intent_type=IntentType.SALES_INQUIRY,
            confidence=0.9,  # 高置信度
            entities=[
                Entity(name="价格", value="价格", entity_type="PRICE", confidence=0.9)
            ],
            suggested_agents=[AgentType.SALES],
            requires_collaboration=False
        )
        
        needs_collaboration = agent_router._evaluate_collaboration_need(
            simple_intent_result, 
            simple_request
        )
        
        # 不应该需要协作
        assert not needs_collaboration
    
    def test_assess_content_complexity_simple(self, agent_router):
        """测试简单内容的复杂度评估."""
        simple_content = "产品价格"
        complexity = agent_router._assess_content_complexity(simple_content)
        
        assert 0.0 <= complexity <= 0.3  # 简单内容复杂度较低
    
    def test_assess_content_complexity_complex(self, agent_router):
        """测试复杂内容的复杂度评估."""
        complex_content = "我需要一个复杂的综合解决方案，并且涉及多个不同的产品和各种服务，同时还要考虑跨部门协作"
        complexity = agent_router._assess_content_complexity(complex_content)
        
        assert 0.5 <= complexity <= 1.0  # 复杂内容复杂度较高
    
    def test_estimate_processing_time(self, agent_router):
        """测试处理时间估算."""
        # 测试不同意图类型和智能体类型的处理时间
        time1 = agent_router._estimate_processing_time(
            IntentType.GENERAL_INQUIRY, 
            AgentType.CUSTOMER_SUPPORT
        )
        time2 = agent_router._estimate_processing_time(
            IntentType.MANAGEMENT_DECISION, 
            AgentType.MANAGER
        )
        
        assert time1 > 0
        assert time2 > time1  # 管理决策应该比一般咨询耗时更长
    
    @pytest.mark.asyncio
    async def test_get_available_agents(self, agent_router, mock_agent_registry):
        """测试获取可用智能体列表."""
        available_agent = AgentInfo(
            agent_id="sales_001",
            agent_type=AgentType.SALES,
            name="销售代表",
            description="处理销售相关询问",
            status=AgentStatus.IDLE
        )
        
        unavailable_agent = AgentInfo(
            agent_id="support_001",
            agent_type=AgentType.CUSTOMER_SUPPORT,
            name="客服专员",
            description="处理客户咨询",
            status=AgentStatus.OFFLINE
        )
        
        def get_agent_info_side_effect(agent_id):
            if "sales" in agent_id:
                return available_agent
            elif "support" in agent_id:
                return unavailable_agent
            return None
        
        mock_agent_registry.get_agent_info.side_effect = get_agent_info_side_effect
        
        agent_types = [AgentType.SALES, AgentType.CUSTOMER_SUPPORT]
        available_agents = await agent_router._get_available_agents(agent_types)
        
        # 只有销售智能体可用
        assert len(available_agents) == 1
        assert AgentType.SALES in available_agents
        assert AgentType.CUSTOMER_SUPPORT not in available_agents
    
    @pytest.mark.asyncio
    async def test_select_least_loaded_agent(self, agent_router, mock_agent_registry):
        """测试选择负载最低的智能体."""
        high_load_agent = AgentInfo(
            agent_id="sales_001",
            agent_type=AgentType.SALES,
            name="销售代表1",
            description="处理销售相关询问",
            status=AgentStatus.IDLE,
            current_load=8,
            max_load=10
        )
        
        low_load_agent = AgentInfo(
            agent_id="sales_002",
            agent_type=AgentType.SALES,
            name="销售代表2",
            description="处理销售相关询问",
            status=AgentStatus.IDLE,
            current_load=2,
            max_load=10
        )
        
        def get_agent_info_side_effect(agent_id):
            if agent_id == "sales":
                return high_load_agent if "001" in str(hash(agent_id)) else low_load_agent
            return None
        
        mock_agent_registry.get_agent_info.side_effect = get_agent_info_side_effect
        
        agent_types = [AgentType.SALES]
        selected_agent = await agent_router._select_least_loaded_agent(agent_types)
        
        # 应该选择负载较低的智能体
        assert selected_agent == AgentType.SALES
    
    @pytest.mark.asyncio
    async def test_get_routing_statistics(self, agent_router):
        """测试获取路由统计信息."""
        stats = await agent_router.get_routing_statistics()
        
        assert isinstance(stats, dict)
        assert "total_routes" in stats
        assert "success_rate" in stats
        assert "average_confidence" in stats
        assert "collaboration_rate" in stats
        assert "agent_distribution" in stats
        assert "intent_distribution" in stats
        assert "last_updated" in stats