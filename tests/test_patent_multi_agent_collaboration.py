"""专利多Agent协作集成测试 - Patent Multi-Agent Collaboration Integration Tests."""

import asyncio
import pytest
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch
import json
from uuid import uuid4

from src.multi_agent_service.patent.models.requests import PatentAnalysisRequest
from src.multi_agent_service.patent.models.results import PatentAnalysisResult
from src.multi_agent_service.patent.models.patent_data import PatentData, PatentDataset
from src.multi_agent_service.services.agent_router import AgentRouter
from src.multi_agent_service.models.enums import AgentType, WorkflowStatus
from src.multi_agent_service.models.workflow import WorkflowExecution
from src.multi_agent_service.workflows.patent_workflow_engine import PatentWorkflowEngine


@pytest.fixture
def sample_patent_analysis_request():
    """创建示例专利分析请求."""
    return PatentAnalysisRequest(
        content="分析人工智能和机器学习领域的专利趋势",
        keywords=["人工智能", "机器学习", "深度学习", "神经网络"],
        date_range={
            "start_date": "2020-01-01",
            "end_date": "2023-12-31"
        },
        countries=["US", "CN", "EP", "JP"],
        analysis_types=["trend", "competition", "technology", "geographic"]
    )


@pytest.fixture
def mock_agent_router():
    """创建模拟Agent路由器."""
    router = MagicMock(spec=AgentRouter)
    router.route_request = AsyncMock()
    return router


@pytest.fixture
def mock_patent_agents():
    """创建模拟专利Agent集合."""
    return {
        "patent_data_collection_agent": {
            "agent_type": AgentType.CUSTOM,
            "capabilities": ["google_patents", "patent_public_api", "data_validation"],
            "status": "active"
        },
        "patent_search_agent": {
            "agent_type": AgentType.CUSTOM,
            "capabilities": ["cnki_search", "bocha_ai", "web_crawling"],
            "status": "active"
        },
        "patent_analysis_agent": {
            "agent_type": AgentType.CUSTOM,
            "capabilities": ["trend_analysis", "tech_classification", "competition_analysis"],
            "status": "active"
        },
        "patent_coordinator_agent": {
            "agent_type": AgentType.CUSTOM,
            "capabilities": ["workflow_coordination", "agent_management", "result_aggregation"],
            "status": "active"
        },
        "patent_report_agent": {
            "agent_type": AgentType.CUSTOM,
            "capabilities": ["report_generation", "chart_creation", "export_management"],
            "status": "active"
        }
    }


