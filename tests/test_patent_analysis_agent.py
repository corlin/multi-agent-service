"""Tests for PatentAnalysisAgent."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from collections import defaultdict

from src.multi_agent_service.patent.agents.analysis import PatentAnalysisAgent
from src.multi_agent_service.patent.models.requests import PatentAnalysisRequest
from src.multi_agent_service.patent.models.results import (
    PatentAnalysisResult, TrendAnalysisModel, TechClassificationModel, 
    CompetitionAnalysisModel
)
from src.multi_agent_service.patent.models.patent_data import PatentData, PatentDataset
from src.multi_agent_service.patent.models.external_data import EnhancedData
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
        agent_id="patent-analysis-agent-001",
        agent_type=AgentType.PATENT_ANALYSIS,
        name="Patent Analysis Agent",
        description="A patent analysis agent for testing",
        capabilities=["trend_analysis", "tech_classification", "competition_analysis"],
        llm_config=model_config,
        prompt_template="You are a patent analysis agent. {input}",
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
async def analysis_agent(agent_config, mock_model_client):
    """Create a patent analysis agent instance."""
    agent = PatentAnalysisAgent(agent_config, mock_model_client)
    await agent.initialize()
    return agent


@pytest.fixture
def patent_request():
    """Create a test patent analysis request."""
    from src.multi_agent_service.models.enums import AnalysisType
    
    class MockAnalysisType:
        def __init__(self, value):
            self.value = value
    
    return PatentAnalysisRequest(
        content="Analyze AI patents",
        user_id="test-user",
        keywords=["artificial intelligence", "machine learning"],
        analysis_types=[
            MockAnalysisType("trend_analysis"),
            MockAnalysisType("tech_classification"),
            MockAnalysisType("competition_analysis")
        ]
    )


@pytest.fixture
def sample_patent_dataset():
    """Create a sample patent dataset for testing."""
    patents = []
    
    # Create sample patents with varying data
    for i in range(50):
        year = 2020 + (i % 5)  # 2020-2024
        country = ["US", "CN", "JP", "DE", "KR"][i % 5]
        applicant = f"Company {chr(65 + i % 10)}"  # Company A-J
        
        patent = PatentData(
            application_number=f"{country}{year}{1000 + i}",
            title=f"AI Patent {i}: Advanced Machine Learning System",
            abstract=f"This patent describes an advanced AI system for {i}...",
            applicants=[applicant],
            inventors=[f"Inventor {i % 20}"],
            application_date=datetime(year, 1 + i % 12, 1 + i % 28),
            country=country,
            status=["申请中", "已公开", "已授权"][i % 3],
            ipc_classes=[f"G06F{i % 20}/00", f"H04L{i % 15}/00"][:(i % 2 + 1)],
            data_source="test_source"
        )
        patents.append(patent)
    
    return PatentDataset(
        patents=patents,
        total_count=len(patents),
        search_keywords=["artificial intelligence"],
        collection_date=datetime.now(),
        data_sources=["test_source"]
    )


class TestPatentAnalysisAgent:
    """Test cases for PatentAnalysisAgent."""
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, agent_config, mock_model_client):
        """Test agent initialization."""
        agent = PatentAnalysisAgent(agent_config, mock_model_client)
        
        # Check initial state
        assert agent.agent_id == "patent-analysis-agent-001"
        assert agent.agent_type == AgentType.PATENT_ANALYSIS
        assert agent.name == "Patent Analysis Agent"
        
        # Initialize agent
        result = await agent.initialize()
        assert result is True
        
        # Check analysis configuration
        assert agent.analysis_config['enable_trend_analysis'] is True
        assert agent.analysis_config['enable_tech_classification'] is True
        assert agent.analysis_config['enable_competition_analysis'] is True
        assert agent.analysis_config['min_patents_for_analysis'] == 10
    
    @pytest.mark.asyncio
    async def test_get_specific_capabilities(self, analysis_agent):
        """Test getting agent capabilities."""
        capabilities = await analysis_agent._get_specific_capabilities()
        
        expected_capabilities = [
            "专利趋势分析",
            "技术分类统计",
            "竞争格局分析",
            "地域分布分析",
            "IPC分类分析",
            "申请人统计分析",
            "时间序列分析",
            "技术演进预测"
        ]
        
        assert all(cap in capabilities for cap in expected_capabilities)
    
    @pytest.mark.asyncio
    async def test_process_patent_request_success(self, analysis_agent, patent_request):
        """Test successful patent analysis request processing."""
        # Mock cache and data methods
        analysis_agent._get_from_cache = AsyncMock(return_value=None)
        analysis_agent._save_to_cache = AsyncMock()
        
        # Process request
        result = await analysis_agent._process_patent_request(patent_request)
        
        # Verify result structure
        assert result["status"] == "completed"
        assert "analysis_result" in result
        assert "insights" in result
        assert "recommendations" in result
        assert "quality_score" in result
        assert "processing_time" in result
        assert "total_patents_analyzed" in result
        
        # Verify analysis result
        analysis_result = result["analysis_result"]
        assert isinstance(analysis_result, PatentAnalysisResult)
        assert analysis_result.request_id == patent_request.request_id
    
    @pytest.mark.asyncio
    async def test_process_patent_request_cached(self, analysis_agent, patent_request):
        """Test patent analysis request with cached results."""
        # Mock cached result
        cached_result = {
            "status": "completed",
            "analysis_result": PatentAnalysisResult(
                request_id=patent_request.request_id,
                analysis_date=datetime.now()
            ),
            "quality_score": 0.85,
            "processing_time": 2.5
        }
        analysis_agent._get_from_cache = AsyncMock(return_value=cached_result)
        
        # Process request
        result = await analysis_agent._process_patent_request(patent_request)
        
        # Should return cached result
        assert result == cached_result
        assert result["quality_score"] == 0.85
    
    @pytest.mark.asyncio
    async def test_process_patent_request_insufficient_data(self, analysis_agent, patent_request):
        """Test patent analysis with insufficient data."""
        # Mock methods to return insufficient data
        analysis_agent._get_from_cache = AsyncMock(return_value=None)
        analysis_agent._get_patent_dataset = AsyncMock(return_value=PatentDataset(
            patents=[],  # Empty dataset
            total_count=0
        ))
        
        # Process request
        result = await analysis_agent._process_patent_request(patent_request)
        
        # Should fail due to insufficient data
        assert result["status"] == "failed"
        assert "Insufficient patent data" in result["error"]
        assert result["total_patents_analyzed"] == 0
    
    @pytest.mark.asyncio
    async def test_get_patent_dataset(self, analysis_agent, patent_request):
        """Test getting patent dataset."""
        # Get patent dataset
        dataset = await analysis_agent._get_patent_dataset(patent_request)
        
        # Verify dataset
        assert dataset is not None
        assert isinstance(dataset, PatentDataset)
        assert len(dataset.patents) == 100  # Mock implementation creates 100 patents
        assert dataset.search_keywords == patent_request.keywords
        
        # Verify patent data
        for patent in dataset.patents[:5]:  # Check first 5 patents
            assert patent.application_number is not None
            assert patent.title is not None
            assert len(patent.applicants) > 0
            assert len(patent.inventors) > 0
            assert patent.application_date is not None
    
    @pytest.mark.asyncio
    async def test_get_enhanced_data(self, analysis_agent, patent_request):
        """Test getting enhanced data."""
        # Get enhanced data
        enhanced_data = await analysis_agent._get_enhanced_data(patent_request)
        
        # Verify enhanced data (mock implementation returns minimal data)
        assert enhanced_data is not None
        assert isinstance(enhanced_data, EnhancedData)
        assert enhanced_data.collection_date is not None
    
    @pytest.mark.asyncio
    async def test_perform_comprehensive_analysis(self, analysis_agent, patent_request, sample_patent_dataset):
        """Test comprehensive patent analysis."""
        # Perform analysis
        analysis_result = await analysis_agent._perform_comprehensive_analysis(
            sample_patent_dataset, None, patent_request
        )
        
        # Verify analysis result
        assert isinstance(analysis_result, PatentAnalysisResult)
        assert analysis_result.request_id == patent_request.request_id
        assert analysis_result.total_patents_analyzed == len(sample_patent_dataset.patents)
        
        # Verify individual analyses
        assert analysis_result.trend_analysis is not None
        assert analysis_result.tech_classification is not None
        assert analysis_result.competition_analysis is not None
        assert analysis_result.geographic_analysis is not None
    
    @pytest.mark.asyncio
    async def test_analyze_trends(self, analysis_agent, sample_patent_dataset):
        """Test trend analysis."""
        # Perform trend analysis
        trend_analysis = await analysis_agent._analyze_trends(sample_patent_dataset)
        
        # Verify trend analysis
        assert isinstance(trend_analysis, TrendAnalysisModel)
        assert len(trend_analysis.yearly_counts) > 0
        assert trend_analysis.total_patents == len(sample_patent_dataset.patents)
        assert trend_analysis.trend_direction in ["increasing", "decreasing", "stable"]
        
        # Verify yearly counts
        total_from_counts = sum(trend_analysis.yearly_counts.values())
        assert total_from_counts == trend_analysis.total_patents
        
        # Verify growth rates
        if len(trend_analysis.growth_rates) > 0:
            for year, rate in trend_analysis.growth_rates.items():
                assert isinstance(rate, float)
    
    @pytest.mark.asyncio
    async def test_classify_technologies(self, analysis_agent, sample_patent_dataset):
        """Test technology classification."""
        # Perform technology classification
        tech_classification = await analysis_agent._classify_technologies(sample_patent_dataset)
        
        # Verify classification
        assert isinstance(tech_classification, TechClassificationModel)
        assert len(tech_classification.ipc_distribution) > 0
        assert len(tech_classification.keyword_clusters) > 0
        assert len(tech_classification.main_technologies) > 0
        
        # Verify IPC distribution
        total_ipc_count = sum(tech_classification.ipc_distribution.values())
        assert total_ipc_count > 0
        
        # Verify keyword clusters
        for cluster in tech_classification.keyword_clusters:
            assert "cluster_id" in cluster
            assert "main_keyword" in cluster
            assert "patent_count" in cluster
    
    @pytest.mark.asyncio
    async def test_analyze_competition(self, analysis_agent, sample_patent_dataset):
        """Test competition analysis."""
        # Perform competition analysis
        competition_analysis = await analysis_agent._analyze_competition(sample_patent_dataset)
        
        # Verify competition analysis
        assert isinstance(competition_analysis, CompetitionAnalysisModel)
        assert len(competition_analysis.applicant_distribution) > 0
        assert len(competition_analysis.top_applicants) > 0
        assert 0.0 <= competition_analysis.market_concentration <= 1.0
        assert 0.0 <= competition_analysis.hhi_index <= 1.0
        
        # Verify top applicants are sorted by patent count
        for i in range(len(competition_analysis.top_applicants) - 1):
            current_count = competition_analysis.top_applicants[i][1]
            next_count = competition_analysis.top_applicants[i + 1][1]
            assert current_count >= next_count
    
    @pytest.mark.asyncio
    async def test_analyze_geography(self, analysis_agent, sample_patent_dataset):
        """Test geographic analysis."""
        # Perform geographic analysis
        geographic_analysis = await analysis_agent._analyze_geography(sample_patent_dataset)
        
        # Verify geographic analysis
        assert isinstance(geographic_analysis, dict)
        assert "country_distribution" in geographic_analysis
        assert "top_countries" in geographic_analysis
        assert "globalization_index" in geographic_analysis
        
        # Verify country distribution
        country_dist = geographic_analysis["country_distribution"]
        assert len(country_dist) > 0
        total_country_count = sum(country_dist.values())
        assert total_country_count == len(sample_patent_dataset.patents)
        
        # Verify globalization index
        globalization_index = geographic_analysis["globalization_index"]
        assert 0.0 <= globalization_index <= 1.0
    
    @pytest.mark.asyncio
    async def test_generate_insights(self, analysis_agent, sample_patent_dataset):
        """Test insights generation."""
        # Create analysis result
        analysis_result = await analysis_agent._perform_comprehensive_analysis(
            sample_patent_dataset, None, patent_request()
        )
        
        # Generate insights
        insights = await analysis_agent._generate_insights(analysis_result, None)
        
        # Verify insights
        assert isinstance(insights, list)
        assert len(insights) > 0
        
        # Verify insight content
        for insight in insights:
            assert isinstance(insight, str)
            assert len(insight) > 10  # Should be meaningful insights
    
    @pytest.mark.asyncio
    async def test_generate_recommendations(self, analysis_agent, sample_patent_dataset):
        """Test recommendations generation."""
        # Create analysis result
        analysis_result = await analysis_agent._perform_comprehensive_analysis(
            sample_patent_dataset, None, patent_request()
        )
        
        # Generate recommendations
        recommendations = await analysis_agent._generate_recommendations(analysis_result, None)
        
        # Verify recommendations
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        # Verify recommendation content
        for rec in recommendations:
            assert isinstance(rec, str)
            assert len(rec) > 10  # Should be meaningful recommendations
    
    @pytest.mark.asyncio
    async def test_evaluate_analysis_quality(self, analysis_agent, sample_patent_dataset):
        """Test analysis quality evaluation."""
        # Create analysis result
        analysis_result = await analysis_agent._perform_comprehensive_analysis(
            sample_patent_dataset, None, patent_request()
        )
        
        # Evaluate quality
        quality_score = await analysis_agent._evaluate_analysis_quality(
            analysis_result, sample_patent_dataset
        )
        
        # Verify quality score
        assert 0.0 <= quality_score <= 1.0
        assert quality_score > 0.5  # Should be reasonable quality with complete analysis
    
    @pytest.mark.asyncio
    async def test_generate_response_content_success(self, analysis_agent):
        """Test response content generation for successful analysis."""
        result = {
            "status": "completed",
            "total_patents_analyzed": 100,
            "quality_score": 0.85,
            "processing_time": 5.2,
            "insights": [
                "专利申请呈上升趋势",
                "AI技术占主导地位",
                "市场竞争激烈"
            ],
            "recommendations": [
                "建议加大研发投入",
                "关注新兴技术",
                "加强专利布局"
            ]
        }
        
        # Generate response content
        content = await analysis_agent._generate_response_content(result)
        
        # Verify content
        assert "专利分析已完成" in content
        assert "分析专利数量: 100" in content
        assert "0.85/1.0" in content
        assert "5.2秒" in content
        assert "专利申请呈上升趋势" in content
        assert "建议加大研发投入" in content
    
    @pytest.mark.asyncio
    async def test_generate_response_content_failure(self, analysis_agent):
        """Test response content generation for failed analysis."""
        result = {
            "status": "failed",
            "error": "Insufficient data for analysis"
        }
        
        # Generate response content
        content = await analysis_agent._generate_response_content(result)
        
        # Verify error content
        assert "专利分析失败" in content
        assert "Insufficient data for analysis" in content


class TestPatentAnalysisAgentEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.mark.asyncio
    async def test_empty_dataset_analysis(self, analysis_agent):
        """Test analysis with empty dataset."""
        empty_dataset = PatentDataset(patents=[], total_count=0)
        
        # Should handle empty dataset gracefully
        trend_analysis = await analysis_agent._analyze_trends(empty_dataset)
        assert len(trend_analysis.yearly_counts) == 0
        assert trend_analysis.total_patents == 0
        assert trend_analysis.trend_direction == "stable"
    
    @pytest.mark.asyncio
    async def test_single_patent_analysis(self, analysis_agent):
        """Test analysis with single patent."""
        single_patent = PatentData(
            application_number="US2024001",
            title="Single AI Patent",
            abstract="This is a single patent for testing",
            applicants=["Test Company"],
            inventors=["Test Inventor"],
            application_date=datetime(2024, 1, 1),
            country="US",
            status="申请中",
            ipc_classes=["G06F15/00"],
            data_source="test"
        )
        
        single_dataset = PatentDataset(
            patents=[single_patent],
            total_count=1
        )
        
        # Perform analyses
        trend_analysis = await analysis_agent._analyze_trends(single_dataset)
        tech_classification = await analysis_agent._classify_technologies(single_dataset)
        competition_analysis = await analysis_agent._analyze_competition(single_dataset)
        
        # Verify results
        assert trend_analysis.total_patents == 1
        assert len(tech_classification.ipc_distribution) == 1
        assert len(competition_analysis.applicant_distribution) == 1
    
    @pytest.mark.asyncio
    async def test_missing_data_handling(self, analysis_agent):
        """Test handling of patents with missing data."""
        incomplete_patent = PatentData(
            application_number="US2024002",
            title="Incomplete Patent",
            abstract="Missing some data",
            applicants=[],  # Empty applicants
            inventors=[],   # Empty inventors
            application_date=datetime(2024, 1, 1),
            country="US",
            status="申请中",
            ipc_classes=[],  # Empty IPC classes
            data_source="test"
        )
        
        incomplete_dataset = PatentDataset(
            patents=[incomplete_patent],
            total_count=1
        )
        
        # Should handle missing data gracefully
        tech_classification = await analysis_agent._classify_technologies(incomplete_dataset)
        competition_analysis = await analysis_agent._analyze_competition(incomplete_dataset)
        
        # Verify handling of empty data
        assert len(tech_classification.ipc_distribution) == 0
        assert len(competition_analysis.applicant_distribution) == 0
    
    @pytest.mark.asyncio
    async def test_analysis_with_exceptions(self, analysis_agent, patent_request):
        """Test analysis when sub-methods raise exceptions."""
        # Mock one analysis method to raise exception
        analysis_agent._analyze_trends = AsyncMock(side_effect=Exception("Trend analysis failed"))
        analysis_agent._get_from_cache = AsyncMock(return_value=None)
        
        # Process request should handle exception gracefully
        result = await analysis_agent._process_patent_request(patent_request)
        
        # Should fail gracefully
        assert result["status"] == "failed"
        assert "Trend analysis failed" in result["error"]


def patent_request():
    """Helper function to create patent request."""
    class MockAnalysisType:
        def __init__(self, value):
            self.value = value
    
    return PatentAnalysisRequest(
        content="Analyze patents",
        user_id="test-user",
        keywords=["test"],
        analysis_types=[MockAnalysisType("comprehensive")]
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])