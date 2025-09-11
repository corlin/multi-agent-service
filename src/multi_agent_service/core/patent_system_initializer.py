"""Patent system initializer for integrating patent functionality into the main application."""

import logging
from typing import Dict, Any, Optional

from ..agents.registry import AgentRegistry
from ..agents.patent_registry import PatentAgentRegistry, initialize_patent_agents
from ..workflows.patent_workflow_registry import PatentWorkflowRegistry, initialize_patent_workflow_system
from ..workflows.state_management import WorkflowStateManager
from ..models.enums import ModelProvider


logger = logging.getLogger(__name__)


class PatentSystemInitializer:
    """专利系统初始化器，负责在应用启动时初始化所有专利相关组件."""
    
    def __init__(self, agent_registry: AgentRegistry, state_manager: Optional[WorkflowStateManager] = None):
        """初始化专利系统初始化器."""
        self.agent_registry = agent_registry
        self.state_manager = state_manager or WorkflowStateManager()
        
        # 专利组件
        self.patent_agent_registry: Optional[PatentAgentRegistry] = None
        self.patent_workflow_registry: Optional[PatentWorkflowRegistry] = None
        
        # 初始化状态
        self.is_initialized = False
        self.initialization_errors = []
        
        self.logger = logging.getLogger(f"{__name__}.PatentSystemInitializer")
    
    async def initialize(self) -> bool:
        """初始化专利系统."""
        try:
            self.logger.info("Starting patent system initialization...")
            
            # 清理之前的错误
            self.initialization_errors.clear()
            
            # 1. 初始化专利Agent注册器
            agent_success = await self._initialize_patent_agents()
            
            # 2. 初始化专利工作流注册器
            workflow_success = await self._initialize_patent_workflows()
            
            # 3. 验证系统完整性
            validation_success = await self._validate_patent_system()
            
            # 4. 设置监控和健康检查
            monitoring_success = await self._setup_patent_monitoring()
            
            # 综合判断初始化是否成功
            self.is_initialized = all([
                agent_success,
                workflow_success,
                validation_success,
                monitoring_success
            ])
            
            if self.is_initialized:
                self.logger.info("Patent system initialization completed successfully")
            else:
                self.logger.error(f"Patent system initialization failed. Errors: {self.initialization_errors}")
            
            return self.is_initialized
            
        except Exception as e:
            self.logger.error(f"Patent system initialization failed with exception: {str(e)}")
            self.initialization_errors.append(f"Initialization exception: {str(e)}")
            self.is_initialized = False
            return False
    
    async def _initialize_patent_agents(self) -> bool:
        """初始化专利Agent."""
        try:
            self.logger.info("Initializing patent agents...")
            
            # 创建专利Agent注册器
            self.patent_agent_registry = PatentAgentRegistry(self.agent_registry)
            
            # 注册所有专利Agent类
            success = self.patent_agent_registry.register_all_patent_agents()
            
            if success:
                self.logger.info("Patent agent classes registered successfully")
                
                # 验证注册状态
                validation = self.patent_agent_registry.validate_patent_agent_registration()
                if not validation["is_valid"]:
                    self.logger.warning(f"Patent agent validation warnings: {validation['warnings']}")
                    for error in validation["errors"]:
                        self.initialization_errors.append(f"Agent validation: {error}")
                
                # 尝试创建默认的专利Agent实例（如果配置存在）
                await self._create_default_patent_agent_instances()
                
                return validation["is_valid"]
            else:
                self.initialization_errors.append("Failed to register patent agents")
                return False
                
        except Exception as e:
            self.logger.error(f"Patent agent initialization failed: {str(e)}")
            self.initialization_errors.append(f"Agent initialization: {str(e)}")
            return False
    
    async def _create_default_patent_agent_instances(self) -> None:
        """创建默认的专利Agent实例."""
        try:
            from ..models.config import AgentConfig
            from ..services.model_client import BaseModelClient
            
            # 获取默认的模型客户端
            try:
                from ..services.model_router import ModelRouter
                from ..config.config_manager import ConfigManager
                
                config_manager = ConfigManager()
                
                # 检查是否有模型配置
                try:
                    model_configs = config_manager.get_config("models")
                    if not model_configs:
                        self.logger.warning("No model configurations available, skipping agent instance creation")
                        return
                except Exception as e:
                    self.logger.warning(f"Could not get model configs: {str(e)}")
                    # 继续使用模拟客户端
                
                # 创建模型路由器
                model_configs_list = list(config_manager.get_all_model_configs().values())
                model_router = ModelRouter(model_configs_list) if model_configs_list else None
                
                # 尝试获取默认客户端
                default_client = None
                try:
                    if model_router:
                        default_client = model_router.get_default_client()
                except Exception as e:
                    self.logger.warning(f"Could not get default client from router: {str(e)}")
                
                # 如果没有默认客户端，尝试创建一个简单的模拟客户端
                if not default_client:
                    self.logger.info("Creating mock model client for patent agent instances")
                    default_client = self._create_mock_model_client()
                    
            except Exception as e:
                self.logger.warning(f"Could not initialize model router: {str(e)}")
                # 创建模拟客户端作为后备
                default_client = self._create_mock_model_client()
            
            # 定义默认的专利Agent配置
            default_patent_agents = [
                {
                    "agent_id": "patent_coordinator_default",
                    "agent_type": "patent_coordinator",
                    "name": "Patent Coordinator Agent",
                    "description": "Default patent analysis coordinator agent",
                    "enabled": True
                },
                {
                    "agent_id": "patent_data_collection_default", 
                    "agent_type": "patent_data_collection",
                    "name": "Patent Data Collection Agent",
                    "description": "Default patent data collection agent",
                    "enabled": True
                },
                {
                    "agent_id": "patent_search_default",
                    "agent_type": "patent_search", 
                    "name": "Patent Search Agent",
                    "description": "Default patent search enhancement agent",
                    "enabled": True
                },
                {
                    "agent_id": "patent_analysis_default",
                    "agent_type": "patent_analysis",
                    "name": "Patent Analysis Agent", 
                    "description": "Default patent analysis processing agent",
                    "enabled": True
                },
                {
                    "agent_id": "patent_report_default",
                    "agent_type": "patent_report",
                    "name": "Patent Report Agent",
                    "description": "Default patent report generation agent", 
                    "enabled": True
                }
            ]
            
            # 创建Agent实例
            created_count = 0
            for agent_config_dict in default_patent_agents:
                try:
                    from ..models.enums import AgentType
                    
                    # 将字符串转换为AgentType枚举
                    agent_type_str = agent_config_dict["agent_type"]
                    agent_type_mapping = {
                        "patent_coordinator": AgentType.PATENT_COORDINATOR,
                        "patent_data_collection": AgentType.PATENT_DATA_COLLECTION,
                        "patent_search": AgentType.PATENT_SEARCH,
                        "patent_analysis": AgentType.PATENT_ANALYSIS,
                        "patent_report": AgentType.PATENT_REPORT
                    }
                    
                    agent_type = agent_type_mapping.get(agent_type_str)
                    if not agent_type:
                        self.logger.warning(f"Unknown agent type: {agent_type_str}")
                        continue
                    
                    # 创建模型配置
                    from ..models.config import ModelConfig
                    llm_config = ModelConfig(
                        provider=ModelProvider.OPENAI,
                        model_name="mock-model",
                        api_key="mock-key",
                        base_url="http://localhost:8000",
                        max_tokens=2048,
                        temperature=0.7,
                        timeout=30
                    )
                    
                    # 创建提示词模板
                    prompt_template = f"""你是一个专业的{agent_config_dict['name']}。

你的主要职责是：
{agent_config_dict['description']}

请根据用户的请求，提供专业、准确的回答。

用户请求：{{user_input}}

请回答："""
                    
                    # 创建AgentConfig对象
                    agent_config = AgentConfig(
                        agent_id=agent_config_dict["agent_id"],
                        agent_type=agent_type,
                        name=agent_config_dict["name"],
                        description=agent_config_dict["description"],
                        enabled=agent_config_dict["enabled"],
                        llm_config=llm_config,
                        prompt_template=prompt_template
                    )
                    
                    # 创建Agent实例
                    success = await self.agent_registry.create_agent(agent_config, default_client)
                    if success:
                        created_count += 1
                        self.logger.info(f"Created default patent agent: {agent_config.agent_id}")
                        
                        # 启动Agent
                        start_success = await self.agent_registry.start_agent(agent_config.agent_id)
                        if start_success:
                            self.logger.info(f"Started default patent agent: {agent_config.agent_id}")
                        else:
                            self.logger.warning(f"Failed to start default patent agent: {agent_config.agent_id}")
                    else:
                        self.logger.warning(f"Failed to create default patent agent: {agent_config.agent_id}")
                        
                except Exception as e:
                    self.logger.error(f"Error creating patent agent {agent_config_dict['agent_id']}: {str(e)}")
                    continue
            
            self.logger.info(f"Created and started {created_count}/{len(default_patent_agents)} default patent agent instances")
            
        except Exception as e:
            self.logger.error(f"Error creating default patent agent instances: {str(e)}")
            # Don't fail initialization if we can't create instances
    
    def _create_mock_model_client(self):
        """创建模拟的模型客户端用于演示."""
        from ..services.model_client import BaseModelClient
        from ..models.model_service import ModelConfig
        from ..models.enums import ModelProvider
        
        class MockModelClient(BaseModelClient):
            """模拟模型客户端，用于演示和测试."""
            
            def __init__(self):
                # 创建模拟配置
                mock_config = ModelConfig(
                    provider=ModelProvider.OPENAI,  # 使用一个有效的枚举值
                    model_name="mock-model",
                    api_key="mock-key",
                    base_url="http://localhost:8000",
                    enabled=True,
                    timeout=30.0
                )
                super().__init__(mock_config)
                self.provider = "mock"
                self.model_name = "mock-model"
                self.is_available = True
            
            def _get_auth_headers(self):
                """获取认证头."""
                return {}
            
            def _prepare_request_data(self, request):
                """准备请求数据."""
                return {
                    "messages": request.messages,
                    "model": self.model_name,
                    "max_tokens": request.max_tokens or 100,
                    "temperature": request.temperature or 0.7
                }
            
            def _parse_response_data(self, response_data, request):
                """解析响应数据."""
                from ..models.model_service import ModelResponse
                from ..models.enums import ModelProvider
                import time
                
                return ModelResponse(
                    id="mock-response-id",
                    created=int(time.time()),
                    model=self.model_name,
                    choices=[{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "这是一个模拟的AI响应，用于演示专利分析系统。"
                        },
                        "finish_reason": "stop"
                    }],
                    usage={"total_tokens": 50, "prompt_tokens": 20, "completion_tokens": 30},
                    provider=ModelProvider.OPENAI,
                    response_time=0.1
                )
            
            async def health_check(self):
                """健康检查."""
                return True
        
        return MockModelClient()
    
    async def _initialize_patent_workflows(self) -> bool:
        """初始化专利工作流."""
        try:
            self.logger.info("Initializing patent workflows...")
            
            # 创建专利工作流注册器
            self.patent_workflow_registry = PatentWorkflowRegistry(self.state_manager)
            
            # 注册所有专利工作流
            success = self.patent_workflow_registry.register_patent_workflows()
            
            if success:
                self.logger.info("Patent workflows initialized successfully")
                
                # 验证注册状态
                validation = self.patent_workflow_registry.validate_patent_workflow_setup()
                if not validation["is_valid"]:
                    self.logger.warning(f"Patent workflow validation warnings: {validation['warnings']}")
                    for error in validation["errors"]:
                        self.initialization_errors.append(f"Workflow validation: {error}")
                
                return validation["is_valid"]
            else:
                self.initialization_errors.append("Failed to register patent workflows")
                return False
                
        except Exception as e:
            self.logger.error(f"Patent workflow initialization failed: {str(e)}")
            self.initialization_errors.append(f"Workflow initialization: {str(e)}")
            return False
    
    async def _validate_patent_system(self) -> bool:
        """验证专利系统完整性."""
        try:
            self.logger.info("Validating patent system...")
            
            validation_results = {
                "agents_valid": True,
                "workflows_valid": True,
                "integration_valid": True
            }
            
            # 验证Agent系统
            if self.patent_agent_registry:
                agent_validation = self.patent_agent_registry.validate_patent_agent_registration()
                validation_results["agents_valid"] = agent_validation["is_valid"]
                
                if not agent_validation["is_valid"]:
                    for error in agent_validation["errors"]:
                        self.initialization_errors.append(f"System validation - Agents: {error}")
            else:
                validation_results["agents_valid"] = False
                self.initialization_errors.append("System validation: Patent agent registry not initialized")
            
            # 验证工作流系统
            if self.patent_workflow_registry:
                workflow_validation = self.patent_workflow_registry.validate_patent_workflow_setup()
                validation_results["workflows_valid"] = workflow_validation["is_valid"]
                
                if not workflow_validation["is_valid"]:
                    for error in workflow_validation["errors"]:
                        self.initialization_errors.append(f"System validation - Workflows: {error}")
            else:
                validation_results["workflows_valid"] = False
                self.initialization_errors.append("System validation: Patent workflow registry not initialized")
            
            # 验证集成
            if self.patent_agent_registry and self.patent_workflow_registry:
                # 检查Agent和工作流的兼容性
                agent_types = self.patent_agent_registry.get_registered_patent_agents().keys()
                workflow_templates = self.patent_workflow_registry.get_registered_patent_templates().keys()
                
                if len(agent_types) > 0 and len(workflow_templates) > 0:
                    validation_results["integration_valid"] = True
                    self.logger.info("Patent system integration validation passed")
                else:
                    validation_results["integration_valid"] = False
                    self.initialization_errors.append("System validation: No agents or workflows registered")
            else:
                validation_results["integration_valid"] = False
                self.initialization_errors.append("System validation: Missing patent registries")
            
            overall_valid = all(validation_results.values())
            
            if overall_valid:
                self.logger.info("Patent system validation completed successfully")
            else:
                self.logger.error("Patent system validation failed")
            
            return overall_valid
            
        except Exception as e:
            self.logger.error(f"Patent system validation failed: {str(e)}")
            self.initialization_errors.append(f"System validation: {str(e)}")
            return False
    
    async def _setup_patent_monitoring(self) -> bool:
        """设置专利系统监控."""
        try:
            self.logger.info("Setting up patent system monitoring...")
            
            # 这里可以集成到现有的MonitoringSystem
            # 现在只是记录基本信息
            
            monitoring_info = {
                "patent_agents_registered": len(self.patent_agent_registry.get_registered_patent_agents()) if self.patent_agent_registry else 0,
                "patent_workflows_registered": len(self.patent_workflow_registry.get_registered_patent_templates()) if self.patent_workflow_registry else 0,
                "initialization_time": "startup",
                "status": "active"
            }
            
            self.logger.info(f"Patent system monitoring setup completed: {monitoring_info}")
            return True
            
        except Exception as e:
            self.logger.error(f"Patent system monitoring setup failed: {str(e)}")
            self.initialization_errors.append(f"Monitoring setup: {str(e)}")
            return False
    
    def get_initialization_status(self) -> Dict[str, Any]:
        """获取初始化状态."""
        status = {
            "is_initialized": self.is_initialized,
            "errors": self.initialization_errors.copy(),
            "components": {}
        }
        
        # Agent注册器状态
        if self.patent_agent_registry:
            status["components"]["patent_agents"] = {
                "initialized": True,
                "registered_count": len(self.patent_agent_registry.get_registered_patent_agents()),
                "info": self.patent_agent_registry.get_patent_agent_info()
            }
        else:
            status["components"]["patent_agents"] = {
                "initialized": False,
                "error": "Patent agent registry not initialized"
            }
        
        # 工作流注册器状态
        if self.patent_workflow_registry:
            status["components"]["patent_workflows"] = {
                "initialized": True,
                "registered_count": len(self.patent_workflow_registry.get_registered_patent_templates()),
                "statistics": self.patent_workflow_registry.get_patent_workflow_statistics()
            }
        else:
            status["components"]["patent_workflows"] = {
                "initialized": False,
                "error": "Patent workflow registry not initialized"
            }
        
        return status
    
    async def health_check(self) -> Dict[str, Any]:
        """专利系统健康检查."""
        health_status = {
            "is_healthy": self.is_initialized,
            "components": {},
            "overall_status": "healthy" if self.is_initialized else "unhealthy"
        }
        
        try:
            # Agent系统健康检查
            if self.patent_agent_registry:
                # 这里可以添加更详细的Agent健康检查
                health_status["components"]["patent_agents"] = {
                    "status": "healthy",
                    "registered_agents": len(self.patent_agent_registry.get_registered_patent_agents())
                }
            else:
                health_status["components"]["patent_agents"] = {
                    "status": "unhealthy",
                    "error": "Patent agent registry not available"
                }
                health_status["is_healthy"] = False
            
            # 工作流系统健康检查
            if self.patent_workflow_registry:
                workflow_health = await self.patent_workflow_registry.health_check()
                health_status["components"]["patent_workflows"] = workflow_health
                
                if not workflow_health["is_healthy"]:
                    health_status["is_healthy"] = False
            else:
                health_status["components"]["patent_workflows"] = {
                    "status": "unhealthy",
                    "error": "Patent workflow registry not available"
                }
                health_status["is_healthy"] = False
            
            # 更新整体状态
            health_status["overall_status"] = "healthy" if health_status["is_healthy"] else "unhealthy"
            
        except Exception as e:
            health_status["is_healthy"] = False
            health_status["overall_status"] = "unhealthy"
            health_status["error"] = str(e)
        
        return health_status
    
    async def shutdown(self):
        """关闭专利系统."""
        try:
            self.logger.info("Shutting down patent system...")
            
            # 关闭工作流注册器
            if self.patent_workflow_registry:
                await self.patent_workflow_registry.shutdown()
            
            # 清理资源
            self.patent_agent_registry = None
            self.patent_workflow_registry = None
            self.is_initialized = False
            
            self.logger.info("Patent system shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during patent system shutdown: {str(e)}")
    
    def get_patent_system_info(self) -> Dict[str, Any]:
        """获取专利系统信息."""
        info = {
            "system_status": "initialized" if self.is_initialized else "not_initialized",
            "initialization_errors": self.initialization_errors.copy(),
            "components": {}
        }
        
        # Agent信息
        if self.patent_agent_registry:
            info["components"]["agents"] = self.patent_agent_registry.get_patent_agent_info()
        
        # 工作流信息
        if self.patent_workflow_registry:
            info["components"]["workflows"] = self.patent_workflow_registry.get_patent_workflow_statistics()
        
        return info


