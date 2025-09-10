"""Tests for PatentDataCollectionAgent."""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.multi_agent_service.patent.agents.data_collection import PatentDataCollectionAgent
from src.multi_agent_service.patent.models.requests import PatentAnalysisRequest
from src.multi_agent_service.patent.models.patent_data import (
    PatentData, PatentDataset, PatentApplicant, PatentInventor, PatentClassification
)
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
        agent_id="patent-data-collection-agent-001",
        agent_type=AgentType.PATENT_DATA_COLLECTION,
        name="Patent Data Collection Agent",
        description="A patent data collection agent for testing",
        capabilities=["google_patents", "patent_public_api", "data_validation"],
        llm_config=model_config,
        prompt_template="You are a patent data collection agent. {input}",
        max_concurrent_tasks=3
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


class MockPatentDataCollectionAgent(PatentDataCollectionAgent):
    """Mock PatentDataCollectionAgent for testing."""
    
    async def _process_request_specific(self, request):
        return MagicMock()
    
    async def _process_patent_request_specific(self, request):
        return {"status": "success", "data": "mock_result"}
    
    async def can_handle_request(self, request):
        return 0.9
    
    async def estimate_processing_time(self, request):
        return 30.0
    
    async def get_capabilities(self):
        return ["google_patents", "patent_public_api", "data_validation"]


@pytest.fixture
def data_collection_agent(agent_config, mock_model_router):
    """Create a PatentDataCollectionAgent instance for testing."""
    return MockPatentDataCollectionAgent(agent_config, mock_model_router)


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
def sample_patent_data():
    """Create sample patent data for testing."""
    applicant = PatentApplicant(
        name="Tech Corp",
        normalized_name="Tech Corp",
        country="US",
        applicant_type="company"
    )
    inventor = PatentInventor(
        name="John Smith",
        normalized_name="John Smith",
        country="US"
    )
    classification = PatentClassification(
        ipc_class="G06N 3/08"
    )
    
    return PatentData(
        application_number="US16123456",
        title="Advanced Machine Learning System",
        abstract="A system for advanced machine learning applications with sufficient length for validation",
        applicants=[applicant],
        inventors=[inventor],
        application_date=datetime(2022, 1, 15),
        classifications=[classification],
        country="US",
        status="已公开",
        data_source="test"
    )


class TestPatentDataCollectionAgent:
    """Test cases for PatentDataCollectionAgent."""
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, data_collection_agent):
        """Test agent initialization."""
        assert data_collection_agent.agent_id == "patent-data-collection-agent-001"
        assert data_collection_agent.agent_type == AgentType.PATENT_DATA_COLLECTION
        assert data_collection_agent.name == "Patent Data Collection Agent"
        assert "google_patents" in data_collection_agent.config.capabilities
        assert "patent_public_api" in data_collection_agent.config.capabilities
    
    @pytest.mark.asyncio
    async def test_process_request_success(self, data_collection_agent, patent_request, sample_patent_data):
        """Test successful patent data collection request processing."""
        # Mock cache methods
        data_collection_agent._get_from_cache = AsyncMock(return_value=None)
        data_collection_agent._save_to_cache = AsyncMock()
        
        # Mock data collection methods
        data_collection_agent._collect_from_source = AsyncMock(
            return_value={"patents": [sample_patent_data.model_dump()], "total": 1}
        )
        data_collection_agent._merge_and_clean_data = AsyncMock(
            return_value={"patents": [sample_patent_data.model_dump()], "total": 1}
        )
        
        # Process request
        result = await data_collection_agent.process_request(patent_request)
        
        # Verify result
        assert result.response_content is not None
        assert result.agent_id == data_collection_agent.agent_id
        
        # Verify cache was called
        data_collection_agent._save_to_cache.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_request_cached(self, data_collection_agent, patent_request, sample_patent_data):
        """Test patent data collection request with cached results."""
        # Mock cached result
        cached_data = {
            "status": "success",
            "data": {"patents": [sample_patent_data.dict()], "total": 1},
            "total_patents": 1
        }
        data_collection_agent._get_from_cache = AsyncMock(return_value=cached_data)
        
        # Process request
        result = await data_collection_agent.process_request(patent_request.dict())
        
        # Verify cached result is returned
        assert result == cached_data
        assert result["status"] == "success"
        assert result["total_patents"] == 1
    
    @pytest.mark.asyncio
    async def test_collect_from_google_patents(self, data_collection_agent, sample_patent_data):
        """Test collecting data from Google Patents API."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock API response
            mock_response = MagicMock()
            mock_response.json = AsyncMock(return_value={
                "patents": [sample_patent_data.dict()],
                "total": 1
            })
            mock_response.status = 200
            mock_get.return_value.__aenter__.return_value = mock_response
            
            # Test data collection
            result = await data_collection_agent._collect_from_source(
                "google_patents", ["AI", "ML"], 10
            )
            
            # Verify result
            assert "patents" in result
            assert result["total"] == 1
    
    @pytest.mark.asyncio
    async def test_collect_from_patent_public_api(self, data_collection_agent, sample_patent_data):
        """Test collecting data from Patent Public API."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock API response
            mock_response = MagicMock()
            mock_response.json = AsyncMock(return_value={
                "patents": [sample_patent_data.dict()],
                "count": 1
            })
            mock_response.status = 200
            mock_get.return_value.__aenter__.return_value = mock_response
            
            # Test data collection
            result = await data_collection_agent._collect_from_source(
                "patent_public_api", ["artificial intelligence"], 20
            )
            
            # Verify result
            assert "patents" in result
    
    @pytest.mark.asyncio
    async def test_data_merge_and_clean(self, data_collection_agent, sample_patent_data):
        """Test data merging and cleaning functionality."""
        # Mock raw data from multiple sources
        raw_data = [
            {"patents": [sample_patent_data.dict()], "total": 1},
            {"patents": [sample_patent_data.dict()], "total": 1}  # Duplicate
        ]
        
        # Test merge and clean
        result = await data_collection_agent._merge_and_clean_data(raw_data)
        
        # Verify deduplication and cleaning
        assert "patents" in result
        assert len(result["patents"]) == 1  # Duplicates should be removed
    
    @pytest.mark.asyncio
    async def test_data_validation(self, data_collection_agent):
        """Test patent data validation."""
        # Test valid data
        valid_patent = {
            "application_number": "US16123456",
            "title": "Test Patent",
            "abstract": "Test abstract",
            "applicants": [{"name": "Test Corp", "country": "US", "applicant_type": "company"}],
            "inventors": [{"name": "John Doe", "country": "US"}],
            "application_date": "2022-01-15T00:00:00",
            "classifications": [{"ipc_class": "G06N3/08"}],
            "country": "US",
            "status": "published"
        }
        
        is_valid = data_collection_agent._validate_patent_data(valid_patent)
        assert is_valid is True
        
        # Test invalid data
        invalid_patent = {
            "application_number": "",  # Empty application number
            "title": "Test Patent"
        }
        
        is_valid = data_collection_agent._validate_patent_data(invalid_patent)
        assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_cache_operations(self, data_collection_agent):
        """Test cache get and set operations."""
        # Mock Redis operations
        with patch('redis.Redis') as mock_redis:
            mock_redis_instance = MagicMock()
            mock_redis.return_value = mock_redis_instance
            
            # Test cache set
            test_data = {"test": "data"}
            await data_collection_agent._save_to_cache("test_key", test_data)
            
            # Test cache get
            mock_redis_instance.get.return_value = '{"test": "data"}'
            result = await data_collection_agent._get_from_cache("test_key")
            
            assert result == test_data