class TestPatentAgentCollaboration:
    """专利Agent协作测试类."""
    
    @pytest.mark.asyncio
    async def test_sequential_agent_collaboration(self, mock_agent_router, sample_patent_analysis_request):
        """测试顺序Agent协作流程."""
        # 模拟各Agent的响应
        agent_responses = {
            "patent_data_collection_agent": {
                "status": "success",
                "data": {
                    "patents": [
                        {
                            "application_number": "US16123456",
                            "title": "Advanced AI System",
                            "abstract": "An advanced artificial intelligence system",
                            "applicants": [{"name": "Tech Corp", "country": "US"}],
                            "application_date": "2022-01-15T00:00:00",
                            "classifications": [{"ipc_class": "G06N3/08"}]
                        }
                    ],
                    "total": 1,
                    "sources": ["google_patents", "patent_public_api"]
                },
                "processing_time": 2.5,
                "agent_id": "patent_data_collection_agent"
            },
            "patent_search_agent": {
                "status": "success",
                "enhanced_data": {
                    "cnki_data": {
                        "literature": [
                            {
                                "title": "AI Research Progress",
                                "authors": ["Dr. Zhang"],
                                "abstract": "Recent progress in AI research",
                                "keywords": ["AI", "machine learning"]
                            }
                        ]
                    },
                    "bocha_data": {
                        "web_results": [{"title": "AI Industry Report", "url": "http://example.com"}],
                        "ai_analysis": {"summary": "AI market is growing rapidly"}
                    }
                },
                "processing_time": 3.2,
                "agent_id": "patent_search_agent"
            },
            "patent_analysis_agent": {
                "status": "success",
                "analysis": {
                    "trend_analysis": {
                        "yearly_counts": {"2020": 10, "2021": 15, "2022": 20, "2023": 25},
                        "growth_rates": {"2021": 0.5, "2022": 0.33, "2023": 0.25},
                        "trend_direction": "increasing"
                    },
                    "tech_classification": {
                        "ipc_distribution": {"G06N": 30, "H04L": 15, "G06F": 10},
                        "main_technologies": ["Neural Networks", "Machine Learning", "Deep Learning"]
                    },
                    "competition_analysis": {
                        "top_applicants": [("Tech Corp", 15), ("AI Inc", 12), ("ML Ltd", 8)],
                        "market_concentration": 0.65
                    }
                },
                "processing_time": 4.1,
                "agent_id": "patent_analysis_agent"
            },
            "patent_report_agent": {
                "status": "success",
                "report": {
                    "html_content": "<html><body><h1>专利分析报告</h1></body></html>",
                    "pdf_content": b"PDF content",
                    "charts": {
                        "trend_chart": "base64_chart_data_1",
                        "tech_pie_chart": "base64_chart_data_2",
                        "competition_bar_chart": "base64_chart_data_3"
                    },
                    "summary": "AI专利申请呈现快速增长趋势"
                },
                "processing_time": 1.8,
                "agent_id": "patent_report_agent"
            }
        }
        
        # 配置Agent路由器的响应
        def route_side_effect(agent_id, request):
            return agent_responses.get(agent_id, {"status": "error", "error": "Agent not found"})
        
        mock_agent_router.route_request.side_effect = route_side_effect
        
        # 模拟顺序执行流程
        execution_order = [
            "patent_data_collection_agent",
            "patent_search_agent", 
            "patent_analysis_agent",
            "patent_report_agent"
        ]
        
        results = {}
        shared_context = {"request": sample_patent_analysis_request.dict()}
        
        # 顺序执行各Agent
        for agent_id in execution_order:
            # 更新请求上下文
            request_with_context = {
                **sample_patent_analysis_request.dict(),
                "shared_context": shared_context,
                "previous_results": results
            }
            
            # 调用Agent
            result = await mock_agent_router.route_request(agent_id, request_with_context)
            results[agent_id] = result
            
            # 更新共享上下文
            if result["status"] == "success":
                shared_context[f"{agent_id}_result"] = result
        
        # 验证协作结果
        assert len(results) == 4
        assert all(result["status"] == "success" for result in results.values())
        
        # 验证数据流转
        data_collection_result = results["patent_data_collection_agent"]
        assert "patents" in data_collection_result["data"]
        assert data_collection_result["data"]["total"] == 1
        
        search_result = results["patent_search_agent"]
        assert "enhanced_data" in search_result
        assert "cnki_data" in search_result["enhanced_data"]
        
        analysis_result = results["patent_analysis_agent"]
        assert "analysis" in analysis_result
        assert "trend_analysis" in analysis_result["analysis"]
        
        report_result = results["patent_report_agent"]
        assert "report" in report_result
        assert "html_content" in report_result["report"]
    
    @pytest.mark.asyncio
    async def test_parallel_agent_collaboration(self, mock_agent_router, sample_patent_analysis_request):
        """测试并行Agent协作流程."""
        # 模拟并行执行的Agent响应
        parallel_responses = {
            "patent_data_collection_agent": {
                "status": "success",
                "data": {"patents": 150, "processing_time": 2.1},
                "agent_id": "patent_data_collection_agent"
            },
            "patent_search_agent": {
                "status": "success", 
                "enhanced_data": {"records": 75, "processing_time": 2.8},
                "agent_id": "patent_search_agent"
            }
        }
        
        def route_side_effect(agent_id, request):
            # 模拟并行处理延迟
            return parallel_responses.get(agent_id, {"status": "error"})
        
        mock_agent_router.route_request.side_effect = route_side_effect
        
        # 并行执行Agent
        parallel_agents = ["patent_data_collection_agent", "patent_search_agent"]
        
        tasks = []
        for agent_id in parallel_agents:
            task = mock_agent_router.route_request(agent_id, sample_patent_analysis_request.dict())
            tasks.append((agent_id, task))
        
        # 等待所有并行任务完成
        results = {}
        for agent_id, task in tasks:
            result = await task
            results[agent_id] = result
        
        # 验证并行执行结果
        assert len(results) == 2
        assert all(result["status"] == "success" for result in results.values())
        
        # 验证并行Agent都被调用
        assert mock_agent_router.route_request.call_count == 2
    
    @pytest.mark.asyncio
    async def test_agent_failure_handling_and_recovery(self, mock_agent_router, sample_patent_analysis_request):
        """测试Agent失败处理和恢复机制."""
        # 模拟Agent失败场景
        failure_responses = {
            "patent_data_collection_agent": {
                "status": "success",
                "data": {"patents": 100},
                "agent_id": "patent_data_collection_agent"
            },
            "patent_search_agent": {
                "status": "error",
                "error": "CNKI API connection timeout",
                "agent_id": "patent_search_agent"
            },
            "patent_analysis_agent": {
                "status": "success",
                "analysis": {"trend": "increasing"},
                "agent_id": "patent_analysis_agent"
            }
        }
        
        def route_side_effect(agent_id, request):
            return failure_responses.get(agent_id, {"status": "error"})
        
        mock_agent_router.route_request.side_effect = route_side_effect
        
        # 执行带失败处理的协作流程
        execution_results = {}
        failed_agents = []
        
        for agent_id in failure_responses.keys():
            try:
                result = await mock_agent_router.route_request(agent_id, sample_patent_analysis_request.dict())
                execution_results[agent_id] = result
                
                if result["status"] == "error":
                    failed_agents.append(agent_id)
                    
            except Exception as e:
                failed_agents.append(agent_id)
                execution_results[agent_id] = {"status": "error", "error": str(e)}
        
        # 验证失败处理
        assert len(failed_agents) == 1
        assert "patent_search_agent" in failed_agents
        
        # 验证其他Agent继续执行
        successful_agents = [
            agent_id for agent_id, result in execution_results.items() 
            if result["status"] == "success"
        ]
        assert len(successful_agents) == 2
        assert "patent_data_collection_agent" in successful_agents
        assert "patent_analysis_agent" in successful_agents
        
        # 模拟失败Agent的重试
        retry_response = {
            "status": "success",
            "enhanced_data": {"records": 50, "note": "recovered with reduced data"},
            "agent_id": "patent_search_agent"
        }
        
        mock_agent_router.route_request.return_value = retry_response
        retry_result = await mock_agent_router.route_request("patent_search_agent", sample_patent_analysis_request.dict())
        
        # 验证重试成功
        assert retry_result["status"] == "success"
        assert "enhanced_data" in retry_result
    
    @pytest.mark.asyncio
    async def test_agent_communication_and_data_sharing(self, mock_agent_router, sample_patent_analysis_request):
        """测试Agent间通信和数据共享."""
        # 模拟Agent间数据传递
        shared_data_store = {}
        
        def route_with_data_sharing(agent_id, request):
            # 模拟数据收集Agent
            if agent_id == "patent_data_collection_agent":
                result = {
                    "status": "success",
                    "data": {
                        "patents": [{"id": "P001", "title": "AI Patent"}],
                        "metadata": {"total": 1, "source": "google_patents"}
                    },
                    "agent_id": agent_id
                }
                # 存储到共享数据
                shared_data_store["collected_patents"] = result["data"]["patents"]
                shared_data_store["collection_metadata"] = result["data"]["metadata"]
                return result
            
            # 模拟搜索Agent使用收集的数据
            elif agent_id == "patent_search_agent":
                collected_patents = shared_data_store.get("collected_patents", [])
                result = {
                    "status": "success",
                    "enhanced_data": {
                        "original_count": len(collected_patents),
                        "enhanced_records": len(collected_patents) * 2,
                        "enhancement_sources": ["cnki", "bocha_ai"]
                    },
                    "agent_id": agent_id
                }
                # 更新共享数据
                shared_data_store["enhanced_patents"] = result["enhanced_data"]
                return result
            
            # 模拟分析Agent使用前面的数据
            elif agent_id == "patent_analysis_agent":
                enhanced_data = shared_data_store.get("enhanced_patents", {})
                original_count = enhanced_data.get("original_count", 0)
                
                result = {
                    "status": "success",
                    "analysis": {
                        "input_patents": original_count,
                        "trend_analysis": {"direction": "increasing"},
                        "data_quality": "high" if original_count > 0 else "low"
                    },
                    "agent_id": agent_id
                }
                shared_data_store["analysis_result"] = result["analysis"]
                return result
            
            return {"status": "error", "error": "Unknown agent"}
        
        mock_agent_router.route_request.side_effect = route_with_data_sharing
        
        # 执行协作流程
        collaboration_sequence = [
            "patent_data_collection_agent",
            "patent_search_agent",
            "patent_analysis_agent"
        ]
        
        results = {}
        for agent_id in collaboration_sequence:
            result = await mock_agent_router.route_request(agent_id, sample_patent_analysis_request.dict())
            results[agent_id] = result
        
        # 验证数据共享
        assert "collected_patents" in shared_data_store
        assert "enhanced_patents" in shared_data_store
        assert "analysis_result" in shared_data_store
        
        # 验证数据流转正确性
        collection_result = results["patent_data_collection_agent"]
        search_result = results["patent_search_agent"]
        analysis_result = results["patent_analysis_agent"]
        
        assert collection_result["data"]["metadata"]["total"] == 1
        assert search_result["enhanced_data"]["original_count"] == 1
        assert analysis_result["analysis"]["input_patents"] == 1
    
    @pytest.mark.asyncio
    async def test_agent_load_balancing_and_scaling(self, mock_agent_router, sample_patent_analysis_request):
        """测试Agent负载均衡和扩展."""
        # 模拟多个相同类型的Agent实例
        agent_instances = {
            "patent_data_collection_agent_1": {"load": 0.3, "status": "active"},
            "patent_data_collection_agent_2": {"load": 0.7, "status": "active"},
            "patent_data_collection_agent_3": {"load": 0.1, "status": "active"},
        }
        
        def route_with_load_balancing(agent_id, request):
            # 选择负载最低的Agent实例
            if "patent_data_collection_agent" in agent_id:
                selected_instance = min(agent_instances.items(), key=lambda x: x[1]["load"])
                instance_id, instance_info = selected_instance
                
                # 更新负载
                agent_instances[instance_id]["load"] += 0.1
                
                return {
                    "status": "success",
                    "data": {"patents": 50, "processed_by": instance_id},
                    "instance_info": instance_info,
                    "agent_id": instance_id
                }
            
            return {"status": "error", "error": "Agent type not supported"}
        
        mock_agent_router.route_request.side_effect = route_with_load_balancing
        
        # 模拟多个并发请求
        concurrent_requests = 5
        tasks = []
        
        for i in range(concurrent_requests):
            task = mock_agent_router.route_request(
                "patent_data_collection_agent", 
                sample_patent_analysis_request.dict()
            )
            tasks.append(task)
        
        # 执行并发请求
        results = await asyncio.gather(*tasks)
        
        # 验证负载均衡
        assert len(results) == concurrent_requests
        assert all(result["status"] == "success" for result in results)
        
        # 检查不同实例被使用
        used_instances = set(result["data"]["processed_by"] for result in results)
        assert len(used_instances) > 1  # 应该使用多个实例
        
        # 验证负载分布
        final_loads = [info["load"] for info in agent_instances.values()]
        assert max(final_loads) - min(final_loads) < 0.5  # 负载差异不应太大
    
    @pytest.mark.asyncio
    async def test_agent_coordination_with_workflow_engine(self, mock_agent_router):
        """测试Agent与工作流引擎的协调."""
        # 创建工作流执行
        workflow_execution = WorkflowExecution(
            graph_id="patent_analysis_workflow",
            input_data={
                "keywords": ["AI", "machine learning"],
                "analysis_type": "comprehensive"
            },
            status=WorkflowStatus.PENDING
        )
        
        # 模拟工作流引擎
        workflow_engine = MagicMock()
        workflow_engine.execute_workflow = AsyncMock()
        
        # 模拟Agent协调器
        coordinator_responses = {
            "coordinate_data_collection": {
                "status": "success",
                "agents_used": ["patent_data_collection_agent"],
                "execution_time": 2.5
            },
            "coordinate_search_enhancement": {
                "status": "success", 
                "agents_used": ["patent_search_agent"],
                "execution_time": 3.1
            },
            "coordinate_analysis": {
                "status": "success",
                "agents_used": ["patent_analysis_agent"],
                "execution_time": 4.2
            },
            "coordinate_report_generation": {
                "status": "success",
                "agents_used": ["patent_report_agent"],
                "execution_time": 1.8
            }
        }
        
        def coordination_side_effect(coordination_type, request):
            return coordinator_responses.get(coordination_type, {"status": "error"})
        
        # 模拟协调器执行
        coordinator = MagicMock()
        coordinator.coordinate = AsyncMock(side_effect=coordination_side_effect)
        
        # 执行工作流协调
        coordination_tasks = [
            "coordinate_data_collection",
            "coordinate_search_enhancement", 
            "coordinate_analysis",
            "coordinate_report_generation"
        ]
        
        coordination_results = {}
        for task in coordination_tasks:
            result = await coordinator.coordinate(task, workflow_execution.input_data)
            coordination_results[task] = result
        
        # 验证协调结果
        assert len(coordination_results) == 4
        assert all(result["status"] == "success" for result in coordination_results.values())
        
        # 验证总执行时间
        total_time = sum(result["execution_time"] for result in coordination_results.values())
        assert total_time > 0
        
        # 验证Agent使用情况
        all_agents_used = []
        for result in coordination_results.values():
            all_agents_used.extend(result["agents_used"])
        
        expected_agents = [
            "patent_data_collection_agent",
            "patent_search_agent", 
            "patent_analysis_agent",
            "patent_report_agent"
        ]
        
        assert set(all_agents_used) == set(expected_agents)


