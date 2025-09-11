"""Configuration models for the multi-agent service."""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator

from .enums import AgentType, ModelProvider, DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE, DEFAULT_TIMEOUT


class ModelConfig(BaseModel):
    """模型配置模型."""
    
    provider: ModelProvider = Field(..., description="模型服务提供商")
    model_name: str = Field(..., description="模型名称")
    api_key: str = Field(..., description="API密钥")
    base_url: str = Field(..., description="API基础URL")
    max_tokens: int = Field(default=DEFAULT_MAX_TOKENS, description="最大token数")
    temperature: float = Field(default=DEFAULT_TEMPERATURE, description="温度参数")
    timeout: int = Field(default=DEFAULT_TIMEOUT, description="超时时间(秒)")
    max_retries: int = Field(default=3, description="最大重试次数")
    retry_delay: float = Field(default=1.0, description="重试延迟(秒)")
    enabled: bool = Field(default=True, description="是否启用")
    priority: int = Field(default=1, description="优先级，数字越小优先级越高")
    rate_limit: Optional[int] = Field(None, description="速率限制(请求/分钟)")
    custom_headers: Dict[str, str] = Field(default_factory=dict, description="自定义请求头")
    
    @field_validator('temperature')
    @classmethod
    def validate_temperature(cls, v):
        """验证温度参数范围."""
        if not 0.0 <= v <= 2.0:
            raise ValueError('Temperature must be between 0.0 and 2.0')
        return v
    
    @field_validator('max_tokens')
    @classmethod
    def validate_max_tokens(cls, v):
        """验证最大token数."""
        if v <= 0:
            raise ValueError('Max tokens must be positive')
        return v
    
    @field_validator('timeout')
    @classmethod
    def validate_timeout(cls, v):
        """验证超时时间."""
        if v <= 0:
            raise ValueError('Timeout must be positive')
        return v


class AgentConfig(BaseModel):
    """智能体配置模型."""
    
    agent_id: str = Field(..., description="智能体ID")
    agent_type: AgentType = Field(..., description="智能体类型")
    name: str = Field(..., description="智能体名称")
    description: str = Field(..., description="智能体描述")
    enabled: bool = Field(default=True, description="是否启用")
    capabilities: List[str] = Field(default_factory=list, description="能力列表")
    llm_config: ModelConfig = Field(..., description="模型配置")
    prompt_template: str = Field(..., description="提示词模板")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    max_concurrent_tasks: int = Field(default=5, description="最大并发任务数")
    priority: int = Field(default=1, description="优先级(1-10)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    
    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        """验证优先级范围."""
        if not 1 <= v <= 10:
            raise ValueError('Priority must be between 1 and 10')
        return v
    
    @field_validator('max_concurrent_tasks')
    @classmethod
    def validate_max_concurrent_tasks(cls, v):
        """验证最大并发任务数."""
        if v <= 0:
            raise ValueError('Max concurrent tasks must be positive')
        return v


class WorkflowConfig(BaseModel):
    """工作流配置模型."""
    
    workflow_id: str = Field(..., description="工作流ID")
    name: str = Field(..., description="工作流名称")
    description: str = Field(..., description="工作流描述")
    enabled: bool = Field(default=True, description="是否启用")
    workflow_type: str = Field(..., description="工作流类型")
    participating_agents: List[str] = Field(..., description="参与的智能体ID列表")
    execution_order: Optional[List[str]] = Field(None, description="执行顺序(Sequential模式)")
    parallel_groups: Optional[List[List[str]]] = Field(None, description="并行组(Parallel模式)")
    coordinator_agent: Optional[str] = Field(None, description="协调员智能体(Hierarchical模式)")
    timeout: int = Field(default=300, description="工作流超时时间(秒)")
    retry_policy: Dict[str, Any] = Field(default_factory=dict, description="重试策略")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    
    @field_validator('timeout')
    @classmethod
    def validate_timeout(cls, v):
        """验证超时时间."""
        if v <= 0:
            raise ValueError('Timeout must be positive')
        return v


class IntentRoutingConfig(BaseModel):
    """意图路由配置模型."""
    
    intent_type: str = Field(..., description="意图类型")
    description: str = Field(..., description="意图描述")
    keywords: List[str] = Field(default_factory=list, description="关键词列表")
    patterns: List[str] = Field(default_factory=list, description="正则表达式模式")
    target_agents: List[AgentType] = Field(..., description="目标智能体列表")
    confidence_threshold: float = Field(default=0.8, description="置信度阈值")
    requires_collaboration: bool = Field(default=False, description="是否需要协作")
    fallback_agent: Optional[AgentType] = Field(None, description="备用智能体")
    
    @field_validator('confidence_threshold')
    @classmethod
    def validate_confidence_threshold(cls, v):
        """验证置信度阈值."""
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence threshold must be between 0.0 and 1.0')
        return v


class SystemConfig(BaseModel):
    """系统配置模型."""
    
    service_name: str = Field(default="multi-agent-service", description="服务名称")
    version: str = Field(default="1.0.0", description="服务版本")
    debug: bool = Field(default=False, description="调试模式")
    log_level: str = Field(default="INFO", description="日志级别")
    max_concurrent_requests: int = Field(default=100, description="最大并发请求数")
    request_timeout: int = Field(default=60, description="请求超时时间(秒)")
    health_check_interval: int = Field(default=120, description="健康检查间隔(秒)")
    health_check_timeout: int = Field(default=10, description="健康检查超时时间(秒)")
    health_check_retry_delay: int = Field(default=60, description="健康检查失败重试延迟(秒)")
    auth_error_cooldown: int = Field(default=300, description="认证错误冷却时间(秒)")
    metrics_enabled: bool = Field(default=True, description="是否启用指标收集")
    
    # 数据库配置
    database_url: Optional[str] = Field(None, description="数据库连接URL")
    redis_url: Optional[str] = Field(None, description="Redis连接URL")
    
    # 安全配置
    api_key_required: bool = Field(default=False, description="是否需要API密钥")
    allowed_origins: List[str] = Field(default_factory=list, description="允许的跨域来源")
    rate_limit_enabled: bool = Field(default=True, description="是否启用速率限制")
    rate_limit_requests: int = Field(default=100, description="速率限制请求数")
    rate_limit_window: int = Field(default=60, description="速率限制时间窗口(秒)")
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        """验证日志级别."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of {valid_levels}')
        return v.upper()
    
    @field_validator('max_concurrent_requests')
    @classmethod
    def validate_max_concurrent_requests(cls, v):
        """验证最大并发请求数."""
        if v <= 0:
            raise ValueError('Max concurrent requests must be positive')
        return v


class ServiceConfig(BaseModel):
    """服务总配置模型."""
    
    system: SystemConfig = Field(default_factory=SystemConfig, description="系统配置")
    agents: List[AgentConfig] = Field(default_factory=list, description="智能体配置列表")
    workflows: List[WorkflowConfig] = Field(default_factory=list, description="工作流配置列表")
    intent_routing: List[IntentRoutingConfig] = Field(default_factory=list, description="意图路由配置列表")
    model_providers: List[ModelConfig] = Field(default_factory=list, description="模型提供商配置列表")
    
    def get_agent_config(self, agent_id: str) -> Optional[AgentConfig]:
        """根据智能体ID获取配置."""
        for agent in self.agents:
            if agent.agent_id == agent_id:
                return agent
        return None
    
    def get_agents_by_type(self, agent_type: AgentType) -> List[AgentConfig]:
        """根据智能体类型获取配置列表."""
        return [agent for agent in self.agents if agent.agent_type == agent_type]
    
    def get_workflow_config(self, workflow_id: str) -> Optional[WorkflowConfig]:
        """根据工作流ID获取配置."""
        for workflow in self.workflows:
            if workflow.workflow_id == workflow_id:
                return workflow
        return None
    
    def get_intent_config(self, intent_type: str) -> Optional[IntentRoutingConfig]:
        """根据意图类型获取路由配置."""
        for intent in self.intent_routing:
            if intent.intent_type == intent_type:
                return intent
        return None
    
    def get_model_config(self, provider: ModelProvider) -> Optional[ModelConfig]:
        """根据提供商获取模型配置."""
        for model in self.model_providers:
            if model.provider == provider:
                return model
        return None
    
    def validate_configuration(self) -> List[str]:
        """验证配置完整性，返回错误列表."""
        errors = []
        
        # 检查智能体配置
        agent_ids = set()
        for agent in self.agents:
            if agent.agent_id in agent_ids:
                errors.append(f"Duplicate agent ID: {agent.agent_id}")
            agent_ids.add(agent.agent_id)
        
        # 检查工作流配置
        workflow_ids = set()
        for workflow in self.workflows:
            if workflow.workflow_id in workflow_ids:
                errors.append(f"Duplicate workflow ID: {workflow.workflow_id}")
            workflow_ids.add(workflow.workflow_id)
            
            # 检查工作流中引用的智能体是否存在
            for agent_id in workflow.participating_agents:
                if agent_id not in agent_ids:
                    errors.append(f"Workflow {workflow.workflow_id} references non-existent agent: {agent_id}")
        
        # 检查意图路由配置
        intent_types = set()
        for intent in self.intent_routing:
            if intent.intent_type in intent_types:
                errors.append(f"Duplicate intent type: {intent.intent_type}")
            intent_types.add(intent.intent_type)
        
        return errors


class ConfigValidationResult(BaseModel):
    """配置验证结果模型."""
    
    is_valid: bool = Field(..., description="是否有效")
    errors: List[str] = Field(default_factory=list, description="错误列表")
    warnings: List[str] = Field(default_factory=list, description="警告列表")
    
    def add_error(self, error: str):
        """添加错误."""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        """添加警告."""
        self.warnings.append(warning)


class ConfigUpdateRequest(BaseModel):
    """配置更新请求模型."""
    
    config_type: str = Field(..., description="配置类型")
    config_id: str = Field(..., description="配置ID")
    config_data: Dict[str, Any] = Field(..., description="配置数据")
    validate_only: bool = Field(default=False, description="仅验证不更新")
    hot_reload: bool = Field(default=False, description="是否热重载")
    
    @field_validator('config_type')
    @classmethod
    def validate_config_type(cls, v):
        """验证配置类型."""
        valid_types = ['agent', 'workflow', 'intent_routing', 'model', 'system']
        if v not in valid_types:
            raise ValueError(f'Config type must be one of {valid_types}')
        return v


class ConfigUpdateResponse(BaseModel):
    """配置更新响应模型."""
    
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    validation_result: Optional[ConfigValidationResult] = Field(None, description="验证结果")
    updated_config: Optional[Dict[str, Any]] = Field(None, description="更新后的配置")