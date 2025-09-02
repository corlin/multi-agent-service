#!/usr/bin/env python3
"""Service startup script for multi-agent system."""

import asyncio
import logging
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any, List

from .core.lifecycle_manager import lifecycle_manager
from .config.settings import settings


def setup_logging():
    """Setup logging configuration."""
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging with both console and file handlers
    handlers = [logging.StreamHandler(sys.stdout)]
    
    # Add file handler if not in debug mode or explicitly requested
    if not settings.api_debug or os.getenv("LOG_TO_FILE", "false").lower() == "true":
        log_file = log_dir / "multi_agent_service.log"
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
        force=True  # Override any existing configuration
    )


async def startup_service() -> bool:
    """Start the multi-agent service with comprehensive initialization.
    
    Returns:
        bool: True if startup successful, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("=" * 60)
        logger.info("Multi-Agent LangGraph Service Startup")
        logger.info("=" * 60)
        
        # Step 1: Validate configuration
        logger.info("🔍 Step 1: Validating configuration...")
        if not await validate_configuration():
            logger.error("❌ Configuration validation failed")
            return False
        
        # Step 2: Perform core service startup
        logger.info("🚀 Step 2: Starting core services...")
        success = await lifecycle_manager.startup()
        
        if not success:
            logger.error("❌ Core service startup failed")
            return False
        
        # Step 3: Preload agents and workflows
        logger.info("🔄 Step 3: Preloading agents and workflows...")
        if not await preload_agents_and_workflows():
            logger.warning("⚠️  Agent and workflow preloading failed, continuing...")
        
        # Step 4: Perform comprehensive health checks
        logger.info("🔍 Step 4: Performing startup health checks...")
        health_status = await perform_startup_health_checks()
        
        if health_status.get("overall_healthy", False):
            logger.info("✅ Service startup completed successfully")
            
            # Log final status summary
            logger.info("📊 Final Startup Summary:")
            logger.info(f"   - Services initialized: {health_status.get('system', {}).get('service_container', {}).get('initialized_services', 0)}")
            logger.info(f"   - Agents active: {health_status.get('system', {}).get('agent_registry', {}).get('active_agents', 0)}")
            logger.info(f"   - Uptime: {lifecycle_manager.uptime:.2f} seconds")
            logger.info(f"   - Health Status: {'Healthy' if health_status['overall_healthy'] else 'Unhealthy'}")
            
            return True
        else:
            logger.warning("⚠️  Service started but health checks failed")
            return True  # Still consider startup successful if core services are running
            
    except Exception as e:
        logger.error(f"❌ Startup error: {str(e)}")
        return False


async def shutdown_service() -> bool:
    """Shutdown the multi-agent service.
    
    Returns:
        bool: True if shutdown successful, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🔄 Initiating service shutdown...")
        success = await lifecycle_manager.shutdown()
        
        if success:
            logger.info("✅ Service shutdown completed successfully")
        else:
            logger.error("❌ Service shutdown failed")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Shutdown error: {str(e)}")
        return False


