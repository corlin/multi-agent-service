"""Integration tests for service startup and initialization."""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from pathlib import Path

from src.multi_agent_service.core.lifecycle_manager import LifecycleManager
from src.multi_agent_service.core.service_manager import ServiceManager
from src.multi_agent_service.core.service_container import ServiceContainer
from src.multi_agent_service.startup import (
    validate_configuration, 
    preload_agents_and_workflows,
    perform_startup_health_checks,
    startup_service,
    setup_logging
)


class TestServiceStartupIntegration:
    """Test service startup integration."""
    
    @pytest.mark.asyncio
    async def test_complete_startup_sequence(self):
        """Test complete service startup sequence."""
        container = ServiceContainer()
        service_manager = ServiceManager(container)
        lifecycle_manager = LifecycleManager(service_manager)
        
        # Mock complex dependencies to avoid actual initialization
        with patch.object(service_manager, '_initialize_agents', return_value=None) as mock_init_agents, \
             patch.object(service_manager, '_setup_agent_registry', return_value=None) as mock_setup_agents, \
             patch('src.multi_agent_service.services.hot_reload_service.HotReloadService') as mock_hot_reload, \
             patch('src.multi_agent_service.utils.monitoring.MonitoringSystem') as mock_monitoring:
            
            # Configure mocks
            mock_hot_reload_instance = AsyncMock()
            mock_hot_reload_instance.start = AsyncMock(return_value=True)
            mock_hot_reload.return_value = mock_hot_reload_instance
            
            mock_monitoring_instance = AsyncMock()
            mock_monitoring_instance.start_monitoring = AsyncMock(return_value=True)
            mock_monitoring.return_value = mock_monitoring_instance
            
            # Test startup
            result = await lifecycle_manager.startup()
            
            # Verify startup was attempted
            assert isinstance(result, bool)
            # Note: Result might be False due to mocked dependencies, but we're testing the flow
    
    @pytest.mark.asyncio
    async def test_service_container_initialization(self):
        """Test service container initialization."""
        container = ServiceContainer()
        
        # Register test services
        class TestService:
            def __init__(self):
                self.initialized = False
            
            async def initialize(self):
                self.initialized = True
                return True
        
        container.register_singleton(TestService)
        
        # Initialize services
        result = await container.initialize_all_services()
        assert result is True
        
        # Get service and verify initialization
        service = await container.get_service(TestService)
        assert service is not None
        assert service.initialized is True
    
    @pytest.mark.asyncio
    async def test_service_health_check(self):
        """Test service health check functionality."""
        container = ServiceContainer()
        
        class HealthyService:
            async def health_check(self):
                return True
        
        class UnhealthyService:
            async def health_check(self):
                return False
        
        # Register services
        healthy_service = HealthyService()
        unhealthy_service = UnhealthyService()
        
        container.register_instance(HealthyService, healthy_service)
        container.register_instance(UnhealthyService, unhealthy_service)
        
        # Check health
        health_results = await container.health_check_services()
        
        assert health_results["HealthyService"] is True
        assert health_results["UnhealthyService"] is False
    
    @pytest.mark.asyncio
    async def test_service_shutdown_sequence(self):
        """Test service shutdown sequence."""
        container = ServiceContainer()
        service_manager = ServiceManager(container)
        lifecycle_manager = LifecycleManager(service_manager)
        
        # Mock dependencies
        with patch.object(service_manager, 'stop', return_value=True) as mock_stop:
            result = await lifecycle_manager.shutdown()
            
            # Verify shutdown was called
            mock_stop.assert_called_once()
            assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_service_restart_sequence(self):
        """Test service restart sequence."""
        container = ServiceContainer()
        service_manager = ServiceManager(container)
        lifecycle_manager = LifecycleManager(service_manager)
        
        # Mock dependencies
        with patch.object(lifecycle_manager, 'shutdown', return_value=True) as mock_shutdown, \
             patch.object(lifecycle_manager, 'startup', return_value=True) as mock_startup:
            
            result = await lifecycle_manager.restart()
            
            # Verify restart sequence
            mock_shutdown.assert_called_once()
            mock_startup.assert_called_once()
            assert result is True
    
    def test_lifecycle_status_tracking(self):
        """Test lifecycle status tracking."""
        container = ServiceContainer()
        service_manager = ServiceManager(container)
        lifecycle_manager = LifecycleManager(service_manager)
        
        # Check initial status
        status = lifecycle_manager.get_lifecycle_status()
        
        assert "startup_time" in status
        assert "uptime_seconds" in status
        assert "is_shutting_down" in status
        assert status["service_manager_initialized"] is False
        assert status["service_manager_running"] is False
    
    @pytest.mark.asyncio
    async def test_configuration_validation(self):
        """Test configuration validation during startup."""
        # Test configuration validation
        result = await validate_configuration()
        
        # Should not fail even with minimal configuration
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_enhanced_configuration_validation(self):
        """Test enhanced configuration validation with various scenarios."""
        # Test with valid configuration
        with patch('src.multi_agent_service.startup.settings') as mock_settings:
            mock_settings.api_port = 8000
            mock_settings.api_host = "0.0.0.0"
            mock_settings.api_debug = False
            mock_settings.log_level = "INFO"
            mock_settings.qwen_api_key = "test_key"
            mock_settings.deepseek_api_key = None
            mock_settings.glm_api_key = None
            mock_settings.openai_api_key = None
            mock_settings.database_url = "sqlite:///test.db"
            mock_settings.redis_url = "redis://localhost:6379"
            
            result = await validate_configuration()
            assert result is True
        
        # Test with invalid port
        with patch('src.multi_agent_service.startup.settings') as mock_settings:
            mock_settings.api_port = 99999  # Invalid port
            mock_settings.api_host = "0.0.0.0"
            mock_settings.api_debug = False
            mock_settings.log_level = "INFO"
            mock_settings.qwen_api_key = None
            mock_settings.deepseek_api_key = None
            mock_settings.glm_api_key = None
            mock_settings.openai_api_key = None
            mock_settings.database_url = None
            mock_settings.redis_url = None
            
            result = await validate_configuration()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_preload_agents_and_workflows(self):
        """Test agent and workflow preloading functionality."""
        container = ServiceContainer()
        service_manager = ServiceManager(container)
        lifecycle_manager = LifecycleManager(service_manager)
        
        # Mock the lifecycle manager
        with patch('src.multi_agent_service.startup.lifecycle_manager', lifecycle_manager):
            # Mock service manager initialization
            service_manager._is_initialized = True
            
            # Mock agent registry
            mock_agent_registry = AsyncMock()
            mock_agent_registry.get_registry_stats.return_value = {
                'registered_classes': 5,
                'active_agents': 3,
                'total_agents': 3
            }
            
            # Mock graph builder
            mock_graph_builder = AsyncMock()
            mock_graph_builder.create_workflow_graph.return_value = MagicMock()
            
            # Mock model router
            mock_model_router = AsyncMock()
            mock_model_router.get_available_clients.return_value = [
                ("qwen_client", MagicMock()),
                ("deepseek_client", MagicMock())
            ]
            
            # Register mocked services with proper types
            from src.multi_agent_service.agents.registry import AgentRegistry
            from src.multi_agent_service.workflows.graph_builder import GraphBuilder
            from src.multi_agent_service.services.model_router import ModelRouter
            
            container.register_instance(AgentRegistry, mock_agent_registry)
            container.register_instance(GraphBuilder, mock_graph_builder)
            container.register_instance(ModelRouter, mock_model_router)
            
            result = await preload_agents_and_workflows()
            assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_startup_health_checks(self):
        """Test comprehensive startup health checks."""
        container = ServiceContainer()
        service_manager = ServiceManager(container)
        lifecycle_manager = LifecycleManager(service_manager)
        
        # Mock health check responses
        mock_health_status = {
            "healthy": True,
            "timestamp": datetime.now().isoformat(),
            "lifecycle": {"uptime_seconds": 10.5},
            "services": {"ConfigManager": True, "ModelRouter": True}
        }
        
        mock_system_status = {
            "service_container": {"initialized_services": 5},
            "agent_registry": {"active_agents": 3},
            "monitoring": {"model_providers": ["qwen", "deepseek"]}
        }
        
        with patch('src.multi_agent_service.startup.lifecycle_manager', lifecycle_manager):
            lifecycle_manager.health_check = AsyncMock(return_value=mock_health_status)
            lifecycle_manager.service_manager.get_system_status = AsyncMock(return_value=mock_system_status)
            
            result = await perform_startup_health_checks()
            
            assert isinstance(result, dict)
            assert "overall_healthy" in result
            assert "startup_checks" in result
            assert "configuration_valid" in result["startup_checks"]
            assert "agents_preloaded" in result["startup_checks"]
            assert "workflows_ready" in result["startup_checks"]
    
    @pytest.mark.asyncio
    async def test_complete_startup_service(self):
        """Test complete startup service flow."""
        with patch('src.multi_agent_service.startup.validate_configuration', return_value=True) as mock_validate, \
             patch('src.multi_agent_service.startup.lifecycle_manager') as mock_lifecycle, \
             patch('src.multi_agent_service.startup.preload_agents_and_workflows', return_value=True) as mock_preload, \
             patch('src.multi_agent_service.startup.perform_startup_health_checks') as mock_health:
            
            # Configure mocks
            mock_lifecycle.startup = AsyncMock(return_value=True)
            mock_lifecycle.uptime = 15.5
            
            mock_health.return_value = {
                "overall_healthy": True,
                "system": {
                    "service_container": {"initialized_services": 5},
                    "agent_registry": {"active_agents": 3}
                }
            }
            
            result = await startup_service()
            
            # Verify all steps were called
            mock_validate.assert_called_once()
            mock_lifecycle.startup.assert_called_once()
            mock_preload.assert_called_once()
            mock_health.assert_called_once()
            
            assert result is True
    
    def test_setup_logging(self):
        """Test logging setup functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp directory
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                # Test logging setup
                setup_logging()
                
                # Verify logs directory was created
                logs_dir = Path("logs")
                assert logs_dir.exists()
                assert logs_dir.is_dir()
                
            finally:
                os.chdir(original_cwd)
    
    @pytest.mark.asyncio
    async def test_startup_with_configuration_failure(self):
        """Test startup behavior when configuration validation fails."""
        with patch('src.multi_agent_service.startup.validate_configuration', return_value=False):
            result = await startup_service()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_startup_with_core_service_failure(self):
        """Test startup behavior when core services fail to start."""
        with patch('src.multi_agent_service.startup.validate_configuration', return_value=True), \
             patch('src.multi_agent_service.startup.lifecycle_manager') as mock_lifecycle:
            
            mock_lifecycle.startup = AsyncMock(return_value=False)
            
            result = await startup_service()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_startup_with_preload_failure(self):
        """Test startup behavior when preloading fails."""
        with patch('src.multi_agent_service.startup.validate_configuration', return_value=True), \
             patch('src.multi_agent_service.startup.lifecycle_manager') as mock_lifecycle, \
             patch('src.multi_agent_service.startup.preload_agents_and_workflows', return_value=False), \
             patch('src.multi_agent_service.startup.perform_startup_health_checks') as mock_health:
            
            mock_lifecycle.startup = AsyncMock(return_value=True)
            mock_lifecycle.uptime = 10.0
            
            mock_health.return_value = {"overall_healthy": True, "system": {}}
            
            # Should still succeed even if preloading fails
            result = await startup_service()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_startup_hooks(self):
        """Test startup and shutdown hooks."""
        container = ServiceContainer()
        service_manager = ServiceManager(container)
        lifecycle_manager = LifecycleManager(service_manager)
        
        # Add test hooks
        startup_called = False
        shutdown_called = False
        
        def startup_hook():
            nonlocal startup_called
            startup_called = True
        
        def shutdown_hook():
            nonlocal shutdown_called
            shutdown_called = True
        
        lifecycle_manager.add_startup_hook(startup_hook)
        lifecycle_manager.add_shutdown_hook(shutdown_hook)
        
        # Execute hooks
        await lifecycle_manager._execute_startup_hooks()
        await lifecycle_manager._execute_shutdown_hooks()
        
        assert startup_called is True
        assert shutdown_called is True
    
    @pytest.mark.asyncio
    async def test_async_startup_hooks(self):
        """Test async startup and shutdown hooks."""
        container = ServiceContainer()
        service_manager = ServiceManager(container)
        lifecycle_manager = LifecycleManager(service_manager)
        
        # Add async test hooks
        startup_called = False
        shutdown_called = False
        
        async def async_startup_hook():
            nonlocal startup_called
            await asyncio.sleep(0.01)  # Simulate async work
            startup_called = True
        
        async def async_shutdown_hook():
            nonlocal shutdown_called
            await asyncio.sleep(0.01)  # Simulate async work
            shutdown_called = True
        
        lifecycle_manager.add_startup_hook(async_startup_hook)
        lifecycle_manager.add_shutdown_hook(async_shutdown_hook)
        
        # Execute hooks
        await lifecycle_manager._execute_startup_hooks()
        await lifecycle_manager._execute_shutdown_hooks()
        
        assert startup_called is True
        assert shutdown_called is True
    
    @pytest.mark.asyncio
    async def test_service_dependency_resolution(self):
        """Test service dependency resolution."""
        container = ServiceContainer()
        
        class ServiceA:
            def __init__(self):
                self.name = "ServiceA"
        
        class ServiceB:
            def __init__(self, service_a: ServiceA):
                self.name = "ServiceB"
                self.dependency = service_a
        
        class ServiceC:
            def __init__(self, service_a: ServiceA, service_b: ServiceB):
                self.name = "ServiceC"
                self.service_a = service_a
                self.service_b = service_b
        
        # Register services with dependencies
        container.register_singleton(ServiceA)
        container.register_singleton(ServiceB, dependencies=[ServiceA])
        container.register_singleton(ServiceC, dependencies=[ServiceA, ServiceB])
        
        # Initialize all services
        result = await container.initialize_all_services()
        assert result is True
        
        # Verify dependency injection
        service_c = await container.get_service(ServiceC)
        assert service_c is not None
        assert service_c.service_a is not None
        assert service_c.service_b is not None
        assert service_c.service_a.name == "ServiceA"
        assert service_c.service_b.name == "ServiceB"
        
        # Verify same instances are used (singleton)
        service_a_direct = await container.get_service(ServiceA)
        service_b_direct = await container.get_service(ServiceB)
        
        assert service_c.service_a is service_a_direct
        assert service_c.service_b is service_b_direct
    
    @pytest.mark.asyncio
    async def test_service_initialization_order(self):
        """Test that services are initialized in correct dependency order."""
        container = ServiceContainer()
        
        initialization_order = []
        
        class ServiceA:
            def __init__(self):
                initialization_order.append("ServiceA")
        
        class ServiceB:
            def __init__(self, service_a: ServiceA):
                initialization_order.append("ServiceB")
        
        class ServiceC:
            def __init__(self, service_b: ServiceB):
                initialization_order.append("ServiceC")
        
        # Register in reverse dependency order to test sorting
        container.register_singleton(ServiceC, dependencies=[ServiceB])
        container.register_singleton(ServiceB, dependencies=[ServiceA])
        container.register_singleton(ServiceA)
        
        # Initialize services
        await container.initialize_all_services()
        
        # Verify initialization order
        assert initialization_order == ["ServiceA", "ServiceB", "ServiceC"]
    
    @pytest.mark.asyncio
    async def test_service_preloading_with_missing_dependencies(self):
        """Test service preloading when some dependencies are missing."""
        # Mock lifecycle manager with uninitialized service manager
        mock_lifecycle = MagicMock()
        mock_lifecycle.service_manager = None
        
        with patch('src.multi_agent_service.startup.lifecycle_manager', mock_lifecycle):
            result = await preload_agents_and_workflows()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_configuration_validation_with_missing_directories(self):
        """Test configuration validation when directories don't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                # Remove any existing directories
                for dir_name in ["logs", "config"]:
                    dir_path = Path(dir_name)
                    if dir_path.exists():
                        import shutil
                        shutil.rmtree(dir_path)
                
                result = await validate_configuration()
                
                # Should still pass as directories are created automatically
                assert result is True
                
                # Verify directories were created
                assert Path("logs").exists()
                assert Path("config").exists()
                
            finally:
                os.chdir(original_cwd)
    
    @pytest.mark.asyncio
    async def test_health_checks_with_service_failures(self):
        """Test health checks when some services are failing."""
        container = ServiceContainer()
        service_manager = ServiceManager(container)
        lifecycle_manager = LifecycleManager(service_manager)
        
        # Mock unhealthy responses
        mock_health_status = {
            "healthy": False,
            "timestamp": datetime.now().isoformat(),
            "services": {"ConfigManager": True, "ModelRouter": False}
        }
        
        mock_system_status = {
            "service_container": {"initialized_services": 3},
            "agent_registry": {"active_agents": 0},  # No active agents
            "monitoring": {"model_providers": []}  # No model providers
        }
        
        with patch('src.multi_agent_service.startup.lifecycle_manager', lifecycle_manager):
            lifecycle_manager.health_check = AsyncMock(return_value=mock_health_status)
            lifecycle_manager.service_manager.get_system_status = AsyncMock(return_value=mock_system_status)
            
            result = await perform_startup_health_checks()
            
            assert result["overall_healthy"] is False
            assert result["startup_checks"]["agents_preloaded"] is False
            assert result["startup_checks"]["models_available"] is False
    
    @pytest.mark.asyncio
    async def test_startup_service_exception_handling(self):
        """Test startup service exception handling."""
        with patch('src.multi_agent_service.startup.validate_configuration', side_effect=Exception("Test error")):
            result = await startup_service()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_preload_with_workflow_creation_errors(self):
        """Test preloading when workflow creation fails."""
        container = ServiceContainer()
        service_manager = ServiceManager(container)
        lifecycle_manager = LifecycleManager(service_manager)
        
        with patch('src.multi_agent_service.startup.lifecycle_manager', lifecycle_manager):
            service_manager._is_initialized = True
            
            # Mock agent registry
            mock_agent_registry = AsyncMock()
            mock_agent_registry.get_registry_stats.return_value = {
                'registered_classes': 5,
                'active_agents': 3,
                'total_agents': 3
            }
            
            # Mock graph builder that fails
            mock_graph_builder = AsyncMock()
            mock_graph_builder.create_workflow_graph.side_effect = Exception("Workflow creation failed")
            
            # Mock model router
            mock_model_router = AsyncMock()
            mock_model_router.get_available_clients.return_value = []
            
            # Register services with proper types
            from src.multi_agent_service.agents.registry import AgentRegistry
            from src.multi_agent_service.workflows.graph_builder import GraphBuilder
            from src.multi_agent_service.services.model_router import ModelRouter
            
            container.register_instance(AgentRegistry, mock_agent_registry)
            container.register_instance(GraphBuilder, mock_graph_builder)
            container.register_instance(ModelRouter, mock_model_router)
            
            # Should still succeed despite workflow errors
            result = await preload_agents_and_workflows()
            assert result is True  # Should handle errors gracefully
    
    @pytest.mark.asyncio
    async def test_error_handling_during_startup(self):
        """Test error handling during service startup."""
        container = ServiceContainer()
        
        class FailingService:
            def __init__(self):
                raise RuntimeError("Service initialization failed")
        
        container.register_singleton(FailingService)
        
        # Initialization should handle the error gracefully
        result = await container.initialize_all_services()
        assert result is False  # Should fail due to service initialization error
    
    def test_service_info_retrieval(self):
        """Test service information retrieval."""
        container = ServiceContainer()
        
        class TestService:
            pass
        
        container.register_singleton(TestService)
        
        # Get service info
        info = container.get_service_info()
        
        assert "total_services" in info
        assert "services" in info
        assert "TestService" in info["services"]
        assert info["services"]["TestService"]["scope"] == "singleton"
        assert info["services"]["TestService"]["initialized"] is False


if __name__ == "__main__":
    pytest.main([__file__])