"""OpenAI API client implementation."""

import time
from typing import Any, Dict, List

from ...models.model_service import ModelRequest, ModelResponse
from ...models.enums import ModelProvider
from ..model_client import BaseModelClient, ModelClientFactory


class OpenAIClient(BaseModelClient):
    """OpenAI API客户端实现."""
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """获取OpenAI API认证头."""
        return {
            "Authorization": f"Bearer {self.config.api_key}"
        }
    
    def _prepare_request_data(self, request: ModelRequest) -> Dict[str, Any]:
        """准备OpenAI API请求数据."""
        # 标准OpenAI API格式
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
        """解析OpenAI API响应数据."""
        # 标准OpenAI API响应格式
        return ModelResponse(
            id=response_data.get("id", ""),
            object=response_data.get("object", "chat.completion"),
            created=response_data.get("created", int(time.time())),
            model=response_data.get("model", request.model or self.config.model_name),
            choices=response_data.get("choices", []),
            usage=response_data.get("usage", {}),
            provider=ModelProvider.OPENAI,
            response_time=0.01  # 将在调用处设置
        )


# 注册OpenAI客户端
ModelClientFactory.register_client(ModelProvider.OPENAI, OpenAIClient)