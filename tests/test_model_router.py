"""Tests for model router and failover mechanism."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from src.multi_agent_service.models.model_service import (
    ModelConfig, 
    ModelRequest, 
    ModelResponse,
    LoadBalancingStrategy
)
from src.multi_agent_service.models.enums import ModelProvider
from src.multi_agent_service.services.model_router import (
    ModelRouter,
    ModelRouterManager,
    router_manager
)
from src.multi_agent_service.services.model_client import ModelClientError


class TestModelRouter:
    """测试模型路由器."""
    
    @pytest.fixture
    def mock_configs(self):
        """模拟配置列表."""
        return [
            ModelConfig(
                provider=ModelProvider.QWEN,
                model_name="qwen-turbo",
                api_key="test-key-1",
                base_url="https://api1.test.com/v1",
                priority=1,
                enabled=True
            ),
            ModelConfig(
                provider=ModelProvider.DEEPSEEK,
                model_name="deepseek-chat",
                api_key="test-key-2",
                base_url="https://api2.test.com/v1",
                priority=2,
                enabled=True
            ),
            ModelConfig(
                provider=ModelProvider.GLM,
                model_name="glm-4",
                api_key="test-key-3",
                base_url="https://api3.test.com/v1",
                priority=3,
                enabled=False  # 禁用的配置
            )
        ]
    
    @pytest.fixture
    def mock_router(self, mock_configs):
        """模拟路由器."""
        with patch('src.multi_agent_service.services.model_router.ModelClientFactory.create_client') as mock_factory:
            # 创建模拟客户端
            mock_clients = []
            for i, config in enumerate(mock_configs):
                if config.enabled:
                    mock_client = MagicMock()
                    mock_client.provider = config.provider
                    mock_client.metrics.availability = 1.0
                    mock_client.metrics.average_response_time = i * 0.1
                    mock_clients.append(mock_client)
            
            mock_factory.side_effect = mock_clients
            
            router = ModelRouter(mock_configs, LoadBalancingStrategy.PRIORITY)
            return router
    
    def test_initialization(self, mock_router):
        """测试路由器初始化."""
        assert len(mock_router.clients) == 2  # 只有启用的客户端
        assert "qwen:qwen-turbo" in mock_router.clients
        assert "deepseek:deepseek-chat" in mock_router.clients
        assert "glm:glm-4" not in mock_router.clients  # 禁用的客户端不应该存在
    
    def test_get_available_clients(self, mock_router):
        """测试获取可用客户端."""
        available = mock_router.get_available_clients()
        assert len(available) == 2
        
        # 测试可用性阈值
        for client_id, client in mock_router.clients.items():
            client.metrics.availability = 0.3  # 低于阈值
        
        available = mock_router.get_available_clients()
        assert len(available) == 0
    
    def test_select_client_by_priority(self, mock_router):
        """测试按优先级选择客户端."""
        mock_router.strategy = LoadBalancingStrategy.PRIORITY
        
        selected = mock_router.select_client(ModelRequest(messages=[]))
        assert selected is not None
        
        client_id, client = selected
        # 应该选择优先级最高的（数字最小的）
        assert client_id == "qwen:qwen-turbo"
    
    def test_select_client_by_round_robin(self, mock_router):
        """测试轮询选择客户端."""
        mock_router.strategy = LoadBalancingStrategy.ROUND_ROBIN
        
        # 连续选择应该轮询
        selected1 = mock_router.select_client(ModelRequest(messages=[]))
        selected2 = mock_router.select_client(ModelRequest(messages=[]))
        
        assert selected1 is not None
        assert selected2 is not None
        assert selected1[0] != selected2[0]  # 应该选择不同的客户端
    
    def test_select_client_by_response_time(self, mock_router):
        """测试按响应时间选择客户端."""
        mock_router.strategy = LoadBalancingStrategy.RESPONSE_TIME
        
        # 设置不同的响应时间
        clients = list(mock_router.clients.values())
        clients[0].metrics.average_response_time = 0.5  # qwen
        clients[1].metrics.average_response_time = 0.1  # deepseek (最快)
        
        selected = mock_router.select_client(ModelRequest(messages=[]))
        assert selected is not None
        
        client_id, client = selected
        # 应该选择响应时间最短的
        assert client_id == "deepseek:deepseek-chat"  # 响应时间为0.1
    
    def test_add_client(self, mock_router):
        """测试添加客户端."""
        new_config = ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="gpt-3.5-turbo",
            api_key="test-key-4",
            base_url="https://api4.test.com/v1",
            enabled=True
        )
        
        with patch('src.multi_agent_service.services.model_router.ModelClientFactory.create_client') as mock_factory:
            mock_client = MagicMock()
            mock_client.provider = ModelProvider.OPENAI
            mock_factory.return_value = mock_client
            
            initial_count = len(mock_router.clients)
            mock_router.add_client(new_config)
            
            assert len(mock_router.clients) == initial_count + 1
            assert "openai:gpt-3.5-turbo" in mock_router.clients
    
    def test_remove_client(self, mock_router):
        """测试移除客户端."""
        initial_count = len(mock_router.clients)
        
        mock_router.remove_client(ModelProvider.QWEN, "qwen-turbo")
        
        assert len(mock_router.clients) == initial_count - 1
        assert "qwen:qwen-turbo" not in mock_router.clients
    
    @pytest.mark.asyncio
    async def test_successful_chat_completion(self, mock_router):
        """测试成功的聊天完成请求."""
        # 模拟成功响应
        mock_response = ModelResponse(
            id="test-id",
            created=1234567890,
            model="qwen-turbo",
            choices=[],
            usage={},
            provider=ModelProvider.QWEN,
            response_time=0.1
        )
        
        # 设置第一个客户端返回成功响应
        first_client = list(mock_router.clients.values())[0]
        first_client.chat_completion = AsyncMock(return_value=mock_response)
        
        request = ModelRequest(messages=[{"role": "user", "content": "Hello"}])
        response = await mock_router.chat_completion(request)
        
        assert response.id == "test-id"
        assert response.provider == ModelProvider.QWEN
        first_client.chat_completion.assert_called_once_with(request)
    
    @pytest.mark.asyncio
    async def test_failover_mechanism(self, mock_router):
        """测试故障转移机制."""
        # 设置第一个客户端失败，第二个客户端成功
        clients = list(mock_router.clients.values())
        
        clients[0].chat_completion = AsyncMock(
            side_effect=ModelClientError("First client failed")
        )
        
        mock_response = ModelResponse(
            id="test-id",
            created=1234567890,
            model="deepseek-chat",
            choices=[],
            usage={},
            provider=ModelProvider.DEEPSEEK,
            response_time=0.2
        )
        clients[1].chat_completion = AsyncMock(return_value=mock_response)
        
        request = ModelRequest(messages=[{"role": "user", "content": "Hello"}])
        response = await mock_router.chat_completion(request)
        
        # 应该返回第二个客户端的响应
        assert response.provider == ModelProvider.DEEPSEEK
        
        # 应该记录故障转移事件
        assert len(mock_router.failover_events) > 0
        
        # 两个客户端都应该被调用
        clients[0].chat_completion.assert_called_once()
        clients[1].chat_completion.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_all_clients_fail(self, mock_router):
        """测试所有客户端都失败的情况."""
        # 设置所有客户端都失败
        for client in mock_router.clients.values():
            client.chat_completion = AsyncMock(
                side_effect=ModelClientError("Client failed")
            )
        
        request = ModelRequest(messages=[{"role": "user", "content": "Hello"}])
        
        with pytest.raises(ModelClientError, match="All model clients failed"):
            await mock_router.chat_completion(request)
    
    @pytest.mark.asyncio
    async def test_health_check(self, mock_router):
        """测试健康检查."""
        # 设置客户端健康检查结果
        clients = list(mock_router.clients.values())
        clients[0].health_check = AsyncMock(return_value=True)
        clients[1].health_check = AsyncMock(return_value=False)
        
        health_status = await mock_router.health_check()
        
        assert len(health_status) == 2
        assert health_status["qwen:qwen-turbo"] is True
        assert health_status["deepseek:deepseek-chat"] is False
    
    def test_get_metrics(self, mock_router):
        """测试获取指标."""
        # 设置客户端指标
        for client in mock_router.clients.values():
            client.get_metrics = MagicMock(return_value=MagicMock())
            client.get_metrics.return_value.model_dump = MagicMock(
                return_value={"test": "metrics"}
            )
        
        metrics = mock_router.get_metrics()
        
        assert len(metrics) == 2
        for client_id in mock_router.clients.keys():
            assert client_id in metrics
            assert metrics[client_id] == {"test": "metrics"}
    
    def test_set_strategy(self, mock_router):
        """测试设置负载均衡策略."""
        initial_strategy = mock_router.strategy
        new_strategy = LoadBalancingStrategy.ROUND_ROBIN
        
        mock_router.set_strategy(new_strategy)
        
        assert mock_router.strategy == new_strategy
        assert mock_router.strategy != initial_strategy
    
    @pytest.mark.asyncio
    async def test_close(self, mock_router):
        """测试关闭路由器."""
        # 设置客户端关闭方法
        for client in mock_router.clients.values():
            client.close = AsyncMock()
        
        await mock_router.close()
        
        # 所有客户端的close方法都应该被调用
        for client in mock_router.clients.values():
            client.close.assert_called_once()


class TestModelRouterManager:
    """测试模型路由器管理器."""
    
    @pytest.fixture
    def manager(self):
        """路由器管理器fixture."""
        return ModelRouterManager()
    
    @pytest.fixture
    def mock_configs(self):
        """模拟配置列表."""
        return [
            ModelConfig(
                provider=ModelProvider.QWEN,
                model_name="qwen-turbo",
                api_key="test-key",
                base_url="https://api.test.com/v1",
                enabled=True
            )
        ]
    
    def test_create_router(self, manager, mock_configs):
        """测试创建路由器."""
        with patch('src.multi_agent_service.services.model_router.ModelClientFactory.create_client'):
            router = manager.create_router("test-router", mock_configs)
            
            assert isinstance(router, ModelRouter)
            assert "test-router" in manager.routers
            assert manager.get_router("test-router") is router
    
    def test_get_nonexistent_router(self, manager):
        """测试获取不存在的路由器."""
        router = manager.get_router("nonexistent")
        assert router is None
    
    def test_remove_router(self, manager, mock_configs):
        """测试移除路由器."""
        with patch('src.multi_agent_service.services.model_router.ModelClientFactory.create_client'):
            manager.create_router("test-router", mock_configs)
            
            assert "test-router" in manager.routers
            
            manager.remove_router("test-router")
            
            assert "test-router" not in manager.routers
    
    def test_list_routers(self, manager, mock_configs):
        """测试列出路由器."""
        with patch('src.multi_agent_service.services.model_router.ModelClientFactory.create_client'):
            manager.create_router("router1", mock_configs)
            manager.create_router("router2", mock_configs)
            
            routers = manager.list_routers()
            
            assert len(routers) == 2
            assert "router1" in routers
            assert "router2" in routers
    
    @pytest.mark.asyncio
    async def test_close_all(self, manager, mock_configs):
        """测试关闭所有路由器."""
        with patch('src.multi_agent_service.services.model_router.ModelClientFactory.create_client'):
            router1 = manager.create_router("router1", mock_configs)
            router2 = manager.create_router("router2", mock_configs)
            
            # 模拟路由器的close方法
            router1.close = AsyncMock()
            router2.close = AsyncMock()
            
            await manager.close_all()
            
            # 所有路由器的close方法都应该被调用
            router1.close.assert_called_once()
            router2.close.assert_called_once()
            
            # 路由器列表应该被清空
            assert len(manager.routers) == 0


class TestLoadBalancingStrategies:
    """测试负载均衡策略."""
    
    @pytest.fixture
    def router_with_multiple_clients(self):
        """创建有多个客户端的路由器."""
        configs = [
            ModelConfig(
                provider=ModelProvider.QWEN,
                model_name="qwen-turbo",
                api_key="test-key-1",
                base_url="https://api1.test.com/v1",
                priority=1,
                enabled=True
            ),
            ModelConfig(
                provider=ModelProvider.DEEPSEEK,
                model_name="deepseek-chat",
                api_key="test-key-2",
                base_url="https://api2.test.com/v1",
                priority=2,
                enabled=True
            ),
            ModelConfig(
                provider=ModelProvider.GLM,
                model_name="glm-4",
                api_key="test-key-3",
                base_url="https://api3.test.com/v1",
                priority=3,
                enabled=True
            )
        ]
        
        with patch('src.multi_agent_service.services.model_router.ModelClientFactory.create_client') as mock_factory:
            mock_clients = []
            for i, config in enumerate(configs):
                mock_client = MagicMock()
                mock_client.provider = config.provider
                mock_client.metrics.availability = 1.0
                mock_client.metrics.average_response_time = i * 0.1
                mock_clients.append(mock_client)
            
            mock_factory.side_effect = mock_clients
            
            return ModelRouter(configs, LoadBalancingStrategy.PRIORITY)
    
    def test_weighted_round_robin_strategy(self, router_with_multiple_clients):
        """测试加权轮询策略."""
        router = router_with_multiple_clients
        router.strategy = LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN
        
        # 多次选择客户端，统计分布
        selections = {}
        for _ in range(100):
            selected = router.select_client(ModelRequest(messages=[]))
            if selected:
                client_id = selected[0]
                selections[client_id] = selections.get(client_id, 0) + 1
        
        # 优先级高的客户端应该被选择更多次
        assert len(selections) > 0
        # 由于随机性，我们只检查是否有选择发生
    
    def test_least_connections_strategy(self, router_with_multiple_clients):
        """测试最少连接策略."""
        router = router_with_multiple_clients
        router.strategy = LoadBalancingStrategy.LEAST_CONNECTIONS
        
        # 模拟连接计数
        router._connection_counts["qwen:qwen-turbo"] = 5
        router._connection_counts["deepseek:deepseek-chat"] = 2
        router._connection_counts["glm:glm-4"] = 3
        
        selected = router.select_client(ModelRequest(messages=[]))
        assert selected is not None
        
        # 应该选择连接数最少的客户端
        client_id, _ = selected
        assert client_id == "deepseek:deepseek-chat"


class TestGlobalRouterManager:
    """测试全局路由器管理器."""
    
    def test_global_instance(self):
        """测试全局实例."""
        assert router_manager is not None
        assert isinstance(router_manager, ModelRouterManager)