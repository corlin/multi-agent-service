#!/usr/bin/env python3
"""Check syntax."""

with open('src/multi_agent_service/agents/patent/template_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

try:
    compile(content, 'template_engine.py', 'exec')
    print('✅ File compiles successfully')
    
    # Try to execute and see what's defined
    namespace = {}
    exec(content, namespace)
    
    classes = [k for k, v in namespace.items() if isinstance(v, type)]
    print(f'Classes found: {classes}')
    
    if 'PatentTemplateEngine' in namespace:
        print('✅ PatentTemplateEngine found')
    else:
        print('❌ PatentTemplateEngine NOT found')
        print('Available items:', [k for k in namespace.keys() if not k.startswith('__')])
        
except SyntaxError as e:
    print(f'❌ Syntax error at line {e.lineno}: {e.msg}')
    print(f'Text: {e.text}')
except Exception as e:
    print(f'❌ Runtime error: {e}')
    import traceback
    traceback.print_exc()