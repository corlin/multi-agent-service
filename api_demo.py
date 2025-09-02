#!/usr/bin/env python3
"""
多智能体服务API演示
Multi-Agent Service API Demo
"""

import asyncio
import json
import os
import sys
import time
from typing import Dict, Any, List
from dotenv import load_dotenv
import httpx


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


def print_json(data: Dict[str, Any], title: str = "响应"):
    """格式化打印JSON"""
    print(f"\n🔍 {title}:")
    print(json.dumps(data, ensure_ascii=False, indent=2))


class APIDemo:
    """API演示类"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def test_health(self):
        """测试健康检查接口"""
        print_section("健康检查接口")
        
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/health")
            data = response.json()
            
            print(f"📡 GET /api/v1/health")
            print(f"📊 状态码: {response.status_code}")
            print_json(data)
            
            if data.get("status") == "healthy":
                print("✅ 服务健康")
            else:
                print("⚠️ 服务状态异常")
                
        except Exception as e:
            print(f"❌ 健康检查失败: {e}")
    
    async def test_chat_completions(self):
        """测试聊天完成接口"""
        print_section("聊天完成接口")
        
        test_cases = [
            {
                "messages": [{"role": "user", "content": "你好，请介绍一下你的功能"}],
                "model": "multi-agent-service",
                "max_tokens": 500,
                "temperature": 0.7
            },
            {
                "messages": [
                    {"role": "user", "content": "我想购买产品"},
                    {"role": "assistant", "content": "好的，我来为您介绍我们的产品"},
                    {"role": "user", "content": "价格是多少？"}
                ],
                "model": "multi-agent-service",
                "max_tokens": 300
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🔍 测试用例 {i}:")
            print(f"💬 消息: {test_case['messages'][-1]['content']}")
            
            try:
                start_time = time.time()
                response = await self.client.post(
                    f"{self.base_url}/api/v1/chat/completions",
                    json=test_case
                )
                duration = time.time() - start_time
                
                print(f"📡 POST /api/v1/chat/completions")
                print(f"📊 状态码: {response.status_code}")
                print(f"⏱️ 响应时间: {duration:.2f}秒")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if "choices" in data and data["choices"]:
                        content = data["choices"][0].get("message", {}).get("content", "")
                        print(f"✅ 回复: {content[:200]}...")
                        
                        if "usage" in data:
                            usage = data["usage"]
                            print(f"📊 Token使用: {usage}")
                    else:
                        print_json(data)
                else:
                    print(f"❌ 请求失败: {response.text}")
                    
            except Exception as e:
                print(f"❌ 聊天请求失败: {e}")
    
    async def test_agent_routing(self):
        """测试智能体路由接口"""
        print_section("智能体路由接口")
        
        test_cases = [
            {
                "content": "我想了解产品价格和购买流程",
                "user_id": "demo_user_1",
                "priority": "medium"
            },
            {
                "content": "设备出现故障，无法正常工作",
                "user_id": "demo_user_2", 
                "priority": "high"
            },
            {
                "content": "对服务质量不满意，要投诉",
                "user_id": "demo_user_3",
                "priority": "high"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🔍 测试用例 {i}:")
            print(f"📝 内容: {test_case['content']}")
            
            try:
                start_time = time.time()
                response = await self.client.post(
                    f"{self.base_url}/api/v1/agents/route",
                    json=test_case
                )
                duration = time.time() - start_time
                
                print(f"📡 POST /api/v1/agents/route")
                print(f"📊 状态码: {response.status_code}")
                print(f"⏱️ 响应时间: {duration:.2f}秒")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if "recommended_agent" in data:
                        agent = data["recommended_agent"]
                        confidence = data.get("confidence", 0)
                        
                        print(f"✅ 推荐智能体: {agent.get('name', '未知')}")
                        print(f"📊 置信度: {confidence:.2%}")
                        
                        if "reasoning" in data:
                            print(f"💭 推理: {data['reasoning']}")
                    else:
                        print_json(data)
                else:
                    print(f"❌ 请求失败: {response.text}")
                    
            except Exception as e:
                print(f"❌ 路由请求失败: {e}")
    
    async def test_workflow_execution(self):
        """测试工作流执行接口"""
        print_section("工作流执行接口")
        
        test_cases = [
            {
                "workflow_type": "sequential",
                "task_description": "处理客户销售咨询",
                "participating_agents": ["sales_agent", "customer_support_agent"]
            },
            {
                "workflow_type": "parallel",
                "task_description": "综合服务响应",
                "participating_agents": ["sales_agent", "customer_support_agent", "field_service_agent"]
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🔍 测试用例 {i}:")
            print(f"⚙️ 工作流类型: {test_case['workflow_type']}")
            print(f"📝 任务描述: {test_case['task_description']}")
            
            try:
                start_time = time.time()
                response = await self.client.post(
                    f"{self.base_url}/api/v1/workflows/execute",
                    json=test_case
                )
                duration = time.time() - start_time
                
                print(f"📡 POST /api/v1/workflows/execute")
                print(f"📊 状态码: {response.status_code}")
                print(f"⏱️ 响应时间: {duration:.2f}秒")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if "workflow_id" in data:
                        workflow_id = data["workflow_id"]
                        status = data.get("status", "unknown")
                        
                        print(f"✅ 工作流ID: {workflow_id}")
                        print(f"📊 状态: {status}")
                        
                        if "participating_agents" in data:
                            agents = data["participating_agents"]
                            print(f"🤖 参与智能体: {', '.join(agents)}")
                    else:
                        print_json(data)
                else:
                    print(f"❌ 请求失败: {response.text}")
                    
            except Exception as e:
                print(f"❌ 工作流请求失败: {e}")
    
    async def test_agent_status(self):
        """测试智能体状态接口"""
        print_section("智能体状态接口")
        
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/agents/status")
            
            print(f"📡 GET /api/v1/agents/status")
            print(f"📊 状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if "agents" in data:
                    agents = data["agents"]
                    print(f"✅ 找到 {len(agents)} 个智能体")
                    
                    for agent_id, agent_info in agents.items():
                        name = agent_info.get("name", agent_id)
                        enabled = agent_info.get("enabled", False)
                        status = "✅ 启用" if enabled else "❌ 禁用"
                        print(f"   🤖 {name}: {status}")
                else:
                    print_json(data)
            else:
                print(f"❌ 请求失败: {response.text}")
                
        except Exception as e:
            print(f"❌ 状态查询失败: {e}")
    
    async def test_agent_types(self):
        """测试智能体类型接口"""
        print_section("智能体类型接口")
        
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/agents/types")
            
            print(f"📡 GET /api/v1/agents/types")
            print(f"📊 状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if "agent_types" in data:
                    types = data["agent_types"]
                    print(f"✅ 支持的智能体类型:")
                    
                    for agent_type in types:
                        print(f"   🏷️ {agent_type}")
                else:
                    print_json(data)
            else:
                print(f"❌ 请求失败: {response.text}")
                
        except Exception as e:
            print(f"❌ 类型查询失败: {e}")
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()


async def check_service_availability(base_url: str) -> bool:
    """检查服务可用性"""
    print("🔍 检查服务可用性...")
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.get(f"{base_url}/api/v1/health")
            if response.status_code == 200:
                print("✅ 服务可用")
                return True
            else:
                print(f"❌ 服务响应异常: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 无法连接到服务: {e}")
            return False


async def main():
    """主函数"""
    print_header("多智能体服务API演示")
    
    print("🎯 本演示将测试以下API接口:")
    print("   • 健康检查接口")
    print("   • 聊天完成接口")
    print("   • 智能体路由接口")
    print("   • 工作流执行接口")
    print("   • 智能体状态接口")
    print("   • 智能体类型接口")
    
    base_url = "http://localhost:8000"
    
    # 检查服务可用性
    if not await check_service_availability(base_url):
        print(f"\n❌ 服务不可用，请先启动服务:")
        print(f"   uv run uvicorn src.multi_agent_service.main:app --reload")
        return
    
    demo = APIDemo(base_url)
    
    try:
        # API测试列表
        tests = [
            ("健康检查", demo.test_health),
            ("智能体状态", demo.test_agent_status),
            ("智能体类型", demo.test_agent_types),
            ("聊天完成", demo.test_chat_completions),
            ("智能体路由", demo.test_agent_routing),
            ("工作流执行", demo.test_workflow_execution)
        ]
        
        results = []
        total_start_time = time.time()
        
        for test_name, test_func in tests:
            try:
                print_header(test_name)
                start_time = time.time()
                
                await test_func()
                
                duration = time.time() - start_time
                print(f"\n✅ {test_name} 测试完成 (耗时: {duration:.2f}秒)")
                results.append((test_name, True, duration))
                
            except Exception as e:
                print(f"\n❌ {test_name} 测试失败: {e}")
                results.append((test_name, False, 0))
        
        # 总结
        total_duration = time.time() - total_start_time
        
        print_header("测试总结")
        
        successful = sum(1 for _, success, _ in results if success)
        total = len(results)
        
        print(f"📊 测试结果: {successful}/{total} 成功")
        print(f"⏱️ 总耗时: {total_duration:.2f}秒")
        
        print(f"\n📋 详细结果:")
        for test_name, success, duration in results:
            status = "✅" if success else "❌"
            time_info = f"({duration:.2f}s)" if success else ""
            print(f"   {status} {test_name} {time_info}")
        
        if successful == total:
            print(f"\n🎉 所有API测试成功！服务运行正常！")
        else:
            print(f"\n⚠️ 部分API测试失败，请检查服务状态和配置")
    
    finally:
        await demo.close()


if __name__ == "__main__":
    # 加载环境变量
    load_dotenv()
    
    # 检查基本配置
    api_keys = [
        os.getenv("QWEN_API_KEY"),
        os.getenv("DEEPSEEK_API_KEY"),
        os.getenv("GLM_API_KEY")
    ]
    
    valid_keys = sum(1 for key in api_keys if key and not key.startswith("your_"))
    
    if valid_keys == 0:
        print("⚠️ 警告: 没有找到有效的API配置")
        print("请检查 .env 文件中的API密钥配置")
        print("某些功能可能无法正常工作")
    
    asyncio.run(main())