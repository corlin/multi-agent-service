"""Startup validation utilities for multi-agent service."""

import asyncio
import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime

from .config.settings import settings
from .core.lifecycle_manager import lifecycle_manager


logger = logging.getLogger(__name__)


class StartupValidator:
    """Validates service startup and initialization."""
    
    def __init__(self):
        """Initialize startup validator."""
        self.logger = logging.getLogger(f"{__name__}.StartupValidator")
        self.validation_results: List[Tuple[str, bool, str]] = []
    
    async def validate_complete_startup(self) -> Dict[str, Any]:
        """Perform complete startup validation.
        
        Returns:
            dict: Comprehensive validation results
        """
        self.logger.info("🔍 Starting complete startup validation...")
        self.validation_results.clear()
        
        try:
            # Validate core services
            await self._validate_core_services()
            
            # Validate agent system
            await self._validate_agent_system()
            
            # Validate workflow system
            await self._validate_workflow_system()
            
            # Validate model services
            await self._validate_model_services()
            
            # Validate API endpoints
            await self._validate_api_endpoints()
            
            # Validate monitoring and logging
            await self._validate_monitoring_system()
            
            # Compile results
            return self._compile_validation_results()
            
        except Exception as e:
            self.logger.error(f"❌ Startup validation failed: {str(e)}")
            return {
                "overall_valid": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _validate_core_services(self) -> None:
        """Validate core service initialization."""
        self.logger.debug("Validating core services...")
        
        # Check lifecycle manager
        if lifecycle_manager and lifecycle_manager.service_manager:
            self._add_result("lifecycle_manager", True, "Lifecycle manager initialized")
            
            # Check service manager
            service_manager = lifecycle_manager.service_manager
            if service_manager.is_initialized and service_manager.is_running:
                self._add_result("service_manager", True, "Service manager running")
            else:
                self._add_result("service_manager", False, "Service manager not running")
            
            # Check service container
            container = service_manager.container
            if container:
                service_info = container.get_service_info()
                initialized_count = service_info.get("initialized_services", 0)
                total_count = service_info.get("total_services", 0)
                
                if initialized_count > 0:
                    self._add_result("service_container", True, 
                                   f"Service container: {initialized_count}/{total_count} services initialized")
                else:
                    self._add_result("service_container", False, "No services initialized")
            else:
                self._add_result("service_container", False, "Service container not available")
        else:
            self._add_result("lifecycle_manager", False, "Lifecycle manager not initialized")
    
    async def _validate_agent_system(self) -> None:
        """Validate agent system initialization."""
        self.logger.debug("Validating agent system...")
        
        try:
            from .agents.registry import AgentRegistry
            
            service_manager = lifecycle_manager.service_manager
            if service_manager and service_manager.container.is_initialized(AgentRegistry):
                agent_registry = await service_manager.container.get_service(AgentRegistry)
                
                if agent_registry:
                    stats = agent_registry.get_registry_stats()
                    registered_classes = stats.get("registered_classes", 0)
                    active_agents = stats.get("active_agents", 0)
                    
                    if registered_classes > 0:
                        self._add_result("agent_classes", True, 
                                       f"Agent classes registered: {registered_classes}")
                    else:
                        self._add_result("agent_classes", False, "No agent classes registered")
                    
                    if active_agents > 0:
                        self._add_result("agent_instances", True, 
                                       f"Active agent instances: {active_agents}")
                    else:
                        self._add_result("agent_instances", False, "No active agent instances")
                    
                    # Test agent health
                    health_results = await agent_registry.health_check_all()
                    healthy_agents = sum(health_results.values()) if health_results else 0
                    
                    if healthy_agents > 0:
                        self._add_result("agent_health", True, 
                                       f"Healthy agents: {healthy_agents}/{len(health_results)}")
                    else:
                        self._add_result("agent_health", False, "No healthy agents")
                else:
                    self._add_result("agent_registry", False, "Agent registry not available")
            else:
                self._add_result("agent_registry", False, "Agent registry not initialized")
                
        except Exception as e:
            self._add_result("agent_system", False, f"Agent system validation error: {str(e)}")
    
    async def _validate_workflow_system(self) -> None:
        """Validate workflow system initialization."""
        self.logger.debug("Validating workflow system...")
        
        try:
            from .workflows.graph_builder import GraphBuilder
            from .workflows.state_management import WorkflowStateManager
            from .models.enums import WorkflowType
            
            service_manager = lifecycle_manager.service_manager
            
            # Check graph builder
            if service_manager and service_manager.container.is_initialized(GraphBuilder):
                graph_builder = await service_manager.container.get_service(GraphBuilder)
                
                if graph_builder:
                    self._add_result("graph_builder", True, "Graph builder initialized")
                    
                    # Test workflow creation
                    workflow_types = [WorkflowType.SEQUENTIAL, WorkflowType.PARALLEL, WorkflowType.HIERARCHICAL]
                    successful_workflows = 0
                    
                    for workflow_type in workflow_types:
                        try:
                            test_graph = graph_builder.create_workflow_graph(workflow_type, [])
                            if test_graph:
                                successful_workflows += 1
                        except Exception as e:
                            self.logger.debug(f"Workflow creation test failed for {workflow_type}: {e}")
                    
                    if successful_workflows > 0:
                        self._add_result("workflow_creation", True, 
                                       f"Workflow creation: {successful_workflows}/{len(workflow_types)} types")
                    else:
                        self._add_result("workflow_creation", False, "Workflow creation failed")
                else:
                    self._add_result("graph_builder", False, "Graph builder not available")
            else:
                self._add_result("graph_builder", False, "Graph builder not initialized")
            
            # Check state manager
            if service_manager and service_manager.container.is_initialized(WorkflowStateManager):
                state_manager = await service_manager.container.get_service(WorkflowStateManager)
                
                if state_manager:
                    self._add_result("state_manager", True, "Workflow state manager initialized")
                else:
                    self._add_result("state_manager", False, "Workflow state manager not available")
            else:
                self._add_result("state_manager", False, "Workflow state manager not initialized")
                
        except Exception as e:
            self._add_result("workflow_system", False, f"Workflow system validation error: {str(e)}")
    
    async def _validate_model_services(self) -> None:
        """Validate model services initialization."""
        self.logger.debug("Validating model services...")
        
        try:
            from .services.model_router import ModelRouter
            
            service_manager = lifecycle_manager.service_manager
            if service_manager and service_manager.container.is_initialized(ModelRouter):
                model_router = await service_manager.container.get_service(ModelRouter)
                
                if model_router:
                    self._add_result("model_router", True, "Model router initialized")
                    
                    # Check available clients
                    available_clients = model_router.get_available_clients()
                    if available_clients:
                        client_names = [client_id for client_id, _ in available_clients]
                        self._add_result("model_clients", True, 
                                       f"Available model clients: {', '.join(client_names)}")
                    else:
                        self._add_result("model_clients", False, "No model clients available")
                    
                    # Test model selection
                    from .models.model_service import ModelRequest
                    test_request = ModelRequest(messages=[{"role": "user", "content": "test"}])
                    
                    try:
                        client_result = model_router.select_client(test_request)
                        if client_result:
                            self._add_result("model_selection", True, "Model selection working")
                        else:
                            self._add_result("model_selection", False, "Model selection failed")
                    except Exception as e:
                        self._add_result("model_selection", False, f"Model selection error: {str(e)}")
                else:
                    self._add_result("model_router", False, "Model router not available")
            else:
                self._add_result("model_router", False, "Model router not initialized")
                
        except Exception as e:
            self._add_result("model_services", False, f"Model services validation error: {str(e)}")
    
    async def _validate_api_endpoints(self) -> None:
        """Validate API endpoint availability."""
        self.logger.debug("Validating API endpoints...")
        
        try:
            # Check if FastAPI app is available
            try:
                from .main import app
                
                if app:
                    self._add_result("fastapi_app", True, "FastAPI application initialized")
                    
                    # Check router registration
                    router_count = len(app.routes)
                    if router_count > 0:
                        self._add_result("api_routes", True, f"API routes registered: {router_count}")
                    else:
                        self._add_result("api_routes", False, "No API routes registered")
                else:
                    self._add_result("fastapi_app", False, "FastAPI application not available")
            except ImportError as e:
                self._add_result("fastapi_app", False, f"FastAPI application import failed: {str(e)}")
                
        except Exception as e:
            self._add_result("api_endpoints", False, f"API endpoint validation error: {str(e)}")
    
    async def _validate_monitoring_system(self) -> None:
        """Validate monitoring and logging system."""
        self.logger.debug("Validating monitoring system...")
        
        try:
            from .utils.monitoring import MonitoringSystem
            from .utils.logging import LoggingSystem
            
            service_manager = lifecycle_manager.service_manager
            
            # Check monitoring system
            if service_manager and service_manager.container.is_initialized(MonitoringSystem):
                monitoring_system = await service_manager.container.get_service(MonitoringSystem)
                
                if monitoring_system:
                    self._add_result("monitoring_system", True, "Monitoring system initialized")
                else:
                    self._add_result("monitoring_system", False, "Monitoring system not available")
            else:
                self._add_result("monitoring_system", False, "Monitoring system not initialized")
            
            # Check logging system
            if service_manager and service_manager.container.is_initialized(LoggingSystem):
                logging_system = await service_manager.container.get_service(LoggingSystem)
                
                if logging_system:
                    self._add_result("logging_system", True, "Logging system initialized")
                else:
                    self._add_result("logging_system", False, "Logging system not available")
            else:
                self._add_result("logging_system", False, "Logging system not initialized")
                
        except Exception as e:
            self._add_result("monitoring_system", False, f"Monitoring system validation error: {str(e)}")
    
    def _add_result(self, component: str, success: bool, message: str) -> None:
        """Add validation result."""
        self.validation_results.append((component, success, message))
        
        if success:
            self.logger.debug(f"✅ {component}: {message}")
        else:
            self.logger.warning(f"❌ {component}: {message}")
    
    def _compile_validation_results(self) -> Dict[str, Any]:
        """Compile validation results into summary."""
        total_checks = len(self.validation_results)
        successful_checks = sum(1 for _, success, _ in self.validation_results if success)
        
        overall_valid = successful_checks == total_checks
        
        # Group results by category
        results_by_category = {}
        for component, success, message in self.validation_results:
            category = self._get_component_category(component)
            if category not in results_by_category:
                results_by_category[category] = []
            results_by_category[category].append({
                "component": component,
                "success": success,
                "message": message
            })
        
        # Calculate category success rates
        category_summary = {}
        for category, results in results_by_category.items():
            total = len(results)
            successful = sum(1 for r in results if r["success"])
            category_summary[category] = {
                "total_checks": total,
                "successful_checks": successful,
                "success_rate": successful / total if total > 0 else 0,
                "healthy": successful == total
            }
        
        return {
            "overall_valid": overall_valid,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_checks": total_checks,
                "successful_checks": successful_checks,
                "success_rate": successful_checks / total_checks if total_checks > 0 else 0
            },
            "categories": category_summary,
            "detailed_results": results_by_category,
            "failed_components": [
                {"component": comp, "message": msg} 
                for comp, success, msg in self.validation_results 
                if not success
            ]
        }
    
    def _get_component_category(self, component: str) -> str:
        """Get category for component."""
        category_mapping = {
            "lifecycle_manager": "core",
            "service_manager": "core",
            "service_container": "core",
            "agent_classes": "agents",
            "agent_instances": "agents",
            "agent_health": "agents",
            "agent_registry": "agents",
            "agent_system": "agents",
            "graph_builder": "workflows",
            "workflow_creation": "workflows",
            "state_manager": "workflows",
            "workflow_system": "workflows",
            "model_router": "models",
            "model_clients": "models",
            "model_selection": "models",
            "model_services": "models",
            "fastapi_app": "api",
            "api_routes": "api",
            "api_endpoints": "api",
            "monitoring_system": "monitoring",
            "logging_system": "monitoring"
        }
        
        return category_mapping.get(component, "other")


# Global startup validator instance
startup_validator = StartupValidator()


async def validate_startup() -> Dict[str, Any]:
    """Convenience function to validate startup.
    
    Returns:
        dict: Validation results
    """
    return await startup_validator.validate_complete_startup()