"""Service initializer for creating and configuring agent instances."""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from ..config.config_manager import ConfigManager
from ..agents.registry import AgentRegistry
from ..services.model_router import ModelRouter
from ..models.config import AgentConfig
from ..models.enums import AgentType

logger = logging.getLogger(__name__)


class ServiceInitializer:
    """Handles initialization of agents and other services with proper configuration."""
    
    def __init__(
        self, 
        config_manager: ConfigManager,
        agent_registry: AgentRegistry,
        model_router: ModelRouter
    ):
        """Initialize service initializer."""
        self.config_manager = config_manager
        self.agent_registry = agent_registry
        self.model_router = model_router
        self.logger = logging.getLogger(f"{__name__}.ServiceInitializer")
    
    async def initialize_agents(self) -> bool:
        """Initialize all configured agents."""
        try:
            self.logger.info("Initializing agents...")
            
            # Get agent configurations
            agent_configs = await self._get_agent_configurations()
            
            if not agent_configs:
                self.logger.warning("No agent configurations found, creating default agents")
                agent_configs = self._create_default_agent_configs()
            
            # Create and initialize agents
            success_count = 0
            for config in agent_configs:
                if await self._create_agent(config):
                    success_count += 1
                else:
                    self.logger.error(f"Failed to create agent: {config.agent_id}")
            
            self.logger.info(f"Successfully initialized {success_count}/{len(agent_configs)} agents")
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"Agent initialization failed: {str(e)}")
            return False
    
    async def _get_agent_configurations(self) -> List[AgentConfig]:
        """Get agent configurations from config manager."""
        try:
            # Try to get configurations from config manager
            config_data = self.config_manager.get_config("agents")
            
            if not config_data or "agents" not in config_data:
                return []
            
            agent_configs = []
            agents_dict = config_data["agents"]
            
            # Handle both list and dict formats
            if isinstance(agents_dict, dict):
                # If it's a dict with agent_id as keys
                for agent_id, agent_data in agents_dict.items():
                    try:
                        if isinstance(agent_data, dict):
                            config = AgentConfig(**agent_data)
                        else:
                            self.logger.warning(f"Invalid agent config format for {agent_id}: {type(agent_data)}")
                            continue
                        agent_configs.append(config)
                    except Exception as e:
                        self.logger.warning(f"Invalid agent config: {agent_id}, error: {e}")
                        continue
            elif isinstance(agents_dict, list):
                # If it's a list of agent configs
                for agent_data in agents_dict:
                    try:
                        if isinstance(agent_data, dict):
                            config = AgentConfig(**agent_data)
                        else:
                            self.logger.warning(f"Invalid agent config format: {type(agent_data)}")
                            continue
                        agent_configs.append(config)
                    except Exception as e:
                        self.logger.warning(f"Invalid agent config: {agent_data}, error: {e}")
                        continue
            
            return agent_configs
            
        except Exception as e:
            self.logger.warning(f"Failed to load agent configurations: {str(e)}")
            return []
    
    def _create_default_agent_configs(self) -> List[AgentConfig]:
        """Create default agent configurations."""
        default_configs = []
        
        # Default agent configurations
        agent_definitions = [
            {
                "agent_type": AgentType.SALES,
                "name": "销售代表智能体",
                "description": "专业的销售代表，负责产品咨询、报价和客户关系管理"
            },
            {
                "agent_type": AgentType.CUSTOMER_SUPPORT,
                "name": "客服专员智能体", 
                "description": "专业的客服专员，负责客户问题解决和技术支持"
            },
            {
                "agent_type": AgentType.FIELD_SERVICE,
                "name": "现场服务人员智能体",
                "description": "专业的现场服务人员，负责技术服务和现场支持"
            },
            {
                "agent_type": AgentType.MANAGER,
                "name": "公司管理者智能体",
                "description": "专业的管理者，负责决策分析和战略规划"
            },
            {
                "agent_type": AgentType.COORDINATOR,
                "name": "智能体总协调员",
                "description": "智能体协调员，负责多智能体协作和任务分配"
            }
        ]
        
        for i, definition in enumerate(agent_definitions):
            # Create the required llm_config using the models.config.ModelConfig
            from ..models.config import ModelConfig as ConfigModelConfig
            from ..models.enums import ModelProvider
            
            llm_config = ConfigModelConfig(
                provider=ModelProvider.QWEN,
                model_name="qwen-turbo",
                api_key="",  # Will be loaded from environment
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                max_tokens=2000,
                temperature=0.7
            )
            
            config = AgentConfig(
                agent_id=f"{definition['agent_type'].value}_{i+1}",
                agent_type=definition["agent_type"],
                name=definition["name"],
                description=definition["description"],
                capabilities=[
                    "text_processing",
                    "conversation",
                    "problem_solving"
                ],
                llm_config=llm_config,
                prompt_template="",  # Will be set by agent class
            )
            default_configs.append(config)
        
        self.logger.info(f"Created {len(default_configs)} default agent configurations")
        return default_configs
    
    async def _create_agent(self, config: AgentConfig) -> bool:
        """Create and initialize a single agent."""
        try:
            self.logger.debug(f"Creating agent: {config.agent_id}")
            
            # Get model client for the agent
            # Create a dummy request to select a client
            from ..models.model_service import ModelRequest
            dummy_request = ModelRequest(messages=[{"role": "user", "content": "test"}])
            
            client_result = self.model_router.select_client(dummy_request)
            if not client_result:
                self.logger.error(f"No model client available for agent {config.agent_id}")
                return False
            
            client_id, model_client = client_result
            
            if not model_client:
                self.logger.error(f"Failed to get model client for agent {config.agent_id}")
                return False
            
            # Create agent through registry
            if not await self.agent_registry.create_agent(config, model_client):
                self.logger.error(f"Failed to create agent {config.agent_id}")
                return False
            
            # Start the agent
            if not await self.agent_registry.start_agent(config.agent_id):
                self.logger.error(f"Failed to start agent {config.agent_id}")
                return False
            
            self.logger.info(f"Successfully created and started agent: {config.agent_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating agent {config.agent_id}: {str(e)}")
            return False
    
    async def create_agent_from_config(self, agent_config: Dict) -> bool:
        """Create a single agent from configuration dictionary."""
        try:
            config = AgentConfig(**agent_config)
            return await self._create_agent(config)
        except Exception as e:
            self.logger.error(f"Failed to create agent from config: {str(e)}")
            return False
    
    async def initialize_workflows(self) -> bool:
        """Initialize workflow engine and templates."""
        try:
            self.logger.info("Initializing workflows...")
            
            # Workflow initialization will be handled by the workflow engine
            # This is a placeholder for future workflow initialization logic
            
            self.logger.info("Workflows initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Workflow initialization failed: {str(e)}")
            return False
    
    async def validate_service_dependencies(self) -> bool:
        """Validate that all service dependencies are available."""
        try:
            self.logger.debug("Validating service dependencies...")
            
            # Check model router
            if not self.model_router:
                self.logger.error("Model router not available")
                return False
            
            # Check agent registry
            if not self.agent_registry:
                self.logger.error("Agent registry not available")
                return False
            
            # Check config manager
            if not self.config_manager:
                self.logger.error("Config manager not available")
                return False
            
            # Test model router connectivity
            try:
                available_clients = self.model_router.get_available_clients()
                if not available_clients:
                    self.logger.warning("No model clients available")
                else:
                    client_names = [client_id for client_id, _ in available_clients]
                    self.logger.info(f"Available model clients: {client_names}")
            except Exception as e:
                self.logger.warning(f"Could not check model providers: {str(e)}")
            
            self.logger.debug("Service dependencies validated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Service dependency validation failed: {str(e)}")
            return False
    
    async def get_initialization_status(self) -> Dict[str, any]:
        """Get initialization status information."""
        try:
            # Get agent registry stats
            agent_stats = self.agent_registry.get_registry_stats()
            
            # Get model router status
            model_status = {}
            try:
                model_status = {
                    "available_providers": await self.model_router.get_available_providers(),
                    "default_provider": self.model_router.default_provider
                }
            except Exception as e:
                model_status = {"error": str(e)}
            
            return {
                "timestamp": datetime.now().isoformat(),
                "agents": agent_stats,
                "models": model_status,
                "config_manager_available": self.config_manager is not None
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get initialization status: {str(e)}")
            return {"error": str(e)}