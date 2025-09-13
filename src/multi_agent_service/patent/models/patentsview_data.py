"""PatentsView API 数据模型."""

from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime


class PatentRecord(BaseModel):
    """专利记录模型."""
    
    patent_id: str = Field(..., description="专利ID")
    patent_number: Optional[str] = Field(None, description="专利号")
    patent_title: Optional[str] = Field(None, description="专利标题")
    patent_abstract: Optional[str] = Field(None, description="专利摘要")
    patent_date: Optional[str] = Field(None, description="专利日期")
    patent_type: Optional[str] = Field(None, description="专利类型")
    
    # 申请人信息
    assignee_organization: Optional[str] = Field(None, description="申请机构")
    assignee_country: Optional[str] = Field(None, description="申请人国家")
    
    # 发明人信息
    inventor_name_first: Optional[str] = Field(None, description="发明人名")
    inventor_name_last: Optional[str] = Field(None, description="发明人姓")
    
    # 分类信息
    ipc_class: Optional[str] = Field(None, description="IPC分类")
    cpc_class: Optional[str] = Field(None, description="CPC分类")
    
    class Config:
        """Pydantic 配置."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PatentSummary(BaseModel):
    """专利摘要模型."""
    
    patent_id: str = Field(..., description="专利ID")
    summary_text: str = Field(..., description="摘要文本")


class PatentClaim(BaseModel):
    """专利权利要求模型."""
    
    patent_id: str = Field(..., description="专利ID")
    claim_sequence: int = Field(..., description="权利要求序号")
    claim_text: str = Field(..., description="权利要求文本")


class PatentDescription(BaseModel):
    """专利说明书模型."""
    
    patent_id: str = Field(..., description="专利ID")
    description_text: str = Field(..., description="说明书文本")


class PatentDrawingDescription(BaseModel):
    """专利附图说明模型."""
    
    patent_id: str = Field(..., description="专利ID")
    draw_desc_sequence: int = Field(..., description="附图说明序号")
    draw_desc_text: str = Field(..., description="附图说明文本")


class PublicationRecord(BaseModel):
    """专利公开记录模型."""
    
    document_number: str = Field(..., description="文档号")
    publication_date: Optional[str] = Field(None, description="公开日期")
    publication_type: Optional[str] = Field(None, description="公开类型")
    title: Optional[str] = Field(None, description="标题")
    abstract: Optional[str] = Field(None, description="摘要")
    
    # 申请人信息
    assignee_organization: Optional[str] = Field(None, description="申请机构")
    assignee_country: Optional[str] = Field(None, description="申请人国家")
    
    # 发明人信息
    inventor_names: Optional[List[str]] = Field(None, description="发明人姓名列表")
    
    # 分类信息
    ipc_classes: Optional[List[str]] = Field(None, description="IPC分类列表")
    cpc_classes: Optional[List[str]] = Field(None, description="CPC分类列表")


class AssigneeRecord(BaseModel):
    """专利权人记录模型."""
    
    assignee_id: str = Field(..., description="专利权人ID")
    assignee_organization: Optional[str] = Field(None, description="机构名称")
    assignee_individual_name_first: Optional[str] = Field(None, description="个人名")
    assignee_individual_name_last: Optional[str] = Field(None, description="个人姓")
    assignee_country: Optional[str] = Field(None, description="国家")
    assignee_state: Optional[str] = Field(None, description="州/省")
    assignee_city: Optional[str] = Field(None, description="城市")


class InventorRecord(BaseModel):
    """发明人记录模型."""
    
    inventor_id: str = Field(..., description="发明人ID")
    inventor_name_first: Optional[str] = Field(None, description="名")
    inventor_name_last: Optional[str] = Field(None, description="姓")
    inventor_country: Optional[str] = Field(None, description="国家")
    inventor_state: Optional[str] = Field(None, description="州/省")
    inventor_city: Optional[str] = Field(None, description="城市")


class CPCClass(BaseModel):
    """CPC分类模型."""
    
    cpc_class: str = Field(..., description="CPC分类号")
    cpc_class_title: Optional[str] = Field(None, description="CPC分类标题")


class CPCSubclass(BaseModel):
    """CPC子分类模型."""
    
    cpc_subclass: str = Field(..., description="CPC子分类号")
    cpc_subclass_title: Optional[str] = Field(None, description="CPC子分类标题")


class CPCGroup(BaseModel):
    """CPC组分类模型."""
    
    cpc_group: str = Field(..., description="CPC组分类号")
    cpc_group_title: Optional[str] = Field(None, description="CPC组分类标题")


class IPCClass(BaseModel):
    """IPC分类模型."""
    
    ipc_class: str = Field(..., description="IPC分类号")
    ipc_class_title: Optional[str] = Field(None, description="IPC分类标题")


class USPCMainClass(BaseModel):
    """USPC主分类模型."""
    
    uspc_mainclass_id: str = Field(..., description="USPC主分类ID")
    uspc_mainclass_title: Optional[str] = Field(None, description="USPC主分类标题")


class USPCSubClass(BaseModel):
    """USPC子分类模型."""
    
    uspc_subclass_id: str = Field(..., description="USPC子分类ID")
    uspc_subclass_title: Optional[str] = Field(None, description="USPC子分类标题")


class WIPOClass(BaseModel):
    """WIPO分类模型."""
    
    wipo_id: str = Field(..., description="WIPO分类ID")
    wipo_field_title: Optional[str] = Field(None, description="WIPO领域标题")


class ForeignCitation(BaseModel):
    """外国引用模型."""
    
    patent_id: str = Field(..., description="专利ID")
    foreign_citation_sequence: int = Field(..., description="外国引用序号")
    foreign_citation_country: Optional[str] = Field(None, description="引用国家")
    foreign_citation_number: Optional[str] = Field(None, description="引用号")
    foreign_citation_date: Optional[str] = Field(None, description="引用日期")


class USApplicationCitation(BaseModel):
    """美国申请引用模型."""
    
    patent_id: str = Field(..., description="专利ID")
    us_application_citation_sequence: int = Field(..., description="美国申请引用序号")
    us_application_citation_number: Optional[str] = Field(None, description="美国申请引用号")
    us_application_citation_date: Optional[str] = Field(None, description="美国申请引用日期")


class USPatentCitation(BaseModel):
    """美国专利引用模型."""
    
    patent_id: str = Field(..., description="专利ID")
    us_patent_citation_sequence: int = Field(..., description="美国专利引用序号")
    us_patent_citation_number: Optional[str] = Field(None, description="美国专利引用号")
    us_patent_citation_date: Optional[str] = Field(None, description="美国专利引用日期")


class OtherReference(BaseModel):
    """其他引用模型."""
    
    patent_id: str = Field(..., description="专利ID")
    other_reference_sequence: int = Field(..., description="其他引用序号")
    other_reference_text: Optional[str] = Field(None, description="其他引用文本")


class LocationRecord(BaseModel):
    """地理位置记录模型."""
    
    location_id: str = Field(..., description="位置ID")
    city: Optional[str] = Field(None, description="城市")
    state: Optional[str] = Field(None, description="州/省")
    country: Optional[str] = Field(None, description="国家")
    latitude: Optional[float] = Field(None, description="纬度")
    longitude: Optional[float] = Field(None, description="经度")


class PatentsViewSearchResult(BaseModel):
    """PatentsView 搜索结果模型."""
    
    # 基础专利数据
    patents: List[PatentRecord] = Field(default_factory=list, description="专利记录列表")
    publications: List[PublicationRecord] = Field(default_factory=list, description="公开记录列表")
    
    # 文本数据
    patent_summaries: List[PatentSummary] = Field(default_factory=list, description="专利摘要列表")
    patent_claims: List[PatentClaim] = Field(default_factory=list, description="专利权利要求列表")
    patent_descriptions: List[PatentDescription] = Field(default_factory=list, description="专利说明书列表")
    patent_drawings: List[PatentDrawingDescription] = Field(default_factory=list, description="专利附图说明列表")
    
    # 实体数据
    assignees: List[AssigneeRecord] = Field(default_factory=list, description="专利权人列表")
    inventors: List[InventorRecord] = Field(default_factory=list, description="发明人列表")
    locations: List[LocationRecord] = Field(default_factory=list, description="地理位置列表")
    
    # 分类数据
    cpc_classes: List[CPCClass] = Field(default_factory=list, description="CPC分类列表")
    cpc_subclasses: List[CPCSubclass] = Field(default_factory=list, description="CPC子分类列表")
    cpc_groups: List[CPCGroup] = Field(default_factory=list, description="CPC组分类列表")
    ipc_classes: List[IPCClass] = Field(default_factory=list, description="IPC分类列表")
    uspc_mainclasses: List[USPCMainClass] = Field(default_factory=list, description="USPC主分类列表")
    uspc_subclasses: List[USPCSubClass] = Field(default_factory=list, description="USPC子分类列表")
    wipo_classes: List[WIPOClass] = Field(default_factory=list, description="WIPO分类列表")
    
    # 引用数据
    foreign_citations: List[ForeignCitation] = Field(default_factory=list, description="外国引用列表")
    us_application_citations: List[USApplicationCitation] = Field(default_factory=list, description="美国申请引用列表")
    us_patent_citations: List[USPatentCitation] = Field(default_factory=list, description="美国专利引用列表")
    other_references: List[OtherReference] = Field(default_factory=list, description="其他引用列表")
    
    # 元数据
    search_metadata: Dict[str, Any] = Field(default_factory=dict, description="搜索元数据")
    quality_metrics: Dict[str, float] = Field(default_factory=dict, description="质量指标")
    processing_info: Dict[str, Any] = Field(default_factory=dict, description="处理信息")
    
    class Config:
        """Pydantic 配置."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PatentsViewAPIResponse(BaseModel):
    """PatentsView API 响应模型."""
    
    # API 响应状态
    status: str = Field(..., description="响应状态")
    total_count: int = Field(0, description="总记录数")
    
    # 响应数据 (根据不同端点会有不同的字段)
    patents: Optional[List[Dict[str, Any]]] = Field(None, description="专利数据")
    publications: Optional[List[Dict[str, Any]]] = Field(None, description="公开数据")
    g_brf_sum_texts: Optional[List[Dict[str, Any]]] = Field(None, description="专利摘要文本")
    g_claims: Optional[List[Dict[str, Any]]] = Field(None, description="专利权利要求")
    g_detail_desc_texts: Optional[List[Dict[str, Any]]] = Field(None, description="专利详细说明")
    g_draw_desc_texts: Optional[List[Dict[str, Any]]] = Field(None, description="专利附图说明")
    
    pg_brf_sum_texts: Optional[List[Dict[str, Any]]] = Field(None, description="公开摘要文本")
    pg_claims: Optional[List[Dict[str, Any]]] = Field(None, description="公开权利要求")
    pg_detail_desc_texts: Optional[List[Dict[str, Any]]] = Field(None, description="公开详细说明")
    pg_draw_desc_texts: Optional[List[Dict[str, Any]]] = Field(None, description="公开附图说明")
    
    assignees: Optional[List[Dict[str, Any]]] = Field(None, description="专利权人数据")
    inventors: Optional[List[Dict[str, Any]]] = Field(None, description="发明人数据")
    locations: Optional[List[Dict[str, Any]]] = Field(None, description="地理位置数据")
    
    cpc_classes: Optional[List[Dict[str, Any]]] = Field(None, description="CPC分类数据")
    cpc_subclasses: Optional[List[Dict[str, Any]]] = Field(None, description="CPC子分类数据")
    cpc_groups: Optional[List[Dict[str, Any]]] = Field(None, description="CPC组分类数据")
    ipc_classes: Optional[List[Dict[str, Any]]] = Field(None, description="IPC分类数据")
    uspc_mainclasses: Optional[List[Dict[str, Any]]] = Field(None, description="USPC主分类数据")
    uspc_subclasses: Optional[List[Dict[str, Any]]] = Field(None, description="USPC子分类数据")
    wipo_classes: Optional[List[Dict[str, Any]]] = Field(None, description="WIPO分类数据")
    
    foreign_citations: Optional[List[Dict[str, Any]]] = Field(None, description="外国引用数据")
    us_application_citations: Optional[List[Dict[str, Any]]] = Field(None, description="美国申请引用数据")
    us_patent_citations: Optional[List[Dict[str, Any]]] = Field(None, description="美国专利引用数据")
    other_references: Optional[List[Dict[str, Any]]] = Field(None, description="其他引用数据")
    
    # 错误信息
    error: Optional[str] = Field(None, description="错误信息")
    error_code: Optional[str] = Field(None, description="错误代码")
    
    # 分页信息
    page: Optional[int] = Field(None, description="当前页")
    per_page: Optional[int] = Field(None, description="每页记录数")
    total_pages: Optional[int] = Field(None, description="总页数")
    
    class Config:
        """Pydantic 配置."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PatentsViewQuery(BaseModel):
    """PatentsView 查询模型."""
    
    # 查询条件
    query: Dict[str, Any] = Field(default_factory=dict, description="查询条件")
    
    # 返回字段
    fields: List[str] = Field(default_factory=list, description="返回字段列表")
    
    # 排序
    sort: List[Dict[str, str]] = Field(default_factory=list, description="排序条件")
    
    # 选项
    options: Dict[str, Any] = Field(default_factory=dict, description="查询选项")
    
    # 端点
    endpoint: str = Field(..., description="API端点")
    
    class Config:
        """Pydantic 配置."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }