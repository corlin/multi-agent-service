#!/usr/bin/env python3
"""
多智能体服务一键演示
One-Click Multi-Agent Service Demo
"""

import asyncio
import os
import sys
import time
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, 'src')


def print_banner():
    """打印横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        🚀 多智能体LangGraph服务演示程序                        ║
║           Multi-Agent LangGraph Service Demo                 ║
║                                                              ║
║  🤖 支持多种智能体协作模式                                      ║
║  🔀 智能路由与意图识别                                          ║
║  🌐 OpenAI兼容API接口                                          ║
║  ⚙️ 灵活的工作流编排                                           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


async def quick_demo():
    """快速演示核心功能"""
    from multi_agent_service.config.config_manager import ConfigManager
    from multi_agent_service.models.base import UserRequest
    from multi_agent_service.models.enums import IntentType
    
    print("🎯 快速演示 - 核心功能展示")
    print("="*50)
    
    # 1. 配置加载演示
    print("\n📋 1. 配置加载")
    config_manager = ConfigManager()
    
    # 获取智能体配置
    agent_configs = config_manager.get_all_agent_configs()
    enabled_agents = sum(1 for agent in agent_configs.values() if agent.enabled)
    print(f"✅ 成功加载 {enabled_agents} 个启用的智能体")
    
    # 获取模型配置
    model_configs = config_manager.get_all_model_configs()
    print(f"✅ 成功加载 {len(model_configs)} 个模型配置")
    
    # 获取工作流配置
    workflow_configs = config_manager.get_all_workflow_configs()
    enabled_workflows = sum(1 for workflow in workflow_configs.values() if workflow.enabled)
    print(f"✅ 成功加载 {enabled_workflows} 个启用的工作流")
    
    # 2. 简单意图分析演示（基于规则）
    print("\n🧠 2. 意图分析（基于关键词规则）")
    
    test_queries = [
        "我想购买你们的产品",
        "设备出现故障需要维修", 
        "对服务不满意要投诉"
    ]
    
    # 简单的关键词匹配规则
    intent_rules = {
        "购买|产品|价格|报价|销售": IntentType.SALES_INQUIRY,
        "故障|维修|技术|现场|安装": IntentType.TECHNICAL_SERVICE,
        "投诉|不满意|问题|支持|帮助": IntentType.CUSTOMER_SUPPORT,
        "决策|管理|策略|分析": IntentType.MANAGEMENT_DECISION
    }
    
    for query in test_queries:
        detected_intent = IntentType.GENERAL_INQUIRY
        confidence = 0.5
        
        # 简单的关键词匹配
        for keywords, intent_type in intent_rules.items():
            import re
            if re.search(keywords, query):
                detected_intent = intent_type
                confidence = 0.8
                break
        
        print(f"   📝 '{query}' → {detected_intent.value} ({confidence:.1%})")
    
    # 3. 智能体信息展示
    print("\n🤖 3. 可用智能体")
    for agent_id, agent_config in agent_configs.items():
        if agent_config.enabled:
            print(f"   • {agent_config.name} - {agent_config.description[:50]}...")
    
    # 4. 配置状态信息
    print("\n📊 4. 配置状态")
    config_status = config_manager.get_config_status()
    print(f"   📁 配置目录: {config_status['config_directory']}")
    print(f"   📋 智能体配置: {config_status['agent_configs_count']} 个")
    print(f"   🧠 模型配置: {config_status['model_configs_count']} 个")
    print(f"   ⚙️ 工作流配置: {config_status['workflow_configs_count']} 个")
    print(f"   🕐 最后重载: {config_status['last_reload_time']}")
    
    print(f"\n✅ 核心功能演示完成！")


def check_quick_requirements():
    """检查快速演示的基本要求"""
    print("🔍 环境检查...")
    
    # 检查Python版本
    if sys.version_info < (3, 12):
        print("❌ 需要Python 3.12或更高版本")
        return False
    
    # 检查uv是否可用
    try:
        import subprocess
        result = subprocess.run(['uv', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ uv 可用: {result.stdout.strip()}")
        else:
            print("⚠️ uv 不可用，但可以继续")
    except FileNotFoundError:
        print("⚠️ uv 未安装，建议安装uv包管理器")
    
    # 检查基本依赖
    try:
        import pydantic
        print("✅ 基本依赖检查通过")
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: uv sync")
        return False
    
    # 检查配置文件
    config_files = ["config/agents.json", "config/models.json"]
    for config_file in config_files:
        if not os.path.exists(config_file):
            print(f"❌ 配置文件不存在: {config_file}")
            return False
    
    print("✅ 环境检查通过")
    return True


def show_api_info():
    """显示API信息"""
    load_dotenv()
    
    print("\n🔑 API配置状态:")
    api_keys = {
        "Qwen": os.getenv("QWEN_API_KEY"),
        "DeepSeek": os.getenv("DEEPSEEK_API_KEY"),
        "GLM": os.getenv("GLM_API_KEY")
    }
    
    valid_count = 0
    for provider, key in api_keys.items():
        if key and not key.startswith("your_"):
            print(f"   ✅ {provider}: {key[:10]}...")
            valid_count += 1
        else:
            print(f"   ❌ {provider}: 未配置")
    
    if valid_count > 0:
        print(f"✅ 找到 {valid_count} 个有效的API配置")
    else:
        print("⚠️ 没有找到有效的API配置，某些功能可能受限")
    
    return valid_count > 0


def show_next_steps():
    """显示后续步骤"""
    print("\n🚀 后续步骤:")
    print("   1. 运行完整演示: python run_demo.py")
    print("   2. 启动API服务: uv run uvicorn src.multi_agent_service.main:app --reload")
    print("   3. 查看API文档: http://localhost:8000/docs")
    print("   4. 运行API测试: python api_demo.py")
    print("   5. 交互式聊天: python interactive_demo.py")
    
    print("\n📚 更多信息:")
    print("   • 项目文档: README.md")
    print("   • 演示说明: DEMO_README.md")
    print("   • 配置文件: config/ 目录")


async def main():
    """主函数"""
    print_banner()
    
    print("🎯 这是一个快速演示程序，展示多智能体服务的核心功能")
    print("📝 无需启动HTTP服务，直接展示系统能力")
    
    # 环境检查
    if not check_quick_requirements():
        print("\n❌ 环境检查失败，请解决上述问题后重试")
        return
    
    # API配置检查
    has_api_keys = show_api_info()
    
    if not has_api_keys:
        print("\n⚠️ 建议配置API密钥以获得完整功能体验")
        print("编辑 .env 文件，添加至少一个AI服务提供商的API密钥")
    
    # 询问是否继续
    print(f"\n准备开始演示...")
    try:
        input("按回车键开始，或按 Ctrl+C 退出: ")
    except KeyboardInterrupt:
        print("\n👋 演示取消")
        return
    
    # 运行快速演示
    try:
        start_time = time.time()
        await quick_demo()
        duration = time.time() - start_time
        
        print(f"\n🎉 演示完成！耗时: {duration:.2f}秒")
        
        # 显示后续步骤
        show_next_steps()
        
    except Exception as e:
        print(f"\n❌ 演示过程中出错: {e}")
        print("请检查配置和依赖是否正确安装")
    
    print(f"\n👋 感谢使用多智能体服务演示程序！")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n👋 程序被用户中断")
    except Exception as e:
        print(f"\n❌ 程序出错: {e}")
        print("请检查环境配置和依赖安装")