#!/usr/bin/env python3
"""生成详细版专利报告的测试脚本."""

import sys
import asyncio
import json
from datetime import datetime
from pathlib import Path

sys.path.append('src')

async def generate_detailed_patent_report():
    """生成详细版专利报告."""
    try:
        print("🚀 开始生成详细版专利报告...")
        
        # 导入必要的组件
        from multi_agent_service.agents.patent.report_agent import PatentReportAgent
        from multi_agent_service.models.config import AgentConfig, ModelConfig
        from multi_agent_service.models.base import UserRequest
        from multi_agent_service.models.enums import AgentType, ModelProvider
        
        # 创建模拟的模型客户端
        class MockModelClient:
            async def generate_response(self, prompt: str) -> str:
                return "这是一个模拟的AI响应，用于演示报告生成功能。"
        
        # 创建模拟的模型配置
        llm_config = ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="gpt-3.5-turbo",
            api_key="mock_api_key",
            max_tokens=2000,
            temperature=0.7
        )
        
        # 配置Agent
        config = AgentConfig(
            agent_id="patent_report_agent_test",
            agent_type=AgentType.PATENT_REPORT,
            name="专利报告生成Agent",
            description="用于生成专利分析报告的智能Agent",
            llm_config=llm_config,
            prompt_template="你是一个专业的专利分析师，请根据以下信息生成专利分析报告：{content}"
        )
        
        model_client = MockModelClient()
        
        # 创建PatentReportAgent实例
        print("📊 初始化PatentReportAgent...")
        report_agent = PatentReportAgent(config, model_client)
        
        # 准备报告参数
        report_params = {
            "format": "html",
            "template": "detailed",
            "include_charts": True,
            "include_raw_data": False,
            "language": "zh",
            "sections": ["summary", "trend", "competition", "technology", "geographic"],
            "chart_types": ["line", "pie", "bar"],
            "keywords": ["人工智能", "机器学习", "深度学习"]
        }
        
        print("📈 生成分析数据...")
        # 获取模拟分析数据
        analysis_data = await report_agent._get_analysis_data_for_report(report_params)
        
        if not analysis_data:
            print("❌ 无法获取分析数据")
            return False
        
        print("🎨 初始化报告组件...")
        # 初始化组件
        await report_agent._initialize_components()
        
        print("📊 生成图表...")
        # 生成图表
        charts = await report_agent._chart_generator.generate_charts(analysis_data, report_params)
        print(f"  - 生成了 {len(charts)} 个图表")
        
        print("📝 生成报告内容...")
        # 生成内容
        content = await report_agent._content_generator.generate_content(analysis_data, report_params)
        print(f"  - 生成了 {len(content.get('sections', {}))} 个分析章节")
        
        print("🎯 渲染详细模板...")
        # 渲染模板
        try:
            rendered_content = await report_agent._template_engine.render_template_with_jinja2(
                template_name="detailed",
                content=content,
                charts=charts,
                params=report_params
            )
        except Exception as e:
            print(f"⚠️ Jinja2渲染失败，使用后备模板: {str(e)}")
            rendered_content = await report_agent._template_engine.render_template(
                template_name="detailed",
                content=content,
                charts=charts,
                params=report_params
            )
        
        print("💾 导出报告文件...")
        # 导出报告
        export_result = await report_agent._report_exporter.export_report(
            content=rendered_content,
            format="html",
            params=report_params
        )
        
        # 显示结果
        print("\n🎉 详细版专利报告生成完成！")
        print("=" * 60)
        
        if "html" in export_result:
            html_info = export_result["html"]
            print(f"📄 HTML报告:")
            print(f"  - 文件路径: {html_info['path']}")
            print(f"  - 文件大小: {html_info['size']}")
            print(f"  - 生成时间: {html_info['created_at']}")
            print(f"  - 版本信息: v{html_info['version_info']['version_number']}")
        
        print(f"\n📊 报告统计:")
        print(f"  - 图表数量: {len(charts)}")
        print(f"  - 分析章节: {len(content.get('sections', {}))}")
        print(f"  - 内容字数: {content.get('metadata', {}).get('word_count', 'N/A')}")
        print(f"  - 质量评分: {content.get('metadata', {}).get('quality_score', 'N/A')}")
        
        print(f"\n📈 生成的图表:")
        for chart_name, chart_info in charts.items():
            print(f"  - {chart_name}: {chart_info.get('type', 'unknown')}图表")
            if 'path' in chart_info:
                print(f"    路径: {chart_info['path']}")
        
        print(f"\n📋 报告章节:")
        for section_name in content.get('sections', {}).keys():
            print(f"  - {section_name}分析")
        
        # 生成额外格式
        print(f"\n📦 生成其他格式...")
        
        # JSON格式
        json_result = await report_agent._report_exporter.export_report(
            content=rendered_content,
            format="json",
            params=report_params
        )
        
        if "json" in json_result:
            json_info = json_result["json"]
            print(f"📄 JSON报告: {json_info['path']} ({json_info['size']})")
        
        print("\n✅ 详细版专利报告生成任务完成！")
        print("🔍 您可以查看生成的文件来验证报告内容。")
        
        return True
        
    except Exception as e:
        print(f"❌ 生成报告时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_report_agent_capabilities():
    """测试报告Agent的各种能力."""
    try:
        print("\n🧪 测试PatentReportAgent的高级功能...")
        
        from multi_agent_service.agents.patent.report_agent import PatentReportAgent
        from multi_agent_service.models.config import AgentConfig, ModelConfig
        from multi_agent_service.models.enums import AgentType, ModelProvider
        
        class MockModelClient:
            async def generate_response(self, prompt: str) -> str:
                return "模拟AI响应"
        
        llm_config = ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="gpt-3.5-turbo",
            api_key="mock_api_key"
        )
        
        config = AgentConfig(
            agent_id="test_agent",
            agent_type=AgentType.PATENT_REPORT,
            name="测试Agent",
            description="测试用的专利报告Agent",
            llm_config=llm_config,
            prompt_template="测试提示词模板"
        )
        
        agent = PatentReportAgent(config, MockModelClient())
        
        # 测试能力列表
        capabilities = await agent.get_capabilities()
        print(f"📋 Agent能力: {len(capabilities)}项")
        for i, capability in enumerate(capabilities[:5], 1):
            print(f"  {i}. {capability}")
        if len(capabilities) > 5:
            print(f"  ... 还有{len(capabilities) - 5}项能力")
        
        # 测试模板管理
        templates = await agent.get_report_templates()
        print(f"\n📄 可用模板: {len(templates)}个")
        for template in templates:
            print(f"  - {template['name']}: {template.get('file', 'N/A')}")
        
        # 测试报告统计
        stats = await agent.get_report_statistics()
        print(f"\n📊 报告统计信息:")
        if 'agent_info' in stats:
            agent_info = stats['agent_info']
            print(f"  - Agent ID: {agent_info.get('agent_id', 'N/A')}")
            print(f"  - Agent类型: {agent_info.get('agent_type', 'N/A')}")
            print(f"  - 能力数量: {agent_info.get('capabilities_count', 'N/A')}")
        
        print("\n✅ 高级功能测试完成！")
        
    except Exception as e:
        print(f"❌ 测试高级功能时发生错误: {str(e)}")

if __name__ == "__main__":
    async def main():
        print("🎯 专利报告生成系统演示")
        print("=" * 60)
        
        # 生成详细报告
        success = await generate_detailed_patent_report()
        
        if success:
            # 测试高级功能
            await test_report_agent_capabilities()
            
            print("\n🎉 所有测试完成！")
            print("📁 请查看 reports/patent/reports/ 目录下的生成文件")
        else:
            print("\n❌ 报告生成失败")
            sys.exit(1)
    
    asyncio.run(main())