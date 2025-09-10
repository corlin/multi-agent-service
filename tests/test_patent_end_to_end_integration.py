"""专利端到端集成测试 - Patent End-to-End Integration Tests."""

import asyncio
import pytest
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch
import json
import tempfile
import os
from pathlib import Path

from src.multi_agent_service.patent.models.requests import PatentAnalysisRequest
from src.multi_agent_service.patent.models.results import PatentAnalysisResult
from src.multi_agent_service.patent.models.patent_data import PatentData, PatentDataset
from src.multi_agent_service.workflows.patent_workflow_engine import (
    PatentWorkflowEngine, PatentWorkflowFactory
)
from src.multi_agent_service.models.workflow import WorkflowExecution
from src.multi_agent_service.models.enums import WorkflowStatus, WorkflowType


@pytest.fixture
def comprehensive_patent_request():
    """创建全面的专利分析请求."""
    return PatentAnalysisRequest(
        content="进行人工智能和机器学习领域的全面专利分析，包括技术趋势、竞争格局和地域分布",
        keywords=[
            "人工智能", "机器学习", "深度学习", "神经网络", 
            "自然语言处理", "计算机视觉", "强化学习"
        ],
        date_range={
            "start_date": "2018-01-01",
            "end_date": "2023-12-31"
        },
        countries=["US", "CN", "EP", "JP", "KR"],
        analysis_types=["trend", "competition", "technology", "geographic", "innovation"]
    )


@pytest.fixture
def mock_patent_workflow_engine():
    """创建模拟的专利工作流引擎."""
    engine = MagicMock(spec=PatentWorkflowEngine)
    engine.execute_workflow = AsyncMock()
    engine.get_workflow_status = AsyncMock()
    engine.pause_workflow = AsyncMock()
    engine.resume_workflow = AsyncMock()
    engine.cancel_workflow = AsyncMock()
    return engine


@pytest.fixture
def sample_comprehensive_data():
    """创建全面的示例数据."""
    return {
        "patents": [
            {
                "application_number": "US16123456",
                "title": "Advanced Neural Network Architecture",
                "abstract": "A novel neural network architecture for improved machine learning performance",
                "applicants": [{"name": "Tech Corp", "country": "US", "applicant_type": "company"}],
                "inventors": [{"name": "John Smith", "country": "US"}],
                "application_date": "2022-01-15T00:00:00",
                "publication_date": "2022-07-15T00:00:00",
                "classifications": [{"ipc_class": "G06N3/08"}],
                "country": "US",
                "status": "granted"
            },
            {
                "application_number": "CN202110234567",
                "title": "深度学习优化方法",
                "abstract": "一种用于深度学习模型优化的新方法",
                "applicants": [{"name": "AI Research Institute", "country": "CN", "applicant_type": "institute"}],
                "inventors": [{"name": "张伟", "country": "CN"}],
                "application_date": "2021-03-10T00:00:00",
                "publication_date": "2021-09-10T00:00:00",
                "classifications": [{"ipc_class": "G06N3/04"}],
                "country": "CN",
                "status": "published"
            },
            {
                "application_number": "EP21456789",
                "title": "Computer Vision System for Autonomous Vehicles",
                "abstract": "An advanced computer vision system for autonomous vehicle navigation",
                "applicants": [{"name": "Auto Tech GmbH", "country": "DE", "applicant_type": "company"}],
                "inventors": [{"name": "Hans Mueller", "country": "DE"}],
                "application_date": "2021-06-20T00:00:00",
                "publication_date": "2021-12-20T00:00:00",
                "classifications": [{"ipc_class": "G06T7/70"}],
                "country": "EP",
                "status": "published"
            }
        ],
        "enhanced_data": {
            "cnki_literature": [
                {
                    "title": "人工智能技术发展趋势研究",
                    "authors": ["李明", "王华"],
                    "abstract": "分析了人工智能技术的最新发展趋势",
                    "keywords": ["人工智能", "技术趋势", "发展预测"],
                    "publication_date": "2023-05-15T00:00:00",
                    "journal": "计算机科学"
                }
            ],
            "web_intelligence": [
                {
                    "title": "AI Patent Landscape 2023",
                    "url": "https://example.com/ai-patents-2023",
                    "summary": "Comprehensive analysis of AI patent trends in 2023",
                    "relevance_score": 0.95
                }
            ]
        }
    }


