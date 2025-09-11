"""Patent agent registration module for integrating patent agents into the existing system."""

import logging
from typing import Dict, Type, List

from .registry import AgentRegistry
from .base import BaseAgent
from ..models.enums import AgentType

# Import patent agents
from .patent.base import PatentBaseAgent
from .patent.data_collection_agent import PatentDataCollectionAgent
from .patent.coordinator_agent import PatentCoordinatorAgent
from .patent.search_agent import PatentSearchAgent
from .patent.analysis_agent import PatentAnalysisAgent
from .patent.report_agent import PatentReportAgent


logger = logging.getLogger(__name__)


class PatentAgentRegistry:
    """专利Agent注册器，负责将所有专利Agent注册到现有的AgentRegistry中."""
    
    def __init__(self, agent_registry: AgentRegistry):
        """初始化专利Agent注册器."""
        self.agent_registry = agent_registry
        self.registered_patent_agents: Dict[AgentType, Type[BaseAgent]] = {}
        
        # 专利Agent类映射
        self.patent_agent_classes = {
            AgentType.PATENT_DATA_COLLECTION: PatentDataCollectionAgent,
            AgentType.PATENT_COORDINATOR: PatentCoordinatorAgent,
            AgentType.PATENT_SEARCH: PatentSearchAgent,
            AgentType.PATENT_ANALYSIS: PatentAnalysisAgent,
            AgentType.PATENT_REPORT: PatentReportAgent,
        }
        
        self.logger = logging.getLogger(f"{__name__}.PatentAgentRegistry")
    
    def register_all_patent_agents(self) -> bool:
        """注册所有专利Agent到现有的AgentRegistry."""
        try:
            self.logger.info("Starting patent agent registration...")
            self.logger.info(f"Available patent agent classes: {list(self.patent_agent_classes.keys())}")
            
            success_count = 0
            total_count = len(self.patent_agent_classes)
            
            for agent_type, agent_class in self.patent_agent_classes.items():
                try:
                    self.logger.info(f"Attempting to register patent agent: {agent_type.value} -> {agent_class.__name__}")
                    
                    # 检查Agent类型是否已经注册
                    if self.agent_registry.is_agent_type_registered(agent_type):
                        self.logger.warning(f"Agent type {agent_type.value} already registered, skipping")
                        self.registered_patent_agents[agent_type] = agent_class
                        success_count += 1
                        continue
                    
                    # 验证Agent类
                    if not issubclass(agent_class, BaseAgent):
                        self.logger.error(f"Agent class {agent_class.__name__} is not a subclass of BaseAgent")
                        continue
                    
                    # 注册Agent类
                    self.agent_registry.register_agent_class(agent_type, agent_class)
                    self.registered_patent_agents[agent_type] = agent_class
                    
                    success_count += 1
                    self.logger.info(f"Successfully registered patent agent: {agent_type.value} -> {agent_class.__name__}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to register patent agent {agent_type.value}: {str(e)}")
                    import traceback
                    self.logger.error(f"Registration error traceback: {traceback.format_exc()}")
            
            self.logger.info(f"Patent agent registration completed: {success_count}/{total_count} agents registered")
            
            # 验证注册结果
            registered_types = self.agent_registry.get_registered_agent_types()
            self.logger.info(f"All registered agent types: {[t.value for t in registered_types]}")
            
            return success_count == total_count
            
        except Exception as e:
            self.logger.error(f"Patent agent registration failed: {str(e)}")
            import traceback
            self.logger.error(f"Registration failure traceback: {traceback.format_exc()}")
            return False
    
    def register_patent_agent(self, agent_type: AgentType, agent_class: Type[BaseAgent]) -> bool:
        """注册单个专利Agent."""
        try:
            if agent_type not in [AgentType.PATENT_COORDINATOR, AgentType.PATENT_SEARCH, 
                                 AgentType.PATENT_ANALYSIS, AgentType.PATENT_REPORT, 
                                 AgentType.PATENT_DATA_COLLECTION]:
                self.logger.error(f"Invalid patent agent type: {agent_type.value}")
                return False
            
            # 检查是否已注册
            if self.agent_registry.is_agent_type_registered(agent_type):
                self.logger.warning(f"Agent type {agent_type.value} already registered")
                return True
            
            # 验证Agent类
            if not issubclass(agent_class, BaseAgent):
                self.logger.error(f"Agent class {agent_class.__name__} must inherit from BaseAgent")
                return False
            
            # 注册到AgentRegistry
            self.agent_registry.register_agent_class(agent_type, agent_class)
            self.registered_patent_agents[agent_type] = agent_class
            
            self.logger.info(f"Successfully registered patent agent: {agent_type.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register patent agent {agent_type.value}: {str(e)}")
            return False
    
    def unregister_patent_agent(self, agent_type: AgentType) -> bool:
        """注销专利Agent."""
        try:
            if agent_type in self.registered_patent_agents:
                # 注意：AgentRegistry没有提供unregister方法，这里只是从本地记录中移除
                del self.registered_patent_agents[agent_type]
                self.logger.info(f"Unregistered patent agent: {agent_type.value}")
                return True
            else:
                self.logger.warning(f"Patent agent {agent_type.value} not found in registry")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to unregister patent agent {agent_type.value}: {str(e)}")
            return False
    
    def get_registered_patent_agents(self) -> Dict[AgentType, Type[BaseAgent]]:
        """获取已注册的专利Agent列表."""
        return self.registered_patent_agents.copy()
    
    def is_patent_agent_registered(self, agent_type: AgentType) -> bool:
        """检查专利Agent是否已注册."""
        return agent_type in self.registered_patent_agents
    
    def get_patent_agent_info(self) -> Dict[str, any]:
        """获取专利Agent注册信息."""
        return {
            "total_registered": len(self.registered_patent_agents),
            "registered_types": [agent_type.value for agent_type in self.registered_patent_agents.keys()],
            "available_types": [agent_type.value for agent_type in self.patent_agent_classes.keys()],
            "registration_status": {
                agent_type.value: agent_type in self.registered_patent_agents
                for agent_type in self.patent_agent_classes.keys()
            }
        }
    
    def validate_patent_agent_registration(self) -> Dict[str, any]:
        """验证专利Agent注册状态."""
        validation_results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "registered_agents": [],
            "missing_agents": []
        }
        
        try:
            # 检查所有预期的专利Agent是否已注册
            for agent_type in self.patent_agent_classes.keys():
                if self.agent_registry.is_agent_type_registered(agent_type):
                    validation_results["registered_agents"].append(agent_type.value)
                else:
                    validation_results["missing_agents"].append(agent_type.value)
                    validation_results["errors"].append(f"Patent agent {agent_type.value} not registered")
                    validation_results["is_valid"] = False
            
            # 检查Agent类的有效性
            for agent_type, agent_class in self.registered_patent_agents.items():
                if not issubclass(agent_class, BaseAgent):
                    validation_results["errors"].append(
                        f"Agent class {agent_class.__name__} does not inherit from BaseAgent"
                    )
                    validation_results["is_valid"] = False
            
            # 生成警告
            if len(self.registered_patent_agents) < len(self.patent_agent_classes):
                missing_count = len(self.patent_agent_classes) - len(self.registered_patent_agents)
                validation_results["warnings"].append(
                    f"{missing_count} patent agents are not registered"
                )
            
        except Exception as e:
            validation_results["is_valid"] = False
            validation_results["errors"].append(f"Validation failed: {str(e)}")
        
        return validation_results


