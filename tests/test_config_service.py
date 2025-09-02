"""Tests for configuration service."""

import json
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from src.multi_agent_service.services.config_service import ConfigService
from src.multi_agent_service.config.config_manager import ConfigManager
from src.multi_agent_service.models.config import (
    AgentConfig, ModelConfig, WorkflowConfig,
    ConfigUpdateRequest, ConfigValidationResult
)
from src.multi_agent_service.models.enums import AgentType, ModelProvider


class TestConfigService:
    """配置服务测试类."""
    
    @pytest.fixture
    def temp_config_dir(self):
        """创建临时配置目录."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def mock_config_manager(self):
        """模拟配置管理器."""
        mock_manager = MagicMock(spec=ConfigManager)
        mock_manager.get_config_status.return_value = {
            "last_reload_time": "2024-01-01T00:00:00",
            "agent_configs_count": 2,
            "model_configs_count": 2,
            "workflow_configs_count": 1,
            "file_watching_active": False,
            "config_directory": "/test/config",
            "settings_loaded": True
        }
        return mock_manager
    
    @pytest.fixture
    def config_service(self, mock_config_manager):
        """配置服务实例."""
        return ConfigService(mock_config_manager)
    
    @pytest.fixture
    def sample_agent_config_data(self):
        """示例智能体配置数据."""
        return {
            "agent_id": "test_agent",
            "agent_type": "sales",
            "name": "测试智能体",
            "description": "用于测试的智能体",
            "enabled": True,
            "capabilities": ["test_capability"],
            "llm_config": {
                "provider": "openai",
                "model_name": "gpt-3.5-turbo",
                "api_key": "test_key",
                "max_tokens": 2000,
                "temperature": 0.7,
                "timeout": 30,
                "retry_attempts": 3
            },
            "prompt_template": "测试提示词模板",
            "max_concurrent_tasks": 5,
            "priority": 8
        }
    
    @pytest.fixture
    def sample_model_config_data(self):
        """示例模型配置数据."""
        return {
            "provider": "openai",
            "model_name": "gpt-3.5-turbo",
            "api_key": "test_key",
            "max_tokens": 2000,
            "temperature": 0.7,
            "timeout": 30,
            "retry_attempts": 3,
            "enabled": True
        }
    
    @pytest.fixture
    def sample_workflow_config_data(self):
        """示例工作流配置数据."""
        return {
            "workflow_id": "test_workflow",
            "name": "测试工作流",
            "description": "用于测试的工作流",
            "enabled": True,
            "workflow_type": "sequential",
            "participating_agents": ["test_agent"],
            "timeout": 300
        }
    
    @pytest.mark.asyncio
    async def test_initialize_service(self, config_service, mock_config_manager):
        """测试服务初始化."""
        await config_service.initialize()
        
        mock_config_manager.start_file_watching.assert_called_once()
        assert config_service._initialized is True
    
    @pytest.mark.asyncio
    async def test_shutdown_service(self, config_service, mock_config_manager):
        """测试服务关闭."""
        # 先初始化
        await config_service.initialize()
        
        # 然后关闭
        await config_service.shutdown()
        
        mock_config_manager.stop_file_watching.assert_called_once()
        assert config_service._initialized is False
    
    def test_get_agent_config(self, config_service, mock_config_manager, sample_agent_config_data):
        """测试获取智能体配置."""
        # 设置模拟返回值
        expected_config = AgentConfig(**sample_agent_config_data)
        mock_config_manager.get_agent_config.return_value = expected_config
        
        # 调用方法
        result = config_service.get_agent_config("test_agent")
        
        # 验证结果
        assert result == expected_config
        mock_config_manager.get_agent_config.assert_called_once_with("test_agent")
    
    def test_get_all_agent_configs(self, config_service, mock_config_manager, sample_agent_config_data):
        """测试获取所有智能体配置."""
        # 设置模拟返回值
        expected_configs = {"test_agent": AgentConfig(**sample_agent_config_data)}
        mock_config_manager.get_all_agent_configs.return_value = expected_configs
        
        # 调用方法
        result = config_service.get_all_agent_configs()
        
        # 验证结果
        assert result == expected_configs
        mock_config_manager.get_all_agent_configs.assert_called_once()
    
    def test_get_enabled_agent_configs(self, config_service, mock_config_manager, sample_agent_config_data):
        """测试获取启用的智能体配置."""
        # 创建启用和禁用的配置
        enabled_config_data = sample_agent_config_data.copy()
        enabled_config_data["enabled"] = True
        
        disabled_config_data = sample_agent_config_data.copy()
        disabled_config_data["agent_id"] = "disabled_agent"
        disabled_config_data["enabled"] = False
        
        all_configs = {
            "test_agent": AgentConfig(**enabled_config_data),
            "disabled_agent": AgentConfig(**disabled_config_data)
        }
        
        mock_config_manager.get_all_agent_configs.return_value = all_configs
        
        # 调用方法
        result = config_service.get_enabled_agent_configs()
        
        # 验证结果
        assert len(result) == 1
        assert "test_agent" in result
        assert "disabled_agent" not in result
    
    def test_validate_agent_config_valid(self, config_service, mock_config_manager, sample_agent_config_data):
        """测试验证有效的智能体配置."""
        # 设置模拟返回值
        mock_config_manager.get_model_config.return_value = None
        
        # 调用方法
        result = config_service.validate_agent_config("test_agent", sample_agent_config_data)
        
        # 验证结果
        assert isinstance(result, ConfigValidationResult)
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_agent_config_invalid(self, config_service, mock_config_manager):
        """测试验证无效的智能体配置."""
        # 无效配置（缺少必需字段）
        invalid_config = {
            "agent_id": "test_agent"
            # 缺少其他必需字段
        }
        
        # 调用方法
        result = config_service.validate_agent_config("test_agent", invalid_config)
        
        # 验证结果
        assert isinstance(result, ConfigValidationResult)
        assert result.is_valid is False
        assert len(result.errors) > 0
    
    @patch.dict(os.environ, {}, clear=True)
    def test_validate_agent_config_missing_api_key(self, config_service, mock_config_manager, sample_agent_config_data):
        """测试验证缺少API密钥的智能体配置."""
        # 设置模拟返回值
        mock_config_manager.get_model_config.return_value = None
        
        # 调用方法
        result = config_service.validate_agent_config("test_agent", sample_agent_config_data)
        
        # 验证结果
        assert isinstance(result, ConfigValidationResult)
        assert result.is_valid is True  # 仍然有效，但有警告
        assert len(result.warnings) > 0
        assert any("OPENAI_API_KEY" in warning for warning in result.warnings)
    
    def test_validate_model_config_valid(self, config_service, sample_model_config_data):
        """测试验证有效的模型配置."""
        # 调用方法
        result = config_service.validate_model_config("test_model", sample_model_config_data)
        
        # 验证结果
        assert isinstance(result, ConfigValidationResult)
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_workflow_config_valid(self, config_service, mock_config_manager, sample_workflow_config_data, sample_agent_config_data):
        """测试验证有效的工作流配置."""
        # 设置模拟返回值
        mock_config_manager.get_all_agent_configs.return_value = {
            "test_agent": AgentConfig(**sample_agent_config_data)
        }
        
        # 调用方法
        result = config_service.validate_workflow_config("test_workflow", sample_workflow_config_data)
        
        # 验证结果
        assert isinstance(result, ConfigValidationResult)
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_workflow_config_missing_agent(self, config_service, mock_config_manager, sample_workflow_config_data):
        """测试验证引用不存在智能体的工作流配置."""
        # 设置模拟返回值（空的智能体配置）
        mock_config_manager.get_all_agent_configs.return_value = {}
        
        # 调用方法
        result = config_service.validate_workflow_config("test_workflow", sample_workflow_config_data)
        
        # 验证结果
        assert isinstance(result, ConfigValidationResult)
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any("test_agent" in error for error in result.errors)
    
    @pytest.mark.asyncio
    async def test_update_agent_config_success(self, config_service, mock_config_manager, sample_agent_config_data):
        """测试成功更新智能体配置."""
        # 设置模拟返回值
        mock_config_manager.get_model_config.return_value = None
        mock_config_manager.update_agent_config.return_value = None
        
        # 创建更新请求
        request = ConfigUpdateRequest(
            config_type="agent",
            config_id="test_agent",
            config_data=sample_agent_config_data
        )
        
        # 调用方法
        response = await config_service.update_agent_config(request)
        
        # 验证结果
        assert response.success is True
        assert "updated successfully" in response.message
        assert response.validation_result is not None
        assert response.updated_config is not None
        mock_config_manager.update_agent_config.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_agent_config_validation_only(self, config_service, mock_config_manager, sample_agent_config_data):
        """测试仅验证智能体配置."""
        # 设置模拟返回值
        mock_config_manager.get_model_config.return_value = None
        
        # 创建验证请求
        request = ConfigUpdateRequest(
            config_type="agent",
            config_id="test_agent",
            config_data=sample_agent_config_data,
            validate_only=True
        )
        
        # 调用方法
        response = await config_service.update_agent_config(request)
        
        # 验证结果
        assert response.success is True
        assert "validation completed" in response.message
        assert response.validation_result is not None
        mock_config_manager.update_agent_config.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_update_agent_config_validation_failed(self, config_service, mock_config_manager):
        """测试更新智能体配置验证失败."""
        # 无效配置
        invalid_config = {"agent_id": "test_agent"}
        
        # 创建更新请求
        request = ConfigUpdateRequest(
            config_type="agent",
            config_id="test_agent",
            config_data=invalid_config
        )
        
        # 调用方法
        response = await config_service.update_agent_config(request)
        
        # 验证结果
        assert response.success is False
        assert "validation failed" in response.message
        assert response.validation_result is not None
        assert not response.validation_result.is_valid
        mock_config_manager.update_agent_config.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_reload_configuration(self, config_service, mock_config_manager):
        """测试重新加载配置."""
        # 设置模拟返回值
        mock_config_manager.reload_config.return_value = None
        mock_config_manager.get_config_status.return_value = {"status": "ok"}
        
        # 调用方法
        result = await config_service.reload_configuration("agents")
        
        # 验证结果
        assert result["success"] is True
        assert "reloaded successfully" in result["message"]
        assert "status" in result
        mock_config_manager.reload_config.assert_called_once_with("agents")
    
    def test_get_configuration_status(self, config_service, mock_config_manager):
        """测试获取配置状态."""
        # 设置模拟返回值
        expected_status = {"status": "ok"}
        mock_config_manager.get_config_status.return_value = expected_status
        
        # 调用方法
        result = config_service.get_configuration_status()
        
        # 验证结果
        assert result == expected_status
        mock_config_manager.get_config_status.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_export_configuration(self, config_service, mock_config_manager):
        """测试导出配置."""
        # 设置模拟返回值
        mock_config_manager.export_config.return_value = None
        
        # 调用方法
        result = await config_service.export_configuration("/test/path.json", "agents")
        
        # 验证结果
        assert result["success"] is True
        assert "exported to" in result["message"]
        assert result["output_path"] == "/test/path.json"
        assert result["config_type"] == "agents"
        mock_config_manager.export_config.assert_called_once_with("/test/path.json", "agents")
    
    @patch.dict(os.environ, {
        "OPENAI_API_KEY": "sk-1234567890abcdef",
        "QWEN_API_KEY": "qwen-key-123",
        "API_HOST": "0.0.0.0",
        "API_PORT": "8000"
    })
    def test_get_environment_variables(self, config_service):
        """测试获取环境变量."""
        # 调用方法
        result = config_service.get_environment_variables()
        
        # 验证结果
        assert "OPENAI_API_KEY" in result
        assert "QWEN_API_KEY" in result
        assert "API_HOST" in result
        assert "API_PORT" in result
        
        # 验证敏感信息被隐藏
        assert result["OPENAI_API_KEY"] == "sk-1...cdef"
        assert result["QWEN_API_KEY"] == "qwen...123"
        
        # 验证非敏感信息正常显示
        assert result["API_HOST"] == "0.0.0.0"
        assert result["API_PORT"] == "8000"
    
    @patch.dict(os.environ, {}, clear=True)
    def test_validate_environment_missing_keys(self, config_service, mock_config_manager):
        """测试验证缺少环境变量的环境."""
        # 设置模拟返回值（启用的模型需要API密钥）
        mock_model_config = MagicMock()
        mock_model_config.provider.value = "OPENAI"
        mock_config_manager.get_enabled_model_configs.return_value = {
            "test_model": mock_model_config
        }
        
        # 调用方法
        result = config_service.validate_environment()
        
        # 验证结果
        assert isinstance(result, ConfigValidationResult)
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any("OPENAI_API_KEY" in error for error in result.errors)
    
    def test_validate_environment_missing_config_files(self, config_service, mock_config_manager):
        """测试验证缺少配置文件的环境."""
        # 设置模拟返回值
        mock_config_manager.get_enabled_model_configs.return_value = {}
        
        # 调用方法
        result = config_service.validate_environment()
        
        # 验证结果
        assert isinstance(result, ConfigValidationResult)
        # 可能有警告但仍然有效
        assert len(result.warnings) >= 0


class TestConfigServiceIntegration:
    """配置服务集成测试."""
    
    @pytest.fixture
    def real_config_setup(self, tmp_path):
        """真实配置设置."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        
        # 创建真实的配置文件
        agents_config = {
            "agents": {
                "sales_agent": {
                    "agent_id": "sales_agent",
                    "agent_type": "sales",
                    "name": "销售智能体",
                    "description": "销售专员",
                    "enabled": True,
                    "capabilities": ["sales"],
                    "llm_config": {
                        "provider": "openai",
                        "model_name": "gpt-3.5-turbo",
                        "api_key": "test_key",
                        "max_tokens": 2000,
                        "temperature": 0.7,
                        "timeout": 30,
                        "retry_attempts": 3
                    },
                    "prompt_template": "销售提示词",
                    "max_concurrent_tasks": 5,
                    "priority": 8
                }
            }
        }
        
        models_config = {
            "models": {
                "gpt35": {
                    "provider": "openai",
                    "model_name": "gpt-3.5-turbo",
                    "api_key": "test_key",
                    "max_tokens": 2000,
                    "temperature": 0.7,
                    "timeout": 30,
                    "retry_attempts": 3,
                    "enabled": True
                }
            }
        }
        
        # 保存配置文件
        with open(config_dir / "agents.json", 'w', encoding='utf-8') as f:
            json.dump(agents_config, f)
        
        with open(config_dir / "models.json", 'w', encoding='utf-8') as f:
            json.dump(models_config, f)
        
        return config_dir
    
    @pytest.mark.asyncio
    async def test_full_service_lifecycle(self, real_config_setup):
        """测试完整的服务生命周期."""
        # 创建真实的配置管理器和服务
        config_manager = ConfigManager(str(real_config_setup))
        config_service = ConfigService(config_manager)
        
        try:
            # 初始化服务
            await config_service.initialize()
            
            # 获取配置
            agent_config = config_service.get_agent_config("sales_agent")
            assert agent_config is not None
            assert agent_config.name == "销售智能体"
            
            # 获取所有配置
            all_agents = config_service.get_all_agent_configs()
            assert len(all_agents) == 1
            
            # 获取启用的配置
            enabled_agents = config_service.get_enabled_agent_configs()
            assert len(enabled_agents) == 1
            
            # 验证配置
            validation_result = config_service.validate_agent_config(
                "sales_agent", 
                agent_config.model_dump()
            )
            assert validation_result.is_valid
            
            # 获取状态
            status = config_service.get_configuration_status()
            assert status["agent_configs_count"] == 1
            
        finally:
            # 关闭服务
            await config_service.shutdown()
    
    @pytest.mark.asyncio
    async def test_configuration_update_integration(self, real_config_setup):
        """测试配置更新集成."""
        # 创建真实的配置管理器和服务
        config_manager = ConfigManager(str(real_config_setup))
        config_service = ConfigService(config_manager)
        
        try:
            await config_service.initialize()
            
            # 获取原始配置
            original_config = config_service.get_agent_config("sales_agent")
            assert original_config.name == "销售智能体"
            
            # 更新配置
            updated_data = original_config.model_dump()
            updated_data["name"] = "更新后的销售智能体"
            
            request = ConfigUpdateRequest(
                config_type="agent",
                config_id="sales_agent",
                config_data=updated_data
            )
            
            response = await config_service.update_agent_config(request)
            assert response.success is True
            
            # 验证更新
            updated_config = config_service.get_agent_config("sales_agent")
            assert updated_config.name == "更新后的销售智能体"
            
        finally:
            await config_service.shutdown()