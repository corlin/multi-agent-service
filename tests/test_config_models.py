"""Unit tests for configuration models."""

import pytest
from pydantic import ValidationError

from src.multi_agent_service.models import (
    ModelConfig,
    AgentConfig,
    WorkflowConfig,
    IntentRoutingConfig,
    SystemConfig,
    ServiceConfig,
    ConfigValidationResult,
    ConfigUpdateRequest,
    ConfigUpdateResponse,
    ModelProvider,
    AgentType,
)


class TestModelConfig:
    """测试模型配置模型."""
    
    def test_model_config_creation(self):
        """测试模型配置创建."""
        config = ModelConfig(
            provider=ModelProvider.QWEN,
            model_name="qwen-turbo",
            api_key="test-key",
            api_base="https://api.qwen.com",
            max_tokens=1024,
            temperature=0.7,
            timeout=30
        )
        assert config.provider == ModelProvider.QWEN
        assert config.model_name == "qwen-turbo"
        assert config.api_key == "test-key"
        assert config.max_tokens == 1024
        assert config.temperature == 0.7
    
    def test_model_config_defaults(self):
        """测试模型配置默认值."""
        config = ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="gpt-3.5-turbo",
            api_key="test-key"
        )
        assert config.max_tokens == 2048  # DEFAULT_MAX_TOKENS
        assert config.temperature == 0.7  # DEFAULT_TEMPERATURE
        assert config.timeout == 30  # DEFAULT_TIMEOUT
        assert config.retry_attempts == 3
        assert config.custom_headers == {}
    
    def test_model_config_validation(self):
        """测试模型配置验证."""
        # 测试温度参数验证
        with pytest.raises(ValidationError):
            ModelConfig(
                provider=ModelProvider.OPENAI,
                model_name="gpt-3.5-turbo",
                api_key="test-key",
                temperature=2.5  # 超出范围
            )
        
        # 测试最大token数验证
        with pytest.raises(ValidationError):
            ModelConfig(
                provider=ModelProvider.OPENAI,
                model_name="gpt-3.5-turbo",
                api_key="test-key",
                max_tokens=-1  # 负数
            )
        
        # 测试超时时间验证
        with pytest.raises(ValidationError):
            ModelConfig(
                provider=ModelProvider.OPENAI,
                model_name="gpt-3.5-turbo",
                api_key="test-key",
                timeout=0  # 零值
            )


class TestAgentConfig:
    """测试智能体配置模型."""
    
    def test_agent_config_creation(self):
        """测试智能体配置创建."""
        model_config = ModelConfig(
            provider=ModelProvider.QWEN,
            model_name="qwen-turbo",
            api_key="test-key"
        )
        
        agent_config = AgentConfig(
            agent_id="sales_001",
            agent_type=AgentType.SALES,
            name="Sales Representative",
            description="Handles sales inquiries",
            llm_config=model_config,
            prompt_template="You are a sales representative. {input}",
            capabilities=["product_info", "pricing"],
            max_concurrent_tasks=3,
            priority=5
        )
        
        assert agent_config.agent_id == "sales_001"
        assert agent_config.agent_type == AgentType.SALES
        assert agent_config.enabled is True  # 默认值
        assert len(agent_config.capabilities) == 2
        assert agent_config.max_concurrent_tasks == 3
        assert agent_config.priority == 5
    
    def test_agent_config_validation(self):
        """测试智能体配置验证."""
        model_config = ModelConfig(
            provider=ModelProvider.QWEN,
            model_name="qwen-turbo",
            api_key="test-key"
        )
        
        # 测试优先级验证
        with pytest.raises(ValidationError):
            AgentConfig(
                agent_id="test",
                agent_type=AgentType.SALES,
                name="Test",
                description="Test",
                llm_config=model_config,
                prompt_template="test",
                priority=11  # 超出范围
            )
        
        # 测试最大并发任务数验证
        with pytest.raises(ValidationError):
            AgentConfig(
                agent_id="test",
                agent_type=AgentType.SALES,
                name="Test",
                description="Test",
                llm_config=model_config,
                prompt_template="test",
                max_concurrent_tasks=0  # 零值
            )


class TestWorkflowConfig:
    """测试工作流配置模型."""
    
    def test_workflow_config_creation(self):
        """测试工作流配置创建."""
        config = WorkflowConfig(
            workflow_id="wf_001",
            name="Sales Process",
            description="Handle sales inquiries",
            workflow_type="sequential",
            participating_agents=["sales_001", "manager_001"],
            execution_order=["sales_001", "manager_001"],
            timeout=300
        )
        
        assert config.workflow_id == "wf_001"
        assert config.name == "Sales Process"
        assert config.workflow_type == "sequential"
        assert len(config.participating_agents) == 2
        assert config.execution_order == ["sales_001", "manager_001"]
        assert config.enabled is True  # 默认值
    
    def test_workflow_config_validation(self):
        """测试工作流配置验证."""
        # 测试超时时间验证
        with pytest.raises(ValidationError):
            WorkflowConfig(
                workflow_id="test",
                name="Test",
                description="Test",
                workflow_type="sequential",
                participating_agents=["agent1"],
                timeout=-1  # 负数
            )


class TestIntentRoutingConfig:
    """测试意图路由配置模型."""
    
    def test_intent_routing_config_creation(self):
        """测试意图路由配置创建."""
        config = IntentRoutingConfig(
            intent_type="sales_inquiry",
            description="Sales related inquiries",
            keywords=["price", "product", "buy"],
            patterns=[r".*price.*", r".*cost.*"],
            target_agents=[AgentType.SALES, AgentType.COORDINATOR],
            confidence_threshold=0.85,
            requires_collaboration=True,
            fallback_agent=AgentType.CUSTOMER_SUPPORT
        )
        
        assert config.intent_type == "sales_inquiry"
        assert len(config.keywords) == 3
        assert len(config.patterns) == 2
        assert AgentType.SALES in config.target_agents
        assert config.confidence_threshold == 0.85
        assert config.requires_collaboration is True
    
    def test_intent_routing_config_validation(self):
        """测试意图路由配置验证."""
        # 测试置信度阈值验证
        with pytest.raises(ValidationError):
            IntentRoutingConfig(
                intent_type="test",
                description="Test",
                target_agents=[AgentType.SALES],
                confidence_threshold=1.5  # 超出范围
            )


class TestSystemConfig:
    """测试系统配置模型."""
    
    def test_system_config_creation(self):
        """测试系统配置创建."""
        config = SystemConfig(
            service_name="test-service",
            version="2.0.0",
            debug=True,
            log_level="DEBUG",
            max_concurrent_requests=200,
            api_key_required=True,
            allowed_origins=["http://localhost:3000"],
            rate_limit_requests=50
        )
        
        assert config.service_name == "test-service"
        assert config.version == "2.0.0"
        assert config.debug is True
        assert config.log_level == "DEBUG"
        assert config.max_concurrent_requests == 200
        assert config.api_key_required is True
        assert len(config.allowed_origins) == 1
    
    def test_system_config_defaults(self):
        """测试系统配置默认值."""
        config = SystemConfig()
        
        assert config.service_name == "multi-agent-service"
        assert config.version == "1.0.0"
        assert config.debug is False
        assert config.log_level == "INFO"
        assert config.max_concurrent_requests == 100
        assert config.metrics_enabled is True
    
    def test_system_config_validation(self):
        """测试系统配置验证."""
        # 测试日志级别验证
        with pytest.raises(ValidationError):
            SystemConfig(log_level="INVALID")
        
        # 测试最大并发请求数验证
        with pytest.raises(ValidationError):
            SystemConfig(max_concurrent_requests=0)


