"""专利监控系统集成工具."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from ...utils.monitoring import (
    MonitoringSystem,
    track_patent_analysis,
    track_patent_data_collection,
    track_patent_search,
    track_patent_report_generation,
    track_patent_api_call
)
from ...utils.health_check_manager import HealthCheckManager
from .health_check import PatentHealthChecker
from ...utils.logging import get_logger, LogCategory

logger = get_logger("multi_agent_service.patent.monitoring_integration")


class PatentMonitoringIntegrator:
    """专利监控系统集成器."""
    
    def __init__(self, monitoring_system: MonitoringSystem, health_check_manager: HealthCheckManager):
        self.monitoring_system = monitoring_system
        self.health_check_manager = health_check_manager
        self.patent_health_checker = PatentHealthChecker(health_check_manager)
        self.logger = logger
        
        # 专利Agent注册表
        self._registered_agents: Dict[str, Any] = {}
        
        # 监控配置
        self.monitoring_config = {
            'enable_performance_tracking': True,
            'enable_health_monitoring': True,
            'enable_alerting': True,
            'metrics_retention_hours': 24,
            'health_check_interval_seconds': 30,
            'alert_thresholds': {
                'analysis_failure_rate': 0.1,
                'data_quality_threshold': 0.7,
                'api_response_time_threshold': 30.0,
                'cache_hit_rate_threshold': 0.5
            }
        }
    
    async def initialize(self) -> bool:
        """初始化专利监控集成."""
        try:
            self.logger.info("Initializing patent monitoring integration", category=LogCategory.SYSTEM)
            
            # 注册专利指标到监控系统
            await self._register_patent_metrics()
            
            # 配置告警阈值
            self.monitoring_system.update_patent_alert_thresholds(
                self.monitoring_config['alert_thresholds']
            )
            
            self.logger.info("Patent monitoring integration initialized successfully", category=LogCategory.SYSTEM)
            return True
            
        except Exception as e:
            self.logger.error(
                f"Failed to initialize patent monitoring integration: {str(e)}",
                category=LogCategory.SYSTEM
            )
            return False
    
    async def register_patent_agent(self, agent_id: str, agent_instance, agent_type: str) -> None:
        """注册专利Agent到监控系统."""
        try:
            # 注册到健康检查系统
            if self.monitoring_config['enable_health_monitoring']:
                await self.patent_health_checker.register_patent_agent(agent_id, agent_instance)
            
            # 注册到监控系统
            if self.monitoring_config['enable_performance_tracking']:
                self.monitoring_system.register_patent_agent(agent_id, agent_type, {
                    'agent_instance': agent_instance,
                    'registered_at': datetime.now().isoformat()
                })
            
            # 记录到本地注册表
            self._registered_agents[agent_id] = {
                'agent_instance': agent_instance,
                'agent_type': agent_type,
                'registered_at': datetime.now(),
                'health_monitoring': self.monitoring_config['enable_health_monitoring'],
                'performance_tracking': self.monitoring_config['enable_performance_tracking']
            }
            
            self.logger.info(
                f"Patent agent registered for monitoring: {agent_id} ({agent_type})",
                category=LogCategory.SYSTEM,
                agent_id=agent_id,
                agent_type=agent_type
            )
            
        except Exception as e:
            self.logger.error(
                f"Failed to register patent agent {agent_id} for monitoring: {str(e)}",
                category=LogCategory.SYSTEM,
                agent_id=agent_id
            )
    
    async def unregister_patent_agent(self, agent_id: str) -> None:
        """从监控系统注销专利Agent."""
        try:
            # 从健康检查系统注销
            await self.patent_health_checker.unregister_patent_agent(agent_id)
            
            # 从监控系统注销
            self.monitoring_system.unregister_patent_agent(agent_id)
            
            # 从本地注册表移除
            if agent_id in self._registered_agents:
                del self._registered_agents[agent_id]
            
            self.logger.info(
                f"Patent agent unregistered from monitoring: {agent_id}",
                category=LogCategory.SYSTEM,
                agent_id=agent_id
            )
            
        except Exception as e:
            self.logger.error(
                f"Failed to unregister patent agent {agent_id} from monitoring: {str(e)}",
                category=LogCategory.SYSTEM,
                agent_id=agent_id
            )
    
    async def track_patent_operation(
        self,
        operation_type: str,
        agent_id: str,
        duration: float,
        success: bool,
        **kwargs
    ) -> None:
        """跟踪专利操作指标."""
        try:
            if not self.monitoring_config['enable_performance_tracking']:
                return
            
            agent_info = self._registered_agents.get(agent_id)
            if not agent_info:
                self.logger.warning(f"Agent {agent_id} not registered for monitoring")
                return
            
            agent_type = agent_info['agent_type']
            
            # 根据操作类型调用相应的跟踪函数
            if operation_type == 'analysis':
                track_patent_analysis(
                    agent_id=agent_id,
                    agent_type=agent_type,
                    analysis_type=kwargs.get('analysis_type', 'general'),
                    duration=duration,
                    success=success,
                    data_quality_score=kwargs.get('data_quality_score'),
                    patents_processed=kwargs.get('patents_processed')
                )
            
            elif operation_type == 'data_collection':
                track_patent_data_collection(
                    agent_id=agent_id,
                    data_source=kwargs.get('data_source', 'unknown'),
                    duration=duration,
                    success=success,
                    patents_collected=kwargs.get('patents_collected'),
                    cache_hit=kwargs.get('cache_hit', False)
                )
            
            elif operation_type == 'search':
                track_patent_search(
                    agent_id=agent_id,
                    search_engine=kwargs.get('search_engine', 'unknown'),
                    duration=duration,
                    success=success,
                    results_count=kwargs.get('results_count'),
                    search_type=kwargs.get('search_type', 'general')
                )
            
            elif operation_type == 'report_generation':
                track_patent_report_generation(
                    agent_id=agent_id,
                    report_type=kwargs.get('report_type', 'general'),
                    duration=duration,
                    success=success,
                    report_size_kb=kwargs.get('report_size_kb'),
                    charts_generated=kwargs.get('charts_generated')
                )
            
            elif operation_type == 'api_call':
                track_patent_api_call(
                    api_name=kwargs.get('api_name', 'unknown'),
                    endpoint=kwargs.get('endpoint', 'unknown'),
                    duration=duration,
                    success=success,
                    response_size_kb=kwargs.get('response_size_kb'),
                    rate_limited=kwargs.get('rate_limited', False)
                )
            
            else:
                self.logger.warning(f"Unknown operation type: {operation_type}")
            
        except Exception as e:
            self.logger.error(
                f"Failed to track patent operation {operation_type} for agent {agent_id}: {str(e)}",
                category=LogCategory.SYSTEM,
                operation_type=operation_type,
                agent_id=agent_id
            )
    
    async def get_comprehensive_monitoring_report(self) -> Dict[str, Any]:
        """获取综合监控报告."""
        try:
            # 获取专利指标
            patent_metrics = await self.monitoring_system.get_patent_metrics()
            
            # 获取健康状态
            health_report = await self.patent_health_checker.get_patent_system_health_report()
            
            # 获取告警信息
            alerts = await self.monitoring_system.check_patent_alerts()
            
            # 生成综合报告
            report = {
                'timestamp': datetime.now().isoformat(),
                'monitoring_config': self.monitoring_config,
                'registered_agents': {
                    'total': len(self._registered_agents),
                    'agents': list(self._registered_agents.keys())
                },
                'metrics': patent_metrics,
                'health': health_report,
                'alerts': {
                    'total': len(alerts),
                    'by_severity': self._group_alerts_by_severity(alerts),
                    'details': alerts
                },
                'recommendations': self._generate_monitoring_recommendations(
                    patent_metrics, health_report, alerts
                )
            }
            
            return report
            
        except Exception as e:
            self.logger.error(
                f"Failed to generate comprehensive monitoring report: {str(e)}",
                category=LogCategory.SYSTEM
            )
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    async def run_monitoring_diagnostics(self) -> Dict[str, Any]:
        """运行监控系统诊断."""
        try:
            diagnostics = {
                'timestamp': datetime.now().isoformat(),
                'monitoring_system_status': {
                    'is_monitoring': self.monitoring_system.is_monitoring,
                    'registered_patent_agents': len(self.monitoring_system._patent_agents),
                    'metrics_collector_status': 'active' if self.monitoring_system.metrics_collector else 'inactive'
                },
                'health_check_status': {
                    'is_running': self.health_check_manager.is_running,
                    'total_services': len(self.health_check_manager.trackers),
                    'patent_services': len([
                        s for s in self.health_check_manager.trackers.keys()
                        if s.startswith('patent_agent_')
                    ])
                },
                'integration_status': {
                    'registered_agents': len(self._registered_agents),
                    'config': self.monitoring_config
                }
            }
            
            # 运行健康检查诊断
            health_diagnostics = await self.patent_health_checker.run_health_check_diagnostics()
            diagnostics['health_check_diagnostics'] = health_diagnostics
            
            return diagnostics
            
        except Exception as e:
            self.logger.error(
                f"Failed to run monitoring diagnostics: {str(e)}",
                category=LogCategory.SYSTEM
            )
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    async def _register_patent_metrics(self):
        """注册专利指标到监控系统."""
        # 这里可以预注册一些专利特定的指标
        # 实际的指标会在运行时通过track_*函数记录
        pass
    
    def _group_alerts_by_severity(self, alerts: List[Dict[str, Any]]) -> Dict[str, int]:
        """按严重程度分组告警."""
        severity_counts = {'critical': 0, 'warning': 0, 'info': 0}
        
        for alert in alerts:
            severity = alert.get('severity', 'info')
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        return severity_counts
    
    def _generate_monitoring_recommendations(
        self,
        metrics: Dict[str, Any],
        health: Dict[str, Any],
        alerts: List[Dict[str, Any]]
    ) -> List[str]:
        """生成监控建议."""
        recommendations = []
        
        try:
            # 基于指标的建议
            if metrics.get('patent_analysis', {}).get('success_rate', 1.0) < 0.9:
                recommendations.append("专利分析成功率偏低，建议检查Agent配置和数据源")
            
            if metrics.get('patent_data_collection', {}).get('cache_hit_rate', 1.0) < 0.5:
                recommendations.append("缓存命中率偏低，建议优化缓存策略")
            
            # 基于健康状态的建议
            if health.get('overall_status') != 'healthy':
                recommendations.append("系统健康状态异常，建议检查Agent和数据源状态")
            
            # 基于告警的建议
            critical_alerts = [a for a in alerts if a.get('severity') == 'critical']
            if critical_alerts:
                recommendations.append("存在关键告警，需要立即处理")
            
            if not recommendations:
                recommendations.append("监控系统运行正常，继续保持")
            
        except Exception as e:
            self.logger.error(f"Failed to generate monitoring recommendations: {str(e)}")
            recommendations.append("生成监控建议时出错，请检查监控配置")
        
        return recommendations
    
    def update_monitoring_config(self, new_config: Dict[str, Any]):
        """更新监控配置."""
        try:
            self.monitoring_config.update(new_config)
            
            # 更新告警阈值
            if 'alert_thresholds' in new_config:
                self.monitoring_system.update_patent_alert_thresholds(
                    new_config['alert_thresholds']
                )
            
            self.logger.info(
                "Patent monitoring configuration updated",
                category=LogCategory.SYSTEM,
                config=new_config
            )
            
        except Exception as e:
            self.logger.error(
                f"Failed to update monitoring configuration: {str(e)}",
                category=LogCategory.SYSTEM
            )
    
    async def shutdown(self):
        """关闭监控集成."""
        try:
            # 注销所有已注册的Agent
            for agent_id in list(self._registered_agents.keys()):
                await self.unregister_patent_agent(agent_id)
            
            self.logger.info("Patent monitoring integration shutdown completed", category=LogCategory.SYSTEM)
            
        except Exception as e:
            self.logger.error(
                f"Error during patent monitoring integration shutdown: {str(e)}",
                category=LogCategory.SYSTEM
            )