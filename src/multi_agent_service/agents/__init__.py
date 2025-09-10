"""Multi-agent system components."""

from .base import (
    BaseAgent,
    AgentLifecycleInterface,
    AgentCollaborationInterface,
    AgentProcessingInterface
)
from .registry import AgentRegistry, agent_registry
from .exceptions import (
    AgentException,
    AgentInitializationError,
    AgentConfigurationError,
    AgentProcessingError,
    AgentOverloadError,
    AgentCollaborationError,
    AgentNotFoundError,
    AgentUnavailableError,
    AgentTimeoutError,
    AgentModelError,
    AgentRegistryError,
    AgentValidationError
)

# Specific agent implementations
from .sales_agent import SalesAgent
from .customer_support_agent import CustomerSupportAgent
from .manager_agent import ManagerAgent
from .field_service_agent import FieldServiceAgent
from .coordinator_agent import CoordinatorAgent

# Patent agent implementations
from .patent.data_collection_agent import PatentDataCollectionAgent
from .patent.coordinator_agent import PatentCoordinatorAgent
from .patent.search_agent import PatentSearchAgent
from .patent.analysis_agent import PatentAnalysisAgent
from .patent.report_agent import PatentReportAgent

# Patent agent registry
from .patent_registry import (
    PatentAgentRegistry,
    register_patent_agents,
    get_patent_agent_registry_info,
    validate_patent_agent_setup,
    initialize_patent_agents
)

__all__ = [
    # Base classes and interfaces
    "BaseAgent",
    "AgentLifecycleInterface", 
    "AgentCollaborationInterface",
    "AgentProcessingInterface",
    
    # Registry
    "AgentRegistry",
    "agent_registry",
    
    # Specific agent implementations
    "SalesAgent",
    "CustomerSupportAgent",
    "ManagerAgent",
    "FieldServiceAgent",
    "CoordinatorAgent",
    
    # Patent agent implementations
    "PatentDataCollectionAgent",
    "PatentCoordinatorAgent",
    "PatentSearchAgent", 
    "PatentAnalysisAgent",
    "PatentReportAgent",
    
    # Patent agent registry
    "PatentAgentRegistry",
    "register_patent_agents",
    "get_patent_agent_registry_info",
    "validate_patent_agent_setup",
    "initialize_patent_agents",
    
    # Exceptions
    "AgentException",
    "AgentInitializationError",
    "AgentConfigurationError", 
    "AgentProcessingError",
    "AgentOverloadError",
    "AgentCollaborationError",
    "AgentNotFoundError",
    "AgentUnavailableError",
    "AgentTimeoutError",
    "AgentModelError",
    "AgentRegistryError",
    "AgentValidationError"
]