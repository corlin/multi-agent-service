"""Tests for PatentReportAgent."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.multi_agent_service.patent.agents.report import PatentReportAgent
from src.multi_agent_service.patent.models.requests import PatentAnalysisRequest
from src.multi_agent_service.patent.models.results import (
    PatentAnalysisResult, TrendAnalysisModel, TechClassificationModel, 
    CompetitionAnalysisModel
)
from src.multi_agent_service.patent.models.reports import Report, ReportContent
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
        agent_id="patent-report-agent-001",
        agent_type=AgentType.PATENT_REPORT,
        name="Patent Report Agent",
        description="A patent report generation agent for testing",
        capabilities=["report_generation", "chart_creation", "pdf_export"],
        llm_config=model_config,
        prompt_template="You are a patent report agent. {input}",
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
async def report_agent(agent_config, mock_model_client):
    """Create a patent report agent instance."""
    agent = PatentReportAgent(agent_config, mock_model_client)
    await agent.initialize()
    return agent


@pytest.fixture
def patent_request():
    """Create a test patent analysis request."""
    return PatentAnalysisRequest(
        content="Generate patent report",
        user_id="test-user",
        keywords=["artificial intelligence", "machine learning"],
        report_format="html"
    )


@pytest.fixture
def sample_analysis_result():
    """Create a sample analysis result for testing."""
    trend_analysis = TrendAnalysisModel(
        yearly_counts={2020: 45, 2021: 52, 2022: 68, 2023: 78, 2024: 85},
        growth_rates={2021: 0.16, 2022: 0.31, 2023: 0.15, 2024: 0.09},
        trend_direction="increasing",
        peak_year=2024,
        total_patents=328,
        average_annual_growth=0.18
    )
    
    tech_classification = TechClassificationModel(
        ipc_distribution={"G06F": 45, "H04L": 32, "G06N": 28, "H04W": 22, "G06Q": 18},
        keyword_clusters=[
            {"cluster_id": 0, "main_keyword": "artificial intelligence", "patent_count": 35},
            {"cluster_id": 1, "main_keyword": "machine learning", "patent_count": 28},
            {"cluster_id": 2, "main_keyword": "neural network", "patent_count": 22}
        ],
        main_technologies=["G06F (45 patents)", "H04L (32 patents)", "G06N (28 patents)"]
    )
    
    competition_analysis = CompetitionAnalysisModel(
        applicant_distribution={"Company A": 25, "Company B": 18, "Company C": 15, "Company D": 12},
        top_applicants=[("Company A", 25), ("Company B", 18), ("Company C", 15)],
        market_concentration=0.42,
        hhi_index=0.18
    )
    
    return PatentAnalysisResult(
        request_id="test-request-123",
        analysis_date=datetime.now(),
        trend_analysis=trend_analysis,
        tech_classification=tech_classification,
        competition_analysis=competition_analysis,
        insights=[
            "专利申请呈稳定增长趋势，年均增长率18%",
            "人工智能相关技术占主导地位",
            "市场竞争相对分散，前三名申请人占比58%"
        ],
        recommendations=[
            "建议加大AI技术研发投入",
            "关注G06F和H04L技术领域机会",
            "考虑与领先企业建立合作关系"
        ],
        data_quality_score=0.85,
        confidence_level=0.88,
        total_patents_analyzed=328,
        data_sources_used=["google_patents", "patent_public_api"],
        processing_time=5.2
    )


class TestPatentReportAgent:
    """Test cases for PatentReportAgent."""
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, agent_config, mock_model_client):
        """Test agent initialization."""
        agent = PatentReportAgent(agent_config, mock_model_client)
        
        # Check initial state
        assert agent.agent_id == "patent-report-agent-001"
        assert agent.agent_type == AgentType.PATENT_REPORT
        assert agent.name == "Patent Report Agent"
        
        # Initialize agent
        result = await agent.initialize()
        assert result is True
        
        # Check report configuration
        assert agent.report_config['supported_formats'] == ['html', 'pdf']
        assert agent.report_config['chart_generation_enabled'] is True
        assert 'comprehensive' in agent.report_templates
        assert 'executive' in agent.report_templates
        assert 'technical' in agent.report_templates
    
    @pytest.mark.asyncio
    async def test_get_specific_capabilities(self, report_agent):
        """Test getting agent capabilities."""
        capabilities = await report_agent._get_specific_capabilities()
        
        expected_capabilities = [
            "专利分析报告生成",
            "多格式报告导出",
            "图表自动生成",
            "报告模板管理",
            "内容质量检查",
            "报告版本控制",
            "批量报告生成"
        ]
        
        assert all(cap in capabilities for cap in expected_capabilities)
    
    @pytest.mark.asyncio
    async def test_process_patent_request_success(self, report_agent, patent_request):
        """Test successful patent report request processing."""
        # Mock cache methods
        report_agent._get_from_cache = AsyncMock(return_value=None)
        report_agent._save_to_cache = AsyncMock()
        
        # Process request
        result = await report_agent._process_patent_request(patent_request)
        
        # Verify result structure
        assert result["status"] == "completed"
        assert "report" in result
        assert "report_id" in result
        assert "quality_score" in result
        assert "processing_time" in result
        assert "formats_generated" in result
        assert "file_size" in result
        
        # Verify report
        report = result["report"]
        assert isinstance(report, Report)
        assert report.request_id == patent_request.request_id
        assert report.html_content is not None
        assert len(report.html_content) > 0
    
    @pytest.mark.asyncio
    async def test_process_patent_request_cached(self, report_agent, patent_request):
        """Test patent report request with cached results."""
        # Mock cached result
        cached_result = {
            "status": "completed",
            "report": Report(
                report_id="cached-report-123",
                request_id=patent_request.request_id,
                html_content="<html>Cached Report</html>",
                summary="Cached report summary",
                generation_date=datetime.now()
            ),
            "quality_score": 0.90,
            "processing_time": 1.0
        }
        report_agent._get_from_cache = AsyncMock(return_value=cached_result)
        
        # Process request
        result = await report_agent._process_patent_request(patent_request)
        
        # Should return cached result
        assert result == cached_result
        assert result["quality_score"] == 0.90
    
    @pytest.mark.asyncio
    async def test_get_analysis_result(self, report_agent, patent_request):
        """Test getting analysis result."""
        # Get analysis result (mock implementation)
        analysis_result = await report_agent._get_analysis_result(patent_request)
        
        # Verify analysis result
        assert analysis_result is not None
        assert isinstance(analysis_result, PatentAnalysisResult)
        assert analysis_result.request_id == patent_request.request_id
        assert analysis_result.trend_analysis is not None
        assert analysis_result.tech_classification is not None
        assert analysis_result.competition_analysis is not None
        assert len(analysis_result.insights) > 0
        assert len(analysis_result.recommendations) > 0
    
    @pytest.mark.asyncio
    async def test_generate_comprehensive_report(self, report_agent, patent_request, sample_analysis_result):
        """Test comprehensive report generation."""
        report_id = "test-report-123"
        
        # Generate report
        report = await report_agent._generate_comprehensive_report(
            report_id, patent_request, sample_analysis_result
        )
        
        # Verify report
        assert isinstance(report, Report)
        assert report.report_id == report_id
        assert report.request_id == patent_request.request_id
        assert report.html_content is not None
        assert len(report.html_content) > 100  # Should be substantial content
        assert report.summary is not None
        assert report.generation_date is not None
        
        # Verify charts
        assert len(report.charts) > 0
        assert 'trend_chart' in report.charts
        assert 'tech_pie_chart' in report.charts
        assert 'competition_bar_chart' in report.charts
        
        # Verify metadata
        assert 'template_used' in report.metadata
        assert 'charts_count' in report.metadata
        assert 'analysis_confidence' in report.metadata
    
    @pytest.mark.asyncio
    async def test_generate_charts(self, report_agent, sample_analysis_result):
        """Test chart generation."""
        # Generate charts
        charts = await report_agent._generate_charts(sample_analysis_result)
        
        # Verify charts
        assert isinstance(charts, dict)
        assert len(charts) >= 3  # Should have at least 3 charts
        
        # Verify specific charts
        assert 'trend_chart' in charts
        assert 'tech_pie_chart' in charts
        assert 'competition_bar_chart' in charts
        
        # Verify chart content (placeholder implementation)
        for chart_name, chart_content in charts.items():
            assert isinstance(chart_content, str)
            assert len(chart_content) > 0
            assert 'chart' in chart_content.lower()
    
    @pytest.mark.asyncio
    async def test_create_trend_chart(self, report_agent):
        """Test trend chart creation."""
        # Mock trend analysis
        trend_analysis = TrendAnalysisModel(
            yearly_counts={2020: 10, 2021: 15, 2022: 20, 2023: 25},
            growth_rates={},
            trend_direction="increasing"
        )
        
        # Create trend chart
        chart_html = await report_agent._create_trend_chart(trend_analysis)
        
        # Verify chart
        assert isinstance(chart_html, str)
        assert 'chart' in chart_html
        assert '趋势图表' in chart_html
    
    @pytest.mark.asyncio
    async def test_create_tech_pie_chart(self, report_agent):
        """Test technology pie chart creation."""
        # Mock tech classification
        tech_classification = TechClassificationModel(
            ipc_distribution={"G06F": 30, "H04L": 20, "G06N": 15},
            keyword_clusters=[],
            main_technologies=[]
        )
        
        # Create pie chart
        chart_html = await report_agent._create_tech_pie_chart(tech_classification)
        
        # Verify chart
        assert isinstance(chart_html, str)
        assert 'chart' in chart_html
        assert '技术分类' in chart_html
    
    @pytest.mark.asyncio
    async def test_create_competition_chart(self, report_agent):
        """Test competition chart creation."""
        # Mock competition analysis
        competition_analysis = CompetitionAnalysisModel(
            applicant_distribution={},
            top_applicants=[("Company A", 25), ("Company B", 18), ("Company C", 15)],
            market_concentration=0.5
        )
        
        # Create competition chart
        chart_html = await report_agent._create_competition_chart(competition_analysis)
        
        # Verify chart
        assert isinstance(chart_html, str)
        assert 'chart' in chart_html
        assert '竞争格局' in chart_html
    
    @pytest.mark.asyncio
    async def test_generate_report_content(self, report_agent, sample_analysis_result):
        """Test report content generation."""
        # Generate report content
        content = await report_agent._generate_report_content(sample_analysis_result)
        
        # Verify content
        assert isinstance(content, ReportContent)
        assert content.summary is not None
        assert len(content.summary) > 50
        assert content.trend_section is not None
        assert content.tech_section is not None
        assert content.competition_section is not None
        assert content.conclusions is not None
        assert content.methodology is not None
        assert content.limitations is not None
    
    @pytest.mark.asyncio
    async def test_generate_summary(self, report_agent, sample_analysis_result):
        """Test summary generation."""
        # Generate summary
        summary = await report_agent._generate_summary(sample_analysis_result)
        
        # Verify summary
        assert isinstance(summary, str)
        assert len(summary) > 50
        assert str(sample_analysis_result.total_patents_analyzed) in summary
        assert f"{sample_analysis_result.confidence_level:.1%}" in summary
        
        # Should contain insights
        for insight in sample_analysis_result.insights[:3]:
            assert insight in summary
    
    @pytest.mark.asyncio
    async def test_generate_trend_section(self, report_agent):
        """Test trend section generation."""
        # Mock trend analysis
        trend_analysis = TrendAnalysisModel(
            yearly_counts={2020: 10, 2021: 15, 2022: 20},
            growth_rates={2021: 0.5, 2022: 0.33},
            trend_direction="increasing",
            peak_year=2022,
            total_patents=45,
            average_annual_growth=0.42
        )
        
        # Generate trend section
        section = await report_agent._generate_trend_section(trend_analysis)
        
        # Verify section
        assert isinstance(section, str)
        assert "专利申请趋势分析" in section
        assert "总体趋势" in section
        assert "年度分布" in section
        assert str(trend_analysis.total_patents) in section
        assert "increasing" in section
        
        # Should contain yearly data
        for year, count in trend_analysis.yearly_counts.items():
            assert f"{year}年: {count} 件" in section
    
    @pytest.mark.asyncio
    async def test_generate_tech_section(self, report_agent):
        """Test technology section generation."""
        # Mock tech classification
        tech_classification = TechClassificationModel(
            ipc_distribution={"G06F": 30, "H04L": 20, "G06N": 15},
            keyword_clusters=[],
            main_technologies=["G06F (30 patents)", "H04L (20 patents)"]
        )
        
        # Generate tech section
        section = await report_agent._generate_tech_section(tech_classification)
        
        # Verify section
        assert isinstance(section, str)
        assert "技术分类分析" in section
        assert "IPC分类分布" in section
        assert "主要技术领域" in section
        
        # Should contain IPC data
        for ipc, count in tech_classification.ipc_distribution.items():
            assert f"{ipc}: {count} 件" in section
    
    @pytest.mark.asyncio
    async def test_generate_competition_section(self, report_agent):
        """Test competition section generation."""
        # Mock competition analysis
        competition_analysis = CompetitionAnalysisModel(
            applicant_distribution={},
            top_applicants=[("Company A", 25), ("Company B", 18)],
            market_concentration=0.42,
            hhi_index=0.18
        )
        
        # Generate competition section
        section = await report_agent._generate_competition_section(competition_analysis)
        
        # Verify section
        assert isinstance(section, str)
        assert "竞争格局分析" in section
        assert "市场集中度" in section
        assert "主要申请人" in section
        assert "0.42" in section
        assert "0.18" in section
        
        # Should contain applicant data
        for applicant, count in competition_analysis.top_applicants:
            assert f"{applicant}: {count} 件" in section
    
    @pytest.mark.asyncio
    async def test_generate_conclusions(self, report_agent, sample_analysis_result):
        """Test conclusions generation."""
        # Generate conclusions
        conclusions = await report_agent._generate_conclusions(sample_analysis_result)
        
        # Verify conclusions
        assert isinstance(conclusions, str)
        assert "结论与建议" in conclusions
        assert "主要结论" in conclusions
        assert "建议" in conclusions
        
        # Should contain insights and recommendations
        for insight in sample_analysis_result.insights:
            assert insight in conclusions
        
        for recommendation in sample_analysis_result.recommendations:
            assert recommendation in conclusions
    
    @pytest.mark.asyncio
    async def test_render_html_report(self, report_agent, patent_request):
        """Test HTML report rendering."""
        # Mock report content
        content = ReportContent(
            summary="Test summary",
            trend_section="Test trend section",
            tech_section="Test tech section",
            competition_section="Test competition section",
            conclusions="Test conclusions",
            methodology="Test methodology",
            limitations="Test limitations"
        )
        
        charts = {
            'trend_chart': '<div>Trend Chart</div>',
            'tech_pie_chart': '<div>Tech Chart</div>',
            'competition_bar_chart': '<div>Competition Chart</div>'
        }
        
        # Render HTML report
        html_content = await report_agent._render_html_report(content, charts, patent_request)
        
        # Verify HTML content
        assert isinstance(html_content, str)
        assert "<!DOCTYPE html>" in html_content
        assert "<html" in html_content
        assert "专利分析报告" in html_content
        assert ', '.join(patent_request.keywords) in html_content
        
        # Should contain all sections
        assert content.summary in html_content
        assert content.trend_section in html_content
        assert content.tech_section in html_content
        assert content.competition_section in html_content
        assert content.conclusions in html_content
        
        # Should contain charts
        for chart in charts.values():
            assert chart in html_content
    
    @pytest.mark.asyncio
    async def test_generate_pdf_report(self, report_agent):
        """Test PDF report generation."""
        html_content = "<html><body><h1>Test Report</h1></body></html>"
        
        # Generate PDF
        pdf_content = await report_agent._generate_pdf_report(html_content)
        
        # Verify PDF (mock implementation returns bytes)
        assert pdf_content is not None
        assert isinstance(pdf_content, bytes)
        assert len(pdf_content) > 0
    
    @pytest.mark.asyncio
    async def test_validate_report_quality(self, report_agent):
        """Test report quality validation."""
        # Create test report
        report = Report(
            report_id="test-report",
            request_id="test-request",
            html_content="<html>" + "x" * 2000 + "</html>",  # Long content
            pdf_content=b"PDF content",
            charts={'chart1': 'content1', 'chart2': 'content2'},
            summary="This is a comprehensive summary with sufficient detail.",
            generation_date=datetime.now()
        )
        
        # Validate quality
        quality_score = await report_agent._validate_report_quality(report)
        
        # Verify quality score
        assert 0.0 <= quality_score <= 1.0
        assert quality_score > 0.8  # Should be high quality with all components
    
    @pytest.mark.asyncio
    async def test_validate_report_quality_low(self, report_agent):
        """Test report quality validation with low quality report."""
        # Create low quality report
        report = Report(
            report_id="test-report",
            request_id="test-request",
            html_content="<html>Short</html>",  # Short content
            pdf_content=None,  # No PDF
            charts={},  # No charts
            summary="Short",  # Short summary
            generation_date=datetime.now()
        )
        
        # Validate quality
        quality_score = await report_agent._validate_report_quality(report)
        
        # Verify quality score
        assert 0.0 <= quality_score <= 1.0
        assert quality_score < 0.5  # Should be low quality
    
    @pytest.mark.asyncio
    async def test_generate_response_content_success(self, report_agent):
        """Test response content generation for successful report."""
        result = {
            "status": "completed",
            "report_id": "report-123",
            "quality_score": 0.92,
            "processing_time": 3.5,
            "file_size": 15360,  # 15KB
            "formats_generated": ["html", "pdf"]
        }
        
        # Generate response content
        content = await report_agent._generate_response_content(result)
        
        # Verify content
        assert "专利分析报告生成完成" in content
        assert "report-123" in content
        assert "0.92/1.0" in content
        assert "3.5秒" in content
        assert "15.0 KB" in content
        assert "html, pdf" in content
    
    @pytest.mark.asyncio
    async def test_generate_response_content_failure(self, report_agent):
        """Test response content generation for failed report."""
        result = {
            "status": "failed",
            "report_id": "report-456",
            "error": "Analysis data not available"
        }
        
        # Generate response content
        content = await report_agent._generate_response_content(result)
        
        # Verify error content
        assert "报告生成失败" in content
        assert "report-456" in content
        assert "Analysis data not available" in content


class TestPatentReportAgentErrorHandling:
    """Test error handling in PatentReportAgent."""
    
    @pytest.mark.asyncio
    async def test_process_request_no_analysis_result(self, report_agent, patent_request):
        """Test processing request when no analysis result is available."""
        # Mock methods
        report_agent._get_from_cache = AsyncMock(return_value=None)
        report_agent._get_analysis_result = AsyncMock(return_value=None)
        
        # Process request
        result = await report_agent._process_patent_request(patent_request)
        
        # Should fail with no analysis result
        assert result["status"] == "failed"
        assert "No analysis result available" in result["error"]
    
    @pytest.mark.asyncio
    async def test_chart_generation_failure(self, report_agent, sample_analysis_result):
        """Test handling of chart generation failures."""
        # Mock chart generation to fail
        report_agent._create_trend_chart = AsyncMock(side_effect=Exception("Chart generation failed"))
        
        # Generate charts (should handle exception gracefully)
        charts = await report_agent._generate_charts(sample_analysis_result)
        
        # Should return empty or partial charts
        assert isinstance(charts, dict)
        # May have some charts that succeeded
    
    @pytest.mark.asyncio
    async def test_pdf_generation_failure(self, report_agent):
        """Test handling of PDF generation failures."""
        html_content = "<html><body>Test</body></html>"
        
        # Mock PDF generation to fail
        with patch.object(report_agent, '_generate_pdf_report', side_effect=Exception("PDF failed")):
            pdf_content = await report_agent._generate_pdf_report(html_content)
        
        # Should return None on failure
        assert pdf_content is None
    
    @pytest.mark.asyncio
    async def test_missing_analysis_components(self, report_agent, patent_request):
        """Test handling when analysis result has missing components."""
        # Create incomplete analysis result
        incomplete_result = PatentAnalysisResult(
            request_id=patent_request.request_id,
            analysis_date=datetime.now(),
            trend_analysis=None,  # Missing
            tech_classification=None,  # Missing
            competition_analysis=None,  # Missing
            insights=[],
            recommendations=[],
            total_patents_analyzed=0
        )
        
        # Mock methods
        report_agent._get_from_cache = AsyncMock(return_value=None)
        report_agent._save_to_cache = AsyncMock()
        report_agent._get_analysis_result = AsyncMock(return_value=incomplete_result)
        
        # Process request
        result = await report_agent._process_patent_request(patent_request)
        
        # Should still complete but with lower quality
        assert result["status"] == "completed"
        assert result["quality_score"] < 0.5  # Lower quality due to missing components


if __name__ == "__main__":
    pytest.main([__file__, "-v"])