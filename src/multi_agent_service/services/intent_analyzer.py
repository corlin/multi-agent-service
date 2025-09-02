"""Intent recognition and analysis service."""

import json
import logging
from typing import Dict, List, Optional, Any

from ..models.base import UserRequest, IntentResult, Entity
from ..models.enums import IntentType, AgentType
from ..services.model_client import BaseModelClient
from ..config.settings import settings

logger = logging.getLogger(__name__)


class IntentAnalyzer:
    """基于LLM的意图分析器."""
    
    def __init__(self, model_client: BaseModelClient):
        """初始化意图分析器.
        
        Args:
            model_client: 模型客户端实例
        """
        self.model_client = model_client
        self.settings = settings
        
        # 意图识别提示词模板
        self.intent_prompt_template = """
你是一个专业的意图识别系统。请分析用户的输入，识别其意图类型并提取相关实体。

可用的意图类型：
- sales_inquiry: 销售咨询（产品询价、功能介绍、购买咨询等）
- customer_support: 客户支持（问题报告、故障咨询、使用帮助等）
- technical_service: 技术服务（现场服务、维修指导、技术支持等）
- management_decision: 管理决策（数据分析、策略制定、资源配置等）
- general_inquiry: 一般咨询（公司信息、基本问题等）
- collaboration_required: 需要协作（复杂问题需要多个专业领域协作）

用户输入：{user_input}

请以JSON格式返回分析结果，包含以下字段：
{{
    "intent_type": "意图类型",
    "confidence": 0.95,
    "entities": [
        {{
            "name": "实体名称",
            "value": "实体值",
            "entity_type": "实体类型",
            "confidence": 0.9
        }}
    ],
    "suggested_agents": ["建议的智能体类型"],
    "requires_collaboration": false,
    "reasoning": "推理过程说明"
}}

智能体类型映射：
- sales_inquiry -> ["sales"]
- customer_support -> ["customer_support"]
- technical_service -> ["field_service"]
- management_decision -> ["manager"]
- general_inquiry -> ["customer_support"]
- collaboration_required -> ["coordinator"]
"""
        
        # 实体提取提示词模板
        self.entity_prompt_template = """
请从以下文本中提取关键实体信息：

文本：{text}

请识别以下类型的实体：
- PRODUCT: 产品名称
- SERVICE: 服务类型
- PERSON: 人名
- COMPANY: 公司名称
- DATE: 日期时间
- LOCATION: 地点
- PROBLEM: 问题描述
- FEATURE: 功能特性
- PRICE: 价格金额
- CONTACT: 联系方式

以JSON格式返回：
{{
    "entities": [
        {{
            "name": "实体名称",
            "value": "实体值",
            "entity_type": "实体类型",
            "confidence": 0.9
        }}
    ]
}}
"""

    async def analyze_intent(self, user_request: UserRequest) -> IntentResult:
        """分析用户请求的意图.
        
        Args:
            user_request: 用户请求对象
            
        Returns:
            IntentResult: 意图识别结果
        """
        try:
            logger.info(f"开始分析意图，请求ID: {user_request.request_id}")
            
            # 构建提示词
            prompt = self.intent_prompt_template.format(
                user_input=user_request.content
            )
            
            # 调用LLM进行意图识别
            from ..models.model_service import ModelRequest
            
            model_request = ModelRequest(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.1  # 使用较低温度确保一致性
            )
            
            model_response = await self.model_client.chat_completion(model_request)
            response = model_response.choices[0]["message"]["content"]
            
            # 解析响应
            result_data = self._parse_llm_response(response)
            
            # 创建意图结果对象
            intent_result = IntentResult(
                intent_type=IntentType(result_data.get("intent_type", "general_inquiry")),
                confidence=result_data.get("confidence", 0.5),
                entities=self._parse_entities(result_data.get("entities", [])),
                suggested_agents=self._parse_agent_types(result_data.get("suggested_agents", [])),
                requires_collaboration=result_data.get("requires_collaboration", False),
                reasoning=result_data.get("reasoning", "")
            )
            
            logger.info(f"意图识别完成: {intent_result.intent_type}, 置信度: {intent_result.confidence}")
            return intent_result
            
        except Exception as e:
            logger.error(f"意图识别失败: {str(e)}")
            # 返回默认结果
            return IntentResult(
                intent_type=IntentType.GENERAL_INQUIRY,
                confidence=0.1,
                entities=[],
                suggested_agents=[AgentType.CUSTOMER_SUPPORT],
                requires_collaboration=False,
                reasoning=f"意图识别失败，使用默认路由: {str(e)}"
            )

    async def extract_entities(self, text: str) -> List[Entity]:
        """从文本中提取实体.
        
        Args:
            text: 输入文本
            
        Returns:
            List[Entity]: 提取的实体列表
        """
        try:
            logger.debug(f"开始提取实体: {text[:100]}...")
            
            # 构建提示词
            prompt = self.entity_prompt_template.format(text=text)
            
            # 调用LLM进行实体提取
            from ..models.model_service import ModelRequest
            
            model_request = ModelRequest(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.1
            )
            
            model_response = await self.model_client.chat_completion(model_request)
            response = model_response.choices[0]["message"]["content"]
            
            # 解析响应
            result_data = self._parse_llm_response(response)
            entities = self._parse_entities(result_data.get("entities", []))
            
            logger.debug(f"提取到 {len(entities)} 个实体")
            return entities
            
        except Exception as e:
            logger.error(f"实体提取失败: {str(e)}")
            return []

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """解析LLM响应.
        
        Args:
            response: LLM响应文本
            
        Returns:
            Dict[str, Any]: 解析后的数据
        """
        try:
            # 尝试直接解析JSON
            return json.loads(response)
        except json.JSONDecodeError:
            # 如果直接解析失败，尝试提取JSON部分
            try:
                start_idx = response.find('{')
                end_idx = response.rfind('}') + 1
                if start_idx != -1 and end_idx > start_idx:
                    json_str = response[start_idx:end_idx]
                    return json.loads(json_str)
            except (json.JSONDecodeError, ValueError):
                pass
            
            logger.warning(f"无法解析LLM响应: {response}")
            return {}

    def _parse_entities(self, entities_data: List[Dict[str, Any]]) -> List[Entity]:
        """解析实体数据.
        
        Args:
            entities_data: 实体数据列表
            
        Returns:
            List[Entity]: 实体对象列表
        """
        entities = []
        for entity_data in entities_data:
            try:
                entity = Entity(
                    name=entity_data.get("name", ""),
                    value=entity_data.get("value", ""),
                    confidence=float(entity_data.get("confidence", 0.5)),
                    entity_type=entity_data.get("entity_type", "UNKNOWN")
                )
                entities.append(entity)
            except (ValueError, TypeError) as e:
                logger.warning(f"跳过无效实体数据: {entity_data}, 错误: {e}")
                continue
        
        return entities

    def _parse_agent_types(self, agent_types_data: List[str]) -> List[AgentType]:
        """解析智能体类型数据.
        
        Args:
            agent_types_data: 智能体类型字符串列表
            
        Returns:
            List[AgentType]: 智能体类型枚举列表
        """
        agent_types = []
        for agent_type_str in agent_types_data:
            try:
                agent_type = AgentType(agent_type_str)
                agent_types.append(agent_type)
            except ValueError:
                logger.warning(f"无效的智能体类型: {agent_type_str}")
                continue
        
        return agent_types

    def get_intent_rules(self) -> Dict[IntentType, Dict[str, Any]]:
        """获取意图路由规则配置.
        
        Returns:
            Dict[IntentType, Dict[str, Any]]: 意图路由规则
        """
        return {
            IntentType.SALES_INQUIRY: {
                "primary_agents": [AgentType.SALES],
                "fallback_agents": [AgentType.CUSTOMER_SUPPORT],
                "keywords": ["价格", "购买", "产品", "报价", "销售", "优惠"],
                "confidence_threshold": 0.7,
                "requires_collaboration": False
            },
            IntentType.CUSTOMER_SUPPORT: {
                "primary_agents": [AgentType.CUSTOMER_SUPPORT],
                "fallback_agents": [AgentType.FIELD_SERVICE],
                "keywords": ["问题", "帮助", "支持", "故障", "咨询"],
                "confidence_threshold": 0.7,
                "requires_collaboration": False
            },
            IntentType.TECHNICAL_SERVICE: {
                "primary_agents": [AgentType.FIELD_SERVICE],
                "fallback_agents": [AgentType.CUSTOMER_SUPPORT],
                "keywords": ["维修", "技术", "现场", "安装", "调试"],
                "confidence_threshold": 0.7,
                "requires_collaboration": False
            },
            IntentType.MANAGEMENT_DECISION: {
                "primary_agents": [AgentType.MANAGER],
                "fallback_agents": [AgentType.COORDINATOR],
                "keywords": ["决策", "管理", "策略", "分析", "规划"],
                "confidence_threshold": 0.8,
                "requires_collaboration": True
            },
            IntentType.GENERAL_INQUIRY: {
                "primary_agents": [AgentType.CUSTOMER_SUPPORT],
                "fallback_agents": [AgentType.SALES],
                "keywords": ["信息", "了解", "介绍", "什么是"],
                "confidence_threshold": 0.6,
                "requires_collaboration": False
            },
            IntentType.COLLABORATION_REQUIRED: {
                "primary_agents": [AgentType.COORDINATOR],
                "fallback_agents": [AgentType.CUSTOMER_SUPPORT],
                "keywords": ["复杂", "多个", "协作", "综合"],
                "confidence_threshold": 0.8,
                "requires_collaboration": True
            }
        }

    def validate_intent_result(self, intent_result: IntentResult) -> bool:
        """验证意图识别结果的有效性.
        
        Args:
            intent_result: 意图识别结果
            
        Returns:
            bool: 是否有效
        """
        # 检查置信度阈值
        rules = self.get_intent_rules()
        intent_rule = rules.get(intent_result.intent_type)
        
        if intent_rule:
            threshold = intent_rule.get("confidence_threshold", 0.5)
            if intent_result.confidence < threshold:
                logger.warning(f"意图置信度 {intent_result.confidence} 低于阈值 {threshold}")
                return False
        
        # 检查建议的智能体是否有效
        if not intent_result.suggested_agents:
            logger.warning("没有建议的智能体")
            return False
        
        return True