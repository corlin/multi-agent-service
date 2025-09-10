"""Tests for PatentSearchAgent."""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.multi_agent_service.patent.agents.search import PatentSearchAgent
from src.multi_agent_service.patent.models.requests import PatentAnalysisRequest
from src.multi_agent_service.patent.models.external_data import (
    EnhancedData, CNKIData, BochaData, WebDataset, Literature, WebPage
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
        agent_id="patent-search-agent-001",
        agent_type=AgentType.PATENT_SEARCH,
        name="Patent Search Agent",
        description="A patent search enhancement agent for testing",
        capabilities=["cnki_search", "bocha_search", "web_crawling"],
        llm_config=model_config,
        prompt_template="You are a patent search agent. {input}",
        max_concurrent_tasks=3
    )


@pytest.fixture
def mock_model_client():
    """Create a mock model client."""
    client = MagicMock()
    client.initialize = AsyncMock(return_value=True)
    client.health_check = AsyncMock(return_value=True)
    client.cleanup = AsyncMock()
    return client


@pytest.fixture
async def search_agent(agent_config, mock_model_client):
    """Create a patent search agent instance."""
    agent = PatentSearchAgent(agent_config, mock_model_client)
    await agent.initialize()
    return agent


@pytest.fixture
def patent_request():
    """Create a test patent analysis request."""
    return PatentAnalysisRequest(
        content="Search for AI patents",
        user_id="test-user",
        keywords=["artificial intelligence", "machine learning"],
        include_academic_search=True,
        include_web_search=True
    )


