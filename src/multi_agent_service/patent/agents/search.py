"""Patent search enhancement agent."""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base import PatentBaseAgent
from ...models.enums import AgentType
from ...models.config import AgentConfig
from ...services.model_client import BaseModelClient

from ..models.requests import PatentAnalysisRequest
from ..models.external_data import EnhancedData, CNKIData, BochaData, WebDataset


logger = logging.getLogger(__name__)


class PatentSearchAgent(PatentBaseAgent):
    """专利搜索增强智能体，集成CNKI和博查AI."""
    
    agent_type = AgentType.PATENT_SEARCH
    
    def __init__(self, config: AgentConfig, model_client: BaseModelClient):
        """初始化专利搜索智能体."""
        super().__init__(config, model_client)
        
        # 搜索增强专用配置
        self.search_config = {
            'enable_cnki_search': True,
            'enable_bocha_search': True,
            'enable_web_crawling': True,
            'max_search_results': 100,
            'search_timeout': 60
        }
        
        self.logger = logging.getLogger(f"{__name__}.PatentSearchAgent")
    
    async def _get_specific_capabilities(self) -> List[str]:
        """获取搜索增强智能体的特定能力."""
        return [
            "CNKI学术搜索集成",
            "博查AI智能搜索",
            "网页爬取增强",
            "多源搜索结果整合",
            "搜索结果质量评估",
            "实时信息获取",
            "学术文献检索"
        ]
    
    async def _process_patent_request(self, request: PatentAnalysisRequest) -> Dict[str, Any]:
        """处理专利搜索增强请求."""
        start_time = datetime.now()
        
        try:
            self.logger.info(f"Starting patent search enhancement for request {request.request_id}")
            
            # 检查缓存
            cache_key = f"patent_search_{hash(str(request.keywords))}"
            cached_result = await self._get_from_cache(cache_key)
            if cached_result:
                self.logger.info(f"Using cached search results for request {request.request_id}")
                return cached_result
            
            # 并行执行多种搜索
            search_tasks = []
            
            if self.search_config['enable_cnki_search'] and request.include_academic_search:
                search_tasks.append(self._search_cnki(request.keywords))
            
            if self.search_config['enable_bocha_search'] and request.include_web_search:
                search_tasks.append(self._search_bocha(request.keywords))
            
            if self.search_config['enable_web_crawling'] and request.include_web_search:
                search_tasks.append(self._crawl_web_data(request.keywords))
            
            if not search_tasks:
                raise Exception("No search methods enabled")
            
            # 执行并行搜索
            results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # 整合搜索结果
            enhanced_data = await self._integrate_search_results(results)
            
            # 评估结果质量
            quality_score = await self._evaluate_search_quality(enhanced_data)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                "status": "completed",
                "enhanced_data": enhanced_data,
                "quality_score": quality_score,
                "processing_time": processing_time,
                "search_methods": [
                    "cnki" if self.search_config['enable_cnki_search'] else None,
                    "bocha_ai" if self.search_config['enable_bocha_search'] else None,
                    "web_crawling" if self.search_config['enable_web_crawling'] else None
                ]
            }
            
            # 保存到缓存
            await self._save_to_cache(cache_key, result)
            
            self.logger.info(f"Patent search enhancement completed for request {request.request_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Patent search enhancement failed for request {request.request_id}: {str(e)}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "status": "failed",
                "error": str(e),
                "processing_time": processing_time,
                "search_methods": []
            }
    
    async def _search_cnki(self, keywords: List[str]) -> Optional[CNKIData]:
        """调用CNKI学术搜索."""
        try:
            self.logger.info(f"Searching CNKI with keywords: {keywords}")
            
            # 模拟CNKI API调用
            await asyncio.sleep(2)  # 模拟API延迟
            
            # 模拟学术文献数据
            from ..models.external_data import Literature
            
            literature = []
            for i in range(min(10, len(keywords) * 3)):
                lit = Literature(
                    title=f"Academic paper on {' '.join(keywords)} - Study {i+1}",
                    authors=[f"Author {i+1}", f"Co-author {i+1}"],
                    abstract=f"This academic paper investigates {' '.join(keywords)} from theoretical and practical perspectives...",
                    keywords=keywords + [f"keyword{i+1}"],
                    publication_date=datetime(2024, 1 + i % 12, 1),
                    journal=f"Journal of {keywords[0] if keywords else 'Technology'} Research",
                    citation_count=50 + i * 10,
                    relevance_score=0.8 - i * 0.05
                )
                literature.append(lit)
            
            # 模拟概念解释
            concepts = [
                {
                    "concept": keyword,
                    "definition": f"Definition of {keyword} from academic perspective",
                    "related_terms": [f"related_term_{i}" for i in range(3)]
                }
                for keyword in keywords[:5]
            ]
            
            cnki_data = CNKIData(
                literature=literature,
                concepts=concepts,
                search_metadata={
                    "total_results": len(literature),
                    "search_time": 2.0,
                    "database": "CNKI"
                }
            )
            
            self.logger.info(f"CNKI search completed, found {len(literature)} papers")
            return cnki_data
            
        except Exception as e:
            self.logger.error(f"CNKI search failed: {str(e)}")
            return None
    
    async def _search_bocha(self, keywords: List[str]) -> Optional[BochaData]:
        """调用博查AI搜索."""
        try:
            self.logger.info(f"Searching Bocha AI with keywords: {keywords}")
            
            # 模拟博查AI API调用
            await asyncio.sleep(1.5)  # 模拟API延迟
            
            # 模拟Web搜索结果
            web_results = []
            for i in range(min(15, len(keywords) * 5)):
                result = {
                    "title": f"Web result for {' '.join(keywords)} - {i+1}",
                    "url": f"https://example.com/result_{i+1}",
                    "snippet": f"This web page discusses {' '.join(keywords)} and related technologies...",
                    "relevance_score": 0.9 - i * 0.03,
                    "source_type": "news" if i % 3 == 0 else "blog" if i % 3 == 1 else "forum"
                }
                web_results.append(result)
            
            # 模拟AI分析结果
            ai_analysis = {
                "summary": f"Based on web intelligence, {' '.join(keywords)} shows significant development trends...",
                "key_insights": [
                    f"Insight 1: {keywords[0] if keywords else 'Technology'} is gaining momentum",
                    f"Insight 2: Market adoption of {' '.join(keywords)} is accelerating",
                    "Insight 3: Regulatory environment is becoming more favorable"
                ],
                "trend_indicators": {
                    "market_interest": 0.85,
                    "technology_maturity": 0.72,
                    "competitive_intensity": 0.68
                },
                "related_technologies": [f"related_tech_{i}" for i in range(5)]
            }
            
            bocha_data = BochaData(
                web_results=web_results,
                ai_analysis=ai_analysis,
                search_metadata={
                    "total_results": len(web_results),
                    "search_time": 1.5,
                    "ai_confidence": 0.82
                }
            )
            
            self.logger.info(f"Bocha AI search completed, found {len(web_results)} results")
            return bocha_data
            
        except Exception as e:
            self.logger.error(f"Bocha AI search failed: {str(e)}")
            return None
    
    async def _crawl_web_data(self, keywords: List[str]) -> Optional[WebDataset]:
        """爬取相关网页数据."""
        try:
            self.logger.info(f"Crawling web data for keywords: {keywords}")
            
            # 模拟网页爬取
            await asyncio.sleep(3)  # 模拟爬取延迟
            
            from ..models.external_data import WebPage
            
            web_pages = []
            target_sites = [
                "patents.google.com",
                "www.wipo.int",
                "techcrunch.com",
                "ieee.org",
                "nature.com"
            ]
            
            for i, site in enumerate(target_sites):
                for j in range(2):  # 每个站点爬取2页
                    page = WebPage(
                        url=f"https://{site}/article_{i}_{j}",
                        title=f"Article about {' '.join(keywords)} from {site}",
                        content=f"This article from {site} discusses {' '.join(keywords)} in detail...",
                        extracted_data={
                            "main_topics": keywords,
                            "publication_date": datetime(2024, 1 + i, 1 + j),
                            "author": f"Author from {site}",
                            "category": "technology"
                        },
                        crawl_date=datetime.now(),
                        source_type="news" if "techcrunch" in site else "academic",
                        relevance_score=0.8 - i * 0.1
                    )
                    web_pages.append(page)
            
            web_dataset = WebDataset(
                data=web_pages,
                sources=target_sites,
                collection_date=datetime.now(),
                total_pages=len(web_pages),
                metadata={
                    "crawl_method": "smart_crawler",
                    "success_rate": 0.9,
                    "average_page_size": 15000
                }
            )
            
            self.logger.info(f"Web crawling completed, collected {len(web_pages)} pages")
            return web_dataset
            
        except Exception as e:
            self.logger.error(f"Web crawling failed: {str(e)}")
            return None
    
    async def _integrate_search_results(self, results: List[Any]) -> EnhancedData:
        """整合搜索结果."""
        cnki_data = None
        bocha_data = None
        web_dataset = None
        
        for result in results:
            if isinstance(result, Exception):
                self.logger.warning(f"Skipping failed search: {str(result)}")
                continue
            
            if isinstance(result, CNKIData):
                cnki_data = result
            elif isinstance(result, BochaData):
                bocha_data = result
            elif isinstance(result, WebDataset):
                web_dataset = result
        
        enhanced_data = EnhancedData(
            academic_data=cnki_data,
            web_intelligence=bocha_data,
            web_crawl_data=web_dataset,
            collection_date=datetime.now()
        )
        
        return enhanced_data
    
    async def _evaluate_search_quality(self, enhanced_data: EnhancedData) -> float:
        """评估搜索结果质量."""
        quality_score = 0.0
        components = 0
        
        # 评估学术数据质量
        if enhanced_data.academic_data and enhanced_data.academic_data.literature:
            academic_quality = min(len(enhanced_data.academic_data.literature) / 10, 1.0)
            quality_score += academic_quality * 0.4
            components += 1
        
        # 评估网络智能数据质量
        if enhanced_data.web_intelligence and enhanced_data.web_intelligence.web_results:
            web_intel_quality = min(len(enhanced_data.web_intelligence.web_results) / 15, 1.0)
            quality_score += web_intel_quality * 0.3
            components += 1
        
        # 评估网页爬取数据质量
        if enhanced_data.web_crawl_data and enhanced_data.web_crawl_data.data:
            crawl_quality = min(len(enhanced_data.web_crawl_data.data) / 10, 1.0)
            quality_score += crawl_quality * 0.3
            components += 1
        
        # 计算平均质量
        if components > 0:
            quality_score = quality_score / components * (components / 3)  # 奖励多样性
        
        return min(quality_score, 1.0)
    
    async def _generate_response_content(self, result: Dict[str, Any]) -> str:
        """生成搜索增强响应内容."""
        if result.get("status") == "completed":
            enhanced_data = result.get("enhanced_data")
            quality_score = result.get("quality_score", 0.0)
            processing_time = result.get("processing_time", 0.0)
            
            # 统计收集到的数据
            academic_count = 0
            web_intel_count = 0
            crawl_count = 0
            
            if enhanced_data:
                if enhanced_data.academic_data and enhanced_data.academic_data.literature:
                    academic_count = len(enhanced_data.academic_data.literature)
                if enhanced_data.web_intelligence and enhanced_data.web_intelligence.web_results:
                    web_intel_count = len(enhanced_data.web_intelligence.web_results)
                if enhanced_data.web_crawl_data and enhanced_data.web_crawl_data.data:
                    crawl_count = len(enhanced_data.web_crawl_data.data)
            
            return f"""专利搜索增强已完成！

🔍 搜索结果:
• 学术文献: {academic_count} 篇
• 网络情报: {web_intel_count} 条
• 网页数据: {crawl_count} 页
• 数据质量评分: {quality_score:.2f}/1.0
• 处理时间: {processing_time:.1f}秒

增强数据已准备就绪，为专利分析提供了丰富的背景信息和市场洞察。"""
        
        elif result.get("status") == "failed":
            error = result.get("error", "未知错误")
            return f"专利搜索增强失败: {error}"
        
        else:
            return f"专利搜索增强状态: {result.get('status', 'unknown')}"