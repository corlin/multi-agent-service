"""Patent data models."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


@dataclass
class Patent:
    """专利数据模型."""
    application_number: str
    title: str
    abstract: str
    applicants: List[str]
    inventors: List[str]
    application_date: datetime
    publication_date: Optional[datetime]
    ipc_classes: List[str]
    country: str
    status: str
    priority_date: Optional[datetime] = None
    grant_date: Optional[datetime] = None
    family_id: Optional[str] = None
    citations: List[str] = None
    
    def __post_init__(self):
        if self.citations is None:
            self.citations = []


@dataclass
class PatentDataset:
    """专利数据集."""
    patents: List[Patent]
    total_count: int
    search_keywords: List[str]
    collection_date: datetime
    data_sources: List[str]
    quality_score: float = 0.0
    
    def get_patents_by_year(self, year: int) -> List[Patent]:
        """获取指定年份的专利."""
        return [p for p in self.patents if p.application_date.year == year]
    
    def get_patents_by_applicant(self, applicant: str) -> List[Patent]:
        """获取指定申请人的专利."""
        return [p for p in self.patents if applicant in p.applicants]
    
    def get_patents_by_ipc(self, ipc_class: str) -> List[Patent]:
        """获取指定IPC分类的专利."""
        return [p for p in self.patents if ipc_class in p.ipc_classes]


class PatentDataSource(BaseModel):
    """专利数据源配置."""
    name: str = Field(..., description="数据源名称")
    base_url: str = Field(..., description="API基础URL")
    api_key: Optional[str] = Field(None, description="API密钥")
    rate_limit: int = Field(10, description="速率限制(请求/秒)")
    timeout: int = Field(30, description="超时时间(秒)")
    max_results: int = Field(1000, description="最大结果数")
    enabled: bool = Field(True, description="是否启用")
    priority: int = Field(1, description="优先级")
    
    
class PatentDataQuality(BaseModel):
    """专利数据质量指标."""
    completeness_score: float = Field(0.0, description="完整性评分")
    accuracy_score: float = Field(0.0, description="准确性评分")
    consistency_score: float = Field(0.0, description="一致性评分")
    timeliness_score: float = Field(0.0, description="时效性评分")
    overall_score: float = Field(0.0, description="总体评分")
    issues: List[str] = Field(default_factory=list, description="质量问题列表")
    
    def calculate_overall_score(self):
        """计算总体评分."""
        scores = [
            self.completeness_score,
            self.accuracy_score, 
            self.consistency_score,
            self.timeliness_score
        ]
        self.overall_score = sum(scores) / len(scores) if scores else 0.0
        return self.overall_score