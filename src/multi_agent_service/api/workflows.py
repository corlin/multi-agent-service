"""Workflow execution API endpoints."""

import logging
import time
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from fastapi.responses import JSONResponse

from ..models.api import (
    WorkflowExecuteRequest, WorkflowExecuteResponse,
    WorkflowStatusRequest, WorkflowStatusResponse,
    ErrorResponse
)
from ..models.base import WorkflowState, ExecutionStep
from ..models.enums import WorkflowType, WorkflowStatus, AgentType
from ..workflows.graph_builder import GraphBuilder
from .workflow_adapter import WorkflowAdapter
from ..agents.registry import AgentRegistry
from ..config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/workflows", tags=["workflows"])

# 工作流执行状态存储（生产环境应使用数据库）
workflow_states: Dict[str, WorkflowState] = {}


# Dependency injection functions
async def get_graph_builder() -> GraphBuilder:
    """Get graph builder instance."""
    return GraphBuilder()


async def get_agent_registry() -> AgentRegistry:
    """Get agent registry instance."""
    return AgentRegistry()


@router.post("/execute", response_model=WorkflowExecuteResponse)
async def execute_workflow(
    request: WorkflowExecuteRequest,
    http_request: Request,
    background_tasks: BackgroundTasks,
    graph_builder: GraphBuilder = Depends(get_graph_builder),
    agent_registry: AgentRegistry = Depends(get_agent_registry)
) -> WorkflowExecuteResponse:
    """
    执行工作流接口.
    
    支持三种协作模式：Sequential（顺序）、Parallel（并行）、Hierarchical（分层）。
    """
    workflow_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        logger.info(f"收到工作流执行请求: {workflow_id}, 类型: {request.workflow_type}")
        
        # 1. 验证请求参数
        if not request.tasks:
            raise HTTPException(
                status_code=400,
                detail="任务列表不能为空"
            )
        
        if not request.participating_agents:
            raise HTTPException(
                status_code=400,
                detail="参与智能体列表不能为空"
            )
        
        # 2. 验证智能体可用性
        available_agents = []
        for agent_type in request.participating_agents:
            agent_info = await agent_registry.get_agent_info(agent_type.value)
            if not agent_info:
                raise HTTPException(
                    status_code=400,
                    detail=f"智能体 {agent_type.value} 不存在"
                )
            available_agents.append(agent_info)
        
        # 3. 创建工作流状态
        workflow_state = WorkflowState(
            workflow_id=workflow_id,
            status=WorkflowStatus.PENDING,
            current_step=0,
            total_steps=len(request.tasks),
            participating_agents=[agent.agent_id for agent in available_agents],
            execution_history=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # 4. 存储工作流状态
        workflow_states[workflow_id] = workflow_state
        
        # 5. 估算完成时间
        estimated_completion_time = _estimate_workflow_completion_time(
            request.workflow_type,
            len(request.tasks),
            len(request.participating_agents)
        )
        
        # 6. 在后台启动工作流执行
        background_tasks.add_task(
            _execute_workflow_background,
            workflow_id,
            request,
            graph_builder,
            agent_registry
        )
        
        # 7. 构建响应
        response = WorkflowExecuteResponse(
            workflow_id=workflow_id,
            status=WorkflowStatus.PENDING.value,
            message=f"工作流 {workflow_id} 已启动，正在执行中",
            estimated_completion_time=estimated_completion_time
        )
        
        logger.info(f"工作流执行请求已接受: {workflow_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"工作流执行请求失败: {workflow_id}, 错误: {str(e)}", exc_info=True)
        
        error_response = ErrorResponse(
            error_code="WORKFLOW_EXECUTION_ERROR",
            error_message="工作流执行失败",
            error_details={
                "workflow_id": workflow_id,
                "error": str(e)
            }
        )
        
        raise HTTPException(
            status_code=500,
            detail=error_response.model_dump()
        )


@router.get("/{workflow_id}/status", response_model=WorkflowStatusResponse)
async def get_workflow_status(
    workflow_id: str,
    include_history: bool = False,
    include_agent_details: bool = False,
    agent_registry: AgentRegistry = Depends(get_agent_registry)
) -> WorkflowStatusResponse:
    """
    查询工作流状态接口.
    
    Args:
        workflow_id: 工作流ID
        include_history: 是否包含执行历史
        include_agent_details: 是否包含智能体详情
    """
    try:
        logger.info(f"收到工作流状态查询请求: {workflow_id}")
        
        # 1. 查找工作流状态
        workflow_state = workflow_states.get(workflow_id)
        if not workflow_state:
            raise HTTPException(
                status_code=404,
                detail=f"未找到工作流: {workflow_id}"
            )
        
        # 2. 计算进度百分比
        progress_percentage = 0.0
        if workflow_state.total_steps > 0:
            progress_percentage = (workflow_state.current_step / workflow_state.total_steps) * 100
        
        # 3. 估算剩余时间
        estimated_remaining_time = None
        if workflow_state.status == WorkflowStatus.RUNNING:
            elapsed_time = (datetime.now() - workflow_state.created_at).total_seconds()
            if workflow_state.current_step > 0:
                avg_time_per_step = elapsed_time / workflow_state.current_step
                remaining_steps = workflow_state.total_steps - workflow_state.current_step
                estimated_remaining_time = int(avg_time_per_step * remaining_steps)
        
        # 4. 获取智能体响应（如果需要）
        agent_responses = None
        if include_agent_details:
            agent_responses = []
            # 这里可以从执行历史中提取智能体响应
            for step in workflow_state.execution_history:
                if hasattr(step, 'agent_response'):
                    agent_responses.append(step.agent_response)
        
        # 5. 构建响应
        response = WorkflowStatusResponse(
            workflow_state=workflow_state,
            agent_responses=agent_responses,
            progress_percentage=progress_percentage,
            estimated_remaining_time=estimated_remaining_time
        )
        
        logger.info(f"工作流状态查询成功: {workflow_id}, 状态: {workflow_state.status}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"工作流状态查询失败: {workflow_id}, 错误: {str(e)}", exc_info=True)
        
        error_response = ErrorResponse(
            error_code="WORKFLOW_STATUS_ERROR",
            error_message="工作流状态查询失败",
            error_details={
                "workflow_id": workflow_id,
                "error": str(e)
            }
        )
        
        raise HTTPException(
            status_code=500,
            detail=error_response.model_dump()
        )


@router.get("/list")
async def list_workflows(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """
    获取工作流列表.
    
    Args:
        status: 过滤状态（可选）
        limit: 返回数量限制
        offset: 偏移量
    """
    try:
        logger.info(f"收到工作流列表查询请求: status={status}, limit={limit}, offset={offset}")
        
        # 1. 过滤工作流
        filtered_workflows = []
        
        for workflow_state in workflow_states.values():
            # 状态过滤
            if status and workflow_state.status.value != status:
                continue
            
            filtered_workflows.append({
                "workflow_id": workflow_state.workflow_id,
                "status": workflow_state.status.value,
                "current_step": workflow_state.current_step,
                "total_steps": workflow_state.total_steps,
                "participating_agents": workflow_state.participating_agents,
                "created_at": workflow_state.created_at.isoformat(),
                "updated_at": workflow_state.updated_at.isoformat()
            })
        
        # 2. 排序（按创建时间倒序）
        filtered_workflows.sort(key=lambda x: x["created_at"], reverse=True)
        
        # 3. 分页
        total_count = len(filtered_workflows)
        paginated_workflows = filtered_workflows[offset:offset + limit]
        
        return {
            "workflows": paginated_workflows,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total_count
        }
        
    except Exception as e:
        logger.error(f"工作流列表查询失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="工作流列表查询失败"
        )


@router.delete("/{workflow_id}")
async def cancel_workflow(workflow_id: str) -> Dict[str, Any]:
    """
    取消工作流执行.
    
    Args:
        workflow_id: 工作流ID
    """
    try:
        logger.info(f"收到工作流取消请求: {workflow_id}")
        
        # 1. 查找工作流
        workflow_state = workflow_states.get(workflow_id)
        if not workflow_state:
            raise HTTPException(
                status_code=404,
                detail=f"未找到工作流: {workflow_id}"
            )
        
        # 2. 检查工作流状态
        if workflow_state.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]:
            raise HTTPException(
                status_code=400,
                detail=f"工作流 {workflow_id} 已结束，无法取消"
            )
        
        # 3. 更新状态为取消
        workflow_state.status = WorkflowStatus.CANCELLED
        workflow_state.updated_at = datetime.now()
        
        # 4. 添加取消记录到执行历史
        from ..models.base import Action
        
        cancel_action = Action(
            action_type="cancel_workflow",
            parameters={"reason": "用户取消"},
            description="工作流取消"
        )
        
        cancel_step = ExecutionStep(
            step_id=str(uuid.uuid4()),
            agent_id="system",
            action=cancel_action,
            result={"message": "工作流已被用户取消"},
            status="cancelled",
            start_time=datetime.now(),
            end_time=datetime.now(),
            error_message=None
        )
        workflow_state.execution_history.append(cancel_step)
        
        logger.info(f"工作流取消成功: {workflow_id}")
        
        return {
            "workflow_id": workflow_id,
            "status": "cancelled",
            "message": "工作流已成功取消"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"工作流取消失败: {workflow_id}, 错误: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="工作流取消失败"
        )


async def _execute_workflow_background(
    workflow_id: str,
    request: WorkflowExecuteRequest,
    graph_builder: GraphBuilder,
    agent_registry: AgentRegistry
):
    """
    后台执行工作流.
    
    Args:
        workflow_id: 工作流ID
        request: 工作流执行请求
        graph_builder: 图构建器
        agent_registry: 智能体注册表
    """
    try:
        logger.info(f"开始后台执行工作流: {workflow_id}")
        
        # 1. 更新状态为运行中
        workflow_state = workflow_states[workflow_id]
        workflow_state.status = WorkflowStatus.RUNNING
        workflow_state.updated_at = datetime.now()
        
        # 2. 创建工作流适配器并执行
        adapter = WorkflowAdapter()
        execution_result = await adapter.execute(
            tasks=request.tasks,
            participating_agents=request.participating_agents,
            context=request.context,
            workflow_id=workflow_id,
            workflow_type=request.workflow_type
        )
        
        # 4. 更新最终状态
        workflow_state.status = WorkflowStatus.COMPLETED if execution_result.success else WorkflowStatus.FAILED
        workflow_state.current_step = workflow_state.total_steps
        workflow_state.updated_at = datetime.now()
        
        # 5. 添加执行结果到历史
        final_action = Action(
            action_type="complete_workflow",
            parameters={"workflow_type": request.workflow_type.value},
            description="工作流完成"
        )
        
        final_step = ExecutionStep(
            step_id=str(uuid.uuid4()),
            agent_id="system",
            action=final_action,
            result=execution_result.results,
            status="completed" if execution_result.success else "failed",
            start_time=execution_result.start_time,
            end_time=execution_result.end_time,
            error_message=execution_result.error_message if not execution_result.success else None
        )
        workflow_state.execution_history.append(final_step)
        
        logger.info(f"工作流执行完成: {workflow_id}, 成功: {execution_result.success}")
        
    except Exception as e:
        logger.error(f"工作流执行失败: {workflow_id}, 错误: {str(e)}", exc_info=True)
        
        # 更新状态为失败
        if workflow_id in workflow_states:
            workflow_state = workflow_states[workflow_id]
            workflow_state.status = WorkflowStatus.FAILED
            workflow_state.updated_at = datetime.now()
            
            # 添加错误记录
            error_action = Action(
                action_type="workflow_error",
                parameters={},
                description="工作流执行错误"
            )
            
            error_step = ExecutionStep(
                step_id=str(uuid.uuid4()),
                agent_id="system",
                action=error_action,
                result={},
                status="failed",
                start_time=datetime.now(),
                end_time=datetime.now(),
                error_message=str(e)
            )
            workflow_state.execution_history.append(error_step)


def _estimate_workflow_completion_time(
    workflow_type: WorkflowType,
    task_count: int,
    agent_count: int
) -> datetime:
    """
    估算工作流完成时间.
    
    Args:
        workflow_type: 工作流类型
        task_count: 任务数量
        agent_count: 智能体数量
        
    Returns:
        datetime: 预估完成时间
    """
    # 基础时间估算（秒）
    base_time_per_task = 60  # 每个任务基础时间
    
    if workflow_type == WorkflowType.SEQUENTIAL:
        # 顺序执行：任务依次执行
        total_time = task_count * base_time_per_task
    elif workflow_type == WorkflowType.PARALLEL:
        # 并行执行：任务同时执行，受智能体数量限制
        parallel_factor = min(agent_count, task_count)
        total_time = (task_count / parallel_factor) * base_time_per_task
    elif workflow_type == WorkflowType.HIERARCHICAL:
        # 分层执行：包含协调开销
        coordination_overhead = 0.3
        total_time = task_count * base_time_per_task * (1 + coordination_overhead)
    else:
        total_time = task_count * base_time_per_task
    
    return datetime.now() + timedelta(seconds=int(total_time))