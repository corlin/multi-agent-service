"""Tests for intent analyzer service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

from src.multi_agent_service.services.intent_analyzer import IntentAnalyzer
from src.multi_agent_service.models.model_service import ModelResponse
from src.multi_agent_service.models.base import UserRequest, IntentResult, Entity
from src.multi_agent_service.models.enums import IntentType, AgentType, Priority, ModelProvider


class TestIntentAnalyzer:
    """意图分析器测试类."""
    
    def _create_mock_response(self, content: str, response_id: str = "test_response") -> ModelResponse:
        """创建模拟的模型响应."""
        return ModelResponse(
            id=response_id,
            created=1234567890,
            model="test_model",
            choices=[{"message": {"content": content}}],
            usage={"total_tokens": 100},
            provider=ModelProvider.QWEN,
            response_time=0.5
        )
    
    @pytest.fixture
    def mock_model_client(self):
        """模拟模型客户端."""
        client = AsyncMock()
        return client
    
    @pytest.fixture
    def intent_analyzer(self, mock_model_client):
        """创建意图分析器实例."""
        return IntentAnalyzer(mock_model_client)
    
    @pytest.fixture
    def sample_user_request(self):
        """示例用户请求."""
        return UserRequest(
            content="我想了解你们产品的价格，大概多少钱？",
            user_id="test_user_123",
            priority=Priority.NORMAL
        )
    
    @pytest.mark.asyncio
    async def test_analyze_intent_sales_inquiry(self, intent_analyzer, mock_model_client, sample_user_request):
        """测试销售咨询意图识别."""
        # 模拟LLM响应
        mock_response = json.dumps({
            "intent_type": "sales_inquiry",
            "confidence": 0.9,
            "entities": [
                {
                    "name": "产品",
                    "value": "产品",
                    "entity_type": "PRODUCT",
                    "confidence": 0.8
                },
                {
                    "name": "价格",
                    "value": "价格",
                    "entity_type": "PRICE",
                    "confidence": 0.9
                }
            ],
            "suggested_agents": ["sales"],
            "requires_collaboration": False,
            "reasoning": "用户询问产品价格，属于销售咨询"
        })
        
        mock_model_client.chat_completion.return_value = self._create_mock_response(mock_response)
        
        # 执行意图分析
        result = await intent_analyzer.analyze_intent(sample_user_request)
        
        # 验证结果
        assert isinstance(result, IntentResult)
        assert result.intent_type == IntentType.SALES_INQUIRY
        assert result.confidence == 0.9
        assert len(result.entities) == 2
        assert result.entities[0].name == "产品"
        assert result.entities[0].entity_type == "PRODUCT"
        assert AgentType.SALES in result.suggested_agents
        assert not result.requires_collaboration
        
        # 验证模型客户端调用
        mock_model_client.chat_completion.assert_called_once()
        call_args = mock_model_client.chat_completion.call_args
        # 检查传入的ModelRequest对象
        model_request = call_args[0][0]  # 第一个位置参数
        assert "价格" in model_request.messages[0]["content"]
    
    @pytest.mark.asyncio
    async def test_analyze_intent_customer_support(self, intent_analyzer, mock_model_client):
        """测试客户支持意图识别."""
        user_request = UserRequest(
            content="我的系统出现了故障，无法正常使用，请帮助解决",
            user_id="test_user_456"
        )
        
        mock_response = json.dumps({
            "intent_type": "customer_support",
            "confidence": 0.85,
            "entities": [
                {
                    "name": "系统故障",
                    "value": "系统故障",
                    "entity_type": "PROBLEM",
                    "confidence": 0.9
                }
            ],
            "suggested_agents": ["customer_support"],
            "requires_collaboration": False,
            "reasoning": "用户报告系统故障，需要客户支持"
        })
        
        mock_model_client.chat_completion.return_value = self._create_mock_response(mock_response, "customer_support_test")
        
        result = await intent_analyzer.analyze_intent(user_request)
        
        assert result.intent_type == IntentType.CUSTOMER_SUPPORT
        assert result.confidence == 0.85
        assert len(result.entities) == 1
        assert result.entities[0].entity_type == "PROBLEM"
        assert AgentType.CUSTOMER_SUPPORT in result.suggested_agents
    
    @pytest.mark.asyncio
    async def test_analyze_intent_collaboration_required(self, intent_analyzer, mock_model_client):
        """测试需要协作的复杂意图识别."""
        user_request = UserRequest(
            content="我需要一个综合的解决方案，包括产品选型、技术支持和售后服务，这是一个复杂的项目",
            user_id="test_user_789",
            priority=Priority.HIGH
        )
        
        mock_response = json.dumps({
            "intent_type": "collaboration_required",
            "confidence": 0.95,
            "entities": [
                {
                    "name": "综合解决方案",
                    "value": "综合解决方案",
                    "entity_type": "SERVICE",
                    "confidence": 0.9
                },
                {
                    "name": "产品选型",
                    "value": "产品选型",
                    "entity_type": "PRODUCT",
                    "confidence": 0.8
                },
                {
                    "name": "技术支持",
                    "value": "技术支持",
                    "entity_type": "SERVICE",
                    "confidence": 0.85
                }
            ],
            "suggested_agents": ["coordinator"],
            "requires_collaboration": True,
            "reasoning": "复杂项目需要多个专业领域协作"
        })
        
        mock_model_client.chat_completion.return_value = self._create_mock_response(mock_response, "collaboration_test")
        
        result = await intent_analyzer.analyze_intent(user_request)
        
        assert result.intent_type == IntentType.COLLABORATION_REQUIRED
        assert result.confidence == 0.95
        assert len(result.entities) == 3
        assert result.requires_collaboration
        assert AgentType.COORDINATOR in result.suggested_agents
    
    @pytest.mark.asyncio
    async def test_analyze_intent_llm_failure(self, intent_analyzer, mock_model_client):
        """测试LLM调用失败的情况."""
        user_request = UserRequest(content="测试请求")
        
        # 模拟LLM调用失败
        mock_model_client.chat_completion.side_effect = Exception("API调用失败")
        
        result = await intent_analyzer.analyze_intent(user_request)
        
        # 应该返回默认结果
        assert result.intent_type == IntentType.GENERAL_INQUIRY
        assert result.confidence == 0.1
        assert AgentType.CUSTOMER_SUPPORT in result.suggested_agents
        assert not result.requires_collaboration
        assert "意图识别失败" in result.reasoning
    
    @pytest.mark.asyncio
    async def test_extract_entities(self, intent_analyzer, mock_model_client):
        """测试实体提取功能."""
        text = "我想购买iPhone 15，价格是多少？联系电话：13800138000"
        
        mock_response = json.dumps({
            "entities": [
                {
                    "name": "iPhone 15",
                    "value": "iPhone 15",
                    "entity_type": "PRODUCT",
                    "confidence": 0.95
                },
                {
                    "name": "价格",
                    "value": "价格",
                    "entity_type": "PRICE",
                    "confidence": 0.8
                },
                {
                    "name": "13800138000",
                    "value": "13800138000",
                    "entity_type": "CONTACT",
                    "confidence": 0.9
                }
            ]
        })
        
        mock_model_client.chat_completion.return_value = self._create_mock_response(mock_response, "entity_extraction_test")
        
        entities = await intent_analyzer.extract_entities(text)
        
        assert len(entities) == 3
        assert entities[0].name == "iPhone 15"
        assert entities[0].entity_type == "PRODUCT"
        assert entities[1].entity_type == "PRICE"
        assert entities[2].entity_type == "CONTACT"
    
    @pytest.mark.asyncio
    async def test_extract_entities_failure(self, intent_analyzer, mock_model_client):
        """测试实体提取失败的情况."""
        text = "测试文本"
        
        # 模拟调用失败
        mock_model_client.chat_completion.side_effect = Exception("提取失败")
        
        entities = await intent_analyzer.extract_entities(text)
        
        # 应该返回空列表
        assert entities == []
    
    def test_parse_llm_response_valid_json(self, intent_analyzer):
        """测试解析有效JSON响应."""
        response = '{"intent_type": "sales_inquiry", "confidence": 0.9}'
        result = intent_analyzer._parse_llm_response(response)
        
        assert result["intent_type"] == "sales_inquiry"
        assert result["confidence"] == 0.9
    
    def test_parse_llm_response_embedded_json(self, intent_analyzer):
        """测试解析嵌入在文本中的JSON."""
        response = '这是一些前置文本 {"intent_type": "sales_inquiry", "confidence": 0.9} 这是一些后置文本'
        result = intent_analyzer._parse_llm_response(response)
        
        assert result["intent_type"] == "sales_inquiry"
        assert result["confidence"] == 0.9
    
    def test_parse_llm_response_invalid_json(self, intent_analyzer):
        """测试解析无效JSON响应."""
        response = "这不是有效的JSON"
        result = intent_analyzer._parse_llm_response(response)
        
        assert result == {}
    
    def test_parse_entities_valid_data(self, intent_analyzer):
        """测试解析有效实体数据."""
        entities_data = [
            {
                "name": "产品A",
                "value": "产品A",
                "entity_type": "PRODUCT",
                "confidence": 0.9
            },
            {
                "name": "价格",
                "value": "1000元",
                "entity_type": "PRICE",
                "confidence": 0.8
            }
        ]
        
        entities = intent_analyzer._parse_entities(entities_data)
        
        assert len(entities) == 2
        assert entities[0].name == "产品A"
        assert entities[0].entity_type == "PRODUCT"
        assert entities[0].confidence == 0.9
    
    def test_parse_entities_invalid_data(self, intent_analyzer):
        """测试解析无效实体数据."""
        entities_data = [
            {
                "name": "产品A",
                "value": "产品A",
                "entity_type": "PRODUCT",
                "confidence": 0.9
            },
            {
                "name": "无效实体",
                # 缺少必要字段
                "confidence": "无效置信度"  # 无效类型
            }
        ]
        
        entities = intent_analyzer._parse_entities(entities_data)
        
        # 应该只返回有效的实体
        assert len(entities) == 1
        assert entities[0].name == "产品A"
    
    def test_parse_agent_types_valid_data(self, intent_analyzer):
        """测试解析有效智能体类型数据."""
        agent_types_data = ["sales", "customer_support", "manager"]
        
        agent_types = intent_analyzer._parse_agent_types(agent_types_data)
        
        assert len(agent_types) == 3
        assert AgentType.SALES in agent_types
        assert AgentType.CUSTOMER_SUPPORT in agent_types
        assert AgentType.MANAGER in agent_types
    
    def test_parse_agent_types_invalid_data(self, intent_analyzer):
        """测试解析无效智能体类型数据."""
        agent_types_data = ["sales", "invalid_agent", "customer_support"]
        
        agent_types = intent_analyzer._parse_agent_types(agent_types_data)
        
        # 应该只返回有效的智能体类型
        assert len(agent_types) == 2
        assert AgentType.SALES in agent_types
        assert AgentType.CUSTOMER_SUPPORT in agent_types
    
    def test_get_intent_rules(self, intent_analyzer):
        """测试获取意图路由规则."""
        rules = intent_analyzer.get_intent_rules()
        
        assert isinstance(rules, dict)
        assert IntentType.SALES_INQUIRY in rules
        assert IntentType.CUSTOMER_SUPPORT in rules
        
        # 检查销售咨询规则
        sales_rule = rules[IntentType.SALES_INQUIRY]
        assert AgentType.SALES in sales_rule["primary_agents"]
        assert "keywords" in sales_rule
        assert "confidence_threshold" in sales_rule
    
    def test_validate_intent_result_valid(self, intent_analyzer):
        """测试验证有效的意图识别结果."""
        intent_result = IntentResult(
            intent_type=IntentType.SALES_INQUIRY,
            confidence=0.8,
            entities=[],
            suggested_agents=[AgentType.SALES],
            requires_collaboration=False
        )
        
        is_valid = intent_analyzer.validate_intent_result(intent_result)
        assert is_valid
    
    def test_validate_intent_result_low_confidence(self, intent_analyzer):
        """测试验证低置信度的意图识别结果."""
        intent_result = IntentResult(
            intent_type=IntentType.SALES_INQUIRY,
            confidence=0.5,  # 低于阈值0.7
            entities=[],
            suggested_agents=[AgentType.SALES],
            requires_collaboration=False
        )
        
        is_valid = intent_analyzer.validate_intent_result(intent_result)
        assert not is_valid
    
    def test_validate_intent_result_no_agents(self, intent_analyzer):
        """测试验证没有建议智能体的意图识别结果."""
        intent_result = IntentResult(
            intent_type=IntentType.SALES_INQUIRY,
            confidence=0.8,
            entities=[],
            suggested_agents=[],  # 没有建议的智能体
            requires_collaboration=False
        )
        
        is_valid = intent_analyzer.validate_intent_result(intent_result)
        assert not is_valid
    
    @pytest.mark.asyncio
    async def test_analyze_intent_with_context(self, intent_analyzer, mock_model_client):
        """测试带上下文的意图分析."""
        user_request = UserRequest(
            content="继续之前的讨论",
            context={
                "previous_intent": "sales_inquiry",
                "conversation_history": ["用户询问了产品价格"]
            }
        )
        
        mock_response = json.dumps({
            "intent_type": "sales_inquiry",
            "confidence": 0.8,
            "entities": [],
            "suggested_agents": ["sales"],
            "requires_collaboration": False,
            "reasoning": "基于上下文继续销售咨询"
        })
        
        mock_model_client.chat_completion.return_value = self._create_mock_response(mock_response, "context_test")
        
        result = await intent_analyzer.analyze_intent(user_request)
        
        assert result.intent_type == IntentType.SALES_INQUIRY
        assert result.confidence == 0.8
    
    def test_intent_rules_completeness(self, intent_analyzer):
        """测试意图规则的完整性."""
        rules = intent_analyzer.get_intent_rules()
        
        # 确保所有意图类型都有对应的规则
        for intent_type in IntentType:
            assert intent_type in rules, f"缺少意图类型 {intent_type} 的规则"
            
            rule = rules[intent_type]
            assert "primary_agents" in rule
            assert "fallback_agents" in rule
            assert "keywords" in rule
            assert "confidence_threshold" in rule
            assert isinstance(rule["primary_agents"], list)
            assert isinstance(rule["fallback_agents"], list)
            assert isinstance(rule["keywords"], list)
            assert isinstance(rule["confidence_threshold"], (int, float))