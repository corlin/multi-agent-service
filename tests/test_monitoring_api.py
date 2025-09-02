"""Tests for monitoring and management API endpoints."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from src.multi_agent_service.main import app
from src.multi_agent_service.models.api import HealthCheckResponse
from src.multi_agent_service.models.base import AgentInfo
from src.multi_agent_service.models.enums import AgentType, AgentStatus


# client fixture is now provided by conftest.py


@pytest.fixture
def mock_agent_registry():
    """Mock agent registry."""
    mock_registry = AsyncMock()
    
    # Mock agent info list
    mock_agents = [
        AgentInfo(
            agent_id="sales_001",
            agent_type=AgentType.SALES,
            name="销售代表智能体",
            description="处理销售咨询",
            status=AgentStatus.ACTIVE,
            capabilities=["产品介绍", "报价咨询"],
            current_load=2,
            max_load=10,
            last_activity=datetime.now()
        ),
        AgentInfo(
            agent_id="support_001",
            agent_type=AgentType.CUSTOMER_SUPPORT,
            name="客服专员智能体",
            description="提供客户支持",
            status=AgentStatus.ACTIVE,
            capabilities=["问题解决", "客户咨询"],
            current_load=0,
            max_load=10,
            last_activity=datetime.now()
        ),
        AgentInfo(
            agent_id="manager_001",
            agent_type=AgentType.MANAGER,
            name="管理者智能体",
            description="管理决策支持",
            status=AgentStatus.OFFLINE,
            capabilities=["决策分析", "战略规划"],
            current_load=0,
            max_load=5,
            last_activity=datetime.now() - timedelta(hours=1)
        )
    ]
    
    mock_registry.list_agents.return_value = mock_agents
    return mock_registry


class TestHealthCheckAPI:
    """Test health check API endpoints."""
    
    @patch('src.multi_agent_service.api.monitoring.get_agent_registry')
    @patch('src.multi_agent_service.api.monitoring._get_system_metrics')
    def test_health_check_healthy(self, mock_get_metrics, mock_get_registry, client, mock_agent_registry):
        """Test health check with healthy status."""
        mock_get_registry.return_value = mock_agent_registry
        mock_get_metrics.return_value = {
            "cpu_usage_percent": 45.0,
            "memory_usage_percent": 60.0,
            "disk_usage_percent": 30.0
        }
        
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["status"] == "healthy"
        assert response_data["version"] == "0.1.0"
        assert "uptime" in response_data
        assert "agents_status" in response_data
        assert "system_metrics" in response_data
        
        # Check agents status summary
        agents_status = response_data["agents_status"]
        assert agents_status["total_agents"] == 3
        assert agents_status["active_agents"] == 2
        assert agents_status["offline_agents"] == 1
        assert agents_status["busy_agents"] == 1  # sales_001 has load > 0
    
    @patch('src.multi_agent_service.api.monitoring.get_agent_registry')
    @patch('src.multi_agent_service.api.monitoring._get_system_metrics')
    def test_health_check_degraded_no_agents(self, mock_get_metrics, mock_get_registry, client):
        """Test health check with degraded status due to no agents."""
        mock_registry = AsyncMock()
        mock_registry.list_agents.return_value = []  # No agents
        mock_get_registry.return_value = mock_registry
        
        mock_get_metrics.return_value = {
            "cpu_usage_percent": 20.0,
            "memory_usage_percent": 30.0,
            "disk_usage_percent": 25.0
        }
        
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["status"] == "degraded"
    
    @patch('src.multi_agent_service.api.monitoring.get_agent_registry')
    @patch('src.multi_agent_service.api.monitoring._get_system_metrics')
    def test_health_check_degraded_high_resource_usage(self, mock_get_metrics, mock_get_registry, client, mock_agent_registry):
        """Test health check with degraded status due to high resource usage."""
        mock_get_registry.return_value = mock_agent_registry
        mock_get_metrics.return_value = {
            "cpu_usage_percent": 95.0,  # High CPU usage
            "memory_usage_percent": 92.0,  # High memory usage
            "disk_usage_percent": 85.0
        }
        
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["status"] == "degraded"
    
    @patch('src.multi_agent_service.api.monitoring.get_agent_registry')
    def test_health_check_unhealthy_error(self, mock_get_registry, client):
        """Test health check with error causing unhealthy status."""
        mock_registry = AsyncMock()
        mock_registry.list_agents.side_effect = Exception("数据库连接失败")
        mock_get_registry.return_value = mock_registry
        
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["status"] == "unhealthy"
        assert "agents_status" in response_data
        assert "error" in response_data["agents_status"]


class TestSystemMetricsAPI:
    """Test system metrics API endpoints."""
    
    @patch('src.multi_agent_service.api.monitoring._get_system_metrics')
    def test_get_system_metrics_success(self, mock_get_metrics, client):
        """Test getting system metrics successfully."""
        mock_metrics = {
            "cpu_usage_percent": 45.2,
            "cpu_count": 8,
            "memory_total_gb": 16.0,
            "memory_used_gb": 8.5,
            "memory_usage_percent": 53.1,
            "disk_total_gb": 500.0,
            "disk_used_gb": 150.0,
            "disk_usage_percent": 30.0,
            "network_bytes_sent": 1024000,
            "network_bytes_recv": 2048000,
            "load_average": [1.2, 1.5, 1.8]
        }
        mock_get_metrics.return_value = mock_metrics
        
        response = client.get("/api/v1/metrics")
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["cpu_usage_percent"] == 45.2
        assert response_data["memory_usage_percent"] == 53.1
        assert response_data["disk_usage_percent"] == 30.0
        assert "service_uptime" in response_data
        assert "api_version" in response_data
        assert "timestamp" in response_data
    
    @patch('src.multi_agent_service.api.monitoring._get_system_metrics')
    def test_get_system_metrics_error(self, mock_get_metrics, client):
        """Test getting system metrics with error."""
        mock_get_metrics.side_effect = Exception("系统指标获取失败")
        
        response = client.get("/api/v1/metrics")
        
        assert response.status_code == 500
        assert "获取系统指标失败" in response.json()["detail"]


class TestAgentStatisticsAPI:
    """Test agent statistics API endpoints."""
    
    @patch('src.multi_agent_service.api.monitoring.get_agent_registry')
    def test_get_agent_statistics_success(self, mock_get_registry, client, mock_agent_registry):
        """Test getting agent statistics successfully."""
        # Add performance metrics to mock agents
        agents = mock_agent_registry.list_agents.return_value
        for agent in agents:
            agent.total_requests = 100
            agent.successful_requests = 95
            agent.failed_requests = 5
            agent.average_response_time = 1.5
        
        mock_get_registry.return_value = mock_agent_registry
        
        response = client.get("/api/v1/stats/agents")
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["total_agents"] == 3
        assert response_data["active_agents"] == 2
        assert response_data["idle_agents"] == 1  # support_001 has no load
        assert response_data["busy_agents"] == 1  # sales_001 has load > 0
        assert response_data["offline_agents"] == 1  # manager_001 is offline
        
        # Check agent types distribution
        agent_types = response_data["agent_types"]
        assert agent_types["sales"] == 1
        assert agent_types["customer_support"] == 1
        assert agent_types["manager"] == 1
        
        # Check performance metrics
        perf_metrics = response_data["performance_metrics"]
        assert perf_metrics["total_requests"] == 300  # 3 agents * 100 requests
        assert perf_metrics["successful_requests"] == 285  # 3 agents * 95 requests
        assert perf_metrics["failed_requests"] == 15  # 3 agents * 5 requests
        assert perf_metrics["success_rate"] == 95.0
        assert perf_metrics["average_response_time"] == 1.5
        
        assert "timestamp" in response_data
    
    @patch('src.multi_agent_service.api.monitoring.get_agent_registry')
    def test_get_agent_statistics_error(self, mock_get_registry, client):
        """Test getting agent statistics with error."""
        mock_registry = AsyncMock()
        mock_registry.list_agents.side_effect = Exception("获取智能体列表失败")
        mock_get_registry.return_value = mock_registry
        
        response = client.get("/api/v1/stats/agents")
        
        assert response.status_code == 500
        assert "获取智能体统计信息失败" in response.json()["detail"]


class TestWorkflowStatisticsAPI:
    """Test workflow statistics API endpoints."""
    
    def test_get_workflow_statistics_success(self, client):
        """Test getting workflow statistics successfully."""
        # Setup test workflow states
        from src.multi_agent_service.api.workflows import workflow_states
        from src.multi_agent_service.models.enums import WorkflowStatus
        from src.multi_agent_service.models.base import WorkflowState
        
        # Clear existing states
        workflow_states.clear()
        
        # Add test workflows
        now = datetime.now()
        test_workflows = [
            WorkflowState(
                workflow_id="wf_1",
                status=WorkflowStatus.COMPLETED,
                current_step=3,
                total_steps=3,
                participating_agents=["sales_001"],
                execution_history=[],
                created_at=now - timedelta(hours=2),
                updated_at=now - timedelta(hours=1)
            ),
            WorkflowState(
                workflow_id="wf_2",
                status=WorkflowStatus.RUNNING,
                current_step=1,
                total_steps=2,
                participating_agents=["support_001"],
                execution_history=[],
                created_at=now - timedelta(minutes=30),
                updated_at=now - timedelta(minutes=10)
            ),
            WorkflowState(
                workflow_id="wf_3",
                status=WorkflowStatus.FAILED,
                current_step=1,
                total_steps=4,
                participating_agents=["manager_001"],
                execution_history=[],
                created_at=now - timedelta(hours=5),
                updated_at=now - timedelta(hours=4)
            )
        ]
        
        for wf in test_workflows:
            workflow_states[wf.workflow_id] = wf
        
        response = client.get("/api/v1/stats/workflows")
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["total_workflows"] == 3
        
        # Check status distribution
        status_dist = response_data["status_distribution"]
        assert status_dist["completed"] == 1
        assert status_dist["running"] == 1
        assert status_dist["failed"] == 1
        
        # Check completion rate
        assert response_data["completion_rate"] == pytest.approx(33.33, rel=1e-2)  # 1/3 completed
        
        # Check recent activity (last 24 hours)
        recent_activity = response_data["recent_activity"]
        assert len(recent_activity) == 3  # All workflows are within 24 hours
        
        # Check sorting (most recent first)
        assert recent_activity[0]["workflow_id"] == "wf_2"  # Most recent
        
        assert "timestamp" in response_data
    
    def test_get_workflow_statistics_empty(self, client):
        """Test getting workflow statistics with no workflows."""
        from src.multi_agent_service.api.workflows import workflow_states
        
        # Clear all workflows
        workflow_states.clear()
        
        response = client.get("/api/v1/stats/workflows")
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["total_workflows"] == 0
        assert response_data["completion_rate"] == 0.0
        assert response_data["average_execution_time"] == 0.0
        assert len(response_data["recent_activity"]) == 0


class TestLogsAPI:
    """Test logs API endpoints."""
    
    def test_get_recent_logs_success(self, client):
        """Test getting recent logs successfully."""
        response = client.get("/api/v1/logs")
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert "logs" in response_data
        assert "total_count" in response_data
        assert response_data["level_filter"] == "INFO"
        assert response_data["limit"] == 100
        assert "timestamp" in response_data
        
        # Check log structure
        if response_data["logs"]:
            log_entry = response_data["logs"][0]
            assert "timestamp" in log_entry
            assert "level" in log_entry
            assert "logger" in log_entry
            assert "message" in log_entry
            assert "module" in log_entry
    
    def test_get_recent_logs_with_filters(self, client):
        """Test getting recent logs with filters."""
        response = client.get("/api/v1/logs?level=ERROR&limit=50&since=2023-01-01T00:00:00")
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["level_filter"] == "ERROR"
        assert response_data["limit"] == 50
    
    def test_get_recent_logs_error(self, client):
        """Test getting recent logs with error."""
        # This test would need to mock the logging system to simulate an error
        # For now, we just test that the endpoint exists and returns a response
        response = client.get("/api/v1/logs")
        
        # Should not return an error for basic request
        assert response.status_code == 200


class TestHealthCheckModel:
    """Test HealthCheckResponse model."""
    
    def test_health_check_response_model(self):
        """Test HealthCheckResponse model validation."""
        response_data = {
            "status": "healthy",
            "version": "0.1.0",
            "uptime": 3600,
            "agents_status": {
                "total_agents": 5,
                "active_agents": 4,
                "offline_agents": 1
            },
            "system_metrics": {
                "cpu_usage_percent": 45.0,
                "memory_usage_percent": 60.0
            }
        }
        
        response = HealthCheckResponse(**response_data)
        
        assert response.status == "healthy"
        assert response.version == "0.1.0"
        assert response.uptime == 3600
        assert response.agents_status["total_agents"] == 5
        assert response.system_metrics["cpu_usage_percent"] == 45.0
        assert response.timestamp is not None
    
    def test_health_check_response_defaults(self):
        """Test HealthCheckResponse default values."""
        response_data = {
            "status": "healthy",
            "version": "0.1.0",
            "uptime": 3600,
            "agents_status": {}
        }
        
        response = HealthCheckResponse(**response_data)
        
        assert response.system_metrics == {}
        assert response.timestamp is not None


if __name__ == "__main__":
    pytest.main([__file__])