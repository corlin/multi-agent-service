"""Tests for startup validator."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from src.multi_agent_service.startup_validator import StartupValidator, validate_startup
from src.multi_agent_service.core.lifecycle_manager import LifecycleManager
from src.multi_agent_service.core.service_manager import ServiceManager
from src.multi_agent_service.core.service_container import ServiceContainer


class TestStartupValidator:
    """Test startup validator functionality."""
    
    @pytest.fixture
    def validator(self):
        """Create startup validator instance."""
        return StartupValidator()
    
    @pytest.fixture
    def mock_lifecycle_manager(self):
        """Create mock lifecycle manager."""
        mock_container = Mock()
        mock_container.get_service_info = Mock(return_value={
            "initialized_services": 5,
            "total_services": 6
        })
        mock_container.is_initialized = Mock(return_value=True)
        mock_container.get_service = Mock()
        
        mock_service_manager = Mock()
        mock_service_manager._is_initialized = True
        mock_service_manager._is_running = True
        mock_service_manager.is_initialized = True
        mock_service_manager.is_running = True
        mock_service_manager.container = mock_container
        
        mock_lifecycle_manager = Mock()
        mock_lifecycle_manager.service_manager = mock_service_manager
        
        return mock_lifecycle_manager
    
    @pytest.mark.asyncio
    async def test_validate_complete_startup_success(self, validator, mock_lifecycle_manager):
        """Test complete startup validation with successful results."""
        with patch('src.multi_agent_service.startup_validator.lifecycle_manager', mock_lifecycle_manager):
            # Mock all validation methods to succeed
            validator._validate_core_services = AsyncMock()
            validator._validate_agent_system = AsyncMock()
            validator._validate_workflow_system = AsyncMock()
            validator._validate_model_services = AsyncMock()
            validator._validate_api_endpoints = AsyncMock()
            validator._validate_monitoring_system = AsyncMock()
            
            # Add some successful results
            validator.validation_results = [
                ("lifecycle_manager", True, "Lifecycle manager initialized"),
                ("service_manager", True, "Service manager running"),
                ("agent_registry", True, "Agent registry initialized"),
                ("model_router", True, "Model router initialized")
            ]
            
            result = await validator.validate_complete_startup()
            
            assert isinstance(result, dict)
            assert "overall_valid" in result
            assert "timestamp" in result
            assert "summary" in result
            assert "categories" in result
    
    @pytest.mark.asyncio
    async def test_validate_complete_startup_with_failures(self, validator, mock_lifecycle_manager):
        """Test complete startup validation with some failures."""
        with patch('src.multi_agent_service.startup_validator.lifecycle_manager', mock_lifecycle_manager):
            # Mock validation methods to add specific results
            async def mock_validate_core():
                validator._add_result("lifecycle_manager", True, "Lifecycle manager initialized")
                validator._add_result("service_manager", False, "Service manager not running")
            
            async def mock_validate_agents():
                validator._add_result("agent_registry", True, "Agent registry initialized")
            
            async def mock_validate_models():
                validator._add_result("model_router", False, "Model router failed")
            
            validator._validate_core_services = mock_validate_core
            validator._validate_agent_system = mock_validate_agents
            validator._validate_workflow_system = AsyncMock()
            validator._validate_model_services = mock_validate_models
            validator._validate_api_endpoints = AsyncMock()
            validator._validate_monitoring_system = AsyncMock()
            
            result = await validator.validate_complete_startup()
            
            assert result["overall_valid"] is False
            assert result["summary"]["successful_checks"] == 2
            assert result["summary"]["total_checks"] == 4
            assert len(result["failed_components"]) == 2
    
    @pytest.mark.asyncio
    async def test_validate_core_services(self, validator, mock_lifecycle_manager):
        """Test core services validation."""
        with patch('src.multi_agent_service.startup_validator.lifecycle_manager', mock_lifecycle_manager):
            await validator._validate_core_services()
            
            # Check that results were added
            assert len(validator.validation_results) > 0
            
            # Check specific results
            result_components = [result[0] for result in validator.validation_results]
            assert "lifecycle_manager" in result_components
            assert "service_manager" in result_components
            assert "service_container" in result_components
    
    @pytest.mark.asyncio
    async def test_validate_agent_system(self, validator, mock_lifecycle_manager):
        """Test agent system validation."""
        # Mock agent registry
        mock_agent_registry = AsyncMock()
        mock_agent_registry.get_registry_stats.return_value = {
            "registered_classes": 5,
            "active_agents": 3,
            "total_agents": 3
        }
        mock_agent_registry.health_check_all.return_value = {
            "agent_1": True,
            "agent_2": True,
            "agent_3": False
        }
        
        # Configure container mock
        mock_lifecycle_manager.service_manager.container.is_initialized.return_value = True
        mock_lifecycle_manager.service_manager.container.get_service.return_value = mock_agent_registry
        
        with patch('src.multi_agent_service.startup_validator.lifecycle_manager', mock_lifecycle_manager):
            await validator._validate_agent_system()
            
            # Check results
            result_components = [result[0] for result in validator.validation_results]
            assert "agent_classes" in result_components
            assert "agent_instances" in result_components
            assert "agent_health" in result_components
    
    @pytest.mark.asyncio
    async def test_validate_workflow_system(self, validator, mock_lifecycle_manager):
        """Test workflow system validation."""
        # Mock graph builder
        mock_graph_builder = AsyncMock()
        mock_graph_builder.create_workflow_graph.return_value = MagicMock()
        
        # Mock state manager
        mock_state_manager = AsyncMock()
        
        # Mock container responses
        def mock_is_initialized(service_type):
            return True
        
        def mock_get_service(service_type):
            if "GraphBuilder" in str(service_type):
                return mock_graph_builder
            elif "WorkflowStateManager" in str(service_type):
                return mock_state_manager
            return None
        
        mock_lifecycle_manager.service_manager.container.is_initialized.side_effect = mock_is_initialized
        mock_lifecycle_manager.service_manager.container.get_service.side_effect = mock_get_service
        
        with patch('src.multi_agent_service.startup_validator.lifecycle_manager', mock_lifecycle_manager):
            await validator._validate_workflow_system()
            
            # Check results
            result_components = [result[0] for result in validator.validation_results]
            assert "graph_builder" in result_components
            assert "workflow_creation" in result_components
            assert "state_manager" in result_components
    
    @pytest.mark.asyncio
    async def test_validate_model_services(self, validator, mock_lifecycle_manager):
        """Test model services validation."""
        # Mock model router
        mock_model_router = AsyncMock()
        mock_model_router.get_available_clients.return_value = [
            ("qwen_client", MagicMock()),
            ("deepseek_client", MagicMock())
        ]
        mock_model_router.select_client.return_value = ("qwen_client", MagicMock())
        
        mock_lifecycle_manager.service_manager.container.is_initialized.return_value = True
        mock_lifecycle_manager.service_manager.container.get_service.return_value = mock_model_router
        
        with patch('src.multi_agent_service.startup_validator.lifecycle_manager', mock_lifecycle_manager):
            await validator._validate_model_services()
            
            # Check results
            result_components = [result[0] for result in validator.validation_results]
            assert "model_router" in result_components
            assert "model_clients" in result_components
            assert "model_selection" in result_components
    
    @pytest.mark.asyncio
    async def test_validate_api_endpoints(self, validator):
        """Test API endpoints validation."""
        # Mock FastAPI app
        mock_app = MagicMock()
        mock_app.routes = [MagicMock() for _ in range(10)]  # 10 routes
        
        # Patch the import in the validation method
        with patch('src.multi_agent_service.startup_validator.app', mock_app):
            await validator._validate_api_endpoints()
            
            # Check results
            result_components = [result[0] for result in validator.validation_results]
            assert "fastapi_app" in result_components
            assert "api_routes" in result_components
    
    @pytest.mark.asyncio
    async def test_validate_monitoring_system(self, validator, mock_lifecycle_manager):
        """Test monitoring system validation."""
        # Mock monitoring and logging systems
        mock_monitoring = AsyncMock()
        mock_logging = AsyncMock()
        
        def mock_is_initialized(service_type):
            return True
        
        def mock_get_service(service_type):
            if "MonitoringSystem" in str(service_type):
                return mock_monitoring
            elif "LoggingSystem" in str(service_type):
                return mock_logging
            return None
        
        mock_lifecycle_manager.service_manager.container.is_initialized.side_effect = mock_is_initialized
        mock_lifecycle_manager.service_manager.container.get_service.side_effect = mock_get_service
        
        with patch('src.multi_agent_service.startup_validator.lifecycle_manager', mock_lifecycle_manager):
            await validator._validate_monitoring_system()
            
            # Check results
            result_components = [result[0] for result in validator.validation_results]
            assert "monitoring_system" in result_components
            assert "logging_system" in result_components
    
    def test_add_result(self, validator):
        """Test adding validation results."""
        validator._add_result("test_component", True, "Test message")
        
        assert len(validator.validation_results) == 1
        assert validator.validation_results[0] == ("test_component", True, "Test message")
    
    def test_compile_validation_results(self, validator):
        """Test compiling validation results."""
        # Add test results
        validator.validation_results = [
            ("lifecycle_manager", True, "OK"),
            ("service_manager", True, "OK"),
            ("agent_registry", False, "Failed"),
            ("model_router", True, "OK")
        ]
        
        result = validator._compile_validation_results()
        
        assert result["overall_valid"] is False
        assert result["summary"]["total_checks"] == 4
        assert result["summary"]["successful_checks"] == 3
        assert result["summary"]["success_rate"] == 0.75
        assert len(result["failed_components"]) == 1
        assert result["failed_components"][0]["component"] == "agent_registry"
    
    def test_get_component_category(self, validator):
        """Test component category mapping."""
        assert validator._get_component_category("lifecycle_manager") == "core"
        assert validator._get_component_category("agent_registry") == "agents"
        assert validator._get_component_category("graph_builder") == "workflows"
        assert validator._get_component_category("model_router") == "models"
        assert validator._get_component_category("fastapi_app") == "api"
        assert validator._get_component_category("monitoring_system") == "monitoring"
        assert validator._get_component_category("unknown_component") == "other"
    
    @pytest.mark.asyncio
    async def test_validate_startup_function(self, mock_lifecycle_manager):
        """Test the convenience validate_startup function."""
        with patch('src.multi_agent_service.startup_validator.lifecycle_manager', mock_lifecycle_manager), \
             patch.object(StartupValidator, 'validate_complete_startup') as mock_validate:
            
            mock_validate.return_value = {"overall_valid": True}
            
            result = await validate_startup()
            
            assert result == {"overall_valid": True}
            mock_validate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validation_exception_handling(self, validator):
        """Test exception handling during validation."""
        # Mock a validation method that raises an exception
        def failing_validation():
            raise Exception("Test validation error")
        
        validator._validate_core_services = failing_validation
        
        result = await validator.validate_complete_startup()
        
        assert result["overall_valid"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_agent_system_validation_with_no_registry(self, validator, mock_lifecycle_manager):
        """Test agent system validation when registry is not available."""
        mock_lifecycle_manager.service_manager.container.is_initialized.return_value = False
        
        with patch('src.multi_agent_service.startup_validator.lifecycle_manager', mock_lifecycle_manager):
            await validator._validate_agent_system()
            
            # Should have failure result
            failures = [result for result in validator.validation_results if not result[1]]
            assert len(failures) > 0
            assert any("agent_registry" in result[0] for result in failures)
    
    @pytest.mark.asyncio
    async def test_model_services_validation_with_no_clients(self, validator, mock_lifecycle_manager):
        """Test model services validation when no clients are available."""
        mock_model_router = AsyncMock()
        mock_model_router.get_available_clients.return_value = []  # No clients
        
        mock_lifecycle_manager.service_manager.container.is_initialized.return_value = True
        mock_lifecycle_manager.service_manager.container.get_service.return_value = mock_model_router
        
        with patch('src.multi_agent_service.startup_validator.lifecycle_manager', mock_lifecycle_manager):
            await validator._validate_model_services()
            
            # Should have failure for model clients
            failures = [result for result in validator.validation_results if not result[1]]
            assert any("model_clients" in result[0] for result in failures)


if __name__ == "__main__":
    pytest.main([__file__])