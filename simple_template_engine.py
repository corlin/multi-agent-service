
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
