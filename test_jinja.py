#!/usr/bin/env python3
"""Test jinja2 import."""

try:
    from jinja2 import Environment, FileSystemLoader, Template, select_autoescape
    print('✅ Jinja2 imported successfully')
except ImportError as e:
    print(f'❌ Jinja2 import failed: {e}')

# Test the template engine file step by step
import sys
sys.path.append('src')

try:
    # Test basic imports
    import asyncio
    import logging
    import os
    from typing import Dict, List, Any, Optional
    from datetime import datetime
    from pathlib import Path
    import json
    print('✅ All basic imports successful')
    
    # Now try to execute the template engine file
    with open('src/multi_agent_service/agents/patent/template_engine.py', 'r', encoding='utf-8') as f:
        code = f.read()
    
    # Try to compile and execute
    compiled_code = compile(code, 'template_engine.py', 'exec')
    namespace = {}
    exec(compiled_code, namespace)
    
    print('✅ Template engine code executed successfully')
    print('Available in namespace:', [k for k in namespace.keys() if not k.startswith('__')])
    
    if 'PatentTemplateEngine' in namespace:
        print('✅ PatentTemplateEngine class found in namespace')
        cls = namespace['PatentTemplateEngine']
        instance = cls()
        print('✅ PatentTemplateEngine instance created successfully')
    else:
        print('❌ PatentTemplateEngine class not found in namespace')
        
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()