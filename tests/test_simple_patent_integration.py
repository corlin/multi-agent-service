"""Simple patent integration test to verify setup."""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock


class TestSimplePatentIntegration:
    """Simple patent integration test."""
    
    def test_basic_import(self):
        """Test basic imports work."""
        try:
            from src.multi_agent_service.workflows.patent_workflow_engine import PatentWorkflowEngine
            from src.multi_agent_service.models.workflow import WorkflowExecution
            from src.multi_agent_service.models.enums import WorkflowStatus
            assert True
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")
    
    @pytest.mark.asyncio
    async def test_basic_workflow_creation(self):
        """Test basic workflow creation."""
        from src.multi_agent_service.workflows.patent_workflow_engine import PatentWorkflowEngine
        from src.multi_agent_service.models.workflow import WorkflowExecution
        from src.multi_agent_service.models.enums import WorkflowStatus
        
        # Create workflow engine
        engine = PatentWorkflowEngine()
        
        # Create simple execution
        execution = WorkflowExecution(
            graph_id="test_workflow",
            input_data={"test": "data"}
        )
        
        assert execution.graph_id == "test_workflow"
        assert execution.input_data["test"] == "data"
        assert execution.status == WorkflowStatus.PENDING
    
    def test_workflow_templates(self):
        """Test workflow templates are available."""
        from src.multi_agent_service.workflows.patent_workflow_engine import PatentWorkflowEngine
        
        engine = PatentWorkflowEngine()
        templates = engine.get_available_templates()
        
        assert len(templates) > 0
        assert "comprehensive_patent_analysis" in templates
        assert "quick_patent_search" in templates
        assert "patent_trend_analysis" in templates