async def restart_service() -> bool:
    """Restart the multi-agent service.
    
    Returns:
        bool: True if restart successful, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🔄 Initiating service restart...")
        success = await lifecycle_manager.restart()
        
        if success:
            logger.info("✅ Service restart completed successfully")
        else:
            logger.error("❌ Service restart failed")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Restart error: {str(e)}")
        return False


async def health_check() -> dict:
    """Perform health check on the service.
    
    Returns:
        dict: Health check results
    """
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🔍 Performing health check...")
        health_status = await lifecycle_manager.health_check()
        
        if health_status.get("healthy", False):
            logger.info("✅ Health check passed")
        else:
            logger.warning("⚠️  Health check failed")
        
        return health_status
        
    except Exception as e:
        logger.error(f"❌ Health check error: {str(e)}")
        return {"healthy": False, "error": str(e)}


async def validate_configuration() -> bool:
    """Validate service configuration.
    
    Returns:
        bool: True if configuration is valid, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🔍 Validating configuration...")
        
        # Validate basic settings
        validation_results = []
        
        # Check API configuration
        if not (1 <= settings.api_port <= 65535):
            validation_results.append(f"❌ Invalid API port: {settings.api_port}")
        else:
            validation_results.append(f"✅ API Port: {settings.api_port}")
        
        validation_results.append(f"✅ API Host: {settings.api_host}")
        validation_results.append(f"✅ Debug Mode: {settings.api_debug}")
        validation_results.append(f"✅ Log Level: {settings.log_level}")
        
        # Check required directories
        required_dirs = ["logs", "config"]
        for dir_name in required_dirs:
            dir_path = Path(dir_name)
            dir_path.mkdir(parents=True, exist_ok=True)
            validation_results.append(f"✅ Directory: {dir_path}")
        
        # Check configuration files
        config_files = [
            "config/agents.json",
            "config/models.json", 
            "config/workflows.json"
        ]
        
        for config_file in config_files:
            config_path = Path(config_file)
            if config_path.exists():
                validation_results.append(f"✅ Configuration file: {config_file}")
            else:
                validation_results.append(f"⚠️  Configuration file not found: {config_file} (will use defaults)")
        
        # Check environment variables for model API keys
        model_env_vars = [
            ("QWEN_API_KEY", settings.qwen_api_key),
            ("DEEPSEEK_API_KEY", settings.deepseek_api_key),
            ("GLM_API_KEY", settings.glm_api_key),
            ("OPENAI_API_KEY", settings.openai_api_key)
        ]
        
        available_models = []
        for env_var, value in model_env_vars:
            if value:
                available_models.append(env_var.replace("_API_KEY", ""))
                validation_results.append(f"✅ Model API key configured: {env_var}")
            else:
                validation_results.append(f"⚠️  Model API key not configured: {env_var}")
        
        if not available_models:
            validation_results.append("⚠️  No model API keys configured - service will use mock responses")
        else:
            validation_results.append(f"✅ Available model providers: {', '.join(available_models)}")
        
        # Check database configuration
        if settings.database_url:
            validation_results.append(f"✅ Database URL: {settings.database_url}")
        else:
            validation_results.append("⚠️  Database URL not configured")
        
        # Check Redis configuration
        if settings.redis_url:
            validation_results.append(f"✅ Redis URL: {settings.redis_url}")
        else:
            validation_results.append("⚠️  Redis URL not configured")
        
        # Log all validation results
        for result in validation_results:
            if result.startswith("❌"):
                logger.error(result)
            elif result.startswith("⚠️"):
                logger.warning(result)
            else:
                logger.info(result)
        
        # Check for critical errors
        has_errors = any(result.startswith("❌") for result in validation_results)
        
        if has_errors:
            logger.error("❌ Configuration validation failed with errors")
            return False
        else:
            logger.info("✅ Configuration validation completed successfully")
            return True
        
    except Exception as e:
        logger.error(f"❌ Configuration validation error: {str(e)}")
        return False


