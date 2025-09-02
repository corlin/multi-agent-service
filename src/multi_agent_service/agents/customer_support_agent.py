"""Customer support agent implementation."""

import re
from typing import Dict, List, Any
from datetime import datetime

from .base import BaseAgent
from ..models.base import UserRequest, AgentResponse, Action
from ..models.config import AgentConfig
from ..models.enums import AgentType
from ..services.model_client import BaseModelClient


class CustomerSupportAgent(BaseAgent):
    """客服专员智能体，专门处理客户问题和技术支持."""
    
    def __init__(self, config: AgentConfig, model_client: BaseModelClient):
        """初始化客服专员智能体."""
        super().__init__(config, model_client)
        
        # 客服相关的关键词
        self.support_keywords = [
            "问题", "故障", "错误", "bug", "异常", "不能", "无法", "失败",
            "帮助", "支持", "解决", "修复", "处理", "咨询", "投诉", "建议",
            "登录", "注册", "密码", "账号", "权限", "访问", "连接", "网络",
            "problem", "issue", "error", "bug", "failure", "help", "support",
            "solve", "fix", "login", "register", "password", "account", "access"
        ]
        
        # 问题分类
        self.issue_categories = {
            "账户问题": ["登录", "注册", "密码", "账号", "权限"],
            "网络连接": ["网络连接", "网络", "连接", "超时", "慢", "卡顿", "断开"],
            "投诉建议": ["投诉", "建议", "意见", "反馈", "不满", "改进"],
            "功能咨询": ["如何", "怎么", "怎样", "操作", "设置"],
            "技术问题": ["bug", "错误", "故障", "异常", "不能", "无法", "失败", "系统"]
        }
        
        # 问题严重程度
        self.severity_levels = {
            "紧急": ["无法使用", "系统崩溃", "数据丢失", "安全问题"],
            "高": ["功能异常", "影响业务", "多人反馈"],
            "中": ["部分功能", "偶尔出现", "影响体验"],
            "低": ["建议", "咨询", "优化", "小问题"]
        }
        
        # 常见问题解决方案
        self.common_solutions = {
            "登录问题": {
                "steps": [
                    "1. 检查用户名和密码是否正确",
                    "2. 确认账号是否已激活",
                    "3. 清除浏览器缓存和Cookie",
                    "4. 尝试重置密码",
                    "5. 检查网络连接是否正常"
                ],
                "escalation": "如果以上步骤都无法解决，请联系技术支持"
            },
            "网络连接": {
                "steps": [
                    "1. 检查网络连接是否稳定",
                    "2. 尝试刷新页面或重新连接",
                    "3. 检查防火墙设置",
                    "4. 更换网络环境测试",
                    "5. 联系网络管理员"
                ],
                "escalation": "如果问题持续存在，请提供网络环境详细信息"
            },
            "功能异常": {
                "steps": [
                    "1. 确认操作步骤是否正确",
                    "2. 检查浏览器兼容性",
                    "3. 清除缓存后重试",
                    "4. 尝试使用其他浏览器",
                    "5. 记录错误信息和操作步骤"
                ],
                "escalation": "请提供详细的错误截图和操作步骤"
            }
        }
        
        # 客服回复模板
        self.response_templates = {
            "greeting": "您好！我是客服专员，很高兴为您服务。请详细描述您遇到的问题，我会尽快为您解决。",
            "acknowledgment": "感谢您的反馈，我已经收到您的问题描述。让我为您分析一下...",
            "solution_intro": "根据您描述的情况，我为您提供以下解决方案：",
            "escalation": "这个问题需要技术团队进一步处理，我会立即为您转接到相关部门。",
            "follow_up": "问题解决后，请告诉我是否还有其他需要帮助的地方。",
            "closing": "感谢您的耐心，如果还有其他问题，随时联系我们。"
        }
    
    async def can_handle_request(self, request: UserRequest) -> float:
        """判断是否能处理客服相关请求."""
        content = request.content.lower()
        
        # 检查客服关键词
        keyword_matches = sum(1 for keyword in self.support_keywords if keyword in content)
        keyword_score = min(keyword_matches * 0.15, 0.6)
        
        # 检查问号（求助性质）
        question_score = 0.15 if "?" in content or "？" in content else 0
        
        # 检查特定客服意图
        support_patterns = [
            r"(问题|故障|错误|bug)",
            r"(帮助|支持|解决)",
            r"(不能|无法|失败)",
            r"(如何|怎么|怎样).*?(操作|使用|设置)",
            r"(登录|注册|密码).*?(问题|失败)",
            r"(投诉|建议|反馈)",
            r"(网络|连接).*?(问题|异常)",
            # English patterns
            r"(problem|issue|error|bug)",
            r"(help|support|solve|fix)",
            r"(cannot|can't|unable|fail)",
            r"(how to|how can).*?(use|operate|set)",
            r"(login|register|password).*?(problem|issue)",
            r"(complaint|suggestion|feedback)"
        ]
        
        pattern_score = 0
        for pattern in support_patterns:
            if re.search(pattern, content):
                pattern_score += 0.2
        
        # 基础客服意图检查
        base_support_score = 0
        chinese_support_words = ["问题", "帮助", "支持", "故障", "错误", "不能", "如何", "投诉"]
        english_support_words = ["problem", "help", "support", "issue", "error", "cannot", "how", "complaint"]
        
        if any(word in content for word in chinese_support_words + english_support_words):
            base_support_score = 0.4
        
        total_score = min(keyword_score + question_score + pattern_score + base_support_score, 1.0)
        
        # 如果明确提到销售相关内容，降低置信度但不完全拒绝
        sales_keywords = ["价格", "购买", "产品介绍", "方案", "报价", "price", "buy", "purchase"]
        if any(keyword in content for keyword in sales_keywords):
            total_score *= 0.6
        
        # 确保至少有基础的处理能力，避免完全拒绝
        return max(total_score, 0.2)
    
    async def get_capabilities(self) -> List[str]:
        """获取客服专员的能力列表."""
        return [
            "问题诊断",
            "故障排除",
            "技术支持",
            "账户问题处理",
            "使用指导",
            "投诉处理",
            "建议收集",
            "问题升级"
        ]
    
    async def estimate_processing_time(self, request: UserRequest) -> int:
        """估算处理时间."""
        content = request.content.lower()
        
        # 简单咨询：5-10秒
        if any(word in content for word in ["如何", "怎么", "操作", "使用"]):
            return 8
        
        # 技术问题：15-30秒
        if any(word in content for word in ["故障", "错误", "bug", "异常"]):
            return 20
        
        # 投诉处理：20-40秒
        if any(word in content for word in ["投诉", "不满", "问题"]):
            return 30
        
        # 默认处理时间
        return 15
    
    async def _process_request_specific(self, request: UserRequest) -> AgentResponse:
        """处理客服相关的具体请求."""
        content = request.content
        
        # 分析问题类型和严重程度
        issue_category = self._categorize_issue(content)
        severity = self._assess_severity(content)
        
        # 检查是否为销售相关请求
        sales_keywords = ["价格", "购买", "产品介绍", "方案", "报价", "price", "buy", "purchase", "解决方案"]
        is_sales_related = any(keyword in content.lower() for keyword in sales_keywords)
        
        # 根据问题类型生成响应
        if is_sales_related:
            response_content = await self._handle_sales_inquiry(content)
        elif issue_category == "技术问题":
            response_content = await self._handle_technical_issue(content)
        elif issue_category == "账户问题":
            response_content = await self._handle_account_issue(content)
        elif issue_category == "功能咨询":
            response_content = await self._handle_usage_inquiry(content)
        elif issue_category == "投诉建议":
            response_content = await self._handle_complaint_suggestion(content)
        elif issue_category == "网络连接":
            response_content = await self._handle_network_issue(content)
        else:
            # 使用通用客服响应
            response_content = await self._generate_general_support_response(content)
        
        # 生成后续动作建议
        next_actions = self._generate_next_actions(issue_category, severity, content)
        
        # 判断是否需要升级
        needs_escalation = self._needs_escalation(content, severity)
        
        return AgentResponse(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            response_content=response_content,
            confidence=0.9,
            next_actions=next_actions,
            collaboration_needed=needs_escalation,
            metadata={
                "issue_category": issue_category,
                "severity": severity,
                "needs_escalation": needs_escalation,
                "processed_at": datetime.now().isoformat()
            }
        )
    
    def _categorize_issue(self, content: str) -> str:
        """分类问题类型."""
        content_lower = content.lower()
        
        # 按优先级检查，更具体的类别优先
        category_priority = [
            "账户问题", "网络连接", "投诉建议", "功能咨询", "技术问题"
        ]
        
        for category in category_priority:
            if category in self.issue_categories:
                keywords = self.issue_categories[category]
                if any(keyword in content_lower for keyword in keywords):
                    return category
        
        return "一般咨询"
    
    def _assess_severity(self, content: str) -> str:
        """评估问题严重程度."""
        content_lower = content.lower()
        
        for severity, keywords in self.severity_levels.items():
            if any(keyword in content_lower for keyword in keywords):
                return severity
        
        return "中"
    
    async def _handle_technical_issue(self, content: str) -> str:
        """处理技术问题."""
        response = self.response_templates["acknowledgment"] + "\n\n"
        response += "我看到您遇到了技术问题。为了更好地帮助您，请提供以下信息：\n\n"
        response += "1. 具体的错误信息或现象\n"
        response += "2. 出现问题的操作步骤\n"
        response += "3. 使用的浏览器和版本\n"
        response += "4. 问题出现的频率\n\n"
        
        # 提供通用解决方案
        if "功能异常" in self.common_solutions:
            solution = self.common_solutions["功能异常"]
            response += "同时，您可以先尝试以下解决步骤：\n"
            for step in solution["steps"]:
                response += f"  {step}\n"
            response += f"\n{solution['escalation']}"
        
        return response
    
    async def _handle_account_issue(self, content: str) -> str:
        """处理账户问题."""
        response = self.response_templates["acknowledgment"] + "\n\n"
        
        if any(word in content.lower() for word in ["登录", "login"]):
            response += "我来帮您解决登录问题：\n\n"
            if "登录问题" in self.common_solutions:
                solution = self.common_solutions["登录问题"]
                for step in solution["steps"]:
                    response += f"  {step}\n"
                response += f"\n{solution['escalation']}"
        else:
            response += "关于账户问题，我需要了解更多详情：\n\n"
            response += "1. 具体遇到什么问题？\n"
            response += "2. 错误提示信息是什么？\n"
            response += "3. 您的账户注册邮箱（用于验证身份）\n\n"
            response += "为了保护您的账户安全，我可能需要进行身份验证。"
        
        return response
    
    async def _handle_usage_inquiry(self, content: str) -> str:
        """处理使用咨询."""
        response = "我很乐意为您提供使用指导！\n\n"
        
        # 根据内容提供相应的指导
        if any(word in content.lower() for word in ["设置", "配置", "setting"]):
            response += "关于系统设置，您可以：\n"
            response += "1. 进入【设置】菜单\n"
            response += "2. 选择相应的配置项\n"
            response += "3. 根据需要调整参数\n"
            response += "4. 保存设置并测试效果\n\n"
        elif any(word in content.lower() for word in ["操作", "使用", "功能"]):
            response += "关于功能使用，建议您：\n"
            response += "1. 查看用户手册或帮助文档\n"
            response += "2. 观看操作演示视频\n"
            response += "3. 从基础功能开始熟悉\n"
            response += "4. 遇到问题及时联系客服\n\n"
        else:
            response += "请告诉我您具体想了解哪个功能的使用方法，我会为您详细说明。\n\n"
        
        response += "如果需要更详细的指导，我可以为您安排专门的培训或演示。"
        
        return response
    
    async def _handle_complaint_suggestion(self, content: str) -> str:
        """处理投诉和建议."""
        if any(word in content.lower() for word in ["投诉", "不满", "complaint"]):
            response = "非常抱歉给您带来了不好的体验。我会认真对待您的投诉。\n\n"
            response += "为了更好地处理您的投诉，请提供：\n"
            response += "1. 具体的问题描述\n"
            response += "2. 发生的时间和地点\n"
            response += "3. 相关的截图或证据\n"
            response += "4. 您希望的解决方案\n\n"
            response += "我会将您的投诉转交给相关部门，并在24小时内给您回复处理结果。"
        else:
            response = "感谢您的宝贵建议！我们非常重视用户的反馈。\n\n"
            response += "您的建议对我们改进产品和服务非常有价值。我会：\n"
            response += "1. 详细记录您的建议内容\n"
            response += "2. 转交给产品团队评估\n"
            response += "3. 跟进实施的可能性\n"
            response += "4. 及时反馈处理结果\n\n"
            response += "如果您还有其他建议或想法，欢迎随时告诉我们。"
        
        return response
    
    async def _handle_network_issue(self, content: str) -> str:
        """处理网络连接问题."""
        response = "我来帮您解决网络连接问题：\n\n"
        
        if "网络连接" in self.common_solutions:
            solution = self.common_solutions["网络连接"]
            response += "请按以下步骤排查：\n"
            for step in solution["steps"]:
                response += f"  {step}\n"
            response += f"\n{solution['escalation']}\n\n"
        
        response += "如果问题仍然存在，请提供：\n"
        response += "1. 网络环境（WiFi/有线/移动网络）\n"
        response += "2. 错误提示信息\n"
        response += "3. 其他设备是否正常\n"
        response += "4. 问题出现的时间规律"
        
        return response
    
    async def _handle_sales_inquiry(self, content: str) -> str:
        """处理销售相关咨询."""
        response = "感谢您对我们产品的关注！\n\n"
        response += "我是客服专员，虽然销售咨询不是我的主要专业领域，但我很乐意为您提供初步的帮助：\n\n"
        
        if any(word in content.lower() for word in ["价格", "报价", "price"]):
            response += "关于产品价格和报价，我建议您：\n"
            response += "1. 联系我们的专业销售团队获取详细报价\n"
            response += "2. 说明您的具体需求和使用场景\n"
            response += "3. 我们会为您提供个性化的解决方案\n\n"
        
        if any(word in content.lower() for word in ["功能", "特点", "解决方案"]):
            response += "关于产品功能和解决方案：\n"
            response += "1. 我们提供企业级AI服务平台\n"
            response += "2. 支持多种AI模型和应用场景\n"
            response += "3. 具备高可用性和安全性保障\n"
            response += "4. 提供完整的技术支持服务\n\n"
        
        response += "为了给您提供更专业和详细的信息，我建议将您转接给我们的销售专家。"
        response += "他们会根据您的具体需求提供最合适的解决方案和报价。\n\n"
        response += "如果您有任何技术问题或需要售后支持，我随时为您服务！"
        
        return response

    async def _generate_general_support_response(self, content: str) -> str:
        """生成通用客服响应."""
        response = self.response_templates["greeting"] + "\n\n"
        response += "我已经收到您的问题。为了更好地帮助您，请提供更多详细信息：\n\n"
        response += "1. 问题的具体描述\n"
        response += "2. 您想要达到的目标\n"
        response += "3. 已经尝试过的解决方法\n"
        response += "4. 问题的紧急程度\n\n"
        response += self.response_templates["follow_up"]
        
        return response
    
    def _generate_next_actions(self, issue_category: str, severity: str, content: str) -> List[Action]:
        """生成后续动作建议."""
        actions = []
        
        if issue_category == "技术问题":
            actions.extend([
                Action(
                    action_type="collect_logs",
                    parameters={"type": "error_logs"},
                    description="收集错误日志"
                ),
                Action(
                    action_type="remote_assistance",
                    parameters={"method": "screen_share"},
                    description="提供远程协助"
                )
            ])
        elif issue_category == "账户问题":
            actions.extend([
                Action(
                    action_type="verify_identity",
                    parameters={"method": "email_verification"},
                    description="验证用户身份"
                ),
                Action(
                    action_type="reset_credentials",
                    parameters={"type": "password_reset"},
                    description="重置登录凭据"
                )
            ])
        elif issue_category == "投诉建议":
            actions.extend([
                Action(
                    action_type="escalate_complaint",
                    parameters={"department": "quality_assurance"},
                    description="升级投诉处理"
                ),
                Action(
                    action_type="schedule_callback",
                    parameters={"timeframe": "24_hours"},
                    description="安排回访"
                )
            ])
        
        # 根据严重程度添加动作
        if severity in ["紧急", "高"]:
            actions.append(
                Action(
                    action_type="priority_escalation",
                    parameters={"priority": "high"},
                    description="优先级升级处理"
                )
            )
        
        # 通用后续动作
        actions.append(
            Action(
                action_type="follow_up",
                parameters={"schedule": "2_hours"},
                description="2小时内跟进"
            )
        )
        
        return actions
    
    def _needs_escalation(self, content: str, severity: str) -> bool:
        """判断是否需要升级处理."""
        content_lower = content.lower()
        
        # 高严重程度问题需要升级
        if severity in ["紧急", "高"]:
            return True
        
        # 技术复杂问题需要升级
        if any(word in content_lower for word in ["数据丢失", "安全", "系统崩溃", "无法访问"]):
            return True
        
        # 投诉需要升级
        if any(word in content_lower for word in ["投诉", "不满", "要求退款", "法律"]):
            return True
        
        # 需要其他部门协助
        if any(word in content_lower for word in ["技术支持", "销售", "财务", "法务"]):
            return True
        
        return False
    
    async def _validate_config(self) -> bool:
        """验证客服智能体配置."""
        # 检查必要的配置项
        if self.agent_type != AgentType.CUSTOMER_SUPPORT:
            self.logger.error(f"Invalid agent type for CustomerSupportAgent: {self.agent_type}")
            return False
        
        # 检查客服相关的能力配置
        required_capabilities = ["support", "customer_service", "problem_solving"]
        if not any(cap in self.config.capabilities for cap in required_capabilities):
            self.logger.warning("CustomerSupportAgent missing recommended capabilities")
        
        return True
    
    async def _initialize_specific(self) -> bool:
        """客服智能体特定的初始化."""
        self.logger.info("Initializing customer support specific components...")
        
        # 初始化客服数据
        self._load_support_data()
        
        # 验证解决方案库
        if not self.common_solutions:
            self.logger.warning("Common solutions library is empty")
        
        self.logger.info("Customer support agent initialization completed")
        return True
    
    def _load_support_data(self):
        """加载客服相关数据."""
        # 这里可以从配置文件或数据库加载实际的客服数据
        # 当前使用硬编码的示例数据
        self.logger.info(f"Loaded {len(self.common_solutions)} solution templates")
        self.logger.info(f"Loaded {len(self.issue_categories)} issue categories")
        self.logger.info(f"Loaded {len(self.response_templates)} response templates")
    
    async def _health_check_specific(self) -> bool:
        """客服智能体特定的健康检查."""
        # 检查解决方案库是否可用
        if not self.common_solutions:
            self.logger.error("Common solutions library is not available")
            return False
        
        # 检查关键客服功能
        try:
            test_content = "登录遇到问题"
            confidence = await self.can_handle_request(
                UserRequest(content=test_content)
            )
            if confidence < 0.3:
                self.logger.error("Customer support capability test failed")
                return False
        except Exception as e:
            self.logger.error(f"Customer support health check failed: {str(e)}")
            return False
        
        return True