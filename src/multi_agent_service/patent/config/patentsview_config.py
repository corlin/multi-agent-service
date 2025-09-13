"""PatentsView API 配置."""

import os
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

# 加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # 如果没有安装 python-dotenv，尝试手动加载
    env_file = ".env"
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value


class PatentsViewEndpointConfig(BaseModel):
    """PatentsView API 端点配置."""
    
    name: str = Field(..., description="端点名称")
    path: str = Field(..., description="端点路径")
    description: str = Field("", description="端点描述")
    default_fields: List[str] = Field(default_factory=list, description="默认返回字段")
    max_page_size: int = Field(1000, description="最大页面大小")
    supports_post: bool = Field(True, description="是否支持POST请求")


class PatentsViewAPIConfig(BaseModel):
    """PatentsView API 配置."""
    
    # API 基础配置
    base_url: str = Field("https://search.patentsview.org/api/v1", description="API基础URL")
    api_key: Optional[str] = Field(None, description="API密钥")
    
    # 请求配置
    timeout: int = Field(30, description="请求超时时间(秒)")
    max_retries: int = Field(3, description="最大重试次数")
    rate_limit_delay: float = Field(1.0, description="请求间隔(秒)")
    
    # 分页配置
    default_page_size: int = Field(100, description="默认页面大小")
    max_page_size: int = Field(1000, description="最大页面大小")
    
    # 缓存配置
    enable_cache: bool = Field(True, description="是否启用缓存")
    cache_ttl: int = Field(3600, description="缓存TTL(秒)")
    
    # 日志配置
    enable_request_logging: bool = Field(True, description="是否启用请求日志")
    log_level: str = Field("INFO", description="日志级别")
    
    @classmethod
    def from_env(cls) -> "PatentsViewAPIConfig":
        """从环境变量创建配置."""
        return cls(
            api_key=os.getenv("PATENT_VIEW_API_KEY"),
            base_url=os.getenv("PATENT_VIEW_BASE_URL", "https://search.patentsview.org/api/v1"),
            timeout=int(os.getenv("PATENT_VIEW_TIMEOUT", "30")),
            max_retries=int(os.getenv("PATENT_VIEW_MAX_RETRIES", "3")),
            rate_limit_delay=float(os.getenv("PATENT_VIEW_RATE_LIMIT_DELAY", "1.0")),
            default_page_size=int(os.getenv("PATENT_VIEW_DEFAULT_PAGE_SIZE", "100")),
            max_page_size=int(os.getenv("PATENT_VIEW_MAX_PAGE_SIZE", "1000")),
            enable_cache=os.getenv("PATENT_VIEW_ENABLE_CACHE", "true").lower() == "true",
            cache_ttl=int(os.getenv("PATENT_VIEW_CACHE_TTL", "3600")),
            enable_request_logging=os.getenv("PATENT_VIEW_ENABLE_REQUEST_LOGGING", "true").lower() == "true",
            log_level=os.getenv("PATENT_VIEW_LOG_LEVEL", "INFO")
        )


