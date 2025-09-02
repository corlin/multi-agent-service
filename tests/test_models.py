"""Unit tests for data models."""

import pytest
from datetime import datetime
from uuid import UUID

from src.multi_agent_service.models import (
    AgentType,
    IntentType,
    WorkflowType,
    WorkflowStatus,
    AgentStatus,
    Priority,
    ModelProvider,
    Entity,
    Action,
    UserRequest,
    IntentResult,
    AgentResponse,
    ExecutionStep,
    WorkflowState,
    AgentInfo,
    CollaborationResult,
    Conflict,
    ChatCompletionRequest,
    ChatCompletionResponse,
    RouteRequest,
    RouteResponse,
    WorkflowExecuteRequest,
    WorkflowExecuteResponse,
    AgentStatusRequest,
    AgentStatusResponse,
    WorkflowStatusRequest,
    WorkflowStatusResponse,
    HealthCheckResponse,
    ErrorResponse,
)


class TestEnums:
    """测试枚举类型."""
    
    def test_agent_type_enum(self):
        """测试智能体类型枚举."""
        assert AgentType.COORDINATOR == "coordinator"
        assert AgentType.SALES == "sales"
        assert AgentType.MANAGER == "manager"
        assert AgentType.FIELD_SERVICE == "field_service"
        assert AgentType.CUSTOMER_SUPPORT == "customer_support"
    
    def test_intent_type_enum(self):
        """测试意图类型枚举."""
        assert IntentType.SALES_INQUIRY == "sales_inquiry"
        assert IntentType.CUSTOMER_SUPPORT == "customer_support"
        assert IntentType.TECHNICAL_SERVICE == "technical_service"
        assert IntentType.MANAGEMENT_DECISION == "management_decision"
        assert IntentType.GENERAL_INQUIRY == "general_inquiry"
        assert IntentType.COLLABORATION_REQUIRED == "collaboration_required"
    
    def test_workflow_type_enum(self):
        """测试工作流类型枚举."""
        assert WorkflowType.SEQUENTIAL == "sequential"
        assert WorkflowType.PARALLEL == "parallel"
        assert WorkflowType.HIERARCHICAL == "hierarchical"
    
    def test_workflow_status_enum(self):
        """测试工作流状态枚举."""
        assert WorkflowStatus.PENDING == "pending"
        assert WorkflowStatus.RUNNING == "running"
        assert WorkflowStatus.COMPLETED == "completed"
        assert WorkflowStatus.FAILED == "failed"
        assert WorkflowStatus.CANCELLED == "cancelled"
    
    def test_agent_status_enum(self):
        """测试智能体状态枚举."""
        assert AgentStatus.IDLE == "idle"
        assert AgentStatus.BUSY == "busy"
        assert AgentStatus.ERROR == "error"
        assert AgentStatus.OFFLINE == "offline"
    
    def test_priority_enum(self):
        """测试优先级枚举."""
        assert Priority.LOW == "low"
        assert Priority.NORMAL == "normal"
        assert Priority.HIGH == "high"
        assert Priority.URGENT == "urgent"
    
    def test_model_provider_enum(self):
        """测试模型提供商枚举."""
        assert ModelProvider.QWEN == "qwen"
        assert ModelProvider.DEEPSEEK == "deepseek"
        assert ModelProvider.GLM == "glm"
        assert ModelProvider.OPENAI == "openai"
        assert ModelProvider.CUSTOM == "custom"


