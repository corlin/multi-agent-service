"""Agent routing and management API endpoints."""

import logging
import time
import uuid
from typing import Dict, Any, List

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse

from ..models.api import (
    RouteRequest, RouteResponse, AgentStatusRequest, AgentStatusResponse,
    ErrorResponse
)
from ..models.base import UserRequest
from ..models.enums import Priority, AgentType, AgentStatus
from ..services.intent_analyzer import IntentAnalyzer
from ..services.agent_router import AgentRouter
from ..agents.registry import AgentRegistry
from ..config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


# Dependency injection functions
async def get_intent_analyzer() -> IntentAnalyzer:
    """Get intent analyzer instance."""
    from ..services.model_clients.mock_client import MockModelClient
    from ..models.model_service import ModelConfig
    from ..models.enums import ModelProvider
    
    # Create a mock configuration for testing
    mock_config = ModelConfig(
        provider=ModelProvider.QWEN,
        model_name="qwen-turbo",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        #api_key="mock-key",
        enabled=True
    )
    model_client = MockModelClient(mock_config)
    return IntentAnalyzer(model_client)


async def get_agent_router() -> AgentRouter:
    """Get agent router instance."""
    intent_analyzer = await get_intent_analyzer()
    agent_registry = AgentRegistry()
    return AgentRouter(intent_analyzer, agent_registry)


async def get_agent_registry() -> AgentRegistry:
    """Get agent registry instance."""
    from ..core.service_manager import service_manager
    
    # Get properly initialized services from service manager
    if service_manager.is_initialized:
        try:
            return await service_manager.get_service(AgentRegistry)
        except Exception as e:
            logger.warning(f"Failed to get AgentRegistry from service manager: {e}")
    
    # Fallback to global instance
    from ..agents.registry import agent_registry
    return agent_registry


