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
    
    async def create_custom_template(self, template_name: str, template_content: str) -> Dict[str, Any]:
        """创建自定义模板."""
        try:
            template_file = f"{template_name}.html"
            template_path = self.template_dir / template_file
            
            # 写入模板文件
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(template_content)
            
            # 添加到可用模板列表
            self.available_templates[template_name] = template_file
            
            self.logger.info(f"Created custom template: {template_name}")
            
            return {
                "success": True,
                "template_name": template_name,
                "template_file": template_file,
                "path": str(template_path)
            }
            
        except Exception as e:
            self.logger.error(f"Error creating custom template: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_template(self, template_name: str, template_content: str) -> Dict[str, Any]:
        """更新现有模板."""
        try:
            if template_name not in self.available_templates:
                return {"success": False, "error": f"Template {template_name} not found"}
            
            template_file = self.available_templates[template_name]
            template_path = self.template_dir / template_file
            
            # 备份原模板
            backup_path = self.template_dir / f"{template_file}.backup"
            if template_path.exists():
                import shutil
                shutil.copy2(template_path, backup_path)
            
            # 写入新内容
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(template_content)
            
            self.logger.info(f"Updated template: {template_name}")
            
            return {
                "success": True,
                "template_name": template_name,
                "backup_created": backup_path.exists()
            }
            
        except Exception as e:
            self.logger.error(f"Error updating template: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def delete_template(self, template_name: str) -> Dict[str, Any]:
        """删除模板."""
        try:
            if template_name not in self.available_templates:
                return {"success": False, "error": f"Template {template_name} not found"}
            
            # 不允许删除内置模板
            builtin_templates = ["standard", "simple", "detailed", "executive"]
            if template_name in builtin_templates:
                return {"success": False, "error": f"Cannot delete builtin template: {template_name}"}
            
            template_file = self.available_templates[template_name]
            template_path = self.template_dir / template_file
            
            # 删除文件
            if template_path.exists():
                template_path.unlink()
            
            # 从可用模板列表中移除
            del self.available_templates[template_name]
            
            self.logger.info(f"Deleted template: {template_name}")
            
            return {
                "success": True,
                "template_name": template_name
            }
            
        except Exception as e:
            self.logger.error(f"Error deleting template: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_template_content(self, template_name: str) -> Dict[str, Any]:
        """获取模板内容."""
        try:
            if template_name not in self.available_templates:
                return {"success": False, "error": f"Template {template_name} not found"}
            
            template_file = self.available_templates[template_name]
            template_path = self.template_dir / template_file
            
            if not template_path.exists():
                return {"success": False, "error": f"Template file not found: {template_file}"}
            
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "success": True,
                "template_name": template_name,
                "content": content,
                "file_size": len(content),
                "last_modified": datetime.fromtimestamp(template_path.stat().st_mtime).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting template content: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_templates_with_info(self) -> List[Dict[str, Any]]:
        """列出所有模板及其信息."""
        try:
            templates_info = []
            
            for template_name, template_file in self.available_templates.items():
                template_path = self.template_dir / template_file
                
                info = {
                    "name": template_name,
                    "file": template_file,
                    "path": str(template_path),
                    "exists": template_path.exists(),
                    "builtin": template_name in ["standard", "simple", "detailed", "executive"]
                }
                
                if template_path.exists():
                    stat = template_path.stat()
                    info.update({
                        "size": stat.st_size,
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
                
                templates_info.append(info)
            
            return templates_info
            
        except Exception as e:
            self.logger.error(f"Error listing templates: {str(e)}")
            return []
    
    async def render_template_with_jinja2(self, template_name: str, content: Dict[str, Any], 
                                        charts: Dict[str, Any], params: Dict[str, Any]) -> str:
        """使用Jinja2渲染模板（如果可用）."""
        try:
            # 尝试导入Jinja2
            try:
                from jinja2 import Environment, FileSystemLoader, select_autoescape
                jinja2_available = True
            except ImportError:
                jinja2_available = False
            
            if not jinja2_available:
                self.logger.warning("Jinja2 not available, falling back to simple template rendering")
                return await self._render_fallback_template(content, charts, params)
            
            # 验证模板
            validation = await self.validate_template(template_name)
            if not validation["valid"]:
                return await self._render_fallback_template(content, charts, params)
            
            # 设置Jinja2环境
            env = Environment(
                loader=FileSystemLoader(str(self.template_dir)),
                autoescape=select_autoescape(['html', 'xml'])
            )
            
            # 加载模板
            template_file = self.available_templates[template_name]
            template = env.get_template(template_file)
            
            # 准备渲染数据
            render_data = {
                "content": content,
                "charts": charts,
                "params": params,
                "language": params.get("language", "zh"),
                "generation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "template_name": template_name
            }
            
            # 渲染模板
            rendered_html = template.render(**render_data)
            
            self.logger.info(f"Successfully rendered template {template_name} with Jinja2")
            return rendered_html
            
        except Exception as e:
            self.logger.error(f"Error rendering template with Jinja2: {str(e)}")
            return await self._render_fallback_template(content, charts, params)
    
    def _create_default_templates(self):
        """创建默认模板文件."""
        try:
            # 简单模板
            simple_template = '''<!DOCTYPE html>
<html lang="{{ language or 'zh' }}">
<head>
    <meta charset="UTF-8">
    <title>简单专利分析报告</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .section { margin-bottom: 20px; }
        h1 { color: #333; }
        h2 { color: #666; border-bottom: 1px solid #ccc; }
    </style>
</head>
<body>
    <h1>专利分析报告</h1>
    <p>生成时间: {{ generation_time }}</p>
    
    {% if content.summary %}
    <div class="section">
        <h2>摘要</h2>
        <p>{{ content.summary }}</p>
    </div>
    {% endif %}
    
    {% for section_name, section_content in content.sections.items() %}
    <div class="section">
        <h2>{{ section_name.title() }}</h2>
        <div>{{ section_content }}</div>
    </div>
    {% endfor %}
</body>
</html>'''
            
            # 详细模板
            detailed_template = '''{% extends "base.html" %}

{% block title %}详细专利分析报告{% endblock %}

{% block header_title %}详细专利分析报告{% endblock %}

{% block extra_css %}
.detailed-section {
    background: #f9f9f9;
    padding: 20px;
    margin: 20px 0;
    border-radius: 8px;
}
.data-highlight {
    background: #e3f2fd;
    padding: 10px;
    border-left: 4px solid #2196f3;
    margin: 10px 0;
}
{% endblock %}

{% block content %}
<!-- 详细内容实现 -->
{% if content.summary %}
<div class="detailed-section">
    <h2>📋 执行摘要</h2>
    <div class="data-highlight">
        <p>{{ content.summary }}</p>
    </div>
</div>
{% endif %}

<!-- 其他详细章节... -->
{% endblock %}'''
            
            # 执行摘要模板
            executive_template = '''{% extends "base.html" %}

{% block title %}执行摘要报告{% endblock %}

{% block header_title %}执行摘要报告{% endblock %}

{% block content %}
<!-- 执行摘要专用内容 -->
{% if content.summary %}
<div class="section">
    <h2>📋 核心发现</h2>
    <p>{{ content.summary }}</p>
</div>
{% endif %}

<!-- 关键指标 -->
<div class="section">
    <h2>📊 关键指标</h2>
    <!-- 指标内容 -->
</div>
{% endblock %}'''
            
            # 创建模板文件
            templates_to_create = {
                "simple.html": simple_template,
                "detailed.html": detailed_template,
                "executive.html": executive_template
            }
            
            for filename, content in templates_to_create.items():
                template_path = self.template_dir / filename
                if not template_path.exists():
                    with open(template_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    self.logger.info(f"Created default template: {filename}")
            
        except Exception as e:
            self.logger.error(f"Error creating default templates: {str(e)}")
    
    async def get_template_variables(self, template_name: str) -> Dict[str, Any]:
        """获取模板中使用的变量."""
        try:
            template_content_result = await self.get_template_content(template_name)
            if not template_content_result["success"]:
                return {"success": False, "error": template_content_result["error"]}
            
            content = template_content_result["content"]
            
            # 简单的变量提取（基于Jinja2语法）
            import re
            
            # 提取 {{ variable }} 格式的变量
            variable_pattern = r'\{\{\s*([^}]+)\s*\}\}'
            variables = re.findall(variable_pattern, content)
            
            # 提取 {% if variable %} 格式的变量
            if_pattern = r'\{\%\s*if\s+([^%]+)\s*\%\}'
            if_variables = re.findall(if_pattern, content)
            
            # 提取 {% for item in variable %} 格式的变量
            for_pattern = r'\{\%\s*for\s+\w+\s+in\s+([^%]+)\s*\%\}'
            for_variables = re.findall(for_pattern, content)
            
            all_variables = list(set(variables + if_variables + for_variables))
            
            return {
                "success": True,
                "template_name": template_name,
                "variables": all_variables,
                "variable_count": len(all_variables)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting template variables: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }