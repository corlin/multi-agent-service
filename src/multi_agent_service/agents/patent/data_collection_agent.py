"""Patent data collection agent implementation."""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import re

from .base import PatentBaseAgent
from ...models.base import UserRequest, AgentResponse, Action
from ...models.config import AgentConfig
from ...models.enums import AgentType
from ...services.model_client import BaseModelClient

# 导入 PatentsView 相关模块
from ...patent.services.patentsview_service import PatentsViewService
from ...patent.config.patentsview_config import PatentsViewAPIConfig
from ...patent.models.patentsview_data import PatentsViewSearchResult, PatentRecord
from ...patent.models.requests import PatentAnalysisRequest


logger = logging.getLogger(__name__)


class PatentDataCollectionAgent(PatentBaseAgent):
    """专利数据收集Agent，负责从PatentsView API收集专利信息."""
    
    agent_type = AgentType.PATENT_DATA_COLLECTION
    
    def __init__(self, config: AgentConfig, model_client: BaseModelClient):
        """初始化专利数据收集Agent."""
        super().__init__(config, model_client)
        
        # 数据收集相关关键词
        self.collection_keywords = [
            "收集", "获取", "采集", "抓取", "下载", "导入", "同步",
            "collect", "gather", "fetch", "retrieve", "download", "import", "sync"
        ]
        
        # 初始化 PatentsView 服务
        self.patentsview_config = PatentsViewAPIConfig.from_env()
        self.patentsview_service = None
        
        # 数据源配置 - 专注于 PatentsView API
        self.data_sources_config = {
            'patentsview_api': {
                'base_url': self.patentsview_config.base_url,
                'rate_limit': 5,
                'timeout': self.patentsview_config.timeout,
                'enabled': True,
                'service_class': PatentsViewService
            }
        }
        
        # 数据质量配置
        self.quality_config = {
            "min_title_length": 5,
            "required_fields": ["patent_title", "patent_id"],
            "max_duplicates_ratio": 0.1
        }
        
        # 初始化专利数据源
        self._patent_data_sources = {}
        self._patent_data_sources['patentsview_api'] = {
            'enabled': True,
            'priority': 1,
            'rate_limit': 5,
            'timeout': self.patentsview_config.timeout
        }
    
    async def can_handle_request(self, request: UserRequest) -> float:
        """判断是否能处理数据收集相关请求."""
        # 先调用父类的专利相关判断
        base_confidence = await super().can_handle_request(request)
        
        content = request.content.lower()
        
        # 检查数据收集关键词
        collection_matches = sum(1 for keyword in self.collection_keywords if keyword in content)
        collection_score = min(collection_matches * 0.3, 0.6)
        
        # 检查数据收集特定模式
        collection_patterns = [
            r"(收集|获取|采集).*?(专利|数据|信息)",
            r"(下载|导入|同步).*?(专利|文件|数据)",
            r"(抓取|爬取).*?(专利|网站|数据)",
            r"(collect|gather|fetch).*?(patent|data|information)",
            r"(download|import|sync).*?(patent|file|data)"
        ]
        
        pattern_score = 0
        for pattern in collection_patterns:
            if re.search(pattern, content):
                pattern_score += 0.25
        
        # 综合评分
        total_score = min(base_confidence + collection_score + pattern_score, 1.0)
        
        return max(total_score, 0.0)
    
    async def get_capabilities(self) -> List[str]:
        """获取数据收集Agent的能力列表."""
        base_capabilities = await super().get_capabilities()
        collection_capabilities = [
            "PatentsView API 专利数据收集",
            "多端点数据整合",
            "专利基础信息收集",
            "专利摘要和权利要求收集",
            "专利权人和发明人信息收集",
            "专利分类信息收集",
            "数据标准化和清洗",
            "数据去重和质量控制",
            "批量数据处理",
            "增量数据同步"
        ]
        return base_capabilities + collection_capabilities
    
    async def estimate_processing_time(self, request: UserRequest) -> int:
        """估算数据收集处理时间."""
        content = request.content.lower()
        
        # 小量数据：20-30秒
        if any(word in content for word in ["少量", "几个", "10", "20"]):
            return 25
        
        # 中量数据：45-60秒
        if any(word in content for word in ["中等", "100", "200"]):
            return 50
        
        # 大量数据：90-120秒
        if any(word in content for word in ["大量", "全部", "1000", "批量"]):
            return 105
        
        # 默认收集时间
        return 40
    
    async def _process_request_specific(self, request: UserRequest) -> AgentResponse:
        """处理数据收集相关的具体请求."""
        start_time = datetime.now()
        
        try:
            # 解析收集请求
            collection_params = self._parse_collection_request(request.content)
            
            # 检查缓存
            cache_key = self._generate_collection_cache_key(collection_params)
            cached_result = await self.get_from_cache(cache_key)
            
            if cached_result:
                self.logger.info("Returning cached collection results")
                return AgentResponse(
                    agent_id=self.agent_id,
                    agent_type=self.agent_type,
                    response_content=cached_result["response_content"],
                    confidence=0.9,
                    metadata={
                        **cached_result.get("metadata", {}),
                        "from_cache": True
                    }
                )
            
            # 执行数据收集
            collection_results = await self._execute_data_collection(collection_params)
            
            # 数据处理和质量控制
            processed_data = await self._process_and_validate_data(collection_results)
            
            # 生成响应内容
            response_content = await self._generate_collection_response(
                collection_params, processed_data
            )
            
            # 生成后续动作
            next_actions = self._generate_collection_actions(collection_params, processed_data)
            
            # 缓存结果
            result_data = {
                "response_content": response_content,
                "metadata": {
                    "collection_params": collection_params,
                    "total_collected": len(processed_data.get("patents", [])),
                    "processing_time": (datetime.now() - start_time).total_seconds(),
                    "sources_used": list(collection_results.keys()),
                    "data_quality_score": processed_data.get("quality_score", 0.0)
                }
            }
            await self.save_to_cache(cache_key, result_data)
            
            # 记录性能指标
            duration = (datetime.now() - start_time).total_seconds()
            self.log_performance_metrics("data_collection", duration, True)
            
            return AgentResponse(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                response_content=response_content,
                confidence=0.85,
                next_actions=next_actions,
                collaboration_needed=False,
                metadata=result_data["metadata"]
            )
            
        except Exception as e:
            self.logger.error(f"Error processing collection request: {str(e)}")
            
            # 记录失败指标
            duration = (datetime.now() - start_time).total_seconds()
            self.log_performance_metrics("data_collection", duration, False)
            
            return AgentResponse(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                response_content=f"数据收集过程中发生错误: {str(e)}。请稍后重试或联系技术支持。",
                confidence=0.0,
                collaboration_needed=True,
                metadata={
                    "error": str(e),
                    "processing_time": duration
                }
            )
    
    def _parse_collection_request(self, content: str) -> Dict[str, Any]:
        """解析数据收集请求参数."""
        params = {
            "keywords": [],
            "sources": list(self.data_sources_config.keys()),
            "limit": 100,
            "date_range": None,
            "collection_type": "comprehensive",
            "quality_level": "standard"
        }
        
        content_lower = content.lower()
        
        # 提取关键词
        keywords = []
        
        # 查找引号中的关键词
        quoted_keywords = re.findall(r'["""\'](.*?)["""\']', content)
        keywords.extend(quoted_keywords)
        
        # 查找常见的技术术语
        tech_patterns = [
            r'(人工智能|AI|机器学习|深度学习)',
            r'(区块链|blockchain)',
            r'(物联网|IoT)',
            r'(5G|通信技术)',
            r'(新能源|电池技术)',
            r'(生物技术|基因)',
            r'(芯片|半导体)',
        ]
        
        for pattern in tech_patterns:
            matches = re.findall(pattern, content)
            keywords.extend(matches)
        
        # 如果没有找到特定关键词，使用简单分词
        if not keywords:
            stop_words = {"的", "了", "在", "是", "有", "和", "与", "或", "但", "等", "收集", "专利"}
            words = content.split()
            keywords = [word for word in words if len(word) > 1 and word not in stop_words]
        
        params["keywords"] = keywords[:5]  # 限制关键词数量
        
        # 判断收集类型
        if any(word in content_lower for word in ["快速", "简单", "基础"]):
            params["collection_type"] = "quick"
            params["limit"] = 50
        elif any(word in content_lower for word in ["全面", "详细", "完整"]):
            params["collection_type"] = "comprehensive"
            params["limit"] = 200
        elif any(word in content_lower for word in ["深度", "专业", "高质量"]):
            params["collection_type"] = "deep"
            params["quality_level"] = "high"
        
        # 判断数据源偏好 - 默认使用 PatentsView
        if "google" in content_lower:
            params["sources"] = ["google_patents"]
        elif "cnipa" in content_lower or "中国" in content_lower:
            params["sources"] = ["cnipa_api"]
        elif "patentsview" in content_lower or "美国" in content_lower:
            params["sources"] = ["patentsview_api"]
        else:
            # 默认使用 PatentsView API
            params["sources"] = ["patentsview_api"]
        
        # 提取数量限制
        limit_match = re.search(r'(\d+).*?(个|条|件)', content)
        if limit_match:
            params["limit"] = min(int(limit_match.group(1)), 500)  # 最大限制500
        
        # 提取时间范围
        year_matches = re.findall(r'(\d{4})', content)
        if len(year_matches) >= 2:
            years = [int(y) for y in year_matches if 2000 <= int(y) <= 2024]
            if len(years) >= 2:
                params["date_range"] = {
                    "start_year": min(years),
                    "end_year": max(years)
                }
        
        return params
    
    def _generate_collection_cache_key(self, collection_params: Dict[str, Any]) -> str:
        """生成收集缓存键."""
        key_parts = [
            "collection",
            "_".join(sorted(collection_params["keywords"])),
            "_".join(sorted(collection_params["sources"])),
            str(collection_params["limit"]),
            collection_params["collection_type"]
        ]
        
        if collection_params.get("date_range"):
            date_range = collection_params["date_range"]
            key_parts.append(f"{date_range['start_year']}-{date_range['end_year']}")
        
        return "_".join(key_parts).replace(" ", "_")
    
    async def _execute_data_collection(self, collection_params: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """执行数据收集."""
        results = {}
        
        # 初始化 PatentsView 服务
        if not self.patentsview_service:
            self.patentsview_service = PatentsViewService(
                api_key=self.patentsview_config.api_key,
                base_url=self.patentsview_config.base_url
            )
        
        try:
            # 使用 PatentsView API 进行数据收集
            patentsview_data = await self._collect_from_patentsview(collection_params)
            
            # 转换为标准格式
            patents_data = self._convert_patentsview_to_standard_format(patentsview_data)
            results["patentsview_api"] = patents_data
            
            # 如果启用了其他数据源，可以在这里添加
            for source in collection_params["sources"]:
                if (source != "patentsview_api" and 
                    source in self.data_sources_config and 
                    self.data_sources_config[source]["enabled"]):
                    
                    # 为其他数据源保留原有的收集逻辑
                    try:
                        source_data = await self._collect_from_source(source, collection_params)
                        results[source] = source_data or []
                    except Exception as e:
                        self.logger.error(f"Collection failed for {source}: {str(e)}")
                        results[source] = []
            
            return results
            
        except Exception as e:
            self.logger.error(f"PatentsView collection failed: {str(e)}")
            # 如果 PatentsView 失败，返回空结果
            results["patentsview_api"] = []
            return results
    
    async def _collect_from_source(self, source: str, collection_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从指定数据源收集数据."""
        try:
            keywords = collection_params["keywords"]
            limit = collection_params["limit"]
            
            # 使用重试机制
            return await self.with_retry(
                self._fetch_from_source,
                max_retries=3,
                delay=1.0,
                source=source,
                keywords=keywords,
                limit=limit
            )
            
        except Exception as e:
            self.logger.error(f"Error collecting from {source}: {str(e)}")
            return []
    
    async def _collect_from_patentsview(self, collection_params: Dict[str, Any]) -> Dict[str, Any]:
        """从 PatentsView API 收集数据."""
        try:
            keywords = collection_params.get("keywords", [])
            limit = collection_params.get("limit", 100)
            date_range = collection_params.get("date_range")
            
            self.logger.info(f"Collecting from PatentsView with keywords: {keywords}, limit: {limit}")
            
            # 构建搜索查询
            query = await self._build_patentsview_query(keywords, date_range)
            
            # 执行多个搜索任务
            search_tasks = []
            
            # 基础专利搜索
            search_tasks.append(self._search_patents_direct(query, limit))
            
            # 专利文本搜索
            search_tasks.append(self._search_patent_texts_direct(query))
            
            # 执行并行搜索
            results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # 整合搜索结果
            integrated_data = await self._integrate_patentsview_results(results)
            
            self.logger.info(f"Collected {len(integrated_data.get('patents', []))} patents from PatentsView")
            return integrated_data
            
        except Exception as e:
            self.logger.error(f"Error collecting from PatentsView: {str(e)}")
            # 返回空的结果
            return {"patents": [], "patent_texts": {"summaries": [], "claims": []}, "errors": [str(e)]}
    
    def _convert_patentsview_to_standard_format(self, integrated_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """将 PatentsView 搜索结果转换为标准格式."""
        standard_patents = []
        
        try:
            patents = integrated_data.get("patents", [])
            patent_texts = integrated_data.get("patent_texts", {})
            summaries = patent_texts.get("summaries", [])
            claims = patent_texts.get("claims", [])
            
            # 创建摘要和权利要求的字典
            summary_dict = {summary.get("patent_id"): summary.get("summary_text", "") 
                          for summary in summaries if summary.get("patent_id")}
            
            claims_dict = {}
            for claim in claims:
                patent_id = claim.get("patent_id")
                if patent_id:
                    if patent_id not in claims_dict:
                        claims_dict[patent_id] = []
                    claims_dict[patent_id].append({
                        "sequence": claim.get("claim_sequence", 0),
                        "text": claim.get("claim_text", "")
                    })
            
            for patent in patents:
                # 转换为标准格式
                patent_id = patent.get("patent_id", "")
                standard_patent = {
                    "patent_id": patent_id,
                    "patent_number": patent.get("patent_number") or patent_id,
                    "title": patent.get("patent_title") or "未知标题",
                    "abstract": patent.get("patent_abstract") or "",
                    "applicants": [patent.get("assignee_organization")] if patent.get("assignee_organization") else [],
                    "inventors": [],
                    "application_date": patent.get("patent_date") or "",
                    "publication_date": patent.get("patent_date") or "",
                    "ipc_classes": [patent.get("ipc_class")] if patent.get("ipc_class") else [],
                    "cpc_classes": [patent.get("cpc_class")] if patent.get("cpc_class") else [],
                    "country": patent.get("assignee_country") or "US",
                    "status": "已公开",
                    "source": "patentsview_api",
                    "collected_at": datetime.now().isoformat(),
                    "patent_type": patent.get("patent_type") or "utility"
                }
                
                # 添加发明人信息
                first_name = patent.get("inventor_name_first", "")
                last_name = patent.get("inventor_name_last", "")
                if first_name or last_name:
                    inventor_name = f"{first_name} {last_name}".strip()
                    if inventor_name:
                        standard_patent["inventors"] = [inventor_name]
                
                # 添加摘要文本
                if patent_id in summary_dict:
                    standard_patent["summary_text"] = summary_dict[patent_id]
                
                # 添加权利要求
                if patent_id in claims_dict:
                    standard_patent["claims"] = claims_dict[patent_id]
                
                standard_patents.append(standard_patent)
            
            self.logger.info(f"Converted {len(standard_patents)} patents to standard format")
            return standard_patents
            
        except Exception as e:
            self.logger.error(f"Error converting PatentsView data: {str(e)}")
            return []
    
    async def _fetch_from_source(self, source: str, keywords: List[str], limit: int) -> List[Dict[str, Any]]:
        """从其他数据源获取数据（保留原有模拟实现作为后备）."""
        # 这里保留原有的模拟实现作为其他数据源的后备
        
        self.logger.info(f"Fetching data from {source} with keywords: {keywords}")
        
        # 模拟网络延迟
        await asyncio.sleep(0.5)
        
        # 生成模拟数据
        mock_patents = []
        
        applicants = [
            "华为技术有限公司", "腾讯科技", "阿里巴巴", "百度", "字节跳动",
            "Apple Inc.", "Google LLC", "Microsoft Corporation", "Samsung Electronics"
        ]
        
        ipc_classes = ["G06F", "H04L", "G06N", "H04W", "G06Q", "H01L"]
        countries = ["CN", "US", "JP", "KR", "DE"]
        
        import random
        random.seed(hash(source + str(keywords)))  # 确保结果可重现
        
        for i in range(min(limit, 50)):  # 每个源最多返回50条
            year = random.randint(2020, 2024)
            month = random.randint(1, 12)
            day = random.randint(1, 28)
            
            patent = {
                "patent_id": f"{source.upper()}{year}{i:04d}",
                "patent_number": f"{source.upper()}{year}{i:04d}",
                "title": f"关于{keywords[0] if keywords else '技术'}的{random.choice(['方法', '系统', '装置'])} - {source}",
                "abstract": f"本发明涉及{keywords[0] if keywords else '技术'}领域，来源于{source}数据库...",
                "applicants": [random.choice(applicants)],
                "inventors": [f"发明人{i+1}"],
                "application_date": f"{year}-{month:02d}-{day:02d}",
                "publication_date": f"{year}-{month+3 if month <= 9 else month-9:02d}-{day:02d}",
                "ipc_classes": [random.choice(ipc_classes)],
                "country": random.choice(countries),
                "status": random.choice(["已授权", "审查中", "已公开"]),
                "source": source,
                "collected_at": datetime.now().isoformat()
            }
            mock_patents.append(patent)
        
        self.logger.info(f"Collected {len(mock_patents)} patents from {source}")
        return mock_patents
    
    async def _process_and_validate_data(self, collection_results: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """处理和验证收集的数据."""
        try:
            # 合并所有数据源的结果
            all_patents = []
            source_stats = {}
            
            for source, patents in collection_results.items():
                source_stats[source] = len(patents)
                for patent in patents:
                    patent["data_source"] = source
                    all_patents.append(patent)
            
            # 数据清洗
            cleaned_patents = []
            for patent in all_patents:
                if self.validate_patent_data(patent):
                    cleaned_patent = self.clean_patent_data(patent)
                    cleaned_patents.append(cleaned_patent)
            
            # 去重
            deduplicated_patents = self._deduplicate_patents(cleaned_patents)
            
            # 质量评估
            quality_score = self._calculate_data_quality(deduplicated_patents)
            
            # 统计信息
            stats = {
                "total_collected": len(all_patents),
                "after_cleaning": len(cleaned_patents),
                "after_deduplication": len(deduplicated_patents),
                "source_breakdown": source_stats,
                "quality_score": quality_score,
                "duplicate_ratio": (len(cleaned_patents) - len(deduplicated_patents)) / max(len(cleaned_patents), 1)
            }
            
            return {
                "patents": deduplicated_patents,
                "statistics": stats,
                "quality_score": quality_score
            }
            
        except Exception as e:
            self.logger.error(f"Error processing collected data: {str(e)}")
            return {
                "patents": [],
                "statistics": {"error": str(e)},
                "quality_score": 0.0
            }
    
    def _deduplicate_patents(self, patents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重专利数据."""
        seen_signatures = set()
        deduplicated = []
        
        for patent in patents:
            # 生成专利签名
            signature = self._generate_patent_signature(patent)
            
            if signature not in seen_signatures:
                seen_signatures.add(signature)
                deduplicated.append(patent)
            else:
                self.logger.debug(f"Duplicate patent found: {patent.get('title', 'Unknown')}")
        
        return deduplicated
    
    def _generate_patent_signature(self, patent: Dict[str, Any]) -> str:
        """生成专利签名用于去重."""
        # 使用专利ID/专利号和标题的组合作为签名
        patent_id = patent.get("patent_id", "").strip().lower()
        patent_number = patent.get("patent_number", "").strip().lower()
        title = patent.get("title", "").strip().lower()
        
        # 优先使用专利ID，其次是专利号
        identifier = patent_id or patent_number
        
        # 标准化标题（移除常见的变化）
        title = re.sub(r'[^\w\s]', '', title)  # 移除标点符号
        title = re.sub(r'\s+', ' ', title)     # 标准化空格
        
        return f"{identifier}|{title}"
    
    def validate_patent_data(self, patent: Dict[str, Any]) -> bool:
        """验证专利数据的有效性."""
        try:
            # 检查必需字段
            required_fields = self.quality_config["required_fields"]
            for field in required_fields:
                if not patent.get(field):
                    return False
            
            # 检查标题长度
            title = patent.get("title", "")
            if len(title) < self.quality_config["min_title_length"]:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating patent data: {str(e)}")
            return False
    
    def clean_patent_data(self, patent: Dict[str, Any]) -> Dict[str, Any]:
        """清洗专利数据."""
        try:
            cleaned_patent = patent.copy()
            
            # 清理标题
            if "title" in cleaned_patent:
                title = cleaned_patent["title"].strip()
                # 移除多余的空格
                title = re.sub(r'\s+', ' ', title)
                cleaned_patent["title"] = title
            
            # 清理摘要
            if "abstract" in cleaned_patent:
                abstract = cleaned_patent["abstract"].strip()
                # 移除多余的空格和换行
                abstract = re.sub(r'\s+', ' ', abstract)
                cleaned_patent["abstract"] = abstract
            
            # 标准化日期格式
            for date_field in ["application_date", "publication_date"]:
                if date_field in cleaned_patent and cleaned_patent[date_field]:
                    try:
                        # 尝试解析和标准化日期
                        date_str = cleaned_patent[date_field]
                        if isinstance(date_str, str) and len(date_str) >= 10:
                            # 保持 YYYY-MM-DD 格式
                            cleaned_patent[date_field] = date_str[:10]
                    except Exception:
                        pass
            
            # 确保列表字段是列表
            list_fields = ["applicants", "inventors", "ipc_classes", "cpc_classes"]
            for field in list_fields:
                if field in cleaned_patent:
                    if not isinstance(cleaned_patent[field], list):
                        if cleaned_patent[field]:
                            cleaned_patent[field] = [cleaned_patent[field]]
                        else:
                            cleaned_patent[field] = []
            
            return cleaned_patent
            
        except Exception as e:
            self.logger.error(f"Error cleaning patent data: {str(e)}")
            return patent
    
    def _calculate_data_quality(self, patents: List[Dict[str, Any]]) -> float:
        """计算数据质量分数."""
        if not patents:
            return 0.0
        
        quality_factors = {
            "completeness": 0,
            "validity": 0,
            "consistency": 0
        }
        
        total_patents = len(patents)
        
        # 完整性检查
        complete_patents = 0
        for patent in patents:
            required_fields = self.quality_config["required_fields"]
            if all(patent.get(field) for field in required_fields):
                complete_patents += 1
        
        quality_factors["completeness"] = complete_patents / total_patents
        
        # 有效性检查
        valid_patents = 0
        for patent in patents:
            title_length = len(patent.get("title", ""))
            if title_length >= self.quality_config["min_title_length"]:
                valid_patents += 1
        
        quality_factors["validity"] = valid_patents / total_patents
        
        # 一致性检查（简单实现）
        quality_factors["consistency"] = 0.8  # 假设一致性较好
        
        # 综合质量分数
        overall_quality = (
            quality_factors["completeness"] * 0.4 +
            quality_factors["validity"] * 0.4 +
            quality_factors["consistency"] * 0.2
        )
        
        return round(overall_quality, 2)
    
    async def _generate_collection_response(self, collection_params: Dict[str, Any], processed_data: Dict[str, Any]) -> str:
        """生成数据收集响应内容."""
        try:
            patents = processed_data.get("patents", [])
            stats = processed_data.get("statistics", {})
            quality_score = processed_data.get("quality_score", 0.0)
            
            response_parts = []
            
            # 添加收集概述
            keywords_str = "、".join(collection_params.get("keywords", ["相关技术"]))
            response_parts.append(f"## 专利数据收集报告")
            response_parts.append(f"**收集主题**: {keywords_str}")
            response_parts.append(f"**收集类型**: {collection_params.get('collection_type', 'comprehensive')}")
            response_parts.append("")
            
            # 添加统计信息
            response_parts.append("### 📊 收集统计")
            response_parts.append(f"- **总收集数量**: {stats.get('total_collected', 0)}件")
            response_parts.append(f"- **清洗后数量**: {stats.get('after_cleaning', 0)}件")
            response_parts.append(f"- **去重后数量**: {stats.get('after_deduplication', 0)}件")
            response_parts.append(f"- **数据质量分数**: {quality_score:.2f}/1.00")
            response_parts.append("")
            
            # 添加数据源统计
            source_breakdown = stats.get("source_breakdown", {})
            if source_breakdown:
                response_parts.append("### 🔗 数据源分布")
                for source, count in source_breakdown.items():
                    response_parts.append(f"- **{source}**: {count}件")
                response_parts.append("")
            
            # 添加样本数据
            if patents:
                response_parts.append("### 📋 样本数据")
                for i, patent in enumerate(patents[:3]):  # 显示前3个样本
                    response_parts.append(f"**样本 {i+1}:**")
                    response_parts.append(f"- 标题: {patent.get('title', 'N/A')}")
                    response_parts.append(f"- 专利号: {patent.get('patent_number', 'N/A')}")
                    response_parts.append(f"- 专利ID: {patent.get('patent_id', 'N/A')}")
                    response_parts.append(f"- 申请人: {', '.join(patent.get('applicants', ['N/A']))}")
                    response_parts.append(f"- 申请日期: {patent.get('application_date', 'N/A')}")
                    response_parts.append("")
            
            # 添加质量评估
            duplicate_ratio = stats.get("duplicate_ratio", 0)
            response_parts.append("### 🎯 质量评估")
            response_parts.append(f"- **重复率**: {duplicate_ratio:.1%}")
            
            if quality_score >= 0.8:
                response_parts.append("- **质量等级**: 优秀 ✅")
            elif quality_score >= 0.6:
                response_parts.append("- **质量等级**: 良好 ⚠️")
            else:
                response_parts.append("- **质量等级**: 需改进 ❌")
            
            # 添加建议
            response_parts.append("\n### 💡 建议")
            if quality_score < 0.7:
                response_parts.append("- 建议调整搜索关键词以提高数据质量")
            if duplicate_ratio > 0.2:
                response_parts.append("- 检测到较高重复率，建议优化数据源选择")
            if len(patents) < collection_params.get("limit", 100) * 0.5:
                response_parts.append("- 收集数量较少，建议扩大搜索范围")
            
            response_parts.append("- 数据已准备就绪，可进行后续分析处理")
            
            # 添加数据说明
            response_parts.append("\n---")
            response_parts.append("*收集的专利数据已经过清洗和去重处理，可用于进一步的分析和研究。*")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            self.logger.error(f"Error generating collection response: {str(e)}")
            return f"数据收集报告生成过程中发生错误: {str(e)}"
    
    def _generate_collection_actions(self, collection_params: Dict[str, Any], processed_data: Dict[str, Any]) -> List[Action]:
        """生成数据收集后续动作."""
        actions = []
        
        try:
            patents = processed_data.get("patents", [])
            
            # 基础后续动作
            if patents:
                actions.append(Action(
                    action_type="export_collected_data",
                    parameters={"format": "json", "include_metadata": True},
                    description="导出收集的专利数据"
                ))
                
                actions.append(Action(
                    action_type="start_analysis",
                    parameters={"data_count": len(patents), "analysis_type": "comprehensive"},
                    description="开始专利数据分析"
                ))
                
                actions.append(Action(
                    action_type="data_validation",
                    parameters={"validation_level": "detailed"},
                    description="执行详细数据验证"
                ))
            
            # 基于质量的动作
            quality_score = processed_data.get("quality_score", 0.0)
            if quality_score < 0.7:
                actions.append(Action(
                    action_type="improve_data_quality",
                    parameters={"target_quality": 0.8, "retry_collection": True},
                    description="改进数据质量"
                ))
            
            # 基于数量的动作
            if len(patents) < collection_params.get("limit", 100) * 0.5:
                actions.append(Action(
                    action_type="expand_collection",
                    parameters={"additional_sources": True, "broader_keywords": True},
                    description="扩大数据收集范围"
                ))
            
            return actions
            
        except Exception as e:
            self.logger.error(f"Error generating collection actions: {str(e)}")
            return []
    
    async def cleanup(self):
        """清理资源."""
        try:
            if self.patentsview_service:
                await self.patentsview_service.cleanup()
                self.patentsview_service = None
            
            # 调用父类清理方法
            await super().cleanup()
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
    
    async def _build_patentsview_query(self, keywords: List[str], date_range: Optional[Dict[str, int]]) -> Dict[str, Any]:
        """构建 PatentsView API 搜索查询."""
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
            if date_range.get("start_year"):
                date_condition["_gte"] = f"{date_range['start_year']}-01-01"
            if date_range.get("end_year"):
                date_condition["_lte"] = f"{date_range['end_year']}-12-31"
            
            if date_condition:
                query["patent_date"] = date_condition
        
        return query
    
    async def _search_patents_direct(self, query: Dict[str, Any], max_results: int = 1000) -> Dict[str, Any]:
        """直接搜索专利基础信息."""
        try:
            endpoint = "/patent/"
            
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
                    "size": min(max_results, 1000),
                    "pad_patent_id": False
                }),
                's': json.dumps([{"patent_date": "desc"}])
            }
            
            response_data = await self._make_patentsview_request(endpoint, params)
            
            return {
                "type": "patents",
                "data": response_data.get("patents", []),
                "total_count": response_data.get("total_patent_count", 0)
            }
            
        except Exception as e:
            self.logger.error(f"Error searching patents: {str(e)}")
            return {"type": "patents", "data": [], "error": str(e)}
    
    async def _search_patent_texts_direct(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """直接搜索专利文本信息."""
        try:
            # 搜索专利摘要
            summary_endpoint = "/g_brf_sum_text/"
            summary_params = {
                'q': json.dumps(query),
                'f': json.dumps(["patent_id", "summary_text"]),
                'o': json.dumps({"size": 100})
            }
            
            summary_data = await self._make_patentsview_request(summary_endpoint, summary_params)
            
            # 搜索权利要求
            claims_endpoint = "/g_claim/"
            claims_params = {
                'q': json.dumps(query),
                'f': json.dumps(["patent_id", "claim_sequence", "claim_text"]),
                'o': json.dumps({"size": 200})
            }
            
            claims_data = await self._make_patentsview_request(claims_endpoint, claims_params)
            
            return {
                "type": "patent_texts",
                "summaries": summary_data.get("g_brf_sum_texts", []),
                "claims": claims_data.get("g_claims", [])
            }
            
        except Exception as e:
            self.logger.error(f"Error searching patent texts: {str(e)}")
            return {"type": "patent_texts", "summaries": [], "claims": [], "error": str(e)}
    
    async def _make_patentsview_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """发起 PatentsView API 请求."""
        url = f"{self.patentsview_config.base_url}{endpoint}"
        
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'PatentDataCollectionAgent/1.0'
        }
        
        # 添加 API 密钥（如果有）
        if self.patentsview_config.api_key:
            headers['X-API-Key'] = self.patentsview_config.api_key
        
        # 重试机制
        for attempt in range(self.patentsview_config.max_retries):
            try:
                timeout = aiohttp.ClientTimeout(total=self.patentsview_config.timeout)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    
                    # 使用 POST 请求发送复杂查询
                    async with session.post(url, json=params, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            return data
                        elif response.status == 429:
                            # 速率限制，等待后重试
                            wait_time = self.patentsview_config.rate_limit_delay * (2 ** attempt)
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            error_text = await response.text()
                            raise Exception(f"API request failed with status {response.status}: {error_text}")
            
            except asyncio.TimeoutError:
                if attempt == self.patentsview_config.max_retries - 1:
                    raise Exception("API request timeout after all retries")
                await asyncio.sleep(self.patentsview_config.rate_limit_delay)
            
            except Exception as e:
                if attempt == self.patentsview_config.max_retries - 1:
                    raise e
                await asyncio.sleep(self.patentsview_config.rate_limit_delay)
        
        raise Exception("API request failed after all retries")
    
    async def _integrate_patentsview_results(self, results: List[Any]) -> Dict[str, Any]:
        """整合 PatentsView 搜索结果."""
        integrated_data = {
            "patents": [],
            "patent_texts": {"summaries": [], "claims": []},
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
                
                # 记录错误
                if "error" in result:
                    integrated_data["errors"].append(result["error"])
        
        return integrated_data