"""FastAPI错误处理器集成测试."""

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ValidationError

from src.multi_agent_service.utils.exceptions import (
    BadRequestException,
    UnauthorizedException,
    NotFoundException,
    InternalServerErrorException,
    AgentException,
    WorkflowException,
    ModelException,
    ErrorCode
)
from src.multi_agent_service.utils.fastapi_handlers import (
    setup_exception_handlers,
    create_error_response,
    handle_agent_error,
    handle_workflow_error,
    handle_model_error
)


# 创建测试应用
def create_test_app():
    """创建测试FastAPI应用."""
    app = FastAPI()
    setup_exception_handlers(app)
    
    @app.get("/test/success")
    async def success_endpoint():
        return {"message": "success"}
    
    @app.get("/test/bad-request")
    async def bad_request_endpoint():
        raise BadRequestException("Invalid request parameter")
    
    @app.get("/test/unauthorized")
    async def unauthorized_endpoint():
        raise UnauthorizedException("Authentication required")
    
    @app.get("/test/not-found")
    async def not_found_endpoint():
        raise NotFoundException("Resource not found")
    
    @app.get("/test/internal-error")
    async def internal_error_endpoint():
        raise InternalServerErrorException("Internal server error")
    
    @app.get("/test/http-exception")
    async def http_exception_endpoint():
        raise HTTPException(status_code=403, detail="Forbidden")
    
    @app.get("/test/agent-error")
    async def agent_error_endpoint():
        raise AgentException(
            message="Agent processing failed",
            error_code=ErrorCode.AGENT_PROCESSING_ERROR,
            agent_id="test-agent-123"
        )
    
    @app.get("/test/workflow-error")
    async def workflow_error_endpoint():
        raise WorkflowException(
            message="Workflow execution failed",
            error_code=ErrorCode.WORKFLOW_EXECUTION_FAILED,
            workflow_id="test-workflow-456"
        )
    
    @app.get("/test/model-error")
    async def model_error_endpoint():
        raise ModelException(
            message="Model API error",
            error_code=ErrorCode.MODEL_API_ERROR,
            provider="qwen"
        )
    
    @app.get("/test/unknown-error")
    async def unknown_error_endpoint():
        raise ValueError("Unknown error")
    
    class TestModel(BaseModel):
        name: str
        age: int
    
    @app.post("/test/validation-error")
    async def validation_error_endpoint(data: TestModel):
        return {"received": data}
    
    return app


@pytest.fixture
def test_app():
    """测试应用fixture."""
    return create_test_app()


@pytest.fixture
def client(test_app):
    """测试客户端fixture."""
    return TestClient(test_app)


class TestFastAPIErrorHandlers:
    """测试FastAPI错误处理器."""
    
    def test_success_endpoint(self, client):
        """测试正常端点."""
        response = client.get("/test/success")
        assert response.status_code == 200
        assert response.json() == {"message": "success"}
    
    def test_bad_request_exception(self, client):
        """测试BadRequestException处理."""
        response = client.get("/test/bad-request")
        assert response.status_code == 400
        
        data = response.json()
        assert "error" in data
        assert data["error"]["error_code"] == ErrorCode.BAD_REQUEST
        assert data["error"]["category"] == "api"
        assert "Invalid request parameter" in data["error"]["message"]
    
    def test_unauthorized_exception(self, client):
        """测试UnauthorizedException处理."""
        response = client.get("/test/unauthorized")
        assert response.status_code == 401
        
        data = response.json()
        assert "error" in data
        assert data["error"]["error_code"] == ErrorCode.UNAUTHORIZED
        assert data["error"]["category"] == "api"
    
    def test_not_found_exception(self, client):
        """测试NotFoundException处理."""
        response = client.get("/test/not-found")
        assert response.status_code == 404
        
        data = response.json()
        assert "error" in data
        assert data["error"]["error_code"] == ErrorCode.NOT_FOUND
        assert data["error"]["category"] == "api"
    
    def test_internal_server_error_exception(self, client):
        """测试InternalServerErrorException处理."""
        response = client.get("/test/internal-error")
        assert response.status_code == 500
        
        data = response.json()
        assert "error" in data
        assert data["error"]["error_code"] == ErrorCode.INTERNAL_SERVER_ERROR
        assert data["error"]["category"] == "api"
        assert data["error"]["severity"] == "high"
    
    def test_http_exception(self, client):
        """测试HTTPException处理."""
        response = client.get("/test/http-exception")
        assert response.status_code == 403
        
        data = response.json()
        assert "error" in data
        assert data["error"]["error_code"] == "HTTP_403"
        assert data["error"]["category"] == "api"
        assert "Forbidden" in data["error"]["message"]
    
    def test_agent_exception(self, client):
        """测试AgentException处理."""
        response = client.get("/test/agent-error")
        assert response.status_code == 422
        
        data = response.json()
        assert "error" in data
        assert data["error"]["error_code"] == ErrorCode.AGENT_PROCESSING_ERROR
        assert data["error"]["category"] == "agent"
        assert data["error"]["agent_id"] == "test-agent-123"
        assert "recovery_actions" in data["error"]
    
    def test_workflow_exception(self, client):
        """测试WorkflowException处理."""
        response = client.get("/test/workflow-error")
        assert response.status_code == 422
        
        data = response.json()
        assert "error" in data
        assert data["error"]["error_code"] == ErrorCode.WORKFLOW_EXECUTION_FAILED
        assert data["error"]["category"] == "workflow"
        assert data["error"]["workflow_id"] == "test-workflow-456"
        assert "recovery_actions" in data["error"]
    
    def test_model_exception(self, client):
        """测试ModelException处理."""
        response = client.get("/test/model-error")
        assert response.status_code == 503
        
        data = response.json()
        assert "error" in data
        assert data["error"]["error_code"] == ErrorCode.MODEL_API_ERROR
        assert data["error"]["category"] == "model"
        assert data["error"]["provider"] == "qwen"
        assert "recovery_actions" in data["error"]
    
    def test_unknown_exception(self, client):
        """测试未知异常处理."""
        # 由于异常处理器会捕获并转换异常，我们需要使用不同的方法测试
        # 这里我们直接测试异常处理器的功能
        from src.multi_agent_service.utils.fastapi_handlers import general_exception_handler
        from fastapi import Request
        from unittest.mock import Mock
        
        # 创建模拟请求
        mock_request = Mock(spec=Request)
        mock_request.url = "http://testserver/test/unknown-error"
        mock_request.method = "GET"
        mock_request.client = Mock()
        mock_request.client.host = "testserver"
        
        # 测试异常处理器
        import asyncio
        response = asyncio.run(general_exception_handler(mock_request, ValueError("Unknown error")))
        
        assert response.status_code == 500
        
        import json
        data = json.loads(response.body.decode())
        assert "error" in data
        assert data["error"]["error_code"] == ErrorCode.INTERNAL_SERVER_ERROR
        assert data["error"]["category"] == "api"
        assert "服务器内部错误" in data["error"]["message"]
    
    def test_validation_error(self, client):
        """测试请求验证错误处理."""
        # 发送无效数据
        response = client.post("/test/validation-error", json={"name": "test"})  # 缺少age字段
        assert response.status_code == 422
        
        data = response.json()
        assert "error" in data
        assert data["error"]["error_code"] == ErrorCode.UNPROCESSABLE_ENTITY
        assert data["error"]["category"] == "api"
        assert "请求参数验证失败" in data["error"]["message"]
        assert "suggestions" in data["error"]
    
    def test_validation_error_with_invalid_type(self, client):
        """测试类型错误的验证异常."""
        # 发送错误类型的数据
        response = client.post("/test/validation-error", json={"name": "test", "age": "not_a_number"})
        assert response.status_code == 422
        
        data = response.json()
        assert "error" in data
        assert data["error"]["error_code"] == ErrorCode.UNPROCESSABLE_ENTITY
        assert "请求参数验证失败" in data["error"]["message"]


