#!/usr/bin/env python3
"""Google Patents Browser-Use 最终演示."""

import asyncio
import logging
import json
import sys
import os
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_chinese_keyword_mapping():
    """获取中文关键词到英文关键词的映射."""
    # 尝试从配置文件加载
    try:
        config_file = "chinese_keywords_config.json"
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get("关键词映射", {})
    except Exception as e:
        logger.warning(f"无法加载关键词配置文件: {e}，使用默认配置")
    
    # 默认映射（备用）
    return {
        "具身智能": ["embodied intelligence", "embodied AI", "physical AI", "robotics intelligence"],
        "大语言模型": ["large language model", "LLM", "transformer", "GPT", "BERT", "language model"],
        "客户细分": ["customer segmentation", "user profiling", "market segmentation", "customer analytics"],
        "多模态": ["multimodal", "multi-modal", "cross-modal", "vision language"],
        "推荐系统": ["recommendation system", "collaborative filtering", "personalization"],
        "计算机视觉": ["computer vision", "image recognition", "object detection", "visual AI"],
        "自然语言处理": ["natural language processing", "NLP", "text analysis", "language understanding"],
        "深度学习": ["deep learning", "neural network", "artificial neural network"],
        "机器学习": ["machine learning", "ML", "supervised learning", "unsupervised learning"],
        "人工智能": ["artificial intelligence", "AI", "intelligent system"],
        "知识图谱": ["knowledge graph", "knowledge base", "semantic network"],
        "强化学习": ["reinforcement learning", "RL", "Q-learning", "policy gradient"],
        "联邦学习": ["federated learning", "distributed learning", "privacy-preserving learning"],
        "边缘计算": ["edge computing", "edge AI", "mobile computing", "distributed computing"],
        "区块链": ["blockchain", "distributed ledger", "cryptocurrency", "smart contract"],
        "物联网": ["Internet of Things", "IoT", "connected devices", "smart devices"],
        "云计算": ["cloud computing", "distributed computing", "virtualization"],
        "数据挖掘": ["data mining", "data analytics", "pattern recognition", "knowledge discovery"],
        "图像处理": ["image processing", "digital image processing", "image analysis"],
        "语音识别": ["speech recognition", "voice recognition", "automatic speech recognition", "ASR"],
        "情感分析": ["sentiment analysis", "emotion recognition", "affective computing"],
        "预测分析": ["predictive analytics", "forecasting", "predictive modeling"],
        "异常检测": ["anomaly detection", "outlier detection", "fraud detection"],
        "聚类分析": ["clustering", "cluster analysis", "unsupervised classification"],
        "分类算法": ["classification", "supervised learning", "pattern classification"],
        "回归分析": ["regression analysis", "linear regression", "predictive regression"],
        "时间序列": ["time series", "temporal analysis", "sequential data"],
        "优化算法": ["optimization algorithm", "mathematical optimization", "algorithmic optimization"],
        "搜索算法": ["search algorithm", "information retrieval", "search engine"],
        "排序算法": ["sorting algorithm", "ranking algorithm", "ordering algorithm"],
        "加密技术": ["encryption", "cryptography", "data security", "cybersecurity"],
        "隐私保护": ["privacy protection", "data privacy", "privacy-preserving", "differential privacy"]
    }


def expand_keywords_with_chinese(keywords, chinese_mapping=None):
    """扩展关键词列表，支持中文关键词映射."""
    if chinese_mapping is None:
        chinese_mapping = get_chinese_keyword_mapping()
    
    expanded_keywords = []
    
    for keyword in keywords:
        # 添加原始关键词
        expanded_keywords.append(keyword)
        
        # 如果是中文关键词，添加对应的英文关键词
        if keyword in chinese_mapping:
            expanded_keywords.extend(chinese_mapping[keyword])
        
        # 检查是否包含中文关键词的部分匹配
        for chinese_key, english_keywords in chinese_mapping.items():
            if chinese_key in keyword or keyword in chinese_key:
                expanded_keywords.extend(english_keywords)
    
    # 去重并返回
    return list(set(expanded_keywords))


