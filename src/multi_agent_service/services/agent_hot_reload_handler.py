"""Agent hot reload handler for dynamic agent reconfiguration."""

import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .hot_reload_service import ConfigChangeHandler, ConfigChangeEvent
from ..utils.exceptions import ConfigurationError

if TYPE_CHECKING:
    from ..services.agent_registry import AgentRegistry
    from ..workflows.graph_builder import GraphBuilder


logger = logging.getLogger(__name__)


class AgentHotReloadHandler(ConfigChangeHandler):
    """智能体热重载处理器，负责动态重新配置智能体."""
    
    def __init__(self, agent_registry: Optional['AgentRegistry'] = None, graph_builder: Optional['GraphBuilder'] = None):
        """初始化智能体热重载处理器.
        
        Args:
            agent_registry: 智能体注册表
            graph_builder: 图构建器
        """
        self.agent_registry = agent_registry
        self.graph_builder = graph_builder
        self._active_agents: Dict[str, Any] = {}
        self._active_workflows: Dict[str, Any] = {}
    
    async def handle_agent_config_change(self, event: ConfigChangeEvent) -> None:
        """处理智能体配置变更.
        
        Args:
            event: 配置变更事件
        """
        try:
            agent_id = event.config_id
            
            if event.change_type == 'created':
                await self._create_agent(agent_id, event.new_config)
            elif event.change_type == 'updated':
                await self._update_agent(agent_id, event.old_config, event.new_config)
            elif event.change_type == 'deleted':
                await self._delete_agent(agent_id, event.old_config)
            
            logger.info(f"Successfully handled agent config change: {event}")
            
        except Exception as e:
            logger.error(f"Failed to handle agent config change {event}: {e}")
            raise ConfigurationError(f"Agent hot reload failed: {e}")
    
    async def handle_model_config_change(self, event: ConfigChangeEvent) -> None:
        """处理模型配置变更.
        
        Args:
            event: 配置变更事件
        """
        try:
            model_id = event.config_id
            
            # 查找使用该模型的智能体
            affected_agents = self._find_agents_using_model(model_id)
            
            if event.change_type == 'created':
                logger.info(f"New model configuration created: {model_id}")
            elif event.change_type == 'updated':
                await self._update_agents_model_config(affected_agents, event.new_config)
            elif event.change_type == 'deleted':
                await self._handle_model_deletion(affected_agents, model_id)
            
            logger.info(f"Successfully handled model config change: {event}")
            
        except Exception as e:
            logger.error(f"Failed to handle model config change {event}: {e}")
            raise ConfigurationError(f"Model hot reload failed: {e}")
    
    async def handle_workflow_config_change(self, event: ConfigChangeEvent) -> None:
        """处理工作流配置变更.
        
        Args:
            event: 配置变更事件
        """
        try:
            workflow_id = event.config_id
            
            if event.change_type == 'created':
                await self._create_workflow(workflow_id, event.new_config)
            elif event.change_type == 'updated':
                await self._update_workflow(workflow_id, event.old_config, event.new_config)
            elif event.change_type == 'deleted':
                await self._delete_workflow(workflow_id, event.old_config)
            
            logger.info(f"Successfully handled workflow config change: {event}")
            
        except Exception as e:
            logger.error(f"Failed to handle workflow config change {event}: {e}")
            raise ConfigurationError(f"Workflow hot reload failed: {e}")
    
    async def _create_agent(self, agent_id: str, config: Dict[str, Any]) -> None:
        """创建新智能体.
        
        Args:
            agent_id: 智能体ID
            config: 智能体配置
        """
        if not config.get('enabled', True):
            logger.info(f"Skipping creation of disabled agent: {agent_id}")
            return
        
        if self.agent_registry:
            try:
                # 通过注册表创建智能体
                agent = await self.agent_registry.create_agent(agent_id, config)
                self._active_agents[agent_id] = agent
                logger.info(f"Created new agent: {agent_id}")
            except Exception as e:
                logger.error(f"Failed to create agent {agent_id}: {e}")
                raise
        else:
            logger.warning(f"Agent registry not available, cannot create agent: {agent_id}")
    
    async def _update_agent(self, agent_id: str, old_config: Dict[str, Any], new_config: Dict[str, Any]) -> None:
        """更新智能体配置.
        
        Args:
            agent_id: 智能体ID
            old_config: 旧配置
            new_config: 新配置
        """
        # 检查是否需要重新创建智能体
        needs_recreation = self._needs_agent_recreation(old_config, new_config)
        
        if needs_recreation:
            # 删除旧智能体并创建新的
            await self._delete_agent(agent_id, old_config)
            await self._create_agent(agent_id, new_config)
        else:
            # 仅更新配置
            if agent_id in self._active_agents:
                agent = self._active_agents[agent_id]
                if hasattr(agent, 'update_config'):
                    await agent.update_config(new_config)
                    logger.info(f"Updated agent configuration: {agent_id}")
                else:
                    logger.warning(f"Agent {agent_id} does not support config updates, recreating...")
                    await self._delete_agent(agent_id, old_config)
                    await self._create_agent(agent_id, new_config)
            else:
                # 智能体不存在，创建新的
                await self._create_agent(agent_id, new_config)
    
    async def _delete_agent(self, agent_id: str, config: Dict[str, Any]) -> None:
        """删除智能体.
        
        Args:
            agent_id: 智能体ID
            config: 智能体配置
        """
        if agent_id in self._active_agents:
            agent = self._active_agents[agent_id]
            
            # 停止智能体
            if hasattr(agent, 'stop'):
                try:
                    await agent.stop()
                except Exception as e:
                    logger.error(f"Error stopping agent {agent_id}: {e}")
            
            # 从注册表移除
            if self.agent_registry:
                try:
                    await self.agent_registry.unregister_agent(agent_id)
                except Exception as e:
                    logger.error(f"Error unregistering agent {agent_id}: {e}")
            
            # 从活跃列表移除
            del self._active_agents[agent_id]
            logger.info(f"Deleted agent: {agent_id}")
        else:
            logger.warning(f"Agent {agent_id} not found in active agents")
    
    async def _create_workflow(self, workflow_id: str, config: Dict[str, Any]) -> None:
        """创建新工作流.
        
        Args:
            workflow_id: 工作流ID
            config: 工作流配置
        """
        if not config.get('enabled', True):
            logger.info(f"Skipping creation of disabled workflow: {workflow_id}")
            return
        
        if self.graph_builder:
            try:
                # 通过图构建器创建工作流
                workflow = await self.graph_builder.create_workflow(workflow_id, config)
                self._active_workflows[workflow_id] = workflow
                logger.info(f"Created new workflow: {workflow_id}")
            except Exception as e:
                logger.error(f"Failed to create workflow {workflow_id}: {e}")
                raise
        else:
            logger.warning(f"Graph builder not available, cannot create workflow: {workflow_id}")
    
    async def _update_workflow(self, workflow_id: str, old_config: Dict[str, Any], new_config: Dict[str, Any]) -> None:
        """更新工作流配置.
        
        Args:
            workflow_id: 工作流ID
            old_config: 旧配置
            new_config: 新配置
        """
        # 检查是否需要重新创建工作流
        needs_recreation = self._needs_workflow_recreation(old_config, new_config)
        
        if needs_recreation:
            # 删除旧工作流并创建新的
            await self._delete_workflow(workflow_id, old_config)
            await self._create_workflow(workflow_id, new_config)
        else:
            # 仅更新配置
            if workflow_id in self._active_workflows:
                workflow = self._active_workflows[workflow_id]
                if hasattr(workflow, 'update_config'):
                    await workflow.update_config(new_config)
                    logger.info(f"Updated workflow configuration: {workflow_id}")
                else:
                    logger.warning(f"Workflow {workflow_id} does not support config updates, recreating...")
                    await self._delete_workflow(workflow_id, old_config)
                    await self._create_workflow(workflow_id, new_config)
            else:
                # 工作流不存在，创建新的
                await self._create_workflow(workflow_id, new_config)
    
    async def _delete_workflow(self, workflow_id: str, config: Dict[str, Any]) -> None:
        """删除工作流.
        
        Args:
            workflow_id: 工作流ID
            config: 工作流配置
        """
        if workflow_id in self._active_workflows:
            workflow = self._active_workflows[workflow_id]
            
            # 停止工作流
            if hasattr(workflow, 'stop'):
                try:
                    await workflow.stop()
                except Exception as e:
                    logger.error(f"Error stopping workflow {workflow_id}: {e}")
            
            # 从活跃列表移除
            del self._active_workflows[workflow_id]
            logger.info(f"Deleted workflow: {workflow_id}")
        else:
            logger.warning(f"Workflow {workflow_id} not found in active workflows")
    
    def _needs_agent_recreation(self, old_config: Dict[str, Any], new_config: Dict[str, Any]) -> bool:
        """判断是否需要重新创建智能体.
        
        Args:
            old_config: 旧配置
            new_config: 新配置
            
        Returns:
            bool: 是否需要重新创建
        """
        # 检查关键配置是否变更
        critical_fields = [
            'agent_type', 'llm_config.provider', 'llm_config.model_name'
        ]
        
        for field in critical_fields:
            old_value = self._get_nested_value(old_config, field)
            new_value = self._get_nested_value(new_config, field)
            if old_value != new_value:
                return True
        
        # 检查启用状态变更
        old_enabled = old_config.get('enabled', True)
        new_enabled = new_config.get('enabled', True)
        if old_enabled != new_enabled:
            return True
        
        return False
    
    def _needs_workflow_recreation(self, old_config: Dict[str, Any], new_config: Dict[str, Any]) -> bool:
        """判断是否需要重新创建工作流.
        
        Args:
            old_config: 旧配置
            new_config: 新配置
            
        Returns:
            bool: 是否需要重新创建
        """
        # 检查关键配置是否变更
        critical_fields = [
            'workflow_type', 'participating_agents', 'execution_order', 
            'parallel_groups', 'coordinator_agent'
        ]
        
        for field in critical_fields:
            old_value = old_config.get(field)
            new_value = new_config.get(field)
            if old_value != new_value:
                return True
        
        # 检查启用状态变更
        old_enabled = old_config.get('enabled', True)
        new_enabled = new_config.get('enabled', True)
        if old_enabled != new_enabled:
            return True
        
        return False
    
    def _get_nested_value(self, config: Dict[str, Any], field_path: str) -> Any:
        """获取嵌套字段值.
        
        Args:
            config: 配置字典
            field_path: 字段路径，如 'llm_config.provider'
            
        Returns:
            Any: 字段值
        """
        fields = field_path.split('.')
        value = config
        
        for field in fields:
            if isinstance(value, dict) and field in value:
                value = value[field]
            else:
                return None
        
        return value
    
    def _find_agents_using_model(self, model_id: str) -> List[str]:
        """查找使用指定模型的智能体.
        
        Args:
            model_id: 模型ID
            
        Returns:
            List[str]: 使用该模型的智能体ID列表
        """
        affected_agents = []
        
        for agent_id, agent in self._active_agents.items():
            if hasattr(agent, 'config') and hasattr(agent.config, 'llm_config'):
                if agent.config.llm_config.model_name == model_id:
                    affected_agents.append(agent_id)
        
        return affected_agents
    
    async def _update_agents_model_config(self, agent_ids: List[str], model_config: Dict[str, Any]) -> None:
        """更新智能体的模型配置.
        
        Args:
            agent_ids: 智能体ID列表
            model_config: 新的模型配置
        """
        for agent_id in agent_ids:
            if agent_id in self._active_agents:
                agent = self._active_agents[agent_id]
                if hasattr(agent, 'update_model_config'):
                    try:
                        await agent.update_model_config(model_config)
                        logger.info(f"Updated model config for agent {agent_id}")
                    except Exception as e:
                        logger.error(f"Failed to update model config for agent {agent_id}: {e}")
    
    async def _handle_model_deletion(self, agent_ids: List[str], model_id: str) -> None:
        """处理模型删除.
        
        Args:
            agent_ids: 受影响的智能体ID列表
            model_id: 被删除的模型ID
        """
        for agent_id in agent_ids:
            logger.warning(f"Model {model_id} deleted, agent {agent_id} may be affected")
            # 可以选择停用智能体或切换到备用模型
            if agent_id in self._active_agents:
                agent = self._active_agents[agent_id]
                if hasattr(agent, 'set_fallback_model'):
                    try:
                        await agent.set_fallback_model()
                        logger.info(f"Set fallback model for agent {agent_id}")
                    except Exception as e:
                        logger.error(f"Failed to set fallback model for agent {agent_id}: {e}")
    
    def get_active_agents(self) -> Dict[str, Any]:
        """获取活跃的智能体列表.
        
        Returns:
            Dict[str, Any]: 活跃智能体字典
        """
        return self._active_agents.copy()
    
    def get_active_workflows(self) -> Dict[str, Any]:
        """获取活跃的工作流列表.
        
        Returns:
            Dict[str, Any]: 活跃工作流字典
        """
        return self._active_workflows.copy()
    
    def get_status(self) -> Dict[str, Any]:
        """获取处理器状态.
        
        Returns:
            Dict[str, Any]: 状态信息
        """
        return {
            "active_agents_count": len(self._active_agents),
            "active_workflows_count": len(self._active_workflows),
            "active_agents": list(self._active_agents.keys()),
            "active_workflows": list(self._active_workflows.keys())
        }