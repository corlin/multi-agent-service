"""Tests for agent hot reload handler."""

import pytest
from unittest.mock import MagicMock, AsyncMock

from src.multi_agent_service.services.agent_hot_reload_handler import AgentHotReloadHandler
from src.multi_agent_service.services.hot_reload_service import ConfigChangeEvent


class MockAgent:
    """模拟智能体."""
    
    def __init__(self, agent_id: str, config: dict):
        self.agent_id = agent_id
        self.config = MagicMock()
        self.config.llm_config.model_name = config.get("llm_config", {}).get("model_name", "default")
        self._stopped = False
    
    async def update_config(self, config: dict) -> None:
        """更新配置."""
        pass
    
    async def update_model_config(self, model_config: dict) -> None:
        """更新模型配置."""
        pass
    
    async def set_fallback_model(self) -> None:
        """设置备用模型."""
        pass
    
    async def stop(self) -> None:
        """停止智能体."""
        self._stopped = True


class MockWorkflow:
    """模拟工作流."""
    
    def __init__(self, workflow_id: str, config: dict):
        self.workflow_id = workflow_id
        self.config = config
        self._stopped = False
    
    async def update_config(self, config: dict) -> None:
        """更新配置."""
        pass
    
    async def stop(self) -> None:
        """停止工作流."""
        self._stopped = True


class MockAgentRegistry:
    """模拟智能体注册表."""
    
    def __init__(self):
        self.agents = {}
    
    async def create_agent(self, agent_id: str, config: dict) -> MockAgent:
        """创建智能体."""
        agent = MockAgent(agent_id, config)
        self.agents[agent_id] = agent
        return agent
    
    async def unregister_agent(self, agent_id: str) -> None:
        """注销智能体."""
        if agent_id in self.agents:
            del self.agents[agent_id]


class MockGraphBuilder:
    """模拟图构建器."""
    
    def __init__(self):
        self.workflows = {}
    
    async def create_workflow(self, workflow_id: str, config: dict) -> MockWorkflow:
        """创建工作流."""
        workflow = MockWorkflow(workflow_id, config)
        self.workflows[workflow_id] = workflow
        return workflow


