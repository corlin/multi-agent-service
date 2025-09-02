"""Tests for the BaseAgent class and agent framework."""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.multi_agent_service.agents.base import BaseAgent
from src.multi_agent_service.agents.exceptions import AgentProcessingError
from src.multi_agent_service.models.base import UserRequest, AgentResponse, Conflict
from src.multi_agent_service.models.config import AgentConfig, ModelConfig
from src.multi_agent_service.models.enums import (
    AgentType, AgentStatus, Priority, ModelProvider
)
# from src.multi_agent_service.services.model_client import BaseModelClient


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


class TestAgent(BaseAgent):
    """Test implementation of BaseAgent."""
    
    def __init__(self, config: AgentConfig, model_client):
        super().__init__(config, model_client)
        self.test_capabilities = ["test_capability_1", "test_capability_2"]
        self.processing_time = 1  # Default processing time in seconds
    
    async def can_handle_request(self, request: UserRequest) -> float:
        """Test implementation - returns high confidence for test requests."""
        if "test" in request.content.lower():
            return 0.9
        return 0.3
    
    async def get_capabilities(self) -> list[str]:
        """Return test capabilities."""
        return self.test_capabilities
    
    async def estimate_processing_time(self, request: UserRequest) -> int:
        """Return estimated processing time."""
        return self.processing_time
    
    async def _process_request_specific(self, request: UserRequest) -> AgentResponse:
        """Test-specific request processing."""
        # Simulate processing time
        await asyncio.sleep(0.1)
        
        return AgentResponse(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            response_content=f"Test response for: {request.content}",
            confidence=0.9,
            collaboration_needed=False,
            metadata={"processed_by": "TestAgent"}
        )


@pytest.fixture
def model_config():
    """Create a test model configuration."""
    return ModelConfig(
        provider=ModelProvider.OPENAI,
        model_name="gpt-3.5-turbo",
        api_key="test-key",
        max_tokens=1000,
        temperature=0.7
    )


@pytest.fixture
def agent_config(model_config):
    """Create a test agent configuration."""
    return AgentConfig(
        agent_id="test-agent-001",
        agent_type=AgentType.SALES,
        name="Test Sales Agent",
        description="A test sales agent for unit testing",
        capabilities=["sales", "consultation"],
        llm_config=model_config,
        prompt_template="You are a helpful sales agent. {input}",
        max_concurrent_tasks=3
    )


@pytest.fixture
def mock_model_client():
    """Create a mock model client."""
    return MockModelClient()


@pytest.fixture
async def test_agent(agent_config, mock_model_client):
    """Create a test agent instance."""
    agent = TestAgent(agent_config, mock_model_client)
    await agent.initialize()
    return agent


@pytest.fixture
def user_request():
    """Create a test user request."""
    return UserRequest(
        content="This is a test request for sales information",
        user_id="test-user-123",
        priority=Priority.NORMAL
    )