class TestErrorResponseHelpers:
    """测试错误响应辅助函数."""
    
    def test_create_error_response(self):
        """测试创建错误响应函数."""
        response = create_error_response(
            error_code=ErrorCode.BAD_REQUEST,
            message="Test error",
            status_code=400,
            user_message="User friendly message",
            suggestions=["Try again"],
            context={"test": "value"}
        )
        
        assert response.status_code == 400
        data = response.body.decode()
        assert "error" in data
        assert ErrorCode.BAD_REQUEST in data
    
    def test_handle_agent_error(self):
        """测试处理智能体错误函数."""
        response = handle_agent_error(
            agent_id="test-agent",
            error_message="Agent failed",
            error_code=ErrorCode.AGENT_TIMEOUT
        )
        
        assert response.status_code == 422
        data = response.body.decode()
        assert "error" in data
        assert ErrorCode.AGENT_TIMEOUT in data
        assert "test-agent" in data
    
    def test_handle_workflow_error(self):
        """测试处理工作流错误函数."""
        response = handle_workflow_error(
            workflow_id="test-workflow",
            error_message="Workflow failed",
            error_code=ErrorCode.WORKFLOW_STEP_FAILED
        )
        
        assert response.status_code == 422
        data = response.body.decode()
        assert "error" in data
        assert ErrorCode.WORKFLOW_STEP_FAILED in data
        assert "test-workflow" in data
    
    def test_handle_model_error(self):
        """测试处理模型错误函数."""
        response = handle_model_error(
            provider="qwen",
            error_message="Model failed",
            error_code=ErrorCode.MODEL_QUOTA_EXCEEDED
        )
        
        assert response.status_code == 503
        data = response.body.decode()
        assert "error" in data
        assert ErrorCode.MODEL_QUOTA_EXCEEDED in data
        assert "qwen" in data


class TestErrorResponseFormat:
    """测试错误响应格式."""
    
    def test_error_response_structure(self, client):
        """测试错误响应结构."""
        response = client.get("/test/bad-request")
        data = response.json()
        
        # 验证错误响应结构
        assert "error" in data
        error = data["error"]
        
        # 必需字段
        assert "error_id" in error
        assert "error_code" in error
        assert "message" in error
        assert "category" in error
        assert "severity" in error
        assert "timestamp" in error
        
        # 可选字段
        if "suggestions" in error:
            assert isinstance(error["suggestions"], list)
        
        if "recovery_actions" in error:
            assert isinstance(error["recovery_actions"], list)
    
    def test_error_id_uniqueness(self, client):
        """测试错误ID唯一性."""
        response1 = client.get("/test/bad-request")
        response2 = client.get("/test/bad-request")
        
        data1 = response1.json()
        data2 = response2.json()
        
        # 每次错误应该有不同的error_id
        assert data1["error"]["error_id"] != data2["error"]["error_id"]
    
    def test_timestamp_format(self, client):
        """测试时间戳格式."""
        response = client.get("/test/bad-request")
        data = response.json()
        
        timestamp = data["error"]["timestamp"]
        # 验证ISO格式时间戳
        assert "T" in timestamp
        assert timestamp.endswith("Z") or "+" in timestamp or timestamp.count(":") >= 2


if __name__ == "__main__":
    pytest.main([__file__])