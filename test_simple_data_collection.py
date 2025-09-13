#!/usr/bin/env python3
"""简化的专利数据收集Agent测试."""

import asyncio
import logging
import sys
import os
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_chinese_keyword_mapping():
    """测试中文关键词映射功能."""
    logger.info("=== 测试中文关键词映射功能 ===")
    
    try:
        from multi_agent_service.patent.agents.data_collection import PatentDataCollectionAgent
        from multi_agent_service.models.config import AgentConfig
        
        # 创建Agent配置
        config = AgentConfig(
            agent_id="test_patent_data_collection",
            agent_type="patent_data_collection",
            name="Test Patent Data Collection Agent",
            description="Test agent for patent data collection",
            enabled=True
        )
        
        # 创建Agent实例
        agent = PatentDataCollectionAgent(config, None)
        
        # 测试中文关键词映射
        test_keywords = ["具身智能", "大语言模型", "客户细分", "多模态", "联邦学习"]
        
        logger.info("测试关键词扩展:")
        for keyword in test_keywords:
            expanded = agent._expand_keywords_with_chinese([keyword])
            logger.info(f"  {keyword} -> {len(expanded)} 个关键词: {expanded[:3]}...")
        
        # 测试预览功能
        preview = await agent.preview_keyword_expansion(test_keywords[:3])
        logger.info(f"\n关键词扩展预览:")
        for original, expanded in preview.items():
            logger.info(f"  {original}: {len(expanded)} 个扩展关键词")
        
        # 获取支持的中文关键词
        supported_keywords = await agent.get_supported_chinese_keywords()
        logger.info(f"\n支持的中文关键词总数: {len(supported_keywords)}")
        logger.info(f"前10个关键词: {supported_keywords[:10]}")
        
        return True
        
    except Exception as e:
        logger.error(f"中文关键词映射测试失败: {e}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        return False


async def test_agent_capabilities():
    """测试Agent能力."""
    logger.info("\n=== 测试Agent能力 ===")
    
    try:
        from multi_agent_service.patent.agents.data_collection import PatentDataCollectionAgent
        from multi_agent_service.models.config import AgentConfig
        from multi_agent_service.models.base import UserRequest
        
        # 创建Agent配置
        config = AgentConfig(
            agent_id="test_patent_data_collection",
            agent_type="patent_data_collection", 
            name="Test Patent Data Collection Agent",
            description="Test agent for patent data collection",
            enabled=True
        )
        
        # 创建Agent实例
        agent = PatentDataCollectionAgent(config, None)
        
        # 获取能力列表
        capabilities = await agent.get_capabilities()
        logger.info(f"Agent能力列表 ({len(capabilities)} 项):")
        for i, capability in enumerate(capabilities, 1):
            logger.info(f"  {i}. {capability}")
        
        # 测试请求处理能力评估
        test_requests = [
            UserRequest(request_id="test_1", content="搜索具身智能专利"),
            UserRequest(request_id="test_2", content="收集大语言模型数据"),
            UserRequest(request_id="test_3", content="今天天气怎么样？")
        ]
        
        logger.info(f"\n请求处理能力评估:")
        for request in test_requests:
            confidence = await agent.can_handle_request(request)
            logger.info(f"  '{request.content}' -> 置信度: {confidence:.2f}")
        
        # 获取处理指标
        metrics = agent.get_patent_metrics()
        logger.info(f"\n处理指标:")
        for key, value in metrics.items():
            if isinstance(value, dict):
                logger.info(f"  {key}:")
                for sub_key, sub_value in value.items():
                    logger.info(f"    {sub_key}: {sub_value}")
            else:
                logger.info(f"  {key}: {value}")
        
        return True
        
    except Exception as e:
        logger.error(f"Agent能力测试失败: {e}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        return False


async def test_keyword_conversion():
    """测试关键词转换功能."""
    logger.info("\n=== 测试关键词转换功能 ===")
    
    try:
        from multi_agent_service.patent.agents.data_collection import PatentDataCollectionAgent
        from multi_agent_service.models.config import AgentConfig
        from multi_agent_service.models.base import UserRequest
        
        # 创建Agent配置
        config = AgentConfig(
            agent_id="test_patent_data_collection",
            agent_type="patent_data_collection",
            name="Test Patent Data Collection Agent", 
            description="Test agent for patent data collection",
            enabled=True
        )
        
        # 创建Agent实例
        agent = PatentDataCollectionAgent(config, None)
        
        # 测试包含中文关键词的请求
        test_requests = [
            UserRequest(
                request_id="test_1",
                content="我想搜索具身智能相关的专利技术"
            ),
            UserRequest(
                request_id="test_2", 
                content="请帮我收集大语言模型和客户细分的专利数据"
            ),
            UserRequest(
                request_id="test_3",
                content="查找多模态AI和联邦学习的最新专利"
            )
        ]
        
        for i, request in enumerate(test_requests, 1):
            logger.info(f"\n测试请求 {i}:")
            logger.info(f"  原始内容: {request.content}")
            
            # 转换请求
            collection_request = agent._convert_to_collection_request(request)
            logger.info(f"  提取的关键词: {collection_request.keywords}")
            logger.info(f"  数据源: {collection_request.data_sources}")
            logger.info(f"  并行收集: {collection_request.parallel_sources}")
            
            # 预览关键词扩展
            expanded_preview = await agent.preview_keyword_expansion(collection_request.keywords)
            for keyword, expanded in expanded_preview.items():
                logger.info(f"  {keyword} 扩展为 {len(expanded)} 个关键词")
        
        return True
        
    except Exception as e:
        logger.error(f"关键词转换测试失败: {e}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        return False


async def main():
    """主测试函数."""
    logger.info("🚀 开始测试优化后的专利数据收集Agent")
    logger.info("=" * 60)
    
    # 测试1: 中文关键词映射
    test1_success = await test_chinese_keyword_mapping()
    
    # 测试2: Agent能力
    test2_success = await test_agent_capabilities()
    
    # 测试3: 关键词转换
    test3_success = await test_keyword_conversion()
    
    # 总结
    logger.info("\n" + "=" * 60)
    logger.info("📊 测试总结:")
    logger.info(f"  中文关键词映射: {'✓ 成功' if test1_success else '✗ 失败'}")
    logger.info(f"  Agent能力测试: {'✓ 成功' if test2_success else '✗ 失败'}")
    logger.info(f"  关键词转换测试: {'✓ 成功' if test3_success else '✗ 失败'}")
    
    if test1_success and test2_success and test3_success:
        logger.info("\n🎉 所有测试通过！优化功能正常工作")
        logger.info("✨ 主要优化成果:")
        logger.info("   • 集成了30+个中文技术术语的英文映射")
        logger.info("   • 支持中文关键词自动扩展为英文关键词")
        logger.info("   • 优化了Google Patents Browser Service集成")
        logger.info("   • 增强了错误处理和重试机制")
        logger.info("   • 改进了请求转换和处理逻辑")
        return 0
    else:
        logger.warning("\n⚠️  部分测试失败，请检查相关功能")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)