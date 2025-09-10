"""Monitoring and management API endpoints."""

import logging
import time
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from ..models.api import HealthCheckResponse, ErrorResponse
from ..models.enums import AgentStatus, WorkflowStatus
from ..agents.registry import AgentRegistry
from ..config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["monitoring"])

# 模板引擎
templates = Jinja2Templates(directory="src/multi_agent_service/templates")

# 服务启动时间
service_start_time = datetime.now()


# Dependency injection functions
async def get_agent_registry() -> AgentRegistry:
    """Get agent registry instance."""
    return AgentRegistry()


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    agent_registry: AgentRegistry = Depends(get_agent_registry)
) -> HealthCheckResponse:
    """
    健康检查接口.
    
    返回服务整体健康状态、运行时间、智能体状态摘要和系统指标。
    """
    try:
        logger.debug("执行健康检查")
        
        # 1. 计算运行时间
        uptime_seconds = int((datetime.now() - service_start_time).total_seconds())
        
        # 2. 获取智能体状态摘要
        agents_status = await _get_agents_status_summary(agent_registry)
        
        # 3. 获取系统指标
        system_metrics = _get_system_metrics()
        
        # 4. 判断整体服务状态
        service_status = "healthy"
        
        # 检查智能体状态
        if "error" in agents_status:
            service_status = "unhealthy"
        elif agents_status.get("total_agents", 0) == 0:
            service_status = "degraded"
        elif agents_status.get("total_agents", 0) > 0 and agents_status.get("active_agents", 0) / agents_status["total_agents"] < 0.5:
            service_status = "degraded"
        
        # 检查系统资源
        if system_metrics["memory_usage_percent"] > 90 or system_metrics["cpu_usage_percent"] > 90:
            service_status = "degraded"
        
        # 5. 构建响应
        response = HealthCheckResponse(
            status=service_status,
            version="0.1.0",
            uptime=uptime_seconds,
            agents_status=agents_status,
            system_metrics=system_metrics
        )
        
        logger.debug(f"健康检查完成: 状态={service_status}, 运行时间={uptime_seconds}s")
        return response
        
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}", exc_info=True)
        
        # 返回不健康状态
        return HealthCheckResponse(
            status="unhealthy",
            version="0.1.0",
            uptime=int((datetime.now() - service_start_time).total_seconds()),
            agents_status={"error": str(e)},
            system_metrics={}
        )


@router.get("/metrics")
async def get_system_metrics() -> Dict[str, Any]:
    """
    获取详细的系统性能指标.
    """
    try:
        logger.debug("获取系统指标")
        
        # 1. 基础系统指标
        metrics = _get_system_metrics()
        
        # 2. 服务特定指标
        service_metrics = {
            "service_uptime": int((datetime.now() - service_start_time).total_seconds()),
            "service_start_time": service_start_time.isoformat(),
            "api_version": "0.1.0"
        }
        
        # 3. 合并指标
        all_metrics = {
            **metrics,
            **service_metrics,
            "timestamp": datetime.now().isoformat()
        }
        
        return all_metrics
        
    except Exception as e:
        logger.error(f"获取系统指标失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="获取系统指标失败"
        )


