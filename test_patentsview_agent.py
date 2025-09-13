"""测试 PatentsView 搜索智能体."""

import asyncio
import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath('.'))

from src.multi_agent_service.patent.agents.patent_search import PatentsViewSearchAgent
from src.multi_agent_service.patent.models.requests import PatentAnalysisRequest
from src.multi_agent_service.models.config import AgentConfig
from src.multi_agent_service.models.enums import AgentType
from src.multi_agent_service.services.model_client import BaseModelClient


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class MockModelClient(BaseModelClient):
    """模拟模型客户端."""
    
    def __init__(self):
        """初始化模拟客户端."""
        # 创建一个模拟的配置
        from src.multi_agent_service.models.config import ModelConfig
        from src.multi_agent_service.models.enums import ModelProvider
        
        config = ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="gpt-3.5-turbo",
            api_key="test_key",
            base_url="https://api.openai.com/v1"
        )
        super().__init__(config)
    
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """生成模拟响应."""
        return f"Mock response for: {prompt[:100]}..."
    
    async def generate_structured_response(self, prompt: str, schema: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """生成结构化模拟响应."""
        return {"mock": "structured_response", "prompt_preview": prompt[:50]}
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """获取认证头."""
        return {"Authorization": "Bearer test_key"}
    
    def _prepare_request_data(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """准备请求数据."""
        return {
            "model": self.config.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature)
        }
    
    def _parse_response_data(self, response_data: Dict[str, Any]) -> str:
        """解析响应数据."""
        return response_data.get("choices", [{}])[0].get("message", {}).get("content", "Mock response")


async def test_patentsview_agent():
    """测试 PatentsView 搜索智能体."""
    
    logger.info("开始测试 PatentsView 搜索智能体")
    
    # 导入必要的配置类
    from src.multi_agent_service.models.config import ModelConfig
    from src.multi_agent_service.models.enums import ModelProvider
    
    # 创建模型配置
    llm_config = ModelConfig(
        provider=ModelProvider.OPENAI,
        model_name="gpt-3.5-turbo",
        api_key="test_key",
        base_url="https://api.openai.com/v1"
    )
    
    # 创建 Agent 配置
    config = AgentConfig(
        agent_id="patentsview_search_agent_001",
        agent_type=AgentType.PATENT_SEARCH,
        name="PatentsView搜索智能体",
        description="基于PatentsView API的专利搜索智能体",
        capabilities=["专利搜索", "数据检索", "API集成"],
        llm_config=llm_config,
        prompt_template="你是一个专利搜索智能体，专门处理基于PatentsView API的专利检索任务。",
        metadata={
            "patentsview_api": {
                "base_url": "https://search.patentsview.org/api/v1",
                "timeout": 30,
                "max_retries": 3,
                "rate_limit_delay": 1.0,
                "default_page_size": 100,
                "max_page_size": 1000
            }
        }
    )
    
    # 创建模拟模型客户端
    model_client = MockModelClient()
    
    # 创建 PatentsView 搜索智能体
    agent = PatentsViewSearchAgent(config, model_client)
    
    try:
        # 初始化 Agent
        logger.info("初始化 PatentsView 搜索智能体...")
        await agent.initialize()
        
        # 测试能力检查
        logger.info("测试能力检查...")
        capabilities = await agent.get_capabilities()
        logger.info(f"Agent 能力: {capabilities}")
        
        # 创建测试请求
        test_request = PatentAnalysisRequest(
            request_id="test_001",
            keywords=["artificial intelligence", "machine learning", "neural network"],
            analysis_types=["search", "comprehensive"],
            date_range={"start": "2020-01-01", "end": "2024-12-31"},
            countries=["US", "CN", "EP"],
            max_patents=100
        )
        
        # 测试请求处理能力
        logger.info("测试请求处理能力...")
        confidence = await agent.can_handle_request(test_request)
        logger.info(f"处理置信度: {confidence}")
        
        # 估算处理时间
        logger.info("估算处理时间...")
        estimated_time = await agent.estimate_processing_time(test_request)
        logger.info(f"估算处理时间: {estimated_time}秒")
        
        # 测试健康检查
        logger.info("测试健康检查...")
        health_status = await agent.health_check()
        logger.info(f"健康状态: {health_status}")
        
        # 获取指标
        logger.info("获取Agent指标...")
        metrics = agent.get_patent_metrics()
        logger.info(f"Agent指标: {metrics}")
        
        # 注意：实际的API调用需要有效的网络连接和可能的API密钥
        # 这里我们只测试Agent的基本功能，不进行实际的API调用
        logger.info("PatentsView 搜索智能体基本功能测试完成")
        
        # 如果需要测试实际的API调用，可以取消下面的注释
        # logger.info("开始实际API调用测试...")
        # response = await agent.process_request(test_request)
        # logger.info(f"API调用响应: {response.response_content}")
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {str(e)}")
        raise
    
    finally:
        # 清理资源
        logger.info("清理Agent资源...")
        await agent.cleanup()
        logger.info("PatentsView 搜索智能体测试完成")


async def test_patentsview_service():
    """测试 PatentsView 服务."""
    
    logger.info("开始测试 PatentsView 服务")
    
    try:
        from src.multi_agent_service.patent.services.patentsview_service import PatentsViewService
        
        # 创建服务实例
        service = PatentsViewService()
        
        # 测试查询构建
        logger.info("测试查询构建...")
        
        # 文本搜索查询
        text_query = service.build_text_search_query(
            keywords=["artificial intelligence", "machine learning"],
            search_fields=["patent_title", "patent_abstract"]
        )
        logger.info(f"文本搜索查询: {text_query}")
        
        # 日期范围查询
        date_query = service.build_date_range_query(
            start_date="2020-01-01",
            end_date="2024-12-31"
        )
        logger.info(f"日期范围查询: {date_query}")
        
        # 分类查询
        classification_query = service.build_classification_query(
            ipc_classes=["G06F", "G06N"],
            cpc_classes=["G06F15", "G06N3"]
        )
        logger.info(f"分类查询: {classification_query}")
        
        # 组合查询
        combined_query = service.combine_queries(text_query, date_query, classification_query)
        logger.info(f"组合查询: {combined_query}")
        
        logger.info("PatentsView 服务测试完成")
        
    except Exception as e:
        logger.error(f"服务测试过程中发生错误: {str(e)}")
        raise


async def test_patentsview_config():
    """测试 PatentsView 配置."""
    
    logger.info("开始测试 PatentsView 配置")
    
    try:
        from src.multi_agent_service.patent.config.patentsview_config import (
            PatentsViewAPIConfig,
            PatentsViewEndpoints,
            PatentsViewQueryBuilder
        )
        
        # 测试配置创建
        logger.info("测试配置创建...")
        config = PatentsViewAPIConfig.from_env()
        logger.info(f"API配置: {config.model_dump()}")
        
        # 测试端点配置
        logger.info("测试端点配置...")
        endpoints = PatentsViewEndpoints.get_all_endpoints()
        logger.info(f"可用端点数量: {len(endpoints)}")
        
        for name, endpoint in list(endpoints.items())[:5]:  # 只显示前5个
            logger.info(f"端点 {name}: {endpoint.path} - {endpoint.description}")
        
        # 测试查询构建器
        logger.info("测试查询构建器...")
        operators = PatentsViewQueryBuilder.OPERATORS
        logger.info(f"支持的操作符数量: {len(operators)}")
        
        templates = PatentsViewQueryBuilder.QUERY_TEMPLATES
        logger.info(f"查询模板数量: {len(templates)}")
        
        field_groups = PatentsViewQueryBuilder.FIELD_GROUPS
        logger.info(f"字段组数量: {len(field_groups)}")
        
        logger.info("PatentsView 配置测试完成")
        
    except Exception as e:
        logger.error(f"配置测试过程中发生错误: {str(e)}")
        raise


async def test_patentsview_models():
    """测试 PatentsView 数据模型."""
    
    logger.info("开始测试 PatentsView 数据模型")
    
    try:
        from src.multi_agent_service.patent.models.patentsview_data import (
            PatentRecord,
            PatentSummary,
            PatentClaim,
            AssigneeRecord,
            InventorRecord,
            CPCClass,
            IPCClass,
            PatentsViewSearchResult,
            PatentsViewAPIResponse
        )
        
        # 测试专利记录模型
        logger.info("测试专利记录模型...")
        patent = PatentRecord(
            patent_id="12345678",
            patent_number="US12345678B2",
            patent_title="Test Patent for AI Technology",
            patent_abstract="This is a test patent abstract for artificial intelligence technology.",
            patent_date="2024-01-15",
            patent_type="utility",
            assignee_organization="Test Company Inc.",
            assignee_country="US",
            inventor_name_first="John",
            inventor_name_last="Doe",
            ipc_class="G06F",
            cpc_class="G06F15/18"
        )
        logger.info(f"专利记录: {patent.patent_title}")
        
        # 测试专利摘要模型
        logger.info("测试专利摘要模型...")
        summary = PatentSummary(
            patent_id="12345678",
            summary_text="This patent describes an innovative AI system..."
        )
        logger.info(f"专利摘要: {summary.summary_text[:50]}...")
        
        # 测试权利要求模型
        logger.info("测试权利要求模型...")
        claim = PatentClaim(
            patent_id="12345678",
            claim_sequence=1,
            claim_text="A method for processing data using artificial intelligence..."
        )
        logger.info(f"权利要求: {claim.claim_text[:50]}...")
        
        # 测试搜索结果模型
        logger.info("测试搜索结果模型...")
        search_result = PatentsViewSearchResult(
            patents=[patent],
            patent_summaries=[summary],
            patent_claims=[claim],
            search_metadata={
                "keywords": ["artificial intelligence"],
                "search_time": datetime.now().isoformat()
            }
        )
        logger.info(f"搜索结果包含 {len(search_result.patents)} 个专利")
        
        logger.info("PatentsView 数据模型测试完成")
        
    except Exception as e:
        logger.error(f"数据模型测试过程中发生错误: {str(e)}")
        raise


async def main():
    """主测试函数."""
    
    logger.info("开始 PatentsView 集成测试")
    
    try:
        # 测试配置
        await test_patentsview_config()
        
        # 测试数据模型
        await test_patentsview_models()
        
        # 测试服务
        await test_patentsview_service()
        
        # 测试智能体
        await test_patentsview_agent()
        
        logger.info("所有测试完成！")
        
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())