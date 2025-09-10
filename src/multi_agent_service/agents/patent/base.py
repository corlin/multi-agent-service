"""Patent base agent implementation."""

import asyncio
import logging
from abc import abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..base import BaseAgent
from ...models.base import UserRequest, AgentResponse
from ...models.config import AgentConfig
from ...models.enums import AgentType
from ...services.model_client import BaseModelClient


logger = logging.getLogger(__name__)


class PatentBaseAgent(BaseAgent):
    """专利分析基础Agent，为所有专利相关Agent提供通用功能."""
    
    def __init__(self, config: AgentConfig, model_client: BaseModelClient):
        """初始化专利基础Agent."""
        super().__init__(config, model_client)
        
        # 专利相关的通用关键词
        self.patent_keywords = [
            # 中文关键词
            "专利", "发明", "实用新型", "外观设计", "知识产权", "申请", "授权",
            "技术", "创新", "研发", "分析", "检索", "搜索", "趋势", "竞争",
            "申请人", "发明人", "IPC", "分类", "领域", "行业", "市场",
            # 英文关键词
            "patent", "invention", "utility", "design", "intellectual property",
            "application", "grant", "technology", "innovation", "research",
            "analysis", "search", "trend", "competition", "applicant", "inventor"
        ]
        
        # 专利数据源配置
        self.data_sources = {
            "google_patents": {
                "enabled": True,
                "rate_limit": 10,
                "timeout": 30
            },
            "cnki": {
                "enabled": True,
                "rate_limit": 5,
                "timeout": 30
            },
            "bocha_ai": {
                "enabled": True,
                "rate_limit": 8,
                "timeout": 25
            }
        }
        
        # 缓存配置
        self.cache_config = {
            "enabled": True,
            "ttl": 3600,  # 1小时
            "max_size": 1000
        }
        
        # 内存缓存
        self._cache: Dict[str, Dict[str, Any]] = {}
        
    async def can_handle_request(self, request: UserRequest) -> float:
        """判断是否能处理专利相关请求."""
        content = request.content.lower()
        
        # 检查专利关键词
        keyword_matches = sum(1 for keyword in self.patent_keywords if keyword in content)
        keyword_score = min(keyword_matches * 0.2, 0.8)
        
        # 检查专利特定模式
        patent_patterns = [
            "专利.*?(分析|检索|搜索|查询)",
            "技术.*?(趋势|发展|分析)",
            "知识产权.*?(分析|检索)",
            "发明.*?(专利|申请)",
            "patent.*?(analysis|search|trend)",
            "intellectual.*?property",
            "technology.*?(trend|analysis)"
        ]
        
        import re
        pattern_score = 0
        for pattern in patent_patterns:
            if re.search(pattern, content):
                pattern_score += 0.3
        
        total_score = min(keyword_score + pattern_score, 1.0)
        
        # 如果明确提到其他领域，降低置信度
        other_domain_keywords = ["销售", "客服", "管理", "财务", "人事"]
        if any(keyword in content for keyword in other_domain_keywords):
            total_score *= 0.3
        
        return max(total_score, 0.0)
    
    async def get_capabilities(self) -> List[str]:
        """获取专利Agent的通用能力列表."""
        return [
            "专利数据处理",
            "专利信息缓存",
            "多数据源集成",
            "错误处理和重试",
            "性能监控"
        ]
    
    async def estimate_processing_time(self, request: UserRequest) -> int:
        """估算专利请求处理时间."""
        content = request.content.lower()
        
        # 简单查询：10-20秒
        if any(word in content for word in ["查询", "搜索", "检索"]):
            return 15
        
        # 分析任务：30-60秒
        if any(word in content for word in ["分析", "趋势", "竞争"]):
            return 45
        
        # 复杂任务：60-120秒
        if any(word in content for word in ["报告", "深度", "全面"]):
            return 90
        
        # 默认处理时间
        return 30
    
    # 缓存相关方法
    async def get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """从缓存获取数据."""
        if not self.cache_config["enabled"]:
            return None
        
        try:
            cached_data = self._cache.get(cache_key)
            if cached_data:
                # 检查是否过期
                cache_time = cached_data.get("cached_at", 0)
                if datetime.now().timestamp() - cache_time < self.cache_config["ttl"]:
                    self.logger.debug(f"Cache hit for key: {cache_key}")
                    return cached_data.get("data")
                else:
                    # 过期数据，删除
                    del self._cache[cache_key]
                    self.logger.debug(f"Cache expired for key: {cache_key}")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting from cache: {str(e)}")
            return None
    
    async def save_to_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """保存数据到缓存."""
        if not self.cache_config["enabled"]:
            return
        
        try:
            # 检查缓存大小限制
            if len(self._cache) >= self.cache_config["max_size"]:
                # 删除最旧的缓存项
                oldest_key = min(
                    self._cache.keys(),
                    key=lambda k: self._cache[k].get("cached_at", 0)
                )
                del self._cache[oldest_key]
                self.logger.debug(f"Cache full, removed oldest key: {oldest_key}")
            
            # 保存新数据
            self._cache[cache_key] = {
                "data": data,
                "cached_at": datetime.now().timestamp()
            }
            
            self.logger.debug(f"Cached data for key: {cache_key}")
            
        except Exception as e:
            self.logger.error(f"Error saving to cache: {str(e)}")
    
    # 错误处理和重试机制
    async def with_retry(self, func, max_retries: int = 3, delay: float = 1.0, *args, **kwargs):
        """带重试机制的函数执行."""
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    wait_time = delay * (2 ** attempt)  # 指数退避
                    self.logger.warning(
                        f"Attempt {attempt + 1} failed: {str(e)}, "
                        f"retrying in {wait_time}s"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error(f"All {max_retries} attempts failed")
        
        raise last_exception
    
    # 数据验证和清洗
    def validate_patent_data(self, data: Dict[str, Any]) -> bool:
        """验证专利数据的完整性."""
        required_fields = ["title", "application_number"]
        
        try:
            for field in required_fields:
                if field not in data or not data[field]:
                    self.logger.warning(f"Missing required field: {field}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating patent data: {str(e)}")
            return False
    
    def clean_patent_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """清洗专利数据."""
        try:
            cleaned_data = {}
            
            # 清洗标题
            if "title" in data:
                cleaned_data["title"] = str(data["title"]).strip()
            
            # 清洗申请号
            if "application_number" in data:
                cleaned_data["application_number"] = str(data["application_number"]).strip()
            
            # 清洗申请人
            if "applicants" in data:
                if isinstance(data["applicants"], list):
                    cleaned_data["applicants"] = [str(a).strip() for a in data["applicants"]]
                else:
                    cleaned_data["applicants"] = [str(data["applicants"]).strip()]
            
            # 清洗日期
            if "application_date" in data:
                cleaned_data["application_date"] = data["application_date"]
            
            # 保留其他字段
            for key, value in data.items():
                if key not in cleaned_data:
                    cleaned_data[key] = value
            
            return cleaned_data
            
        except Exception as e:
            self.logger.error(f"Error cleaning patent data: {str(e)}")
            return data
    
    # 性能监控
    def log_performance_metrics(self, operation: str, duration: float, success: bool):
        """记录性能指标."""
        try:
            status = "success" if success else "failed"
            self.logger.info(
                f"Performance: {operation} {status} in {duration:.2f}s"
            )
            
            # 这里可以集成到现有的监控系统
            # 例如发送到 MonitoringSystem
            
        except Exception as e:
            self.logger.error(f"Error logging performance metrics: {str(e)}")
    
    # 专利Agent特定的初始化和健康检查
    async def _initialize_specific(self) -> bool:
        """专利Agent特定的初始化."""
        try:
            self.logger.info("Initializing patent-specific components...")
            
            # 初始化缓存
            self._cache = {}
            
            # 验证数据源配置
            for source_name, config in self.data_sources.items():
                if config.get("enabled", False):
                    self.logger.info(f"Data source {source_name} is enabled")
            
            self.logger.info("Patent agent initialization completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Patent agent initialization failed: {str(e)}")
            return False
    
    async def _health_check_specific(self) -> bool:
        """专利Agent特定的健康检查."""
        try:
            # 检查缓存系统
            test_key = "health_check_test"
            test_data = {"test": True, "timestamp": datetime.now().isoformat()}
            
            await self.save_to_cache(test_key, test_data)
            cached_data = await self.get_from_cache(test_key)
            
            if not cached_data or cached_data.get("test") != True:
                self.logger.error("Cache system health check failed")
                return False
            
            # 清理测试数据
            if test_key in self._cache:
                del self._cache[test_key]
            
            return True
            
        except Exception as e:
            self.logger.error(f"Patent agent health check failed: {str(e)}")
            return False
    
    # 抽象方法，子类必须实现
    @abstractmethod
    async def _process_request_specific(self, request: UserRequest) -> AgentResponse:
        """子类特定的请求处理逻辑."""
        pass