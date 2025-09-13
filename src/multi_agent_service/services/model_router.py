"""Model router and failover mechanism implementation."""

import asyncio
import logging
import random
import time
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

from ..models.model_service import (
    ModelConfig, 
    ModelRequest, 
    ModelResponse, 
    ModelError, 
    FailoverEvent,
    LoadBalancingStrategy
)
from ..models.enums import ModelProvider
from .model_client import BaseModelClient, ModelClientFactory, ModelClientError


logger = logging.getLogger(__name__)


class ModelRouter:
    """模型路由器，支持负载均衡和故障转移."""
    
    def __init__(self, configs: List[ModelConfig], 
                 strategy: LoadBalancingStrategy = LoadBalancingStrategy.PRIORITY):
        """初始化模型路由器.
        
        Args:
            configs: 模型配置列表
            strategy: 负载均衡策略
        """
        self.strategy = strategy
        self.clients: Dict[str, BaseModelClient] = {}
        self.configs: Dict[str, ModelConfig] = {}
        self.failover_events: List[FailoverEvent] = []
        
        # 负载均衡相关
        self._round_robin_index = 0
        self._connection_counts: Dict[str, int] = defaultdict(int)
        
        # 初始化客户端
        self._initialize_clients(configs)
        
        logger.info(f"Initialized model router with {len(self.clients)} clients, "
                   f"strategy: {strategy}")
    
    def _initialize_clients(self, configs: List[ModelConfig]) -> None:
        """初始化模型客户端."""
        for config in configs:
            if config.enabled:
                try:
                    client = ModelClientFactory.create_client(config)
                    client_id = f"{config.provider.value}:{config.model_name}"
                    self.clients[client_id] = client
                    self.configs[client_id] = config
                    logger.info(f"Initialized client: {client_id}")
                except Exception as e:
                    logger.error(f"Failed to initialize client for {config.provider}:"
                               f"{config.model_name}: {str(e)}")
    
    def add_client(self, config: ModelConfig) -> None:
        """添加新的模型客户端.
        
        Args:
            config: 模型配置
        """
        if config.enabled:
            try:
                client = ModelClientFactory.create_client(config)
                client_id = f"{config.provider.value}:{config.model_name}"
                self.clients[client_id] = client
                self.configs[client_id] = config
                logger.info(f"Added new client: {client_id}")
            except Exception as e:
                logger.error(f"Failed to add client for {config.provider}:"
                           f"{config.model_name}: {str(e)}")
    
    def remove_client(self, provider: ModelProvider, model_name: str) -> None:
        """移除模型客户端.
        
        Args:
            provider: 模型提供商
            model_name: 模型名称
        """
        client_id = f"{provider.value}:{model_name}"
        if client_id in self.clients:
            del self.clients[client_id]
            del self.configs[client_id]
            logger.info(f"Removed client: {client_id}")
    
    def get_available_clients(self) -> List[Tuple[str, BaseModelClient]]:
        """获取可用的客户端列表.
        
        Returns:
            List[Tuple[str, BaseModelClient]]: 可用客户端列表
        """
        available = []
        for client_id, client in self.clients.items():
            config = self.configs[client_id]
            if config.enabled and client.metrics.availability > 0.5:  # 可用性阈值
                available.append((client_id, client))
        
        return available
    
    def get_default_client(self) -> Optional[BaseModelClient]:
        """获取默认客户端（优先级最高的可用客户端）.
        
        Returns:
            Optional[BaseModelClient]: 默认客户端，如果没有可用客户端则返回None
        """
        available_clients = self.get_available_clients()
        if not available_clients:
            # 如果没有可用客户端，返回第一个客户端（如果存在）
            if self.clients:
                return next(iter(self.clients.values()))
            return None
        
        # 按优先级排序（数字越小优先级越高）
        sorted_clients = sorted(
            available_clients,
            key=lambda x: self.configs[x[0]].priority
        )
        
        return sorted_clients[0][1]
    
    def _select_client_by_priority(self) -> Optional[Tuple[str, BaseModelClient]]:
        """按优先级选择客户端."""
        available_clients = self.get_available_clients()
        if not available_clients:
            return None
        
        # 按优先级排序（数字越小优先级越高）
        sorted_clients = sorted(
            available_clients,
            key=lambda x: self.configs[x[0]].priority
        )
        
        return sorted_clients[0]
    
    def _select_client_by_round_robin(self) -> Optional[Tuple[str, BaseModelClient]]:
        """轮询选择客户端."""
        available_clients = self.get_available_clients()
        if not available_clients:
            return None
        
        # 轮询选择
        client = available_clients[self._round_robin_index % len(available_clients)]
        self._round_robin_index += 1
        
        return client
    
    def _select_client_by_weighted_round_robin(self) -> Optional[Tuple[str, BaseModelClient]]:
        """加权轮询选择客户端."""
        available_clients = self.get_available_clients()
        if not available_clients:
            return None
        
        # 根据优先级计算权重（优先级越高权重越大）
        weighted_clients = []
        for client_id, client in available_clients:
            config = self.configs[client_id]
            weight = max(1, 10 - config.priority)  # 优先级1-10转换为权重10-1
            weighted_clients.extend([(client_id, client)] * weight)
        
        if weighted_clients:
            return random.choice(weighted_clients)
        
        return None
    
    def _select_client_by_least_connections(self) -> Optional[Tuple[str, BaseModelClient]]:
        """最少连接选择客户端."""
        available_clients = self.get_available_clients()
        if not available_clients:
            return None
        
        # 选择连接数最少的客户端
        min_connections = min(
            self._connection_counts[client_id] for client_id, _ in available_clients
        )
        
        candidates = [
            (client_id, client) for client_id, client in available_clients
            if self._connection_counts[client_id] == min_connections
        ]
        
        return random.choice(candidates) if candidates else None
    
    def _select_client_by_response_time(self) -> Optional[Tuple[str, BaseModelClient]]:
        """按响应时间选择客户端."""
        available_clients = self.get_available_clients()
        if not available_clients:
            return None
        
        # 选择平均响应时间最短的客户端
        best_client = min(
            available_clients,
            key=lambda x: x[1].metrics.average_response_time or float('inf')
        )
        
        return best_client
    
    def select_client(self, request: ModelRequest) -> Optional[Tuple[str, BaseModelClient]]:
        """根据策略选择客户端.
        
        Args:
            request: 模型请求
            
        Returns:
            Optional[Tuple[str, BaseModelClient]]: 选择的客户端，如果没有可用客户端则返回None
        """
        if self.strategy == LoadBalancingStrategy.PRIORITY:
            return self._select_client_by_priority()
        elif self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._select_client_by_round_robin()
        elif self.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            return self._select_client_by_weighted_round_robin()
        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return self._select_client_by_least_connections()
        elif self.strategy == LoadBalancingStrategy.RESPONSE_TIME:
            return self._select_client_by_response_time()
        else:
            return self._select_client_by_priority()
    
    async def chat_completion(self, request: ModelRequest) -> ModelResponse:
        """执行聊天完成请求，支持故障转移.
        
        Args:
            request: 模型请求
            
        Returns:
            ModelResponse: 模型响应
            
        Raises:
            ModelClientError: 所有客户端都不可用时抛出
        """
        attempted_clients = set()
        last_error = None
        
        while len(attempted_clients) < len(self.clients):
            # 选择客户端
            selected = self.select_client(request)
            if not selected:
                break
            
            client_id, client = selected
            
            # 跳过已尝试的客户端
            if client_id in attempted_clients:
                continue
            
            attempted_clients.add(client_id)
            
            try:
                # 更新连接计数
                self._connection_counts[client_id] += 1
                
                # 执行请求
                response = await client.chat_completion(request)
                
                logger.debug(f"Successfully completed request using {client_id}")
                return response
                
            except Exception as e:
                last_error = e
                logger.warning(f"Request failed for {client_id}: {str(e)}")
                
                # 记录故障转移事件
                if len(attempted_clients) < len(self.clients):
                    # 选择下一个客户端作为故障转移目标
                    next_selected = self.select_client(request)
                    if next_selected and next_selected[0] not in attempted_clients:
                        failover_event = FailoverEvent(
                            original_provider=client.provider,
                            fallback_provider=next_selected[1].provider,
                            reason=str(e),
                            request_id=request.request_id,
                            success=True  # 假设会成功，实际结果在下次循环中确定
                        )
                        self.failover_events.append(failover_event)
                        logger.info(f"Failing over from {client_id} to {next_selected[0]}")
                
            finally:
                # 减少连接计数
                self._connection_counts[client_id] = max(0, 
                    self._connection_counts[client_id] - 1)
        
        # 所有客户端都失败了
        error_msg = f"All model clients failed. Last error: {str(last_error)}"
        logger.error(error_msg)
        raise ModelClientError(error_msg, "ALL_CLIENTS_FAILED")
    
    async def chat_completion_stream(self, request: ModelRequest):
        """执行流式聊天完成请求.
        
        Args:
            request: 模型请求
            
        Yields:
            str: 流式响应数据块
            
        Raises:
            ModelClientError: 所有客户端都不可用时抛出
        """
        attempted_clients = set()
        last_error = None
        
        while len(attempted_clients) < len(self.clients):
            # 选择客户端
            selected = self.select_client(request)
            if not selected:
                break
            
            client_id, client = selected
            
            # 跳过已尝试的客户端
            if client_id in attempted_clients:
                continue
            
            attempted_clients.add(client_id)
            
            try:
                # 更新连接计数
                self._connection_counts[client_id] += 1
                
                # 执行流式请求
                async for chunk in client.chat_completion_stream(request):
                    yield chunk
                
                logger.debug(f"Successfully completed stream request using {client_id}")
                return
                
            except Exception as e:
                last_error = e
                logger.warning(f"Stream request failed for {client_id}: {str(e)}")
                
            finally:
                # 减少连接计数
                self._connection_counts[client_id] = max(0, 
                    self._connection_counts[client_id] - 1)
        
        # 所有客户端都失败了
        error_msg = f"All model clients failed for stream request. Last error: {str(last_error)}"
        logger.error(error_msg)
        raise ModelClientError(error_msg, "ALL_CLIENTS_FAILED")
    
    async def health_check(self) -> Dict[str, bool]:
        """检查所有客户端的健康状态.
        
        Returns:
            Dict[str, bool]: 客户端健康状态映射
        """
        health_status = {}
        
        # 限制并发数量，避免过多并发请求
        semaphore = asyncio.Semaphore(5)  # 最多5个并发健康检查
        
        async def check_with_semaphore(client_id: str, client: BaseModelClient):
            async with semaphore:
                return await self._check_client_health(client_id, client)
        
        # 并发检查所有客户端
        tasks = []
        for client_id, client in self.clients.items():
            task = asyncio.create_task(check_with_semaphore(client_id, client))
            tasks.append((client_id, task))
        
        # 设置超时时间，避免长时间等待
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*[task for _, task in tasks], return_exceptions=True),
                timeout=30.0  # 30秒超时
            )
            
            for i, (client_id, _) in enumerate(tasks):
                result = results[i]
                if isinstance(result, Exception):
                    health_status[client_id] = False
                    logger.debug(f"Health check failed for {client_id}: {str(result)}")
                else:
                    health_status[client_id] = result
                    
        except asyncio.TimeoutError:
            logger.warning("Health check timeout, marking all clients as unhealthy")
            for client_id, _ in tasks:
                health_status[client_id] = False
        
        return health_status
    
    async def _check_client_health(self, client_id: str, client: BaseModelClient) -> bool:
        """检查单个客户端的健康状态."""
        try:
            # 检查是否在冷却期
            if (hasattr(client, '_last_health_check_failed') and 
                client._last_health_check_failed and
                hasattr(client, '_health_check_cooldown_until')):
                import time
                if time.time() < client._health_check_cooldown_until:
                    logger.debug(f"Client {client_id} in cooldown period, skipping health check")
                    return False
            
            # 添加超时控制
            return await asyncio.wait_for(client.health_check(), timeout=5.0)
        except asyncio.TimeoutError:
            logger.debug(f"Health check timeout for {client_id}")
            return False
        except Exception as e:
            logger.debug(f"Health check error for {client_id}: {str(e)}")
            return False
    
    def get_metrics(self) -> Dict[str, Dict]:
        """获取所有客户端的性能指标.
        
        Returns:
            Dict[str, Dict]: 客户端指标映射
        """
        metrics = {}
        for client_id, client in self.clients.items():
            metrics[client_id] = client.get_metrics().model_dump()
        
        return metrics
    
    def get_failover_events(self, limit: int = 100) -> List[FailoverEvent]:
        """获取故障转移事件历史.
        
        Args:
            limit: 返回事件数量限制
            
        Returns:
            List[FailoverEvent]: 故障转移事件列表
        """
        return self.failover_events[-limit:]
    
    def set_strategy(self, strategy: LoadBalancingStrategy) -> None:
        """设置负载均衡策略.
        
        Args:
            strategy: 负载均衡策略
        """
        self.strategy = strategy
        logger.info(f"Changed load balancing strategy to: {strategy}")
    
    async def close(self) -> None:
        """关闭所有客户端连接."""
        tasks = []
        for client in self.clients.values():
            task = asyncio.create_task(client.close())
            tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("Closed all model clients")
    
    def __len__(self) -> int:
        """返回客户端数量."""
        return len(self.clients)
    
    def __str__(self) -> str:
        return f"ModelRouter(clients={len(self.clients)}, strategy={self.strategy})"
    
    def __repr__(self) -> str:
        client_info = [f"{cid}({self.configs[cid].enabled})" 
                      for cid in self.clients.keys()]
        return (f"ModelRouter(strategy={self.strategy}, "
                f"clients=[{', '.join(client_info)}])")


