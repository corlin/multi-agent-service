#!/usr/bin/env python3
"""
多智能体交互场景演示
Multi-Agent Interaction Scenarios Demo

演示5个智能体在不同业务场景下的协作：
1. 销售代表 - 产品咨询、报价
2. 客服专员 - 问题解答、技术支持  
3. 现场服务 - 技术服务、现场支持
4. 管理者 - 决策分析、战略规划
5. 协调员 - 任务协调、智能体管理
"""

import asyncio
import json
import os
import sys
import time
from typing import Dict, Any, List
from dotenv import load_dotenv
import httpx


class MultiAgentDemo:
    """多智能体交互演示类"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=120.0)
        
        # 智能体信息
        self.agents = {
            "sales_agent": "销售代表",
            "customer_support_agent": "客服专员", 
            "field_service_agent": "现场服务人员",
            "manager_agent": "管理者",
            "coordinator_agent": "协调员"
        }
    
    def print_header(self, title: str, width: int = 80):
        """打印标题"""
        print(f"\n{'='*width}")
        print(f"🚀 {title.center(width-4)}")
        print(f"{'='*width}")
    
    def print_section(self, title: str, width: int = 60):
        """打印章节"""
        print(f"\n{'-'*width}")
        print(f"📋 {title}")
        print(f"{'-'*width}")
    
    def print_agent_response(self, agent_name: str, content: str, duration: float = 0):
        """打印智能体回复"""
        print(f"\n🤖 {agent_name} ({duration:.2f}s):")
        print(f"   {content}")
    
    async def chat_with_agent(self, messages: List[Dict], agent_hint: str = None) -> Dict[str, Any]:
        """与指定智能体聊天"""
        data = {
            "messages": messages,
            "model": "multi-agent-service",
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        if agent_hint:
            # 在消息中添加智能体提示
            system_msg = {
                "role": "system", 
                "content": f"请以{agent_hint}的身份回复用户"
            }
            data["messages"] = [system_msg] + messages
        
        response = await self.client.post(f"{self.base_url}/api/v1/chat/completions", json=data)
        return response.json()
    
    async def route_to_agent(self, content: str, user_id: str = "demo_user") -> Dict[str, Any]:
        """路由到合适的智能体"""
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
    
    async def scenario_1_sales_consultation(self):
        """场景1: 销售咨询流程"""
        self.print_section("场景1: 销售咨询流程")
        print("📝 客户询问产品信息 → 销售代表介绍 → 客服跟进")
        
        # 步骤1: 客户咨询
        customer_query = "我想了解你们的企业级AI解决方案，包括功能特点和价格"
        print(f"\n👤 客户: {customer_query}")
        
        # 路由到销售代表
        route_result = await self.route_to_agent(customer_query, "customer_001")
        if "recommended_agent" in route_result:
            agent_info = route_result["recommended_agent"]
            print(f"🎯 系统路由: {agent_info.get('name', '未知智能体')}")
        
        # 销售代表回复
        start_time = time.time()
        sales_response = await self.chat_with_agent(
            [{"role": "user", "content": customer_query}],
            "销售代表"
        )
        duration = time.time() - start_time
        
        if "choices" in sales_response and sales_response["choices"]:
            content = sales_response["choices"][0]["message"]["content"]
            self.print_agent_response("销售代表", content, duration)
        
        # 步骤2: 客服跟进
        followup_query = "刚才销售说的技术细节我不太明白，能详细解释一下吗？"
        print(f"\n👤 客户: {followup_query}")
        
        start_time = time.time()
        support_response = await self.chat_with_agent(
            [
                {"role": "user", "content": customer_query},
                {"role": "assistant", "content": content},
                {"role": "user", "content": followup_query}
            ],
            "客服专员"
        )
        duration = time.time() - start_time
        
        if "choices" in support_response and support_response["choices"]:
            content = support_response["choices"][0]["message"]["content"]
            self.print_agent_response("客服专员", content, duration)
        
        print("\n✅ 销售咨询流程完成")
    
    async def scenario_2_technical_support(self):
        """场景2: 技术支持协作"""
        self.print_section("场景2: 技术支持协作")
        print("📝 技术故障 → 客服初步诊断 → 现场服务处理")
        
        # 步骤1: 故障报告
        issue_report = "我们的AI系统突然无法正常响应，所有API调用都返回超时错误"
        print(f"\n👤 客户: {issue_report}")
        
        # 客服初步诊断
        start_time = time.time()
        support_diagnosis = await self.chat_with_agent(
            [{"role": "user", "content": issue_report}],
            "客服专员"
        )
        duration = time.time() - start_time
        
        if "choices" in support_diagnosis and support_diagnosis["choices"]:
            diagnosis_content = support_diagnosis["choices"][0]["message"]["content"]
            self.print_agent_response("客服专员", diagnosis_content, duration)
        
        # 步骤2: 现场服务介入
        technical_query = "根据客服的初步诊断，需要进行深度技术检查和现场处理"
        print(f"\n🔧 技术升级: {technical_query}")
        
        start_time = time.time()
        field_response = await self.chat_with_agent(
            [
                {"role": "user", "content": issue_report},
                {"role": "assistant", "content": diagnosis_content},
                {"role": "user", "content": technical_query}
            ],
            "现场服务工程师"
        )
        duration = time.time() - start_time
        
        if "choices" in field_response and field_response["choices"]:
            field_content = field_response["choices"][0]["message"]["content"]
            self.print_agent_response("现场服务工程师", field_content, duration)
        
        print("\n✅ 技术支持协作完成")
    
    async def scenario_3_escalation_management(self):
        """场景3: 问题升级管理"""
        self.print_section("场景3: 问题升级管理")
        print("📝 客户投诉 → 协调员分析 → 管理者决策")
        
        # 步骤1: 客户投诉
        complaint = "我对你们的服务非常不满意！响应速度慢，技术支持不专业，要求退款并赔偿损失！"
        print(f"\n😡 客户投诉: {complaint}")
        
        # 协调员分析
        start_time = time.time()
        coordinator_analysis = await self.chat_with_agent(
            [{"role": "user", "content": f"客户投诉：{complaint}。请分析情况并提出处理建议。"}],
            "协调员"
        )
        duration = time.time() - start_time
        
        if "choices" in coordinator_analysis and coordinator_analysis["choices"]:
            analysis_content = coordinator_analysis["choices"][0]["message"]["content"]
            self.print_agent_response("协调员", analysis_content, duration)
        
        # 步骤2: 管理者决策
        management_query = f"协调员分析：{analysis_content}。作为管理者，请制定具体的解决方案和补偿措施。"
        
        start_time = time.time()
        manager_decision = await self.chat_with_agent(
            [{"role": "user", "content": management_query}],
            "管理者"
        )
        duration = time.time() - start_time
        
        if "choices" in manager_decision and manager_decision["choices"]:
            decision_content = manager_decision["choices"][0]["message"]["content"]
            self.print_agent_response("管理者", decision_content, duration)
        
        print("\n✅ 问题升级管理完成")
    
    async def scenario_4_comprehensive_service(self):
        """场景4: 综合服务协作"""
        self.print_section("场景4: 综合服务协作")
        print("📝 复杂需求 → 多智能体并行处理 → 协调员整合")
        
        # 复杂客户需求
        complex_request = """
        我们是一家大型制造企业，需要：
        1. 采购AI智能质检系统（销售）
        2. 解决现有系统集成问题（技术支持）
        3. 安排现场部署和培训（现场服务）
        4. 制定长期合作战略（管理层）
        请提供完整的解决方案。
        """
        print(f"\n🏢 企业客户: {complex_request}")
        
        # 执行并行工作流
        workflow_result = await self.execute_workflow(
            "parallel",
            "企业级AI系统综合服务",
            ["sales_agent", "customer_support_agent", "field_service_agent", "manager_agent"]
        )
        
        if "workflow_id" in workflow_result:
            print(f"🔄 启动并行工作流: {workflow_result['workflow_id']}")
        
        # 模拟各智能体并行处理
        tasks = [
            ("销售代表", "请提供AI智能质检系统的产品方案和报价"),
            ("客服专员", "请分析现有系统集成可能遇到的技术问题和解决方案"),
            ("现场服务工程师", "请制定现场部署和培训计划"),
            ("管理者", "请从战略角度分析长期合作的价值和规划")
        ]
        
        responses = {}
        
        # 并行处理各项任务
        async def process_task(agent_role, task_content):
            start_time = time.time()
            response = await self.chat_with_agent(
                [{"role": "user", "content": f"企业客户需求：{complex_request}\n\n具体任务：{task_content}"}],
                agent_role
            )
            duration = time.time() - start_time
            
            if "choices" in response and response["choices"]:
                content = response["choices"][0]["message"]["content"]
                self.print_agent_response(agent_role, content, duration)
                return content
            return ""
        
        # 并发执行所有任务
        results = await asyncio.gather(*[
            process_task(agent_role, task_content) 
            for agent_role, task_content in tasks
        ])
        
        # 协调员整合结果
        integration_query = f"""
        各智能体处理结果：
        销售方案：{results[0][:200]}...
        技术方案：{results[1][:200]}...
        部署方案：{results[2][:200]}...
        战略规划：{results[3][:200]}...
        
        请作为协调员，整合以上信息，提供统一的综合解决方案。
        """
        
        start_time = time.time()
        coordinator_integration = await self.chat_with_agent(
            [{"role": "user", "content": integration_query}],
            "协调员"
        )
        duration = time.time() - start_time
        
        if "choices" in coordinator_integration and coordinator_integration["choices"]:
            integration_content = coordinator_integration["choices"][0]["message"]["content"]
            self.print_agent_response("协调员 (整合方案)", integration_content, duration)
        
        print("\n✅ 综合服务协作完成")
    
    async def scenario_5_emergency_response(self):
        """场景5: 紧急响应处理"""
        self.print_section("场景5: 紧急响应处理")
        print("📝 紧急故障 → 协调员快速响应 → 多智能体协同处理")
        
        # 紧急故障
        emergency = """
        🚨 紧急故障报告：
        - 时间：刚刚发生
        - 影响：全部AI服务中断
        - 客户：50+企业客户受影响
        - 损失：每分钟损失约10万元
        需要立即处理！
        """
        print(f"\n🚨 紧急故障: {emergency}")
        
        # 协调员快速响应
        start_time = time.time()
        coordinator_emergency = await self.chat_with_agent(
            [{"role": "user", "content": f"紧急情况：{emergency}\n请立即制定应急响应计划并协调各部门。"}],
            "协调员"
        )
        duration = time.time() - start_time
        
        if "choices" in coordinator_emergency and coordinator_emergency["choices"]:
            emergency_plan = coordinator_emergency["choices"][0]["message"]["content"]
            self.print_agent_response("协调员 (应急指挥)", emergency_plan, duration)
        
        # 执行紧急响应工作流
        emergency_workflow = await self.execute_workflow(
            "hierarchical",
            "紧急故障响应",
            ["coordinator_agent", "field_service_agent", "customer_support_agent", "manager_agent"]
        )
        
        if "workflow_id" in emergency_workflow:
            print(f"🚨 启动紧急响应工作流: {emergency_workflow['workflow_id']}")
        
        # 各智能体紧急行动
        emergency_tasks = [
            ("现场服务工程师", "立即进行技术故障排查和修复"),
            ("客服专员", "向所有受影响客户发送故障通知和预计恢复时间"),
            ("管理者", "评估损失并制定客户补偿方案")
        ]
        
        for agent_role, task in emergency_tasks:
            start_time = time.time()
            response = await self.chat_with_agent(
                [{"role": "user", "content": f"紧急故障：{emergency}\n\n紧急任务：{task}"}],
                agent_role
            )
            duration = time.time() - start_time
            
            if "choices" in response and response["choices"]:
                content = response["choices"][0]["message"]["content"]
                self.print_agent_response(f"{agent_role} (紧急行动)", content, duration)
        
        print("\n✅ 紧急响应处理完成")
    
    async def scenario_6_strategic_planning(self):
        """场景6: 战略规划协作"""
        self.print_section("场景6: 战略规划协作")
        print("📝 市场分析 → 各部门输入 → 管理者决策 → 协调员执行")
        
        # 战略规划需求
        strategic_need = """
        公司需要制定2025年AI服务发展战略：
        - 市场竞争加剧
        - 客户需求多样化
        - 技术快速迭代
        - 成本控制压力
        需要各部门提供专业意见。
        """
        print(f"\n📊 战略规划需求: {strategic_need}")
        
        # 各部门提供专业意见
        department_inputs = [
            ("销售代表", "从市场和客户角度分析发展机会和挑战"),
            ("客服专员", "从服务质量和客户满意度角度提供建议"),
            ("现场服务工程师", "从技术实施和运维角度评估能力需求"),
        ]
        
        insights = []
        for agent_role, perspective in department_inputs:
            start_time = time.time()
            response = await self.chat_with_agent(
                [{"role": "user", "content": f"战略规划背景：{strategic_need}\n\n请{perspective}"}],
                agent_role
            )
            duration = time.time() - start_time
            
            if "choices" in response and response["choices"]:
                content = response["choices"][0]["message"]["content"]
                self.print_agent_response(f"{agent_role} (战略输入)", content, duration)
                insights.append(content)
        
        # 管理者综合决策
        decision_query = f"""
        战略规划背景：{strategic_need}
        
        各部门意见：
        销售视角：{insights[0][:200]}...
        服务视角：{insights[1][:200]}...
        技术视角：{insights[2][:200]}...
        
        请制定2025年发展战略和具体行动计划。
        """
        
        start_time = time.time()
        manager_strategy = await self.chat_with_agent(
            [{"role": "user", "content": decision_query}],
            "管理者"
        )
        duration = time.time() - start_time
        
        if "choices" in manager_strategy and manager_strategy["choices"]:
            strategy_content = manager_strategy["choices"][0]["message"]["content"]
            self.print_agent_response("管理者 (战略决策)", strategy_content, duration)
        
        # 协调员制定执行计划
        execution_query = f"""
        管理者战略决策：{strategy_content}
        
        请制定详细的执行计划，包括时间节点、责任分工和监控机制。
        """
        
        start_time = time.time()
        coordinator_execution = await self.chat_with_agent(
            [{"role": "user", "content": execution_query}],
            "协调员"
        )
        duration = time.time() - start_time
        
        if "choices" in coordinator_execution and coordinator_execution["choices"]:
            execution_content = coordinator_execution["choices"][0]["message"]["content"]
            self.print_agent_response("协调员 (执行计划)", execution_content, duration)
        
        print("\n✅ 战略规划协作完成")
    
    async def run_all_scenarios(self):
        """运行所有交互场景"""
        self.print_header("多智能体交互场景演示")
        
        print("🎯 演示场景:")
        print("   1. 销售咨询流程")
        print("   2. 技术支持协作")
        print("   3. 问题升级管理")
        print("   4. 综合服务协作")
        print("   5. 紧急响应处理")
        print("   6. 战略规划协作")
        
        scenarios = [
            ("销售咨询流程", self.scenario_1_sales_consultation),
            ("技术支持协作", self.scenario_2_technical_support),
            ("问题升级管理", self.scenario_3_escalation_management),
            ("综合服务协作", self.scenario_4_comprehensive_service),
            ("紧急响应处理", self.scenario_5_emergency_response),
            ("战略规划协作", self.scenario_6_strategic_planning)
        ]
        
        results = []
        total_start_time = time.time()
        
        for scenario_name, scenario_func in scenarios:
            try:
                print(f"\n{'='*80}")
                print(f"🎬 开始场景: {scenario_name}")
                print(f"{'='*80}")
                
                start_time = time.time()
                await scenario_func()
                duration = time.time() - start_time
                
                print(f"\n✅ 场景 '{scenario_name}' 完成 (耗时: {duration:.2f}秒)")
                results.append((scenario_name, True, duration))
                
                # 场景间暂停
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"\n❌ 场景 '{scenario_name}' 失败: {e}")
                results.append((scenario_name, False, 0))
        
        # 总结
        total_duration = time.time() - total_start_time
        
        self.print_header("演示总结")
        
        successful = sum(1 for _, success, _ in results if success)
        total = len(results)
        
        print(f"📊 场景结果: {successful}/{total} 成功")
        print(f"⏱️ 总耗时: {total_duration:.2f}秒")
        
        print(f"\n📋 详细结果:")
        for scenario_name, success, duration in results:
            status = "✅" if success else "❌"
            time_info = f"({duration:.2f}s)" if success else ""
            print(f"   {status} {scenario_name} {time_info}")
        
        if successful == total:
            print(f"\n🎉 所有多智能体交互场景演示成功！")
            print(f"\n🚀 系统展示了以下能力:")
            print(f"   • 智能体角色专业化")
            print(f"   • 多智能体协作流程")
            print(f"   • 任务路由和分配")
            print(f"   • 并行和串行工作流")
            print(f"   • 紧急响应机制")
            print(f"   • 战略决策支持")
        else:
            print(f"\n⚠️ 部分场景失败，请检查服务状态")
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()


async def check_service_health(base_url: str) -> bool:
    """检查服务健康状态"""
    print("🔍 检查多智能体服务状态...")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{base_url}/api/v1/health")
            if response.status_code == 200:
                health_data = response.json()
                if health_data.get("status") == "healthy":
                    print("✅ 服务健康，可以开始演示")
                    return True
                else:
                    print(f"❌ 服务状态异常: {health_data}")
                    return False
            else:
                print(f"❌ 服务响应异常: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 无法连接到服务: {e}")
            return False


async def main():
    """主函数"""
    print("🚀 多智能体交互场景演示")
    print("=" * 80)
    
    # 加载环境变量
    load_dotenv()
    
    # 检查API配置
    api_keys = [
        ("QWEN_API_KEY", os.getenv("QWEN_API_KEY")),
        ("DEEPSEEK_API_KEY", os.getenv("DEEPSEEK_API_KEY")),
        ("GLM_API_KEY", os.getenv("GLM_API_KEY"))
    ]
    
    valid_keys = sum(1 for name, key in api_keys 
                    if key and not key.startswith("your_"))
    
    print(f"🔑 API配置检查: {valid_keys}/3 个有效")
    
    if valid_keys == 0:
        print("❌ 错误: 没有找到有效的API配置")
        print("请检查 .env 文件中的API密钥配置")
        return
    
    base_url = "http://localhost:8000"
    
    # 检查服务状态
    if not await check_service_health(base_url):
        print(f"\n❌ 服务不可用，请先启动服务:")
        print(f"   uv run uvicorn src.multi_agent_service.main:app --reload")
        return
    
    # 运行演示
    demo = MultiAgentDemo(base_url)
    
    try:
        await demo.run_all_scenarios()
    finally:
        await demo.close()


if __name__ == "__main__":
    asyncio.run(main())