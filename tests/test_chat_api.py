"""Tests for chat completion API endpoints."""

import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from src.multi_agent_service.main import app
from src.multi_agent_service.models.api import ChatCompletionRequest, ChatCompletionResponse
from src.multi_agent_service.models.base import UserRequest, IntentResult, AgentResponse
from src.multi_agent_service.models.enums import AgentType, IntentType, Priority


# client fixture is now provided by conftest.py


@pytest.fixture
def mock_agent_router():
    """Mock agent router."""
    mock_router = AsyncMock()
    
    # Mock route result
    mock_route_result = MagicMock()
    mock_route_result.selected_agent = AgentType.CUSTOMER_SUPPORT
    mock_route_result.confidence = 0.85
    mock_route_result.alternative_agents = [AgentType.SALES]
    mock_route_result.requires_collaboration = False
    mock_route_result.estimated_processing_time = 60
    
    # Mock intent result
    mock_intent_result = IntentResult(
        intent_type=IntentType.CUSTOMER_SUPPORT,
        confidence=0.9,
        entities=[],
        suggested_agents=[AgentType.CUSTOMER_SUPPORT],
        requires_collaboration=False,
        reasoning="客户支持相关询问"
    )
    
    mock_router.route_request.return_value = (mock_route_result, mock_intent_result)
    return mock_router


@pytest.fixture
def mock_agent():
    """Mock agent."""
    mock_agent = AsyncMock()
    
    # Mock agent response
    mock_response = AgentResponse(
        agent_id="customer_support_001",
        agent_type=AgentType.CUSTOMER_SUPPORT,
        response_content="您好！我是客服专员，很高兴为您服务。请问有什么可以帮助您的吗？",
        confidence=0.9,
        next_actions=[],
        collaboration_needed=False
    )
    
    mock_agent.process_request.return_value = mock_response
    return mock_agent


@pytest.fixture
def mock_agent_registry():
    """Mock agent registry."""
    mock_registry = AsyncMock()
    return mock_registry


class TestChatCompletionsAPI:
    """Test chat completions API endpoints."""
    
    @patch('src.multi_agent_service.api.chat.get_agent_router')
    @patch('src.multi_agent_service.agents.registry.AgentRegistry')
    def test_chat_completions_success(self, mock_registry_class, mock_get_router, client, mock_agent_router, mock_agent):
        """Test successful chat completion request."""
        # Setup mocks
        mock_get_router.return_value = mock_agent_router
        mock_registry_instance = AsyncMock()
        mock_registry_instance.get_agent.return_value = mock_agent
        mock_registry_class.return_value = mock_registry_instance
        
        # Prepare request
        request_data = {
            "messages": [
                {"role": "user", "content": "我需要帮助"}
            ],
            "model": "multi-agent-service",
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        # Make request
        response = client.post("/api/v1/chat/completions", json=request_data)
        
        # Assertions
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["object"] == "chat.completion"
        assert response_data["model"] == "multi-agent-service"
        assert len(response_data["choices"]) == 1
        
        choice = response_data["choices"][0]
        assert choice["message"]["role"] == "assistant"
        assert "客服专员" in choice["message"]["content"]
        assert choice["finish_reason"] == "stop"
        
        # Check agent info
        agent_info = response_data["agent_info"]
        assert agent_info["agent_type"] == "customer_support"
        assert agent_info["intent_type"] == "customer_support"
        assert agent_info["confidence"] == 0.9
        
        # Verify usage statistics
        usage = response_data["usage"]
        assert "prompt_tokens" in usage
        assert "completion_tokens" in usage
        assert "total_tokens" in usage
    
    def test_chat_completions_empty_messages(self, client):
        """Test chat completion with empty messages."""
        request_data = {
            "messages": [],
            "model": "multi-agent-service"
        }
        
        response = client.post("/api/v1/chat/completions", json=request_data)
        
        assert response.status_code == 400
        assert "消息列表不能为空" in response.json()["detail"]
    
    def test_chat_completions_no_user_message(self, client):
        """Test chat completion with no user message."""
        request_data = {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant"}
            ],
            "model": "multi-agent-service"
        }
        
        response = client.post("/api/v1/chat/completions", json=request_data)
        
        assert response.status_code == 400
        assert "未找到有效的用户消息内容" in response.json()["detail"]
    
    def test_chat_completions_empty_user_message(self, client):
        """Test chat completion with empty user message."""
        request_data = {
            "messages": [
                {"role": "user", "content": "   "}
            ],
            "model": "multi-agent-service"
        }
        
        response = client.post("/api/v1/chat/completions", json=request_data)
        
        assert response.status_code == 400
        assert "未找到有效的用户消息内容" in response.json()["detail"]
    
    @patch('src.multi_agent_service.api.chat.get_agent_router')
    def test_chat_completions_routing_error(self, mock_get_router, client):
        """Test chat completion with routing error."""
        # Setup mock to raise exception
        mock_router = AsyncMock()
        mock_router.route_request.side_effect = Exception("路由失败")
        mock_get_router.return_value = mock_router
        
        request_data = {
            "messages": [
                {"role": "user", "content": "测试消息"}
            ]
        }
        
        response = client.post("/api/v1/chat/completions", json=request_data)
        
        assert response.status_code == 500
        error_detail = response.json()["detail"]
        assert error_detail["error_code"] == "CHAT_COMPLETION_ERROR"
        assert "聊天完成请求处理失败" in error_detail["error_message"]
    
    @patch('src.multi_agent_service.api.chat.get_agent_router')
    @patch('src.multi_agent_service.agents.registry.AgentRegistry')
    def test_chat_completions_agent_unavailable(self, mock_registry_class, mock_get_router, client, mock_agent_router):
        """Test chat completion with unavailable agent."""
        # Setup mocks
        mock_get_router.return_value = mock_agent_router
        mock_registry_instance = AsyncMock()
        mock_registry_instance.get_agent.return_value = None  # Agent not available
        mock_registry_class.return_value = mock_registry_instance
        
        request_data = {
            "messages": [
                {"role": "user", "content": "测试消息"}
            ]
        }
        
        response = client.post("/api/v1/chat/completions", json=request_data)
        
        assert response.status_code == 503
        assert "不可用" in response.json()["detail"]
    
    @patch('src.multi_agent_service.api.chat.get_agent_router')
    @patch('src.multi_agent_service.agents.registry.AgentRegistry')
    def test_chat_completions_with_context(self, mock_registry_class, mock_get_router, client, mock_agent_router, mock_agent):
        """Test chat completion with context information."""
        # Setup mocks
        mock_get_router.return_value = mock_agent_router
        mock_registry_instance = AsyncMock()
        mock_registry_instance.get_agent.return_value = mock_agent
        mock_registry_class.return_value = mock_registry_instance
        
        request_data = {
            "messages": [
                {"role": "user", "content": "我需要帮助"}
            ],
            "user_id": "user123",
            "context": {
                "session_id": "session456",
                "previous_topic": "产品咨询"
            }
        }
        
        response = client.post("/api/v1/chat/completions", json=request_data)
        
        assert response.status_code == 200
        
        # Verify that router was called with correct user request
        mock_agent_router.route_request.assert_called_once()
        call_args = mock_agent_router.route_request.call_args[0][0]
        assert isinstance(call_args, UserRequest)
        assert call_args.user_id == "user123"
        assert call_args.context["session_id"] == "session456"
    
    def test_chat_completions_stream_not_implemented(self, client):
        """Test that streaming endpoint returns not implemented."""
        request_data = {
            "messages": [
                {"role": "user", "content": "测试消息"}
            ],
            "stream": True
        }
        
        response = client.post("/api/v1/chat/completions/stream", json=request_data)
        
        assert response.status_code == 501
        assert "流式聊天完成功能暂未实现" in response.json()["detail"]
    
    def test_list_chat_models(self, client):
        """Test listing available chat models."""
        response = client.get("/api/v1/chat/models")
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["object"] == "list"
        assert len(response_data["data"]) > 0
        
        model = response_data["data"][0]
        assert model["id"] == "multi-agent-service"
        assert model["object"] == "model"
        assert model["owned_by"] == "multi-agent-service"