@router.get("/stats/agents")
async def get_agent_statistics(
    agent_registry: AgentRegistry = Depends(get_agent_registry)
) -> Dict[str, Any]:
    """
    获取智能体统计信息.
    """
    try:
        logger.debug("获取智能体统计信息")
        
        # 1. 获取所有智能体信息
        all_agents = await agent_registry.list_agents()
        
        # 2. 统计各种指标
        stats = {
            "total_agents": len(all_agents),
            "active_agents": 0,
            "idle_agents": 0,
            "busy_agents": 0,
            "offline_agents": 0,
            "agent_types": {},
            "load_distribution": {},
            "performance_metrics": {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "average_response_time": 0.0
            }
        }
        
        total_response_time = 0.0
        response_time_count = 0
        
        for agent_info in all_agents:
            # 状态统计
            if agent_info.status == AgentStatus.ACTIVE:
                if agent_info.current_load > 0:
                    stats["busy_agents"] += 1
                else:
                    stats["idle_agents"] += 1
                stats["active_agents"] += 1
            else:
                stats["offline_agents"] += 1
            
            # 类型统计
            agent_type = agent_info.agent_type.value
            if agent_type not in stats["agent_types"]:
                stats["agent_types"][agent_type] = 0
            stats["agent_types"][agent_type] += 1
            
            # 负载分布
            load_ratio = agent_info.current_load / agent_info.max_load if agent_info.max_load > 0 else 0
            load_bucket = f"{int(load_ratio * 10) * 10}-{int(load_ratio * 10) * 10 + 10}%"
            if load_bucket not in stats["load_distribution"]:
                stats["load_distribution"][load_bucket] = 0
            stats["load_distribution"][load_bucket] += 1
            
            # 性能指标
            if hasattr(agent_info, 'total_requests'):
                stats["performance_metrics"]["total_requests"] += getattr(agent_info, 'total_requests', 0)
                stats["performance_metrics"]["successful_requests"] += getattr(agent_info, 'successful_requests', 0)
                stats["performance_metrics"]["failed_requests"] += getattr(agent_info, 'failed_requests', 0)
                
                avg_time = getattr(agent_info, 'average_response_time', 0.0)
                if avg_time > 0:
                    total_response_time += avg_time
                    response_time_count += 1
        
        # 计算平均响应时间
        if response_time_count > 0:
            stats["performance_metrics"]["average_response_time"] = total_response_time / response_time_count
        
        # 计算成功率
        total_requests = stats["performance_metrics"]["total_requests"]
        if total_requests > 0:
            stats["performance_metrics"]["success_rate"] = (
                stats["performance_metrics"]["successful_requests"] / total_requests
            ) * 100
        else:
            stats["performance_metrics"]["success_rate"] = 0.0
        
        stats["timestamp"] = datetime.now().isoformat()
        
        return stats
        
    except Exception as e:
        logger.error(f"获取智能体统计信息失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="获取智能体统计信息失败"
        )


@router.get("/stats/workflows")
async def get_workflow_statistics() -> Dict[str, Any]:
    """
    获取工作流统计信息.
    """
    try:
        logger.debug("获取工作流统计信息")
        
        # 从工作流API模块导入状态存储
        from .workflows import workflow_states
        
        # 统计各种指标
        stats = {
            "total_workflows": len(workflow_states),
            "status_distribution": {},
            "type_distribution": {},
            "completion_rate": 0.0,
            "average_execution_time": 0.0,
            "recent_activity": []
        }
        
        total_execution_time = 0.0
        completed_workflows = 0
        execution_time_count = 0
        
        for workflow_state in workflow_states.values():
            # 状态分布
            status = workflow_state.status.value
            if status not in stats["status_distribution"]:
                stats["status_distribution"][status] = 0
            stats["status_distribution"][status] += 1
            
            # 计算执行时间
            if workflow_state.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]:
                execution_time = (workflow_state.updated_at - workflow_state.created_at).total_seconds()
                total_execution_time += execution_time
                execution_time_count += 1
                
                if workflow_state.status == WorkflowStatus.COMPLETED:
                    completed_workflows += 1
            
            # 最近活动（最近24小时）
            if workflow_state.created_at > datetime.now() - timedelta(hours=24):
                stats["recent_activity"].append({
                    "workflow_id": workflow_state.workflow_id,
                    "status": workflow_state.status.value,
                    "created_at": workflow_state.created_at.isoformat(),
                    "progress": (workflow_state.current_step / workflow_state.total_steps) * 100 if workflow_state.total_steps > 0 else 0
                })
        
        # 计算完成率
        if stats["total_workflows"] > 0:
            stats["completion_rate"] = (completed_workflows / stats["total_workflows"]) * 100
        
        # 计算平均执行时间
        if execution_time_count > 0:
            stats["average_execution_time"] = total_execution_time / execution_time_count
        
        # 按创建时间排序最近活动
        stats["recent_activity"].sort(key=lambda x: x["created_at"], reverse=True)
        stats["recent_activity"] = stats["recent_activity"][:10]  # 只返回最近10个
        
        stats["timestamp"] = datetime.now().isoformat()
        
        return stats
        
    except Exception as e:
        logger.error(f"获取工作流统计信息失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="获取工作流统计信息失败"
        )


