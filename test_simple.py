import sys
sys.path.append('src')

try:
    from multi_agent_service.agents.patent.report_exporter import ReportExporter
    print('✅ ReportExporter imported successfully')
except Exception as e:
    print(f'❌ Import error: {e}')
    import traceback
    traceback.print_exc()