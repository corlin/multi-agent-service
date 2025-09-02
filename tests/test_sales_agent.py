"""Tests for the SalesAgent implementation."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock

from src.multi_agent_service.agents.sales_agent import SalesAgent
from src.multi_agent_service.models.base import UserRequest, AgentResponse
from src.multi_agent_service.models.config import AgentConfig, ModelConfig
from src.multi_agent_service.models.enums import AgentType, Priority, ModelProvider


class MockModelClient:
    """Mock model client for testing."""
    
    def __init__(self):
        self.initialized = False
        self.healthy = True
    
    async def initialize(self) -> bool:
        self.initialized = True
        return True
    
    async def health_check(self) -> bool:
        return self.healthy
    
    async def cleanup(self):
        self.initialized = False


@pytest.fixture
def model_config():
    """Create a test model configuration."""
    return ModelConfig(
        provider=ModelProvider.OPENAI,
        model_name="gpt-3.5-turbo",
        api_key="test-key",
        base_url="https://api.openai.com/v1",
        max_tokens=1000,
        temperature=0.7
    )


@pytest.fixture
def sales_agent_config(model_config):
    """Create a test sales agent configuration."""
    return AgentConfig(
        agent_id="sales-agent-001",
        agent_type=AgentType.SALES,
        name="Test Sales Agent",
        description="A test sales agent for unit testing",
        capabilities=["sales", "consultation", "pricing"],
        llm_config=model_config,
        prompt_template="You are a helpful sales agent. {input}",
        max_concurrent_tasks=3
    )


@pytest.fixture
def mock_model_client():
    """Create a mock model client."""
    return MockModelClient()


@pytest.fixture
async def sales_agent(sales_agent_config, mock_model_client):
    """Create a sales agent instance."""
    agent = SalesAgent(sales_agent_config, mock_model_client)
    await agent.initialize()
    return agent


class TestSalesAgent:
    """Test cases for SalesAgent class."""
    
    @pytest.mark.asyncio
    async def test_sales_agent_initialization(self, sales_agent_config, mock_model_client):
        """Test sales agent initialization."""
        agent = SalesAgent(sales_agent_config, mock_model_client)
        
        # Check initial state
        assert agent.agent_id == "sales-agent-001"
        assert agent.agent_type == AgentType.SALES
        assert agent.name == "Test Sales Agent"
        
        # Check sales-specific attributes
        assert len(agent.sales_keywords) > 0
        assert len(agent.product_catalog) > 0
        assert "基础版" in agent.product_catalog
        assert "专业版" in agent.product_catalog
        assert "企业版" in agent.product_catalog
        
        # Initialize agent
        result = await agent.initialize()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_can_handle_sales_requests(self, sales_agent):
        """Test sales request handling capability assessment."""
        # High confidence for sales-related requests
        sales_requests = [
            "请问你们的产品价格是多少？",
            "我想了解一下你们的服务",
            "能给我介绍一下产品功能吗？",
            "有什么优惠政策吗？",
            "I want to know the price of your product"
        ]
        
        for request_content in sales_requests:
            request = UserRequest(content=request_content)
            confidence = await sales_agent.can_handle_request(request)
            assert confidence >= 0.5, f"Low confidence for sales request: {request_content}"
    
    @pytest.mark.asyncio
    async def test_cannot_handle_non_sales_requests(self, sales_agent):
        """Test that non-sales requests get low confidence."""
        non_sales_requests = [
            "系统出现了bug，需要技术支持",
            "我需要制定公司战略规划",
            "设备故障了，需要现场维修",
            "这是一个纯技术问题"
        ]
        
        for request_content in non_sales_requests:
            request = UserRequest(content=request_content)
            confidence = await sales_agent.can_handle_request(request)
            assert confidence < 0.8, f"High confidence for non-sales request: {request_content}"
    
    @pytest.mark.asyncio
    async def test_get_capabilities(self, sales_agent):
        """Test getting sales agent capabilities."""
        capabilities = await sales_agent.get_capabilities()
        
        expected_capabilities = [
            "产品咨询", "价格报价", "方案推荐", "优惠政策",
            "购买流程", "产品对比", "需求分析", "客户关系管理"
        ]
        
        for capability in expected_capabilities:
            assert capability in capabilities
    
    @pytest.mark.asyncio
    async def test_estimate_processing_time(self, sales_agent):
        """Test processing time estimation."""
        # Price inquiry - should be quick
        price_request = UserRequest(content="请问价格多少？")
        time_estimate = await sales_agent.estimate_processing_time(price_request)
        assert time_estimate <= 10
        
        # Product introduction - medium time
        product_request = UserRequest(content="请介绍一下产品功能")
        time_estimate = await sales_agent.estimate_processing_time(product_request)
        assert 10 <= time_estimate <= 20
        
        # Solution design - longer time
        solution_request = UserRequest(content="我需要定制方案")
        time_estimate = await sales_agent.estimate_processing_time(solution_request)
        assert time_estimate >= 20
    
    @pytest.mark.asyncio
    async def test_process_price_inquiry(self, sales_agent):
        """Test processing price inquiry requests."""
        await sales_agent.start()
        
        request = UserRequest(
            content="请问你们的产品价格是多少？",
            user_id="test-user-123"
        )
        
        response = await sales_agent.process_request(request)
        
        assert isinstance(response, AgentResponse)
        assert response.agent_type == AgentType.SALES
        assert "价格" in response.response_content or "¥" in response.response_content
        assert response.confidence >= 0.8
        assert response.metadata["request_type"] == "价格咨询"
        
        # Should have next actions
        assert len(response.next_actions) > 0
        action_types = [action.action_type for action in response.next_actions]
        assert "schedule_demo" in action_types or "send_quote" in action_types
    
    @pytest.mark.asyncio
    async def test_process_product_introduction(self, sales_agent):
        """Test processing product introduction requests."""
        await sales_agent.start()
        
        request = UserRequest(
            content="能介绍一下你们的产品吗？",
            user_id="test-user-123"
        )
        
        response = await sales_agent.process_request(request)
        
        assert isinstance(response, AgentResponse)
        assert "产品" in response.response_content
        assert response.confidence >= 0.8
        assert response.metadata["request_type"] == "产品介绍"
        
        # Should mention different versions
        assert "基础版" in response.response_content or "专业版" in response.response_content
    
    @pytest.mark.asyncio
    async def test_process_solution_recommendation(self, sales_agent):
        """Test processing solution recommendation requests."""
        await sales_agent.start()
        
        request = UserRequest(
            content="我是一个小企业，需要什么方案比较合适？",
            user_id="test-user-123"
        )
        
        response = await sales_agent.process_request(request)
        
        assert isinstance(response, AgentResponse)
        assert "方案" in response.response_content
        assert response.metadata["request_type"] == "方案推荐"
        
        # Should recommend basic version for small business
        assert "基础版" in response.response_content
    
    @pytest.mark.asyncio
    async def test_process_purchase_process(self, sales_agent):
        """Test processing purchase process inquiries."""
        await sales_agent.start()
        
        request = UserRequest(
            content="购买流程是怎样的？",
            user_id="test-user-123"
        )
        
        response = await sales_agent.process_request(request)
        
        assert isinstance(response, AgentResponse)
        assert "流程" in response.response_content
        assert response.metadata["request_type"] == "购买流程"
        
        # Should mention key steps
        assert any(step in response.response_content for step in ["需求确认", "试用", "合同"])
    
    @pytest.mark.asyncio
    async def test_analyze_request_type(self, sales_agent):
        """Test request type analysis."""
        test_cases = [
            ("请问价格多少？", "价格咨询"),
            ("介绍一下产品功能", "产品介绍"),
            ("推荐一个方案", "方案推荐"),
            ("如何购买？", "购买流程"),
            ("有什么服务？", "一般咨询")
        ]
        
        for content, expected_type in test_cases:
            result = sales_agent._analyze_request_type(content)
            assert result == expected_type, f"Wrong type for '{content}': got {result}, expected {expected_type}"
    
    @pytest.mark.asyncio
    async def test_identify_sales_stage(self, sales_agent):
        """Test sales stage identification."""
        test_cases = [
            ("了解一下你们的产品", "需求识别"),
            ("产品有什么功能？", "产品介绍"),
            ("给我推荐个方案", "方案设计"),
            ("价格是多少？", "报价谈判"),
            ("怎么购买？", "合同签署"),
            ("售后服务怎么样？", "售后服务")
        ]
        
        for content, expected_stage in test_cases:
            result = sales_agent._identify_sales_stage(content)
            assert result == expected_stage, f"Wrong stage for '{content}': got {result}, expected {expected_stage}"
    
    @pytest.mark.asyncio
    async def test_needs_collaboration(self, sales_agent):
        """Test collaboration need assessment."""
        # Should need collaboration
        collaboration_cases = [
            "需要技术集成支持",
            "这是一个大额企业级项目",
            "遇到了技术问题需要解决"
        ]
        
        for content in collaboration_cases:
            result = sales_agent._needs_collaboration(content)
            assert result is True, f"Should need collaboration for: {content}"
        
        # Should not need collaboration
        no_collaboration_cases = [
            "请问价格多少？",
            "介绍一下基础功能",
            "有什么优惠吗？"
        ]
        
        for content in no_collaboration_cases:
            result = sales_agent._needs_collaboration(content)
            assert result is False, f"Should not need collaboration for: {content}"
    
    @pytest.mark.asyncio
    async def test_generate_next_actions(self, sales_agent):
        """Test next actions generation."""
        # Price inquiry should suggest demo and quote
        actions = sales_agent._generate_next_actions("价格咨询", "价格多少？")
        action_types = [action.action_type for action in actions]
        assert "schedule_demo" in action_types
        assert "send_quote" in action_types
        assert "follow_up" in action_types
        
        # Product introduction should suggest trial and brochure
        actions = sales_agent._generate_next_actions("产品介绍", "介绍产品")
        action_types = [action.action_type for action in actions]
        assert "provide_trial" in action_types
        assert "send_brochure" in action_types
    
    @pytest.mark.asyncio
    async def test_product_catalog_access(self, sales_agent):
        """Test product catalog functionality."""
        # Check catalog structure
        assert "基础版" in sales_agent.product_catalog
        assert "专业版" in sales_agent.product_catalog
        assert "企业版" in sales_agent.product_catalog
        
        # Check product information completeness
        for version, info in sales_agent.product_catalog.items():
            assert "price" in info
            assert "features" in info
            assert "description" in info
            assert isinstance(info["features"], list)
            assert len(info["features"]) > 0
    
    @pytest.mark.asyncio
    async def test_sales_keywords_coverage(self, sales_agent):
        """Test sales keywords coverage."""
        # Should have both Chinese and English keywords
        chinese_keywords = [kw for kw in sales_agent.sales_keywords if any('\u4e00' <= char <= '\u9fff' for char in kw)]
        english_keywords = [kw for kw in sales_agent.sales_keywords if kw.isascii()]
        
        assert len(chinese_keywords) > 0, "Should have Chinese keywords"
        assert len(english_keywords) > 0, "Should have English keywords"
        
        # Should cover key sales concepts
        key_concepts = ["价格", "产品", "服务", "price", "product", "service"]
        for concept in key_concepts:
            assert concept in sales_agent.sales_keywords, f"Missing key concept: {concept}"
    
    @pytest.mark.asyncio
    async def test_health_check_specific(self, sales_agent):
        """Test sales-specific health check."""
        # Normal health check should pass
        result = await sales_agent._health_check_specific()
        assert result is True
        
        # Health check should fail if product catalog is empty
        original_catalog = sales_agent.product_catalog
        sales_agent.product_catalog = {}
        
        result = await sales_agent._health_check_specific()
        assert result is False
        
        # Restore catalog
        sales_agent.product_catalog = original_catalog
    
    @pytest.mark.asyncio
    async def test_config_validation(self, sales_agent):
        """Test configuration validation."""
        # Valid config should pass
        result = await sales_agent._validate_config()
        assert result is True
        
        # Invalid agent type should fail
        original_type = sales_agent.agent_type
        sales_agent.agent_type = AgentType.MANAGER
        
        result = await sales_agent._validate_config()
        assert result is False
        
        # Restore original type
        sales_agent.agent_type = original_type


class TestSalesAgentIntegration:
    """Integration tests for SalesAgent."""
    
    @pytest.mark.asyncio
    async def test_full_sales_conversation_flow(self, sales_agent):
        """Test a complete sales conversation flow."""
        await sales_agent.start()
        
        # Step 1: Initial inquiry
        inquiry = UserRequest(content="我想了解一下你们的产品")
        response1 = await sales_agent.process_request(inquiry)
        
        assert response1.confidence >= 0.8
        assert "产品" in response1.response_content
        
        # Step 2: Price question
        price_question = UserRequest(content="价格是多少？")
        response2 = await sales_agent.process_request(price_question)
        
        assert response2.confidence >= 0.8
        assert "¥" in response2.response_content or "价格" in response2.response_content
        
        # Step 3: Purchase inquiry
        purchase_question = UserRequest(content="如何购买？")
        response3 = await sales_agent.process_request(purchase_question)
        
        assert response3.confidence >= 0.8
        assert "流程" in response3.response_content
        
        # Check metrics after conversation
        metrics = sales_agent.get_metrics()
        assert metrics["total_requests"] == 3
        assert metrics["successful_requests"] == 3
        assert metrics["success_rate"] == 100.0
    
    @pytest.mark.asyncio
    async def test_concurrent_sales_requests(self, sales_agent):
        """Test handling multiple concurrent sales requests."""
        await sales_agent.start()
        
        requests = [
            UserRequest(content="价格多少？", user_id="user1"),
            UserRequest(content="产品功能介绍", user_id="user2"),
            UserRequest(content="推荐方案", user_id="user3")
        ]
        
        # Process requests concurrently
        import asyncio
        tasks = [sales_agent.process_request(req) for req in requests]
        responses = await asyncio.gather(*tasks)
        
        # All requests should be processed successfully
        assert len(responses) == 3
        for response in responses:
            assert response.confidence >= 0.8
            assert response.agent_type == AgentType.SALES
        
        # Check different request types were handled
        request_types = [resp.metadata["request_type"] for resp in responses]
        assert "价格咨询" in request_types
        assert "产品介绍" in request_types
        assert "方案推荐" in request_types


if __name__ == "__main__":
    pytest.main([__file__])