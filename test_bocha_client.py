#!/usr/bin/env python3
"""
测试优化后的BochaAIClient - 增强版本
"""

import asyncio
import sys
import os
import logging
import time

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from multi_agent_service.agents.patent.search_agent import BochaAIClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def test_bocha_client():
    """测试优化后的BochaAIClient的各种功能."""
    
    print("🚀 开始测试优化后的BochaAIClient")
    print("=" * 60)
    
    async with BochaAIClient() as client:
        
        # 显示API状态
        print("\n📋 API状态信息")
        print("-" * 30)
        api_status = client.get_api_status()
        api_key_info = api_status['api_key_info']
        
        print(f"✅ API密钥配置: {'是' if api_status['api_key_configured'] else '否'}")
        print(f"🔍 密钥格式验证: {'通过' if api_status['api_key_valid'] else '失败'}")
        print(f"🔑 密钥来源: {api_status['api_key_source']}")
        print(f"📏 密钥长度: {api_key_info['api_key_length']} 字符")
        print(f"🔐 密钥前缀: {api_key_info['api_key_prefix']}")
        print(f"⚠️ 使用默认密钥: {'是' if api_key_info['is_default_key'] else '否'}")
        print(f"🌐 基础URL: {api_status['base_url']}")
        
        # 显示环境变量状态
        print("\n🔧 环境变量状态:")
        for env_var, status in api_key_info['environment_variables'].items():
            status_icon = "✅" if status['exists'] and status['valid_format'] else "❌" if status['exists'] else "⚪"
            print(f"  {status_icon} {env_var}: {'存在' if status['exists'] else '不存在'}")
            if status['exists']:
                print(f"     长度: {status['length']}, 格式: {'有效' if status['valid_format'] else '无效'}")
        
        print(f"\n📊 性能配置: 速率限制 {api_status['health']['rate_limit']}, 超时 {api_status['health']['timeout']}")
        
        # 测试1: Web搜索
        print("\n📄 测试1: Web搜索")
        print("-" * 30)
        
        try:
            web_results = await client._web_search("人工智能专利技术", "patent", 5)
            print(f"✅ Web搜索完成，获得 {len(web_results)} 个结果")
            
            for i, result in enumerate(web_results[:2]):
                print(f"  {i+1}. {result.get('title', 'N/A')}")
                print(f"     来源: {result.get('source', 'N/A')}")
                print(f"     相关性: {result.get('relevance_score', 0):.2f}")
                
        except Exception as e:
            print(f"❌ Web搜索失败: {str(e)}")
        
        # 测试2: AI搜索
        print("\n🤖 测试2: AI搜索")
        print("-" * 30)
        
        try:
            ai_results = await client._ai_search("区块链技术应用", "academic", 3)
            print(f"✅ AI搜索完成，获得 {len(ai_results)} 个结果")
            
            for i, result in enumerate(ai_results[:2]):
                print(f"  {i+1}. {result.get('title', 'N/A')}")
                print(f"     类型: {result.get('content_type', 'N/A')}")
                print(f"     相关性: {result.get('relevance_score', 0):.2f}")
                
        except Exception as e:
            print(f"❌ AI搜索失败: {str(e)}")
        
        # 测试3: Agent搜索
        print("\n🎯 测试3: Agent搜索")
        print("-" * 30)
        
        try:
            agent_results = await client._agent_search("机器学习算法研究", "academic", 3)
            print(f"✅ Agent搜索完成，获得 {len(agent_results)} 个结果")
            
            for i, result in enumerate(agent_results[:2]):
                print(f"  {i+1}. {result.get('title', 'N/A')}")
                print(f"     Agent: {result.get('source', 'N/A')}")
                print(f"     权威性: {result.get('authority_score', 0):.2f}")
                
        except Exception as e:
            print(f"❌ Agent搜索失败: {str(e)}")
        
        # 测试4: 综合搜索 - 多种搜索类型
        print("\n🔍 测试4: 综合搜索")
        print("-" * 30)
        
        search_scenarios = [
            (["深度学习", "神经网络"], "academic", "学术搜索"),
            (["人工智能", "专利技术"], "patent", "专利搜索"),
            (["阿里巴巴", "企业信息"], "company", "企业搜索"),
            (["机器学习", "算法"], "general", "通用搜索")
        ]
        
        for keywords, search_type, description in search_scenarios:
            try:
                start_time = time.time()
                results = await client.search(keywords, search_type, 8)
                duration = time.time() - start_time
                
                print(f"  📝 {description}: {len(results)} 个结果 (耗时: {duration:.2f}s)")
                
                if results:
                    # 显示最佳结果
                    best_result = results[0]
                    print(f"     🏆 最佳: {best_result.get('title', 'N/A')[:50]}...")
                    print(f"     📊 质量: {best_result.get('quality_score', 0):.2f}")
                    
                    # 统计来源
                    sources = {}
                    for result in results:
                        source = result.get('search_source', result.get('source', 'unknown'))
                        sources[source] = sources.get(source, 0) + 1
                    
                    source_info = ", ".join([f"{k}:{v}" for k, v in sources.items()])
                    print(f"     🔍 来源: {source_info}")
                
            except Exception as e:
                print(f"  ❌ {description}失败: {str(e)}")
        
        # 显示客户端统计信息
        print("\n📈 客户端性能统计:")
        stats = client.stats
        print(f"  总请求数: {stats['total_requests']}")
        print(f"  成功率: {stats['successful_requests']}/{stats['total_requests']}")
        print(f"  平均响应时间: {stats['average_response_time']:.2f}s")
        if stats['api_errors']:
            print(f"  错误统计: {stats['api_errors']}")
        
        # 测试5: 语义重排序
        print("\n🔄 测试5: 语义重排序")
        print("-" * 30)
        
        try:
            # 创建一些测试结果
            test_results = [
                {
                    "title": "人工智能在医疗领域的应用",
                    "content": "人工智能技术在医疗诊断中发挥重要作用",
                    "relevance_score": 0.6
                },
                {
                    "title": "深度学习算法优化研究",
                    "content": "深度学习神经网络算法的性能优化方法",
                    "relevance_score": 0.7
                },
                {
                    "title": "机器学习在金融风控中的应用",
                    "content": "机器学习技术用于金融风险控制和预测",
                    "relevance_score": 0.5
                }
            ]
            
            reranked_results = await client._rerank_results("深度学习算法", test_results)
            print(f"✅ 语义重排序完成，处理 {len(reranked_results)} 个结果")
            
            for i, result in enumerate(reranked_results):
                print(f"  {i+1}. {result.get('title', 'N/A')}")
                print(f"     重排序分数: {result.get('rerank_score', 'N/A')}")
                
        except Exception as e:
            print(f"❌ 语义重排序失败: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🎉 BochaAIClient测试完成!")

