"""Coordinator agent implementation for hierarchical multi-agent collaboration."""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from uuid import uuid4

from .base import BaseAgent
from ..models.base import UserRequest, AgentResponse, Action, CollaborationResult, Conflict
from ..models.config import AgentConfig
from ..models.enums import AgentType
from ..services.model_client import BaseModelClient


class CoordinatorAgent(BaseAgent):
    """智能体协调员，负责管理和协调其他智能体的协作."""
    
    def __init__(self, config: AgentConfig, model_client: BaseModelClient):
        """初始化协调员智能体."""
        super().__init__(config, model_client)
        
        # 协调相关的关键词
        self.coordination_keywords = [
            "协调", "统筹", "管理", "分配", "调度", "安排", "组织", "整合",
            "多个", "团队", "协作", "配合", "合作", "联合", "综合", "全面",
            "coordinate", "manage", "organize", "integrate", "collaborate",
            "multiple", "team", "cooperation", "comprehensive"
        ]
        
        # 任务分解策略
        self.decomposition_strategies = {
            "sequential": "按顺序依次执行各个子任务",
            "parallel": "同时并行处理多个独立任务",
            "hierarchical": "分层分级处理复杂任务",
            "hybrid": "混合使用多种策略"
        }
        
        # 智能体能力映射
        self.agent_capabilities = {
            AgentType.SALES: ["销售咨询", "产品介绍", "价格报价", "客户关系"],
            AgentType.CUSTOMER_SUPPORT: ["问题诊断", "故障排除", "客户服务", "投诉处理"],
            AgentType.MANAGER: ["战略规划", "决策分析", "资源管理", "团队管理"],
            AgentType.FIELD_SERVICE: ["现场服务", "设备维修", "技术支持", "安装调试"]
        }
        
        # 协作模式
        self.collaboration_modes = {
            "consultation": "咨询模式 - 收集各方意见",
            "delegation": "委派模式 - 分配具体任务",
            "consensus": "共识模式 - 达成一致意见",
            "arbitration": "仲裁模式 - 解决冲突争议"
        }
        
        # 冲突解决策略
        self.conflict_resolution_strategies = {
            "priority_based": "基于优先级的决策",
            "expertise_based": "基于专业性的决策",
            "consensus_building": "建立共识的协商",
            "escalation": "升级到更高层级"
        }
        
        # 协调状态跟踪
        self.active_collaborations: Dict[str, Dict[str, Any]] = {}
        self.task_assignments: Dict[str, List[str]] = {}
        self.agent_workloads: Dict[str, int] = {}
    
    async def can_handle_request(self, request: UserRequest) -> float:
        """判断是否需要协调员处理的复杂请求."""
        content = request.content.lower()
        
        # 检查协调关键词
        keyword_matches = sum(1 for keyword in self.coordination_keywords if keyword in content)
        keyword_score = min(keyword_matches * 0.2, 0.6)
        
        # 检查复杂性指标
        complexity_indicators = [
            "多个", "全面", "整体", "综合", "协调", "统筹",
            "multiple", "comprehensive", "overall", "coordinate"
        ]
        complexity_score = 0.3 if any(indicator in content for indicator in complexity_indicators) else 0
        
        # 检查跨领域需求
        domain_count = 0
        domains = ["销售", "客服", "管理", "技术", "现场"]
        for domain in domains:
            if domain in content:
                domain_count += 1
        
        cross_domain_score = min(domain_count * 0.2, 0.4) if domain_count > 1 else 0
        
        # 检查协作意图
        collaboration_patterns = [
            r"需要.*?(多个|各个|所有).*?(部门|团队|人员)",
            r"(协调|统筹|安排).*?(各方|多方)",
            r"(整合|综合).*?(资源|信息|方案)",
            r"(全面|整体).*?(解决|处理|分析)"
        ]
        
        import re
        pattern_score = 0
        for pattern in collaboration_patterns:
            if re.search(pattern, content):
                pattern_score += 0.2
        
        total_score = min(keyword_score + complexity_score + cross_domain_score + pattern_score, 1.0)
        
        return max(total_score, 0.0)
    
    async def get_capabilities(self) -> List[str]:
        """获取协调员的能力列表."""
        return [
            "任务分解",
            "智能体调度",
            "协作管理",
            "冲突解决",
            "资源协调",
            "进度监控",
            "结果整合",
            "决策仲裁"
        ]
    
    async def estimate_processing_time(self, request: UserRequest) -> int:
        """估算处理时间（协调任务通常需要更长时间）."""
        content = request.content.lower()
        
        # 简单协调：30-45秒
        if any(word in content for word in ["简单", "基本", "一般"]):
            return 35
        
        # 复杂协调：60-90秒
        if any(word in content for word in ["复杂", "全面", "整体"]):
            return 75
        
        # 跨部门协调：45-60秒
        domain_count = sum(1 for domain in ["销售", "客服", "管理", "技术"] if domain in content)
        if domain_count > 1:
            return 50
        
        # 默认处理时间
        return 40
    
    async def _process_request_specific(self, request: UserRequest) -> AgentResponse:
        """处理需要协调的复杂请求."""
        content = request.content
        
        # 分析任务复杂度和所需智能体
        task_analysis = await self._analyze_task_complexity(content)
        required_agents = await self._identify_required_agents(content)
        
        # 制定协作策略
        collaboration_strategy = self._determine_collaboration_strategy(task_analysis, required_agents)
        
        # 执行任务协调
        coordination_result = await self._coordinate_task_execution(
            request, required_agents, collaboration_strategy
        )
        
        # 生成协调响应
        response_content = await self._generate_coordination_response(
            coordination_result, collaboration_strategy
        )
        
        # 生成后续动作
        next_actions = self._generate_coordination_actions(
            coordination_result, required_agents
        )
        
        return AgentResponse(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            response_content=response_content,
            confidence=0.9,
            next_actions=next_actions,
            collaboration_needed=False,  # 协调员本身不需要进一步协作
            metadata={
                "coordination_strategy": collaboration_strategy,
                "required_agents": [agent.value for agent in required_agents],
                "task_complexity": task_analysis,
                "coordination_id": coordination_result.collaboration_id,
                "processed_at": datetime.now().isoformat()
            }
        )
    
    async def _analyze_task_complexity(self, content: str) -> Dict[str, Any]:
        """分析任务复杂度."""
        content_lower = content.lower()
        
        # 复杂度指标
        complexity_factors = {
            "cross_domain": len([d for d in ["销售", "客服", "管理", "技术"] if d in content_lower]),
            "urgency": 1 if any(word in content_lower for word in ["紧急", "立即", "马上"]) else 0,
            "scope": 1 if any(word in content_lower for word in ["全面", "整体", "综合"]) else 0,
            "stakeholders": len([s for s in ["客户", "用户", "管理层", "团队"] if s in content_lower])
        }
        
        # 计算总体复杂度
        total_complexity = sum(complexity_factors.values())
        
        if total_complexity >= 4:
            complexity_level = "high"
        elif total_complexity >= 2:
            complexity_level = "medium"
        else:
            complexity_level = "low"
        
        return {
            "level": complexity_level,
            "factors": complexity_factors,
            "score": total_complexity
        }
    
    async def _identify_required_agents(self, content: str) -> List[AgentType]:
        """识别需要参与的智能体类型."""
        content_lower = content.lower()
        required_agents = []
        
        # 销售相关
        if any(word in content_lower for word in ["销售", "价格", "产品", "客户关系", "报价"]):
            required_agents.append(AgentType.SALES)
        
        # 客服相关
        if any(word in content_lower for word in ["问题", "故障", "支持", "投诉", "服务"]):
            required_agents.append(AgentType.CUSTOMER_SUPPORT)
        
        # 管理相关
        if any(word in content_lower for word in ["决策", "战略", "管理", "规划", "资源"]):
            required_agents.append(AgentType.MANAGER)
        
        # 现场服务相关
        if any(word in content_lower for word in ["现场", "维修", "安装", "技术", "设备"]):
            required_agents.append(AgentType.FIELD_SERVICE)
        
        # 如果没有明确指向，根据复杂度添加相关智能体
        if not required_agents:
            required_agents = [AgentType.SALES, AgentType.CUSTOMER_SUPPORT]  # 默认组合
        
        return list(set(required_agents))  # 去重
    
    def _determine_collaboration_strategy(self, task_analysis: Dict[str, Any], 
                                        required_agents: List[AgentType]) -> str:
        """确定协作策略."""
        complexity_level = task_analysis["level"]
        agent_count = len(required_agents)
        
        if complexity_level == "high" or agent_count > 2:
            return "hierarchical"
        elif agent_count > 1:
            return "parallel"
        else:
            return "sequential"
    
    async def _coordinate_task_execution(self, request: UserRequest, 
                                       required_agents: List[AgentType],
                                       strategy: str) -> CollaborationResult:
        """协调任务执行."""
        collaboration_id = str(uuid4())
        
        # 记录协作开始
        self.active_collaborations[collaboration_id] = {
            "request": request,
            "agents": required_agents,
            "strategy": strategy,
            "start_time": datetime.now(),
            "status": "in_progress"
        }
        
        try:
            if strategy == "sequential":
                result = await self._execute_sequential_collaboration(
                    collaboration_id, request, required_agents
                )
            elif strategy == "parallel":
                result = await self._execute_parallel_collaboration(
                    collaboration_id, request, required_agents
                )
            elif strategy == "hierarchical":
                result = await self._execute_hierarchical_collaboration(
                    collaboration_id, request, required_agents
                )
            else:
                result = await self._execute_default_collaboration(
                    collaboration_id, request, required_agents
                )
            
            # 更新协作状态
            self.active_collaborations[collaboration_id]["status"] = "completed"
            self.active_collaborations[collaboration_id]["end_time"] = datetime.now()
            
            return result
            
        except Exception as e:
            self.logger.error(f"Collaboration {collaboration_id} failed: {str(e)}")
            
            # 返回失败结果
            return CollaborationResult(
                collaboration_id=collaboration_id,
                participating_agents=[agent.value for agent in required_agents] + [self.agent_id],
                final_result=f"协作执行失败: {str(e)}",
                consensus_reached=False,
                resolution_method="error_handling"
            )
    
    async def _execute_sequential_collaboration(self, collaboration_id: str,
                                             request: UserRequest,
                                             required_agents: List[AgentType]) -> CollaborationResult:
        """执行顺序协作."""
        responses = []
        accumulated_context = request.context.copy()
        
        for agent_type in required_agents:
            # 创建带有累积上下文的请求
            agent_request = UserRequest(
                content=request.content,
                user_id=request.user_id,
                context=accumulated_context,
                priority=request.priority
            )
            
            # 模拟智能体响应（实际实现中会调用真实智能体）
            response = await self._simulate_agent_response(agent_type, agent_request)
            responses.append(response)
            
            # 更新累积上下文
            accumulated_context[f"{agent_type.value}_response"] = response.response_content
        
        # 整合所有响应
        final_result = self._integrate_sequential_responses(responses)
        
        return CollaborationResult(
            collaboration_id=collaboration_id,
            participating_agents=[agent.value for agent in required_agents] + [self.agent_id],
            final_result=final_result,
            individual_responses=responses,
            consensus_reached=True,
            resolution_method="sequential_integration"
        )
    
    async def _execute_parallel_collaboration(self, collaboration_id: str,
                                            request: UserRequest,
                                            required_agents: List[AgentType]) -> CollaborationResult:
        """执行并行协作."""
        # 创建并行任务
        tasks = []
        for agent_type in required_agents:
            task = self._simulate_agent_response(agent_type, request)
            tasks.append(task)
        
        # 等待所有任务完成
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 过滤异常响应
        valid_responses = [r for r in responses if isinstance(r, AgentResponse)]
        
        # 整合并行响应
        final_result = self._integrate_parallel_responses(valid_responses)
        
        return CollaborationResult(
            collaboration_id=collaboration_id,
            participating_agents=[agent.value for agent in required_agents] + [self.agent_id],
            final_result=final_result,
            individual_responses=valid_responses,
            consensus_reached=len(valid_responses) == len(required_agents),
            resolution_method="parallel_integration"
        )
    
    async def _execute_hierarchical_collaboration(self, collaboration_id: str,
                                                request: UserRequest,
                                                required_agents: List[AgentType]) -> CollaborationResult:
        """执行分层协作."""
        # 第一层：收集各智能体的初步响应
        initial_responses = []
        for agent_type in required_agents:
            response = await self._simulate_agent_response(agent_type, request)
            initial_responses.append(response)
        
        # 第二层：分析响应并识别冲突
        conflicts = self._identify_conflicts(initial_responses)
        
        # 第三层：解决冲突并形成最终决策
        if conflicts:
            resolution = await self._resolve_conflicts(conflicts, initial_responses)
            final_result = f"经过协调解决冲突后的综合方案：\n{resolution}"
            consensus_reached = True
        else:
            final_result = self._integrate_hierarchical_responses(initial_responses)
            consensus_reached = True
        
        return CollaborationResult(
            collaboration_id=collaboration_id,
            participating_agents=[agent.value for agent in required_agents] + [self.agent_id],
            final_result=final_result,
            individual_responses=initial_responses,
            consensus_reached=consensus_reached,
            resolution_method="hierarchical_coordination"
        )
    
    async def _execute_default_collaboration(self, collaboration_id: str,
                                           request: UserRequest,
                                           required_agents: List[AgentType]) -> CollaborationResult:
        """执行默认协作模式."""
        # 简单的并行处理
        return await self._execute_parallel_collaboration(collaboration_id, request, required_agents)
    
    async def _simulate_agent_response(self, agent_type: AgentType, request: UserRequest) -> AgentResponse:
        """模拟智能体响应（在实际实现中会调用真实智能体）."""
        # 这里是模拟实现，实际中会调用对应的智能体
        capabilities = self.agent_capabilities.get(agent_type, ["通用处理"])
        
        response_content = f"来自{agent_type.value}智能体的响应：\n"
        response_content += f"基于我的专业能力（{', '.join(capabilities)}），"
        response_content += f"针对您的请求'{request.content[:50]}...'，我的建议是..."
        
        return AgentResponse(
            agent_id=f"{agent_type.value}-001",
            agent_type=agent_type,
            response_content=response_content,
            confidence=0.8,
            collaboration_needed=False,
            metadata={"simulated": True}
        )
    
    def _integrate_sequential_responses(self, responses: List[AgentResponse]) -> str:
        """整合顺序响应."""
        result = "基于各智能体的顺序协作，综合方案如下：\n\n"
        
        for i, response in enumerate(responses, 1):
            result += f"**阶段 {i} - {response.agent_type.value}智能体：**\n"
            result += f"{response.response_content}\n\n"
        
        result += "**协调员总结：**\n"
        result += "各阶段建议已整合，请按照上述顺序执行相关措施。"
        
        return result
    
    def _integrate_parallel_responses(self, responses: List[AgentResponse]) -> str:
        """整合并行响应."""
        result = "基于各智能体的并行协作，综合方案如下：\n\n"
        
        for response in responses:
            result += f"**{response.agent_type.value}智能体建议：**\n"
            result += f"{response.response_content}\n\n"
        
        result += "**协调员总结：**\n"
        result += "以上建议可以同时执行，建议建立跨部门协作机制确保有效实施。"
        
        return result
    
    def _integrate_hierarchical_responses(self, responses: List[AgentResponse]) -> str:
        """整合分层响应."""
        result = "基于分层协作分析，最终协调方案如下：\n\n"
        
        # 按重要性排序响应
        sorted_responses = sorted(responses, key=lambda r: r.confidence, reverse=True)
        
        result += "**核心建议（按优先级排序）：**\n"
        for i, response in enumerate(sorted_responses, 1):
            result += f"{i}. {response.agent_type.value}：{response.response_content[:100]}...\n"
        
        result += "\n**执行建议：**\n"
        result += "建议按照上述优先级顺序，分阶段实施各项措施，确保资源合理配置。"
        
        return result
    
    def _identify_conflicts(self, responses: List[AgentResponse]) -> List[Conflict]:
        """识别响应中的冲突."""
        conflicts = []
        
        # 简化的冲突检测逻辑
        if len(responses) > 1:
            # 检查置信度差异
            confidences = [r.confidence for r in responses]
            if max(confidences) - min(confidences) > 0.3:
                conflict = Conflict(
                    conflicting_agents=[r.agent_id for r in responses],
                    conflict_type="confidence_mismatch",
                    description="智能体间置信度差异较大",
                    proposed_solutions=["重新评估", "专家仲裁", "数据验证"]
                )
                conflicts.append(conflict)
        
        return conflicts
    
    async def _resolve_conflicts(self, conflicts: List[Conflict], 
                               responses: List[AgentResponse]) -> str:
        """解决冲突."""
        resolution = "冲突解决方案：\n\n"
        
        for conflict in conflicts:
            if conflict.conflict_type == "confidence_mismatch":
                # 选择置信度最高的响应作为主要方案
                best_response = max(responses, key=lambda r: r.confidence)
                resolution += f"采用{best_response.agent_type.value}智能体的高置信度方案，"
                resolution += "同时参考其他智能体的补充建议。\n"
        
        return resolution
    
    async def _generate_coordination_response(self, coordination_result: CollaborationResult,
                                            strategy: str) -> str:
        """生成协调响应."""
        response = f"🤝 **多智能体协作完成** 🤝\n\n"
        response += f"**协作模式：** {strategy.upper()}\n"
        response += f"**参与智能体：** {', '.join(coordination_result.participating_agents)}\n"
        response += f"**协作ID：** {coordination_result.collaboration_id}\n\n"
        
        response += "**协作结果：**\n"
        response += coordination_result.final_result
        
        if coordination_result.consensus_reached:
            response += "\n\n✅ **协作状态：** 已达成共识"
        else:
            response += "\n\n⚠️ **协作状态：** 存在分歧，需要进一步协调"
        
        response += f"\n\n**解决方法：** {coordination_result.resolution_method}"
        
        return response
    
    def _generate_coordination_actions(self, coordination_result: CollaborationResult,
                                     required_agents: List[AgentType]) -> List[Action]:
        """生成协调相关的后续动作."""
        actions = []
        
        # 协作监控
        actions.append(
            Action(
                action_type="monitor_collaboration",
                parameters={
                    "collaboration_id": coordination_result.collaboration_id,
                    "check_interval": "1_hour"
                },
                description="监控协作执行进度"
            )
        )
        
        # 结果验证
        actions.append(
            Action(
                action_type="validate_results",
                parameters={
                    "validation_method": "cross_check",
                    "timeline": "24_hours"
                },
                description="验证协作结果有效性"
            )
        )
        
        # 如果未达成共识，添加进一步协调动作
        if not coordination_result.consensus_reached:
            actions.append(
                Action(
                    action_type="escalate_coordination",
                    parameters={
                        "escalation_level": "senior_coordinator",
                        "reason": "consensus_not_reached"
                    },
                    description="升级协调处理"
                )
            )
        
        # 反馈收集
        actions.append(
            Action(
                action_type="collect_feedback",
                parameters={
                    "from_agents": [agent.value for agent in required_agents],
                    "feedback_type": "collaboration_effectiveness"
                },
                description="收集协作效果反馈"
            )
        )
        
        return actions
    
    async def _validate_config(self) -> bool:
        """验证协调员智能体配置."""
        if self.agent_type != AgentType.COORDINATOR:
            self.logger.error(f"Invalid agent type for CoordinatorAgent: {self.agent_type}")
            return False
        
        required_capabilities = ["coordination", "task_management", "conflict_resolution"]
        if not any(cap in self.config.capabilities for cap in required_capabilities):
            self.logger.warning("CoordinatorAgent missing recommended capabilities")
        
        return True
    
    async def _initialize_specific(self) -> bool:
        """协调员智能体特定的初始化."""
        self.logger.info("Initializing coordinator specific components...")
        
        # 初始化协调数据结构
        self.active_collaborations.clear()
        self.task_assignments.clear()
        self.agent_workloads.clear()
        
        self.logger.info("Coordinator agent initialization completed")
        return True
    
    async def _health_check_specific(self) -> bool:
        """协调员智能体特定的健康检查."""
        try:
            test_content = "需要协调多个部门处理复杂问题"
            confidence = await self.can_handle_request(
                UserRequest(content=test_content)
            )
            if confidence < 0.3:
                self.logger.error("Coordination capability test failed")
                return False
        except Exception as e:
            self.logger.error(f"Coordinator health check failed: {str(e)}")
            return False
        
        return True
    
    # 协调员特有的管理方法
    def get_active_collaborations(self) -> Dict[str, Dict[str, Any]]:
        """获取当前活跃的协作."""
        return self.active_collaborations.copy()
    
    def get_agent_workloads(self) -> Dict[str, int]:
        """获取智能体工作负载."""
        return self.agent_workloads.copy()
    
    async def terminate_collaboration(self, collaboration_id: str) -> bool:
        """终止指定的协作."""
        if collaboration_id in self.active_collaborations:
            self.active_collaborations[collaboration_id]["status"] = "terminated"
            self.active_collaborations[collaboration_id]["end_time"] = datetime.now()
            self.logger.info(f"Terminated collaboration {collaboration_id}")
            return True
        return False