class TestServiceConfig:
    """测试服务总配置模型."""
    
    def create_sample_configs(self):
        """创建示例配置."""
        model_config = ModelConfig(
            provider=ModelProvider.QWEN,
            model_name="qwen-turbo",
            api_key="test-key"
        )
        
        agent_config = AgentConfig(
            agent_id="sales_001",
            agent_type=AgentType.SALES,
            name="Sales Agent",
            description="Sales representative",
            llm_config=model_config,
            prompt_template="You are a sales agent. {input}"
        )
        
        workflow_config = WorkflowConfig(
            workflow_id="wf_001",
            name="Sales Workflow",
            description="Sales process",
            workflow_type="sequential",
            participating_agents=["sales_001"]
        )
        
        intent_config = IntentRoutingConfig(
            intent_type="sales_inquiry",
            description="Sales inquiries",
            target_agents=[AgentType.SALES]
        )
        
        return model_config, agent_config, workflow_config, intent_config
    
    def test_service_config_creation(self):
        """测试服务配置创建."""
        model_config, agent_config, workflow_config, intent_config = self.create_sample_configs()
        
        service_config = ServiceConfig(
            agents=[agent_config],
            workflows=[workflow_config],
            intent_routing=[intent_config],
            model_providers=[model_config]
        )
        
        assert len(service_config.agents) == 1
        assert len(service_config.workflows) == 1
        assert len(service_config.intent_routing) == 1
        assert len(service_config.model_providers) == 1
    
    def test_service_config_get_methods(self):
        """测试服务配置获取方法."""
        model_config, agent_config, workflow_config, intent_config = self.create_sample_configs()
        
        service_config = ServiceConfig(
            agents=[agent_config],
            workflows=[workflow_config],
            intent_routing=[intent_config],
            model_providers=[model_config]
        )
        
        # 测试获取智能体配置
        found_agent = service_config.get_agent_config("sales_001")
        assert found_agent is not None
        assert found_agent.agent_id == "sales_001"
        
        # 测试获取不存在的智能体
        not_found = service_config.get_agent_config("nonexistent")
        assert not_found is None
        
        # 测试按类型获取智能体
        sales_agents = service_config.get_agents_by_type(AgentType.SALES)
        assert len(sales_agents) == 1
        assert sales_agents[0].agent_type == AgentType.SALES
        
        # 测试获取工作流配置
        found_workflow = service_config.get_workflow_config("wf_001")
        assert found_workflow is not None
        assert found_workflow.workflow_id == "wf_001"
        
        # 测试获取意图配置
        found_intent = service_config.get_intent_config("sales_inquiry")
        assert found_intent is not None
        assert found_intent.intent_type == "sales_inquiry"
        
        # 测试获取模型配置
        found_model = service_config.get_model_config(ModelProvider.QWEN)
        assert found_model is not None
        assert found_model.provider == ModelProvider.QWEN
    
    def test_service_config_validation(self):
        """测试服务配置验证."""
        model_config, agent_config, workflow_config, intent_config = self.create_sample_configs()
        
        # 创建重复ID的配置
        duplicate_agent = AgentConfig(
            agent_id="sales_001",  # 重复ID
            agent_type=AgentType.MANAGER,
            name="Manager Agent",
            description="Manager",
            llm_config=model_config,
            prompt_template="You are a manager. {input}"
        )
        
        service_config = ServiceConfig(
            agents=[agent_config, duplicate_agent],
            workflows=[workflow_config],
            intent_routing=[intent_config],
            model_providers=[model_config]
        )
        
        errors = service_config.validate_configuration()
        assert len(errors) > 0
        assert any("Duplicate agent ID" in error for error in errors)
        
        # 测试工作流引用不存在的智能体
        invalid_workflow = WorkflowConfig(
            workflow_id="wf_002",
            name="Invalid Workflow",
            description="References non-existent agent",
            workflow_type="sequential",
            participating_agents=["nonexistent_agent"]
        )
        
        service_config.workflows.append(invalid_workflow)
        errors = service_config.validate_configuration()
        assert any("references non-existent agent" in error for error in errors)


class TestConfigValidationResult:
    """测试配置验证结果模型."""
    
    def test_config_validation_result_creation(self):
        """测试配置验证结果创建."""
        result = ConfigValidationResult(
            is_valid=True,
            errors=[],
            warnings=["This is a warning"]
        )
        
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 1
    
    def test_config_validation_result_methods(self):
        """测试配置验证结果方法."""
        result = ConfigValidationResult(is_valid=True)
        
        # 添加错误应该设置is_valid为False
        result.add_error("Test error")
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0] == "Test error"
        
        # 添加警告不应该影响is_valid
        result.add_warning("Test warning")
        assert result.is_valid is False  # 仍然是False因为有错误
        assert len(result.warnings) == 1
        assert result.warnings[0] == "Test warning"


class TestConfigUpdateRequest:
    """测试配置更新请求模型."""
    
    def test_config_update_request_creation(self):
        """测试配置更新请求创建."""
        request = ConfigUpdateRequest(
            config_type="agent",
            config_id="sales_001",
            config_data={"name": "Updated Sales Agent"},
            validate_only=True
        )
        
        assert request.config_type == "agent"
        assert request.config_id == "sales_001"
        assert request.config_data["name"] == "Updated Sales Agent"
        assert request.validate_only is True
    
    def test_config_update_request_validation(self):
        """测试配置更新请求验证."""
        # 测试无效的配置类型
        with pytest.raises(ValidationError):
            ConfigUpdateRequest(
                config_type="invalid_type",
                config_id="test",
                config_data={}
            )


