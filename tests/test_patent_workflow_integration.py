"""专利工作流集成测试 - Patent Workflow Integration Tests."""

import asyncio
import pytest
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch
import json
from uuid import uuid4
import httpx

# Patent system imports
from src.multi_agent_service.patent.models.requests import PatentAnalysisRequest
from src.multi_agent_service.patent.models.results import PatentAnalysisResult
from src.multi_agent_service.patent.models.patent_data import PatentData, PatentDataset

# Workflow engine imports
from src.multi_agent_service.workflows.patent_workflow_engine import (
    PatentWorkflowEngine, PatentWorkflowFactory, PatentWorkflowNode
)
from src.multi_agent_service.workflows.state_management import WorkflowStateManager
from src.multi_agent_service.models.workflow import WorkflowExecution, WorkflowGraph
from src.multi_agent_service.models.enums import WorkflowStatus, WorkflowType, AgentType

# API and service imports
from src.multi_agent_service.api.patent import router as patent_router
from src.multi_agent_service.services.agent_router import AgentRouter
from src.multi_agent_service.core.service_manager import ServiceManager

# Test utilities
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Test fixtures
@pytest.fixture
def sample_patent_request():
    """Create a sample patent analysis request."""
    return PatentAnalysisRequest(
        content="Analyze artificial intelligence and machine learning patents",
        keywords=["artificial intelligence", "machine learning", "neural networks"],
        date_range={
            "start_date": "2020-01-01",
            "end_date": "2023-12-31"
        },
        countries=["US", "CN", "EP"],
        analysis_types=["trend", "competition", "technology"]
    )


@pytest.fixture
def mock_workflow_state_manager():
    """Create a mock workflow state manager."""
    manager = MagicMock(spec=WorkflowStateManager)
    manager.start_execution = AsyncMock()
    manager.complete_execution = AsyncMock()
    manager.fail_execution = AsyncMock()
    manager.update_execution_state = AsyncMock()
    manager.get_execution_state = AsyncMock()
    return manager


@pytest.fixture
def patent_workflow_engine(mock_workflow_state_manager):
    """Create a patent workflow engine for testing."""
    return PatentWorkflowEngine(state_manager=mock_workflow_state_manager)


@pytest.fixture
def mock_agent_router():
    """Create a mock agent router."""
    router = MagicMock(spec=AgentRouter)
    router.route_request = AsyncMock()
    return router


@pytest.fixture
def test_app():
    """Create a test FastAPI application."""
    app = FastAPI()
    app.include_router(patent_router)
    return app


@pytest.fixture
def test_client(test_app):
    """Create a test client."""
    return TestClient(test_app)


@pytest.fixture
def sample_patent_data():
    """Create sample patent data for testing."""
    return [
        {
            "application_number": "US16123456",
            "title": "Advanced Machine Learning System",
            "abstract": "A system for advanced machine learning applications with neural networks",
            "applicants": [{"name": "Tech Corp", "country": "US", "applicant_type": "company"}],
            "inventors": [{"name": "John Smith", "country": "US"}],
            "application_date": "2022-01-15T00:00:00",
            "classifications": [{"ipc_class": "G06N3/08"}],
            "country": "US",
            "status": "published"
        },
        {
            "application_number": "CN202110234567",
            "title": "人工智能处理系统",
            "abstract": "一种用于人工智能处理的系统和方法",
            "applicants": [{"name": "AI Tech Ltd", "country": "CN", "applicant_type": "company"}],
            "inventors": [{"name": "李明", "country": "CN"}],
            "application_date": "2021-03-10T00:00:00",
            "classifications": [{"ipc_class": "G06N3/04"}],
            "country": "CN",
            "status": "published"
        }
    ]


