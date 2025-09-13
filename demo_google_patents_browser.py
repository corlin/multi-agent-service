#!/usr/bin/env python3
"""Google Patents Browser-Use 功能演示脚本."""

import asyncio
import json
import logging
from datetime import datetime
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_basic_search():
    """演示基础搜索功能."""
    logger.info("=== 演示1: 基础搜索功能 ===")
    
    try:
        from multi_agent_service.patent.services.google_patents_browser import GooglePatentsBrowserService
        
        # 搜索参数
        keywords = ["blockchain", "cryptocurrency"]
        limit = 5
        
        logger.info(f"搜索关键词: {keywords}")
        logger.info(f"结果限制: {limit}")
        
        async with GooglePatentsBrowserService(headless=True, timeout=60) as browser_service:
            patents = await browser_service.search_patents(
                keywords=keywords,
                limit=limit
            )
            
            logger.info(f"找到 {len(patents)} 个专利")
            
            for i, patent in enumerate(patents, 1):
                logger.info(f"\n专利 {i}:")
                logger.info(f"  标题: {patent.get('title', 'N/A')}")
                logger.info(f"  专利号: {patent.get('patent_number', 'N/A')}")
                logger.info(f"  申请人: {', '.join(patent.get('applicants', []))}")
                logger.info(f"  发布日期: {patent.get('publication_date', 'N/A')}")
        
        return True
        
    except Exception as e:
        logger.error(f"基础搜索演示失败: {str(e)}")
        return False


