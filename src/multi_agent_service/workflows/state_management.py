"""状态管理和消息传递实现."""

import asyncio
import json
from typing import Any, Dict, List, Optional, Set
from datetime import datetime
from collections import defaultdict, deque
from abc import ABC, abstractmethod

from .interfaces import StateManagerInterface, MessageBusInterface
from ..models.workflow import WorkflowMessage, WorkflowExecution, NodeExecutionContext
from ..models.enums import WorkflowStatus


class InMemoryStateManager(StateManagerInterface):
    """内存状态管理器."""
    
    def __init__(self):
        self.states: Dict[str, Dict[str, Any]] = {}
        self.state_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.locks: Dict[str, asyncio.Lock] = {}
    
    async def get_state(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """获取执行状态."""
        return self.states.get(execution_id)
    
    async def update_state(self, execution_id: str, state_data: Dict[str, Any]) -> bool:
        """更新执行状态."""
        try:
            # 获取或创建锁
            if execution_id not in self.locks:
                self.locks[execution_id] = asyncio.Lock()
            
            async with self.locks[execution_id]:
                # 保存历史状态
                if execution_id in self.states:
                    self.state_history[execution_id].append({
                        "timestamp": datetime.now().isoformat(),
                        "state": self.states[execution_id].copy()
                    })
                
                # 更新当前状态
                if execution_id not in self.states:
                    self.states[execution_id] = {}
                
                self.states[execution_id].update(state_data)
                self.states[execution_id]["last_updated"] = datetime.now().isoformat()
                
                return True
        except Exception:
            return False
    
    async def delete_state(self, execution_id: str) -> bool:
        """删除执行状态."""
        try:
            if execution_id in self.states:
                del self.states[execution_id]
            
            if execution_id in self.state_history:
                del self.state_history[execution_id]
            
            if execution_id in self.locks:
                del self.locks[execution_id]
            
            return True
        except Exception:
            return False
    
    async def persist_state(self, execution_id: str) -> bool:
        """持久化状态（内存实现中为空操作）."""
        # 在实际实现中，这里会将状态保存到持久化存储
        return True
    
    async def get_state_history(self, execution_id: str) -> List[Dict[str, Any]]:
        """获取状态历史."""
        return self.state_history.get(execution_id, [])
    
    async def cleanup_old_states(self, max_age_hours: int = 24) -> int:
        """清理旧状态."""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        cleaned_count = 0
        
        execution_ids_to_remove = []
        for execution_id, state in self.states.items():
            last_updated = state.get("last_updated")
            if last_updated:
                try:
                    update_time = datetime.fromisoformat(last_updated).timestamp()
                    if update_time < cutoff_time:
                        execution_ids_to_remove.append(execution_id)
                except ValueError:
                    # 如果时间格式无效，也删除
                    execution_ids_to_remove.append(execution_id)
        
        for execution_id in execution_ids_to_remove:
            await self.delete_state(execution_id)
            cleaned_count += 1
        
        return cleaned_count


class InMemoryMessageBus(MessageBusInterface):
    """内存消息总线."""
    
    def __init__(self):
        self.message_queues: Dict[str, deque] = defaultdict(deque)
        self.subscriptions: Dict[str, Set[str]] = defaultdict(set)
        self.message_history: List[WorkflowMessage] = []
        self.max_history_size = 1000
        self.locks: Dict[str, asyncio.Lock] = {}
    
    async def send_message(self, message: WorkflowMessage) -> bool:
        """发送消息."""
        try:
            # 记录消息历史
            self.message_history.append(message)
            if len(self.message_history) > self.max_history_size:
                self.message_history.pop(0)
            
            # 如果指定了接收者，直接发送
            if message.receiver_node:
                await self._deliver_message(message.receiver_node, message)
            else:
                # 广播给所有订阅了该消息类型的节点
                subscribers = self.subscriptions.get(message.message_type, set())
                for subscriber in subscribers:
                    await self._deliver_message(subscriber, message)
            
            return True
        except Exception:
            return False
    
    async def receive_message(self, node_id: str) -> Optional[WorkflowMessage]:
        """接收消息."""
        try:
            if node_id not in self.locks:
                self.locks[node_id] = asyncio.Lock()
            
            async with self.locks[node_id]:
                queue = self.message_queues[node_id]
                if queue:
                    return queue.popleft()
                return None
        except Exception:
            return None
    
    async def broadcast_message(self, message: WorkflowMessage, target_nodes: List[str]) -> bool:
        """广播消息."""
        try:
            for node_id in target_nodes:
                await self._deliver_message(node_id, message)
            
            # 记录消息历史
            self.message_history.append(message)
            if len(self.message_history) > self.max_history_size:
                self.message_history.pop(0)
            
            return True
        except Exception:
            return False
    
    async def subscribe(self, node_id: str, message_types: List[str]) -> bool:
        """订阅消息类型."""
        try:
            for message_type in message_types:
                self.subscriptions[message_type].add(node_id)
            return True
        except Exception:
            return False
    
    async def unsubscribe(self, node_id: str, message_types: List[str]) -> bool:
        """取消订阅消息类型."""
        try:
            for message_type in message_types:
                self.subscriptions[message_type].discard(node_id)
            return True
        except Exception:
            return False
    
    async def _deliver_message(self, node_id: str, message: WorkflowMessage) -> None:
        """投递消息到节点队列."""
        if node_id not in self.locks:
            self.locks[node_id] = asyncio.Lock()
        
        async with self.locks[node_id]:
            self.message_queues[node_id].append(message)
    
    async def get_message_history(self, limit: int = 100) -> List[WorkflowMessage]:
        """获取消息历史."""
        return self.message_history[-limit:]
    
    async def get_queue_size(self, node_id: str) -> int:
        """获取节点消息队列大小."""
        return len(self.message_queues[node_id])
    
    async def clear_queue(self, node_id: str) -> int:
        """清空节点消息队列."""
        if node_id not in self.locks:
            self.locks[node_id] = asyncio.Lock()
        
        async with self.locks[node_id]:
            queue = self.message_queues[node_id]
            size = len(queue)
            queue.clear()
            return size


class WorkflowStateManager:
    """工作流状态管理器，整合状态管理和消息传递."""
    
    def __init__(
        self, 
        state_manager: Optional[StateManagerInterface] = None,
        message_bus: Optional[MessageBusInterface] = None
    ):
        self.state_manager = state_manager or InMemoryStateManager()
        self.message_bus = message_bus or InMemoryMessageBus()
        self.active_executions: Dict[str, WorkflowExecution] = {}
    
    async def start_execution(self, execution: WorkflowExecution) -> bool:
        """开始工作流执行."""
        try:
            self.active_executions[execution.execution_id] = execution
            
            # 初始化状态
            initial_state = {
                "execution_id": execution.execution_id,
                "graph_id": execution.graph_id,
                "status": execution.status.value,
                "start_time": execution.start_time.isoformat() if execution.start_time else None,
                "input_data": execution.input_data,
                "current_node": execution.current_node,
                "node_results": execution.node_results
            }
            
            await self.state_manager.update_state(execution.execution_id, initial_state)
            
            # 发送执行开始消息
            start_message = WorkflowMessage(
                sender_node="system",
                message_type="execution_started",
                content={
                    "execution_id": execution.execution_id,
                    "graph_id": execution.graph_id,
                    "timestamp": datetime.now().isoformat()
                }
            )
            await self.message_bus.send_message(start_message)
            
            return True
        except Exception:
            return False
    
    async def update_execution_state(
        self, 
        execution_id: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """更新执行状态."""
        try:
            # 更新内存中的执行对象
            if execution_id in self.active_executions:
                execution = self.active_executions[execution_id]
                
                if "status" in updates:
                    execution.status = WorkflowStatus(updates["status"])
                if "current_node" in updates:
                    execution.current_node = updates["current_node"]
                if "node_results" in updates:
                    execution.node_results.update(updates["node_results"])
                if "output_data" in updates:
                    execution.output_data = updates["output_data"]
                if "error_message" in updates:
                    execution.error_message = updates["error_message"]
                if "end_time" in updates:
                    execution.end_time = datetime.fromisoformat(updates["end_time"])
            
            # 更新持久化状态
            await self.state_manager.update_state(execution_id, updates)
            
            # 发送状态更新消息
            update_message = WorkflowMessage(
                sender_node="system",
                message_type="state_updated",
                content={
                    "execution_id": execution_id,
                    "updates": updates,
                    "timestamp": datetime.now().isoformat()
                }
            )
            await self.message_bus.send_message(update_message)
            
            return True
        except Exception:
            return False
    
    async def complete_execution(self, execution_id: str, final_result: Dict[str, Any]) -> bool:
        """完成工作流执行."""
        try:
            updates = {
                "status": WorkflowStatus.COMPLETED.value,
                "output_data": final_result,
                "end_time": datetime.now().isoformat()
            }
            
            await self.update_execution_state(execution_id, updates)
            
            # 发送执行完成消息
            complete_message = WorkflowMessage(
                sender_node="system",
                message_type="execution_completed",
                content={
                    "execution_id": execution_id,
                    "final_result": final_result,
                    "timestamp": datetime.now().isoformat()
                }
            )
            await self.message_bus.send_message(complete_message)
            
            # 从活跃执行中移除
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
            
            return True
        except Exception:
            return False
    
    async def fail_execution(self, execution_id: str, error_message: str) -> bool:
        """标记工作流执行失败."""
        try:
            updates = {
                "status": WorkflowStatus.FAILED.value,
                "error_message": error_message,
                "end_time": datetime.now().isoformat()
            }
            
            await self.update_execution_state(execution_id, updates)
            
            # 发送执行失败消息
            fail_message = WorkflowMessage(
                sender_node="system",
                message_type="execution_failed",
                content={
                    "execution_id": execution_id,
                    "error_message": error_message,
                    "timestamp": datetime.now().isoformat()
                }
            )
            await self.message_bus.send_message(fail_message)
            
            # 从活跃执行中移除
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
            
            return True
        except Exception:
            return False
    
    async def get_execution_state(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """获取执行状态."""
        return await self.state_manager.get_state(execution_id)
    
    async def update_state(self, execution_id: str, state_data: Dict[str, Any]) -> bool:
        """更新状态（直接调用底层状态管理器）."""
        return await self.state_manager.update_state(execution_id, state_data)
    
    async def get_state(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """获取状态（直接调用底层状态管理器）."""
        return await self.state_manager.get_state(execution_id)
    
    async def delete_state(self, execution_id: str) -> bool:
        """删除状态（直接调用底层状态管理器）."""
        return await self.state_manager.delete_state(execution_id)
    
    async def send_node_message(
        self, 
        sender_node: str, 
        receiver_node: str, 
        message_type: str, 
        content: Dict[str, Any]
    ) -> bool:
        """发送节点间消息."""
        message = WorkflowMessage(
            sender_node=sender_node,
            receiver_node=receiver_node,
            message_type=message_type,
            content=content
        )
        return await self.message_bus.send_message(message)
    
    async def receive_node_message(self, node_id: str) -> Optional[WorkflowMessage]:
        """接收节点消息."""
        return await self.message_bus.receive_message(node_id)
    
    async def subscribe_to_messages(self, node_id: str, message_types: List[str]) -> bool:
        """订阅消息类型."""
        return await self.message_bus.subscribe(node_id, message_types)


class StateSnapshot:
    """状态快照，用于状态回滚和恢复."""
    
    def __init__(self, execution_id: str, state_data: Dict[str, Any]):
        self.execution_id = execution_id
        self.state_data = state_data.copy()
        self.timestamp = datetime.now()
        self.snapshot_id = f"{execution_id}_{self.timestamp.isoformat()}"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典."""
        return {
            "snapshot_id": self.snapshot_id,
            "execution_id": self.execution_id,
            "state_data": self.state_data,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StateSnapshot':
        """从字典创建快照."""
        snapshot = cls(data["execution_id"], data["state_data"])
        snapshot.snapshot_id = data["snapshot_id"]
        snapshot.timestamp = datetime.fromisoformat(data["timestamp"])
        return snapshot


class SnapshotManager:
    """快照管理器，用于状态快照和恢复."""
    
    def __init__(self, max_snapshots_per_execution: int = 10):
        self.snapshots: Dict[str, List[StateSnapshot]] = defaultdict(list)
        self.max_snapshots_per_execution = max_snapshots_per_execution
    
    async def create_snapshot(self, execution_id: str, state_data: Dict[str, Any]) -> str:
        """创建状态快照."""
        snapshot = StateSnapshot(execution_id, state_data)
        
        # 添加快照
        self.snapshots[execution_id].append(snapshot)
        
        # 限制快照数量
        if len(self.snapshots[execution_id]) > self.max_snapshots_per_execution:
            self.snapshots[execution_id].pop(0)
        
        return snapshot.snapshot_id
    
    async def get_snapshot(self, snapshot_id: str) -> Optional[StateSnapshot]:
        """获取快照."""
        for execution_snapshots in self.snapshots.values():
            for snapshot in execution_snapshots:
                if snapshot.snapshot_id == snapshot_id:
                    return snapshot
        return None
    
    async def get_latest_snapshot(self, execution_id: str) -> Optional[StateSnapshot]:
        """获取最新快照."""
        snapshots = self.snapshots.get(execution_id, [])
        return snapshots[-1] if snapshots else None
    
    async def list_snapshots(self, execution_id: str) -> List[StateSnapshot]:
        """列出执行的所有快照."""
        return self.snapshots.get(execution_id, []).copy()
    
    async def restore_from_snapshot(
        self, 
        snapshot_id: str, 
        state_manager: StateManagerInterface
    ) -> bool:
        """从快照恢复状态."""
        snapshot = await self.get_snapshot(snapshot_id)
        if not snapshot:
            return False
        
        try:
            await state_manager.update_state(snapshot.execution_id, snapshot.state_data)
            return True
        except Exception:
            return False
    
    async def cleanup_snapshots(self, execution_id: str) -> int:
        """清理执行的快照."""
        if execution_id in self.snapshots:
            count = len(self.snapshots[execution_id])
            del self.snapshots[execution_id]
            return count
        return 0


class MessageFilter:
    """消息过滤器，用于消息路由和过滤."""
    
    def __init__(self):
        self.filters: Dict[str, List[callable]] = defaultdict(list)
    
    def add_filter(self, message_type: str, filter_func: callable) -> None:
        """添加消息过滤器."""
        self.filters[message_type].append(filter_func)
    
    def remove_filter(self, message_type: str, filter_func: callable) -> bool:
        """移除消息过滤器."""
        if message_type in self.filters:
            try:
                self.filters[message_type].remove(filter_func)
                return True
            except ValueError:
                pass
        return False
    
    async def filter_message(self, message: WorkflowMessage) -> bool:
        """过滤消息，返回是否应该传递."""
        filters = self.filters.get(message.message_type, [])
        
        for filter_func in filters:
            try:
                if not await filter_func(message):
                    return False
            except Exception:
                # 过滤器异常时，默认通过
                continue
        
        return True


class EventEmitter:
    """事件发射器，用于工作流事件处理."""
    
    def __init__(self):
        self.listeners: Dict[str, List[callable]] = defaultdict(list)
    
    def on(self, event_type: str, listener: callable) -> None:
        """添加事件监听器."""
        self.listeners[event_type].append(listener)
    
    def off(self, event_type: str, listener: callable) -> bool:
        """移除事件监听器."""
        if event_type in self.listeners:
            try:
                self.listeners[event_type].remove(listener)
                return True
            except ValueError:
                pass
        return False
    
    async def emit(self, event_type: str, *args, **kwargs) -> None:
        """发射事件."""
        listeners = self.listeners.get(event_type, [])
        
        for listener in listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(*args, **kwargs)
                else:
                    listener(*args, **kwargs)
            except Exception:
                # 监听器异常不应该影响其他监听器
                continue
    
    def listener_count(self, event_type: str) -> int:
        """获取事件监听器数量."""
        return len(self.listeners.get(event_type, []))


class StateTransition:
    """状态转换管理器."""
    
    def __init__(self):
        self.transitions: Dict[str, Dict[str, List[str]]] = {}
        self.transition_handlers: Dict[str, callable] = {}
    
    def define_transitions(self, state_machine: Dict[str, Dict[str, List[str]]]) -> None:
        """定义状态转换规则."""
        self.transitions = state_machine
    
    def add_transition_handler(self, transition: str, handler: callable) -> None:
        """添加状态转换处理器."""
        self.transition_handlers[transition] = handler
    
    async def can_transition(self, from_state: str, to_state: str) -> bool:
        """检查是否可以进行状态转换."""
        if from_state not in self.transitions:
            return False
        
        allowed_transitions = []
        for event, states in self.transitions[from_state].items():
            allowed_transitions.extend(states)
        
        return to_state in allowed_transitions
    
    async def transition(
        self, 
        execution_id: str, 
        from_state: str, 
        to_state: str, 
        event: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """执行状态转换."""
        if not await self.can_transition(from_state, to_state):
            return False
        
        transition_key = f"{from_state}->{to_state}"
        
        # 执行转换处理器
        if transition_key in self.transition_handlers:
            handler = self.transition_handlers[transition_key]
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(execution_id, from_state, to_state, event, context)
                else:
                    handler(execution_id, from_state, to_state, event, context)
            except Exception:
                return False
        
        return True