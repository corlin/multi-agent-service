#!/usr/bin/env python3
"""测试更新后的专利数据收集代理."""

import asyncio
import logging
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath('.'))

from src.multi_agent_service.agents.patent.data_collection_agent import PatentDataCollectionAgent
from src.multi_agent_service.models.base import UserRequest
from src.multi_agent_service.models.config import AgentConfig, ModelConfig
from src.multi_agent_service.models.enums import AgentType, ModelProvider
from src.multi_agent_service.services.model_client import BaseModelClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockModelClient(BaseModelClient):
    """模拟模型客户端."""
    
    def __init__(self, config):
        """初始化模拟客户端."""
        super().__init__(config)
    
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """生成模拟响应."""
        return "这是一个模拟的AI响应，用于测试专利数据收集代理。"
    
    async def initialize(self):
        """初始化客户端."""
        pass
    
    async def cleanup(self):
        """清理客户端."""
        pass
    
    def _get_auth_headers(self) -> dict:
        """获取认证头."""
        return {}
    
    def _parse_response_data(self, response_data: dict) -> str:
        """解析响应数据."""
        return str(response_data)
    
    def _prepare_request_data(self, prompt: str, **kwargs) -> dict:
        """准备请求数据."""
        return {"prompt": prompt, **kwargs}


async def test_data_collection_agent():
    """测试专利数据收集代理."""
    
    logger.info("开始测试更新后的专利数据收集代理")
    
    try:
        # 创建模型配置
        model_config = ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="gpt-3.5-turbo",
            api_key="test-key",
            base_url="https://api.openai.com/v1",
            temperature=0.7,
            max_tokens=2000
        )
        
        # 创建代理配置
        agent_config = AgentConfig(
            agent_id="patent_data_collection_agent_001",
            agent_type=AgentType.PATENT_DATA_COLLECTION,
            name="专利数据收集代理",
            description="基于PatentsView API的专利数据收集代理",
            capabilities=["专利数据收集", "PatentsView API集成", "数据清洗"],
            llm_config=model_config,
            prompt_template="你是一个专利数据收集代理，专门处理基于PatentsView API的专利数据收集任务。",
            metadata={
                "patentsview_api": {
                    "base_url": "https://search.patentsview.org/api/v1",
                    "timeout": 30,
                    "max_retries": 3
                }
            }
        )
        
        # 创建模型客户端
        model_client = MockModelClient(model_config)
        
        # 创建专利数据收集代理
        agent = PatentDataCollectionAgent(agent_config, model_client)
        
        # 初始化代理
        logger.info("初始化专利数据收集代理...")
        await agent.initialize()
        
        # 测试1: 检查代理能力
        logger.info("测试1: 检查代理能力")
        capabilities = await agent.get_capabilities()
        logger.info(f"代理能力: {capabilities}")
        
        # 测试2: 测试请求处理能力判断
        logger.info("测试2: 测试请求处理能力判断")
        
        test_requests = [
            "收集关于人工智能的专利数据",
            "获取机器学习相关的专利信息",
            "从PatentsView采集区块链技术专利",
            "下载2020-2023年的5G通信专利",
            "这是一个不相关的请求"
        ]
        
        for request_text in test_requests:
            request = UserRequest(
                user_id="test_user",
                content=request_text,
                request_type="patent_collection"
            )
            
            confidence = await agent.can_handle_request(request)
            logger.info(f"请求: '{request_text}' - 处理信心度: {confidence:.2f}")
        
        # 测试3: 测试数据收集请求处理
        logger.info("测试3: 测试数据收集请求处理")
        
        collection_request = UserRequest(
            user_id="test_user",
            content="收集关于人工智能和机器学习的专利数据，限制100件，时间范围2020-2023年",
            request_type="patent_collection"
        )
        
        logger.info("处理数据收集请求...")
        response = await agent.process_request(collection_request)
        
        logger.info(f"响应信心度: {response.confidence}")
        logger.info(f"响应内容预览: {response.response_content[:500]}...")
        logger.info(f"后续动作数量: {len(response.next_actions) if response.next_actions else 0}")
        logger.info(f"需要协作: {response.collaboration_needed}")
        
        if response.metadata:
            logger.info(f"元数据: {response.metadata}")
        
        # 测试4: 测试处理时间估算
        logger.info("测试4: 测试处理时间估算")
        
        time_requests = [
            "收集少量专利数据",
            "获取100件专利信息",
            "批量下载1000件专利数据"
        ]
        
        for request_text in time_requests:
            request = UserRequest(
                user_id="test_user",
                content=request_text,
                request_type="patent_collection"
            )
            
            estimated_time = await agent.estimate_processing_time(request)
            logger.info(f"请求: '{request_text}' - 估算处理时间: {estimated_time}秒")
        
        logger.info("专利数据收集代理测试完成")
        
        # 清理资源
        logger.info("清理代理资源...")
        await agent.cleanup()
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {str(e)}", exc_info=True)
        return False
    
    return True


async def main():
    """主函数."""
    
    logger.info("开始专利数据收集代理测试")
    
    success = await test_data_collection_agent()
    
    if success:
        logger.info("🎉 所有测试通过！专利数据收集代理更新成功。")
    else:
        logger.error("❌ 测试失败，请检查代理实现。")
    
    return success


if __name__ == "__main__":
    # 运行测试
    result = asyncio.run(main())
    sys.exit(0 if result else 1)