def register_patent_agents(agent_registry: AgentRegistry) -> bool:
    """便捷函数：注册所有专利Agent到指定的AgentRegistry."""
    patent_registry = PatentAgentRegistry(agent_registry)
    return patent_registry.register_all_patent_agents()


def get_patent_agent_registry_info(agent_registry: AgentRegistry) -> Dict[str, any]:
    """便捷函数：获取专利Agent注册信息."""
    patent_registry = PatentAgentRegistry(agent_registry)
    return patent_registry.get_patent_agent_info()


def validate_patent_agent_setup(agent_registry: AgentRegistry) -> Dict[str, any]:
    """便捷函数：验证专利Agent设置."""
    patent_registry = PatentAgentRegistry(agent_registry)
    return patent_registry.validate_patent_agent_registration()


# 全局专利Agent注册器实例（可选）
_global_patent_registry: PatentAgentRegistry = None


def get_global_patent_registry(agent_registry: AgentRegistry = None) -> PatentAgentRegistry:
    """获取全局专利Agent注册器实例."""
    global _global_patent_registry
    
    if _global_patent_registry is None:
        if agent_registry is None:
            from .registry import agent_registry as default_registry
            agent_registry = default_registry
        
        _global_patent_registry = PatentAgentRegistry(agent_registry)
    
    return _global_patent_registry


def initialize_patent_agents(agent_registry: AgentRegistry = None) -> bool:
    """初始化专利Agent系统."""
    try:
        patent_registry = get_global_patent_registry(agent_registry)
        success = patent_registry.register_all_patent_agents()
        
        if success:
            logger.info("Patent agent system initialized successfully")
        else:
            logger.error("Patent agent system initialization failed")
        
        return success
        
    except Exception as e:
        logger.error(f"Patent agent system initialization error: {str(e)}")
        return False