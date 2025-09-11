"""Mock model client for testing purposes."""

import time
from typing import Dict, Any

from ..model_client import BaseModelClient
from ...models.model_service import ModelRequest, ModelResponse, ModelConfig
from ...models.enums import ModelProvider


class MockModelClient(BaseModelClient):
    """Mock model client for testing and development."""
    
    def __init__(self, config: ModelConfig):
        """Initialize mock model client."""
        super().__init__(config)
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        return {
            "Authorization": f"Bearer {self.config.api_key}"
        }
    
    def _prepare_request_data(self, request: ModelRequest) -> Dict[str, Any]:
        """Prepare request data for mock API."""
        return {
            "model": self.config.model_name,
            "messages": request.messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "stream": request.stream
        }
    
    def _parse_response_data(self, response_data: Dict[str, Any], 
                           request: ModelRequest) -> ModelResponse:
        """Parse mock response data."""
        # Return a mock response
        mock_content = "This is a mock response from the mock model client."
        
        return ModelResponse(
            id=f"mock-{int(time.time())}",
            created=int(time.time()),
            model=self.config.model_name,
            choices=[
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": mock_content
                    },
                    "finish_reason": "stop"
                }
            ],
            usage={
                "prompt_tokens": sum(len(msg.get("content", "").split()) for msg in request.messages),
                "completion_tokens": len(mock_content.split()),
                "total_tokens": sum(len(msg.get("content", "").split()) for msg in request.messages) + len(mock_content.split())
            },
            provider=self.provider,
            response_time=0.1
        )
    
    async def _make_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Mock HTTP request - return fake response."""
        # Simulate API delay
        import asyncio
        await asyncio.sleep(0.1)
        
        # Return mock response data
        return {
            "id": f"mock-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": self.config.model_name,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "This is a mock response from the mock model client."
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 12,
                "total_tokens": 22
            }
        }
    
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate a mock response for the given prompt.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional parameters
            
        Returns:
            str: Mock response text
        """
        # Simulate processing delay
        import asyncio
        await asyncio.sleep(0.1)
        
        # Return a contextual mock response based on prompt content
        if "专利" in prompt or "patent" in prompt.lower():
            return "这是一个关于专利分析的模拟AI响应。基于输入的专利数据，我们可以看到相关技术领域的发展趋势和创新方向。"
        elif "分析" in prompt or "analysis" in prompt.lower():
            return "这是一个数据分析的模拟AI响应。通过对提供的数据进行深入分析，我们发现了一些有趣的模式和趋势。"
        elif "报告" in prompt or "report" in prompt.lower():
            return "这是一个报告生成的模拟AI响应。报告内容包括数据概览、关键发现、趋势分析和建议等部分。"
        else:
            return "这是一个通用的模拟AI响应，用于演示和测试目的。实际使用时会根据具体的模型和配置生成相应的内容。"