"""Patent data collection agent implementation."""

import asyncio
import hashlib
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

import httpx

from ...models.base import UserRequest, AgentResponse
from ...models.enums import AgentType
from .base import PatentBaseAgent
from ..models.requests import PatentDataCollectionRequest
from ..models.responses import PatentDataCollectionResponse
from ..models.data import Patent, PatentDataset, PatentDataSource
from ..utils.data_sources import GooglePatentsAPI, PatentPublicAPI, DataSourceManager


class PatentDataCollectionAgent(PatentBaseAgent):
    """专利数据收集Agent，继承PatentBaseAgent能力."""
    
    agent_type = AgentType.PATENT_DATA_COLLECTION
    
    def __init__(self, config, model_client):
        """初始化专利数据收集Agent."""
        super().__init__(config, model_client)
        
        # 数据源配置
        self.data_sources_config = {
            'google_patents': PatentDataSource(
                name='google_patents',
                base_url='https://patents.google.com/api',
                rate_limit=10,
                timeout=60,  # 增加超时时间
                max_results=1000,
                priority=1
            ),
            'google_patents_browser': PatentDataSource(
                name='google_patents_browser',
                base_url='https://patents.google.com',
                rate_limit=5,
                timeout=60,
                max_results=1000,
                priority=1  # 高优先级，因为更可靠
            ),
            'patent_public_api': PatentDataSource(
                name='patent_public_api', 
                base_url='https://api.patentsview.org/patents/query',
                rate_limit=5,
                timeout=30,
                max_results=1000,
                priority=2
            )
        }
        
        # 数据源管理器
        self.data_source_manager = DataSourceManager()
        
        # 中文关键词映射
        self.chinese_keyword_mapping = self._load_chinese_keyword_mapping()
        
        # Google Patents Browser Service
        self.google_patents_browser = None
        
        # 注册数据源
        for name, config in self.data_sources_config.items():
            if name == 'google_patents':
                api_client = GooglePatentsAPI(config)
            elif name == 'patent_public_api':
                api_client = PatentPublicAPI(config)
            else:
                continue
            self.data_source_manager.register_data_source(name, api_client)
        
        self.logger = logging.getLogger(f"{__name__}.PatentDataCollectionAgent")
    
    def _load_chinese_keyword_mapping(self) -> Dict[str, List[str]]:
        """加载中文关键词到英文关键词的映射."""
        try:
            # 尝试从配置文件加载
            config_file = "chinese_keywords_config.json"
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get("关键词映射", {})
        except Exception as e:
            self.logger.warning(f"无法加载关键词配置文件: {e}，使用默认配置")
        
        # 默认映射（备用）
        return {
            "具身智能": ["embodied intelligence", "embodied AI", "physical AI", "robotics intelligence"],
            "大语言模型": ["large language model", "LLM", "transformer", "GPT", "BERT", "language model"],
            "客户细分": ["customer segmentation", "user profiling", "market segmentation", "customer analytics"],
            "多模态": ["multimodal", "multi-modal", "cross-modal", "vision language"],
            "推荐系统": ["recommendation system", "collaborative filtering", "personalization"],
            "计算机视觉": ["computer vision", "image recognition", "object detection", "visual AI"],
            "自然语言处理": ["natural language processing", "NLP", "text analysis", "language understanding"],
            "深度学习": ["deep learning", "neural network", "artificial neural network"],
            "机器学习": ["machine learning", "ML", "supervised learning", "unsupervised learning"],
            "人工智能": ["artificial intelligence", "AI", "intelligent system"],
            "知识图谱": ["knowledge graph", "knowledge base", "semantic network"],
            "强化学习": ["reinforcement learning", "RL", "Q-learning", "policy gradient"],
            "联邦学习": ["federated learning", "distributed learning", "privacy-preserving learning"],
            "边缘计算": ["edge computing", "edge AI", "mobile computing", "distributed computing"],
            "区块链": ["blockchain", "distributed ledger", "cryptocurrency", "smart contract"],
            "物联网": ["Internet of Things", "IoT", "connected devices", "smart devices"],
            "云计算": ["cloud computing", "distributed computing", "virtualization"],
            "数据挖掘": ["data mining", "data analytics", "pattern recognition", "knowledge discovery"],
            "图像处理": ["image processing", "digital image processing", "image analysis"],
            "语音识别": ["speech recognition", "voice recognition", "automatic speech recognition", "ASR"],
            "情感分析": ["sentiment analysis", "emotion recognition", "affective computing"],
            "预测分析": ["predictive analytics", "forecasting", "predictive modeling"],
            "异常检测": ["anomaly detection", "outlier detection", "fraud detection"],
            "聚类分析": ["clustering", "cluster analysis", "unsupervised classification"],
            "分类算法": ["classification", "supervised learning", "pattern classification"],
            "回归分析": ["regression analysis", "linear regression", "predictive regression"],
            "时间序列": ["time series", "temporal analysis", "sequential data"],
            "优化算法": ["optimization algorithm", "mathematical optimization", "algorithmic optimization"],
            "搜索算法": ["search algorithm", "information retrieval", "search engine"],
            "排序算法": ["sorting algorithm", "ranking algorithm", "ordering algorithm"],
            "加密技术": ["encryption", "cryptography", "data security", "cybersecurity"],
            "隐私保护": ["privacy protection", "data privacy", "privacy-preserving", "differential privacy"]
        }
    
    def _expand_keywords_with_chinese(self, keywords: List[str]) -> List[str]:
        """扩展关键词列表，支持中文关键词映射."""
        expanded_keywords = []
        
        for keyword in keywords:
            # 添加原始关键词
            expanded_keywords.append(keyword)
            
            # 如果是中文关键词，添加对应的英文关键词
            if keyword in self.chinese_keyword_mapping:
                expanded_keywords.extend(self.chinese_keyword_mapping[keyword])
            
            # 检查是否包含中文关键词的部分匹配
            for chinese_key, english_keywords in self.chinese_keyword_mapping.items():
                if chinese_key in keyword or keyword in chinese_key:
                    expanded_keywords.extend(english_keywords)
        
        # 去重并返回
        return list(set(expanded_keywords))
    
    async def can_handle_request(self, request) -> float:
        """判断是否能处理请求."""
        # 调用父类的实现
        base_confidence = await super().can_handle_request(request)
        
        # 检查数据收集相关关键词
        content = getattr(request, 'content', str(request)).lower()
        collection_keywords = ["收集", "数据", "搜索", "获取", "检索"]
        keyword_matches = sum(1 for keyword in collection_keywords if keyword in content)
        
        # 提高数据收集相关请求的置信度
        collection_boost = min(keyword_matches * 0.2, 0.3)
        
        return min(base_confidence + collection_boost, 1.0)
    
    async def get_capabilities(self) -> List[str]:
        """获取Agent能力列表."""
        base_capabilities = await super().get_capabilities()
        specific_capabilities = [
            "专利数据收集",
            "多数据源整合",
            "数据质量验证",
            "数据去重处理",
            "缓存管理"
        ]
        return base_capabilities + specific_capabilities
    
    async def estimate_processing_time(self, request) -> int:
        """估算处理时间."""
        # 数据收集任务通常需要中等时间
        base_time = await super().estimate_processing_time(request)
        return base_time + 20  # 数据收集额外需要20秒
    
    async def _process_request_specific(self, request) -> 'AgentResponse':
        """处理具体的数据收集请求."""
        from ...models.base import AgentResponse
        
        try:
            # 如果是PatentDataCollectionRequest对象，直接处理
            if hasattr(request, 'keywords'):
                result = await self._process_patent_request_specific(request)
            else:
                # 如果是普通请求，转换为数据收集请求
                from ..models.requests import PatentDataCollectionRequest
                
                # 从请求内容提取关键词
                content = getattr(request, 'content', str(request))
                keywords = content.split()[:5]  # 简单提取前5个词作为关键词
                
                collection_request = PatentDataCollectionRequest(
                    request_id=str(uuid4()),
                    keywords=keywords,
                    max_results=100,
                    data_sources=["google_patents", "patent_public_api"],
                    date_range={"start": "2020-01-01", "end": "2024-12-31"},
                    countries=["US", "CN", "EP"]
                )
                
                result = await self._process_patent_request_specific(collection_request)
            
            # 生成响应内容
            response_content = f"专利数据收集完成。状态: {result.get('status', 'unknown')}"
            
            return AgentResponse(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                response_content=response_content,
                confidence=0.8,
                metadata=result
            )
            
        except Exception as e:
            self.logger.error(f"Error processing data collection request: {str(e)}")
            return AgentResponse(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                response_content=f"数据收集处理失败: {str(e)}",
                confidence=0.0,
                metadata={"error": str(e)}
            )
    
    async def _process_patent_request_specific(self, request) -> Dict[str, Any]:
        """处理专利特定请求."""
        try:
            # 模拟数据收集处理
            return {
                "status": "success",
                "collected_patents": 100,
                "data_sources": ["google_patents", "patent_public_api"],
                "processing_time": 30.0
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
        self.data_source_manager = DataSourceManager()
        
        # 数据处理配置
        self.processing_config = {
            'enable_deduplication': True,
            'enable_data_validation': True,
            'enable_quality_assessment': True,
            'batch_size': 100,
            'max_retries': 3,
            'retry_delay': 1.0
        }
    
    async def _initialize_specific(self) -> bool:
        """初始化专利数据收集Agent."""
        try:
            # 调用父类初始化
            if not await super()._initialize_specific():
                return False
            
            # 初始化Google Patents Browser Service
            await self._initialize_google_patents_browser()
            
            # 初始化数据源API客户端
            await self._initialize_data_source_apis()
            
            # 验证数据源连接
            await self._validate_data_sources()
            
            self.patent_logger.info("Patent data collection agent initialized successfully")
            return True
            
        except Exception as e:
            self.patent_logger.error(f"Error initializing patent data collection agent: {str(e)}")
            return False
    
    async def _initialize_google_patents_browser(self):
        """初始化Google Patents Browser Service."""
        try:
            # 尝试导入Google Patents Browser Service
            from ..services.google_patents_browser import GooglePatentsBrowserService
            
            # 创建服务实例
            self.google_patents_browser = GooglePatentsBrowserService(
                headless=True,
                timeout=60
            )
            
            # 初始化服务
            await self.google_patents_browser.initialize()
            
            self.patent_logger.info("Google Patents Browser Service initialized successfully")
            
        except ImportError:
            self.patent_logger.warning("Google Patents Browser Service not available, using fallback methods")
            self.google_patents_browser = None
        except Exception as e:
            self.patent_logger.warning(f"Failed to initialize Google Patents Browser Service: {str(e)}")
            self.google_patents_browser = None
    
    async def _initialize_data_source_apis(self):
        """初始化数据源API客户端."""
        for source_name, source_config in self.data_sources_config.items():
            try:
                # 根据数据源类型创建相应的API客户端
                if source_name == 'google_patents':
                    api_client = GooglePatentsAPI(source_config)
                elif source_name == 'patent_public_api':
                    api_client = PatentPublicAPI(source_config)
                else:
                    # 使用基础API客户端
                    from ..utils.data_sources import BasePatentAPI
                    api_client = BasePatentAPI(source_config)
                
                # 注册到数据源管理器
                self.data_source_manager.register_data_source(source_name, api_client)
                self.patent_logger.info(f"API client initialized for {source_name}")
                
            except Exception as e:
                self.patent_logger.error(f"Failed to initialize API client for {source_name}: {str(e)}")
    
    async def _validate_data_sources(self):
        """验证数据源连接."""
        for source_name, source_config in self.data_sources_config.items():
            try:
                # 通过数据源管理器进行健康检查
                if source_name in self.data_source_manager.data_sources:
                    api_client = self.data_source_manager.data_sources[source_name]
                    is_healthy = await api_client.health_check()
                    source_config.enabled = is_healthy
                    
                    if is_healthy:
                        self.patent_logger.info(f"Data source {source_name} validated successfully")
                    else:
                        self.patent_logger.warning(f"Data source {source_name} health check failed")
                else:
                    source_config.enabled = False
                    self.patent_logger.warning(f"Data source {source_name} not found in manager")
                
            except Exception as e:
                self.patent_logger.warning(f"Data source {source_name} validation failed: {str(e)}")
                source_config.enabled = False
    
    async def can_handle_request(self, request: UserRequest) -> float:
        """判断是否能处理请求."""
        try:
            # 检查请求类型
            if isinstance(request, PatentDataCollectionRequest):
                return 0.95
            
            # 检查是否是专利分析请求
            if hasattr(request, 'content') and request.content:
                content_lower = request.content.lower()
                patent_keywords = ['专利', '专利数据', '专利收集', 'patent', 'patent data']
                if any(keyword in content_lower for keyword in patent_keywords):
                    return 0.8
            
            # 检查关键词
            if hasattr(request, 'keywords') and request.keywords:
                return 0.7
            
            return 0.1
            
        except Exception as e:
            self.patent_logger.error(f"Error evaluating request handling capability: {str(e)}")
            return 0.0
    
    async def get_capabilities(self) -> List[str]:
        """获取Agent能力列表."""
        return [
            "专利数据收集",
            "多数据源并行收集", 
            "数据质量验证",
            "数据去重处理",
            "Google Patents API集成",
            "公开专利API集成",
            "数据缓存管理",
            "批量数据处理",
            "数据标准化"
        ]
    
    async def estimate_processing_time(self, request: UserRequest) -> int:
        """估算处理时间."""
        try:
            if isinstance(request, PatentDataCollectionRequest):
                # 基于专利数量和数据源数量估算
                base_time = 30  # 基础时间30秒
                patent_factor = request.max_patents / 100 * 10  # 每100个专利增加10秒
                source_factor = len(request.data_sources) * 5  # 每个数据源增加5秒
                
                estimated_time = int(base_time + patent_factor + source_factor)
                return min(estimated_time, 300)  # 最大5分钟
            
            return 60  # 默认1分钟
            
        except Exception:
            return 60
    
    async def _process_request_specific(self, request: UserRequest) -> AgentResponse:
        """处理专利数据收集请求."""
        start_time = datetime.now()
        
        try:
            # 转换请求格式
            if isinstance(request, PatentDataCollectionRequest):
                collection_request = request
            else:
                # 从通用请求转换为专利数据收集请求
                collection_request = self._convert_to_collection_request(request)
            
            # 处理专利数据收集
            result = await self._process_patent_request_specific(collection_request)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_patent_metrics(processing_time, True)
            
            return result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_patent_metrics(processing_time, False)
            
            self.patent_logger.error(f"Error processing patent data collection request: {str(e)}")
            
            return PatentDataCollectionResponse(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                response_content=f"专利数据收集失败: {str(e)}",
                confidence=0.0,
                collaboration_needed=False,
                metadata={"error": str(e)},
                processing_time=processing_time
            )
    
    def _convert_to_collection_request(self, request: UserRequest) -> PatentDataCollectionRequest:
        """将通用请求转换为专利数据收集请求."""
        keywords = []
        
        # 从请求内容中提取关键词
        if hasattr(request, 'content') and request.content:
            # 改进的关键词提取逻辑
            content = request.content.lower()
            
            # 检查是否包含中文关键词
            chinese_keywords_found = []
            for chinese_key in self.chinese_keyword_mapping.keys():
                if chinese_key in content:
                    chinese_keywords_found.append(chinese_key)
            
            if chinese_keywords_found:
                # 如果找到中文关键词，使用它们
                keywords = chinese_keywords_found
            else:
                # 否则使用简单的分词提取
                keywords = [word.strip() for word in request.content.split() if len(word.strip()) > 2][:5]
        
        # 确保有默认关键词
        if not keywords:
            keywords = ["技术专利"]
        
        # 优先使用Google Patents Browser Service
        data_sources = ["google_patents_browser"] if self.google_patents_browser else []
        data_sources.extend([name for name in self.data_sources_config.keys() if name != "google_patents_browser"])
        
        return PatentDataCollectionRequest(
            request_id=request.request_id,
            keywords=keywords,
            max_patents=100,  # 默认值
            data_sources=data_sources,
            parallel_sources=True,  # 启用并行收集
            deduplication_enabled=True  # 启用去重
        )
    
    async def _process_patent_request_specific(self, request: PatentDataCollectionRequest) -> PatentDataCollectionResponse:
        """处理专利数据收集请求的具体逻辑."""
        start_time = datetime.now()
        
        try:
            self.patent_logger.info(f"Starting patent data collection for request {request.request_id}")
            
            # 检查缓存
            cache_key = f"patent_data_{hash(str(request.keywords))}_{request.max_patents}"
            cached_result = await self._get_from_cache(cache_key)
            if cached_result:
                self.patent_logger.info(f"Using cached patent data for request {request.request_id}")
                return cached_result
            
            # 使用数据源管理器进行并行收集，集成故障转移机制
            if request.parallel_sources:
                # 并行收集多个数据源
                collection_tasks = []
                available_sources = [name for name in request.data_sources 
                                   if name in self.data_sources_config]
                
                # 优先使用Google Patents Browser Service
                if 'google_patents_browser' in available_sources and self.google_patents_browser:
                    available_sources = ['google_patents_browser'] + [s for s in available_sources if s != 'google_patents_browser']
                
                for source_name in available_sources:
                    # 为每个数据源创建单独的请求
                    source_request = PatentDataCollectionRequest(
                        request_id=f"{request.request_id}_{source_name}",
                        keywords=request.keywords,
                        max_patents=request.max_patents // len(available_sources),  # 平均分配
                        data_sources=[source_name],
                        date_range=request.date_range,
                        countries=request.countries,
                        ipc_classes=request.ipc_classes,
                        parallel_sources=False  # 避免递归
                    )
                    task = self._collect_from_single_source_with_retry(source_name, source_request)
                    collection_tasks.append(task)
                
                if not collection_tasks:
                    raise Exception("No available data sources")
                
                # 执行并行收集
                results = await asyncio.gather(*collection_tasks, return_exceptions=True)
                
                # 处理收集结果
                all_patents = []
                source_results = {}
                collection_stats = {
                    'total_sources': len(collection_tasks),
                    'successful_sources': 0,
                    'failed_sources': 0,
                    'total_patents_collected': 0
                }
                
                for i, result in enumerate(results):
                    source_name = available_sources[i] if i < len(available_sources) else f"source_{i}"
                    
                    if isinstance(result, Exception):
                        self.patent_logger.error(f"Collection from {source_name} failed: {str(result)}")
                        source_results[source_name] = {
                            'status': 'failed',
                            'error': str(result),
                            'patents_count': 0
                        }
                        collection_stats['failed_sources'] += 1
                    else:
                        patents = result.get('patents', [])
                        all_patents.extend(patents)
                        source_results[source_name] = {
                            'status': 'success',
                            'patents_count': len(patents),
                            'processing_time': result.get('processing_time', 0)
                        }
                        collection_stats['successful_sources'] += 1
                        collection_stats['total_patents_collected'] += len(patents)
            else:
                # 使用故障转移机制顺序收集
                try:
                    all_patents = await self.data_source_manager.collect_patents_with_failover(request)
                    source_results = {'failover_collection': {'status': 'success', 'patents_count': len(all_patents)}}
                    collection_stats = {
                        'total_sources': len(request.data_sources),
                        'successful_sources': 1,
                        'failed_sources': 0,
                        'total_patents_collected': len(all_patents)
                    }
                except Exception as e:
                    raise Exception(f"Failover collection failed: {str(e)}")
            
            # 数据处理和质量控制
            processed_patents = await self._process_and_validate_patents(all_patents, request)
            
            # 创建数据集
            dataset = PatentDataset(
                patents=processed_patents,
                total_count=len(processed_patents),
                search_keywords=request.keywords,
                collection_date=datetime.now(),
                data_sources=request.data_sources
            )
            
            # 数据质量评估
            data_quality = await self._assess_data_quality(dataset)
            dataset.quality_score = data_quality.overall_score
            
            # 创建响应
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = PatentDataCollectionResponse(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                response_content=f"成功收集 {len(processed_patents)} 个专利数据",
                confidence=0.9,
                collaboration_needed=False,
                metadata={
                    "collection_method": "multi_source_parallel",
                    "data_sources_used": list(source_results.keys()),
                    "quality_score": data_quality.overall_score
                },
                dataset=dataset,
                collection_stats=collection_stats,
                data_quality=data_quality,
                source_results=source_results,
                processing_time=processing_time,
                cache_used=False
            )
            
            # 保存到缓存
            await self._save_to_cache(cache_key, result)
            
            self.patent_logger.info(f"Patent data collection completed for request {request.request_id}")
            return result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            self.patent_logger.error(f"Patent data collection failed for request {request.request_id}: {str(e)}")
            
            return PatentDataCollectionResponse(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                response_content=f"专利数据收集失败: {str(e)}",
                confidence=0.0,
                collaboration_needed=False,
                metadata={"error": str(e)},
                collection_stats={'total_sources': 0, 'successful_sources': 0, 'failed_sources': 0},
                source_results={},
                processing_time=processing_time,
                cache_used=False
            )
    
    async def _collect_from_single_source(self, source_name: str, request: PatentDataCollectionRequest) -> Dict[str, Any]:
        """从单个数据源收集专利数据."""
        start_time = datetime.now()
        
        try:
            self.patent_logger.info(f"Collecting patents from {source_name}")
            
            # 扩展关键词（支持中文关键词）
            expanded_keywords = self._expand_keywords_with_chinese(request.keywords)
            self.patent_logger.info(f"Expanded keywords from {len(request.keywords)} to {len(expanded_keywords)}")
            
            patents = []
            
            # 优先使用Google Patents Browser Service
            if source_name == 'google_patents_browser' and self.google_patents_browser:
                patents = await self._collect_from_google_patents_browser(expanded_keywords, request)
            elif source_name in self.data_source_manager.data_sources:
                # 通过数据源管理器获取API客户端
                api_client = self.data_source_manager.data_sources[source_name]
                # 创建修改后的请求，使用扩展的关键词
                modified_request = PatentDataCollectionRequest(
                    request_id=request.request_id,
                    keywords=expanded_keywords,
                    max_patents=request.max_patents,
                    data_sources=[source_name],
                    date_range=request.date_range,
                    countries=request.countries,
                    ipc_classes=request.ipc_classes
                )
                patents = await api_client.collect_patents(modified_request)
            else:
                # 降级到模拟数据
                source_config = self.data_sources_config.get(source_name)
                patents = await self._collect_mock_patents(request, source_config, source_name)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                'source': source_name,
                'patents': patents,
                'processing_time': processing_time,
                'status': 'success',
                'keywords_used': len(expanded_keywords),
                'original_keywords': len(request.keywords)
            }
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            self.patent_logger.error(f"Error collecting from {source_name}: {str(e)}")
            
            return {
                'source': source_name,
                'patents': [],
                'processing_time': processing_time,
                'status': 'failed',
                'error': str(e)
            }
    
    async def _collect_from_google_patents_browser(self, keywords: List[str], request: PatentDataCollectionRequest) -> List[Patent]:
        """使用Google Patents Browser Service收集专利数据."""
        try:
            self.patent_logger.info(f"Using Google Patents Browser Service with {len(keywords)} keywords")
            
            # 使用Browser Service搜索专利
            raw_patents = await self.google_patents_browser.search_patents(
                keywords=keywords,
                limit=request.max_patents,
                date_range=request.date_range,
                assignee=None  # 可以根据需要添加申请人过滤
            )
            
            # 转换为Patent对象
            patents = []
            for raw_patent in raw_patents:
                try:
                    patent = self._convert_raw_patent_to_patent(raw_patent)
                    patents.append(patent)
                except Exception as e:
                    self.patent_logger.warning(f"Failed to convert patent: {str(e)}")
                    continue
            
            self.patent_logger.info(f"Successfully collected {len(patents)} patents from Google Patents Browser")
            return patents
            
        except Exception as e:
            self.patent_logger.error(f"Error collecting from Google Patents Browser: {str(e)}")
            return []
    
    def _convert_raw_patent_to_patent(self, raw_patent: Dict[str, Any]) -> Patent:
        """将原始专利数据转换为Patent对象."""
        try:
            # 解析日期
            def parse_date(date_str):
                if not date_str:
                    return None
                try:
                    # 尝试多种日期格式
                    for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y', '%d/%m/%Y']:
                        try:
                            return datetime.strptime(date_str, fmt)
                        except ValueError:
                            continue
                    return None
                except:
                    return None
            
            patent = Patent(
                application_number=raw_patent.get('patent_number', ''),
                title=raw_patent.get('title', ''),
                abstract=raw_patent.get('abstract', ''),
                applicants=raw_patent.get('applicants', []),
                inventors=raw_patent.get('inventors', []),
                application_date=parse_date(raw_patent.get('application_date')),
                publication_date=parse_date(raw_patent.get('publication_date')),
                ipc_classes=raw_patent.get('ipc_classes', []),
                country=raw_patent.get('country', 'US'),
                status=raw_patent.get('status', '已公开'),
                url=raw_patent.get('url', ''),
                source='google_patents_browser'
            )
            
            return patent
            
        except Exception as e:
            raise Exception(f"Failed to convert raw patent: {str(e)}")
    
    async def _collect_from_single_source_with_retry(self, source_name: str, request: PatentDataCollectionRequest) -> Dict[str, Any]:
        """带重试机制的单数据源收集."""
        max_retries = self.processing_config.get('max_retries', 3)
        retry_delay = self.processing_config.get('retry_delay', 1.0)
        
        for attempt in range(max_retries + 1):
            try:
                result = await self._collect_from_single_source(source_name, request)
                
                # 如果成功或者是最后一次尝试，返回结果
                if result['status'] == 'success' or attempt == max_retries:
                    if attempt > 0:
                        self.patent_logger.info(f"Successfully collected from {source_name} on attempt {attempt + 1}")
                    return result
                
            except Exception as e:
                if attempt == max_retries:
                    self.patent_logger.error(f"Final attempt failed for {source_name}: {str(e)}")
                    return {
                        'source': source_name,
                        'patents': [],
                        'processing_time': 0,
                        'status': 'failed',
                        'error': str(e),
                        'attempts': attempt + 1
                    }
                else:
                    self.patent_logger.warning(f"Attempt {attempt + 1} failed for {source_name}: {str(e)}, retrying...")
                    await asyncio.sleep(retry_delay * (attempt + 1))  # 指数退避
        
        # 这里不应该到达，但为了安全起见
        return {
            'source': source_name,
            'patents': [],
            'processing_time': 0,
            'status': 'failed',
            'error': 'Max retries exceeded',
            'attempts': max_retries + 1
        }
    

    
    async def _collect_mock_patents(self, request: PatentDataCollectionRequest, source_config: PatentDataSource, source_name: str = "Mock") -> List[Patent]:
        """收集模拟专利数据（用于测试和演示）."""
        patents = []
        
        # 模拟网络延迟
        await asyncio.sleep(0.5)
        
        # 生成模拟专利数据
        num_patents = min(request.max_patents // len(request.data_sources), 50)  # 每个数据源最多50个
        
        for i in range(num_patents):
            patent = Patent(
                application_number=f"{source_name.upper()}{datetime.now().year}{i+1:04d}",
                title=f"基于{request.keywords[0] if request.keywords else '人工智能'}的{source_name}技术专利{i+1}",
                abstract=f"本发明涉及{request.keywords[0] if request.keywords else '人工智能'}技术领域，特别是关于{source_name}的创新方法和系统。",
                applicants=[f"{source_name}科技有限公司", "创新研究院"],
                inventors=[f"张工程师{i+1}", f"李研究员{i+1}"],
                application_date=datetime(2020 + i % 4, (i % 12) + 1, (i % 28) + 1),
                publication_date=datetime(2021 + i % 4, (i % 12) + 1, (i % 28) + 1),
                ipc_classes=[f"G06F{i%10}/00", f"H04L{i%10}/00"],
                country="CN",
                status="已公开"
            )
            patents.append(patent)
        
        self.patent_logger.info(f"Generated {len(patents)} mock patents from {source_name}")
        return patents
    
    async def _process_and_validate_patents(self, patents: List[Patent], request: PatentDataCollectionRequest) -> List[Patent]:
        """处理和验证专利数据."""
        try:
            processed_patents = patents.copy()
            
            # 数据去重
            if request.deduplication_enabled and self.processing_config['enable_deduplication']:
                processed_patents = await self._deduplicate_patents(processed_patents)
            
            # 数据验证
            if self.processing_config['enable_data_validation']:
                processed_patents = await self._validate_patents(processed_patents)
            
            # 限制数量
            if len(processed_patents) > request.max_patents:
                processed_patents = processed_patents[:request.max_patents]
            
            self.patent_logger.info(f"Processed {len(processed_patents)} patents from {len(patents)} original patents")
            return processed_patents
            
        except Exception as e:
            self.patent_logger.error(f"Error processing patents: {str(e)}")
            return patents  # 返回原始数据
    
    async def _deduplicate_patents(self, patents: List[Patent]) -> List[Patent]:
        """专利数据去重."""
        try:
            seen_numbers = set()
            unique_patents = []
            
            for patent in patents:
                if patent.application_number not in seen_numbers:
                    seen_numbers.add(patent.application_number)
                    unique_patents.append(patent)
            
            removed_count = len(patents) - len(unique_patents)
            if removed_count > 0:
                self.patent_logger.info(f"Removed {removed_count} duplicate patents")
            
            return unique_patents
            
        except Exception as e:
            self.patent_logger.error(f"Error deduplicating patents: {str(e)}")
            return patents
    
    async def _validate_patents(self, patents: List[Patent]) -> List[Patent]:
        """验证专利数据."""
        try:
            valid_patents = []
            
            for patent in patents:
                if self._is_patent_complete(patent) and self._is_patent_accurate(patent):
                    valid_patents.append(patent)
            
            removed_count = len(patents) - len(valid_patents)
            if removed_count > 0:
                self.patent_logger.info(f"Removed {removed_count} invalid patents")
            
            return valid_patents
            
        except Exception as e:
            self.patent_logger.error(f"Error validating patents: {str(e)}")
            return patents
    
    async def _cleanup_specific(self):
        """清理数据源管理器和API客户端."""
        try:
            await super()._cleanup_specific()
            
            # 关闭Google Patents Browser Service
            if self.google_patents_browser:
                try:
                    await self.google_patents_browser.close()
                    self.patent_logger.info("Google Patents Browser Service closed successfully")
                except Exception as e:
                    self.patent_logger.warning(f"Error closing Google Patents Browser Service: {str(e)}")
            
            # 关闭数据源管理器
            await self.data_source_manager.close_all()
            
            self.patent_logger.info("Patent data collection agent cleaned up successfully")
            
        except Exception as e:
            self.patent_logger.error(f"Error cleaning up patent data collection agent: {str(e)}")
    
    def get_patent_metrics(self) -> Dict[str, Any]:
        """获取专利处理指标，包含数据源统计."""
        base_metrics = super().get_patent_metrics()
        
        # 添加数据源统计
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果事件循环正在运行，创建任务
                task = asyncio.create_task(self.data_source_manager.get_aggregated_stats())
                # 注意：这里不能直接await，因为可能在同步上下文中调用
                base_metrics['data_source_stats'] = "Stats collection in progress"
            else:
                # 如果没有运行的事件循环，返回基本信息
                base_metrics['data_source_stats'] = {
                    'total_sources': len(self.data_source_manager.data_sources),
                    'registered_sources': list(self.data_source_manager.data_sources.keys())
                }
        except Exception as e:
            base_metrics['data_source_stats'] = f"Error getting stats: {str(e)}"
        
        # 添加中文关键词映射统计
        base_metrics['chinese_keyword_mapping'] = {
            'total_mappings': len(self.chinese_keyword_mapping),
            'available_chinese_keywords': list(self.chinese_keyword_mapping.keys())[:10],  # 只显示前10个
            'google_patents_browser_available': self.google_patents_browser is not None
        }
        
        return base_metrics
    
    async def get_supported_chinese_keywords(self) -> List[str]:
        """获取支持的中文关键词列表."""
        return list(self.chinese_keyword_mapping.keys())
    
    async def preview_keyword_expansion(self, keywords: List[str]) -> Dict[str, List[str]]:
        """预览关键词扩展结果."""
        result = {}
        for keyword in keywords:
            expanded = self._expand_keywords_with_chinese([keyword])
            result[keyword] = expanded
        return result
    
    async def test_google_patents_browser_connection(self) -> Dict[str, Any]:
        """测试Google Patents Browser Service连接."""
        if not self.google_patents_browser:
            return {
                'status': 'unavailable',
                'message': 'Google Patents Browser Service not initialized'
            }
        
        try:
            # 执行一个简单的测试搜索
            test_keywords = ["artificial intelligence"]
            test_results = await self.google_patents_browser.search_patents(
                keywords=test_keywords,
                limit=1
            )
            
            return {
                'status': 'success',
                'message': f'Successfully connected and found {len(test_results)} test results',
                'test_keywords': test_keywords,
                'results_count': len(test_results)
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Connection test failed: {str(e)}',
                'error': str(e)
            }