class TestChatCompletionModels:
    """Test chat completion data models."""
    
    def test_chat_completion_request_model(self):
        """Test ChatCompletionRequest model validation."""
        # Valid request
        request_data = {
            "messages": [
                {"role": "user", "content": "Hello"}
            ],
            "model": "gpt-3.5-turbo",
            "max_tokens": 1000,
            "temperature": 0.7,
            "stream": False,
            "user_id": "user123",
            "context": {"key": "value"}
        }
        
        request = ChatCompletionRequest(**request_data)
        
        assert len(request.messages) == 1
        assert request.messages[0]["role"] == "user"
        assert request.model == "gpt-3.5-turbo"
        assert request.max_tokens == 1000
        assert request.temperature == 0.7
        assert request.stream is False
        assert request.user_id == "user123"
        assert request.context == {"key": "value"}
    
    def test_chat_completion_request_defaults(self):
        """Test ChatCompletionRequest default values."""
        request_data = {
            "messages": [
                {"role": "user", "content": "Hello"}
            ]
        }
        
        request = ChatCompletionRequest(**request_data)
        
        assert request.model is None
        assert request.max_tokens is None
        assert request.temperature is None
        assert request.stream is False
        assert request.user_id is None
        assert request.context == {}
    
    def test_chat_completion_response_model(self):
        """Test ChatCompletionResponse model."""
        response_data = {
            "id": "chatcmpl-123",
            "created": 1677652288,
            "model": "gpt-3.5-turbo",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello! How can I help you today?"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 9,
                "completion_tokens": 12,
                "total_tokens": 21
            }
        }
        
        response = ChatCompletionResponse(**response_data)
        
        assert response.id == "chatcmpl-123"
        assert response.object == "chat.completion"
        assert response.created == 1677652288
        assert response.model == "gpt-3.5-turbo"
        assert len(response.choices) == 1
        assert response.usage["total_tokens"] == 21
        assert response.agent_info is None


if __name__ == "__main__":
    pytest.main([__file__])