class PatentsViewEndpoints:
    """PatentsView API 端点定义."""
    
    # 专利文本相关端点
    PATENT_SUMMARY = PatentsViewEndpointConfig(
        name="patent_summary",
        path="/g_brf_sum_text/",
        description="专利摘要文本",
        default_fields=["patent_id", "summary_text"]
    )
    
    PATENT_CLAIMS = PatentsViewEndpointConfig(
        name="patent_claims",
        path="/g_claim/",
        description="专利权利要求",
        default_fields=["patent_id", "claim_sequence", "claim_text"]
    )
    
    PATENT_DESCRIPTION = PatentsViewEndpointConfig(
        name="patent_description",
        path="/g_detail_desc_text/",
        description="专利详细说明",
        default_fields=["patent_id", "description_text"]
    )
    
    PATENT_DRAWINGS = PatentsViewEndpointConfig(
        name="patent_drawings",
        path="/g_draw_desc_text/",
        description="专利附图说明",
        default_fields=["patent_id", "draw_desc_sequence", "draw_desc_text"]
    )
    
    # 发布文本相关端点
    PUBLICATION_SUMMARY = PatentsViewEndpointConfig(
        name="publication_summary",
        path="/pg_brf_sum_text/",
        description="发布摘要文本",
        default_fields=["document_number", "summary_text"]
    )
    
    PUBLICATION_CLAIMS = PatentsViewEndpointConfig(
        name="publication_claims",
        path="/pg_claim/",
        description="发布权利要求",
        default_fields=["document_number", "claim_sequence", "claim_text"]
    )
    
    PUBLICATION_DESCRIPTION = PatentsViewEndpointConfig(
        name="publication_description",
        path="/pg_detail_desc_text/",
        description="发布详细说明",
        default_fields=["document_number", "description_text"]
    )
    
    PUBLICATION_DRAWINGS = PatentsViewEndpointConfig(
        name="publication_drawings",
        path="/pg_draw_desc_text/",
        description="发布附图说明",
        default_fields=["document_number", "draw_desc_sequence", "draw_desc_text"]
    )
    
    # 专利信息相关端点
    PATENTS = PatentsViewEndpointConfig(
        name="patents",
        path="/patent/",
        description="专利基础信息",
        default_fields=[
            "patent_id", "patent_number", "patent_title", 
            "patent_abstract", "patent_date", "patent_type",
            "assignee_organization", "assignee_country",
            "inventor_name_first", "inventor_name_last",
            "ipc_class", "cpc_class"
        ]
    )
    
    PUBLICATIONS = PatentsViewEndpointConfig(
        name="publications",
        path="/publication/",
        description="专利发布信息",
        default_fields=[
            "document_number", "publication_date", "publication_type",
            "title", "abstract", "assignee_organization", "assignee_country"
        ]
    )
    
    ASSIGNEES = PatentsViewEndpointConfig(
        name="assignees",
        path="/assignee/",
        description="专利权人信息",
        default_fields=[
            "assignee_id", "assignee_organization", 
            "assignee_individual_name_first", "assignee_individual_name_last",
            "assignee_country", "assignee_state", "assignee_city"
        ]
    )
    
    INVENTORS = PatentsViewEndpointConfig(
        name="inventors",
        path="/inventor/",
        description="发明人信息",
        default_fields=[
            "inventor_id", "inventor_name_first", "inventor_name_last",
            "inventor_country", "inventor_state", "inventor_city"
        ]
    )
    
    LOCATIONS = PatentsViewEndpointConfig(
        name="locations",
        path="/location/",
        description="地理位置信息",
        default_fields=[
            "location_id", "city", "state", "country", "latitude", "longitude"
        ]
    )
    
    # 分类相关端点
    CPC_CLASSES = PatentsViewEndpointConfig(
        name="cpc_classes",
        path="/cpc_class/",
        description="CPC分类",
        default_fields=["cpc_class", "cpc_class_title"]
    )
    
    CPC_SUBCLASSES = PatentsViewEndpointConfig(
        name="cpc_subclasses",
        path="/cpc_subclass/",
        description="CPC子分类",
        default_fields=["cpc_subclass", "cpc_subclass_title"]
    )
    
    CPC_GROUPS = PatentsViewEndpointConfig(
        name="cpc_groups",
        path="/cpc_group/",
        description="CPC组分类",
        default_fields=["cpc_group", "cpc_group_title"]
    )
    
    IPC_CLASSES = PatentsViewEndpointConfig(
        name="ipc_classes",
        path="/ipc/",
        description="IPC分类",
        default_fields=["ipc_class", "ipc_class_title"]
    )
    
    USPC_MAINCLASSES = PatentsViewEndpointConfig(
        name="uspc_mainclasses",
        path="/uspc_mainclass/",
        description="USPC主分类",
        default_fields=["uspc_mainclass_id", "uspc_mainclass_title"]
    )
    
    USPC_SUBCLASSES = PatentsViewEndpointConfig(
        name="uspc_subclasses",
        path="/uspc_subclass/",
        description="USPC子分类",
        default_fields=["uspc_subclass_id", "uspc_subclass_title"]
    )
    
    WIPO_CLASSES = PatentsViewEndpointConfig(
        name="wipo_classes",
        path="/wipo/",
        description="WIPO分类",
        default_fields=["wipo_id", "wipo_field_title"]
    )
    
    # 引用相关端点
    FOREIGN_CITATIONS = PatentsViewEndpointConfig(
        name="foreign_citations",
        path="/patent/foreign_citation/",
        description="外国引用",
        default_fields=[
            "patent_id", "foreign_citation_sequence", 
            "foreign_citation_country", "foreign_citation_number", "foreign_citation_date"
        ]
    )
    
    US_APPLICATION_CITATIONS = PatentsViewEndpointConfig(
        name="us_application_citations",
        path="/patent/us_application_citation/",
        description="美国申请引用",
        default_fields=[
            "patent_id", "us_application_citation_sequence",
            "us_application_citation_number", "us_application_citation_date"
        ]
    )
    
    US_PATENT_CITATIONS = PatentsViewEndpointConfig(
        name="us_patent_citations",
        path="/patent/us_patent_citation/",
        description="美国专利引用",
        default_fields=[
            "patent_id", "us_patent_citation_sequence",
            "us_patent_citation_number", "us_patent_citation_date"
        ]
    )
    
    OTHER_REFERENCES = PatentsViewEndpointConfig(
        name="other_references",
        path="/patent/other_reference/",
        description="其他引用",
        default_fields=[
            "patent_id", "other_reference_sequence", "other_reference_text"
        ]
    )
    
    @classmethod
    def get_all_endpoints(cls) -> Dict[str, PatentsViewEndpointConfig]:
        """获取所有端点配置."""
        endpoints = {}
        for attr_name in dir(cls):
            if not attr_name.startswith('_') and attr_name != 'get_all_endpoints':
                attr_value = getattr(cls, attr_name)
                if isinstance(attr_value, PatentsViewEndpointConfig):
                    endpoints[attr_value.name] = attr_value
        return endpoints
    
    @classmethod
    def get_endpoint_by_name(cls, name: str) -> Optional[PatentsViewEndpointConfig]:
        """根据名称获取端点配置."""
        endpoints = cls.get_all_endpoints()
        return endpoints.get(name)


