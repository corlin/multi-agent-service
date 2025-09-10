#!/usr/bin/env python3
"""
专利分析系统端到端演示脚本

这个脚本演示了从关键词输入到报告生成的完整专利分析流程，
验证所有Agent协作和工作流执行。

使用方法:
    python patent_analysis_demo.py
    
或者使用uv:
    uv run python patent_analysis_demo.py
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from src.multi_agent_service.models.base import UserRequest
from src.multi_agent_service.models.enums import AgentType
from src.multi_agent_service.core.patent_system_initializer import (
    get_global_patent_initializer, 
    patent_system_health_check
)
from src.multi_agent_service.agents.registry import agent_registry


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("patent_demo.log")
    ]
)
logger = logging.getLogger(__name__)


class PatentAnalysisDemo:
    """专利分析演示类."""
    
    def __init__(self):
        """初始化演示环境."""
        self.demo_scenarios = [
            {
                "name": "人工智能专利快速检索",
                "keywords": ["人工智能", "机器学习", "深度学习"],
                "analysis_type": "quick_search",
                "description": "快速检索人工智能相关专利，适合初步了解技术发展"
            },
            {
                "name": "区块链技术全面分析",
                "keywords": ["区块链", "分布式账本", "智能合约"],
                "analysis_type": "comprehensive_analysis",
                "description": "全面分析区块链技术专利，包括数据收集、搜索增强、深度分析和报告生成"
            },
            {
                "name": "5G通信技术趋势分析",
                "keywords": ["5G", "通信技术", "无线网络"],
                "analysis_type": "trend_analysis",
                "description": "分析5G通信技术的发展趋势和技术演进"
            },
            {
                "name": "新能源汽车竞争分析",
                "keywords": ["新能源汽车", "电动汽车", "电池技术"],
                "analysis_type": "competitive_analysis",
                "description": "分析新能源汽车领域的竞争格局和主要参与者"
            }
        ]
        
        self.demo_results = []
        self.system_initialized = False
    
    async def initialize_system(self) -> bool:
        """初始化专利分析系统."""
        try:
            logger.info("🚀 开始初始化专利分析系统...")
            
            # 获取专利系统初始化器
            initializer = get_global_patent_initializer(agent_registry)
            
            # 执行初始化
            success = await initializer.initialize()
            
            if success:
                logger.info("✅ 专利分析系统初始化成功")
                self.system_initialized = True
                
                # 显示系统状态
                await self.show_system_status()
                return True
            else:
                logger.error("❌ 专利分析系统初始化失败")
                return False
                
        except Exception as e:
            logger.error(f"❌ 系统初始化异常: {str(e)}")
            return False
    
    async def show_system_status(self):
        """显示系统状态."""
        try:
            logger.info("📊 系统状态检查...")
            
            # 获取健康检查结果
            health_status = await patent_system_health_check()
            
            print("\n" + "="*60)
            print("📋 专利分析系统状态报告")
            print("="*60)
            
            print(f"🔧 系统健康状态: {'✅ 健康' if health_status.get('is_healthy') else '❌ 异常'}")
            print(f"⏰ 检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 显示组件状态
            components = health_status.get("components", {})
            
            if "patent_agents" in components:
                agent_info = components["patent_agents"]
                print(f"\n🤖 专利Agent状态:")
                print(f"   - 注册状态: {'✅ 已注册' if agent_info.get('status') == 'healthy' else '❌ 未注册'}")
                print(f"   - 注册数量: {agent_info.get('registered_agents', 0)}")
            
            if "patent_workflows" in components:
                workflow_info = components["patent_workflows"]
                print(f"\n🔄 专利工作流状态:")
                print(f"   - 工作流状态: {'✅ 正常' if workflow_info.get('status') == 'healthy' else '❌ 异常'}")
            
            print("="*60 + "\n")
            
        except Exception as e:
            logger.error(f"获取系统状态失败: {str(e)}")
    
    async def run_demo_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """运行单个演示场景."""
        try:
            logger.info(f"🎯 开始演示场景: {scenario['name']}")
            
            print(f"\n{'='*60}")
            print(f"🎯 演示场景: {scenario['name']}")
            print(f"📝 描述: {scenario['description']}")
            print(f"🔍 关键词: {', '.join(scenario['keywords'])}")
            print(f"📊 分析类型: {scenario['analysis_type']}")
            print(f"{'='*60}")
            
            # 创建用户请求
            request_content = f"请进行{scenario['analysis_type']}，关键词：{', '.join(scenario['keywords'])}"
            
            user_request = UserRequest(
                content=request_content,
                user_id="demo_user",
                context={
                    "demo_scenario": scenario['name'],
                    "keywords": scenario['keywords'],
                    "analysis_type": scenario['analysis_type'],
                    "demo_mode": True
                }
            )
            
            # 获取专利协调Agent
            coordinator = await self.get_patent_coordinator()
            if not coordinator:
                raise Exception("无法获取专利协调Agent")
            
            # 执行分析
            start_time = datetime.now()
            logger.info(f"⏳ 开始执行专利分析...")
            
            response = await coordinator.process_request(user_request)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # 处理结果
            result = {
                "scenario": scenario,
                "request": user_request.dict(),
                "response": {
                    "agent_id": response.agent_id,
                    "agent_type": response.agent_type.value if response.agent_type else "unknown",
                    "content": response.response_content,
                    "confidence": response.confidence,
                    "collaboration_needed": response.collaboration_needed,
                    "metadata": response.metadata
                },
                "execution_time": duration,
                "timestamp": end_time.isoformat(),
                "success": response.confidence > 0.0
            }
            
            # 显示结果
            await self.display_scenario_result(result)
            
            logger.info(f"✅ 场景 '{scenario['name']}' 执行完成，耗时 {duration:.2f} 秒")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 场景 '{scenario['name']}' 执行失败: {str(e)}")
            
            error_result = {
                "scenario": scenario,
                "error": str(e),
                "success": False,
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"\n❌ 场景执行失败: {str(e)}")
            return error_result
    
    async def get_patent_coordinator(self):
        """获取专利协调Agent."""
        try:
            # 尝试获取已注册的专利协调Agent
            agents = agent_registry.get_agents_by_type(AgentType.PATENT_COORDINATOR)
            
            if agents:
                return agents[0]  # 使用第一个可用的协调Agent
            
            # 如果没有注册的Agent，创建一个临时的
            logger.warning("未找到注册的专利协调Agent，创建临时实例")
            
            from src.multi_agent_service.agents.patent.coordinator_agent import PatentCoordinatorAgent
            from src.multi_agent_service.models.config import AgentConfig
            from src.multi_agent_service.services.model_client import BaseModelClient
            from src.multi_agent_service.models.model_service import ModelConfig
            from src.multi_agent_service.models.enums import ModelProvider
            
            # 创建临时配置
            config = AgentConfig(
                agent_id="demo_patent_coordinator",
                agent_type=AgentType.PATENT_COORDINATOR,
                name="Demo Patent Coordinator",
                description="Temporary coordinator for demo",
                capabilities=["patent_coordination", "workflow_management"],
                config={}
            )
            
            # 创建临时模型客户端
            class DemoModelClient(BaseModelClient):
                def __init__(self):
                    mock_config = ModelConfig(
                        provider=ModelProvider.CUSTOM,
                        model_name="demo-client",
                        api_key="demo",
                        base_url="http://localhost",
                        timeout=30.0,
                        enabled=True
                    )
                    super().__init__(mock_config)
                
                async def initialize(self) -> bool:
                    return True
                
                async def generate_response(self, request):
                    return {"content": "Demo response"}
                
                async def health_check(self) -> bool:
                    return True
                
                async def close(self):
                    pass
            
            model_client = DemoModelClient()
            coordinator = PatentCoordinatorAgent(config, model_client)
            
            # 初始化
            await coordinator.initialize()
            
            return coordinator
            
        except Exception as e:
            logger.error(f"获取专利协调Agent失败: {str(e)}")
            return None
    
    async def display_scenario_result(self, result: Dict[str, Any]):
        """显示场景执行结果."""
        try:
            print(f"\n📊 执行结果:")
            print(f"   ⏱️  执行时间: {result.get('execution_time', 0):.2f} 秒")
            print(f"   ✅ 成功状态: {'成功' if result.get('success') else '失败'}")
            
            if result.get('success'):
                response = result.get('response', {})
                print(f"   🎯 置信度: {response.get('confidence', 0):.2f}")
                print(f"   🤝 需要协作: {'是' if response.get('collaboration_needed') else '否'}")
                
                # 显示响应内容的摘要
                content = response.get('content', '')
                if content:
                    # 显示前200个字符作为摘要
                    summary = content[:200] + "..." if len(content) > 200 else content
                    print(f"\n📝 响应摘要:")
                    print(f"   {summary}")
                
                # 显示元数据信息
                metadata = response.get('metadata', {})
                if metadata:
                    print(f"\n🔍 执行详情:")
                    if 'workflow_type' in metadata:
                        print(f"   - 工作流类型: {metadata['workflow_type']}")
                    if 'required_agents' in metadata:
                        print(f"   - 涉及Agent: {', '.join(metadata['required_agents'])}")
                    if 'coordination_id' in metadata:
                        print(f"   - 协调ID: {metadata['coordination_id']}")
            else:
                error = result.get('error', '未知错误')
                print(f"   ❌ 错误信息: {error}")
            
            print(f"   🕐 完成时间: {result.get('timestamp', 'unknown')}")
            
        except Exception as e:
            logger.error(f"显示结果失败: {str(e)}")
    
    async def run_all_scenarios(self):
        """运行所有演示场景."""
        try:
            logger.info("🎬 开始运行所有演示场景...")
            
            print(f"\n🎬 专利分析系统端到端演示")
            print(f"📅 演示时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"🎯 演示场景数量: {len(self.demo_scenarios)}")
            
            total_start_time = datetime.now()
            
            for i, scenario in enumerate(self.demo_scenarios, 1):
                print(f"\n🔄 执行场景 {i}/{len(self.demo_scenarios)}")
                
                result = await self.run_demo_scenario(scenario)
                self.demo_results.append(result)
                
                # 场景间暂停
                if i < len(self.demo_scenarios):
                    print(f"\n⏸️  暂停 2 秒后继续下一个场景...")
                    await asyncio.sleep(2)
            
            total_end_time = datetime.now()
            total_duration = (total_end_time - total_start_time).total_seconds()
            
            # 显示总结
            await self.display_demo_summary(total_duration)
            
        except Exception as e:
            logger.error(f"运行演示场景失败: {str(e)}")
    
    async def display_demo_summary(self, total_duration: float):
        """显示演示总结."""
        try:
            print(f"\n{'='*60}")
            print(f"📊 演示总结报告")
            print(f"{'='*60}")
            
            successful_scenarios = [r for r in self.demo_results if r.get('success')]
            failed_scenarios = [r for r in self.demo_results if not r.get('success')]
            
            print(f"📈 总体统计:")
            print(f"   - 总场景数: {len(self.demo_results)}")
            print(f"   - 成功场景: {len(successful_scenarios)}")
            print(f"   - 失败场景: {len(failed_scenarios)}")
            print(f"   - 成功率: {len(successful_scenarios)/len(self.demo_results)*100:.1f}%")
            print(f"   - 总执行时间: {total_duration:.2f} 秒")
            
            if successful_scenarios:
                avg_time = sum(r.get('execution_time', 0) for r in successful_scenarios) / len(successful_scenarios)
                avg_confidence = sum(r.get('response', {}).get('confidence', 0) for r in successful_scenarios) / len(successful_scenarios)
                
                print(f"\n✅ 成功场景分析:")
                print(f"   - 平均执行时间: {avg_time:.2f} 秒")
                print(f"   - 平均置信度: {avg_confidence:.2f}")
            
            if failed_scenarios:
                print(f"\n❌ 失败场景:")
                for result in failed_scenarios:
                    scenario_name = result.get('scenario', {}).get('name', 'Unknown')
                    error = result.get('error', 'Unknown error')
                    print(f"   - {scenario_name}: {error}")
            
            # 保存详细结果
            await self.save_demo_results()
            
            print(f"\n🎉 演示完成！详细结果已保存到 patent_demo_results.json")
            print(f"{'='*60}")
            
        except Exception as e:
            logger.error(f"显示演示总结失败: {str(e)}")
    
    async def save_demo_results(self):
        """保存演示结果到文件."""
        try:
            results_data = {
                "demo_info": {
                    "timestamp": datetime.now().isoformat(),
                    "total_scenarios": len(self.demo_scenarios),
                    "system_initialized": self.system_initialized
                },
                "scenarios": self.demo_scenarios,
                "results": self.demo_results,
                "summary": {
                    "total_count": len(self.demo_results),
                    "successful_count": len([r for r in self.demo_results if r.get('success')]),
                    "failed_count": len([r for r in self.demo_results if not r.get('success')])
                }
            }
            
            with open("patent_demo_results.json", "w", encoding="utf-8") as f:
                json.dump(results_data, f, ensure_ascii=False, indent=2)
            
            logger.info("演示结果已保存到 patent_demo_results.json")
            
        except Exception as e:
            logger.error(f"保存演示结果失败: {str(e)}")
    
    async def run_interactive_demo(self):
        """运行交互式演示."""
        try:
            print(f"\n🎮 专利分析系统交互式演示")
            print(f"{'='*60}")
            
            while True:
                print(f"\n📋 可用的演示场景:")
                for i, scenario in enumerate(self.demo_scenarios, 1):
                    print(f"   {i}. {scenario['name']}")
                    print(f"      📝 {scenario['description']}")
                
                print(f"   0. 退出演示")
                print(f"   99. 运行所有场景")
                
                try:
                    choice = input(f"\n请选择要运行的场景 (0-{len(self.demo_scenarios)}, 99): ").strip()
                    
                    if choice == "0":
                        print("👋 感谢使用专利分析系统演示！")
                        break
                    elif choice == "99":
                        await self.run_all_scenarios()
                        break
                    else:
                        choice_num = int(choice)
                        if 1 <= choice_num <= len(self.demo_scenarios):
                            scenario = self.demo_scenarios[choice_num - 1]
                            result = await self.run_demo_scenario(scenario)
                            self.demo_results.append(result)
                        else:
                            print("❌ 无效的选择，请重新输入")
                
                except ValueError:
                    print("❌ 请输入有效的数字")
                except KeyboardInterrupt:
                    print("\n👋 演示已中断")
                    break
                
        except Exception as e:
            logger.error(f"交互式演示失败: {str(e)}")


async def main():
    """主函数."""
    try:
        print("🚀 专利分析系统端到端演示")
        print("="*60)
        
        # 创建演示实例
        demo = PatentAnalysisDemo()
        
        # 初始化系统
        if not await demo.initialize_system():
            print("❌ 系统初始化失败，无法继续演示")
            return 1
        
        # 检查命令行参数
        if len(sys.argv) > 1:
            if sys.argv[1] == "--all":
                # 运行所有场景
                await demo.run_all_scenarios()
            elif sys.argv[1] == "--interactive":
                # 交互式模式
                await demo.run_interactive_demo()
            else:
                print(f"❌ 未知参数: {sys.argv[1]}")
                print("使用方法:")
                print("  python patent_analysis_demo.py           # 交互式模式")
                print("  python patent_analysis_demo.py --all     # 运行所有场景")
                print("  python patent_analysis_demo.py --interactive  # 交互式模式")
                return 1
        else:
            # 默认交互式模式
            await demo.run_interactive_demo()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n👋 演示已被用户中断")
        return 0
    except Exception as e:
        logger.error(f"演示执行失败: {str(e)}")
        print(f"❌ 演示执行失败: {str(e)}")
        return 1


if __name__ == "__main__":
    # 运行演示
    exit_code = asyncio.run(main())
    sys.exit(exit_code)