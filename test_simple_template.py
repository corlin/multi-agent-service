#!/usr/bin/env python3
"""Test simple template engine."""

# Create a simple template engine file without any complex dependencies
simple_template_code = '''
"""Simple template engine."""

class PatentTemplateEngine:
    """Simple template engine for testing."""
    
    def __init__(self):
        self.name = "PatentTemplateEngine"
    
    async def render_template(self, template_name, content, charts, params):
        """Simple render method."""
        return f"<html><body><h1>Report: {template_name}</h1><p>{content.get('summary', 'No summary')}</p></body></html>"
    
    async def get_available_templates(self):
        """Get available templates."""
        return ["standard", "simple"]
'''

# Write to a test file
with open('simple_template_engine.py', 'w', encoding='utf-8') as f:
    f.write(simple_template_code)

# Test import
try:
    import sys
    sys.path.append('.')
    
    from simple_template_engine import PatentTemplateEngine
    print('✅ Simple template engine imported successfully')
    
    engine = PatentTemplateEngine()
    print('✅ Engine instance created')
    
    # Test async method
    import asyncio
    
    async def test():
        result = await engine.render_template(
            "test", 
            {"summary": "Test summary"}, 
            {}, 
            {}
        )
        print(f'✅ Render result: {result[:50]}...')
        
        templates = await engine.get_available_templates()
        print(f'✅ Available templates: {templates}')
    
    asyncio.run(test())
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()