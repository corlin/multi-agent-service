#!/usr/bin/env python3
"""Test script for content generator implementation."""

import sys
sys.path.append('src')

from multi_agent_service.agents.patent.content_generator import ReportContentGenerator, ContentQualityController

def test_content_generator():
    """Test the content generator implementation."""
    try:
        # Create instances
        generator = ReportContentGenerator()
        controller = ContentQualityController()
        
        print("✅ Content generator created successfully")
        print("✅ Quality controller created successfully")
        
        # Test data
        test_analysis_data = {
            'trend_analysis': {
                'yearly_counts': {'2020': 45, '2021': 52, '2022': 68},
                'growth_rates': {'2021': 15.6, '2022': 30.8},
                'trend_direction': 'increasing'
            },
            'competition_analysis': {
                'top_applicants': [('华为技术有限公司', 28), ('腾讯科技', 15)],
                'market_concentration': 0.65
            },
            'metadata': {'total_patents': 107}
        }
        
        test_params = {
            'keywords': ['人工智能'],
            'sections': ['summary', 'trend'],
            'language': 'zh'
        }
        
        print("✅ Test data prepared")
        
        # Test quality validation
        test_content = {
            "summary": "这是一个测试摘要，用于验证内容质量控制功能。本摘要包含了足够的内容来通过基本的质量检查。",
            "sections": {
                "trend": "趋势分析显示该技术领域正在快速发展，专利申请量逐年增加。"
            }
        }
        
        import asyncio
        
        async def test_quality():
            quality_report = await controller.validate_content(test_content)
            print(f"✅ Quality validation completed. Overall quality: {quality_report['overall_quality']:.2f}")
            return quality_report
        
        # Run async test
        quality_result = asyncio.run(test_quality())
        
        print("✅ All tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_content_generator()
    sys.exit(0 if success else 1)