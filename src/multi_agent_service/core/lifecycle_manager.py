"""Lifecycle manager for application startup and shutdown."""

import asyncio
import logging
import signal
import sys
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from contextlib import asynccontextmanager

from .service_manager import ServiceManager, service_manager
from ..config.settings import settings

logger = logging.getLogger(__name__)


class LifecycleManager:
    """Manages application lifecycle including startup, shutdown, and signal handling."""
    
    def __init__(self, service_manager_instance: Optional[ServiceManager] = None):
        """Initialize lifecycle manager."""
        self.service_manager = service_manager_instance or service_manager
        self.logger = logging.getLogger(f"{__name__}.LifecycleManager")
        
        # Lifecycle state
        self._startup_time: Optional[datetime] = None
        self._shutdown_time: Optional[datetime] = None
        self._is_shutting_down = False
        
        # Lifecycle hooks
        self._startup_hooks: List[Callable] = []
        self._shutdown_hooks: List[Callable] = []
        
        # Signal handlers
        self._signal_handlers_registered = False
    
    def add_startup_hook(self, hook: Callable) -> None:
        """Add a startup hook function."""
        self._startup_hooks.append(hook)
        self.logger.debug(f"Added startup hook: {hook.__name__}")
    
    def add_shutdown_hook(self, hook: Callable) -> None:
        """Add a shutdown hook function."""
        self._shutdown_hooks.append(hook)
        self.logger.debug(f"Added shutdown hook: {hook.__name__}")
    
    async def startup(self) -> bool:
        """Perform application startup sequence."""
        try:
            self.logger.info("Starting application lifecycle...")
            self._startup_time = datetime.now()
            
            # Register signal handlers
            self._register_signal_handlers()
            
            # Execute startup hooks
            await self._execute_startup_hooks()
            
            # Initialize service manager
            if not await self.service_manager.initialize():
                self.logger.error("Service manager initialization failed")
                return False
            
            # Start all services
            if not await self.service_manager.start():
                self.logger.error("Service startup failed")
                return False
            
            # Perform initial health check
            health_status = await self.service_manager.health_check()
            if not health_status.get("overall_healthy", False):
                self.logger.warning("System health check failed after startup")
                # Don't fail startup, but log the warning
            
            self.logger.info("Application startup completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Application startup failed: {str(e)}")
            return False
    
    async def shutdown(self) -> bool:
        """Perform application shutdown sequence."""
        if self._is_shutting_down:
            self.logger.warning("Shutdown already in progress")
            return True
        
        try:
            self.logger.info("Starting application shutdown...")
            self._is_shutting_down = True
            self._shutdown_time = datetime.now()
            
            # Execute shutdown hooks
            await self._execute_shutdown_hooks()
            
            # Stop service manager
            if not await self.service_manager.stop():
                self.logger.error("Service manager shutdown failed")
                return False
            
            # Unregister signal handlers
            self._unregister_signal_handlers()
            
            uptime = (self._shutdown_time - self._startup_time).total_seconds() if self._startup_time else 0
            self.logger.info(f"Application shutdown completed successfully (uptime: {uptime:.2f}s)")
            return True
            
        except Exception as e:
            self.logger.error(f"Application shutdown failed: {str(e)}")
            return False
        finally:
            self._is_shutting_down = False
    
    async def restart(self) -> bool:
        """Restart the application."""
        self.logger.info("Restarting application...")
        
        if not await self.shutdown():
            self.logger.error("Failed to shutdown during restart")
            return False
        
        # Wait a moment before restarting
        await asyncio.sleep(2)
        
        if not await self.startup():
            self.logger.error("Failed to startup during restart")
            return False
        
        self.logger.info("Application restarted successfully")
        return True
    
    async def _execute_startup_hooks(self) -> None:
        """Execute all startup hooks."""
        self.logger.debug(f"Executing {len(self._startup_hooks)} startup hooks...")
        
        for hook in self._startup_hooks:
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook()
                else:
                    hook()
                self.logger.debug(f"Executed startup hook: {hook.__name__}")
            except Exception as e:
                self.logger.error(f"Startup hook {hook.__name__} failed: {str(e)}")
                # Continue with other hooks
    
    async def _execute_shutdown_hooks(self) -> None:
        """Execute all shutdown hooks."""
        self.logger.debug(f"Executing {len(self._shutdown_hooks)} shutdown hooks...")
        
        # Execute shutdown hooks in reverse order
        for hook in reversed(self._shutdown_hooks):
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook()
                else:
                    hook()
                self.logger.debug(f"Executed shutdown hook: {hook.__name__}")
            except Exception as e:
                self.logger.error(f"Shutdown hook {hook.__name__} failed: {str(e)}")
                # Continue with other hooks
    
    def _register_signal_handlers(self) -> None:
        """Register signal handlers for graceful shutdown."""
        if self._signal_handlers_registered:
            return
        
        try:
            # Handle SIGINT (Ctrl+C) and SIGTERM
            if sys.platform != "win32":
                loop = asyncio.get_event_loop()
                
                for sig in (signal.SIGINT, signal.SIGTERM):
                    loop.add_signal_handler(sig, self._signal_handler, sig)
                
                self.logger.debug("Signal handlers registered")
            else:
                # Windows doesn't support add_signal_handler
                signal.signal(signal.SIGINT, self._signal_handler_sync)
                signal.signal(signal.SIGTERM, self._signal_handler_sync)
                self.logger.debug("Signal handlers registered (Windows)")
            
            self._signal_handlers_registered = True
            
        except Exception as e:
            self.logger.warning(f"Failed to register signal handlers: {str(e)}")
    
    def _unregister_signal_handlers(self) -> None:
        """Unregister signal handlers."""
        if not self._signal_handlers_registered:
            return
        
        try:
            if sys.platform != "win32":
                loop = asyncio.get_event_loop()
                
                for sig in (signal.SIGINT, signal.SIGTERM):
                    loop.remove_signal_handler(sig)
            else:
                # Reset to default handlers on Windows
                signal.signal(signal.SIGINT, signal.SIG_DFL)
                signal.signal(signal.SIGTERM, signal.SIG_DFL)
            
            self._signal_handlers_registered = False
            self.logger.debug("Signal handlers unregistered")
            
        except Exception as e:
            self.logger.warning(f"Failed to unregister signal handlers: {str(e)}")
    
    def _signal_handler(self, signum: int) -> None:
        """Handle shutdown signals (async version)."""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        
        # Create a task to handle shutdown
        asyncio.create_task(self._graceful_shutdown())
    
    def _signal_handler_sync(self, signum: int, frame) -> None:
        """Handle shutdown signals (sync version for Windows)."""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        
        # For Windows, we need to handle this differently
        # Create a new event loop if needed
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self._graceful_shutdown())
            else:
                loop.run_until_complete(self._graceful_shutdown())
        except RuntimeError:
            # No event loop running, create one
            asyncio.run(self._graceful_shutdown())
    
    async def _graceful_shutdown(self) -> None:
        """Perform graceful shutdown."""
        try:
            await self.shutdown()
        except Exception as e:
            self.logger.error(f"Error during graceful shutdown: {str(e)}")
        finally:
            # Force exit if needed
            sys.exit(0)
    
    @asynccontextmanager
    async def lifespan_context(self):
        """Context manager for application lifespan."""
        try:
            # Startup
            if not await self.startup():
                raise RuntimeError("Application startup failed")
            
            yield
            
        finally:
            # Shutdown
            await self.shutdown()
    
    @property
    def uptime(self) -> float:
        """Get current uptime in seconds."""
        if self._startup_time:
            if self._shutdown_time:
                return (self._shutdown_time - self._startup_time).total_seconds()
            else:
                return (datetime.now() - self._startup_time).total_seconds()
        return 0.0
    
    def get_lifecycle_status(self) -> Dict[str, Any]:
        """Get lifecycle status information."""
        uptime = self.uptime
        
        return {
            "startup_time": self._startup_time.isoformat() if self._startup_time else None,
            "shutdown_time": self._shutdown_time.isoformat() if self._shutdown_time else None,
            "uptime_seconds": uptime,
            "is_shutting_down": self._is_shutting_down,
            "signal_handlers_registered": self._signal_handlers_registered,
            "startup_hooks_count": len(self._startup_hooks),
            "shutdown_hooks_count": len(self._shutdown_hooks),
            "service_manager_initialized": self.service_manager.is_initialized,
            "service_manager_running": self.service_manager.is_running
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform lifecycle health check."""
        try:
            # Get service manager health
            service_health = await self.service_manager.health_check()
            
            # Get lifecycle status
            lifecycle_status = self.get_lifecycle_status()
            
            # Determine overall health
            is_healthy = (
                service_health.get("overall_healthy", False) and
                not self._is_shutting_down and
                self.service_manager.is_running
            )
            
            return {
                "healthy": is_healthy,
                "lifecycle": lifecycle_status,
                "services": service_health,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Lifecycle health check failed: {str(e)}")
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# Global lifecycle manager instance
lifecycle_manager = LifecycleManager()