@router.get("/logs")
async def get_recent_logs(
    level: str = "INFO",
    limit: int = 100,
    since: Optional[str] = None
) -> Dict[str, Any]:
    """
    获取最近的日志记录.
    
    Args:
        level: 日志级别过滤 (DEBUG, INFO, WARNING, ERROR)
        limit: 返回条数限制
        since: 起始时间 (ISO格式)
    """
    try:
        logger.debug(f"获取最近日志: level={level}, limit={limit}")
        
        # 这里应该从实际的日志系统中获取日志
        # 暂时返回模拟数据
        logs = [
            {
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "logger": "multi_agent_service.api.monitoring",
                "message": "健康检查执行成功",
                "module": "monitoring"
            },
            {
                "timestamp": (datetime.now() - timedelta(minutes=1)).isoformat(),
                "level": "INFO",
                "logger": "multi_agent_service.services.agent_router",
                "message": "智能体路由完成",
                "module": "agent_router"
            }
        ]
        
        return {
            "logs": logs,
            "total_count": len(logs),
            "level_filter": level,
            "limit": limit,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取日志失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="获取日志失败"
        )


async def _get_agents_status_summary(agent_registry: AgentRegistry) -> Dict[str, Any]:
    """
    获取智能体状态摘要.
    
    Args:
        agent_registry: 智能体注册表
        
    Returns:
        Dict[str, Any]: 状态摘要
    """
    try:
        all_agents = await agent_registry.list_agents()
        
        summary = {
            "total_agents": len(all_agents),
            "active_agents": 0,
            "offline_agents": 0,
            "busy_agents": 0
        }
        
        for agent_info in all_agents:
            if agent_info.status == AgentStatus.ACTIVE:
                summary["active_agents"] += 1
                if agent_info.current_load > 0:
                    summary["busy_agents"] += 1
            else:
                summary["offline_agents"] += 1
        
        return summary
        
    except Exception as e:
        logger.warning(f"获取智能体状态摘要失败: {e}")
        return {"error": str(e)}


def _get_system_metrics() -> Dict[str, Any]:
    """
    获取系统性能指标.
    
    Returns:
        Dict[str, Any]: 系统指标
    """
    if not PSUTIL_AVAILABLE:
        return {
            "error": "psutil not available",
            "cpu_usage_percent": 0,
            "memory_usage_percent": 0,
            "disk_usage_percent": 0,
            "cpu_count": 1,
            "memory_total_gb": 0,
            "memory_used_gb": 0,
            "disk_total_gb": 0,
            "disk_used_gb": 0,
            "network_bytes_sent": 0,
            "network_bytes_recv": 0,
            "load_average": [0, 0, 0]
        }
    
    try:
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=0.1)  # Reduce interval for tests
        
        # 内存使用情况
        memory = psutil.virtual_memory()
        
        # 磁盘使用情况 - use current directory instead of root
        import os
        disk = psutil.disk_usage(os.getcwd())
        
        # 网络统计
        network = psutil.net_io_counters()
        
        return {
            "cpu_usage_percent": cpu_percent,
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "memory_used_gb": round(memory.used / (1024**3), 2),
            "memory_usage_percent": memory.percent,
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "disk_used_gb": round(disk.used / (1024**3), 2),
            "disk_usage_percent": round((disk.used / disk.total) * 100, 2),
            "network_bytes_sent": network.bytes_sent,
            "network_bytes_recv": network.bytes_recv,
            "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
        }
        
    except Exception as e:
        logger.warning(f"获取系统指标失败: {e}")
        return {
            "error": str(e),
            "cpu_usage_percent": 0,
            "memory_usage_percent": 0,
            "disk_usage_percent": 0,
            "cpu_count": 1,
            "memory_total_gb": 0,
            "memory_used_gb": 0,
            "disk_total_gb": 0,
            "disk_used_gb": 0,
            "network_bytes_sent": 0,
            "network_bytes_recv": 0,
            "load_average": [0, 0, 0]
        }


# 专利监控专用端点
@router.get("/patent/metrics")
async def get_patent_metrics() -> Dict[str, Any]:
    """
    获取专利分析系统专用指标.
    
    Returns:
        Dict[str, Any]: 专利系统指标
    """
    try:
        logger.debug("获取专利系统指标")
        
        # 获取监控系统实例
        from ..core.service_manager import service_manager
        monitoring_system = service_manager.get_service("monitoring_system")
        
        if not monitoring_system:
            raise HTTPException(
                status_code=503,
                detail="Monitoring system not available"
            )
        
        # 获取专利指标
        patent_metrics = await monitoring_system.get_patent_metrics()
        
        return patent_metrics
        
    except Exception as e:
        logger.error(f"获取专利系统指标失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取专利系统指标失败: {str(e)}"
        )


