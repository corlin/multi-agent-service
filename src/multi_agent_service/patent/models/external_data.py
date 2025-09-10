"""External data models for patent analysis."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


@dataclass
class WebPage:
    """网页数据模型."""
    
    url: str
    title: str
    content: str
    extracted_data: Dict[str, Any]
    crawl_date: datetime
    source_type: str = "web"  # web, forum, blog, news
    relevance_score: float = 0.0


class WebPageModel(BaseModel):
    """Pydantic model for web page."""
    
    url: str = Field(..., description="网页URL")
    title: str = Field(..., description="网页标题")
    content: str = Field(..., description="网页内容")
    extracted_data: Dict[str, Any] = Field(default_factory=dict, description="提取的数据")
    crawl_date: datetime = Field(default_factory=datetime.now, description="爬取日期")
    source_type: str = Field("web", description="来源类型")
    relevance_score: float = Field(0.0, description="相关性评分")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


@dataclass
class WebDataset:
    """网页数据集."""
    
    data: List[WebPage]
    sources: List[str]
    collection_date: datetime
    total_pages: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Post-initialization processing."""
        if self.metadata is None:
            self.metadata = {}
        if self.total_pages == 0:
            self.total_pages = len(self.data)


class WebDatasetModel(BaseModel):
    """Pydantic model for web dataset."""
    
    data: List[WebPageModel] = Field(default_factory=list, description="网页数据列表")
    sources: List[str] = Field(default_factory=list, description="数据源列表")
    collection_date: datetime = Field(default_factory=datetime.now, description="收集日期")
    total_pages: int = Field(0, description="网页总数")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


@dataclass
class Literature:
    """学术文献模型."""
    
    title: str
    authors: List[str]
    abstract: str
    keywords: List[str]
    publication_date: datetime
    journal: str
    doi: Optional[str] = None
    citation_count: int = 0
    relevance_score: float = 0.0


class LiteratureModel(BaseModel):
    """Pydantic model for literature."""
    
    title: str = Field(..., description="文献标题")
    authors: List[str] = Field(default_factory=list, description="作者列表")
    abstract: str = Field(..., description="摘要")
    keywords: List[str] = Field(default_factory=list, description="关键词")
    publication_date: datetime = Field(..., description="发表日期")
    journal: str = Field(..., description="期刊名称")
    doi: Optional[str] = Field(None, description="DOI")
    citation_count: int = Field(0, description="引用次数")
    relevance_score: float = Field(0.0, description="相关性评分")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


@dataclass
class CNKIData:
    """CNKI数据."""
    
    literature: List[Literature]
    concepts: List[Dict[str, Any]]
    search_metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Post-initialization processing."""
        if self.search_metadata is None:
            self.search_metadata = {}


class CNKIDataModel(BaseModel):
    """Pydantic model for CNKI data."""
    
    literature: List[LiteratureModel] = Field(default_factory=list, description="文献列表")
    concepts: List[Dict[str, Any]] = Field(default_factory=list, description="概念列表")
    search_metadata: Dict[str, Any] = Field(default_factory=dict, description="搜索元数据")


@dataclass
class BochaData:
    """博查AI数据."""
    
    web_results: List[Dict[str, Any]]
    ai_analysis: Dict[str, Any]
    search_metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Post-initialization processing."""
        if self.search_metadata is None:
            self.search_metadata = {}


class BochaDataModel(BaseModel):
    """Pydantic model for Bocha AI data."""
    
    web_results: List[Dict[str, Any]] = Field(default_factory=list, description="网页搜索结果")
    ai_analysis: Dict[str, Any] = Field(default_factory=dict, description="AI分析结果")
    search_metadata: Dict[str, Any] = Field(default_factory=dict, description="搜索元数据")


@dataclass
class EnhancedData:
    """增强数据."""
    
    academic_data: Optional[CNKIData]
    web_intelligence: Optional[BochaData]
    web_crawl_data: Optional[WebDataset] = None
    collection_date: datetime = None
    
    def __post_init__(self):
        """Post-initialization processing."""
        if self.collection_date is None:
            self.collection_date = datetime.now()


class EnhancedDataModel(BaseModel):
    """Pydantic model for enhanced data."""
    
    academic_data: Optional[CNKIDataModel] = Field(None, description="学术数据")
    web_intelligence: Optional[BochaDataModel] = Field(None, description="网络智能数据")
    web_crawl_data: Optional[WebDatasetModel] = Field(None, description="网页爬取数据")
    collection_date: datetime = Field(default_factory=datetime.now, description="收集日期")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }