"""Patent workflow registration module for integrating patent workflows into the existing system."""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .patent_workflow_engine import PatentWorkflowEngine, PatentWorkflowFactory
from .state_management import WorkflowStateManager
from ..models.enums import WorkflowType, WorkflowStatus
from ..models.workflow import WorkflowTemplate, WorkflowExecution


logger = logging.getLogger(__name__)


class PatentWorkflowRegistry:
    """专利工作流注册器，负责将专利工作流集成到现有的工作流引擎中."""
    
    def __init__(self, state_manager: Optional[WorkflowStateManager] = None):
        """初始化专利工作流注册器."""
        self.state_manager = state_manager or WorkflowStateManager()
        self.patent_workflow_engine = PatentWorkflowEngine(self.state_manager)
        
        # 注册的专利工作流模板
        self.registered_templates: Dict[str, WorkflowTemplate] = {}
        
        # 活跃的专利工作流执行
        self.active_executions: Dict[str, WorkflowExecution] = {}
        
        # 专利工作流统计
        self.execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_duration": 0.0
        }
        
        self.logger = logging.getLogger(f"{__name__}.PatentWorkflowRegistry")
    
    def register_patent_workflows(self) -> bool:
        """注册所有专利工作流模板."""
        try:
            self.logger.info("Starting patent workflow registration...")
            
            # 获取可用的专利工作流模板
            available_templates = self.patent_workflow_engine.get_available_templates()
            
            success_count = 0
            for template_name in available_templates:
                try:
                    # 获取模板信息
                    template_info = self.patent_workflow_engine.get_template_info(template_name)
                    
                    if template_info:
                        # 创建WorkflowTemplate对象
                        template = WorkflowTemplate(
                            template_id=template_name,
                            name=template_info["name"],
                            description=template_info["description"],
                            workflow_type=WorkflowType(template_info["workflow_type"]),
                            node_templates=[],  # 这些在PatentWorkflowEngine中管理
                            edge_templates=[],
                            metadata={
                                "node_count": template_info["node_count"],
                                "edge_count": template_info["edge_count"],
                                "engine": "patent_workflow_engine"
                            }
                        )
                        
                        self.registered_templates[template_name] = template
                        success_count += 1
                        
                        self.logger.info(f"Successfully registered patent workflow template: {template_name}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to register patent workflow template {template_name}: {str(e)}")
            
            self.logger.info(f"Patent workflow registration completed: {success_count}/{len(available_templates)} templates registered")
            return success_count == len(available_templates)
            
        except Exception as e:
            self.logger.error(f"Patent workflow registration failed: {str(e)}")
            return False
    
    def register_patent_workflow_template(self, template_name: str, template_config: Dict[str, Any]) -> bool:
        """注册单个专利工作流模板."""
        try:
            # 验证模板配置
            if not self._validate_template_config(template_config):
                self.logger.error(f"Invalid template configuration for {template_name}")
                return False
            
            # 创建WorkflowTemplate对象
            template = WorkflowTemplate(
                template_id=template_name,
                name=template_config.get("name", template_name),
                description=template_config.get("description", ""),
                workflow_type=WorkflowType(template_config.get("workflow_type", "sequential")),
                node_templates=template_config.get("node_templates", []),
                edge_templates=template_config.get("edge_templates", []),
                metadata=template_config.get("metadata", {})
            )
            
            self.registered_templates[template_name] = template
            
            self.logger.info(f"Successfully registered patent workflow template: {template_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register patent workflow template {template_name}: {str(e)}")
            return False
    
    def _validate_template_config(self, config: Dict[str, Any]) -> bool:
        """验证模板配置."""
        required_fields = ["name", "workflow_type"]
        
        for field in required_fields:
            if field not in config:
                self.logger.error(f"Missing required field in template config: {field}")
                return False
        
        # 验证工作流类型
        try:
            WorkflowType(config["workflow_type"])
        except ValueError:
            self.logger.error(f"Invalid workflow type: {config['workflow_type']}")
            return False
        
        return True
    
    async def create_patent_workflow_execution(self, template_name: str, input_data: Dict[str, Any]) -> Optional[WorkflowExecution]:
        """创建专利工作流执行."""
        try:
            if template_name not in self.registered_templates:
                self.logger.error(f"Patent workflow template not found: {template_name}")
                return None
            
            # 使用PatentWorkflowEngine创建执行
            execution = await self.patent_workflow_engine.create_execution_from_template(
                template_name, input_data
            )
            
            # 记录执行
            self.active_executions[execution.execution_id] = execution
            self.execution_stats["total_executions"] += 1
            
            self.logger.info(f"Created patent workflow execution: {execution.execution_id}")
            return execution
            
        except Exception as e:
            self.logger.error(f"Failed to create patent workflow execution: {str(e)}")
            return None
    
    async def execute_patent_workflow(self, execution: WorkflowExecution) -> WorkflowExecution:
        """执行专利工作流."""
        try:
            start_time = datetime.now()
            
            # 使用PatentWorkflowEngine执行工作流
            result = await self.patent_workflow_engine.execute_workflow(execution)
            
            # 更新统计信息
            duration = (datetime.now() - start_time).total_seconds()
            self._update_execution_stats(result, duration)
            
            # 清理活跃执行记录
            if execution.execution_id in self.active_executions:
                del self.active_executions[execution.execution_id]
            
            return result
            
        except Exception as e:
            self.logger.error(f"Patent workflow execution failed: {str(e)}")
            
            # 更新失败统计
            self.execution_stats["failed_executions"] += 1
            
            # 设置执行状态为失败
            execution.status = WorkflowStatus.FAILED
            execution.error_message = str(e)
            execution.end_time = datetime.now()
            
            return execution
    
    def _update_execution_stats(self, execution: WorkflowExecution, duration: float):
        """更新执行统计信息."""
        if execution.status == WorkflowStatus.COMPLETED:
            self.execution_stats["successful_executions"] += 1
        elif execution.status == WorkflowStatus.FAILED:
            self.execution_stats["failed_executions"] += 1
        
        # 更新平均执行时间
        total_executions = self.execution_stats["total_executions"]
        current_avg = self.execution_stats["average_duration"]
        
        if total_executions > 0:
            self.execution_stats["average_duration"] = (
                (current_avg * (total_executions - 1) + duration) / total_executions
            )
    
    async def pause_patent_workflow(self, execution_id: str) -> bool:
        """暂停专利工作流."""
        try:
            return await self.patent_workflow_engine.pause_workflow(execution_id)
        except Exception as e:
            self.logger.error(f"Failed to pause patent workflow {execution_id}: {str(e)}")
            return False
    
    async def resume_patent_workflow(self, execution_id: str) -> bool:
        """恢复专利工作流."""
        try:
            return await self.patent_workflow_engine.resume_workflow(execution_id)
        except Exception as e:
            self.logger.error(f"Failed to resume patent workflow {execution_id}: {str(e)}")
            return False
    
    async def cancel_patent_workflow(self, execution_id: str) -> bool:
        """取消专利工作流."""
        try:
            success = await self.patent_workflow_engine.cancel_workflow(execution_id)
            
            # 从活跃执行中移除
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to cancel patent workflow {execution_id}: {str(e)}")
            return False
    
    async def get_patent_workflow_status(self, execution_id: str) -> Optional[WorkflowStatus]:
        """获取专利工作流状态."""
        try:
            return await self.patent_workflow_engine.get_workflow_status(execution_id)
        except Exception as e:
            self.logger.error(f"Failed to get patent workflow status {execution_id}: {str(e)}")
            return None
    
    def get_registered_patent_templates(self) -> Dict[str, WorkflowTemplate]:
        """获取已注册的专利工作流模板."""
        return self.registered_templates.copy()
    
    def get_patent_template_info(self, template_name: str) -> Optional[Dict[str, Any]]:
        """获取专利工作流模板信息."""
        if template_name in self.registered_templates:
            template = self.registered_templates[template_name]
            return {
                "template_id": template.template_id,
                "name": template.name,
                "description": template.description,
                "workflow_type": template.workflow_type.value,
                "metadata": template.metadata
            }
        return None
    
    def get_active_patent_executions(self) -> Dict[str, WorkflowExecution]:
        """获取活跃的专利工作流执行."""
        return self.active_executions.copy()
    
    def get_patent_workflow_statistics(self) -> Dict[str, Any]:
        """获取专利工作流统计信息."""
        stats = self.execution_stats.copy()
        stats.update({
            "registered_templates": len(self.registered_templates),
            "active_executions": len(self.active_executions),
            "success_rate": (
                stats["successful_executions"] / max(stats["total_executions"], 1)
            ) * 100,
            "last_updated": datetime.now().isoformat()
        })
        return stats
    
    def validate_patent_workflow_setup(self) -> Dict[str, Any]:
        """验证专利工作流设置."""
        validation_results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "registered_templates": [],
            "missing_components": []
        }
        
        try:
            # 检查是否有注册的模板
            if not self.registered_templates:
                validation_results["errors"].append("No patent workflow templates registered")
                validation_results["is_valid"] = False
            else:
                validation_results["registered_templates"] = list(self.registered_templates.keys())
            
            # 检查PatentWorkflowEngine
            if not self.patent_workflow_engine:
                validation_results["errors"].append("PatentWorkflowEngine not initialized")
                validation_results["is_valid"] = False
            
            # 检查StateManager
            if not self.state_manager:
                validation_results["errors"].append("WorkflowStateManager not initialized")
                validation_results["is_valid"] = False
            
            # 检查模板完整性
            for template_name, template in self.registered_templates.items():
                if not template.name:
                    validation_results["warnings"].append(f"Template {template_name} has no name")
                
                if not template.description:
                    validation_results["warnings"].append(f"Template {template_name} has no description")
            
            # 检查引擎统计
            engine_stats = self.patent_workflow_engine.get_execution_statistics()
            if engine_stats["available_templates"] == 0:
                validation_results["warnings"].append("No templates available in PatentWorkflowEngine")
            
        except Exception as e:
            validation_results["is_valid"] = False
            validation_results["errors"].append(f"Validation failed: {str(e)}")
        
        return validation_results
    
    async def health_check(self) -> Dict[str, Any]:
        """专利工作流系统健康检查."""
        health_status = {
            "is_healthy": True,
            "components": {},
            "statistics": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # 检查PatentWorkflowEngine
            try:
                engine_stats = self.patent_workflow_engine.get_execution_statistics()
                health_status["components"]["patent_workflow_engine"] = {
                    "status": "healthy",
                    "statistics": engine_stats
                }
            except Exception as e:
                health_status["components"]["patent_workflow_engine"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_status["is_healthy"] = False
            
            # 检查StateManager
            try:
                # 简单的状态管理器检查
                test_execution_id = "health_check_test"
                await self.state_manager.get_execution_state(test_execution_id)
                health_status["components"]["state_manager"] = {
                    "status": "healthy"
                }
            except Exception as e:
                health_status["components"]["state_manager"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_status["is_healthy"] = False
            
            # 添加统计信息
            health_status["statistics"] = self.get_patent_workflow_statistics()
            
        except Exception as e:
            health_status["is_healthy"] = False
            health_status["error"] = str(e)
        
        return health_status
    
    async def shutdown(self):
        """关闭专利工作流注册器."""
        try:
            self.logger.info("Shutting down patent workflow registry...")
            
            # 取消所有活跃的执行
            for execution_id in list(self.active_executions.keys()):
                await self.cancel_patent_workflow(execution_id)
            
            # 清理资源
            self.registered_templates.clear()
            self.active_executions.clear()
            
            self.logger.info("Patent workflow registry shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during patent workflow registry shutdown: {str(e)}")


# 便捷函数
def register_patent_workflows(state_manager: Optional[WorkflowStateManager] = None) -> PatentWorkflowRegistry:
    """便捷函数：创建并注册专利工作流."""
    registry = PatentWorkflowRegistry(state_manager)
    registry.register_patent_workflows()
    return registry


def get_patent_workflow_info(registry: PatentWorkflowRegistry) -> Dict[str, Any]:
    """便捷函数：获取专利工作流信息."""
    return {
        "templates": registry.get_registered_patent_templates(),
        "statistics": registry.get_patent_workflow_statistics(),
        "active_executions": len(registry.get_active_patent_executions())
    }


def validate_patent_workflow_system(registry: PatentWorkflowRegistry) -> Dict[str, Any]:
    """便捷函数：验证专利工作流系统."""
    return registry.validate_patent_workflow_setup()


# 全局专利工作流注册器实例（可选）
_global_patent_workflow_registry: PatentWorkflowRegistry = None


def get_global_patent_workflow_registry(state_manager: Optional[WorkflowStateManager] = None) -> PatentWorkflowRegistry:
    """获取全局专利工作流注册器实例."""
    global _global_patent_workflow_registry
    
    if _global_patent_workflow_registry is None:
        _global_patent_workflow_registry = PatentWorkflowRegistry(state_manager)
        _global_patent_workflow_registry.register_patent_workflows()
    
    return _global_patent_workflow_registry


def initialize_patent_workflow_system(state_manager: Optional[WorkflowStateManager] = None) -> bool:
    """初始化专利工作流系统."""
    try:
        registry = get_global_patent_workflow_registry(state_manager)
        validation = registry.validate_patent_workflow_setup()
        
        if validation["is_valid"]:
            logger.info("Patent workflow system initialized successfully")
            return True
        else:
            logger.error(f"Patent workflow system initialization failed: {validation['errors']}")
            return False
            
    except Exception as e:
        logger.error(f"Patent workflow system initialization error: {str(e)}")
        return False