class TestConfigUpdateResponse:
    """测试配置更新响应模型."""
    
    def test_config_update_response_creation(self):
        """测试配置更新响应创建."""
        validation_result = ConfigValidationResult(
            is_valid=True,
            errors=[],
            warnings=[]
        )
        
        response = ConfigUpdateResponse(
            success=True,
            message="Configuration updated successfully",
            validation_result=validation_result,
            updated_config={"agent_id": "sales_001", "name": "Updated Agent"}
        )
        
        assert response.success is True
        assert response.message == "Configuration updated successfully"
        assert response.validation_result.is_valid is True
        assert response.updated_config["agent_id"] == "sales_001"


class TestConfigModelIntegration:
    """测试配置模型集成."""
    
    def test_complete_service_configuration(self):
        """测试完整的服务配置."""
        # 创建模型配置
        qwen_config = ModelConfig(
            provider=ModelProvider.QWEN,
            model_name="qwen-turbo",
            api_key="qwen-key"
        )
        
        deepseek_config = ModelConfig(
            provider=ModelProvider.DEEPSEEK,
            model_name="deepseek-chat",
            api_key="deepseek-key"
        )
        
        # 创建智能体配置
        sales_agent = AgentConfig(
            agent_id="sales_001",
            agent_type=AgentType.SALES,
            name="Sales Representative",
            description="Handles sales inquiries and product information",
            llm_config=qwen_config,
            prompt_template="You are a professional sales representative. Help customers with: {input}",
            capabilities=["product_info", "pricing", "quotation"]
        )
        
        support_agent = AgentConfig(
            agent_id="support_001",
            agent_type=AgentType.CUSTOMER_SUPPORT,
            name="Customer Support",
            description="Provides customer support and technical assistance",
            llm_config=deepseek_config,
            prompt_template="You are a helpful customer support agent. Assist with: {input}",
            capabilities=["troubleshooting", "account_help", "general_support"]
        )
        
        # 创建工作流配置
        sales_workflow = WorkflowConfig(
            workflow_id="sales_process",
            name="Sales Process Workflow",
            description="Complete sales inquiry handling process",
            workflow_type="sequential",
            participating_agents=["sales_001", "support_001"],
            execution_order=["sales_001", "support_001"]
        )
        
        # 创建意图路由配置
        sales_intent = IntentRoutingConfig(
            intent_type="sales_inquiry",
            description="Customer sales and product inquiries",
            keywords=["price", "product", "buy", "purchase", "cost"],
            target_agents=[AgentType.SALES],
            confidence_threshold=0.8
        )
        
        support_intent = IntentRoutingConfig(
            intent_type="customer_support",
            description="Customer support and technical issues",
            keywords=["help", "problem", "issue", "support", "error"],
            target_agents=[AgentType.CUSTOMER_SUPPORT],
            confidence_threshold=0.8
        )
        
        # 创建系统配置
        system_config = SystemConfig(
            service_name="multi-agent-sales-service",
            version="1.0.0",
            debug=False,
            log_level="INFO",
            max_concurrent_requests=50,
            api_key_required=True,
            rate_limit_enabled=True
        )
        
        # 创建完整服务配置
        service_config = ServiceConfig(
            system=system_config,
            agents=[sales_agent, support_agent],
            workflows=[sales_workflow],
            intent_routing=[sales_intent, support_intent],
            model_providers=[qwen_config, deepseek_config]
        )
        
        # 验证配置
        errors = service_config.validate_configuration()
        assert len(errors) == 0, f"Configuration validation failed: {errors}"
        
        # 测试配置查询功能
        assert service_config.get_agent_config("sales_001") is not None
        assert len(service_config.get_agents_by_type(AgentType.SALES)) == 1
        assert service_config.get_workflow_config("sales_process") is not None
        assert service_config.get_intent_config("sales_inquiry") is not None
        assert service_config.get_model_config(ModelProvider.QWEN) is not None
        
        # 验证配置数据完整性
        assert len(service_config.agents) == 2
        assert len(service_config.workflows) == 1
        assert len(service_config.intent_routing) == 2
        assert len(service_config.model_providers) == 2