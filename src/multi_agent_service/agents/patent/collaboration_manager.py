"""Patent Agent collaboration and communication management."""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime
from uuid import uuid4
from collections import defaultdict, deque

from ...models.base import AgentResponse, UserRequest, CollaborationResult
from ...models.enums import AgentType, AgentStatus
from ...workflows.state_management import WorkflowStateManager, WorkflowMessage
from ...services.agent_router import AgentRouter


logger = logging.getLogger(__name__)


class PatentAgentMessage:
    """专利Agent间通信消息."""
    
    def __init__(self, sender_id: str, receiver_id: str, message_type: str, 
                 content: Dict[str, Any], priority: int = 1):
        self.message_id = str(uuid4())
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.message_type = message_type
        self.content = content
        self.priority = priority
        self.timestamp = datetime.now()
        self.processed = False
        self.response_required = message_type in ["request", "query", "task_assignment"]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典."""
        return {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "message_type": self.message_type,
            "content": self.content,
            "priority": self.priority,
            "timestamp": self.timestamp.isoformat(),
            "processed": self.processed,
            "response_required": self.response_required
        }


class PatentTaskAssignment:
    """专利任务分配."""
    
    def __init__(self, task_id: str, agent_id: str, task_type: str, 
                 task_data: Dict[str, Any], priority: int = 1):
        self.task_id = task_id
        self.agent_id = agent_id
        self.task_type = task_type
        self.task_data = task_data
        self.priority = priority
        self.status = "assigned"
        self.assigned_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
    
    def start_task(self):
        """开始任务."""
        self.status = "running"
        self.started_at = datetime.now()
    
    def complete_task(self, result: Dict[str, Any]):
        """完成任务."""
        self.status = "completed"
        self.completed_at = datetime.now()
        self.result = result
    
    def fail_task(self, error: str):
        """任务失败."""
        self.status = "failed"
        self.completed_at = datetime.now()
        self.error = error
    
    def get_execution_time(self) -> Optional[float]:
        """获取执行时间（秒）."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class PatentAgentLoadBalancer:
    """专利Agent负载均衡器."""
    
    def __init__(self):
        self.agent_loads: Dict[str, int] = defaultdict(int)
        self.agent_capacities: Dict[str, int] = defaultdict(lambda: 5)  # 默认容量
        self.agent_performance: Dict[str, List[float]] = defaultdict(list)
        self.agent_specialties: Dict[str, List[str]] = {}
    
    def register_agent(self, agent_id: str, capacity: int, specialties: List[str]):
        """注册Agent."""
        self.agent_capacities[agent_id] = capacity
        self.agent_specialties[agent_id] = specialties
        self.agent_loads[agent_id] = 0
    
    def get_best_agent_for_task(self, task_type: str, available_agents: List[str]) -> Optional[str]:
        """为任务选择最佳Agent."""
        if not available_agents:
            return None
        
        # 过滤有能力处理该任务类型的Agent
        capable_agents = []
        for agent_id in available_agents:
            specialties = self.agent_specialties.get(agent_id, [])
            if not specialties or task_type in specialties or "general" in specialties:
                capable_agents.append(agent_id)
        
        if not capable_agents:
            capable_agents = available_agents  # 如果没有专门的Agent，使用所有可用的
        
        # 选择负载最低的Agent
        best_agent = None
        min_load_ratio = float('inf')
        
        for agent_id in capable_agents:
            current_load = self.agent_loads[agent_id]
            capacity = self.agent_capacities[agent_id]
            
            if current_load < capacity:
                load_ratio = current_load / capacity
                
                # 考虑性能历史
                performance_bonus = 0
                if agent_id in self.agent_performance:
                    avg_performance = sum(self.agent_performance[agent_id]) / len(self.agent_performance[agent_id])
                    performance_bonus = (1.0 - avg_performance) * 0.1  # 性能好的Agent获得优势
                
                adjusted_load_ratio = load_ratio - performance_bonus
                
                if adjusted_load_ratio < min_load_ratio:
                    min_load_ratio = adjusted_load_ratio
                    best_agent = agent_id
        
        return best_agent
    
    def assign_task_to_agent(self, agent_id: str, task_id: str):
        """分配任务给Agent."""
        self.agent_loads[agent_id] += 1
    
    def complete_task_for_agent(self, agent_id: str, task_id: str, execution_time: float, success: bool):
        """Agent完成任务."""
        self.agent_loads[agent_id] = max(0, self.agent_loads[agent_id] - 1)
        
        # 记录性能
        performance_score = 1.0 if success else 0.0
        if execution_time > 0:
            # 基于执行时间调整性能分数（假设30秒是理想时间）
            time_factor = min(30.0 / execution_time, 1.0)
            performance_score *= time_factor
        
        self.agent_performance[agent_id].append(performance_score)
        
        # 保持性能历史在合理范围内
        if len(self.agent_performance[agent_id]) > 100:
            self.agent_performance[agent_id].pop(0)
    
    def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """获取Agent状态."""
        return {
            "agent_id": agent_id,
            "current_load": self.agent_loads[agent_id],
            "capacity": self.agent_capacities[agent_id],
            "load_ratio": self.agent_loads[agent_id] / self.agent_capacities[agent_id],
            "specialties": self.agent_specialties.get(agent_id, []),
            "avg_performance": (
                sum(self.agent_performance[agent_id]) / len(self.agent_performance[agent_id])
                if self.agent_performance[agent_id] else 0.0
            )
        }


class PatentCollaborationManager:
    """专利Agent协作管理器."""
    
    def __init__(self, state_manager: Optional[WorkflowStateManager] = None,
                 agent_router: Optional[AgentRouter] = None):
        self.state_manager = state_manager or WorkflowStateManager()
        self.agent_router = agent_router
        self.load_balancer = PatentAgentLoadBalancer()
        
        # 消息队列和路由
        self.message_queues: Dict[str, deque] = defaultdict(deque)
        self.message_subscriptions: Dict[str, Set[str]] = defaultdict(set)
        self.message_history: List[PatentAgentMessage] = []
        
        # 任务管理
        self.active_tasks: Dict[str, PatentTaskAssignment] = {}
        self.task_dependencies: Dict[str, List[str]] = {}
        self.completed_tasks: Dict[str, PatentTaskAssignment] = {}
        
        # Agent注册和状态
        self.registered_agents: Dict[str, Dict[str, Any]] = {}
        self.agent_heartbeats: Dict[str, datetime] = {}
        
        # 协作会话
        self.active_collaborations: Dict[str, Dict[str, Any]] = {}
        
        # 性能监控
        self.collaboration_metrics: Dict[str, Any] = {
            "total_messages": 0,
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "avg_task_time": 0.0
        }
        
        # 初始化专利Agent
        self._initialize_patent_agents()
    
    def _initialize_patent_agents(self):
        """初始化专利Agent配置."""
        patent_agents = {
            "patent_data_collection_agent": {
                "capacity": 3,
                "specialties": ["data_collection", "api_integration", "data_cleaning"]
            },
            "patent_search_agent": {
                "capacity": 5,
                "specialties": ["search", "cnki_search", "bocha_ai_search", "web_crawling"]
            },
            "patent_analysis_agent": {
                "capacity": 2,
                "specialties": ["analysis", "trend_analysis", "competition_analysis", "classification"]
            },
            "patent_report_agent": {
                "capacity": 2,
                "specialties": ["report_generation", "visualization", "document_creation"]
            }
        }
        
        for agent_id, config in patent_agents.items():
            self.load_balancer.register_agent(
                agent_id, 
                config["capacity"], 
                config["specialties"]
            )
    
    async def register_agent(self, agent_id: str, agent_info: Dict[str, Any]) -> bool:
        """注册Agent."""
        try:
            self.registered_agents[agent_id] = {
                "agent_id": agent_id,
                "agent_type": agent_info.get("agent_type"),
                "capabilities": agent_info.get("capabilities", []),
                "status": "online",
                "registered_at": datetime.now(),
                "last_heartbeat": datetime.now()
            }
            
            self.agent_heartbeats[agent_id] = datetime.now()
            
            # 订阅通用消息类型
            await self.subscribe_agent_to_messages(agent_id, [
                "task_assignment", "collaboration_request", "status_update", "broadcast"
            ])
            
            logger.info(f"Agent {agent_id} registered successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register agent {agent_id}: {str(e)}")
            return False
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """注销Agent."""
        try:
            if agent_id in self.registered_agents:
                self.registered_agents[agent_id]["status"] = "offline"
                
                # 重新分配该Agent的活跃任务
                await self._reassign_agent_tasks(agent_id)
                
                logger.info(f"Agent {agent_id} unregistered")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to unregister agent {agent_id}: {str(e)}")
            return False
    
    async def send_message(self, message: PatentAgentMessage) -> bool:
        """发送消息."""
        try:
            # 记录消息
            self.message_history.append(message)
            self.collaboration_metrics["total_messages"] += 1
            
            # 投递消息
            if message.receiver_id == "broadcast":
                # 广播消息
                for agent_id in self.registered_agents:
                    if agent_id != message.sender_id:
                        self.message_queues[agent_id].append(message)
            else:
                # 单播消息
                self.message_queues[message.receiver_id].append(message)
            
            # 通过状态管理器发送
            workflow_message = WorkflowMessage(
                sender_node=message.sender_id,
                receiver_node=message.receiver_id,
                message_type=message.message_type,
                content=message.content
            )
            
            await self.state_manager.message_bus.send_message(workflow_message)
            
            logger.debug(f"Message sent from {message.sender_id} to {message.receiver_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")
            return False
    
    async def receive_message(self, agent_id: str) -> Optional[PatentAgentMessage]:
        """接收消息."""
        try:
            queue = self.message_queues[agent_id]
            if queue:
                message = queue.popleft()
                message.processed = True
                return message
            return None
            
        except Exception as e:
            logger.error(f"Failed to receive message for agent {agent_id}: {str(e)}")
            return None
    
    async def assign_task(self, task_type: str, task_data: Dict[str, Any], 
                         preferred_agent: Optional[str] = None, 
                         priority: int = 1) -> Optional[str]:
        """分配任务."""
        try:
            task_id = str(uuid4())
            
            # 选择Agent
            if preferred_agent and preferred_agent in self.registered_agents:
                selected_agent = preferred_agent
            else:
                available_agents = [
                    agent_id for agent_id, info in self.registered_agents.items()
                    if info["status"] == "online"
                ]
                selected_agent = self.load_balancer.get_best_agent_for_task(task_type, available_agents)
            
            if not selected_agent:
                logger.warning(f"No available agent for task type: {task_type}")
                return None
            
            # 创建任务分配
            task_assignment = PatentTaskAssignment(
                task_id=task_id,
                agent_id=selected_agent,
                task_type=task_type,
                task_data=task_data,
                priority=priority
            )
            
            self.active_tasks[task_id] = task_assignment
            self.load_balancer.assign_task_to_agent(selected_agent, task_id)
            
            # 发送任务分配消息
            message = PatentAgentMessage(
                sender_id="collaboration_manager",
                receiver_id=selected_agent,
                message_type="task_assignment",
                content={
                    "task_id": task_id,
                    "task_type": task_type,
                    "task_data": task_data,
                    "priority": priority
                },
                priority=priority
            )
            
            await self.send_message(message)
            
            self.collaboration_metrics["total_tasks"] += 1
            logger.info(f"Task {task_id} assigned to agent {selected_agent}")
            
            return task_id
            
        except Exception as e:
            logger.error(f"Failed to assign task: {str(e)}")
            return None
    
    async def complete_task(self, task_id: str, result: Dict[str, Any], 
                          agent_id: str) -> bool:
        """完成任务."""
        try:
            if task_id not in self.active_tasks:
                logger.warning(f"Task {task_id} not found in active tasks")
                return False
            
            task = self.active_tasks[task_id]
            
            if task.agent_id != agent_id:
                logger.warning(f"Agent {agent_id} is not assigned to task {task_id}")
                return False
            
            # 完成任务
            task.complete_task(result)
            
            # 更新负载均衡器
            execution_time = task.get_execution_time() or 0
            self.load_balancer.complete_task_for_agent(agent_id, task_id, execution_time, True)
            
            # 移动到已完成任务
            self.completed_tasks[task_id] = task
            del self.active_tasks[task_id]
            
            # 更新指标
            self.collaboration_metrics["successful_tasks"] += 1
            self._update_avg_task_time(execution_time)
            
            # 检查依赖任务
            await self._check_task_dependencies(task_id)
            
            logger.info(f"Task {task_id} completed by agent {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to complete task {task_id}: {str(e)}")
            return False
    
    async def fail_task(self, task_id: str, error: str, agent_id: str) -> bool:
        """任务失败."""
        try:
            if task_id not in self.active_tasks:
                return False
            
            task = self.active_tasks[task_id]
            
            if task.agent_id != agent_id:
                return False
            
            # 标记任务失败
            task.fail_task(error)
            
            # 更新负载均衡器
            execution_time = task.get_execution_time() or 0
            self.load_balancer.complete_task_for_agent(agent_id, task_id, execution_time, False)
            
            # 移动到已完成任务
            self.completed_tasks[task_id] = task
            del self.active_tasks[task_id]
            
            # 更新指标
            self.collaboration_metrics["failed_tasks"] += 1
            
            # 尝试重新分配任务
            await self._retry_failed_task(task)
            
            logger.warning(f"Task {task_id} failed for agent {agent_id}: {error}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to handle task failure {task_id}: {str(e)}")
            return False
    
    async def start_collaboration(self, collaboration_type: str, participants: List[str],
                                context: Dict[str, Any]) -> str:
        """开始协作会话."""
        collaboration_id = str(uuid4())
        
        collaboration = {
            "collaboration_id": collaboration_id,
            "collaboration_type": collaboration_type,
            "participants": participants,
            "context": context,
            "status": "active",
            "start_time": datetime.now(),
            "messages": [],
            "shared_data": {}
        }
        
        self.active_collaborations[collaboration_id] = collaboration
        
        # 通知所有参与者
        for participant in participants:
            message = PatentAgentMessage(
                sender_id="collaboration_manager",
                receiver_id=participant,
                message_type="collaboration_start",
                content={
                    "collaboration_id": collaboration_id,
                    "collaboration_type": collaboration_type,
                    "participants": participants,
                    "context": context
                }
            )
            await self.send_message(message)
        
        logger.info(f"Collaboration {collaboration_id} started with participants: {participants}")
        return collaboration_id
    
    async def end_collaboration(self, collaboration_id: str, result: Dict[str, Any]) -> bool:
        """结束协作会话."""
        if collaboration_id not in self.active_collaborations:
            return False
        
        collaboration = self.active_collaborations[collaboration_id]
        collaboration["status"] = "completed"
        collaboration["end_time"] = datetime.now()
        collaboration["result"] = result
        
        # 通知所有参与者
        for participant in collaboration["participants"]:
            message = PatentAgentMessage(
                sender_id="collaboration_manager",
                receiver_id=participant,
                message_type="collaboration_end",
                content={
                    "collaboration_id": collaboration_id,
                    "result": result
                }
            )
            await self.send_message(message)
        
        del self.active_collaborations[collaboration_id]
        
        logger.info(f"Collaboration {collaboration_id} ended")
        return True
    
    async def share_data(self, sender_id: str, data_type: str, data: Dict[str, Any],
                        recipients: Optional[List[str]] = None) -> bool:
        """共享数据."""
        try:
            if recipients is None:
                recipients = list(self.registered_agents.keys())
            
            for recipient in recipients:
                if recipient != sender_id and recipient in self.registered_agents:
                    message = PatentAgentMessage(
                        sender_id=sender_id,
                        receiver_id=recipient,
                        message_type="data_share",
                        content={
                            "data_type": data_type,
                            "data": data,
                            "shared_at": datetime.now().isoformat()
                        }
                    )
                    await self.send_message(message)
            
            logger.info(f"Data shared by {sender_id} to {len(recipients)} agents")
            return True
            
        except Exception as e:
            logger.error(f"Failed to share data: {str(e)}")
            return False
    
    async def subscribe_agent_to_messages(self, agent_id: str, message_types: List[str]) -> bool:
        """订阅消息类型."""
        try:
            for message_type in message_types:
                self.message_subscriptions[message_type].add(agent_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to subscribe agent {agent_id}: {str(e)}")
            return False
    
    async def heartbeat(self, agent_id: str) -> bool:
        """Agent心跳."""
        if agent_id in self.registered_agents:
            self.agent_heartbeats[agent_id] = datetime.now()
            self.registered_agents[agent_id]["last_heartbeat"] = datetime.now()
            return True
        return False
    
    async def _reassign_agent_tasks(self, agent_id: str):
        """重新分配Agent的任务."""
        tasks_to_reassign = [
            task for task in self.active_tasks.values()
            if task.agent_id == agent_id and task.status in ["assigned", "running"]
        ]
        
        for task in tasks_to_reassign:
            # 取消原任务
            del self.active_tasks[task.task_id]
            
            # 重新分配
            new_task_id = await self.assign_task(
                task.task_type,
                task.task_data,
                priority=task.priority
            )
            
            if new_task_id:
                logger.info(f"Task {task.task_id} reassigned as {new_task_id}")
            else:
                logger.warning(f"Failed to reassign task {task.task_id}")
    
    async def _retry_failed_task(self, failed_task: PatentTaskAssignment):
        """重试失败的任务."""
        # 简单的重试策略：如果是临时错误，重新分配
        if "timeout" in failed_task.error.lower() or "network" in failed_task.error.lower():
            new_task_id = await self.assign_task(
                failed_task.task_type,
                failed_task.task_data,
                priority=failed_task.priority + 1  # 提高优先级
            )
            
            if new_task_id:
                logger.info(f"Failed task {failed_task.task_id} retried as {new_task_id}")
    
    async def _check_task_dependencies(self, completed_task_id: str):
        """检查任务依赖."""
        # 检查是否有任务依赖于刚完成的任务
        dependent_tasks = self.task_dependencies.get(completed_task_id, [])
        
        for dependent_task_id in dependent_tasks:
            if dependent_task_id in self.active_tasks:
                task = self.active_tasks[dependent_task_id]
                if task.status == "waiting_for_dependency":
                    # 启动依赖任务
                    message = PatentAgentMessage(
                        sender_id="collaboration_manager",
                        receiver_id=task.agent_id,
                        message_type="dependency_resolved",
                        content={
                            "task_id": dependent_task_id,
                            "dependency_result": self.completed_tasks[completed_task_id].result
                        }
                    )
                    await self.send_message(message)
    
    def _update_avg_task_time(self, execution_time: float):
        """更新平均任务时间."""
        current_avg = self.collaboration_metrics["avg_task_time"]
        total_successful = self.collaboration_metrics["successful_tasks"]
        
        if total_successful == 1:
            self.collaboration_metrics["avg_task_time"] = execution_time
        else:
            # 计算移动平均
            self.collaboration_metrics["avg_task_time"] = (
                (current_avg * (total_successful - 1) + execution_time) / total_successful
            )
    
    # 监控和统计方法
    def get_collaboration_statistics(self) -> Dict[str, Any]:
        """获取协作统计信息."""
        return {
            **self.collaboration_metrics,
            "active_agents": len([
                agent for agent in self.registered_agents.values()
                if agent["status"] == "online"
            ]),
            "active_tasks": len(self.active_tasks),
            "active_collaborations": len(self.active_collaborations),
            "message_queue_sizes": {
                agent_id: len(queue) for agent_id, queue in self.message_queues.items()
            }
        }
    
    def get_agent_performance(self, agent_id: str) -> Dict[str, Any]:
        """获取Agent性能统计."""
        if agent_id not in self.registered_agents:
            return {}
        
        load_status = self.load_balancer.get_agent_status(agent_id)
        
        # 计算任务统计
        completed_tasks = [
            task for task in self.completed_tasks.values()
            if task.agent_id == agent_id
        ]
        
        successful_tasks = [task for task in completed_tasks if task.status == "completed"]
        failed_tasks = [task for task in completed_tasks if task.status == "failed"]
        
        return {
            **load_status,
            "total_completed_tasks": len(completed_tasks),
            "successful_tasks": len(successful_tasks),
            "failed_tasks": len(failed_tasks),
            "success_rate": len(successful_tasks) / len(completed_tasks) if completed_tasks else 0,
            "avg_execution_time": (
                sum(task.get_execution_time() or 0 for task in successful_tasks) / len(successful_tasks)
                if successful_tasks else 0
            )
        }
    
    async def cleanup_inactive_agents(self, timeout_minutes: int = 5):
        """清理不活跃的Agent."""
        cutoff_time = datetime.now().timestamp() - (timeout_minutes * 60)
        
        inactive_agents = []
        for agent_id, last_heartbeat in self.agent_heartbeats.items():
            if last_heartbeat.timestamp() < cutoff_time:
                inactive_agents.append(agent_id)
        
        for agent_id in inactive_agents:
            await self.unregister_agent(agent_id)
            logger.info(f"Cleaned up inactive agent: {agent_id}")
        
        return len(inactive_agents)