async def test_api_connectivity():
    """测试API连接性."""
    print("\n🔗 测试API连接性")
    print("-" * 30)
    
    import aiohttp
    
    api_endpoints = [
        ("Web搜索API", "https://api.bochaai.com/v1/web-search"),
        ("AI搜索API", "https://api.bochaai.com/v1/ai-search"),
        ("Agent搜索API", "https://api.bochaai.com/v1/agent-search"),
        ("语义重排序API", "https://api.bochaai.com/v1/rerank")
    ]
    
    async with aiohttp.ClientSession() as session:
        for name, url in api_endpoints:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status in [200, 401, 422]:  # 401表示需要认证，422表示参数错误，都说明API可达
                        print(f"  ✅ {name}: 可达 (状态码: {response.status})")
                    else:
                        print(f"  ⚠️  {name}: 异常状态码 {response.status}")
            except asyncio.TimeoutError:
                print(f"  ❌ {name}: 连接超时")
            except Exception as e:
                print(f"  ❌ {name}: 连接失败 - {str(e)}")

def check_environment_setup():
    """检查环境设置."""
    print("🔧 BochaAIClient 优化测试工具")
    print("基于博查AI官方API文档实现")
    print("=" * 60)
    
    # 检查.env文件
    env_file = ".env"
    if os.path.exists(env_file):
        print(f"✅ 找到 {env_file} 文件")
        try:
            with open(env_file, 'r') as f:
                content = f.read()
                if "BOCHA_AI_API_KEY" in content:
                    print("✅ .env文件包含BOCHA_AI_API_KEY配置")
                else:
                    print("⚠️ .env文件不包含BOCHA_AI_API_KEY配置")
        except Exception as e:
            print(f"❌ 读取.env文件失败: {str(e)}")
    else:
        print(f"⚠️ 未找到 {env_file} 文件")
    
    # 检查环境变量
    env_vars = ["BOCHA_AI_API_KEY", "BOCHAAI_API_KEY", "BOCHA_API_KEY"]
    found_valid_key = False
    
    for env_var in env_vars:
        api_key = os.getenv(env_var)
        if api_key:
            is_valid = api_key.startswith("sk-") and len(api_key) > 20
            status = "✅ 有效" if is_valid else "⚠️ 格式可能无效"
            print(f"{status} {env_var}: {api_key[:15]}...")
            if is_valid:
                found_valid_key = True
        else:
            print(f"❌ {env_var}: 未设置")
    
    if not found_valid_key:
        print("\n💡 建议:")
        print("1. 确保.env文件存在且包含: BOCHA_AI_API_KEY=sk-your-key")
        print("2. 或者设置环境变量: export BOCHA_AI_API_KEY=sk-your-key")
    
    print()

def main():
    """主函数."""
    check_environment_setup()
    
    # 运行测试
    asyncio.run(test_api_connectivity())
    asyncio.run(test_bocha_client())

if __name__ == "__main__":
    main()