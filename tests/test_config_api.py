"""Tests for configuration management API endpoints."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from src.multi_agent_service.main import app
from src.multi_agent_service.models.config import AgentConfig, ModelConfig, ConfigUpdateRequest
from src.multi_agent_service.models.base import AgentInfo
from src.multi_agent_service.models.enums import AgentType, AgentStatus, ModelProvider


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
            current_load=0,
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
        )
    ]
    
    mock_registry.list_agents.return_value = mock_agents
    return mock_registry


@pytest.fixture
def sample_agent_config():
    """Sample agent configuration."""
    model_config = ModelConfig(
        provider=ModelProvider.OPENAI,
        model_name="gpt-3.5-turbo",
        api_key="test_api_key",
        base_url="https://api.openai.com/v1",
        max_tokens=1000,
        temperature=0.7,
        timeout=30
    )
    
    return AgentConfig(
        agent_id="sales_001",
        agent_type=AgentType.SALES,
        name="销售代表智能体",
        description="专门处理销售咨询和客户关系管理",
        capabilities=["产品介绍", "报价咨询", "客户关系管理"],
        llm_config=model_config,
        prompt_template="你是一个专业的销售代表..."
    )


class TestAgentConfigurationAPI:
    """Test agent configuration API endpoints."""
    
    @patch('src.multi_agent_service.api.config.get_agent_registry')
    def test_get_agent_configurations_all(self, mock_get_registry, client, mock_agent_registry):
        """Test getting all agent configurations."""
        mock_get_registry.return_value = mock_agent_registry
        
        response = client.get("/api/v1/config/agents")
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert "configurations" in response_data
        assert "total_count" in response_data
        assert response_data["total_count"] == 2
        assert len(response_data["configurations"]) == 2
        
        # Check configuration structure
        config = response_data["configurations"][0]
        assert "agent_id" in config
        assert "agent_type" in config
        assert "name" in config
        assert "description" in config
        assert "capabilities" in config
        assert "model_config" in config
        assert "prompt_template" in config
        
        # Check that API key is masked
        model_config = config["model_config"]
        assert model_config["api_key"] == "***" or model_config["api_key"] is None
    
    @patch('src.multi_agent_service.api.config.get_agent_registry')
    def test_get_agent_configurations_filtered_by_type(self, mock_get_registry, client, mock_agent_registry):
        """Test getting agent configurations filtered by type."""
        mock_get_registry.return_value = mock_agent_registry
        
        response = client.get("/api/v1/config/agents?agent_type=sales")
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["total_count"] == 1
        assert response_data["configurations"][0]["agent_type"] == "sales"
    
    @patch('src.multi_agent_service.api.config.get_agent_registry')
    def test_get_agent_configuration_by_id_success(self, mock_get_registry, client, mock_agent_registry):
        """Test getting specific agent configuration by ID."""
        mock_get_registry.return_value = mock_agent_registry
        
        response = client.get("/api/v1/config/agents/sales_001")
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["agent_id"] == "sales_001"
        assert response_data["agent_type"] == "sales"
        assert "model_config" in response_data
        assert "capabilities" in response_data
    
    @patch('src.multi_agent_service.api.config.get_agent_registry')
    def test_get_agent_configuration_not_found(self, mock_get_registry, client):
        """Test getting configuration for non-existent agent."""
        mock_registry = AsyncMock()
        mock_registry.list_agents.return_value = []  # No agents
        mock_get_registry.return_value = mock_registry
        
        response = client.get("/api/v1/config/agents/nonexistent")
        
        assert response.status_code == 404
        assert "未找到智能体" in response.json()["detail"]
    
    @patch('src.multi_agent_service.api.config.get_agent_registry')
    def test_update_agent_configuration_success(self, mock_get_registry, client, mock_agent_registry):
        """Test updating agent configuration successfully."""
        mock_get_registry.return_value = mock_agent_registry
        
        update_data = {
            "config_data": {
                "name": "更新的销售代表智能体",
                "description": "更新后的描述",
                "capabilities": ["产品介绍", "报价咨询", "客户关系管理", "售后服务"],
                "max_tokens": 1500,
                "temperature": 0.8,
                "prompt_template": "你是一个经验丰富的销售代表..."
            },
            "hot_reload": False
        }
        
        response = client.put("/api/v1/config/agents/sales_001", json=update_data)
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["success"] is True
        assert "配置更新成功" in response_data["message"]
        assert response_data["validation_result"]["is_valid"] is True
        assert response_data["hot_reload_applied"] is False
    
    @patch('src.multi_agent_service.api.config.get_agent_registry')
    def test_update_agent_configuration_with_hot_reload(self, mock_get_registry, client, mock_agent_registry):
        """Test updating agent configuration with hot reload."""
        mock_get_registry.return_value = mock_agent_registry
        
        update_data = {
            "config_data": {
                "name": "热更新的销售代表智能体",
                "temperature": 0.9
            },
            "hot_reload": True
        }
        
        response = client.put("/api/v1/config/agents/sales_001", json=update_data)
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["success"] is True
        assert response_data["hot_reload_applied"] is True
        assert response_data["hot_reload_success"] is True
    
    @patch('src.multi_agent_service.api.config.get_agent_registry')
    def test_update_agent_configuration_validation_error(self, mock_get_registry, client, mock_agent_registry):
        """Test updating agent configuration with validation errors."""
        mock_get_registry.return_value = mock_agent_registry
        
        update_data = {
            "config_data": {
                "name": "",  # Empty name should cause validation error
                "max_tokens": 5000,  # Too high
                "temperature": 3.0  # Out of range
            },
            "hot_reload": False
        }
        
        response = client.put("/api/v1/config/agents/sales_001", json=update_data)
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["success"] is False
        assert "配置验证失败" in response_data["message"]
        assert response_data["validation_result"]["is_valid"] is False
        assert len(response_data["validation_result"]["errors"]) > 0
    
    @patch('src.multi_agent_service.api.config.get_agent_registry')
    def test_validate_agent_configuration_success(self, mock_get_registry, client, mock_agent_registry):
        """Test validating agent configuration successfully."""
        mock_get_registry.return_value = mock_agent_registry
        
        config_data = {
            "name": "测试智能体",
            "description": "测试描述",
            "capabilities": ["测试能力"],
            "prompt_template": "这是一个测试提示词模板",
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        response = client.post("/api/v1/config/agents/sales_001/validate", json=config_data)
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["is_valid"] is True
        assert len(response_data["errors"]) == 0
    
    @patch('src.multi_agent_service.api.config.get_agent_registry')
    def test_validate_agent_configuration_errors(self, mock_get_registry, client, mock_agent_registry):
        """Test validating agent configuration with errors."""
        mock_get_registry.return_value = mock_agent_registry
        
        config_data = {
            "name": "",  # Missing required field
            "max_tokens": -1,  # Invalid value
            "temperature": 5.0  # Out of range
        }
        
        response = client.post("/api/v1/config/agents/sales_001/validate", json=config_data)
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["is_valid"] is False
        assert len(response_data["errors"]) > 0


class TestSystemConfigurationAPI:
    """Test system configuration API endpoints."""
    
    def test_get_system_configuration_success(self, client):
        """Test getting system configuration successfully."""
        response = client.get("/api/v1/config/system")
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert "configuration" in response_data
        assert "timestamp" in response_data
        
        config = response_data["configuration"]
        assert "api_settings" in config
        assert "model_settings" in config
        assert "workflow_settings" in config
        assert "agent_settings" in config
        assert "custom_settings" in config
        
        # Check API settings structure
        api_settings = config["api_settings"]
        assert "host" in api_settings
        assert "port" in api_settings
        assert "debug" in api_settings
        assert "log_level" in api_settings
    
    def test_update_system_configuration_success(self, client):
        """Test updating system configuration successfully."""
        config_data = {
            "max_concurrent_workflows": 20,
            "workflow_timeout": 7200,
            "custom_feature_enabled": True
        }
        
        response = client.put("/api/v1/config/system", json=config_data)
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["success"] is True
        assert "配置更新成功" in response_data["message"]
        assert response_data["hot_reload_applied"] is False
    
    def test_update_system_configuration_with_hot_reload(self, client):
        """Test updating system configuration with hot reload."""
        config_data = {
            "log_level": "DEBUG",
            "enable_metrics": True
        }
        
        response = client.put("/api/v1/config/system?hot_reload=true", json=config_data)
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["success"] is True
        assert response_data["hot_reload_applied"] is True


class TestConfigurationModels:
    """Test configuration data models."""
    
    def test_agent_config_model(self, sample_agent_config):
        """Test AgentConfig model validation."""
        config = sample_agent_config
        
        assert config.agent_id == "sales_001"
        assert config.agent_type == AgentType.SALES
        assert config.name == "销售代表智能体"
        assert len(config.capabilities) == 3
        assert config.llm_config.provider == ModelProvider.OPENAI
    
    def test_model_config_model(self):
        """Test ModelConfig model validation."""
        config_data = {
            "provider": "openai",
            "model_name": "gpt-4",
            "api_key": "sk-test123",
            "base_url": "https://api.openai.com/v1",
            "max_tokens": 2000,
            "temperature": 0.5,
            "timeout": 60
        }
        
        config = ModelConfig(**config_data)
        
        assert config.provider == ModelProvider.OPENAI
        assert config.model_name == "gpt-4"
        assert config.api_key == "sk-test123"
        assert config.max_tokens == 2000
        assert config.temperature == 0.5
        assert config.timeout == 60
    
    def test_config_update_request_model(self):
        """Test ConfigUpdateRequest model validation."""
        request_data = {
            "config_type": "agent",
            "config_id": "test_agent_001",
            "config_data": {
                "name": "更新的智能体",
                "temperature": 0.8
            },
            "hot_reload": True
        }
        
        request = ConfigUpdateRequest(**request_data)
        
        assert request.config_data["name"] == "更新的智能体"
        assert request.config_data["temperature"] == 0.8
        assert request.hot_reload is True
    
    def test_config_update_request_defaults(self):
        """Test ConfigUpdateRequest default values."""
        request_data = {
            "config_type": "agent",
            "config_id": "test_agent_002",
            "config_data": {
                "name": "测试智能体"
            }
        }
        
        request = ConfigUpdateRequest(**request_data)
        
        assert request.hot_reload is False


class TestConfigurationValidation:
    """Test configuration validation functions."""
    
    def test_validate_agent_config_valid(self):
        """Test validating valid agent configuration."""
        from src.multi_agent_service.api.config import _validate_agent_config
        
        config_data = {
            "name": "测试智能体",
            "description": "这是一个测试智能体",
            "capabilities": ["测试能力1", "测试能力2"],
            "prompt_template": "你是一个测试智能体，专门用于测试目的",
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        result = _validate_agent_config(config_data, AgentType.SALES)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_agent_config_missing_fields(self):
        """Test validating agent configuration with missing fields."""
        from src.multi_agent_service.api.config import _validate_agent_config
        
        config_data = {
            "name": "",  # Empty name
            "max_tokens": 5000,  # Too high
            "temperature": -1  # Invalid range
        }
        
        result = _validate_agent_config(config_data, AgentType.SALES)
        
        assert result.is_valid is False
        assert len(result.errors) > 0
        
        # Check specific error messages
        error_messages = " ".join(result.errors)
        assert "缺少必需字段" in error_messages or "必须是" in error_messages
    
    def test_validate_agent_config_warnings(self):
        """Test validating agent configuration with warnings."""
        from src.multi_agent_service.api.config import _validate_agent_config
        
        config_data = {
            "name": "测试智能体",
            "description": "测试描述",
            "capabilities": [],  # Empty capabilities should generate warning
            "prompt_template": "短",  # Short template should generate warning
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        result = _validate_agent_config(config_data, AgentType.SALES)
        
        assert result.is_valid is True  # No errors, just warnings
        assert len(result.warnings) > 0


if __name__ == "__main__":
    pytest.main([__file__])