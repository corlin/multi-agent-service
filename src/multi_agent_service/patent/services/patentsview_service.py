"""PatentsView API 服务类."""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import json
import aiohttp

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

from ..models.patentsview_data import (
    PatentsViewQuery,
    PatentsViewAPIResponse,
    PatentsViewSearchResult,
    PatentRecord,
    PatentSummary,
    PatentClaim,
    AssigneeRecord,
    InventorRecord,
    CPCClass,
    IPCClass
)


logger = logging.getLogger(__name__)


class PatentsViewService:
    """PatentsView API 服务类."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://search.patentsview.org/api/v1"):
        """初始化 PatentsView 服务."""
        self.api_key = api_key or os.getenv('PATENT_VIEW_API_KEY')
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        
        # API 配置
        self.config = {
            'timeout': 30,
            'max_retries': 3,
            'rate_limit_delay': 1.0,
            'default_page_size': 100,
            'max_page_size': 1000
        }
        
        # 端点映射
        self.endpoints = {
            # 专利文本相关
            'patent_summary': '/g_brf_sum_text/',
            'patent_claims': '/g_claim/',
            'patent_description': '/g_detail_desc_text/',
            'patent_drawings': '/g_draw_desc_text/',
            
            # 发布文本相关
            'publication_summary': '/pg_brf_sum_text/',
            'publication_claims': '/pg_claim/',
            'publication_description': '/pg_detail_desc_text/',
            'publication_drawings': '/pg_draw_desc_text/',
            
            # 专利信息相关
            'patents': '/patent/',
            'publications': '/publication/',
            'assignees': '/assignee/',
            'inventors': '/inventor/',
            'locations': '/location/',
            
            # 分类相关
            'cpc_classes': '/cpc_class/',
            'cpc_subclasses': '/cpc_subclass/',
            'cpc_groups': '/cpc_group/',
            'ipc_classes': '/ipc/',
            'uspc_mainclasses': '/uspc_mainclass/',
            'uspc_subclasses': '/uspc_subclass/',
            'wipo_classes': '/wipo/',
            
            # 引用相关
            'foreign_citations': '/patent/foreign_citation/',
            'us_app_citations': '/patent/us_application_citation/',
            'us_patent_citations': '/patent/us_patent_citation/',
            'other_references': '/patent/other_reference/'
        }
        
        self.logger = logging.getLogger(f"{__name__}.PatentsViewService")
    
    async def __aenter__(self):
        """异步上下文管理器入口."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口."""
        await self.cleanup()
    
    async def initialize(self):
        """初始化服务."""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=self.config['timeout'])
            self.session = aiohttp.ClientSession(timeout=timeout)
            self.logger.info("PatentsView service initialized")
    
    async def cleanup(self):
        """清理服务."""
        if self.session:
            await self.session.close()
            self.session = None
            self.logger.info("PatentsView service cleaned up")
    
    async def search_patents(
        self,
        query: Dict[str, Any],
        fields: Optional[List[str]] = None,
        sort: Optional[List[Dict[str, str]]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> PatentsViewAPIResponse:
        """搜索专利."""
        
        if fields is None:
            fields = [
                "patent_id", "patent_number", "patent_title", 
                "patent_abstract", "patent_date", "patent_type",
                "assignee_organization", "assignee_country",
                "inventor_name_first", "inventor_name_last",
                "ipc_class", "cpc_class"
            ]
        
        if sort is None:
            sort = [{"patent_date": "desc"}]
        
        if options is None:
            options = {"size": self.config['default_page_size']}
        
        params = {
            'q': json.dumps(query),
            'f': json.dumps(fields),
            's': json.dumps(sort),
            'o': json.dumps(options)
        }
        
        response_data = await self._make_request(self.endpoints['patents'], params)
        return PatentsViewAPIResponse(**response_data)
    
    async def search_patent_summaries(
        self,
        query: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None
    ) -> PatentsViewAPIResponse:
        """搜索专利摘要."""
        
        fields = ["patent_id", "summary_text"]
        
        if options is None:
            options = {"size": self.config['default_page_size']}
        
        params = {
            'q': json.dumps(query),
            'f': json.dumps(fields),
            'o': json.dumps(options)
        }
        
        response_data = await self._make_request(self.endpoints['patent_summary'], params)
        return PatentsViewAPIResponse(**response_data)
    
    async def search_patent_claims(
        self,
        query: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None
    ) -> PatentsViewAPIResponse:
        """搜索专利权利要求."""
        
        fields = ["patent_id", "claim_sequence", "claim_text"]
        sort = [{"patent_id": "asc"}, {"claim_sequence": "asc"}]
        
        if options is None:
            options = {"size": self.config['default_page_size']}
        
        params = {
            'q': json.dumps(query),
            'f': json.dumps(fields),
            's': json.dumps(sort),
            'o': json.dumps(options)
        }
        
        response_data = await self._make_request(self.endpoints['patent_claims'], params)
        return PatentsViewAPIResponse(**response_data)
    
    async def search_assignees(
        self,
        query: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None
    ) -> PatentsViewAPIResponse:
        """搜索专利权人."""
        
        fields = [
            "assignee_id", "assignee_organization", 
            "assignee_individual_name_first", "assignee_individual_name_last",
            "assignee_country", "assignee_state", "assignee_city"
        ]
        
        if options is None:
            options = {"size": self.config['default_page_size']}
        
        params = {
            'q': json.dumps(query),
            'f': json.dumps(fields),
            'o': json.dumps(options)
        }
        
        response_data = await self._make_request(self.endpoints['assignees'], params)
        return PatentsViewAPIResponse(**response_data)
    
    async def search_inventors(
        self,
        query: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None
    ) -> PatentsViewAPIResponse:
        """搜索发明人."""
        
        fields = [
            "inventor_id", "inventor_name_first", "inventor_name_last",
            "inventor_country", "inventor_state", "inventor_city"
        ]
        
        if options is None:
            options = {"size": self.config['default_page_size']}
        
        params = {
            'q': json.dumps(query),
            'f': json.dumps(fields),
            'o': json.dumps(options)
        }
        
        response_data = await self._make_request(self.endpoints['inventors'], params)
        return PatentsViewAPIResponse(**response_data)
    
    async def search_cpc_classes(
        self,
        query: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> PatentsViewAPIResponse:
        """搜索CPC分类."""
        
        if query is None:
            query = {}
        
        fields = ["cpc_class", "cpc_class_title"]
        
        if options is None:
            options = {"size": self.config['default_page_size']}
        
        params = {
            'q': json.dumps(query),
            'f': json.dumps(fields),
            'o': json.dumps(options)
        }
        
        response_data = await self._make_request(self.endpoints['cpc_classes'], params)
        return PatentsViewAPIResponse(**response_data)
    
    async def search_ipc_classes(
        self,
        query: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> PatentsViewAPIResponse:
        """搜索IPC分类."""
        
        if query is None:
            query = {}
        
        fields = ["ipc_class", "ipc_class_title"]
        
        if options is None:
            options = {"size": self.config['default_page_size']}
        
        params = {
            'q': json.dumps(query),
            'f': json.dumps(fields),
            'o': json.dumps(options)
        }
        
        response_data = await self._make_request(self.endpoints['ipc_classes'], params)
        return PatentsViewAPIResponse(**response_data)
    
    async def comprehensive_search(
        self,
        keywords: List[str],
        date_range: Optional[Dict[str, str]] = None,
        countries: Optional[List[str]] = None,
        ipc_classes: Optional[List[str]] = None,
        max_results: int = 1000
    ) -> PatentsViewSearchResult:
        """综合搜索专利数据."""
        
        # 构建基础查询
        query = await self._build_comprehensive_query(keywords, date_range, countries, ipc_classes)
        
        # 并行执行多个搜索
        search_tasks = [
            self.search_patents(query, options={"size": min(max_results, self.config['max_page_size'])}),
            self.search_patent_summaries(query),
            self.search_patent_claims(query),
            self.search_assignees(query),
            self.search_inventors(query),
            self.search_cpc_classes(),
            self.search_ipc_classes()
        ]
        
        try:
            results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # 整合结果
            search_result = PatentsViewSearchResult()
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.warning(f"Search task {i} failed: {str(result)}")
                    continue
                
                if isinstance(result, PatentsViewAPIResponse):
                    await self._integrate_response_data(search_result, result, i)
            
            # 添加元数据
            search_result.search_metadata = {
                "keywords": keywords,
                "date_range": date_range,
                "countries": countries,
                "ipc_classes": ipc_classes,
                "max_results": max_results,
                "search_time": datetime.now().isoformat()
            }
            
            return search_result
            
        except Exception as e:
            self.logger.error(f"Comprehensive search failed: {str(e)}")
            raise
    
    async def _build_comprehensive_query(
        self,
        keywords: List[str],
        date_range: Optional[Dict[str, str]] = None,
        countries: Optional[List[str]] = None,
        ipc_classes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """构建综合查询条件."""
        
        query = {}
        
        # 关键词查询
        if keywords:
            keyword_conditions = []
            for keyword in keywords:
                keyword_conditions.append({
                    "_text_any": {
                        "patent_title": keyword,
                        "patent_abstract": keyword
                    }
                })
            
            if len(keyword_conditions) == 1:
                query.update(keyword_conditions[0])
            else:
                query["_or"] = keyword_conditions
        
        # 日期范围
        if date_range:
            date_condition = {}
            if date_range.get("start"):
                date_condition["_gte"] = date_range["start"]
            if date_range.get("end"):
                date_condition["_lte"] = date_range["end"]
            
            if date_condition:
                query["patent_date"] = date_condition
        
        # 国家限制
        if countries:
            query["assignee_country"] = {"_in": countries}
        
        # IPC 分类限制
        if ipc_classes:
            query["ipc_class"] = {"_in": ipc_classes}
        
        return query
    
    async def _integrate_response_data(
        self,
        search_result: PatentsViewSearchResult,
        response: PatentsViewAPIResponse,
        task_index: int
    ):
        """整合响应数据到搜索结果中."""
        
        try:
            if task_index == 0 and response.patents:
                # 专利数据
                for patent_data in response.patents:
                    patent = PatentRecord(**patent_data)
                    search_result.patents.append(patent)
            
            elif task_index == 1 and response.g_brf_sum_texts:
                # 专利摘要
                for summary_data in response.g_brf_sum_texts:
                    summary = PatentSummary(**summary_data)
                    search_result.patent_summaries.append(summary)
            
            elif task_index == 2 and response.g_claims:
                # 专利权利要求
                for claim_data in response.g_claims:
                    claim = PatentClaim(**claim_data)
                    search_result.patent_claims.append(claim)
            
            elif task_index == 3 and response.assignees:
                # 专利权人
                for assignee_data in response.assignees:
                    assignee = AssigneeRecord(**assignee_data)
                    search_result.assignees.append(assignee)
            
            elif task_index == 4 and response.inventors:
                # 发明人
                for inventor_data in response.inventors:
                    inventor = InventorRecord(**inventor_data)
                    search_result.inventors.append(inventor)
            
            elif task_index == 5 and response.cpc_classes:
                # CPC分类
                for cpc_data in response.cpc_classes:
                    cpc_class = CPCClass(**cpc_data)
                    search_result.cpc_classes.append(cpc_class)
            
            elif task_index == 6 and response.ipc_classes:
                # IPC分类
                for ipc_data in response.ipc_classes:
                    ipc_class = IPCClass(**ipc_data)
                    search_result.ipc_classes.append(ipc_class)
        
        except Exception as e:
            self.logger.warning(f"Error integrating response data for task {task_index}: {str(e)}")
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """发起 API 请求."""
        
        if not self.session:
            await self.initialize()
        
        url = f"{self.base_url}{endpoint}"
        
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'PatentsViewService/1.0'
        }
        
        # 添加 API 密钥（如果有）
        if self.api_key:
            headers['X-API-Key'] = self.api_key
        
        # 重试机制
        for attempt in range(self.config['max_retries']):
            try:
                # 使用 POST 请求发送复杂查询
                async with self.session.post(url, json=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    elif response.status == 429:
                        # 速率限制，等待后重试
                        wait_time = self.config['rate_limit_delay'] * (2 ** attempt)
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        error_text = await response.text()
                        raise Exception(f"API request failed with status {response.status}: {error_text}")
            
            except asyncio.TimeoutError:
                if attempt == self.config['max_retries'] - 1:
                    raise Exception("API request timeout after all retries")
                await asyncio.sleep(self.config['rate_limit_delay'])
            
            except Exception as e:
                if attempt == self.config['max_retries'] - 1:
                    raise e
                await asyncio.sleep(self.config['rate_limit_delay'])
        
        raise Exception("API request failed after all retries")
    
    def build_text_search_query(self, keywords: List[str], search_fields: List[str] = None) -> Dict[str, Any]:
        """构建文本搜索查询."""
        
        if search_fields is None:
            search_fields = ["patent_title", "patent_abstract"]
        
        if not keywords:
            return {}
        
        if len(keywords) == 1:
            # 单个关键词
            keyword = keywords[0]
            text_conditions = {}
            for field in search_fields:
                text_conditions[field] = keyword
            return {"_text_any": text_conditions}
        else:
            # 多个关键词，使用 OR 逻辑
            keyword_conditions = []
            for keyword in keywords:
                text_conditions = {}
                for field in search_fields:
                    text_conditions[field] = keyword
                keyword_conditions.append({"_text_any": text_conditions})
            
            return {"_or": keyword_conditions}
    
    def build_date_range_query(self, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """构建日期范围查询."""
        
        if not start_date and not end_date:
            return {}
        
        date_condition = {}
        if start_date:
            date_condition["_gte"] = start_date
        if end_date:
            date_condition["_lte"] = end_date
        
        return {"patent_date": date_condition}
    
    def build_classification_query(
        self,
        ipc_classes: List[str] = None,
        cpc_classes: List[str] = None
    ) -> Dict[str, Any]:
        """构建分类查询."""
        
        conditions = []
        
        if ipc_classes:
            conditions.append({"ipc_class": {"_in": ipc_classes}})
        
        if cpc_classes:
            conditions.append({"cpc_class": {"_in": cpc_classes}})
        
        if not conditions:
            return {}
        elif len(conditions) == 1:
            return conditions[0]
        else:
            return {"_and": conditions}
    
    def combine_queries(self, *queries: Dict[str, Any]) -> Dict[str, Any]:
        """组合多个查询条件."""
        
        valid_queries = [q for q in queries if q]
        
        if not valid_queries:
            return {}
        elif len(valid_queries) == 1:
            return valid_queries[0]
        else:
            return {"_and": valid_queries}