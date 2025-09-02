"""Chat completion API endpoints."""

import logging
import time
import uuid
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse

from ..models.api import ChatCompletionRequest, ChatCompletionResponse, ErrorResponse
from ..models.base import UserRequest
from ..models.enums import Priority
from ..services.intent_analyzer import IntentAnalyzer
from ..services.agent_router import AgentRouter
from ..services.model_router import ModelRouter
from ..agents.registry import AgentRegistry
from ..config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["chat"])


# Dependency injection functions
async def get_intent_analyzer() -> IntentAnalyzer:
    """Get intent analyzer instance."""
    # This will be properly injected in production
    # For now, return a mock instance
    from ..services.model_clients.mock_client import MockModelClient
    from ..models.model_service import ModelConfig
    from ..models.enums import ModelProvider
    
    # Create a mock configuration for testing
    mock_config = ModelConfig(
        provider=ModelProvider.OPENAI,
        model_name="gpt-3.5-turbo",
        base_url="https://api.openai.com/v1",
        api_key="mock-key",
        enabled=True
    )
    model_client = MockModelClient(mock_config)
    return IntentAnalyzer(model_client)


async def get_agent_router() -> AgentRouter:
    """Get agent router instance."""
    from ..core.service_manager import service_manager
    
    # Get properly initialized services from service manager
    if service_manager.is_initialized:
        try:
            return await service_manager.get_service(AgentRouter)
        except Exception as e:
            logger.warning(f"Failed to get AgentRouter from service manager: {e}")
    
    # Fallback to creating a new instance
    intent_analyzer = await get_intent_analyzer()
    from ..agents.registry import agent_registry
    return AgentRouter(intent_analyzer, agent_registry)


async def get_model_router() -> ModelRouter:
    """Get model router instance."""
    from ..core.service_manager import service_manager
    
    # Get properly initialized services from service manager
    if service_manager.is_initialized:
        try:
            return await service_manager.get_service(ModelRouter)
        except Exception as e:
            logger.warning(f"Failed to get ModelRouter from service manager: {e}")
    
    # Fallback to creating a new instance with default config
    from ..models.model_service import ModelConfig
    from ..models.enums import ModelProvider
    
    # Create default configurations
    default_configs = [
        ModelConfig(
            provider=ModelProvider.QWEN,
            model_name="qwen-turbo",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key="",  # Will be loaded from environment
            enabled=True
        )
    ]
    return ModelRouter(default_configs)


