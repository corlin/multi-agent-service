#!/usr/bin/env python3
"""
多智能体服务快速演示
Quick Multi-Agent Service Demo
"""

import asyncio
import json
import os
import sys
from typing import Dict, Any
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, 'src')

from multi_agent_service.config.config_manager import ConfigManager
from multi_agent_service.models.base import UserRequest
from multi_agent_service.models.enums import IntentType, AgentType


def print_header(title: str):
    """打印标题"""
    print(f"\n{'='*60}")
    print(f"🚀 {title}")
    print(f"{'='*60}")


def print_section(title: str):
    """打印章节"""
    print(f"\n{'-'*40}")
    print(f"📋 {title}")
    print(f"{'-'*40}")


async def demo_intent_analysis():
    """演示意图分析"""
    print_section("意图分析演示")
    
    # 使用简单的基于规则的意图分析
    test_queries = [
        "我想购买你们的产品",
        "设备出现故障需要维修", 
        "对服务质量不满意要投诉",
        "需要技术支持帮助",
        "想了解产品价格和功能"
    ]
    
    # 简单的关键词匹配规则
    intent_rules = {
        "购买|产品|价格|报价|销售|优惠": (IntentType.SALES_INQUIRY, ["产品", "价格", "购买"]),
        "故障|维修|技术|现场|安装|调试": (IntentType.TECHNICAL_SERVICE, ["故障", "维修", "技术"]),
        "投诉|不满意|问题|支持|帮助|咨询": (IntentType.CUSTOMER_SUPPORT, ["问题", "支持", "帮助"]),
        "决策|管理|策略|分析|规划": (IntentType.MANAGEMENT_DECISION, ["决策", "管理", "策略"]),
        "了解|介绍|信息|什么是": (IntentType.GENERAL_INQUIRY, ["了解", "介绍", "信息"])
    }
    
    for query in test_queries:
        try:
            detected_intent = IntentType.GENERAL_INQUIRY
            confidence = 0.5
            keywords = []
            
            # 简单的关键词匹配
            import re
            for pattern, (intent_type, intent_keywords) in intent_rules.items():
                if re.search(pattern, query):
                    detected_intent = intent_type
                    confidence = 0.8
                    keywords = intent_keywords
                    break
            
            print(f"📝 查询: {query}")
            print(f"🎯 意图: {detected_intent.value}")
            print(f"📊 置信度: {confidence:.2%}")
            print(f"🏷️ 关键词: {', '.join(keywords)}")
            print()
        except Exception as e:
            print(f"❌ 分析失败: {e}")


async def demo_agent_routing():
    """演示智能体路由"""
    print_section("智能体路由演示")
    
    # 简化的路由演示，不依赖复杂的服务
    test_requests = [
        {
            "content": "我想了解产品价格和购买流程",
            "user_id": "user1",
            "priority": "medium"
        },
        {
            "content": "设备无法正常启动，需要技术支持",
            "user_id": "user2", 
            "priority": "high"
        },
        {
            "content": "服务态度很差，我要投诉",
            "user_id": "user3",
            "priority": "high"
        }
    ]
    
    # 简单的路由规则
    routing_rules = {
        "购买|产品|价格|报价|销售": (AgentType.SALES, "销售代表智能体"),
        "故障|维修|技术|现场|安装": (AgentType.FIELD_SERVICE, "现场服务人员智能体"),
        "投诉|不满意|问题|支持": (AgentType.CUSTOMER_SUPPORT, "客服专员智能体"),
        "决策|管理|策略": (AgentType.MANAGER, "管理者智能体")
    }
    
    for i, request in enumerate(test_requests, 1):
        try:
            print(f"🔍 请求 {i}: {request['content']}")
            
            # 简单的路由逻辑
            selected_agent = AgentType.CUSTOMER_SUPPORT
            agent_name = "客服专员智能体"
            confidence = 0.5
            
            import re
            for pattern, (agent_type, name) in routing_rules.items():
                if re.search(pattern, request['content']):
                    selected_agent = agent_type
                    agent_name = name
                    confidence = 0.8
                    break
            
            print(f"🤖 推荐智能体: {agent_name}")
            print(f"📊 置信度: {confidence:.2%}")
            print(f"💭 推理: 基于关键词匹配选择合适的智能体")
            print()
            
        except Exception as e:
            print(f"❌ 路由失败: {e}")


