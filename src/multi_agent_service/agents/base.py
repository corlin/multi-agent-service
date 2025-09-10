"""Base agent class and interfaces for the multi-agent service."""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from ..models.base import (
    AgentResponse, 
    UserRequest, 
    Action, 
    AgentInfo, 
    CollaborationResult,
    Conflict
)
from ..models.config import AgentConfig
from ..models.enums import AgentStatus, AgentType
from ..services.model_client import BaseModelClient


logger = logging.getLogger(__name__)


class AgentLifecycleInterface(ABC):
    """智能体生命周期管理接口."""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """初始化智能体."""
        pass
    
    @abstractmethod
    async def start(self) -> bool:
        """启动智能体."""
        pass
    
    @abstractmethod
    async def stop(self) -> bool:
        """停止智能体."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> bool:
        """清理智能体资源."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查."""
        pass


class AgentCollaborationInterface(ABC):
    """智能体协作接口."""
    
    @abstractmethod
    async def collaborate(self, other_agents: List['BaseAgent'], context: Dict[str, Any]) -> CollaborationResult:
        """与其他智能体协作."""
        pass
    
    @abstractmethod
    async def handle_conflict(self, conflict: Conflict) -> str:
        """处理冲突."""
        pass
    
    @abstractmethod
    async def share_information(self, information: Dict[str, Any], target_agents: List[str]) -> bool:
        """共享信息给其他智能体."""
        pass
    
    @abstractmethod
    async def receive_information(self, information: Dict[str, Any], source_agent: str) -> bool:
        """接收来自其他智能体的信息."""
        pass


class AgentProcessingInterface(ABC):
    """智能体处理接口."""
    
    @abstractmethod
    async def process_request(self, request: UserRequest) -> AgentResponse:
        """处理用户请求."""
        pass
    
    @abstractmethod
    async def can_handle_request(self, request: UserRequest) -> float:
        """判断是否能处理请求，返回置信度."""
        pass
    
    @abstractmethod
    async def get_capabilities(self) -> List[str]:
        """获取智能体能力列表."""
        pass
    
    @abstractmethod
    async def estimate_processing_time(self, request: UserRequest) -> int:
        """估算处理时间（秒）."""
        pass