@router.get("/patent/dashboard")
async def get_patent_dashboard_data() -> Dict[str, Any]:
    """
    获取专利监控面板数据.
    
    Returns:
        Dict[str, Any]: 专利监控面板数据
    """
    try:
        logger.debug("获取专利监控面板数据")
        
        # 获取服务实例
        from ..core.service_manager import service_manager
        monitoring_system = service_manager.get_service("monitoring_system")
        health_check_manager = service_manager.get_service("health_check_manager")
        
        if not monitoring_system or not health_check_manager:
            raise HTTPException(
                status_code=503,
                detail="Required services not available"
            )
        
        # 获取专利指标
        patent_metrics = await monitoring_system.get_patent_metrics()
        
        # 获取专利健康状态
        patent_health = health_check_manager.get_patent_agents_status()
        
        # 检查专利告警
        patent_alerts = await monitoring_system.check_patent_alerts()
        
        # 构建面板数据
        dashboard_data = {
            "timestamp": datetime.now().isoformat(),
            "overview": {
                "total_patent_agents": patent_health.get("total_patent_agents", 0),
                "healthy_patent_agents": patent_health.get("healthy_patent_agents", 0),
                "patent_health_percentage": patent_health.get("patent_health_percentage", 0),
                "active_alerts": len(patent_alerts)
            },
            "performance": {
                "patent_analysis_count": patent_metrics.get("patent_analysis", {}).get("total_count", 0),
                "patent_analysis_success_rate": patent_metrics.get("patent_analysis", {}).get("success_rate", 0),
                "patent_analysis_avg_duration": patent_metrics.get("patent_analysis", {}).get("avg_duration", 0),
                "patent_cache_hit_rate": patent_metrics.get("patent_data_collection", {}).get("cache_hit_rate", 0),
                "patent_data_quality_avg": patent_metrics.get("patent_data_collection", {}).get("data_quality_avg", 0)
            },
            "activity": {
                "data_collection_count": patent_metrics.get("patent_data_collection", {}).get("total_count", 0),
                "search_count": patent_metrics.get("patent_search", {}).get("total_count", 0),
                "report_generation_count": patent_metrics.get("patent_reports", {}).get("total_count", 0),
                "api_calls_count": patent_metrics.get("patent_api_calls", {}).get("total_count", 0),
                "api_success_rate": patent_metrics.get("patent_api_calls", {}).get("success_rate", 0)
            },
            "agents_status": patent_health.get("patent_agents", {}),
            "alerts": patent_alerts,
            "charts_data": {
                "agent_health_distribution": _prepare_agent_health_chart_data(patent_health),
                "performance_trends": _prepare_performance_trends_data(patent_metrics),
                "activity_breakdown": _prepare_activity_breakdown_data(patent_metrics)
            }
        }
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"获取专利监控面板数据失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取专利监控面板数据失败: {str(e)}"
        )


@router.get("/patent/alerts")
async def get_patent_alerts() -> Dict[str, Any]:
    """
    获取专利系统告警信息.
    
    Returns:
        Dict[str, Any]: 专利系统告警
    """
    try:
        logger.debug("获取专利系统告警")
        
        # 获取监控系统实例
        from ..core.service_manager import service_manager
        monitoring_system = service_manager.get_service("monitoring_system")
        
        if not monitoring_system:
            raise HTTPException(
                status_code=503,
                detail="Monitoring system not available"
            )
        
        # 获取专利告警
        alerts = await monitoring_system.check_patent_alerts()
        
        # 按严重程度分类
        alerts_by_severity = {
            "critical": [],
            "warning": [],
            "info": []
        }
        
        for alert in alerts:
            severity = alert.get("severity", "info")
            if severity in alerts_by_severity:
                alerts_by_severity[severity].append(alert)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_alerts": len(alerts),
            "alerts_by_severity": alerts_by_severity,
            "all_alerts": alerts
        }
        
    except Exception as e:
        logger.error(f"获取专利系统告警失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取专利系统告警失败: {str(e)}"
        )


