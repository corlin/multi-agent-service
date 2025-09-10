"""Patent analysis API endpoints."""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query, Path as FastAPIPath, Response, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
import json
from datetime import datetime
import asyncio
from uuid import uuid4

from ..agents.patent.report_exporter import ReportExporter
from ..models.base import UserRequest, AgentResponse, Action
from ..models.enums import AgentType
from ..core.patent_system_initializer import get_global_patent_initializer
from ..agents.registry import agent_registry


class PatentAnalysisRequest(BaseModel):
    """专利分析请求模型."""
    keywords: List[str] = Field(..., description="分析关键词", min_items=1, max_items=10)
    analysis_type: str = Field(default="comprehensive", description="分析类型: quick_search, comprehensive_analysis, trend_analysis, competitive_analysis, report_generation")
    data_sources: Optional[List[str]] = Field(default=None, description="数据源列表")
    limit: Optional[int] = Field(default=100, ge=1, le=500, description="数据收集限制")
    date_range: Optional[Dict[str, int]] = Field(default=None, description="时间范围 {start_year: 2020, end_year: 2024}")
    quality_level: str = Field(default="standard", description="质量级别: standard, high")
    output_format: str = Field(default="json", description="输出格式: json, html, pdf")
    async_processing: bool = Field(default=True, description="是否异步处理")
    user_id: Optional[str] = Field(default="anonymous", description="用户ID")


class PatentAnalysisResponse(BaseModel):
    """专利分析响应模型."""
    task_id: str
    status: str
    message: str
    analysis_type: str
    estimated_duration: Optional[int] = None
    progress: Optional[Dict[str, Any]] = None
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str
    updated_at: str


class TaskStatusResponse(BaseModel):
    """任务状态响应模型."""
    task_id: str
    status: str
    progress: Dict[str, Any]
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str
    updated_at: str


class ExportRequest(BaseModel):
    """报告导出请求模型."""
    content: str
    format: str
    params: Optional[Dict[str, Any]] = None


logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/v1/patent", tags=["patent"])

# 全局报告导出器实例
_report_exporter: Optional[ReportExporter] = None

# 全局任务管理
_active_tasks: Dict[str, Dict[str, Any]] = {}
_task_results: Dict[str, Dict[str, Any]] = {}


def get_report_exporter() -> ReportExporter:
    """获取报告导出器实例."""
    global _report_exporter
    if _report_exporter is None:
        _report_exporter = ReportExporter()
    return _report_exporter


async def get_patent_coordinator_agent():
    """获取专利协调Agent实例."""
    try:
        # 获取专利系统初始化器
        initializer = get_global_patent_initializer(agent_registry)
        
        if not initializer.is_initialized:
            logger.warning("Patent system not initialized, attempting initialization...")
            await initializer.initialize()
        
        # 从Agent注册器获取专利协调Agent
        if agent_registry.is_agent_type_registered(AgentType.PATENT_COORDINATOR):
            # 创建Agent实例
            from ..agents.patent.coordinator_agent import PatentCoordinatorAgent
            from ..models.config import AgentConfig
            from ..services.model_client import BaseModelClient
            from ..models.model_service import ModelConfig
            from ..models.enums import ModelProvider
            
            config = AgentConfig(
                agent_id="patent_coordinator_main",
                agent_type=AgentType.PATENT_COORDINATOR,
                name="Patent Coordinator Agent",
                description="Main patent analysis coordinator",
                capabilities=["patent_coordination", "workflow_management"],
                config={}
            )
            
            # Create a simple mock model client for patent coordination
            class MockModelClient(BaseModelClient):
                def __init__(self):
                    mock_config = ModelConfig(
                        provider=ModelProvider.CUSTOM,
                        model_name="patent-coordinator-mock",
                        api_key="mock",
                        base_url="http://localhost",
                        timeout=30.0,
                        enabled=True
                    )
                    super().__init__(mock_config)
                
                async def initialize(self) -> bool:
                    return True
                
                async def generate_response(self, request):
                    return {"content": "Mock response for patent coordination"}
                
                async def health_check(self) -> bool:
                    return True
                
                async def close(self):
                    pass
            
            model_client = MockModelClient()
            coordinator = PatentCoordinatorAgent(config, model_client)
            return coordinator
        else:
            raise HTTPException(
                status_code=503, 
                detail="Patent coordinator agent not registered. Please check system initialization."
            )
    except Exception as e:
        logger.error(f"Failed to get patent coordinator agent: {str(e)}")
        raise HTTPException(
            status_code=503, 
            detail=f"Patent system unavailable: {str(e)}"
        )


