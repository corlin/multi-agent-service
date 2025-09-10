"""Patent analysis response models."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from ...models.base import AgentResponse
from .data import PatentDataset, PatentDataQuality


class PatentDataCollectionResponse(AgentResponse):
    """专利数据收集响应模型."""
    
    dataset: Optional[PatentDataset] = Field(None, description="专利数据集")
    collection_stats: Dict[str, Any] = Field(default_factory=dict, description="收集统计信息")
    data_quality: Optional[PatentDataQuality] = Field(None, description="数据质量评估")
    source_results: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="各数据源结果")
    processing_time: float = Field(0.0, description="处理时间(秒)")
    cache_used: bool = Field(False, description="是否使用了缓存")
    
    
class PatentSearchResponse(AgentResponse):
    """专利搜索响应模型."""
    
    search_results: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict, description="搜索结果")
    enhanced_data: Dict[str, Any] = Field(default_factory=dict, description="增强数据")
    source_stats: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="数据源统计")
    processing_time: float = Field(0.0, description="处理时间(秒)")
    cache_used: bool = Field(False, description="是否使用了缓存")


class PatentAnalysisResponse(AgentResponse):
    """专利分析响应模型."""
    
    analysis_results: Dict[str, Any] = Field(default_factory=dict, description="分析结果")
    trend_analysis: Optional[Dict[str, Any]] = Field(None, description="趋势分析")
    competition_analysis: Optional[Dict[str, Any]] = Field(None, description="竞争分析")
    technology_analysis: Optional[Dict[str, Any]] = Field(None, description="技术分析")
    geographic_analysis: Optional[Dict[str, Any]] = Field(None, description="地域分析")
    insights: List[str] = Field(default_factory=list, description="分析洞察")
    confidence_scores: Dict[str, float] = Field(default_factory=dict, description="置信度评分")
    processing_time: float = Field(0.0, description="处理时间(秒)")


class PatentReportResponse(AgentResponse):
    """专利报告响应模型."""
    
    report_id: str = Field(..., description="报告ID")
    report_content: str = Field(..., description="报告内容")
    report_format: str = Field(..., description="报告格式")
    charts: Dict[str, str] = Field(default_factory=dict, description="图表数据")
    file_path: Optional[str] = Field(None, description="文件路径")
    download_url: Optional[str] = Field(None, description="下载链接")
    generation_time: float = Field(0.0, description="生成时间(秒)")
    file_size: int = Field(0, description="文件大小(字节)")


class PatentCoordinationResponse(AgentResponse):
    """专利协调响应模型."""
    
    workflow_id: str = Field(..., description="工作流ID")
    coordination_results: Dict[str, Any] = Field(default_factory=dict, description="协调结果")
    agent_results: Dict[str, AgentResponse] = Field(default_factory=dict, description="各Agent结果")
    execution_timeline: List[Dict[str, Any]] = Field(default_factory=list, description="执行时间线")
    quality_metrics: Dict[str, float] = Field(default_factory=dict, description="质量指标")
    total_processing_time: float = Field(0.0, description="总处理时间(秒)")
    success_rate: float = Field(0.0, description="成功率")