class TestPatentDataCollectionAgentErrorHandling:
    """Test error handling in PatentDataCollectionAgent."""
    
    @pytest.mark.asyncio
    async def test_api_timeout_handling(self, data_collection_agent):
        """Test handling of API timeout errors."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock timeout error
            mock_get.side_effect = asyncio.TimeoutError("Request timeout")
            
            # Test error handling
            result = await data_collection_agent._collect_from_source(
                "google_patents", ["AI"], 10
            )
            
            # Should return empty result on timeout
            assert result == {"patents": [], "total": 0}
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, data_collection_agent):
        """Test handling of API errors."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock API error response
            mock_response = MagicMock()
            mock_response.status = 500
            mock_response.text = AsyncMock(return_value="Internal Server Error")
            mock_get.return_value.__aenter__.return_value = mock_response
            
            # Test error handling
            result = await data_collection_agent._collect_from_source(
                "google_patents", ["AI"], 10
            )
            
            # Should return empty result on API error
            assert result == {"patents": [], "total": 0}
    
    @pytest.mark.asyncio
    async def test_invalid_response_handling(self, data_collection_agent):
        """Test handling of invalid API responses."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock invalid JSON response
            mock_response = MagicMock()
            mock_response.json = AsyncMock(side_effect=ValueError("Invalid JSON"))
            mock_response.status = 200
            mock_get.return_value.__aenter__.return_value = mock_response
            
            # Test error handling
            result = await data_collection_agent._collect_from_source(
                "google_patents", ["AI"], 10
            )
            
            # Should return empty result on invalid response
            assert result == {"patents": [], "total": 0}
    
    @pytest.mark.asyncio
    async def test_process_request_error(self, data_collection_agent, patent_request):
        """Test error handling in process_request method."""
        # Mock method to raise exception
        data_collection_agent._get_from_cache = AsyncMock(side_effect=Exception("Cache error"))
        
        # Process request
        result = await data_collection_agent.process_request(patent_request.dict())
        
        # Verify error response
        assert result["status"] == "error"
        assert "error" in result
        assert result["data"]["patents"] == []


class TestPatentDataCollectionAgentEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.mark.asyncio
    async def test_empty_keywords(self, data_collection_agent):
        """Test handling of empty keywords."""
        request = {"keywords": [], "limit": 10}
        
        result = await data_collection_agent.process_request(request)
        
        # Should handle empty keywords gracefully
        assert result["status"] == "success"
        assert result["data"]["patents"] == []
    
    @pytest.mark.asyncio
    async def test_large_limit(self, data_collection_agent):
        """Test handling of large limit values."""
        request = {"keywords": ["AI"], "limit": 10000}
        
        # Mock cache methods
        data_collection_agent._get_from_cache = AsyncMock(return_value=None)
        data_collection_agent._save_to_cache = AsyncMock()
        data_collection_agent._collect_from_source = AsyncMock(
            return_value={"patents": [], "total": 0}
        )
        data_collection_agent._merge_and_clean_data = AsyncMock(
            return_value={"patents": [], "total": 0}
        )
        
        result = await data_collection_agent.process_request(request)
        
        # Should handle large limits
        assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_special_characters_in_keywords(self, data_collection_agent):
        """Test handling of special characters in keywords."""
        request = {"keywords": ["AI & ML", "C++", "IoT/5G"], "limit": 10}
        
        # Mock cache methods
        data_collection_agent._get_from_cache = AsyncMock(return_value=None)
        data_collection_agent._save_to_cache = AsyncMock()
        data_collection_agent._collect_from_source = AsyncMock(
            return_value={"patents": [], "total": 0}
        )
        data_collection_agent._merge_and_clean_data = AsyncMock(
            return_value={"patents": [], "total": 0}
        )
        
        result = await data_collection_agent.process_request(request)
        
        # Should handle special characters
        assert result["status"] == "success"