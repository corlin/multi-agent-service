"""Pytest configuration and fixtures."""

import pytest
import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from src.multi_agent_service.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function", autouse=True)
def setup_test_environment():
    """Setup test environment variables."""
    # Set dummy API keys to avoid configuration errors
    test_env = {
        "OPENAI_API_KEY": "test-openai-key",
        "QWEN_API_KEY": "test-qwen-key", 
        "DEEPSEEK_API_KEY": "test-deepseek-key",
        "GLM_API_KEY": "test-glm-key"
    }
    
    # Store original values
    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield
    
    # Restore original values
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


@pytest.fixture(scope="function")
def mock_model_clients():
    """Mock all model clients to avoid real API calls."""
    with patch('src.multi_agent_service.services.model_client.BaseModelClient.health_check') as mock_health:
        mock_health.return_value = True
        
        with patch('src.multi_agent_service.services.model_client.BaseModelClient.chat_completion') as mock_chat:
            mock_chat.return_value = {
                "choices": [{"message": {"content": "test response"}}],
                "usage": {"total_tokens": 10}
            }
            
            # Mock ModelRouter health_check to return all clients as healthy
            with patch('src.multi_agent_service.services.model_router.ModelRouter.health_check') as mock_router_health:
                mock_router_health.return_value = True
                
                # Mock agent health checks
                with patch('src.multi_agent_service.agents.base.BaseAgent.health_check') as mock_agent_health:
                    mock_agent_health.return_value = True
                    
                    yield mock_health, mock_chat


@pytest.fixture(scope="function")
def client(setup_test_environment, mock_model_clients):
    """Create test client with mocked dependencies."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
async def async_client(setup_test_environment, mock_model_clients):
    """Create async test client with mocked dependencies."""
    from httpx import AsyncClient
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac