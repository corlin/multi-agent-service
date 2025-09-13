"""简化的 PatentsView 测试脚本."""

import asyncio
import logging
import sys
import os
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath('.'))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


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
        
        # 测试模型序列化
        logger.info("测试模型序列化...")
        patent_json = patent.model_dump_json()
        logger.info(f"专利记录 JSON 长度: {len(patent_json)} 字符")
        
        search_result_json = search_result.model_dump_json()
        logger.info(f"搜索结果 JSON 长度: {len(search_result_json)} 字符")
        
        logger.info("PatentsView 数据模型测试完成")
        return True
        
    except Exception as e:
        logger.error(f"数据模型测试过程中发生错误: {str(e)}")
        return False


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
        return True
        
    except Exception as e:
        logger.error(f"配置测试过程中发生错误: {str(e)}")
        return False


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
        return True
        
    except Exception as e:
        logger.error(f"服务测试过程中发生错误: {str(e)}")
        return False


async def test_query_examples():
    """测试查询示例."""
    
    logger.info("开始测试查询示例")
    
    try:
        from src.multi_agent_service.patent.services.patentsview_service import PatentsViewService
        
        service = PatentsViewService()
        
        # 示例1: 简单关键词搜索
        logger.info("示例1: 简单关键词搜索")
        simple_query = service.build_text_search_query(["neural network"])
        logger.info(f"简单查询: {simple_query}")
        
        # 示例2: 多关键词搜索
        logger.info("示例2: 多关键词搜索")
        multi_query = service.build_text_search_query(
            ["deep learning", "convolutional neural network", "transformer"],
            ["patent_title", "patent_abstract"]
        )
        logger.info(f"多关键词查询: {multi_query}")
        
        # 示例3: 日期范围限制
        logger.info("示例3: 日期范围限制")
        date_limited_query = service.build_date_range_query("2022-01-01", "2024-12-31")
        logger.info(f"日期限制查询: {date_limited_query}")
        
        # 示例4: 分类限制
        logger.info("示例4: 分类限制")
        class_limited_query = service.build_classification_query(
            ipc_classes=["G06N", "G06F"],
            cpc_classes=["G06N3/02", "G06F15/18"]
        )
        logger.info(f"分类限制查询: {class_limited_query}")
        
        # 示例5: 复合查询
        logger.info("示例5: 复合查询")
        complex_query = service.combine_queries(
            service.build_text_search_query(["artificial intelligence"]),
            service.build_date_range_query("2020-01-01", "2024-12-31"),
            service.build_classification_query(ipc_classes=["G06N"])
        )
        logger.info(f"复合查询: {complex_query}")
        
        logger.info("查询示例测试完成")
        return True
        
    except Exception as e:
        logger.error(f"查询示例测试过程中发生错误: {str(e)}")
        return False


async def main():
    """主测试函数."""
    
    logger.info("开始 PatentsView 简化集成测试")
    
    test_results = []
    
    # 测试配置
    logger.info("=" * 50)
    result1 = await test_patentsview_config()
    test_results.append(("配置测试", result1))
    
    # 测试数据模型
    logger.info("=" * 50)
    result2 = await test_patentsview_models()
    test_results.append(("数据模型测试", result2))
    
    # 测试服务
    logger.info("=" * 50)
    result3 = await test_patentsview_service()
    test_results.append(("服务测试", result3))
    
    # 测试查询示例
    logger.info("=" * 50)
    result4 = await test_query_examples()
    test_results.append(("查询示例测试", result4))
    
    # 汇总结果
    logger.info("=" * 50)
    logger.info("测试结果汇总:")
    all_passed = True
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        logger.info("🎉 所有测试通过！PatentsView 集成准备就绪。")
    else:
        logger.error("❌ 部分测试失败，请检查错误信息。")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)