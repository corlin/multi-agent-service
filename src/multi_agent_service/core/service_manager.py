"""Service manager for coordinating all system components."""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .service_container import ServiceContainer, service_container
from ..config.settings import settings
from ..config.config_manager import ConfigManager
from ..services.model_router import ModelRouter
from ..services.intent_analyzer import IntentAnalyzer
from ..services.agent_router import AgentRouter
from ..services.hot_reload_service import HotReloadService
# Import providers to ensure they are registered with ModelClientFactory
from ..services import providers
from ..agents.registry import AgentRegistry, agent_registry
from ..workflows.graph_builder import GraphBuilder
from ..workflows.state_management import WorkflowStateManager
from ..utils.monitoring import MonitoringSystem
from ..utils.logging import LoggingSystem
from ..utils.health_check_manager import HealthCheckManager
from ..models.config import SystemConfig

logger = logging.getLogger(__name__)


class ServiceManager:
    """Central service manager for coordinating all system components."""
    
    def __init__(self, container: Optional[ServiceContainer] = None):
        """Initialize service manager."""
        self.container = container or service_container
        self.logger = logging.getLogger(f"{__name__}.ServiceManager")
        self._startup_time: Optional[datetime] = None
        self._is_initialized = False
        self._is_running = False
        
        # Service health status
        self._service_health: Dict[str, bool] = {}
        self._last_health_check: Optional[datetime] = None
        
        # Health check manager
        self._health_check_manager: Optional[HealthCheckManager] = None
    
    async def initialize(self) -> bool:
        """Initialize all system services."""
        try:
            self.logger.info("Starting service manager initialization...")
            self._startup_time = datetime.now()
            
            # Register all core services
            await self._register_core_services()
            
            # Initialize all services in dependency order
            if not await self.container.initialize_all_services():
                self.logger.error("Failed to initialize services")
                return False
            
            # Perform post-initialization setup
            await self._post_initialization_setup()
            
            self._is_initialized = True
            self.logger.info("Service manager initialization completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Service manager initialization failed: {str(e)}")
            return False
    
    async def _register_core_services(self) -> None:
        """Register all core services with the container."""
        self.logger.info("Registering core services...")
        
        # Configuration services
        self.container.register_singleton(
            ConfigManager,
            dependencies=[]
        )
        
        # Logging and monitoring
        self.container.register_singleton(
            LoggingSystem,
            dependencies=[]
        )
        
        self.container.register_singleton(
            MonitoringSystem,
            dependencies=[]
        )
        
        # Health check manager
        self.container.register_singleton(
            HealthCheckManager,
            factory=self._create_health_check_manager,
            dependencies=[ConfigManager]
        )
        
        # Model services
        self.container.register_singleton(
            ModelRouter,
            factory=self._create_model_router,
            dependencies=[ConfigManager]
        )
        
        # Agent services
        self.container.register_instance(AgentRegistry, agent_registry)
        
        self.container.register_singleton(
            IntentAnalyzer,
            dependencies=[ModelRouter]
        )
        
        self.container.register_singleton(
            AgentRouter,
            dependencies=[IntentAnalyzer, AgentRegistry]
        )
        
        # Workflow services
        self.container.register_singleton(
            WorkflowStateManager,
            dependencies=[]
        )
        
        self.container.register_singleton(
            GraphBuilder,
            dependencies=[]
        )
        
        # Hot reload service
        self.container.register_singleton(
            HotReloadService,
            dependencies=[ConfigManager]
        )
        
        self.logger.info("Core services registered successfully")
    
    async def _post_initialization_setup(self) -> None:
        """Perform post-initialization setup."""
        self.logger.info("Performing post-initialization setup...")
        
        try:
            # Initialize agent registry with agent classes
            await self._setup_agent_registry()
            
            # Initialize agents using service initializer
            await self._initialize_agents()
            
            # Start hot reload service
            hot_reload_service = await self.container.get_service(HotReloadService)
            await hot_reload_service.start()
            
            # Initialize monitoring
            monitoring_system = await self.container.get_service(MonitoringSystem)
            await monitoring_system.start_monitoring()
            
            self.logger.info("Post-initialization setup completed")
            
        except Exception as e:
            self.logger.error(f"Post-initialization setup failed: {str(e)}")
            raise
    
    async def _setup_agent_registry(self) -> None:
        """Setup agent registry with all agent classes."""
        from ..agents.sales_agent import SalesAgent
        from ..agents.customer_support_agent import CustomerSupportAgent
        from ..agents.field_service_agent import FieldServiceAgent
        from ..agents.manager_agent import ManagerAgent
        from ..agents.coordinator_agent import CoordinatorAgent
        from ..models.enums import AgentType
        
        agent_registry = await self.container.get_service(AgentRegistry)
        
        # Register agent classes
        agent_registry.register_agent_class(AgentType.SALES, SalesAgent)
        agent_registry.register_agent_class(AgentType.CUSTOMER_SUPPORT, CustomerSupportAgent)
        agent_registry.register_agent_class(AgentType.FIELD_SERVICE, FieldServiceAgent)
        agent_registry.register_agent_class(AgentType.MANAGER, ManagerAgent)
        agent_registry.register_agent_class(AgentType.COORDINATOR, CoordinatorAgent)
        
        self.logger.info("Agent classes registered successfully")
    
    async def _initialize_agents(self) -> None:
        """Initialize agent instances using service initializer."""
        from .service_initializer import ServiceInitializer
        
        # Get required services
        config_manager = await self.container.get_service(ConfigManager)
        agent_registry = await self.container.get_service(AgentRegistry)
        model_router = await self.container.get_service(ModelRouter)
        
        # Create service initializer
        initializer = ServiceInitializer(config_manager, agent_registry, model_router)
        
        # Validate dependencies
        if not await initializer.validate_service_dependencies():
            raise RuntimeError("Service dependency validation failed")
        
        # Initialize agents
        if not await initializer.initialize_agents():
            raise RuntimeError("Agent initialization failed")
        
        # Initialize workflows
        if not await initializer.initialize_workflows():
            self.logger.warning("Workflow initialization failed, continuing...")
        
        self.logger.info("Agent initialization completed successfully")
    
    async def _create_model_router(self, config_manager: ConfigManager) -> ModelRouter:
        """Factory method to create ModelRouter with proper configuration."""
        from ..models.model_service import ModelConfig, LoadBalancingStrategy  # Use the model_service version
        from ..models.enums import ModelProvider
        
        # Create default model configurations with environment variables
        try:
            model_configs_dict = config_manager.get_all_model_configs()
            if model_configs_dict:
                # Convert from config.ModelConfig to model_service.ModelConfig
                default_configs = []
                for config_model in model_configs_dict.values():
                    # Convert to model_service.ModelConfig format
                    service_config = ModelConfig(
                        provider=config_model.provider,
                        model_name=config_model.model_name,
                        api_key=config_model.api_key,
                        base_url=config_model.base_url or "https://api.openai.com/v1",
                        max_tokens=config_model.max_tokens,
                        temperature=config_model.temperature,
                        timeout=config_model.timeout,
                        max_retries=config_model.max_retries,
                        enabled=config_model.enabled,
                        priority=config_model.priority
                    )
                    default_configs.append(service_config)
            else:
                # Create default configurations with environment variables
                default_configs = []
                
                # Qwen configuration
                if settings.qwen_api_key:
                    default_configs.append(ModelConfig(
                        provider=ModelProvider.QWEN,
                        model_name="qwen-turbo",
                        api_key=settings.qwen_api_key,
                        base_url=settings.qwen_api_url,
                        max_tokens=2000,
                        temperature=0.7,
                        priority=1,
                        enabled=True
                    ))
                    default_configs.append(ModelConfig(
                        provider=ModelProvider.QWEN,
                        model_name="qwen-plus",
                        api_key=settings.qwen_api_key,
                        base_url=settings.qwen_api_url,
                        max_tokens=2000,
                        temperature=0.7,
                        priority=2,
                        enabled=True
                    ))
                
                # DeepSeek configuration
                if settings.deepseek_api_key:
                    default_configs.append(ModelConfig(
                        provider=ModelProvider.DEEPSEEK,
                        model_name="deepseek-chat",
                        api_key=settings.deepseek_api_key,
                        base_url=settings.deepseek_api_url,
                        max_tokens=2000,
                        temperature=0.7,
                        priority=3,
                        enabled=True
                    ))
                    default_configs.append(ModelConfig(
                        provider=ModelProvider.DEEPSEEK,
                        model_name="deepseek-coder",
                        api_key=settings.deepseek_api_key,
                        base_url=settings.deepseek_api_url,
                        max_tokens=2000,
                        temperature=0.7,
                        priority=4,
                        enabled=True
                    ))
                
                # GLM configuration
                if settings.glm_api_key:
                    default_configs.append(ModelConfig(
                        provider=ModelProvider.GLM,
                        model_name="glm-4",
                        api_key=settings.glm_api_key,
                        base_url=settings.glm_api_url,
                        max_tokens=2000,
                        temperature=0.7,
                        priority=5,
                        enabled=True
                    ))
                    default_configs.append(ModelConfig(
                        provider=ModelProvider.GLM,
                        model_name="glm-3-turbo",
                        api_key=settings.glm_api_key,
                        base_url=settings.glm_api_url,
                        max_tokens=2000,
                        temperature=0.7,
                        priority=6,
                        enabled=True
                    ))
                
                # OpenAI configuration (if available)
                if settings.openai_api_key:
                    default_configs.append(ModelConfig(
                        provider=ModelProvider.OPENAI,
                        model_name="gpt-3.5-turbo",
                        api_key=settings.openai_api_key,
                        base_url=settings.openai_api_url,
                        max_tokens=2000,
                        temperature=0.7,
                        priority=7,
                        enabled=True
                    ))
                
                # If no API keys are configured, create disabled configs as placeholders
                if not default_configs:
                    self.logger.warning("No API keys configured, creating disabled model configurations")
                    default_configs = [
                        ModelConfig(
                            provider=ModelProvider.QWEN,
                            model_name="qwen-turbo",
                            api_key="",
                            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                            max_tokens=2000,
                            temperature=0.7,
                            priority=1,
                            enabled=False  # Disabled without API key
                        ),
                        ModelConfig(
                            provider=ModelProvider.DEEPSEEK,
                            model_name="deepseek-chat",
                            api_key="",
                            base_url="https://api.deepseek.com/v1",
                            max_tokens=2000,
                            temperature=0.7,
                            priority=2,
                            enabled=False  # Disabled without API key
                        )
                    ]
        
        except Exception as e:
            self.logger.warning(f"Failed to load model configurations: {e}, using fallback")
            # Fallback to basic disabled configuration
            default_configs = [
                ModelConfig(
                    provider=ModelProvider.QWEN,
                    model_name="qwen-turbo",
                    api_key="",
                    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                    max_tokens=2000,
                    temperature=0.7,
                    priority=1,
                    enabled=False
                )
            ]
        
        return ModelRouter(default_configs, LoadBalancingStrategy.PRIORITY)
    
    async def _create_health_check_manager(self, config_manager: ConfigManager) -> HealthCheckManager:
        """Factory method to create HealthCheckManager with proper configuration."""
        # Create system config with health check settings
        system_config = SystemConfig(
            health_check_interval=120,  # 2分钟间隔
            health_check_timeout=10,    # 10秒超时
            health_check_retry_delay=60,  # 1分钟重试延迟
            auth_error_cooldown=300     # 5分钟认证错误冷却期
        )
        
        return HealthCheckManager(system_config)
    
    async def start(self) -> bool:
        """Start all services."""
        try:
            if not self._is_initialized:
                self.logger.error("Service manager not initialized")
                return False
            
            self.logger.info("Starting all services...")
            
            # Start agent registry
            agent_registry = await self.container.get_service(AgentRegistry)
            if not await agent_registry.start_all_agents():
                self.logger.warning("Some agents failed to start")
            
            # Start monitoring
            monitoring_system = await self.container.get_service(MonitoringSystem)
            await monitoring_system.start_monitoring()
            
            # Initialize and start health check manager (with delay)
            await self._setup_health_check_manager_delayed()
            
            self._is_running = True
            self.logger.info("All services started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start services: {str(e)}")
            return False
    
    async def stop(self) -> bool:
        """Stop all services."""
        try:
            self.logger.info("Stopping all services...")
            
            # Stop health check manager
            if self._health_check_manager:
                await self._health_check_manager.stop()
                self._health_check_manager = None
            
            # Stop monitoring
            if self.container.is_initialized(MonitoringSystem):
                monitoring_system = await self.container.get_service(MonitoringSystem)
                await monitoring_system.stop_monitoring()
            
            # Stop hot reload service
            if self.container.is_initialized(HotReloadService):
                hot_reload_service = await self.container.get_service(HotReloadService)
                await hot_reload_service.stop()
            
            # Stop agent registry
            if self.container.is_initialized(AgentRegistry):
                agent_registry = await self.container.get_service(AgentRegistry)
                await agent_registry.stop_all_agents()
            
            # Shutdown all services
            await self.container.shutdown_all_services()
            
            self._is_running = False
            self.logger.info("All services stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop services: {str(e)}")
            return False
    
    async def restart(self) -> bool:
        """Restart all services."""
        self.logger.info("Restarting all services...")
        
        if not await self.stop():
            self.logger.error("Failed to stop services during restart")
            return False
        
        # Wait a moment before restarting
        await asyncio.sleep(1)
        
        if not await self.initialize():
            self.logger.error("Failed to initialize services during restart")
            return False
        
        if not await self.start():
            self.logger.error("Failed to start services during restart")
            return False
        
        self.logger.info("Services restarted successfully")
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        try:
            self.logger.debug("Performing system health check...")
            
            # Use health check manager if available
            if self._health_check_manager:
                health_status = self._health_check_manager.get_all_status()
                self._last_health_check = datetime.now()
                
                health_report = {
                    "overall_healthy": health_status.get("overall_healthy", False),
                    "timestamp": self._last_health_check.isoformat(),
                    "uptime_seconds": (datetime.now() - self._startup_time).total_seconds() if self._startup_time else 0,
                    "is_initialized": self._is_initialized,
                    "is_running": self._is_running,
                    "health_manager": health_status
                }
                
                self.logger.debug(f"Health check completed via manager: {health_status.get('overall_healthy', False)}")
                return health_report
            
            # Fallback to legacy health check
            # Check service container health
            container_health = await self.container.health_check_services()
            
            # Check agent registry health
            agent_health = {}
            if self.container.is_initialized(AgentRegistry):
                agent_registry = await self.container.get_service(AgentRegistry)
                agent_health = await agent_registry.health_check_all()
            
            # Calculate overall health
            all_services_healthy = all(v for v in container_health.values() if v is True)
            all_agents_healthy = all(v for v in agent_health.values() if isinstance(v, bool)) if agent_health else True
            overall_healthy = all_services_healthy and all_agents_healthy
            
            # Update internal health status
            self._service_health = {
                **container_health,
                **{f"agent_{k}": v for k, v in agent_health.items()}
            }
            self._last_health_check = datetime.now()
            
            health_report = {
                "overall_healthy": overall_healthy,
                "timestamp": self._last_health_check.isoformat(),
                "uptime_seconds": (datetime.now() - self._startup_time).total_seconds() if self._startup_time else 0,
                "is_initialized": self._is_initialized,
                "is_running": self._is_running,
                "services": container_health,
                "agents": agent_health,
                "service_count": len(container_health),
                "agent_count": len(agent_health),
                "healthy_services": sum(1 for v in container_health.values() if v is True),
                "healthy_agents": sum(1 for v in agent_health.values() if v is True) if agent_health else 0
            }
            
            self.logger.debug(f"Health check completed: {overall_healthy}")
            return health_report
            
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return {
                "overall_healthy": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        try:
            # Get service container info
            container_info = self.container.get_service_info()
            
            # Get agent registry stats
            agent_stats = {}
            if self.container.is_initialized(AgentRegistry):
                agent_registry = await self.container.get_service(AgentRegistry)
                agent_stats = agent_registry.get_registry_stats()
            
            # Get monitoring data
            monitoring_data = {}
            if self.container.is_initialized(MonitoringSystem):
                monitoring_system = await self.container.get_service(MonitoringSystem)
                monitoring_data = await monitoring_system.get_system_metrics()
            
            return {
                "service_manager": {
                    "initialized": self._is_initialized,
                    "running": self._is_running,
                    "startup_time": self._startup_time.isoformat() if self._startup_time else None,
                    "uptime_seconds": (datetime.now() - self._startup_time).total_seconds() if self._startup_time else 0
                },
                "service_container": container_info,
                "agent_registry": agent_stats,
                "monitoring": monitoring_data,
                "last_health_check": self._last_health_check.isoformat() if self._last_health_check else None
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get system status: {str(e)}")
            return {"error": str(e)}
    
    async def reload_configuration(self) -> bool:
        """Reload system configuration."""
        try:
            self.logger.info("Reloading system configuration...")
            
            # Reload config manager
            if self.container.is_initialized(ConfigManager):
                config_manager = await self.container.get_service(ConfigManager)
                await config_manager.reload_config()
            
            # Trigger hot reload
            if self.container.is_initialized(HotReloadService):
                hot_reload_service = await self.container.get_service(HotReloadService)
                await hot_reload_service.trigger_reload()
            
            self.logger.info("Configuration reloaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to reload configuration: {str(e)}")
            return False
    
    def get_service(self, service_type):
        """Get a service instance from the container."""
        return self.container.get_service(service_type)
    
    def is_healthy(self) -> bool:
        """Check if the system is healthy based on last health check."""
        if not self._service_health or not self._last_health_check:
            return False
        
        # Consider system unhealthy if last check was more than 5 minutes ago
        time_since_check = (datetime.now() - self._last_health_check).total_seconds()
        if time_since_check > 300:  # 5 minutes
            return False
        
        return all(self._service_health.values())
    
    @property
    def is_initialized(self) -> bool:
        """Check if service manager is initialized."""
        return self._is_initialized
    
    @property
    def is_running(self) -> bool:
        """Check if service manager is running."""
        return self._is_running
    
    @property
    def uptime(self) -> float:
        """Get system uptime in seconds."""
        if not self._startup_time:
            return 0.0
        return (datetime.now() - self._startup_time).total_seconds()
    
    async def _setup_health_check_manager_delayed(self) -> None:
        """设置健康检查管理器（延迟启动）."""
        try:
            # 获取健康检查管理器
            self._health_check_manager = await self.container.get_service(HealthCheckManager)
            
            # 注册模型路由器的健康检查
            if self.container.is_initialized(ModelRouter):
                model_router = await self.container.get_service(ModelRouter)
                self._health_check_manager.register_service(
                    "model_router", 
                    model_router.health_check
                )
            
            # 注册代理注册表的健康检查
            if self.container.is_initialized(AgentRegistry):
                agent_registry = await self.container.get_service(AgentRegistry)
                self._health_check_manager.register_service(
                    "agent_registry",
                    agent_registry.health_check_all
                )
            
            # 注册监控系统的健康检查
            if self.container.is_initialized(MonitoringSystem):
                monitoring_system = await self.container.get_service(MonitoringSystem)
                self._health_check_manager.register_service(
                    "monitoring_system",
                    monitoring_system.health_check
                )
            
            # 启动健康检查管理器
            await self._health_check_manager.start()
            
            self.logger.info("Health check manager setup completed")
            
            # 延迟启动健康检查，给系统时间稳定
            asyncio.create_task(self._delayed_health_check_start())
            
        except Exception as e:
            self.logger.error(f"Failed to setup health check manager: {str(e)}")
    
    async def _delayed_health_check_start(self) -> None:
        """延迟启动健康检查."""
        try:
            # 等待30秒让系统稳定
            await asyncio.sleep(30)
            
            self.logger.info("Starting delayed health checks after system stabilization")
            
            # 这里可以触发一次手动健康检查或其他初始化操作
            if self._health_check_manager:
                status = self._health_check_manager.get_all_status()
                self.logger.info(f"Initial health status: {status.get('health_percentage', 0):.1f}% healthy")
                
        except Exception as e:
            self.logger.error(f"Failed in delayed health check start: {str(e)}")
    
    async def _setup_health_check_manager(self) -> None:
        """设置健康检查管理器."""
        try:
            # 获取健康检查管理器
            self._health_check_manager = await self.container.get_service(HealthCheckManager)
            
            # 注册模型路由器的健康检查
            if self.container.is_initialized(ModelRouter):
                model_router = await self.container.get_service(ModelRouter)
                self._health_check_manager.register_service(
                    "model_router", 
                    model_router.health_check
                )
            
            # 注册代理注册表的健康检查
            if self.container.is_initialized(AgentRegistry):
                agent_registry = await self.container.get_service(AgentRegistry)
                self._health_check_manager.register_service(
                    "agent_registry",
                    agent_registry.health_check_all
                )
            
            # 注册监控系统的健康检查
            if self.container.is_initialized(MonitoringSystem):
                monitoring_system = await self.container.get_service(MonitoringSystem)
                self._health_check_manager.register_service(
                    "monitoring_system",
                    monitoring_system.health_check
                )
            
            # 启动健康检查管理器
            await self._health_check_manager.start()
            
            self.logger.info("Health check manager setup completed")
            
        except Exception as e:
            self.logger.error(f"Failed to setup health check manager: {str(e)}")


# Global service manager instance
service_manager = ServiceManager()