@router.get("/patent/performance-history")
async def get_patent_performance_history(
    hours: int = 24,
    metric: str = "analysis_duration"
) -> Dict[str, Any]:
    """
    获取专利系统性能历史数据.
    
    Args:
        hours: 历史数据时间范围（小时）
        metric: 指标类型
        
    Returns:
        Dict[str, Any]: 性能历史数据
    """
    try:
        logger.debug(f"获取专利性能历史数据: metric={metric}, hours={hours}")
        
        # 获取监控系统实例
        from ..core.service_manager import service_manager
        monitoring_system = service_manager.get_service("monitoring_system")
        
        if not monitoring_system:
            raise HTTPException(
                status_code=503,
                detail="Monitoring system not available"
            )
        
        # 计算时间范围
        since = datetime.now() - timedelta(hours=hours)
        
        # 获取指标历史数据
        metric_name = f"patent.{metric}"
        history_data = monitoring_system.metrics_collector.get_metric_history(
            metric_name, since=since
        )
        
        # 格式化数据用于图表显示
        chart_data = []
        for point in history_data:
            chart_data.append({
                "timestamp": point.timestamp.isoformat(),
                "value": point.value,
                "tags": point.tags
            })
        
        return {
            "metric": metric,
            "time_range_hours": hours,
            "data_points": len(chart_data),
            "history": chart_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取专利性能历史数据失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取专利性能历史数据失败: {str(e)}"
        )


def _prepare_agent_health_chart_data(patent_health: Dict[str, Any]) -> Dict[str, Any]:
    """准备Agent健康状态图表数据."""
    try:
        total_agents = patent_health.get("total_patent_agents", 0)
        healthy_agents = patent_health.get("healthy_patent_agents", 0)
        unhealthy_agents = total_agents - healthy_agents
        
        return {
            "type": "pie",
            "data": {
                "labels": ["健康", "不健康"],
                "datasets": [{
                    "data": [healthy_agents, unhealthy_agents],
                    "backgroundColor": ["#28a745", "#dc3545"],
                    "borderWidth": 1
                }]
            }
        }
    except Exception as e:
        logger.warning(f"准备Agent健康图表数据失败: {str(e)}")
        return {"type": "pie", "data": {"labels": [], "datasets": []}}


def _prepare_performance_trends_data(patent_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """准备性能趋势图表数据."""
    try:
        # 模拟趋势数据，实际应该从历史指标中获取
        hours = list(range(24))
        analysis_durations = [2.5 + (i % 5) * 0.3 for i in hours]  # 模拟数据
        success_rates = [95 + (i % 3) * 2 for i in hours]  # 模拟数据
        
        return {
            "type": "line",
            "data": {
                "labels": [f"{h}:00" for h in hours],
                "datasets": [
                    {
                        "label": "分析耗时(秒)",
                        "data": analysis_durations,
                        "borderColor": "#007bff",
                        "backgroundColor": "rgba(0, 123, 255, 0.1)",
                        "yAxisID": "y"
                    },
                    {
                        "label": "成功率(%)",
                        "data": success_rates,
                        "borderColor": "#28a745",
                        "backgroundColor": "rgba(40, 167, 69, 0.1)",
                        "yAxisID": "y1"
                    }
                ]
            }
        }
    except Exception as e:
        logger.warning(f"准备性能趋势图表数据失败: {str(e)}")
        return {"type": "line", "data": {"labels": [], "datasets": []}}


def _prepare_activity_breakdown_data(patent_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """准备活动分解图表数据."""
    try:
        data_collection = patent_metrics.get("patent_data_collection", {}).get("total_count", 0)
        search = patent_metrics.get("patent_search", {}).get("total_count", 0)
        analysis = patent_metrics.get("patent_analysis", {}).get("total_count", 0)
        reports = patent_metrics.get("patent_reports", {}).get("total_count", 0)
        
        return {
            "type": "bar",
            "data": {
                "labels": ["数据收集", "搜索增强", "分析处理", "报告生成"],
                "datasets": [{
                    "label": "活动次数",
                    "data": [data_collection, search, analysis, reports],
                    "backgroundColor": [
                        "#007bff",
                        "#28a745", 
                        "#ffc107",
                        "#17a2b8"
                    ],
                    "borderWidth": 1
                }]
            }
        }
    except Exception as e:
        logger.warning(f"准备活动分解图表数据失败: {str(e)}")
        return {"type": "bar", "data": {"labels": [], "datasets": []}}


# 专利监控面板页面
@router.get("/patent/dashboard/view", response_class=HTMLResponse)
async def patent_dashboard_view():
    """
    专利监控面板页面.
    
    Returns:
        HTMLResponse: 专利监控面板HTML页面
    """
    try:
        # 读取HTML模板文件
        import os
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "templates", 
            "patent_dashboard.html"
        )
        
        with open(template_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"加载专利监控面板页面失败: {str(e)}")
        return HTMLResponse(
            content=f"<html><body><h1>Error</h1><p>Failed to load dashboard: {str(e)}</p></body></html>",
            status_code=500
        )