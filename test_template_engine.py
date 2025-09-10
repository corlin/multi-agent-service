#!/usr/bin/env python3
"""Test script for template engine implementation."""

import sys
sys.path.append('src')

from multi_agent_service.agents.patent.template_engine import PatentTemplateEngine
import asyncio

def test_template_engine():
    """Test the template engine implementation."""
    try:
        # Create template engine
        engine = PatentTemplateEngine()
        
        print("✅ Template engine created successfully")
        
        # Test data
        test_content = {
            "summary": "这是一个测试摘要，展示专利分析系统的报告生成能力。",
            "sections": {
                "trend": "趋势分析显示该技术领域正在快速发展。",
                "competition": "竞争分析表明市场集中度较高。"
            },
            "insights": ["技术发展迅速", "市场竞争激烈"],
            "recommendations": ["加强研发投入", "关注市场动态"]
        }
        
        test_charts = {
            "trend_chart": {
                "type": "line",
                "path": "charts/trend.png"
            }
        }
        
        test_params = {
            "template": "standard",
            "language": "zh",
            "keywords": ["人工智能"]
        }
        
        async def test_render():
            # Test template rendering
            rendered = await engine.render_template(
                template_name="standard",
                content=test_content,
                charts=test_charts,
                params=test_params
            )
            
            print("✅ Template rendered successfully")
            print(f"✅ Rendered content length: {len(rendered)} characters")
            
            # Test available templates
            templates = await engine.get_available_templates()
            print(f"✅ Available templates: {templates}")
            
            # Test template validation
            validation = await engine.validate_template("standard")
            print(f"✅ Template validation: {validation['valid']}")
            
            return rendered
        
        # Run async test
        result = asyncio.run(test_render())
        
        print("✅ All template engine tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_template_engine()
    sys.exit(0 if success else 1)