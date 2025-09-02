"""Tests for hot reload service."""

import asyncio
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

from src.multi_agent_service.services.hot_reload_service import (
    HotReloadService, ConfigChangeEvent, ConfigChangeHandler
)
from src.multi_agent_service.config.config_manager import ConfigManager
from src.multi_agent_service.models.config import AgentConfig, ModelConfig, WorkflowConfig


class TestConfigChangeEvent:
    """配置变更事件测试类."""
    
    def test_config_change_event_creation(self):
        """测试配置变更事件创建."""
        event = ConfigChangeEvent(
            config_type="agent",
            config_id="test_agent",
            change_type="created",
            new_config={"name": "Test Agent"}
        )
        
        assert event.config_type == "agent"
        assert event.config_id == "test_agent"
        assert event.change_type == "created"
        assert event.new_config == {"name": "Test Agent"}
        assert event.old_config is None
        assert event.timestamp is not None
    
    def test_config_change_event_str(self):
        """测试配置变更事件字符串表示."""
        event = ConfigChangeEvent(
            config_type="model",
            config_id="test_model",
            change_type="updated"
        )
        
        expected_str = "ConfigChangeEvent(model.test_model: updated)"
        assert str(event) == expected_str


class MockConfigChangeHandler(ConfigChangeHandler):
    """模拟配置变更处理器."""
    
    def __init__(self):
        self.agent_changes = []
        self.model_changes = []
        self.workflow_changes = []
    
    async def handle_agent_config_change(self, event: ConfigChangeEvent) -> None:
        """处理智能体配置变更."""
        self.agent_changes.append(event)
    
    async def handle_model_config_change(self, event: ConfigChangeEvent) -> None:
        """处理模型配置变更."""
        self.model_changes.append(event)
    
    async def handle_workflow_config_change(self, event: ConfigChangeEvent) -> None:
        """处理工作流配置变更."""
        self.workflow_changes.append(event)


