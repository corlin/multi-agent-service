"""Tests for agent routing and management API endpoints."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from src.multi_agent_service.main import app
from src.multi_agent_service.models.api import RouteRequest, RouteResponse
from src.multi_agent_service.models.base import UserRequest, IntentResult, AgentInfo
from src.multi_agent_service.models.enums import AgentType, IntentType, Priority, AgentStatus


# client fixture is now provided by conftest.py


@pytest.fixture
def mock_agent_router():
    """Mock agent router."""
    mock_router = AsyncMock()
    
    # Mock route result
    mock_route_result = MagicMock()
    mock_route_result.selected_agent = AgentType.SALES
    mock_route_result.confidence = 0.85
    mock_route_result.alternative_agents = [AgentType.CUSTOMER_SUPPORT]
    mock_route_result.requires_collaboration = False
    mock_route_result.estimated_processing_time = 90
    
    # Mock intent result
    mock_intent_result = IntentResult(
        intent_type=IntentType.SALES_INQUIRY,
        confidence=0.9,
        entities=[],
        suggested_agents=[AgentType.SALES],
        requires_collaboration=False,
        reasoning="销售咨询相关询问"
    )
    
    mock_router.route_request.return_value = (mock_route_result, mock_intent_result)
    return mock_router


@pytest.fixture
def mock_agent_registry():
    """Mock agent registry."""
    mock_registry = AsyncMock()
    
    # Mock agent info list
    mock_agents = [
        AgentInfo(
            agent_id="sales_001",
            agent_type=AgentType.SALES,
            name="销售代表智能体",
            description="专门处理销售咨询",
            status=AgentStatus.ACTIVE,
            capabilities=["产品介绍", "报价咨询"],
            current_load=2,
            max_load=10,
            last_activity=datetime.now()
        ),
        AgentInfo(
            agent_id="support_001",
            agent_type=AgentType.CUSTOMER_SUPPORT,
            name="客服专员智能体",
            description="提供客户支持服务",
            status=AgentStatus.ACTIVE,
            capabilities=["问题解决", "客户咨询"],
            current_load=0,
            max_load=10,
            last_activity=datetime.now()
        )
    ]
    
    mock_registry.list_agents.return_value = mock_agents
    mock_registry.get_agent_info.return_value = mock_agents[0]
    
    return mock_registry


class TestAgentRoutingAPI:
    """Test agent routing API endpoints."""
    
    @patch('src.multi_agent_service.api.agents.get_agent_router')
    def test_route_request_success(self, mock_get_router, client, mock_agent_router):
        """Test successful agent routing request."""
        mock_get_router.return_value = mock_agent_router
        
        request_data = {
            "content": "我想了解你们的产品价格",
            "user_id": "user123",
            "context": {"session_id": "session456"},
            "priority": "normal"
        }
        
        response = client.post("/api/v1/agents/route", json=request_data)
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["selected_agent"] == "sales"
        assert response_data["routing_confidence"] == 0.85
        assert response_data["alternative_agents"] == ["customer_support"]
        assert response_data["requires_collaboration"] is False
        assert response_data["estimated_processing_time"] == 90
        
        # Check intent result
        intent_result = response_data["intent_result"]
        assert intent_result["intent_type"] == "sales_inquiry"
        assert intent_result["confidence"] == 0.9
        assert intent_result["suggested_agents"] == ["sales"]
    
    def test_route_request_empty_content(self, client):
        """Test routing request with empty content."""
        request_data = {
            "content": "   ",
            "user_id": "user123"
        }
        
        response = client.post("/api/v1/agents/route", json=request_data)
        
        assert response.status_code == 400
        assert "请求内容不能为空" in response.json()["detail"]
    
    @patch('src.multi_agent_service.api.agents.get_agent_router')
    def test_route_request_with_preferred_agents(self, mock_get_router, client, mock_agent_router):
        """Test routing request with preferred agents."""
        mock_get_router.return_value = mock_agent_router
        
        request_data = {
            "content": "我需要技术支持",
            "preferred_agents": ["field_service", "customer_support"],
            "priority": "high"
        }
        
        response = client.post("/api/v1/agents/route", json=request_data)
        
        assert response.status_code == 200
        
        # Verify that router was called with correct parameters
        mock_agent_router.route_request.assert_called_once()
        call_args = mock_agent_router.route_request.call_args[0][0]
        assert isinstance(call_args, UserRequest)
        assert call_args.content == "我需要技术支持"
        assert call_args.priority == Priority.HIGH
    
    @patch('src.multi_agent_service.api.agents.get_agent_router')
    def test_route_request_error(self, mock_get_router, client):
        """Test routing request with error."""
        mock_router = AsyncMock()
        mock_router.route_request.side_effect = Exception("路由失败")
        mock_get_router.return_value = mock_router
        
        request_data = {
            "content": "测试消息"
        }
        
        response = client.post("/api/v1/agents/route", json=request_data)
        
        assert response.status_code == 500
        error_detail = response.json()["detail"]
        assert error_detail["error_code"] == "ROUTING_ERROR"
        assert "智能体路由失败" in error_detail["error_message"]


class TestAgentStatusAPI:
    """Test agent status API endpoints."""
    
    @patch('src.multi_agent_service.api.agents.get_agent_registry')
    def test_get_agents_status_all(self, mock_get_registry, mock_agent_registry, client):
        """Test getting all agents status."""
        mock_get_registry.return_value = mock_agent_registry
        
        # Debug: check if list_agents is properly mocked
        print(f"Mock list_agents return value: {mock_agent_registry.list_agents.return_value}")
        
        response = client.get("/api/v1/agents/status")
        
        assert response.status_code == 200
        
        response_data = response.json()
        print(f"Response data: {response_data}")  # Debug output
        assert response_data["total_count"] == 2
        assert response_data["active_count"] == 2
        assert len(response_data["agents"]) == 2
        
        # Check first agent
        agent = response_data["agents"][0]
        assert agent["agent_id"] == "sales_001"
        assert agent["agent_type"] == "sales"
        assert agent["status"] == "active"
        assert agent["load_ratio"] == 0.2  # 2/10
        assert "capabilities" in agent
    
    @patch('src.multi_agent_service.api.agents.get_agent_registry')
    def test_get_agents_status_filtered_by_type(self, mock_get_registry, client, mock_agent_registry):
        """Test getting agents status filtered by type."""
        mock_get_registry.return_value = mock_agent_registry
        
        response = client.get("/api/v1/agents/status?agent_types=sales")
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["total_count"] == 1
        assert len(response_data["agents"]) == 1
        assert response_data["agents"][0]["agent_type"] == "sales"
    
    @patch('src.multi_agent_service.api.agents.get_agent_registry')
    def test_get_agents_status_with_metrics(self, mock_get_registry, client, mock_agent_registry):
        """Test getting agents status with metrics."""
        mock_get_registry.return_value = mock_agent_registry
        
        response = client.get("/api/v1/agents/status?include_metrics=true")
        
        assert response.status_code == 200
        
        response_data = response.json()
        agent = response_data["agents"][0]
        assert "metrics" in agent
        assert "total_requests" in agent["metrics"]
        assert "success_rate" in agent["metrics"]
    
    @patch('src.multi_agent_service.api.agents.get_agent_registry')
    def test_get_agents_status_filtered_by_ids(self, mock_get_registry, client, mock_agent_registry):
        """Test getting agents status filtered by IDs."""
        mock_get_registry.return_value = mock_agent_registry
        
        response = client.get("/api/v1/agents/status?agent_ids=sales_001")
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["total_count"] == 1
        assert response_data["agents"][0]["agent_id"] == "sales_001"
    
    @patch('src.multi_agent_service.api.agents.get_agent_registry')
    def test_get_agents_status_error(self, mock_get_registry, client):
        """Test getting agents status with error."""
        mock_registry = AsyncMock()
        mock_registry.list_agents.side_effect = Exception("获取失败")
        mock_get_registry.return_value = mock_registry
        
        response = client.get("/api/v1/agents/status")
        
        assert response.status_code == 500
        error_detail = response.json()["detail"]
        assert error_detail["error_code"] == "AGENT_STATUS_ERROR"


class TestAgentTypesAPI:
    """Test agent types API endpoints."""
    
    def test_list_agent_types(self, client):
        """Test listing agent types."""
        response = client.get("/api/v1/agents/types")
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert "agent_types" in response_data
        assert "total_count" in response_data
        assert response_data["total_count"] > 0
        
        # Check that all agent types are included
        agent_types = [at["type"] for at in response_data["agent_types"]]
        expected_types = ["coordinator", "sales", "manager", "field_service", "customer_support"]
        for expected_type in expected_types:
            assert expected_type in agent_types
        
        # Check structure of agent type info
        agent_type = response_data["agent_types"][0]
        assert "type" in agent_type
        assert "name" in agent_type
        assert "description" in agent_type
    
    @patch('src.multi_agent_service.api.agents.get_agent_registry')
    def test_get_agent_capabilities_success(self, mock_get_registry, client, mock_agent_registry):
        """Test getting agent capabilities."""
        mock_get_registry.return_value = mock_agent_registry
        
        response = client.get("/api/v1/agents/capabilities/sales")
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["agent_type"] == "sales"
        assert "name" in response_data
        assert "description" in response_data
        assert "capabilities" in response_data
        assert "status" in response_data
        assert "supported_intents" in response_data
        
        # Check supported intents
        assert "sales_inquiry" in response_data["supported_intents"]
    
    def test_get_agent_capabilities_invalid_type(self, client):
        """Test getting capabilities for invalid agent type."""
        response = client.get("/api/v1/agents/capabilities/invalid_type")
        
        assert response.status_code == 400
        assert "无效的智能体类型" in response.json()["detail"]
    
    @patch('src.multi_agent_service.api.agents.get_agent_registry')
    def test_get_agent_capabilities_not_found(self, mock_get_registry, client):
        """Test getting capabilities for non-existent agent."""
        mock_registry = AsyncMock()
        mock_registry.get_agent_info.return_value = None
        mock_get_registry.return_value = mock_registry
        
        response = client.get("/api/v1/agents/capabilities/sales")
        
        assert response.status_code == 404
        assert "未找到智能体类型" in response.json()["detail"]


class TestRouteRequestModel:
    """Test RouteRequest model validation."""
    
    def test_route_request_model_valid(self):
        """Test valid RouteRequest model."""
        request_data = {
            "content": "我想了解产品信息",
            "user_id": "user123",
            "context": {"session_id": "session456"},
            "priority": "high",
            "preferred_agents": ["sales", "customer_support"]
        }
        
        request = RouteRequest(**request_data)
        
        assert request.content == "我想了解产品信息"
        assert request.user_id == "user123"
        assert request.context == {"session_id": "session456"}
        assert request.priority == Priority.HIGH
        assert request.preferred_agents == [AgentType.SALES, AgentType.CUSTOMER_SUPPORT]
    
    def test_route_request_model_defaults(self):
        """Test RouteRequest model with default values."""
        request_data = {
            "content": "测试内容"
        }
        
        request = RouteRequest(**request_data)
        
        assert request.content == "测试内容"
        assert request.user_id is None
        assert request.context == {}
        assert request.priority == Priority.NORMAL
        assert request.preferred_agents is None
    
    def test_route_response_model(self):
        """Test RouteResponse model."""
        intent_result = IntentResult(
            intent_type=IntentType.SALES_INQUIRY,
            confidence=0.9,
            entities=[],
            suggested_agents=[AgentType.SALES],
            requires_collaboration=False,
            reasoning="销售咨询"
        )
        
        response_data = {
            "intent_result": intent_result,
            "selected_agent": AgentType.SALES,
            "routing_confidence": 0.85,
            "alternative_agents": [AgentType.CUSTOMER_SUPPORT],
            "requires_collaboration": False,
            "estimated_processing_time": 60
        }
        
        response = RouteResponse(**response_data)
        
        assert response.selected_agent == AgentType.SALES
        assert response.routing_confidence == 0.85
        assert response.alternative_agents == [AgentType.CUSTOMER_SUPPORT]
        assert response.requires_collaboration is False
        assert response.estimated_processing_time == 60


if __name__ == "__main__":
    pytest.main([__file__])