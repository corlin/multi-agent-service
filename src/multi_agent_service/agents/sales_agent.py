"""Sales representative agent implementation."""

import re
from typing import Dict, List, Any
from datetime import datetime

from .base import BaseAgent
from ..models.base import UserRequest, AgentResponse, Action
from ..models.config import AgentConfig
from ..models.enums import AgentType
from ..services.model_client import BaseModelClient


class SalesAgent(BaseAgent):
    """销售代表智能体，专门处理销售相关的咨询和业务."""
    
    def __init__(self, config: AgentConfig, model_client: BaseModelClient):
        """初始化销售代表智能体."""
        super().__init__(config, model_client)
        
        # 销售相关的关键词
        self.sales_keywords = [
            "价格", "报价", "优惠", "折扣", "购买", "订购", "产品", "服务",
            "咨询", "了解", "介绍", "功能", "特点", "优势", "方案", "套餐",
            "政策", "促销", "活动", "费用", "成本", "投资", "预算", "性价比",
            "price", "quote", "discount", "buy", "purchase", "product", "service",
            "inquiry", "information", "feature", "advantage", "solution", "package",
            "policy", "promotion", "cost", "budget", "value"
        ]
        
        # 销售流程阶段
        self.sales_stages = [
            "需求识别", "产品介绍", "方案设计", "报价谈判", "合同签署", "售后服务"
        ]
        
        # 产品信息（示例数据）
        self.product_catalog = {
            "基础版": {
                "price": 999,
                "features": ["基础功能", "标准支持", "在线文档"],
                "description": "适合小型企业的基础解决方案"
            },
            "专业版": {
                "price": 2999,
                "features": ["高级功能", "优先支持", "定制培训", "API接入"],
                "description": "适合中型企业的专业解决方案"
            },
            "企业版": {
                "price": 9999,
                "features": ["全功能", "7x24支持", "专属客服", "定制开发", "私有部署"],
                "description": "适合大型企业的完整解决方案"
            }
        }
        
        # 常见问题和回答
        self.faq = {
            "价格": "我们提供三个版本：基础版999元、专业版2999元、企业版9999元，都有不同的功能和服务。",
            "试用": "我们提供30天免费试用，您可以充分体验产品功能。",
            "支持": "我们提供多层次技术支持，从在线文档到7x24专属客服。",
            "定制": "企业版支持定制开发，我们可以根据您的具体需求进行功能定制。"
        }
    
    async def can_handle_request(self, request: UserRequest) -> float:
        """判断是否能处理销售相关请求."""
        content = request.content.lower()
        
        # 检查销售关键词
        keyword_matches = sum(1 for keyword in self.sales_keywords if keyword in content)
        keyword_score = min(keyword_matches * 0.15, 0.6)
        
        # 检查问号（咨询性质）
        question_score = 0.1 if "?" in content or "？" in content else 0
        
        # 检查特定销售意图
        sales_patterns = [
            r"(价格|报价|多少钱|费用)",
            r"(购买|订购|下单)",
            r"(产品|服务).*?(介绍|了解|咨询)",
            r"(功能|特点|优势)",
            r"(方案|套餐|版本)",
            r"(了解|咨询).*?(产品|服务)",
            r"(推荐|建议).*?(方案|产品)",
            r"(优惠|折扣|促销).*?(政策|活动)",
            r"什么.*?(优惠|折扣|政策)",
            # English patterns
            r"(price|cost|pricing)",
            r"(buy|purchase|order)",
            r"(product|service).*?(information|introduction)",
            r"(feature|function|advantage)",
            r"(solution|package|plan)",
            r"(know|learn).*?(about|price|product)",
            r"(discount|promotion|offer)",
            r"what.*?(price|cost|discount)"
        ]
        
        pattern_score = 0
        for pattern in sales_patterns:
            if re.search(pattern, content):
                pattern_score += 0.2
        
        # 基础销售意图检查 - 更宽泛的匹配
        base_sales_score = 0
        chinese_sales_words = ["产品", "服务", "价格", "购买", "咨询", "了解", "介绍", "优惠"]
        english_sales_words = ["product", "service", "price", "buy", "purchase", "know", "information", "discount"]
        
        if any(word in content for word in chinese_sales_words + english_sales_words):
            base_sales_score = 0.4
        
        total_score = min(keyword_score + question_score + pattern_score + base_sales_score, 1.0)
        
        # 如果明确提到其他领域（技术支持、管理等），降低置信度
        other_domain_keywords = ["故障", "bug", "错误", "管理", "决策", "战略", "技术问题", "系统"]
        if any(keyword in content for keyword in other_domain_keywords):
            total_score *= 0.6
        
        return max(total_score, 0.0)
    
    async def get_capabilities(self) -> List[str]:
        """获取销售代表的能力列表."""
        return [
            "产品咨询",
            "价格报价", 
            "方案推荐",
            "优惠政策",
            "购买流程",
            "产品对比",
            "需求分析",
            "客户关系管理"
        ]
    
    async def estimate_processing_time(self, request: UserRequest) -> int:
        """估算处理时间."""
        content = request.content.lower()
        
        # 简单咨询：5-10秒
        if any(word in content for word in ["价格", "多少钱", "费用"]):
            return 5
        
        # 产品介绍：10-15秒
        if any(word in content for word in ["产品", "功能", "介绍"]):
            return 12
        
        # 方案设计：15-30秒
        if any(word in content for word in ["方案", "定制", "需求"]):
            return 25
        
        # 默认处理时间
        return 10
    
    async def _process_request_specific(self, request: UserRequest) -> AgentResponse:
        """处理销售相关的具体请求."""
        content = request.content
        
        # 分析请求类型
        request_type = self._analyze_request_type(content)
        
        # 根据请求类型生成响应
        if request_type == "价格咨询":
            response_content = await self._handle_price_inquiry(content)
        elif request_type == "产品介绍":
            response_content = await self._handle_product_introduction(content)
        elif request_type == "方案推荐":
            response_content = await self._handle_solution_recommendation(content)
        elif request_type == "购买流程":
            response_content = await self._handle_purchase_process(content)
        else:
            # 使用LLM生成通用销售响应
            response_content = await self._generate_llm_response(content)
        
        # 生成后续动作建议
        next_actions = self._generate_next_actions(request_type, content)
        
        # 判断是否需要协作
        collaboration_needed = self._needs_collaboration(content)
        
        return AgentResponse(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            response_content=response_content,
            confidence=0.9,
            next_actions=next_actions,
            collaboration_needed=collaboration_needed,
            metadata={
                "request_type": request_type,
                "sales_stage": self._identify_sales_stage(content),
                "processed_at": datetime.now().isoformat()
            }
        )
    
    def _analyze_request_type(self, content: str) -> str:
        """分析请求类型."""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ["价格", "报价", "多少钱", "费用", "price"]):
            return "价格咨询"
        elif any(word in content_lower for word in ["产品", "功能", "介绍", "了解", "product"]):
            return "产品介绍"
        elif any(word in content_lower for word in ["方案", "推荐", "建议", "solution"]):
            return "方案推荐"
        elif any(word in content_lower for word in ["购买", "订购", "下单", "buy", "purchase"]):
            return "购买流程"
        else:
            return "一般咨询"
    
    async def _handle_price_inquiry(self, content: str) -> str:
        """处理价格咨询."""
        response = "我们的产品定价如下：\n\n"
        
        for version, info in self.product_catalog.items():
            response += f"**{version}** - ¥{info['price']}\n"
            response += f"  {info['description']}\n"
            response += f"  主要功能：{', '.join(info['features'])}\n\n"
        
        response += "我们还提供30天免费试用，以及针对批量采购的优惠政策。"
        response += "您希望了解哪个版本的详细信息呢？"
        
        return response
    
    async def _handle_product_introduction(self, content: str) -> str:
        """处理产品介绍请求."""
        response = "我很高兴为您介绍我们的产品！\n\n"
        response += "我们提供三个版本的解决方案，每个版本都针对不同规模的企业需求：\n\n"
        
        for version, info in self.product_catalog.items():
            response += f"🔹 **{version}**\n"
            response += f"   {info['description']}\n"
            response += f"   核心功能：{', '.join(info['features'][:3])}\n\n"
        
        response += "所有版本都包含我们的核心技术和稳定的服务保障。"
        response += "您的企业规模大概是怎样的？我可以为您推荐最适合的版本。"
        
        return response
    
    async def _handle_solution_recommendation(self, content: str) -> str:
        """处理方案推荐请求."""
        response = "为了给您推荐最合适的解决方案，我需要了解一些信息：\n\n"
        response += "1. 您的企业规模（员工人数）\n"
        response += "2. 主要业务需求和使用场景\n"
        response += "3. 预算范围\n"
        response += "4. 是否需要定制功能\n\n"
        
        # 基于内容关键词给出初步建议
        content_lower = content.lower()
        if any(word in content_lower for word in ["小企业", "初创", "startup"]):
            response += "基于您提到的情况，我初步推荐**基础版**，它包含了核心功能，性价比很高。"
        elif any(word in content_lower for word in ["中型", "成长", "扩展"]):
            response += "基于您提到的情况，我推荐**专业版**，它提供了更多高级功能和优先支持。"
        elif any(word in content_lower for word in ["大型", "企业级", "定制"]):
            response += "基于您提到的情况，我推荐**企业版**，它提供全功能和专属服务。"
        else:
            response += "请告诉我更多详细信息，我会为您量身定制最合适的方案。"
        
        return response
    
    async def _handle_purchase_process(self, content: str) -> str:
        """处理购买流程咨询."""
        response = "购买流程非常简单，包含以下步骤：\n\n"
        response += "1. **需求确认** - 确定适合的产品版本\n"
        response += "2. **免费试用** - 30天全功能试用体验\n"
        response += "3. **商务洽谈** - 确定具体配置和价格\n"
        response += "4. **合同签署** - 签署正式服务合同\n"
        response += "5. **系统部署** - 技术团队协助部署配置\n"
        response += "6. **培训交付** - 提供使用培训和文档\n\n"
        response += "整个流程通常在1-2周内完成。您现在处于哪个阶段？我可以为您详细介绍下一步。"
        
        return response
    
    async def _generate_llm_response(self, content: str) -> str:
        """使用LLM生成通用销售响应."""
        # 构建销售专业的提示词
        system_prompt = """你是一位专业的销售代表，负责为客户提供产品咨询和销售服务。
        
你的特点：
- 热情友好，专业可靠
- 深入了解产品功能和优势
- 善于倾听客户需求并提供合适建议
- 能够清晰解释产品价值和解决方案

请根据客户的询问，提供专业、有帮助的回复。回复应该：
1. 直接回答客户问题
2. 突出产品价值和优势
3. 引导客户进入下一步销售流程
4. 保持友好专业的语调"""
        
        user_prompt = f"客户询问：{content}\n\n请提供专业的销售回复："
        
        try:
            # 这里应该调用实际的LLM API
            # 由于当前是基础框架实现，先返回模板响应
            response = f"感谢您的咨询！针对您提到的'{content[:50]}...'，我很乐意为您详细介绍。"
            response += "我们的产品在这方面有很好的解决方案。您方便留个联系方式吗？我可以为您安排详细的产品演示。"
            
            return response
            
        except Exception as e:
            self.logger.error(f"LLM response generation failed: {str(e)}")
            return "感谢您的咨询！我会尽快为您提供详细的产品信息。请问您希望了解哪方面的具体内容？"
    
    def _generate_next_actions(self, request_type: str, content: str) -> List[Action]:
        """生成后续动作建议."""
        actions = []
        
        if request_type == "价格咨询":
            actions.extend([
                Action(
                    action_type="schedule_demo",
                    parameters={"type": "product_demo"},
                    description="安排产品演示"
                ),
                Action(
                    action_type="send_quote",
                    parameters={"format": "detailed"},
                    description="发送详细报价单"
                )
            ])
        elif request_type == "产品介绍":
            actions.extend([
                Action(
                    action_type="provide_trial",
                    parameters={"duration": "30_days"},
                    description="提供免费试用"
                ),
                Action(
                    action_type="send_brochure",
                    parameters={"type": "product_catalog"},
                    description="发送产品手册"
                )
            ])
        elif request_type == "方案推荐":
            actions.extend([
                Action(
                    action_type="needs_assessment",
                    parameters={"method": "questionnaire"},
                    description="进行需求评估"
                ),
                Action(
                    action_type="custom_proposal",
                    parameters={"timeline": "3_days"},
                    description="制定定制方案"
                )
            ])
        
        # 通用后续动作
        actions.append(
            Action(
                action_type="follow_up",
                parameters={"schedule": "24_hours"},
                description="24小时内跟进"
            )
        )
        
        return actions
    
    def _needs_collaboration(self, content: str) -> bool:
        """判断是否需要与其他智能体协作."""
        content_lower = content.lower()
        
        # 需要技术支持协作的情况
        if any(word in content_lower for word in ["技术", "集成", "API", "部署", "配置"]):
            return True
        
        # 需要管理层决策的情况
        if any(word in content_lower for word in ["大额", "企业级", "定制开发", "长期合作"]):
            return True
        
        # 需要客服协作的情况
        if any(word in content_lower for word in ["问题", "投诉", "售后", "支持"]):
            return True
        
        return False
    
    def _identify_sales_stage(self, content: str) -> str:
        """识别当前销售阶段."""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ["了解", "介绍", "是什么"]):
            return "需求识别"
        elif any(word in content_lower for word in ["功能", "特点", "演示"]):
            return "产品介绍"
        elif any(word in content_lower for word in ["方案", "建议", "推荐"]):
            return "方案设计"
        elif any(word in content_lower for word in ["价格", "报价", "优惠"]):
            return "报价谈判"
        elif any(word in content_lower for word in ["购买", "签约", "合同"]):
            return "合同签署"
        elif any(word in content_lower for word in ["售后", "支持", "培训"]):
            return "售后服务"
        else:
            return "需求识别"
    
    async def _validate_config(self) -> bool:
        """验证销售智能体配置."""
        # 检查必要的配置项
        if self.agent_type != AgentType.SALES:
            self.logger.error(f"Invalid agent type for SalesAgent: {self.agent_type}")
            return False
        
        # 检查销售相关的能力配置
        required_capabilities = ["sales", "consultation", "pricing"]
        if not any(cap in self.config.capabilities for cap in required_capabilities):
            self.logger.warning("SalesAgent missing recommended capabilities")
        
        return True
    
    async def _initialize_specific(self) -> bool:
        """销售智能体特定的初始化."""
        self.logger.info("Initializing sales-specific components...")
        
        # 初始化销售数据
        self._load_sales_data()
        
        # 验证产品目录
        if not self.product_catalog:
            self.logger.warning("Product catalog is empty")
        
        self.logger.info("Sales agent initialization completed")
        return True
    
    def _load_sales_data(self):
        """加载销售相关数据."""
        # 这里可以从配置文件或数据库加载实际的产品数据
        # 当前使用硬编码的示例数据
        self.logger.info(f"Loaded {len(self.product_catalog)} products in catalog")
        self.logger.info(f"Loaded {len(self.faq)} FAQ entries")
    
    async def _health_check_specific(self) -> bool:
        """销售智能体特定的健康检查."""
        # 检查产品目录是否可用
        if not self.product_catalog:
            self.logger.error("Product catalog is not available")
            return False
        
        # 检查关键销售功能
        try:
            test_content = "产品价格咨询"
            confidence = await self.can_handle_request(
                UserRequest(content=test_content)
            )
            if confidence < 0.5:
                self.logger.error("Sales capability test failed")
                return False
        except Exception as e:
            self.logger.error(f"Sales health check failed: {str(e)}")
            return False
        
        return True