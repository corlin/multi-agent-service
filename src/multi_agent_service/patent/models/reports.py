"""Report models for patent analysis."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


@dataclass
class ReportContent:
    """报告内容."""
    
    summary: str
    trend_section: str
    tech_section: str
    competition_section: str
    conclusions: str
    methodology: Optional[str] = None
    limitations: Optional[str] = None


class ReportContentModel(BaseModel):
    """Pydantic model for report content."""
    
    summary: str = Field(..., description="摘要")
    trend_section: str = Field(..., description="趋势分析部分")
    tech_section: str = Field(..., description="技术分析部分")
    competition_section: str = Field(..., description="竞争分析部分")
    conclusions: str = Field(..., description="结论")
    methodology: Optional[str] = Field(None, description="方法论")
    limitations: Optional[str] = Field(None, description="局限性")


@dataclass
class Report:
    """报告."""
    
    report_id: str
    request_id: str
    html_content: str
    pdf_content: Optional[bytes]
    charts: Dict[str, str]
    summary: str
    generation_date: datetime
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Post-initialization processing."""
        if self.metadata is None:
            self.metadata = {}


class ReportModel(BaseModel):
    """Pydantic model for report."""
    
    report_id: str = Field(..., description="报告ID")
    request_id: str = Field(..., description="请求ID")
    html_content: str = Field(..., description="HTML内容")
    pdf_content: Optional[bytes] = Field(None, description="PDF内容")
    charts: Dict[str, str] = Field(default_factory=dict, description="图表")
    summary: str = Field(..., description="摘要")
    generation_date: datetime = Field(default_factory=datetime.now, description="生成日期")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            bytes: lambda v: v.decode('utf-8') if v else None
        }


class ChartConfig(BaseModel):
    """图表配置模型."""
    
    chart_type: str = Field(..., description="图表类型")  # line, bar, pie, scatter
    title: str = Field(..., description="图表标题")
    x_label: Optional[str] = Field(None, description="X轴标签")
    y_label: Optional[str] = Field(None, description="Y轴标签")
    data: Dict[str, Any] = Field(..., description="图表数据")
    style: Dict[str, Any] = Field(default_factory=dict, description="样式配置")
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class ReportTemplate(BaseModel):
    """报告模板模型."""
    
    template_id: str = Field(..., description="模板ID")
    name: str = Field(..., description="模板名称")
    description: str = Field(..., description="模板描述")
    template_content: str = Field(..., description="模板内容")
    supported_formats: List[str] = Field(default_factory=list, description="支持的格式")
    variables: List[str] = Field(default_factory=list, description="模板变量")
    created_date: datetime = Field(default_factory=datetime.now, description="创建日期")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }