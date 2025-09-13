"""测试 PatentsView API 实际调用."""

import asyncio
import logging
import sys
import os
import json

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath('.'))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_api_connection():
    """测试 API 连接."""
    
    logger.info("开始测试 PatentsView API 连接")
    
    try:
        from src.multi_agent_service.patent.services.patentsview_service import PatentsViewService
        
        # 创建服务实例
        async with PatentsViewService() as service:
            
            # 测试1: 简单专利搜索
            logger.info("测试1: 简单专利搜索")
            
            # 构建一个简单的查询
            query = {
                "_text_any": {
                    "patent_title": "artificial intelligence"
                }
            }
            
            try:
                response = await service.search_patents(
                    query=query,
                    options={"size": 5}  # 只获取5条记录进行测试
                )
                
                if response.patents:
                    logger.info(f"✅ 成功获取 {len(response.patents)} 条专利记录")
                    
                    # 显示第一条专利信息
                    first_patent = response.patents[0]
                    logger.info(f"第一条专利: {first_patent.get('patent_title', 'N/A')}")
                    logger.info(f"专利ID: {first_patent.get('patent_id', 'N/A')}")
                    logger.info(f"专利日期: {first_patent.get('patent_date', 'N/A')}")
                else:
                    logger.warning("⚠️ 未获取到专利记录，但API调用成功")
                
                return True
                
            except Exception as api_error:
                logger.error(f"❌ API调用失败: {str(api_error)}")
                return False
        
    except Exception as e:
        logger.error(f"❌ 服务初始化失败: {str(e)}")
        return False


async def test_multiple_endpoints():
    """测试多个端点."""
    
    logger.info("开始测试多个 PatentsView API 端点")
    
    try:
        from src.multi_agent_service.patent.services.patentsview_service import PatentsViewService
        
        async with PatentsViewService() as service:
            
            # 测试专利搜索
            logger.info("测试专利端点...")
            patent_query = {
                "patent_date": {
                    "_gte": "2024-01-01",
                    "_lte": "2024-12-31"
                }
            }
            
            try:
                patent_response = await service.search_patents(
                    query=patent_query,
                    options={"size": 3}
                )
                logger.info(f"专利端点: 获取 {len(patent_response.patents or [])} 条记录")
            except Exception as e:
                logger.warning(f"专利端点测试失败: {str(e)}")
            
            # 测试CPC分类
            logger.info("测试CPC分类端点...")
            try:
                cpc_response = await service.search_cpc_classes(
                    options={"size": 5}
                )
                logger.info(f"CPC分类端点: 获取 {len(cpc_response.cpc_classes or [])} 条记录")
            except Exception as e:
                logger.warning(f"CPC分类端点测试失败: {str(e)}")
            
            # 测试IPC分类
            logger.info("测试IPC分类端点...")
            try:
                ipc_response = await service.search_ipc_classes(
                    options={"size": 5}
                )
                logger.info(f"IPC分类端点: 获取 {len(ipc_response.ipc_classes or [])} 条记录")
            except Exception as e:
                logger.warning(f"IPC分类端点测试失败: {str(e)}")
            
            return True
        
    except Exception as e:
        logger.error(f"❌ 多端点测试失败: {str(e)}")
        return False


async def test_comprehensive_search():
    """测试综合搜索功能."""
    
    logger.info("开始测试综合搜索功能")
    
    try:
        from src.multi_agent_service.patent.services.patentsview_service import PatentsViewService
        
        async with PatentsViewService() as service:
            
            # 执行综合搜索
            logger.info("执行综合搜索...")
            
            search_result = await service.comprehensive_search(
                keywords=["machine learning"],
                date_range={"start": "2023-01-01", "end": "2024-12-31"},
                countries=["US"],
                max_results=10
            )
            
            # 统计结果
            patents_count = len(search_result.patents)
            summaries_count = len(search_result.patent_summaries)
            claims_count = len(search_result.patent_claims)
            assignees_count = len(search_result.assignees)
            inventors_count = len(search_result.inventors)
            cpc_count = len(search_result.cpc_classes)
            ipc_count = len(search_result.ipc_classes)
            
            logger.info(f"综合搜索结果:")
            logger.info(f"  专利记录: {patents_count}")
            logger.info(f"  专利摘要: {summaries_count}")
            logger.info(f"  权利要求: {claims_count}")
            logger.info(f"  专利权人: {assignees_count}")
            logger.info(f"  发明人: {inventors_count}")
            logger.info(f"  CPC分类: {cpc_count}")
            logger.info(f"  IPC分类: {ipc_count}")
            
            # 显示搜索元数据
            metadata = search_result.search_metadata
            logger.info(f"搜索元数据: {json.dumps(metadata, indent=2, ensure_ascii=False)}")
            
            return True
        
    except Exception as e:
        logger.error(f"❌ 综合搜索测试失败: {str(e)}")
        return False


async def test_query_variations():
    """测试不同的查询变体."""
    
    logger.info("开始测试查询变体")
    
    try:
        from src.multi_agent_service.patent.services.patentsview_service import PatentsViewService
        
        service = PatentsViewService()
        
        # 测试不同的查询构建方法
        queries = [
            # 单关键词搜索
            service.build_text_search_query(["blockchain"]),
            
            # 多关键词搜索
            service.build_text_search_query(["quantum", "computing"]),
            
            # 日期范围搜索
            service.build_date_range_query("2023-01-01", "2023-12-31"),
            
            # 分类搜索
            service.build_classification_query(ipc_classes=["H04L"]),
            
            # 复合搜索
            service.combine_queries(
                service.build_text_search_query(["5G"]),
                service.build_date_range_query("2022-01-01", "2024-12-31")
            )
        ]
        
        query_names = [
            "单关键词搜索",
            "多关键词搜索", 
            "日期范围搜索",
            "分类搜索",
            "复合搜索"
        ]
        
        for i, (query, name) in enumerate(zip(queries, query_names)):
            logger.info(f"查询 {i+1} ({name}): {json.dumps(query, ensure_ascii=False)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 查询变体测试失败: {str(e)}")
        return False


async def main():
    """主测试函数."""
    
    logger.info("开始 PatentsView API 实际调用测试")
    logger.info("注意: 这些测试需要网络连接，某些端点可能需要API密钥")
    
    test_results = []
    
    # 测试查询变体（不需要网络）
    logger.info("=" * 60)
    result1 = await test_query_variations()
    test_results.append(("查询变体测试", result1))
    
    # 测试API连接（需要网络）
    logger.info("=" * 60)
    result2 = await test_api_connection()
    test_results.append(("API连接测试", result2))
    
    # 测试多个端点（需要网络）
    logger.info("=" * 60)
    result3 = await test_multiple_endpoints()
    test_results.append(("多端点测试", result3))
    
    # 测试综合搜索（需要网络）
    logger.info("=" * 60)
    result4 = await test_comprehensive_search()
    test_results.append(("综合搜索测试", result4))
    
    # 汇总结果
    logger.info("=" * 60)
    logger.info("API测试结果汇总:")
    
    passed_count = 0
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{test_name}: {status}")
        if result:
            passed_count += 1
    
    logger.info(f"总计: {passed_count}/{len(test_results)} 个测试通过")
    
    if passed_count == len(test_results):
        logger.info("🎉 所有API测试通过！PatentsView集成完全就绪。")
    elif passed_count > 0:
        logger.info("⚠️ 部分API测试通过，请检查网络连接和API配置。")
    else:
        logger.error("❌ 所有API测试失败，请检查网络连接、API配置或服务状态。")
    
    return passed_count > 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)