"""Patent report template engine implementation."""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class PatentTemplateEngine:
    """专利报告模板引擎，负责管理和渲染报告模板."""
    
    def __init__(self, template_dir: str = "templates/patent", config: Optional[Dict[str, Any]] = None):
        """初始化模板引擎."""
        self.template_dir = Path(template_dir)
        self.config = config or {}
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.available_templates = {
            "standard": "standard.html",
            "simple": "simple.html", 
            "detailed": "detailed.html",
            "executive": "executive.html"
        }
        self.logger = logging.getLogger(f"{__name__}.PatentTemplateEngine")
    
    async def render_template(self, template_name: str, content: Dict[str, Any], 
                            charts: Dict[str, Any], params: Dict[str, Any]) -> str:
        """渲染模板."""
        try:
            return await self._render_fallback_template(content, charts, params)
        except Exception as e:
            self.logger.error(f"Error rendering template {template_name}: {str(e)}")
            return "<html><body><h1>报告生成失败</h1><p>模板渲染过程中发生错误。</p></body></html>"
    
    async def _render_fallback_template(self, content: Dict[str, Any], 
                                      charts: Dict[str, Any], params: Dict[str, Any]) -> str:
        """渲染后备模板."""
        try:
            html_content = self._render_content_as_html(content)
            
            fallback_html = f'''<!DOCTYPE html>
<html lang="{params.get('language', 'zh')}">
<head>
    <meta charset="UTF-8">
    <title>专利分析报告</title>
    <style>
        body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; margin: 20px; }}
        .section {{ margin-bottom: 30px; }}
        .section h2 {{ color: #333; border-left: 4px solid #007acc; padding-left: 15px; }}
    </style>
</head>
<body>
    <h1>专利分析报告</h1>
    <p><em>生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</em></p>
    {html_content}
    <div class="section">
        <h2>📈 图表信息</h2>
        <p>本报告包含 <strong>{len(charts)}</strong> 个图表。</p>
    </div>
</body>
</html>'''
            return fallback_html
        except Exception as e:
            self.logger.error(f"Error rendering fallback template: {str(e)}")
            return "<html><body><h1>报告生成失败</h1></body></html>"
    
    def _render_content_as_html(self, content: Dict[str, Any]) -> str:
        """将内容渲染为HTML."""
        html_parts = []
        
        if "summary" in content:
            html_parts.append(f'<div class="section"><h2>📋 执行摘要</h2><p>{content["summary"]}</p></div>')
        
        if "sections" in content:
            for section_name, section_content in content["sections"].items():
                html_parts.append(f'<div class="section"><h2>📄 {section_name.title()}分析</h2><div>{str(section_content)}</div></div>')
        
        if "insights" in content:
            html_parts.append(f'<div class="section"><h2>💡 关键洞察</h2><div>{str(content["insights"])}</div></div>')
        
        if "recommendations" in content:
            html_parts.append(f'<div class="section"><h2>📋 建议和结论</h2><div>{str(content["recommendations"])}</div></div>')
        
        return ''.join(html_parts)
    
    async def get_available_templates(self) -> List[str]:
        """获取可用模板列表."""
        return list(self.available_templates.keys())
    
    async def validate_template(self, template_name: str) -> Dict[str, Any]:
        """验证模板."""
        try:
            template_file = self.available_templates.get(template_name)
            if not template_file:
                return {"valid": False, "error": f"Template {template_name} not found"}
            return {"valid": True, "template_file": template_file}
        except Exception as e:
            return {"valid": False, "error": str(e)}