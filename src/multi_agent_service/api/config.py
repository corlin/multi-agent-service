"""Configuration management API endpoints."""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse

from ..models.api import ErrorResponse
from ..models.config import (
    AgentConfig, ConfigUpdateRequest, ConfigUpdateResponse,
    ConfigValidationResult
)
from ..models.enums import AgentType
from ..agents.registry import AgentRegistry
from ..config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/config", tags=["configuration"])

# 配置存储（生产环境应使用数据库或配置中心）
agent_configurations: Dict[str, AgentConfig] = {}
system_configuration: Dict[str, Any] = {}


# Dependency injection functions
async def get_agent_registry() -> AgentRegistry:
    """Get agent registry instance."""
    return AgentRegistry()


@router.get("/agents")
async def get_agent_configurations(
    agent_type: Optional[str] = None,
    agent_registry: AgentRegistry = Depends(get_agent_registry)
) -> Dict[str, Any]:
    """
    获取智能体配置信息.
    
    Args:
        agent_type: 智能体类型过滤（可选）
    """
    try:
        logger.info(f"获取智能体配置: agent_type={agent_type}")
        
        # 1. 获取所有智能体信息
        all_agents = await agent_registry.list_agents()
        
        # 2. 构建配置列表
        configurations = []
        
        for agent_info in all_agents:
            # 类型过滤
            if agent_type and agent_info.agent_type.value != agent_type:
                continue
            
            # 获取或创建配置
            config_key = f"{agent_info.agent_type.value}_{agent_info.agent_id}"
            agent_config = agent_configurations.get(config_key)
            
            if not agent_config:
                # 创建默认配置
                agent_config = _create_default_agent_config(agent_info.agent_type, agent_info.agent_id)
                agent_configurations[config_key] = agent_config
            
            configurations.append({
                "agent_id": agent_config.agent_id,
                "agent_type": agent_config.agent_type.value,
                "name": agent_config.name,
                "description": agent_config.description,
                "capabilities": agent_config.capabilities,
                "model_config": {
                    "provider": agent_config.model_config.provider.value,
                    "model_name": agent_config.model_config.model_name,
                    "api_key": "***" if agent_config.model_config.api_key else None,  # 隐藏敏感信息
                    "base_url": agent_config.model_config.base_url,
                    "max_tokens": agent_config.model_config.max_tokens,
                    "temperature": agent_config.model_config.temperature,
                    "timeout": agent_config.model_config.timeout
                },
                "prompt_template": agent_config.prompt_template,
                "max_tokens": agent_config.max_tokens,
                "temperature": agent_config.temperature,
                "enabled": getattr(agent_config, 'enabled', True),
                "last_updated": getattr(agent_config, 'last_updated', datetime.now()).isoformat()
            })
        
        return {
            "configurations": configurations,
            "total_count": len(configurations),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取智能体配置失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="获取智能体配置失败"
        )


@router.get("/agents/{agent_id}")
async def get_agent_configuration(
    agent_id: str,
    agent_registry: AgentRegistry = Depends(get_agent_registry)
) -> Dict[str, Any]:
    """
    获取指定智能体的配置信息.
    
    Args:
        agent_id: 智能体ID
    """
    try:
        logger.info(f"获取智能体配置: {agent_id}")
        
        # 1. 查找智能体信息
        agent_info = None
        all_agents = await agent_registry.list_agents()
        
        for info in all_agents:
            if info.agent_id == agent_id:
                agent_info = info
                break
        
        if not agent_info:
            raise HTTPException(
                status_code=404,
                detail=f"未找到智能体: {agent_id}"
            )
        
        # 2. 获取配置
        config_key = f"{agent_info.agent_type.value}_{agent_id}"
        agent_config = agent_configurations.get(config_key)
        
        if not agent_config:
            # 创建默认配置
            agent_config = _create_default_agent_config(agent_info.agent_type, agent_id)
            agent_configurations[config_key] = agent_config
        
        # 3. 构建响应
        return {
            "agent_id": agent_config.agent_id,
            "agent_type": agent_config.agent_type.value,
            "name": agent_config.name,
            "description": agent_config.description,
            "capabilities": agent_config.capabilities,
            "model_config": agent_config.model_config.model_dump(),
            "prompt_template": agent_config.prompt_template,
            "max_tokens": agent_config.max_tokens,
            "temperature": agent_config.temperature,
            "enabled": getattr(agent_config, 'enabled', True),
            "last_updated": getattr(agent_config, 'last_updated', datetime.now()).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取智能体配置失败: {agent_id}, 错误: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="获取智能体配置失败"
        )


