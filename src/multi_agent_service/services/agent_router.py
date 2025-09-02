"""Agent routing service for multi-agent collaboration."""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from ..models.base import UserRequest, IntentResult, AgentInfo
from ..models.enums import AgentType, IntentType, AgentStatus
from ..services.intent_analyzer import IntentAnalyzer
from ..agents.registry import AgentRegistry

logger = logging.getLogger(__name__)


class RouteResult:
    """路由结果类."""
    
    def __init__(
        self,
        selected_agent: AgentType,
        confidence: float,
        alternative_agents: List[AgentType],
        requires_collaboration: bool,
        reasoning: str,
        estimated_processing_time: Optional[int] = None
    ):
        self.selected_agent = selected_agent
        self.confidence = confidence
        self.alternative_agents = alternative_agents
        self.requires_collaboration = requires_collaboration
        self.reasoning = reasoning
        self.estimated_processing_time = estimated_processing_time


class AgentRouter:
    """智能体路由器，负责根据意图选择合适的智能体."""
    
    def __init__(self, intent_analyzer: IntentAnalyzer, agent_registry: AgentRegistry):
        """初始化智能体路由器.
        
        Args:
            intent_analyzer: 意图分析器实例
            agent_registry: 智能体注册表实例
        """
        self.intent_analyzer = intent_analyzer
        self.agent_registry = agent_registry
        
        # 路由策略配置
        self.routing_strategies = {
            "load_balanced": self._load_balanced_routing,
            "capability_based": self._capability_based_routing,
            "priority_based": self._priority_based_routing
        }
        
        # 协作决策阈值
        self.collaboration_thresholds = {
            IntentType.MANAGEMENT_DECISION: 0.8,
            IntentType.COLLABORATION_REQUIRED: 0.6,  # 降低阈值，更容易触发协作
            IntentType.SALES_INQUIRY: 0.6,  # 复杂销售问题可能需要协作
            IntentType.TECHNICAL_SERVICE: 0.7,  # 复杂技术问题可能需要协作
            IntentType.CUSTOMER_SUPPORT: 0.5,
            IntentType.GENERAL_INQUIRY: 0.3
        }

    async def route_request(
        self, 
        user_request: UserRequest, 
        strategy: str = "capability_based"
    ) -> Tuple[RouteResult, IntentResult]:
        """路由用户请求到合适的智能体.
        
        Args:
            user_request: 用户请求
            strategy: 路由策略 ("load_balanced", "capability_based", "priority_based")
            
        Returns:
            Tuple[RouteResult, IntentResult]: 路由结果和意图识别结果
        """
        try:
            logger.info(f"开始路由请求: {user_request.request_id}")
            
            # 1. 意图识别
            intent_result = await self.intent_analyzer.analyze_intent(user_request)
            
            # 2. 验证意图结果
            if not self.intent_analyzer.validate_intent_result(intent_result):
                logger.warning("意图识别结果验证失败，使用默认路由")
                intent_result = self._get_default_intent_result()
            
            # 3. 选择路由策略
            routing_func = self.routing_strategies.get(strategy, self._capability_based_routing)
            
            # 4. 执行路由决策
            route_result = await routing_func(intent_result, user_request)
            
            # 5. 评估是否需要协作
            collaboration_needed = self._evaluate_collaboration_need(intent_result, user_request)
            route_result.requires_collaboration = collaboration_needed
            
            logger.info(f"路由完成: {route_result.selected_agent}, 置信度: {route_result.confidence}")
            return route_result, intent_result
            
        except Exception as e:
            logger.error(f"路由失败: {str(e)}")
            # 返回默认路由结果
            default_intent = self._get_default_intent_result()
            default_route = RouteResult(
                selected_agent=AgentType.CUSTOMER_SUPPORT,
                confidence=0.1,
                alternative_agents=[AgentType.SALES],
                requires_collaboration=False,
                reasoning=f"路由失败，使用默认路由: {str(e)}"
            )
            return default_route, default_intent

    async def _capability_based_routing(
        self, 
        intent_result: IntentResult, 
        user_request: UserRequest
    ) -> RouteResult:
        """基于能力的路由策略.
        
        Args:
            intent_result: 意图识别结果
            user_request: 用户请求
            
        Returns:
            RouteResult: 路由结果
        """
        # 获取意图路由规则
        intent_rules = self.intent_analyzer.get_intent_rules()
        rule = intent_rules.get(intent_result.intent_type)
        
        if not rule:
            logger.warning(f"未找到意图类型 {intent_result.intent_type} 的路由规则")
            return RouteResult(
                selected_agent=AgentType.CUSTOMER_SUPPORT,
                confidence=0.3,
                alternative_agents=[],
                requires_collaboration=False,
                reasoning="未找到匹配的路由规则"
            )
        
        # 获取主要智能体候选
        primary_agents = rule.get("primary_agents", [])
        fallback_agents = rule.get("fallback_agents", [])
        
        # 检查主要智能体可用性
        available_primary = await self._get_available_agents(primary_agents)
        
        if available_primary:
            selected_agent = available_primary[0]
            confidence = intent_result.confidence * 0.9  # 基于意图置信度调整
            alternatives = available_primary[1:] + fallback_agents
        else:
            # 使用备用智能体
            available_fallback = await self._get_available_agents(fallback_agents)
            if available_fallback:
                selected_agent = available_fallback[0]
                confidence = intent_result.confidence * 0.6  # 降低置信度
                alternatives = available_fallback[1:]
            else:
                # 所有智能体都不可用，使用默认
                selected_agent = AgentType.CUSTOMER_SUPPORT
                confidence = 0.2
                alternatives = []
        
        # 估算处理时间
        processing_time = self._estimate_processing_time(intent_result.intent_type, selected_agent)
        
        return RouteResult(
            selected_agent=selected_agent,
            confidence=confidence,
            alternative_agents=alternatives,
            requires_collaboration=rule.get("requires_collaboration", False),
            reasoning=f"基于能力匹配选择 {selected_agent.value}",
            estimated_processing_time=processing_time
        )

    async def _load_balanced_routing(
        self, 
        intent_result: IntentResult, 
        user_request: UserRequest
    ) -> RouteResult:
        """基于负载均衡的路由策略.
        
        Args:
            intent_result: 意图识别结果
            user_request: 用户请求
            
        Returns:
            RouteResult: 路由结果
        """
        # 先使用能力路由获取候选智能体
        capability_result = await self._capability_based_routing(intent_result, user_request)
        
        # 获取所有候选智能体（包括主选和备选）
        all_candidates = [capability_result.selected_agent] + capability_result.alternative_agents
        
        # 根据负载选择最优智能体
        best_agent = await self._select_least_loaded_agent(all_candidates)
        
        if best_agent:
            # 重新计算备选列表
            alternatives = [agent for agent in all_candidates if agent != best_agent]
            
            return RouteResult(
                selected_agent=best_agent,
                confidence=capability_result.confidence * 0.95,  # 负载均衡略微提升置信度
                alternative_agents=alternatives,
                requires_collaboration=capability_result.requires_collaboration,
                reasoning=f"基于负载均衡选择 {best_agent.value}",
                estimated_processing_time=capability_result.estimated_processing_time
            )
        else:
            # 如果无法获取负载信息，回退到能力路由
            return capability_result

    async def _priority_based_routing(
        self, 
        intent_result: IntentResult, 
        user_request: UserRequest
    ) -> RouteResult:
        """基于优先级的路由策略.
        
        Args:
            intent_result: 意图识别结果
            user_request: 用户请求
            
        Returns:
            RouteResult: 路由结果
        """
        # 先使用能力路由获取基础结果
        base_result = await self._capability_based_routing(intent_result, user_request)
        
        # 根据请求优先级调整路由
        if user_request.priority.value in ["high", "urgent"]:
            # 高优先级请求优先选择最有经验的智能体
            experienced_agent = await self._select_most_experienced_agent(
                [base_result.selected_agent] + base_result.alternative_agents
            )
            
            if experienced_agent:
                alternatives = [agent for agent in base_result.alternative_agents 
                              if agent != experienced_agent]
                if base_result.selected_agent != experienced_agent:
                    alternatives.insert(0, base_result.selected_agent)
                
                return RouteResult(
                    selected_agent=experienced_agent,
                    confidence=min(base_result.confidence * 1.1, 1.0),  # 提升置信度
                    alternative_agents=alternatives,
                    requires_collaboration=base_result.requires_collaboration,
                    reasoning=f"基于高优先级选择经验丰富的 {experienced_agent.value}",
                    estimated_processing_time=base_result.estimated_processing_time
                )
        
        return base_result

    def _evaluate_collaboration_need(
        self, 
        intent_result: IntentResult, 
        user_request: UserRequest
    ) -> bool:
        """评估是否需要多智能体协作.
        
        Args:
            intent_result: 意图识别结果
            user_request: 用户请求
            
        Returns:
            bool: 是否需要协作
        """
        # 1. 检查意图结果中的协作标识
        if intent_result.requires_collaboration:
            return True
        
        # 2. 检查意图类型的协作阈值
        threshold = self.collaboration_thresholds.get(intent_result.intent_type, 0.5)
        logger.debug(f"协作评估 - 意图类型: {intent_result.intent_type}, 阈值: {threshold}")
        
        # 3. 基于多个因素评估协作需求
        collaboration_score = 0.0
        
        # 意图置信度低可能需要协作
        if intent_result.confidence < 0.7:
            collaboration_score += 0.3
        
        # 提取到多个不同类型的实体可能需要协作
        entity_types = set(entity.entity_type for entity in intent_result.entities)
        if len(entity_types) > 3:
            collaboration_score += 0.2
        
        # 请求内容复杂度评估
        content_complexity = self._assess_content_complexity(user_request.content)
        collaboration_score += content_complexity * 0.3
        
        # 高优先级请求更可能需要协作
        if user_request.priority.value in ["high", "urgent"]:
            collaboration_score += 0.2
        
        logger.debug(f"协作评估 - 最终分数: {collaboration_score}, 阈值: {threshold}, 需要协作: {collaboration_score >= threshold}")
        return collaboration_score >= threshold

    def _assess_content_complexity(self, content: str) -> float:
        """评估内容复杂度.
        
        Args:
            content: 请求内容
            
        Returns:
            float: 复杂度分数 (0.0-1.0)
        """
        # 简单的复杂度评估指标
        complexity_indicators = [
            "并且", "同时", "另外", "还有", "以及",  # 多个需求
            "复杂", "困难", "紧急", "重要",  # 复杂性关键词
            "多个", "各种", "不同", "综合",  # 多样性关键词
            "跨部门", "协作", "配合", "联合"  # 协作关键词
        ]
        
        # 计算关键词匹配数
        matches = sum(1 for indicator in complexity_indicators if indicator in content)
        
        # 基于长度和关键词计算复杂度
        length_score = min(len(content) / 200, 1.0)  # 降低长度阈值，使其更敏感
        keyword_score = min(matches / 3, 1.0)  # 降低关键词阈值
        
        # 给关键词更高的权重
        return (length_score * 0.3 + keyword_score * 0.7)

    async def _get_available_agents(self, agent_types: List[AgentType]) -> List[AgentType]:
        """获取可用的智能体列表.
        
        Args:
            agent_types: 智能体类型列表
            
        Returns:
            List[AgentType]: 可用的智能体类型列表
        """
        available_agents = []
        
        for agent_type in agent_types:
            try:
                # 检查agent_registry.get_agent_info是否是异步方法
                if hasattr(self.agent_registry.get_agent_info, '__call__'):
                    # 尝试调用，如果是协程则await，否则直接使用
                    result = self.agent_registry.get_agent_info(agent_type.value)
                    if hasattr(result, '__await__'):
                        agent_info = await result
                    else:
                        agent_info = result
                else:
                    agent_info = await self.agent_registry.get_agent_info(agent_type.value)
                
                if agent_info and agent_info.status != AgentStatus.OFFLINE:
                    available_agents.append(agent_type)
            except Exception as e:
                logger.warning(f"检查智能体 {agent_type} 可用性失败: {e}")
                continue
        
        return available_agents

    async def _select_least_loaded_agent(self, agent_types: List[AgentType]) -> Optional[AgentType]:
        """选择负载最低的智能体.
        
        Args:
            agent_types: 智能体类型列表
            
        Returns:
            Optional[AgentType]: 负载最低的智能体类型
        """
        min_load = float('inf')
        selected_agent = None
        
        for agent_type in agent_types:
            try:
                # 检查agent_registry.get_agent_info是否是异步方法
                result = self.agent_registry.get_agent_info(agent_type.value)
                if hasattr(result, '__await__'):
                    agent_info = await result
                else:
                    agent_info = result
                
                if agent_info and agent_info.status != AgentStatus.OFFLINE:
                    load_ratio = agent_info.current_load / agent_info.max_load
                    if load_ratio < min_load:
                        min_load = load_ratio
                        selected_agent = agent_type
            except Exception as e:
                logger.warning(f"获取智能体 {agent_type} 负载信息失败: {e}")
                continue
        
        return selected_agent

    async def _select_most_experienced_agent(self, agent_types: List[AgentType]) -> Optional[AgentType]:
        """选择最有经验的智能体（基于历史处理次数）.
        
        Args:
            agent_types: 智能体类型列表
            
        Returns:
            Optional[AgentType]: 最有经验的智能体类型
        """
        # 这里可以基于历史数据选择，暂时使用简单的优先级排序
        priority_order = [
            AgentType.COORDINATOR,
            AgentType.MANAGER,
            AgentType.SALES,
            AgentType.FIELD_SERVICE,
            AgentType.CUSTOMER_SUPPORT
        ]
        
        for agent_type in priority_order:
            if agent_type in agent_types:
                # 检查智能体是否可用
                try:
                    result = self.agent_registry.get_agent_info(agent_type.value)
                    if hasattr(result, '__await__'):
                        agent_info = await result
                    else:
                        agent_info = result
                    
                    if agent_info and agent_info.status != AgentStatus.OFFLINE:
                        return agent_type
                except Exception:
                    continue
        
        return agent_types[0] if agent_types else None

    def _estimate_processing_time(self, intent_type: IntentType, agent_type: AgentType) -> int:
        """估算处理时间（秒）.
        
        Args:
            intent_type: 意图类型
            agent_type: 智能体类型
            
        Returns:
            int: 预估处理时间（秒）
        """
        # 基于意图类型和智能体类型的处理时间估算
        base_times = {
            IntentType.GENERAL_INQUIRY: 30,
            IntentType.SALES_INQUIRY: 60,
            IntentType.CUSTOMER_SUPPORT: 90,
            IntentType.TECHNICAL_SERVICE: 120,
            IntentType.MANAGEMENT_DECISION: 180,
            IntentType.COLLABORATION_REQUIRED: 300
        }
        
        agent_multipliers = {
            AgentType.CUSTOMER_SUPPORT: 1.0,
            AgentType.SALES: 1.2,
            AgentType.FIELD_SERVICE: 1.5,
            AgentType.MANAGER: 2.0,
            AgentType.COORDINATOR: 2.5
        }
        
        base_time = base_times.get(intent_type, 60)
        multiplier = agent_multipliers.get(agent_type, 1.0)
        
        return int(base_time * multiplier)

    def _get_default_intent_result(self) -> IntentResult:
        """获取默认意图识别结果.
        
        Returns:
            IntentResult: 默认意图结果
        """
        return IntentResult(
            intent_type=IntentType.GENERAL_INQUIRY,
            confidence=0.5,
            entities=[],
            suggested_agents=[AgentType.CUSTOMER_SUPPORT],
            requires_collaboration=False,
            reasoning="使用默认意图识别结果"
        )

    async def get_routing_statistics(self) -> Dict[str, Any]:
        """获取路由统计信息.
        
        Returns:
            Dict[str, Any]: 路由统计数据
        """
        # 这里可以实现路由统计逻辑
        # 暂时返回基本信息
        return {
            "total_routes": 0,
            "success_rate": 0.0,
            "average_confidence": 0.0,
            "collaboration_rate": 0.0,
            "agent_distribution": {},
            "intent_distribution": {},
            "last_updated": datetime.now().isoformat()
        }