class TestBaseAgent:
    """Test cases for BaseAgent class."""
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, agent_config, mock_model_client):
        """Test agent initialization."""
        agent = TestAgent(agent_config, mock_model_client)
        
        # Check initial state
        assert agent.agent_id == "test-agent-001"
        assert agent.agent_type == AgentType.SALES
        assert agent.name == "Test Sales Agent"
        assert agent._status == AgentStatus.OFFLINE
        assert agent._current_load == 0
        
        # Initialize agent
        result = await agent.initialize()
        assert result is True
        assert agent._status == AgentStatus.IDLE
        assert mock_model_client.initialized is True
    
    @pytest.mark.asyncio
    async def test_agent_start_stop(self, test_agent):
        """Test agent start and stop lifecycle."""
        # Start agent
        result = await test_agent.start()
        assert result is True
        assert test_agent._status == AgentStatus.IDLE
        
        # Stop agent
        result = await test_agent.stop()
        assert result is True
        assert test_agent._status == AgentStatus.OFFLINE
    
    @pytest.mark.asyncio
    async def test_agent_cleanup(self, test_agent):
        """Test agent cleanup."""
        # Add some data to shared memory
        test_agent._shared_memory["test_key"] = "test_value"
        test_agent._collaboration_partners.add("other-agent")
        
        # Cleanup
        result = await test_agent.cleanup()
        assert result is True
        assert len(test_agent._shared_memory) == 0
        assert len(test_agent._collaboration_partners) == 0
    
    @pytest.mark.asyncio
    async def test_health_check(self, test_agent):
        """Test health check functionality."""
        # Healthy agent
        result = await test_agent.health_check()
        assert result is True
        
        # Set agent to error state
        test_agent._status = AgentStatus.ERROR
        result = await test_agent.health_check()
        assert result is False
        
        # Reset to idle
        test_agent._status = AgentStatus.IDLE
        
        # Unhealthy model client
        test_agent.model_client.healthy = False
        result = await test_agent.health_check()
        assert result is False
    
    @pytest.mark.asyncio
    async def test_process_request(self, test_agent, user_request):
        """Test request processing."""
        await test_agent.start()
        
        # Process request
        response = await test_agent.process_request(user_request)
        
        # Verify response
        assert isinstance(response, AgentResponse)
        assert response.agent_id == test_agent.agent_id
        assert response.agent_type == test_agent.agent_type
        assert "Test response for:" in response.response_content
        assert response.confidence == 0.9
        
        # Check metrics
        metrics = test_agent.get_metrics()
        assert metrics["total_requests"] == 1
        assert metrics["successful_requests"] == 1
        assert metrics["failed_requests"] == 0
    
    @pytest.mark.asyncio
    async def test_process_request_overload(self, test_agent, user_request):
        """Test request processing when agent is overloaded."""
        await test_agent.start()
        
        # Set agent to maximum load
        test_agent._current_load = test_agent._max_load
        
        # Process request should handle overload
        response = await test_agent.process_request(user_request)
        
        # Should return error response
        assert "错误" in response.response_content or "error" in response.response_content.lower()
        assert response.confidence == 0.0
        
        # Check metrics
        metrics = test_agent.get_metrics()
        assert metrics["failed_requests"] == 1
    
    @pytest.mark.asyncio
    async def test_can_handle_request(self, test_agent, user_request):
        """Test request handling capability assessment."""
        # Test request with "test" keyword
        confidence = await test_agent.can_handle_request(user_request)
        assert confidence == 0.9
        
        # Request without "test" keyword
        user_request.content = "This is a sales inquiry"
        confidence = await test_agent.can_handle_request(user_request)
        assert confidence == 0.3
    
    @pytest.mark.asyncio
    async def test_get_capabilities(self, test_agent):
        """Test getting agent capabilities."""
        capabilities = await test_agent.get_capabilities()
        assert capabilities == ["test_capability_1", "test_capability_2"]
    
    @pytest.mark.asyncio
    async def test_estimate_processing_time(self, test_agent, user_request):
        """Test processing time estimation."""
        time_estimate = await test_agent.estimate_processing_time(user_request)
        assert time_estimate == 1
    
    @pytest.mark.asyncio
    async def test_get_status(self, test_agent):
        """Test getting agent status."""
        status = test_agent.get_status()
        
        assert status.agent_id == test_agent.agent_id
        assert status.agent_type == test_agent.agent_type
        assert status.name == test_agent.name
        assert status.status == test_agent._status
        assert status.current_load == test_agent._current_load
        assert status.max_load == test_agent._max_load
    
    @pytest.mark.asyncio
    async def test_get_metrics(self, test_agent):
        """Test getting agent metrics."""
        metrics = test_agent.get_metrics()
        
        expected_keys = [
            "total_requests", "successful_requests", "failed_requests",
            "success_rate", "average_response_time", "current_load",
            "max_load", "active_tasks", "collaboration_partners"
        ]
        
        for key in expected_keys:
            assert key in metrics
        
        assert metrics["success_rate"] == 0.0  # No requests processed yet
        assert metrics["current_load"] == 0
        assert metrics["max_load"] == 3
    
    @pytest.mark.asyncio
    async def test_share_information(self, test_agent):
        """Test information sharing."""
        information = {"key": "value", "data": [1, 2, 3]}
        target_agents = ["agent-1", "agent-2"]
        
        result = await test_agent.share_information(information, target_agents)
        assert result is True
        
        # Check that information is stored in shared memory
        assert len(test_agent._shared_memory) == 1
        
        # Get the stored information
        stored_info = list(test_agent._shared_memory.values())[0]
        assert stored_info["data"] == information
        assert stored_info["source"] == test_agent.agent_id
        assert stored_info["targets"] == target_agents
    
    @pytest.mark.asyncio
    async def test_receive_information(self, test_agent):
        """Test receiving information from other agents."""
        information = {"message": "Hello from another agent"}
        source_agent = "other-agent-123"
        
        result = await test_agent.receive_information(information, source_agent)
        assert result is True
        
        # Check that information is stored
        assert len(test_agent._shared_memory) == 1
        
        # Get the stored information
        stored_info = list(test_agent._shared_memory.values())[0]
        assert stored_info["data"] == information
        assert stored_info["source"] == source_agent
    
    @pytest.mark.asyncio
    async def test_collaborate(self, test_agent):
        """Test collaboration with other agents."""
        # Create mock other agents
        other_agent1 = MagicMock()
        other_agent1.agent_id = "agent-1"
        
        other_agent2 = MagicMock()
        other_agent2.agent_id = "agent-2"
        
        other_agents = [other_agent1, other_agent2]
        context = {"task": "collaborative_task"}
        
        # Test collaboration
        result = await test_agent.collaborate(other_agents, context)
        
        assert result.participating_agents == ["agent-1", "agent-2", test_agent.agent_id]
        assert result.consensus_reached is True
        assert result.resolution_method == "basic_aggregation"
        
        # Check collaboration partners are recorded
        assert "agent-1" in test_agent._collaboration_partners
        assert "agent-2" in test_agent._collaboration_partners
    
    @pytest.mark.asyncio
    async def test_handle_conflict(self, test_agent):
        """Test conflict handling."""
        conflict = Conflict(
            conflicting_agents=["agent-1", "agent-2"],
            conflict_type="resource_conflict",
            description="Agents competing for same resource",
            proposed_solutions=["solution_1", "solution_2"]
        )
        
        resolution = await test_agent.handle_conflict(conflict)
        assert resolution == "solution_1"  # Default implementation picks first solution
    
    @pytest.mark.asyncio
    async def test_concurrent_request_processing(self, test_agent):
        """Test processing multiple concurrent requests."""
        await test_agent.start()
        
        # Create multiple requests
        requests = [
            UserRequest(content=f"Test request {i}", user_id=f"user-{i}")
            for i in range(3)
        ]
        
        # Process requests concurrently
        tasks = [test_agent.process_request(req) for req in requests]
        responses = await asyncio.gather(*tasks)
        
        # Verify all requests were processed
        assert len(responses) == 3
        for i, response in enumerate(responses):
            assert f"Test request {i}" in response.response_content
        
        # Check metrics
        metrics = test_agent.get_metrics()
        assert metrics["total_requests"] == 3
        assert metrics["successful_requests"] == 3
    
    @pytest.mark.asyncio
    async def test_agent_load_management(self, test_agent, user_request):
        """Test agent load management during request processing."""
        await test_agent.start()
        
        # Start processing a request (but don't await it yet)
        task = asyncio.create_task(test_agent.process_request(user_request))
        
        # Give it a moment to start
        await asyncio.sleep(0.05)
        
        # Check that load increased
        assert test_agent._current_load == 1
        assert test_agent._status == AgentStatus.BUSY
        
        # Wait for completion
        await task
        
        # Check that load decreased
        assert test_agent._current_load == 0
        assert test_agent._status == AgentStatus.IDLE