async def execute_patent_analysis_task(task_id: str, request: PatentAnalysisRequest):
    """执行专利分析任务（后台任务）."""
    try:
        # 更新任务状态
        _active_tasks[task_id]["status"] = "running"
        _active_tasks[task_id]["progress"] = {"stage": "initializing", "percentage": 0}
        _active_tasks[task_id]["updated_at"] = datetime.now().isoformat()
        
        # 获取专利协调Agent
        coordinator = await get_patent_coordinator_agent()
        
        # 构建用户请求
        content = f"请进行{request.analysis_type}类型的专利分析，关键词：{', '.join(request.keywords)}"
        if request.date_range:
            content += f"，时间范围：{request.date_range['start_year']}-{request.date_range['end_year']}"
        if request.limit:
            content += f"，数据限制：{request.limit}条"
        
        user_request = UserRequest(
            content=content,
            user_id=request.user_id,
            context={
                "analysis_type": request.analysis_type,
                "keywords": request.keywords,
                "data_sources": request.data_sources or ["google_patents", "patent_public_api"],
                "limit": request.limit,
                "date_range": request.date_range,
                "quality_level": request.quality_level,
                "output_format": request.output_format,
                "task_id": task_id
            }
        )
        
        # 更新进度
        _active_tasks[task_id]["progress"] = {"stage": "processing", "percentage": 20}
        _active_tasks[task_id]["updated_at"] = datetime.now().isoformat()
        
        # 执行分析
        logger.info(f"Starting patent analysis task {task_id} with coordinator")
        response = await coordinator.process_request(user_request)
        
        # 更新进度
        _active_tasks[task_id]["progress"] = {"stage": "finalizing", "percentage": 90}
        _active_tasks[task_id]["updated_at"] = datetime.now().isoformat()
        
        # 保存结果
        result_data = {
            "task_id": task_id,
            "status": "completed",
            "analysis_type": request.analysis_type,
            "keywords": request.keywords,
            "response": {
                "content": response.response_content,
                "confidence": response.confidence,
                "metadata": response.metadata,
                "next_actions": [action.dict() if hasattr(action, 'dict') else str(action) 
                               for action in (response.next_actions or [])]
            },
            "completed_at": datetime.now().isoformat()
        }
        
        _task_results[task_id] = result_data
        
        # 更新最终状态
        _active_tasks[task_id]["status"] = "completed"
        _active_tasks[task_id]["progress"] = {"stage": "completed", "percentage": 100}
        _active_tasks[task_id]["results"] = result_data
        _active_tasks[task_id]["updated_at"] = datetime.now().isoformat()
        
        logger.info(f"Patent analysis task {task_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Patent analysis task {task_id} failed: {str(e)}")
        
        # 更新错误状态
        _active_tasks[task_id]["status"] = "failed"
        _active_tasks[task_id]["error"] = str(e)
        _active_tasks[task_id]["updated_at"] = datetime.now().isoformat()
        
        # 保存错误结果
        _task_results[task_id] = {
            "task_id": task_id,
            "status": "failed",
            "error": str(e),
            "failed_at": datetime.now().isoformat()
        }


@router.post("/analyze", summary="提交专利分析请求", response_model=PatentAnalysisResponse)
async def analyze_patents(
    request: PatentAnalysisRequest,
    background_tasks: BackgroundTasks
) -> PatentAnalysisResponse:
    """
    提交专利分析请求，支持异步处理.
    
    Args:
        request: 专利分析请求参数
        background_tasks: FastAPI后台任务管理器
    
    Returns:
        专利分析响应，包含任务ID和状态信息
    """
    try:
        # 验证请求参数
        if not request.keywords:
            raise HTTPException(status_code=400, detail="Keywords cannot be empty")
        
        valid_analysis_types = [
            "quick_search", "comprehensive_analysis", "trend_analysis", 
            "competitive_analysis", "report_generation"
        ]
        if request.analysis_type not in valid_analysis_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid analysis_type. Must be one of: {', '.join(valid_analysis_types)}"
            )
        
        # 生成任务ID
        task_id = str(uuid4())
        
        # 估算处理时间
        estimated_duration = _estimate_analysis_duration(request)
        
        # 创建任务记录
        task_info = {
            "task_id": task_id,
            "status": "pending",
            "analysis_type": request.analysis_type,
            "keywords": request.keywords,
            "estimated_duration": estimated_duration,
            "progress": {"stage": "queued", "percentage": 0},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "request_params": request.dict()
        }
        
        _active_tasks[task_id] = task_info
        
        # 根据处理模式决定执行方式
        if request.async_processing:
            # 异步处理
            background_tasks.add_task(execute_patent_analysis_task, task_id, request)
            
            return PatentAnalysisResponse(
                task_id=task_id,
                status="pending",
                message=f"专利分析任务已提交，预计需要 {estimated_duration} 秒完成",
                analysis_type=request.analysis_type,
                estimated_duration=estimated_duration,
                progress={"stage": "queued", "percentage": 0},
                created_at=task_info["created_at"],
                updated_at=task_info["updated_at"]
            )
        else:
            # 同步处理
            await execute_patent_analysis_task(task_id, request)
            
            # 获取结果
            if task_id in _task_results:
                result = _task_results[task_id]
                return PatentAnalysisResponse(
                    task_id=task_id,
                    status=result["status"],
                    message="专利分析已完成" if result["status"] == "completed" else f"分析失败: {result.get('error', 'Unknown error')}",
                    analysis_type=request.analysis_type,
                    results=result,
                    error=result.get("error"),
                    created_at=task_info["created_at"],
                    updated_at=datetime.now().isoformat()
                )
            else:
                raise HTTPException(status_code=500, detail="Analysis completed but results not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting patent analysis request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to submit analysis request: {str(e)}")


