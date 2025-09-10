#!/usr/bin/env python3
"""Test direct import."""

import sys
import os
sys.path.append('src')

# Test if the file exists and is readable
template_file = 'src/multi_agent_service/agents/patent/template_engine.py'
print(f'File exists: {os.path.exists(template_file)}')

if os.path.exists(template_file):
    with open(template_file, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f'File size: {len(content)} characters')
    print(f'Contains class: {"class PatentTemplateEngine:" in content}')

# Try to import the module directly
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("template_engine", template_file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    print('✅ Module loaded successfully')
    print(f'Module attributes: {[attr for attr in dir(module) if not attr.startswith("_")]}')
    
    if hasattr(module, 'PatentTemplateEngine'):
        print('✅ PatentTemplateEngine found')
        cls = getattr(module, 'PatentTemplateEngine')
        instance = cls()
        print('✅ Instance created successfully')
    else:
        print('❌ PatentTemplateEngine not found')
        
except Exception as e:
    print(f'❌ Import error: {e}')
    import traceback
    traceback.print_exc()