class TestAgentErrorHandling:
    """Test error handling in agents."""
    
    @pytest.mark.asyncio
    async def test_initialization_failure(self, agent_config):
        """Test handling of initialization failures."""
        # Create a mock client that fails to initialize
        mock_client = MockModelClient()
        mock_client.initialize = AsyncMock(return_value=False)
        
        agent = TestAgent(agent_config, mock_client)
        result = await agent.initialize()
        
        assert result is False
        assert agent._status == AgentStatus.ERROR
    
    @pytest.mark.asyncio
    async def test_processing_error_handling(self, test_agent):
        """Test error handling during request processing."""
        await test_agent.start()
        
        # Mock the specific processing method to raise an exception
        async def failing_process(request):
            raise Exception("Processing failed")
        
        test_agent._process_request_specific = failing_process
        
        # Process request
        request = UserRequest(content="Test request")
        response = await test_agent.process_request(request)
        
        # Should return error response
        assert "错误" in response.response_content or "error" in response.response_content.lower()
        assert response.confidence == 0.0
        
        # Check metrics
        metrics = test_agent.get_metrics()
        assert metrics["failed_requests"] == 1
    
    @pytest.mark.asyncio
    async def test_health_check_error_recovery(self, test_agent):
        """Test error recovery through health checks."""
        await test_agent.start()
        
        # Set agent to error state
        test_agent._status = AgentStatus.ERROR
        
        # Health check should detect error
        assert await test_agent.health_check() is False
        
        # Reset to healthy state
        test_agent._status = AgentStatus.IDLE
        
        # Health check should pass
        assert await test_agent.health_check() is True


if __name__ == "__main__":
    pytest.main([__file__])