@router.get("/analyze/{task_id}", summary="获取分析任务状态", response_model=TaskStatusResponse)
async def get_analysis_status(
    task_id: str = FastAPIPath(..., description="任务ID")
) -> TaskStatusResponse:
    """
    获取专利分析任务的状态和进度.
    
    Args:
        task_id: 任务ID
    
    Returns:
        任务状态和进度信息
    """
    try:
        # 检查活跃任务
        if task_id in _active_tasks:
            task_info = _active_tasks[task_id]
            
            return TaskStatusResponse(
                task_id=task_id,
                status=task_info["status"],
                progress=task_info.get("progress", {}),
                results=task_info.get("results"),
                error=task_info.get("error"),
                created_at=task_info["created_at"],
                updated_at=task_info["updated_at"]
            )
        
        # 检查已完成任务
        elif task_id in _task_results:
            result = _task_results[task_id]
            
            return TaskStatusResponse(
                task_id=task_id,
                status=result["status"],
                progress={"stage": "completed" if result["status"] == "completed" else "failed", "percentage": 100},
                results=result if result["status"] == "completed" else None,
                error=result.get("error"),
                created_at=result.get("created_at", "unknown"),
                updated_at=result.get("completed_at", result.get("failed_at", "unknown"))
            )
        
        else:
            raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task status for {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")


@router.get("/analyze", summary="列出分析任务")
async def list_analysis_tasks(
    status: Optional[str] = Query(None, description="状态过滤: pending, running, completed, failed"),
    limit: int = Query(10, ge=1, le=100, description="返回任务数量限制")
) -> Dict[str, Any]:
    """
    列出专利分析任务.
    
    Args:
        status: 状态过滤器
        limit: 返回数量限制
    
    Returns:
        任务列表
    """
    try:
        all_tasks = []
        
        # 收集活跃任务
        for task_id, task_info in _active_tasks.items():
            if status is None or task_info["status"] == status:
                all_tasks.append({
                    "task_id": task_id,
                    "status": task_info["status"],
                    "analysis_type": task_info["analysis_type"],
                    "keywords": task_info["keywords"],
                    "progress": task_info.get("progress", {}),
                    "created_at": task_info["created_at"],
                    "updated_at": task_info["updated_at"]
                })
        
        # 收集已完成任务
        for task_id, result in _task_results.items():
            if task_id not in _active_tasks:  # 避免重复
                if status is None or result["status"] == status:
                    all_tasks.append({
                        "task_id": task_id,
                        "status": result["status"],
                        "analysis_type": result.get("analysis_type", "unknown"),
                        "keywords": result.get("keywords", []),
                        "progress": {"stage": "completed" if result["status"] == "completed" else "failed", "percentage": 100},
                        "created_at": result.get("created_at", "unknown"),
                        "updated_at": result.get("completed_at", result.get("failed_at", "unknown"))
                    })
        
        # 按创建时间排序并限制数量
        all_tasks.sort(key=lambda x: x["created_at"], reverse=True)
        limited_tasks = all_tasks[:limit]
        
        return {
            "success": True,
            "data": {
                "tasks": limited_tasks,
                "total_count": len(all_tasks),
                "returned_count": len(limited_tasks),
                "status_filter": status,
                "limit": limit
            },
            "message": f"Successfully retrieved {len(limited_tasks)} tasks"
        }
        
    except Exception as e:
        logger.error(f"Error listing analysis tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list tasks: {str(e)}")


def _estimate_analysis_duration(request: PatentAnalysisRequest) -> int:
    """估算分析持续时间（秒）."""
    base_duration = {
        "quick_search": 30,
        "comprehensive_analysis": 120,
        "trend_analysis": 90,
        "competitive_analysis": 100,
        "report_generation": 60
    }
    
    duration = base_duration.get(request.analysis_type, 90)
    
    # 根据关键词数量调整
    duration += len(request.keywords) * 5
    
    # 根据数据限制调整
    if request.limit and request.limit > 200:
        duration += 30
    elif request.limit and request.limit > 100:
        duration += 15
    
    # 根据质量级别调整
    if request.quality_level == "high":
        duration += 20
    
    return duration


@router.get("/reports", summary="列出已导出的报告")
async def list_reports(
    limit: int = Query(10, ge=1, le=100, description="返回报告数量限制"),
    format_filter: Optional[str] = Query(None, description="格式过滤 (html, pdf, json, zip)")
) -> Dict[str, Any]:
    """
    列出已导出的专利分析报告.
    
    Args:
        limit: 返回报告数量限制 (1-100)
        format_filter: 格式过滤器，可选值: html, pdf, json, zip
    
    Returns:
        包含报告列表的响应
    """
    try:
        exporter = get_report_exporter()
        reports = await exporter.list_exported_reports(limit=limit, format_filter=format_filter)
        
        return {
            "success": True,
            "data": {
                "reports": reports,
                "total_count": len(reports),
                "limit": limit,
                "format_filter": format_filter
            },
            "message": f"Successfully retrieved {len(reports)} reports"
        }
        
    except Exception as e:
        logger.error(f"Error listing reports: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list reports: {str(e)}")


@router.get("/reports/{filename}", summary="获取报告信息")
async def get_report_info(
    filename: str = FastAPIPath(..., description="报告文件名")
) -> Dict[str, Any]:
    """
    获取指定报告的详细信息.
    
    Args:
        filename: 报告文件名
    
    Returns:
        报告详细信息
    """
    try:
        exporter = get_report_exporter()
        report_info = await exporter.get_report_by_filename(filename)
        
        if not report_info:
            raise HTTPException(status_code=404, detail=f"Report not found: {filename}")
        
        return {
            "success": True,
            "data": report_info,
            "message": f"Successfully retrieved report info for {filename}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting report info for {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get report info: {str(e)}")


@router.get("/reports/download/{filename}", summary="下载报告文件")
async def download_report(
    filename: str = FastAPIPath(..., description="报告文件名"),
    as_attachment: bool = Query(True, description="是否作为附件下载")
) -> FileResponse:
    """
    下载指定的报告文件.
    
    Args:
        filename: 报告文件名
        as_attachment: 是否作为附件下载 (True: 下载, False: 在浏览器中查看)
    
    Returns:
        文件响应
    """
    try:
        exporter = get_report_exporter()
        download_info = await exporter.get_download_info(filename)
        
        if not download_info:
            raise HTTPException(status_code=404, detail=f"Report not found: {filename}")
        
        if not download_info["exists"]:
            raise HTTPException(status_code=404, detail=f"Report file not found on disk: {filename}")
        
        file_path = download_info["path"]
        mime_type = download_info["mime_type"]
        download_name = download_info["download_name"]
        
        # 设置响应头
        headers = {}
        if as_attachment:
            headers["Content-Disposition"] = f'attachment; filename="{download_name}"'
        else:
            headers["Content-Disposition"] = f'inline; filename="{download_name}"'
        
        return FileResponse(
            path=file_path,
            media_type=mime_type,
            filename=download_name,
            headers=headers
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading report {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to download report: {str(e)}")


@router.get("/reports/view/{filename}", summary="在线查看报告")
async def view_report(
    filename: str = FastAPIPath(..., description="报告文件名")
) -> Response:
    """
    在线查看报告内容 (仅支持HTML和JSON格式).
    
    Args:
        filename: 报告文件名
    
    Returns:
        报告内容响应
    """
    try:
        exporter = get_report_exporter()
        download_info = await exporter.get_download_info(filename)
        
        if not download_info:
            raise HTTPException(status_code=404, detail=f"Report not found: {filename}")
        
        if not download_info["exists"]:
            raise HTTPException(status_code=404, detail=f"Report file not found on disk: {filename}")
        
        file_format = download_info["format"]
        file_path = download_info["path"]
        
        # 只支持HTML和JSON在线查看
        if file_format not in ["html", "json"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Online viewing not supported for {file_format} format. Use download endpoint instead."
            )
        
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 设置适当的媒体类型
        media_type = download_info["mime_type"]
        
        return Response(content=content, media_type=media_type)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error viewing report {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to view report: {str(e)}")


@router.delete("/reports/{filename}", summary="删除报告")
async def delete_report(
    filename: str = FastAPIPath(..., description="报告文件名"),
    delete_versions: bool = Query(False, description="是否删除所有版本")
) -> Dict[str, Any]:
    """
    删除指定的报告文件.
    
    Args:
        filename: 报告文件名
        delete_versions: 是否删除该报告的所有版本
    
    Returns:
        删除操作结果
    """
    try:
        exporter = get_report_exporter()
        result = await exporter.delete_report(filename, delete_versions=delete_versions)
        
        if not result["deleted"]:
            if result["error"]:
                raise HTTPException(status_code=404, detail=result["error"])
            else:
                raise HTTPException(status_code=404, detail=f"Report not found: {filename}")
        
        return {
            "success": True,
            "data": result,
            "message": f"Successfully deleted report {filename}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting report {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete report: {str(e)}")


@router.post("/reports/cleanup", summary="清理旧报告")
async def cleanup_old_reports(
    days: Optional[int] = Query(None, ge=1, description="清理多少天前的报告 (默认使用配置值)")
) -> Dict[str, Any]:
    """
    清理旧的报告文件和版本.
    
    Args:
        days: 清理多少天前的报告，不指定则使用配置的默认值
    
    Returns:
        清理操作结果
    """
    try:
        exporter = get_report_exporter()
        result = await exporter.cleanup_old_reports(days=days)
        
        return {
            "success": True,
            "data": result,
            "message": f"Cleanup completed. Deleted {result['reports_deleted']} reports, "
                      f"{result['versions_cleaned']} versions, {result['temp_files_deleted']} temp files. "
                      f"Freed {result['total_space_freed']} bytes."
        }
        
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup reports: {str(e)}")


@router.get("/export/info", summary="获取导出器信息")
async def get_export_info() -> Dict[str, Any]:
    """
    获取报告导出器的配置信息.
    
    Returns:
        导出器配置信息
    """
    try:
        exporter = get_report_exporter()
        export_info = await exporter.get_export_info()
        
        return {
            "success": True,
            "data": export_info,
            "message": "Successfully retrieved export info"
        }
        
    except Exception as e:
        logger.error(f"Error getting export info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get export info: {str(e)}")


@router.post("/export", summary="导出报告")
async def export_report(request: ExportRequest) -> Dict[str, Any]:
    """
    导出报告到指定格式.
    
    Args:
        request: 导出请求，包含内容、格式和参数
    
    Returns:
        导出结果
    """
    try:
        if not request.content:
            raise HTTPException(status_code=400, detail="Content cannot be empty")
        
        if request.format not in ["html", "pdf", "json", "zip"]:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {request.format}")
        
        exporter = get_report_exporter()
        export_params = request.params or {}
        
        result = await exporter.export_report(request.content, request.format, export_params)
        
        return {
            "success": True,
            "data": result,
            "message": f"Successfully exported report in {request.format} format"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to export report: {str(e)}")


@router.get("/health", summary="检查专利API健康状态")
async def health_check() -> Dict[str, Any]:
    """
    检查专利分析API的健康状态.
    
    Returns:
        健康状态信息
    """
    try:
        exporter = get_report_exporter()
        export_info = await exporter.get_export_info()
        
        # 检查目录是否存在和可写
        directories = export_info.get("directories", {})
        directory_status = {}
        
        for dir_name, dir_path in directories.items():
            path_obj = Path(dir_path)
            directory_status[dir_name] = {
                "exists": path_obj.exists(),
                "writable": path_obj.exists() and path_obj.is_dir(),
                "path": dir_path
            }
        
        # 检查依赖
        dependencies = {}
        
        # 检查weasyprint
        try:
            import weasyprint
            dependencies["weasyprint"] = {"available": True, "version": weasyprint.__version__}
        except ImportError as e:
            dependencies["weasyprint"] = {"available": False, "error": f"Import error: {str(e)}"}
        except Exception as e:
            dependencies["weasyprint"] = {"available": False, "error": f"Library error: {str(e)}"}
        
        return {
            "success": True,
            "data": {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "directories": directory_status,
                "dependencies": dependencies,
                "export_info": export_info
            },
            "message": "Patent API is healthy"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "success": False,
            "data": {
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            },
            "message": f"Patent API health check failed: {str(e)}"
        }