class TestBaseModels:
    """测试基础数据模型."""
    
    def test_entity_model(self):
        """测试实体模型."""
        entity = Entity(
            name="product",
            value="iPhone 15",
            confidence=0.95,
            entity_type="product_name"
        )
        assert entity.name == "product"
        assert entity.value == "iPhone 15"
        assert entity.confidence == 0.95
        assert entity.entity_type == "product_name"
    
    def test_entity_model_validation(self):
        """测试实体模型验证."""
        # 测试置信度范围验证
        with pytest.raises(ValueError):
            Entity(
                name="test",
                value="test",
                confidence=1.5,  # 超出范围
                entity_type="test"
            )
        
        with pytest.raises(ValueError):
            Entity(
                name="test",
                value="test",
                confidence=-0.1,  # 超出范围
                entity_type="test"
            )
    
    def test_action_model(self):
        """测试动作模型."""
        action = Action(
            action_type="send_message",
            parameters={"recipient": "user123", "message": "Hello"},
            description="Send a message to user"
        )
        assert action.action_type == "send_message"
        assert action.parameters["recipient"] == "user123"
        assert action.description == "Send a message to user"
    
    def test_user_request_model(self):
        """测试用户请求模型."""
        request = UserRequest(
            content="I need help with my order",
            user_id="user123",
            context={"session_id": "sess456"},
            priority=Priority.HIGH
        )
        assert request.content == "I need help with my order"
        assert request.user_id == "user123"
        assert request.priority == Priority.HIGH
        assert "session_id" in request.context
        assert isinstance(request.timestamp, datetime)
        # 验证request_id是有效的UUID
        UUID(request.request_id)
    
    def test_user_request_defaults(self):
        """测试用户请求模型默认值."""
        request = UserRequest(content="Test message")
        assert request.priority == Priority.NORMAL
        assert request.context == {}
        assert request.user_id is None
        assert isinstance(request.request_id, str)
        assert isinstance(request.timestamp, datetime)
    
    def test_intent_result_model(self):
        """测试意图识别结果模型."""
        entities = [
            Entity(name="product", value="laptop", confidence=0.9, entity_type="product")
        ]
        intent = IntentResult(
            intent_type=IntentType.SALES_INQUIRY,
            confidence=0.85,
            entities=entities,
            suggested_agents=[AgentType.SALES, AgentType.COORDINATOR],
            requires_collaboration=True,
            reasoning="Customer asking about laptop specifications"
        )
        assert intent.intent_type == IntentType.SALES_INQUIRY
        assert intent.confidence == 0.85
        assert len(intent.entities) == 1
        assert AgentType.SALES in intent.suggested_agents
        assert intent.requires_collaboration is True
    
    def test_agent_response_model(self):
        """测试智能体响应模型."""
        actions = [
            Action(action_type="follow_up", parameters={"delay": 3600})
        ]
        response = AgentResponse(
            agent_id="agent_001",
            agent_type=AgentType.SALES,
            response_content="I can help you with that product inquiry.",
            confidence=0.92,
            next_actions=actions,
            collaboration_needed=False,
            metadata={"processing_time": 1.5}
        )
        assert response.agent_id == "agent_001"
        assert response.agent_type == AgentType.SALES
        assert response.confidence == 0.92
        assert len(response.next_actions) == 1
        assert response.collaboration_needed is False
        assert isinstance(response.timestamp, datetime)
    
    def test_execution_step_model(self):
        """测试执行步骤模型."""
        action = Action(action_type="analyze", parameters={"text": "sample"})
        step = ExecutionStep(
            agent_id="agent_001",
            action=action,
            result={"analysis": "positive"},
            status="completed"
        )
        assert step.agent_id == "agent_001"
        assert step.action.action_type == "analyze"
        assert step.result["analysis"] == "positive"
        assert step.status == "completed"
        assert isinstance(step.start_time, datetime)
        UUID(step.step_id)  # 验证step_id是有效的UUID
    
    def test_workflow_state_model(self):
        """测试工作流状态模型."""
        workflow = WorkflowState(
            status=WorkflowStatus.RUNNING,
            current_step=2,
            total_steps=5,
            participating_agents=["agent_001", "agent_002"],
            metadata={"priority": "high"}
        )
        assert workflow.status == WorkflowStatus.RUNNING
        assert workflow.current_step == 2
        assert workflow.total_steps == 5
        assert len(workflow.participating_agents) == 2
        assert isinstance(workflow.created_at, datetime)
        assert isinstance(workflow.updated_at, datetime)
        UUID(workflow.workflow_id)  # 验证workflow_id是有效的UUID
    
    def test_agent_info_model(self):
        """测试智能体信息模型."""
        agent = AgentInfo(
            agent_id="sales_001",
            agent_type=AgentType.SALES,
            name="Sales Representative",
            description="Handles sales inquiries and product information",
            capabilities=["product_info", "pricing", "quotation"],
            current_load=3,
            max_load=10
        )
        assert agent.agent_id == "sales_001"
        assert agent.agent_type == AgentType.SALES
        assert agent.status == AgentStatus.IDLE  # 默认状态
        assert len(agent.capabilities) == 3
        assert agent.current_load == 3
        assert isinstance(agent.last_active, datetime)
    
    def test_collaboration_result_model(self):
        """测试协作结果模型."""
        responses = [
            AgentResponse(
                agent_id="agent_001",
                agent_type=AgentType.SALES,
                response_content="Sales perspective",
                confidence=0.9
            )
        ]
        collaboration = CollaborationResult(
            participating_agents=["agent_001", "agent_002"],
            final_result="Collaborative solution reached",
            individual_responses=responses,
            consensus_reached=True,
            resolution_method="voting"
        )
        assert len(collaboration.participating_agents) == 2
        assert collaboration.consensus_reached is True
        assert len(collaboration.individual_responses) == 1
        UUID(collaboration.collaboration_id)
    
    def test_conflict_model(self):
        """测试冲突模型."""
        conflict = Conflict(
            conflicting_agents=["agent_001", "agent_002"],
            conflict_type="priority_disagreement",
            description="Agents disagree on task priority",
            proposed_solutions=["solution_a", "solution_b"],
            resolution="solution_a",
            resolved=True
        )
        assert len(conflict.conflicting_agents) == 2
        assert conflict.conflict_type == "priority_disagreement"
        assert conflict.resolved is True
        assert len(conflict.proposed_solutions) == 2
        UUID(conflict.conflict_id)


