"""Patent analysis request models."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from ...models.base import UserRequest


class PatentAnalysisRequest(UserRequest):
    """专利分析请求模型."""
    
    keywords: List[str] = Field(..., description="搜索关键词")
    analysis_types: List[str] = Field(
        default=["trend", "competition", "technology"], 
        description="分析类型列表"
    )
    date_range: Optional[Dict[str, str]] = Field(None, description="日期范围")
    countries: List[str] = Field(default_factory=list, description="国家/地区限制")
    ipc_classes: List[str] = Field(default_factory=list, description="IPC分类限制")
    max_patents: int = Field(1000, description="最大专利数量")
    include_citations: bool = Field(False, description="是否包含引用信息")
    language: str = Field("zh", description="报告语言")
    generate_report: bool = Field(True, description="是否生成报告")
    report_format: str = Field("html", description="报告格式")
    
    
class PatentDataCollectionRequest(BaseModel):
    """专利数据收集请求模型."""
    
    request_id: str = Field(..., description="请求ID")
    keywords: List[str] = Field(..., description="搜索关键词")
    max_patents: int = Field(1000, description="最大专利数量")
    data_sources: List[str] = Field(
        default=["google_patents", "patent_public_api"], 
        description="数据源列表"
    )
    date_range: Optional[Dict[str, str]] = Field(None, description="日期范围")
    countries: List[str] = Field(default_factory=list, description="国家/地区限制")
    ipc_classes: List[str] = Field(default_factory=list, description="IPC分类限制")
    include_abstracts: bool = Field(True, description="是否包含摘要")
    include_claims: bool = Field(False, description="是否包含权利要求")
    include_citations: bool = Field(False, description="是否包含引用信息")
    quality_threshold: float = Field(0.7, description="数据质量阈值")
    deduplication_enabled: bool = Field(True, description="是否启用去重")
    cache_enabled: bool = Field(True, description="是否启用缓存")
    cache_ttl: int = Field(3600, description="缓存TTL(秒)")
    parallel_sources: bool = Field(True, description="是否并行收集多个数据源")
    timeout: int = Field(300, description="超时时间(秒)")


class PatentSearchRequest(BaseModel):
    """专利搜索请求模型."""
    
    request_id: str = Field(..., description="请求ID")
    keywords: List[str] = Field(..., description="搜索关键词")
    search_types: List[str] = Field(
        default=["cnki", "bocha", "web_crawl"], 
        description="搜索类型列表"
    )
    max_results: int = Field(100, description="最大结果数量")
    language: str = Field("zh", description="搜索语言")
    enable_cnki: bool = Field(True, description="是否启用CNKI搜索")
    enable_bocha: bool = Field(True, description="是否启用博查AI搜索")
    enable_web_crawl: bool = Field(True, description="是否启用网页爬取")
    crawl_sites: List[str] = Field(default_factory=list, description="指定爬取网站")
    timeout: int = Field(180, description="超时时间(秒)")


class PatentReportRequest(BaseModel):
    """专利报告生成请求模型."""
    
    request_id: str = Field(..., description="请求ID")
    analysis_data: Dict[str, Any] = Field(..., description="分析数据")
    report_format: str = Field("html", description="报告格式")
    template_name: str = Field("comprehensive", description="报告模板")
    include_charts: bool = Field(True, description="是否包含图表")
    include_summary: bool = Field(True, description="是否包含摘要")
    language: str = Field("zh", description="报告语言")
    custom_sections: List[str] = Field(default_factory=list, description="自定义章节")
    export_pdf: bool = Field(False, description="是否导出PDF")
    timeout: int = Field(300, description="超时时间(秒)")