"""专利数据模型和验证框架."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Union
from uuid import uuid4
import hashlib
import re

from pydantic import BaseModel, Field, field_validator, computed_field, ConfigDict, model_validator

from ...models.base import Entity


class PatentApplicant(BaseModel):
    """专利申请人模型."""
    
    name: str = Field(..., description="申请人名称")
    normalized_name: str = Field(..., description="标准化名称")
    country: Optional[str] = Field(None, description="国家/地区")
    applicant_type: Optional[str] = Field(None, description="申请人类型(个人/企业)")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """验证申请人名称."""
        if not v or len(v.strip()) < 2:
            raise ValueError('申请人名称不能为空且长度至少为2个字符')
        return v.strip()
    
    @field_validator('normalized_name')
    @classmethod
    def validate_normalized_name(cls, v):
        """验证标准化名称."""
        if not v or len(v.strip()) < 2:
            raise ValueError('标准化名称不能为空且长度至少为2个字符')
        return v.strip()


class PatentInventor(BaseModel):
    """专利发明人模型."""
    
    name: str = Field(..., description="发明人姓名")
    normalized_name: str = Field(..., description="标准化姓名")
    country: Optional[str] = Field(None, description="国家/地区")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """验证发明人姓名."""
        if not v or len(v.strip()) < 2:
            raise ValueError('发明人姓名不能为空且长度至少为2个字符')
        return v.strip()


class PatentClassification(BaseModel):
    """专利分类模型."""
    
    ipc_class: Optional[str] = Field(None, description="IPC分类号")
    cpc_class: Optional[str] = Field(None, description="CPC分类号")
    national_class: Optional[str] = Field(None, description="国家分类号")
    description: Optional[str] = Field(None, description="分类描述")
    
    @field_validator('ipc_class')
    @classmethod
    def validate_ipc_class(cls, v):
        """验证IPC分类号格式."""
        if v and not re.match(r'^[A-H]\d{2}[A-Z]\s*\d+/\d+', v):
            raise ValueError('IPC分类号格式不正确')
        return v


class PatentData(BaseModel):
    """专利数据模型."""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    # 基本信息
    patent_id: str = Field(default_factory=lambda: str(uuid4()), description="内部专利ID")
    application_number: str = Field(..., description="申请号")
    publication_number: Optional[str] = Field(None, description="公开号")
    title: str = Field(..., description="专利标题")
    abstract: str = Field(..., description="专利摘要")
    
    # 申请人和发明人
    applicants: List[Union[PatentApplicant, str]] = Field(default_factory=list, description="申请人列表")
    inventors: List[Union[PatentInventor, str]] = Field(default_factory=list, description="发明人列表")
    
    # 日期信息
    application_date: datetime = Field(..., description="申请日期")
    publication_date: Optional[datetime] = Field(None, description="公开日期")
    grant_date: Optional[datetime] = Field(None, description="授权日期")
    
    # 分类信息
    classifications: List[PatentClassification] = Field(default_factory=list, description="分类信息")
    ipc_classes: List[str] = Field(default_factory=list, description="IPC分类列表")
    
    # 地理信息
    country: str = Field(..., description="申请国家/地区")
    priority_countries: List[str] = Field(default_factory=list, description="优先权国家")
    
    # 状态信息
    status: str = Field(..., description="专利状态")
    legal_status: Optional[str] = Field(None, description="法律状态")
    
    # 技术信息
    technical_field: Optional[str] = Field(None, description="技术领域")
    keywords: List[str] = Field(default_factory=list, description="关键词")
    
    # 数据来源和质量
    data_source: str = Field(..., description="数据来源")
    data_quality_score: float = Field(default=0.0, ge=0.0, le=1.0, description="数据质量评分")
    collection_timestamp: datetime = Field(default_factory=datetime.now, description="收集时间戳")
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    
    @field_validator('application_number')
    @classmethod
    def validate_application_number(cls, v):
        """验证申请号格式."""
        if not v or len(v.strip()) < 3:  # 降低最小长度要求
            raise ValueError('申请号不能为空且长度至少为3个字符')
        return v.strip()
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        """验证专利标题."""
        if not v or len(v.strip()) < 2:  # 降低最小长度要求
            raise ValueError('专利标题不能为空且长度至少为2个字符')
        if len(v.strip()) > 500:
            raise ValueError('专利标题长度不能超过500个字符')
        return v.strip()
    
    @field_validator('abstract')
    @classmethod
    def validate_abstract(cls, v):
        """验证专利摘要."""
        if not v or len(v.strip()) < 5:  # 降低最小长度要求
            raise ValueError('专利摘要不能为空且长度至少为5个字符')
        if len(v.strip()) > 5000:
            raise ValueError('专利摘要长度不能超过5000个字符')
        return v.strip()
    
    @field_validator('country')
    @classmethod
    def validate_country(cls, v):
        """验证国家代码."""
        if not v or len(v.strip()) < 2:
            raise ValueError('国家代码不能为空且长度至少为2个字符')
        return v.strip().upper()
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """验证专利状态."""
        # 支持中文和英文状态
        valid_statuses_cn = ['申请中', '已公开', '已授权', '已失效', '已撤回', '已驳回']
        valid_statuses_en = ['pending', 'published', 'granted', 'expired', 'withdrawn', 'rejected']
        
        # 英文到中文的映射
        status_mapping = {
            'pending': '申请中',
            'published': '已公开', 
            'granted': '已授权',
            'expired': '已失效',
            'withdrawn': '已撤回',
            'rejected': '已驳回'
        }
        
        # 如果是英文状态，转换为中文
        if v.lower() in status_mapping:
            return status_mapping[v.lower()]
        
        # 检查是否为有效的中文状态
        if v in valid_statuses_cn:
            return v
            
        # 都不匹配则报错
        all_valid = valid_statuses_cn + valid_statuses_en
        raise ValueError(f'专利状态必须是以下之一: {all_valid}')
        
        return v
    
    @model_validator(mode='before')
    @classmethod
    def convert_string_fields(cls, values):
        """转换字符串字段为对象."""
        if isinstance(values, dict):
            # 转换申请人字符串为对象
            if 'applicants' in values and values['applicants']:
                converted_applicants = []
                for applicant in values['applicants']:
                    if isinstance(applicant, str):
                        converted_applicants.append(PatentApplicant(
                            name=applicant,
                            normalized_name=applicant
                        ))
                    else:
                        converted_applicants.append(applicant)
                values['applicants'] = converted_applicants
            
            # 转换发明人字符串为对象
            if 'inventors' in values and values['inventors']:
                converted_inventors = []
                for inventor in values['inventors']:
                    if isinstance(inventor, str):
                        converted_inventors.append(PatentInventor(
                            name=inventor,
                            normalized_name=inventor
                        ))
                    else:
                        converted_inventors.append(inventor)
                values['inventors'] = converted_inventors
        
        return values
    
    @computed_field
    @property
    def content_hash(self) -> str:
        """计算内容哈希值用于去重."""
        content = f"{self.application_number}|{self.title}|{self.abstract}|{self.application_date.isoformat()}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    @computed_field
    @property
    def similarity_hash(self) -> str:
        """计算相似性哈希值用于近似去重."""
        # 使用标题和摘要的关键部分
        title_words = set(self.title.lower().split())
        abstract_words = set(self.abstract.lower().split()[:50])  # 只取前50个词
        combined_words = sorted(title_words.union(abstract_words))
        content = '|'.join(combined_words)
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def calculate_quality_score(self) -> float:
        """计算数据质量评分."""
        score = 0.0
        max_score = 10.0
        
        # 基本信息完整性 (30%)
        if self.application_number:
            score += 1.0
        if self.title and len(self.title) >= 10:
            score += 1.0
        if self.abstract and len(self.abstract) >= 50:
            score += 1.0
        
        # 申请人和发明人信息 (20%)
        if self.applicants:
            score += 1.0
        if self.inventors:
            score += 1.0
        
        # 日期信息 (20%)
        if self.application_date:
            score += 1.0
        if self.publication_date:
            score += 1.0
        
        # 分类信息 (20%)
        if self.classifications:
            score += 1.0
        if self.technical_field:
            score += 1.0
        
        # 其他信息 (10%)
        if self.keywords:
            score += 0.5
        if self.country:
            score += 0.5
        
        return min(score / max_score, 1.0)
    
    def normalize_data(self) -> 'PatentData':
        """标准化数据."""
        # 标准化申请人名称
        for applicant in self.applicants:
            applicant.normalized_name = self._normalize_name(applicant.name)
        
        # 标准化发明人名称
        for inventor in self.inventors:
            inventor.normalized_name = self._normalize_name(inventor.name)
        
        # 标准化关键词
        self.keywords = [kw.strip().lower() for kw in self.keywords if kw.strip()]
        
        # 更新质量评分
        self.data_quality_score = self.calculate_quality_score()
        
        return self
    
    def _normalize_name(self, name: str) -> str:
        """标准化名称."""
        # 移除多余空格
        name = re.sub(r'\s+', ' ', name.strip())
        
        # 统一公司后缀
        company_suffixes = {
            '有限公司': 'Co., Ltd.',
            '股份有限公司': 'Co., Ltd.',
            '科技有限公司': 'Technology Co., Ltd.',
            'Inc.': 'Inc.',
            'Corp.': 'Corp.',
            'LLC': 'LLC'
        }
        
        for chinese, english in company_suffixes.items():
            if name.endswith(chinese):
                name = name.replace(chinese, english)
        
        return name


class PatentDataset(BaseModel):
    """专利数据集模型."""
    
    dataset_id: str = Field(default_factory=lambda: str(uuid4()), description="数据集ID")
    patents: List[PatentData] = Field(default_factory=list, description="专利数据列表")
    total_count: int = Field(default=0, description="总数量")
    search_keywords: List[str] = Field(default_factory=list, description="搜索关键词")
    collection_date: datetime = Field(default_factory=datetime.now, description="收集日期")
    data_sources: List[str] = Field(default_factory=list, description="数据来源列表")
    quality_metrics: Dict[str, Any] = Field(default_factory=dict, description="质量指标")
    
    def add_patent(self, patent: PatentData) -> bool:
        """添加专利数据."""
        # 标准化数据
        patent.normalize_data()
        
        # 检查重复
        if not self._is_duplicate(patent):
            self.patents.append(patent)
            self.total_count = len(self.patents)
            return True
        return False
    
    def _is_duplicate(self, patent: PatentData) -> bool:
        """检查是否重复."""
        for existing_patent in self.patents:
            if existing_patent.content_hash == patent.content_hash:
                return True
            # 检查相似性哈希
            if existing_patent.similarity_hash == patent.similarity_hash:
                return True
        return False
    
    def remove_duplicates(self) -> int:
        """移除重复数据，返回移除的数量."""
        seen_hashes = set()
        unique_patents = []
        removed_count = 0
        
        for patent in self.patents:
            if patent.content_hash not in seen_hashes:
                seen_hashes.add(patent.content_hash)
                unique_patents.append(patent)
            else:
                removed_count += 1
        
        self.patents = unique_patents
        self.total_count = len(self.patents)
        return removed_count
    
    def calculate_quality_metrics(self) -> Dict[str, Any]:
        """计算质量指标."""
        if not self.patents:
            return {}
        
        quality_scores = [patent.data_quality_score for patent in self.patents]
        
        metrics = {
            'total_patents': len(self.patents),
            'average_quality_score': sum(quality_scores) / len(quality_scores),
            'min_quality_score': min(quality_scores),
            'max_quality_score': max(quality_scores),
            'high_quality_count': len([s for s in quality_scores if s >= 0.8]),
            'medium_quality_count': len([s for s in quality_scores if 0.5 <= s < 0.8]),
            'low_quality_count': len([s for s in quality_scores if s < 0.5]),
            'data_sources': list(set(patent.data_source for patent in self.patents)),
            'countries': list(set(patent.country for patent in self.patents)),
            'status_distribution': self._get_status_distribution(),
            'collection_period': {
                'start': min(patent.collection_timestamp for patent in self.patents).isoformat(),
                'end': max(patent.collection_timestamp for patent in self.patents).isoformat()
            }
        }
        
        self.quality_metrics = metrics
        return metrics
    
    def _get_status_distribution(self) -> Dict[str, int]:
        """获取状态分布."""
        status_count = {}
        for patent in self.patents:
            status_count[patent.status] = status_count.get(patent.status, 0) + 1
        return status_count
    
    def filter_by_quality(self, min_score: float = 0.5) -> 'PatentDataset':
        """按质量评分过滤."""
        filtered_patents = [p for p in self.patents if p.data_quality_score >= min_score]
        
        new_dataset = PatentDataset(
            patents=filtered_patents,
            total_count=len(filtered_patents),
            search_keywords=self.search_keywords,
            collection_date=self.collection_date,
            data_sources=self.data_sources
        )
        new_dataset.calculate_quality_metrics()
        return new_dataset


class PatentAnalysisRequest(BaseModel):
    """专利分析请求模型."""
    
    request_id: str = Field(default_factory=lambda: str(uuid4()), description="请求ID")
    keywords: List[str] = Field(..., description="搜索关键词")
    countries: List[str] = Field(default_factory=list, description="目标国家")
    date_range: Optional[Dict[str, str]] = Field(None, description="日期范围")
    limit: int = Field(default=100, ge=1, le=10000, description="结果数量限制")
    quality_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="质量阈值")
    include_similar: bool = Field(default=True, description="是否包含相似专利")
    analysis_types: List[str] = Field(default_factory=list, description="分析类型")
    
    @field_validator('keywords')
    @classmethod
    def validate_keywords(cls, v):
        """验证关键词."""
        if not v or len(v) == 0:
            raise ValueError('至少需要一个搜索关键词')
        return [kw.strip() for kw in v if kw.strip()]


class PatentAnalysisResult(BaseModel):
    """专利分析结果模型."""
    
    result_id: str = Field(default_factory=lambda: str(uuid4()), description="结果ID")
    request_id: str = Field(..., description="请求ID")
    dataset: PatentDataset = Field(..., description="专利数据集")
    analysis_summary: Dict[str, Any] = Field(default_factory=dict, description="分析摘要")
    trend_analysis: Dict[str, Any] = Field(default_factory=dict, description="趋势分析")
    competition_analysis: Dict[str, Any] = Field(default_factory=dict, description="竞争分析")
    technology_analysis: Dict[str, Any] = Field(default_factory=dict, description="技术分析")
    geographic_analysis: Dict[str, Any] = Field(default_factory=dict, description="地理分析")
    insights: List[str] = Field(default_factory=list, description="洞察和建议")
    processing_time: float = Field(default=0.0, description="处理时间(秒)")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    
    def generate_summary(self) -> Dict[str, Any]:
        """生成分析摘要."""
        summary = {
            'total_patents': self.dataset.total_count,
            'quality_metrics': self.dataset.quality_metrics,
            'processing_time': self.processing_time,
            'analysis_types': list(self.trend_analysis.keys()) + 
                            list(self.competition_analysis.keys()) + 
                            list(self.technology_analysis.keys()),
            'key_insights_count': len(self.insights),
            'created_at': self.created_at.isoformat()
        }
        
        self.analysis_summary = summary
        return summary


class DataQualityReport(BaseModel):
    """数据质量报告模型."""
    
    report_id: str = Field(default_factory=lambda: str(uuid4()), description="报告ID")
    dataset_id: str = Field(..., description="数据集ID")
    total_records: int = Field(..., description="总记录数")
    valid_records: int = Field(..., description="有效记录数")
    invalid_records: int = Field(..., description="无效记录数")
    duplicate_records: int = Field(..., description="重复记录数")
    quality_score: float = Field(..., description="整体质量评分")
    
    # 详细质量指标
    completeness_score: float = Field(..., description="完整性评分")
    accuracy_score: float = Field(..., description="准确性评分")
    consistency_score: float = Field(..., description="一致性评分")
    
    # 问题统计
    missing_fields: Dict[str, int] = Field(default_factory=dict, description="缺失字段统计")
    invalid_formats: Dict[str, int] = Field(default_factory=dict, description="格式错误统计")
    data_anomalies: List[str] = Field(default_factory=list, description="数据异常列表")
    
    # 建议
    recommendations: List[str] = Field(default_factory=list, description="改进建议")
    
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    
    def add_recommendation(self, recommendation: str):
        """添加改进建议."""
        if recommendation not in self.recommendations:
            self.recommendations.append(recommendation)
    
    def calculate_overall_score(self) -> float:
        """计算整体质量评分."""
        self.quality_score = (
            self.completeness_score * 0.4 + 
            self.accuracy_score * 0.4 + 
            self.consistency_score * 0.2
        )
        return self.quality_score