async def demo_advanced_search():
    """演示高级搜索功能."""
    logger.info("\n=== 演示2: 高级搜索功能 ===")
    
    try:
        from multi_agent_service.patent.services.google_patents_browser import GooglePatentsBrowserService
        
        # 高级搜索参数
        keywords = ["artificial intelligence", "neural network"]
        limit = 3
        date_range = {"start_year": "2023", "end_year": "2024"}
        assignee = "Google"
        
        logger.info(f"搜索关键词: {keywords}")
        logger.info(f"日期范围: {date_range}")
        logger.info(f"申请人过滤: {assignee}")
        
        async with GooglePatentsBrowserService(headless=True, timeout=60) as browser_service:
            patents = await browser_service.search_patents(
                keywords=keywords,
                limit=limit,
                date_range=date_range,
                assignee=assignee
            )
            
            logger.info(f"找到 {len(patents)} 个专利")
            
            for i, patent in enumerate(patents, 1):
                logger.info(f"\n专利 {i}:")
                logger.info(f"  标题: {patent.get('title', 'N/A')}")
                logger.info(f"  专利号: {patent.get('patent_number', 'N/A')}")
                logger.info(f"  申请人: {', '.join(patent.get('applicants', []))}")
                logger.info(f"  摘要: {patent.get('abstract', 'N/A')[:150]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"高级搜索演示失败: {str(e)}")
        return False


async def demo_data_collection_agent():
    """演示数据收集代理的浏览器功能."""
    logger.info("\n=== 演示3: 数据收集代理集成 ===")
    
    try:
        from multi_agent_service.agents.patent.data_collection_agent import PatentDataCollectionAgent
        from multi_agent_service.models.base import UserRequest
        from multi_agent_service.models.config import AgentConfig
        from multi_agent_service.services.model_client import BaseModelClient
        
        # 创建模拟的模型客户端
        class MockModelClient(BaseModelClient):
            async def generate_response(self, prompt: str, **kwargs) -> str:
                return "Mock response for patent analysis"
        
        # 创建代理配置
        config = AgentConfig(
            agent_id="demo_agent",
            name="Demo Patent Collection Agent",
            description="演示专利收集代理",
            capabilities=[]
        )
        
        # 创建数据收集代理
        agent = PatentDataCollectionAgent(config, MockModelClient())
        
        # 检查浏览器功能状态
        browser_status = agent._get_browser_collection_status()
        logger.info("浏览器功能状态:")
        logger.info(f"  Browser-Use可用: {browser_status['browser_use_available']}")
        logger.info(f"  Google Patents浏览器启用: {browser_status['google_patents_browser_enabled']}")
        logger.info(f"  支持的功能: {', '.join(browser_status['supported_features'])}")
        
        # 创建测试请求
        test_requests = [
            "收集关于5G技术的专利数据，使用浏览器方式",
            "从Google Patents获取人工智能相关专利，限制20个结果",
            "使用浏览器自动化收集区块链专利信息"
        ]
        
        for i, content in enumerate(test_requests, 1):
            logger.info(f"\n测试请求 {i}: {content}")
            
            request = UserRequest(
                content=content,
                user_id="demo_user",
                session_id="demo_session"
            )
            
            # 测试处理能力
            confidence = await agent.can_handle_request(request)
            logger.info(f"  处理置信度: {confidence:.2f}")
            
            if confidence > 0.5:
                logger.info("  ✓ 代理可以处理该请求")
            else:
                logger.info("  ✗ 代理无法处理该请求")
        
        return True
        
    except Exception as e:
        logger.error(f"代理演示失败: {str(e)}")
        return False


async def demo_data_conversion():
    """演示数据转换功能."""
    logger.info("\n=== 演示4: 数据转换功能 ===")
    
    try:
        from multi_agent_service.patent.services.google_patents_browser import GooglePatentsBrowserService
        
        # 模拟浏览器收集的数据
        mock_browser_data = [
            {
                "patent_id": "US11123456B2",
                "patent_number": "US11123456B2",
                "title": "Method and System for Artificial Intelligence Processing",
                "abstract": "A method and system for processing artificial intelligence data...",
                "applicants": ["Tech Corp Inc."],
                "inventors": ["John Doe", "Jane Smith"],
                "publication_date": "2024-01-15",
                "url": "https://patents.google.com/patent/US11123456B2",
                "source": "google_patents_browser",
                "collected_at": datetime.now().isoformat()
            }
        ]
        
        # 创建服务实例（不需要实际初始化浏览器）
        service = GooglePatentsBrowserService(headless=True)
        
        # 转换数据
        patent_records = service.convert_to_patent_records(mock_browser_data)
        
        logger.info(f"转换了 {len(patent_records)} 个专利记录")
        
        for record in patent_records:
            logger.info(f"\n转换后的专利记录:")
            logger.info(f"  专利ID: {record.patent_id}")
            logger.info(f"  标题: {record.patent_title}")
            logger.info(f"  申请人: {record.assignee_organization}")
            logger.info(f"  发明人: {record.inventor_name_first} {record.inventor_name_last}")
            logger.info(f"  日期: {record.patent_date}")
        
        return True
        
    except Exception as e:
        logger.error(f"数据转换演示失败: {str(e)}")
        return False


async def demo_error_handling():
    """演示错误处理功能."""
    logger.info("\n=== 演示5: 错误处理功能 ===")
    
    try:
        from multi_agent_service.patent.services.google_patents_browser import GooglePatentsBrowserService
        
        # 测试无效搜索
        logger.info("测试无效搜索参数...")
        
        async with GooglePatentsBrowserService(headless=True, timeout=10) as browser_service:
            # 使用空关键词搜索
            patents = await browser_service.search_patents(
                keywords=[],
                limit=5
            )
            
            logger.info(f"空关键词搜索结果: {len(patents)} 个专利")
            
            # 测试无效URL的详情获取
            logger.info("测试无效URL的详情获取...")
            details = await browser_service.get_patent_details("https://invalid-url.com")
            
            if details:
                logger.info("意外获得了详情数据")
            else:
                logger.info("正确处理了无效URL")
        
        return True
        
    except Exception as e:
        logger.info(f"错误处理演示完成，捕获到预期错误: {str(e)}")
        return True


def create_demo_report(results):
    """创建演示报告."""
    report = {
        "demo_time": datetime.now().isoformat(),
        "results": {
            "basic_search": results[0],
            "advanced_search": results[1],
            "agent_integration": results[2],
            "data_conversion": results[3],
            "error_handling": results[4]
        },
        "summary": {
            "total_demos": len(results),
            "successful_demos": sum(results),
            "success_rate": sum(results) / len(results) * 100
        }
    }
    
    report_file = f"google_patents_browser_demo_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info(f"演示报告已保存到: {report_file}")
    except Exception as e:
        logger.error(f"保存报告失败: {str(e)}")


async def main():
    """主演示函数."""
    logger.info("🚀 Google Patents Browser-Use 功能演示开始")
    logger.info("=" * 60)
    
    # 检查依赖
    try:
        import browser_use
        import playwright
        logger.info("✓ 依赖检查通过")
    except ImportError as e:
        logger.error(f"✗ 依赖缺失: {str(e)}")
        logger.error("请运行: python setup_browser_use.py")
        return 1
    
    # 运行演示
    demos = [
        demo_basic_search,
        demo_advanced_search,
        demo_data_collection_agent,
        demo_data_conversion,
        demo_error_handling
    ]
    
    results = []
    
    for demo in demos:
        try:
            result = await demo()
            results.append(result)
        except Exception as e:
            logger.error(f"演示执行失败: {str(e)}")
            results.append(False)
        
        # 演示间隔
        await asyncio.sleep(1)
    
    # 生成报告
    logger.info("\n" + "=" * 60)
    logger.info("📊 演示结果总结:")
    logger.info(f"  总演示数: {len(results)}")
    logger.info(f"  成功演示: {sum(results)}")
    logger.info(f"  成功率: {sum(results)/len(results)*100:.1f}%")
    
    create_demo_report(results)
    
    if all(results):
        logger.info("🎉 所有演示成功完成!")
        return 0
    else:
        logger.warning("⚠️  部分演示失败，请检查错误信息")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)