"""OpenAI compatible model client base interface."""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, AsyncGenerator
import logging

import httpx
from pydantic import ValidationError

from ..models.model_service import (
    ModelRequest, 
    ModelResponse, 
    ModelConfig, 
    ModelError, 
    ModelMetrics
)
from ..models.enums import ModelProvider


logger = logging.getLogger(__name__)


class ModelClientError(Exception):
    """模型客户端异常基类."""
    
    def __init__(self, message: str, error_code: str = "MODEL_CLIENT_ERROR", 
                 provider: Optional[ModelProvider] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.provider = provider


class ModelAPIError(ModelClientError):
    """模型API调用异常."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, 
                 response_data: Optional[Dict[str, Any]] = None,
                 provider: Optional[ModelProvider] = None):
        super().__init__(message, "MODEL_API_ERROR", provider)
        self.status_code = status_code
        self.response_data = response_data


class ModelTimeoutError(ModelClientError):
    """模型API超时异常."""
    
    def __init__(self, message: str, timeout: float, 
                 provider: Optional[ModelProvider] = None):
        super().__init__(message, "MODEL_TIMEOUT_ERROR", provider)
        self.timeout = timeout


class BaseModelClient(ABC):
    """OpenAI兼容的模型客户端抽象基类."""
    
    def __init__(self, config: ModelConfig):
        """初始化模型客户端.
        
        Args:
            config: 模型配置
        """
        self.config = config
        self.provider = config.provider
        self.metrics = ModelMetrics(
            provider=config.provider,
            model_name=config.model_name
        )
        
        # 创建HTTP客户端
        self._http_client = httpx.AsyncClient(
            base_url=config.base_url,
            timeout=httpx.Timeout(config.timeout),
            headers=self._get_default_headers()
        )
        
        # 初始化健康检查状态
        self._last_health_check_failed = False
        self._health_check_cooldown_until = None
        
        # 如果API密钥为空或无效，预设冷却期
        if not config.api_key or config.api_key.strip() == "":
            import time
            self._last_health_check_failed = True
            self._health_check_cooldown_until = time.time() + 300  # 5分钟冷却期
            logger.info(f"No API key configured for {self.provider}, setting initial cooldown")
        
        logger.info(f"Initialized {self.provider} model client for {config.model_name}")
    
    async def initialize(self) -> bool:
        """Initialize the model client.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Basic initialization - can be overridden by subclasses
            logger.info(f"Initializing {self.provider} model client")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize {self.provider} model client: {str(e)}")
            return False
    
    def _get_default_headers(self) -> Dict[str, str]:
        """获取默认HTTP头."""
        return {
            "Content-Type": "application/json",
            "User-Agent": "multi-agent-service/1.0.0"
        }
    
    @abstractmethod
    def _get_auth_headers(self) -> Dict[str, str]:
        """获取认证头，由子类实现."""
        pass
    
    @abstractmethod
    def _prepare_request_data(self, request: ModelRequest) -> Dict[str, Any]:
        """准备请求数据，由子类实现以适配不同提供商的API格式."""
        pass
    
    @abstractmethod
    def _parse_response_data(self, response_data: Dict[str, Any], 
                           request: ModelRequest) -> ModelResponse:
        """解析响应数据，由子类实现以适配不同提供商的响应格式."""
        pass
    
    async def chat_completion(self, request: ModelRequest) -> ModelResponse:
        """执行聊天完成请求.
        
        Args:
            request: 模型请求
            
        Returns:
            ModelResponse: 模型响应
            
        Raises:
            ModelClientError: 客户端错误
            ModelAPIError: API调用错误
            ModelTimeoutError: 超时错误
        """
        if not self.config.enabled:
            raise ModelClientError(
                f"Model provider {self.provider} is disabled",
                "MODEL_DISABLED",
                self.provider
            )
        
        start_time = time.time()
        
        try:
            # 更新指标
            self.metrics.total_requests += 1
            
            # 准备请求数据
            request_data = self._prepare_request_data(request)
            
            # 添加认证头
            headers = {**self._get_default_headers(), **self._get_auth_headers()}
            
            # 发送请求
            response = await self._make_request(
                method="POST",
                url="/chat/completions",
                json=request_data,
                headers=headers,
                timeout=request.timeout or self.config.timeout
            )
            
            # 解析响应
            model_response = self._parse_response_data(response, request)
            
            # 更新成功指标
            response_time = time.time() - start_time
            self._update_success_metrics(response_time)
            
            logger.debug(f"Chat completion successful for {self.provider}, "
                        f"response_time: {response_time:.2f}s")
            
            return model_response
            
        except (httpx.TimeoutException, asyncio.TimeoutError) as e:
            self._update_error_metrics()
            raise ModelTimeoutError(
                f"Request timeout for {self.provider}: {str(e)}",
                request.timeout or self.config.timeout,
                self.provider
            )
        except httpx.HTTPStatusError as e:
            self._update_error_metrics()
            error_data = None
            try:
                error_data = e.response.json()
            except Exception:
                pass
            
            raise ModelAPIError(
                f"HTTP error {e.response.status_code} for {self.provider}: {str(e)}",
                e.response.status_code,
                error_data,
                self.provider
            )
        except Exception as e:
            self._update_error_metrics()
            logger.error(f"Unexpected error in chat completion for {self.provider}: {str(e)}")
            raise ModelClientError(
                f"Unexpected error for {self.provider}: {str(e)}",
                "UNEXPECTED_ERROR",
                self.provider
            )
    
    async def chat_completion_stream(self, request: ModelRequest) -> AsyncGenerator[str, None]:
        """执行流式聊天完成请求.
        
        Args:
            request: 模型请求
            
        Yields:
            str: 流式响应数据块
            
        Raises:
            ModelClientError: 客户端错误
        """
        if not self.config.enabled:
            raise ModelClientError(
                f"Model provider {self.provider} is disabled",
                "MODEL_DISABLED",
                self.provider
            )
        
        # 设置流式请求
        stream_request = request.model_copy()
        stream_request.stream = True
        
        try:
            # 准备请求数据
            request_data = self._prepare_request_data(stream_request)
            
            # 添加认证头
            headers = {**self._get_default_headers(), **self._get_auth_headers()}
            
            # 发送流式请求
            async with self._http_client.stream(
                method="POST",
                url="/chat/completions",
                json=request_data,
                headers=headers,
                timeout=request.timeout or self.config.timeout
            ) as response:
                response.raise_for_status()
                
                async for chunk in response.aiter_text():
                    if chunk.strip():
                        yield chunk
                        
        except Exception as e:
            logger.error(f"Stream completion error for {self.provider}: {str(e)}")
            raise ModelClientError(
                f"Stream completion error for {self.provider}: {str(e)}",
                "STREAM_ERROR",
                self.provider
            )
    
    async def _make_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """发送HTTP请求.
        
        Args:
            method: HTTP方法
            url: 请求URL
            **kwargs: 其他请求参数
            
        Returns:
            Dict[str, Any]: 响应数据
            
        Raises:
            httpx.HTTPStatusError: HTTP状态错误
            httpx.TimeoutException: 超时错误
        """
        response = await self._http_client.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
    
    def _update_success_metrics(self, response_time: float) -> None:
        """更新成功请求指标."""
        self.metrics.successful_requests += 1
        self.metrics.last_request_time = time.time()
        
        # 更新平均响应时间
        total_successful = self.metrics.successful_requests
        current_avg = self.metrics.average_response_time
        self.metrics.average_response_time = (
            (current_avg * (total_successful - 1) + response_time) / total_successful
        )
        
        # 更新错误率和可用性
        self._update_availability()
    
    def _update_error_metrics(self) -> None:
        """更新错误请求指标."""
        self.metrics.failed_requests += 1
        self._update_availability()
    
    def _update_availability(self) -> None:
        """更新可用性指标."""
        total_requests = self.metrics.total_requests
        if total_requests > 0:
            self.metrics.error_rate = self.metrics.failed_requests / total_requests
            self.metrics.availability = self.metrics.successful_requests / total_requests
    
    async def health_check(self) -> bool:
        """健康检查.
        
        Returns:
            bool: 是否健康
        """
        try:
            # 检查是否在冷却期内（避免频繁检查失败的服务）
            if hasattr(self, '_last_health_check_failed') and self._last_health_check_failed:
                if hasattr(self, '_health_check_cooldown_until'):
                    import time
                    if time.time() < self._health_check_cooldown_until:
                        logger.debug(f"Health check for {self.provider} in cooldown period")
                        return False
            
            # 发送简单的健康检查请求，使用更短的超时
            test_request = ModelRequest(
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1,
                temperature=0.01,
                timeout=60  # 使用较短的超时时间进行健康检查
            )
            
            await self.chat_completion(test_request)
            
            # 重置失败状态
            self._last_health_check_failed = False
            if hasattr(self, '_health_check_cooldown_until'):
                delattr(self, '_health_check_cooldown_until')
            
            return True
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # 对于认证错误，设置较长的冷却期
            if "401" in error_msg or "unauthorized" in error_msg or "authentication" in error_msg:
                import time
                self._last_health_check_failed = True
                self._health_check_cooldown_until = time.time() + 300  # 5分钟冷却期
                logger.warning(f"Authentication failed for {self.provider}, setting 5min cooldown: {str(e)}")
            
            # 对于其他错误，设置较短的冷却期
            elif "timeout" in error_msg or "connection" in error_msg:
                import time
                self._last_health_check_failed = True
                self._health_check_cooldown_until = time.time() + 60  # 1分钟冷却期
                logger.warning(f"Connection/timeout error for {self.provider}, setting 1min cooldown: {str(e)}")
            
            else:
                logger.warning(f"Health check failed for {self.provider}: {str(e)}")
            
            return False
    
    def get_metrics(self) -> ModelMetrics:
        """获取性能指标.
        
        Returns:
            ModelMetrics: 性能指标
        """
        return self.metrics.model_copy()
    
    async def close(self) -> None:
        """关闭客户端连接."""
        await self._http_client.aclose()
        logger.info(f"Closed {self.provider} model client")
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.provider}:{self.config.model_name})"
    
    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}(provider={self.provider}, "
                f"model={self.config.model_name}, enabled={self.config.enabled})")


class ModelClientFactory:
    """模型客户端工厂类."""
    
    _client_classes: Dict[ModelProvider, type] = {}
    
    @classmethod
    def register_client(cls, provider: ModelProvider, client_class: type) -> None:
        """注册模型客户端类.
        
        Args:
            provider: 模型提供商
            client_class: 客户端类
        """
        cls._client_classes[provider] = client_class
        logger.info(f"Registered client class for provider: {provider}")
    
    @classmethod
    def create_client(cls, config: ModelConfig) -> BaseModelClient:
        """创建模型客户端实例.
        
        Args:
            config: 模型配置
            
        Returns:
            BaseModelClient: 模型客户端实例
            
        Raises:
            ValueError: 不支持的提供商
        """
        if config.provider not in cls._client_classes:
            raise ValueError(f"Unsupported model provider: {config.provider}")
        
        client_class = cls._client_classes[config.provider]
        return client_class(config)
    
    @classmethod
    def get_supported_providers(cls) -> List[ModelProvider]:
        """获取支持的提供商列表.
        
        Returns:
            List[ModelProvider]: 支持的提供商列表
        """
        return list(cls._client_classes.keys())