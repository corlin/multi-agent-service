"""PatentsView API 专利搜索智能体."""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import json
import aiohttp

from .base import PatentBaseAgent
from ...models.enums import AgentType
from ...models.config import AgentConfig
from ...services.model_client import BaseModelClient
from ..models.requests import PatentAnalysisRequest


logger = logging.getLogger(__name__)


class PatentsViewSearchAgent(PatentBaseAgent):
    """基于 PatentsView API 的专利搜索智能体."""
    
    agent_type = AgentType.PATENT_SEARCH
    
    def __init__(self, config: AgentConfig, model_client: BaseModelClient):
        """初始化 PatentsView 搜索智能体."""
        super().__init__(config, model_client)
        
        # PatentsView API 配置
        self.api_config = {
            'base_url': 'https://search.patentsview.org/api/v1',
            'api_key': None,  # 从环境变量或配置中获取
            'timeout': 30,
            'max_retries': 3,
            'rate_limit_delay': 1.0,  # 请求间隔
            'default_page_size': 100,
            'max_page_size': 1000
        }
        
        # 支持的端点映射
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
        
        self.logger = logging.getLogger(f"{__name__}.PatentsViewSearchAgent")
        
        # 从配置中加载 API 密钥
        self._load_api_config()
    
    def _load_api_config(self):
        """从配置中加载 API 相关设置."""
        # 确保加载 .env 文件
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            # 如果没有安装 python-dotenv，尝试手动加载
            import os
            env_file = ".env"
            if os.path.exists(env_file):
                with open(env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key] = value
        
        if hasattr(self.config, 'metadata') and self.config.metadata:
            api_metadata = self.config.metadata.get('patentsview_api', {})
            self.api_config.update(api_metadata)
            
        # 从环境变量获取 API 密钥
        import os
        if not self.api_config.get('api_key'):
            self.api_config['api_key'] = os.getenv('PATENT_VIEW_API_KEY')
    
    async def can_handle_request(self, request) -> float:
        """判断是否能处理请求."""
        base_confidence = await super().can_handle_request(request)
        
        # 检查专利搜索相关关键词
        content = getattr(request, 'content', str(request)).lower()
        search_keywords = [
            "专利搜索", "patent search", "专利检索", "专利查询",
            "patentsview", "专利数据", "专利信息", "专利文本",
            "权利要求", "claims", "摘要", "summary", "说明书", "description"
        ]
        
        keyword_matches = sum(1 for keyword in search_keywords if keyword in content)
        search_boost = min(keyword_matches * 0.15, 0.4)
        
        return min(base_confidence + search_boost, 1.0)
    
    async def get_capabilities(self) -> List[str]:
        """获取Agent能力列表."""
        base_capabilities = await super().get_capabilities()
        specific_capabilities = [
            "PatentsView API 专利搜索",
            "专利文本检索 (摘要、权利要求、说明书)",
            "专利分类信息查询 (CPC、IPC、USPC)",
            "专利权人和发明人信息查询",
            "专利引用关系分析",
            "多维度专利数据获取",
            "结构化专利数据处理",
            "专利发布信息查询"
        ]
        return base_capabilities + specific_capabilities
    
    async def estimate_processing_time(self, request) -> int:
        """估算处理时间."""
        base_time = await super().estimate_processing_time(request)
        
        # 根据请求复杂度估算额外时间
        if hasattr(request, 'keywords') and len(request.keywords) > 5:
            return base_time + 45  # 复杂搜索需要更多时间
        elif hasattr(request, 'max_patents') and getattr(request, 'max_patents', 0) > 500:
            return base_time + 60  # 大量数据需要更多时间
        else:
            return base_time + 30  # 标准搜索时间
    
    async def _process_request_specific(self, request) -> 'AgentResponse':
        """处理具体的搜索请求."""
        from ...models.base import AgentResponse
        from uuid import uuid4
        
        try:
            # 处理不同类型的请求
            if hasattr(request, 'analysis_types'):
                result = await self._process_patent_request_specific(request)
            else:
                # 转换为标准专利分析请求
                analysis_request = self._convert_to_patent_request(request)
                result = await self._process_patent_request_specific(analysis_request)
            
            # 生成响应内容
            response_content = await self._generate_response_content(result)
            
            return AgentResponse(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                response_content=response_content,
                confidence=0.85,
                metadata=result
            )
            
        except Exception as e:
            self.logger.error(f"Error processing PatentsView search request: {str(e)}")
            return AgentResponse(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                response_content=f"PatentsView 搜索处理失败: {str(e)}",
                confidence=0.0,
                metadata={"error": str(e)}
            )
    
    def _convert_to_patent_request(self, request) -> PatentAnalysisRequest:
        """将普通请求转换为专利分析请求."""
        from ..models.requests import PatentAnalysisRequest
        from uuid import uuid4
        
        content = getattr(request, 'content', str(request))
        keywords = content.split()[:10]  # 提取前10个词作为关键词
        
        return PatentAnalysisRequest(
            request_id=str(uuid4()),
            keywords=keywords,
            analysis_types=["search", "data_collection"],
            date_range={"start": "2020-01-01", "end": "2024-12-31"},
            countries=["US", "CN", "EP", "JP"],
            max_patents=500
        )
    
    async def _process_patent_request_specific(self, request: PatentAnalysisRequest) -> Dict[str, Any]:
        """处理专利特定请求."""
        start_time = datetime.now()
        
        try:
            self.logger.info(f"Starting PatentsView search for request {request.request_id}")
            
            # 检查缓存
            cache_key = f"patentsview_search_{hash(str(request.keywords))}"
            cached_result = await self._get_from_cache(cache_key)
            if cached_result:
                self.logger.info(f"Using cached PatentsView results for request {request.request_id}")
                return cached_result
            
            # 构建搜索查询
            search_query = await self._build_search_query(request)
            
            # 执行多个搜索任务
            search_tasks = []
            
            # 基础专利搜索
            search_tasks.append(self._search_patents(search_query, request.max_patents))
            
            # 专利文本搜索
            if "text" in request.analysis_types or "comprehensive" in request.analysis_types:
                search_tasks.append(self._search_patent_texts(search_query))
            
            # 专利分类搜索
            if "classification" in request.analysis_types or "comprehensive" in request.analysis_types:
                search_tasks.append(self._search_classifications(search_query))
            
            # 执行并行搜索
            results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # 整合搜索结果
            integrated_data = await self._integrate_search_results(results)
            
            # 数据质量评估
            quality_score = await self._evaluate_data_quality(integrated_data)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                "status": "completed",
                "search_data": integrated_data,
                "quality_score": quality_score,
                "processing_time": processing_time,
                "api_calls": len(search_tasks),
                "total_patents": len(integrated_data.get("patents", [])),
                "search_query": search_query
            }
            
            # 保存到缓存
            await self._save_to_cache(cache_key, result)
            
            self.logger.info(f"PatentsView search completed for request {request.request_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"PatentsView search failed for request {request.request_id}: {str(e)}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "status": "failed",
                "error": str(e),
                "processing_time": processing_time,
                "api_calls": 0,
                "total_patents": 0
            }
    
    async def _build_search_query(self, request: PatentAnalysisRequest) -> Dict[str, Any]:
        """构建 PatentsView API 搜索查询."""
        query = {}
        
        # 关键词查询
        if request.keywords:
            # 构建文本搜索条件
            keyword_conditions = []
            for keyword in request.keywords:
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
        if request.date_range:
            date_condition = {}
            if request.date_range.get("start"):
                date_condition["_gte"] = request.date_range["start"]
            if request.date_range.get("end"):
                date_condition["_lte"] = request.date_range["end"]
            
            if date_condition:
                query["patent_date"] = date_condition
        
        # 国家限制
        if request.countries:
            query["assignee_country"] = {"_in": request.countries}
        
        # IPC 分类限制
        if request.ipc_classes:
            query["ipc_class"] = {"_in": request.ipc_classes}
        
        return query
    
    async def _search_patents(self, query: Dict[str, Any], max_results: int = 1000) -> Dict[str, Any]:
        """搜索专利基础信息."""
        try:
            endpoint = self.endpoints['patents']
            
            # 构建请求参数
            params = {
                'q': json.dumps(query),
                'f': json.dumps([
                    "patent_id", "patent_number", "patent_title", 
                    "patent_abstract", "patent_date", "patent_type",
                    "assignee_organization", "assignee_country",
                    "inventor_name_first", "inventor_name_last",
                    "ipc_class", "cpc_class"
                ]),
                'o': json.dumps({
                    "size": min(max_results, self.api_config['max_page_size']),
                    "pad_patent_id": False
                }),
                's': json.dumps([{"patent_date": "desc"}])
            }
            
            response_data = await self._make_api_request(endpoint, params)
            
            return {
                "type": "patents",
                "data": response_data.get("patents", []),
                "total_count": response_data.get("total_patent_count", 0)
            }
            
        except Exception as e:
            self.logger.error(f"Error searching patents: {str(e)}")
            return {"type": "patents", "data": [], "error": str(e)}
    
    async def _search_patent_texts(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """搜索专利文本信息."""
        try:
            # 搜索专利摘要
            summary_endpoint = self.endpoints['patent_summary']
            summary_params = {
                'q': json.dumps(query),
                'f': json.dumps(["patent_id", "summary_text"]),
                'o': json.dumps({"size": 100})
            }
            
            summary_data = await self._make_api_request(summary_endpoint, summary_params)
            
            # 搜索权利要求
            claims_endpoint = self.endpoints['patent_claims']
            claims_params = {
                'q': json.dumps(query),
                'f': json.dumps(["patent_id", "claim_sequence", "claim_text"]),
                'o': json.dumps({"size": 200})
            }
            
            claims_data = await self._make_api_request(claims_endpoint, claims_params)
            
            return {
                "type": "patent_texts",
                "summaries": summary_data.get("g_brf_sum_texts", []),
                "claims": claims_data.get("g_claims", [])
            }
            
        except Exception as e:
            self.logger.error(f"Error searching patent texts: {str(e)}")
            return {"type": "patent_texts", "summaries": [], "claims": [], "error": str(e)}
    
    async def _search_classifications(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """搜索专利分类信息."""
        try:
            # 搜索 CPC 分类
            cpc_endpoint = self.endpoints['cpc_classes']
            cpc_params = {
                'q': json.dumps({}),  # 获取所有相关分类
                'f': json.dumps(["cpc_class", "cpc_class_title"]),
                'o': json.dumps({"size": 100})
            }
            
            cpc_data = await self._make_api_request(cpc_endpoint, cpc_params)
            
            # 搜索 IPC 分类
            ipc_endpoint = self.endpoints['ipc_classes']
            ipc_params = {
                'q': json.dumps({}),
                'f': json.dumps(["ipc_class", "ipc_class_title"]),
                'o': json.dumps({"size": 100})
            }
            
            ipc_data = await self._make_api_request(ipc_endpoint, ipc_params)
            
            return {
                "type": "classifications",
                "cpc_classes": cpc_data.get("cpc_classes", []),
                "ipc_classes": ipc_data.get("ipc_classes", [])
            }
            
        except Exception as e:
            self.logger.error(f"Error searching classifications: {str(e)}")
            return {"type": "classifications", "cpc_classes": [], "ipc_classes": [], "error": str(e)}
    
    async def _make_api_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """发起 API 请求."""
        url = f"{self.api_config['base_url']}{endpoint}"
        
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'PatentSearchAgent/1.0'
        }
        
        # 添加 API 密钥（如果有）
        if self.api_config.get('api_key'):
            headers['X-API-Key'] = self.api_config['api_key']
        
        # 重试机制
        for attempt in range(self.api_config['max_retries']):
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(
                    total=self.api_config['timeout']
                )) as session:
                    
                    # 使用 POST 请求发送复杂查询
                    async with session.post(url, json=params, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            return data
                        elif response.status == 429:
                            # 速率限制，等待后重试
                            wait_time = self.api_config['rate_limit_delay'] * (2 ** attempt)
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            error_text = await response.text()
                            raise Exception(f"API request failed with status {response.status}: {error_text}")
            
            except asyncio.TimeoutError:
                if attempt == self.api_config['max_retries'] - 1:
                    raise Exception("API request timeout after all retries")
                await asyncio.sleep(self.api_config['rate_limit_delay'])
            
            except Exception as e:
                if attempt == self.api_config['max_retries'] - 1:
                    raise e
                await asyncio.sleep(self.api_config['rate_limit_delay'])
        
        raise Exception("API request failed after all retries")
    
    async def _integrate_search_results(self, results: List[Any]) -> Dict[str, Any]:
        """整合搜索结果."""
        integrated_data = {
            "patents": [],
            "patent_texts": {"summaries": [], "claims": []},
            "classifications": {"cpc_classes": [], "ipc_classes": []},
            "errors": []
        }
        
        for result in results:
            if isinstance(result, Exception):
                integrated_data["errors"].append(str(result))
                continue
            
            if isinstance(result, dict):
                result_type = result.get("type")
                
                if result_type == "patents":
                    integrated_data["patents"] = result.get("data", [])
                elif result_type == "patent_texts":
                    integrated_data["patent_texts"]["summaries"] = result.get("summaries", [])
                    integrated_data["patent_texts"]["claims"] = result.get("claims", [])
                elif result_type == "classifications":
                    integrated_data["classifications"]["cpc_classes"] = result.get("cpc_classes", [])
                    integrated_data["classifications"]["ipc_classes"] = result.get("ipc_classes", [])
                
                # 记录错误
                if "error" in result:
                    integrated_data["errors"].append(result["error"])
        
        return integrated_data
    
    async def _evaluate_data_quality(self, data: Dict[str, Any]) -> float:
        """评估数据质量."""
        quality_score = 0.0
        components = 0
        
        # 评估专利数据质量
        patents = data.get("patents", [])
        if patents:
            complete_patents = sum(1 for p in patents if self._is_patent_data_complete(p))
            patent_quality = complete_patents / len(patents) if patents else 0
            quality_score += patent_quality * 0.5
            components += 1
        
        # 评估文本数据质量
        summaries = data.get("patent_texts", {}).get("summaries", [])
        claims = data.get("patent_texts", {}).get("claims", [])
        if summaries or claims:
            text_quality = min((len(summaries) + len(claims)) / 50, 1.0)
            quality_score += text_quality * 0.3
            components += 1
        
        # 评估分类数据质量
        cpc_classes = data.get("classifications", {}).get("cpc_classes", [])
        ipc_classes = data.get("classifications", {}).get("ipc_classes", [])
        if cpc_classes or ipc_classes:
            class_quality = min((len(cpc_classes) + len(ipc_classes)) / 20, 1.0)
            quality_score += class_quality * 0.2
            components += 1
        
        # 计算平均质量
        if components > 0:
            quality_score = quality_score / components * (components / 3)
        
        # 考虑错误影响
        errors = data.get("errors", [])
        if errors:
            error_penalty = min(len(errors) * 0.1, 0.3)
            quality_score = max(quality_score - error_penalty, 0.0)
        
        return min(quality_score, 1.0)
    
    def _is_patent_data_complete(self, patent: Dict[str, Any]) -> bool:
        """检查专利数据是否完整."""
        required_fields = ['patent_id', 'patent_title', 'patent_date']
        return all(field in patent and patent[field] for field in required_fields)
    
    async def _generate_response_content(self, result: Dict[str, Any]) -> str:
        """生成响应内容."""
        if result.get("status") == "completed":
            search_data = result.get("search_data", {})
            quality_score = result.get("quality_score", 0.0)
            processing_time = result.get("processing_time", 0.0)
            total_patents = result.get("total_patents", 0)
            api_calls = result.get("api_calls", 0)
            
            # 统计各类数据
            patents_count = len(search_data.get("patents", []))
            summaries_count = len(search_data.get("patent_texts", {}).get("summaries", []))
            claims_count = len(search_data.get("patent_texts", {}).get("claims", []))
            cpc_count = len(search_data.get("classifications", {}).get("cpc_classes", []))
            ipc_count = len(search_data.get("classifications", {}).get("ipc_classes", []))
            errors_count = len(search_data.get("errors", []))
            
            return f"""PatentsView API 专利搜索已完成！

🔍 搜索结果统计:
• 专利记录: {patents_count} 条
• 专利摘要: {summaries_count} 条
• 权利要求: {claims_count} 条
• CPC 分类: {cpc_count} 条
• IPC 分类: {ipc_count} 条

📊 质量指标:
• 数据质量评分: {quality_score:.2f}/1.0
• API 调用次数: {api_calls}
• 处理时间: {processing_time:.1f}秒
• 错误数量: {errors_count}

✅ 专利数据已成功获取并整合，可用于后续分析处理。"""
        
        elif result.get("status") == "failed":
            error = result.get("error", "未知错误")
            return f"PatentsView API 搜索失败: {error}"
        
        else:
            return f"PatentsView API 搜索状态: {result.get('status', 'unknown')}"