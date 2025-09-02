#!/usr/bin/env python3
"""
多智能体服务交互式演示程序
Interactive Multi-Agent Service Demo
"""

import asyncio
import json
import os
import sys
import time
from typing import Dict, Any, List
from dotenv import load_dotenv
import httpx

# Add src to path
sys.path.insert(0, 'src')

from multi_agent_service.main import app
import uvicorn
from threading import Thread
import signal


class DemoClient:
    """演示客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        response = await self.client.get(f"{self.base_url}/api/v1/health")
        return response.json()
    
    async def chat_completion(self, messages: List[Dict], model: str = "multi-agent-service") -> Dict[str, Any]:
        """聊天完成接口"""
        data = {
            "messages": messages,
            "model": model,
            "max_tokens": 2000,
            "temperature": 0.7
        }
        response = await self.client.post(f"{self.base_url}/api/v1/chat/completions", json=data)
        return response.json()
    
    async def route_agent(self, content: str, user_id: str = "demo_user") -> Dict[str, Any]:
        """智能体路由"""
        data = {
            "content": content,
            "user_id": user_id,
            "priority": "medium"
        }
        response = await self.client.post(f"{self.base_url}/api/v1/agents/route", json=data)
        return response.json()
    
    async def execute_workflow(self, workflow_type: str, task_description: str, 
                             participating_agents: List[str]) -> Dict[str, Any]:
        """执行工作流"""
        data = {
            "workflow_type": workflow_type,
            "task_description": task_description,
            "participating_agents": participating_agents
        }
        response = await self.client.post(f"{self.base_url}/api/v1/workflows/execute", json=data)
        return response.json()
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """获取智能体状态"""
        response = await self.client.get(f"{self.base_url}/api/v1/agents/status")
        return response.json()
    
    async def get_agent_types(self) -> Dict[str, Any]:
        """获取智能体类型"""
        response = await self.client.get(f"{self.base_url}/api/v1/agents/types")
        return response.json()
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()


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


def print_response(response: Dict[str, Any], title: str = "响应"):
    """格式化打印响应"""
    print(f"\n🔍 {title}:")
    print(json.dumps(response, ensure_ascii=False, indent=2))


async def wait_for_service(client: DemoClient, max_attempts: int = 30):
    """等待服务启动"""
    print("⏳ 等待服务启动...")
    
    for attempt in range(max_attempts):
        try:
            await client.health_check()
            print("✅ 服务已启动")
            return True
        except Exception:
            if attempt < max_attempts - 1:
                await asyncio.sleep(1)
            else:
                print("❌ 服务启动超时")
                return False
    
    return False


async def demo_health_check(client: DemoClient):
    """演示健康检查"""
    print_section("健康检查")
    
    try:
        health = await client.health_check()
        print_response(health, "健康状态")
        
        if health.get("status") == "healthy":
            print("✅ 系统健康")
        else:
            print("⚠️ 系统状态异常")
    
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")


async def demo_agent_info(client: DemoClient):
    """演示智能体信息"""
    print_section("智能体信息")
    
    try:
        # 获取智能体类型
        types = await client.get_agent_types()
        print_response(types, "智能体类型")
        
        # 获取智能体状态
        status = await client.get_agent_status()
        print_response(status, "智能体状态")
        
        # 统计信息
        if "agents" in status:
            total_agents = len(status["agents"])
            enabled_agents = sum(1 for agent in status["agents"].values() 
                               if agent.get("enabled", False))
            print(f"\n📊 统计: {enabled_agents}/{total_agents} 个智能体已启用")
    
    except Exception as e:
        print(f"❌ 获取智能体信息失败: {e}")


async def demo_chat_completion(client: DemoClient):
    """演示聊天完成"""
    print_section("聊天完成演示")
    
    test_messages = [
        [{"role": "user", "content": "你好，我想了解你们的产品"}],
        [{"role": "user", "content": "我遇到了技术问题，需要帮助"}],
        [{"role": "user", "content": "我想投诉一个服务问题"}]
    ]
    
    for i, messages in enumerate(test_messages, 1):
        print(f"\n🔍 测试 {i}: {messages[0]['content']}")
        
        try:
            start_time = time.time()
            response = await client.chat_completion(messages)
            duration = time.time() - start_time
            
            if "choices" in response and response["choices"]:
                content = response["choices"][0].get("message", {}).get("content", "")
                print(f"✅ 回复 ({duration:.2f}s): {content[:200]}...")
                
                if "usage" in response:
                    usage = response["usage"]
                    print(f"📊 Token使用: {usage}")
            else:
                print(f"❌ 无有效回复: {response}")
        
        except Exception as e:
            print(f"❌ 聊天失败: {e}")


async def demo_agent_routing(client: DemoClient):
    """演示智能体路由"""
    print_section("智能体路由演示")
    
    test_queries = [
        "我想购买你们的产品，请提供报价",
        "设备出现故障，需要技术支持",
        "对服务不满意，要投诉",
        "需要制定新的业务策略",
        "安排现场维修服务"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 查询 {i}: {query}")
        
        try:
            start_time = time.time()
            response = await client.route_agent(query, f"user_{i}")
            duration = time.time() - start_time
            
            if "recommended_agent" in response:
                agent_info = response["recommended_agent"]
                agent_name = agent_info.get("name", "未知")
                confidence = response.get("confidence", 0)
                
                print(f"✅ 推荐智能体 ({duration:.2f}s): {agent_name}")
                print(f"📊 置信度: {confidence:.2%}")
                
                if "reasoning" in response:
                    print(f"💭 推理: {response['reasoning']}")
            else:
                print(f"❌ 路由失败: {response}")
        
        except Exception as e:
            print(f"❌ 路由失败: {e}")


async def demo_workflows(client: DemoClient):
    """演示工作流执行"""
    print_section("工作流执行演示")
    
    workflows = [
        {
            "type": "sequential",
            "description": "处理客户销售咨询",
            "agents": ["sales_agent", "customer_support_agent"]
        },
        {
            "type": "parallel", 
            "description": "综合服务响应",
            "agents": ["sales_agent", "customer_support_agent", "field_service_agent"]
        },
        {
            "type": "hierarchical",
            "description": "紧急问题处理",
            "agents": ["coordinator_agent", "customer_support_agent", "manager_agent"]
        }
    ]
    
    for i, workflow in enumerate(workflows, 1):
        print(f"\n🔍 工作流 {i}: {workflow['type']} - {workflow['description']}")
        
        try:
            start_time = time.time()
            response = await client.execute_workflow(
                workflow["type"],
                workflow["description"], 
                workflow["agents"]
            )
            duration = time.time() - start_time
            
            if "workflow_id" in response:
                workflow_id = response["workflow_id"]
                status = response.get("status", "unknown")
                
                print(f"✅ 工作流启动 ({duration:.2f}s)")
                print(f"📋 ID: {workflow_id}")
                print(f"📊 状态: {status}")
                
                if "participating_agents" in response:
                    agents = response["participating_agents"]
                    print(f"🤖 参与智能体: {', '.join(agents)}")
            else:
                print(f"❌ 工作流启动失败: {response}")
        
        except Exception as e:
            print(f"❌ 工作流执行失败: {e}")


async def demo_interactive_chat(client: DemoClient):
    """交互式聊天演示"""
    print_section("交互式聊天")
    print("💬 输入消息与智能体对话 (输入 'quit' 退出)")
    
    conversation = []
    
    while True:
        try:
            user_input = input("\n👤 您: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("👋 再见！")
                break
            
            if not user_input:
                continue
            
            conversation.append({"role": "user", "content": user_input})
            
            print("🤖 智能体正在思考...")
            start_time = time.time()
            
            response = await client.chat_completion(conversation)
            duration = time.time() - start_time
            
            if "choices" in response and response["choices"]:
                content = response["choices"][0].get("message", {}).get("content", "")
                print(f"🤖 智能体 ({duration:.2f}s): {content}")
                
                conversation.append({"role": "assistant", "content": content})
                
                # 限制对话历史长度
                if len(conversation) > 10:
                    conversation = conversation[-10:]
            else:
                print("❌ 智能体无法回复")
        
        except KeyboardInterrupt:
            print("\n👋 再见！")
            break
        except Exception as e:
            print(f"❌ 对话错误: {e}")


def start_server():
    """启动服务器"""
    print("🚀 启动多智能体服务...")
    uvicorn.run(
        "src.multi_agent_service.main:app",
        host="0.0.0.0",
        port=8000,
        log_level="warning"  # 减少日志输出
    )


async def run_demos():
    """运行所有演示"""
    load_dotenv()
    
    # 检查API配置
    api_keys = {
        "QWEN_API_KEY": os.getenv("QWEN_API_KEY"),
        "DEEPSEEK_API_KEY": os.getenv("DEEPSEEK_API_KEY"), 
        "GLM_API_KEY": os.getenv("GLM_API_KEY")
    }
    
    valid_keys = sum(1 for key in api_keys.values() 
                    if key and not key.startswith("your_"))
    
    print(f"🔑 找到 {valid_keys} 个有效的API配置")
    
    if valid_keys == 0:
        print("❌ 警告: 没有找到有效的API配置，某些功能可能无法正常工作")
        print("请检查 .env 文件中的API密钥配置")
    
    client = DemoClient()
    
    try:
        # 等待服务启动
        if not await wait_for_service(client):
            print("❌ 无法连接到服务，请确保服务正在运行")
            return
        
        # 运行演示
        demos = [
            ("健康检查", demo_health_check),
            ("智能体信息", demo_agent_info),
            ("聊天完成", demo_chat_completion),
            ("智能体路由", demo_agent_routing),
            ("工作流执行", demo_workflows)
        ]
        
        results = []
        
        for demo_name, demo_func in demos:
            try:
                print_header(demo_name)
                start_time = time.time()
                
                await demo_func(client)
                
                duration = time.time() - start_time
                print(f"\n✅ {demo_name} 完成 (耗时: {duration:.2f}秒)")
                results.append((demo_name, True, duration))
                
            except Exception as e:
                print(f"\n❌ {demo_name} 失败: {e}")
                results.append((demo_name, False, 0))
        
        # 显示结果总结
        print_header("演示总结")
        
        successful = sum(1 for _, success, _ in results if success)
        total = len(results)
        
        print(f"📊 演示结果: {successful}/{total} 成功")
        
        for demo_name, success, duration in results:
            status = "✅" if success else "❌"
            time_info = f"({duration:.2f}s)" if success else ""
            print(f"   {status} {demo_name} {time_info}")
        
        # 交互式聊天
        if successful > 0:
            print(f"\n🎉 基础演示完成！")
            
            while True:
                choice = input(f"\n选择操作:\n1. 交互式聊天\n2. 退出\n请输入选择 (1-2): ").strip()
                
                if choice == "1":
                    await demo_interactive_chat(client)
                elif choice == "2":
                    break
                else:
                    print("❌ 无效选择，请重新输入")
        
    finally:
        await client.close()


def main():
    """主函数"""
    print_header("多智能体服务交互式演示")
    
    print("🎯 本演示将展示以下功能:")
    print("   • 系统健康检查")
    print("   • 智能体信息查询") 
    print("   • OpenAI兼容聊天接口")
    print("   • 智能体路由功能")
    print("   • 工作流执行")
    print("   • 交互式对话")
    
    # 启动服务器线程
    server_thread = Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # 等待一下让服务器启动
    time.sleep(3)
    
    try:
        # 运行演示
        asyncio.run(run_demos())
    except KeyboardInterrupt:
        print("\n👋 演示被用户中断")
    except Exception as e:
        print(f"\n❌ 演示出错: {e}")
    
    print("\n🎉 演示结束，感谢使用多智能体服务！")


if __name__ == "__main__":
    main()