class TestAgentHotReloadHandler:
    """智能体热重载处理器测试类."""
    
    @pytest.fixture
    def mock_agent_registry(self):
        """模拟智能体注册表."""
        return MockAgentRegistry()
    
    @pytest.fixture
    def mock_graph_builder(self):
        """模拟图构建器."""
        return MockGraphBuilder()
    
    @pytest.fixture
    def handler(self, mock_agent_registry, mock_graph_builder):
        """智能体热重载处理器实例."""
        return AgentHotReloadHandler(mock_agent_registry, mock_graph_builder)
    
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
    
    @pytest.fixture
    def sample_workflow_config(self):
        """示例工作流配置."""
        return {
            "workflow_id": "test_workflow",
            "name": "测试工作流",
            "description": "用于测试的工作流",
            "enabled": True,
            "workflow_type": "sequential",
            "participating_agents": ["test_agent"],
            "timeout": 300
        }
    
    def test_handler_initialization(self, handler, mock_agent_registry, mock_graph_builder):
        """测试处理器初始化."""
        assert handler.agent_registry == mock_agent_registry
        assert handler.graph_builder == mock_graph_builder
        assert len(handler._active_agents) == 0
        assert len(handler._active_workflows) == 0
    
    @pytest.mark.asyncio
    async def test_handle_agent_config_created(self, handler, sample_agent_config):
        """测试处理智能体配置创建事件."""
        event = ConfigChangeEvent(
            config_type="agent",
            config_id="test_agent",
            change_type="created",
            new_config=sample_agent_config
        )
        
        await handler.handle_agent_config_change(event)
        
        # 验证智能体已创建
        assert "test_agent" in handler._active_agents
        assert len(handler._active_agents) == 1
        
        # 验证注册表中有智能体
        assert "test_agent" in handler.agent_registry.agents
    
    @pytest.mark.asyncio
    async def test_handle_agent_config_created_disabled(self, handler, sample_agent_config):
        """测试处理禁用智能体配置创建事件."""
        # 设置为禁用状态
        sample_agent_config["enabled"] = False
        
        event = ConfigChangeEvent(
            config_type="agent",
            config_id="test_agent",
            change_type="created",
            new_config=sample_agent_config
        )
        
        await handler.handle_agent_config_change(event)
        
        # 验证智能体未创建
        assert "test_agent" not in handler._active_agents
        assert len(handler._active_agents) == 0
    
    @pytest.mark.asyncio
    async def test_handle_agent_config_updated(self, handler, sample_agent_config):
        """测试处理智能体配置更新事件."""
        # 先创建智能体
        create_event = ConfigChangeEvent(
            config_type="agent",
            config_id="test_agent",
            change_type="created",
            new_config=sample_agent_config
        )
        await handler.handle_agent_config_change(create_event)
        
        # 更新配置
        updated_config = sample_agent_config.copy()
        updated_config["name"] = "更新后的智能体"
        
        update_event = ConfigChangeEvent(
            config_type="agent",
            config_id="test_agent",
            change_type="updated",
            old_config=sample_agent_config,
            new_config=updated_config
        )
        
        await handler.handle_agent_config_change(update_event)
        
        # 验证智能体仍然存在
        assert "test_agent" in handler._active_agents
        assert len(handler._active_agents) == 1
    
    @pytest.mark.asyncio
    async def test_handle_agent_config_deleted(self, handler, sample_agent_config):
        """测试处理智能体配置删除事件."""
        # 先创建智能体
        create_event = ConfigChangeEvent(
            config_type="agent",
            config_id="test_agent",
            change_type="created",
            new_config=sample_agent_config
        )
        await handler.handle_agent_config_change(create_event)
        
        # 验证智能体已创建
        assert "test_agent" in handler._active_agents
        
        # 删除配置
        delete_event = ConfigChangeEvent(
            config_type="agent",
            config_id="test_agent",
            change_type="deleted",
            old_config=sample_agent_config
        )
        
        await handler.handle_agent_config_change(delete_event)
        
        # 验证智能体已删除
        assert "test_agent" not in handler._active_agents
        assert len(handler._active_agents) == 0
        
        # 验证注册表中智能体已移除
        assert "test_agent" not in handler.agent_registry.agents
    
    @pytest.mark.asyncio
    async def test_handle_workflow_config_created(self, handler, sample_workflow_config):
        """测试处理工作流配置创建事件."""
        event = ConfigChangeEvent(
            config_type="workflow",
            config_id="test_workflow",
            change_type="created",
            new_config=sample_workflow_config
        )
        
        await handler.handle_workflow_config_change(event)
        
        # 验证工作流已创建
        assert "test_workflow" in handler._active_workflows
        assert len(handler._active_workflows) == 1
        
        # 验证图构建器中有工作流
        assert "test_workflow" in handler.graph_builder.workflows
    
    @pytest.mark.asyncio
    async def test_handle_workflow_config_deleted(self, handler, sample_workflow_config):
        """测试处理工作流配置删除事件."""
        # 先创建工作流
        create_event = ConfigChangeEvent(
            config_type="workflow",
            config_id="test_workflow",
            change_type="created",
            new_config=sample_workflow_config
        )
        await handler.handle_workflow_config_change(create_event)
        
        # 验证工作流已创建
        assert "test_workflow" in handler._active_workflows
        
        # 删除配置
        delete_event = ConfigChangeEvent(
            config_type="workflow",
            config_id="test_workflow",
            change_type="deleted",
            old_config=sample_workflow_config
        )
        
        await handler.handle_workflow_config_change(delete_event)
        
        # 验证工作流已删除
        assert "test_workflow" not in handler._active_workflows
        assert len(handler._active_workflows) == 0
    
    def test_needs_agent_recreation_agent_type_change(self, handler):
        """测试智能体类型变更需要重新创建."""
        old_config = {"agent_type": "sales", "enabled": True}
        new_config = {"agent_type": "customer_support", "enabled": True}
        
        result = handler._needs_agent_recreation(old_config, new_config)
        assert result is True
    
    def test_needs_agent_recreation_model_change(self, handler):
        """测试模型变更需要重新创建."""
        old_config = {
            "agent_type": "sales",
            "enabled": True,
            "llm_config": {"provider": "openai", "model_name": "gpt-3.5-turbo"}
        }
        new_config = {
            "agent_type": "sales",
            "enabled": True,
            "llm_config": {"provider": "openai", "model_name": "gpt-4"}
        }
        
        result = handler._needs_agent_recreation(old_config, new_config)
        assert result is True
    
    def test_needs_agent_recreation_enabled_change(self, handler):
        """测试启用状态变更需要重新创建."""
        old_config = {"agent_type": "sales", "enabled": True}
        new_config = {"agent_type": "sales", "enabled": False}
        
        result = handler._needs_agent_recreation(old_config, new_config)
        assert result is True
    
    def test_needs_agent_recreation_minor_change(self, handler):
        """测试小的变更不需要重新创建."""
        old_config = {
            "agent_type": "sales",
            "enabled": True,
            "name": "旧名称",
            "llm_config": {"provider": "openai", "model_name": "gpt-3.5-turbo"}
        }
        new_config = {
            "agent_type": "sales",
            "enabled": True,
            "name": "新名称",
            "llm_config": {"provider": "openai", "model_name": "gpt-3.5-turbo"}
        }
        
        result = handler._needs_agent_recreation(old_config, new_config)
        assert result is False
    
    def test_needs_workflow_recreation_type_change(self, handler):
        """测试工作流类型变更需要重新创建."""
        old_config = {"workflow_type": "sequential", "enabled": True}
        new_config = {"workflow_type": "parallel", "enabled": True}
        
        result = handler._needs_workflow_recreation(old_config, new_config)
        assert result is True
    
    def test_needs_workflow_recreation_agents_change(self, handler):
        """测试参与智能体变更需要重新创建."""
        old_config = {
            "workflow_type": "sequential",
            "enabled": True,
            "participating_agents": ["agent1", "agent2"]
        }
        new_config = {
            "workflow_type": "sequential",
            "enabled": True,
            "participating_agents": ["agent1", "agent3"]
        }
        
        result = handler._needs_workflow_recreation(old_config, new_config)
        assert result is True
    
    def test_get_nested_value(self, handler):
        """测试获取嵌套字段值."""
        config = {
            "llm_config": {
                "provider": "openai",
                "model_name": "gpt-3.5-turbo"
            }
        }
        
        # 测试存在的嵌套字段
        result = handler._get_nested_value(config, "llm_config.provider")
        assert result == "openai"
        
        # 测试不存在的字段
        result = handler._get_nested_value(config, "llm_config.nonexistent")
        assert result is None
        
        # 测试顶级字段
        result = handler._get_nested_value(config, "llm_config")
        assert result == config["llm_config"]
    
    def test_find_agents_using_model(self, handler, sample_agent_config):
        """测试查找使用指定模型的智能体."""
        # 创建模拟智能体
        agent = MockAgent("test_agent", sample_agent_config)
        handler._active_agents["test_agent"] = agent
        
        # 查找使用指定模型的智能体
        result = handler._find_agents_using_model("gpt-3.5-turbo")
        assert "test_agent" in result
        
        # 查找不存在的模型
        result = handler._find_agents_using_model("nonexistent-model")
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_handle_model_config_change_update(self, handler, sample_agent_config):
        """测试处理模型配置更新事件."""
        # 创建使用该模型的智能体
        agent = MockAgent("test_agent", sample_agent_config)
        handler._active_agents["test_agent"] = agent
        
        # 模拟模型配置更新事件
        model_config = {
            "provider": "openai",
            "model_name": "gpt-3.5-turbo",
            "temperature": 0.8  # 更新温度参数
        }
        
        event = ConfigChangeEvent(
            config_type="model",
            config_id="gpt-3.5-turbo",
            change_type="updated",
            new_config=model_config
        )
        
        await handler.handle_model_config_change(event)
        
        # 验证没有异常抛出（实际的更新逻辑在模拟对象中）
        assert True
    
    @pytest.mark.asyncio
    async def test_handle_model_config_change_deleted(self, handler, sample_agent_config):
        """测试处理模型配置删除事件."""
        # 创建使用该模型的智能体
        agent = MockAgent("test_agent", sample_agent_config)
        handler._active_agents["test_agent"] = agent
        
        # 模拟模型配置删除事件
        event = ConfigChangeEvent(
            config_type="model",
            config_id="gpt-3.5-turbo",
            change_type="deleted",
            old_config={"model_name": "gpt-3.5-turbo"}
        )
        
        await handler.handle_model_config_change(event)
        
        # 验证没有异常抛出
        assert True
    
    def test_get_active_agents(self, handler, sample_agent_config):
        """测试获取活跃智能体列表."""
        # 添加智能体
        agent = MockAgent("test_agent", sample_agent_config)
        handler._active_agents["test_agent"] = agent
        
        # 获取活跃智能体
        active_agents = handler.get_active_agents()
        
        assert len(active_agents) == 1
        assert "test_agent" in active_agents
        assert active_agents["test_agent"] == agent
    
    def test_get_active_workflows(self, handler, sample_workflow_config):
        """测试获取活跃工作流列表."""
        # 添加工作流
        workflow = MockWorkflow("test_workflow", sample_workflow_config)
        handler._active_workflows["test_workflow"] = workflow
        
        # 获取活跃工作流
        active_workflows = handler.get_active_workflows()
        
        assert len(active_workflows) == 1
        assert "test_workflow" in active_workflows
        assert active_workflows["test_workflow"] == workflow
    
    def test_get_status(self, handler, sample_agent_config, sample_workflow_config):
        """测试获取处理器状态."""
        # 添加智能体和工作流
        agent = MockAgent("test_agent", sample_agent_config)
        workflow = MockWorkflow("test_workflow", sample_workflow_config)
        handler._active_agents["test_agent"] = agent
        handler._active_workflows["test_workflow"] = workflow
        
        # 获取状态
        status = handler.get_status()
        
        assert status["active_agents_count"] == 1
        assert status["active_workflows_count"] == 1
        assert "test_agent" in status["active_agents"]
        assert "test_workflow" in status["active_workflows"]