class TestAPIModels:
    """测试API模型."""
    
    def test_chat_completion_request(self):
        """测试聊天完成请求模型."""
        request = ChatCompletionRequest(
            messages=[{"role": "user", "content": "Hello"}],
            model="gpt-3.5-turbo",
            max_tokens=100,
            temperature=0.7,
            stream=False,
            user_id="user123"
        )
        assert len(request.messages) == 1
        assert request.model == "gpt-3.5-turbo"
        assert request.max_tokens == 100
        assert request.temperature == 0.7
        assert request.stream is False
    
    def test_chat_completion_response(self):
        """测试聊天完成响应模型."""
        response = ChatCompletionResponse(
            id="resp_123",
            created=1234567890,
            model="gpt-3.5-turbo",
            choices=[{"message": {"content": "Hello back!"}}],
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
        )
        assert response.id == "resp_123"
        assert response.object == "chat.completion"
        assert response.model == "gpt-3.5-turbo"
        assert len(response.choices) == 1
        assert response.usage["total_tokens"] == 15
    
    def test_route_request(self):
        """测试路由请求模型."""
        request = RouteRequest(
            content="I need technical support",
            user_id="user123",
            context={"session": "sess456"},
            priority=Priority.HIGH,
            preferred_agents=[AgentType.CUSTOMER_SUPPORT]
        )
        assert request.content == "I need technical support"
        assert request.priority == Priority.HIGH
        assert AgentType.CUSTOMER_SUPPORT in request.preferred_agents
    
    def test_route_response(self):
        """测试路由响应模型."""
        intent = IntentResult(
            intent_type=IntentType.CUSTOMER_SUPPORT,
            confidence=0.9,
            suggested_agents=[AgentType.CUSTOMER_SUPPORT]
        )
        response = RouteResponse(
            intent_result=intent,
            selected_agent=AgentType.CUSTOMER_SUPPORT,
            routing_confidence=0.95,
            alternative_agents=[AgentType.FIELD_SERVICE],
            requires_collaboration=False,
            estimated_processing_time=30
        )
        assert response.selected_agent == AgentType.CUSTOMER_SUPPORT
        assert response.routing_confidence == 0.95
        assert response.requires_collaboration is False
    
    def test_workflow_execute_request(self):
        """测试工作流执行请求模型."""
        request = WorkflowExecuteRequest(
            workflow_type=WorkflowType.SEQUENTIAL,
            tasks=[{"task": "analyze", "params": {}}],
            participating_agents=[AgentType.SALES, AgentType.MANAGER],
            context={"priority": "high"},
            timeout=300
        )
        assert request.workflow_type == WorkflowType.SEQUENTIAL
        assert len(request.tasks) == 1
        assert len(request.participating_agents) == 2
        assert request.timeout == 300
    
    def test_workflow_execute_response(self):
        """测试工作流执行响应模型."""
        response = WorkflowExecuteResponse(
            workflow_id="wf_123",
            status="started",
            message="Workflow execution initiated",
            estimated_completion_time=datetime.now()
        )
        assert response.workflow_id == "wf_123"
        assert response.status == "started"
        assert isinstance(response.estimated_completion_time, datetime)
    
    def test_agent_status_request(self):
        """测试智能体状态请求模型."""
        request = AgentStatusRequest(
            agent_ids=["agent_001", "agent_002"],
            agent_types=[AgentType.SALES],
            include_metrics=True
        )
        assert len(request.agent_ids) == 2
        assert AgentType.SALES in request.agent_types
        assert request.include_metrics is True
    
    def test_agent_status_response(self):
        """测试智能体状态响应模型."""
        response = AgentStatusResponse(
            agents=[{"id": "agent_001", "status": "idle"}],
            total_count=5,
            active_count=3
        )
        assert len(response.agents) == 1
        assert response.total_count == 5
        assert response.active_count == 3
        assert isinstance(response.timestamp, datetime)
    
    def test_workflow_status_request(self):
        """测试工作流状态请求模型."""
        request = WorkflowStatusRequest(
            workflow_id="wf_123",
            include_history=True,
            include_agent_details=False
        )
        assert request.workflow_id == "wf_123"
        assert request.include_history is True
        assert request.include_agent_details is False
    
    def test_workflow_status_response(self):
        """测试工作流状态响应模型."""
        workflow_state = WorkflowState(
            status=WorkflowStatus.RUNNING,
            current_step=2,
            total_steps=5
        )
        response = WorkflowStatusResponse(
            workflow_state=workflow_state,
            progress_percentage=40.0,
            estimated_remaining_time=120
        )
        assert response.workflow_state.status == WorkflowStatus.RUNNING
        assert response.progress_percentage == 40.0
        assert response.estimated_remaining_time == 120
    
    def test_health_check_response(self):
        """测试健康检查响应模型."""
        response = HealthCheckResponse(
            status="healthy",
            version="1.0.0",
            uptime=3600,
            agents_status={"sales": "active", "support": "active"},
            system_metrics={"cpu": 45.2, "memory": 67.8}
        )
        assert response.status == "healthy"
        assert response.version == "1.0.0"
        assert response.uptime == 3600
        assert len(response.agents_status) == 2
        assert isinstance(response.timestamp, datetime)
    
    def test_error_response(self):
        """测试错误响应模型."""
        response = ErrorResponse(
            error_code="AGENT_NOT_FOUND",
            error_message="The specified agent was not found",
            error_details={"agent_id": "invalid_agent"},
            request_id="req_123"
        )
        assert response.error_code == "AGENT_NOT_FOUND"
        assert response.error_message == "The specified agent was not found"
        assert response.error_details["agent_id"] == "invalid_agent"
        assert response.request_id == "req_123"
        assert isinstance(response.timestamp, datetime)


