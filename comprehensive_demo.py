#!/usr/bin/env python3
"""
全面的多提供商AI服务演示
Comprehensive Multi-Provider AI Service Demo
"""

import asyncio
import os
import sys
import time
from typing import List, Dict, Any
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, 'src')

from multi_agent_service.models.model_service import ModelConfig, ModelRequest
from multi_agent_service.models.enums import ModelProvider
from multi_agent_service.services.model_router import ModelRouter, LoadBalancingStrategy
from multi_agent_service.services import providers


def print_header(title: str, width: int = 80):
    """打印标题"""
    print(f"\n{'='*width}")
    print(f"🚀 {title.center(width-4)}")
    print(f"{'='*width}")


def print_section(title: str, width: int = 60):
    """打印章节"""
    print(f"\n{'-'*width}")
    print(f"📋 {title}")
    print(f"{'-'*width}")


async def setup_router() -> ModelRouter:
    """设置路由器"""
    load_dotenv()
    
    configs = [
        ModelConfig(
            provider=ModelProvider.QWEN,
            model_name="qwen-turbo",
            api_key=os.getenv("QWEN_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            priority=1,
            enabled=True
        ),
        ModelConfig(
            provider=ModelProvider.DEEPSEEK,
            model_name="deepseek-chat",
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com/v1",
            priority=2,
            enabled=True
        ),
        ModelConfig(
            provider=ModelProvider.GLM,
            model_name="glm-4-flash",
            api_key=os.getenv("GLM_API_KEY"),
            base_url="https://open.bigmodel.cn/api/paas/v4",
            priority=3,
            enabled=True
        )
    ]
    
    return ModelRouter(configs, LoadBalancingStrategy.PRIORITY)


async def demo_provider_comparison():
    """演示提供商对比"""
    print_section("AI提供商能力对比")
    
    router = await setup_router()
    
    try:
        questions = [
            "什么是机器学习？",
            "解释深度学习的概念",
            "人工智能的应用领域"
        ]
        
        for i, question in enumerate(questions, 1):
            print(f"\n🔍 问题 {i}: {question}")
            print("=" * 60)
            
            # 为每个提供商单独测试
            for client_id, client in router.clients.items():
                provider_name = client_id.split(':')[0].upper()
                
                try:
                    request = ModelRequest(
                        messages=[{"role": "user", "content": question}],
                        max_tokens=100,
                        temperature=0.7
                    )
                    
                    start_time = time.time()
                    response = await client.chat_completion(request)
                    response_time = time.time() - start_time
                    
                    if response.choices:
                        content = response.choices[0].get("message", {}).get("content", "")
                        # 截断长回复
                        if len(content) > 150:
                            content = content[:150] + "..."
                    
                    print(f"\n🤖 {provider_name}:")
                    print(f"   回复: {content}")
                    print(f"   响应时间: {response_time:.2f}秒")
                    
                    if response.usage:
                        usage = response.usage
                        total_tokens = usage.get('total_tokens', 0)
                        print(f"   Token使用: {total_tokens}")
                    
                except Exception as e:
                    print(f"\n❌ {provider_name}: {str(e)}")
    
    finally:
        await router.close()


async def demo_load_balancing():
    """演示负载均衡"""
    print_section("智能负载均衡演示")
    
    strategies = [
        (LoadBalancingStrategy.PRIORITY, "优先级策略"),
        (LoadBalancingStrategy.ROUND_ROBIN, "轮询策略"),
        (LoadBalancingStrategy.RESPONSE_TIME, "响应时间策略")
    ]
    
    for strategy, name in strategies:
        print(f"\n🎯 {name}")
        
        router = await setup_router()
        router.set_strategy(strategy)
        
        try:
            # 发送多个请求
            for i in range(3):
                request = ModelRequest(
                    messages=[{"role": "user", "content": f"这是第{i+1}个测试请求"}],
                    max_tokens=30,
                    temperature=0.7
                )
                
                response = await router.chat_completion(request)
                print(f"   请求{i+1} → {response.provider.value.upper()}")
        
        finally:
            await router.close()


async def demo_failover():
    """演示故障转移"""
    print_section("故障转移机制演示")
    
    router = await setup_router()
    
    try:
        print("🔧 初始状态: 所有提供商启用")
        
        # 正常请求
        request = ModelRequest(
            messages=[{"role": "user", "content": "测试正常请求"}],
            max_tokens=30
        )
        
        response = await router.chat_completion(request)
        print(f"✅ 正常请求成功，使用: {response.provider.value.upper()}")
        
        # 禁用第一个提供商
        first_client_id = list(router.clients.keys())[0]
        first_provider = first_client_id.split(':')[0].upper()
        
        print(f"\n🚫 禁用 {first_provider}")
        router.configs[first_client_id].enabled = False
        
        # 故障转移请求
        response = await router.chat_completion(request)
        print(f"🔄 故障转移成功，使用: {response.provider.value.upper()}")
        
        # 检查故障转移事件
        events = router.get_failover_events()
        if events:
            latest = events[-1]
            print(f"📝 记录: {latest.original_provider.value} → {latest.fallback_provider.value}")
        
        # 恢复提供商
        print(f"\n🔄 恢复 {first_provider}")
        router.configs[first_client_id].enabled = True
        
        response = await router.chat_completion(request)
        print(f"✅ 恢复成功，使用: {response.provider.value.upper()}")
    
    finally:
        await router.close()


async def demo_performance():
    """演示性能监控"""
    print_section("性能监控演示")
    
    router = await setup_router()
    
    try:
        # 发送多个请求收集性能数据
        questions = [
            "什么是云计算？",
            "解释区块链技术",
            "人工智能的未来",
            "量子计算原理",
            "5G技术优势"
        ]
        
        print("📊 发送测试请求收集性能数据...")
        
        for question in questions:
            request = ModelRequest(
                messages=[{"role": "user", "content": question}],
                max_tokens=50,
                temperature=0.7
            )
            
            response = await router.chat_completion(request)
            print(f"   ✓ {response.provider.value.upper()}")
        
        # 显示性能统计
        print(f"\n📈 性能统计:")
        print(f"{'提供商':<12} {'请求数':<8} {'成功数':<8} {'平均响应时间':<12} {'可用性':<8}")
        print("-" * 60)
        
        metrics = router.get_metrics()
        for client_id, client_metrics in metrics.items():
            provider = client_id.split(':')[0].upper()
            total = client_metrics.get('total_requests', 0)
            success = client_metrics.get('successful_requests', 0)
            avg_time = client_metrics.get('average_response_time', 0)
            availability = client_metrics.get('availability', 0)
            
            print(f"{provider:<12} {total:<8} {success:<8} {avg_time:<12.2f} {availability:<8.1%}")
    
    finally:
        await router.close()


async def demo_health_check():
    """演示健康检查"""
    print_section("健康检查演示")
    
    router = await setup_router()
    
    try:
        print("🏥 检查所有提供商健康状态...")
        
        health_status = await router.health_check()
        
        print(f"\n📊 健康检查结果:")
        for client_id, is_healthy in health_status.items():
            provider = client_id.split(':')[0].upper()
            status = "✅ 健康" if is_healthy else "❌ 不健康"
            print(f"   {provider}: {status}")
        
        healthy_count = sum(1 for status in health_status.values() if status)
        total_count = len(health_status)
        
        print(f"\n📈 健康统计: {healthy_count}/{total_count} 个提供商健康")
        
        if healthy_count == total_count:
            print("🎉 所有提供商都处于健康状态！")
        else:
            print(f"⚠️  有 {total_count - healthy_count} 个提供商需要检查")
    
    finally:
        await router.close()


async def main():
    """主演示函数"""
    print_header("多提供商AI服务全面演示")
    
    # 检查配置
    load_dotenv()
    
    providers_info = [
        ("Qwen", os.getenv("QWEN_API_KEY")),
        ("DeepSeek", os.getenv("DEEPSEEK_API_KEY")),
        ("GLM", os.getenv("GLM_API_KEY"))
    ]
    
    print("🔑 API配置检查:")
    valid_count = 0
    for name, key in providers_info:
        if key and key != f"your_{name.lower()}_api_key_here":
            print(f"   ✅ {name}: {key[:10]}...")
            valid_count += 1
        else:
            print(f"   ❌ {name}: 未配置")
    
    if valid_count == 0:
        print("\n❌ 错误: 没有找到有效的API配置")
        return
    
    print(f"\n🎯 找到 {valid_count} 个有效配置，开始演示...")
    
    # 演示列表
    demos = [
        ("AI提供商能力对比", demo_provider_comparison),
        ("智能负载均衡", demo_load_balancing),
        ("故障转移机制", demo_failover),
        ("性能监控", demo_performance),
        ("健康检查", demo_health_check)
    ]
    
    results = []
    total_start_time = time.time()
    
    for demo_name, demo_func in demos:
        try:
            print_header(demo_name)
            
            start_time = time.time()
            await demo_func()
            duration = time.time() - start_time
            
            print(f"\n✅ {demo_name} 完成 (耗时: {duration:.2f}秒)")
            results.append((demo_name, True, duration))
            
        except Exception as e:
            print(f"\n❌ {demo_name} 失败: {str(e)}")
            results.append((demo_name, False, 0))
    
    # 总结
    total_duration = time.time() - total_start_time
    
    print_header("演示总结")
    
    successful = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    print(f"📊 演示结果: {successful}/{total} 成功")
    print(f"⏱️  总耗时: {total_duration:.2f}秒")
    
    print(f"\n📋 详细结果:")
    for demo_name, success, duration in results:
        status = "✅" if success else "❌"
        time_info = f"({duration:.2f}s)" if success else ""
        print(f"   {status} {demo_name} {time_info}")
    
    if successful == total:
        print(f"\n🎉 所有演示成功！多提供商AI服务系统完全就绪！")
        print(f"\n🚀 系统特性:")
        print(f"   • 支持 Qwen、DeepSeek、GLM 三大AI提供商")
        print(f"   • OpenAI兼容API格式")
        print(f"   • 智能负载均衡 (优先级/轮询/响应时间)")
        print(f"   • 自动故障转移机制")
        print(f"   • 实时性能监控")
        print(f"   • 健康检查功能")
        print(f"   • 统一错误处理")
    else:
        print(f"\n⚠️  部分演示失败，请检查网络和配置")


if __name__ == "__main__":
    asyncio.run(main())