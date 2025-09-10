"""Patent data processing service integrating all data processing components."""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from ..models.data import Patent, PatentDataset, PatentDataQuality
from ..utils.data_processor import PatentDataProcessor
from ..utils.database import PatentDatabaseManager
from ..utils.validation import PatentDataQualityValidator, DatasetValidationResult
from ...utils.monitoring import metrics_collector, measure_performance, MonitoringSystem


class PatentDataProcessingService:
    """专利数据处理服务，集成现有监控和数据库存储机制."""
    
    def __init__(self, monitoring_system: Optional[MonitoringSystem] = None):
        """初始化数据处理服务."""
        self.logger = logging.getLogger(__name__)
        
        # 集成现有监控系统
        self.monitoring_system = monitoring_system
        
        # 初始化组件
        self.db_manager = PatentDatabaseManager()
        self.data_processor = PatentDataProcessor(self.db_manager)
        self.quality_validator = PatentDataQualityValidator()
        
        # 服务状态
        self.is_initialized = False
        self.processing_queue = asyncio.Queue()
        self.active_tasks = {}
        
    async def initialize(self) -> bool:
        """初始化服务."""
        try:
            with measure_performance("patent.service.initialization"):
                # 初始化数据库
                await self.db_manager.initialize()
                
                # 启动监控
                if self.monitoring_system:
                    await self.monitoring_system.start_monitoring()
                
                self.is_initialized = True
                
                # 记录监控指标
                metrics_collector.record_metric(
                    "patent.service.initialized", 
                    1, 
                    tags={"status": "success"}
                )
                
                self.logger.info("Patent data processing service initialized successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to initialize patent data processing service: {str(e)}")
            
            # 记录错误监控指标
            metrics_collector.record_metric(
                "patent.service.initialization_error", 
                1, 
                tags={"error": str(e)[:50]}
            )
            
            return False
    
    async def process_patent_data(self, 
                                patents: List[Patent],
                                dataset_id: Optional[str] = None,
                                processing_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        处理专利数据的主要接口.
        
        Args:
            patents: 专利数据列表
            dataset_id: 数据集ID
            processing_options: 处理选项
            
        Returns:
            处理结果字典
        """
        if not self.is_initialized:
            raise RuntimeError("Service not initialized")
        
        # 生成任务ID
        task_id = str(uuid4())
        dataset_id = dataset_id or f"dataset_{int(datetime.now().timestamp())}"
        
        # 默认处理选项
        options = processing_options or {}
        enable_standardization = options.get('enable_standardization', True)
        enable_deduplication = options.get('enable_deduplication', True)
        enable_quality_control = options.get('enable_quality_control', True)
        save_to_database = options.get('save_to_database', True)
        
        try:
            with measure_performance("patent.service.process_data"):
                self.logger.info(f"Starting data processing task {task_id} for dataset {dataset_id}")
                
                # 记录任务开始
                self.active_tasks[task_id] = {
                    'dataset_id': dataset_id,
                    'start_time': datetime.now(),
                    'status': 'processing',
                    'input_count': len(patents)
                }
                
                # 记录开始监控指标
                metrics_collector.record_metric(
                    "patent.service.task_started", 
                    1, 
                    tags={
                        "task_id": task_id,
                        "dataset_id": dataset_id,
                        "input_count": str(len(patents))
                    }
                )
                
                # 执行数据处理
                processed_patents, quality_assessment, validation_result = await self.data_processor.process_patent_dataset(
                    patents=patents,
                    dataset_id=dataset_id,
                    enable_standardization=enable_standardization,
                    enable_deduplication=enable_deduplication,
                    enable_quality_control=enable_quality_control,
                    save_to_database=save_to_database
                )
                
                # 更新任务状态
                self.active_tasks[task_id].update({
                    'status': 'completed',
                    'end_time': datetime.now(),
                    'output_count': len(processed_patents),
                    'quality_score': quality_assessment.overall_score
                })
                
                # 生成处理报告
                processing_report = await self._generate_processing_report(
                    task_id, dataset_id, processed_patents, quality_assessment, validation_result
                )
                
                # 记录完成监控指标
                metrics_collector.record_metric(
                    "patent.service.task_completed", 
                    1, 
                    tags={
                        "task_id": task_id,
                        "dataset_id": dataset_id,
                        "output_count": str(len(processed_patents)),
                        "quality_score": f"{quality_assessment.overall_score:.2f}"
                    }
                )
                
                self.logger.info(f"Data processing task {task_id} completed successfully")
                
                return {
                    'task_id': task_id,
                    'dataset_id': dataset_id,
                    'status': 'success',
                    'processed_patents': processed_patents,
                    'quality_assessment': quality_assessment,
                    'validation_result': validation_result,
                    'processing_report': processing_report,
                    'processing_stats': self.data_processor.get_processing_stats()
                }
                
        except Exception as e:
            # 更新任务状态为错误
            if task_id in self.active_tasks:
                self.active_tasks[task_id].update({
                    'status': 'error',
                    'end_time': datetime.now(),
                    'error': str(e)
                })
            
            self.logger.error(f"Data processing task {task_id} failed: {str(e)}")
            
            # 记录错误监控指标
            metrics_collector.record_metric(
                "patent.service.task_error", 
                1, 
                tags={
                    "task_id": task_id,
                    "dataset_id": dataset_id,
                    "error_type": type(e).__name__
                }
            )
            
            return {
                'task_id': task_id,
                'dataset_id': dataset_id,
                'status': 'error',
                'error': str(e),
                'processing_stats': self.data_processor.get_processing_stats()
            }
        
        finally:
            # 清理完成的任务
            if task_id in self.active_tasks:
                task_info = self.active_tasks.pop(task_id)
                self.logger.debug(f"Cleaned up task {task_id}: {task_info}")
    
    async def validate_patent_data(self, 
                                 patents: List[Patent], 
                                 dataset_id: Optional[str] = None) -> Dict[str, Any]:
        """
        验证专利数据质量.
        
        Args:
            patents: 专利数据列表
            dataset_id: 数据集ID
            
        Returns:
            验证结果字典
        """
        try:
            with measure_performance("patent.service.validate_data"):
                dataset_id = dataset_id or f"validation_{int(datetime.now().timestamp())}"
                
                self.logger.info(f"Starting data validation for dataset {dataset_id}")
                
                # 执行验证
                validation_result, quality_assessment = await self.quality_validator.validate_and_assess_quality(
                    patents, dataset_id
                )
                
                # 记录监控指标
                metrics_collector.record_metric(
                    "patent.service.validation_completed", 
                    1, 
                    tags={
                        "dataset_id": dataset_id,
                        "total_patents": str(len(patents)),
                        "valid_patents": str(validation_result.valid_patents),
                        "quality_score": f"{quality_assessment.overall_score:.2f}"
                    }
                )
                
                return {
                    'dataset_id': dataset_id,
                    'status': 'success',
                    'validation_result': validation_result,
                    'quality_assessment': quality_assessment,
                    'summary': {
                        'total_patents': len(patents),
                        'valid_patents': validation_result.valid_patents,
                        'invalid_patents': validation_result.invalid_patents,
                        'validation_score': validation_result.validation_score,
                        'quality_score': quality_assessment.overall_score
                    }
                }
                
        except Exception as e:
            self.logger.error(f"Data validation failed for dataset {dataset_id}: {str(e)}")
            
            # 记录错误监控指标
            metrics_collector.record_metric(
                "patent.service.validation_error", 
                1, 
                tags={
                    "dataset_id": dataset_id or "unknown",
                    "error_type": type(e).__name__
                }
            )
            
            return {
                'dataset_id': dataset_id,
                'status': 'error',
                'error': str(e)
            }
    
    async def get_processing_status(self, task_id: str) -> Dict[str, Any]:
        """获取处理任务状态."""
        try:
            if task_id in self.active_tasks:
                task_info = self.active_tasks[task_id].copy()
                
                # 计算处理时间
                if 'end_time' in task_info:
                    duration = (task_info['end_time'] - task_info['start_time']).total_seconds()
                else:
                    duration = (datetime.now() - task_info['start_time']).total_seconds()
                
                task_info['duration_seconds'] = duration
                
                return {
                    'task_id': task_id,
                    'found': True,
                    'task_info': task_info
                }
            else:
                return {
                    'task_id': task_id,
                    'found': False,
                    'message': 'Task not found or already completed'
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get processing status for task {task_id}: {str(e)}")
            return {
                'task_id': task_id,
                'found': False,
                'error': str(e)
            }
    
    async def get_dataset_history(self, dataset_id: str) -> Dict[str, Any]:
        """获取数据集处理历史."""
        try:
            with measure_performance("patent.service.get_history"):
                history = await self.data_processor.get_processing_history(dataset_id)
                
                # 记录监控指标
                metrics_collector.record_metric(
                    "patent.service.history_retrieved", 
                    1, 
                    tags={"dataset_id": dataset_id}
                )
                
                return {
                    'dataset_id': dataset_id,
                    'status': 'success',
                    'history': history
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get dataset history for {dataset_id}: {str(e)}")
            
            # 记录错误监控指标
            metrics_collector.record_metric(
                "patent.service.history_error", 
                1, 
                tags={"dataset_id": dataset_id, "error": str(e)[:50]}
            )
            
            return {
                'dataset_id': dataset_id,
                'status': 'error',
                'error': str(e)
            }
    
    async def get_service_metrics(self) -> Dict[str, Any]:
        """获取服务监控指标，集成现有MonitoringSystem."""
        try:
            with measure_performance("patent.service.get_metrics"):
                # 获取数据处理性能监控
                processing_performance = await self.data_processor.monitor_processing_performance()
                
                # 获取当前活跃任务
                active_tasks_info = {
                    'count': len(self.active_tasks),
                    'tasks': list(self.active_tasks.keys())
                }
                
                # 获取系统监控指标（如果监控系统可用）
                system_metrics = {}
                if self.monitoring_system:
                    try:
                        system_metrics = await self.monitoring_system.get_system_metrics()
                    except Exception as e:
                        self.logger.warning(f"Failed to get system metrics: {str(e)}")
                
                return {
                    'timestamp': datetime.now().isoformat(),
                    'service_status': 'healthy' if self.is_initialized else 'not_initialized',
                    'processing_performance': processing_performance,
                    'active_tasks': active_tasks_info,
                    'system_metrics': system_metrics
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get service metrics: {str(e)}")
            return {
                'timestamp': datetime.now().isoformat(),
                'service_status': 'error',
                'error': str(e)
            }
    
    async def _generate_processing_report(self, 
                                        task_id: str,
                                        dataset_id: str,
                                        processed_patents: List[Patent],
                                        quality_assessment: PatentDataQuality,
                                        validation_result: DatasetValidationResult) -> Dict[str, Any]:
        """生成处理报告."""
        try:
            task_info = self.active_tasks.get(task_id, {})
            processing_stats = self.data_processor.get_processing_stats()
            
            # 计算处理时间
            start_time = task_info.get('start_time')
            end_time = task_info.get('end_time', datetime.now())
            duration = (end_time - start_time).total_seconds() if start_time else 0
            
            report = {
                'task_id': task_id,
                'dataset_id': dataset_id,
                'processing_summary': {
                    'input_patents': task_info.get('input_count', 0),
                    'output_patents': len(processed_patents),
                    'processing_duration_seconds': duration,
                    'patents_per_second': len(processed_patents) / duration if duration > 0 else 0
                },
                'processing_steps': {
                    'standardization': {
                        'enabled': True,
                        'processed_count': processing_stats.get('standardized_count', 0)
                    },
                    'deduplication': {
                        'enabled': True,
                        'duplicates_removed': processing_stats.get('duplicates_removed', 0)
                    },
                    'quality_control': {
                        'enabled': True,
                        'invalid_removed': processing_stats.get('invalid_patents_removed', 0),
                        'issues_fixed': processing_stats.get('quality_issues_fixed', 0)
                    }
                },
                'quality_assessment': {
                    'overall_score': quality_assessment.overall_score,
                    'completeness_score': quality_assessment.completeness_score,
                    'accuracy_score': quality_assessment.accuracy_score,
                    'consistency_score': quality_assessment.consistency_score,
                    'timeliness_score': quality_assessment.timeliness_score,
                    'issues_count': len(quality_assessment.issues),
                    'issues': quality_assessment.issues
                },
                'validation_summary': {
                    'total_patents': validation_result.total_patents,
                    'valid_patents': validation_result.valid_patents,
                    'invalid_patents': validation_result.invalid_patents,
                    'validation_score': validation_result.validation_score,
                    'summary_issues': validation_result.summary_issues
                },
                'recommendations': self._generate_recommendations(quality_assessment, validation_result)
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to generate processing report: {str(e)}")
            return {
                'task_id': task_id,
                'dataset_id': dataset_id,
                'error': f"Failed to generate report: {str(e)}"
            }
    
    def _generate_recommendations(self, 
                                quality_assessment: PatentDataQuality, 
                                validation_result: DatasetValidationResult) -> List[str]:
        """生成改进建议."""
        recommendations = []
        
        try:
            # 基于质量评分生成建议
            if quality_assessment.overall_score < 0.7:
                recommendations.append("数据质量较低，建议检查数据源和收集流程")
            
            if quality_assessment.completeness_score < 0.8:
                recommendations.append("数据完整性不足，建议补充缺失字段")
            
            if quality_assessment.accuracy_score < 0.8:
                recommendations.append("数据准确性有问题，建议加强数据验证")
            
            if quality_assessment.consistency_score < 0.8:
                recommendations.append("数据格式不一致，建议统一数据标准")
            
            if quality_assessment.timeliness_score < 0.6:
                recommendations.append("数据时效性较差，建议更新数据源")
            
            # 基于验证结果生成建议
            if validation_result.validation_score < 0.8:
                recommendations.append("验证通过率较低，建议优化数据处理流程")
            
            if validation_result.invalid_patents > validation_result.total_patents * 0.2:
                recommendations.append("无效专利比例过高，建议加强数据预处理")
            
            # 基于具体问题生成建议
            for issue in quality_assessment.issues:
                if "缺少摘要" in issue:
                    recommendations.append("建议从其他数据源补充专利摘要信息")
                elif "缺少IPC分类" in issue:
                    recommendations.append("建议使用自动分类工具补充IPC分类")
                elif "日期" in issue:
                    recommendations.append("建议检查和修正专利日期信息")
            
            # 如果没有问题，给出积极建议
            if not recommendations:
                recommendations.append("数据质量良好，可以进行后续分析")
            
        except Exception as e:
            self.logger.warning(f"Failed to generate recommendations: {str(e)}")
            recommendations.append("无法生成建议，请检查数据处理结果")
        
        return recommendations
    
    async def cleanup_old_data(self, days: int = 30) -> Dict[str, Any]:
        """清理旧数据."""
        try:
            with measure_performance("patent.service.cleanup"):
                success = await self.db_manager.cleanup_old_records(days)
                
                # 记录监控指标
                metrics_collector.record_metric(
                    "patent.service.cleanup_completed", 
                    1, 
                    tags={"days": str(days), "success": str(success)}
                )
                
                return {
                    'status': 'success' if success else 'failed',
                    'days': days,
                    'message': f'Cleanup completed for records older than {days} days'
                }
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {str(e)}")
            
            # 记录错误监控指标
            metrics_collector.record_metric(
                "patent.service.cleanup_error", 
                1, 
                tags={"days": str(days), "error": str(e)[:50]}
            )
            
            return {
                'status': 'error',
                'days': days,
                'error': str(e)
            }
    
    async def shutdown(self):
        """关闭服务."""
        try:
            self.logger.info("Shutting down patent data processing service")
            
            # 等待活跃任务完成
            if self.active_tasks:
                self.logger.info(f"Waiting for {len(self.active_tasks)} active tasks to complete")
                # 这里可以实现更复杂的任务取消逻辑
            
            # 停止监控
            if self.monitoring_system:
                await self.monitoring_system.stop_monitoring()
            
            self.is_initialized = False
            
            # 记录监控指标
            metrics_collector.record_metric(
                "patent.service.shutdown", 
                1, 
                tags={"status": "success"}
            )
            
            self.logger.info("Patent data processing service shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during service shutdown: {str(e)}")
            
            # 记录错误监控指标
            metrics_collector.record_metric(
                "patent.service.shutdown_error", 
                1, 
                tags={"error": str(e)[:50]}
            )