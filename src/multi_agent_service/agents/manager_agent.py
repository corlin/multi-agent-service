"""Manager agent implementation."""

import re
from typing import Dict, List, Any
from datetime import datetime

from .base import BaseAgent
from ..models.base import UserRequest, AgentResponse, Action
from ..models.config import AgentConfig
from ..models.enums import AgentType
from ..services.model_client import BaseModelClient


class ManagerAgent(BaseAgent):
    """管理者智能体，专门处理管理决策和战略规划."""
    
    def __init__(self, config: AgentConfig, model_client: BaseModelClient):
        """初始化管理者智能体."""
        super().__init__(config, model_client)
        
        # 管理相关的关键词
        self.management_keywords = [
            "决策", "战略", "规划", "管理", "领导", "策略", "方向", "目标",
            "预算", "资源", "团队", "组织", "流程", "政策", "制度", "标准",
            "绩效", "考核", "评估", "分析", "报告", "数据", "指标", "KPI",
            "decision", "strategy", "planning", "management", "leadership",
            "budget", "resource", "team", "organization", "policy", "performance"
        ]
        
        # 管理领域分类
        self.management_areas = {
            "战略规划": ["战略", "规划", "方向", "目标", "愿景", "使命"],
            "资源管理": ["预算", "资源", "分配", "优化", "成本", "投资"],
            "团队管理": ["团队", "人员", "组织", "领导", "激励", "培训"],
            "流程管理": ["流程", "制度", "政策", "标准", "规范", "优化"],
            "绩效管理": ["绩效", "考核", "评估", "指标", "KPI", "目标"],
            "风险管理": ["风险", "控制", "合规", "安全", "审计", "监督"]
        }
        
        # 决策类型
        self.decision_types = {
            "战略决策": ["长期", "战略", "方向性", "重大", "全局"],
            "运营决策": ["日常", "运营", "执行", "操作", "具体"],
            "投资决策": ["投资", "预算", "采购", "资金", "财务"],
            "人事决策": ["招聘", "晋升", "调动", "培训", "薪酬"]
        }
        
        # 管理工具和方法
        self.management_tools = {
            "SWOT分析": {
                "description": "分析优势、劣势、机会、威胁",
                "use_case": "战略规划和决策制定"
            },
            "PDCA循环": {
                "description": "计划-执行-检查-改进循环",
                "use_case": "流程改进和质量管理"
            },
            "OKR目标管理": {
                "description": "目标与关键结果管理法",
                "use_case": "目标设定和绩效管理"
            },
            "平衡计分卡": {
                "description": "多维度绩效评估工具",
                "use_case": "绩效评估和战略执行"
            }
        }
        
        # 管理建议模板
        self.advice_templates = {
            "strategic": "基于当前情况分析，建议采用以下战略方向：",
            "operational": "针对运营效率提升，建议实施以下措施：",
            "financial": "从财务管理角度，建议考虑以下方案：",
            "hr": "关于人力资源管理，建议采取以下行动：",
            "risk": "风险控制方面，建议建立以下机制："
        }
    
    async def can_handle_request(self, request: UserRequest) -> float:
        """判断是否能处理管理相关请求."""
        content = request.content.lower()
        
        # 检查管理关键词
        keyword_matches = sum(1 for keyword in self.management_keywords if keyword in content)
        keyword_score = min(keyword_matches * 0.15, 0.6)
        
        # 检查管理意图模式
        management_patterns = [
            r"(决策|战略|规划|管理)",
            r"(如何|怎么|怎样).*?(管理|领导|决策)",
            r"(制定|建立|设计).*?(策略|制度|流程)",
            r"(分析|评估|考核).*?(绩效|团队|业务)",
            r"(预算|资源|成本).*?(分配|控制|优化)",
            # English patterns
            r"(strategy|planning|management|decision)",
            r"(how to|how can).*?(manage|lead|decide)",
            r"(develop|establish|design).*?(strategy|policy|process)",
            r"(analyze|evaluate|assess).*?(performance|team|business)"
        ]
        
        pattern_score = 0
        for pattern in management_patterns:
            if re.search(pattern, content):
                pattern_score += 0.2
        
        # 基础管理意图检查
        base_management_score = 0
        chinese_mgmt_words = ["管理", "决策", "战略", "规划", "领导", "团队", "绩效", "预算"]
        english_mgmt_words = ["management", "decision", "strategy", "planning", "leadership", "team", "budget"]
        
        if any(word in content for word in chinese_mgmt_words + english_mgmt_words):
            base_management_score = 0.4
        
        total_score = min(keyword_score + pattern_score + base_management_score, 1.0)
        
        # 如果明确提到技术或客服问题，降低置信度
        other_domain_keywords = ["技术问题", "bug", "故障", "登录", "密码", "客服"]
        if any(keyword in content for keyword in other_domain_keywords):
            total_score *= 0.5
        
        return max(total_score, 0.0)
    
    async def get_capabilities(self) -> List[str]:
        """获取管理者的能力列表."""
        return [
            "战略规划",
            "决策分析",
            "资源配置",
            "团队管理",
            "绩效评估",
            "流程优化",
            "风险控制",
            "政策制定"
        ]
    
    async def estimate_processing_time(self, request: UserRequest) -> int:
        """估算处理时间."""
        content = request.content.lower()
        
        # 简单管理咨询：10-15秒
        if any(word in content for word in ["如何", "怎么", "建议"]):
            return 12
        
        # 战略规划：20-30秒
        if any(word in content for word in ["战略", "规划", "方向"]):
            return 25
        
        # 复杂决策分析：30-45秒
        if any(word in content for word in ["分析", "评估", "决策"]):
            return 35
        
        # 默认处理时间
        return 18
    
    async def _process_request_specific(self, request: UserRequest) -> AgentResponse:
        """处理管理相关的具体请求."""
        content = request.content
        
        # 分析管理领域和决策类型
        management_area = self._identify_management_area(content)
        decision_type = self._identify_decision_type(content)
        
        # 根据管理领域生成响应
        if management_area == "战略规划":
            response_content = await self._handle_strategic_planning(content)
        elif management_area == "资源管理":
            response_content = await self._handle_resource_management(content)
        elif management_area == "团队管理":
            response_content = await self._handle_team_management(content)
        elif management_area == "流程管理":
            response_content = await self._handle_process_management(content)
        elif management_area == "绩效管理":
            response_content = await self._handle_performance_management(content)
        elif management_area == "风险管理":
            response_content = await self._handle_risk_management(content)
        else:
            # 使用通用管理建议
            response_content = await self._generate_general_management_advice(content)
        
        # 生成后续动作建议
        next_actions = self._generate_next_actions(management_area, decision_type, content)
        
        # 判断是否需要协作
        needs_collaboration = self._needs_collaboration(content, management_area)
        
        return AgentResponse(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            response_content=response_content,
            confidence=0.9,
            next_actions=next_actions,
            collaboration_needed=needs_collaboration,
            metadata={
                "management_area": management_area,
                "decision_type": decision_type,
                "needs_collaboration": needs_collaboration,
                "processed_at": datetime.now().isoformat()
            }
        )
    
    def _identify_management_area(self, content: str) -> str:
        """识别管理领域."""
        content_lower = content.lower()
        
        for area, keywords in self.management_areas.items():
            if any(keyword in content_lower for keyword in keywords):
                return area
        
        return "综合管理"
    
    def _identify_decision_type(self, content: str) -> str:
        """识别决策类型."""
        content_lower = content.lower()
        
        for decision_type, keywords in self.decision_types.items():
            if any(keyword in content_lower for keyword in keywords):
                return decision_type
        
        return "一般决策"
    
    async def _handle_strategic_planning(self, content: str) -> str:
        """处理战略规划请求."""
        response = "关于战略规划，我建议采用系统性的方法：\n\n"
        response += "**战略分析框架：**\n"
        response += "1. **环境分析** - 分析外部市场环境和内部资源能力\n"
        response += "2. **SWOT分析** - 识别优势、劣势、机会和威胁\n"
        response += "3. **目标设定** - 制定明确、可衡量的战略目标\n"
        response += "4. **策略制定** - 设计实现目标的具体策略\n"
        response += "5. **执行计划** - 制定详细的实施路线图\n\n"
        
        response += "**关键考虑因素：**\n"
        response += "• 市场趋势和竞争态势\n"
        response += "• 组织核心竞争力\n"
        response += "• 资源配置和能力建设\n"
        response += "• 风险评估和应对措施\n\n"
        
        response += "建议定期回顾和调整战略，确保与市场变化保持同步。"
        
        return response
    
    async def _handle_resource_management(self, content: str) -> str:
        """处理资源管理请求."""
        response = "资源管理的核心是实现资源的最优配置：\n\n"
        response += "**资源管理原则：**\n"
        response += "1. **需求分析** - 准确评估各部门资源需求\n"
        response += "2. **优先级排序** - 根据战略重要性确定资源分配优先级\n"
        response += "3. **效率最大化** - 追求资源利用效率的最大化\n"
        response += "4. **动态调整** - 根据执行情况灵活调整资源配置\n\n"
        
        response += "**预算管理建议：**\n"
        response += "• 建立详细的预算编制流程\n"
        response += "• 实施预算执行监控机制\n"
        response += "• 定期进行成本效益分析\n"
        response += "• 建立应急资源储备\n\n"
        
        response += "建议采用零基预算法，从零开始重新评估每项支出的必要性。"
        
        return response
    
    async def _handle_team_management(self, content: str) -> str:
        """处理团队管理请求."""
        response = "有效的团队管理需要关注以下几个方面：\n\n"
        response += "**团队建设要素：**\n"
        response += "1. **明确目标** - 确保团队成员理解共同目标\n"
        response += "2. **角色分工** - 合理分配任务和职责\n"
        response += "3. **沟通机制** - 建立有效的内部沟通渠道\n"
        response += "4. **激励体系** - 设计合理的激励和认可机制\n"
        response += "5. **能力发展** - 持续提升团队成员能力\n\n"
        
        response += "**领导力建议：**\n"
        response += "• 以身作则，树立良好榜样\n"
        response += "• 倾听团队成员的意见和建议\n"
        response += "• 提供必要的支持和资源\n"
        response += "• 及时给予反馈和指导\n\n"
        
        response += "建议定期进行团队建设活动，增强团队凝聚力。"
        
        return response
    
    async def _handle_performance_management(self, content: str) -> str:
        """处理绩效管理请求."""
        response = "绩效管理是提升组织效能的重要工具：\n\n"
        response += "**绩效管理循环：**\n"
        response += "1. **目标设定** - 制定SMART目标\n"
        response += "2. **过程监控** - 定期跟踪执行进度\n"
        response += "3. **绩效评估** - 客观评价工作成果\n"
        response += "4. **反馈改进** - 提供建设性反馈\n"
        response += "5. **发展规划** - 制定能力提升计划\n\n"
        
        response += "**关键绩效指标(KPI)设计：**\n"
        response += "• 与战略目标紧密关联\n"
        response += "• 可量化和可衡量\n"
        response += "• 具有挑战性但可实现\n"
        response += "• 定期回顾和调整\n\n"
        
        response += "建议采用OKR(目标与关键结果)方法，提高目标管理的透明度和执行力。"
        
        return response
    
    async def _handle_process_management(self, content: str) -> str:
        """处理流程管理请求."""
        response = "流程管理的目标是提高运营效率和质量：\n\n"
        response += "**流程优化步骤：**\n"
        response += "1. **现状分析** - 梳理现有流程和问题点\n"
        response += "2. **流程设计** - 重新设计优化的流程\n"
        response += "3. **标准制定** - 建立流程执行标准\n"
        response += "4. **培训实施** - 培训相关人员\n"
        response += "5. **持续改进** - 定期评估和优化\n\n"
        
        response += "**流程管理原则：**\n"
        response += "• 以客户价值为导向\n"
        response += "• 消除不必要的环节\n"
        response += "• 标准化和规范化\n"
        response += "• 数字化和自动化\n\n"
        
        response += "建议采用PDCA循环方法，持续改进流程效率。"
        
        return response
    
    async def _handle_risk_management(self, content: str) -> str:
        """处理风险管理请求."""
        response = "风险管理是保障组织稳健发展的重要保障：\n\n"
        response += "**风险管理流程：**\n"
        response += "1. **风险识别** - 全面识别潜在风险\n"
        response += "2. **风险评估** - 评估风险概率和影响\n"
        response += "3. **风险应对** - 制定风险应对策略\n"
        response += "4. **监控预警** - 建立风险监控机制\n"
        response += "5. **应急响应** - 制定应急处理预案\n\n"
        
        response += "**风险应对策略：**\n"
        response += "• **规避** - 避免高风险活动\n"
        response += "• **缓解** - 降低风险发生概率\n"
        response += "• **转移** - 通过保险等方式转移风险\n"
        response += "• **接受** - 接受低影响风险\n\n"
        
        response += "建议建立风险管理委员会，定期评估和更新风险清单。"
        
        return response
    
    async def _generate_general_management_advice(self, content: str) -> str:
        """生成通用管理建议."""
        response = "作为管理者，我建议从以下几个维度来思考这个问题：\n\n"
        response += "**管理决策框架：**\n"
        response += "1. **问题分析** - 深入了解问题的本质和根因\n"
        response += "2. **方案设计** - 制定多个可行的解决方案\n"
        response += "3. **影响评估** - 评估各方案的影响和风险\n"
        response += "4. **决策执行** - 选择最优方案并制定执行计划\n"
        response += "5. **效果跟踪** - 监控执行效果并及时调整\n\n"
        
        response += "**管理要点提醒：**\n"
        response += "• 保持数据驱动的决策方式\n"
        response += "• 充分考虑利益相关者的需求\n"
        response += "• 平衡短期效益和长期发展\n"
        response += "• 建立有效的沟通和反馈机制\n\n"
        
        response += "如需更具体的建议，请提供更多背景信息和具体需求。"
        
        return response
    
    def _generate_next_actions(self, management_area: str, decision_type: str, content: str) -> List[Action]:
        """生成后续动作建议."""
        actions = []
        
        if management_area == "战略规划":
            actions.extend([
                Action(
                    action_type="conduct_swot_analysis",
                    parameters={"scope": "organizational"},
                    description="进行SWOT分析"
                ),
                Action(
                    action_type="stakeholder_consultation",
                    parameters={"method": "workshop"},
                    description="组织利益相关者研讨"
                )
            ])
        elif management_area == "团队管理":
            actions.extend([
                Action(
                    action_type="team_assessment",
                    parameters={"type": "capability_matrix"},
                    description="进行团队能力评估"
                ),
                Action(
                    action_type="development_plan",
                    parameters={"focus": "skill_enhancement"},
                    description="制定能力发展计划"
                )
            ])
        elif management_area == "绩效管理":
            actions.extend([
                Action(
                    action_type="kpi_review",
                    parameters={"frequency": "quarterly"},
                    description="定期KPI回顾"
                ),
                Action(
                    action_type="performance_coaching",
                    parameters={"method": "one_on_one"},
                    description="提供绩效辅导"
                )
            ])
        
        # 根据决策类型添加动作
        if decision_type in ["战略决策", "投资决策"]:
            actions.append(
                Action(
                    action_type="executive_approval",
                    parameters={"level": "senior_management"},
                    description="高层管理审批"
                )
            )
        
        # 通用后续动作
        actions.append(
            Action(
                action_type="follow_up_review",
                parameters={"schedule": "1_week"},
                description="一周后跟进回顾"
            )
        )
        
        return actions
    
    def _needs_collaboration(self, content: str, management_area: str) -> bool:
        """判断是否需要与其他智能体协作."""
        content_lower = content.lower()
        
        # 涉及销售策略需要销售团队协作
        if any(word in content_lower for word in ["销售策略", "市场推广", "客户关系"]):
            return True
        
        # 涉及技术决策需要技术团队协作
        if any(word in content_lower for word in ["技术选型", "系统架构", "IT规划"]):
            return True
        
        # 涉及客户服务需要客服团队协作
        if any(word in content_lower for word in ["客户满意度", "服务质量", "客户体验"]):
            return True
        
        # 重大战略决策需要多方协作
        if management_area == "战略规划" and any(word in content_lower for word in ["重大", "全面", "整体"]):
            return True
        
        return False
    
    async def _validate_config(self) -> bool:
        """验证管理者智能体配置."""
        if self.agent_type != AgentType.MANAGER:
            self.logger.error(f"Invalid agent type for ManagerAgent: {self.agent_type}")
            return False
        
        required_capabilities = ["management", "decision_making", "strategic_planning"]
        if not any(cap in self.config.capabilities for cap in required_capabilities):
            self.logger.warning("ManagerAgent missing recommended capabilities")
        
        return True
    
    async def _initialize_specific(self) -> bool:
        """管理者智能体特定的初始化."""
        self.logger.info("Initializing management specific components...")
        
        # 初始化管理工具和方法
        self._load_management_tools()
        
        self.logger.info("Manager agent initialization completed")
        return True
    
    def _load_management_tools(self):
        """加载管理工具和方法."""
        self.logger.info(f"Loaded {len(self.management_tools)} management tools")
        self.logger.info(f"Loaded {len(self.management_areas)} management areas")
    
    async def _health_check_specific(self) -> bool:
        """管理者智能体特定的健康检查."""
        try:
            test_content = "如何制定战略规划"
            confidence = await self.can_handle_request(
                UserRequest(content=test_content)
            )
            if confidence < 0.3:
                self.logger.error("Management capability test failed")
                return False
        except Exception as e:
            self.logger.error(f"Management health check failed: {str(e)}")
            return False
        
        return True