async def preload_agents_and_workflows() -> bool:
    """Preload agents and workflows for faster startup.
    
    Returns:
        bool: True if preloading successful, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🔄 Preloading agents and workflows...")
        
        # Get service manager
        service_manager = lifecycle_manager.service_manager
        
        if not service_manager or not service_manager.is_initialized:
            logger.error("❌ Service manager not initialized")
            return False
        
        # Get agent registry
        from .agents.registry import AgentRegistry
        agent_registry = await service_manager.container.get_service(AgentRegistry)
        
        if not agent_registry:
            logger.error("❌ Agent registry not available")
            return False
        
        # Preload agent configurations
        agent_stats = agent_registry.get_registry_stats()
        logger.info(f"✅ Agent registry loaded:")
        logger.info(f"   - Registered agent classes: {agent_stats.get('registered_classes', 0)}")
        logger.info(f"   - Active agent instances: {agent_stats.get('active_agents', 0)}")
        logger.info(f"   - Total agents created: {agent_stats.get('total_agents', 0)}")
        
        # Preload workflow templates
        from .workflows.graph_builder import GraphBuilder
        graph_builder = await service_manager.container.get_service(GraphBuilder)
        
        if graph_builder:
            # Test workflow creation capabilities
            from .models.enums import WorkflowType
            workflow_types = [WorkflowType.SEQUENTIAL, WorkflowType.PARALLEL, WorkflowType.HIERARCHICAL]
            
            for workflow_type in workflow_types:
                try:
                    # Test workflow graph creation (without execution)
                    test_graph = graph_builder.create_workflow_graph(workflow_type, [])
                    if test_graph:
                        logger.info(f"✅ Workflow template validated: {workflow_type.value}")
                    else:
                        logger.warning(f"⚠️  Workflow template validation failed: {workflow_type.value}")
                except Exception as e:
                    logger.warning(f"⚠️  Workflow template error for {workflow_type.value}: {str(e)}")
        
        # Validate model router
        from .services.model_router import ModelRouter
        model_router = await service_manager.container.get_service(ModelRouter)
        
        if model_router:
            available_clients = model_router.get_available_clients()
            if available_clients:
                client_names = [client_id for client_id, _ in available_clients]
                logger.info(f"✅ Model clients preloaded: {', '.join(client_names)}")
            else:
                logger.warning("⚠️  No model clients available")
        
        logger.info("✅ Agent and workflow preloading completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Preloading error: {str(e)}")
        return False


async def perform_startup_health_checks() -> Dict[str, Any]:
    """Perform comprehensive startup health checks.
    
    Returns:
        dict: Health check results with detailed status
    """
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🔍 Performing startup health checks...")
        
        # Get comprehensive health status
        health_status = await lifecycle_manager.health_check()
        
        # Get system status
        system_status = await lifecycle_manager.service_manager.get_system_status()
        
        # Compile startup health report
        startup_health = {
            "overall_healthy": health_status.get("healthy", False),
            "timestamp": health_status.get("timestamp"),
            "lifecycle": health_status.get("lifecycle", {}),
            "services": health_status.get("services", {}),
            "system": system_status,
            "startup_checks": {
                "configuration_valid": True,  # Assume valid if we got this far
                "agents_preloaded": system_status.get("agent_registry", {}).get("active_agents", 0) > 0,
                "workflows_ready": system_status.get("service_container", {}).get("initialized_services", 0) > 0,
                "models_available": len(system_status.get("monitoring", {}).get("model_providers", [])) > 0
            }
        }
        
        # Log health check results
        if startup_health["overall_healthy"]:
            logger.info("✅ Startup health checks passed")
        else:
            logger.warning("⚠️  Startup health checks failed")
        
        # Log detailed status
        logger.info("📊 Startup Health Summary:")
        logger.info(f"   - Overall Status: {'Healthy' if startup_health['overall_healthy'] else 'Unhealthy'}")
        logger.info(f"   - Configuration: {'Valid' if startup_health['startup_checks']['configuration_valid'] else 'Invalid'}")
        logger.info(f"   - Agents Preloaded: {'Yes' if startup_health['startup_checks']['agents_preloaded'] else 'No'}")
        logger.info(f"   - Workflows Ready: {'Yes' if startup_health['startup_checks']['workflows_ready'] else 'No'}")
        logger.info(f"   - Models Available: {'Yes' if startup_health['startup_checks']['models_available'] else 'No'}")
        
        return startup_health
        
    except Exception as e:
        logger.error(f"❌ Startup health check error: {str(e)}")
        return {
            "overall_healthy": False,
            "error": str(e),
            "timestamp": None
        }


def main():
    """Main entry point for the startup script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Multi-Agent LangGraph Service")
    parser.add_argument("command", choices=["start", "stop", "restart", "health", "validate", "validate-full"], 
                       help="Command to execute")
    parser.add_argument("--wait", action="store_true", 
                       help="Wait for service to be ready (for start command)")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    async def run_command():
        if args.command == "start":
            success = await startup_service()
            if success and args.wait:
                logger.info("🔄 Waiting for service to be ready...")
                # Keep the service running
                try:
                    while True:
                        await asyncio.sleep(1)
                except KeyboardInterrupt:
                    logger.info("🔄 Received shutdown signal")
                    await shutdown_service()
            return success
            
        elif args.command == "stop":
            return await shutdown_service()
            
        elif args.command == "restart":
            return await restart_service()
            
        elif args.command == "health":
            health_status = await health_check()
            return health_status.get("healthy", False)
            
        elif args.command == "validate":
            return await validate_configuration()
            
        elif args.command == "validate-full":
            # Perform comprehensive validation
            from .startup_validator import validate_startup
            validation_results = await validate_startup()
            
            # Print detailed results
            logger.info("📊 Comprehensive Validation Results:")
            logger.info(f"   Overall Valid: {validation_results.get('overall_valid', False)}")
            logger.info(f"   Success Rate: {validation_results.get('summary', {}).get('success_rate', 0):.2%}")
            
            for category, stats in validation_results.get('categories', {}).items():
                status = "✅" if stats['healthy'] else "❌"
                logger.info(f"   {status} {category.title()}: {stats['successful_checks']}/{stats['total_checks']}")
            
            # Show failed components
            failed = validation_results.get('failed_components', [])
            if failed:
                logger.warning("❌ Failed Components:")
                for failure in failed:
                    logger.warning(f"   - {failure['component']}: {failure['message']}")
            
            return validation_results.get("overall_valid", False)
        
        return False
    
    try:
        success = asyncio.run(run_command())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("🔄 Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()