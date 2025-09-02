"""Tests for model service clients."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
import time

from src.multi_agent_service.models.model_service import ModelConfig, ModelRequest, ModelResponse
from src.multi_agent_service.models.enums import ModelProvider
from src.multi_agent_service.services.model_client import (
    BaseModelClient, 
    ModelClientFactory,
    ModelClientError,
    ModelAPIError,
    ModelTimeoutError
)
from src.multi_agent_service.services.providers import (
    QwenClient,
    DeepSeekClient,
    GLMClient,
    OpenAIClient,
    CustomClient
)


class TestModelClientFactory:
    """测试模型客户端工厂类."""
    
    def test_get_supported_providers(self):
        """测试获取支持的提供商列表."""
        providers = ModelClientFactory.get_supported_providers()
        
        expected_providers = [
            ModelProvider.QWEN,
            ModelProvider.DEEPSEEK,
            ModelProvider.GLM,
            ModelProvider.OPENAI,
            ModelProvider.CUSTOM
        ]
        
        for provider in expected_providers:
            assert provider in providers
    
    def test_create_qwen_client(self):
        """测试创建Qwen客户端."""
        config = ModelConfig(
            provider=ModelProvider.QWEN,
            model_name="qwen-turbo",
            api_key="test-key",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        
        client = ModelClientFactory.create_client(config)
        assert isinstance(client, QwenClient)
        assert client.provider == ModelProvider.QWEN
    
    def test_create_deepseek_client(self):
        """测试创建DeepSeek客户端."""
        config = ModelConfig(
            provider=ModelProvider.DEEPSEEK,
            model_name="deepseek-chat",
            api_key="test-key",
            base_url="https://api.deepseek.com/v1"
        )
        
        client = ModelClientFactory.create_client(config)
        assert isinstance(client, DeepSeekClient)
        assert client.provider == ModelProvider.DEEPSEEK
    
    def test_create_glm_client(self):
        """测试创建GLM客户端."""
        config = ModelConfig(
            provider=ModelProvider.GLM,
            model_name="glm-4",
            api_key="test-key",
            base_url="https://open.bigmodel.cn/api/paas/v4"
        )
        
        client = ModelClientFactory.create_client(config)
        assert isinstance(client, GLMClient)
        assert client.provider == ModelProvider.GLM
    
    def test_create_openai_client(self):
        """测试创建OpenAI客户端."""
        config = ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="gpt-3.5-turbo",
            api_key="test-key",
            base_url="https://api.openai.com/v1"
        )
        
        client = ModelClientFactory.create_client(config)
        assert isinstance(client, OpenAIClient)
        assert client.provider == ModelProvider.OPENAI
    
    def test_create_custom_client(self):
        """测试创建自定义客户端."""
        config = ModelConfig(
            provider=ModelProvider.CUSTOM,
            model_name="custom-model",
            api_key="test-key",
            base_url="https://api.custom.com/v1"
        )
        
        client = ModelClientFactory.create_client(config)
        assert isinstance(client, CustomClient)
        assert client.provider == ModelProvider.CUSTOM
    
    def test_unsupported_provider(self):
        """测试不支持的提供商."""
        # 测试Pydantic验证错误
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            ModelConfig(
                provider="unsupported",  # type: ignore
                model_name="test-model",
                api_key="test-key",
                base_url="https://api.test.com/v1"
            )


class TestQwenClient:
    """测试Qwen客户端."""
    
    @pytest.fixture
    def qwen_config(self):
        """Qwen配置fixture."""
        return ModelConfig(
            provider=ModelProvider.QWEN,
            model_name="qwen-turbo",
            api_key="test-key",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
    
    @pytest.fixture
    def qwen_client(self, qwen_config):
        """Qwen客户端fixture."""
        return QwenClient(qwen_config)
    
    def test_auth_headers(self, qwen_client):
        """测试认证头."""
        headers = qwen_client._get_auth_headers()
        assert headers["Authorization"] == "Bearer test-key"
    
    def test_prepare_request_data(self, qwen_client):
        """测试准备请求数据."""
        request = ModelRequest(
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=100,
            temperature=0.8
        )
        
        data = qwen_client._prepare_request_data(request)
        
        assert data["model"] == "qwen-turbo"
        assert data["messages"] == [{"role": "user", "content": "Hello"}]
        assert data["max_tokens"] == 100
        assert data["temperature"] == 0.8
        assert data["stream"] is False
    
    def test_parse_response_data(self, qwen_client):
        """测试解析响应数据."""
        request = ModelRequest(
            messages=[{"role": "user", "content": "Hello"}]
        )
        
        response_data = {
            "id": "test-id",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "qwen-turbo",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "Hello!"},
                    "finish_reason": "stop"
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
        }
        
        response = qwen_client._parse_response_data(response_data, request)
        
        assert response.id == "test-id"
        assert response.model == "qwen-turbo"
        assert response.provider == ModelProvider.QWEN
        assert len(response.choices) == 1
        assert response.usage["total_tokens"] == 15


class TestDeepSeekClient:
    """测试DeepSeek客户端."""
    
    @pytest.fixture
    def deepseek_config(self):
        """DeepSeek配置fixture."""
        return ModelConfig(
            provider=ModelProvider.DEEPSEEK,
            model_name="deepseek-chat",
            api_key="test-key",
            base_url="https://api.deepseek.com/v1"
        )
    
    @pytest.fixture
    def deepseek_client(self, deepseek_config):
        """DeepSeek客户端fixture."""
        return DeepSeekClient(deepseek_config)
    
    def test_auth_headers(self, deepseek_client):
        """测试认证头."""
        headers = deepseek_client._get_auth_headers()
        assert headers["Authorization"] == "Bearer test-key"
    
    def test_prepare_request_data(self, deepseek_client):
        """测试准备请求数据."""
        request = ModelRequest(
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=100,
            temperature=0.8
        )
        
        data = deepseek_client._prepare_request_data(request)
        
        assert data["model"] == "deepseek-chat"
        assert data["messages"] == [{"role": "user", "content": "Hello"}]
        assert data["max_tokens"] == 100
        assert data["temperature"] == 0.8


class TestGLMClient:
    """测试GLM客户端."""
    
    @pytest.fixture
    def glm_config(self):
        """GLM配置fixture."""
        return ModelConfig(
            provider=ModelProvider.GLM,
            model_name="glm-4",
            api_key="test-key",
            base_url="https://open.bigmodel.cn/api/paas/v4"
        )
    
    @pytest.fixture
    def glm_client(self, glm_config):
        """GLM客户端fixture."""
        return GLMClient(glm_config)
    
    def test_auth_headers(self, glm_client):
        """测试认证头."""
        headers = glm_client._get_auth_headers()
        assert headers["Authorization"] == "Bearer test-key"
    
    def test_prepare_request_data_excludes_unsupported_params(self, glm_client):
        """测试GLM不支持的参数被正确排除."""
        request = ModelRequest(
            messages=[{"role": "user", "content": "Hello"}],
            frequency_penalty=0.5,  # GLM可能不支持
            presence_penalty=0.3    # GLM可能不支持
        )
        
        data = glm_client._prepare_request_data(request)
        
        # GLM客户端应该排除这些参数
        assert "frequency_penalty" not in data
        assert "presence_penalty" not in data


class TestOpenAIClient:
    """测试OpenAI客户端."""
    
    @pytest.fixture
    def openai_config(self):
        """OpenAI配置fixture."""
        return ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="gpt-3.5-turbo",
            api_key="test-key",
            base_url="https://api.openai.com/v1"
        )
    
    @pytest.fixture
    def openai_client(self, openai_config):
        """OpenAI客户端fixture."""
        return OpenAIClient(openai_config)
    
    def test_auth_headers(self, openai_client):
        """测试认证头."""
        headers = openai_client._get_auth_headers()
        assert headers["Authorization"] == "Bearer test-key"
    
    def test_prepare_request_data_includes_all_params(self, openai_client):
        """测试OpenAI支持所有参数."""
        request = ModelRequest(
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=100,
            temperature=0.8,
            top_p=0.9,
            frequency_penalty=0.5,
            presence_penalty=0.3,
            stop=["\\n"],
            user="test-user"
        )
        
        data = openai_client._prepare_request_data(request)
        
        assert data["max_tokens"] == 100
        assert data["temperature"] == 0.8
        assert data["top_p"] == 0.9
        assert data["frequency_penalty"] == 0.5
        assert data["presence_penalty"] == 0.3
        assert data["stop"] == ["\\n"]
        assert data["user"] == "test-user"


class TestCustomClient:
    """测试自定义客户端."""
    
    @pytest.fixture
    def custom_config(self):
        """自定义配置fixture."""
        return ModelConfig(
            provider=ModelProvider.CUSTOM,
            model_name="custom-model",
            api_key="test-key",
            base_url="https://api.custom.com/v1"
        )
    
    @pytest.fixture
    def custom_client(self, custom_config):
        """自定义客户端fixture."""
        return CustomClient(custom_config)
    
    def test_auth_headers_bearer_token(self, custom_client):
        """测试Bearer token认证."""
        custom_client.config.api_key = "Bearer test-token"
        headers = custom_client._get_auth_headers()
        assert headers["Authorization"] == "Bearer test-token"
    
    def test_auth_headers_sk_prefix(self, custom_client):
        """测试sk-前缀的API key."""
        custom_client.config.api_key = "sk-test-key"
        headers = custom_client._get_auth_headers()
        assert headers["Authorization"] == "Bearer sk-test-key"
    
    def test_auth_headers_api_key(self, custom_client):
        """测试API Key header认证."""
        custom_client.config.api_key = "test-api-key"
        headers = custom_client._get_auth_headers()
        assert headers["X-API-Key"] == "test-api-key"


@pytest.mark.asyncio
class TestBaseModelClientAsync:
    """测试基础模型客户端的异步功能."""
    
    @pytest.fixture
    def mock_config(self):
        """模拟配置fixture."""
        return ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="test-model",
            api_key="test-key",
            base_url="https://api.test.com/v1"
        )
    
    @pytest.fixture
    def mock_client(self, mock_config):
        """模拟客户端fixture."""
        return OpenAIClient(mock_config)
    
    async def test_disabled_client_raises_error(self, mock_client):
        """测试禁用的客户端抛出错误."""
        mock_client.config.enabled = False
        
        request = ModelRequest(
            messages=[{"role": "user", "content": "Hello"}]
        )
        
        with pytest.raises(ModelClientError, match="is disabled"):
            await mock_client.chat_completion(request)
    
    @patch('httpx.AsyncClient.request')
    async def test_successful_chat_completion(self, mock_request, mock_client):
        """测试成功的聊天完成请求."""
        # 模拟成功响应
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "test-id",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "test-model",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "Hello!"},
                    "finish_reason": "stop"
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
        }
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        request = ModelRequest(
            messages=[{"role": "user", "content": "Hello"}]
        )
        
        response = await mock_client.chat_completion(request)
        
        assert response.id == "test-id"
        assert response.provider == ModelProvider.OPENAI
        assert mock_client.metrics.successful_requests == 1
        assert mock_client.metrics.total_requests == 1
    
    @patch('httpx.AsyncClient.request')
    async def test_timeout_error(self, mock_request, mock_client):
        """测试超时错误."""
        mock_request.side_effect = httpx.TimeoutException("Request timeout")
        
        request = ModelRequest(
            messages=[{"role": "user", "content": "Hello"}]
        )
        
        with pytest.raises(ModelTimeoutError):
            await mock_client.chat_completion(request)
        
        assert mock_client.metrics.failed_requests == 1
    
    @patch('httpx.AsyncClient.request')
    async def test_http_status_error(self, mock_request, mock_client):
        """测试HTTP状态错误."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "Bad request"}
        
        mock_request.side_effect = httpx.HTTPStatusError(
            "Bad request", request=MagicMock(), response=mock_response
        )
        
        request = ModelRequest(
            messages=[{"role": "user", "content": "Hello"}]
        )
        
        with pytest.raises(ModelAPIError) as exc_info:
            await mock_client.chat_completion(request)
        
        assert exc_info.value.status_code == 400
        assert mock_client.metrics.failed_requests == 1
    
    async def test_metrics_calculation(self, mock_client):
        """测试指标计算."""
        # 模拟一些成功和失败的请求
        mock_client.metrics.total_requests = 10
        mock_client.metrics.successful_requests = 8
        mock_client.metrics.failed_requests = 2
        
        mock_client._update_availability()
        
        assert mock_client.metrics.error_rate == 0.2
        assert mock_client.metrics.availability == 0.8
    
    async def test_close_client(self, mock_client):
        """测试关闭客户端."""
        with patch.object(mock_client._http_client, 'aclose') as mock_close:
            await mock_client.close()
            mock_close.assert_called_once()