class PatentsViewQueryBuilder:
    """PatentsView 查询构建器配置."""
    
    # 支持的查询操作符
    OPERATORS = {
        # 比较操作符
        "_eq": "等于",
        "_neq": "不等于",
        "_gt": "大于",
        "_gte": "大于等于",
        "_lt": "小于",
        "_lte": "小于等于",
        
        # 包含操作符
        "_in": "包含在列表中",
        "_not_in": "不包含在列表中",
        
        # 文本操作符
        "_text_any": "文本匹配任意字段",
        "_text_all": "文本匹配所有字段",
        "_begins": "开始于",
        "_contains": "包含",
        
        # 逻辑操作符
        "_and": "逻辑与",
        "_or": "逻辑或",
        "_not": "逻辑非"
    }
    
    # 常用查询模板
    QUERY_TEMPLATES = {
        "keyword_search": {
            "_text_any": {
                "patent_title": "{keyword}",
                "patent_abstract": "{keyword}"
            }
        },
        
        "date_range": {
            "patent_date": {
                "_gte": "{start_date}",
                "_lte": "{end_date}"
            }
        },
        
        "country_filter": {
            "assignee_country": {
                "_in": ["{countries}"]
            }
        },
        
        "classification_filter": {
            "_or": [
                {"ipc_class": {"_in": ["{ipc_classes}"]}},
                {"cpc_class": {"_in": ["{cpc_classes}"]}}
            ]
        },
        
        "assignee_search": {
            "_text_any": {
                "assignee_organization": "{assignee_name}"
            }
        },
        
        "inventor_search": {
            "_or": [
                {"inventor_name_first": {"_contains": "{inventor_name}"}},
                {"inventor_name_last": {"_contains": "{inventor_name}"}}
            ]
        }
    }
    
    # 常用字段组合
    FIELD_GROUPS = {
        "basic_patent": [
            "patent_id", "patent_number", "patent_title", 
            "patent_abstract", "patent_date", "patent_type"
        ],
        
        "assignee_info": [
            "assignee_organization", "assignee_country", 
            "assignee_state", "assignee_city"
        ],
        
        "inventor_info": [
            "inventor_name_first", "inventor_name_last",
            "inventor_country", "inventor_state", "inventor_city"
        ],
        
        "classification_info": [
            "ipc_class", "cpc_class", "uspc_mainclass", "wipo_field"
        ],
        
        "text_content": [
            "patent_title", "patent_abstract", "summary_text", "claim_text"
        ],
        
        "citation_info": [
            "foreign_citation_number", "us_patent_citation_number",
            "us_application_citation_number", "other_reference_text"
        ]
    }


# 默认配置实例
DEFAULT_CONFIG = PatentsViewAPIConfig.from_env()
DEFAULT_ENDPOINTS = PatentsViewEndpoints.get_all_endpoints()