"""Workflow execution adapter for API integration."""

import asyncio
from typing import Dict, Any, List
from datetime import datetime

from ..models.enums import WorkflowType, AgentType
from ..models.workflow import WorkflowExecution
from ..workflows.sequential import SequentialWorkflowEngine
from ..workflows.parallel import ParallelWorkflowEngine
from ..workflows.hierarchical import HierarchicalWorkflowEngine


class WorkflowExecutionResult:
    """Workflow execution result."""
    
    def __init__(self, success: bool, start_time: datetime, end_time: datetime, 
                 results: Dict[str, Any], error_message: str = None):
        self.success = success
        self.start_time = start_time
        self.end_time = end_time
        self.results = results
        self.error_message = error_message


class WorkflowAdapter:
    """Adapter to integrate workflow engines with the API."""
    
    def __init__(self):
        self.engines = {
            WorkflowType.SEQUENTIAL: SequentialWorkflowEngine(),
            WorkflowType.PARALLEL: ParallelWorkflowEngine(),
            WorkflowType.HIERARCHICAL: HierarchicalWorkflowEngine()
        }
    
    async def execute(
        self, 
        tasks: List[Dict[str, Any]], 
        participating_agents: List[AgentType],
        context: Dict[str, Any],
        workflow_id: str,
        workflow_type: WorkflowType = WorkflowType.SEQUENTIAL
    ) -> WorkflowExecutionResult:
        """Execute workflow with given parameters."""
        start_time = datetime.now()
        
        try:
            # Create workflow execution object
            execution = WorkflowExecution(
                execution_id=workflow_id,
                graph_id=f"graph_{workflow_type.value}",
                input_data={
                    "tasks": tasks,
                    "participating_agents": [agent.value for agent in participating_agents],
                    "context": context
                },
                node_results={},
                output_data={}
            )
            
            # Get appropriate engine
            engine = self.engines.get(workflow_type)
            if not engine:
                raise ValueError(f"Unsupported workflow type: {workflow_type}")
            
            # Execute workflow
            result_execution = await engine.execute_workflow(execution)
            
            end_time = datetime.now()
            
            # Create result
            return WorkflowExecutionResult(
                success=result_execution.status.value == "completed",
                start_time=start_time,
                end_time=end_time,
                results=result_execution.output_data or {},
                error_message=result_execution.error_message
            )
            
        except Exception as e:
            end_time = datetime.now()
            return WorkflowExecutionResult(
                success=False,
                start_time=start_time,
                end_time=end_time,
                results={},
                error_message=str(e)
            )