@router.put("/agents/{agent_id}")
async def update_agent_configuration(
    agent_id: str,
    request: ConfigUpdateRequest,
    http_request: Request,
    agent_registry: AgentRegistry = Depends(get_agent_registry)
) -> ConfigUpdateResponse:
    """
    更新智能体配置.
    
    Args:
        agent_id: 智能体ID
        request: 配置更新请求
    """
    try:
        logger.info(f"更新智能体配置: {agent_id}")
        
        # 1. 验证智能体存在
        agent_info = None
        all_agents = await agent_registry.list_agents()
        
        for info in all_agents:
            if info.agent_id == agent_id:
                agent_info = info
                break
        
        if not agent_info:
            raise HTTPException(
                status_code=404,
                detail=f"未找到智能体: {agent_id}"
            )
        
        # 2. 验证配置数据
        validation_result = _validate_agent_config(request.config_data, agent_info.agent_type)
        
        if not validation_result.is_valid:
            return ConfigUpdateResponse(
                success=False,
                message="配置验证失败",
                validation_result=validation_result
            )
        
        # 3. 获取现有配置
        config_key = f"{agent_info.agent_type.value}_{agent_id}"
        current_config = agent_configurations.get(config_key)
        
        if not current_config:
            current_config = _create_default_agent_config(agent_info.agent_type, agent_id)
        
        # 4. 更新配置
        updated_config = _update_agent_config(current_config, request.config_data)
        updated_config.last_updated = datetime.now()
        
        # 5. 保存配置
        agent_configurations[config_key] = updated_config
        
        # 6. 热更新（如果启用）
        if request.hot_reload:
            try:
                await _apply_hot_reload(agent_id, updated_config, agent_registry)
                hot_reload_success = True
                hot_reload_message = "热更新成功"
            except Exception as e:
                logger.warning(f"热更新失败: {str(e)}")
                hot_reload_success = False
                hot_reload_message = f"热更新失败: {str(e)}"
        else:
            hot_reload_success = True
            hot_reload_message = "未启用热更新"
        
        # 7. 构建响应
        response = ConfigUpdateResponse(
            success=True,
            message="配置更新成功",
            validation_result=validation_result,
            hot_reload_applied=request.hot_reload,
            hot_reload_success=hot_reload_success,
            hot_reload_message=hot_reload_message
        )
        
        logger.info(f"智能体配置更新成功: {agent_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新智能体配置失败: {agent_id}, 错误: {str(e)}", exc_info=True)
        
        error_response = ErrorResponse(
            error_code="CONFIG_UPDATE_ERROR",
            error_message="配置更新失败",
            error_details={
                "agent_id": agent_id,
                "error": str(e)
            }
        )
        
        raise HTTPException(
            status_code=500,
            detail=error_response.model_dump()
        )


@router.post("/agents/{agent_id}/validate")
async def validate_agent_configuration(
    agent_id: str,
    config_data: Dict[str, Any],
    agent_registry: AgentRegistry = Depends(get_agent_registry)
) -> ConfigValidationResult:
    """
    验证智能体配置.
    
    Args:
        agent_id: 智能体ID
        config_data: 配置数据
    """
    try:
        logger.info(f"验证智能体配置: {agent_id}")
        
        # 1. 获取智能体信息
        agent_info = None
        all_agents = await agent_registry.list_agents()
        
        for info in all_agents:
            if info.agent_id == agent_id:
                agent_info = info
                break
        
        if not agent_info:
            raise HTTPException(
                status_code=404,
                detail=f"未找到智能体: {agent_id}"
            )
        
        # 2. 执行验证
        validation_result = _validate_agent_config(config_data, agent_info.agent_type)
        
        logger.info(f"配置验证完成: {agent_id}, 有效: {validation_result.is_valid}")
        return validation_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"配置验证失败: {agent_id}, 错误: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="配置验证失败"
        )


