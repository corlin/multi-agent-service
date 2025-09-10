#!/usr/bin/env python3
"""Test script for PatentReportAgent components."""

import sys
import os
sys.path.append('src')

async def test_patent_report_components():
    """Test all PatentReportAgent components."""
    try:
        print("🧪 Testing PatentReportAgent components...")
        
        # Test imports
        from multi_agent_service.agents.patent.chart_generator import ChartGenerator
        from multi_agent_service.agents.patent.content_generator import ReportContentGenerator
        from multi_agent_service.agents.patent.report_exporter import ReportExporter
        from multi_agent_service.agents.patent.template_engine import PatentTemplateEngine
        from multi_agent_service.agents.patent.chart_styles import ChartStyleConfig, ChartTemplates
        
        print("✅ All imports successful")
        
        # Test ChartGenerator
        print("\n📊 Testing ChartGenerator...")
        chart_gen = ChartGenerator()
        supported_types = chart_gen.get_supported_chart_types()
        cache_info = chart_gen.get_cache_info()
        print(f"  - Supported chart types: {supported_types}")
        print(f"  - Cache info: {cache_info}")
        
        # Test ChartStyleConfig
        print("\n🎨 Testing ChartStyleConfig...")
        default_style = ChartStyleConfig.get_style_config("default")
        professional_style = ChartStyleConfig.get_style_config("professional")
        print(f"  - Default style colors: {len(default_style['colors'])} colors")
        print(f"  - Professional style DPI: {professional_style['dpi']}")
        
        # Test ChartTemplates
        trend_template = ChartTemplates.get_trend_chart_template()
        competition_template = ChartTemplates.get_competition_chart_template()
        print(f"  - Trend template type: {trend_template['type']}")
        print(f"  - Competition template type: {competition_template['type']}")
        
        # Test ReportContentGenerator
        print("\n📝 Testing ReportContentGenerator...")
        content_gen = ReportContentGenerator()
        print("  - ReportContentGenerator initialized successfully")
        
        # Test ReportExporter
        print("\n📤 Testing ReportExporter...")
        exporter = ReportExporter()
        export_info = await exporter.get_export_info()
        print(f"  - Supported formats: {exporter.export_config['supported_formats']}")
        print(f"  - Output directory: {exporter.export_config['output_dir']}")
        
        # Test PatentTemplateEngine
        print("\n📄 Testing PatentTemplateEngine...")
        template_engine = PatentTemplateEngine()
        available_templates = await template_engine.get_available_templates()
        print(f"  - Available templates: {available_templates}")
        
        # Test template validation
        validation_result = await template_engine.validate_template("standard")
        print(f"  - Standard template validation: {validation_result}")
        
        print("\n🎉 All PatentReportAgent components are working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import asyncio
    
    async def main():
        success = await test_patent_report_components()
        if success:
            print("\n✅ All tests passed!")
        else:
            print("\n❌ Some tests failed!")
            sys.exit(1)
    
    # Run the test
    asyncio.run(main())