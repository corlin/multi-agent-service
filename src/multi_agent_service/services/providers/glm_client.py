"""智谱AI (GLM) API client implementation."""

import time
from typing import Any, Dict, List

from ...models.model_service import ModelRequest, ModelResponse
from ...models.enums import ModelProvider
from ..model_client import BaseModelClient, ModelClientFactory


class GLMClient(BaseModelClient):
    """智谱AI (GLM) API客户端实现."""
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """获取GLM API认证头."""
        return {
            "Authorization": f"Bearer {self.config.api_key}"
        }
    
    def _prepare_request_data(self, request: ModelRequest) -> Dict[str, Any]:
        """准备GLM API请求数据."""
        # GLM API使用OpenAI兼容格式，但有一些特殊参数
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
            
        # GLM特有参数处理
        if request.stop is not None:
            data["stop"] = request.stop
            
        if request.user is not None:
            data["user"] = request.user
        
        # GLM可能不支持frequency_penalty和presence_penalty，跳过这些参数
        
        return data
    
    def _parse_response_data(self, response_data: Dict[str, Any], 
                           request: ModelRequest) -> ModelResponse:
        """解析GLM API响应数据."""
        # GLM API返回OpenAI兼容格式
        return ModelResponse(
            id=response_data.get("id", ""),
            object=response_data.get("object", "chat.completion"),
            created=response_data.get("created", int(time.time())),
            model=response_data.get("model", request.model or self.config.model_name),
            choices=response_data.get("choices", []),
            usage=response_data.get("usage", {}),
            provider=ModelProvider.GLM,
            response_time=0.01  # 将在调用处设置
        )


# 注册GLM客户端
ModelClientFactory.register_client(ModelProvider.GLM, GLMClient)