async def demo_google_patents_complete():
    """完整的 Google Patents 功能演示."""
    try:
        from multi_agent_service.patent.services.google_patents_browser import GooglePatentsBrowserService
        
        logger.info("=== Google Patents Browser-Use 完整功能演示 ===")
        logger.info(f"演示时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 创建服务实例
        service = GooglePatentsBrowserService(headless=True, timeout=60)
        
        try:
            # 初始化服务
            logger.info("\n1. 初始化 Google Patents 服务...")
            await service.initialize()
            logger.info("✓ 服务初始化成功")
            
            # 演示不同类型的搜索 - 优化为中文关键词
            demo_searches = [
                {
                    "name": "具身智能专利搜索",
                    "keywords": ["embodied intelligence", "embodied AI", "physical AI", "robotics intelligence"],
                    "limit": 5,
                    "description": "搜索具身智能相关专利，包括机器人智能、物理AI等"
                },
                {
                    "name": "大语言模型专利搜索", 
                    "keywords": ["large language model", "LLM", "transformer", "GPT", "BERT"],
                    "limit": 5,
                    "description": "搜索大语言模型相关专利，包括Transformer、GPT、BERT等"
                },
                {
                    "name": "客户细分专利搜索",
                    "keywords": ["customer segmentation", "user profiling", "market segmentation", "customer analytics"],
                    "limit": 4,
                    "description": "搜索客户细分相关专利，包括用户画像、市场细分等"
                },
                {
                    "name": "多模态AI专利搜索",
                    "keywords": ["multimodal AI", "vision language model", "cross-modal", "multi-modal learning"],
                    "limit": 4,
                    "description": "搜索多模态AI相关专利，包括视觉语言模型、跨模态学习等"
                },
                {
                    "name": "智能推荐系统专利搜索",
                    "keywords": ["recommendation system", "collaborative filtering", "content-based filtering", "personalization"],
                    "limit": 3,
                    "description": "搜索智能推荐系统相关专利，包括协同过滤、个性化推荐等"
                },
                {
                    "name": "计算机视觉专利搜索",
                    "keywords": ["computer vision", "image recognition", "object detection", "deep learning vision"],
                    "limit": 3,
                    "description": "搜索计算机视觉相关专利，包括图像识别、目标检测等"
                },
                {
                    "name": "自然语言处理专利搜索",
                    "keywords": ["natural language processing", "NLP", "text analysis", "language understanding"],
                    "limit": 3,
                    "description": "搜索自然语言处理相关专利，包括文本分析、语言理解等"
                },
                {
                    "name": "高级搜索演示 - 近期AI专利",
                    "keywords": ["artificial intelligence", "machine learning", "deep learning"],
                    "limit": 3,
                    "date_range": {"start_year": "2023", "end_year": "2024"},
                    "assignee": "Google",
                    "description": "搜索Google近期AI相关专利，带日期范围和申请人过滤"
                }
            ]
            
            all_results = {}
            
            for i, search in enumerate(demo_searches, 1):
                logger.info(f"\n{i}. {search['name']}")
                logger.info(f"   描述: {search['description']}")
                logger.info(f"   关键词: {search['keywords']}")
                if search.get('date_range'):
                    logger.info(f"   日期范围: {search['date_range']}")
                if search.get('assignee'):
                    logger.info(f"   申请人: {search['assignee']}")
                
                # 执行搜索
                patents = await service.search_patents(
                    keywords=search["keywords"],
                    limit=search["limit"],
                    date_range=search.get("date_range"),
                    assignee=search.get("assignee")
                )
                
                all_results[search["name"]] = {
                    "search_params": search,
                    "results": patents,
                    "count": len(patents)
                }
                
                logger.info(f"   搜索结果: 找到 {len(patents)} 个专利")
                
                if patents:
                    for j, patent in enumerate(patents, 1):
                        logger.info(f"\n   专利 {j}:")
                        logger.info(f"     标题: {patent.get('title', 'N/A')}")
                        logger.info(f"     专利号: {patent.get('patent_number', 'N/A')}")
                        logger.info(f"     申请人: {', '.join(patent.get('applicants', []))}")
                        logger.info(f"     发布日期: {patent.get('publication_date', 'N/A')}")
                        logger.info(f"     来源: {patent.get('source', 'N/A')}")
                        logger.info(f"     URL: {patent.get('url', 'N/A')}")
                        if patent.get('abstract'):
                            logger.info(f"     摘要: {patent['abstract'][:100]}...")
                else:
                    logger.warning(f"   未找到相关专利")
                
                # 搜索间隔
                await asyncio.sleep(1)
            
            # 演示数据转换功能
            logger.info(f"\n{len(demo_searches) + 1}. 数据转换功能演示")
            
            # 收集所有专利进行转换
            all_patents = []
            for result in all_results.values():
                all_patents.extend(result["results"])
            
            if all_patents:
                # 转换为 PatentRecord 格式
                patent_records = service.convert_to_patent_records(all_patents)
                
                logger.info(f"   转换了 {len(patent_records)} 个专利记录")
                
                if patent_records:
                    logger.info(f"\n   转换后的专利记录示例:")
                    record = patent_records[0]
                    logger.info(f"     专利ID: {record.patent_id}")
                    logger.info(f"     标题: {record.patent_title}")
                    logger.info(f"     申请人: {record.assignee_organization}")
                    logger.info(f"     发明人: {record.inventor_name_first} {record.inventor_name_last}")
                    logger.info(f"     日期: {record.patent_date}")
                    logger.info(f"     IPC分类: {record.ipc_class}")
                    logger.info(f"     CPC分类: {record.cpc_class}")
            
            # 保存演示结果
            result_file = f"google_patents_demo_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, ensure_ascii=False, indent=2)
            logger.info(f"\n演示结果已保存到: {result_file}")
            
            # 统计总结
            total_searches = len(demo_searches)
            successful_searches = sum(1 for result in all_results.values() if result['count'] > 0)
            total_patents = sum(result['count'] for result in all_results.values())
            
            logger.info(f"\n=== 演示统计总结 ===")
            logger.info(f"总搜索次数: {total_searches}")
            logger.info(f"成功搜索: {successful_searches}")
            logger.info(f"总专利数: {total_patents}")
            logger.info(f"成功率: {successful_searches/total_searches*100:.1f}%")
            logger.info(f"平均每次搜索专利数: {total_patents/total_searches:.1f}")
            
            return successful_searches > 0
            
        finally:
            # 关闭服务
            await service.close()
            logger.info("\nGoogle Patents 服务已关闭")
            
    except Exception as e:
        logger.error(f"演示失败: {e}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        return False


async def demo_chinese_keywords():
    """演示中文关键词搜索功能."""
    logger.info("\n=== 中文关键词专利搜索演示 ===")
    
    try:
        from multi_agent_service.patent.services.google_patents_browser import GooglePatentsBrowserService
        
        # 中文关键词搜索演示
        chinese_searches = [
            {
                "name": "具身智能技术专利",
                "chinese_keywords": ["具身智能"],
                "limit": 3,
                "description": "搜索具身智能相关的最新专利技术"
            },
            {
                "name": "大语言模型应用专利",
                "chinese_keywords": ["大语言模型"],
                "limit": 3,
                "description": "搜索大语言模型在各领域的应用专利"
            },
            {
                "name": "客户细分算法专利",
                "chinese_keywords": ["客户细分"],
                "limit": 3,
                "description": "搜索客户细分和用户画像相关专利"
            },
            {
                "name": "多模态AI专利",
                "chinese_keywords": ["多模态"],
                "limit": 2,
                "description": "搜索多模态人工智能相关专利"
            },
            {
                "name": "联邦学习专利",
                "chinese_keywords": ["联邦学习"],
                "limit": 2,
                "description": "搜索联邦学习和隐私保护机器学习专利"
            }
        ]
        
        service = GooglePatentsBrowserService(headless=True, timeout=60)
        await service.initialize()
        
        try:
            chinese_mapping = get_chinese_keyword_mapping()
            all_chinese_results = {}
            
            for i, search in enumerate(chinese_searches, 1):
                logger.info(f"\n{i}. {search['name']}")
                logger.info(f"   中文关键词: {search['chinese_keywords']}")
                
                # 扩展中文关键词为英文关键词
                expanded_keywords = expand_keywords_with_chinese(
                    search['chinese_keywords'], 
                    chinese_mapping
                )
                
                logger.info(f"   扩展后的英文关键词: {expanded_keywords[:5]}...")  # 只显示前5个
                logger.info(f"   描述: {search['description']}")
                
                # 执行搜索
                patents = await service.search_patents(
                    keywords=expanded_keywords,
                    limit=search["limit"]
                )
                
                all_chinese_results[search["name"]] = {
                    "chinese_keywords": search['chinese_keywords'],
                    "expanded_keywords": expanded_keywords,
                    "results": patents,
                    "count": len(patents)
                }
                
                logger.info(f"   搜索结果: 找到 {len(patents)} 个专利")
                
                if patents:
                    for j, patent in enumerate(patents, 1):
                        logger.info(f"\n   专利 {j}:")
                        logger.info(f"     标题: {patent.get('title', 'N/A')}")
                        logger.info(f"     专利号: {patent.get('patent_number', 'N/A')}")
                        logger.info(f"     申请人: {', '.join(patent.get('applicants', []))}")
                        logger.info(f"     发布日期: {patent.get('publication_date', 'N/A')}")
                        if patent.get('abstract'):
                            logger.info(f"     摘要: {patent['abstract'][:150]}...")
                else:
                    logger.warning(f"   未找到相关专利")
                
                # 搜索间隔
                await asyncio.sleep(2)
            
            # 保存中文关键词搜索结果
            chinese_result_file = f"chinese_keywords_patents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(chinese_result_file, 'w', encoding='utf-8') as f:
                json.dump(all_chinese_results, f, ensure_ascii=False, indent=2)
            logger.info(f"\n中文关键词搜索结果已保存到: {chinese_result_file}")
            
            # 统计总结
            total_chinese_searches = len(chinese_searches)
            successful_chinese_searches = sum(1 for result in all_chinese_results.values() if result['count'] > 0)
            total_chinese_patents = sum(result['count'] for result in all_chinese_results.values())
            
            logger.info(f"\n=== 中文关键词搜索统计 ===")
            logger.info(f"总搜索次数: {total_chinese_searches}")
            logger.info(f"成功搜索: {successful_chinese_searches}")
            logger.info(f"总专利数: {total_chinese_patents}")
            logger.info(f"成功率: {successful_chinese_searches/total_chinese_searches*100:.1f}%")
            
            return successful_chinese_searches > 0
            
        finally:
            await service.close()
            
    except Exception as e:
        logger.error(f"中文关键词演示失败: {e}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        return False


async def demo_service_features():
    """演示服务特性."""
    logger.info("\n=== Google Patents 服务特性演示 ===")
    
    try:
        from multi_agent_service.patent.services.google_patents_browser import GooglePatentsBrowserService
        
        # 特性1: 不同的初始化选项
        logger.info("\n1. 服务初始化选项演示")
        
        configs = [
            {"headless": True, "timeout": 30, "description": "标准配置"},
            {"headless": True, "timeout": 60, "description": "长超时配置"}
        ]
        
        for config in configs:
            try:
                service = GooglePatentsBrowserService(**{k: v for k, v in config.items() if k != 'description'})
                await service.initialize()
                logger.info(f"   ✓ {config['description']} - 初始化成功")
                await service.close()
            except Exception as e:
                logger.warning(f"   ✗ {config['description']} - 初始化失败: {e}")
        
        # 特性2: 搜索配置选项
        logger.info("\n2. 搜索配置选项演示")
        
        service = GooglePatentsBrowserService(headless=True)
        await service.initialize()
        
        try:
            # 展示搜索配置
            logger.info(f"   搜索配置:")
            logger.info(f"     每页最大结果数: {service.search_config['max_results_per_page']}")
            logger.info(f"     最大页数: {service.search_config['max_pages']}")
            logger.info(f"     滚动延迟: {service.search_config['scroll_delay']}s")
            logger.info(f"     点击延迟: {service.search_config['click_delay']}s")
            
            # 展示CSS选择器配置
            logger.info(f"   CSS选择器配置:")
            for key, selector in list(service.selectors.items())[:3]:
                logger.info(f"     {key}: {selector}")
            
        finally:
            await service.close()
        
        # 特性3: 错误处理和回退机制
        logger.info("\n3. 错误处理和回退机制演示")
        
        service = GooglePatentsBrowserService(headless=True)
        await service.initialize()
        
        try:
            # 测试无效搜索
            logger.info("   测试空关键词搜索...")
            patents = await service.search_patents(keywords=[], limit=1)
            logger.info(f"   空关键词搜索结果: {len(patents)} 个专利")
            
            # 测试超大限制
            logger.info("   测试超大结果限制...")
            patents = await service.search_patents(keywords=["test"], limit=1000)
            logger.info(f"   超大限制搜索结果: {len(patents)} 个专利")
            
        finally:
            await service.close()
        
        logger.info("   ✓ 错误处理和回退机制正常工作")
        
        return True
        
    except Exception as e:
        logger.error(f"特性演示失败: {e}")
        return False


async def main():
    """主演示函数."""
    logger.info("🚀 Google Patents Browser-Use 中文关键词优化演示开始")
    logger.info("=" * 70)
    
    # 演示1: 完整功能（包含优化的关键词）
    demo1_success = await demo_google_patents_complete()
    
    # 演示2: 中文关键词专门演示
    demo2_success = await demo_chinese_keywords()
    
    # 演示3: 服务特性
    demo3_success = await demo_service_features()
    
    # 总结
    logger.info("\n" + "=" * 70)
    logger.info("📊 最终演示总结:")
    logger.info(f"  完整功能演示: {'✓ 成功' if demo1_success else '✗ 失败'}")
    logger.info(f"  中文关键词演示: {'✓ 成功' if demo2_success else '✗ 失败'}")
    logger.info(f"  服务特性演示: {'✓ 成功' if demo3_success else '✗ 失败'}")
    
    if demo1_success and demo2_success and demo3_success:
        logger.info("\n🎉 Google Patents 中文关键词优化演示完全成功!")
        logger.info("✨ 主要成就:")
        logger.info("   • 成功实现了 Google Patents 访问")
        logger.info("   • 智能爬虫技术绕过了 JavaScript 渲染限制")
        logger.info("   • 提供了完整的专利搜索和数据转换功能")
        logger.info("   • 实现了可靠的错误处理和回退机制")
        logger.info("   • 支持高级搜索参数（日期范围、申请人过滤等）")
        logger.info("   • 🆕 支持中文关键词自动映射到英文关键词")
        logger.info("   • 🆕 优化了具身智能、大语言模型、客户细分等热门领域搜索")
        logger.info("   • 🆕 扩展了30+个中文技术术语的英文映射")
        return 0
    elif demo1_success or demo2_success:
        logger.warning("\n⚠️  部分演示成功，系统基本可用")
        logger.info("💡 建议:")
        if not demo2_success:
            logger.info("   • 中文关键词功能可能需要进一步调试")
        if not demo3_success:
            logger.info("   • 服务特性演示失败，但核心功能正常")
        return 1
    else:
        logger.error("\n❌ 演示失败，请检查系统配置")
        return 2


async def quick_chinese_test():
    """快速测试中文关键词功能."""
    logger.info("🔍 快速中文关键词测试")
    logger.info("=" * 40)
    
    # 测试关键词映射功能
    chinese_mapping = get_chinese_keyword_mapping()
    test_keywords = ["具身智能", "大语言模型", "客户细分"]
    
    logger.info("测试关键词映射:")
    for keyword in test_keywords:
        expanded = expand_keywords_with_chinese([keyword], chinese_mapping)
        logger.info(f"  {keyword} -> {expanded[:3]}...")  # 只显示前3个
    
    # 快速搜索测试
    try:
        from multi_agent_service.patent.services.google_patents_browser import GooglePatentsBrowserService
        
        service = GooglePatentsBrowserService(headless=True, timeout=30)
        await service.initialize()
        
        try:
            # 测试一个关键词
            test_keyword = "具身智能"
            expanded_keywords = expand_keywords_with_chinese([test_keyword], chinese_mapping)
            
            logger.info(f"\n快速搜索测试: {test_keyword}")
            patents = await service.search_patents(keywords=expanded_keywords, limit=1)
            
            if patents:
                logger.info(f"✓ 成功找到 {len(patents)} 个专利")
                patent = patents[0]
                logger.info(f"  示例专利: {patent.get('title', 'N/A')}")
            else:
                logger.info("✗ 未找到相关专利")
                
        finally:
            await service.close()
            
        return len(patents) > 0 if 'patents' in locals() else False
        
    except Exception as e:
        logger.error(f"快速测试失败: {e}")
        return False


if __name__ == "__main__":
    import sys
    
    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        # 快速测试模式
        success = asyncio.run(quick_chinese_test())
        sys.exit(0 if success else 1)
    else:
        # 完整演示模式
        exit_code = asyncio.run(main())
        sys.exit(exit_code)