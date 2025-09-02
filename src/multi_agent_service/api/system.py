"""System management API endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any, Optional

from ..core.service_manager import service_manager
from ..core.lifecycle_manager import lifecycle_manager
from ..core.service_container import service_container

router = APIRouter(prefix="/api/v1/system", tags=["system"])


class SystemStatusResponse(BaseModel):
    """System status response model."""
    timestamp: datetime
    uptime_seconds: float
    healthy: bool
    service_manager: Dict[str, Any]
    service_container: Dict[str, Any]
    lifecycle: Dict[str, Any]


class ServiceInfo(BaseModel):
    """Service information model."""
    name: str
    initialized: bool
    healthy: bool
    dependencies: list
    scope: str


class RestartRequest(BaseModel):
    """Restart request model."""
    component: Optional[str] = None  # "all", "agents", "services", or specific service name
    force: bool = False


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status() -> SystemStatusResponse:
    """
    Get comprehensive system status.
    
    Returns:
        SystemStatusResponse: Complete system status information
    """
    try:
        # Get system status from service manager
        system_status = await service_manager.get_system_status()
        
        # Get health status
        health_status = await lifecycle_manager.health_check()
        
        # Get service container info
        container_info = service_container.get_service_info()
        
        return SystemStatusResponse(
            timestamp=datetime.now(),
            uptime_seconds=lifecycle_manager.uptime,
            healthy=health_status.get("healthy", False),
            service_manager=system_status.get("service_manager", {}),
            service_container=container_info,
            lifecycle=health_status.get("lifecycle", {})
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get system status: {str(e)}"
        )


@router.get("/services")
async def list_services() -> Dict[str, Any]:
    """
    List all registered services and their status.
    
    Returns:
        Dict: Services information
    """
    try:
        # Get service container info
        container_info = service_container.get_service_info()
        
        # Get health status for services
        health_status = await service_container.health_check_services()
        
        services = []
        for service_name, service_info in container_info.get("services", {}).items():
            services.append({
                "name": service_name,
                "initialized": service_info.get("initialized", False),
                "healthy": health_status.get(service_name, False),
                "dependencies": service_info.get("dependencies", []),
                "scope": service_info.get("scope", "unknown"),
                "implementation": service_info.get("implementation")
            })
        
        return {
            "total_services": len(services),
            "healthy_services": sum(1 for s in services if s["healthy"]),
            "initialized_services": sum(1 for s in services if s["initialized"]),
            "services": services,
            "initialization_order": container_info.get("initialization_order", []),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list services: {str(e)}"
        )


@router.post("/restart")
async def restart_system(request: RestartRequest) -> Dict[str, Any]:
    """
    Restart system components.
    
    Args:
        request: Restart request with component specification
        
    Returns:
        Dict: Restart operation result
    """
    try:
        component = request.component or "all"
        
        if component == "all":
            # Restart entire system
            success = await lifecycle_manager.restart()
            return {
                "success": success,
                "component": "all",
                "message": "System restart completed" if success else "System restart failed",
                "timestamp": datetime.now().isoformat()
            }
        
        elif component == "services":
            # Restart service manager
            success = await service_manager.restart()
            return {
                "success": success,
                "component": "services",
                "message": "Services restart completed" if success else "Services restart failed",
                "timestamp": datetime.now().isoformat()
            }
        
        elif component == "agents":
            # Restart agents only
            from ..agents.registry import AgentRegistry
            agent_registry = await service_container.get_service(AgentRegistry)
            
            # Stop all agents
            await agent_registry.stop_all_agents()
            
            # Start all agents
            success = await agent_registry.start_all_agents()
            
            return {
                "success": success,
                "component": "agents",
                "message": "Agents restart completed" if success else "Agents restart failed",
                "timestamp": datetime.now().isoformat()
            }
        
        else:
            # Restart specific service (not implemented yet)
            return {
                "success": False,
                "component": component,
                "message": f"Restart of specific component '{component}' not implemented",
                "timestamp": datetime.now().isoformat()
            }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Restart operation failed: {str(e)}"
        )


@router.post("/reload-config")
async def reload_configuration() -> Dict[str, Any]:
    """
    Reload system configuration.
    
    Returns:
        Dict: Configuration reload result
    """
    try:
        success = await service_manager.reload_configuration()
        
        return {
            "success": success,
            "message": "Configuration reloaded successfully" if success else "Configuration reload failed",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Configuration reload failed: {str(e)}"
        )


@router.get("/metrics")
async def get_system_metrics() -> Dict[str, Any]:
    """
    Get system performance metrics.
    
    Returns:
        Dict: System metrics
    """
    try:
        # Get monitoring system if available
        from ..utils.monitoring import MonitoringSystem
        
        if service_container.is_initialized(MonitoringSystem):
            monitoring_system = await service_container.get_service(MonitoringSystem)
            metrics = await monitoring_system.get_system_metrics()
        else:
            metrics = {"error": "Monitoring system not available"}
        
        # Add basic system info
        basic_metrics = {
            "uptime_seconds": lifecycle_manager.uptime,
            "timestamp": datetime.now().isoformat(),
            "service_count": len(service_container.get_service_info().get("services", {})),
            "healthy": lifecycle_manager.service_manager.is_healthy()
        }
        
        return {
            **basic_metrics,
            "detailed_metrics": metrics
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get system metrics: {str(e)}"
        )


@router.get("/logs")
async def get_system_logs(
    lines: int = 100,
    level: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get recent system logs.
    
    Args:
        lines: Number of log lines to return
        level: Log level filter (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        Dict: System logs
    """
    try:
        # This is a placeholder - in a real implementation, you would
        # integrate with your logging system to retrieve logs
        
        return {
            "message": "Log retrieval not implemented yet",
            "requested_lines": lines,
            "requested_level": level,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get system logs: {str(e)}"
        )