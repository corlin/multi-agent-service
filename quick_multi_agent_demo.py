#!/usr/bin/env python3
"""
快速多智能体交互演示
Quick Multi-Agent Interaction Demo

快速演示5个智能体的核心交互场景
"""

import asyncio
import json
import os
import time
from typing import Dict, Any, List
from dotenv import load_dotenv
import httpx


class QuickAgentDemo:
    """快速智能体演示"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def chat_request(self, content: str, agent_role: str = None) -> str:
        """发送聊天请求"""
        messages = [{"role": "user", "content": content}]
        
        if agent_role:
            system_msg = {"role": "system", "content": f"你是{agent_role}，请以专业的身份回复"}
            messages = [system_msg] + messages
        
        data = {
            "messages": messages,
            "model": "multi-agent-service",
            "max_tokens": 800,
            "temperature": 0.7
        }
        
        response = await self.client.post(f"{self.base_url}/api/v1/chat/completions", json=data)
        result = response.json()
        
        if "choices" in result and result["choices"]:
            return result["choices"][0]["message"]["content"]
        return "无回复"
    
    async def demo_scenario_1(self):
        """场景1: 客户购买咨询"""
        print("\n" + "="*60)
        print("🛒 场景1: 客户购买咨询")
        print("="*60)
        
        query = "我想购买AI客服系统，需要了解功能和价格"
        print(f"👤 客户: {query}")
        
        # 销售代表回复
        sales_response = await self.chat_request(query, "销售代表")
        print(f"\n🤖 销售代表: {sales_response}")
        
        # 客服跟进技术细节
        followup = "技术架构是怎样的？支持多少并发用户？"
        print(f"\n👤 客户: {followup}")
        
        support_response = await self.chat_request(
            f"客户之前询问：{query}\n销售回复：{sales_response}\n现在问：{followup}",
            "客服专员"
        )
        print(f"\n🤖 客服专员: {support_response}")
    
    async def demo_scenario_2(self):
        """场景2: 技术故障处理"""
        print("\n" + "="*60)
        print("🔧 场景2: 技术故障处理")
        print("="*60)
        
        issue = "系统突然无法访问，所有API都返回500错误"
        print(f"👤 客户: {issue}")
        
        # 客服初步诊断
        support_diagnosis = await self.chat_request(issue, "客服专员")
        print(f"\n🤖 客服专员: {support_diagnosis}")
        
        # 现场服务深度处理
        technical_escalation = f"客服诊断：{support_diagnosis}\n需要现场技术支持处理这个问题"
        
        field_response = await self.chat_request(technical_escalation, "现场服务工程师")
        print(f"\n🤖 现场服务工程师: {field_response}")
    
    async def demo_scenario_3(self):
        """场景3: 投诉升级处理"""
        print("\n" + "="*60)
        print("😡 场景3: 投诉升级处理")
        print("="*60)
        
        complaint = "你们的服务太差了！系统经常出问题，客服态度不好，我要投诉！"
        print(f"👤 客户: {complaint}")
        
        # 协调员分析
        coordinator_analysis = await self.chat_request(
            f"客户投诉：{complaint}\n请分析问题并提出解决方案",
            "协调员"
        )
        print(f"\n🤖 协调员: {coordinator_analysis}")
        
        # 管理者决策
        management_decision = await self.chat_request(
            f"投诉内容：{complaint}\n协调员分析：{coordinator_analysis}\n请制定处理方案",
            "管理者"
        )
        print(f"\n🤖 管理者: {management_decision}")
    
    async def demo_scenario_4(self):
        """场景4: 紧急响应"""
        print("\n" + "="*60)
        print("🚨 场景4: 紧急响应")
        print("="*60)
        
        emergency = "紧急！全系统宕机，100+客户受影响，每分钟损失巨大！"
        print(f"🚨 紧急情况: {emergency}")
        
        # 协调员快速响应
        emergency_response = await self.chat_request(
            f"紧急情况：{emergency}\n请立即制定应急方案",
            "协调员"
        )
        print(f"\n🤖 协调员: {emergency_response}")
        
        # 现场服务紧急处理
        field_emergency = await self.chat_request(
            f"紧急故障：{emergency}\n立即进行技术抢修",
            "现场服务工程师"
        )
        print(f"\n🤖 现场服务工程师: {field_emergency}")
        
        # 客服通知客户
        customer_notification = await self.chat_request(
            f"系统故障：{emergency}\n请向客户发送故障通知",
            "客服专员"
        )
        print(f"\n🤖 客服专员: {customer_notification}")
    
    async def demo_scenario_5(self):
        """场景5: 战略规划"""
        print("\n" + "="*60)
        print("📊 场景5: 战略规划")
        print("="*60)
        
        strategy_need = "公司需要制定2025年AI服务发展战略，请各部门提供专业建议"
        print(f"📋 战略需求: {strategy_need}")
        
        # 销售视角
        sales_input = await self.chat_request(
            f"{strategy_need}\n从销售和市场角度分析",
            "销售代表"
        )
        print(f"\n🤖 销售代表: {sales_input}")
        
        # 技术视角
        tech_input = await self.chat_request(
            f"{strategy_need}\n从技术实施角度分析",
            "现场服务工程师"
        )
        print(f"\n🤖 现场服务工程师: {tech_input}")
        
        # 管理者综合决策
        strategic_decision = await self.chat_request(
            f"战略规划需求：{strategy_need}\n销售建议：{sales_input}\n技术建议：{tech_input}\n请制定综合战略",
            "管理者"
        )
        print(f"\n🤖 管理者: {strategic_decision}")
    
    async def run_quick_demo(self):
        """运行快速演示"""
        print("🚀 快速多智能体交互演示")
        print("展示5个智能体在不同场景下的协作")
        
        scenarios = [
            ("客户购买咨询", self.demo_scenario_1),
            ("技术故障处理", self.demo_scenario_2),
            ("投诉升级处理", self.demo_scenario_3),
            ("紧急响应", self.demo_scenario_4),
            ("战略规划", self.demo_scenario_5)
        ]
        
        results = []
        start_time = time.time()
        
        for name, scenario_func in scenarios:
            try:
                scenario_start = time.time()
                await scenario_func()
                duration = time.time() - scenario_start
                
                print(f"\n✅ {name} 完成 ({duration:.1f}s)")
                results.append((name, True, duration))
                
            except Exception as e:
                print(f"\n❌ {name} 失败: {e}")
                results.append((name, False, 0))
        
        # 总结
        total_time = time.time() - start_time
        successful = sum(1 for _, success, _ in results if success)
        
        print("\n" + "="*60)
        print("📊 演示总结")
        print("="*60)
        print(f"成功场景: {successful}/{len(scenarios)}")
        print(f"总耗时: {total_time:.1f}秒")
        
        for name, success, duration in results:
            status = "✅" if success else "❌"
            time_info = f"({duration:.1f}s)" if success else ""
            print(f"  {status} {name} {time_info}")
        
        if successful == len(scenarios):
            print(f"\n🎉 所有场景演示成功！")
            print(f"🤖 智能体协作能力:")
            print(f"  • 销售代表: 产品咨询、报价")
            print(f"  • 客服专员: 问题解答、技术支持")
            print(f"  • 现场服务: 技术服务、现场支持")
            print(f"  • 管理者: 决策分析、战略规划")
            print(f"  • 协调员: 任务协调、智能体管理")
    
    async def close(self):
        """关闭连接"""
        await self.client.aclose()


async def main():
    """主函数"""
    load_dotenv()
    
    # 检查服务
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.get(f"{base_url}/api/v1/health")
            if response.status_code != 200:
                print("❌ 服务不可用，请先启动:")
                print("   uv run uvicorn src.multi_agent_service.main:app --reload")
                return
        except Exception:
            print("❌ 无法连接服务，请先启动:")
            print("   uv run uvicorn src.multi_agent_service.main:app --reload")
            return
    
    # 运行演示
    demo = QuickAgentDemo(base_url)
    try:
        await demo.run_quick_demo()
    finally:
        await demo.close()


if __name__ == "__main__":
    asyncio.run(main())