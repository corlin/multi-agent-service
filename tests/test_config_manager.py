"""Tests for configuration manager."""

import json
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.multi_agent_service.config.config_manager import ConfigManager
from src.multi_agent_service.models.config import AgentConfig, ModelConfig, WorkflowConfig
from src.multi_agent_service.models.enums import AgentType, ModelProvider
from src.multi_agent_service.utils.exceptions import ConfigurationError


class TestConfigManager:
    """配置管理器测试类."""
    
    @pytest.fixture
    def temp_config_dir(self):
        """创建临时配置目录."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def sample_agent_config(self):
        """示例智能体配置."""
        return {
            "agents": {
                "test_agent": {
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
            }
        }
    
    @pytest.fixture
    def sample_model_config(self):
        """示例模型配置."""
        return {
            "models": {
                "test_model": {
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
    
    @pytest.fixture
    def sample_workflow_config(self):
        """示例工作流配置."""
        return {
            "workflows": {
                "test_workflow": {
                    "workflow_id": "test_workflow",
                    "name": "测试工作流",
                    "description": "用于测试的工作流",
                    "enabled": True,
                    "workflow_type": "sequential",
                    "participating_agents": ["test_agent"],
                    "timeout": 300
                }
            }
        }
    
    def test_config_manager_initialization(self, temp_config_dir):
        """测试配置管理器初始化."""
        config_manager = ConfigManager(str(temp_config_dir))
        
        assert config_manager.config_dir == temp_config_dir
        assert temp_config_dir.exists()
        assert config_manager._settings is not None
    
    def test_load_agent_config_json(self, temp_config_dir, sample_agent_config):
        """测试加载JSON格式的智能体配置."""
        # 创建配置文件
        config_file = temp_config_dir / "agents.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(sample_agent_config, f)
        
        config_manager = ConfigManager(str(temp_config_dir))
        
        # 验证配置加载
        agent_config = config_manager.get_agent_config("test_agent")
        assert agent_config is not None
        assert agent_config.agent_id == "test_agent"
        assert agent_config.agent_type == AgentType.SALES
        assert agent_config.name == "测试智能体"
    
    def test_load_model_config_json(self, temp_config_dir, sample_model_config):
        """测试加载JSON格式的模型配置."""
        # 创建配置文件
        config_file = temp_config_dir / "models.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(sample_model_config, f)
        
        config_manager = ConfigManager(str(temp_config_dir))
        
        # 验证配置加载
        model_config = config_manager.get_model_config("test_model")
        assert model_config is not None
        assert model_config.provider == ModelProvider.OPENAI
        assert model_config.model_name == "gpt-3.5-turbo"
    
    def test_load_workflow_config_json(self, temp_config_dir, sample_workflow_config):
        """测试加载JSON格式的工作流配置."""
        # 创建配置文件
        config_file = temp_config_dir / "workflows.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(sample_workflow_config, f)
        
        config_manager = ConfigManager(str(temp_config_dir))
        
        # 验证配置加载
        workflow_config = config_manager.get_workflow_config("test_workflow")
        assert workflow_config is not None
        assert workflow_config.workflow_id == "test_workflow"
        assert workflow_config.name == "测试工作流"
        assert workflow_config.workflow_type == "sequential"
    
    def test_apply_defaults(self, temp_config_dir):
        """测试默认值应用."""
        # 创建最小配置
        minimal_config = {
            "agents": {
                "minimal_agent": {
                    "agent_id": "minimal_agent",
                    "agent_type": "SALES",
                    "name": "最小配置智能体",
                    "description": "最小配置",
                    "llm_config": {
                        "provider": "OPENAI",
                        "model_name": "gpt-3.5-turbo",
                        "api_key": "test_key"
                    },
                    "prompt_template": "测试"
                }
            }
        }
        
        config_file = temp_config_dir / "agents.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(minimal_config, f)
        
        config_manager = ConfigManager(str(temp_config_dir))
        
        # 验证默认值应用
        agent_config = config_manager.get_agent_config("minimal_agent")
        assert agent_config.enabled is True  # 默认值
        assert agent_config.max_concurrent_tasks == 5  # 默认值
        assert agent_config.priority == 8  # 默认值
        assert agent_config.llm_config.max_tokens == 2000  # 默认值
    
    def test_config_validation_invalid_agent(self, temp_config_dir):
        """测试无效智能体配置验证."""
        invalid_config = {
            "agents": {
                "invalid_agent": {
                    "agent_id": "invalid_agent",
                    # 缺少必需字段
                }
            }
        }
        
        config_file = temp_config_dir / "agents.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(invalid_config, f)
        
        with pytest.raises(ConfigurationError):
            ConfigManager(str(temp_config_dir))
    
    def test_update_agent_config(self, temp_config_dir, sample_agent_config):
        """测试更新智能体配置."""
        # 创建初始配置
        config_file = temp_config_dir / "agents.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(sample_agent_config, f)
        
        config_manager = ConfigManager(str(temp_config_dir))
        
        # 更新配置
        updated_config_data = sample_agent_config["agents"]["test_agent"].copy()
        updated_config_data["name"] = "更新后的智能体"
        updated_config = AgentConfig(**updated_config_data)
        
        config_manager.update_agent_config("test_agent", updated_config)
        
        # 验证更新
        agent_config = config_manager.get_agent_config("test_agent")
        assert agent_config.name == "更新后的智能体"
        
        # 验证文件保存
        with open(config_file, 'r', encoding='utf-8') as f:
            saved_config = json.load(f)
        assert saved_config["agents"]["test_agent"]["name"] == "更新后的智能体"
    
    def test_reload_config(self, temp_config_dir, sample_agent_config):
        """测试配置重新加载."""
        # 创建初始配置
        config_file = temp_config_dir / "agents.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(sample_agent_config, f)
        
        config_manager = ConfigManager(str(temp_config_dir))
        
        # 验证初始配置
        agent_config = config_manager.get_agent_config("test_agent")
        assert agent_config.name == "测试智能体"
        
        # 修改配置文件
        updated_config = sample_agent_config.copy()
        updated_config["agents"]["test_agent"]["name"] = "外部修改的智能体"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(updated_config, f)
        
        # 重新加载配置
        config_manager.reload_config("agents")
        
        # 验证配置更新
        agent_config = config_manager.get_agent_config("test_agent")
        assert agent_config.name == "外部修改的智能体"
    
    def test_get_all_configs(self, temp_config_dir, sample_agent_config, sample_model_config):
        """测试获取所有配置."""
        # 创建配置文件
        agents_file = temp_config_dir / "agents.json"
        with open(agents_file, 'w', encoding='utf-8') as f:
            json.dump(sample_agent_config, f)
        
        models_file = temp_config_dir / "models.json"
        with open(models_file, 'w', encoding='utf-8') as f:
            json.dump(sample_model_config, f)
        
        config_manager = ConfigManager(str(temp_config_dir))
        
        # 验证获取所有配置
        all_agents = config_manager.get_all_agent_configs()
        assert len(all_agents) == 1
        assert "test_agent" in all_agents
        
        all_models = config_manager.get_all_model_configs()
        assert len(all_models) == 1
        assert "test_model" in all_models
    
    def test_config_status(self, temp_config_dir):
        """测试配置状态获取."""
        config_manager = ConfigManager(str(temp_config_dir))
        
        status = config_manager.get_config_status()
        
        assert "last_reload_time" in status
        assert "agent_configs_count" in status
        assert "model_configs_count" in status
        assert "workflow_configs_count" in status
        assert "file_watching_active" in status
        assert "config_directory" in status
        assert "settings_loaded" in status
        
        assert status["config_directory"] == str(temp_config_dir)
        assert status["settings_loaded"] is True
    
    def test_export_config(self, temp_config_dir, sample_agent_config):
        """测试配置导出."""
        # 创建配置
        config_file = temp_config_dir / "agents.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(sample_agent_config, f)
        
        config_manager = ConfigManager(str(temp_config_dir))
        
        # 导出配置
        export_file = temp_config_dir / "exported_config.json"
        config_manager.export_config(str(export_file), "agents")
        
        # 验证导出文件
        assert export_file.exists()
        with open(export_file, 'r', encoding='utf-8') as f:
            exported_data = json.load(f)
        
        assert "agents" in exported_data
        assert "test_agent" in exported_data["agents"]
    
    def test_file_watching(self, temp_config_dir):
        """测试文件监控功能."""
        config_manager = ConfigManager(str(temp_config_dir))
        
        # 启动文件监控
        config_manager.start_file_watching()
        assert len(config_manager._observers) > 0
        
        # 停止文件监控
        config_manager.stop_file_watching()
        assert len(config_manager._observers) == 0
    
    def test_context_manager(self, temp_config_dir):
        """测试上下文管理器."""
        with ConfigManager(str(temp_config_dir)) as config_manager:
            assert config_manager is not None
            # 在上下文中使用配置管理器
            status = config_manager.get_config_status()
            assert status is not None
        
        # 上下文退出后，文件监控应该停止
        assert len(config_manager._observers) == 0
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    def test_environment_variable_integration(self, temp_config_dir):
        """测试环境变量集成."""
        config_manager = ConfigManager(str(temp_config_dir))
        settings = config_manager.get_settings()
        
        assert settings.openai_api_key == "test_key"
    
    def test_invalid_config_file_format(self, temp_config_dir):
        """测试无效配置文件格式处理."""
        # 创建无效JSON文件
        config_file = temp_config_dir / "agents.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write("invalid json content")
        
        with pytest.raises(ConfigurationError):
            ConfigManager(str(temp_config_dir))
    
    def test_missing_config_file(self, temp_config_dir):
        """测试缺失配置文件处理."""
        # 不创建任何配置文件
        config_manager = ConfigManager(str(temp_config_dir))
        
        # 应该能正常初始化，但没有配置
        assert len(config_manager.get_all_agent_configs()) == 0
        assert len(config_manager.get_all_model_configs()) == 0
        assert len(config_manager.get_all_workflow_configs()) == 0


class TestConfigManagerIntegration:
    """配置管理器集成测试."""
    
    @pytest.fixture
    def full_config_setup(self, tmp_path):
        """完整配置设置."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        
        # 创建完整的配置文件
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
                },
                "support_agent": {
                    "agent_id": "support_agent",
                    "agent_type": "customer_support",
                    "name": "客服智能体",
                    "description": "客服专员",
                    "enabled": True,
                    "capabilities": ["support"],
                    "llm_config": {
                        "provider": "qwen",
                        "model_name": "qwen-turbo",
                        "api_key": "test_key",
                        "max_tokens": 1500,
                        "temperature": 0.6,
                        "timeout": 25,
                        "retry_attempts": 3
                    },
                    "prompt_template": "客服提示词",
                    "max_concurrent_tasks": 8,
                    "priority": 9
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
                },
                "qwen_turbo": {
                    "provider": "qwen",
                    "model_name": "qwen-turbo",
                    "api_key": "test_key",
                    "max_tokens": 1500,
                    "temperature": 0.6,
                    "timeout": 25,
                    "retry_attempts": 3,
                    "enabled": True
                }
            }
        }
        
        workflows_config = {
            "workflows": {
                "sales_workflow": {
                    "workflow_id": "sales_workflow",
                    "name": "销售工作流",
                    "description": "销售流程",
                    "enabled": True,
                    "workflow_type": "sequential",
                    "participating_agents": ["sales_agent", "support_agent"],
                    "execution_order": ["sales_agent", "support_agent"],
                    "timeout": 600
                }
            }
        }
        
        # 保存配置文件
        with open(config_dir / "agents.json", 'w', encoding='utf-8') as f:
            json.dump(agents_config, f)
        
        with open(config_dir / "models.json", 'w', encoding='utf-8') as f:
            json.dump(models_config, f)
        
        with open(config_dir / "workflows.json", 'w', encoding='utf-8') as f:
            json.dump(workflows_config, f)
        
        return config_dir
    
    def test_full_configuration_loading(self, full_config_setup):
        """测试完整配置加载."""
        config_manager = ConfigManager(str(full_config_setup))
        
        # 验证智能体配置
        agents = config_manager.get_all_agent_configs()
        assert len(agents) == 2
        assert "sales_agent" in agents
        assert "support_agent" in agents
        
        # 验证模型配置
        models = config_manager.get_all_model_configs()
        assert len(models) == 2
        assert "gpt35" in models
        assert "qwen_turbo" in models
        
        # 验证工作流配置
        workflows = config_manager.get_all_workflow_configs()
        assert len(workflows) == 1
        assert "sales_workflow" in workflows
        
        # 验证工作流引用的智能体存在
        workflow = workflows["sales_workflow"]
        for agent_id in workflow.participating_agents:
            assert agent_id in agents
    
    def test_configuration_cross_references(self, full_config_setup):
        """测试配置间的交叉引用."""
        config_manager = ConfigManager(str(full_config_setup))
        
        # 获取工作流配置
        workflow = config_manager.get_workflow_config("sales_workflow")
        assert workflow is not None
        
        # 验证工作流中引用的智能体都存在
        for agent_id in workflow.participating_agents:
            agent = config_manager.get_agent_config(agent_id)
            assert agent is not None
            assert agent.enabled is True
        
        # 验证执行顺序中的智能体都在参与列表中
        for agent_id in workflow.execution_order:
            assert agent_id in workflow.participating_agents