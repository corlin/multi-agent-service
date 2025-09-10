"""Clean tests for patent data models."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.multi_agent_service.patent.models.patent_data import (
    PatentApplicant, PatentInventor, PatentClassification, PatentData, 
    PatentDataset, DataQualityReport
)


class TestPatentApplicant:
    """Test PatentApplicant model."""
    
    def test_patent_applicant_creation(self):
        """Test creating a patent applicant."""
        applicant = PatentApplicant(
            name="Test Company Ltd",
            normalized_name="Test Company Ltd",
            country="US",
            applicant_type="company"
        )
        assert applicant.name == "Test Company Ltd"
        assert applicant.normalized_name == "Test Company Ltd"
        assert applicant.country == "US"
        assert applicant.applicant_type == "company"
    
    def test_patent_applicant_validation(self):
        """Test patent applicant validation."""
        with pytest.raises(ValidationError):
            PatentApplicant(name="", normalized_name="", country="US")


class TestPatentInventor:
    """Test PatentInventor model."""
    
    def test_patent_inventor_creation(self):
        """Test creating a patent inventor."""
        inventor = PatentInventor(
            name="John Doe",
            normalized_name="John Doe",
            country="US"
        )
        assert inventor.name == "John Doe"
        assert inventor.normalized_name == "John Doe"
        assert inventor.country == "US"


class TestPatentClassification:
    """Test PatentClassification model."""
    
    def test_patent_classification_creation(self):
        """Test creating a patent classification."""
        classification = PatentClassification(
            ipc_class="H04L 29/06",
            cpc_class="H04L63/0428"
        )
        assert classification.ipc_class == "H04L 29/06"
        assert classification.cpc_class == "H04L63/0428"


class TestPatentData:
    """Test PatentData model."""
    
    def test_patent_data_creation(self):
        """Test creating patent data."""
        applicant = PatentApplicant(
            name="Test Company", 
            normalized_name="Test Company", 
            country="US", 
            applicant_type="company"
        )
        inventor = PatentInventor(
            name="John Doe", 
            normalized_name="John Doe", 
            country="US"
        )
        classification = PatentClassification(ipc_class="H04L 29/06")
        
        patent = PatentData(
            application_number="US12345678",
            title="Test Patent Title",
            abstract="This is a test patent abstract with sufficient length for validation",
            applicants=[applicant],
            inventors=[inventor],
            application_date=datetime(2023, 1, 1),
            classifications=[classification],
            country="US",
            status="已公开",
            data_source="test"
        )
        
        assert patent.application_number == "US12345678"
        assert patent.title == "Test Patent Title"
        assert len(patent.applicants) == 1
        assert len(patent.inventors) == 1
        assert len(patent.classifications) == 1


class TestPatentDataset:
    """Test PatentDataset model."""
    
    def test_patent_dataset_creation(self):
        """Test creating a patent dataset."""
        dataset = PatentDataset(
            patents=[],
            total_count=0,
            search_keywords=["test", "patent"],
            collection_date=datetime.now()
        )
        
        assert len(dataset.patents) == 0
        assert dataset.total_count == 0
        assert dataset.search_keywords == ["test", "patent"]


class TestDataQualityReport:
    """Test DataQualityReport model."""
    
    def test_data_quality_report_creation(self):
        """Test creating a data quality report."""
        report = DataQualityReport(
            dataset_id="test-dataset",
            total_records=100,
            valid_records=95,
            invalid_records=5,
            duplicate_records=0,
            quality_score=0.95,
            completeness_score=0.95,
            accuracy_score=0.98,
            consistency_score=0.97
        )
        
        assert report.total_records == 100
        assert report.valid_records == 95
        assert report.invalid_records == 5
        assert report.completeness_score == 0.95