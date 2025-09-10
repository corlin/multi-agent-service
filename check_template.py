#!/usr/bin/env python3
"""Check template engine file."""

with open('src/multi_agent_service/agents/patent/template_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()
    print(f'File length: {len(content)} characters')
    print('Last 200 characters:')
    print(repr(content[-200:]))
    
    # Check for class definition
    if 'class PatentTemplateEngine:' in content:
        print('✅ PatentTemplateEngine class found')
    else:
        print('❌ PatentTemplateEngine class NOT found')
    
    # Check for syntax errors
    try:
        compile(content, 'template_engine.py', 'exec')
        print('✅ File compiles successfully')
    except SyntaxError as e:
        print(f'❌ Syntax error: {e}')
        print(f'Line {e.lineno}: {e.text}')