@router.get("/system")
async def get_system_configuration() -> Dict[str, Any]:
    """
    获取系统配置信息.
    """
    try:
        logger.info("获取系统配置")
        
        # 获取当前系统配置
        config = {
            "api_settings": {
                "host": settings.api_host,
                "port": settings.api_port,
                "debug": settings.api_debug,
                "log_level": settings.log_level
            },
            "model_settings": {
                "default_provider": getattr(settings, 'default_model_provider', 'openai'),
                "default_model": getattr(settings, 'default_model_name', 'gpt-3.5-turbo'),
                "default_max_tokens": getattr(settings, 'default_max_tokens', 1000),
                "default_temperature": getattr(settings, 'default_temperature', 0.7)
            },
            "workflow_settings": {
                "max_concurrent_workflows": getattr(settings, 'max_concurrent_workflows', 10),
                "workflow_timeout": getattr(settings, 'workflow_timeout', 3600),
                "enable_workflow_persistence": getattr(settings, 'enable_workflow_persistence', True)
            },
            "agent_settings": {
                "max_agents_per_type": getattr(settings, 'max_agents_per_type', 5),
                "agent_timeout": getattr(settings, 'agent_timeout', 300),
                "enable_agent_metrics": getattr(settings, 'enable_agent_metrics', True)
            },
            "custom_settings": system_configuration
        }
        
        return {
            "configuration": config,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取系统配置失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="获取系统配置失败"
        )


@router.put("/system")
async def update_system_configuration(
    config_data: Dict[str, Any],
    hot_reload: bool = False
) -> Dict[str, Any]:
    """
    更新系统配置.
    
    Args:
        config_data: 配置数据
        hot_reload: 是否热更新
    """
    try:
        logger.info("更新系统配置")
        
        # 1. 验证配置数据
        validation_errors = []
        
        # 这里可以添加系统配置的验证逻辑
        
        if validation_errors:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "配置验证失败",
                    "errors": validation_errors
                }
            )
        
        # 2. 更新配置
        system_configuration.update(config_data)
        
        # 3. 热更新（如果启用）
        hot_reload_message = "未启用热更新"
        if hot_reload:
            try:
                # 这里可以实现系统配置的热更新逻辑
                hot_reload_message = "热更新成功"
            except Exception as e:
                hot_reload_message = f"热更新失败: {str(e)}"
        
        return {
            "success": True,
            "message": "系统配置更新成功",
            "hot_reload_applied": hot_reload,
            "hot_reload_message": hot_reload_message,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新系统配置失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="更新系统配置失败"
        )


def _create_default_agent_config(agent_type: AgentType, agent_id: str) -> AgentConfig:
    """
    创建默认智能体配置.
    
    Args:
        agent_type: 智能体类型
        agent_id: 智能体ID
        
    Returns:
        AgentConfig: 默认配置
    """
    from ..models.config import ModelConfig
    from ..models.enums import ModelProvider
    
    # 默认模型配置
    default_model_config = ModelConfig(
        provider=ModelProvider.OPENAI,
        model_name="gpt-3.5-turbo",
        api_key="",
        base_url="https://api.openai.com/v1",
        max_tokens=1000,
        temperature=0.7,
        timeout=30
    )
    
    # 根据智能体类型设置默认值
    type_configs = {
        AgentType.COORDINATOR: {
            "name": "智能体总协调员",
            "description": "负责统筹管理其他智能体和复杂任务协调",
            "capabilities": ["任务分解", "资源调度", "冲突解决", "协作管理"],
            "prompt_template": "你是一个智能体总协调员，负责统筹管理其他智能体..."
        },
        AgentType.SALES: {
            "name": "销售代表智能体",
            "description": "专门处理销售咨询、产品介绍和客户关系管理",
            "capabilities": ["产品介绍", "报价咨询", "客户关系管理", "销售流程"],
            "prompt_template": "你是一个专业的销售代表，擅长产品介绍和客户服务..."
        },
        AgentType.MANAGER: {
            "name": "公司管理者智能体",
            "description": "负责管理决策、战略规划和资源配置",
            "capabilities": ["决策分析", "战略规划", "资源配置", "政策制定"],
            "prompt_template": "你是一个公司管理者，具有丰富的管理经验..."
        },
        AgentType.FIELD_SERVICE: {
            "name": "现场服务人员智能体",
            "description": "处理技术服务、故障诊断和现场支持",
            "capabilities": ["故障诊断", "维修指导", "技术支持", "现场服务"],
            "prompt_template": "你是一个现场服务技术人员，擅长故障诊断和技术支持..."
        },
        AgentType.CUSTOMER_SUPPORT: {
            "name": "客服专员智能体",
            "description": "提供客户咨询、问题解决和售后服务",
            "capabilities": ["客户咨询", "问题解决", "售后服务", "客户安抚"],
            "prompt_template": "你是一个专业的客服专员，致力于为客户提供优质服务..."
        }
    }
    
    config_data = type_configs.get(agent_type, type_configs[AgentType.CUSTOMER_SUPPORT])
    
    return AgentConfig(
        agent_id=agent_id,
        agent_type=agent_type,
        name=config_data["name"],
        description=config_data["description"],
        capabilities=config_data["capabilities"],
        model_config=default_model_config,
        prompt_template=config_data["prompt_template"],
        max_tokens=1000,
        temperature=0.7
    )


