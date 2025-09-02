"""智能健康检查管理器."""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, Set, Callable
from datetime import datetime, timedelta
from enum import Enum

from ..models.config import SystemConfig

logger = logging.getLogger(__name__)


class HealthCheckStatus(Enum):
    """健康检查状态."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    COOLDOWN = "cooldown"
    UNKNOWN = "unknown"


class HealthCheckResult:
    """健康检查结果."""
    
    def __init__(self, service_id: str, status: HealthCheckStatus, 
                 message: str = "", error_type: str = ""):
        self.service_id = service_id
        self.status = status
        self.message = message
        self.error_type = error_type
        self.timestamp = datetime.now()


class ServiceHealthTracker:
    """服务健康状态跟踪器."""
    
    def __init__(self, service_id: str, config: SystemConfig):
        self.service_id = service_id
        self.config = config
        
        # 健康状态
        self.current_status = HealthCheckStatus.UNKNOWN
        self.last_check_time: Optional[datetime] = None
        self.last_success_time: Optional[datetime] = None
        self.consecutive_failures = 0
        
        # 冷却期管理
        self.cooldown_until: Optional[datetime] = None
        self.cooldown_duration = timedelta(seconds=config.health_check_retry_delay)
        self.auth_cooldown_duration = timedelta(seconds=config.auth_error_cooldown)
        
        # 动态间隔调整
        self.base_interval = timedelta(seconds=config.health_check_interval)
        self.current_interval = self.base_interval
        self.max_interval = timedelta(seconds=config.health_check_interval * 4)
        
        # 错误统计
        self.error_counts: Dict[str, int] = {}
        self.last_errors: Dict[str, datetime] = {}
    
    def should_check_now(self) -> bool:
        """判断是否应该进行健康检查."""
        now = datetime.now()
        
        # 检查是否在冷却期
        if self.cooldown_until and now < self.cooldown_until:
            return False
        
        # 检查是否到了检查时间
        if self.last_check_time:
            return now >= self.last_check_time + self.current_interval
        
        return True
    
    def record_success(self):
        """记录成功的健康检查."""
        now = datetime.now()
        self.current_status = HealthCheckStatus.HEALTHY
        self.last_check_time = now
        self.last_success_time = now
        self.consecutive_failures = 0
        self.cooldown_until = None
        
        # 重置检查间隔
        self.current_interval = self.base_interval
        
        logger.debug(f"Health check success for {self.service_id}")
    
    def record_failure(self, error_type: str = "unknown", message: str = ""):
        """记录失败的健康检查."""
        now = datetime.now()
        self.current_status = HealthCheckStatus.UNHEALTHY
        self.last_check_time = now
        self.consecutive_failures += 1
        
        # 更新错误统计
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        self.last_errors[error_type] = now
        
        # 根据错误类型设置冷却期
        if error_type in ["auth_error", "401", "unauthorized"]:
            self.cooldown_until = now + self.auth_cooldown_duration
            self.current_status = HealthCheckStatus.COOLDOWN
            logger.warning(f"Auth error for {self.service_id}, cooldown until {self.cooldown_until}")
        
        elif error_type in ["timeout", "connection_error"]:
            # 连接错误使用较短的冷却期
            self.cooldown_until = now + self.cooldown_duration
            self.current_status = HealthCheckStatus.COOLDOWN
            logger.warning(f"Connection error for {self.service_id}, cooldown until {self.cooldown_until}")
        
        else:
            # 其他错误，动态调整检查间隔
            self._adjust_check_interval()
        
        logger.debug(f"Health check failure for {self.service_id}: {error_type} - {message}")
    
    def _adjust_check_interval(self):
        """根据连续失败次数动态调整检查间隔."""
        if self.consecutive_failures >= 3:
            # 连续失败3次后，增加检查间隔
            multiplier = min(2 ** (self.consecutive_failures - 2), 4)
            self.current_interval = min(
                self.base_interval * multiplier,
                self.max_interval
            )
            logger.debug(f"Adjusted check interval for {self.service_id} to {self.current_interval.total_seconds()}s")
    
    def get_status_info(self) -> Dict[str, Any]:
        """获取状态信息."""
        return {
            "service_id": self.service_id,
            "status": self.current_status.value,
            "last_check_time": self.last_check_time.isoformat() if self.last_check_time else None,
            "last_success_time": self.last_success_time.isoformat() if self.last_success_time else None,
            "consecutive_failures": self.consecutive_failures,
            "cooldown_until": self.cooldown_until.isoformat() if self.cooldown_until else None,
            "current_interval_seconds": self.current_interval.total_seconds(),
            "error_counts": self.error_counts.copy(),
            "is_in_cooldown": self.cooldown_until and datetime.now() < self.cooldown_until
        }


class HealthCheckManager:
    """智能健康检查管理器."""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.HealthCheckManager")
        
        # 服务跟踪器
        self.trackers: Dict[str, ServiceHealthTracker] = {}
        
        # 健康检查函数注册
        self.check_functions: Dict[str, Callable] = {}
        
        # 运行状态
        self.is_running = False
        self._check_task: Optional[asyncio.Task] = None
        
        # 全局统计
        self.total_checks = 0
        self.total_successes = 0
        self.total_failures = 0
        self.start_time: Optional[datetime] = None
    
    def register_service(self, service_id: str, check_function: Callable) -> None:
        """注册服务健康检查."""
        self.trackers[service_id] = ServiceHealthTracker(service_id, self.config)
        self.check_functions[service_id] = check_function
        self.logger.info(f"Registered health check for service: {service_id}")
    
    def unregister_service(self, service_id: str) -> None:
        """注销服务健康检查."""
        if service_id in self.trackers:
            del self.trackers[service_id]
        if service_id in self.check_functions:
            del self.check_functions[service_id]
        self.logger.info(f"Unregistered health check for service: {service_id}")
    
    async def start(self) -> None:
        """启动健康检查管理器."""
        if self.is_running:
            self.logger.warning("Health check manager is already running")
            return
        
        self.is_running = True
        self.start_time = datetime.now()
        self._check_task = asyncio.create_task(self._check_loop())
        self.logger.info("Health check manager started")
    
    async def stop(self) -> None:
        """停止健康检查管理器."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self._check_task:
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Health check manager stopped")
    
    async def _check_loop(self) -> None:
        """健康检查循环."""
        while self.is_running:
            try:
                await self._perform_checks()
                await asyncio.sleep(10)  # 每10秒检查一次是否有服务需要检查
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in health check loop: {str(e)}")
                await asyncio.sleep(30)  # 出错后等待30秒再继续
    
    async def _perform_checks(self) -> None:
        """执行健康检查."""
        check_tasks = []
        
        for service_id, tracker in self.trackers.items():
            if tracker.should_check_now():
                check_function = self.check_functions.get(service_id)
                if check_function:
                    task = asyncio.create_task(
                        self._check_service(service_id, check_function, tracker)
                    )
                    check_tasks.append(task)
        
        if check_tasks:
            await asyncio.gather(*check_tasks, return_exceptions=True)
    
    async def _check_service(self, service_id: str, check_function: Callable, 
                           tracker: ServiceHealthTracker) -> None:
        """检查单个服务."""
        try:
            self.total_checks += 1
            
            # 执行健康检查
            result = await asyncio.wait_for(
                check_function(),
                timeout=self.config.health_check_timeout
            )
            
            if result:
                tracker.record_success()
                self.total_successes += 1
            else:
                tracker.record_failure("check_failed", "Health check returned False")
                self.total_failures += 1
        
        except asyncio.TimeoutError:
            tracker.record_failure("timeout", "Health check timeout")
            self.total_failures += 1
        
        except Exception as e:
            error_msg = str(e).lower()
            
            # 分类错误类型
            if "401" in error_msg or "unauthorized" in error_msg:
                error_type = "auth_error"
            elif "timeout" in error_msg:
                error_type = "timeout"
            elif "connection" in error_msg:
                error_type = "connection_error"
            else:
                error_type = "unknown"
            
            tracker.record_failure(error_type, str(e))
            self.total_failures += 1
    
    async def check_service_now(self, service_id: str) -> HealthCheckResult:
        """立即检查指定服务."""
        if service_id not in self.trackers:
            return HealthCheckResult(
                service_id, HealthCheckStatus.UNKNOWN, 
                "Service not registered"
            )
        
        tracker = self.trackers[service_id]
        check_function = self.check_functions.get(service_id)
        
        if not check_function:
            return HealthCheckResult(
                service_id, HealthCheckStatus.UNKNOWN,
                "No check function registered"
            )
        
        try:
            result = await asyncio.wait_for(
                check_function(),
                timeout=self.config.health_check_timeout
            )
            
            if result:
                tracker.record_success()
                return HealthCheckResult(
                    service_id, HealthCheckStatus.HEALTHY,
                    "Health check passed"
                )
            else:
                tracker.record_failure("manual_check_failed")
                return HealthCheckResult(
                    service_id, HealthCheckStatus.UNHEALTHY,
                    "Health check returned False"
                )
        
        except Exception as e:
            error_msg = str(e).lower()
            if "401" in error_msg or "unauthorized" in error_msg:
                error_type = "auth_error"
            elif "timeout" in error_msg:
                error_type = "timeout"
            else:
                error_type = "unknown"
            
            tracker.record_failure(error_type, str(e))
            return HealthCheckResult(
                service_id, HealthCheckStatus.UNHEALTHY,
                str(e), error_type
            )
    
    def get_service_status(self, service_id: str) -> Optional[Dict[str, Any]]:
        """获取服务状态."""
        tracker = self.trackers.get(service_id)
        return tracker.get_status_info() if tracker else None
    
    def get_all_status(self) -> Dict[str, Any]:
        """获取所有服务状态."""
        services_status = {}
        healthy_count = 0
        total_count = len(self.trackers)
        
        for service_id, tracker in self.trackers.items():
            status_info = tracker.get_status_info()
            services_status[service_id] = status_info
            
            if tracker.current_status == HealthCheckStatus.HEALTHY:
                healthy_count += 1
        
        uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        success_rate = (self.total_successes / self.total_checks * 100) if self.total_checks > 0 else 0
        
        return {
            "overall_healthy": healthy_count == total_count and total_count > 0,
            "healthy_services": healthy_count,
            "total_services": total_count,
            "health_percentage": (healthy_count / total_count * 100) if total_count > 0 else 0,
            "services": services_status,
            "statistics": {
                "total_checks": self.total_checks,
                "total_successes": self.total_successes,
                "total_failures": self.total_failures,
                "success_rate_percent": success_rate,
                "uptime_seconds": uptime
            },
            "manager_status": {
                "is_running": self.is_running,
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "registered_services": list(self.trackers.keys())
            }
        }