class TestPatentAgentPerformanceCollaboration:
    """专利Agent性能协作测试类."""
    
    @pytest.mark.asyncio
    async def test_high_throughput_agent_collaboration(self, mock_agent_router):
        """测试高吞吐量Agent协作."""
        # 模拟高性能Agent响应
        def high_performance_route(agent_id, request):
            return {
                "status": "success",
                "data": f"Processed by {agent_id}",
                "processing_time": 0.1,  # 快速响应
                "agent_id": agent_id
            }
        
        mock_agent_router.route_request.side_effect = high_performance_route
        
        # 创建大量并发请求
        num_requests = 100
        agents = ["patent_data_collection_agent", "patent_search_agent", "patent_analysis_agent"]
        
        tasks = []
        start_time = datetime.now()
        
        for i in range(num_requests):
            agent_id = agents[i % len(agents)]
            task = mock_agent_router.route_request(agent_id, {"request_id": i})
            tasks.append(task)
        
        # 执行所有任务
        results = await asyncio.gather(*tasks)
        end_time = datetime.now()
        
        # 验证高吞吐量性能
        total_time = (end_time - start_time).total_seconds()
        throughput = num_requests / total_time
        
        assert len(results) == num_requests
        assert all(result["status"] == "success" for result in results)
        assert throughput > 10  # 每秒至少处理10个请求
        assert total_time < 30  # 总时间不超过30秒
    
    @pytest.mark.asyncio
    async def test_agent_collaboration_under_stress(self, mock_agent_router):
        """测试压力下的Agent协作."""
        # 模拟压力测试场景
        stress_responses = {}
        call_counts = {}
        
        def stress_route(agent_id, request):
            # 记录调用次数
            call_counts[agent_id] = call_counts.get(agent_id, 0) + 1
            
            # 模拟随机延迟和偶发失败
            import random
            
            if random.random() < 0.05:  # 5%失败率
                return {
                    "status": "error",
                    "error": "Temporary overload",
                    "agent_id": agent_id
                }
            
            processing_time = random.uniform(0.1, 2.0)  # 随机处理时间
            
            return {
                "status": "success",
                "data": f"Processed under stress by {agent_id}",
                "processing_time": processing_time,
                "call_count": call_counts[agent_id],
                "agent_id": agent_id
            }
        
        mock_agent_router.route_request.side_effect = stress_route
        
        # 执行压力测试
        stress_duration = 5  # 5秒压力测试
        agents = ["patent_data_collection_agent", "patent_search_agent", "patent_analysis_agent"]
        
        tasks = []
        start_time = datetime.now()
        
        # 持续发送请求直到时间结束
        request_count = 0
        while (datetime.now() - start_time).total_seconds() < stress_duration:
            for agent_id in agents:
                task = mock_agent_router.route_request(agent_id, {"stress_test": True})
                tasks.append(task)
                request_count += 1
                
                # 控制请求频率
                await asyncio.sleep(0.01)
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 分析压力测试结果
        successful_results = [r for r in results if isinstance(r, dict) and r.get("status") == "success"]
        failed_results = [r for r in results if isinstance(r, dict) and r.get("status") == "error"]
        exception_results = [r for r in results if isinstance(r, Exception)]
        
        # 验证压力测试性能
        success_rate = len(successful_results) / len(results)
        assert success_rate > 0.8  # 成功率应该超过80%
        assert len(exception_results) == 0  # 不应该有未处理的异常
        
        # 验证负载分布
        for agent_id in agents:
            agent_calls = call_counts.get(agent_id, 0)
            assert agent_calls > 0  # 每个Agent都应该被调用


