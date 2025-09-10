#!/usr/bin/env python3
"""Simple import test."""

import sys
sys.path.append('src')

# Test step by step
print("Testing import...")

try:
    # First test the module
    import multi_agent_service.agents.patent.template_engine as te_module
    print("✅ Module imported")
    
    # Check what's in the module
    print(f"Module attributes: {[attr for attr in dir(te_module) if not attr.startswith('_')]}")
    
    # Try to get the class
    if hasattr(te_module, 'PatentTemplateEngine'):
        print("✅ PatentTemplateEngine found in module")
        cls = getattr(te_module, 'PatentTemplateEngine')
        print(f"✅ Class retrieved: {cls}")
        
        # Try to create instance
        instance = cls()
        print("✅ Instance created successfully")
        
    else:
        print("❌ PatentTemplateEngine NOT found in module")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()