class TestHotReloadService:
    """热重载服务测试类."""
    
    @pytest.fixture
    def temp_config_dir(self):
        """创建临时配置目录."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def mock_config_manager(self, temp_config_dir):
        """模拟配置管理器."""
        return ConfigManager(str(temp_config_dir))
    
    @pytest.fixture
    def hot_reload_service(self, mock_config_manager):
        """热重载服务实例."""
        return HotReloadService(mock_config_manager)
    
    @pytest.fixture
    def sample_agent_config(self):
        """示例智能体配置."""
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
    
    def test_hot_reload_service_initialization(self, hot_reload_service):
        """测试热重载服务初始化."""
        assert hot_reload_service.config_manager is not None
        assert len(hot_reload_service._handlers) == 0
        assert not hot_reload_service._is_running
        assert hot_reload_service._change_queue is not None
    
    def test_add_remove_handler(self, hot_reload_service):
        """测试添加和移除处理器."""
        handler = MockConfigChangeHandler()
        
        # 添加处理器
        hot_reload_service.add_handler(handler)
        assert len(hot_reload_service._handlers) == 1
        assert handler in hot_reload_service._handlers
        
        # 移除处理器
        hot_reload_service.remove_handler(handler)
        assert len(hot_reload_service._handlers) == 0
        assert handler not in hot_reload_service._handlers
    
    def test_add_remove_change_listener(self, hot_reload_service):
        """测试添加和移除变更监听器."""
        def mock_listener(event):
            pass
        
        # 添加监听器
        hot_reload_service.add_change_listener("agent", mock_listener)
        assert len(hot_reload_service._change_listeners["agent"]) == 1
        assert mock_listener in hot_reload_service._change_listeners["agent"]
        
        # 移除监听器
        hot_reload_service.remove_change_listener("agent", mock_listener)
        assert len(hot_reload_service._change_listeners["agent"]) == 0
        assert mock_listener not in hot_reload_service._change_listeners["agent"]
    
    @pytest.mark.asyncio
    async def test_start_stop_service(self, hot_reload_service):
        """测试启动和停止服务."""
        # 启动服务
        await hot_reload_service.start()
        assert hot_reload_service._is_running is True
        assert hot_reload_service._processing_task is not None
        
        # 停止服务
        await hot_reload_service.stop()
        assert hot_reload_service._is_running is False
    
    @pytest.mark.asyncio
    async def test_apply_config_change_agent(self, hot_reload_service, sample_agent_config):
        """测试应用智能体配置变更."""
        # 应用配置变更
        result = await hot_reload_service.apply_config_change(
            config_type="agent",
            config_id="test_agent",
            config_data=sample_agent_config,
            hot_reload=False  # 不触发热重载事件
        )
        
        # 验证结果
        assert result["success"] is True
        assert "applied" in result["message"]
        assert result["change_type"] == "created"
        
        # 验证配置已保存
        agent_config = hot_reload_service.config_manager.get_agent_config("test_agent")
        assert agent_config is not None
        assert agent_config.name == "测试智能体"
    
    @pytest.mark.asyncio
    async def test_apply_config_change_with_hot_reload(self, hot_reload_service, sample_agent_config):
        """测试带热重载的配置变更."""
        handler = MockConfigChangeHandler()
        hot_reload_service.add_handler(handler)
        
        # 启动服务
        await hot_reload_service.start()
        
        try:
            # 应用配置变更
            result = await hot_reload_service.apply_config_change(
                config_type="agent",
                config_id="test_agent",
                config_data=sample_agent_config,
                hot_reload=True
            )
            
            # 等待事件处理
            await asyncio.sleep(0.1)
            
            # 验证结果
            assert result["success"] is True
            assert result["hot_reload"] is True
            
            # 验证处理器收到事件
            assert len(handler.agent_changes) == 1
            event = handler.agent_changes[0]
            assert event.config_type == "agent"
            assert event.config_id == "test_agent"
            assert event.change_type == "created"
            
        finally:
            await hot_reload_service.stop()
    
    @pytest.mark.asyncio
    async def test_remove_config(self, hot_reload_service, sample_agent_config):
        """测试移除配置."""
        # 先添加配置
        await hot_reload_service.apply_config_change(
            config_type="agent",
            config_id="test_agent",
            config_data=sample_agent_config,
            hot_reload=False
        )
        
        # 移除配置
        result = await hot_reload_service.remove_config(
            config_type="agent",
            config_id="test_agent",
            hot_reload=False
        )
        
        # 验证结果
        assert result["success"] is True
        assert result["change_type"] == "deleted"
        
        # 验证配置已禁用
        agent_config = hot_reload_service.config_manager.get_agent_config("test_agent")
        assert agent_config is not None
        assert agent_config.enabled is False
    
    @pytest.mark.asyncio
    async def test_reload_config(self, hot_reload_service, temp_config_dir, sample_agent_config):
        """测试重新加载配置."""
        # 创建配置文件
        config_file = temp_config_dir / "agents.json"
        config_data = {"agents": {"test_agent": sample_agent_config}}
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        # 重新加载配置
        result = await hot_reload_service.reload_config("agents")
        
        # 验证结果
        assert result["success"] is True
        assert "reloaded" in result["message"]
        
        # 验证配置已加载
        agent_config = hot_reload_service.config_manager.get_agent_config("test_agent")
        assert agent_config is not None
        assert agent_config.name == "测试智能体"
    
    @pytest.mark.asyncio
    async def test_detect_agent_changes(self, hot_reload_service, sample_agent_config):
        """测试检测智能体配置变更."""
        # 创建初始配置
        initial_config = AgentConfig(**sample_agent_config)
        hot_reload_service.config_manager.update_agent_config("test_agent", initial_config)
        hot_reload_service._update_snapshots()
        
        # 保存旧快照
        old_snapshot = hot_reload_service._agent_config_snapshot.copy()
        
        # 修改配置
        updated_config_data = sample_agent_config.copy()
        updated_config_data["name"] = "更新后的智能体"
        updated_config = AgentConfig(**updated_config_data)
        hot_reload_service.config_manager.update_agent_config("test_agent", updated_config)
        hot_reload_service._update_snapshots()
        
        # 检测变更
        changes = await hot_reload_service._detect_agent_changes(old_snapshot)
        
        # 验证变更
        assert len(changes) == 1
        change = changes[0]
        assert change.config_type == "agent"
        assert change.config_id == "test_agent"
        assert change.change_type == "updated"
        assert change.old_config["name"] == "测试智能体"
        assert change.new_config["name"] == "更新后的智能体"
    
    @pytest.mark.asyncio
    async def test_detect_new_agent(self, hot_reload_service, sample_agent_config):
        """测试检测新增智能体."""
        # 保存空快照
        old_snapshot = {}
        
        # 添加新配置
        new_config = AgentConfig(**sample_agent_config)
        hot_reload_service.config_manager.update_agent_config("test_agent", new_config)
        hot_reload_service._update_snapshots()
        
        # 检测变更
        changes = await hot_reload_service._detect_agent_changes(old_snapshot)
        
        # 验证变更
        assert len(changes) == 1
        change = changes[0]
        assert change.config_type == "agent"
        assert change.config_id == "test_agent"
        assert change.change_type == "created"
        assert change.old_config is None
        assert change.new_config is not None
    
    @pytest.mark.asyncio
    async def test_detect_deleted_agent(self, hot_reload_service, sample_agent_config):
        """测试检测删除的智能体."""
        # 创建初始配置和快照
        initial_config = AgentConfig(**sample_agent_config)
        hot_reload_service.config_manager.update_agent_config("test_agent", initial_config)
        hot_reload_service._update_snapshots()
        old_snapshot = hot_reload_service._agent_config_snapshot.copy()
        
        # 清空配置
        hot_reload_service.config_manager._agent_configs.clear()
        hot_reload_service._update_snapshots()
        
        # 检测变更
        changes = await hot_reload_service._detect_agent_changes(old_snapshot)
        
        # 验证变更
        assert len(changes) == 1
        change = changes[0]
        assert change.config_type == "agent"
        assert change.config_id == "test_agent"
        assert change.change_type == "deleted"
        assert change.old_config is not None
        assert change.new_config is None
    
    def test_get_status(self, hot_reload_service):
        """测试获取服务状态."""
        handler = MockConfigChangeHandler()
        hot_reload_service.add_handler(handler)
        
        status = hot_reload_service.get_status()
        
        assert "is_running" in status
        assert "handlers_count" in status
        assert "change_listeners_count" in status
        assert "queue_size" in status
        assert "config_snapshots" in status
        
        assert status["handlers_count"] == 1
        assert status["is_running"] is False
    
    @pytest.mark.asyncio
    async def test_change_listener_notification(self, hot_reload_service, sample_agent_config):
        """测试变更监听器通知."""
        # 添加监听器
        received_events = []
        
        def listener(event):
            received_events.append(event)
        
        hot_reload_service.add_change_listener("agent", listener)
        
        # 启动服务
        await hot_reload_service.start()
        
        try:
            # 应用配置变更
            await hot_reload_service.apply_config_change(
                config_type="agent",
                config_id="test_agent",
                config_data=sample_agent_config,
                hot_reload=True
            )
            
            # 等待事件处理
            await asyncio.sleep(0.1)
            
            # 验证监听器收到事件
            assert len(received_events) == 1
            event = received_events[0]
            assert event.config_type == "agent"
            assert event.config_id == "test_agent"
            
        finally:
            await hot_reload_service.stop()
    
    @pytest.mark.asyncio
    async def test_async_change_listener(self, hot_reload_service, sample_agent_config):
        """测试异步变更监听器."""
        # 添加异步监听器
        received_events = []
        
        async def async_listener(event):
            received_events.append(event)
        
        hot_reload_service.add_change_listener("agent", async_listener)
        
        # 启动服务
        await hot_reload_service.start()
        
        try:
            # 应用配置变更
            await hot_reload_service.apply_config_change(
                config_type="agent",
                config_id="test_agent",
                config_data=sample_agent_config,
                hot_reload=True
            )
            
            # 等待事件处理
            await asyncio.sleep(0.1)
            
            # 验证异步监听器收到事件
            assert len(received_events) == 1
            event = received_events[0]
            assert event.config_type == "agent"
            assert event.config_id == "test_agent"
            
        finally:
            await hot_reload_service.stop()


class TestHotReloadServiceIntegration:
    """热重载服务集成测试."""
    
    @pytest.fixture
    def real_config_setup(self, tmp_path):
        """真实配置设置."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        
        # 创建初始配置文件
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
        
        with open(config_dir / "agents.json", 'w', encoding='utf-8') as f:
            json.dump(agents_config, f)
        
        return config_dir
    
    @pytest.mark.asyncio
    async def test_full_hot_reload_cycle(self, real_config_setup):
        """测试完整的热重载周期."""
        # 创建真实的配置管理器和热重载服务
        config_manager = ConfigManager(str(real_config_setup))
        hot_reload_service = HotReloadService(config_manager)
        
        # 添加处理器
        handler = MockConfigChangeHandler()
        hot_reload_service.add_handler(handler)
        
        try:
            # 启动服务
            await hot_reload_service.start()
            
            # 验证初始配置
            agent_config = config_manager.get_agent_config("sales_agent")
            assert agent_config is not None
            assert agent_config.name == "销售智能体"
            
            # 应用配置变更
            updated_config = agent_config.model_dump()
            updated_config["name"] = "更新后的销售智能体"
            
            result = await hot_reload_service.apply_config_change(
                config_type="agent",
                config_id="sales_agent",
                config_data=updated_config,
                hot_reload=True
            )
            
            # 等待事件处理
            await asyncio.sleep(0.2)
            
            # 验证结果
            assert result["success"] is True
            
            # 验证配置已更新
            updated_agent_config = config_manager.get_agent_config("sales_agent")
            assert updated_agent_config.name == "更新后的销售智能体"
            
            # 验证处理器收到事件
            assert len(handler.agent_changes) == 1
            event = handler.agent_changes[0]
            assert event.change_type == "updated"
            assert event.old_config["name"] == "销售智能体"
            assert event.new_config["name"] == "更新后的销售智能体"
            
        finally:
            await hot_reload_service.stop()
    
    @pytest.mark.asyncio
    async def test_file_based_hot_reload(self, real_config_setup):
        """测试基于文件的热重载."""
        # 创建真实的配置管理器和热重载服务
        config_manager = ConfigManager(str(real_config_setup))
        hot_reload_service = HotReloadService(config_manager)
        
        # 添加处理器
        handler = MockConfigChangeHandler()
        hot_reload_service.add_handler(handler)
        
        try:
            # 启动服务
            await hot_reload_service.start()
            
            # 修改配置文件
            config_file = real_config_setup / "agents.json"
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            config_data["agents"]["sales_agent"]["name"] = "文件修改后的智能体"
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f)
            
            # 手动触发重新加载
            result = await hot_reload_service.reload_config("agents")
            
            # 等待事件处理
            await asyncio.sleep(0.2)
            
            # 验证结果
            assert result["success"] is True
            
            # 验证配置已更新
            updated_agent_config = config_manager.get_agent_config("sales_agent")
            assert updated_agent_config.name == "文件修改后的智能体"
            
        finally:
            await hot_reload_service.stop()