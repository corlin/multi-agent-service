"""测试状态管理和消息传递实现."""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from src.multi_agent_service.workflows.state_management import (
    InMemoryStateManager,
    InMemoryMessageBus,
    WorkflowStateManager,
    StateSnapshot,
    SnapshotManager,
    MessageFilter,
    EventEmitter,
    StateTransition
)
from src.multi_agent_service.models.workflow import (
    WorkflowMessage,
    WorkflowExecution,
    NodeExecutionContext
)
from src.multi_agent_service.models.enums import WorkflowStatus


class TestInMemoryStateManager:
    """测试内存状态管理器."""
    
    def test_state_manager_creation(self):
        """测试状态管理器创建."""
        manager = InMemoryStateManager()
        
        assert len(manager.states) == 0
        assert len(manager.state_history) == 0
        assert len(manager.locks) == 0
    
    @pytest.mark.asyncio
    async def test_update_and_get_state(self):
        """测试更新和获取状态."""
        manager = InMemoryStateManager()
        
        # 更新状态
        state_data = {"status": "running", "current_node": "node1"}
        success = await manager.update_state("exec1", state_data)
        
        assert success is True
        
        # 获取状态
        retrieved_state = await manager.get_state("exec1")
        
        assert retrieved_state is not None
        assert retrieved_state["status"] == "running"
        assert retrieved_state["current_node"] == "node1"
        assert "last_updated" in retrieved_state
    
    @pytest.mark.asyncio
    async def test_state_history(self):
        """测试状态历史记录."""
        manager = InMemoryStateManager()
        
        # 第一次更新
        await manager.update_state("exec1", {"status": "pending"})
        
        # 第二次更新
        await manager.update_state("exec1", {"status": "running"})
        
        # 第三次更新
        await manager.update_state("exec1", {"status": "completed"})
        
        # 检查历史记录
        history = await manager.get_state_history("exec1")
        
        assert len(history) == 2  # 前两个状态应该在历史中
        assert history[0]["state"]["status"] == "pending"
        assert history[1]["state"]["status"] == "running"
        
        # 当前状态应该是completed
        current_state = await manager.get_state("exec1")
        assert current_state["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_delete_state(self):
        """测试删除状态."""
        manager = InMemoryStateManager()
        
        # 添加状态
        await manager.update_state("exec1", {"status": "running"})
        
        # 确认状态存在
        state = await manager.get_state("exec1")
        assert state is not None
        
        # 删除状态
        success = await manager.delete_state("exec1")
        assert success is True
        
        # 确认状态已删除
        state = await manager.get_state("exec1")
        assert state is None
    
    @pytest.mark.asyncio
    async def test_concurrent_state_updates(self):
        """测试并发状态更新."""
        manager = InMemoryStateManager()
        
        async def update_state(execution_id: str, value: int):
            for i in range(10):
                await manager.update_state(execution_id, {"counter": value * 10 + i})
                await asyncio.sleep(0.001)
        
        # 并发更新
        tasks = [
            asyncio.create_task(update_state("exec1", 1)),
            asyncio.create_task(update_state("exec1", 2)),
            asyncio.create_task(update_state("exec1", 3))
        ]
        
        await asyncio.gather(*tasks)
        
        # 检查最终状态
        final_state = await manager.get_state("exec1")
        assert final_state is not None
        assert "counter" in final_state
    
    @pytest.mark.asyncio
    async def test_cleanup_old_states(self):
        """测试清理旧状态."""
        manager = InMemoryStateManager()
        
        # 添加一些状态
        old_time = (datetime.now() - timedelta(hours=25)).isoformat()
        recent_time = datetime.now().isoformat()
        
        # 手动设置旧状态
        manager.states["old_exec"] = {"status": "completed", "last_updated": old_time}
        manager.states["recent_exec"] = {"status": "running", "last_updated": recent_time}
        
        # 清理旧状态
        cleaned_count = await manager.cleanup_old_states(max_age_hours=24)
        
        assert cleaned_count == 1
        assert "old_exec" not in manager.states
        assert "recent_exec" in manager.states


class TestInMemoryMessageBus:
    """测试内存消息总线."""
    
    def test_message_bus_creation(self):
        """测试消息总线创建."""
        bus = InMemoryMessageBus()
        
        assert len(bus.message_queues) == 0
        assert len(bus.subscriptions) == 0
        assert len(bus.message_history) == 0
    
    @pytest.mark.asyncio
    async def test_send_and_receive_message(self):
        """测试发送和接收消息."""
        bus = InMemoryMessageBus()
        
        # 创建消息
        message = WorkflowMessage(
            sender_node="node1",
            receiver_node="node2",
            message_type="test_message",
            content={"data": "test"}
        )
        
        # 发送消息
        success = await bus.send_message(message)
        assert success is True
        
        # 接收消息
        received_message = await bus.receive_message("node2")
        
        assert received_message is not None
        assert received_message.sender_node == "node1"
        assert received_message.receiver_node == "node2"
        assert received_message.message_type == "test_message"
        assert received_message.content["data"] == "test"
    
    @pytest.mark.asyncio
    async def test_subscription_and_broadcast(self):
        """测试订阅和广播."""
        bus = InMemoryMessageBus()
        
        # 订阅消息类型
        await bus.subscribe("node1", ["notification", "alert"])
        await bus.subscribe("node2", ["notification"])
        
        # 创建广播消息
        message = WorkflowMessage(
            sender_node="system",
            message_type="notification",
            content={"message": "broadcast test"}
        )
        
        # 发送消息（会广播给订阅者）
        success = await bus.send_message(message)
        assert success is True
        
        # 检查订阅者是否收到消息
        message1 = await bus.receive_message("node1")
        message2 = await bus.receive_message("node2")
        
        assert message1 is not None
        assert message1.message_type == "notification"
        assert message2 is not None
        assert message2.message_type == "notification"
    
    @pytest.mark.asyncio
    async def test_broadcast_to_specific_nodes(self):
        """测试向特定节点广播."""
        bus = InMemoryMessageBus()
        
        message = WorkflowMessage(
            sender_node="system",
            message_type="broadcast",
            content={"announcement": "test"}
        )
        
        target_nodes = ["node1", "node2", "node3"]
        success = await bus.broadcast_message(message, target_nodes)
        
        assert success is True
        
        # 检查所有目标节点都收到消息
        for node_id in target_nodes:
            received_message = await bus.receive_message(node_id)
            assert received_message is not None
            assert received_message.message_type == "broadcast"
    
    @pytest.mark.asyncio
    async def test_message_queue_operations(self):
        """测试消息队列操作."""
        bus = InMemoryMessageBus()
        
        # 发送多条消息
        for i in range(5):
            message = WorkflowMessage(
                sender_node="sender",
                receiver_node="receiver",
                message_type="test",
                content={"index": i}
            )
            await bus.send_message(message)
        
        # 检查队列大小
        queue_size = await bus.get_queue_size("receiver")
        assert queue_size == 5
        
        # 接收一条消息
        message = await bus.receive_message("receiver")
        assert message.content["index"] == 0
        
        # 检查队列大小减少
        queue_size = await bus.get_queue_size("receiver")
        assert queue_size == 4
        
        # 清空队列
        cleared_count = await bus.clear_queue("receiver")
        assert cleared_count == 4
        
        # 检查队列为空
        queue_size = await bus.get_queue_size("receiver")
        assert queue_size == 0
    
    @pytest.mark.asyncio
    async def test_message_history(self):
        """测试消息历史."""
        bus = InMemoryMessageBus()
        
        # 发送多条消息
        for i in range(3):
            message = WorkflowMessage(
                sender_node="sender",
                receiver_node="receiver",
                message_type="test",
                content={"index": i}
            )
            await bus.send_message(message)
        
        # 获取消息历史
        history = await bus.get_message_history(limit=10)
        
        assert len(history) == 3
        assert history[0].content["index"] == 0
        assert history[1].content["index"] == 1
        assert history[2].content["index"] == 2


class TestWorkflowStateManager:
    """测试工作流状态管理器."""
    
    def test_workflow_state_manager_creation(self):
        """测试工作流状态管理器创建."""
        manager = WorkflowStateManager()
        
        assert manager.state_manager is not None
        assert manager.message_bus is not None
        assert len(manager.active_executions) == 0
    
    @pytest.mark.asyncio
    async def test_start_execution(self):
        """测试开始执行."""
        manager = WorkflowStateManager()
        
        execution = WorkflowExecution(
            execution_id="test_exec",
            graph_id="test_graph",
            status=WorkflowStatus.PENDING,
            input_data={"input": "test"}
        )
        
        success = await manager.start_execution(execution)
        
        assert success is True
        assert "test_exec" in manager.active_executions
        
        # 检查状态是否已保存
        state = await manager.get_execution_state("test_exec")
        assert state is not None
        assert state["execution_id"] == "test_exec"
        assert state["status"] == "pending"
    
    @pytest.mark.asyncio
    async def test_update_execution_state(self):
        """测试更新执行状态."""
        manager = WorkflowStateManager()
        
        execution = WorkflowExecution(
            execution_id="test_exec",
            graph_id="test_graph",
            status=WorkflowStatus.PENDING
        )
        
        await manager.start_execution(execution)
        
        # 更新状态
        updates = {
            "status": WorkflowStatus.RUNNING.value,
            "current_node": "node1",
            "node_results": {"node1": {"result": "success"}}
        }
        
        success = await manager.update_execution_state("test_exec", updates)
        
        assert success is True
        
        # 检查内存中的执行对象
        execution = manager.active_executions["test_exec"]
        assert execution.status == WorkflowStatus.RUNNING
        assert execution.current_node == "node1"
        
        # 检查持久化状态
        state = await manager.get_execution_state("test_exec")
        assert state["status"] == "running"
        assert state["current_node"] == "node1"
    
    @pytest.mark.asyncio
    async def test_complete_execution(self):
        """测试完成执行."""
        manager = WorkflowStateManager()
        
        execution = WorkflowExecution(
            execution_id="test_exec",
            graph_id="test_graph",
            status=WorkflowStatus.RUNNING
        )
        
        await manager.start_execution(execution)
        
        # 完成执行
        final_result = {"output": "completed successfully"}
        success = await manager.complete_execution("test_exec", final_result)
        
        assert success is True
        
        # 检查执行已从活跃列表中移除
        assert "test_exec" not in manager.active_executions
        
        # 检查最终状态
        state = await manager.get_execution_state("test_exec")
        assert state["status"] == "completed"
        assert state["output_data"] == final_result
    
    @pytest.mark.asyncio
    async def test_fail_execution(self):
        """测试执行失败."""
        manager = WorkflowStateManager()
        
        execution = WorkflowExecution(
            execution_id="test_exec",
            graph_id="test_graph",
            status=WorkflowStatus.RUNNING
        )
        
        await manager.start_execution(execution)
        
        # 标记执行失败
        error_message = "Execution failed due to error"
        success = await manager.fail_execution("test_exec", error_message)
        
        assert success is True
        
        # 检查执行已从活跃列表中移除
        assert "test_exec" not in manager.active_executions
        
        # 检查失败状态
        state = await manager.get_execution_state("test_exec")
        assert state["status"] == "failed"
        assert state["error_message"] == error_message
    
    @pytest.mark.asyncio
    async def test_node_messaging(self):
        """测试节点间消息传递."""
        manager = WorkflowStateManager()
        
        # 发送节点消息
        success = await manager.send_node_message(
            "node1", "node2", "data_transfer", {"data": "test_data"}
        )
        
        assert success is True
        
        # 接收节点消息
        message = await manager.receive_node_message("node2")
        
        assert message is not None
        assert message.sender_node == "node1"
        assert message.receiver_node == "node2"
        assert message.message_type == "data_transfer"
        assert message.content["data"] == "test_data"
    
    @pytest.mark.asyncio
    async def test_message_subscription(self):
        """测试消息订阅."""
        manager = WorkflowStateManager()
        
        # 订阅消息类型
        success = await manager.subscribe_to_messages("node1", ["notification", "alert"])
        
        assert success is True
        
        # 发送广播消息
        await manager.send_node_message("system", None, "notification", {"message": "test"})
        
        # 检查订阅者是否收到消息
        message = await manager.receive_node_message("node1")
        
        assert message is not None
        assert message.message_type == "notification"


class TestStateSnapshot:
    """测试状态快照."""
    
    def test_snapshot_creation(self):
        """测试快照创建."""
        state_data = {"status": "running", "current_node": "node1"}
        snapshot = StateSnapshot("exec1", state_data)
        
        assert snapshot.execution_id == "exec1"
        assert snapshot.state_data == state_data
        assert snapshot.timestamp is not None
        assert snapshot.snapshot_id.startswith("exec1_")
    
    def test_snapshot_serialization(self):
        """测试快照序列化."""
        state_data = {"status": "running", "current_node": "node1"}
        snapshot = StateSnapshot("exec1", state_data)
        
        # 转换为字典
        snapshot_dict = snapshot.to_dict()
        
        assert snapshot_dict["execution_id"] == "exec1"
        assert snapshot_dict["state_data"] == state_data
        assert "timestamp" in snapshot_dict
        assert "snapshot_id" in snapshot_dict
        
        # 从字典恢复
        restored_snapshot = StateSnapshot.from_dict(snapshot_dict)
        
        assert restored_snapshot.execution_id == snapshot.execution_id
        assert restored_snapshot.state_data == snapshot.state_data
        assert restored_snapshot.snapshot_id == snapshot.snapshot_id


class TestSnapshotManager:
    """测试快照管理器."""
    
    def test_snapshot_manager_creation(self):
        """测试快照管理器创建."""
        manager = SnapshotManager(max_snapshots_per_execution=5)
        
        assert manager.max_snapshots_per_execution == 5
        assert len(manager.snapshots) == 0
    
    @pytest.mark.asyncio
    async def test_create_and_get_snapshot(self):
        """测试创建和获取快照."""
        manager = SnapshotManager()
        
        state_data = {"status": "running", "current_node": "node1"}
        snapshot_id = await manager.create_snapshot("exec1", state_data)
        
        assert snapshot_id is not None
        
        # 获取快照
        snapshot = await manager.get_snapshot(snapshot_id)
        
        assert snapshot is not None
        assert snapshot.execution_id == "exec1"
        assert snapshot.state_data == state_data
    
    @pytest.mark.asyncio
    async def test_latest_snapshot(self):
        """测试获取最新快照."""
        manager = SnapshotManager()
        
        # 创建多个快照
        await manager.create_snapshot("exec1", {"step": 1})
        await asyncio.sleep(0.001)  # 确保时间戳不同
        await manager.create_snapshot("exec1", {"step": 2})
        await asyncio.sleep(0.001)
        latest_id = await manager.create_snapshot("exec1", {"step": 3})
        
        # 获取最新快照
        latest_snapshot = await manager.get_latest_snapshot("exec1")
        
        assert latest_snapshot is not None
        assert latest_snapshot.state_data["step"] == 3
        assert latest_snapshot.snapshot_id == latest_id
    
    @pytest.mark.asyncio
    async def test_snapshot_limit(self):
        """测试快照数量限制."""
        manager = SnapshotManager(max_snapshots_per_execution=3)
        
        # 创建超过限制的快照
        for i in range(5):
            await manager.create_snapshot("exec1", {"step": i})
        
        # 检查快照数量
        snapshots = await manager.list_snapshots("exec1")
        
        assert len(snapshots) == 3
        # 应该保留最新的3个快照
        assert snapshots[0].state_data["step"] == 2
        assert snapshots[1].state_data["step"] == 3
        assert snapshots[2].state_data["step"] == 4
    
    @pytest.mark.asyncio
    async def test_restore_from_snapshot(self):
        """测试从快照恢复."""
        manager = SnapshotManager()
        state_manager = InMemoryStateManager()
        
        # 创建快照
        original_state = {"status": "running", "current_node": "node1"}
        snapshot_id = await manager.create_snapshot("exec1", original_state)
        
        # 修改状态
        await state_manager.update_state("exec1", {"status": "failed"})
        
        # 从快照恢复
        success = await manager.restore_from_snapshot(snapshot_id, state_manager)
        
        assert success is True
        
        # 检查状态已恢复
        restored_state = await state_manager.get_state("exec1")
        assert restored_state["status"] == "running"
        assert restored_state["current_node"] == "node1"


class TestMessageFilter:
    """测试消息过滤器."""
    
    def test_message_filter_creation(self):
        """测试消息过滤器创建."""
        filter_manager = MessageFilter()
        
        assert len(filter_manager.filters) == 0
    
    @pytest.mark.asyncio
    async def test_add_and_apply_filter(self):
        """测试添加和应用过滤器."""
        filter_manager = MessageFilter()
        
        # 添加过滤器：只允许来自特定发送者的消息
        async def sender_filter(message):
            return message.sender_node == "trusted_sender"
        
        filter_manager.add_filter("test_message", sender_filter)
        
        # 测试通过过滤器的消息
        allowed_message = WorkflowMessage(
            sender_node="trusted_sender",
            message_type="test_message",
            content={}
        )
        
        result = await filter_manager.filter_message(allowed_message)
        assert result is True
        
        # 测试被过滤器阻止的消息
        blocked_message = WorkflowMessage(
            sender_node="untrusted_sender",
            message_type="test_message",
            content={}
        )
        
        result = await filter_manager.filter_message(blocked_message)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_multiple_filters(self):
        """测试多个过滤器."""
        filter_manager = MessageFilter()
        
        # 添加多个过滤器
        async def sender_filter(message):
            return message.sender_node.startswith("node_")
        
        async def content_filter(message):
            return "important" in message.content
        
        filter_manager.add_filter("test_message", sender_filter)
        filter_manager.add_filter("test_message", content_filter)
        
        # 测试通过所有过滤器的消息
        valid_message = WorkflowMessage(
            sender_node="node_1",
            message_type="test_message",
            content={"important": True}
        )
        
        result = await filter_manager.filter_message(valid_message)
        assert result is True
        
        # 测试只通过部分过滤器的消息
        partial_message = WorkflowMessage(
            sender_node="node_1",
            message_type="test_message",
            content={"data": "normal"}
        )
        
        result = await filter_manager.filter_message(partial_message)
        assert result is False


class TestEventEmitter:
    """测试事件发射器."""
    
    def test_event_emitter_creation(self):
        """测试事件发射器创建."""
        emitter = EventEmitter()
        
        assert len(emitter.listeners) == 0
    
    @pytest.mark.asyncio
    async def test_event_emission_and_listening(self):
        """测试事件发射和监听."""
        emitter = EventEmitter()
        
        # 记录事件调用
        called_events = []
        
        async def async_listener(data):
            called_events.append(f"async_{data}")
        
        def sync_listener(data):
            called_events.append(f"sync_{data}")
        
        # 添加监听器
        emitter.on("test_event", async_listener)
        emitter.on("test_event", sync_listener)
        
        # 发射事件
        await emitter.emit("test_event", "test_data")
        
        # 检查监听器是否被调用
        assert len(called_events) == 2
        assert "async_test_data" in called_events
        assert "sync_test_data" in called_events
    
    def test_listener_management(self):
        """测试监听器管理."""
        emitter = EventEmitter()
        
        def listener1():
            pass
        
        def listener2():
            pass
        
        # 添加监听器
        emitter.on("test_event", listener1)
        emitter.on("test_event", listener2)
        
        assert emitter.listener_count("test_event") == 2
        
        # 移除监听器
        success = emitter.off("test_event", listener1)
        assert success is True
        assert emitter.listener_count("test_event") == 1
        
        # 尝试移除不存在的监听器
        success = emitter.off("test_event", listener1)
        assert success is False


class TestStateTransition:
    """测试状态转换管理器."""
    
    def test_state_transition_creation(self):
        """测试状态转换管理器创建."""
        transition_manager = StateTransition()
        
        assert len(transition_manager.transitions) == 0
        assert len(transition_manager.transition_handlers) == 0
    
    @pytest.mark.asyncio
    async def test_define_and_check_transitions(self):
        """测试定义和检查状态转换."""
        transition_manager = StateTransition()
        
        # 定义状态机
        state_machine = {
            "pending": {
                "start": ["running"],
                "cancel": ["cancelled"]
            },
            "running": {
                "complete": ["completed"],
                "fail": ["failed"],
                "pause": ["paused"]
            },
            "paused": {
                "resume": ["running"],
                "cancel": ["cancelled"]
            }
        }
        
        transition_manager.define_transitions(state_machine)
        
        # 测试有效转换
        assert await transition_manager.can_transition("pending", "running") is True
        assert await transition_manager.can_transition("running", "completed") is True
        assert await transition_manager.can_transition("paused", "running") is True
        
        # 测试无效转换
        assert await transition_manager.can_transition("pending", "completed") is False
        assert await transition_manager.can_transition("completed", "running") is False
    
    @pytest.mark.asyncio
    async def test_transition_with_handler(self):
        """测试带处理器的状态转换."""
        transition_manager = StateTransition()
        
        # 定义状态机
        state_machine = {
            "pending": {"start": ["running"]},
            "running": {"complete": ["completed"]}
        }
        transition_manager.define_transitions(state_machine)
        
        # 记录转换调用
        transition_calls = []
        
        async def transition_handler(execution_id, from_state, to_state, event, context):
            transition_calls.append({
                "execution_id": execution_id,
                "from_state": from_state,
                "to_state": to_state,
                "event": event,
                "context": context
            })
        
        # 添加转换处理器
        transition_manager.add_transition_handler("pending->running", transition_handler)
        
        # 执行转换
        success = await transition_manager.transition(
            "exec1", "pending", "running", "start", {"user": "test"}
        )
        
        assert success is True
        assert len(transition_calls) == 1
        
        call = transition_calls[0]
        assert call["execution_id"] == "exec1"
        assert call["from_state"] == "pending"
        assert call["to_state"] == "running"
        assert call["event"] == "start"
        assert call["context"]["user"] == "test"


class TestIntegration:
    """集成测试."""
    
    @pytest.mark.asyncio
    async def test_complete_workflow_state_management(self):
        """测试完整的工作流状态管理."""
        # 创建管理器
        state_manager = WorkflowStateManager()
        snapshot_manager = SnapshotManager()
        
        # 创建执行
        execution = WorkflowExecution(
            execution_id="integration_test",
            graph_id="test_graph",
            status=WorkflowStatus.PENDING,
            input_data={"test": "data"}
        )
        
        # 1. 开始执行
        await state_manager.start_execution(execution)
        
        # 2. 创建初始快照
        initial_state = await state_manager.get_execution_state("integration_test")
        snapshot_id = await snapshot_manager.create_snapshot("integration_test", initial_state)
        
        # 3. 更新状态
        await state_manager.update_execution_state("integration_test", {
            "status": WorkflowStatus.RUNNING.value,
            "current_node": "node1"
        })
        
        # 4. 发送节点消息
        await state_manager.send_node_message(
            "node1", "node2", "data_transfer", {"processed_data": "result"}
        )
        
        # 5. 接收消息
        message = await state_manager.receive_node_message("node2")
        assert message is not None
        assert message.content["processed_data"] == "result"
        
        # 6. 完成执行
        await state_manager.complete_execution("integration_test", {"final": "result"})
        
        # 7. 验证最终状态
        final_state = await state_manager.get_execution_state("integration_test")
        assert final_state["status"] == "completed"
        assert final_state["output_data"]["final"] == "result"
        
        # 8. 测试快照恢复
        await snapshot_manager.restore_from_snapshot(snapshot_id, state_manager.state_manager)
        restored_state = await state_manager.get_execution_state("integration_test")
        assert restored_state["status"] == "pending"  # 恢复到初始状态
    
    @pytest.mark.asyncio
    async def test_message_filtering_and_events(self):
        """测试消息过滤和事件处理集成."""
        # 创建组件
        message_bus = InMemoryMessageBus()
        message_filter = MessageFilter()
        event_emitter = EventEmitter()
        
        # 设置消息过滤器
        async def priority_filter(message):
            return message.content.get("priority", "normal") in ["high", "urgent"]
        
        message_filter.add_filter("alert", priority_filter)
        
        # 设置事件监听器
        filtered_messages = []
        
        async def message_listener(message):
            if await message_filter.filter_message(message):
                filtered_messages.append(message)
                await event_emitter.emit("message_processed", message)
        
        processed_events = []
        
        async def event_listener(message):
            processed_events.append(message.message_id)
        
        event_emitter.on("message_processed", event_listener)
        
        # 发送不同优先级的消息
        messages = [
            WorkflowMessage(
                sender_node="system",
                receiver_node="handler",
                message_type="alert",
                content={"priority": "low", "text": "Low priority alert"}
            ),
            WorkflowMessage(
                sender_node="system",
                receiver_node="handler",
                message_type="alert",
                content={"priority": "high", "text": "High priority alert"}
            ),
            WorkflowMessage(
                sender_node="system",
                receiver_node="handler",
                message_type="alert",
                content={"priority": "urgent", "text": "Urgent alert"}
            )
        ]
        
        for message in messages:
            await message_bus.send_message(message)
            received = await message_bus.receive_message("handler")
            if received:
                await message_listener(received)
        
        # 验证过滤结果
        assert len(filtered_messages) == 2  # 只有high和urgent优先级的消息通过
        assert len(processed_events) == 2
        
        # 验证过滤的消息内容
        priorities = [msg.content["priority"] for msg in filtered_messages]
        assert "high" in priorities
        assert "urgent" in priorities
        assert "low" not in priorities