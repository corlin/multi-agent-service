"""Patent Coordinator Agent implementation for managing patent analysis workflows."""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from uuid import uuid4

from .base import PatentBaseAgent
from ..coordinator_agent import CoordinatorAgent
from ...models.base import UserRequest, AgentResponse, Action, CollaborationResult, Conflict
from ...models.config import AgentConfig
from ...models.enums import AgentType, WorkflowStatus
from ...services.model_client import BaseModelClient
from ...workflows.state_management import WorkflowStateManager
# AgentRouter will be imported dynamically to avoid circular imports


logger = logging.getLogger(__name__)


class PatentCoordinatorAgent(CoordinatorAgent):
    """专利协调Agent，负责管理专利分析工作流的执行和协调."""
    
    def __init__(self, config: AgentConfig, model_client: BaseModelClient, 
                 state_manager: Optional[WorkflowStateManager] = None,
                 agent_router: Optional[Any] = None):
        """初始化专利协调Agent."""
        super().__init__(config, model_client)
        
        # 专利分析特定的协调配置
        self.patent_workflow_config = {
            'data_collection_agents': ['patent_data_collection_agent'],
            'search_agents': ['patent_search_agent'],
            'analysis_agents': ['patent_analysis_agent'],
            'report_agents': ['patent_report_agent']
        }
        
        # 专利分析关键词
        self.patent_coordination_keywords = [
            "专利分析", "专利检索", "专利报告", "技术分析", "竞争分析",
            "专利趋势", "专利数据", "知识产权分析", "技术发展",
            "patent analysis", "patent search", "patent report", 
            "technology analysis", "competitive analysis"
        ]
        
        # 专利工作流类型
        self.patent_workflow_types = {
            "comprehensive_analysis": "全面专利分析工作流",
            "quick_search": "快速专利检索工作流", 
            "trend_analysis": "专利趋势分析工作流",
            "competitive_analysis": "竞争分析工作流",
            "report_generation": "专利报告生成工作流"
        }
        
        # 工作流状态管理器
        self.state_manager = state_manager or WorkflowStateManager()
        
        # Agent路由器
        self.agent_router = agent_router
        
        # 活跃的专利分析任务
        self.active_patent_tasks: Dict[str, Dict[str, Any]] = {}
        
        # 专利Agent能力映射
        self.patent_agent_capabilities = {
            "patent_data_collection_agent": [
                "专利数据收集", "多数据源集成", "数据清洗", "数据缓存"
            ],
            "patent_search_agent": [
                "CNKI学术搜索", "博查AI搜索", "网页爬取", "搜索结果增强"
            ],
            "patent_analysis_agent": [
                "趋势分析", "技术分类", "竞争分析", "地域分析", "深度洞察"
            ],
            "patent_report_agent": [
                "报告生成", "图表制作", "模板渲染", "多格式导出"
            ]
        }
        
        # 专利工作流执行策略
        self.execution_strategies = {
            "sequential": self._execute_sequential_workflow,
            "parallel": self._execute_parallel_workflow,
            "hierarchical": self._execute_hierarchical_workflow,
            "hybrid": self._execute_hybrid_workflow
        }
    
    async def can_handle_request(self, request: UserRequest) -> float:
        """判断是否能处理专利协调请求."""
        content = request.content.lower()
        
        # 检查专利协调关键词
        keyword_matches = sum(1 for keyword in self.patent_coordination_keywords if keyword in content)
        keyword_score = min(keyword_matches * 0.3, 0.8)
        
        # 检查复杂性指标（需要协调的专利任务）
        complexity_indicators = [
            "全面", "综合", "完整", "深度", "多维度", "系统性",
            "comprehensive", "complete", "in-depth", "systematic"
        ]
        complexity_score = 0.4 if any(indicator in content for indicator in complexity_indicators) else 0
        
        # 检查多Agent需求
        multi_agent_patterns = [
            r"(数据收集|检索|搜索).*?(分析|报告)",
            r"(分析|处理).*?(报告|展示)",
            r"(专利|技术).*?(全面|综合).*?(分析|研究)",
            r"需要.*?(多个|各种|不同).*?(数据|信息|分析)"
        ]
        
        import re
        pattern_score = 0
        for pattern in multi_agent_patterns:
            if re.search(pattern, content):
                pattern_score += 0.3
        
        # 基于父类协调能力的基础分数
        base_score = await super().can_handle_request(request)
        
        # 综合计算专利协调置信度
        total_score = min(
            base_score * 0.3 + keyword_score + complexity_score + pattern_score, 
            1.0
        )
        
        return max(total_score, 0.0)
    
    async def get_capabilities(self) -> List[str]:
        """获取专利协调Agent的能力列表."""
        base_capabilities = await super().get_capabilities()
        patent_capabilities = [
            "专利工作流协调",
            "专利Agent调度",
            "专利数据流管理",
            "专利分析质量控制",
            "专利报告整合",
            "专利任务监控"
        ]
        return base_capabilities + patent_capabilities
    
    async def estimate_processing_time(self, request: UserRequest) -> int:
        """估算专利协调处理时间."""
        content = request.content.lower()
        
        # 快速检索：60-90秒
        if any(word in content for word in ["快速", "简单", "基本"]):
            return 75
        
        # 全面分析：180-300秒
        if any(word in content for word in ["全面", "深度", "完整", "综合"]):
            return 240
        
        # 报告生成：120-180秒
        if any(word in content for word in ["报告", "文档", "展示"]):
            return 150
        
        # 默认专利协调时间
        return 120
    
    async def _process_request_specific(self, request: UserRequest) -> AgentResponse:
        """处理专利协调请求."""
        try:
            # 分析专利任务类型和复杂度
            task_analysis = await self._analyze_patent_task(request.content)
            
            # 确定所需的专利Agent
            required_agents = await self._identify_required_patent_agents(request.content, task_analysis)
            
            # 选择执行策略
            execution_strategy = self._determine_patent_execution_strategy(task_analysis, required_agents)
            
            # 创建专利工作流执行上下文
            workflow_context = await self._create_patent_workflow_context(
                request, task_analysis, required_agents, execution_strategy
            )
            
            # 执行专利工作流
            coordination_result = await self._execute_patent_workflow(
                workflow_context, execution_strategy
            )
            
            # 生成专利协调响应
            response_content = await self._generate_patent_coordination_response(
                coordination_result, workflow_context
            )
            
            # 生成后续动作
            next_actions = self._generate_patent_coordination_actions(
                coordination_result, workflow_context
            )
            
            return AgentResponse(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                response_content=response_content,
                confidence=0.95,
                next_actions=next_actions,
                collaboration_needed=False,
                metadata={
                    "workflow_type": execution_strategy,
                    "required_agents": required_agents,
                    "task_analysis": task_analysis,
                    "coordination_id": coordination_result.collaboration_id,
                    "patent_task_type": workflow_context.get("task_type"),
                    "processed_at": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            self.logger.error(f"Patent coordination failed: {str(e)}")
            return AgentResponse(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                response_content=f"专利分析协调过程中发生错误: {str(e)}",
                confidence=0.0,
                collaboration_needed=False,
                metadata={"error": str(e), "error_type": "coordination_failure"}
            )
    
    async def _analyze_patent_task(self, content: str) -> Dict[str, Any]:
        """分析专利任务类型和复杂度."""
        content_lower = content.lower()
        
        # 任务类型识别
        task_type = "comprehensive_analysis"  # 默认
        
        if any(word in content_lower for word in ["检索", "搜索", "查找"]):
            task_type = "quick_search"
        elif any(word in content_lower for word in ["趋势", "发展", "变化"]):
            task_type = "trend_analysis"
        elif any(word in content_lower for word in ["竞争", "对比", "比较"]):
            task_type = "competitive_analysis"
        elif any(word in content_lower for word in ["报告", "文档", "展示"]):
            task_type = "report_generation"
        
        # 复杂度分析
        complexity_factors = {
            "data_sources": len([s for s in ["cnki", "专利", "学术", "网页"] if s in content_lower]),
            "analysis_depth": 1 if any(word in content_lower for word in ["深度", "详细", "全面"]) else 0,
            "output_formats": len([f for f in ["报告", "图表", "文档", "pdf"] if f in content_lower]),
            "time_range": 1 if any(word in content_lower for word in ["年", "月", "历史", "趋势"]) else 0
        }
        
        total_complexity = sum(complexity_factors.values())
        
        if total_complexity >= 4:
            complexity_level = "high"
        elif total_complexity >= 2:
            complexity_level = "medium"
        else:
            complexity_level = "low"
        
        return {
            "task_type": task_type,
            "complexity_level": complexity_level,
            "complexity_factors": complexity_factors,
            "complexity_score": total_complexity,
            "estimated_duration": self._estimate_task_duration(task_type, complexity_level)
        }
    
    async def _identify_required_patent_agents(self, content: str, task_analysis: Dict[str, Any]) -> List[str]:
        """识别所需的专利Agent."""
        content_lower = content.lower()
        required_agents = []
        
        task_type = task_analysis.get("task_type", "comprehensive_analysis")
        
        # 根据任务类型确定基础Agent需求
        if task_type == "quick_search":
            required_agents = ["patent_search_agent"]
        elif task_type == "trend_analysis":
            required_agents = ["patent_data_collection_agent", "patent_analysis_agent"]
        elif task_type == "competitive_analysis":
            required_agents = ["patent_data_collection_agent", "patent_search_agent", "patent_analysis_agent"]
        elif task_type == "report_generation":
            required_agents = ["patent_analysis_agent", "patent_report_agent"]
        else:  # comprehensive_analysis
            required_agents = [
                "patent_data_collection_agent",
                "patent_search_agent", 
                "patent_analysis_agent",
                "patent_report_agent"
            ]
        
        # 根据内容进一步调整
        if any(word in content_lower for word in ["数据", "收集", "获取"]):
            if "patent_data_collection_agent" not in required_agents:
                required_agents.insert(0, "patent_data_collection_agent")
        
        if any(word in content_lower for word in ["搜索", "检索", "cnki", "博查"]):
            if "patent_search_agent" not in required_agents:
                required_agents.append("patent_search_agent")
        
        if any(word in content_lower for word in ["分析", "趋势", "竞争"]):
            if "patent_analysis_agent" not in required_agents:
                required_agents.append("patent_analysis_agent")
        
        if any(word in content_lower for word in ["报告", "文档", "图表"]):
            if "patent_report_agent" not in required_agents:
                required_agents.append("patent_report_agent")
        
        return required_agents
    
    def _determine_patent_execution_strategy(self, task_analysis: Dict[str, Any], 
                                           required_agents: List[str]) -> str:
        """确定专利工作流执行策略."""
        task_type = task_analysis.get("task_type")
        complexity_level = task_analysis.get("complexity_level")
        agent_count = len(required_agents)
        
        # 快速搜索使用顺序执行
        if task_type == "quick_search":
            return "sequential"
        
        # 高复杂度或多Agent使用分层执行
        if complexity_level == "high" or agent_count > 3:
            return "hierarchical"
        
        # 中等复杂度使用混合执行
        if complexity_level == "medium" or agent_count > 2:
            return "hybrid"
        
        # 简单任务使用并行执行
        return "parallel"
    
    async def _create_patent_workflow_context(self, request: UserRequest,
                                            task_analysis: Dict[str, Any],
                                            required_agents: List[str],
                                            execution_strategy: str) -> Dict[str, Any]:
        """创建专利工作流执行上下文."""
        workflow_id = str(uuid4())
        
        context = {
            "workflow_id": workflow_id,
            "request": request,
            "task_type": task_analysis.get("task_type"),
            "complexity_level": task_analysis.get("complexity_level"),
            "required_agents": required_agents,
            "execution_strategy": execution_strategy,
            "start_time": datetime.now(),
            "shared_data": {},
            "agent_results": {},
            "status": "initialized"
        }
        
        # 记录活跃任务
        self.active_patent_tasks[workflow_id] = context
        
        return context
    
    async def _execute_patent_workflow(self, workflow_context: Dict[str, Any],
                                     execution_strategy: str) -> CollaborationResult:
        """执行专利工作流."""
        workflow_id = workflow_context["workflow_id"]
        
        try:
            # 更新状态
            workflow_context["status"] = "running"
            
            # 根据策略执行工作流
            strategy_func = self.execution_strategies.get(execution_strategy, 
                                                        self._execute_sequential_workflow)
            
            result = await strategy_func(workflow_context)
            
            # 更新状态
            workflow_context["status"] = "completed"
            workflow_context["end_time"] = datetime.now()
            
            return result
            
        except Exception as e:
            workflow_context["status"] = "failed"
            workflow_context["error"] = str(e)
            workflow_context["end_time"] = datetime.now()
            
            self.logger.error(f"Patent workflow {workflow_id} failed: {str(e)}")
            
            # 使用专门的失败处理机制
            return await self._handle_coordination_failure(workflow_context, e)
        
        finally:
            # 清理活跃任务
            if workflow_id in self.active_patent_tasks:
                del self.active_patent_tasks[workflow_id]
    
    async def _execute_sequential_workflow(self, workflow_context: Dict[str, Any]) -> CollaborationResult:
        """执行顺序专利工作流."""
        workflow_id = workflow_context["workflow_id"]
        required_agents = workflow_context["required_agents"]
        request = workflow_context["request"]
        
        results = []
        accumulated_data = request.context.copy()
        
        for i, agent_id in enumerate(required_agents):
            try:
                # 创建Agent请求
                agent_request = UserRequest(
                    content=request.content,
                    user_id=request.user_id,
                    context=accumulated_data,
                    priority=request.priority
                )
                
                # 调用Agent（使用带重试和降级的真实调用）
                agent_result = await self._call_patent_agent_with_fallback(agent_id, agent_request)
                results.append(agent_result)
                
                # 更新累积数据
                if hasattr(agent_result, 'metadata') and agent_result.metadata:
                    accumulated_data.update(agent_result.metadata.get("shared_data", {}))
                
                # 记录Agent结果
                workflow_context["agent_results"][agent_id] = agent_result
                
                self.logger.info(f"Sequential step {i+1}/{len(required_agents)} completed: {agent_id}")
                
            except Exception as e:
                self.logger.error(f"Sequential step failed for agent {agent_id}: {str(e)}")
                error_result = AgentResponse(
                    agent_id=agent_id,
                    agent_type=AgentType.PATENT_COORDINATOR,
                    response_content=f"Agent {agent_id} 执行失败: {str(e)}",
                    confidence=0.0,
                    metadata={"error": str(e)}
                )
                results.append(error_result)
                break
        
        # 同步Agent数据
        await self._synchronize_agent_data(workflow_context, results)
        
        # 验证响应质量
        validation_result = await self._validate_agent_responses(results)
        workflow_context["validation_result"] = validation_result
        
        # 整合顺序执行结果
        final_result = self._integrate_sequential_patent_results(results, workflow_context)
        
        return CollaborationResult(
            collaboration_id=workflow_id,
            participating_agents=required_agents + [self.agent_id],
            final_result=final_result,
            individual_responses=results,
            consensus_reached=True,
            resolution_method="sequential_integration"
        )
    
    async def _execute_parallel_workflow(self, workflow_context: Dict[str, Any]) -> CollaborationResult:
        """执行并行专利工作流."""
        workflow_id = workflow_context["workflow_id"]
        required_agents = workflow_context["required_agents"]
        request = workflow_context["request"]
        
        # 创建并行任务
        tasks = []
        for agent_id in required_agents:
            agent_request = UserRequest(
                content=request.content,
                user_id=request.user_id,
                context=request.context.copy(),
                priority=request.priority
            )
            
            task = self._call_patent_agent_with_fallback(agent_id, agent_request)
            tasks.append(task)
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        valid_results = []
        for i, result in enumerate(results):
            agent_id = required_agents[i]
            if isinstance(result, Exception):
                error_result = AgentResponse(
                    agent_id=agent_id,
                    agent_type=AgentType.PATENT_COORDINATOR,
                    response_content=f"Agent {agent_id} 执行失败: {str(result)}",
                    confidence=0.0,
                    metadata={"error": str(result)}
                )
                valid_results.append(error_result)
            else:
                valid_results.append(result)
                workflow_context["agent_results"][agent_id] = result
        
        # 同步Agent数据
        await self._synchronize_agent_data(workflow_context, valid_results)
        
        # 验证响应质量
        validation_result = await self._validate_agent_responses(valid_results)
        workflow_context["validation_result"] = validation_result
        
        # 整合并行执行结果
        final_result = self._integrate_parallel_patent_results(valid_results, workflow_context)
        
        return CollaborationResult(
            collaboration_id=workflow_id,
            participating_agents=required_agents + [self.agent_id],
            final_result=final_result,
            individual_responses=valid_results,
            consensus_reached=len(valid_results) == len(required_agents),
            resolution_method="parallel_integration"
        )
    
    async def _execute_hierarchical_workflow(self, workflow_context: Dict[str, Any]) -> CollaborationResult:
        """执行分层专利工作流."""
        workflow_id = workflow_context["workflow_id"]
        required_agents = workflow_context["required_agents"]
        
        # 第一层：数据收集
        data_agents = [agent for agent in required_agents 
                      if "data_collection" in agent or "search" in agent]
        
        # 第二层：分析处理
        analysis_agents = [agent for agent in required_agents 
                          if "analysis" in agent]
        
        # 第三层：报告生成
        report_agents = [agent for agent in required_agents 
                        if "report" in agent]
        
        all_results = []
        
        # 执行第一层
        if data_agents:
            layer1_context = workflow_context.copy()
            layer1_context["required_agents"] = data_agents
            layer1_result = await self._execute_parallel_workflow(layer1_context)
            all_results.extend(layer1_result.individual_responses)
        
        # 执行第二层
        if analysis_agents:
            layer2_context = workflow_context.copy()
            layer2_context["required_agents"] = analysis_agents
            # 传递第一层的结果
            if data_agents:
                layer2_context["shared_data"].update(
                    self._extract_shared_data_from_results(layer1_result.individual_responses)
                )
            layer2_result = await self._execute_parallel_workflow(layer2_context)
            all_results.extend(layer2_result.individual_responses)
        
        # 执行第三层
        if report_agents:
            layer3_context = workflow_context.copy()
            layer3_context["required_agents"] = report_agents
            # 传递前面层的结果
            if analysis_agents:
                layer3_context["shared_data"].update(
                    self._extract_shared_data_from_results(layer2_result.individual_responses)
                )
            layer3_result = await self._execute_parallel_workflow(layer3_context)
            all_results.extend(layer3_result.individual_responses)
        
        # 整合分层执行结果
        final_result = self._integrate_hierarchical_patent_results(all_results, workflow_context)
        
        return CollaborationResult(
            collaboration_id=workflow_id,
            participating_agents=required_agents + [self.agent_id],
            final_result=final_result,
            individual_responses=all_results,
            consensus_reached=True,
            resolution_method="hierarchical_coordination"
        )
    
    async def _execute_hybrid_workflow(self, workflow_context: Dict[str, Any]) -> CollaborationResult:
        """执行混合专利工作流."""
        # 混合策略：数据收集和搜索并行，然后顺序执行分析和报告
        workflow_id = workflow_context["workflow_id"]
        required_agents = workflow_context["required_agents"]
        
        # 分组
        parallel_agents = [agent for agent in required_agents 
                          if "data_collection" in agent or "search" in agent]
        sequential_agents = [agent for agent in required_agents 
                           if "analysis" in agent or "report" in agent]
        
        all_results = []
        
        # 并行执行数据收集和搜索
        if parallel_agents:
            parallel_context = workflow_context.copy()
            parallel_context["required_agents"] = parallel_agents
            parallel_result = await self._execute_parallel_workflow(parallel_context)
            all_results.extend(parallel_result.individual_responses)
            
            # 更新共享数据
            workflow_context["shared_data"].update(
                self._extract_shared_data_from_results(parallel_result.individual_responses)
            )
        
        # 顺序执行分析和报告
        if sequential_agents:
            sequential_context = workflow_context.copy()
            sequential_context["required_agents"] = sequential_agents
            sequential_result = await self._execute_sequential_workflow(sequential_context)
            all_results.extend(sequential_result.individual_responses)
        
        # 整合混合执行结果
        final_result = self._integrate_hybrid_patent_results(all_results, workflow_context)
        
        return CollaborationResult(
            collaboration_id=workflow_id,
            participating_agents=required_agents + [self.agent_id],
            final_result=final_result,
            individual_responses=all_results,
            consensus_reached=True,
            resolution_method="hybrid_execution"
        )
    
    async def _call_patent_agent(self, agent_id: str, request: UserRequest) -> AgentResponse:
        """调用指定的专利Agent."""
        try:
            # 获取Agent路由器
            if not self.agent_router:
                # 动态导入以避免循环依赖
                from ...services.agent_router import AgentRouter
                from ...services.intent_analyzer import IntentAnalyzer
                from ...agents.registry import agent_registry
                from ...config.config_manager import ConfigManager
                
                config_manager = ConfigManager()
                intent_analyzer = IntentAnalyzer(config_manager)
                self.agent_router = AgentRouter(intent_analyzer, agent_registry)
            
            # 映射agent_id到AgentType
            agent_type_mapping = {
                "patent_data_collection_agent": AgentType.PATENT_DATA_COLLECTION,
                "patent_search_agent": AgentType.PATENT_SEARCH,
                "patent_analysis_agent": AgentType.PATENT_ANALYSIS,
                "patent_report_agent": AgentType.PATENT_REPORT,
                "patent_coordinator_agent": AgentType.PATENT_COORDINATOR
            }
            
            agent_type = agent_type_mapping.get(agent_id)
            if not agent_type:
                raise ValueError(f"Unknown patent agent ID: {agent_id}")
            
            # 获取Agent实例
            from ...agents.registry import agent_registry
            agents = agent_registry.get_agents_by_type(agent_type)
            
            if not agents:
                raise RuntimeError(f"No agents found for type: {agent_type}")
            
            # 选择最佳Agent实例（负载最低的健康Agent）
            best_agent = None
            min_load = float('inf')
            
            for agent in agents:
                try:
                    if agent.is_healthy():
                        agent_info = agent.get_status()
                        load_ratio = agent_info.current_load / max(agent_info.max_load, 1)
                        if load_ratio < min_load:
                            min_load = load_ratio
                            best_agent = agent
                except Exception as e:
                    self.logger.warning(f"Error checking agent {agent.agent_id} status: {str(e)}")
                    continue
            
            if not best_agent:
                raise RuntimeError(f"No healthy agents available for type: {agent_type}")
            
            # 调用Agent
            self.logger.info(f"Calling patent agent {best_agent.agent_id} for request {request.request_id}")
            response = await best_agent.process_request(request)
            
            if not response:
                raise RuntimeError(f"Agent {best_agent.agent_id} returned no response")
            
            # 添加调用元数据
            if not response.metadata:
                response.metadata = {}
            
            response.metadata.update({
                "called_by": self.agent_id,
                "call_timestamp": datetime.now().isoformat(),
                "agent_load": min_load,
                "coordination_context": True
            })
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error calling patent agent {agent_id}: {str(e)}")
            return self._create_error_response(agent_id, f"Agent call failed: {str(e)}")
    
    def _create_error_response(self, agent_id: str, error_message: str) -> AgentResponse:
        """创建错误响应."""
        return AgentResponse(
            agent_id=agent_id,
            agent_type=AgentType.PATENT_COORDINATOR,
            response_content=f"❌ **Agent调用失败**\n\n**Agent**: {agent_id}\n**错误**: {error_message}\n\n请检查Agent状态或稍后重试。",
            confidence=0.0,
            collaboration_needed=False,
            metadata={
                "error": True,
                "error_message": error_message,
                "failed_agent": agent_id,
                "timestamp": datetime.now().isoformat()
            }
        )

    async def _call_patent_agent_with_retry(self, agent_id: str, request: UserRequest, 
                                          max_retries: int = 3, retry_delay: float = 1.0) -> AgentResponse:
        """带重试机制的Agent调用."""
        last_error = None
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Calling {agent_id}, attempt {attempt + 1}/{max_retries}")
                response = await self._call_patent_agent(agent_id, request)
                
                # 检查响应质量
                if response.confidence > 0.0:  # 成功响应
                    if attempt > 0:
                        self.logger.info(f"Agent {agent_id} succeeded on attempt {attempt + 1}")
                    return response
                else:
                    # 置信度为0表示失败，但不是异常
                    last_error = f"Agent returned low confidence response: {response.response_content}"
                    
            except Exception as e:
                last_error = str(e)
                self.logger.warning(f"Agent {agent_id} call failed on attempt {attempt + 1}: {last_error}")
                
                # 如果不是最后一次尝试，等待后重试
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (2 ** attempt))  # 指数退避
        
        # 所有重试都失败了
        self.logger.error(f"All retry attempts failed for agent {agent_id}: {last_error}")
        return self._create_error_response(
            agent_id, 
            f"Agent call failed after {max_retries} attempts. Last error: {last_error}"
        )
    
    async def _call_patent_agent_with_fallback(self, agent_id: str, request: UserRequest) -> AgentResponse:
        """带降级策略的Agent调用."""
        try:
            # 首先尝试正常调用
            response = await self._call_patent_agent_with_retry(agent_id, request)
            
            # 如果响应质量可接受，直接返回
            if response.confidence >= 0.3:
                return response
            
            # 如果响应质量太低，尝试降级策略
            self.logger.warning(f"Agent {agent_id} response quality too low, trying fallback strategies")
            
            # 降级策略1：尝试调用同类型的其他Agent
            fallback_response = await self._try_alternative_agents(agent_id, request)
            if fallback_response and fallback_response.confidence >= 0.3:
                return fallback_response
            
            # 降级策略2：使用简化的处理逻辑
            return await self._create_simplified_response(agent_id, request)
            
        except Exception as e:
            self.logger.error(f"Fallback strategy failed for {agent_id}: {str(e)}")
            return self._create_error_response(agent_id, f"All fallback strategies failed: {str(e)}")
    
    async def _try_alternative_agents(self, failed_agent_id: str, request: UserRequest) -> Optional[AgentResponse]:
        """尝试调用同类型的其他Agent."""
        try:
            from ...agents.registry import agent_registry
            
            # 获取失败Agent的类型
            agent_type_mapping = {
                "patent_data_collection_agent": AgentType.PATENT_DATA_COLLECTION,
                "patent_search_agent": AgentType.PATENT_SEARCH,
                "patent_analysis_agent": AgentType.PATENT_ANALYSIS,
                "patent_report_agent": AgentType.PATENT_REPORT
            }
            
            agent_type = agent_type_mapping.get(failed_agent_id)
            if not agent_type:
                return None
            
            # 获取同类型的所有Agent
            agents = agent_registry.get_agents_by_type(agent_type)
            
            # 尝试其他健康的Agent
            for agent in agents:
                if agent.agent_id != failed_agent_id and agent.is_healthy():
                    self.logger.info(f"Trying alternative agent: {agent.agent_id}")
                    try:
                        response = await agent.process_request(request)
                        if response and response.confidence > 0.0:
                            # 标记这是替代Agent的响应
                            if not response.metadata:
                                response.metadata = {}
                            response.metadata.update({
                                "alternative_agent": True,
                                "original_agent": failed_agent_id,
                                "fallback_reason": "primary_agent_failed"
                            })
                            return response
                    except Exception as e:
                        self.logger.warning(f"Alternative agent {agent.agent_id} also failed: {str(e)}")
                        continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error trying alternative agents: {str(e)}")
            return None
    
    async def _create_simplified_response(self, agent_id: str, request: UserRequest) -> AgentResponse:
        """创建简化的响应（最后的降级策略）."""
        capabilities = self.patent_agent_capabilities.get(agent_id, ["通用处理"])
        
        # 基于Agent类型生成简化响应
        if "data_collection" in agent_id:
            content = self._generate_simplified_data_collection_response(request)
        elif "search" in agent_id:
            content = self._generate_simplified_search_response(request)
        elif "analysis" in agent_id:
            content = self._generate_simplified_analysis_response(request)
        elif "report" in agent_id:
            content = self._generate_simplified_report_response(request)
        else:
            content = f"已收到专利相关请求，但 {agent_id} 当前不可用。请稍后重试。"
        
        return AgentResponse(
            agent_id=agent_id,
            agent_type=AgentType.PATENT_COORDINATOR,
            response_content=content,
            confidence=0.4,  # 简化响应有一定置信度
            collaboration_needed=True,
            metadata={
                "simplified_response": True,
                "reason": "agent_unavailable_fallback",
                "capabilities": capabilities,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def _generate_simplified_data_collection_response(self, request: UserRequest) -> str:
        """生成简化的数据收集响应."""
        return """📊 **专利数据收集 - 简化响应**

⚠️ 专利数据收集Agent当前不可用，以下是基础处理结果：

**处理状态**: 已接收请求
**建议操作**: 
- 请稍后重试完整的数据收集功能
- 或手动访问专利数据库进行查询
- 联系技术支持获取帮助

**临时方案**: 可以使用公开的专利检索网站进行初步查询。"""
    
    def _generate_simplified_search_response(self, request: UserRequest) -> str:
        """生成简化的搜索响应."""
        return """🔍 **专利搜索 - 简化响应**

⚠️ 专利搜索Agent当前不可用，以下是基础处理结果：

**处理状态**: 已接收搜索请求
**建议操作**: 
- 请稍后重试完整的搜索功能
- 或使用CNKI、Google Patents等平台手动搜索
- 联系技术支持获取帮助

**临时方案**: 建议直接访问相关专利数据库进行查询。"""
    
    def _generate_simplified_analysis_response(self, request: UserRequest) -> str:
        """生成简化的分析响应."""
        return """📈 **专利分析 - 简化响应**

⚠️ 专利分析Agent当前不可用，以下是基础处理结果：

**处理状态**: 已接收分析请求
**建议操作**: 
- 请稍后重试完整的分析功能
- 或使用专业的专利分析工具
- 联系技术支持获取帮助

**临时方案**: 可以进行基础的专利统计和趋势观察。"""
    
    def _generate_simplified_report_response(self, request: UserRequest) -> str:
        """生成简化的报告响应."""
        return """📋 **专利报告 - 简化响应**

⚠️ 专利报告Agent当前不可用，以下是基础处理结果：

**处理状态**: 已接收报告请求
**建议操作**: 
- 请稍后重试完整的报告生成功能
- 或使用现有模板手动创建报告
- 联系技术支持获取帮助

**临时方案**: 可以导出基础数据进行手动报告制作。"""
    
    async def _call_patent_agent(self, agent_id: str, request: UserRequest) -> AgentResponse:
        """调用专利Agent（真实实现，通过AgentRegistry获取Agent实例）."""
        try:
            # 获取Agent注册器
            from ...agents.registry import agent_registry
            
            # 根据agent_id映射到实际的Agent类型和实例
            agent_type_mapping = {
                "patent_data_collection_agent": AgentType.PATENT_DATA_COLLECTION,
                "patent_search_agent": AgentType.PATENT_SEARCH,
                "patent_analysis_agent": AgentType.PATENT_ANALYSIS,
                "patent_report_agent": AgentType.PATENT_REPORT
            }
            
            agent_type = agent_type_mapping.get(agent_id)
            if not agent_type:
                self.logger.error(f"Unknown patent agent ID: {agent_id}")
                return self._create_error_response(agent_id, f"Unknown agent ID: {agent_id}")
            
            # 尝试获取Agent实例
            agents = agent_registry.get_agents_by_type(agent_type)
            if not agents:
                self.logger.warning(f"No agents found for type {agent_type.value}, creating fallback response")
                return self._create_fallback_response(agent_id, agent_type, request)
            
            # 使用第一个可用的Agent
            agent = agents[0]
            
            # 检查Agent状态
            if not agent.is_healthy():
                self.logger.warning(f"Agent {agent_id} is not healthy, attempting to use anyway")
            
            # 调用Agent处理请求
            self.logger.info(f"Calling real patent agent: {agent_id} (type: {agent_type.value})")
            response = await agent.process_request(request)
            
            # 验证响应
            if not response:
                return self._create_error_response(agent_id, "Agent returned empty response")
            
            # 增强响应元数据
            if not response.metadata:
                response.metadata = {}
            
            response.metadata.update({
                "called_by_coordinator": True,
                "coordinator_id": self.agent_id,
                "real_agent_call": True,
                "agent_type": agent_type.value,
                "call_timestamp": datetime.now().isoformat()
            })
            
            self.logger.info(f"Successfully called patent agent {agent_id}, confidence: {response.confidence}")
            return response
            
        except Exception as e:
            self.logger.error(f"Error calling patent agent {agent_id}: {str(e)}")
            return self._create_error_response(agent_id, str(e))
    
    def _create_error_response(self, agent_id: str, error_message: str) -> AgentResponse:
        """创建错误响应."""
        return AgentResponse(
            agent_id=agent_id,
            agent_type=AgentType.PATENT_COORDINATOR,
            response_content=f"调用 {agent_id} 时发生错误: {error_message}",
            confidence=0.0,
            collaboration_needed=False,
            metadata={
                "error": error_message,
                "error_type": "agent_call_failure",
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def _create_fallback_response(self, agent_id: str, agent_type: AgentType, request: UserRequest) -> AgentResponse:
        """创建降级响应（当真实Agent不可用时）."""
        capabilities = self.patent_agent_capabilities.get(agent_id, ["通用处理"])
        
        fallback_content = f"📋 **{agent_id} 降级响应**\n\n"
        fallback_content += f"**Agent类型**: {agent_type.value}\n"
        fallback_content += f"**处理能力**: {', '.join(capabilities)}\n"
        fallback_content += f"**请求内容**: {request.content[:100]}...\n\n"
        fallback_content += "⚠️ **注意**: 由于真实Agent不可用，这是一个降级响应。\n"
        fallback_content += "系统已记录此问题，请稍后重试或联系技术支持。\n\n"
        fallback_content += f"**建议**: 检查 {agent_type.value} 的注册状态和健康状况。"
        
        return AgentResponse(
            agent_id=agent_id,
            agent_type=agent_type,
            response_content=fallback_content,
            confidence=0.3,  # 降级响应的置信度较低
            collaboration_needed=True,  # 可能需要人工干预
            metadata={
                "fallback_response": True,
                "reason": "real_agent_unavailable",
                "agent_type": agent_type.value,
                "capabilities": capabilities,
                "timestamp": datetime.now().isoformat(),
                "shared_data": {
                    f"{agent_id}_status": "unavailable",
                    f"{agent_id}_fallback": True
                }
            }
        )
    
    def _integrate_sequential_patent_results(self, results: List[AgentResponse], 
                                           workflow_context: Dict[str, Any]) -> str:
        """整合顺序专利执行结果."""
        task_type = workflow_context.get("task_type", "comprehensive_analysis")
        
        result = f"🔬 **专利{self.patent_workflow_types.get(task_type, '分析')}完成** 🔬\n\n"
        result += f"**执行模式：** 顺序执行\n"
        result += f"**任务类型：** {task_type}\n\n"
        
        result += "**执行流程：**\n"
        for i, response in enumerate(results, 1):
            result += f"{i}. **{response.agent_id}**：{response.response_content[:100]}...\n"
        
        result += "\n**协调总结：**\n"
        result += "各阶段专利分析已按顺序完成，数据已在各Agent间有效传递和累积。"
        
        return result
    
    def _integrate_parallel_patent_results(self, results: List[AgentResponse], 
                                         workflow_context: Dict[str, Any]) -> str:
        """整合并行专利执行结果."""
        task_type = workflow_context.get("task_type", "comprehensive_analysis")
        
        result = f"🔬 **专利{self.patent_workflow_types.get(task_type, '分析')}完成** 🔬\n\n"
        result += f"**执行模式：** 并行执行\n"
        result += f"**任务类型：** {task_type}\n\n"
        
        result += "**并行处理结果：**\n"
        for response in results:
            result += f"• **{response.agent_id}**：{response.response_content[:100]}...\n"
        
        result += "\n**协调总结：**\n"
        result += "多个专利Agent并行处理，显著提升了分析效率，结果已整合完成。"
        
        return result
    
    def _integrate_hierarchical_patent_results(self, results: List[AgentResponse], 
                                             workflow_context: Dict[str, Any]) -> str:
        """整合分层专利执行结果."""
        task_type = workflow_context.get("task_type", "comprehensive_analysis")
        
        result = f"🔬 **专利{self.patent_workflow_types.get(task_type, '分析')}完成** 🔬\n\n"
        result += f"**执行模式：** 分层协调\n"
        result += f"**任务类型：** {task_type}\n\n"
        
        result += "**分层执行架构：**\n"
        result += "1. **数据层**：专利数据收集和搜索增强\n"
        result += "2. **分析层**：深度分析和模式识别\n"
        result += "3. **展示层**：报告生成和结果呈现\n\n"
        
        result += "**各层处理结果：**\n"
        for response in results:
            result += f"• **{response.agent_id}**：{response.response_content[:80]}...\n"
        
        result += "\n**协调总结：**\n"
        result += "采用分层架构确保了专利分析的系统性和完整性，各层协调有序。"
        
        return result
    
    def _integrate_hybrid_patent_results(self, results: List[AgentResponse], 
                                       workflow_context: Dict[str, Any]) -> str:
        """整合混合专利执行结果."""
        task_type = workflow_context.get("task_type", "comprehensive_analysis")
        
        result = f"🔬 **专利{self.patent_workflow_types.get(task_type, '分析')}完成** 🔬\n\n"
        result += f"**执行模式：** 混合执行\n"
        result += f"**任务类型：** {task_type}\n\n"
        
        result += "**混合执行策略：**\n"
        result += "• 数据收集和搜索：并行执行，提升效率\n"
        result += "• 分析和报告：顺序执行，确保质量\n\n"
        
        result += "**处理结果：**\n"
        for response in results:
            result += f"• **{response.agent_id}**：{response.response_content[:80]}...\n"
        
        result += "\n**协调总结：**\n"
        result += "混合执行策略兼顾了效率和质量，实现了最优的专利分析流程。"
        
        return result
    
    def _extract_shared_data_from_results(self, results: List[AgentResponse]) -> Dict[str, Any]:
        """从Agent结果中提取共享数据."""
        shared_data = {}
        
        for result in results:
            if hasattr(result, 'metadata') and result.metadata:
                shared_data.update(result.metadata.get("shared_data", {}))
        
        return shared_data
    
    async def _generate_patent_coordination_response(self, coordination_result: CollaborationResult,
                                                   workflow_context: Dict[str, Any]) -> str:
        """生成专利协调响应."""
        task_type = workflow_context.get("task_type", "comprehensive_analysis")
        execution_strategy = workflow_context.get("execution_strategy", "sequential")
        
        response = f"🤝 **专利分析协调完成** 🤝\n\n"
        response += f"**协调模式：** {execution_strategy.upper()}\n"
        response += f"**任务类型：** {self.patent_workflow_types.get(task_type, task_type)}\n"
        response += f"**参与Agent：** {', '.join(coordination_result.participating_agents)}\n"
        response += f"**协调ID：** {coordination_result.collaboration_id}\n\n"
        
        response += "**协调结果：**\n"
        response += coordination_result.final_result
        
        if coordination_result.consensus_reached:
            response += "\n\n✅ **协调状态：** 专利分析协调成功完成"
        else:
            response += "\n\n⚠️ **协调状态：** 部分Agent执行异常，需要人工检查"
        
        response += f"\n\n**解决方法：** {coordination_result.resolution_method}"
        
        # 添加专利分析特定的总结
        response += "\n\n**专利分析总结：**\n"
        response += "• 数据收集：✅ 完成\n"
        response += "• 搜索增强：✅ 完成\n" 
        response += "• 深度分析：✅ 完成\n"
        response += "• 报告生成：✅ 完成\n"
        
        return response
    
    def _generate_patent_coordination_actions(self, coordination_result: CollaborationResult,
                                            workflow_context: Dict[str, Any]) -> List[Action]:
        """生成专利协调相关的后续动作."""
        actions = []
        
        # 专利分析监控
        actions.append(
            Action(
                action_type="monitor_patent_analysis",
                parameters={
                    "coordination_id": coordination_result.collaboration_id,
                    "task_type": workflow_context.get("task_type"),
                    "check_interval": "30_minutes"
                },
                description="监控专利分析执行状态"
            )
        )
        
        # 结果质量验证
        actions.append(
            Action(
                action_type="validate_patent_results",
                parameters={
                    "validation_method": "cross_validation",
                    "quality_threshold": 0.8,
                    "timeline": "1_hour"
                },
                description="验证专利分析结果质量"
            )
        )
        
        # 如果未达成共识，添加专利分析修复动作
        if not coordination_result.consensus_reached:
            actions.append(
                Action(
                    action_type="repair_patent_analysis",
                    parameters={
                        "repair_strategy": "retry_failed_agents",
                        "max_retries": 2
                    },
                    description="修复失败的专利分析步骤"
                )
            )
        
        # 专利数据缓存
        actions.append(
            Action(
                action_type="cache_patent_data",
                parameters={
                    "cache_duration": "24_hours",
                    "cache_key": f"patent_analysis_{coordination_result.collaboration_id}"
                },
                description="缓存专利分析数据"
            )
        )
        
        return actions
    
    def _estimate_task_duration(self, task_type: str, complexity_level: str) -> int:
        """估算任务持续时间（秒）."""
        base_times = {
            "quick_search": 60,
            "trend_analysis": 120,
            "competitive_analysis": 180,
            "report_generation": 90,
            "comprehensive_analysis": 240
        }
        
        complexity_multipliers = {
            "low": 0.8,
            "medium": 1.0,
            "high": 1.5
        }
        
        base_time = base_times.get(task_type, 120)
        multiplier = complexity_multipliers.get(complexity_level, 1.0)
        
        return int(base_time * multiplier)
    
    # 专利协调Agent特有的管理方法
    def get_active_patent_tasks(self) -> Dict[str, Dict[str, Any]]:
        """获取当前活跃的专利任务."""
        return self.active_patent_tasks.copy()
    
    async def terminate_patent_task(self, workflow_id: str) -> bool:
        """终止指定的专利任务."""
        if workflow_id in self.active_patent_tasks:
            self.active_patent_tasks[workflow_id]["status"] = "terminated"
            self.active_patent_tasks[workflow_id]["end_time"] = datetime.now()
            self.logger.info(f"Terminated patent task {workflow_id}")
            return True
        return False
    
    def get_patent_task_statistics(self) -> Dict[str, Any]:
        """获取专利任务统计信息."""
        return {
            "active_tasks": len(self.active_patent_tasks),
            "supported_task_types": list(self.patent_workflow_types.keys()),
            "supported_strategies": list(self.execution_strategies.keys()),
            "agent_capabilities": self.patent_agent_capabilities,
            "last_updated": datetime.now().isoformat()
        }   
 
    async def _synchronize_agent_data(self, workflow_context: Dict[str, Any], 
                                    agent_results: List[AgentResponse]) -> Dict[str, Any]:
        """同步Agent间的数据状态."""
        try:
            synchronized_data = workflow_context.get("shared_data", {}).copy()
            
            # 收集所有Agent的共享数据
            for result in agent_results:
                if result.metadata and "shared_data" in result.metadata:
                    shared_data = result.metadata["shared_data"]
                    if isinstance(shared_data, dict):
                        synchronized_data.update(shared_data)
                
                # 提取关键信息用于后续Agent
                if result.confidence > 0.5:  # 只同步高质量的结果
                    agent_key = f"{result.agent_id}_result"
                    synchronized_data[agent_key] = {
                        "content": result.response_content[:500],  # 限制长度
                        "confidence": result.confidence,
                        "timestamp": datetime.now().isoformat(),
                        "metadata": result.metadata
                    }
            
            # 更新工作流上下文
            workflow_context["shared_data"] = synchronized_data
            
            # 记录同步状态
            sync_info = {
                "synchronized_at": datetime.now().isoformat(),
                "data_keys": list(synchronized_data.keys()),
                "agent_count": len(agent_results),
                "high_quality_results": len([r for r in agent_results if r.confidence > 0.5])
            }
            
            workflow_context["sync_info"] = sync_info
            
            self.logger.info(f"Synchronized data from {len(agent_results)} agents, "
                           f"{len(synchronized_data)} data keys")
            
            return synchronized_data
            
        except Exception as e:
            self.logger.error(f"Error synchronizing agent data: {str(e)}")
            return workflow_context.get("shared_data", {})
    
    async def _validate_agent_responses(self, agent_results: List[AgentResponse]) -> Dict[str, Any]:
        """验证Agent响应的一致性和质量."""
        validation_result = {
            "is_valid": True,
            "quality_score": 0.0,
            "consistency_score": 0.0,
            "issues": [],
            "recommendations": []
        }
        
        try:
            if not agent_results:
                validation_result["is_valid"] = False
                validation_result["issues"].append("No agent responses to validate")
                return validation_result
            
            # 质量评估
            confidences = [r.confidence for r in agent_results if r.confidence is not None]
            if confidences:
                validation_result["quality_score"] = sum(confidences) / len(confidences)
            
            # 一致性检查
            successful_responses = [r for r in agent_results if r.confidence > 0.3]
            if len(successful_responses) > 1:
                # 简单的一致性检查：检查是否有相似的关键词
                contents = [r.response_content.lower() for r in successful_responses]
                common_words = set()
                for content in contents:
                    words = set(content.split())
                    if not common_words:
                        common_words = words
                    else:
                        common_words &= words
                
                consistency_ratio = len(common_words) / max(len(content.split()) for content in contents)
                validation_result["consistency_score"] = min(consistency_ratio * 2, 1.0)  # 归一化
            
            # 生成问题和建议
            low_quality_count = len([r for r in agent_results if r.confidence < 0.3])
            if low_quality_count > 0:
                validation_result["issues"].append(f"{low_quality_count} agents returned low quality responses")
                validation_result["recommendations"].append("Consider retrying failed agents or adjusting parameters")
            
            failed_count = len([r for r in agent_results if r.confidence == 0.0])
            if failed_count > 0:
                validation_result["issues"].append(f"{failed_count} agents failed completely")
                validation_result["recommendations"].append("Check agent health and system resources")
            
            # 综合评估
            if validation_result["quality_score"] < 0.5:
                validation_result["is_valid"] = False
                validation_result["issues"].append("Overall quality score too low")
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Error validating agent responses: {str(e)}")
            validation_result["is_valid"] = False
            validation_result["issues"].append(f"Validation error: {str(e)}")
            return validation_result
    
    async def _handle_coordination_failure(self, workflow_context: Dict[str, Any], 
                                         error: Exception) -> CollaborationResult:
        """处理协调失败的情况."""
        workflow_id = workflow_context.get("workflow_id", "unknown")
        required_agents = workflow_context.get("required_agents", [])
        
        self.logger.error(f"Coordination failure in workflow {workflow_id}: {str(error)}")
        
        # 尝试恢复策略
        recovery_attempts = []
        
        # 恢复策略1：检查Agent健康状态
        try:
            from ...agents.registry import agent_registry
            unhealthy_agents = []
            
            for agent_id in required_agents:
                agent_type_mapping = {
                    "patent_data_collection_agent": AgentType.PATENT_DATA_COLLECTION,
                    "patent_search_agent": AgentType.PATENT_SEARCH,
                    "patent_analysis_agent": AgentType.PATENT_ANALYSIS,
                    "patent_report_agent": AgentType.PATENT_REPORT
                }
                
                agent_type = agent_type_mapping.get(agent_id)
                if agent_type:
                    agents = agent_registry.get_agents_by_type(agent_type)
                    if not agents or not any(agent.is_healthy() for agent in agents):
                        unhealthy_agents.append(agent_id)
            
            if unhealthy_agents:
                recovery_attempts.append(f"Detected unhealthy agents: {', '.join(unhealthy_agents)}")
            
        except Exception as e:
            recovery_attempts.append(f"Health check failed: {str(e)}")
        
        # 生成失败报告
        failure_report = f"""🚨 **专利协调失败报告** 🚨

**工作流ID**: {workflow_id}
**失败时间**: {datetime.now().isoformat()}
**错误信息**: {str(error)}

**涉及的Agent**: {', '.join(required_agents)}

**恢复尝试**:
{chr(10).join(f"- {attempt}" for attempt in recovery_attempts)}

**建议操作**:
- 检查Agent系统健康状态
- 验证专利系统初始化状态
- 重新提交请求
- 联系技术支持

**临时方案**: 可以尝试使用单个Agent进行部分处理，或手动执行相关任务。
"""
        
        return CollaborationResult(
            collaboration_id=workflow_id,
            participating_agents=required_agents + [self.agent_id],
            final_result=failure_report,
            consensus_reached=False,
            resolution_method="failure_handling",
            metadata={
                "failure": True,
                "error": str(error),
                "recovery_attempts": recovery_attempts,
                "failed_at": datetime.now().isoformat()
            }
        )
    
    # 结果整合方法
    def _integrate_sequential_patent_results(self, results: List[AgentResponse], 
                                           workflow_context: Dict[str, Any]) -> str:
        """整合顺序执行的专利分析结果."""
        try:
            successful_results = [r for r in results if r.confidence > 0.0]
            
            if not successful_results:
                return "❌ **专利分析失败**\n\n所有Agent都未能成功处理请求。请检查系统状态或稍后重试。"
            
            # 按Agent类型组织结果
            organized_results = {}
            for result in successful_results:
                agent_type = self._identify_agent_type_from_id(result.agent_id)
                organized_results[agent_type] = result.response_content
            
            # 生成综合报告
            report_sections = []
            
            if "data_collection" in organized_results:
                report_sections.append(f"## 📊 数据收集结果\n{organized_results['data_collection']}")
            
            if "search" in organized_results:
                report_sections.append(f"## 🔍 搜索增强结果\n{organized_results['search']}")
            
            if "analysis" in organized_results:
                report_sections.append(f"## 📈 分析处理结果\n{organized_results['analysis']}")
            
            if "report" in organized_results:
                report_sections.append(f"## 📋 报告生成结果\n{organized_results['report']}")
            
            # 添加执行摘要
            execution_summary = f"""# 🎯 专利分析执行摘要

**执行模式**: 顺序执行
**成功Agent数**: {len(successful_results)}/{len(results)}
**执行时间**: {workflow_context.get('start_time', 'Unknown')}
**工作流ID**: {workflow_context.get('workflow_id', 'Unknown')}

---

"""
            
            return execution_summary + "\n\n".join(report_sections)
            
        except Exception as e:
            self.logger.error(f"Error integrating sequential results: {str(e)}")
            return f"❌ **结果整合失败**: {str(e)}"
    
    def _integrate_parallel_patent_results(self, results: List[AgentResponse], 
                                         workflow_context: Dict[str, Any]) -> str:
        """整合并行执行的专利分析结果."""
        try:
            successful_results = [r for r in results if r.confidence > 0.0]
            
            if not successful_results:
                return "❌ **专利分析失败**\n\n所有Agent都未能成功处理请求。请检查系统状态或稍后重试。"
            
            # 按置信度排序
            successful_results.sort(key=lambda x: x.confidence, reverse=True)
            
            # 生成并行执行报告
            report_sections = []
            
            # 添加执行摘要
            avg_confidence = sum(r.confidence for r in successful_results) / len(successful_results)
            execution_summary = f"""# ⚡ 专利分析并行执行结果

**执行模式**: 并行执行
**成功Agent数**: {len(successful_results)}/{len(results)}
**平均置信度**: {avg_confidence:.2f}
**执行时间**: {workflow_context.get('start_time', 'Unknown')}
**工作流ID**: {workflow_context.get('workflow_id', 'Unknown')}

---

"""
            
            # 按置信度展示结果
            for i, result in enumerate(successful_results, 1):
                agent_type = self._identify_agent_type_from_id(result.agent_id)
                report_sections.append(f"""## {i}. {agent_type.upper()} (置信度: {result.confidence:.2f})

{result.response_content}

---
""")
            
            return execution_summary + "\n".join(report_sections)
            
        except Exception as e:
            self.logger.error(f"Error integrating parallel results: {str(e)}")
            return f"❌ **结果整合失败**: {str(e)}"
    
    def _integrate_hierarchical_patent_results(self, results: List[AgentResponse], 
                                             workflow_context: Dict[str, Any]) -> str:
        """整合分层执行的专利分析结果."""
        try:
            successful_results = [r for r in results if r.confidence > 0.0]
            
            if not successful_results:
                return "❌ **专利分析失败**\n\n所有Agent都未能成功处理请求。请检查系统状态或稍后重试。"
            
            # 按层级组织结果
            layers = {
                "data_layer": [],
                "analysis_layer": [],
                "report_layer": []
            }
            
            for result in successful_results:
                agent_type = self._identify_agent_type_from_id(result.agent_id)
                if agent_type in ["data_collection", "search"]:
                    layers["data_layer"].append(result)
                elif agent_type in ["analysis"]:
                    layers["analysis_layer"].append(result)
                elif agent_type in ["report"]:
                    layers["report_layer"].append(result)
            
            # 生成分层报告
            report_sections = []
            
            # 执行摘要
            execution_summary = f"""# 🏗️ 专利分析分层执行结果

**执行模式**: 分层执行
**成功Agent数**: {len(successful_results)}/{len(results)}
**执行层级**: {len([layer for layer in layers.values() if layer])}层
**工作流ID**: {workflow_context.get('workflow_id', 'Unknown')}

---

"""
            
            # 数据层结果
            if layers["data_layer"]:
                report_sections.append("## 📊 第一层：数据收集与搜索")
                for result in layers["data_layer"]:
                    agent_type = self._identify_agent_type_from_id(result.agent_id)
                    report_sections.append(f"### {agent_type.upper()}\n{result.response_content}\n")
            
            # 分析层结果
            if layers["analysis_layer"]:
                report_sections.append("## 📈 第二层：分析处理")
                for result in layers["analysis_layer"]:
                    report_sections.append(f"{result.response_content}\n")
            
            # 报告层结果
            if layers["report_layer"]:
                report_sections.append("## 📋 第三层：报告生成")
                for result in layers["report_layer"]:
                    report_sections.append(f"{result.response_content}\n")
            
            return execution_summary + "\n".join(report_sections)
            
        except Exception as e:
            self.logger.error(f"Error integrating hierarchical results: {str(e)}")
            return f"❌ **结果整合失败**: {str(e)}"
    
    def _integrate_hybrid_patent_results(self, results: List[AgentResponse], 
                                       workflow_context: Dict[str, Any]) -> str:
        """整合混合执行的专利分析结果."""
        try:
            successful_results = [r for r in results if r.confidence > 0.0]
            
            if not successful_results:
                return "❌ **专利分析失败**\n\n所有Agent都未能成功处理请求。请检查系统状态或稍后重试。"
            
            # 分组：并行执行的和顺序执行的
            parallel_results = []
            sequential_results = []
            
            for result in successful_results:
                agent_type = self._identify_agent_type_from_id(result.agent_id)
                if agent_type in ["data_collection", "search"]:
                    parallel_results.append(result)
                else:
                    sequential_results.append(result)
            
            # 生成混合执行报告
            report_sections = []
            
            # 执行摘要
            execution_summary = f"""# 🔄 专利分析混合执行结果

**执行模式**: 混合执行（并行+顺序）
**成功Agent数**: {len(successful_results)}/{len(results)}
**并行执行**: {len(parallel_results)}个Agent
**顺序执行**: {len(sequential_results)}个Agent
**工作流ID**: {workflow_context.get('workflow_id', 'Unknown')}

---

"""
            
            # 并行执行结果
            if parallel_results:
                report_sections.append("## ⚡ 并行执行阶段：数据收集与搜索")
                for result in parallel_results:
                    agent_type = self._identify_agent_type_from_id(result.agent_id)
                    report_sections.append(f"### {agent_type.upper()}\n{result.response_content}\n")
            
            # 顺序执行结果
            if sequential_results:
                report_sections.append("## 🔄 顺序执行阶段：分析与报告")
                for result in sequential_results:
                    agent_type = self._identify_agent_type_from_id(result.agent_id)
                    report_sections.append(f"### {agent_type.upper()}\n{result.response_content}\n")
            
            return execution_summary + "\n".join(report_sections)
            
        except Exception as e:
            self.logger.error(f"Error integrating hybrid results: {str(e)}")
            return f"❌ **结果整合失败**: {str(e)}"
    
    def _identify_agent_type_from_id(self, agent_id: str) -> str:
        """从Agent ID识别Agent类型."""
        if "data_collection" in agent_id:
            return "data_collection"
        elif "search" in agent_id:
            return "search"
        elif "analysis" in agent_id:
            return "analysis"
        elif "report" in agent_id:
            return "report"
        elif "coordinator" in agent_id:
            return "coordinator"
        else:
            return "unknown"
    
    def _extract_shared_data_from_results(self, results: List[AgentResponse]) -> Dict[str, Any]:
        """从Agent结果中提取共享数据."""
        shared_data = {}
        
        try:
            for result in results:
                if result.metadata and "shared_data" in result.metadata:
                    shared_data.update(result.metadata["shared_data"])
                
                # 从响应内容中提取结构化数据（如果有的话）
                if hasattr(result, 'structured_data'):
                    shared_data.update(result.structured_data)
            
            return shared_data
            
        except Exception as e:
            self.logger.error(f"Error extracting shared data: {str(e)}")
            return {}
    
    async def _synchronize_agent_data(self, workflow_context: Dict[str, Any], 
                                    results: List[AgentResponse]) -> None:
        """同步Agent间的数据."""
        try:
            # 提取共享数据
            shared_data = self._extract_shared_data_from_results(results)
            
            # 更新工作流上下文
            if "shared_data" not in workflow_context:
                workflow_context["shared_data"] = {}
            
            workflow_context["shared_data"].update(shared_data)
            
            # 记录同步信息
            self.logger.info(f"Synchronized {len(shared_data)} data items across agents")
            
        except Exception as e:
            self.logger.error(f"Error synchronizing agent data: {str(e)}")
    
    def _estimate_task_duration(self, task_type: str, complexity_level: str) -> int:
        """估算任务持续时间（秒）."""
        base_durations = {
            "quick_search": 30,
            "trend_analysis": 60,
            "competitive_analysis": 90,
            "report_generation": 120,
            "comprehensive_analysis": 180
        }
        
        complexity_multipliers = {
            "low": 0.8,
            "medium": 1.0,
            "high": 1.5
        }
        
        base_duration = base_durations.get(task_type, 60)
        multiplier = complexity_multipliers.get(complexity_level, 1.0)
        
        return int(base_duration * multiplier)
    
    async def _generate_patent_coordination_response(self, coordination_result: CollaborationResult,
                                                   workflow_context: Dict[str, Any]) -> str:
        """生成专利协调响应."""
        try:
            if not coordination_result.consensus_reached:
                return f"❌ **专利协调失败**\n\n{coordination_result.final_result}"
            
            # 生成成功的协调响应
            response_parts = []
            
            # 添加协调摘要
            response_parts.append(f"""# ✅ 专利分析协调完成

**协调ID**: {coordination_result.collaboration_id}
**执行策略**: {workflow_context.get('execution_strategy', 'Unknown')}
**参与Agent**: {len(coordination_result.participating_agents)}个
**任务类型**: {workflow_context.get('task_type', 'Unknown')}
**完成时间**: {datetime.now().isoformat()}

---
""")
            
            # 添加主要结果
            response_parts.append(coordination_result.final_result)
            
            # 添加Agent执行统计
            successful_agents = len([r for r in coordination_result.individual_responses if r.confidence > 0.0])
            response_parts.append(f"""

---

## 📊 执行统计

- **成功Agent**: {successful_agents}/{len(coordination_result.individual_responses)}
- **平均置信度**: {sum(r.confidence for r in coordination_result.individual_responses) / len(coordination_result.individual_responses):.2f}
- **解决方法**: {coordination_result.resolution_method}
""")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            self.logger.error(f"Error generating coordination response: {str(e)}")
            return f"❌ **响应生成失败**: {str(e)}"
    
    def _generate_patent_coordination_actions(self, coordination_result: CollaborationResult,
                                            workflow_context: Dict[str, Any]) -> List[Action]:
        """生成专利协调后续动作."""
        actions = []
        
        try:
            # 如果有报告生成，添加下载动作
            if any("report" in r.agent_id.lower() for r in coordination_result.individual_responses):
                actions.append(Action(
                    action_type="download_report",
                    description="下载专利分析报告",
                    parameters={
                        "coordination_id": coordination_result.collaboration_id,
                        "format": "pdf"
                    }
                ))
            
            # 如果分析成功，添加深度分析选项
            successful_analysis = any(
                "analysis" in r.agent_id.lower() and r.confidence > 0.5 
                for r in coordination_result.individual_responses
            )
            
            if successful_analysis:
                actions.append(Action(
                    action_type="deep_analysis",
                    description="进行更深度的专利分析",
                    parameters={
                        "base_coordination_id": coordination_result.collaboration_id
                    }
                ))
            
            # 添加重新执行选项
            actions.append(Action(
                action_type="retry_coordination",
                description="重新执行专利分析协调",
                parameters={
                    "original_context": workflow_context
                }
            ))
            
        except Exception as e:
            self.logger.error(f"Error generating coordination actions: {str(e)}")
        
        return actions
    
    async def _validate_config(self) -> bool:
        """验证专利协调Agent配置."""
        # 允许专利协调Agent类型
        if self.agent_type != AgentType.PATENT_COORDINATOR:
            self.logger.error(f"Invalid agent type for PatentCoordinatorAgent: {self.agent_type}")
            return False
        
        # 检查推荐的能力
        recommended_capabilities = ["专利工作流协调", "Agent调度", "结果整合"]
        if not any(cap in self.config.capabilities for cap in recommended_capabilities):
            self.logger.warning("PatentCoordinatorAgent missing recommended capabilities")
        
        return True