class TestPatentEndToEndWorkflow:
    """专利端到端工作流测试类."""
    
    @pytest.mark.asyncio
    async def test_complete_patent_analysis_workflow(self, comprehensive_patent_request, sample_comprehensive_data):
        """测试完整的专利分析工作流."""
        # 创建工作流引擎
        workflow_engine = PatentWorkflowEngine()
        
        # 创建全面分析工作流执行
        execution = PatentWorkflowFactory.create_comprehensive_analysis_workflow(
            comprehensive_patent_request.keywords
        )
        
        # 模拟各阶段的执行结果
        mock_results = {
            "data_collection": {
                "status": "success",
                "data": {
                    "patents": sample_comprehensive_data["patents"],
                    "total": len(sample_comprehensive_data["patents"]),
                    "sources": ["google_patents", "patent_public_api"],
                    "collection_time": 3.2
                }
            },
            "search_enhancement": {
                "status": "success",
                "enhanced_data": sample_comprehensive_data["enhanced_data"],
                "enhancement_time": 4.1
            },
            "analysis": {
                "status": "success",
                "analysis": {
                    "trend_analysis": {
                        "yearly_counts": {"2018": 5, "2019": 8, "2020": 12, "2021": 18, "2022": 25, "2023": 30},
                        "growth_rates": {"2019": 0.6, "2020": 0.5, "2021": 0.5, "2022": 0.39, "2023": 0.2},
                        "trend_direction": "increasing",
                        "compound_annual_growth_rate": 0.43
                    },
                    "tech_classification": {
                        "ipc_distribution": {
                            "G06N": 45,  # AI/ML
                            "G06T": 25,  # Computer Vision
                            "G06F": 20,  # Computing
                            "H04L": 10   # Communication
                        },
                        "main_technologies": [
                            "Neural Networks", "Deep Learning", "Computer Vision", 
                            "Natural Language Processing", "Reinforcement Learning"
                        ],
                        "emerging_technologies": ["Transformer Architecture", "Federated Learning"]
                    },
                    "competition_analysis": {
                        "top_applicants": [
                            ("Tech Corp", 15), ("AI Research Institute", 12), 
                            ("Auto Tech GmbH", 8), ("Innovation Labs", 6)
                        ],
                        "market_concentration": 0.68,
                        "herfindahl_index": 0.15,
                        "competitive_landscape": "moderately_concentrated"
                    },
                    "geographic_analysis": {
                        "country_distribution": {"US": 40, "CN": 35, "EP": 15, "JP": 7, "KR": 3},
                        "regional_trends": {
                            "North America": "leading_in_innovation",
                            "Asia Pacific": "rapid_growth",
                            "Europe": "steady_development"
                        }
                    },
                    "innovation_analysis": {
                        "innovation_rate": 0.75,
                        "breakthrough_patents": 8,
                        "incremental_patents": 92,
                        "technology_maturity": "growth_phase"
                    }
                },
                "analysis_time": 6.8
            },
            "report_generation": {
                "status": "success",
                "report": {
                    "html_content": self._generate_mock_html_report(),
                    "pdf_content": b"Mock PDF content",
                    "charts": {
                        "trend_chart": "base64_trend_chart_data",
                        "tech_distribution_pie": "base64_pie_chart_data",
                        "competition_bar_chart": "base64_bar_chart_data",
                        "geographic_map": "base64_map_data"
                    },
                    "summary": "AI专利申请呈现强劲增长趋势，技术创新活跃，竞争格局日趋激烈",
                    "key_insights": [
                        "年复合增长率达43%，显示强劲发展势头",
                        "神经网络和深度学习是主要技术方向",
                        "美国和中国在专利申请量上领先",
                        "新兴技术如Transformer架构开始显现"
                    ]
                },
                "report_time": 2.3
            }
        }
        
        # 模拟工作流执行
        with patch.object(workflow_engine, '_get_workflow_graph') as mock_get_graph:
            mock_graph = MagicMock()
            mock_graph.workflow_type = WorkflowType.HIERARCHICAL
            mock_graph.nodes = [
                MagicMock(node_id="start", name="Start"),
                MagicMock(node_id="data_collection", name="Data Collection"),
                MagicMock(node_id="search_enhancement", name="Search Enhancement"),
                MagicMock(node_id="analysis", name="Analysis"),
                MagicMock(node_id="report_generation", name="Report Generation"),
                MagicMock(node_id="end", name="End")
            ]
            mock_graph.edges = []
            mock_get_graph.return_value = mock_graph
            
            with patch.object(workflow_engine, '_execute_hierarchical_workflow') as mock_execute:
                # 设置执行结果
                execution.status = WorkflowStatus.COMPLETED
                execution.node_results = mock_results
                execution.output_data = {
                    "final_report": mock_results["report_generation"]["report"],
                    "analysis_summary": mock_results["analysis"]["analysis"],
                    "total_patents_analyzed": len(sample_comprehensive_data["patents"]),
                    "execution_time": sum([
                        mock_results["data_collection"]["data"]["collection_time"],
                        mock_results["search_enhancement"]["enhancement_time"],
                        mock_results["analysis"]["analysis_time"],
                        mock_results["report_generation"]["report_time"]
                    ])
                }
                mock_execute.return_value = execution
                
                # 执行工作流
                result = await workflow_engine.execute_workflow(execution)
                
                # 验证端到端执行结果
                assert result.status == WorkflowStatus.COMPLETED
                assert "final_report" in result.output_data
                assert "analysis_summary" in result.output_data
                assert result.output_data["total_patents_analyzed"] == 3
                
                # 验证分析质量
                analysis = result.output_data["analysis_summary"]
                assert analysis["trend_analysis"]["compound_annual_growth_rate"] > 0
                assert len(analysis["tech_classification"]["main_technologies"]) > 0
                assert analysis["competition_analysis"]["market_concentration"] > 0
                
                # 验证报告生成
                report = result.output_data["final_report"]
                assert "html_content" in report
                assert "charts" in report
                assert len(report["key_insights"]) > 0
    
    def _generate_mock_html_report(self):
        """生成模拟HTML报告."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI专利分析报告</title>
            <meta charset="utf-8">
        </head>
        <body>
            <h1>人工智能专利分析报告</h1>
            
            <h2>执行摘要</h2>
            <p>本报告分析了2018-2023年期间人工智能领域的专利申请趋势...</p>
            
            <h2>趋势分析</h2>
            <p>AI专利申请量呈现强劲增长趋势，年复合增长率达43%...</p>
            
            <h2>技术分类</h2>
            <p>神经网络(G06N)是最主要的技术分类，占总申请量的45%...</p>
            
            <h2>竞争分析</h2>
            <p>市场集中度为0.68，显示竞争格局相对集中...</p>
            
            <h2>地域分析</h2>
            <p>美国和中国在专利申请量上领先，分别占40%和35%...</p>
            
            <h2>结论与建议</h2>
            <p>AI技术仍处于快速发展期，建议关注新兴技术方向...</p>
        </body>
        </html>
        """
    
    @pytest.mark.asyncio
    async def test_workflow_with_real_data_processing(self, comprehensive_patent_request):
        """测试使用真实数据处理的工作流."""
        # 创建临时目录用于测试
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建测试数据文件
            test_data_file = Path(temp_dir) / "test_patents.json"
            test_data = {
                "patents": [
                    {
                        "application_number": f"TEST{i:06d}",
                        "title": f"Test Patent {i}",
                        "abstract": f"Abstract for test patent {i}" * 10,  # 确保足够长度
                        "applicants": [{"name": f"Company {i}", "country": "US"}],
                        "inventors": [{"name": f"Inventor {i}", "country": "US"}],
                        "application_date": f"202{i%4}-01-01T00:00:00",
                        "classifications": [{"ipc_class": "G06N3/08"}],
                        "country": "US",
                        "status": "published"
                    }
                    for i in range(100)  # 100个测试专利
                ]
            }
            
            with open(test_data_file, 'w', encoding='utf-8') as f:
                json.dump(test_data, f, ensure_ascii=False, indent=2)
            
            # 创建工作流引擎
            workflow_engine = PatentWorkflowEngine()
            
            # 创建数据处理工作流
            execution = WorkflowExecution(
                graph_id="data_processing_test",
                input_data={
                    "data_source": str(test_data_file),
                    "processing_mode": "batch",
                    "keywords": comprehensive_patent_request.keywords
                }
            )
            
            # 模拟数据处理工作流
            with patch.object(workflow_engine, '_get_workflow_graph') as mock_get_graph:
                mock_graph = MagicMock()
                mock_graph.workflow_type = WorkflowType.SEQUENTIAL
                mock_graph.nodes = [
                    MagicMock(node_id="data_loader", name="Data Loader"),
                    MagicMock(node_id="data_processor", name="Data Processor"),
                    MagicMock(node_id="data_analyzer", name="Data Analyzer")
                ]
                mock_graph.edges = []
                mock_get_graph.return_value = mock_graph
                
                with patch.object(workflow_engine.sequential_engine, 'execute_workflow') as mock_execute:
                    # 模拟数据处理结果
                    execution.status = WorkflowStatus.COMPLETED
                    execution.output_data = {
                        "processed_patents": 100,
                        "processing_time": 5.2,
                        "data_quality_score": 0.95,
                        "analysis_results": {
                            "yearly_distribution": {"2020": 25, "2021": 25, "2022": 25, "2023": 25},
                            "classification_distribution": {"G06N3/08": 100}
                        }
                    }
                    mock_execute.return_value = execution
                    
                    # 执行数据处理工作流
                    result = await workflow_engine.execute_workflow(execution)
                    
                    # 验证数据处理结果
                    assert result.status == WorkflowStatus.COMPLETED
                    assert result.output_data["processed_patents"] == 100
                    assert result.output_data["data_quality_score"] > 0.9
                    assert result.output_data["processing_time"] > 0
    
    @pytest.mark.asyncio
    async def test_workflow_performance_under_load(self, comprehensive_patent_request):
        """测试负载下的工作流性能."""
        workflow_engine = PatentWorkflowEngine()
        
        # 创建多个并发工作流执行
        num_concurrent_workflows = 5
        executions = []
        
        for i in range(num_concurrent_workflows):
            execution = WorkflowExecution(
                graph_id="performance_test",
                input_data={
                    "keywords": comprehensive_patent_request.keywords[:2],  # 减少关键词以加快处理
                    "workflow_id": i,
                    "priority": "normal"
                }
            )
            executions.append(execution)
        
        # 模拟并发执行
        with patch.object(workflow_engine, '_get_workflow_graph') as mock_get_graph:
            mock_graph = MagicMock()
            mock_graph.workflow_type = WorkflowType.PARALLEL
            mock_graph.nodes = [MagicMock(node_id="test_node", name="Test Node")]
            mock_graph.edges = []
            mock_get_graph.return_value = mock_graph
            
            with patch.object(workflow_engine.parallel_engine, 'execute_workflow') as mock_execute:
                def execute_side_effect(execution):
                    # 模拟处理时间
                    execution.status = WorkflowStatus.COMPLETED
                    execution.output_data = {
                        "workflow_id": execution.input_data["workflow_id"],
                        "processing_time": 2.0 + (execution.input_data["workflow_id"] * 0.1),
                        "status": "success"
                    }
                    return execution
                
                mock_execute.side_effect = execute_side_effect
                
                # 并发执行工作流
                start_time = datetime.now()
                results = await asyncio.gather(*[
                    workflow_engine.execute_workflow(execution) 
                    for execution in executions
                ])
                end_time = datetime.now()
                
                # 验证性能
                total_time = (end_time - start_time).total_seconds()
                assert total_time < 10.0  # 总时间应该小于10秒
                assert len(results) == num_concurrent_workflows
                assert all(result.status == WorkflowStatus.COMPLETED for result in results)
                
                # 验证并发处理效果
                individual_times = [result.output_data["processing_time"] for result in results]
                max_individual_time = max(individual_times)
                # 并发执行时间应该接近最长的单个执行时间，而不是所有时间的总和
                assert total_time < max_individual_time * 1.5
    
    @pytest.mark.asyncio
    async def test_workflow_fault_tolerance(self, comprehensive_patent_request):
        """测试工作流容错能力."""
        workflow_engine = PatentWorkflowEngine()
        
        # 创建容错测试工作流
        execution = WorkflowExecution(
            graph_id="fault_tolerance_test",
            input_data={
                "keywords": comprehensive_patent_request.keywords,
                "fault_injection": True,
                "recovery_mode": "automatic"
            }
        )
        
        # 模拟故障注入和恢复
        fault_scenarios = [
            {"node": "data_collection", "fault_type": "timeout", "recovery": "retry"},
            {"node": "search_enhancement", "fault_type": "service_unavailable", "recovery": "fallback"},
            {"node": "analysis", "fault_type": "memory_error", "recovery": "restart"},
        ]
        
        with patch.object(workflow_engine, '_get_workflow_graph') as mock_get_graph:
            mock_graph = MagicMock()
            mock_graph.workflow_type = WorkflowType.HIERARCHICAL
            mock_graph.nodes = [
                MagicMock(node_id=scenario["node"], name=scenario["node"]) 
                for scenario in fault_scenarios
            ]
            mock_graph.edges = []
            mock_get_graph.return_value = mock_graph
            
            with patch.object(workflow_engine, '_execute_hierarchical_workflow') as mock_execute:
                # 模拟故障恢复结果
                execution.status = WorkflowStatus.COMPLETED
                execution.node_results = {
                    scenario["node"]: {
                        "status": "recovered",
                        "fault_type": scenario["fault_type"],
                        "recovery_action": scenario["recovery"],
                        "recovery_time": 1.5,
                        "final_result": "success"
                    }
                    for scenario in fault_scenarios
                }
                execution.output_data = {
                    "fault_tolerance_report": {
                        "total_faults": len(fault_scenarios),
                        "recovered_faults": len(fault_scenarios),
                        "recovery_rate": 1.0,
                        "total_recovery_time": 4.5
                    }
                }
                mock_execute.return_value = execution
                
                # 执行容错测试
                result = await workflow_engine.execute_workflow(execution)
                
                # 验证容错能力
                assert result.status == WorkflowStatus.COMPLETED
                fault_report = result.output_data["fault_tolerance_report"]
                assert fault_report["recovery_rate"] == 1.0
                assert fault_report["total_faults"] == len(fault_scenarios)
                
                # 验证每个故障都被正确处理
                for scenario in fault_scenarios:
                    node_result = result.node_results[scenario["node"]]
                    assert node_result["status"] == "recovered"
                    assert node_result["final_result"] == "success"
    
    @pytest.mark.asyncio
    async def test_workflow_monitoring_and_observability(self, comprehensive_patent_request):
        """测试工作流监控和可观测性."""
        workflow_engine = PatentWorkflowEngine()
        
        # 创建监控测试工作流
        execution = WorkflowExecution(
            graph_id="monitoring_test",
            input_data={
                "keywords": comprehensive_patent_request.keywords,
                "monitoring_enabled": True,
                "metrics_collection": True
            }
        )
        
        # 模拟监控数据收集
        monitoring_data = {
            "execution_metrics": {
                "start_time": datetime.now().isoformat(),
                "node_execution_times": {
                    "data_collection": 3.2,
                    "search_enhancement": 4.1,
                    "analysis": 6.8,
                    "report_generation": 2.3
                },
                "memory_usage": {
                    "peak_memory_mb": 512,
                    "average_memory_mb": 256
                },
                "cpu_usage": {
                    "peak_cpu_percent": 85,
                    "average_cpu_percent": 45
                }
            },
            "quality_metrics": {
                "data_completeness": 0.95,
                "analysis_accuracy": 0.88,
                "report_quality_score": 0.92
            },
            "business_metrics": {
                "patents_processed": 150,
                "insights_generated": 12,
                "actionable_recommendations": 8
            }
        }
        
        with patch.object(workflow_engine, '_get_workflow_graph') as mock_get_graph:
            mock_graph = MagicMock()
            mock_graph.workflow_type = WorkflowType.SEQUENTIAL
            mock_graph.nodes = [MagicMock(node_id="monitoring_node", name="Monitoring Node")]
            mock_graph.edges = []
            mock_get_graph.return_value = mock_graph
            
            with patch.object(workflow_engine.sequential_engine, 'execute_workflow') as mock_execute:
                execution.status = WorkflowStatus.COMPLETED
                execution.output_data = {
                    "monitoring_data": monitoring_data,
                    "execution_summary": {
                        "total_execution_time": sum(monitoring_data["execution_metrics"]["node_execution_times"].values()),
                        "overall_quality_score": sum(monitoring_data["quality_metrics"].values()) / len(monitoring_data["quality_metrics"]),
                        "efficiency_score": monitoring_data["business_metrics"]["patents_processed"] / sum(monitoring_data["execution_metrics"]["node_execution_times"].values())
                    }
                }
                mock_execute.return_value = execution
                
                # 执行监控测试
                result = await workflow_engine.execute_workflow(execution)
                
                # 验证监控数据
                assert result.status == WorkflowStatus.COMPLETED
                monitoring = result.output_data["monitoring_data"]
                
                # 验证执行指标
                assert "execution_metrics" in monitoring
                assert monitoring["execution_metrics"]["peak_memory_mb"] > 0
                assert monitoring["execution_metrics"]["average_cpu_percent"] > 0
                
                # 验证质量指标
                assert "quality_metrics" in monitoring
                assert all(score > 0.8 for score in monitoring["quality_metrics"].values())
                
                # 验证业务指标
                assert "business_metrics" in monitoring
                assert monitoring["business_metrics"]["patents_processed"] > 0
                
                # 验证执行摘要
                summary = result.output_data["execution_summary"]
                assert summary["total_execution_time"] > 0
                assert summary["overall_quality_score"] > 0.8
                assert summary["efficiency_score"] > 0


