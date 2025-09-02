"""FastAPI中间件，用于日志记录和性能监控."""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .logging import api_logger, LogCategory
from .monitoring import track_api_request


class LoggingMiddleware(BaseHTTPMiddleware):
    """日志记录中间件."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 生成请求ID
        request_id = str(uuid.uuid4())
        
        # 获取客户端信息
        client_host = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # 记录请求开始
        start_time = time.time()
        
        api_logger.info(
            f"Request started: {request.method} {request.url.path}",
            category=LogCategory.API,
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            ip_address=client_host,
            user_agent=user_agent,
            tags=["request_start"]
        )
        
        # 将请求ID添加到请求状态中，供后续使用
        request.state.request_id = request_id
        request.state.start_time = start_time
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算执行时间
            execution_time = time.time() - start_time
            
            # 记录请求完成
            api_logger.log_api_request(
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                execution_time=execution_time,
                request_id=request_id,
                ip_address=client_host,
                user_agent=user_agent
            )
            
            # 跟踪API请求指标
            track_api_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code,
                duration=execution_time
            )
            
            # 添加响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{execution_time:.3f}s"
            
            return response
            
        except Exception as exc:
            # 计算执行时间
            execution_time = time.time() - start_time
            
            # 记录请求异常
            api_logger.error(
                f"Request failed: {request.method} {request.url.path} - {str(exc)}",
                category=LogCategory.API,
                request_id=request_id,
                method=request.method,
                url=str(request.url),
                execution_time=execution_time,
                error_message=str(exc),
                ip_address=client_host,
                user_agent=user_agent,
                tags=["request_error"]
            )
            
            # 跟踪API错误指标
            track_api_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=500,  # 假设是服务器错误
                duration=execution_time
            )
            
            # 重新抛出异常，让异常处理器处理
            raise exc


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """性能监控中间件."""
    
    def __init__(self, app, slow_request_threshold: float = 1.0):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        try:
            response = await call_next(request)
            execution_time = time.time() - start_time
            
            # 检查慢请求
            if execution_time > self.slow_request_threshold:
                api_logger.warning(
                    f"Slow request detected: {request.method} {request.url.path} took {execution_time:.3f}s",
                    category=LogCategory.PERFORMANCE,
                    method=request.method,
                    url=str(request.url),
                    execution_time=execution_time,
                    threshold=self.slow_request_threshold,
                    tags=["slow_request"]
                )
            
            return response
            
        except Exception as exc:
            execution_time = time.time() - start_time
            
            # 记录异常请求的执行时间
            api_logger.error(
                f"Request exception: {request.method} {request.url.path} failed after {execution_time:.3f}s",
                category=LogCategory.PERFORMANCE,
                method=request.method,
                url=str(request.url),
                execution_time=execution_time,
                error_message=str(exc),
                tags=["request_exception"]
            )
            
            raise exc


class SecurityLoggingMiddleware(BaseHTTPMiddleware):
    """安全日志记录中间件."""
    
    def __init__(self, app, suspicious_patterns: list = None):
        super().__init__(app)
        self.suspicious_patterns = suspicious_patterns or [
            "script",
            "javascript:",
            "onload=",
            "onerror=",
            "../",
            "..\\",
            "union select",
            "drop table",
            "insert into",
            "delete from"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 检查可疑模式
        request_url = str(request.url).lower()
        client_host = request.client.host if request.client else "unknown"
        
        for pattern in self.suspicious_patterns:
            if pattern in request_url:
                api_logger.log_security_event(
                    event_type="suspicious_request",
                    severity="medium",
                    description=f"Suspicious pattern '{pattern}' detected in URL",
                    ip_address=client_host,
                    url=str(request.url),
                    pattern=pattern
                )
                break
        
        # 检查请求头中的可疑内容
        user_agent = request.headers.get("user-agent", "").lower()
        if any(pattern in user_agent for pattern in ["bot", "crawler", "spider", "scraper"]):
            api_logger.log_security_event(
                event_type="bot_request",
                severity="low",
                description="Bot or crawler detected",
                ip_address=client_host,
                user_agent=user_agent
            )
        
        try:
            response = await call_next(request)
            
            # 检查认证失败
            if response.status_code == 401:
                api_logger.log_security_event(
                    event_type="authentication_failure",
                    severity="medium",
                    description="Authentication failed",
                    ip_address=client_host,
                    url=str(request.url)
                )
            elif response.status_code == 403:
                api_logger.log_security_event(
                    event_type="authorization_failure",
                    severity="medium",
                    description="Authorization failed",
                    ip_address=client_host,
                    url=str(request.url)
                )
            
            return response
            
        except Exception as exc:
            # 记录异常作为安全事件
            api_logger.log_security_event(
                event_type="request_exception",
                severity="high",
                description=f"Request processing exception: {str(exc)}",
                ip_address=client_host,
                url=str(request.url),
                exception_type=type(exc).__name__
            )
            
            raise exc


def setup_middleware(app):
    """设置所有中间件."""
    
    # 添加安全日志中间件
    app.add_middleware(SecurityLoggingMiddleware)
    
    # 添加性能监控中间件
    app.add_middleware(PerformanceMonitoringMiddleware, slow_request_threshold=2.0)
    
    # 添加日志记录中间件
    app.add_middleware(LoggingMiddleware)
    
    api_logger.info("Middleware setup completed", category=LogCategory.SYSTEM)