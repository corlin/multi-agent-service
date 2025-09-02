"""FastAPI异常处理器集成."""

import logging
from typing import Any, Dict

from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .exceptions import (
    BaseServiceException,
    BadRequestException,
    UnprocessableEntityException,
    InternalServerErrorException,
    ErrorCode
)
from .error_handler import error_handler


logger = logging.getLogger(__name__)


async def base_service_exception_handler(request: Request, exc: BaseServiceException) -> JSONResponse:
    """处理基础服务异常."""
    context = {
        "request_url": str(request.url),
        "request_method": request.method,
        "client_host": request.client.host if request.client else None
    }
    
    return error_handler.create_error_response(exc, context)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """处理HTTP异常."""
    context = {
        "request_url": str(request.url),
        "request_method": request.method,
        "client_host": request.client.host if request.client else None
    }
    
    return error_handler.create_error_response(exc, context)


async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """处理Starlette HTTP异常."""
    # 转换为FastAPI HTTPException
    http_exc = HTTPException(status_code=exc.status_code, detail=exc.detail)
    return await http_exception_handler(request, http_exc)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """处理请求验证异常."""
    # 提取验证错误详情
    error_details = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        error_details.append(f"{field_path}: {error['msg']}")
    
    validation_exc = UnprocessableEntityException(
        message="Request validation failed",
        context={
            "validation_errors": exc.errors(),
            "request_url": str(request.url),
            "request_method": request.method
        },
        user_message=f"请求参数验证失败: {'; '.join(error_details)}",
        suggestions=[
            "检查请求参数格式是否正确",
            "确保必需参数已提供",
            "参考API文档确认参数要求"
        ]
    )
    
    context = {
        "request_url": str(request.url),
        "request_method": request.method,
        "client_host": request.client.host if request.client else None
    }
    
    return error_handler.create_error_response(validation_exc, context)


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """处理通用异常."""
    logger.error(f"Unhandled exception in request {request.method} {request.url}: {str(exc)}", exc_info=True)
    
    # 创建内部服务器错误
    internal_exc = InternalServerErrorException(
        message=f"Unhandled exception: {type(exc).__name__}",
        context={
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "request_url": str(request.url),
            "request_method": request.method,
            "client_host": request.client.host if request.client else None
        },
        user_message="服务器内部错误，请稍后重试",
        suggestions=[
            "请稍后重试",
            "如问题持续，请联系技术支持",
            "检查请求参数是否正确"
        ]
    )
    
    context = {
        "request_url": str(request.url),
        "request_method": request.method,
        "client_host": request.client.host if request.client else None
    }
    
    return error_handler.create_error_response(internal_exc, context)


def setup_exception_handlers(app):
    """设置FastAPI应用的异常处理器."""
    
    # 基础服务异常处理器
    app.add_exception_handler(BaseServiceException, base_service_exception_handler)
    
    # HTTP异常处理器
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)
    
    # 请求验证异常处理器
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    # 通用异常处理器（必须放在最后）
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("Exception handlers have been set up")


# 错误响应工具函数
def create_error_response(
    error_code: str,
    message: str,
    status_code: int = 500,
    user_message: str = None,
    suggestions: list = None,
    context: Dict[str, Any] = None
) -> JSONResponse:
    """创建标准化错误响应的工具函数."""
    
    if error_code.startswith("API_"):
        exc_class = BadRequestException if status_code < 500 else InternalServerErrorException
    else:
        exc_class = InternalServerErrorException
    
    exc = exc_class(
        message=message,
        context=context,
        user_message=user_message,
        suggestions=suggestions or []
    )
    
    return error_handler.create_error_response(exc)


def handle_agent_error(agent_id: str, error_message: str, error_code: str = None) -> JSONResponse:
    """处理智能体错误的便捷函数."""
    from .exceptions import AgentException, ErrorCode as EC
    
    exc = AgentException(
        message=error_message,
        error_code=error_code or EC.AGENT_PROCESSING_ERROR,
        agent_id=agent_id,
        user_message="智能体处理请求时出现问题，请稍后重试",
        suggestions=[
            "请稍后重试",
            "检查请求内容是否合适",
            "联系技术支持"
        ]
    )
    
    return error_handler.create_error_response(exc)


def handle_workflow_error(workflow_id: str, error_message: str, error_code: str = None) -> JSONResponse:
    """处理工作流错误的便捷函数."""
    from .exceptions import WorkflowException, ErrorCode as EC
    
    exc = WorkflowException(
        message=error_message,
        error_code=error_code or EC.WORKFLOW_EXECUTION_FAILED,
        workflow_id=workflow_id,
        user_message="工作流执行出现问题，请稍后重试",
        suggestions=[
            "系统将重新尝试执行",
            "检查输入参数是否正确",
            "联系系统管理员"
        ]
    )
    
    return error_handler.create_error_response(exc)


def handle_model_error(provider: str, error_message: str, error_code: str = None) -> JSONResponse:
    """处理模型服务错误的便捷函数."""
    from .exceptions import ModelException, ErrorCode as EC
    
    exc = ModelException(
        message=error_message,
        error_code=error_code or EC.MODEL_API_ERROR,
        provider=provider,
        user_message="AI模型服务暂时不可用，请稍后重试",
        suggestions=[
            "系统将尝试使用备用模型",
            "请稍后重试",
            "联系技术支持"
        ]
    )
    
    return error_handler.create_error_response(exc)