@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(
    request: ChatCompletionRequest,
    http_request: Request,
    agent_router: AgentRouter = Depends(get_agent_router),
    model_router: ModelRouter = Depends(get_model_router)
) -> ChatCompletionResponse:
    """
    OpenAI兼容的聊天完成接口.
    
    处理用户的聊天请求，通过意图识别和智能体路由提供响应。
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        logger.info(f"收到聊天完成请求: {request_id}")
        
        # 1. 验证请求格式
        if not request.messages or len(request.messages) == 0:
            raise HTTPException(
                status_code=400,
                detail="消息列表不能为空"
            )
        
        # 2. 提取用户消息内容
        user_message = ""
        for message in request.messages:
            if message.get("role") == "user":
                user_message = message.get("content", "")
                break
        
        if not user_message.strip():
            raise HTTPException(
                status_code=400,
                detail="未找到有效的用户消息内容"
            )
        
        # 3. 创建用户请求对象
        user_request = UserRequest(
            request_id=request_id,
            user_id=request.user_id,
            content=user_message,
            context=request.context,
            priority=Priority.NORMAL
        )
        
        # 4. 执行意图识别和智能体路由
        route_result, intent_result = await agent_router.route_request(user_request)
        
        logger.info(f"路由结果: 智能体={route_result.selected_agent}, 置信度={route_result.confidence}")
        
        # 5. 获取选中的智能体并处理请求
        from ..core.service_manager import service_manager
        
        # Try to get agent registry from service manager first
        if service_manager.is_initialized:
            try:
                registry = await service_manager.get_service(AgentRegistry)
            except Exception as e:
                logger.warning(f"Failed to get AgentRegistry from service manager: {e}")
                from ..agents.registry import agent_registry
                registry = agent_registry
        else:
            from ..agents.registry import agent_registry
            registry = agent_registry
        
        # Try to get agent by type first, then by exact ID
        agent = registry.get_agent(route_result.selected_agent.value)
        
        # If not found by exact ID, try to find by agent type
        if not agent:
            available_agents = registry.get_agents_by_type(route_result.selected_agent)
            if available_agents:
                agent = available_agents[0]  # Use the first available agent of this type
        
        # If still no agent found, try to create a default one
        if not agent:
            logger.warning(f"No agent found for {route_result.selected_agent.value}, attempting to create default agent")
            
            # Try to create a default agent for this type
            agent = await self._create_default_agent(route_result.selected_agent, registry, model_router)
        
        if not agent:
            # Log available agents for debugging
            all_agents = registry.get_all_agent_info()
            agent_list = [f"{info.agent_id} ({info.agent_type.value})" for info in all_agents]
            logger.error(f"No agent found for {route_result.selected_agent.value}. Available agents: {agent_list}")
            
            raise HTTPException(
                status_code=503,
                detail=f"智能体 {route_result.selected_agent.value} 不可用。可用智能体: {agent_list}"
            )
        
        # 6. 调用智能体处理请求
        agent_response = await agent.process_request(user_request)
        
        # 7. 构建OpenAI兼容的响应格式
        processing_time = time.time() - start_time
        
        response = ChatCompletionResponse(
            id=request_id,
            created=int(start_time),
            model=request.model or "multi-agent-service",
            choices=[
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": agent_response.response_content
                    },
                    "finish_reason": "stop"
                }
            ],
            usage={
                "prompt_tokens": len(user_message.split()),
                "completion_tokens": len(agent_response.response_content.split()),
                "total_tokens": len(user_message.split()) + len(agent_response.response_content.split())
            },
            agent_info={
                "agent_id": agent_response.agent_id,
                "agent_type": agent_response.agent_type.value,
                "confidence": agent_response.confidence,
                "processing_time": processing_time,
                "intent_type": intent_result.intent_type.value,
                "intent_confidence": intent_result.confidence,
                "requires_collaboration": route_result.requires_collaboration,
                "alternative_agents": [agent.value for agent in route_result.alternative_agents]
            }
        )
        
        logger.info(f"聊天完成请求处理成功: {request_id}, 耗时: {processing_time:.2f}s")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"聊天完成请求处理失败: {request_id}, 错误: {str(e)}", exc_info=True)
        
        # 返回错误响应
        error_response = ErrorResponse(
            error_code="CHAT_COMPLETION_ERROR",
            error_message="聊天完成请求处理失败",
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


@router.post("/chat/completions/stream")
async def chat_completions_stream(
    request: ChatCompletionRequest,
    http_request: Request,
    agent_router: AgentRouter = Depends(get_agent_router)
):
    """
    流式聊天完成接口（暂未实现）.
    
    TODO: 实现流式响应功能
    """
    raise HTTPException(
        status_code=501,
        detail="流式聊天完成功能暂未实现"
    )


async def _create_default_agent(agent_type, registry, model_router):
    """Create a default agent instance for the given type."""
    try:
        from ..models.config import AgentConfig, ModelConfig as ConfigModelConfig
        from ..models.enums import ModelProvider
        from ..models.model_service import ModelRequest
        
        # Create default agent configuration
        llm_config = ConfigModelConfig(
            provider=ModelProvider.QWEN,
            model_name="qwen-turbo",
            api_key="",  # Will be loaded from environment
            api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
            max_tokens=2000,
            temperature=0.7
        )
        
        agent_config = AgentConfig(
            agent_id=f"default_{agent_type.value}",
            agent_type=agent_type,
            name=f"默认{agent_type.value}智能体",
            description=f"默认创建的{agent_type.value}智能体",
            capabilities=["text_processing", "conversation", "problem_solving"],
            llm_config=llm_config,
            prompt_template="",
        )
        
        # Get model client
        dummy_request = ModelRequest(messages=[{"role": "user", "content": "test"}])
        client_result = model_router.select_client(dummy_request)
        
        if not client_result:
            logger.error("No model client available for default agent creation")
            return None
        
        client_id, model_client = client_result
        
        if not model_client:
            logger.error("Failed to get model client for default agent creation")
            return None
        
        # Register agent class if not already registered
        if not registry.is_agent_type_registered(agent_type):
            from ..agents.customer_support_agent import CustomerSupportAgent
            from ..agents.sales_agent import SalesAgent
            from ..agents.field_service_agent import FieldServiceAgent
            from ..agents.manager_agent import ManagerAgent
            from ..agents.coordinator_agent import CoordinatorAgent
            from ..models.enums import AgentType
            
            agent_classes = {
                AgentType.CUSTOMER_SUPPORT: CustomerSupportAgent,
                AgentType.SALES: SalesAgent,
                AgentType.FIELD_SERVICE: FieldServiceAgent,
                AgentType.MANAGER: ManagerAgent,
                AgentType.COORDINATOR: CoordinatorAgent,
            }
            
            if agent_type in agent_classes:
                registry.register_agent_class(agent_type, agent_classes[agent_type])
        
        # Create and start agent
        if await registry.create_agent(agent_config, model_client):
            if await registry.start_agent(agent_config.agent_id):
                logger.info(f"Successfully created default agent: {agent_config.agent_id}")
                return registry.get_agent(agent_config.agent_id)
        
        logger.error(f"Failed to create default agent for type: {agent_type}")
        return None
        
    except Exception as e:
        logger.error(f"Error creating default agent for type {agent_type}: {str(e)}")
        return None


@router.get("/chat/models")
async def list_chat_models() -> Dict[str, Any]:
    """
    获取可用的聊天模型列表.
    """
    try:
        # 返回支持的模型列表
        models = [
            {
                "id": "multi-agent-service",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "multi-agent-service",
                "permission": [],
                "root": "multi-agent-service",
                "parent": None
            }
        ]
        
        return {
            "object": "list",
            "data": models
        }
        
    except Exception as e:
        logger.error(f"获取模型列表失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="获取模型列表失败"
        )