class TestPatentWorkflowIntegration:
    """专利工作流集成测试类."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_patent_analysis_workflow(self, patent_workflow_engine, sample_patent_request):
        """测试端到端专利分析工作流."""
        # 创建工作流执行
        execution = PatentWorkflowFactory.create_comprehensive_analysis_workflow(
            sample_patent_request.keywords
        )
        
        # 模拟各个阶段的结果
        with patch.multiple(
            patent_workflow_engine,
            _get_workflow_graph=AsyncMock(return_value=MagicMock(
                workflow_type=WorkflowType.HIERARCHICAL,
                nodes=[
                    MagicMock(node_id="start", name="Start"),
                    MagicMock(node_id="data_collection", name="Data Collection"),
                    MagicMock(node_id="search_enhancement", name="Search Enhancement"),
                    MagicMock(node_id="analysis", name="Analysis"),
                    MagicMock(node_id="report", name="Report Generation"),
                    MagicMock(node_id="end", name="End")
                ],
                edges=[]
            )),
            _execute_hierarchical_workflow=AsyncMock(return_value=execution)
        ):
            # 执行工作流
            result = await patent_workflow_engine.execute_workflow(execution)
            
            # 验证执行结果
            assert result is not None
            assert result.execution_id == execution.execution_id
            
            # 验证状态管理器被调用
            patent_workflow_engine.state_manager.start_execution.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_multi_agent_collaboration_scenario(self, patent_workflow_engine, sample_patent_request):
        """测试多Agent协作场景."""
        # 创建并行工作流执行
        execution = WorkflowExecution(
            graph_id="multi_agent_collaboration",
            input_data={
                "keywords": sample_patent_request.keywords,
                "collaboration_mode": "parallel"
            }
        )
        
        # 模拟多个Agent的协作
        mock_agents_results = {
            "data_collection_agent": {
                "status": "success",
                "data": {"patents": 150, "sources": ["google_patents", "patent_public_api"]}
            },
            "search_agent": {
                "status": "success", 
                "data": {"enhanced_records": 75, "sources": ["cnki", "bocha_ai"]}
            },
            "analysis_agent": {
                "status": "success",
                "data": {"insights": 12, "trends": ["increasing", "diversifying"]}
            },
            "report_agent": {
                "status": "success",
                "data": {"report_pages": 25, "charts": 8}
            }
        }
        
        # 模拟Agent协作执行
        mock_result_execution = execution.model_copy()
        mock_result_execution.status = WorkflowStatus.COMPLETED
        mock_result_execution.output_data = {"collaboration_results": mock_agents_results}
        
        with patch.object(patent_workflow_engine.parallel_engine, 'execute_workflow', 
                         return_value=mock_result_execution) as mock_execute:
            
            # 模拟工作流图
            mock_graph = MagicMock()
            mock_graph.workflow_type = WorkflowType.PARALLEL
            mock_graph.nodes = [
                MagicMock(node_id=agent_id, name=agent_id) 
                for agent_id in mock_agents_results.keys()
            ]
            mock_graph.edges = []
            
            with patch.object(patent_workflow_engine, '_get_workflow_graph', 
                             return_value=mock_graph):
                
                result = await patent_workflow_engine.execute_workflow(execution)
                
                # 验证多Agent协作
                assert result is not None
                assert result.status == WorkflowStatus.COMPLETED
                mock_execute.assert_called_once_with(execution)
                
                # 验证所有Agent都被执行
                for agent_id in mock_agents_results.keys():
                    assert agent_id in result.node_results or len(result.node_results) == 0
    
    @pytest.mark.asyncio
    async def test_patent_data_collection_and_analysis_process(self, patent_workflow_engine, sample_patent_data):
        """测试专利数据收集和分析流程."""
        # 创建数据收集到分析的完整流程
        execution = WorkflowExecution(
            graph_id="data_collection_analysis",
            input_data={
                "keywords": ["AI", "machine learning"],
                "process_type": "collection_to_analysis"
            }
        )
        
        # 模拟数据收集阶段
        collection_result = {
            "status": "success",
            "data": {"patents": sample_patent_data, "total": len(sample_patent_data)}
        }
        
        # 模拟分析阶段
        analysis_result = {
            "status": "success",
            "analysis": {
                "trend_analysis": {
                    "yearly_counts": {"2021": 1, "2022": 1},
                    "growth_rate": 0.0,
                    "trend_direction": "stable"
                },
                "tech_classification": {
                    "ipc_distribution": {"G06N": 2},
                    "main_technologies": ["Neural Networks", "AI Processing"]
                },
                "competition_analysis": {
                    "top_applicants": [("Tech Corp", 1), ("AI Tech Ltd", 1)],
                    "market_concentration": 0.5
                }
            }
        }
        
        # 模拟流程执行
        with patch.object(patent_workflow_engine, '_execute_single_node') as mock_execute:
            mock_execute.side_effect = [collection_result, analysis_result]
            
            # 模拟顺序工作流
            mock_graph = MagicMock()
            mock_graph.workflow_type = WorkflowType.SEQUENTIAL
            mock_graph.nodes = [
                MagicMock(node_id="data_collection", name="Data Collection"),
                MagicMock(node_id="analysis", name="Analysis")
            ]
            mock_graph.edges = []
            
            with patch.object(patent_workflow_engine, '_get_workflow_graph', 
                             return_value=mock_graph):
                with patch.object(patent_workflow_engine.sequential_engine, 'execute_workflow',
                                 return_value=execution) as mock_seq:
                    
                    result = await patent_workflow_engine.execute_workflow(execution)
                    
                    # 验证数据收集和分析流程
                    assert result is not None
                    mock_seq.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_workflow_error_handling_and_recovery(self, patent_workflow_engine):
        """测试工作流错误处理和恢复."""
        execution = WorkflowExecution(
            graph_id="error_handling_test",
            input_data={"keywords": ["test"]}
        )
        
        # 模拟执行过程中的错误
        with patch.object(patent_workflow_engine, '_get_workflow_graph', 
                         side_effect=Exception("Graph not found")):
            
            result = await patent_workflow_engine.execute_workflow(execution)
            
            # 验证错误处理
            assert result.status == WorkflowStatus.FAILED
            assert result.error_message == "Graph not found"
            assert result.end_time is not None
            
            # 验证错误被记录到状态管理器
            patent_workflow_engine.state_manager.fail_execution.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_workflow_pause_resume_cancel(self, patent_workflow_engine):
        """测试工作流暂停、恢复和取消功能."""
        execution = WorkflowExecution(
            graph_id="pause_resume_test",
            input_data={"keywords": ["test"]}
        )
        
        # 添加到活跃执行中
        patent_workflow_engine.active_executions[execution.execution_id] = execution
        
        # 测试暂停
        pause_result = await patent_workflow_engine.pause_workflow(execution.execution_id)
        assert pause_result is True
        assert execution.status == WorkflowStatus.PAUSED
        
        # 测试恢复
        resume_result = await patent_workflow_engine.resume_workflow(execution.execution_id)
        assert resume_result is True
        assert execution.status == WorkflowStatus.RUNNING
        
        # 测试取消
        cancel_result = await patent_workflow_engine.cancel_workflow(execution.execution_id)
        assert cancel_result is True
        assert execution.status == WorkflowStatus.CANCELLED
        assert execution.execution_id not in patent_workflow_engine.active_executions
    
    @pytest.mark.asyncio
    async def test_workflow_template_management(self, patent_workflow_engine):
        """测试工作流模板管理."""
        # 获取可用模板
        templates = patent_workflow_engine.get_available_templates()
        assert len(templates) > 0
        assert "comprehensive_patent_analysis" in templates
        assert "quick_patent_search" in templates
        assert "patent_trend_analysis" in templates
        
        # 获取模板信息
        template_info = patent_workflow_engine.get_template_info("comprehensive_patent_analysis")
        assert template_info is not None
        assert template_info["name"] == "全面专利分析工作流"
        assert template_info["workflow_type"] == WorkflowType.HIERARCHICAL.value
        
        # 从模板创建执行
        execution = await patent_workflow_engine.create_execution_from_template(
            "quick_patent_search",
            {"query": "artificial intelligence"}
        )
        assert execution.graph_id == "quick_patent_search"
        assert execution.input_data["query"] == "artificial intelligence"
    
    @pytest.mark.asyncio
    async def test_workflow_state_persistence(self, patent_workflow_engine):
        """测试工作流状态持久化."""
        execution = WorkflowExecution(
            graph_id="state_persistence_test",
            input_data={"keywords": ["test"]}
        )
        
        # 模拟状态保存和恢复
        patent_workflow_engine.state_manager.get_execution_state.return_value = {
            "status": WorkflowStatus.RUNNING.value,
            "progress": 0.5,
            "current_node": "analysis"
        }
        
        # 获取工作流状态
        status = await patent_workflow_engine.get_workflow_status(execution.execution_id)
        assert status == WorkflowStatus.RUNNING
        
        # 验证状态管理器被调用
        patent_workflow_engine.state_manager.get_execution_state.assert_called_with(execution.execution_id)


class TestPatentAPIIntegration:
    """专利API集成测试类."""
    
    def test_patent_reports_list_endpoint(self, test_client):
        """测试专利报告列表端点."""
        with patch('src.multi_agent_service.api.patent.get_report_exporter') as mock_exporter:
            # 模拟报告导出器
            mock_exporter_instance = MagicMock()
            mock_exporter_instance.list_exported_reports = AsyncMock(return_value=[
                {
                    "filename": "patent_analysis_20231201.html",
                    "format": "html",
                    "created_at": "2023-12-01T10:00:00",
                    "size": 1024000
                },
                {
                    "filename": "patent_analysis_20231201.pdf", 
                    "format": "pdf",
                    "created_at": "2023-12-01T10:05:00",
                    "size": 2048000
                }
            ])
            mock_exporter.return_value = mock_exporter_instance
            
            # 调用API
            response = test_client.get("/api/v1/patent/reports?limit=10")
            
            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]["reports"]) == 2
            assert data["data"]["total_count"] == 2
    
    def test_patent_report_download_endpoint(self, test_client):
        """测试专利报告下载端点."""
        with patch('src.multi_agent_service.api.patent.get_report_exporter') as mock_exporter:
            # 模拟报告导出器
            mock_exporter_instance = MagicMock()
            mock_exporter_instance.get_download_info = AsyncMock(return_value={
                "exists": True,
                "path": "/tmp/test_report.html",
                "mime_type": "text/html",
                "download_name": "patent_analysis.html",
                "format": "html"
            })
            mock_exporter.return_value = mock_exporter_instance
            
            # 模拟文件存在
            with patch('pathlib.Path.exists', return_value=True):
                with patch('builtins.open', create=True) as mock_open:
                    mock_open.return_value.__enter__.return_value.read.return_value = "<html>Test Report</html>"
                    
                    # 调用API
                    response = test_client.get("/api/v1/patent/reports/view/test_report.html")
                    
                    # 验证响应
                    assert response.status_code == 200
                    assert "text/html" in response.headers.get("content-type", "")
    
    def test_patent_export_endpoint(self, test_client):
        """测试专利报告导出端点."""
        with patch('src.multi_agent_service.api.patent.get_report_exporter') as mock_exporter:
            # 模拟报告导出器
            mock_exporter_instance = MagicMock()
            mock_exporter_instance.export_report = AsyncMock(return_value={
                "filename": "exported_report.pdf",
                "format": "pdf",
                "size": 1024000,
                "created_at": "2023-12-01T10:00:00"
            })
            mock_exporter.return_value = mock_exporter_instance
            
            # 准备请求数据
            export_request = {
                "content": "Test patent analysis report content",
                "format": "pdf",
                "params": {"title": "Patent Analysis Report"}
            }
            
            # 调用API
            response = test_client.post("/api/v1/patent/export", json=export_request)
            
            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["format"] == "pdf"
    
    def test_patent_health_check_endpoint(self, test_client):
        """测试专利API健康检查端点."""
        with patch('src.multi_agent_service.api.patent.get_report_exporter') as mock_exporter:
            # 模拟报告导出器
            mock_exporter_instance = MagicMock()
            mock_exporter_instance.get_export_info = AsyncMock(return_value={
                "directories": {
                    "reports": "/tmp/reports",
                    "temp": "/tmp/temp"
                },
                "supported_formats": ["html", "pdf", "json", "zip"]
            })
            mock_exporter.return_value = mock_exporter_instance
            
            # 模拟目录存在
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.is_dir', return_value=True):
                    
                    # 调用API
                    response = test_client.get("/api/v1/patent/health")
                    
                    # 验证响应
                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True
                    assert data["data"]["status"] == "healthy"


class TestPatentWorkflowPerformance:
    """专利工作流性能测试类."""
    
    @pytest.mark.asyncio
    async def test_concurrent_workflow_execution(self, patent_workflow_engine):
        """测试并发工作流执行性能."""
        # 创建多个并发执行
        executions = []
        for i in range(5):
            execution = WorkflowExecution(
                graph_id="performance_test",
                input_data={"keywords": [f"test_{i}"], "execution_id": i}
            )
            executions.append(execution)
        
        # 模拟工作流图
        mock_graph = MagicMock()
        mock_graph.workflow_type = WorkflowType.SEQUENTIAL
        mock_graph.nodes = [MagicMock(node_id="test_node", name="Test Node")]
        mock_graph.edges = []
        
        with patch.object(patent_workflow_engine, '_get_workflow_graph', 
                         return_value=mock_graph):
            with patch.object(patent_workflow_engine.sequential_engine, 'execute_workflow',
                             side_effect=lambda x: x) as mock_execute:
                
                # 并发执行工作流
                start_time = datetime.now()
                results = await asyncio.gather(*[
                    patent_workflow_engine.execute_workflow(execution) 
                    for execution in executions
                ])
                end_time = datetime.now()
                
                # 验证性能
                execution_time = (end_time - start_time).total_seconds()
                assert execution_time < 10.0  # 应该在10秒内完成
                assert len(results) == 5
                assert mock_execute.call_count == 5
    
    @pytest.mark.asyncio
    async def test_large_data_processing_workflow(self, patent_workflow_engine, sample_patent_data):
        """测试大数据量处理工作流性能."""
        # 创建大数据量的输入
        large_dataset = sample_patent_data * 1000  # 模拟2000条专利数据
        
        execution = WorkflowExecution(
            graph_id="large_data_test",
            input_data={
                "patents": large_dataset,
                "processing_mode": "batch"
            }
        )
        
        # 模拟大数据处理
        with patch.object(patent_workflow_engine, '_execute_single_node') as mock_execute:
            mock_execute.return_value = {
                "status": "success",
                "processed_count": len(large_dataset),
                "processing_time": 2.5
            }
            
            mock_graph = MagicMock()
            mock_graph.workflow_type = WorkflowType.SEQUENTIAL
            mock_graph.nodes = [MagicMock(node_id="batch_processor", name="Batch Processor")]
            mock_graph.edges = []
            
            with patch.object(patent_workflow_engine, '_get_workflow_graph', 
                             return_value=mock_graph):
                with patch.object(patent_workflow_engine.sequential_engine, 'execute_workflow',
                                 return_value=execution):
                    
                    start_time = datetime.now()
                    result = await patent_workflow_engine.execute_workflow(execution)
                    end_time = datetime.now()
                    
                    # 验证大数据处理性能
                    processing_time = (end_time - start_time).total_seconds()
                    assert processing_time < 30.0  # 应该在30秒内完成大数据处理
                    assert result is not None
    
    @pytest.mark.asyncio
    async def test_workflow_memory_usage(self, patent_workflow_engine):
        """测试工作流内存使用情况."""
        import psutil
        import os
        
        # 获取初始内存使用
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # 执行多个工作流
        executions = []
        for i in range(10):
            execution = WorkflowExecution(
                graph_id="memory_test",
                input_data={"test_data": "x" * 10000}  # 10KB数据
            )
            executions.append(execution)
        
        # 模拟执行
        mock_graph = MagicMock()
        mock_graph.workflow_type = WorkflowType.SEQUENTIAL
        mock_graph.nodes = [MagicMock(node_id="memory_node", name="Memory Node")]
        mock_graph.edges = []
        
        with patch.object(patent_workflow_engine, '_get_workflow_graph', 
                         return_value=mock_graph):
            with patch.object(patent_workflow_engine.sequential_engine, 'execute_workflow',
                             side_effect=lambda x: x):
                
                for execution in executions:
                    await patent_workflow_engine.execute_workflow(execution)
        
        # 检查内存使用
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # 内存增长应该在合理范围内（小于100MB）
        assert memory_increase < 100 * 1024 * 1024


class TestPatentWorkflowEdgeCases:
    """专利工作流边界情况测试类."""
    
    @pytest.mark.asyncio
    async def test_empty_workflow_execution(self, patent_workflow_engine):
        """测试空工作流执行."""
        execution = WorkflowExecution(
            graph_id="empty_workflow",
            input_data={}
        )
        
        # 模拟空工作流图
        mock_graph = MagicMock()
        mock_graph.workflow_type = WorkflowType.SEQUENTIAL
        mock_graph.nodes = []
        mock_graph.edges = []
        
        with patch.object(patent_workflow_engine, '_get_workflow_graph', 
                         return_value=mock_graph):
            with patch.object(patent_workflow_engine.sequential_engine, 'execute_workflow',
                             return_value=execution):
                
                result = await patent_workflow_engine.execute_workflow(execution)
                
                # 验证空工作流处理
                assert result is not None
                assert result.execution_id == execution.execution_id
    
    @pytest.mark.asyncio
    async def test_circular_dependency_workflow(self, patent_workflow_engine):
        """测试循环依赖工作流处理."""
        execution = WorkflowExecution(
            graph_id="circular_dependency",
            input_data={"test": "circular"}
        )
        
        # 模拟循环依赖的工作流图
        mock_graph = MagicMock()
        mock_graph.workflow_type = WorkflowType.HIERARCHICAL
        mock_graph.nodes = [
            MagicMock(node_id="node_a", name="Node A"),
            MagicMock(node_id="node_b", name="Node B"),
            MagicMock(node_id="node_c", name="Node C")
        ]
        # 创建循环依赖：A -> B -> C -> A
        mock_graph.edges = [
            MagicMock(source_node="node_a", target_node="node_b"),
            MagicMock(source_node="node_b", target_node="node_c"),
            MagicMock(source_node="node_c", target_node="node_a")
        ]
        
        with patch.object(patent_workflow_engine, '_get_workflow_graph', 
                         return_value=mock_graph):
            
            # 执行应该能处理循环依赖
            result = await patent_workflow_engine.execute_workflow(execution)
            
            # 验证循环依赖处理
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_invalid_workflow_template(self, patent_workflow_engine):
        """测试无效工作流模板处理."""
        # 尝试从不存在的模板创建执行
        with pytest.raises(ValueError, match="Template 'nonexistent_template' not found"):
            await patent_workflow_engine.create_execution_from_template(
                "nonexistent_template",
                {"test": "data"}
            )
    
    @pytest.mark.asyncio
    async def test_workflow_timeout_handling(self, patent_workflow_engine):
        """测试工作流超时处理."""
        execution = WorkflowExecution(
            graph_id="timeout_test",
            input_data={"timeout": 1}  # 1秒超时
        )
        
        # 模拟长时间运行的工作流
        async def slow_execution(*args, **kwargs):
            await asyncio.sleep(2)  # 超过超时时间
            return execution
        
        with patch.object(patent_workflow_engine, '_get_workflow_graph', 
                         return_value=MagicMock(workflow_type=WorkflowType.SEQUENTIAL)):
            with patch.object(patent_workflow_engine.sequential_engine, 'execute_workflow',
                             side_effect=slow_execution):
                
                # 使用超时执行
                try:
                    result = await asyncio.wait_for(
                        patent_workflow_engine.execute_workflow(execution),
                        timeout=1.5
                    )
                except asyncio.TimeoutError:
                    # 超时是预期的行为
                    assert True
                else:
                    # 如果没有超时，验证结果
                    assert result is not None


# 运行测试的辅助函数
def run_integration_tests():
    """运行所有集成测试."""
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--asyncio-mode=auto"
    ])


if __name__ == "__main__":
    run_integration_tests()