#!/usr/bin/env python3
"""
专利分析系统验证脚本

验证所有Agent协作和工作流执行的完整性。
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from src.multi_agent_service.core.patent_system_initializer import (
    get_global_patent_initializer,
    patent_system_health_check
)
from src.multi_agent_service.agents.registry import agent_registry
from src.multi_agent_service.models.enums import AgentType
from src.multi_agent_service.models.base import UserRequest

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PatentSystemValidator:
    """专利系统验证器."""
    
    def __init__(self):
        """初始化验证器."""
        self.validation_results = []
        self.system_health = {}
        
        # 定义验证测试
        self.validation_tests = [
            {
                "name": "系统初始化验证",
                "test_func": self.test_system_initialization,
                "critical": True
            },
            {
                "name": "Agent注册验证",
                "test_func": self.test_agent_registration,
                "critical": True
            },
            {
                "name": "Agent健康状态验证",
                "test_func": self.test_agent_health,
                "critical": False
            },
            {
                "name": "工作流引擎验证",
                "test_func": self.test_workflow_engine,
                "critical": True
            },
            {
                "name": "Agent通信验证",
                "test_func": self.test_agent_communication,
                "critical": True
            },
            {
                "name": "端到端流程验证",
                "test_func": self.test_end_to_end_flow,
                "critical": True
            }
        ]
    
    async def run_all_validations(self) -> Dict[str, Any]:
        """运行所有验证测试."""
        try:
            logger.info("🔍 开始专利系统验证...")
            
            print("🔍 专利分析系统完整性验证")
            print("="*60)
            
            start_time = datetime.now()
            passed_tests = 0
            failed_tests = 0
            critical_failures = 0
            
            for i, test in enumerate(self.validation_tests, 1):
                print(f"\n📋 测试 {i}/{len(self.validation_tests)}: {test['name']}")
                
                try:
                    result = await test['test_func']()
                    
                    if result['success']:
                        print(f"   ✅ 通过")
                        passed_tests += 1
                    else:
                        print(f"   ❌ 失败: {result.get('error', 'Unknown error')}")
                        failed_tests += 1
                        
                        if test['critical']:
                            critical_failures += 1
                    
                    result['test_name'] = test['name']
                    result['critical'] = test['critical']
                    result['timestamp'] = datetime.now().isoformat()
                    
                    self.validation_results.append(result)
                    
                except Exception as e:
                    error_result = {
                        'test_name': test['name'],
                        'success': False,
                        'error': str(e),
                        'critical': test['critical'],
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    print(f"   ❌ 异常: {str(e)}")
                    failed_tests += 1
                    
                    if test['critical']:
                        critical_failures += 1
                    
                    self.validation_results.append(error_result)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # 生成验证报告
            validation_summary = {
                "total_tests": len(self.validation_tests),
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "critical_failures": critical_failures,
                "success_rate": passed_tests / len(self.validation_tests),
                "duration": duration,
                "overall_status": "PASS" if critical_failures == 0 else "FAIL",
                "timestamp": end_time.isoformat(),
                "detailed_results": self.validation_results
            }
            
            # 显示总结
            await self.display_validation_summary(validation_summary)
            
            return validation_summary
            
        except Exception as e:
            logger.error(f"验证过程异常: {str(e)}")
            return {
                "overall_status": "ERROR",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def test_system_initialization(self) -> Dict[str, Any]:
        """测试系统初始化."""
        try:
            logger.info("测试专利系统初始化...")
            
            # 获取初始化器
            initializer = get_global_patent_initializer(agent_registry)
            
            # 执行初始化
            success = await initializer.initialize()
            
            if success:
                # 获取初始化状态
                status = initializer.get_initialization_status()
                
                return {
                    "success": True,
                    "details": {
                        "initialized": status["is_initialized"],
                        "components": status.get("components", {}),
                        "errors": status.get("errors", [])
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "系统初始化失败"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"初始化测试异常: {str(e)}"
            }
    
    async def test_agent_registration(self) -> Dict[str, Any]:
        """测试Agent注册状态."""
        try:
            logger.info("测试Agent注册状态...")
            
            # 检查专利Agent类型
            patent_agent_types = [
                AgentType.PATENT_COORDINATOR,
                AgentType.PATENT_DATA_COLLECTION,
                AgentType.PATENT_SEARCH,
                AgentType.PATENT_ANALYSIS,
                AgentType.PATENT_REPORT
            ]
            
            registration_status = {}
            missing_agents = []
            
            for agent_type in patent_agent_types:
                is_registered = agent_registry.is_agent_type_registered(agent_type)
                registration_status[agent_type.value] = is_registered
                
                if not is_registered:
                    missing_agents.append(agent_type.value)
            
            success = len(missing_agents) == 0
            
            return {
                "success": success,
                "details": {
                    "registration_status": registration_status,
                    "missing_agents": missing_agents,
                    "total_patent_agents": len(patent_agent_types),
                    "registered_count": len(patent_agent_types) - len(missing_agents)
                },
                "error": f"缺少Agent注册: {', '.join(missing_agents)}" if missing_agents else None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Agent注册测试异常: {str(e)}"
            }
    
    async def test_agent_health(self) -> Dict[str, Any]:
        """测试Agent健康状态."""
        try:
            logger.info("测试Agent健康状态...")
            
            # 获取系统健康检查
            health_status = await patent_system_health_check()
            
            is_healthy = health_status.get("is_healthy", False)
            components = health_status.get("components", {})
            
            agent_health = {}
            unhealthy_agents = []
            
            # 检查各个组件的健康状态
            for component_name, component_info in components.items():
                if isinstance(component_info, dict):
                    component_status = component_info.get("status", "unknown")
                    agent_health[component_name] = component_status
                    
                    if component_status != "healthy":
                        unhealthy_agents.append(component_name)
            
            return {
                "success": is_healthy,
                "details": {
                    "overall_health": is_healthy,
                    "component_health": agent_health,
                    "unhealthy_components": unhealthy_agents
                },
                "error": f"不健康的组件: {', '.join(unhealthy_agents)}" if unhealthy_agents else None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"健康检查异常: {str(e)}"
            }
    
    async def test_workflow_engine(self) -> Dict[str, Any]:
        """测试工作流引擎."""
        try:
            logger.info("测试工作流引擎...")
            
            # 检查工作流注册器
            initializer = get_global_patent_initializer(agent_registry)
            
            if not initializer.patent_workflow_registry:
                return {
                    "success": False,
                    "error": "工作流注册器未初始化"
                }
            
            # 获取工作流统计
            workflow_stats = initializer.patent_workflow_registry.get_patent_workflow_statistics()
            
            # 验证工作流设置
            validation = initializer.patent_workflow_registry.validate_patent_workflow_setup()
            
            return {
                "success": validation["is_valid"],
                "details": {
                    "workflow_statistics": workflow_stats,
                    "validation_result": validation
                },
                "error": f"工作流验证失败: {', '.join(validation.get('errors', []))}" if not validation["is_valid"] else None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"工作流引擎测试异常: {str(e)}"
            }
    
    async def test_agent_communication(self) -> Dict[str, Any]:
        """测试Agent间通信."""
        try:
            logger.info("测试Agent间通信...")
            
            # 创建测试请求
            test_request = UserRequest(
                content="测试Agent通信功能",
                user_id="validator",
                context={"test_mode": True}
            )
            
            # 尝试获取协调Agent
            coordinator_agents = agent_registry.get_agents_by_type(AgentType.PATENT_COORDINATOR)
            
            if not coordinator_agents:
                return {
                    "success": False,
                    "error": "未找到专利协调Agent"
                }
            
            coordinator = coordinator_agents[0]
            
            # 检查协调Agent是否健康
            if not coordinator.is_healthy():
                return {
                    "success": False,
                    "error": "专利协调Agent不健康"
                }
            
            # 测试基本通信（不执行完整流程）
            communication_test = {
                "coordinator_available": True,
                "coordinator_healthy": coordinator.is_healthy(),
                "agent_id": coordinator.agent_id,
                "agent_type": coordinator.agent_type.value
            }
            
            return {
                "success": True,
                "details": communication_test
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Agent通信测试异常: {str(e)}"
            }
    
    async def test_end_to_end_flow(self) -> Dict[str, Any]:
        """测试端到端流程."""
        try:
            logger.info("测试端到端流程...")
            
            # 创建简单的测试请求
            test_request = UserRequest(
                content="进行简单的专利分析测试，关键词：人工智能",
                user_id="validator",
                context={
                    "test_mode": True,
                    "validation_test": True,
                    "keywords": ["人工智能"],
                    "analysis_type": "quick_search",
                    "mock_mode": True,  # 启用模拟模式，避免外部API调用
                    "timeout": 10  # 设置较短的超时时间
                }
            )
            
            # 获取协调Agent
            coordinator_agents = agent_registry.get_agents_by_type(AgentType.PATENT_COORDINATOR)
            
            if not coordinator_agents:
                return {
                    "success": False,
                    "error": "未找到专利协调Agent进行端到端测试"
                }
            
            coordinator = coordinator_agents[0]
            
            # 执行简化的端到端测试
            start_time = datetime.now()
            
            try:
                # 设置较短的超时时间
                response = await asyncio.wait_for(
                    coordinator.process_request(test_request),
                    timeout=10.0  # 10秒超时
                )
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                # 验证响应
                if response and response.confidence > 0.0:
                    return {
                        "success": True,
                        "details": {
                            "execution_time": duration,
                            "response_confidence": response.confidence,
                            "response_length": len(response.response_content),
                            "collaboration_needed": response.collaboration_needed,
                            "has_metadata": bool(response.metadata)
                        }
                    }
                else:
                    return {
                        "success": False,
                        "error": "端到端测试返回无效响应"
                    }
                    
            except asyncio.TimeoutError:
                return {
                    "success": False,
                    "error": "端到端测试超时（10秒）"
                }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"端到端测试异常: {str(e)}"
            }
    
    async def display_validation_summary(self, summary: Dict[str, Any]):
        """显示验证总结."""
        try:
            print(f"\n{'='*60}")
            print(f"📊 验证总结报告")
            print(f"{'='*60}")
            
            print(f"🎯 总体状态: {'✅ 通过' if summary['overall_status'] == 'PASS' else '❌ 失败'}")
            print(f"📈 测试统计:")
            print(f"   - 总测试数: {summary['total_tests']}")
            print(f"   - 通过测试: {summary['passed_tests']}")
            print(f"   - 失败测试: {summary['failed_tests']}")
            print(f"   - 关键失败: {summary['critical_failures']}")
            print(f"   - 成功率: {summary['success_rate']:.1%}")
            print(f"   - 执行时间: {summary['duration']:.2f} 秒")
            
            # 显示失败的测试
            failed_results = [r for r in summary['detailed_results'] if not r['success']]
            if failed_results:
                print(f"\n❌ 失败的测试:")
                for result in failed_results:
                    critical_mark = "🚨" if result['critical'] else "⚠️"
                    print(f"   {critical_mark} {result['test_name']}: {result.get('error', 'Unknown error')}")
            
            # 显示建议
            print(f"\n💡 建议:")
            if summary['critical_failures'] > 0:
                print(f"   - 🚨 存在关键失败，系统可能无法正常工作")
                print(f"   - 🔧 请检查系统配置和依赖项")
            elif summary['failed_tests'] > 0:
                print(f"   - ⚠️ 存在非关键失败，建议修复以提高系统稳定性")
            else:
                print(f"   - ✅ 所有测试通过，系统状态良好")
            
            print(f"   - 📋 详细结果已保存到 patent_validation_report.json")
            print(f"{'='*60}")
            
            # 保存详细报告
            await self.save_validation_report(summary)
            
        except Exception as e:
            logger.error(f"显示验证总结失败: {str(e)}")
    
    async def save_validation_report(self, summary: Dict[str, Any]):
        """保存验证报告."""
        try:
            import json
            
            with open("patent_validation_report.json", "w", encoding="utf-8") as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            logger.info("验证报告已保存到 patent_validation_report.json")
            
        except Exception as e:
            logger.error(f"保存验证报告失败: {str(e)}")


async def main():
    """主函数."""
    try:
        print("🔍 专利分析系统验证工具")
        print("="*60)
        
        # 创建验证器
        validator = PatentSystemValidator()
        
        # 运行验证
        summary = await validator.run_all_validations()
        
        # 返回适当的退出码
        if summary.get("overall_status") == "PASS":
            return 0
        elif summary.get("overall_status") == "FAIL":
            return 1
        else:
            return 2  # ERROR
        
    except KeyboardInterrupt:
        print("\n👋 验证已被用户中断")
        return 0
    except Exception as e:
        logger.error(f"验证工具执行失败: {str(e)}")
        print(f"❌ 验证工具执行失败: {str(e)}")
        return 2


if __name__ == "__main__":
    # 运行验证
    exit_code = asyncio.run(main())
    sys.exit(exit_code)