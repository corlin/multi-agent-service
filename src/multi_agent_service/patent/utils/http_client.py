"""HTTP client utilities with circuit breaker and retry mechanisms."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, List
from enum import Enum

import httpx


class CircuitBreakerState(Enum):
    """熔断器状态."""
    CLOSED = "closed"      # 正常状态
    OPEN = "open"          # 熔断状态
    HALF_OPEN = "half_open"  # 半开状态


class CircuitBreaker:
    """熔断器实现，集成现有的故障处理机制."""
    
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 expected_exception: type = Exception):
        """
        初始化熔断器.
        
        Args:
            failure_threshold: 失败阈值
            recovery_timeout: 恢复超时时间(秒)
            expected_exception: 预期的异常类型
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitBreakerState.CLOSED
        
        self.logger = logging.getLogger(__name__)
    
    async def call(self, func, *args, **kwargs):
        """通过熔断器调用函数."""
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                self.logger.info("Circuit breaker moved to HALF_OPEN state")
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """检查是否应该尝试重置熔断器."""
        if self.last_failure_time is None:
            return True
        
        return datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)
    
    def _on_success(self):
        """成功时的处理."""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED
    
    def _on_failure(self):
        """失败时的处理."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            self.logger.warning(f"Circuit breaker opened after {self.failure_count} failures")


class RetryConfig:
    """重试配置."""
    
    def __init__(self,
                 max_attempts: int = 3,
                 base_delay: float = 1.0,
                 max_delay: float = 60.0,
                 backoff_factor: float = 2.0,
                 jitter: bool = True):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter


class PatentHTTPClient:
    """专利数据收集专用HTTP客户端，集成重试和熔断器机制."""
    
    def __init__(self, 
                 base_url: str,
                 timeout: int = 30,
                 retry_config: Optional[RetryConfig] = None,
                 circuit_breaker: Optional[CircuitBreaker] = None,
                 headers: Optional[Dict[str, str]] = None):
        """
        初始化HTTP客户端.
        
        Args:
            base_url: 基础URL
            timeout: 超时时间
            retry_config: 重试配置
            circuit_breaker: 熔断器
            headers: 请求头
        """
        self.base_url = base_url
        self.timeout = timeout
        self.retry_config = retry_config or RetryConfig()
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        
        # 默认请求头
        default_headers = {
            'User-Agent': 'Patent-Analysis-Agent/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        if headers:
            default_headers.update(headers)
        
        # 创建HTTP客户端
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(timeout),
            headers=default_headers
        )
        
        self.logger = logging.getLogger(__name__)
        
        # 统计信息
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'retry_attempts': 0,
            'circuit_breaker_opens': 0
        }
    
    async def get(self, url: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> httpx.Response:
        """发送GET请求."""
        return await self._request('GET', url, params=params, **kwargs)
    
    async def post(self, url: str, json: Optional[Dict[str, Any]] = None, data: Optional[Any] = None, **kwargs) -> httpx.Response:
        """发送POST请求."""
        return await self._request('POST', url, json=json, data=data, **kwargs)
    
    async def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """发送HTTP请求，集成重试和熔断器机制."""
        self.stats['total_requests'] += 1
        
        async def _make_request():
            return await self._client.request(method, url, **kwargs)
        
        try:
            # 通过熔断器执行请求
            response = await self.circuit_breaker.call(self._request_with_retry, _make_request)
            self.stats['successful_requests'] += 1
            return response
            
        except Exception as e:
            self.stats['failed_requests'] += 1
            self.logger.error(f"HTTP request failed: {method} {url} - {str(e)}")
            raise e
    
    async def _request_with_retry(self, request_func) -> httpx.Response:
        """带重试机制的请求执行."""
        last_exception = None
        
        for attempt in range(self.retry_config.max_attempts):
            try:
                response = await request_func()
                
                # 检查HTTP状态码
                if response.status_code >= 400:
                    if response.status_code >= 500 and attempt < self.retry_config.max_attempts - 1:
                        # 服务器错误，可以重试
                        raise httpx.HTTPStatusError(
                            f"Server error: {response.status_code}",
                            request=response.request,
                            response=response
                        )
                    else:
                        # 客户端错误或最后一次尝试，不重试
                        response.raise_for_status()
                
                return response
                
            except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.ConnectError) as e:
                last_exception = e
                
                if attempt < self.retry_config.max_attempts - 1:
                    # 计算重试延迟
                    delay = self._calculate_retry_delay(attempt)
                    self.logger.warning(f"Request failed (attempt {attempt + 1}/{self.retry_config.max_attempts}), retrying in {delay:.2f}s: {str(e)}")
                    
                    self.stats['retry_attempts'] += 1
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(f"Request failed after {self.retry_config.max_attempts} attempts: {str(e)}")
        
        # 所有重试都失败了
        if last_exception:
            raise last_exception
        else:
            raise Exception("Request failed after all retry attempts")
    
    def _calculate_retry_delay(self, attempt: int) -> float:
        """计算重试延迟."""
        delay = self.retry_config.base_delay * (self.retry_config.backoff_factor ** attempt)
        delay = min(delay, self.retry_config.max_delay)
        
        # 添加抖动
        if self.retry_config.jitter:
            import random
            delay = delay * (0.5 + random.random() * 0.5)
        
        return delay
    
    async def close(self):
        """关闭HTTP客户端."""
        await self._client.aclose()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息."""
        stats = self.stats.copy()
        
        # 计算成功率
        if stats['total_requests'] > 0:
            stats['success_rate'] = (stats['successful_requests'] / stats['total_requests']) * 100
        else:
            stats['success_rate'] = 0.0
        
        # 添加熔断器状态
        stats['circuit_breaker_state'] = self.circuit_breaker.state.value
        stats['circuit_breaker_failure_count'] = self.circuit_breaker.failure_count
        
        return stats
    
    async def __aenter__(self):
        """异步上下文管理器入口."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口."""
        await self.close()


class RateLimiter:
    """速率限制器."""
    
    def __init__(self, max_requests: int, time_window: int = 60):
        """
        初始化速率限制器.
        
        Args:
            max_requests: 时间窗口内的最大请求数
            time_window: 时间窗口(秒)
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: List[datetime] = []
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """获取请求许可."""
        async with self._lock:
            now = datetime.now()
            
            # 清理过期的请求记录
            cutoff_time = now - timedelta(seconds=self.time_window)
            self.requests = [req_time for req_time in self.requests if req_time > cutoff_time]
            
            # 检查是否超过限制
            if len(self.requests) >= self.max_requests:
                # 计算需要等待的时间
                oldest_request = min(self.requests)
                wait_time = (oldest_request + timedelta(seconds=self.time_window) - now).total_seconds()
                
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    return await self.acquire()  # 递归调用
            
            # 记录当前请求
            self.requests.append(now)
            return True