class TestAgentHotReloadHandlerIntegration:
    """智能体热重载处理器集成测试."""
    
    @pytest.mark.asyncio
    async def test_full_agent_lifecycle(self):
        """测试完整的智能体生命周期."""
        # 创建处理器
        agent_registry = MockAgentRegistry()
        handler = AgentHotReloadHandler(agent_registry)
        
        # 智能体配置
        agent_config = {
            "agent_id": "lifecycle_agent",
            "agent_type": "sales",
            "name": "生命周期测试智能体",
            "enabled": True,
            "llm_config": {
                "provider": "openai",
                "model_name": "gpt-3.5-turbo"
            }
        }
        
        # 1. 创建智能体
        create_event = ConfigChangeEvent(
            config_type="agent",
            config_id="lifecycle_agent",
            change_type="created",
            new_config=agent_config
        )
        
        await handler.handle_agent_config_change(create_event)
        
        # 验证创建
        assert "lifecycle_agent" in handler._active_agents
        assert "lifecycle_agent" in agent_registry.agents
        
        # 2. 更新智能体
        updated_config = agent_config.copy()
        updated_config["name"] = "更新后的智能体"
        
        update_event = ConfigChangeEvent(
            config_type="agent",
            config_id="lifecycle_agent",
            change_type="updated",
            old_config=agent_config,
            new_config=updated_config
        )
        
        await handler.handle_agent_config_change(update_event)
        
        # 验证更新
        assert "lifecycle_agent" in handler._active_agents
        
        # 3. 删除智能体
        delete_event = ConfigChangeEvent(
            config_type="agent",
            config_id="lifecycle_agent",
            change_type="deleted",
            old_config=updated_config
        )
        
        await handler.handle_agent_config_change(delete_event)
        
        # 验证删除
        assert "lifecycle_agent" not in handler._active_agents
        assert "lifecycle_agent" not in agent_registry.agents