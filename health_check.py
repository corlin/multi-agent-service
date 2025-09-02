#!/usr/bin/env python3
"""
多智能体服务健康检查
Multi-Agent Service Health Check
"""

import asyncio
import httpx
import json
import time
from typing import Dict, Any


async def check_service_health(base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """检查服务健康状态"""
    
    print("🏥 多智能体服务健康检查")
    print("=" * 50)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        results = {}
        
        # 1. 基础健康检查
        print("\n📋 1. 基础健康检查")
        try:
            response = await client.get(f"{base_url}/api/v1/health")
            if response.status_code == 200:
                health_data = response.json()
                print("✅ 服务健康检查通过")
                print(f"   状态: {health_data.get('status', 'unknown')}")
                print(f"   版本: {health_data.get('version', 'unknown')}")
                results["health_check"] = True
            else:
                print(f"❌ 健康检查失败: HTTP {response.status_code}")
                results["health_check"] = False
        except Exception as e:
            print(f"❌ 无法连接到服务: {e}")
            results["health_check"] = False
            return results
        
        # 2. API文档检查
        print("\n📚 2. API文档检查")
        try:
            response = await client.get(f"{base_url}/docs")
            if response.status_code == 200:
                print("✅ API文档可访问")
                results["docs_accessible"] = True
            else:
                print(f"❌ API文档不可访问: HTTP {response.status_code}")
                results["docs_accessible"] = False
        except Exception as e:
            print(f"❌ API文档检查失败: {e}")
            results["docs_accessible"] = False
        
        # 3. 智能体状态检查
        print("\n🤖 3. 智能体状态检查")
        try:
            response = await client.get(f"{base_url}/api/v1/agents/status")
            if response.status_code == 200:
                agents_data = response.json()
                if "agents" in agents_data:
                    agents = agents_data["agents"]
                    print(f"✅ 找到 {len(agents)} 个智能体")
                    
                    for agent_id, agent_info in agents.items():
                        name = agent_info.get("name", agent_id)
                        status = agent_info.get("status", "unknown")
                        print(f"   🤖 {name}: {status}")
                    
                    results["agents_count"] = len(agents)
                    results["agents_status"] = True
                else:
                    print("❌ 智能体状态数据格式异常")
                    results["agents_status"] = False
            else:
                print(f"❌ 智能体状态检查失败: HTTP {response.status_code}")
                results["agents_status"] = False
        except Exception as e:
            print(f"❌ 智能体状态检查失败: {e}")
            results["agents_status"] = False
        
        # 4. 智能体类型检查
        print("\n🏷️ 4. 智能体类型检查")
        try:
            response = await client.get(f"{base_url}/api/v1/agents/types")
            if response.status_code == 200:
                types_data = response.json()
                if "agent_types" in types_data:
                    agent_types = types_data["agent_types"]
                    print(f"✅ 支持 {len(agent_types)} 种智能体类型")
                    for agent_type in agent_types:
                        print(f"   🏷️ {agent_type}")
                    results["agent_types"] = agent_types
                else:
                    print("❌ 智能体类型数据格式异常")
            else:
                print(f"❌ 智能体类型检查失败: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ 智能体类型检查失败: {e}")
        
        # 5. 简单聊天测试
        print("\n💬 5. 简单聊天测试")
        try:
            chat_data = {
                "messages": [{"role": "user", "content": "你好，这是一个测试"}],
                "model": "multi-agent-service",
                "max_tokens": 100
            }
            
            start_time = time.time()
            response = await client.post(f"{base_url}/api/v1/chat/completions", json=chat_data)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                chat_response = response.json()
                if "choices" in chat_response and chat_response["choices"]:
                    content = chat_response["choices"][0].get("message", {}).get("content", "")
                    print(f"✅ 聊天接口正常 (响应时间: {response_time:.2f}秒)")
                    print(f"   回复: {content[:100]}...")
                    results["chat_test"] = True
                    results["chat_response_time"] = response_time
                else:
                    print("❌ 聊天响应格式异常")
                    results["chat_test"] = False
            else:
                print(f"❌ 聊天接口失败: HTTP {response.status_code}")
                if response.status_code == 500:
                    error_data = response.json()
                    print(f"   错误: {error_data.get('detail', 'Unknown error')}")
                results["chat_test"] = False
        except Exception as e:
            print(f"❌ 聊天测试失败: {e}")
            results["chat_test"] = False
        
        return results


async def main():
    """主函数"""
    print("🚀 启动多智能体服务健康检查...")
    
    # 检查服务是否运行
    base_url = "http://localhost:8000"
    
    try:
        results = await check_service_health(base_url)
        
        # 生成总结报告
        print("\n" + "=" * 50)
        print("📊 健康检查总结")
        print("=" * 50)
        
        total_checks = 0
        passed_checks = 0
        
        checks = [
            ("基础健康检查", results.get("health_check", False)),
            ("API文档访问", results.get("docs_accessible", False)),
            ("智能体状态", results.get("agents_status", False)),
            ("聊天接口测试", results.get("chat_test", False))
        ]
        
        for check_name, passed in checks:
            total_checks += 1
            if passed:
                passed_checks += 1
                print(f"✅ {check_name}")
            else:
                print(f"❌ {check_name}")
        
        print(f"\n📈 总体状态: {passed_checks}/{total_checks} 项检查通过")
        
        if "agents_count" in results:
            print(f"🤖 智能体数量: {results['agents_count']}")
        
        if "chat_response_time" in results:
            print(f"⏱️ 聊天响应时间: {results['chat_response_time']:.2f}秒")
        
        if passed_checks == total_checks:
            print("\n🎉 服务运行正常！")
        elif passed_checks > 0:
            print(f"\n⚠️ 服务部分功能正常，建议检查失败的项目")
        else:
            print(f"\n❌ 服务存在严重问题，请检查服务状态")
        
        print(f"\n🌐 服务地址: {base_url}")
        print(f"📚 API文档: {base_url}/docs")
        
    except KeyboardInterrupt:
        print("\n👋 健康检查被用户中断")
    except Exception as e:
        print(f"\n❌ 健康检查出错: {e}")


if __name__ == "__main__":
    asyncio.run(main())