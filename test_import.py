#!/usr/bin/env python3
"""Test import."""

import sys
sys.path.append('src')

try:
    import multi_agent_service.agents.patent.template_engine as te
    print('Module imported successfully')
    print('Available attributes:', dir(te))
    
    # Try to import the class
    from multi_agent_service.agents.patent.template_engine import PatentTemplateEngine
    print('PatentTemplateEngine imported successfully')
    
    # Try to create an instance
    engine = PatentTemplateEngine()
    print('PatentTemplateEngine instance created successfully')
    
except Exception as e:
    print('Import error:', e)
    import traceback
    traceback.print_exc()