@router.post("/route", response_model=RouteResponse)
async def route_request(
    request: RouteRequest,
    http_request: Request,
    agent_router: AgentRouter = Depends(get_agent_router)
) -> RouteResponse:
    """
    智能体路由接口.
    
    根据用户输入进行意图识别，并返回推荐的智能体和路由决策信息。
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        logger.info(f"收到路由请求: {request_id}")
        
        # 1. 验证请求内容
        if not request.content.strip():
            raise HTTPException(
                status_code=400,
                detail="请求内容不能为空"
            )
        
        # 2. 创建用户请求对象
        user_request = UserRequest(
            request_id=request_id,
            user_id=request.user_id,
            content=request.content,
            context=request.context,
            priority=request.priority
        )
        
        # 3. 执行路由决策
        route_result, intent_result = await agent_router.route_request(
            user_request, 
            strategy="capability_based"
        )
        
        # 4. 构建响应
        processing_time = time.time() - start_time
        
        response = RouteResponse(
            intent_result=intent_result,
            selected_agent=route_result.selected_agent,
            routing_confidence=route_result.confidence,
            alternative_agents=route_result.alternative_agents,
            requires_collaboration=route_result.requires_collaboration,
            estimated_processing_time=route_result.estimated_processing_time
        )
        
        logger.info(f"路由请求处理成功: {request_id}, 选择智能体: {route_result.selected_agent}, 耗时: {processing_time:.2f}s")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"路由请求处理失败: {request_id}, 错误: {str(e)}", exc_info=True)
        
        error_response = ErrorResponse(
            error_code="ROUTING_ERROR",
            error_message="智能体路由失败",
            error_details={
                "request_id": request_id,
                "error": str(e)
            },
            request_id=request_id
        )
        
        raise HTTPException(
            status_code=500,
            detail=error_response.model_dump()
        )


@router.get("/status", response_model=AgentStatusResponse)
async def get_agents_status(
    agent_ids: str = None,
    agent_types: str = None,
    include_metrics: bool = False,
    agent_registry: AgentRegistry = Depends(get_agent_registry)
) -> AgentStatusResponse:
    """
    查询智能体状态接口.
    
    Args:
        agent_ids: 智能体ID列表，逗号分隔
        agent_types: 智能体类型列表，逗号分隔
        include_metrics: 是否包含性能指标
    """
    try:
        logger.info("收到智能体状态查询请求")
        
        # 1. 解析查询参数
        target_agent_ids = []
        if agent_ids:
            target_agent_ids = [aid.strip() for aid in agent_ids.split(",") if aid.strip()]
        
        target_agent_types = []
        if agent_types:
            type_strs = [at.strip() for at in agent_types.split(",") if at.strip()]
            for type_str in type_strs:
                try:
                    agent_type = AgentType(type_str)
                    target_agent_types.append(agent_type)
                except ValueError:
                    logger.warning(f"无效的智能体类型: {type_str}")
        
        # 2. 获取智能体状态信息
        agents_status = []
        total_count = 0
        active_count = 0
        
        # 获取所有注册的智能体
        all_agents = await agent_registry.list_agents()
        logger.info(f"Retrieved {len(all_agents)} agents from registry")
        
        for agent_info in all_agents:
            # 过滤条件检查
            if target_agent_ids and agent_info.agent_id not in target_agent_ids:
                continue
            
            if target_agent_types and agent_info.agent_type not in target_agent_types:
                continue
            
            # 构建状态信息
            status_info = {
                "agent_id": agent_info.agent_id,
                "agent_type": agent_info.agent_type.value,
                "name": agent_info.name,
                "status": agent_info.status.value,
                "current_load": agent_info.current_load,
                "max_load": agent_info.max_load,
                "load_ratio": agent_info.current_load / agent_info.max_load if agent_info.max_load > 0 else 0,
                "capabilities": agent_info.capabilities,
                "last_activity": agent_info.last_active.isoformat() if agent_info.last_active else None
            }
            
            # 包含性能指标
            if include_metrics:
                status_info["metrics"] = {
                    "total_requests": getattr(agent_info, 'total_requests', 0),
                    "successful_requests": getattr(agent_info, 'successful_requests', 0),
                    "failed_requests": getattr(agent_info, 'failed_requests', 0),
                    "average_response_time": getattr(agent_info, 'average_response_time', 0.0),
                    "success_rate": getattr(agent_info, 'success_rate', 0.0)
                }
            
            agents_status.append(status_info)
            total_count += 1
            
            if agent_info.status == AgentStatus.ACTIVE:
                active_count += 1
        
        # 3. 构建响应
        response = AgentStatusResponse(
            agents=agents_status,
            total_count=total_count,
            active_count=active_count
        )
        
        logger.info(f"智能体状态查询成功: 总数={total_count}, 活跃数={active_count}")
        return response
        
    except Exception as e:
        logger.error(f"智能体状态查询失败: {str(e)}", exc_info=True)
        
        error_response = ErrorResponse(
            error_code="AGENT_STATUS_ERROR",
            error_message="智能体状态查询失败",
            error_details={"error": str(e)}
        )
        
        raise HTTPException(
            status_code=500,
            detail=error_response.model_dump()
        )


@router.get("/types")
async def list_agent_types() -> Dict[str, Any]:
    """
    获取支持的智能体类型列表.
    """
    try:
        agent_types = []
        
        for agent_type in AgentType:
            type_info = {
                "type": agent_type.value,
                "name": agent_type.name,
                "description": _get_agent_type_description(agent_type)
            }
            agent_types.append(type_info)
        
        return {
            "agent_types": agent_types,
            "total_count": len(agent_types)
        }
        
    except Exception as e:
        logger.error(f"获取智能体类型列表失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="获取智能体类型列表失败"
        )


@router.get("/capabilities/{agent_type}")
async def get_agent_capabilities(
    agent_type: str,
    agent_registry: AgentRegistry = Depends(get_agent_registry)
) -> Dict[str, Any]:
    """
    获取指定智能体类型的能力信息.
    
    Args:
        agent_type: 智能体类型
    """
    try:
        # 验证智能体类型
        try:
            agent_type_enum = AgentType(agent_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"无效的智能体类型: {agent_type}"
            )
        
        # 获取智能体信息
        agent_info = agent_registry.get_agent_info_by_type(agent_type_enum)
        
        if not agent_info:
            raise HTTPException(
                status_code=404,
                detail=f"未找到智能体类型: {agent_type}"
            )
        
        return {
            "agent_type": agent_type,
            "name": agent_info.name,
            "description": agent_info.description,
            "capabilities": agent_info.capabilities,
            "status": agent_info.status.value,
            "supported_intents": _get_supported_intents(agent_type_enum)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取智能体能力信息失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="获取智能体能力信息失败"
        )


def _get_agent_type_description(agent_type: AgentType) -> str:
    """获取智能体类型描述."""
    descriptions = {
        AgentType.COORDINATOR: "智能体总协调员，负责统筹管理其他智能体和复杂任务协调",
        AgentType.SALES: "销售代表智能体，专门处理销售咨询、产品介绍和客户关系管理",
        AgentType.MANAGER: "公司管理者智能体，负责管理决策、战略规划和资源配置",
        AgentType.FIELD_SERVICE: "现场服务人员智能体，处理技术服务、故障诊断和现场支持",
        AgentType.CUSTOMER_SUPPORT: "客服专员智能体，提供客户咨询、问题解决和售后服务"
    }
    return descriptions.get(agent_type, "未知智能体类型")


def _get_supported_intents(agent_type: AgentType) -> List[str]:
    """获取智能体支持的意图类型."""
    from ..models.enums import IntentType
    
    intent_mappings = {
        AgentType.COORDINATOR: [
            IntentType.COLLABORATION_REQUIRED.value,
            IntentType.MANAGEMENT_DECISION.value
        ],
        AgentType.SALES: [
            IntentType.SALES_INQUIRY.value,
            IntentType.GENERAL_INQUIRY.value
        ],
        AgentType.MANAGER: [
            IntentType.MANAGEMENT_DECISION.value,
            IntentType.COLLABORATION_REQUIRED.value
        ],
        AgentType.FIELD_SERVICE: [
            IntentType.TECHNICAL_SERVICE.value,
            IntentType.CUSTOMER_SUPPORT.value
        ],
        AgentType.CUSTOMER_SUPPORT: [
            IntentType.CUSTOMER_SUPPORT.value,
            IntentType.GENERAL_INQUIRY.value
        ]
    }
    
    return intent_mappings.get(agent_type, [])