class TestModelValidation:
    """测试模型验证功能."""
    
    def test_confidence_validation(self):
        """测试置信度字段验证."""
        # 有效的置信度值
        entity = Entity(name="test", value="test", confidence=0.5, entity_type="test")
        assert entity.confidence == 0.5
        
        # 边界值测试
        entity_min = Entity(name="test", value="test", confidence=0.0, entity_type="test")
        assert entity_min.confidence == 0.0
        
        entity_max = Entity(name="test", value="test", confidence=1.0, entity_type="test")
        assert entity_max.confidence == 1.0
    
    def test_required_fields(self):
        """测试必填字段验证."""
        # 缺少必填字段应该抛出异常
        with pytest.raises(ValueError):
            UserRequest()  # 缺少content字段
        
        with pytest.raises(ValueError):
            AgentResponse(agent_id="test")  # 缺少其他必填字段
    
    def test_default_values(self):
        """测试默认值设置."""
        request = UserRequest(content="test")
        assert request.priority == Priority.NORMAL
        assert request.context == {}
        
        workflow = WorkflowState()
        assert workflow.status == WorkflowStatus.PENDING
        assert workflow.current_step == 0
        assert workflow.participating_agents == []
    
    def test_json_serialization(self):
        """测试JSON序列化."""
        request = UserRequest(content="test message")
        json_data = request.model_dump()
        
        assert "request_id" in json_data
        assert "content" in json_data
        assert "timestamp" in json_data
        assert json_data["content"] == "test message"
        
        # 测试从JSON反序列化
        new_request = UserRequest.model_validate(json_data)
        assert new_request.content == request.content
        assert new_request.request_id == request.request_id