class BaseAgent(AgentLifecycleInterface, AgentCollaborationInterface, AgentProcessingInterface):
    """智能体基类，实现核心功能和接口."""
    
    def __init__(self, config: AgentConfig, model_client: BaseModelClient):
        """初始化智能体."""
        self.config = config
        self.model_client = model_client
        self.agent_id = config.agent_id
        self.agent_type = config.agent_type
        self.name = config.name
        self.description = config.description
        
        # 状态管理
        self._status = AgentStatus.OFFLINE
        self._current_load = 0
        self._max_load = config.max_concurrent_tasks
        self._last_active = datetime.now()
        self._active_tasks: Set[str] = set()
        self._shared_memory: Dict[str, Any] = {}
        
        # 性能指标
        self._total_requests = 0
        self._successful_requests = 0
        self._failed_requests = 0
        self._average_response_time = 0.0
        
        # 协作相关
        self._collaboration_partners: Set[str] = set()
        self._pending_collaborations: Dict[str, Dict[str, Any]] = {}
        
        # 日志记录器
        self.logger = logging.getLogger(f"{__name__}.{self.agent_type.value}")
        
    async def initialize(self) -> bool:
        """初始化智能体."""
        try:
            self.logger.info(f"Initializing agent {self.agent_id} ({self.agent_type.value})")
            
            # 验证配置
            if not await self._validate_config():
                self.logger.error(f"Configuration validation failed for agent {self.agent_id}")
                return False
            
            # 初始化模型客户端
            if not await self.model_client.initialize():
                self.logger.error(f"Model client initialization failed for agent {self.agent_id}")
                self._status = AgentStatus.ERROR
                return False
            
            # 执行子类特定的初始化
            if not await self._initialize_specific():
                self.logger.error(f"Specific initialization failed for agent {self.agent_id}")
                return False
            
            self._status = AgentStatus.IDLE
            self.logger.info(f"Agent {self.agent_id} initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing agent {self.agent_id}: {str(e)}")
            self._status = AgentStatus.ERROR
            return False
    
    async def start(self) -> bool:
        """启动智能体."""
        try:
            if self._status == AgentStatus.OFFLINE:
                await self.initialize()
            
            if self._status != AgentStatus.IDLE:
                self.logger.warning(f"Agent {self.agent_id} is not in idle state, current status: {self._status}")
                return False
            
            self.logger.info(f"Starting agent {self.agent_id}")
            
            # 启动健康检查任务
            asyncio.create_task(self._health_check_loop())
            
            # 执行子类特定的启动逻辑
            if not await self._start_specific():
                self.logger.error(f"Specific start failed for agent {self.agent_id}")
                return False
            
            self._status = AgentStatus.IDLE
            self._last_active = datetime.now()
            self.logger.info(f"Agent {self.agent_id} started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting agent {self.agent_id}: {str(e)}")
            self._status = AgentStatus.ERROR
            return False
    
    async def stop(self) -> bool:
        """停止智能体."""
        try:
            self.logger.info(f"Stopping agent {self.agent_id}")
            
            # 等待当前任务完成
            while self._active_tasks:
                self.logger.info(f"Waiting for {len(self._active_tasks)} active tasks to complete")
                await asyncio.sleep(1)
            
            # 执行子类特定的停止逻辑
            await self._stop_specific()
            
            self._status = AgentStatus.OFFLINE
            self.logger.info(f"Agent {self.agent_id} stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping agent {self.agent_id}: {str(e)}")
            return False
    
    async def cleanup(self) -> bool:
        """清理智能体资源."""
        try:
            self.logger.info(f"Cleaning up agent {self.agent_id}")
            
            # 清理共享内存
            self._shared_memory.clear()
            self._collaboration_partners.clear()
            self._pending_collaborations.clear()
            self._active_tasks.clear()
            
            # 清理模型客户端
            if hasattr(self.model_client, 'cleanup'):
                await self.model_client.cleanup()
            
            # 执行子类特定的清理
            await self._cleanup_specific()
            
            self.logger.info(f"Agent {self.agent_id} cleaned up successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cleaning up agent {self.agent_id}: {str(e)}")
            return False
    
    async def health_check(self) -> bool:
        """健康检查."""
        try:
            # 检查基本状态
            if self._status == AgentStatus.ERROR:
                return False
            
            # 检查模型客户端（智能跳过冷却期）
            if hasattr(self.model_client, 'health_check'):
                # 检查是否在冷却期
                if (hasattr(self.model_client, '_last_health_check_failed') and 
                    self.model_client._last_health_check_failed and
                    hasattr(self.model_client, '_health_check_cooldown_until')):
                    import time
                    if time.time() < self.model_client._health_check_cooldown_until:
                        self.logger.debug(f"Agent {self.agent_id} model client in cooldown, skipping health check")
                        return False
                
                # 执行健康检查
                if not await self.model_client.health_check():
                    return False
            
            # 检查负载
            if self._current_load > self._max_load:
                self.logger.warning(f"Agent {self.agent_id} is overloaded: {self._current_load}/{self._max_load}")
                return False
            
            # 执行子类特定的健康检查
            return await self._health_check_specific()
            
        except Exception as e:
            self.logger.error(f"Health check failed for agent {self.agent_id}: {str(e)}")
            return False
    
    async def process_request(self, request: UserRequest) -> AgentResponse:
        """处理用户请求."""
        task_id = str(uuid4())
        start_time = datetime.now()
        
        try:
            # 检查是否可以处理更多请求
            if self._current_load >= self._max_load:
                raise Exception(f"Agent {self.agent_id} is at maximum capacity")
            
            # 更新状态
            self._active_tasks.add(task_id)
            self._current_load += 1
            self._status = AgentStatus.BUSY
            self._last_active = datetime.now()
            
            request_id = getattr(request, 'request_id', request.get('request_id', 'unknown')) if hasattr(request, 'get') or hasattr(request, 'request_id') else 'unknown'
            self.logger.info(f"Processing request {request_id} with task {task_id}")
            
            # 检查是否能处理此请求
            confidence = await self.can_handle_request(request)
            if confidence < 0.1:  # 降低置信度阈值，只有极低置信度才拒绝
                # 提供通用回复而不是抛出异常
                self.logger.warning(f"Agent {self.agent_id} has low confidence ({confidence}) for request, providing general response")
                return AgentResponse(
                    agent_id=self.agent_id,
                    agent_type=self.agent_type,
                    response_content=f"感谢您的咨询。虽然这个问题可能不完全在我的专业领域内，但我会尽力为您提供帮助。如需更专业的服务，建议您联系相应的专业部门。",
                    confidence=confidence,
                    collaboration_needed=True,  # 建议协作
                    metadata={"low_confidence_fallback": True, "original_confidence": confidence}
                )
            
            # 执行具体的请求处理
            response = await self._process_request_specific(request)
            
            # 更新统计信息
            self._total_requests += 1
            self._successful_requests += 1
            
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_average_response_time(processing_time)
            
            self.logger.info(f"Successfully processed request {request_id} in {processing_time:.2f}s")
            return response
            
        except Exception as e:
            request_id = getattr(request, 'request_id', request.get('request_id', 'unknown')) if hasattr(request, 'get') or hasattr(request, 'request_id') else 'unknown'
            self.logger.error(f"Error processing request {request_id}: {str(e)}")
            self._failed_requests += 1
            
            # 返回错误响应
            return AgentResponse(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                response_content=f"处理请求时发生错误: {str(e)}",
                confidence=0.0,
                collaboration_needed=False,
                metadata={"error": str(e), "task_id": task_id}
            )
            
        finally:
            # 清理任务状态
            self._active_tasks.discard(task_id)
            self._current_load = max(0, self._current_load - 1)
            
            # 更新状态
            if self._current_load == 0:
                self._status = AgentStatus.IDLE
    
    async def collaborate(self, other_agents: List['BaseAgent'], context: Dict[str, Any]) -> CollaborationResult:
        """与其他智能体协作."""
        collaboration_id = str(uuid4())
        
        try:
            self.logger.info(f"Starting collaboration {collaboration_id} with {len(other_agents)} agents")
            
            # 记录协作伙伴
            for agent in other_agents:
                self._collaboration_partners.add(agent.agent_id)
            
            # 执行具体的协作逻辑
            result = await self._collaborate_specific(other_agents, context)
            
            self.logger.info(f"Collaboration {collaboration_id} completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in collaboration {collaboration_id}: {str(e)}")
            
            # 返回失败的协作结果
            return CollaborationResult(
                collaboration_id=collaboration_id,
                participating_agents=[agent.agent_id for agent in other_agents] + [self.agent_id],
                final_result=f"协作失败: {str(e)}",
                consensus_reached=False,
                resolution_method="error_fallback"
            )
    
    async def handle_conflict(self, conflict: Conflict) -> str:
        """处理冲突."""
        try:
            self.logger.info(f"Handling conflict {conflict.conflict_id}")
            
            # 执行具体的冲突处理逻辑
            resolution = await self._handle_conflict_specific(conflict)
            
            self.logger.info(f"Conflict {conflict.conflict_id} resolved: {resolution}")
            return resolution
            
        except Exception as e:
            self.logger.error(f"Error handling conflict {conflict.conflict_id}: {str(e)}")
            return f"冲突处理失败: {str(e)}"
    
    async def share_information(self, information: Dict[str, Any], target_agents: List[str]) -> bool:
        """共享信息给其他智能体."""
        try:
            # 将信息存储到共享内存
            info_id = str(uuid4())
            self._shared_memory[info_id] = {
                "data": information,
                "source": self.agent_id,
                "targets": target_agents,
                "timestamp": datetime.now()
            }
            
            self.logger.info(f"Shared information {info_id} to {len(target_agents)} agents")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sharing information: {str(e)}")
            return False
    
    async def receive_information(self, information: Dict[str, Any], source_agent: str) -> bool:
        """接收来自其他智能体的信息."""
        try:
            # 处理接收到的信息
            await self._process_received_information(information, source_agent)
            
            self.logger.info(f"Received information from agent {source_agent}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error receiving information from {source_agent}: {str(e)}")
            return False
    
    def get_status(self) -> AgentInfo:
        """获取智能体状态信息."""
        return AgentInfo(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            name=self.name,
            description=self.description,
            status=self._status,
            capabilities=self.config.capabilities,
            current_load=self._current_load,
            max_load=self._max_load,
            last_active=self._last_active
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标."""
        success_rate = (self._successful_requests / max(1, self._total_requests)) * 100
        
        return {
            "total_requests": self._total_requests,
            "successful_requests": self._successful_requests,
            "failed_requests": self._failed_requests,
            "success_rate": success_rate,
            "average_response_time": self._average_response_time,
            "current_load": self._current_load,
            "max_load": self._max_load,
            "active_tasks": len(self._active_tasks),
            "collaboration_partners": len(self._collaboration_partners)
        }
    
    # 抽象方法，子类必须实现
    @abstractmethod
    async def can_handle_request(self, request: UserRequest) -> float:
        """判断是否能处理请求，返回置信度."""
        pass
    
    @abstractmethod
    async def get_capabilities(self) -> List[str]:
        """获取智能体能力列表."""
        pass
    
    @abstractmethod
    async def estimate_processing_time(self, request: UserRequest) -> int:
        """估算处理时间（秒）."""
        pass
    
    @abstractmethod
    async def _process_request_specific(self, request: UserRequest) -> AgentResponse:
        """子类特定的请求处理逻辑."""
        pass
    
    # 可选的钩子方法，子类可以重写
    async def _validate_config(self) -> bool:
        """验证配置，子类可以重写."""
        return True
    
    async def _initialize_specific(self) -> bool:
        """子类特定的初始化逻辑."""
        return True
    
    async def _start_specific(self) -> bool:
        """子类特定的启动逻辑."""
        return True
    
    async def _stop_specific(self) -> None:
        """子类特定的停止逻辑."""
        pass
    
    async def _cleanup_specific(self) -> None:
        """子类特定的清理逻辑."""
        pass
    
    async def _health_check_specific(self) -> bool:
        """子类特定的健康检查."""
        return True
    
    async def _collaborate_specific(self, other_agents: List['BaseAgent'], context: Dict[str, Any]) -> CollaborationResult:
        """子类特定的协作逻辑."""
        # 默认实现：简单的信息聚合
        responses = []
        try:
            for agent in other_agents:
                if hasattr(agent, '_get_collaboration_input'):
                    response = await agent._get_collaboration_input(context)
                    responses.append(response)
            
            return CollaborationResult(
                collaboration_id=str(uuid4()),
                participating_agents=[agent.agent_id for agent in other_agents] + [self.agent_id],
                final_result="协作完成",
                individual_responses=responses,
                consensus_reached=True,
                resolution_method="default_aggregation"
            )
        except Exception as e:
            # 如果协作过程中出现错误，返回基本的协作结果
            return CollaborationResult(
                collaboration_id=str(uuid4()),
                participating_agents=[getattr(agent, 'agent_id', str(agent)) for agent in other_agents] + [self.agent_id],
                final_result="协作完成（基础模式）",
                individual_responses=responses,
                consensus_reached=True,
                resolution_method="basic_aggregation"
            )
    
    async def _handle_conflict_specific(self, conflict: Conflict) -> str:
        """子类特定的冲突处理逻辑."""
        # 默认实现：选择第一个解决方案
        if conflict.proposed_solutions:
            return conflict.proposed_solutions[0]
        return "无可用解决方案"
    
    async def _process_received_information(self, information: Dict[str, Any], source_agent: str) -> None:
        """处理接收到的信息，子类可以重写."""
        # 默认实现：存储到共享内存
        info_id = str(uuid4())
        self._shared_memory[info_id] = {
            "data": information,
            "source": source_agent,
            "received_at": datetime.now()
        }
    
    # 私有辅助方法
    async def _health_check_loop(self) -> None:
        """健康检查循环."""
        while self._status != AgentStatus.OFFLINE:
            try:
                if not await self.health_check():
                    self._status = AgentStatus.ERROR
                    self.logger.error(f"Health check failed for agent {self.agent_id}")
                
                await asyncio.sleep(30)  # 每30秒检查一次
                
            except Exception as e:
                self.logger.error(f"Error in health check loop for agent {self.agent_id}: {str(e)}")
                await asyncio.sleep(30)
    
    def _update_average_response_time(self, new_time: float) -> None:
        """更新平均响应时间."""
        if self._total_requests == 1:
            self._average_response_time = new_time
        else:
            # 使用指数移动平均
            alpha = 0.1
            self._average_response_time = (1 - alpha) * self._average_response_time + alpha * new_time