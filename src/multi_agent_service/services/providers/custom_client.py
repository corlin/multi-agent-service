"""Custom OpenAI-compatible API client implementation."""

import time
from typing import Any, Dict, List

from ...models.model_service import ModelRequest, ModelResponse
from ...models.enums import ModelProvider
from ..model_client import BaseModelClient, ModelClientFactory


class CustomClient(BaseModelClient):
    """自定义OpenAI兼容API客户端实现."""
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """获取自定义API认证头."""
        # 支持多种认证方式
        auth_headers = {}
        
        # Bearer token认证（最常见）
        if self.config.api_key.startswith("Bearer "):
            auth_headers["Authorization"] = self.config.api_key
        elif self.config.api_key.startswith("sk-"):
            auth_headers["Authorization"] = f"Bearer {self.config.api_key}"
        else:
            # 其他认证方式，如API Key header
            auth_headers["X-API-Key"] = self.config.api_key
        
        return auth_headers
    
    def _prepare_request_data(self, request: ModelRequest) -> Dict[str, Any]:
        """准备自定义API请求数据."""
        # 使用标准OpenAI格式，但允许更多灵活性
        data = {
            "model": request.model or self.config.model_name,
            "messages": request.messages,
            "stream": request.stream
        }
        
        # 添加可选参数
        if request.max_tokens is not None:
            data["max_tokens"] = request.max_tokens
        elif self.config.max_tokens:
            data["max_tokens"] = self.config.max_tokens
            
        if request.temperature is not None:
            data["temperature"] = request.temperature
        elif self.config.temperature:
            data["temperature"] = self.config.temperature
            
        if request.top_p is not None:
            data["top_p"] = request.top_p
            
        if request.frequency_penalty is not None:
            data["frequency_penalty"] = request.frequency_penalty
            
        if request.presence_penalty is not None:
            data["presence_penalty"] = request.presence_penalty
            
        if request.stop is not None:
            data["stop"] = request.stop
            
        if request.user is not None:
            data["user"] = request.user
        
        return data
    
    def _parse_response_data(self, response_data: Dict[str, Any], 
                           request: ModelRequest) -> ModelResponse:
        """解析自定义API响应数据."""
        # 假设返回OpenAI兼容格式，但提供更好的错误处理
        return ModelResponse(
            id=response_data.get("id", ""),
            object=response_data.get("object", "chat.completion"),
            created=response_data.get("created", int(time.time())),
            model=response_data.get("model", request.model or self.config.model_name),
            choices=response_data.get("choices", []),
            usage=response_data.get("usage", {}),
            provider=ModelProvider.CUSTOM,
            response_time=0.0  # 将在调用处设置
        )


# 注册自定义客户端
ModelClientFactory.register_client(ModelProvider.CUSTOM, CustomClient)