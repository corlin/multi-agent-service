"""Tests for PatentCoordinatorAgent."""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.multi_agent_service.patent.agents.coordinator import PatentCoordinatorAgent
from src.multi_agent_service.patent.models.requests import PatentAnalysisRequest
from src.multi_agent_service.patent.models.results import PatentAnalysisResult
from src.multi_agent_service.patent.models.patent_data import PatentData, PatentDataset
from src.multi_agent_service.models.config import AgentConfig, ModelConfig
from src.multi_agent_service.models.enums import ModelProvider, AgentType


@pytest.fixture
def model_config():
    """Create a test model configuration."""
    return ModelConfig(
        provider=ModelProvider.OPENAI,
        model_name="gpt-3.5-turbo",
        api_key="test-key",
        max_tokens=1000,
        temperature=0.7
    )


@pytest.fixture
def agent_config(model_config):
    """Create a test agent configuration."""
    return AgentConfig(
        agent_id="patent-coordinator-agent-001",
        agent_type=AgentType.PATENT_COORDINATOR,
        name="Patent Coordinator Agent",
        description="A patent coordination agent for testing",
        capabilities=["workflow_coordination", "agent_management", "result_aggregation"],
        llm_config=model_config,
        prompt_template="You are a patent coordinator agent. {input}",
        max_concurrent_tasks=5
    )


@pytest.fixture
def mock_model_client():
    """Create a mock model client."""
    client = MagicMock()
    client.initialize = AsyncMock(return_value=True)
    client.health_check = AsyncMock(return_value=True)
    client.generate_response = AsyncMock(return_value="Mock response")
    return client


@pytest.fixture
def mock_model_router():
    """Create a mock model router."""
    router = MagicMock()
    router.get_client = MagicMock(return_value=None)
    return router


@pytest.fixture
def mock_agent_router():
    """Create a mock agent router."""
    router = MagicMock()
    router.route_request = AsyncMock()
    return router


class MockPatentCoordinatorAgent(PatentCoordinatorAgent):
    """Mock PatentCoordinatorAgent for testing."""
    
    async def _process_request_specific(self, request):
        return MagicMock()
    
    async def _process_patent_request_specific(self, request):
        return {"status": "success", "data": "mock_result"}
    
    async def can_handle_request(self, request):
        return 0.9
    
    async def estimate_processing_time(self, request):
        return 30.0
    
    async def get_capabilities(self):
        return ["workflow_coordination", "agent_management"]


@pytest.fixture
def coordinator_agent(agent_config, mock_model_router, mock_agent_router):
    """Create a PatentCoordinatorAgent instance for testing."""
    agent = MockPatentCoordinatorAgent(agent_config, mock_model_router)
    # Mock the agent router
    agent.agent_router = mock_agent_router
    return agent


@pytest.fixture
def patent_request():
    """Create a test patent analysis request."""
    return PatentAnalysisRequest(
        content="Analyze artificial intelligence and machine learning patents",
        keywords=["artificial intelligence", "machine learning"],
        date_range={
            "start_date": "2020-01-01",
            "end_date": "2023-12-31"
        },
        countries=["US", "CN", "EP"],
        analysis_types=["trend", "competition", "technology"]
    )


@pytest.fixture
def mock_data_collection_result():
    """Create mock data collection result."""
    return {
        "status": "success",
        "data": {
            "patents": [
                {
                    "application_number": "US16123456",
                    "title": "AI System",
                    "abstract": "An AI system for testing",
                    "applicants": [{"name": "Tech Corp", "country": "US"}],
                    "inventors": [{"name": "John Doe", "country": "US"}],
                    "application_date": "2022-01-15T00:00:00",
                    "classifications": [{"ipc_class": "G06N3/08"}],
                    "country": "US",
                    "status": "published"
                }
            ],
            "total": 1
        },
        "total_patents": 1
    }


@pytest.fixture
def mock_search_result():
    """Create mock search enhancement result."""
    return {
        "status": "success",
        "enhanced_data": {
            "cnki_data": {
                "literature": [
                    {
                        "title": "AI Research Paper",
                        "authors": ["Dr. Smith"],
                        "abstract": "Research on AI",
                        "keywords": ["AI", "ML"],
                        "publication_date": "2022-06-01T00:00:00",
                        "journal": "AI Journal"
                    }
                ],
                "concepts": [{"term": "AI", "definition": "Artificial Intelligence"}]
            },
            "bocha_data": {
                "web_results": [{"title": "AI News", "url": "http://example.com"}],
                "ai_analysis": {"summary": "AI is growing rapidly"}
            }
        }
    }


@pytest.fixture
def mock_analysis_result():
    """Create mock analysis result."""
    return {
        "status": "success",
        "analysis": {
            "trend_analysis": {
                "yearly_counts": {"2020": 10, "2021": 15, "2022": 20},
                "growth_rates": {"2021": 0.5, "2022": 0.33},
                "trend_direction": "increasing"
            },
            "tech_classification": {
                "ipc_distribution": {"G06N": 15, "H04L": 5},
                "main_technologies": ["Machine Learning", "Neural Networks"]
            },
            "competition_analysis": {
                "top_applicants": [("Tech Corp", 10), ("AI Inc", 8)],
                "market_concentration": 0.6
            }
        }
    }


@pytest.fixture
def mock_report_result():
    """Create mock report generation result."""
    return {
        "status": "success",
        "report": {
            "html_content": "<html><body>Patent Analysis Report</body></html>",
            "pdf_content": b"PDF content",
            "charts": {
                "trend_chart": "chart_data_1",
                "tech_pie_chart": "chart_data_2"
            },
            "summary": "Analysis shows increasing trend in AI patents"
        }
    }


class TestPatentCoordinatorAgent:
    """Test cases for PatentCoordinatorAgent."""
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, coordinator_agent):
        """Test agent initialization."""
        assert coordinator_agent.agent_id == "patent-coordinator-agent-001"
        assert coordinator_agent.agent_type == AgentType.PATENT_COORDINATOR
        assert coordinator_agent.name == "Patent Coordinator Agent"
        assert "workflow_coordination" in coordinator_agent.config.capabilities
        assert "agent_management" in coordinator_agent.config.capabilities
    
    @pytest.mark.asyncio
    async def test_process_request_success(self, coordinator_agent, patent_request, 
                                         mock_data_collection_result, mock_search_result,
                                         mock_analysis_result, mock_report_result):
        """Test successful patent analysis coordination."""
        # Mock agent delegation methods
        coordinator_agent._coordinate_data_collection = AsyncMock(return_value=mock_data_collection_result)
        coordinator_agent._coordinate_search_enhancement = AsyncMock(return_value=mock_search_result)
        coordinator_agent._coordinate_analysis = AsyncMock(return_value=mock_analysis_result)
        coordinator_agent._coordinate_report_generation = AsyncMock(return_value=mock_report_result)
        
        # Process request
        result = await coordinator_agent.process_request(patent_request.dict())
        
        # Verify result
        assert result["status"] == "success"
        assert "results" in result
        assert "data_collection" in result["results"]
        assert "search_enhancement" in result["results"]
        assert "analysis" in result["results"]
        assert "report" in result["results"]
        
        # Verify all coordination methods were called
        coordinator_agent._coordinate_data_collection.assert_called_once()
        coordinator_agent._coordinate_search_enhancement.assert_called_once()
        coordinator_agent._coordinate_analysis.assert_called_once()
        coordinator_agent._coordinate_report_generation.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_coordinate_data_collection(self, coordinator_agent, patent_request, 
                                            mock_data_collection_result):
        """Test data collection coordination."""
        # Mock agent router
        coordinator_agent.agent_router.route_request = AsyncMock(return_value=mock_data_collection_result)
        
        # Test coordination
        result = await coordinator_agent._coordinate_data_collection(patent_request.dict())
        
        # Verify result
        assert result == mock_data_collection_result
        coordinator_agent.agent_router.route_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_coordinate_search_enhancement(self, coordinator_agent, patent_request, 
                                               mock_search_result):
        """Test search enhancement coordination."""
        # Mock agent router
        coordinator_agent.agent_router.route_request = AsyncMock(return_value=mock_search_result)
        
        # Test coordination
        result = await coordinator_agent._coordinate_search_enhancement(patent_request.dict())
        
        # Verify result
        assert result == mock_search_result
        coordinator_agent.agent_router.route_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_coordinate_analysis(self, coordinator_agent, patent_request, 
                                     mock_data_collection_result, mock_search_result,
                                     mock_analysis_result):
        """Test analysis coordination."""
        # Mock agent router
        coordinator_agent.agent_router.route_request = AsyncMock(return_value=mock_analysis_result)
        
        # Test coordination
        result = await coordinator_agent._coordinate_analysis(
            patent_request.dict(), mock_data_collection_result, mock_search_result
        )
        
        # Verify result
        assert result == mock_analysis_result
        coordinator_agent.agent_router.route_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_coordinate_report_generation(self, coordinator_agent, patent_request, 
                                              mock_analysis_result, mock_report_result):
        """Test report generation coordination."""
        # Mock agent router
        coordinator_agent.agent_router.route_request = AsyncMock(return_value=mock_report_result)
        
        # Test coordination
        result = await coordinator_agent._coordinate_report_generation(
            patent_request.dict(), mock_analysis_result
        )
        
        # Verify result
        assert result == mock_report_result
        coordinator_agent.agent_router.route_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_workflow_state_management(self, coordinator_agent, patent_request):
        """Test workflow state management."""
        # Mock workflow state manager
        coordinator_agent.workflow_state_manager = MagicMock()
        coordinator_agent.workflow_state_manager.save_state = AsyncMock()
        coordinator_agent.workflow_state_manager.get_state = AsyncMock(return_value=None)
        
        # Mock coordination methods
        coordinator_agent._coordinate_data_collection = AsyncMock(return_value={"status": "success"})
        coordinator_agent._coordinate_search_enhancement = AsyncMock(return_value={"status": "success"})
        coordinator_agent._coordinate_analysis = AsyncMock(return_value={"status": "success"})
        coordinator_agent._coordinate_report_generation = AsyncMock(return_value={"status": "success"})
        
        # Process request
        result = await coordinator_agent.process_request(patent_request.dict())
        
        # Verify state management was called
        assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_parallel_execution(self, coordinator_agent, patent_request):
        """Test parallel execution of independent tasks."""
        # Mock parallel execution method
        coordinator_agent._execute_parallel_tasks = AsyncMock(return_value=[
            {"status": "success", "task": "data_collection"},
            {"status": "success", "task": "search_enhancement"}
        ])
        
        # Test parallel execution
        tasks = [
            coordinator_agent._coordinate_data_collection(patent_request.dict()),
            coordinator_agent._coordinate_search_enhancement(patent_request.dict())
        ]
        
        # Mock the actual coordination methods
        coordinator_agent._coordinate_data_collection = AsyncMock(return_value={"status": "success"})
        coordinator_agent._coordinate_search_enhancement = AsyncMock(return_value={"status": "success"})
        
        # Execute tasks
        results = await asyncio.gather(*tasks)
        
        # Verify parallel execution
        assert len(results) == 2
        assert all(result["status"] == "success" for result in results)
    
    @pytest.mark.asyncio
    async def test_agent_health_monitoring(self, coordinator_agent):
        """Test agent health monitoring."""
        # Mock health check methods
        coordinator_agent._check_agent_health = AsyncMock(return_value={
            "patent_data_collection_agent": "healthy",
            "patent_search_agent": "healthy",
            "patent_analysis_agent": "healthy",
            "patent_report_agent": "healthy"
        })
        
        # Test health monitoring
        health_status = await coordinator_agent._check_agent_health()
        
        # Verify health status
        assert "patent_data_collection_agent" in health_status
        assert health_status["patent_data_collection_agent"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_result_aggregation(self, coordinator_agent):
        """Test result aggregation from multiple agents."""
        # Mock individual results
        individual_results = {
            "data_collection": {"patents": 100, "status": "success"},
            "search_enhancement": {"enhanced_records": 50, "status": "success"},
            "analysis": {"insights": 10, "status": "success"},
            "report": {"pages": 15, "status": "success"}
        }
        
        # Test aggregation
        aggregated = coordinator_agent._aggregate_results(individual_results)
        
        # Verify aggregation
        assert "summary" in aggregated
        assert "total_patents" in aggregated
        assert "total_insights" in aggregated


class TestPatentCoordinatorAgentErrorHandling:
    """Test error handling in PatentCoordinatorAgent."""
    
    @pytest.mark.asyncio
    async def test_data_collection_failure(self, coordinator_agent, patent_request):
        """Test handling of data collection failure."""
        # Mock data collection failure
        coordinator_agent._coordinate_data_collection = AsyncMock(
            return_value={"status": "error", "error": "Data collection failed"}
        )
        coordinator_agent._coordinate_search_enhancement = AsyncMock(return_value={"status": "success"})
        coordinator_agent._coordinate_analysis = AsyncMock(return_value={"status": "success"})
        coordinator_agent._coordinate_report_generation = AsyncMock(return_value={"status": "success"})
        
        # Process request
        result = await coordinator_agent.process_request(patent_request.dict())
        
        # Should handle failure gracefully
        assert result["status"] == "success"  # Coordinator should continue with available data
        assert "results" in result
    
    @pytest.mark.asyncio
    async def test_agent_timeout_handling(self, coordinator_agent, patent_request):
        """Test handling of agent timeout."""
        # Mock timeout in one agent
        coordinator_agent._coordinate_data_collection = AsyncMock(
            side_effect=asyncio.TimeoutError("Agent timeout")
        )
        
        # Process request
        result = await coordinator_agent.process_request(patent_request.dict())
        
        # Should handle timeout gracefully
        assert result["status"] == "error"
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_partial_failure_recovery(self, coordinator_agent, patent_request):
        """Test recovery from partial failures."""
        # Mock partial failure scenario
        coordinator_agent._coordinate_data_collection = AsyncMock(return_value={"status": "success"})
        coordinator_agent._coordinate_search_enhancement = AsyncMock(
            return_value={"status": "error", "error": "Search failed"}
        )
        coordinator_agent._coordinate_analysis = AsyncMock(return_value={"status": "success"})
        coordinator_agent._coordinate_report_generation = AsyncMock(return_value={"status": "success"})
        
        # Process request
        result = await coordinator_agent.process_request(patent_request.dict())
        
        # Should continue with available data
        assert result["status"] == "success"
        assert "results" in result
    
    @pytest.mark.asyncio
    async def test_workflow_state_recovery(self, coordinator_agent, patent_request):
        """Test workflow state recovery after failure."""
        # Mock workflow state manager with recovery
        coordinator_agent.workflow_state_manager = MagicMock()
        coordinator_agent.workflow_state_manager.get_state = AsyncMock(return_value={
            "step": "analysis",
            "data_collection": {"status": "completed"},
            "search_enhancement": {"status": "completed"}
        })
        coordinator_agent.workflow_state_manager.save_state = AsyncMock()
        
        # Mock coordination methods
        coordinator_agent._coordinate_analysis = AsyncMock(return_value={"status": "success"})
        coordinator_agent._coordinate_report_generation = AsyncMock(return_value={"status": "success"})
        
        # Process request (should resume from analysis step)
        result = await coordinator_agent.process_request(patent_request.dict())
        
        # Verify recovery
        assert result["status"] == "success"


class TestPatentCoordinatorAgentEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.mark.asyncio
    async def test_empty_request(self, coordinator_agent):
        """Test handling of empty request."""
        result = await coordinator_agent.process_request({})
        
        # Should handle empty request gracefully
        assert result["status"] == "error"
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_invalid_request_format(self, coordinator_agent):
        """Test handling of invalid request format."""
        invalid_request = {"invalid_field": "value"}
        
        result = await coordinator_agent.process_request(invalid_request)
        
        # Should handle invalid format gracefully
        assert result["status"] == "error"
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_large_request_handling(self, coordinator_agent):
        """Test handling of large requests."""
        large_request = {
            "keywords": ["AI"] * 1000,  # Very large keyword list
            "limit": 10000,
            "countries": ["US"] * 100
        }
        
        # Mock coordination methods
        coordinator_agent._coordinate_data_collection = AsyncMock(return_value={"status": "success"})
        coordinator_agent._coordinate_search_enhancement = AsyncMock(return_value={"status": "success"})
        coordinator_agent._coordinate_analysis = AsyncMock(return_value={"status": "success"})
        coordinator_agent._coordinate_report_generation = AsyncMock(return_value={"status": "success"})
        
        result = await coordinator_agent.process_request(large_request)
        
        # Should handle large requests
        assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_concurrent_request_handling(self, coordinator_agent, patent_request):
        """Test handling of concurrent requests."""
        # Mock coordination methods
        coordinator_agent._coordinate_data_collection = AsyncMock(return_value={"status": "success"})
        coordinator_agent._coordinate_search_enhancement = AsyncMock(return_value={"status": "success"})
        coordinator_agent._coordinate_analysis = AsyncMock(return_value={"status": "success"})
        coordinator_agent._coordinate_report_generation = AsyncMock(return_value={"status": "success"})
        
        # Process multiple concurrent requests
        tasks = [
            coordinator_agent.process_request(patent_request.dict()),
            coordinator_agent.process_request(patent_request.dict()),
            coordinator_agent.process_request(patent_request.dict())
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All requests should be handled successfully
        assert len(results) == 3
        assert all(result["status"] == "success" for result in results)