class TestPatentSearchAgent:
    """Test cases for PatentSearchAgent."""
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, agent_config, mock_model_client):
        """Test agent initialization."""
        agent = PatentSearchAgent(agent_config, mock_model_client)
        
        # Check initial state
        assert agent.agent_id == "patent-search-agent-001"
        assert agent.agent_type == AgentType.PATENT_SEARCH
        assert agent.name == "Patent Search Agent"
        
        # Initialize agent
        result = await agent.initialize()
        assert result is True
        
        # Check search configuration
        assert agent.search_config['enable_cnki_search'] is True
        assert agent.search_config['enable_bocha_search'] is True
        assert agent.search_config['enable_web_crawling'] is True
    
    @pytest.mark.asyncio
    async def test_get_specific_capabilities(self, search_agent):
        """Test getting agent capabilities."""
        capabilities = await search_agent._get_specific_capabilities()
        
        expected_capabilities = [
            "CNKI学术搜索集成",
            "博查AI智能搜索",
            "网页爬取增强",
            "多源搜索结果整合",
            "搜索结果质量评估",
            "实时信息获取",
            "学术文献检索"
        ]
        
        assert all(cap in capabilities for cap in expected_capabilities)
    
    @pytest.mark.asyncio
    async def test_process_patent_request_success(self, search_agent, patent_request):
        """Test successful patent search request processing."""
        # Mock cache methods
        search_agent._get_from_cache = AsyncMock(return_value=None)
        search_agent._save_to_cache = AsyncMock()
        
        # Process request
        result = await search_agent._process_patent_request(patent_request)
        
        # Verify result structure
        assert result["status"] == "completed"
        assert "enhanced_data" in result
        assert "quality_score" in result
        assert "processing_time" in result
        assert "search_methods" in result
        
        # Verify enhanced data
        enhanced_data = result["enhanced_data"]
        assert isinstance(enhanced_data, EnhancedData)
        assert enhanced_data.collection_date is not None
    
    @pytest.mark.asyncio
    async def test_process_patent_request_cached(self, search_agent, patent_request):
        """Test patent search request with cached results."""
        # Mock cached result
        cached_result = {
            "status": "completed",
            "enhanced_data": EnhancedData(collection_date=datetime.now()),
            "quality_score": 0.85,
            "processing_time": 1.5
        }
        search_agent._get_from_cache = AsyncMock(return_value=cached_result)
        
        # Process request
        result = await search_agent._process_patent_request(patent_request)
        
        # Should return cached result
        assert result == cached_result
        assert result["quality_score"] == 0.85
    
    @pytest.mark.asyncio
    async def test_search_cnki_success(self, search_agent):
        """Test successful CNKI search."""
        keywords = ["artificial intelligence", "neural networks"]
        
        # Execute CNKI search
        cnki_data = await search_agent._search_cnki(keywords)
        
        # Verify result
        assert cnki_data is not None
        assert isinstance(cnki_data, CNKIData)
        assert len(cnki_data.literature) > 0
        assert len(cnki_data.concepts) > 0
        
        # Verify literature data
        for lit in cnki_data.literature:
            assert isinstance(lit, Literature)
            assert lit.title is not None
            assert len(lit.authors) > 0
            assert lit.abstract is not None
    
    @pytest.mark.asyncio
    async def test_search_cnki_failure(self, search_agent):
        """Test CNKI search failure handling."""
        keywords = ["artificial intelligence"]
        
        # Mock asyncio.sleep to raise exception
        with patch('asyncio.sleep', side_effect=Exception("CNKI API error")):
            cnki_data = await search_agent._search_cnki(keywords)
        
        # Should return None on failure
        assert cnki_data is None
    
    @pytest.mark.asyncio
    async def test_search_bocha_success(self, search_agent):
        """Test successful Bocha AI search."""
        keywords = ["machine learning", "deep learning"]
        
        # Execute Bocha search
        bocha_data = await search_agent._search_bocha(keywords)
        
        # Verify result
        assert bocha_data is not None
        assert isinstance(bocha_data, BochaData)
        assert len(bocha_data.web_results) > 0
        assert bocha_data.ai_analysis is not None
        
        # Verify web results
        for result in bocha_data.web_results:
            assert "title" in result
            assert "url" in result
            assert "snippet" in result
            assert "relevance_score" in result
        
        # Verify AI analysis
        ai_analysis = bocha_data.ai_analysis
        assert "summary" in ai_analysis
        assert "key_insights" in ai_analysis
        assert "trend_indicators" in ai_analysis
    
    @pytest.mark.asyncio
    async def test_search_bocha_failure(self, search_agent):
        """Test Bocha AI search failure handling."""
        keywords = ["machine learning"]
        
        # Mock asyncio.sleep to raise exception
        with patch('asyncio.sleep', side_effect=Exception("Bocha API error")):
            bocha_data = await search_agent._search_bocha(keywords)
        
        # Should return None on failure
        assert bocha_data is None
    
    @pytest.mark.asyncio
    async def test_crawl_web_data_success(self, search_agent):
        """Test successful web crawling."""
        keywords = ["patent technology", "innovation"]
        
        # Execute web crawling
        web_dataset = await search_agent._crawl_web_data(keywords)
        
        # Verify result
        assert web_dataset is not None
        assert isinstance(web_dataset, WebDataset)
        assert len(web_dataset.data) > 0
        assert len(web_dataset.sources) > 0
        
        # Verify web pages
        for page in web_dataset.data:
            assert isinstance(page, WebPage)
            assert page.url is not None
            assert page.title is not None
            assert page.content is not None
            assert page.crawl_date is not None
    
    @pytest.mark.asyncio
    async def test_crawl_web_data_failure(self, search_agent):
        """Test web crawling failure handling."""
        keywords = ["patent technology"]
        
        # Mock asyncio.sleep to raise exception
        with patch('asyncio.sleep', side_effect=Exception("Crawling error")):
            web_dataset = await search_agent._crawl_web_data(keywords)
        
        # Should return None on failure
        assert web_dataset is None
    
    @pytest.mark.asyncio
    async def test_integrate_search_results(self, search_agent):
        """Test search results integration."""
        # Create mock results
        cnki_data = CNKIData(
            literature=[],
            concepts=[],
            search_metadata={"total_results": 0}
        )
        
        bocha_data = BochaData(
            web_results=[],
            ai_analysis={},
            search_metadata={"total_results": 0}
        )
        
        web_dataset = WebDataset(
            data=[],
            sources=[],
            collection_date=datetime.now(),
            total_pages=0
        )
        
        results = [cnki_data, bocha_data, web_dataset]
        
        # Integrate results
        enhanced_data = await search_agent._integrate_search_results(results)
        
        # Verify integration
        assert isinstance(enhanced_data, EnhancedData)
        assert enhanced_data.academic_data == cnki_data
        assert enhanced_data.web_intelligence == bocha_data
        assert enhanced_data.web_crawl_data == web_dataset
        assert enhanced_data.collection_date is not None
    
    @pytest.mark.asyncio
    async def test_integrate_search_results_with_exceptions(self, search_agent):
        """Test search results integration with exceptions."""
        # Create results with exceptions
        cnki_data = CNKIData(literature=[], concepts=[], search_metadata={})
        exception = Exception("Search failed")
        
        results = [cnki_data, exception]
        
        # Integrate results
        enhanced_data = await search_agent._integrate_search_results(results)
        
        # Should handle exceptions gracefully
        assert isinstance(enhanced_data, EnhancedData)
        assert enhanced_data.academic_data == cnki_data
        assert enhanced_data.web_intelligence is None
        assert enhanced_data.web_crawl_data is None
    
    @pytest.mark.asyncio
    async def test_evaluate_search_quality(self, search_agent):
        """Test search quality evaluation."""
        # Create enhanced data with varying quality
        literature = [Literature(
            title=f"Paper {i}",
            authors=[f"Author {i}"],
            abstract=f"Abstract {i}",
            keywords=[],
            publication_date=datetime.now(),
            journal="Test Journal"
        ) for i in range(8)]
        
        cnki_data = CNKIData(
            literature=literature,
            concepts=[],
            search_metadata={}
        )
        
        web_results = [{"title": f"Result {i}"} for i in range(12)]
        bocha_data = BochaData(
            web_results=web_results,
            ai_analysis={},
            search_metadata={}
        )
        
        web_pages = [WebPage(
            url=f"http://example.com/{i}",
            title=f"Page {i}",
            content=f"Content {i}",
            extracted_data={},
            crawl_date=datetime.now()
        ) for i in range(6)]
        
        web_dataset = WebDataset(
            data=web_pages,
            sources=[],
            collection_date=datetime.now(),
            total_pages=len(web_pages)
        )
        
        enhanced_data = EnhancedData(
            academic_data=cnki_data,
            web_intelligence=bocha_data,
            web_crawl_data=web_dataset,
            collection_date=datetime.now()
        )
        
        # Evaluate quality
        quality_score = await search_agent._evaluate_search_quality(enhanced_data)
        
        # Should return reasonable quality score
        assert 0.0 <= quality_score <= 1.0
        assert quality_score > 0.5  # Should be decent quality with all data sources
    
    @pytest.mark.asyncio
    async def test_evaluate_search_quality_empty_data(self, search_agent):
        """Test search quality evaluation with empty data."""
        enhanced_data = EnhancedData(
            academic_data=None,
            web_intelligence=None,
            web_crawl_data=None,
            collection_date=datetime.now()
        )
        
        # Evaluate quality
        quality_score = await search_agent._evaluate_search_quality(enhanced_data)
        
        # Should return low quality score
        assert quality_score == 0.0
    
    @pytest.mark.asyncio
    async def test_generate_response_content_success(self, search_agent):
        """Test response content generation for successful search."""
        result = {
            "status": "completed",
            "enhanced_data": EnhancedData(
                academic_data=CNKIData(
                    literature=[MagicMock() for _ in range(5)],
                    concepts=[],
                    search_metadata={}
                ),
                web_intelligence=BochaData(
                    web_results=[{} for _ in range(10)],
                    ai_analysis={},
                    search_metadata={}
                ),
                web_crawl_data=WebDataset(
                    data=[MagicMock() for _ in range(8)],
                    sources=[],
                    collection_date=datetime.now(),
                    total_pages=8
                ),
                collection_date=datetime.now()
            ),
            "quality_score": 0.85,
            "processing_time": 5.2
        }
        
        # Generate response content
        content = await search_agent._generate_response_content(result)
        
        # Verify content
        assert "专利搜索增强已完成" in content
        assert "学术文献: 5 篇" in content
        assert "网络情报: 10 条" in content
        assert "网页数据: 8 页" in content
        assert "0.85/1.0" in content
        assert "5.2秒" in content
    
    @pytest.mark.asyncio
    async def test_generate_response_content_failure(self, search_agent):
        """Test response content generation for failed search."""
        result = {
            "status": "failed",
            "error": "API connection timeout"
        }
        
        # Generate response content
        content = await search_agent._generate_response_content(result)
        
        # Verify error content
        assert "专利搜索增强失败" in content
        assert "API connection timeout" in content
    
    @pytest.mark.asyncio
    async def test_process_request_no_search_methods(self, search_agent, patent_request):
        """Test processing request with no search methods enabled."""
        # Disable all search methods
        search_agent.search_config['enable_cnki_search'] = False
        search_agent.search_config['enable_bocha_search'] = False
        search_agent.search_config['enable_web_crawling'] = False
        
        # Mock cache methods
        search_agent._get_from_cache = AsyncMock(return_value=None)
        
        # Process request
        result = await search_agent._process_patent_request(patent_request)
        
        # Should fail with no search methods
        assert result["status"] == "failed"
        assert "No search methods enabled" in result["error"]
    
    @pytest.mark.asyncio
    async def test_concurrent_search_execution(self, search_agent, patent_request):
        """Test concurrent execution of multiple search methods."""
        # Mock cache methods
        search_agent._get_from_cache = AsyncMock(return_value=None)
        search_agent._save_to_cache = AsyncMock()
        
        # Track method calls
        cnki_called = False
        bocha_called = False
        crawl_called = False
        
        original_search_cnki = search_agent._search_cnki
        original_search_bocha = search_agent._search_bocha
        original_crawl_web_data = search_agent._crawl_web_data
        
        async def mock_search_cnki(keywords):
            nonlocal cnki_called
            cnki_called = True
            return await original_search_cnki(keywords)
        
        async def mock_search_bocha(keywords):
            nonlocal bocha_called
            bocha_called = True
            return await original_search_bocha(keywords)
        
        async def mock_crawl_web_data(keywords):
            nonlocal crawl_called
            crawl_called = True
            return await original_crawl_web_data(keywords)
        
        search_agent._search_cnki = mock_search_cnki
        search_agent._search_bocha = mock_search_bocha
        search_agent._crawl_web_data = mock_crawl_web_data
        
        # Process request
        result = await search_agent._process_patent_request(patent_request)
        
        # Verify all methods were called
        assert cnki_called
        assert bocha_called
        assert crawl_called
        assert result["status"] == "completed"


