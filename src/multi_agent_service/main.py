"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config.settings import settings
from .api.health import router as health_router
from .utils.fastapi_handlers import setup_exception_handlers
from .utils.middleware import setup_middleware
from .core.lifecycle_manager import lifecycle_manager
from .core.patent_system_initializer import initialize_patent_system, get_patent_system_status


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager with integrated service management."""
    # Startup
    logger.info("Starting Multi-Agent LangGraph Service...")
    logger.info(f"API Host: {settings.api_host}")
    logger.info(f"API Port: {settings.api_port}")
    logger.info(f"Debug Mode: {settings.api_debug}")
    
    # Initialize all services through lifecycle manager
    if not await lifecycle_manager.startup():
        logger.error("Failed to start services")
        raise RuntimeError("Service startup failed")
    
    # Initialize patent system
    logger.info("Initializing patent analysis system...")
    try:
        # Get the agent registry from service manager
        from .agents.registry import agent_registry
        patent_init_success = await initialize_patent_system(agent_registry)
        
        if patent_init_success:
            logger.info("Patent analysis system initialized successfully")
        else:
            logger.warning("Patent analysis system initialization failed, but continuing startup")
            # Don't fail the entire startup for patent system issues
    except Exception as e:
        logger.error(f"Patent system initialization error: {str(e)}")
        # Continue startup even if patent system fails
    
    logger.info("All services started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Multi-Agent LangGraph Service...")
    await lifecycle_manager.shutdown()
    logger.info("Service shutdown completed")


# Create FastAPI application
app = FastAPI(
    title="Multi-Agent LangGraph Service",
    description="Enterprise-grade multi-agent collaboration service based on LangGraph and FastAPI",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup exception handlers
setup_exception_handlers(app)

# Setup middleware
setup_middleware(app)

# Include routers
app.include_router(health_router)

# Import and include new API routers
from .api.chat import router as chat_router
from .api.agents import router as agents_router
from .api.workflows import router as workflows_router
from .api.monitoring import router as monitoring_router
from .api.config import router as config_router
from .api.system import router as system_router
from .api.patent import router as patent_router

app.include_router(chat_router)
app.include_router(agents_router)
app.include_router(workflows_router)
app.include_router(monitoring_router)
app.include_router(config_router)
app.include_router(system_router)
app.include_router(patent_router)


# Exception handlers are now set up via setup_exception_handlers()


@app.get("/")
async def root():
    """Root endpoint with system information."""
    try:
        # Get basic system status
        is_healthy = lifecycle_manager.service_manager.is_healthy() if lifecycle_manager.service_manager else False
        uptime = lifecycle_manager.uptime
        
        # Get patent system status
        patent_status = await get_patent_system_status()
        patent_initialized = patent_status.get("is_initialized", False)
        
        return {
            "message": "Multi-Agent LangGraph Service",
            "version": "0.1.0",
            "status": "healthy" if is_healthy else "unhealthy",
            "uptime_seconds": uptime,
            "patent_system": {
                "initialized": patent_initialized,
                "status": "active" if patent_initialized else "inactive"
            },
            "endpoints": {
                "docs": "/docs",
                "health": "/api/v1/health",
                "health_detailed": "/api/v1/health/detailed",
                "system_status": "/api/v1/system/status",
                "chat": "/api/v1/chat/completions",
                "agents": "/api/v1/agents",
                "workflows": "/api/v1/workflows",
                "patent_analyze": "/api/v1/patent/analyze",
                "patent_reports": "/api/v1/patent/reports",
                "patent_export": "/api/v1/patent/export"
            },
            "features": [
                "Multi-agent collaboration",
                "Intent recognition and routing", 
                "LangGraph workflow engine",
                "Multiple LLM provider support",
                "Real-time monitoring",
                "Hot configuration reload",
                "Patent analysis and reporting" + (" ✅" if patent_initialized else " ⚠️"),
                "Multi-format report export (HTML, PDF, JSON, ZIP)",
                "Report version management",
                "Report download and distribution API",
                "Patent data collection and processing",
                "Patent search enhancement with CNKI and AI",
                "Patent trend and competition analysis",
                "Automated patent workflow orchestration"
            ],
            "patent_agents": patent_status.get("components", {}).get("patent_agents", {}).get("registered_count", 0) if patent_initialized else 0,
            "patent_workflows": patent_status.get("components", {}).get("patent_workflows", {}).get("registered_count", 0) if patent_initialized else 0
        }
    except Exception as e:
        return {
            "message": "Multi-Agent LangGraph Service",
            "version": "0.1.0",
            "status": "error",
            "error": str(e),
            "docs": "/docs",
            "health": "/api/v1/health"
        }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.multi_agent_service.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_debug,
        log_level=settings.log_level.lower()
    )