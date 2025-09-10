"""Patent coordinator agent."""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import uuid4

from .base import PatentBaseAgent
from ...agents.coordinator_agent import CoordinatorAgent
from ...models.enums import AgentType
from ...models.config import AgentConfig
from ...services.model_client import BaseModelClient
from ...models.base import UserRequest, AgentResponse

from ..models.requests import PatentAnalysisRequest


logger = logging.getLogger(__name__)


class PatentCoordinatorAgent(PatentBaseAgent):
    """专利协调管理智能体，继承现有CoordinatorAgent能力."""
    
    agent_type = AgentType.PATENT_COORDINATOR
    
    def __init__(self, config: AgentConfig, model_client: BaseModelClient):
        """初始化专利协调智能体."""
        super().__init__(config, model_client)
        
        # 专利分析专用工作流配置
        self.patent_workflow_config = {
            'data_collection_agents': ['patent_data_collection_agent'],
            'search_agents': ['patent_search_agent'],
            'analysis_agents': ['patent_analysis_agent'],
            'report_agents': ['patent_report_agent']
        }
        
        # 协调状态管理
        self._active_workflows: Dict[str, Dict[str, Any]] = {}
        self._workflow_results: Dict[str, Dict[str, Any]] = {}
        
        self.logger = logging.getLogger(f"{__name__}.PatentCoordinatorAgent")
    
    async def can_handle_request(self, request) -> float:
        """判断是否能处理请求."""
        # 调用父类的实现
        base_confidence = await super().can_handle_request(request)
        
        # 检查协调相关关键词
        content = getattr(request, 'content', str(request)).lower()
        coordination_keywords = ["协调", "整合", "工作流", "多agent", "综合"]
        keyword_matches = sum(1 for keyword in coordination_keywords if keyword in content)
        
        # 提高协调相关请求的置信度
        coordination_boost = min(keyword_matches * 0.2, 0.3)
        
        return min(base_confidence + coordination_boost, 1.0)
    
    async def get_capabilities(self) -> List[str]:
        """获取Agent能力列表."""
        base_capabilities = await super().get_capabilities()
        specific_capabilities = await self._get_specific_capabilities()
        return base_capabilities + specific_capabilities
    
    async def estimate_processing_time(self, request) -> int:
        """估算处理时间."""
        # 协调任务通常需要更长时间
        base_time = await super().estimate_processing_time(request)
        return base_time + 60  # 协调额外需要60秒
    
    async def _process_request_specific(self, request) -> 'AgentResponse':
        """处理具体的协调请求."""
        from ...models.base import AgentResponse
        
        try:
            # 如果是PatentAnalysisRequest对象，直接处理
            if hasattr(request, 'analysis_types'):
                result = await self._process_patent_request_specific(request)
            else:
                # 如果是普通请求，转换为分析请求
                from ..models.requests import PatentAnalysisRequest, AnalysisType
                
                # 从请求内容提取关键词
                content = getattr(request, 'content', str(request))
                keywords = content.split()[:5]  # 简单提取前5个词作为关键词
                
                analysis_request = PatentAnalysisRequest(
                    request_id=str(uuid4()),
                    keywords=keywords,
                    analysis_types=[AnalysisType.COMPREHENSIVE],
                    date_range={"start": "2020-01-01", "end": "2024-12-31"},
                    countries=["US", "CN", "EP"],
                    max_patents=1000
                )
                
                result = await self._process_patent_request_specific(analysis_request)
            
            # 生成响应内容
            response_content = f"专利分析协调完成。状态: {result.get('status', 'unknown')}"
            
            return AgentResponse(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                response_content=response_content,
                confidence=0.8,
                metadata=result
            )
            
        except Exception as e:
            self.logger.error(f"Error processing coordination request: {str(e)}")
            return AgentResponse(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                response_content=f"协调处理失败: {str(e)}",
                confidence=0.0,
                metadata={"error": str(e)}
            )
    
    async def _process_patent_request_specific(self, request: PatentAnalysisRequest) -> Dict[str, Any]:
        """处理专利特定请求."""
        try:
            # 模拟协调处理
            return {
                "status": "success",
                "workflow_id": str(uuid4()),
                "coordinated_agents": ["data_collection", "search", "analysis", "report"],
                "processing_time": 120.0
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _get_specific_capabilities(self) -> List[str]:
        """获取协调智能体的特定能力."""
        return [
            "专利分析工作流编排",
            "多Agent任务协调",
            "分析结果整合",
            "质量控制管理",
            "进度监控跟踪",
            "异常处理恢复",
            "资源调度优化"
        ]
    
    async def _process_patent_request(self, request: PatentAnalysisRequest) -> Dict[str, Any]:
        """处理专利分析协调请求."""
        workflow_id = str(uuid4())
        start_time = datetime.now()
        
        try:
            self.logger.info(f"Starting patent analysis workflow {workflow_id} for request {request.request_id}")
            
            # 初始化工作流状态
            self._active_workflows[workflow_id] = {
                'request_id': request.request_id,
                'status': 'running',
                'start_time': start_time,
                'current_step': 'initialization',
                'progress': 0.0,
                'steps_completed': [],
                'errors': []
            }
            
            # 执行专利分析工作流
            workflow_result = await self._execute_patent_workflow(workflow_id, request)
            
            # 更新工作流状态
            self._active_workflows[workflow_id]['status'] = 'completed'
            self._active_workflows[workflow_id]['progress'] = 100.0
            self._workflow_results[workflow_id] = workflow_result
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                "status": "completed",
                "workflow_id": workflow_id,
                "workflow_result": workflow_result,
                "processing_time": processing_time,
                "steps_completed": self._active_workflows[workflow_id]['steps_completed']
            }
            
            self.logger.info(f"Patent analysis workflow {workflow_id} completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Patent analysis workflow {workflow_id} failed: {str(e)}")
            
            # 更新工作流状态
            if workflow_id in self._active_workflows:
                self._active_workflows[workflow_id]['status'] = 'failed'
                self._active_workflows[workflow_id]['errors'].append(str(e))
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "status": "failed",
                "workflow_id": workflow_id,
                "error": str(e),
                "processing_time": processing_time,
                "steps_completed": self._active_workflows.get(workflow_id, {}).get('steps_completed', [])
            }
    
    async def _execute_patent_workflow(self, workflow_id: str, request: PatentAnalysisRequest) -> Dict[str, Any]:
        """执行专利分析工作流."""
        workflow_result = {
            'data_collection': None,
            'search_enhancement': None,
            'analysis': None,
            'report': None
        }
        
        try:
            # 步骤1: 数据收集阶段 (Sequential)
            await self._update_workflow_progress(workflow_id, 'data_collection', 10.0)
            data_result = await self._coordinate_data_collection(request)
            workflow_result['data_collection'] = data_result
            await self._update_workflow_progress(workflow_id, 'data_collection_completed', 30.0)
            
            # 步骤2: 搜索增强阶段 (Parallel with data collection if needed)
            await self._update_workflow_progress(workflow_id, 'search_enhancement', 40.0)
            search_result = await self._coordinate_search_enhancement(request)
            workflow_result['search_enhancement'] = search_result
            await self._update_workflow_progress(workflow_id, 'search_enhancement_completed', 60.0)
            
            # 步骤3: 分析处理阶段
            await self._update_workflow_progress(workflow_id, 'analysis', 70.0)
            analysis_result = await self._coordinate_analysis(request, data_result, search_result)
            workflow_result['analysis'] = analysis_result
            await self._update_workflow_progress(workflow_id, 'analysis_completed', 85.0)
            
            # 步骤4: 报告生成阶段
            if request.generate_report:
                await self._update_workflow_progress(workflow_id, 'report_generation', 90.0)
                report_result = await self._coordinate_report_generation(request, analysis_result)
                workflow_result['report'] = report_result
                await self._update_workflow_progress(workflow_id, 'report_completed', 100.0)
            
            # 质量控制和验证
            quality_score = await self._validate_workflow_results(workflow_result)
            workflow_result['quality_score'] = quality_score
            
            return workflow_result
            
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {str(e)}")
            raise e
    
    async def _coordinate_data_collection(self, request: PatentAnalysisRequest) -> Dict[str, Any]:
        """协调数据收集阶段."""
        try:
            request_id = getattr(request, 'request_id', str(uuid4()))
            self.logger.info(f"Coordinating data collection for request {request_id}")
            
            # 模拟调用PatentDataCollectionAgent
            # 实际实现中会通过AgentRouter调用真实的Agent
            await asyncio.sleep(0.1)  # 减少模拟处理时间
            
            return {
                'status': 'success',
                'data': {
                    'patents': [{
                        'application_number': 'US16123456',
                        'title': 'AI System',
                        'abstract': 'An AI system for testing',
                        'applicants': [{'name': 'Tech Corp', 'country': 'US'}],
                        'inventors': [{'name': 'John Doe', 'country': 'US'}],
                        'application_date': '2022-01-15T00:00:00',
                        'classifications': [{'ipc_class': 'G06N3/08'}],
                        'country': 'US',
                        'status': 'published'
                    }],
                    'total': 1
                },
                'total_patents': 1
            }
            
        except Exception as e:
            self.logger.error(f"Data collection coordination failed: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    async def _coordinate_search_enhancement(self, request: PatentAnalysisRequest) -> Dict[str, Any]:
        """协调搜索增强阶段."""
        try:
            request_id = getattr(request, 'request_id', str(uuid4()))
            self.logger.info(f"Coordinating search enhancement for request {request_id}")
            
            # 模拟调用PatentSearchAgent
            await asyncio.sleep(0.1)  # 减少模拟处理时间
            
            return {
                'status': 'success',
                'enhanced_data': {
                    'cnki_data': {
                        'literature': [{
                            'title': 'AI Research Paper',
                            'authors': ['Dr. Smith'],
                            'abstract': 'Research on AI',
                            'keywords': ['AI', 'ML'],
                            'publication_date': '2022-06-01T00:00:00',
                            'journal': 'AI Journal'
                        }],
                        'concepts': [{
                            'term': 'AI',
                            'definition': 'Artificial Intelligence'
                        }]
                    },
                    'bocha_data': {
                        'web_results': [{
                            'title': 'AI News',
                            'url': 'http://example.com'
                        }],
                        'ai_analysis': {
                            'summary': 'AI is growing rapidly'
                        }
                    }
                }
            }
            
        except Exception as e:
            self.logger.error(f"Search enhancement coordination failed: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    async def _coordinate_analysis(self, request: PatentAnalysisRequest, 
                                 data_result: Dict[str, Any], 
                                 search_result: Dict[str, Any]) -> Dict[str, Any]:
        """协调分析处理阶段."""
        try:
            request_id = getattr(request, 'request_id', str(uuid4()))
            self.logger.info(f"Coordinating analysis for request {request_id}")
            
            # 检查前置条件
            if data_result.get('status') != 'success':
                raise Exception("Data collection not completed successfully")
            
            # 模拟调用PatentAnalysisAgent
            await asyncio.sleep(0.1)  # 减少模拟处理时间
            
            return {
                'status': 'success',
                'analysis': {
                    'trend_analysis': {
                        'yearly_counts': {'2020': 10, '2021': 15, '2022': 20},
                        'growth_rates': {'2021': 0.5, '2022': 0.33},
                        'trend_direction': 'increasing'
                    },
                    'tech_classification': {
                        'ipc_distribution': {'G06N': 15, 'H04L': 5},
                        'main_technologies': ['Machine Learning', 'Neural Networks']
                    },
                    'competition_analysis': {
                        'top_applicants': [('Tech Corp', 10), ('AI Inc', 8)],
                        'market_concentration': 0.6
                    }
                }
            }
            
        except Exception as e:
            self.logger.error(f"Analysis coordination failed: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    async def _coordinate_report_generation(self, request: PatentAnalysisRequest, 
                                          analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """协调报告生成阶段."""
        try:
            request_id = getattr(request, 'request_id', str(uuid4()))
            self.logger.info(f"Coordinating report generation for request {request_id}")
            
            # 检查前置条件
            if analysis_result.get('status') != 'success':
                raise Exception("Analysis not completed successfully")
            
            # 模拟调用PatentReportAgent
            await asyncio.sleep(0.1)  # 减少模拟处理时间
            
            return {
                'status': 'success',
                'report': {
                    'html_content': '<html><body>Patent Analysis Report</body></html>',
                    'pdf_content': b'PDF content',
                    'charts': {
                        'trend_chart': 'chart_data_1',
                        'tech_pie_chart': 'chart_data_2'
                    },
                    'summary': 'Analysis shows increasing trend in AI patents'
                }
            }
            
        except Exception as e:
            self.logger.error(f"Report generation coordination failed: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    async def _update_workflow_progress(self, workflow_id: str, step: str, progress: float) -> None:
        """更新工作流进度."""
        if workflow_id in self._active_workflows:
            self._active_workflows[workflow_id]['current_step'] = step
            self._active_workflows[workflow_id]['progress'] = progress
            self._active_workflows[workflow_id]['steps_completed'].append({
                'step': step,
                'timestamp': datetime.now(),
                'progress': progress
            })
            
            self.logger.debug(f"Workflow {workflow_id} progress: {progress}% - {step}")
    
    async def _validate_workflow_results(self, workflow_result: Dict[str, Any]) -> float:
        """验证工作流结果质量."""
        quality_scores = []
        
        # 检查各阶段结果
        if workflow_result.get('data_collection'):
            data_quality = workflow_result['data_collection'].get('quality_score', 0.0)
            quality_scores.append(data_quality * 0.3)
        
        if workflow_result.get('search_enhancement'):
            search_quality = workflow_result['search_enhancement'].get('quality_score', 0.0)
            quality_scores.append(search_quality * 0.2)
        
        if workflow_result.get('analysis'):
            analysis_quality = workflow_result['analysis'].get('quality_score', 0.0)
            quality_scores.append(analysis_quality * 0.4)
        
        if workflow_result.get('report'):
            # 报告生成成功即可获得基础分数
            quality_scores.append(0.1)
        
        return sum(quality_scores) if quality_scores else 0.0
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """获取工作流状态."""
        return self._active_workflows.get(workflow_id)
    
    def get_workflow_result(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """获取工作流结果."""
        return self._workflow_results.get(workflow_id)
    
    async def _generate_response_content(self, result: Dict[str, Any]) -> str:
        """生成协调响应内容."""
        if result.get("status") == "completed":
            workflow_id = result.get("workflow_id", "unknown")
            processing_time = result.get("processing_time", 0.0)
            steps_completed = result.get("steps_completed", [])
            workflow_result = result.get("workflow_result", {})
            
            # 统计各阶段结果
            data_patents = workflow_result.get('data_collection', {}).get('total_patents', 0)
            analysis_insights = len(workflow_result.get('analysis', {}).get('insights', []))
            report_generated = workflow_result.get('report', {}).get('status') == 'completed'
            overall_quality = workflow_result.get('quality_score', 0.0)
            
            content = f"""专利分析工作流已完成！

🔄 工作流信息:
• 工作流ID: {workflow_id}
• 总处理时间: {processing_time:.1f}秒
• 完成步骤数: {len(steps_completed)}
• 整体质量评分: {overall_quality:.2f}/1.0

📊 执行结果:
• 收集专利数量: {data_patents}
• 生成分析洞察: {analysis_insights} 条
• 报告生成: {'✅ 已完成' if report_generated else '❌ 未生成'}

所有分析任务已协调完成，结果已整合并可供使用。"""
            
            return content
        
        elif result.get("status") == "failed":
            workflow_id = result.get("workflow_id", "unknown")
            error = result.get("error", "未知错误")
            steps_completed = result.get("steps_completed", [])
            
            return f"""专利分析工作流执行失败！

❌ 错误信息:
• 工作流ID: {workflow_id}
• 失败原因: {error}
• 已完成步骤: {len(steps_completed)}

请检查相关Agent状态并重试。"""
        
        else:
            return f"专利分析工作流状态: {result.get('status', 'unknown')}"
    
    async def process_request(self, request) -> Dict[str, Any]:
        """处理请求的主要方法."""
        try:
            # 如果是字典，转换为PatentAnalysisRequest对象
            if isinstance(request, dict):
                from ..models.requests import PatentAnalysisRequest
                request = PatentAnalysisRequest(**request)
            
            # 确保请求有request_id属性
            if not hasattr(request, 'request_id'):
                request.request_id = str(uuid4())
            
            # 执行协调工作流
            data_result = await self._coordinate_data_collection(request)
            search_result = await self._coordinate_search_enhancement(request)
            analysis_result = await self._coordinate_analysis(request, data_result, search_result)
            report_result = await self._coordinate_report_generation(request, analysis_result)
            
            return {
                "status": "success",
                "results": {
                    "data_collection": data_result,
                    "search_enhancement": search_result,
                    "analysis": analysis_result,
                    "report": report_result
                }
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _aggregate_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """聚合多个结果."""
        aggregated = {
            'total_results': len(results),
            'successful_results': len([r for r in results if r.get('status') == 'success']),
            'failed_results': len([r for r in results if r.get('status') == 'failed']),
            'results': results
        }
        return aggregated