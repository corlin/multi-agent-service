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


# 专利系统健康检查端点
@router.get("/health/patent")
async def patent_health_check() -> Dict[str, Any]:
    """
    专利系统健康检查端点.
    
    Returns:
        Dict: 专利系统健康状态
    """
    try:
        # 获取健康检查管理器
        health_check_manager = service_manager.get_service("health_check_manager")
        if not health_check_manager:
            return {
                "status": "error",
                "message": "Health check manager not available",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        # 获取专利Agent状态
        patent_status = health_check_manager.get_patent_agents_status()
        
        return {
            "status": "healthy" if patent_status.get("patent_agents_healthy", False) else "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "patent_agents": patent_status
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@router.get("/health/patent/detailed")
async def detailed_patent_health_check() -> Dict[str, Any]:
    """
    详细的专利系统健康检查端点.
    
    Returns:
        Dict: 详细的专利系统健康状态
    """
    try:
        # 获取健康检查管理器
        health_check_manager = service_manager.get_service("health_check_manager")
        if not health_check_manager:
            raise HTTPException(
                status_code=503,
                detail="Health check manager not available"
            )
        
        # 执行全面的专利健康检查
        comprehensive_status = await health_check_manager.comprehensive_patent_health_check()
        
        return comprehensive_status
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Patent health check failed: {str(e)}"
        )


@router.get("/health/patent/data-sources")
async def patent_data_sources_health_check() -> Dict[str, Any]:
    """
    专利数据源健康检查端点.
    
    Returns:
        Dict: 专利数据源健康状态
    """
    try:
        # 获取健康检查管理器
        health_check_manager = service_manager.get_service("health_check_manager")
        if not health_check_manager:
            raise HTTPException(
                status_code=503,
                detail="Health check manager not available"
            )
        
        # 检查专利API端点
        api_endpoints_status = await health_check_manager.check_patent_api_endpoints()
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data_sources": api_endpoints_status,
            "summary": {
                "total_sources": len(api_endpoints_status),
                "healthy_sources": len([
                    s for s in api_endpoints_status.values() 
                    if s.get('status') == 'healthy'
                ]),
                "overall_healthy": all(
                    s.get('status') == 'healthy' 
                    for s in api_endpoints_status.values()
                )
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Patent data sources health check failed: {str(e)}"
        )


@router.get("/health/patent/agent/{agent_id}")
async def patent_agent_health_check(agent_id: str) -> Dict[str, Any]:
    """
    特定专利Agent健康检查端点.
    
    Args:
        agent_id: 专利Agent ID
        
    Returns:
        Dict: 指定专利Agent的健康状态
    """
    try:
        # 获取健康检查管理器
        health_check_manager = service_manager.get_service("health_check_manager")
        if not health_check_manager:
            raise HTTPException(
                status_code=503,
                detail="Health check manager not available"
            )
        
        # 获取特定Agent状态
        agent_status = await health_check_manager.get_patent_agent_status(agent_id)
        
        if agent_status is None:
            raise HTTPException(
                status_code=404,
                detail=f"Patent agent {agent_id} not found in health monitoring"
            )
        
        return {
            "agent_id": agent_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": agent_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Patent agent health check failed: {str(e)}"
        )


@router.post("/health/patent/reset-metrics")
async def reset_patent_metrics() -> Dict[str, Any]:
    """
    重置专利监控指标端点.
    
    Returns:
        Dict: 重置操作结果
    """
    try:
        # 获取监控系统
        monitoring_system = service_manager.get_service("monitoring_system")
        if not monitoring_system:
            raise HTTPException(
                status_code=503,
                detail="Monitoring system not available"
            )
        
        # 重置专利指标
        await monitoring_system.reset_patent_metrics()
        
        return {
            "status": "success",
            "message": "Patent metrics reset successfully",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset patent metrics: {str(e)}"
        )