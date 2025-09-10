"""专利系统健康检查工具."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import aiohttp

from ...utils.health_check_manager import HealthCheckManager, HealthCheckStatus
from ...utils.logging import get_logger, LogCategory

logger = get_logger("multi_agent_service.patent.health_check")


class PatentHealthChecker:
    """专利系统专用健康检查器."""
    
    def __init__(self, health_check_manager: HealthCheckManager):
        self.health_check_manager = health_check_manager
        self.logger = logger
        
        # 专利数据源配置
        self.patent_data_sources = {
            'google_patents': {
                'name': 'Google Patents API',
                'test_url': 'https://patents.google.com/api/health',
                'timeout': 10,
                'critical': True
            },
            'cnki_api': {
                'name': 'CNKI API',
                'test_url': 'https://api.cnki.net/health',  # 示例URL
                'timeout': 15,
                'critical': False
            },
            'bocha_ai': {
                'name': 'Bocha AI API',
                'test_url': 'https://api.bocha.ai/health',  # 示例URL
                'timeout': 15,
                'critical': False
            }
        }
        
        # 专利Agent类型
        self.patent_agent_types = [
            'patent_data_collection_agent',
            'patent_search_agent',
            'patent_analysis_agent',
            'patent_coordinator_agent',
            'patent_report_agent'
        ]
    
    async def register_all_patent_agents(self, agent_registry) -> None:
        """注册所有专利Agent到健康检查系统."""
        try:
            for agent_type in self.patent_agent_types:
                agents = agent_registry.get_agents_by_type(agent_type)
                for agent in agents:
                    await self.register_patent_agent(agent.agent_id, agent)
            
            self.logger.info(
                f"Registered {len(self.patent_agent_types)} patent agent types for health monitoring",
                category=LogCategory.SYSTEM
            )
            
        except Exception as e:
            self.logger.error(
                f"Failed to register patent agents for health monitoring: {str(e)}",
                category=LogCategory.SYSTEM
            )
    
    async def register_patent_agent(self, agent_id: str, agent_instance) -> None:
        """注册单个专利Agent到健康检查系统."""
        try:
            self.health_check_manager.register_patent_agent(agent_id, agent_instance)
            
            self.logger.info(
                f"Registered patent agent for health monitoring: {agent_id}",
                category=LogCategory.SYSTEM,
                agent_id=agent_id
            )
            
        except Exception as e:
            self.logger.error(
                f"Failed to register patent agent {agent_id} for health monitoring: {str(e)}",
                category=LogCategory.SYSTEM,
                agent_id=agent_id
            )
    
    async def unregister_patent_agent(self, agent_id: str) -> None:
        """从健康检查系统注销专利Agent."""
        try:
            self.health_check_manager.unregister_patent_agent(agent_id)
            
            self.logger.info(
                f"Unregistered patent agent from health monitoring: {agent_id}",
                category=LogCategory.SYSTEM,
                agent_id=agent_id
            )
            
        except Exception as e:
            self.logger.error(
                f"Failed to unregister patent agent {agent_id} from health monitoring: {str(e)}",
                category=LogCategory.SYSTEM,
                agent_id=agent_id
            )
    
    async def check_patent_data_sources_health(self) -> Dict[str, Any]:
        """检查专利数据源健康状态."""
        results = {}
        
        for source_id, source_config in self.patent_data_sources.items():
            try:
                start_time = datetime.now()
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        source_config['test_url'],
                        timeout=aiohttp.ClientTimeout(total=source_config['timeout'])
                    ) as response:
                        end_time = datetime.now()
                        response_time = (end_time - start_time).total_seconds()
                        
                        results[source_id] = {
                            'name': source_config['name'],
                            'status': 'healthy' if response.status < 500 else 'unhealthy',
                            'status_code': response.status,
                            'response_time_seconds': response_time,
                            'critical': source_config['critical'],
                            'timestamp': end_time.isoformat(),
                            'error': None
                        }
                        
                        # 记录到日志
                        if response.status < 500:
                            self.logger.debug(
                                f"Patent data source {source_id} health check passed",
                                category=LogCategory.SYSTEM,
                                source_id=source_id,
                                response_time=response_time
                            )
                        else:
                            self.logger.warning(
                                f"Patent data source {source_id} returned error status: {response.status}",
                                category=LogCategory.SYSTEM,
                                source_id=source_id,
                                status_code=response.status
                            )
                        
            except asyncio.TimeoutError:
                results[source_id] = {
                    'name': source_config['name'],
                    'status': 'unhealthy',
                    'status_code': None,
                    'response_time_seconds': source_config['timeout'],
                    'critical': source_config['critical'],
                    'timestamp': datetime.now().isoformat(),
                    'error': 'timeout'
                }
                
                self.logger.warning(
                    f"Patent data source {source_id} health check timeout",
                    category=LogCategory.SYSTEM,
                    source_id=source_id,
                    timeout=source_config['timeout']
                )
                
            except Exception as e:
                results[source_id] = {
                    'name': source_config['name'],
                    'status': 'unhealthy',
                    'status_code': None,
                    'response_time_seconds': None,
                    'critical': source_config['critical'],
                    'timestamp': datetime.now().isoformat(),
                    'error': str(e)
                }
                
                self.logger.error(
                    f"Patent data source {source_id} health check failed: {str(e)}",
                    category=LogCategory.SYSTEM,
                    source_id=source_id,
                    error=str(e)
                )
        
        return results
    
    async def get_patent_system_health_report(self) -> Dict[str, Any]:
        """获取专利系统完整健康报告."""
        try:
            # 获取专利Agent状态
            patent_agents_status = self.health_check_manager.get_patent_agents_status()
            
            # 检查专利数据源
            data_sources_status = await self.check_patent_data_sources_health()
            
            # 计算整体健康状态
            overall_status = self._calculate_overall_health_status(
                patent_agents_status, data_sources_status
            )
            
            # 生成健康问题列表
            health_issues = self._identify_health_issues(
                patent_agents_status, data_sources_status
            )
            
            # 生成建议
            recommendations = self._generate_health_recommendations(health_issues)
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'overall_status': overall_status,
                'patent_agents': patent_agents_status,
                'data_sources': data_sources_status,
                'health_issues': health_issues,
                'recommendations': recommendations,
                'summary': {
                    'total_components': (
                        patent_agents_status.get('total_patent_agents', 0) + 
                        len(data_sources_status)
                    ),
                    'healthy_components': (
                        patent_agents_status.get('healthy_patent_agents', 0) + 
                        len([s for s in data_sources_status.values() if s['status'] == 'healthy'])
                    ),
                    'critical_issues': len([
                        issue for issue in health_issues 
                        if issue.get('severity') == 'critical'
                    ]),
                    'health_score': self._calculate_health_score(
                        patent_agents_status, data_sources_status
                    )
                }
            }
            
            self.logger.info(
                f"Generated patent system health report - Status: {overall_status}",
                category=LogCategory.SYSTEM,
                overall_status=overall_status,
                health_score=report['summary']['health_score']
            )
            
            return report
            
        except Exception as e:
            self.logger.error(
                f"Failed to generate patent system health report: {str(e)}",
                category=LogCategory.SYSTEM
            )
            return {
                'timestamp': datetime.now().isoformat(),
                'overall_status': 'error',
                'error': str(e)
            }
    
    def _calculate_overall_health_status(self, agents_status: Dict[str, Any], 
                                       sources_status: Dict[str, Any]) -> str:
        """计算整体健康状态."""
        try:
            # 检查关键组件
            critical_sources_healthy = all(
                source['status'] == 'healthy' 
                for source in sources_status.values() 
                if source.get('critical', False)
            )
            
            agents_healthy = agents_status.get('patent_agents_healthy', False)
            
            if not critical_sources_healthy:
                return 'critical'
            elif not agents_healthy:
                return 'unhealthy'
            else:
                # 检查非关键组件
                all_sources_healthy = all(
                    source['status'] == 'healthy' 
                    for source in sources_status.values()
                )
                
                if all_sources_healthy:
                    return 'healthy'
                else:
                    return 'degraded'
                    
        except Exception as e:
            self.logger.error(f"Failed to calculate overall health status: {str(e)}")
            return 'unknown'
    
    def _identify_health_issues(self, agents_status: Dict[str, Any], 
                              sources_status: Dict[str, Any]) -> List[Dict[str, Any]]:
        """识别健康问题."""
        issues = []
        
        try:
            # 检查Agent问题
            if not agents_status.get('patent_agents_healthy', False):
                unhealthy_agents = [
                    agent_id for agent_id, agent_info in agents_status.get('patent_agents', {}).items()
                    if agent_info.get('status') != 'healthy'
                ]
                
                if unhealthy_agents:
                    issues.append({
                        'type': 'unhealthy_agents',
                        'severity': 'high',
                        'message': f"Unhealthy patent agents: {', '.join(unhealthy_agents)}",
                        'affected_components': unhealthy_agents,
                        'timestamp': datetime.now().isoformat()
                    })
            
            # 检查数据源问题
            for source_id, source_info in sources_status.items():
                if source_info['status'] != 'healthy':
                    severity = 'critical' if source_info.get('critical', False) else 'medium'
                    issues.append({
                        'type': 'unhealthy_data_source',
                        'severity': severity,
                        'message': f"Data source {source_info['name']} is {source_info['status']}",
                        'affected_components': [source_id],
                        'error': source_info.get('error'),
                        'timestamp': datetime.now().isoformat()
                    })
            
        except Exception as e:
            self.logger.error(f"Failed to identify health issues: {str(e)}")
            issues.append({
                'type': 'health_check_error',
                'severity': 'high',
                'message': f"Health check system error: {str(e)}",
                'timestamp': datetime.now().isoformat()
            })
        
        return issues
    
    def _generate_health_recommendations(self, health_issues: List[Dict[str, Any]]) -> List[str]:
        """生成健康建议."""
        recommendations = []
        
        try:
            for issue in health_issues:
                if issue['type'] == 'unhealthy_agents':
                    recommendations.append(
                        "检查专利Agent配置和依赖，重启不健康的Agent"
                    )
                elif issue['type'] == 'unhealthy_data_source':
                    if issue['severity'] == 'critical':
                        recommendations.append(
                            f"立即检查关键数据源连接: {', '.join(issue['affected_components'])}"
                        )
                    else:
                        recommendations.append(
                            f"检查数据源配置: {', '.join(issue['affected_components'])}"
                        )
                elif issue['type'] == 'health_check_error':
                    recommendations.append(
                        "检查健康检查系统配置和网络连接"
                    )
            
            if not recommendations:
                recommendations.append("系统运行正常，继续监控")
                
        except Exception as e:
            self.logger.error(f"Failed to generate health recommendations: {str(e)}")
            recommendations.append("健康检查系统异常，请检查监控配置")
        
        return recommendations
    
    def _calculate_health_score(self, agents_status: Dict[str, Any], 
                              sources_status: Dict[str, Any]) -> float:
        """计算健康评分 (0-100)."""
        try:
            # Agent健康评分 (权重70%)
            agent_score = agents_status.get('patent_health_percentage', 0) * 0.7
            
            # 数据源健康评分 (权重30%)
            healthy_sources = len([
                s for s in sources_status.values() 
                if s['status'] == 'healthy'
            ])
            total_sources = len(sources_status)
            source_score = (healthy_sources / total_sources if total_sources > 0 else 0) * 30
            
            return round(agent_score + source_score, 2)
            
        except Exception as e:
            self.logger.error(f"Failed to calculate health score: {str(e)}")
            return 0.0
    
    async def run_health_check_diagnostics(self) -> Dict[str, Any]:
        """运行健康检查诊断."""
        diagnostics = {
            'timestamp': datetime.now().isoformat(),
            'diagnostics': {}
        }
        
        try:
            # 检查健康检查管理器状态
            diagnostics['diagnostics']['health_check_manager'] = {
                'is_running': self.health_check_manager.is_running,
                'registered_services': len(self.health_check_manager.trackers),
                'total_checks': self.health_check_manager.total_checks,
                'success_rate': (
                    self.health_check_manager.total_successes / 
                    self.health_check_manager.total_checks * 100
                    if self.health_check_manager.total_checks > 0 else 0
                )
            }
            
            # 检查专利Agent注册状态
            patent_services = [
                service_id for service_id in self.health_check_manager.trackers.keys()
                if service_id.startswith('patent_agent_')
            ]
            diagnostics['diagnostics']['patent_agent_registration'] = {
                'registered_patent_agents': len(patent_services),
                'expected_agent_types': len(self.patent_agent_types),
                'registered_services': patent_services
            }
            
            # 检查数据源配置
            diagnostics['diagnostics']['data_source_configuration'] = {
                'configured_sources': len(self.patent_data_sources),
                'critical_sources': len([
                    s for s in self.patent_data_sources.values() 
                    if s.get('critical', False)
                ]),
                'source_names': list(self.patent_data_sources.keys())
            }
            
            self.logger.info(
                "Health check diagnostics completed",
                category=LogCategory.SYSTEM,
                registered_agents=len(patent_services),
                configured_sources=len(self.patent_data_sources)
            )
            
        except Exception as e:
            self.logger.error(
                f"Health check diagnostics failed: {str(e)}",
                category=LogCategory.SYSTEM
            )
            diagnostics['error'] = str(e)
        
        return diagnostics