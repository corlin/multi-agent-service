#!/usr/bin/env python3
"""Test ModelConfig creation."""

from src.multi_agent_service.models.model_service import ModelConfig, LoadBalancingStrategy
from src.multi_agent_service.models.enums import ModelProvider

try:
    config = ModelConfig(
        provider=ModelProvider.QWEN,
        model_name="qwen-turbo",
        api_key="test",
        base_url="https://test.com",
        enabled=True
    )
    print(f"ModelConfig created successfully: {config}")
    print(f"Has enabled field: {hasattr(config, 'enabled')}")
    print(f"Enabled value: {config.enabled}")
except Exception as e:
    print(f"Error creating ModelConfig: {e}")
    import traceback
    traceback.print_exc()