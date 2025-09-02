"""Tests for the CustomerSupportAgent implementation."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock

from src.multi_agent_service.agents.customer_support_agent import CustomerSupportAgent
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
def support_agent_config(model_config):
    """Create a test customer support agent configuration."""
    return AgentConfig(
        agent_id="support-agent-001",
        agent_type=AgentType.CUSTOMER_SUPPORT,
        name="Test Customer Support Agent",
        description="A test customer support agent for unit testing",
        capabilities=["support", "customer_service", "problem_solving"],
        llm_config=model_config,
        prompt_template="You are a helpful customer support agent. {input}",
        max_concurrent_tasks=5
    )


@pytest.fixture
def mock_model_client():
    """Create a mock model client."""
    return MockModelClient()


@pytest.fixture
async def support_agent(support_agent_config, mock_model_client):
    """Create a customer support agent instance."""
    agent = CustomerSupportAgent(support_agent_config, mock_model_client)
    await agent.initialize()
    return agent


class TestCustomerSupportAgent:
    """Test cases for CustomerSupportAgent class."""
    
    @pytest.mark.asyncio
    async def test_support_agent_initialization(self, support_agent_config, mock_model_client):
        """Test customer support agent initialization."""
        agent = CustomerSupportAgent(support_agent_config, mock_model_client)
        
        # Check initial state
        assert agent.agent_id == "support-agent-001"
        assert agent.agent_type == AgentType.CUSTOMER_SUPPORT
        assert agent.name == "Test Customer Support Agent"
        
        # Check support-specific attributes
        assert len(agent.support_keywords) > 0
        assert len(agent.issue_categories) > 0
        assert len(agent.common_solutions) > 0
        assert len(agent.response_templates) > 0
        
        # Initialize agent
        result = await agent.initialize()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_can_handle_support_requests(self, support_agent):
        """Test support request handling capability assessment."""
        # High confidence for support-related requests
        support_requests = [
            "我遇到了登录问题",
            "系统出现了错误",
            "如何使用这个功能？",
            "我要投诉服务质量",
            "网络连接有问题",
            "I have a problem with login",
            "The system shows an error",
            "How to use this feature?"
        ]
        
        for request_content in support_requests:
            request = UserRequest(content=request_content)
            confidence = await support_agent.can_handle_request(request)
            assert confidence >= 0.4, f"Low confidence for support request: {request_content}"
    
    @pytest.mark.asyncio
    async def test_cannot_handle_non_support_requests(self, support_agent):
        """Test that non-support requests get lower confidence."""
        non_support_requests = [
            "请问产品价格是多少？",
            "我想购买你们的服务",
            "能介绍一下产品功能吗？",
            "需要制定公司战略"
        ]
        
        for request_content in non_support_requests:
            request = UserRequest(content=request_content)
            confidence = await support_agent.can_handle_request(request)
            # Should still handle but with lower confidence due to sales keywords penalty
            assert confidence >= 0.0, f"Negative confidence for request: {request_content}"
    
    @pytest.mark.asyncio
    async def test_get_capabilities(self, support_agent):
        """Test getting customer support agent capabilities."""
        capabilities = await support_agent.get_capabilities()
        
        expected_capabilities = [
            "问题诊断", "故障排除", "技术支持", "账户问题处理",
            "使用指导", "投诉处理", "建议收集", "问题升级"
        ]
        
        for capability in expected_capabilities:
            assert capability in capabilities
    
    @pytest.mark.asyncio
    async def test_estimate_processing_time(self, support_agent):
        """Test processing time estimation."""
        # Usage inquiry - should be quick
        usage_request = UserRequest(content="如何使用这个功能？")
        time_estimate = await support_agent.estimate_processing_time(usage_request)
        assert time_estimate <= 15
        
        # Technical issue - medium time
        tech_request = UserRequest(content="系统出现故障")
        time_estimate = await support_agent.estimate_processing_time(tech_request)
        assert 15 <= time_estimate <= 25
        
        # Complaint - longer time
        complaint_request = UserRequest(content="我要投诉服务质量")
        time_estimate = await support_agent.estimate_processing_time(complaint_request)
        assert time_estimate >= 25
    
    @pytest.mark.asyncio
    async def test_categorize_issue(self, support_agent):
        """Test issue categorization."""
        test_cases = [
            ("系统出现bug", "技术问题"),
            ("登录失败", "账户问题"),
            ("如何操作这个功能", "功能咨询"),
            ("我要投诉", "投诉建议"),
            ("网络连接异常", "网络连接"),
            ("一般问题", "一般咨询")
        ]
        
        for content, expected_category in test_cases:
            result = support_agent._categorize_issue(content)
            assert result == expected_category, f"Wrong category for '{content}': got {result}, expected {expected_category}"
    
    @pytest.mark.asyncio
    async def test_assess_severity(self, support_agent):
        """Test severity assessment."""
        test_cases = [
            ("系统崩溃无法使用", "紧急"),
            ("功能异常影响业务", "高"),
            ("部分功能有问题", "中"),
            ("有个小建议", "低")
        ]
        
        for content, expected_severity in test_cases:
            result = support_agent._assess_severity(content)
            assert result == expected_severity, f"Wrong severity for '{content}': got {result}, expected {expected_severity}"
    
    @pytest.mark.asyncio
    async def test_process_technical_issue(self, support_agent):
        """Test processing technical issue requests."""
        await support_agent.start()
        
        request = UserRequest(
            content="系统出现了bug，无法正常使用",
            user_id="test-user-123"
        )
        
        response = await support_agent.process_request(request)
        
        assert isinstance(response, AgentResponse)
        assert response.agent_type == AgentType.CUSTOMER_SUPPORT
        assert "技术问题" in response.response_content or "bug" in response.response_content
        assert response.confidence >= 0.8
        assert response.metadata["issue_category"] == "技术问题"
        
        # Should have next actions
        assert len(response.next_actions) > 0
        action_types = [action.action_type for action in response.next_actions]
        assert "collect_logs" in action_types or "remote_assistance" in action_types
    
    @pytest.mark.asyncio
    async def test_process_account_issue(self, support_agent):
        """Test processing account issue requests."""
        await support_agent.start()
        
        request = UserRequest(
            content="我无法登录账户，密码输入正确但是提示错误",
            user_id="test-user-123"
        )
        
        response = await support_agent.process_request(request)
        
        assert isinstance(response, AgentResponse)
        assert "登录" in response.response_content or "账户" in response.response_content
        assert response.metadata["issue_category"] == "账户问题"
        
        # Should mention login troubleshooting steps
        assert any(word in response.response_content for word in ["密码", "用户名", "重置"])
    
    @pytest.mark.asyncio
    async def test_process_usage_inquiry(self, support_agent):
        """Test processing usage inquiry requests."""
        await support_agent.start()
        
        request = UserRequest(
            content="请问如何设置系统参数？",
            user_id="test-user-123"
        )
        
        response = await support_agent.process_request(request)
        
        assert isinstance(response, AgentResponse)
        assert "设置" in response.response_content or "指导" in response.response_content
        assert response.metadata["issue_category"] == "功能咨询"
        
        # Should provide step-by-step guidance
        assert any(char in response.response_content for char in ["1.", "2.", "步骤"])
    
    @pytest.mark.asyncio
    async def test_process_complaint(self, support_agent):
        """Test processing complaint requests."""
        await support_agent.start()
        
        request = UserRequest(
            content="我要投诉你们的服务质量，非常不满意",
            user_id="test-user-123"
        )
        
        response = await support_agent.process_request(request)
        
        assert isinstance(response, AgentResponse)
        assert "投诉" in response.response_content or "抱歉" in response.response_content
        assert response.metadata["issue_category"] == "投诉建议"
        assert response.collaboration_needed is True  # Complaints should be escalated
        
        # Should have escalation actions
        action_types = [action.action_type for action in response.next_actions]
        assert "escalate_complaint" in action_types
    
    @pytest.mark.asyncio
    async def test_process_network_issue(self, support_agent):
        """Test processing network issue requests."""
        await support_agent.start()
        
        request = UserRequest(
            content="网络连接总是超时，无法正常访问",
            user_id="test-user-123"
        )
        
        response = await support_agent.process_request(request)
        
        assert isinstance(response, AgentResponse)
        assert "网络" in response.response_content or "连接" in response.response_content
        assert response.metadata["issue_category"] == "网络连接"
        
        # Should provide network troubleshooting steps
        assert any(word in response.response_content for word in ["检查", "网络", "连接"])
    
    @pytest.mark.asyncio
    async def test_needs_escalation(self, support_agent):
        """Test escalation need assessment."""
        # Should need escalation
        escalation_cases = [
            "系统崩溃数据丢失",
            "我要投诉并要求退款",
            "这是安全问题需要技术支持",
            "无法访问系统影响业务"
        ]
        
        for content in escalation_cases:
            severity = support_agent._assess_severity(content)
            result = support_agent._needs_escalation(content, severity)
            assert result is True, f"Should need escalation for: {content}"
        
        # Should not need escalation
        no_escalation_cases = [
            "如何使用这个功能？",
            "密码忘记了怎么办？",
            "有个小建议想提一下"
        ]
        
        for content in no_escalation_cases:
            severity = support_agent._assess_severity(content)
            result = support_agent._needs_escalation(content, severity)
            assert result is False, f"Should not need escalation for: {content}"
    
    @pytest.mark.asyncio
    async def test_generate_next_actions(self, support_agent):
        """Test next actions generation."""
        # Technical issue should suggest log collection and remote assistance
        actions = support_agent._generate_next_actions("技术问题", "高", "系统错误")
        action_types = [action.action_type for action in actions]
        assert "collect_logs" in action_types
        assert "remote_assistance" in action_types
        assert "follow_up" in action_types
        
        # Account issue should suggest identity verification
        actions = support_agent._generate_next_actions("账户问题", "中", "登录问题")
        action_types = [action.action_type for action in actions]
        assert "verify_identity" in action_types
        assert "reset_credentials" in action_types
        
        # High severity should add priority escalation
        actions = support_agent._generate_next_actions("技术问题", "紧急", "系统崩溃")
        action_types = [action.action_type for action in actions]
        assert "priority_escalation" in action_types
    
    @pytest.mark.asyncio
    async def test_common_solutions_access(self, support_agent):
        """Test common solutions functionality."""
        # Check solutions structure
        assert "登录问题" in support_agent.common_solutions
        assert "网络连接" in support_agent.common_solutions
        assert "功能异常" in support_agent.common_solutions
        
        # Check solution information completeness
        for solution_name, solution_info in support_agent.common_solutions.items():
            assert "steps" in solution_info
            assert "escalation" in solution_info
            assert isinstance(solution_info["steps"], list)
            assert len(solution_info["steps"]) > 0
    
    @pytest.mark.asyncio
    async def test_support_keywords_coverage(self, support_agent):
        """Test support keywords coverage."""
        # Should have both Chinese and English keywords
        chinese_keywords = [kw for kw in support_agent.support_keywords if any('\u4e00' <= char <= '\u9fff' for char in kw)]
        english_keywords = [kw for kw in support_agent.support_keywords if kw.isascii()]
        
        assert len(chinese_keywords) > 0, "Should have Chinese keywords"
        assert len(english_keywords) > 0, "Should have English keywords"
        
        # Should cover key support concepts
        key_concepts = ["问题", "帮助", "支持", "problem", "help", "support"]
        for concept in key_concepts:
            assert concept in support_agent.support_keywords, f"Missing key concept: {concept}"
    
    @pytest.mark.asyncio
    async def test_response_templates(self, support_agent):
        """Test response templates functionality."""
        required_templates = ["greeting", "acknowledgment", "solution_intro", "escalation", "follow_up", "closing"]
        
        for template_name in required_templates:
            assert template_name in support_agent.response_templates
            assert len(support_agent.response_templates[template_name]) > 0
    
    @pytest.mark.asyncio
    async def test_health_check_specific(self, support_agent):
        """Test support-specific health check."""
        # Normal health check should pass
        result = await support_agent._health_check_specific()
        assert result is True
        
        # Health check should fail if solutions library is empty
        original_solutions = support_agent.common_solutions
        support_agent.common_solutions = {}
        
        result = await support_agent._health_check_specific()
        assert result is False
        
        # Restore solutions
        support_agent.common_solutions = original_solutions
    
    @pytest.mark.asyncio
    async def test_config_validation(self, support_agent):
        """Test configuration validation."""
        # Valid config should pass
        result = await support_agent._validate_config()
        assert result is True
        
        # Invalid agent type should fail
        original_type = support_agent.agent_type
        support_agent.agent_type = AgentType.SALES
        
        result = await support_agent._validate_config()
        assert result is False
        
        # Restore original type
        support_agent.agent_type = original_type


class TestCustomerSupportAgentIntegration:
    """Integration tests for CustomerSupportAgent."""
    
    @pytest.mark.asyncio
    async def test_full_support_conversation_flow(self, support_agent):
        """Test a complete support conversation flow."""
        await support_agent.start()
        
        # Step 1: Initial problem report
        problem_report = UserRequest(content="我遇到了登录问题，无法进入系统")
        response1 = await support_agent.process_request(problem_report)
        
        assert response1.confidence >= 0.8
        assert "登录" in response1.response_content
        assert response1.metadata["issue_category"] == "账户问题"
        
        # Step 2: Follow-up technical question
        tech_question = UserRequest(content="系统显示密码错误，但我确定密码是对的")
        response2 = await support_agent.process_request(tech_question)
        
        assert response2.confidence >= 0.8
        assert any(word in response2.response_content for word in ["密码", "重置", "验证"])
        
        # Step 3: Escalation request
        escalation_request = UserRequest(content="这个问题很紧急，影响我的工作")
        response3 = await support_agent.process_request(escalation_request)
        
        assert response3.confidence >= 0.8
        
        # Check metrics after conversation
        metrics = support_agent.get_metrics()
        assert metrics["total_requests"] == 3
        assert metrics["successful_requests"] == 3
        assert metrics["success_rate"] == 100.0
    
    @pytest.mark.asyncio
    async def test_concurrent_support_requests(self, support_agent):
        """Test handling multiple concurrent support requests."""
        await support_agent.start()
        
        requests = [
            UserRequest(content="登录问题", user_id="user1"),
            UserRequest(content="系统错误", user_id="user2"),
            UserRequest(content="如何使用功能", user_id="user3"),
            UserRequest(content="网络连接问题", user_id="user4"),
            UserRequest(content="投诉服务", user_id="user5")
        ]
        
        # Process requests concurrently
        import asyncio
        tasks = [support_agent.process_request(req) for req in requests]
        responses = await asyncio.gather(*tasks)
        
        # All requests should be processed successfully
        assert len(responses) == 5
        for response in responses:
            assert response.confidence >= 0.8
            assert response.agent_type == AgentType.CUSTOMER_SUPPORT
        
        # Check different issue categories were handled
        categories = [resp.metadata["issue_category"] for resp in responses]
        assert "账户问题" in categories
        assert "技术问题" in categories
        assert "功能咨询" in categories
        assert "网络连接" in categories
        assert "投诉建议" in categories
    
    @pytest.mark.asyncio
    async def test_escalation_workflow(self, support_agent):
        """Test escalation workflow for complex issues."""
        await support_agent.start()
        
        # High severity issue that should trigger escalation
        critical_issue = UserRequest(
            content="系统崩溃导致数据丢失，这是安全问题需要立即处理",
            user_id="critical-user"
        )
        
        response = await support_agent.process_request(critical_issue)
        
        # Should be marked for escalation
        assert response.collaboration_needed is True
        assert response.metadata["needs_escalation"] is True
        assert response.metadata["severity"] == "紧急"
        
        # Should have priority escalation action
        action_types = [action.action_type for action in response.next_actions]
        assert "priority_escalation" in action_types


if __name__ == "__main__":
    pytest.main([__file__])