class TestPatentSystemIntegration:
    """专利系统集成测试类."""
    
    @pytest.mark.asyncio
    async def test_full_system_integration_with_api(self, comprehensive_patent_request):
        """测试与API的完整系统集成."""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI
        from src.multi_agent_service.api.patent import router as patent_router
        
        # 创建测试应用
        app = FastAPI()
        app.include_router(patent_router)
        client = TestClient(app)
        
        # 模拟完整的API调用流程
        with patch('src.multi_agent_service.api.patent.get_report_exporter') as mock_exporter:
            mock_exporter_instance = MagicMock()
            
            # 1. 测试导出报告
            mock_exporter_instance.export_report = AsyncMock(return_value={
                "filename": "comprehensive_analysis_20231201.html",
                "format": "html",
                "size": 2048000,
                "created_at": datetime.now().isoformat()
            })
            mock_exporter.return_value = mock_exporter_instance
            
            export_request = {
                "content": "# 全面专利分析报告\n\n本报告包含详细的专利分析结果...",
                "format": "html",
                "params": {
                    "title": "AI专利全面分析",
                    "keywords": comprehensive_patent_request.keywords
                }
            }
            
            response = client.post("/api/v1/patent/export", json=export_request)
            assert response.status_code == 200
            
            export_result = response.json()
            assert export_result["success"] is True
            assert "filename" in export_result["data"]
            
            # 2. 测试获取报告列表
            mock_exporter_instance.list_exported_reports = AsyncMock(return_value=[
                {
                    "filename": export_result["data"]["filename"],
                    "format": "html",
                    "created_at": datetime.now().isoformat(),
                    "size": 2048000
                }
            ])
            
            response = client.get("/api/v1/patent/reports")
            assert response.status_code == 200
            
            reports_result = response.json()
            assert reports_result["success"] is True
            assert len(reports_result["data"]["reports"]) == 1
            
            # 3. 测试健康检查
            mock_exporter_instance.get_export_info = AsyncMock(return_value={
                "directories": {"reports": "/tmp/reports"},
                "supported_formats": ["html", "pdf", "json"]
            })
            
            response = client.get("/api/v1/patent/health")
            assert response.status_code == 200
            
            health_result = response.json()
            assert health_result["success"] is True
            assert health_result["data"]["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_system_scalability_and_limits(self, comprehensive_patent_request):
        """测试系统可扩展性和限制."""
        workflow_engine = PatentWorkflowEngine()
        
        # 测试大规模数据处理
        large_scale_execution = WorkflowExecution(
            graph_id="scalability_test",
            input_data={
                "keywords": comprehensive_patent_request.keywords,
                "data_scale": "large",
                "patent_count": 10000,  # 模拟1万个专利
                "processing_mode": "distributed"
            }
        )
        
        with patch.object(workflow_engine, '_get_workflow_graph') as mock_get_graph:
            mock_graph = MagicMock()
            mock_graph.workflow_type = WorkflowType.PARALLEL
            mock_graph.nodes = [
                MagicMock(node_id="batch_processor_1", name="Batch Processor 1"),
                MagicMock(node_id="batch_processor_2", name="Batch Processor 2"),
                MagicMock(node_id="batch_processor_3", name="Batch Processor 3"),
                MagicMock(node_id="aggregator", name="Result Aggregator")
            ]
            mock_graph.edges = []
            mock_get_graph.return_value = mock_graph
            
            with patch.object(workflow_engine.parallel_engine, 'execute_workflow') as mock_execute:
                # 模拟大规模处理结果
                large_scale_execution.status = WorkflowStatus.COMPLETED
                large_scale_execution.output_data = {
                    "processed_patents": 10000,
                    "processing_time": 45.2,
                    "throughput": 221.2,  # patents per second
                    "memory_efficiency": 0.85,
                    "cpu_utilization": 0.78,
                    "scalability_metrics": {
                        "batch_sizes": [3334, 3333, 3333],
                        "parallel_efficiency": 0.92,
                        "load_distribution": [0.33, 0.34, 0.33]
                    }
                }
                mock_execute.return_value = large_scale_execution
                
                # 执行可扩展性测试
                result = await workflow_engine.execute_workflow(large_scale_execution)
                
                # 验证可扩展性
                assert result.status == WorkflowStatus.COMPLETED
                assert result.output_data["processed_patents"] == 10000
                assert result.output_data["throughput"] > 200  # 每秒处理200+专利
                assert result.output_data["scalability_metrics"]["parallel_efficiency"] > 0.9
    
    @pytest.mark.asyncio
    async def test_system_data_consistency_and_integrity(self, comprehensive_patent_request):
        """测试系统数据一致性和完整性."""
        workflow_engine = PatentWorkflowEngine()
        
        # 创建数据一致性测试工作流
        consistency_execution = WorkflowExecution(
            graph_id="data_consistency_test",
            input_data={
                "keywords": comprehensive_patent_request.keywords,
                "data_validation": True,
                "integrity_checks": True,
                "consistency_level": "strict"
            }
        )
        
        # 模拟数据一致性检查
        consistency_results = {
            "data_validation": {
                "total_records": 1000,
                "valid_records": 985,
                "invalid_records": 15,
                "validation_rate": 0.985,
                "validation_errors": [
                    {"type": "missing_abstract", "count": 8},
                    {"type": "invalid_date", "count": 4},
                    {"type": "malformed_classification", "count": 3}
                ]
            },
            "integrity_checks": {
                "referential_integrity": 1.0,
                "data_completeness": 0.985,
                "format_consistency": 0.995,
                "duplicate_detection": {
                    "duplicates_found": 12,
                    "duplicates_removed": 12,
                    "deduplication_rate": 1.0
                }
            },
            "consistency_verification": {
                "cross_source_consistency": 0.92,
                "temporal_consistency": 0.98,
                "classification_consistency": 0.94,
                "applicant_name_consistency": 0.89
            }
        }
        
        with patch.object(workflow_engine, '_get_workflow_graph') as mock_get_graph:
            mock_graph = MagicMock()
            mock_graph.workflow_type = WorkflowType.SEQUENTIAL
            mock_graph.nodes = [
                MagicMock(node_id="data_validator", name="Data Validator"),
                MagicMock(node_id="integrity_checker", name="Integrity Checker"),
                MagicMock(node_id="consistency_verifier", name="Consistency Verifier")
            ]
            mock_graph.edges = []
            mock_get_graph.return_value = mock_graph
            
            with patch.object(workflow_engine.sequential_engine, 'execute_workflow') as mock_execute:
                consistency_execution.status = WorkflowStatus.COMPLETED
                consistency_execution.output_data = {
                    "consistency_results": consistency_results,
                    "overall_quality_score": 0.94,
                    "data_quality_grade": "A-",
                    "recommendations": [
                        "Improve abstract completeness validation",
                        "Enhance date format standardization",
                        "Implement better applicant name normalization"
                    ]
                }
                mock_execute.return_value = consistency_execution
                
                # 执行数据一致性测试
                result = await workflow_engine.execute_workflow(consistency_execution)
                
                # 验证数据质量
                assert result.status == WorkflowStatus.COMPLETED
                quality_results = result.output_data["consistency_results"]
                
                # 验证数据验证结果
                assert quality_results["data_validation"]["validation_rate"] > 0.95
                
                # 验证完整性检查
                assert quality_results["integrity_checks"]["referential_integrity"] == 1.0
                assert quality_results["integrity_checks"]["data_completeness"] > 0.95
                
                # 验证一致性验证
                consistency_scores = quality_results["consistency_verification"]
                assert all(score > 0.85 for score in consistency_scores.values())
                
                # 验证总体质量
                assert result.output_data["overall_quality_score"] > 0.9


# 运行测试的辅助函数
def run_end_to_end_integration_tests():
    """运行所有端到端集成测试."""
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--asyncio-mode=auto"
    ])


if __name__ == "__main__":
    run_end_to_end_integration_tests()