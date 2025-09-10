"""专利数据处理监控集成."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from collections import defaultdict

from ...utils.monitoring import MonitoringSystem, metrics_collector
from ..storage.database import PatentDatabaseManager


logger = logging.getLogger(__name__)


class PatentMonitoringSystem:
    """专利监控系统，集成现有MonitoringSystem."""
    
    def __init__(self, base_monitoring: MonitoringSystem, db_manager: PatentDatabaseManager):
        self.base_monitoring = base_monitoring
        self.db_manager = db_manager
        self.is_monitoring = False
        self._monitoring_task = None
        
        # 专利特定指标
        self.patent_metrics = {
            'data_collection_count': 0,
            'data_processing_count': 0,
            'quality_validation_count': 0,
            'database_operations_count': 0,
            'error_count': 0,
            'average_quality_score': 0.0,
            'total_patents_stored': 0,
            'datasets_processed': 0
        }
    
    async def initialize(self):
        """初始化专利监控系统."""
        try:
            logger.info("Initializing patent monitoring system")
            
            # 初始化基础监控系统
            await self.base_monitoring.initialize()
            
            # 注册专利特定指标
            self._register_patent_metrics()
            
            logger.info("Patent monitoring system initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing patent monitoring system: {str(e)}")
            return False
    
    async def start_monitoring(self):
        """启动专利监控."""
        try:
            logger.info("Starting patent monitoring")
            
            # 启动基础监控
            await self.base_monitoring.start_monitoring()
            
            self.is_monitoring = True
            
            # 启动专利监控任务
            self._monitoring_task = asyncio.create_task(self._patent_monitoring_loop())
            
            logger.info("Patent monitoring started successfully")
            
        except Exception as e:
            logger.error(f"Error starting patent monitoring: {str(e)}")
            raise
    
    async def stop_monitoring(self):
        """停止专利监控."""
        try:
            logger.info("Stopping patent monitoring")
            
            self.is_monitoring = False
            
            # 停止专利监控任务
            if self._monitoring_task:
                self._monitoring_task.cancel()
                try:
                    await self._monitoring_task
                except asyncio.CancelledError:
                    pass
            
            # 停止基础监控
            await self.base_monitoring.stop_monitoring()
            
            logger.info("Patent monitoring stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping patent monitoring: {str(e)}")
    
    async def _patent_monitoring_loop(self):
        """专利监控循环."""
        while self.is_monitoring:
            try:
                # 收集专利特定指标
                await self._collect_patent_metrics()
                
                # 检查数据库健康状态
                await self._check_database_health()
                
                # 生成专利监控报告
                await self._generate_patent_report()
                
                # 等待下一次监控周期
                await asyncio.sleep(60)  # 每分钟监控一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in patent monitoring loop: {str(e)}")
                await asyncio.sleep(30)  # 出错时等待30秒
    
    def _register_patent_metrics(self):
        """注册专利特定指标."""
        # 注册专利数据收集指标
        metrics_collector.record_metric(
            "patent.monitoring_initialized",
            1,
            tags={"component": "patent_monitoring", "unit": "count"}
        )
    
    async def _collect_patent_metrics(self):
        """收集专利指标."""
        try:
            # 获取数据库统计信息
            db_stats = await self.db_manager.get_database_stats()
            
            if db_stats:
                # 记录专利总数
                metrics_collector.record_metric(
                    "patent.total_patents_stored",
                    db_stats.get('total_patents', 0),
                    tags={"unit": "count"}
                )
                
                # 记录数据集总数
                metrics_collector.record_metric(
                    "patent.total_datasets",
                    db_stats.get('total_datasets', 0),
                    tags={"unit": "count"}
                )
                
                # 记录平均质量评分
                avg_quality = db_stats.get('average_quality_score', 0.0)
                metrics_collector.record_metric(
                    "patent.average_quality_score",
                    avg_quality,
                    tags={"unit": "score"}
                )
                
                # 记录按国家分布的专利数量
                for country, count in db_stats.get('patents_by_country', {}).items():
                    metrics_collector.record_metric(
                        "patent.patents_by_country",
                        count,
                        tags={"country": country, "unit": "count"}
                    )
                
                # 记录按状态分布的专利数量
                for status, count in db_stats.get('patents_by_status', {}).items():
                    metrics_collector.record_metric(
                        "patent.patents_by_status",
                        count,
                        tags={"status": status, "unit": "count"}
                    )
                
                # 更新内部指标
                self.patent_metrics['total_patents_stored'] = db_stats.get('total_patents', 0)
                self.patent_metrics['datasets_processed'] = db_stats.get('total_datasets', 0)
                self.patent_metrics['average_quality_score'] = avg_quality
            
        except Exception as e:
            logger.error(f"Error collecting patent metrics: {str(e)}")
            self.patent_metrics['error_count'] += 1
    
    async def _check_database_health(self):
        """检查数据库健康状态."""
        try:
            # 简单的数据库连接测试
            stats = await self.db_manager.get_database_stats()
            
            if stats is not None:
                # 数据库健康
                metrics_collector.record_metric(
                    "patent.database_health",
                    1,
                    tags={"status": "healthy", "unit": "boolean"}
                )
            else:
                # 数据库异常
                metrics_collector.record_metric(
                    "patent.database_health",
                    0,
                    tags={"status": "unhealthy", "unit": "boolean"}
                )
                logger.warning("Patent database health check failed")
            
        except Exception as e:
            logger.error(f"Database health check error: {str(e)}")
            metrics_collector.record_metric(
                "patent.database_health",
                0,
                tags={"status": "error", "unit": "boolean"}
            )
    
    async def _generate_patent_report(self):
        """生成专利监控报告."""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'patent_metrics': self.patent_metrics.copy(),
                'database_stats': await self.db_manager.get_database_stats(),
                'monitoring_status': 'active' if self.is_monitoring else 'inactive'
            }
            
            # 记录报告生成
            metrics_collector.record_metric(
                "patent.monitoring_report_generated",
                1,
                tags={"unit": "count"}
            )
            
            logger.debug(f"Generated patent monitoring report: {report}")
            
        except Exception as e:
            logger.error(f"Error generating patent report: {str(e)}")
    
    def track_data_collection(self, patent_count: int, duration: float, success: bool):
        """跟踪数据收集操作."""
        try:
            # 记录数据收集指标
            metrics_collector.record_metric(
                "patent.data_collection_duration",
                duration,
                tags={"unit": "seconds", "patent_count": str(patent_count)}
            )
            
            metrics_collector.record_metric(
                "patent.data_collection_count",
                1,
                tags={"success": str(success), "unit": "count"}
            )
            
            if success:
                metrics_collector.record_metric(
                    "patent.patents_collected",
                    patent_count,
                    tags={"unit": "count"}
                )
                
                self.patent_metrics['data_collection_count'] += 1
            else:
                self.patent_metrics['error_count'] += 1
            
            logger.info(f"Tracked data collection: {patent_count} patents, {duration:.2f}s, success={success}")
            
        except Exception as e:
            logger.error(f"Error tracking data collection: {str(e)}")
    
    def track_data_processing(self, dataset_id: str, patent_count: int, duration: float, 
                            quality_score: float, success: bool):
        """跟踪数据处理操作."""
        try:
            # 记录数据处理指标
            metrics_collector.record_metric(
                "patent.data_processing_duration",
                duration,
                tags={"unit": "seconds", "patent_count": str(patent_count)}
            )
            
            metrics_collector.record_metric(
                "patent.data_processing_count",
                1,
                tags={"success": str(success), "unit": "count"}
            )
            
            if success:
                metrics_collector.record_metric(
                    "patent.dataset_quality_score",
                    quality_score,
                    tags={"dataset_id": dataset_id, "unit": "score"}
                )
                
                self.patent_metrics['data_processing_count'] += 1
                
                # 更新平均质量评分
                current_avg = self.patent_metrics['average_quality_score']
                processed_count = self.patent_metrics['data_processing_count']
                new_avg = ((current_avg * (processed_count - 1)) + quality_score) / processed_count
                self.patent_metrics['average_quality_score'] = new_avg
            else:
                self.patent_metrics['error_count'] += 1
            
            logger.info(f"Tracked data processing: dataset {dataset_id}, {patent_count} patents, quality={quality_score:.2f}")
            
        except Exception as e:
            logger.error(f"Error tracking data processing: {str(e)}")
    
    def track_quality_validation(self, dataset_id: str, total_records: int, valid_records: int,
                               quality_score: float, duration: float, success: bool):
        """跟踪质量验证操作."""
        try:
            # 记录质量验证指标
            metrics_collector.record_metric(
                "patent.quality_validation_duration",
                duration,
                tags={"unit": "seconds", "record_count": str(total_records)}
            )
            
            metrics_collector.record_metric(
                "patent.quality_validation_count",
                1,
                tags={"success": str(success), "unit": "count"}
            )
            
            if success:
                # 记录验证结果
                validation_rate = valid_records / total_records if total_records > 0 else 0.0
                
                metrics_collector.record_metric(
                    "patent.validation_rate",
                    validation_rate,
                    tags={"dataset_id": dataset_id, "unit": "rate"}
                )
                
                metrics_collector.record_metric(
                    "patent.quality_validation_score",
                    quality_score,
                    tags={"dataset_id": dataset_id, "unit": "score"}
                )
                
                self.patent_metrics['quality_validation_count'] += 1
            else:
                self.patent_metrics['error_count'] += 1
            
            logger.info(f"Tracked quality validation: dataset {dataset_id}, {valid_records}/{total_records} valid")
            
        except Exception as e:
            logger.error(f"Error tracking quality validation: {str(e)}")
    
    def track_database_operation(self, operation: str, record_count: int, duration: float, success: bool):
        """跟踪数据库操作."""
        try:
            # 记录数据库操作指标
            metrics_collector.record_metric(
                "patent.database_operation_duration",
                duration,
                tags={"operation": operation, "unit": "seconds", "record_count": str(record_count)}
            )
            
            metrics_collector.record_metric(
                "patent.database_operation_count",
                1,
                tags={"operation": operation, "success": str(success), "unit": "count"}
            )
            
            if success:
                self.patent_metrics['database_operations_count'] += 1
            else:
                self.patent_metrics['error_count'] += 1
            
            logger.info(f"Tracked database operation: {operation}, {record_count} records, {duration:.2f}s")
            
        except Exception as e:
            logger.error(f"Error tracking database operation: {str(e)}")
    
    async def get_patent_metrics(self) -> Dict[str, Any]:
        """获取专利监控指标."""
        try:
            # 获取基础系统指标
            base_metrics = await self.base_monitoring.get_system_metrics()
            
            # 获取数据库统计
            db_stats = await self.db_manager.get_database_stats()
            
            # 合并专利指标
            patent_metrics = {
                'patent_specific_metrics': self.patent_metrics.copy(),
                'database_statistics': db_stats,
                'base_system_metrics': base_metrics,
                'monitoring_status': {
                    'is_active': self.is_monitoring,
                    'last_update': datetime.now().isoformat()
                }
            }
            
            return patent_metrics
            
        except Exception as e:
            logger.error(f"Error getting patent metrics: {str(e)}")
            return {}
    
    async def health_check(self) -> bool:
        """专利监控系统健康检查."""
        try:
            # 检查基础监控系统
            base_health = await self.base_monitoring.health_check()
            
            # 检查数据库连接
            db_stats = await self.db_manager.get_database_stats()
            db_health = db_stats is not None
            
            # 检查监控任务状态
            task_health = self.is_monitoring and (self._monitoring_task is None or not self._monitoring_task.done())
            
            overall_health = base_health and db_health and task_health
            
            # 记录健康检查结果
            metrics_collector.record_metric(
                "patent.monitoring_health_check",
                1 if overall_health else 0,
                tags={"status": "healthy" if overall_health else "unhealthy", "unit": "boolean"}
            )
            
            return overall_health
            
        except Exception as e:
            logger.error(f"Patent monitoring health check failed: {str(e)}")
            return False
    
    async def shutdown(self):
        """关闭专利监控系统."""
        try:
            logger.info("Shutting down patent monitoring system")
            
            # 停止监控
            await self.stop_monitoring()
            
            # 关闭基础监控系统
            await self.base_monitoring.shutdown()
            
            # 清理数据库连接
            await self.db_manager.cleanup()
            
            logger.info("Patent monitoring system shutdown completed")
            
        except Exception as e:
            logger.error(f"Error shutting down patent monitoring system: {str(e)}")


# 全局专利监控实例（需要在应用启动时初始化）
patent_monitoring_system: Optional[PatentMonitoringSystem] = None


def get_patent_monitoring() -> Optional[PatentMonitoringSystem]:
    """获取专利监控系统实例."""
    return patent_monitoring_system


async def initialize_patent_monitoring(base_monitoring: MonitoringSystem, db_manager: PatentDatabaseManager) -> PatentMonitoringSystem:
    """初始化专利监控系统."""
    global patent_monitoring_system
    
    patent_monitoring_system = PatentMonitoringSystem(base_monitoring, db_manager)
    await patent_monitoring_system.initialize()
    
    return patent_monitoring_system