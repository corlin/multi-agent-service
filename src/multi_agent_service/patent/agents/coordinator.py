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
            self.logger.info(f"Coordinating data collection for request {request.request_id}")
            
            # 模拟调用PatentDataCollectionAgent
            # 实际实现中会通过AgentRouter调用真实的Agent
            await asyncio.sleep(2)  # 模拟处理时间
            
            return {
                'status': 'completed',
                'total_patents': 150,
                'data_sources': ['google_patents', 'patent_public_api'],
                'quality_score': 0.85,
                'processing_time': 2.0
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
            self.logger.info(f"Coordinating search enhancement for request {request.request_id}")
            
            # 模拟调用PatentSearchAgent
            await asyncio.sleep(1.5)  # 模拟处理时间
            
            return {
                'status': 'completed',
                'academic_papers': 25,
                'web_intelligence': 40,
                'crawled_pages': 15,
                'quality_score': 0.78,
                'processing_time': 1.5
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
            self.logger.info(f"Coordinating analysis for request {request.request_id}")
            
            # 检查前置条件
            if data_result.get('status') != 'completed':
                raise Exception("Data collection not completed successfully")
            
            # 模拟调用PatentAnalysisAgent
            await asyncio.sleep(3)  # 模拟处理时间
            
            return {
                'status': 'completed',
                'trend_analysis': {
                    'direction': 'increasing',
                    'growth_rate': 0.15,
                    'peak_year': 2023
                },
                'tech_classification': {
                    'main_categories': ['G06F', 'H04L', 'G06N'],
                    'emerging_tech': ['AI', 'IoT', 'Blockchain']
                },
                'competition_analysis': {
                    'top_applicants': ['Company A', 'Company B', 'Company C'],
                    'market_concentration': 0.45
                },
                'insights': [
                    'Technology shows strong growth trend',
                    'Market competition is intensifying',
                    'AI integration is becoming prevalent'
                ],
                'quality_score': 0.88,
                'processing_time': 3.0
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
            self.logger.info(f"Coordinating report generation for request {request.request_id}")
            
            # 检查前置条件
            if analysis_result.get('status') != 'completed':
                raise Exception("Analysis not completed successfully")
            
            # 模拟调用PatentReportAgent
            await asyncio.sleep(2)  # 模拟处理时间
            
            return {
                'status': 'completed',
                'report_id': f"report_{request.request_id}",
                'formats': ['html', 'pdf'] if request.report_format == 'pdf' else ['html'],
                'charts_generated': 5,
                'pages': 12,
                'file_size': '2.5MB',
                'processing_time': 2.0
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