# 全局专利系统初始化器实例
_global_patent_initializer: Optional[PatentSystemInitializer] = None


def get_global_patent_initializer(agent_registry: AgentRegistry, 
                                 state_manager: Optional[WorkflowStateManager] = None) -> PatentSystemInitializer:
    """获取全局专利系统初始化器实例."""
    global _global_patent_initializer
    
    if _global_patent_initializer is None:
        _global_patent_initializer = PatentSystemInitializer(agent_registry, state_manager)
    
    return _global_patent_initializer


async def initialize_patent_system(agent_registry: AgentRegistry, 
                                  state_manager: Optional[WorkflowStateManager] = None) -> bool:
    """便捷函数：初始化专利系统."""
    try:
        initializer = get_global_patent_initializer(agent_registry, state_manager)
        return await initializer.initialize()
    except Exception as e:
        logger.error(f"Patent system initialization failed: {str(e)}")
        return False


async def get_patent_system_status() -> Dict[str, Any]:
    """便捷函数：获取专利系统状态."""
    global _global_patent_initializer
    
    if _global_patent_initializer:
        return _global_patent_initializer.get_initialization_status()
    else:
        return {
            "is_initialized": False,
            "error": "Patent system initializer not created"
        }


async def patent_system_health_check() -> Dict[str, Any]:
    """便捷函数：专利系统健康检查."""
    global _global_patent_initializer
    
    if _global_patent_initializer:
        return await _global_patent_initializer.health_check()
    else:
        return {
            "is_healthy": False,
            "error": "Patent system initializer not available"
        }