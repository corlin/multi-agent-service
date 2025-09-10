#!/usr/bin/env python3
"""Test minimal template engine."""

import sys
sys.path.append('src')

# Test step by step
try:
    # Test basic class definition
    code = '''
class PatentTemplateEngine:
    def __init__(self):
        self.name = "test"
    
    def test_method(self):
        return "working"
'''
    
    namespace = {}
    exec(code, namespace)
    
    if 'PatentTemplateEngine' in namespace:
        print('✅ Basic class definition works')
        cls = namespace['PatentTemplateEngine']
        instance = cls()
        print(f'✅ Instance created: {instance.test_method()}')
    else:
        print('❌ Basic class definition failed')
        
    # Now test with jinja2
    from jinja2 import Environment, FileSystemLoader
    
    code_with_jinja = '''
from jinja2 import Environment, FileSystemLoader

class PatentTemplateEngine:
    def __init__(self):
        self.env = Environment(loader=FileSystemLoader('.'))
        self.name = "test_with_jinja"
    
    def test_method(self):
        return "working with jinja"
'''
    
    namespace2 = {'Environment': Environment, 'FileSystemLoader': FileSystemLoader}
    exec(code_with_jinja, namespace2)
    
    if 'PatentTemplateEngine' in namespace2:
        print('✅ Class with Jinja2 works')
        cls2 = namespace2['PatentTemplateEngine']
        instance2 = cls2()
        print(f'✅ Instance created: {instance2.test_method()}')
    else:
        print('❌ Class with Jinja2 failed')
        
    # Now test the actual file content but simplified
    print('Testing actual file...')
    
    # Read and execute the actual file
    with open('src/multi_agent_service/agents/patent/template_engine.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f'File length: {len(content)} characters')
    
    # Check if class definition exists in content
    if 'class PatentTemplateEngine:' in content:
        print('✅ Class definition found in file')
    else:
        print('❌ Class definition NOT found in file')
        
    # Try to compile
    try:
        compiled = compile(content, 'template_engine.py', 'exec')
        print('✅ File compiles successfully')
        
        # Try to execute
        namespace3 = {}
        exec(compiled, namespace3)
        print('✅ File executes successfully')
        
        # Check what's in namespace
        classes = [k for k, v in namespace3.items() if isinstance(v, type)]
        print(f'Classes found: {classes}')
        
        if 'PatentTemplateEngine' in namespace3:
            print('✅ PatentTemplateEngine found in namespace')
        else:
            print('❌ PatentTemplateEngine NOT found in namespace')
            print('Available items:', list(namespace3.keys()))
            
    except Exception as e:
        print(f'❌ Compilation/execution error: {e}')
        import traceback
        traceback.print_exc()
        
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()