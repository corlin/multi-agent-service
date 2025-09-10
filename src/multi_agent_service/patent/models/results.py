"""Patent analysis result models."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from pydantic import BaseModel, Field


@dataclass
class TrendAnalysis:
    """趋势分析结果."""
    
    yearly_counts: Dict[int, int]
    growth_rates: Dict[int, float]
    trend_direction: str  # "increasing", "decreasing", "stable"
    peak_year: Optional[int] = None
    total_patents: int = 0
    average_annual_growth: float = 0.0
    forecast: Optional[Dict[int, int]] = None


class TrendAnalysisModel(BaseModel):
    """Pydantic model for trend analysis."""
    
    yearly_counts: Dict[int, int] = Field(default_factory=dict, description="年度专利数量")
    growth_rates: Dict[int, float] = Field(default_factory=dict, description="年度增长率")
    trend_direction: str = Field("", description="趋势方向")
    peak_year: Optional[int] = Field(None, description="峰值年份")
    total_patents: int = Field(0, description="专利总数")
    average_annual_growth: float = Field(0.0, description="平均年增长率")
    forecast: Optional[Dict[int, int]] = Field(None, description="预测数据")


@dataclass
class TechClassification:
    """技术分类结果."""
    
    ipc_distribution: Dict[str, int]
    keyword_clusters: List[Dict[str, Any]]
    main_technologies: List[str]
    technology_evolution: Optional[Dict[str, List[int]]] = None
    emerging_technologies: List[str] = None


class TechClassificationModel(BaseModel):
    """Pydantic model for technology classification."""
    
    ipc_distribution: Dict[str, int] = Field(default_factory=dict, description="IPC分类分布")
    keyword_clusters: List[Dict[str, Any]] = Field(default_factory=list, description="关键词聚类")
    main_technologies: List[str] = Field(default_factory=list, description="主要技术")
    technology_evolution: Optional[Dict[str, List[int]]] = Field(None, description="技术演进")
    emerging_technologies: List[str] = Field(default_factory=list, description="新兴技术")


@dataclass
class CompetitionAnalysis:
    """竞争分析结果."""
    
    applicant_distribution: Dict[str, int]
    top_applicants: List[Tuple[str, int]]
    market_concentration: float
    hhi_index: Optional[float] = None  # Herfindahl-Hirschman Index
    competitive_landscape: Optional[Dict[str, Any]] = None


class CompetitionAnalysisModel(BaseModel):
    """Pydantic model for competition analysis."""
    
    applicant_distribution: Dict[str, int] = Field(default_factory=dict, description="申请人分布")
    top_applicants: List[Tuple[str, int]] = Field(default_factory=list, description="顶级申请人")
    market_concentration: float = Field(0.0, description="市场集中度")
    hhi_index: Optional[float] = Field(None, description="HHI指数")
    competitive_landscape: Optional[Dict[str, Any]] = Field(None, description="竞争格局")


@dataclass
class GeographicAnalysis:
    """地域分析结果."""
    
    country_distribution: Dict[str, int]
    regional_trends: Dict[str, List[int]]
    top_countries: List[Tuple[str, int]]
    globalization_index: Optional[float] = None


class GeographicAnalysisModel(BaseModel):
    """Pydantic model for geographic analysis."""
    
    country_distribution: Dict[str, int] = Field(default_factory=dict, description="国家分布")
    regional_trends: Dict[str, List[int]] = Field(default_factory=dict, description="地区趋势")
    top_countries: List[Tuple[str, int]] = Field(default_factory=list, description="顶级国家")
    globalization_index: Optional[float] = Field(None, description="全球化指数")


class PatentAnalysisResult(BaseModel):
    """专利分析结果模型."""
    
    request_id: str = Field(..., description="请求ID")
    analysis_date: datetime = Field(default_factory=datetime.now, description="分析日期")
    
    # 分析结果
    trend_analysis: Optional[TrendAnalysisModel] = Field(None, description="趋势分析")
    tech_classification: Optional[TechClassificationModel] = Field(None, description="技术分类")
    competition_analysis: Optional[CompetitionAnalysisModel] = Field(None, description="竞争分析")
    geographic_analysis: Optional[GeographicAnalysisModel] = Field(None, description="地域分析")
    
    # 综合洞察
    insights: List[str] = Field(default_factory=list, description="分析洞察")
    recommendations: List[str] = Field(default_factory=list, description="建议")
    
    # 数据质量
    data_quality_score: float = Field(0.0, description="数据质量评分")
    confidence_level: float = Field(0.0, description="置信度")
    
    # 元数据
    total_patents_analyzed: int = Field(0, description="分析的专利总数")
    data_sources_used: List[str] = Field(default_factory=list, description="使用的数据源")
    processing_time: float = Field(0.0, description="处理时间(秒)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AnalysisStatus(BaseModel):
    """分析状态模型."""
    
    request_id: str = Field(..., description="请求ID")
    status: str = Field(..., description="状态")  # pending, running, completed, failed
    progress: float = Field(0.0, description="进度百分比")
    current_step: str = Field("", description="当前步骤")
    estimated_completion: Optional[datetime] = Field(None, description="预计完成时间")
    error_message: Optional[str] = Field(None, description="错误信息")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }