"""Hot reload service for dynamic configuration updates."""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Callable, Set
from datetime import datetime
from threading import Lock
from pathlib import Path

from ..config.config_manager import ConfigManager
from ..models.config import AgentConfig, ModelConfig, WorkflowConfig
from ..utils.exceptions import ConfigurationError


logger = logging.getLogger(__name__)


class ConfigChangeEvent:
    """配置变更事件."""
    
    def __init__(
        self,
        config_type: str,
        config_id: str,
        change_type: str,  # 'created', 'updated', 'deleted'
        old_config: Optional[Dict[str, Any]] = None,
        new_config: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ):
        self.config_type = config_type
        self.config_id = config_id
        self.change_type = change_type
        self.old_config = old_config
        self.new_config = new_config
        self.timestamp = timestamp or datetime.now()
    
    def __str__(self) -> str:
        return f"ConfigChangeEvent({self.config_type}.{self.config_id}: {self.change_type})"


class ConfigChangeHandler:
    """配置变更处理器基类."""
    
    async def handle_agent_config_change(self, event: ConfigChangeEvent) -> None:
        """处理智能体配置变更."""
        pass
    
    async def handle_model_config_change(self, event: ConfigChangeEvent) -> None:
        """处理模型配置变更."""
        pass
    
    async def handle_workflow_config_change(self, event: ConfigChangeEvent) -> None:
        """处理工作流配置变更."""
        pass


class HotReloadService:
    """热重载服务，负责配置的动态更新和通知."""
    
    def __init__(self, config_manager: ConfigManager):
        """初始化热重载服务.
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
        self._handlers: List[ConfigChangeHandler] = []
        self._change_queue: asyncio.Queue = asyncio.Queue()
        self._processing_task: Optional[asyncio.Task] = None
        self._is_running = False
        self._lock = Lock()
        
        # 配置快照，用于检测变更
        self._agent_config_snapshot: Dict[str, Dict[str, Any]] = {}
        self._model_config_snapshot: Dict[str, Dict[str, Any]] = {}
        self._workflow_config_snapshot: Dict[str, Dict[str, Any]] = {}
        
        # 变更监听器
        self._change_listeners: Dict[str, List[Callable]] = {
            'agent': [],
            'model': [],
            'workflow': []
        }
        
        # 初始化快照
        self._update_snapshots()
    
    def add_handler(self, handler: ConfigChangeHandler) -> None:
        """添加配置变更处理器.
        
        Args:
            handler: 配置变更处理器
        """
        with self._lock:
            if handler not in self._handlers:
                self._handlers.append(handler)
                logger.info(f"Added config change handler: {handler.__class__.__name__}")
    
    def remove_handler(self, handler: ConfigChangeHandler) -> None:
        """移除配置变更处理器.
        
        Args:
            handler: 配置变更处理器
        """
        with self._lock:
            if handler in self._handlers:
                self._handlers.remove(handler)
                logger.info(f"Removed config change handler: {handler.__class__.__name__}")
    
    def add_change_listener(self, config_type: str, listener: Callable) -> None:
        """添加配置变更监听器.
        
        Args:
            config_type: 配置类型 ('agent', 'model', 'workflow')
            listener: 监听器函数
        """
        if config_type in self._change_listeners:
            self._change_listeners[config_type].append(listener)
            logger.info(f"Added change listener for {config_type} config")
    
    def remove_change_listener(self, config_type: str, listener: Callable) -> None:
        """移除配置变更监听器.
        
        Args:
            config_type: 配置类型
            listener: 监听器函数
        """
        if config_type in self._change_listeners and listener in self._change_listeners[config_type]:
            self._change_listeners[config_type].remove(listener)
            logger.info(f"Removed change listener for {config_type} config")
    
    async def start(self) -> None:
        """启动热重载服务."""
        if self._is_running:
            return
        
        self._is_running = True
        self._processing_task = asyncio.create_task(self._process_changes())
        
        # 启动配置文件监控
        self.config_manager.start_file_watching()
        
        # 定期检查配置变更
        asyncio.create_task(self._periodic_config_check())
        
        logger.info("Hot reload service started")
    
    async def stop(self) -> None:
        """停止热重载服务."""
        if not self._is_running:
            return
        
        self._is_running = False
        
        # 停止配置文件监控
        self.config_manager.stop_file_watching()
        
        # 停止处理任务
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Hot reload service stopped")
    
    async def reload_config(self, config_type: Optional[str] = None, force: bool = False) -> Dict[str, Any]:
        """手动重新加载配置.
        
        Args:
            config_type: 配置类型，None表示重新加载所有配置
            force: 是否强制重新加载
            
        Returns:
            Dict[str, Any]: 重新加载结果
        """
        try:
            # 保存旧的配置快照
            old_agent_snapshot = self._agent_config_snapshot.copy()
            old_model_snapshot = self._model_config_snapshot.copy()
            old_workflow_snapshot = self._workflow_config_snapshot.copy()
            
            # 重新加载配置
            self.config_manager.reload_config(config_type)
            
            # 更新快照
            self._update_snapshots()
            
            # 检测并处理变更
            changes = []
            
            if config_type is None or config_type == 'agents':
                changes.extend(await self._detect_agent_changes(old_agent_snapshot))
            
            if config_type is None or config_type == 'models':
                changes.extend(await self._detect_model_changes(old_model_snapshot))
            
            if config_type is None or config_type == 'workflows':
                changes.extend(await self._detect_workflow_changes(old_workflow_snapshot))
            
            # 处理变更
            for change in changes:
                await self._change_queue.put(change)
            
            return {
                "success": True,
                "message": f"Configuration reloaded: {config_type or 'all'}",
                "changes_detected": len(changes),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
            return {
                "success": False,
                "message": f"Failed to reload configuration: {e}",
                "changes_detected": 0,
                "timestamp": datetime.now().isoformat()
            }
    
    async def apply_config_change(
        self,
        config_type: str,
        config_id: str,
        config_data: Dict[str, Any],
        hot_reload: bool = True
    ) -> Dict[str, Any]:
        """应用配置变更.
        
        Args:
            config_type: 配置类型
            config_id: 配置ID
            config_data: 配置数据
            hot_reload: 是否热重载
            
        Returns:
            Dict[str, Any]: 应用结果
        """
        try:
            # 获取旧配置
            old_config = None
            if config_type == 'agent':
                old_config_obj = self.config_manager.get_agent_config(config_id)
                old_config = old_config_obj.model_dump() if old_config_obj else None
            elif config_type == 'model':
                old_config_obj = self.config_manager.get_model_config(config_id)
                old_config = old_config_obj.model_dump() if old_config_obj else None
            elif config_type == 'workflow':
                old_config_obj = self.config_manager.get_workflow_config(config_id)
                old_config = old_config_obj.model_dump() if old_config_obj else None
            
            # 应用配置变更
            if config_type == 'agent':
                new_config = AgentConfig(**config_data)
                self.config_manager.update_agent_config(config_id, new_config)
            elif config_type == 'model':
                new_config = ModelConfig(**config_data)
                self.config_manager.update_model_config(config_id, new_config)
            elif config_type == 'workflow':
                new_config = WorkflowConfig(**config_data)
                self.config_manager.update_workflow_config(config_id, new_config)
            else:
                raise ValueError(f"Unsupported config type: {config_type}")
            
            # 更新快照
            self._update_snapshots()
            
            # 如果启用热重载，创建变更事件
            if hot_reload:
                change_type = 'updated' if old_config else 'created'
                event = ConfigChangeEvent(
                    config_type=config_type,
                    config_id=config_id,
                    change_type=change_type,
                    old_config=old_config,
                    new_config=config_data
                )
                
                await self._change_queue.put(event)
            
            return {
                "success": True,
                "message": f"Configuration applied: {config_type}.{config_id}",
                "change_type": 'updated' if old_config else 'created',
                "hot_reload": hot_reload,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to apply config change: {e}")
            return {
                "success": False,
                "message": f"Failed to apply config change: {e}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def remove_config(
        self,
        config_type: str,
        config_id: str,
        hot_reload: bool = True
    ) -> Dict[str, Any]:
        """移除配置.
        
        Args:
            config_type: 配置类型
            config_id: 配置ID
            hot_reload: 是否热重载
            
        Returns:
            Dict[str, Any]: 移除结果
        """
        try:
            # 获取旧配置
            old_config = None
            if config_type == 'agent':
                old_config_obj = self.config_manager.get_agent_config(config_id)
                old_config = old_config_obj.model_dump() if old_config_obj else None
            elif config_type == 'model':
                old_config_obj = self.config_manager.get_model_config(config_id)
                old_config = old_config_obj.model_dump() if old_config_obj else None
            elif config_type == 'workflow':
                old_config_obj = self.config_manager.get_workflow_config(config_id)
                old_config = old_config_obj.model_dump() if old_config_obj else None
            
            if not old_config:
                return {
                    "success": False,
                    "message": f"Configuration not found: {config_type}.{config_id}",
                    "timestamp": datetime.now().isoformat()
                }
            
            # 移除配置（通过设置为禁用状态）
            old_config['enabled'] = False
            
            if config_type == 'agent':
                disabled_config = AgentConfig(**old_config)
                self.config_manager.update_agent_config(config_id, disabled_config)
            elif config_type == 'model':
                disabled_config = ModelConfig(**old_config)
                self.config_manager.update_model_config(config_id, disabled_config)
            elif config_type == 'workflow':
                disabled_config = WorkflowConfig(**old_config)
                self.config_manager.update_workflow_config(config_id, disabled_config)
            
            # 更新快照
            self._update_snapshots()
            
            # 如果启用热重载，创建变更事件
            if hot_reload:
                event = ConfigChangeEvent(
                    config_type=config_type,
                    config_id=config_id,
                    change_type='deleted',
                    old_config=old_config,
                    new_config=None
                )
                
                await self._change_queue.put(event)
            
            return {
                "success": True,
                "message": f"Configuration removed: {config_type}.{config_id}",
                "change_type": "deleted",
                "hot_reload": hot_reload,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to remove config: {e}")
            return {
                "success": False,
                "message": f"Failed to remove config: {e}",
                "timestamp": datetime.now().isoformat()
            }
    
    def _update_snapshots(self) -> None:
        """更新配置快照."""
        # 更新智能体配置快照
        self._agent_config_snapshot = {
            agent_id: config.model_dump()
            for agent_id, config in self.config_manager.get_all_agent_configs().items()
        }
        
        # 更新模型配置快照
        self._model_config_snapshot = {
            model_id: config.model_dump()
            for model_id, config in self.config_manager.get_all_model_configs().items()
        }
        
        # 更新工作流配置快照
        self._workflow_config_snapshot = {
            workflow_id: config.model_dump()
            for workflow_id, config in self.config_manager.get_all_workflow_configs().items()
        }
    
    async def _detect_agent_changes(self, old_snapshot: Dict[str, Dict[str, Any]]) -> List[ConfigChangeEvent]:
        """检测智能体配置变更."""
        changes = []
        current_configs = self.config_manager.get_all_agent_configs()
        
        # 检测新增和更新
        for agent_id, config in current_configs.items():
            current_data = config.model_dump()
            
            if agent_id not in old_snapshot:
                # 新增配置
                changes.append(ConfigChangeEvent(
                    config_type='agent',
                    config_id=agent_id,
                    change_type='created',
                    old_config=None,
                    new_config=current_data
                ))
            elif current_data != old_snapshot[agent_id]:
                # 更新配置
                changes.append(ConfigChangeEvent(
                    config_type='agent',
                    config_id=agent_id,
                    change_type='updated',
                    old_config=old_snapshot[agent_id],
                    new_config=current_data
                ))
        
        # 检测删除
        for agent_id in old_snapshot:
            if agent_id not in current_configs:
                changes.append(ConfigChangeEvent(
                    config_type='agent',
                    config_id=agent_id,
                    change_type='deleted',
                    old_config=old_snapshot[agent_id],
                    new_config=None
                ))
        
        return changes
    
    async def _detect_model_changes(self, old_snapshot: Dict[str, Dict[str, Any]]) -> List[ConfigChangeEvent]:
        """检测模型配置变更."""
        changes = []
        current_configs = self.config_manager.get_all_model_configs()
        
        # 检测新增和更新
        for model_id, config in current_configs.items():
            current_data = config.model_dump()
            
            if model_id not in old_snapshot:
                # 新增配置
                changes.append(ConfigChangeEvent(
                    config_type='model',
                    config_id=model_id,
                    change_type='created',
                    old_config=None,
                    new_config=current_data
                ))
            elif current_data != old_snapshot[model_id]:
                # 更新配置
                changes.append(ConfigChangeEvent(
                    config_type='model',
                    config_id=model_id,
                    change_type='updated',
                    old_config=old_snapshot[model_id],
                    new_config=current_data
                ))
        
        # 检测删除
        for model_id in old_snapshot:
            if model_id not in current_configs:
                changes.append(ConfigChangeEvent(
                    config_type='model',
                    config_id=model_id,
                    change_type='deleted',
                    old_config=old_snapshot[model_id],
                    new_config=None
                ))
        
        return changes
    
    async def _detect_workflow_changes(self, old_snapshot: Dict[str, Dict[str, Any]]) -> List[ConfigChangeEvent]:
        """检测工作流配置变更."""
        changes = []
        current_configs = self.config_manager.get_all_workflow_configs()
        
        # 检测新增和更新
        for workflow_id, config in current_configs.items():
            current_data = config.model_dump()
            
            if workflow_id not in old_snapshot:
                # 新增配置
                changes.append(ConfigChangeEvent(
                    config_type='workflow',
                    config_id=workflow_id,
                    change_type='created',
                    old_config=None,
                    new_config=current_data
                ))
            elif current_data != old_snapshot[workflow_id]:
                # 更新配置
                changes.append(ConfigChangeEvent(
                    config_type='workflow',
                    config_id=workflow_id,
                    change_type='updated',
                    old_config=old_snapshot[workflow_id],
                    new_config=current_data
                ))
        
        # 检测删除
        for workflow_id in old_snapshot:
            if workflow_id not in current_configs:
                changes.append(ConfigChangeEvent(
                    config_type='workflow',
                    config_id=workflow_id,
                    change_type='deleted',
                    old_config=old_snapshot[workflow_id],
                    new_config=None
                ))
        
        return changes
    
    async def _process_changes(self) -> None:
        """处理配置变更队列."""
        while self._is_running:
            try:
                # 等待变更事件
                event = await asyncio.wait_for(self._change_queue.get(), timeout=1.0)
                
                logger.info(f"Processing config change: {event}")
                
                # 通知处理器
                handlers = self._handlers.copy()
                for handler in handlers:
                    try:
                        if event.config_type == 'agent':
                            await handler.handle_agent_config_change(event)
                        elif event.config_type == 'model':
                            await handler.handle_model_config_change(event)
                        elif event.config_type == 'workflow':
                            await handler.handle_workflow_config_change(event)
                    except Exception as e:
                        logger.error(f"Handler {handler.__class__.__name__} failed to process change: {e}")
                
                # 通知监听器
                listeners = self._change_listeners.get(event.config_type, []).copy()
                for listener in listeners:
                    try:
                        if asyncio.iscoroutinefunction(listener):
                            await listener(event)
                        else:
                            listener(event)
                    except Exception as e:
                        logger.error(f"Listener failed to process change: {e}")
                
                # 标记任务完成
                self._change_queue.task_done()
                
            except asyncio.TimeoutError:
                # 超时，继续循环
                continue
            except Exception as e:
                logger.error(f"Error processing config changes: {e}")
    
    async def _periodic_config_check(self) -> None:
        """定期检查配置变更."""
        while self._is_running:
            try:
                await asyncio.sleep(30)  # 每30秒检查一次
                
                # 保存旧快照
                old_agent_snapshot = self._agent_config_snapshot.copy()
                old_model_snapshot = self._model_config_snapshot.copy()
                old_workflow_snapshot = self._workflow_config_snapshot.copy()
                
                # 更新快照
                self._update_snapshots()
                
                # 检测变更
                changes = []
                changes.extend(await self._detect_agent_changes(old_agent_snapshot))
                changes.extend(await self._detect_model_changes(old_model_snapshot))
                changes.extend(await self._detect_workflow_changes(old_workflow_snapshot))
                
                # 处理变更
                for change in changes:
                    await self._change_queue.put(change)
                
                if changes:
                    logger.info(f"Detected {len(changes)} config changes during periodic check")
                
            except Exception as e:
                logger.error(f"Error during periodic config check: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取热重载服务状态."""
        return {
            "is_running": self._is_running,
            "handlers_count": len(self._handlers),
            "change_listeners_count": sum(len(listeners) for listeners in self._change_listeners.values()),
            "queue_size": self._change_queue.qsize(),
            "config_snapshots": {
                "agents": len(self._agent_config_snapshot),
                "models": len(self._model_config_snapshot),
                "workflows": len(self._workflow_config_snapshot)
            }
        }