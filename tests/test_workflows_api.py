"""Tests for workflow execution API endpoints."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from src.multi_agent_service.main import app
from src.multi_agent_service.models.api import WorkflowExecuteRequest, WorkflowExecuteResponse
from src.multi_agent_service.models.base import WorkflowState, ExecutionStep, AgentInfo
from src.multi_agent_service.models.enums import WorkflowType, WorkflowStatus, AgentType, Priority, AgentStatus


# client fixture is now provided by conftest.py


@pytest.fixture
def mock_graph_builder():
    """Mock graph builder."""
    return AsyncMock()


@pytest.fixture
def mock_agent_registry():
    """Mock agent registry."""
    mock_registry = AsyncMock()
    
    # Mock agent info
    mock_agent_info = AgentInfo(
        agent_id="sales_001",
        agent_type=AgentType.SALES,
        name="销售代表智能体",
        description="处理销售咨询",
        status=AgentStatus.ACTIVE,
        capabilities=["产品介绍", "报价咨询"],
        current_load=0,
        max_load=10,
        last_activity=datetime.now()
    )
    
    mock_registry.get_agent_info.return_value = mock_agent_info
    return mock_registry


@pytest.fixture
def mock_workflow_executor():
    """Mock workflow executor."""
    mock_executor = AsyncMock()
    
    # Mock execution result
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.start_time = datetime.now()
    mock_result.end_time = datetime.now() + timedelta(seconds=30)
    mock_result.results = {"status": "completed", "output": "工作流执行成功"}
    mock_result.error_message = None
    
    mock_executor.execute.return_value = mock_result
    return mock_executor


class TestWorkflowExecutionAPI:
    """Test workflow execution API endpoints."""
    
    @patch('src.multi_agent_service.api.workflows.get_agent_registry')
    @patch('src.multi_agent_service.api.workflows.get_graph_builder')
    def test_execute_workflow_success(self, mock_get_builder, mock_get_registry, client, mock_graph_builder, mock_agent_registry):
        """Test successful workflow execution request."""
        mock_get_builder.return_value = mock_graph_builder
        mock_get_registry.return_value = mock_agent_registry
        
        request_data = {
            "workflow_type": "sequential",
            "tasks": [
                {"name": "task1", "description": "第一个任务"},
                {"name": "task2", "description": "第二个任务"}
            ],
            "participating_agents": ["sales", "customer_support"],
            "context": {"project_id": "proj123"},
            "priority": "normal",
            "timeout": 3600
        }
        
        response = client.post("/api/v1/workflows/execute", json=request_data)
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert "workflow_id" in response_data
        assert response_data["status"] == "pending"
        assert "工作流" in response_data["message"]
        assert "estimated_completion_time" in response_data
        
        # Verify workflow was stored
        from src.multi_agent_service.api.workflows import workflow_states
        workflow_id = response_data["workflow_id"]
        assert workflow_id in workflow_states
        
        workflow_state = workflow_states[workflow_id]
        assert workflow_state.status == WorkflowStatus.PENDING
        assert workflow_state.total_steps == 2
        assert len(workflow_state.participating_agents) == 2
    
    def test_execute_workflow_empty_tasks(self, client):
        """Test workflow execution with empty tasks."""
        request_data = {
            "workflow_type": "sequential",
            "tasks": [],
            "participating_agents": ["sales"]
        }
        
        response = client.post("/api/v1/workflows/execute", json=request_data)
        
        assert response.status_code == 400
        assert "任务列表不能为空" in response.json()["detail"]
    
    def test_execute_workflow_empty_agents(self, client):
        """Test workflow execution with empty agents."""
        request_data = {
            "workflow_type": "sequential",
            "tasks": [{"name": "task1"}],
            "participating_agents": []
        }
        
        response = client.post("/api/v1/workflows/execute", json=request_data)
        
        assert response.status_code == 400
        assert "参与智能体列表不能为空" in response.json()["detail"]
    
    @patch('src.multi_agent_service.api.workflows.get_agent_registry')
    @patch('src.multi_agent_service.api.workflows.get_graph_builder')
    def test_execute_workflow_invalid_agent(self, mock_get_builder, mock_get_registry, client, mock_graph_builder):
        """Test workflow execution with invalid agent."""
        mock_get_builder.return_value = mock_graph_builder
        
        mock_registry = AsyncMock()
        mock_registry.get_agent_info.return_value = None  # Agent not found
        mock_get_registry.return_value = mock_registry
        
        request_data = {
            "workflow_type": "sequential",
            "tasks": [{"name": "task1"}],
            "participating_agents": ["invalid_agent"]
        }
        
        response = client.post("/api/v1/workflows/execute", json=request_data)
        
        assert response.status_code == 400
        assert "不存在" in response.json()["detail"]
    
    @patch('src.multi_agent_service.api.workflows.get_agent_registry')
    @patch('src.multi_agent_service.api.workflows.get_graph_builder')
    def test_execute_workflow_different_types(self, mock_get_builder, mock_get_registry, client, mock_graph_builder, mock_agent_registry):
        """Test workflow execution with different workflow types."""
        mock_get_builder.return_value = mock_graph_builder
        mock_get_registry.return_value = mock_agent_registry
        
        workflow_types = ["sequential", "parallel", "hierarchical"]
        
        for workflow_type in workflow_types:
            request_data = {
                "workflow_type": workflow_type,
                "tasks": [{"name": "task1"}],
                "participating_agents": ["sales"]
            }
            
            response = client.post("/api/v1/workflows/execute", json=request_data)
            
            assert response.status_code == 200
            assert response.json()["status"] == "pending"


class TestWorkflowStatusAPI:
    """Test workflow status API endpoints."""
    
    def test_get_workflow_status_success(self, client):
        """Test getting workflow status."""
        # First create a workflow
        from src.multi_agent_service.api.workflows import workflow_states
        
        workflow_id = "test_workflow_123"
        workflow_state = WorkflowState(
            workflow_id=workflow_id,
            status=WorkflowStatus.RUNNING,
            current_step=1,
            total_steps=3,
            participating_agents=["sales_001", "support_001"],
            execution_history=[],
            created_at=datetime.now() - timedelta(minutes=5),
            updated_at=datetime.now()
        )
        workflow_states[workflow_id] = workflow_state
        
        response = client.get(f"/api/v1/workflows/{workflow_id}/status")
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["workflow_state"]["workflow_id"] == workflow_id
        assert response_data["workflow_state"]["status"] == "running"
        assert response_data["progress_percentage"] == pytest.approx(33.33, rel=1e-2)
        assert "estimated_remaining_time" in response_data
    
    def test_get_workflow_status_not_found(self, client):
        """Test getting status for non-existent workflow."""
        response = client.get("/api/v1/workflows/nonexistent/status")
        
        assert response.status_code == 404
        assert "未找到工作流" in response.json()["detail"]
    
    def test_get_workflow_status_with_history(self, client):
        """Test getting workflow status with execution history."""
        from src.multi_agent_service.api.workflows import workflow_states
        
        workflow_id = "test_workflow_456"
        from src.multi_agent_service.models.base import Action
        
        action = Action(
            action_type="initialize",
            parameters={"task": "初始化任务"},
            description="初始化"
        )
        
        execution_step = ExecutionStep(
            step_id="step_001",
            agent_id="sales_001",
            action=action,
            result={"result": "初始化完成"},
            status="completed",
            start_time=datetime.now() - timedelta(minutes=2),
            end_time=datetime.now() - timedelta(minutes=1),
            error_message=None
        )
        
        workflow_state = WorkflowState(
            workflow_id=workflow_id,
            status=WorkflowStatus.COMPLETED,
            current_step=1,
            total_steps=1,
            participating_agents=["sales_001"],
            execution_history=[execution_step],
            created_at=datetime.now() - timedelta(minutes=5),
            updated_at=datetime.now()
        )
        workflow_states[workflow_id] = workflow_state
        
        response = client.get(f"/api/v1/workflows/{workflow_id}/status?include_history=true")
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["progress_percentage"] == 100.0
        assert response_data["estimated_remaining_time"] is None  # Completed workflow
    
    def test_get_workflow_status_with_agent_details(self, client):
        """Test getting workflow status with agent details."""
        from src.multi_agent_service.api.workflows import workflow_states
        
        workflow_id = "test_workflow_789"
        workflow_state = WorkflowState(
            workflow_id=workflow_id,
            status=WorkflowStatus.RUNNING,
            current_step=2,
            total_steps=4,
            participating_agents=["sales_001"],
            execution_history=[],
            created_at=datetime.now() - timedelta(minutes=3),
            updated_at=datetime.now()
        )
        workflow_states[workflow_id] = workflow_state
        
        response = client.get(f"/api/v1/workflows/{workflow_id}/status?include_agent_details=true")
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["progress_percentage"] == 50.0


class TestWorkflowListAPI:
    """Test workflow list API endpoints."""
    
    def test_list_workflows_all(self, client):
        """Test listing all workflows."""
        from src.multi_agent_service.api.workflows import workflow_states
        
        # Clear existing workflows
        workflow_states.clear()
        
        # Add test workflows
        for i in range(3):
            workflow_id = f"workflow_{i}"
            workflow_state = WorkflowState(
                workflow_id=workflow_id,
                status=WorkflowStatus.COMPLETED if i % 2 == 0 else WorkflowStatus.RUNNING,
                current_step=i + 1,
                total_steps=5,
                participating_agents=[f"agent_{i}"],
                execution_history=[],
                created_at=datetime.now() - timedelta(hours=i),
                updated_at=datetime.now()
            )
            workflow_states[workflow_id] = workflow_state
        
        response = client.get("/api/v1/workflows/list")
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["total_count"] == 3
        assert len(response_data["workflows"]) == 3
        assert response_data["limit"] == 50
        assert response_data["offset"] == 0
        assert response_data["has_more"] is False
        
        # Check sorting (should be by created_at desc)
        workflows = response_data["workflows"]
        assert workflows[0]["workflow_id"] == "workflow_0"  # Most recent
    
    def test_list_workflows_filtered_by_status(self, client):
        """Test listing workflows filtered by status."""
        response = client.get("/api/v1/workflows/list?status=completed")
        
        assert response.status_code == 200
        
        response_data = response.json()
        # All returned workflows should have completed status
        for workflow in response_data["workflows"]:
            assert workflow["status"] == "completed"
    
    def test_list_workflows_pagination(self, client):
        """Test workflow list pagination."""
        response = client.get("/api/v1/workflows/list?limit=2&offset=1")
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["limit"] == 2
        assert response_data["offset"] == 1
        assert len(response_data["workflows"]) <= 2


class TestWorkflowCancellationAPI:
    """Test workflow cancellation API endpoints."""
    
    def test_cancel_workflow_success(self, client):
        """Test successful workflow cancellation."""
        from src.multi_agent_service.api.workflows import workflow_states
        
        workflow_id = "cancel_test_workflow"
        workflow_state = WorkflowState(
            workflow_id=workflow_id,
            status=WorkflowStatus.RUNNING,
            current_step=1,
            total_steps=3,
            participating_agents=["sales_001"],
            execution_history=[],
            created_at=datetime.now() - timedelta(minutes=2),
            updated_at=datetime.now()
        )
        workflow_states[workflow_id] = workflow_state
        
        response = client.delete(f"/api/v1/workflows/{workflow_id}")
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["workflow_id"] == workflow_id
        assert response_data["status"] == "cancelled"
        assert "成功取消" in response_data["message"]
        
        # Verify workflow status was updated
        updated_state = workflow_states[workflow_id]
        assert updated_state.status == WorkflowStatus.CANCELLED
        assert len(updated_state.execution_history) == 1  # Cancel step added
    
    def test_cancel_workflow_not_found(self, client):
        """Test cancelling non-existent workflow."""
        response = client.delete("/api/v1/workflows/nonexistent")
        
        assert response.status_code == 404
        assert "未找到工作流" in response.json()["detail"]
    
    def test_cancel_workflow_already_completed(self, client):
        """Test cancelling already completed workflow."""
        from src.multi_agent_service.api.workflows import workflow_states
        
        workflow_id = "completed_workflow"
        workflow_state = WorkflowState(
            workflow_id=workflow_id,
            status=WorkflowStatus.COMPLETED,
            current_step=3,
            total_steps=3,
            participating_agents=["sales_001"],
            execution_history=[],
            created_at=datetime.now() - timedelta(minutes=10),
            updated_at=datetime.now() - timedelta(minutes=5)
        )
        workflow_states[workflow_id] = workflow_state
        
        response = client.delete(f"/api/v1/workflows/{workflow_id}")
        
        assert response.status_code == 400
        assert "已结束，无法取消" in response.json()["detail"]


class TestWorkflowModels:
    """Test workflow request/response models."""
    
    def test_workflow_execute_request_model(self):
        """Test WorkflowExecuteRequest model validation."""
        request_data = {
            "workflow_type": "sequential",
            "tasks": [
                {"name": "task1", "description": "第一个任务"},
                {"name": "task2", "description": "第二个任务"}
            ],
            "participating_agents": ["sales", "customer_support"],
            "context": {"project_id": "proj123"},
            "priority": "high",
            "timeout": 1800
        }
        
        request = WorkflowExecuteRequest(**request_data)
        
        assert request.workflow_type == WorkflowType.SEQUENTIAL
        assert len(request.tasks) == 2
        assert request.participating_agents == [AgentType.SALES, AgentType.CUSTOMER_SUPPORT]
        assert request.context == {"project_id": "proj123"}
        assert request.priority == Priority.HIGH
        assert request.timeout == 1800
    
    def test_workflow_execute_request_defaults(self):
        """Test WorkflowExecuteRequest default values."""
        request_data = {
            "workflow_type": "parallel",
            "tasks": [{"name": "task1"}],
            "participating_agents": ["sales"]
        }
        
        request = WorkflowExecuteRequest(**request_data)
        
        assert request.workflow_type == WorkflowType.PARALLEL
        assert request.context == {}
        assert request.priority == Priority.NORMAL
        assert request.timeout is None
    
    def test_workflow_execute_response_model(self):
        """Test WorkflowExecuteResponse model."""
        response_data = {
            "workflow_id": "workflow_123",
            "status": "pending",
            "message": "工作流已启动",
            "estimated_completion_time": datetime.now() + timedelta(hours=1)
        }
        
        response = WorkflowExecuteResponse(**response_data)
        
        assert response.workflow_id == "workflow_123"
        assert response.status == "pending"
        assert response.message == "工作流已启动"
        assert response.estimated_completion_time is not None


if __name__ == "__main__":
    pytest.main([__file__])