class TestPatentSearchAgentErrorHandling:
    """Test error handling in PatentSearchAgent."""
    
    @pytest.mark.asyncio
    async def test_search_timeout_handling(self, search_agent):
        """Test handling of search timeouts."""
        keywords = ["test"]
        
        # Mock timeout scenario
        with patch('asyncio.sleep', side_effect=asyncio.TimeoutError("Search timeout")):
            cnki_data = await search_agent._search_cnki(keywords)
        
        # Should handle timeout gracefully
        assert cnki_data is None
    
    @pytest.mark.asyncio
    async def test_network_error_handling(self, search_agent):
        """Test handling of network errors."""
        keywords = ["test"]
        
        # Mock network error
        with patch('asyncio.sleep', side_effect=ConnectionError("Network error")):
            bocha_data = await search_agent._search_bocha(keywords)
        
        # Should handle network error gracefully
        assert bocha_data is None
    
    @pytest.mark.asyncio
    async def test_partial_search_failure(self, search_agent, patent_request):
        """Test handling when some search methods fail."""
        # Mock cache methods
        search_agent._get_from_cache = AsyncMock(return_value=None)
        search_agent._save_to_cache = AsyncMock()
        
        # Mock one method to fail
        search_agent._search_cnki = AsyncMock(side_effect=Exception("CNKI failed"))
        
        # Process request
        result = await search_agent._process_patent_request(patent_request)
        
        # Should still complete with partial results
        assert result["status"] == "completed"
        enhanced_data = result["enhanced_data"]
        assert enhanced_data.academic_data is None  # Failed
        assert enhanced_data.web_intelligence is not None  # Should succeed
        assert enhanced_data.web_crawl_data is not None  # Should succeed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])