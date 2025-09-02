#!/usr/bin/env python3
"""
交互式多智能体演示
Interactive Multi-Agent Demo

用户可以选择不同场景，实时体验多智能体协作
"""

import asyncio
import os
import time
from typing import Dict, Any, List
from dotenv import load_dotenv
import httpx


class InteractiveAgentDemo:
    """交互式智能体演示"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)
        
        self.agents = {
            "1": ("销售代表", "负责产品咨询、报价和客户关系管理"),
            "2": ("客服专员", "负责问题解答、技术支持和客户服务"),
            "3": ("现场服务工程师", "负责技术服务、现场支持和设备维护"),
            "4": ("管理者", "负责决策分析、战略规划和政策制定"),
            "5": ("协调员", "负责任务协调、智能体管理和流程优化")
        }
    
    def print_header(self, title: str):
        """打印标题"""
        print(f"\n{'='*60}")
        print(f"🚀 {title}")
        print(f"{'='*60}")
    
    def print_agents(self):
        """显示可用智能体"""
        print("\n🤖 可用智能体:")
        for key, (name, desc) in self.agents.items():
            print(f"  {key}. {name} - {desc}")
    
    async def chat_with_agent(self, content: str, agent_role: str) -> str:
        """与指定智能体对话"""
        messages = [
            {"role": "system", "content": f"你是{agent_role}，请以专业的身份回复用户"},
            {"role": "user", "content": content}
        ]
        
        data = {
            "messages": messages,
            "model": "multi-agent-service",
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        try:
            response = await self.client.post(f"{self.base_url}/api/v1/chat/completions", json=data)
            result = response.json()
            
            if "choices" in result and result["choices"]:
                return result["choices"][0]["message"]["content"]
            return "抱歉，我现在无法回复"
            
        except Exception as e:
            return f"连接错误: {e}"
    
    async def route_query(self, content: str) -> Dict[str, Any]:
        """智能路由查询"""
        data = {
            "content": content,
            "user_id": "interactive_user",
            "priority": "medium"
        }
        
        try:
            response = await self.client.post(f"{self.base_url}/api/v1/agents/route", json=data)
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def single_agent_chat(self):
        """单智能体对话"""
        self.print_header("单智能体对话")
        self.print_agents()
        
        while True:
            agent_choice = input("\n选择智能体 (1-5) 或 'q' 退出: ").strip()
            
            if agent_choice.lower() == 'q':
                break
            
            if agent_choice not in self.agents:
                print("❌ 无效选择，请重新输入")
                continue
            
            agent_name, agent_desc = self.agents[agent_choice]
            print(f"\n🤖 已选择: {agent_name}")
            print(f"📋 职责: {agent_desc}")
            
            while True:
                user_input = input(f"\n👤 您 (输入 'back' 返回): ").strip()
                
                if user_input.lower() == 'back':
                    break
                
                if not user_input:
                    continue
                
                print("🤖 正在思考...")
                start_time = time.time()
                
                response = await self.chat_with_agent(user_input, agent_name)
                duration = time.time() - start_time
                
                print(f"\n🤖 {agent_name} ({duration:.1f}s):")
                print(f"   {response}")
    
    async def smart_routing_demo(self):
        """智能路由演示"""
        self.print_header("智能路由演示")
        print("💡 输入任何问题，系统会自动推荐最合适的智能体")
        
        while True:
            user_input = input(f"\n👤 您的问题 (输入 'q' 退出): ").strip()
            
            if user_input.lower() == 'q':
                break
            
            if not user_input:
                continue
            
            print("🎯 正在分析并路由...")
            start_time = time.time()
            
            # 获取路由建议
            route_result = await self.route_query(user_input)
            route_time = time.time() - start_time
            
            if "recommended_agent" in route_result:
                agent_info = route_result["recommended_agent"]
                agent_name = agent_info.get("name", "未知智能体")
                confidence = route_result.get("confidence", 0)
                
                print(f"\n🎯 路由结果 ({route_time:.1f}s):")
                print(f"   推荐智能体: {agent_name}")
                print(f"   置信度: {confidence:.1%}")
                
                if "reasoning" in route_result:
                    print(f"   推理: {route_result['reasoning']}")
                
                # 询问是否与推荐的智能体对话
                confirm = input(f"\n是否与 {agent_name} 对话? (y/n): ").strip().lower()
                
                if confirm == 'y':
                    print("🤖 正在回复...")
                    chat_start = time.time()
                    
                    response = await self.chat_with_agent(user_input, agent_name)
                    chat_time = time.time() - chat_start
                    
                    print(f"\n🤖 {agent_name} ({chat_time:.1f}s):")
                    print(f"   {response}")
            else:
                print(f"❌ 路由失败: {route_result}")
    
    async def scenario_demo(self):
        """场景演示"""
        self.print_header("预设场景演示")
        
        scenarios = {
            "1": {
                "name": "销售咨询",
                "description": "客户询问产品信息和价格",
                "query": "我想了解你们的AI客服系统，包括功能特点和价格",
                "agents": ["销售代表", "客服专员"]
            },
            "2": {
                "name": "技术支持",
                "description": "系统故障需要技术支持",
                "query": "我们的系统无法正常访问，所有API都返回错误",
                "agents": ["客服专员", "现场服务工程师"]
            },
            "3": {
                "name": "投诉处理",
                "description": "客户投诉需要升级处理",
                "query": "对你们的服务很不满意，响应慢，问题解决不及时",
                "agents": ["协调员", "管理者"]
            },
            "4": {
                "name": "紧急响应",
                "description": "系统紧急故障需要快速响应",
                "query": "紧急！全系统宕机，大量客户受影响，需要立即处理",
                "agents": ["协调员", "现场服务工程师", "客服专员"]
            },
            "5": {
                "name": "战略规划",
                "description": "制定业务发展战略",
                "query": "需要制定2025年AI服务发展战略，请提供专业建议",
                "agents": ["销售代表", "管理者", "协调员"]
            }
        }
        
        while True:
            print("\n📋 可选场景:")
            for key, scenario in scenarios.items():
                print(f"  {key}. {scenario['name']} - {scenario['description']}")
            
            choice = input(f"\n选择场景 (1-5) 或 'q' 退出: ").strip()
            
            if choice.lower() == 'q':
                break
            
            if choice not in scenarios:
                print("❌ 无效选择，请重新输入")
                continue
            
            scenario = scenarios[choice]
            print(f"\n🎬 场景: {scenario['name']}")
            print(f"📝 描述: {scenario['description']}")
            print(f"👤 客户问题: {scenario['query']}")
            
            # 依次让相关智能体处理
            conversation = []
            for i, agent_name in enumerate(scenario['agents']):
                print(f"\n🤖 {agent_name} 正在处理...")
                start_time = time.time()
                
                # 构建上下文
                if i == 0:
                    # 第一个智能体直接处理原始问题
                    context = scenario['query']
                else:
                    # 后续智能体基于之前的对话
                    context = f"客户问题: {scenario['query']}\n"
                    for j, (prev_agent, prev_response) in enumerate(conversation):
                        context += f"{prev_agent}: {prev_response}\n"
                    context += f"现在请{agent_name}继续处理"
                
                response = await self.chat_with_agent(context, agent_name)
                duration = time.time() - start_time
                
                print(f"\n🤖 {agent_name} ({duration:.1f}s):")
                print(f"   {response}")
                
                conversation.append((agent_name, response))
            
            print(f"\n✅ 场景 '{scenario['name']}' 演示完成")
    
    async def multi_agent_collaboration(self):
        """多智能体协作演示"""
        self.print_header("多智能体协作")
        print("💡 输入复杂问题，多个智能体将协作处理")
        
        while True:
            user_input = input(f"\n👤 复杂问题 (输入 'q' 退出): ").strip()
            
            if user_input.lower() == 'q':
                break
            
            if not user_input:
                continue
            
            print("\n🔄 启动多智能体协作...")
            
            # 协调员分析任务
            print("🤖 协调员正在分析任务...")
            coordinator_analysis = await self.chat_with_agent(
                f"请分析这个复杂问题并制定处理计划: {user_input}",
                "协调员"
            )
            print(f"\n🤖 协调员:")
            print(f"   {coordinator_analysis}")
            
            # 根据问题类型选择相关智能体
            relevant_agents = []
            if any(word in user_input.lower() for word in ['购买', '产品', '价格', '销售']):
                relevant_agents.append("销售代表")
            if any(word in user_input.lower() for word in ['技术', '故障', '问题', '支持']):
                relevant_agents.append("客服专员")
            if any(word in user_input.lower() for word in ['现场', '安装', '维修', '部署']):
                relevant_agents.append("现场服务工程师")
            if any(word in user_input.lower() for word in ['战略', '决策', '管理', '规划']):
                relevant_agents.append("管理者")
            
            # 如果没有匹配到特定智能体，使用默认组合
            if not relevant_agents:
                relevant_agents = ["客服专员", "销售代表"]
            
            print(f"\n🎯 参与智能体: {', '.join(relevant_agents)}")
            
            # 各智能体并行处理
            responses = []
            for agent_name in relevant_agents:
                print(f"\n🤖 {agent_name} 正在处理...")
                start_time = time.time()
                
                context = f"协调员分析: {coordinator_analysis}\n\n请从{agent_name}的专业角度处理: {user_input}"
                response = await self.chat_with_agent(context, agent_name)
                duration = time.time() - start_time
                
                print(f"\n🤖 {agent_name} ({duration:.1f}s):")
                print(f"   {response}")
                responses.append((agent_name, response))
            
            # 协调员整合结果
            if len(responses) > 1:
                print(f"\n🤖 协调员正在整合结果...")
                integration_context = f"原始问题: {user_input}\n\n各智能体回复:\n"
                for agent_name, response in responses:
                    integration_context += f"{agent_name}: {response}\n\n"
                integration_context += "请整合以上信息，提供统一的解决方案"
                
                final_response = await self.chat_with_agent(integration_context, "协调员")
                print(f"\n🤖 协调员 (最终整合):")
                print(f"   {final_response}")
            
            print(f"\n✅ 多智能体协作完成")
    
    async def run_interactive_demo(self):
        """运行交互式演示"""
        self.print_header("交互式多智能体演示")
        print("🎯 选择演示模式:")
        
        while True:
            print(f"\n📋 演示模式:")
            print(f"  1. 单智能体对话")
            print(f"  2. 智能路由演示")
            print(f"  3. 预设场景演示")
            print(f"  4. 多智能体协作")
            print(f"  q. 退出")
            
            choice = input(f"\n请选择 (1-4, q): ").strip()
            
            if choice.lower() == 'q':
                print("👋 感谢使用多智能体演示系统！")
                break
            
            try:
                if choice == "1":
                    await self.single_agent_chat()
                elif choice == "2":
                    await self.smart_routing_demo()
                elif choice == "3":
                    await self.scenario_demo()
                elif choice == "4":
                    await self.multi_agent_collaboration()
                else:
                    print("❌ 无效选择，请重新输入")
            
            except KeyboardInterrupt:
                print("\n⏸️ 操作被中断，返回主菜单")
            except Exception as e:
                print(f"\n❌ 发生错误: {e}")
    
    async def close(self):
        """关闭连接"""
        await self.client.aclose()


async def check_service():
    """检查服务状态"""
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.get(f"{base_url}/api/v1/health")
            if response.status_code == 200:
                health = response.json()
                if health.get("status") == "healthy":
                    print("✅ 多智能体服务运行正常")
                    return True
            
            print("❌ 服务状态异常")
            return False
            
        except Exception as e:
            print(f"❌ 无法连接服务: {e}")
            print("请先启动服务:")
            print("   uv run uvicorn src.multi_agent_service.main:app --reload")
            return False


async def main():
    """主函数"""
    print("🚀 交互式多智能体演示系统")
    print("="*60)
    
    # 加载环境变量
    load_dotenv()
    
    # 检查API配置
    api_keys = [
        os.getenv("QWEN_API_KEY"),
        os.getenv("DEEPSEEK_API_KEY"),
        os.getenv("GLM_API_KEY")
    ]
    
    valid_keys = sum(1 for key in api_keys if key and not key.startswith("your_"))
    print(f"🔑 API配置: {valid_keys}/3 个有效")
    
    if valid_keys == 0:
        print("⚠️ 警告: 没有有效的API配置，功能可能受限")
    
    # 检查服务
    if not await check_service():
        return
    
    # 运行演示
    demo = InteractiveAgentDemo()
    try:
        await demo.run_interactive_demo()
    finally:
        await demo.close()


if __name__ == "__main__":
    asyncio.run(main())