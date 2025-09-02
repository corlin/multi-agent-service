#!/usr/bin/env python3
"""Test script for service startup."""

import asyncio
import sys
import traceback

async def test_startup():
    try:
        print('Testing service startup...')
        
        from src.multi_agent_service.core.lifecycle_manager import lifecycle_manager
        
        result = await lifecycle_manager.startup()
        print(f'Startup result: {result}')
        
        if result:
            print('Getting system status...')
            status = await lifecycle_manager.health_check()
            print(f'Health status: {status.get("healthy", False)}')
            
            print('Shutting down...')
            await lifecycle_manager.shutdown()
            print('Shutdown complete')
        else:
            print('Startup failed')
        
    except Exception as e:
        print(f'Error: {e}')
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_startup())
    sys.exit(0 if success else 1)