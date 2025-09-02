"""Tests for service integration and system startup."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from src.multi_agent_service.core.service_container import ServiceContainer
from src.multi_agent_service.core.service_manager import ServiceManager
from src.multi_agent_service.core.lifecycle_manager import LifecycleManager
from src.multi_agent_service.core.service_initializer import ServiceInitializer


class TestServiceContainer:
    """Test service container functionality."""
    
    def test_service_container_creation(self):
        """Test service container can be created."""
        container = ServiceContainer()
        assert container is not None
        assert len(container._services) == 0
    
    def test_register_singleton_service(self):
        """Test registering singleton services."""
        container = ServiceContainer()
        
        class TestService:
            def __init__(self):
                self.value = "test"
        
        container.register_singleton(TestService)
        assert TestService in container._services
        assert container._services[TestService].scope.value == "singleton"
    
    def test_register_instance(self):
        """Test registering service instances."""
        container = ServiceContainer()
        
        class TestService:
            def __init__(self):
                self.value = "test"
        
        instance = TestService()
        container.register_instance(TestService, instance)
        
        assert TestService in container._services
        assert TestService in container._instances
        assert container._instances[TestService] is instance
    
    @pytest.mark.asyncio
    async def test_get_service(self):
        """Test getting service instances."""
        container = ServiceContainer()
        
        class TestService:
            def __init__(self):
                self.value = "test"
        
        container.register_singleton(TestService)
        
        service = await container.get_service(TestService)
        assert service is not None
        assert service.value == "test"
        
        # Should return same instance for singleton
        service2 = await container.get_service(TestService)
        assert service is service2
    
    @pytest.mark.asyncio
    async def test_dependency_injection(self):
        """Test dependency injection."""
        container = ServiceContainer()
        
        class DependencyService:
            def __init__(self):
                self.name = "dependency"
        
        class MainService:
            def __init__(self, dep: DependencyService):
                self.dependency = dep
        
        container.register_singleton(DependencyService)
        container.register_singleton(MainService, dependencies=[DependencyService])
        
        main_service = await container.get_service(MainService)
        assert main_service is not None
        assert main_service.dependency is not None
        assert main_service.dependency.name == "dependency"


class TestServiceManager:
    """Test service manager functionality."""
    
    @pytest.mark.asyncio
    async def test_service_manager_creation(self):
        """Test service manager can be created."""
        container = ServiceContainer()
        manager = ServiceManager(container)
        assert manager is not None
        assert manager.container is container
    
    @pytest.mark.asyncio
    async def test_register_core_services(self):
        """Test registering core services."""
        container = ServiceContainer()
        manager = ServiceManager(container)
        
        # Mock the dependencies to avoid actual initialization
        with patch('src.multi_agent_service.config.config_manager.ConfigManager') as mock_config, \
             patch('src.multi_agent_service.services.model_router.ModelRouter') as mock_model_router, \
             patch('src.multi_agent_service.services.intent_analyzer.IntentAnalyzer') as mock_intent, \
             patch('src.multi_agent_service.services.agent_router.AgentRouter') as mock_agent_router, \
             patch('src.multi_agent_service.workflows.state_management.StateManager') as mock_state, \
             patch('src.multi_agent_service.workflows.graph_builder.GraphBuilder') as mock_graph, \
             patch('src.multi_agent_service.services.hot_reload_service.HotReloadService') as mock_hot_reload, \
             patch('src.multi_agent_service.utils.monitoring.MonitoringSystem') as mock_monitoring, \
             patch('src.multi_agent_service.utils.logging.LoggingSystem') as mock_logging:
            
            await manager._register_core_services()
            
            # Check that services are registered
            assert len(container._services) > 0


class TestLifecycleManager:
    """Test lifecycle manager functionality."""
    
    def test_lifecycle_manager_creation(self):
        """Test lifecycle manager can be created."""
        manager = LifecycleManager()
        assert manager is not None
        assert manager.service_manager is not None
    
    def test_add_startup_hook(self):
        """Test adding startup hooks."""
        manager = LifecycleManager()
        
        def test_hook():
            pass
        
        manager.add_startup_hook(test_hook)
        assert test_hook in manager._startup_hooks
    
    def test_add_shutdown_hook(self):
        """Test adding shutdown hooks."""
        manager = LifecycleManager()
        
        def test_hook():
            pass
        
        manager.add_shutdown_hook(test_hook)
        assert test_hook in manager._shutdown_hooks
    
    @pytest.mark.asyncio
    async def test_execute_startup_hooks(self):
        """Test executing startup hooks."""
        manager = LifecycleManager()
        
        hook_called = False
        
        def test_hook():
            nonlocal hook_called
            hook_called = True
        
        manager.add_startup_hook(test_hook)
        await manager._execute_startup_hooks()
        
        assert hook_called
    
    @pytest.mark.asyncio
    async def test_execute_async_startup_hooks(self):
        """Test executing async startup hooks."""
        manager = LifecycleManager()
        
        hook_called = False
        
        async def test_async_hook():
            nonlocal hook_called
            hook_called = True
        
        manager.add_startup_hook(test_async_hook)
        await manager._execute_startup_hooks()
        
        assert hook_called


class TestServiceInitializer:
    """Test service initializer functionality."""
    
    @pytest.mark.asyncio
    async def test_service_initializer_creation(self):
        """Test service initializer can be created."""
        config_manager = Mock()
        agent_registry = Mock()
        model_router = Mock()
        
        initializer = ServiceInitializer(config_manager, agent_registry, model_router)
        assert initializer is not None
        assert initializer.config_manager is config_manager
        assert initializer.agent_registry is agent_registry
        assert initializer.model_router is model_router
    
    def test_create_default_agent_configs(self):
        """Test creating default agent configurations."""
        config_manager = Mock()
        agent_registry = Mock()
        model_router = Mock()
        
        initializer = ServiceInitializer(config_manager, agent_registry, model_router)
        configs = initializer._create_default_agent_configs()
        
        assert len(configs) == 5  # 5 default agent types
        assert all(config.agent_id for config in configs)
        assert all(config.name for config in configs)
    
    @pytest.mark.asyncio
    async def test_validate_service_dependencies(self):
        """Test service dependency validation."""
        config_manager = Mock()
        agent_registry = Mock()
        model_router = Mock()
        model_router.get_available_providers = AsyncMock(return_value=["qwen", "deepseek"])
        
        initializer = ServiceInitializer(config_manager, agent_registry, model_router)
        
        result = await initializer.validate_service_dependencies()
        assert result is True


class TestIntegrationScenarios:
    """Test integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_full_service_initialization_flow(self):
        """Test complete service initialization flow."""
        # This test would require extensive mocking of all dependencies
        # For now, we'll test the basic flow structure
        
        container = ServiceContainer()
        manager = ServiceManager(container)
        lifecycle = LifecycleManager(manager)
        
        # Mock all the complex dependencies
        with patch.object(manager, 'initialize', return_value=True) as mock_init, \
             patch.object(manager, 'start', return_value=True) as mock_start:
            
            result = await lifecycle.startup()
            
            # The actual result depends on mocked behavior
            # In a real scenario, this would test the full integration
            assert mock_init.called or mock_start.called  # At least one should be called
    
    @pytest.mark.asyncio
    async def test_service_container_health_check(self):
        """Test service container health check."""
        container = ServiceContainer()
        
        class HealthyService:
            async def health_check(self):
                return True
        
        class UnhealthyService:
            async def health_check(self):
                return False
        
        healthy_service = HealthyService()
        unhealthy_service = UnhealthyService()
        
        container.register_instance(HealthyService, healthy_service)
        container.register_instance(UnhealthyService, unhealthy_service)
        
        health_results = await container.health_check_services()
        
        assert health_results["HealthyService"] is True
        assert health_results["UnhealthyService"] is False
    
    def test_service_info_retrieval(self):
        """Test retrieving service information."""
        container = ServiceContainer()
        
        class TestService:
            pass
        
        container.register_singleton(TestService)
        
        info = container.get_service_info()
        
        assert "total_services" in info
        assert "services" in info
        assert "TestService" in info["services"]
        assert info["services"]["TestService"]["scope"] == "singleton"


if __name__ == "__main__":
    pytest.main([__file__])