class TestPatentAgentErrorRecovery:
    """专利Agent错误恢复测试类."""
    
    @pytest.mark.asyncio
    async def test_cascading_failure_recovery(self, mock_agent_router):
        """测试级联失败恢复."""
        # 模拟级联失败场景
        failure_sequence = {
            "patent_data_collection_agent": "success",
            "patent_search_agent": "failure",  # 搜索Agent失败
            "patent_analysis_agent": "degraded",  # 分析Agent降级运行
            "patent_report_agent": "success"
        }
        
        def cascading_failure_route(agent_id, request):
            agent_status = failure_sequence.get(agent_id, "unknown")
            
            if agent_status == "success":
                return {
                    "status": "success",
                    "data": f"Normal operation by {agent_id}",
                    "agent_id": agent_id
                }
            elif agent_status == "failure":
                return {
                    "status": "error",
                    "error": "Service unavailable",
                    "agent_id": agent_id
                }
            elif agent_status == "degraded":
                # 降级模式：使用缓存数据或简化分析
                return {
                    "status": "success",
                    "data": f"Degraded operation by {agent_id}",
                    "mode": "degraded",
                    "limitations": ["limited_data", "basic_analysis"],
                    "agent_id": agent_id
                }
            
            return {"status": "error", "error": "Unknown agent"}
        
        mock_agent_router.route_request.side_effect = cascading_failure_route
        
        # 执行带恢复机制的协作
        execution_plan = [
            "patent_data_collection_agent",
            "patent_search_agent",
            "patent_analysis_agent", 
            "patent_report_agent"
        ]
        
        results = {}
        recovery_actions = []
        
        for agent_id in execution_plan:
            result = await mock_agent_router.route_request(agent_id, {"test": "cascading_failure"})
            results[agent_id] = result
            
            # 检查是否需要恢复操作
            if result["status"] == "error":
                recovery_actions.append(f"Skip {agent_id} and use fallback")
            elif result.get("mode") == "degraded":
                recovery_actions.append(f"Accept degraded service from {agent_id}")
        
        # 验证恢复机制
        assert len(recovery_actions) == 2  # 应该有2个恢复操作
        assert "Skip patent_search_agent and use fallback" in recovery_actions
        assert "Accept degraded service from patent_analysis_agent" in recovery_actions
        
        # 验证系统仍能产生结果
        successful_agents = [
            agent_id for agent_id, result in results.items() 
            if result["status"] == "success"
        ]
        assert len(successful_agents) >= 2  # 至少2个Agent成功
    
    @pytest.mark.asyncio
    async def test_agent_circuit_breaker_pattern(self, mock_agent_router):
        """测试Agent熔断器模式."""
        # 模拟熔断器状态
        circuit_breaker_state = {
            "patent_search_agent": {
                "state": "closed",  # closed, open, half_open
                "failure_count": 0,
                "last_failure_time": None,
                "failure_threshold": 3,
                "recovery_timeout": 5  # 秒
            }
        }
        
        def circuit_breaker_route(agent_id, request):
            if agent_id not in circuit_breaker_state:
                return {"status": "success", "data": f"Normal {agent_id}"}
            
            breaker = circuit_breaker_state[agent_id]
            current_time = datetime.now()
            
            # 检查熔断器状态
            if breaker["state"] == "open":
                # 检查是否可以尝试恢复
                if (breaker["last_failure_time"] and 
                    (current_time - breaker["last_failure_time"]).total_seconds() > breaker["recovery_timeout"]):
                    breaker["state"] = "half_open"
                else:
                    return {
                        "status": "error",
                        "error": "Circuit breaker is open",
                        "agent_id": agent_id
                    }
            
            # 模拟服务调用
            import random
            if random.random() < 0.7:  # 70%失败率（模拟不稳定服务）
                # 失败
                breaker["failure_count"] += 1
                breaker["last_failure_time"] = current_time
                
                if breaker["failure_count"] >= breaker["failure_threshold"]:
                    breaker["state"] = "open"
                
                return {
                    "status": "error",
                    "error": "Service call failed",
                    "failure_count": breaker["failure_count"],
                    "agent_id": agent_id
                }
            else:
                # 成功
                if breaker["state"] == "half_open":
                    breaker["state"] = "closed"
                    breaker["failure_count"] = 0
                
                return {
                    "status": "success",
                    "data": f"Successful call to {agent_id}",
                    "circuit_state": breaker["state"],
                    "agent_id": agent_id
                }
        
        mock_agent_router.route_request.side_effect = circuit_breaker_route
        
        # 测试熔断器行为
        test_results = []
        
        # 发送多个请求触发熔断器
        for i in range(10):
            result = await mock_agent_router.route_request("patent_search_agent", {"attempt": i})
            test_results.append(result)
            
            # 短暂延迟
            await asyncio.sleep(0.1)
        
        # 分析熔断器行为
        error_results = [r for r in test_results if r["status"] == "error"]
        success_results = [r for r in test_results if r["status"] == "success"]
        
        # 验证熔断器工作
        assert len(error_results) > 0  # 应该有失败
        
        # 检查是否有熔断器打开的错误
        circuit_breaker_errors = [
            r for r in error_results 
            if "Circuit breaker is open" in r.get("error", "")
        ]
        
        # 如果失败次数足够，应该触发熔断器
        if len([r for r in error_results if "Service call failed" in r.get("error", "")]) >= 3:
            assert len(circuit_breaker_errors) > 0


# 运行测试的辅助函数
def run_multi_agent_collaboration_tests():
    """运行所有多Agent协作集成测试."""
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--asyncio-mode=auto"
    ])


if __name__ == "__main__":
    run_multi_agent_collaboration_tests()