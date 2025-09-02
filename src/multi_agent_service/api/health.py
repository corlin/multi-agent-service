"""Health check API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Dict, Any

from ..core.service_manager import service_manager
from ..core.lifecycle_manager import lifecycle_manager

router = APIRouter(prefix="/api/v1", tags=["health"])


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: datetime
    version: str
    services: Dict[str, Any]
    uptime_seconds: float
    lifecycle: Dict[str, Any]


class DetailedHealthResponse(BaseModel):
    """Detailed health check response model."""
    overall_healthy: bool
    timestamp: datetime
    version: str
    uptime_seconds: float
    services: Dict[str, Any]
    agents: Dict[str, Any]
    lifecycle: Dict[str, Any]
    system_status: Dict[str, Any]


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Basic health check endpoint.
    
    Returns:
        HealthResponse: Current service health status
    """
    try:
        # Get health status from lifecycle manager
        health_status = await lifecycle_manager.health_check()
        
        # Determine overall status
        status = "healthy" if health_status.get("healthy", False) else "unhealthy"
        
        # Get uptime
        uptime = lifecycle_manager.uptime
        
        return HealthResponse(
            status=status,
            timestamp=datetime.now(timezone.utc),
            version="0.1.0",
            services=health_status.get("services", {}),
            uptime_seconds=uptime,
            lifecycle=health_status.get("lifecycle", {})
        )
        
    except Exception as e:
        return HealthResponse(
            status="error",
            timestamp=datetime.now(timezone.utc),
            version="0.1.0",
            services={"error": str(e)},
            uptime_seconds=0.0,
            lifecycle={}
        )


@router.get("/health/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check() -> DetailedHealthResponse:
    """
    Detailed health check endpoint with comprehensive system status.
    
    Returns:
        DetailedHealthResponse: Comprehensive system health status
    """
    try:
        # Get comprehensive health status
        health_status = await lifecycle_manager.health_check()
        system_status = await service_manager.get_system_status()
        
        return DetailedHealthResponse(
            overall_healthy=health_status.get("healthy", False),
            timestamp=datetime.now(timezone.utc),
            version="0.1.0",
            uptime_seconds=lifecycle_manager.uptime,
            services=health_status.get("services", {}),
            agents=health_status.get("services", {}).get("agents", {}),
            lifecycle=health_status.get("lifecycle", {}),
            system_status=system_status
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Health check failed: {str(e)}"
        )


@router.get("/health/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check endpoint for container orchestration.
    
    Returns:
        Dict: Readiness status
    """
    try:
        is_ready = (
            lifecycle_manager.service_manager.is_initialized and
            lifecycle_manager.service_manager.is_running and
            not lifecycle_manager._is_shutting_down
        )
        
        return {
            "ready": is_ready,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "initialized": lifecycle_manager.service_manager.is_initialized,
            "running": lifecycle_manager.service_manager.is_running,
            "shutting_down": lifecycle_manager._is_shutting_down
        }
        
    except Exception as e:
        return {
            "ready": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@router.get("/health/live")
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness check endpoint for container orchestration.
    
    Returns:
        Dict: Liveness status
    """
    try:
        # Simple liveness check - if we can respond, we're alive
        return {
            "alive": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": lifecycle_manager.uptime
        }
        
    except Exception as e:
        return {
            "alive": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }