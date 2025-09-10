#!/usr/bin/env python3
"""Debug file content."""

import os

file_path = 'src/multi_agent_service/agents/patent/template_engine.py'

print(f"File exists: {os.path.exists(file_path)}")
print(f"File size: {os.path.getsize(file_path)} bytes")

with open(file_path, 'rb') as f:
    raw_content = f.read()
    print(f"Raw content length: {len(raw_content)} bytes")
    print(f"First 100 bytes: {raw_content[:100]}")

with open(file_path, 'r', encoding='utf-8') as f:
    text_content = f.read()
    print(f"Text content length: {len(text_content)} characters")
    print(f"Contains 'class PatentTemplateEngine': {'class PatentTemplateEngine' in text_content}")
    
    # Check for the exact class definition
    lines = text_content.split('\n')
    for i, line in enumerate(lines):
        if 'class PatentTemplateEngine' in line:
            print(f"Found class definition at line {i+1}: {repr(line)}")
            break
    else:
        print("Class definition not found in any line")
        
    # Try to find any class definitions
    for i, line in enumerate(lines):
        if line.strip().startswith('class '):
            print(f"Found class at line {i+1}: {repr(line)}")

# Try to execute the content manually
try:
    namespace = {}
    exec(text_content, namespace)
    print(f"Execution successful. Namespace keys: {list(namespace.keys())}")
    
    # Check for classes specifically
    classes = []
    for name, obj in namespace.items():
        if isinstance(obj, type):
            classes.append(name)
    print(f"Classes found: {classes}")
    
except Exception as e:
    print(f"Execution failed: {e}")
    import traceback
    traceback.print_exc()