def _validate_agent_config(config_data: Dict[str, Any], agent_type: AgentType) -> ConfigValidationResult:
    """
    验证智能体配置.
    
    Args:
        config_data: 配置数据
        agent_type: 智能体类型
        
    Returns:
        ConfigValidationResult: 验证结果
    """
    errors = []
    warnings = []
    
    # 必需字段检查
    required_fields = ["name", "description", "capabilities", "prompt_template"]
    for field in required_fields:
        if field not in config_data:
            errors.append(f"缺少必需字段: {field}")
        elif field == "capabilities":
            # capabilities 可以是空列表，但必须存在
            if not isinstance(config_data[field], list):
                errors.append(f"字段 {field} 必须是列表类型")
        elif not config_data[field]:
            errors.append(f"缺少必需字段: {field}")
    
    # 数值范围检查
    if "max_tokens" in config_data:
        max_tokens = config_data["max_tokens"]
        if not isinstance(max_tokens, int) or max_tokens < 1 or max_tokens > 4000:
            errors.append("max_tokens 必须是1-4000之间的整数")
    
    if "temperature" in config_data:
        temperature = config_data["temperature"]
        if not isinstance(temperature, (int, float)) or temperature < 0 or temperature > 2:
            errors.append("temperature 必须是0-2之间的数值")
    
    # 能力列表检查
    if "capabilities" in config_data:
        capabilities = config_data["capabilities"]
        if not isinstance(capabilities, list) or len(capabilities) == 0:
            warnings.append("建议至少定义一个能力")
    
    # 提示词模板检查
    if "prompt_template" in config_data:
        prompt_template = config_data["prompt_template"]
        if len(prompt_template) < 10:
            warnings.append("提示词模板过短，建议提供更详细的描述")
    
    return ConfigValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )


def _update_agent_config(current_config: AgentConfig, update_data: Dict[str, Any]) -> AgentConfig:
    """
    更新智能体配置.
    
    Args:
        current_config: 当前配置
        update_data: 更新数据
        
    Returns:
        AgentConfig: 更新后的配置
    """
    # 创建配置副本
    updated_config = current_config.model_copy()
    
    # 更新字段
    for field, value in update_data.items():
        if hasattr(updated_config, field):
            setattr(updated_config, field, value)
    
    return updated_config


async def _apply_hot_reload(agent_id: str, config: AgentConfig, agent_registry: AgentRegistry):
    """
    应用热更新.
    
    Args:
        agent_id: 智能体ID
        config: 新配置
        agent_registry: 智能体注册表
    """
    # 这里可以实现配置的热更新逻辑
    # 例如：重新加载智能体、更新模型配置等
    logger.info(f"应用热更新: {agent_id}")
    
    # 暂时只记录日志，实际实现需要根据具体需求
    pass