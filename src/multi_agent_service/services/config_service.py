"""Configuration service for managing system configurations."""

import os
import logging
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from ..config.config_manager import ConfigManager, config_manager
from ..models.config import (
    AgentConfig, ModelConfig, WorkflowConfig, 
    ConfigValidationResult, ConfigUpdateRequest, ConfigUpdateResponse
)
from ..utils.exceptions import ConfigurationError, ValidationError


logger = logging.getLogger(__name__)


class ConfigService:
    """配置服务，提供配置管理的高级接口."""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """初始化配置服务.
        
        Args:
            config_manager: 配置管理器实例，如果为None则使用全局实例
        """
        self.config_manager = config_manager or config_manager
        self._initialized = False
    
    async def initialize(self) -> None:
        """异步初始化配置服务."""
        if self._initialized:
            return
        
        try:
            # 启动文件监控
            self.config_manager.start_file_watching()
            self._initialized = True
            logger.info("Configuration service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize configuration service: {e}")
            raise ConfigurationError(f"Configuration service initialization failed: {e}")
    
    async def shutdown(self) -> None:
        """关闭配置服务."""
        if not self._initialized:
            return
        
        try:
            # 停止文件监控
            self.config_manager.stop_file_watching()
            self._initialized = False
            logger.info("Configuration service shutdown successfully")
            
        except Exception as e:
            logger.error(f"Failed to shutdown configuration service: {e}")
    
    def get_agent_config(self, agent_id: str) -> Optional[AgentConfig]:
        """获取智能体配置.
        
        Args:
            agent_id: 智能体ID
            
        Returns:
            Optional[AgentConfig]: 智能体配置，如果不存在返回None
        """
        return self.config_manager.get_agent_config(agent_id)
    
    def get_all_agent_configs(self) -> Dict[str, AgentConfig]:
        """获取所有智能体配置.
        
        Returns:
            Dict[str, AgentConfig]: 所有智能体配置
        """
        return self.config_manager.get_all_agent_configs()
    
    def get_enabled_agent_configs(self) -> Dict[str, AgentConfig]:
        """获取所有启用的智能体配置.
        
        Returns:
            Dict[str, AgentConfig]: 启用的智能体配置
        """
        all_configs = self.config_manager.get_all_agent_configs()
        return {
            agent_id: config 
            for agent_id, config in all_configs.items() 
            if config.enabled
        }
    
    def get_model_config(self, model_id: str) -> Optional[ModelConfig]:
        """获取模型配置.
        
        Args:
            model_id: 模型ID
            
        Returns:
            Optional[ModelConfig]: 模型配置，如果不存在返回None
        """
        return self.config_manager.get_model_config(model_id)
    
    def get_all_model_configs(self) -> Dict[str, ModelConfig]:
        """获取所有模型配置.
        
        Returns:
            Dict[str, ModelConfig]: 所有模型配置
        """
        return self.config_manager.get_all_model_configs()
    
    def get_enabled_model_configs(self) -> Dict[str, ModelConfig]:
        """获取所有启用的模型配置.
        
        Returns:
            Dict[str, ModelConfig]: 启用的模型配置
        """
        all_configs = self.config_manager.get_all_model_configs()
        return {
            model_id: config 
            for model_id, config in all_configs.items() 
            if config.enabled
        }
    
    def get_workflow_config(self, workflow_id: str) -> Optional[WorkflowConfig]:
        """获取工作流配置.
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            Optional[WorkflowConfig]: 工作流配置，如果不存在返回None
        """
        return self.config_manager.get_workflow_config(workflow_id)
    
    def get_all_workflow_configs(self) -> Dict[str, WorkflowConfig]:
        """获取所有工作流配置.
        
        Returns:
            Dict[str, WorkflowConfig]: 所有工作流配置
        """
        return self.config_manager.get_all_workflow_configs()
    
    def get_enabled_workflow_configs(self) -> Dict[str, WorkflowConfig]:
        """获取所有启用的工作流配置.
        
        Returns:
            Dict[str, WorkflowConfig]: 启用的工作流配置
        """
        all_configs = self.config_manager.get_all_workflow_configs()
        return {
            workflow_id: config 
            for workflow_id, config in all_configs.items() 
            if config.enabled
        }
    
    def validate_agent_config(self, agent_id: str, config_data: Dict[str, Any]) -> ConfigValidationResult:
        """验证智能体配置.
        
        Args:
            agent_id: 智能体ID
            config_data: 配置数据
            
        Returns:
            ConfigValidationResult: 验证结果
        """
        result = ConfigValidationResult(is_valid=True)
        
        try:
            # 尝试创建配置对象进行验证
            config = AgentConfig(**config_data)
            
            # 检查模型配置是否存在
            if config.llm_config and config.llm_config.model_name:
                model_config = self.get_model_config(config.llm_config.model_name)
                if not model_config:
                    result.add_warning(f"Referenced model '{config.llm_config.model_name}' not found in model configurations")
            
            # 检查API密钥
            if config.llm_config:
                provider = config.llm_config.provider.value.lower()
                api_key_env = f"{provider.upper()}_API_KEY"
                if not os.getenv(api_key_env):
                    result.add_warning(f"Environment variable {api_key_env} not set")
            
        except Exception as e:
            result.add_error(f"Invalid agent configuration: {e}")
        
        return result
    
    def validate_model_config(self, model_id: str, config_data: Dict[str, Any]) -> ConfigValidationResult:
        """验证模型配置.
        
        Args:
            model_id: 模型ID
            config_data: 配置数据
            
        Returns:
            ConfigValidationResult: 验证结果
        """
        result = ConfigValidationResult(is_valid=True)
        
        try:
            # 尝试创建配置对象进行验证
            config = ModelConfig(**config_data)
            
            # 检查API密钥
            provider = config.provider.value.lower()
            api_key_env = f"{provider.upper()}_API_KEY"
            if not os.getenv(api_key_env) and "${" not in config.api_key:
                result.add_warning(f"Environment variable {api_key_env} not set and no placeholder in api_key")
            
        except Exception as e:
            result.add_error(f"Invalid model configuration: {e}")
        
        return result
    
    def validate_workflow_config(self, workflow_id: str, config_data: Dict[str, Any]) -> ConfigValidationResult:
        """验证工作流配置.
        
        Args:
            workflow_id: 工作流ID
            config_data: 配置数据
            
        Returns:
            ConfigValidationResult: 验证结果
        """
        result = ConfigValidationResult(is_valid=True)
        
        try:
            # 尝试创建配置对象进行验证
            config = WorkflowConfig(**config_data)
            
            # 检查参与的智能体是否存在
            all_agent_configs = self.get_all_agent_configs()
            for agent_id in config.participating_agents:
                if agent_id not in all_agent_configs:
                    result.add_error(f"Referenced agent '{agent_id}' not found in agent configurations")
            
            # 检查协调员智能体
            if config.coordinator_agent and config.coordinator_agent not in all_agent_configs:
                result.add_error(f"Coordinator agent '{config.coordinator_agent}' not found in agent configurations")
            
            # 检查执行顺序
            if config.execution_order:
                for agent_id in config.execution_order:
                    if agent_id not in config.participating_agents:
                        result.add_error(f"Agent '{agent_id}' in execution_order not in participating_agents")
            
            # 检查并行组
            if config.parallel_groups:
                for group in config.parallel_groups:
                    for agent_id in group:
                        if agent_id not in config.participating_agents:
                            result.add_error(f"Agent '{agent_id}' in parallel_groups not in participating_agents")
            
        except Exception as e:
            result.add_error(f"Invalid workflow configuration: {e}")
        
        return result
    
    async def update_agent_config(self, request: ConfigUpdateRequest) -> ConfigUpdateResponse:
        """更新智能体配置.
        
        Args:
            request: 配置更新请求
            
        Returns:
            ConfigUpdateResponse: 更新响应
        """
        try:
            # 验证配置
            validation_result = self.validate_agent_config(request.config_id, request.config_data)
            
            if request.validate_only:
                return ConfigUpdateResponse(
                    success=validation_result.is_valid,
                    message="Configuration validation completed",
                    validation_result=validation_result
                )
            
            if not validation_result.is_valid:
                return ConfigUpdateResponse(
                    success=False,
                    message="Configuration validation failed",
                    validation_result=validation_result
                )
            
            # 创建配置对象
            config = AgentConfig(**request.config_data)
            
            # 更新配置
            self.config_manager.update_agent_config(request.config_id, config)
            
            return ConfigUpdateResponse(
                success=True,
                message=f"Agent configuration '{request.config_id}' updated successfully",
                validation_result=validation_result,
                updated_config=config.model_dump()
            )
            
        except Exception as e:
            logger.error(f"Failed to update agent configuration: {e}")
            return ConfigUpdateResponse(
                success=False,
                message=f"Failed to update configuration: {e}"
            )
    
    async def update_model_config(self, request: ConfigUpdateRequest) -> ConfigUpdateResponse:
        """更新模型配置.
        
        Args:
            request: 配置更新请求
            
        Returns:
            ConfigUpdateResponse: 更新响应
        """
        try:
            # 验证配置
            validation_result = self.validate_model_config(request.config_id, request.config_data)
            
            if request.validate_only:
                return ConfigUpdateResponse(
                    success=validation_result.is_valid,
                    message="Configuration validation completed",
                    validation_result=validation_result
                )
            
            if not validation_result.is_valid:
                return ConfigUpdateResponse(
                    success=False,
                    message="Configuration validation failed",
                    validation_result=validation_result
                )
            
            # 创建配置对象
            config = ModelConfig(**request.config_data)
            
            # 更新配置
            self.config_manager.update_model_config(request.config_id, config)
            
            return ConfigUpdateResponse(
                success=True,
                message=f"Model configuration '{request.config_id}' updated successfully",
                validation_result=validation_result,
                updated_config=config.model_dump()
            )
            
        except Exception as e:
            logger.error(f"Failed to update model configuration: {e}")
            return ConfigUpdateResponse(
                success=False,
                message=f"Failed to update configuration: {e}"
            )
    
    async def update_workflow_config(self, request: ConfigUpdateRequest) -> ConfigUpdateResponse:
        """更新工作流配置.
        
        Args:
            request: 配置更新请求
            
        Returns:
            ConfigUpdateResponse: 更新响应
        """
        try:
            # 验证配置
            validation_result = self.validate_workflow_config(request.config_id, request.config_data)
            
            if request.validate_only:
                return ConfigUpdateResponse(
                    success=validation_result.is_valid,
                    message="Configuration validation completed",
                    validation_result=validation_result
                )
            
            if not validation_result.is_valid:
                return ConfigUpdateResponse(
                    success=False,
                    message="Configuration validation failed",
                    validation_result=validation_result
                )
            
            # 创建配置对象
            config = WorkflowConfig(**request.config_data)
            
            # 更新配置
            self.config_manager.update_workflow_config(request.config_id, config)
            
            return ConfigUpdateResponse(
                success=True,
                message=f"Workflow configuration '{request.config_id}' updated successfully",
                validation_result=validation_result,
                updated_config=config.model_dump()
            )
            
        except Exception as e:
            logger.error(f"Failed to update workflow configuration: {e}")
            return ConfigUpdateResponse(
                success=False,
                message=f"Failed to update configuration: {e}"
            )
    
    async def reload_configuration(self, config_type: Optional[str] = None) -> Dict[str, Any]:
        """重新加载配置.
        
        Args:
            config_type: 配置类型，None表示重新加载所有配置
            
        Returns:
            Dict[str, Any]: 重新加载结果
        """
        try:
            self.config_manager.reload_config(config_type)
            
            return {
                "success": True,
                "message": f"Configuration reloaded successfully: {config_type or 'all'}",
                "status": self.config_manager.get_config_status()
            }
            
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
            return {
                "success": False,
                "message": f"Failed to reload configuration: {e}",
                "status": self.config_manager.get_config_status()
            }
    
    def get_configuration_status(self) -> Dict[str, Any]:
        """获取配置状态.
        
        Returns:
            Dict[str, Any]: 配置状态信息
        """
        return self.config_manager.get_config_status()
    
    async def export_configuration(self, output_path: str, config_type: Optional[str] = None) -> Dict[str, Any]:
        """导出配置.
        
        Args:
            output_path: 输出文件路径
            config_type: 配置类型，None表示导出所有配置
            
        Returns:
            Dict[str, Any]: 导出结果
        """
        try:
            self.config_manager.export_config(output_path, config_type)
            
            return {
                "success": True,
                "message": f"Configuration exported to {output_path}",
                "output_path": output_path,
                "config_type": config_type or "all"
            }
            
        except Exception as e:
            logger.error(f"Failed to export configuration: {e}")
            return {
                "success": False,
                "message": f"Failed to export configuration: {e}",
                "output_path": output_path,
                "config_type": config_type or "all"
            }
    
    def get_environment_variables(self) -> Dict[str, str]:
        """获取相关的环境变量.
        
        Returns:
            Dict[str, str]: 环境变量字典
        """
        env_vars = {}
        
        # API密钥相关环境变量
        api_key_vars = [
            "OPENAI_API_KEY", "QWEN_API_KEY", "DEEPSEEK_API_KEY", "GLM_API_KEY"
        ]
        
        for var in api_key_vars:
            value = os.getenv(var)
            if value:
                # 隐藏敏感信息，只显示前几位和后几位
                if len(value) > 8:
                    env_vars[var] = f"{value[:4]}...{value[-4:]}"
                else:
                    env_vars[var] = "***"
            else:
                env_vars[var] = "Not Set"
        
        # 其他配置相关环境变量
        other_vars = [
            "API_HOST", "API_PORT", "API_DEBUG", "LOG_LEVEL", "LOG_FORMAT",
            "DATABASE_URL", "REDIS_URL"
        ]
        
        for var in other_vars:
            env_vars[var] = os.getenv(var, "Not Set")
        
        return env_vars
    
    def validate_environment(self) -> ConfigValidationResult:
        """验证环境配置.
        
        Returns:
            ConfigValidationResult: 验证结果
        """
        result = ConfigValidationResult(is_valid=True)
        
        # 检查必需的环境变量
        required_vars = []
        
        # 检查启用的模型配置需要的API密钥
        enabled_models = self.get_enabled_model_configs()
        for model_id, config in enabled_models.items():
            provider = config.provider.value.upper()
            api_key_var = f"{provider}_API_KEY"
            if api_key_var not in required_vars:
                required_vars.append(api_key_var)
        
        # 验证环境变量
        for var in required_vars:
            if not os.getenv(var):
                result.add_error(f"Required environment variable {var} is not set")
        
        # 检查配置文件
        config_dir = Path("config")
        if not config_dir.exists():
            result.add_warning("Configuration directory 'config' does not exist")
        else:
            required_files = ["agents.json", "models.json", "workflows.json"]
            for file in required_files:
                if not (config_dir / file).exists():
                    result.add_warning(f"Configuration file '{file}' does not exist")
        
        return result


# 全局配置服务实例
config_service = ConfigService()