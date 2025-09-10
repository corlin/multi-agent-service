#!/usr/bin/env python3
"""Test script to verify patent MVP system setup."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.multi_agent_service.config.config_manager import ConfigManager
from src.multi_agent_service.patent.agents.base import PatentBaseAgent
from src.multi_agent_service.patent.models.patent_data import PatentData
from src.multi_agent_service.patent.models.requests import PatentAnalysisRequest
from src.multi_agent_service.models.enums import AgentType


def test_configuration_loading():
    """Test that patent configurations load correctly."""
    print("🔧 Testing configuration loading...")
    
    cm = ConfigManager()
    
    # Test agent configs
    agent_configs = cm.get_all_agent_configs()
    patent_agents = [aid for aid in agent_configs.keys() if 'patent' in aid]
    
    print(f"✅ Loaded {len(agent_configs)} total agent configs")
    print(f"✅ Found {len(patent_agents)} patent agents: {patent_agents}")
    
    # Test workflow configs
    workflow_configs = cm.get_all_workflow_configs()
    patent_workflows = [wid for wid in workflow_configs.keys() if 'patent' in wid]
    
    print(f"✅ Loaded {len(workflow_configs)} total workflow configs")
    print(f"✅ Found {len(patent_workflows)} patent workflows: {patent_workflows}")
    
    return len(patent_agents) == 5 and len(patent_workflows) >= 3


def test_patent_models():
    """Test patent data models."""
    print("\n📊 Testing patent data models...")
    
    from datetime import datetime
    
    # Test PatentData model
    patent = PatentData(
        application_number="US20240001",
        title="Test Patent for AI Technology",
        abstract="This is a test patent for AI technology...",
        applicants=["Test Company"],
        inventors=["Test Inventor"],
        application_date=datetime(2024, 1, 1),
        country="US",
        status="Published"
    )
    
    print(f"✅ Created patent: {patent.title}")
    
    # Test PatentAnalysisRequest model
    request = PatentAnalysisRequest(
        request_id="test_request_001",
        keywords=["artificial intelligence", "machine learning"],
        max_patents=100
    )
    
    print(f"✅ Created analysis request: {request.request_id}")
    
    return True


def test_agent_types():
    """Test that new agent types are available."""
    print("\n🤖 Testing agent types...")
    
    patent_agent_types = [
        AgentType.PATENT_DATA_COLLECTION,
        AgentType.PATENT_SEARCH,
        AgentType.PATENT_ANALYSIS,
        AgentType.PATENT_COORDINATOR,
        AgentType.PATENT_REPORT
    ]
    
    for agent_type in patent_agent_types:
        print(f"✅ Agent type available: {agent_type.value}")
    
    return True


def test_uv_dependencies():
    """Test that uv dependencies are installed correctly."""
    print("\n📦 Testing uv dependencies...")
    
    try:
        import aiohttp
        print("✅ aiohttp imported successfully")
        
        import pandas
        print("✅ pandas imported successfully")
        
        import numpy
        print("✅ numpy imported successfully")
        
        import matplotlib
        print("✅ matplotlib imported successfully")
        
        import plotly
        print("✅ plotly imported successfully")
        
        import redis
        print("✅ redis imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


async def test_patent_agent_basic_functionality():
    """Test basic patent agent functionality."""
    print("\n🧪 Testing patent agent basic functionality...")
    
    try:
        from src.multi_agent_service.patent.agents.data_collection import PatentDataCollectionAgent
        from src.multi_agent_service.models.config import AgentConfig
        from src.multi_agent_service.services.model_client import BaseModelClient
        
        # Create a mock model client
        class MockModelClient(BaseModelClient):
            async def initialize(self):
                return True
            
            async def health_check(self):
                return True
        
        # Create agent config
        config = AgentConfig(
            agent_id="test_patent_agent",
            agent_type=AgentType.PATENT_DATA_COLLECTION,
            name="Test Patent Agent",
            description="Test agent",
            enabled=True,
            capabilities=["专利数据处理"],
            llm_config={
                "provider": "qwen",
                "model_name": "qwen-turbo",
                "api_key": "test_key",
                "api_base": "https://test.com",
                "max_tokens": 2000,
                "temperature": 0.3,
                "timeout": 30,
                "retry_attempts": 3
            },
            prompt_template="Test template",
            system_prompt="Test system prompt",
            max_concurrent_tasks=1,
            priority=5
        )
        
        # Create agent
        agent = PatentDataCollectionAgent(config, MockModelClient())
        
        # Test capabilities
        capabilities = await agent.get_capabilities()
        print(f"✅ Agent capabilities: {len(capabilities)} items")
        
        # Test can_handle_request
        from src.multi_agent_service.models.base import UserRequest
        request = UserRequest(
            request_id="test_001",
            content="请帮我分析人工智能相关的专利趋势",
            user_id="test_user"
        )
        
        confidence = await agent.can_handle_request(request)
        print(f"✅ Patent request confidence: {confidence}")
        
        return True
        
    except Exception as e:
        print(f"❌ Patent agent test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Starting Patent MVP System Setup Tests\n")
    
    tests = [
        ("Configuration Loading", test_configuration_loading),
        ("Patent Models", test_patent_models),
        ("Agent Types", test_agent_types),
        ("UV Dependencies", test_uv_dependencies),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    # Run async test
    try:
        async_result = asyncio.run(test_patent_agent_basic_functionality())
        results.append(("Patent Agent Functionality", async_result))
    except Exception as e:
        print(f"❌ Patent Agent Functionality failed with error: {e}")
        results.append(("Patent Agent Functionality", False))
    
    # Print summary
    print("\n" + "="*50)
    print("📋 TEST SUMMARY")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Patent MVP system setup is complete.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the configuration.")
        return 1


if __name__ == "__main__":
    exit(main())