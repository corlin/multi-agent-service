"""Agent registry and management system."""

import asyncio
import logging
from typing import Dict, List, Optional, Type
from datetime import datetime

from .base import BaseAgent
from ..models.base import AgentInfo, UserRequest
from ..models.config import AgentConfig
from ..models.enums import AgentType, AgentStatus
from ..services.model_client import BaseModelClient


logger = logging.getLogger(__name__)


class AgentRegistry:
    """智能体注册表，管理所有智能体实例."""
    
    def __init__(self):
        """初始化智能体注册表."""
        self._agents: Dict[str, BaseAgent] = {}
        self._agent_types: Dict[AgentType, List[str]] = {}
        self._agent_classes: Dict[AgentType, Type[BaseAgent]] = {}
        self._startup_order: List[str] = []
        self._shutdown_order: List[str] = []
        
        # 统计信息
        self._total_agents = 0
        self._active_agents = 0
        self._failed_agents = 0
        
        self.logger = logging.getLogger(f"{__name__}.AgentRegistry")
    
    def register_agent_class(self, agent_type: AgentType, agent_class: Type[BaseAgent]) -> None:
        """注册智能体类."""
        self._agent_classes[agent_type] = agent_class
        self.logger.info(f"Registered agent class for type: {agent_type.value}")
    
    async def create_agent(self, config: AgentConfig, model_client: BaseModelClient) -> bool:
        """创建智能体实例."""
        try:
            # 检查是否已存在
            if config.agent_id in self._agents:
                self.logger.warning(f"Agent {config.agent_id} already exists")
                return False
            
            # 获取智能体类
            agent_class = self._agent_classes.get(config.agent_type)
            if not agent_class:
                self.logger.error(f"No agent class registered for type: {config.agent_type.value}")
                return False
            
            # 创建智能体实例
            agent = agent_class(config, model_client)
            
            # 初始化智能体
            if not await agent.initialize():
                self.logger.error(f"Failed to initialize agent {config.agent_id}")
                return False
            
            # 注册到注册表
            self._agents[config.agent_id] = agent
            
            # 更新类型映射
            if config.agent_type not in self._agent_types:
                self._agent_types[config.agent_type] = []
            self._agent_types[config.agent_type].append(config.agent_id)
            
            # 更新启动顺序
            self._startup_order.append(config.agent_id)
            self._shutdown_order.insert(0, config.agent_id)  # 反向关闭顺序
            
            self._total_agents += 1
            self.logger.info(f"Successfully created agent {config.agent_id} ({config.agent_type.value})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating agent {config.agent_id}: {str(e)}")
            return False
    
    async def start_agent(self, agent_id: str) -> bool:
        """启动指定智能体."""
        agent = self._agents.get(agent_id)
        if not agent:
            self.logger.error(f"Agent {agent_id} not found")
            return False
        
        try:
            if await agent.start():
                self._active_agents += 1
                self.logger.info(f"Started agent {agent_id}")
                return True
            else:
                self.logger.error(f"Failed to start agent {agent_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error starting agent {agent_id}: {str(e)}")
            return False
    
    async def stop_agent(self, agent_id: str) -> bool:
        """停止指定智能体."""
        agent = self._agents.get(agent_id)
        if not agent:
            self.logger.error(f"Agent {agent_id} not found")
            return False
        
        try:
            if await agent.stop():
                self._active_agents = max(0, self._active_agents - 1)
                self.logger.info(f"Stopped agent {agent_id}")
                return True
            else:
                self.logger.error(f"Failed to stop agent {agent_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error stopping agent {agent_id}: {str(e)}")
            return False
    
    async def remove_agent(self, agent_id: str) -> bool:
        """移除智能体."""
        agent = self._agents.get(agent_id)
        if not agent:
            self.logger.error(f"Agent {agent_id} not found")
            return False
        
        try:
            # 先停止智能体
            await self.stop_agent(agent_id)
            
            # 清理资源
            await agent.cleanup()
            
            # 从注册表中移除
            del self._agents[agent_id]
            
            # 更新类型映射
            for agent_type, agent_list in self._agent_types.items():
                if agent_id in agent_list:
                    agent_list.remove(agent_id)
                    break
            
            # 更新启动顺序
            if agent_id in self._startup_order:
                self._startup_order.remove(agent_id)
            if agent_id in self._shutdown_order:
                self._shutdown_order.remove(agent_id)
            
            self._total_agents = max(0, self._total_agents - 1)
            self.logger.info(f"Removed agent {agent_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing agent {agent_id}: {str(e)}")
            return False
    
    async def start_all_agents(self) -> bool:
        """启动所有智能体."""
        self.logger.info("Starting all agents...")
        success_count = 0
        
        for agent_id in self._startup_order:
            if await self.start_agent(agent_id):
                success_count += 1
            else:
                self._failed_agents += 1
        
        self.logger.info(f"Started {success_count}/{len(self._startup_order)} agents")
        return success_count == len(self._startup_order)
    
    async def stop_all_agents(self) -> bool:
        """停止所有智能体."""
        self.logger.info("Stopping all agents...")
        success_count = 0
        
        for agent_id in self._shutdown_order:
            if await self.stop_agent(agent_id):
                success_count += 1
        
        self.logger.info(f"Stopped {success_count}/{len(self._shutdown_order)} agents")
        return success_count == len(self._shutdown_order)
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """获取智能体实例."""
        return self._agents.get(agent_id)
    
    def get_agents_by_type(self, agent_type: AgentType) -> List[BaseAgent]:
        """根据类型获取智能体列表."""
        agent_ids = self._agent_types.get(agent_type, [])
        return [self._agents[agent_id] for agent_id in agent_ids if agent_id in self._agents]
    
    def get_available_agents(self, agent_type: Optional[AgentType] = None) -> List[BaseAgent]:
        """获取可用的智能体列表."""
        agents = []
        
        if agent_type:
            candidates = self.get_agents_by_type(agent_type)
        else:
            candidates = list(self._agents.values())
        
        for agent in candidates:
            status = agent.get_status()
            if status.status in [AgentStatus.IDLE, AgentStatus.BUSY] and status.current_load < status.max_load:
                agents.append(agent)
        
        return agents
    
    def get_best_agent_for_request(self, request: UserRequest, agent_type: Optional[AgentType] = None) -> Optional[BaseAgent]:
        """为请求选择最佳智能体."""
        available_agents = self.get_available_agents(agent_type)
        
        if not available_agents:
            return None
        
        # 简单的负载均衡策略：选择负载最低的智能体
        best_agent = min(available_agents, key=lambda a: a.get_status().current_load)
        return best_agent
    
    def get_all_agent_info(self) -> List[AgentInfo]:
        """获取所有智能体的状态信息."""
        return [agent.get_status() for agent in self._agents.values()]
    
    def get_agent_info(self, agent_id: str) -> Optional[AgentInfo]:
        """获取指定智能体的状态信息."""
        agent = self._agents.get(agent_id)
        return agent.get_status() if agent else None
    
    async def list_agents(self) -> List[AgentInfo]:
        """获取所有智能体的状态信息列表."""
        return [agent.get_status() for agent in self._agents.values()]
    
    def get_agent_info_by_type(self, agent_type: AgentType) -> Optional[AgentInfo]:
        """根据智能体类型获取智能体信息."""
        # 查找该类型的第一个智能体
        for agent in self._agents.values():
            if agent.get_status().agent_type == agent_type:
                return agent.get_status()
        return None
    
    def get_registry_stats(self) -> Dict[str, any]:
        """获取注册表统计信息."""
        active_count = sum(1 for agent in self._agents.values() 
                          if agent.get_status().status in [AgentStatus.IDLE, AgentStatus.BUSY])
        
        error_count = sum(1 for agent in self._agents.values() 
                         if agent.get_status().status == AgentStatus.ERROR)
        
        offline_count = sum(1 for agent in self._agents.values() 
                           if agent.get_status().status == AgentStatus.OFFLINE)
        
        # 按类型统计
        type_stats = {}
        for agent_type, agent_ids in self._agent_types.items():
            type_stats[agent_type.value] = {
                "total": len(agent_ids),
                "active": sum(1 for aid in agent_ids 
                             if aid in self._agents and 
                             self._agents[aid].get_status().status in [AgentStatus.IDLE, AgentStatus.BUSY])
            }
        
        return {
            "total_agents": self._total_agents,
            "active_agents": active_count,
            "error_agents": error_count,
            "offline_agents": offline_count,
            "failed_agents": self._failed_agents,
            "type_statistics": type_stats,
            "registered_types": list(self._agent_classes.keys())
        }
    
    async def health_check_all(self) -> Dict[str, bool]:
        """对所有智能体进行健康检查."""
        results = {}
        
        for agent_id, agent in self._agents.items():
            try:
                results[agent_id] = await agent.health_check()
            except Exception as e:
                self.logger.error(f"Health check failed for agent {agent_id}: {str(e)}")
                results[agent_id] = False
        
        return results
    
    async def restart_failed_agents(self) -> int:
        """重启失败的智能体."""
        restarted_count = 0
        
        for agent_id, agent in self._agents.items():
            status = agent.get_status()
            if status.status == AgentStatus.ERROR:
                self.logger.info(f"Attempting to restart failed agent {agent_id}")
                
                try:
                    # 停止并重新启动
                    await agent.stop()
                    await asyncio.sleep(1)  # 短暂等待
                    
                    if await agent.start():
                        restarted_count += 1
                        self.logger.info(f"Successfully restarted agent {agent_id}")
                    else:
                        self.logger.error(f"Failed to restart agent {agent_id}")
                        
                except Exception as e:
                    self.logger.error(f"Error restarting agent {agent_id}: {str(e)}")
        
        return restarted_count
    
    def list_agent_types(self) -> List[AgentType]:
        """列出所有注册的智能体类型."""
        return list(self._agent_classes.keys())
    
    def is_agent_type_registered(self, agent_type: AgentType) -> bool:
        """检查智能体类型是否已注册."""
        return agent_type in self._agent_classes
    
    async def shutdown(self) -> None:
        """关闭注册表，清理所有资源."""
        self.logger.info("Shutting down agent registry...")
        
        # 停止所有智能体
        await self.stop_all_agents()
        
        # 清理所有智能体
        for agent in self._agents.values():
            try:
                await agent.cleanup()
            except Exception as e:
                self.logger.error(f"Error cleaning up agent {agent.agent_id}: {str(e)}")
        
        # 清理注册表
        self._agents.clear()
        self._agent_types.clear()
        self._startup_order.clear()
        self._shutdown_order.clear()
        
        self.logger.info("Agent registry shutdown complete")


# 全局智能体注册表实例
agent_registry = AgentRegistry()