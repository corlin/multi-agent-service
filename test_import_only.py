#!/usr/bin/env python3
"""Simple import test."""

import sys
sys.path.append('src')

print("Testing imports...")

try:
    from multi_agent_service.agents.patent.chart_generator import ChartGenerator
    print("✅ ChartGenerator imported")
except Exception as e:
    print(f"❌ ChartGenerator import failed: {e}")

try:
    from multi_agent_service.agents.patent.content_generator import ReportContentGenerator
    print("✅ ReportContentGenerator imported")
except Exception as e:
    print(f"❌ ReportContentGenerator import failed: {e}")

try:
    from multi_agent_service.agents.patent.template_engine import PatentTemplateEngine
    print("✅ PatentTemplateEngine imported")
except Exception as e:
    print(f"❌ PatentTemplateEngine import failed: {e}")

try:
    from multi_agent_service.agents.patent.chart_styles import ChartStyleConfig
    print("✅ ChartStyleConfig imported")
except Exception as e:
    print(f"❌ ChartStyleConfig import failed: {e}")

print("All basic imports completed!")