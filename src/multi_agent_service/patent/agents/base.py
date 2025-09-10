"""Base patent agent class."""

import asyncio
import logging
from abc import abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ...agents.base import BaseAgent
from ...models.config import AgentConfig
from ...services.model_client import BaseModelClient
from ..models.requests import PatentAnalysisRequest
from ..models.data import PatentDataQuality


class PatentBaseAgent(BaseAgent):
    """专利分析基础Agent类，继承现有BaseAgent能力."""
    
    def __init__(self, config: AgentConfig, model_client: BaseModelClient):
        """初始化专利基础Agent."""
        super().__init__(config, model_client)
        
        # 专利分析专用配置
        self.patent_config = {
            'cache_enabled': True,
            'cache_ttl': 3600,  # 1小时
            'data_quality_threshold': 0.7,
            'max_concurrent_requests': 5,
            'timeout': 300,  # 5分钟
            'retry_attempts': 3,
            'enable_monitoring': True
        }
        
        # 专利分析专用状态
        self._patent_cache: Dict[str, Any] = {}
        self._patent_data_sources: Dict[str, Dict[str, Any]] = {}
        self._active_patent_requests: Dict[str, PatentAnalysisRequest] = {}
        self._patent_metrics = {
            'total_patent_requests': 0,
            'successful_patent_analyses': 0,
            'failed_patent_analyses': 0,
            'average_patent_processing_time': 0.0,
            'cache_hit_rate': 0.0
        }
        
        # 专利Agent专用日志记录器
        self.patent_logger = logging.getLogger(f"{__name__}.{self.agent_type.value}")
        
        # 从配置中加载专利特定设置
        self._load_patent_config()
    
    def _load_patent_config(self):
        """从Agent配置中加载专利特定设置."""
        if hasattr(self.config, 'metadata') and self.config.metadata:
            patent_metadata = self.config.metadata.get('patent_config', {})
            self.patent_config.update(patent_metadata)
            
            # 加载数据源配置
            if 'supported_data_sources' in patent_metadata:
                for source_name in patent_metadata['supported_data_sources']:
                    self._patent_data_sources[source_name] = {
                        'enabled': True,
                        'priority': 1,
                        'rate_limit': 10,
                        'timeout': 30
                    }
    
    async def _initialize_specific(self) -> bool:
        """专利Agent特定的初始化逻辑."""
        try:
            self.patent_logger.info(f"Initializing patent agent {self.agent_id}")
            
            # 初始化专利数据源连接
            await self._initialize_patent_data_sources()
            
            # 验证专利配置
            if not await self._validate_patent_config():
                self.patent_logger.error("Patent configuration validation failed")
                return False
            
            # 初始化专利缓存
            await self._initialize_patent_cache()
            
            # 注册到健康检查系统
            await self._register_to_health_check()
            
            self.patent_logger.info(f"Patent agent {self.agent_id} initialized successfully")
            return True
            
        except Exception as e:
            self.patent_logger.error(f"Error initializing patent agent {self.agent_id}: {str(e)}")
            return False
    
    async def _initialize_patent_data_sources(self):
        """初始化专利数据源连接."""
        for source_name, source_config in self._patent_data_sources.items():
            try:
                # 这里可以添加具体的数据源初始化逻辑
                # 例如验证API密钥、测试连接等
                self.patent_logger.info(f"Initialized patent data source: {source_name}")
                source_config['status'] = 'active'
            except Exception as e:
                self.patent_logger.warning(f"Failed to initialize data source {source_name}: {str(e)}")
                source_config['status'] = 'error'
    
    async def _validate_patent_config(self) -> bool:
        """验证专利配置."""
        try:
            # 检查必要的配置项
            required_configs = ['cache_enabled', 'data_quality_threshold', 'timeout']
            for config_key in required_configs:
                if config_key not in self.patent_config:
                    self.patent_logger.error(f"Missing required patent config: {config_key}")
                    return False
            
            # 验证配置值的合理性
            if self.patent_config['data_quality_threshold'] < 0 or self.patent_config['data_quality_threshold'] > 1:
                self.patent_logger.error("Invalid data quality threshold")
                return False
            
            if self.patent_config['timeout'] <= 0:
                self.patent_logger.error("Invalid timeout value")
                return False
            
            return True
            
        except Exception as e:
            self.patent_logger.error(f"Error validating patent config: {str(e)}")
            return False
    
    async def _initialize_patent_cache(self):
        """初始化专利缓存."""
        if self.patent_config['cache_enabled']:
            # 这里可以集成Redis或其他缓存系统
            # 目前使用内存缓存作为简单实现
            self._patent_cache = {}
            self.patent_logger.info("Patent cache initialized")
    
    async def _health_check_specific(self) -> bool:
        """专利Agent特定的健康检查."""
        try:
            # 检查专利数据源状态
            active_sources = 0
            for source_name, source_config in self._patent_data_sources.items():
                if source_config.get('status') == 'active':
                    active_sources += 1
            
            if active_sources == 0:
                self.patent_logger.warning("No active patent data sources")
                return False
            
            # 检查缓存状态
            if self.patent_config['cache_enabled'] and self._patent_cache is None:
                self.patent_logger.warning("Patent cache not initialized")
                return False
            
            # 检查当前负载
            if len(self._active_patent_requests) >= self.patent_config['max_concurrent_requests']:
                self.patent_logger.warning("Patent agent at maximum capacity")
                return False
            
            return True
            
        except Exception as e:
            self.patent_logger.error(f"Patent health check failed: {str(e)}")
            return False
    
    async def _cleanup_specific(self):
        """专利Agent特定的清理逻辑."""
        try:
            # 从健康检查系统注销
            await self._unregister_from_health_check()
            
            # 清理活跃的专利请求
            self._active_patent_requests.clear()
            
            # 清理缓存
            if self._patent_cache:
                self._patent_cache.clear()
            
            # 关闭数据源连接
            for source_name in self._patent_data_sources:
                self._patent_data_sources[source_name]['status'] = 'inactive'
            
            self.patent_logger.info(f"Patent agent {self.agent_id} cleaned up successfully")
            
        except Exception as e:
            self.patent_logger.error(f"Error cleaning up patent agent {self.agent_id}: {str(e)}")
    
    # 缓存相关方法
    async def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """从缓存获取数据."""
        if not self.patent_config['cache_enabled']:
            return None
        
        cached_item = self._patent_cache.get(cache_key)
        if cached_item:
            # 检查TTL
            if datetime.now().timestamp() - cached_item['timestamp'] < self.patent_config['cache_ttl']:
                self._patent_metrics['cache_hit_rate'] += 1
                return cached_item['data']
            else:
                # 缓存过期，删除
                del self._patent_cache[cache_key]
        
        return None
    
    async def _save_to_cache(self, cache_key: str, data: Any):
        """保存数据到缓存."""
        if not self.patent_config['cache_enabled']:
            return
        
        self._patent_cache[cache_key] = {
            'data': data,
            'timestamp': datetime.now().timestamp()
        }
    
    async def _clear_cache(self, pattern: Optional[str] = None):
        """清理缓存."""
        if not self.patent_config['cache_enabled']:
            return
        
        if pattern:
            # 清理匹配模式的缓存项
            keys_to_remove = [key for key in self._patent_cache.keys() if pattern in key]
            for key in keys_to_remove:
                del self._patent_cache[key]
        else:
            # 清理所有缓存
            self._patent_cache.clear()
    
    # 数据质量相关方法
    async def _assess_data_quality(self, data: Any) -> PatentDataQuality:
        """评估数据质量."""
        quality = PatentDataQuality()
        
        try:
            if hasattr(data, 'patents') and data.patents:
                patents = data.patents
                total_patents = len(patents)
                
                # 完整性评分
                complete_patents = sum(1 for p in patents if self._is_patent_complete(p))
                quality.completeness_score = complete_patents / total_patents if total_patents > 0 else 0
                
                # 准确性评分（基于数据格式和内容合理性）
                accurate_patents = sum(1 for p in patents if self._is_patent_accurate(p))
                quality.accuracy_score = accurate_patents / total_patents if total_patents > 0 else 0
                
                # 一致性评分（基于数据格式一致性）
                quality.consistency_score = self._calculate_consistency_score(patents)
                
                # 时效性评分（基于数据新鲜度）
                quality.timeliness_score = self._calculate_timeliness_score(patents)
                
                # 计算总体评分
                quality.calculate_overall_score()
                
                # 识别质量问题
                if quality.completeness_score < 0.8:
                    quality.issues.append("数据完整性不足")
                if quality.accuracy_score < 0.8:
                    quality.issues.append("数据准确性有问题")
                if quality.consistency_score < 0.8:
                    quality.issues.append("数据格式不一致")
                if quality.timeliness_score < 0.6:
                    quality.issues.append("数据时效性较差")
            
        except Exception as e:
            self.patent_logger.error(f"Error assessing data quality: {str(e)}")
            quality.issues.append(f"质量评估错误: {str(e)}")
        
        return quality
    
    def _is_patent_complete(self, patent) -> bool:
        """检查专利数据是否完整."""
        required_fields = ['application_number', 'title', 'applicants', 'application_date']
        return all(hasattr(patent, field) and getattr(patent, field) for field in required_fields)
    
    def _is_patent_accurate(self, patent) -> bool:
        """检查专利数据是否准确."""
        try:
            # 检查申请号格式
            if hasattr(patent, 'application_number') and patent.application_number:
                if len(patent.application_number) < 5:
                    return False
            
            # 检查日期合理性
            if hasattr(patent, 'application_date') and patent.application_date:
                if patent.application_date.year < 1900 or patent.application_date.year > datetime.now().year:
                    return False
            
            # 检查标题长度
            if hasattr(patent, 'title') and patent.title:
                if len(patent.title) < 5 or len(patent.title) > 500:
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _calculate_consistency_score(self, patents: List) -> float:
        """计算数据一致性评分."""
        if not patents:
            return 0.0
        
        try:
            # 检查数据格式一致性
            consistent_count = 0
            total_count = len(patents)
            
            for patent in patents:
                # 检查必要字段的数据类型一致性
                if (hasattr(patent, 'applicants') and isinstance(patent.applicants, list) and
                    hasattr(patent, 'ipc_classes') and isinstance(patent.ipc_classes, list)):
                    consistent_count += 1
            
            return consistent_count / total_count if total_count > 0 else 0.0
            
        except Exception:
            return 0.0
    
    def _calculate_timeliness_score(self, patents: List) -> float:
        """计算数据时效性评分."""
        if not patents:
            return 0.0
        
        try:
            current_year = datetime.now().year
            recent_patents = 0
            total_patents = len(patents)
            
            for patent in patents:
                if hasattr(patent, 'application_date') and patent.application_date:
                    # 近5年的专利认为是较新的
                    if current_year - patent.application_date.year <= 5:
                        recent_patents += 1
            
            return recent_patents / total_patents if total_patents > 0 else 0.0
            
        except Exception:
            return 0.0
    
    # 监控和指标相关方法
    def _update_patent_metrics(self, processing_time: float, success: bool):
        """更新专利处理指标."""
        self._patent_metrics['total_patent_requests'] += 1
        
        if success:
            self._patent_metrics['successful_patent_analyses'] += 1
        else:
            self._patent_metrics['failed_patent_analyses'] += 1
        
        # 更新平均处理时间
        total_requests = self._patent_metrics['total_patent_requests']
        current_avg = self._patent_metrics['average_patent_processing_time']
        self._patent_metrics['average_patent_processing_time'] = (
            (current_avg * (total_requests - 1) + processing_time) / total_requests
        )
    
    def get_patent_metrics(self) -> Dict[str, Any]:
        """获取专利处理指标."""
        base_metrics = self.get_metrics()
        base_metrics.update(self._patent_metrics)
        
        # 计算成功率
        total_requests = self._patent_metrics['total_patent_requests']
        if total_requests > 0:
            success_rate = (self._patent_metrics['successful_patent_analyses'] / total_requests) * 100
            base_metrics['patent_success_rate'] = success_rate
        
        # 添加数据源状态
        base_metrics['active_data_sources'] = len([
            s for s in self._patent_data_sources.values() 
            if s.get('status') == 'active'
        ])
        
        return base_metrics
    
    # 健康检查集成方法
    async def _register_to_health_check(self):
        """注册到健康检查系统."""
        try:
            # 这里需要获取健康检查管理器实例
            # 在实际实现中，应该通过依赖注入或服务定位器获取
            from ...utils.health_check_manager import HealthCheckManager
            from ..utils.health_check import PatentHealthChecker
            
            # 注意：这里需要在实际集成时获取正确的健康检查管理器实例
            # health_check_manager = get_health_check_manager()  # 需要实现
            # patent_health_checker = PatentHealthChecker(health_check_manager)
            # await patent_health_checker.register_patent_agent(self.agent_id, self)
            
            self.patent_logger.info(f"Patent agent {self.agent_id} registered to health check system")
            
        except Exception as e:
            self.patent_logger.warning(f"Failed to register patent agent {self.agent_id} to health check: {str(e)}")
    
    async def _unregister_from_health_check(self):
        """从健康检查系统注销."""
        try:
            # 这里需要获取健康检查管理器实例
            # 在实际实现中，应该通过依赖注入或服务定位器获取
            from ...utils.health_check_manager import HealthCheckManager
            from ..utils.health_check import PatentHealthChecker
            
            # 注意：这里需要在实际集成时获取正确的健康检查管理器实例
            # health_check_manager = get_health_check_manager()  # 需要实现
            # patent_health_checker = PatentHealthChecker(health_check_manager)
            # await patent_health_checker.unregister_patent_agent(self.agent_id)
            
            self.patent_logger.info(f"Patent agent {self.agent_id} unregistered from health check system")
            
        except Exception as e:
            self.patent_logger.warning(f"Failed to unregister patent agent {self.agent_id} from health check: {str(e)}")
    
    # 抽象方法，子类必须实现
    @abstractmethod
    async def _process_patent_request_specific(self, request: PatentAnalysisRequest) -> Any:
        """子类特定的专利请求处理逻辑."""
        pass