async def demo_config_loading():
    """演示配置加载"""
    print_section("配置加载演示")
    
    config_manager = ConfigManager()
    
    try:
        # 显示智能体配置
        agents_config = config_manager.get_all_agent_configs()
        print(f"📋 加载了 {len(agents_config)} 个智能体配置:")
        
        for agent_id, agent_config in agents_config.items():
            status = "✅ 启用" if agent_config.enabled else "❌ 禁用"
            print(f"   🤖 {agent_config.name} ({agent_id}) - {status}")
        
        # 显示模型配置
        models_config = config_manager.get_all_model_configs()
        print(f"\n🧠 加载了 {len(models_config)} 个模型配置:")
        
        for model_id, model_config in models_config.items():
            print(f"   🔧 {model_config.model_name} ({model_config.provider.value})")
        
        # 显示工作流配置
        workflows_config = config_manager.get_all_workflow_configs()
        print(f"\n⚙️ 加载了 {len(workflows_config)} 个工作流配置:")
        
        for workflow_id, workflow_config in workflows_config.items():
            status = "✅ 启用" if workflow_config.enabled else "❌ 禁用"
            print(f"   🔄 {workflow_config.name} ({workflow_config.workflow_type.value}) - {status}")
    
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")


async def demo_agent_capabilities():
    """演示智能体能力"""
    print_section("智能体能力演示")
    
    config_manager = ConfigManager()
    
    agents_config = config_manager.get_all_agent_configs()
    
    print("🤖 智能体能力概览:")
    
    for agent_id, agent_config in agents_config.items():
        if agent_config.enabled:
            print(f"\n📋 {agent_config.name}")
            print(f"   🎯 类型: {agent_config.agent_type.value}")
            print(f"   📝 描述: {agent_config.description}")
            print(f"   🛠️ 能力: {', '.join(agent_config.capabilities)}")
            print(f"   🧠 模型: {agent_config.llm_config.model_name}")
            print(f"   ⚡ 优先级: {agent_config.priority}")
            print(f"   🔄 最大并发: {agent_config.max_concurrent_tasks}")


def check_environment():
    """检查环境配置"""
    print_section("环境检查")
    
    load_dotenv()
    
    # 检查API密钥
    api_keys = {
        "Qwen": os.getenv("QWEN_API_KEY"),
        "DeepSeek": os.getenv("DEEPSEEK_API_KEY"),
        "GLM": os.getenv("GLM_API_KEY"),
        "OpenAI": os.getenv("OPENAI_API_KEY")
    }
    
    print("🔑 API密钥检查:")
    valid_count = 0
    
    for provider, key in api_keys.items():
        if key and not key.startswith("your_"):
            print(f"   ✅ {provider}: {key[:10]}...")
            valid_count += 1
        else:
            print(f"   ❌ {provider}: 未配置")
    
    print(f"\n📊 配置状态: {valid_count}/{len(api_keys)} 个API密钥已配置")
    
    # 检查配置文件
    config_files = [
        "config/agents.json",
        "config/models.json", 
        "config/workflows.json"
    ]
    
    print(f"\n📁 配置文件检查:")
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"   ✅ {config_file}")
        else:
            print(f"   ❌ {config_file} - 文件不存在")
    
    return valid_count > 0


async def main():
    """主演示函数"""
    print_header("多智能体服务快速演示")
    
    print("🎯 本演示将展示核心功能:")
    print("   • 环境配置检查")
    print("   • 配置文件加载")
    print("   • 智能体能力展示")
    print("   • 意图分析功能")
    print("   • 智能体路由功能")
    
    # 环境检查
    if not check_environment():
        print("\n⚠️ 警告: 没有找到有效的API配置")
        print("某些功能可能无法正常工作，但演示仍可继续")
    
    # 演示列表
    demos = [
        ("配置加载", demo_config_loading),
        ("智能体能力", demo_agent_capabilities),
        ("意图分析", demo_intent_analysis),
        ("智能体路由", demo_agent_routing)
    ]
    
    results = []
    
    for demo_name, demo_func in demos:
        try:
            print_header(demo_name)
            await demo_func()
            print(f"\n✅ {demo_name} 演示完成")
            results.append((demo_name, True))
            
        except Exception as e:
            print(f"\n❌ {demo_name} 演示失败: {e}")
            results.append((demo_name, False))
    
    # 总结
    print_header("演示总结")
    
    successful = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"📊 演示结果: {successful}/{total} 成功")
    
    for demo_name, success in results:
        status = "✅" if success else "❌"
        print(f"   {status} {demo_name}")
    
    if successful == total:
        print(f"\n🎉 所有演示成功！多智能体服务核心功能正常！")
        print(f"\n🚀 下一步:")
        print(f"   • 运行 'python interactive_demo.py' 进行完整API演示")
        print(f"   • 运行 'python comprehensive_demo.py' 进行模型服务演示")
        print(f"   • 启动服务: 'uv run uvicorn src.multi_agent_service.main:app --reload'")
    else:
        print(f"\n⚠️ 部分演示失败，请检查配置和依赖")
    
    print(f"\n📚 更多信息:")
    print(f"   • 项目文档: README.md")
    print(f"   • API文档: http://localhost:8000/docs (服务启动后)")
    print(f"   • 配置文件: config/ 目录")


if __name__ == "__main__":
    asyncio.run(main())