class ModelRouterManager:
    """模型路由器管理器，支持多个路由器实例."""
    
    def __init__(self):
        """初始化路由器管理器."""
        self.routers: Dict[str, ModelRouter] = {}
        logger.info("Initialized model router manager")
    
    def create_router(self, name: str, configs: List[ModelConfig], 
                     strategy: LoadBalancingStrategy = LoadBalancingStrategy.PRIORITY) -> ModelRouter:
        """创建新的路由器实例.
        
        Args:
            name: 路由器名称
            configs: 模型配置列表
            strategy: 负载均衡策略
            
        Returns:
            ModelRouter: 路由器实例
        """
        router = ModelRouter(configs, strategy)
        self.routers[name] = router
        logger.info(f"Created router: {name}")
        return router
    
    def get_router(self, name: str) -> Optional[ModelRouter]:
        """获取路由器实例.
        
        Args:
            name: 路由器名称
            
        Returns:
            Optional[ModelRouter]: 路由器实例，不存在则返回None
        """
        return self.routers.get(name)
    
    def remove_router(self, name: str) -> None:
        """移除路由器实例.
        
        Args:
            name: 路由器名称
        """
        if name in self.routers:
            del self.routers[name]
            logger.info(f"Removed router: {name}")
    
    async def close_all(self) -> None:
        """关闭所有路由器."""
        tasks = []
        for router in self.routers.values():
            task = asyncio.create_task(router.close())
            tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)
        self.routers.clear()
        logger.info("Closed all routers")
    
    def list_routers(self) -> List[str]:
        """列出所有路由器名称.
        
        Returns:
            List[str]: 路由器名称列表
        """
        return list(self.routers.keys())


# 全局路由器管理器实例
router_manager = ModelRouterManager()