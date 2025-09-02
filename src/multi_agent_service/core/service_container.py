"""Service container for dependency injection and lifecycle management."""

import asyncio
import logging
from typing import Dict, Any, Optional, Type, TypeVar, Callable, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceScope(Enum):
    """Service scope enumeration."""
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


@dataclass
class ServiceDefinition:
    """Service definition for dependency injection."""
    service_type: Type
    implementation: Optional[Type] = None
    factory: Optional[Callable] = None
    instance: Optional[Any] = None
    scope: ServiceScope = ServiceScope.SINGLETON
    dependencies: List[Type] = None
    initialized: bool = False
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class ServiceContainer:
    """Dependency injection container for managing service instances."""
    
    def __init__(self):
        """Initialize service container."""
        self._services: Dict[Type, ServiceDefinition] = {}
        self._instances: Dict[Type, Any] = {}
        self._initialization_order: List[Type] = []
        self._shutdown_order: List[Type] = []
        self._logger = logging.getLogger(f"{__name__}.ServiceContainer")
    
    def register_singleton(
        self, 
        service_type: Type[T], 
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[[], T]] = None,
        dependencies: Optional[List[Type]] = None
    ) -> 'ServiceContainer':
        """Register a singleton service."""
        return self._register_service(
            service_type, 
            implementation, 
            factory, 
            ServiceScope.SINGLETON,
            dependencies or []
        )
    
    def register_transient(
        self, 
        service_type: Type[T], 
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[[], T]] = None,
        dependencies: Optional[List[Type]] = None
    ) -> 'ServiceContainer':
        """Register a transient service."""
        return self._register_service(
            service_type, 
            implementation, 
            factory, 
            ServiceScope.TRANSIENT,
            dependencies or []
        )
    
    def register_instance(self, service_type: Type[T], instance: T) -> 'ServiceContainer':
        """Register a service instance."""
        definition = ServiceDefinition(
            service_type=service_type,
            instance=instance,
            scope=ServiceScope.SINGLETON,
            initialized=True
        )
        self._services[service_type] = definition
        self._instances[service_type] = instance
        self._logger.info(f"Registered instance for {service_type.__name__}")
        return self
    
    def _register_service(
        self,
        service_type: Type[T],
        implementation: Optional[Type[T]],
        factory: Optional[Callable],
        scope: ServiceScope,
        dependencies: List[Type]
    ) -> 'ServiceContainer':
        """Internal method to register a service."""
        if service_type in self._services:
            self._logger.warning(f"Service {service_type.__name__} already registered, overwriting")
        
        definition = ServiceDefinition(
            service_type=service_type,
            implementation=implementation or service_type,
            factory=factory,
            scope=scope,
            dependencies=dependencies
        )
        
        self._services[service_type] = definition
        self._logger.info(f"Registered {scope.value} service {service_type.__name__}")
        return self
    
    async def get_service(self, service_type: Type[T]) -> T:
        """Get a service instance."""
        if service_type not in self._services:
            raise ValueError(f"Service {service_type.__name__} not registered")
        
        definition = self._services[service_type]
        
        # For singleton services, return cached instance if available
        if definition.scope == ServiceScope.SINGLETON and service_type in self._instances:
            return self._instances[service_type]
        
        # Create new instance
        instance = await self._create_instance(definition)
        
        # Cache singleton instances
        if definition.scope == ServiceScope.SINGLETON:
            self._instances[service_type] = instance
            definition.instance = instance
            definition.initialized = True
        
        return instance
    
    async def _create_instance(self, definition: ServiceDefinition) -> Any:
        """Create a service instance."""
        try:
            # Resolve dependencies first
            resolved_dependencies = []
            for dep_type in definition.dependencies:
                dep_instance = await self.get_service(dep_type)
                resolved_dependencies.append(dep_instance)
            
            # Create instance using factory or constructor
            if definition.factory:
                if asyncio.iscoroutinefunction(definition.factory):
                    instance = await definition.factory(*resolved_dependencies)
                else:
                    instance = definition.factory(*resolved_dependencies)
            else:
                instance = definition.implementation(*resolved_dependencies)
            
            # Initialize if it has an async initialize method
            if hasattr(instance, 'initialize') and asyncio.iscoroutinefunction(instance.initialize):
                await instance.initialize()
            
            self._logger.debug(f"Created instance of {definition.service_type.__name__}")
            return instance
            
        except Exception as e:
            self._logger.error(f"Failed to create instance of {definition.service_type.__name__}: {str(e)}")
            raise
    
    async def initialize_all_services(self) -> bool:
        """Initialize all registered services in dependency order."""
        self._logger.info("Initializing all services...")
        
        try:
            # Build initialization order based on dependencies
            self._build_initialization_order()
            
            # Initialize services in order
            for service_type in self._initialization_order:
                if service_type not in self._instances:
                    await self.get_service(service_type)
            
            self._logger.info(f"Successfully initialized {len(self._initialization_order)} services")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to initialize services: {str(e)}")
            return False
    
    def _build_initialization_order(self) -> None:
        """Build service initialization order based on dependencies."""
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(service_type: Type) -> None:
            if service_type in temp_visited:
                raise ValueError(f"Circular dependency detected involving {service_type.__name__}")
            
            if service_type in visited:
                return
            
            temp_visited.add(service_type)
            
            # Visit dependencies first
            definition = self._services.get(service_type)
            if definition:
                for dep_type in definition.dependencies:
                    if dep_type in self._services:
                        visit(dep_type)
            
            temp_visited.remove(service_type)
            visited.add(service_type)
            order.append(service_type)
        
        # Visit all services
        for service_type in self._services:
            if service_type not in visited:
                visit(service_type)
        
        self._initialization_order = order
        self._shutdown_order = list(reversed(order))
        
        self._logger.debug(f"Service initialization order: {[s.__name__ for s in order]}")
    
    async def shutdown_all_services(self) -> None:
        """Shutdown all services in reverse order."""
        self._logger.info("Shutting down all services...")
        
        for service_type in self._shutdown_order:
            instance = self._instances.get(service_type)
            if instance:
                try:
                    # Call shutdown method if available
                    if hasattr(instance, 'shutdown') and asyncio.iscoroutinefunction(instance.shutdown):
                        await instance.shutdown()
                    elif hasattr(instance, 'cleanup') and asyncio.iscoroutinefunction(instance.cleanup):
                        await instance.cleanup()
                    
                    self._logger.debug(f"Shutdown service {service_type.__name__}")
                    
                except Exception as e:
                    self._logger.error(f"Error shutting down {service_type.__name__}: {str(e)}")
        
        # Clear instances
        self._instances.clear()
        
        # Reset initialization flags
        for definition in self._services.values():
            definition.initialized = False
            definition.instance = None
        
        self._logger.info("All services shutdown complete")
    
    def is_registered(self, service_type: Type) -> bool:
        """Check if a service type is registered."""
        return service_type in self._services
    
    def is_initialized(self, service_type: Type) -> bool:
        """Check if a service is initialized."""
        definition = self._services.get(service_type)
        return definition is not None and definition.initialized
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about registered services."""
        services_info = {}
        
        for service_type, definition in self._services.items():
            services_info[service_type.__name__] = {
                "scope": definition.scope.value,
                "initialized": definition.initialized,
                "has_instance": service_type in self._instances,
                "dependencies": [dep.__name__ for dep in definition.dependencies],
                "implementation": definition.implementation.__name__ if definition.implementation else None
            }
        
        return {
            "total_services": len(self._services),
            "initialized_services": len(self._instances),
            "services": services_info,
            "initialization_order": [s.__name__ for s in self._initialization_order],
            "shutdown_order": [s.__name__ for s in self._shutdown_order]
        }
    
    async def health_check_services(self) -> Dict[str, bool]:
        """Perform health check on all services."""
        results = {}
        
        for service_type, instance in self._instances.items():
            try:
                if hasattr(instance, 'health_check'):
                    if asyncio.iscoroutinefunction(instance.health_check):
                        results[service_type.__name__] = await instance.health_check()
                    else:
                        results[service_type.__name__] = instance.health_check()
                else:
                    # If no health check method, assume healthy if instance exists
                    results[service_type.__name__] = True
                    
            except Exception as e:
                self._logger.error(f"Health check failed for {service_type.__name__}: {str(e)}")
                results[service_type.__name__] = False
        
        return results


# Global service container instance
service_container = ServiceContainer()