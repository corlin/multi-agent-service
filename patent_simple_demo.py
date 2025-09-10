#!/usr/bin/env python3
"""专利系统简化演示程序 - 专注于核心功能展示."""

import sys
import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
import random

sys.path.append('src')

async def main():
    """主演示函数."""
    print("🎯 专利系统核心功能演示")
    print("=" * 60)
    print(f"🕒 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 1. 生成演示数据
        print("\n📊 步骤1: 生成演示数据")
        demo_data = generate_demo_data()
        print(f"✅ 生成了 {len(demo_data['patents'])} 件专利数据")
        print(f"  🏢 涉及 {len(set(p['applicant'] for p in demo_data['patents']))} 个申请人")
        print(f"  🌍 覆盖 {len(set(p['country'] for p in demo_data['patents']))} 个国家")
        print(f"  🔬 包含 {len(set(p['tech_area'] for p in demo_data['patents']))} 个技术领域")
        
        # 2. 执行分析
        print("\n🔬 步骤2: 执行专利分析")
        analysis_result = perform_analysis(demo_data['patents'])
        print("✅ 分析完成")
        print(f"  📈 趋势: {analysis_result['trend']['summary']}")
        print(f"  🏢 竞争: 发现 {len(analysis_result['competition']['top_applicants'])} 个主要竞争者")
        print(f"  🔬 技术: 识别 {len(analysis_result['technology']['main_areas'])} 个主要技术方向")
        
        # 3. 生成报告
        print("\n📄 步骤3: 生成分析报告")
        report_result = await generate_report(analysis_result, demo_data['keywords'])
        print("✅ 报告生成完成")
        if report_result['success']:
            print(f"  📄 HTML报告: {report_result['html_path']}")
            print(f"  📊 JSON数据: {report_result['json_path']}")
            print(f"  📏 报告大小: {report_result['html_size']}")
        
        # 4. 显示详细结果
        print("\n📋 步骤4: 详细分析结果")
        display_detailed_results(analysis_result)
        
        print("\n" + "=" * 60)
        print("🎉 专利系统演示成功完成！")
        print(f"📁 报告文件保存在: {report_result.get('html_path', 'N/A')}")
        print(f"🕒 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def generate_demo_data():
    """生成演示用的专利数据."""
    companies = [
        "华为技术有限公司", "腾讯科技", "阿里巴巴集团", "百度在线", "字节跳动",
        "Apple Inc.", "Google LLC", "Microsoft Corporation", "Samsung Electronics",
        "IBM Corporation", "Intel Corporation", "NVIDIA Corporation"
    ]
    
    tech_areas = ["人工智能", "区块链", "物联网", "5G通信", "新能源", "生物技术", "芯片技术"]
    countries = ["CN", "US", "JP", "KR", "DE", "GB", "FR"]
    
    patents = []
    base_date = datetime.now() - timedelta(days=365*5)
    
    for i in range(150):  # 生成150个专利
        days_offset = random.randint(0, 365*5)
        app_date = base_date + timedelta(days=days_offset)
        
        patent = {
            "id": f"P{i+1:03d}",
            "title": f"{random.choice(tech_areas)}相关技术方案-{i+1}",
            "applicant": random.choice(companies),
            "country": random.choice(countries),
            "tech_area": random.choice(tech_areas),
            "application_date": app_date.strftime("%Y-%m-%d"),
            "year": app_date.year,
            "status": random.choice(["已授权", "审查中", "已公开"])
        }
        patents.append(patent)
    
    return {
        "patents": patents,
        "keywords": ["人工智能", "机器学习", "深度学习", "神经网络"]
    }

def perform_analysis(patents):
    """执行专利分析."""
    # 趋势分析
    yearly_counts = {}
    for patent in patents:
        year = patent['year']
        yearly_counts[year] = yearly_counts.get(year, 0) + 1
    
    years = sorted(yearly_counts.keys())
    if len(years) > 1:
        recent_count = yearly_counts[years[-1]]
        prev_count = yearly_counts[years[-2]] if len(years) > 1 else 0
        growth_rate = ((recent_count - prev_count) / prev_count * 100) if prev_count > 0 else 0
        
        if growth_rate > 10:
            trend_summary = f"快速增长，增长率{growth_rate:.1f}%"
        elif growth_rate > 0:
            trend_summary = f"稳定增长，增长率{growth_rate:.1f}%"
        else:
            trend_summary = f"增长放缓，变化率{growth_rate:.1f}%"
    else:
        trend_summary = "数据不足"
    
    # 竞争分析
    applicant_counts = {}
    for patent in patents:
        applicant = patent['applicant']
        applicant_counts[applicant] = applicant_counts.get(applicant, 0) + 1
    
    top_applicants = sorted(applicant_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # 计算市场集中度
    total_patents = len(patents)
    hhi = sum((count / total_patents) ** 2 for count in applicant_counts.values())
    
    # 技术分析
    tech_counts = {}
    for patent in patents:
        tech = patent['tech_area']
        tech_counts[tech] = tech_counts.get(tech, 0) + 1
    
    main_tech_areas = sorted(tech_counts.items(), key=lambda x: x[1], reverse=True)
    
    # 地域分析
    country_counts = {}
    for patent in patents:
        country = patent['country']
        country_counts[country] = country_counts.get(country, 0) + 1
    
    country_names = {
        "CN": "中国", "US": "美国", "JP": "日本", "KR": "韩国",
        "DE": "德国", "GB": "英国", "FR": "法国"
    }
    
    geographic_dist = {
        country_names.get(code, code): count 
        for code, count in country_counts.items()
    }
    
    return {
        "trend": {
            "yearly_counts": yearly_counts,
            "summary": trend_summary,
            "total_patents": total_patents
        },
        "competition": {
            "top_applicants": top_applicants,
            "market_concentration": hhi,
            "total_applicants": len(applicant_counts)
        },
        "technology": {
            "main_areas": main_tech_areas,
            "diversity": len(tech_counts)
        },
        "geographic": {
            "distribution": geographic_dist,
            "total_countries": len(country_counts)
        }
    }

async def generate_report(analysis_result, keywords):
    """生成分析报告."""
    try:
        # 确保输出目录存在
        output_dir = Path("reports/patent/reports")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成报告内容
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # HTML报告
        html_content = generate_html_report(analysis_result, keywords)
        html_path = output_dir / f"patent_demo_report_{timestamp}.html"
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # JSON数据
        json_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "keywords": keywords,
                "report_type": "demo"
            },
            "analysis_results": analysis_result
        }
        
        json_path = output_dir / f"patent_demo_data_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        # 获取文件大小
        html_size = f"{html_path.stat().st_size / 1024:.1f}KB"
        json_size = f"{json_path.stat().st_size / 1024:.1f}KB"
        
        return {
            "success": True,
            "html_path": str(html_path),
            "json_path": str(json_path),
            "html_size": html_size,
            "json_size": json_size
        }
        
    except Exception as e:
        print(f"报告生成错误: {str(e)}")
        return {"success": False, "error": str(e)}

def generate_html_report(analysis_result, keywords):
    """生成HTML报告内容."""
    trend = analysis_result['trend']
    competition = analysis_result['competition']
    technology = analysis_result['technology']
    geographic = analysis_result['geographic']
    
    html = f"""<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>专利分析报告 - 演示版</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #007acc;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #007acc;
            margin: 0;
            font-size: 2.5em;
        }}
        .section {{
            margin-bottom: 40px;
        }}
        .section h2 {{
            color: #333;
            border-left: 4px solid #007acc;
            padding-left: 15px;
            margin-bottom: 20px;
        }}
        .metric {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }}
        .metric-value {{
            font-size: 1.5em;
            font-weight: bold;
            color: #007acc;
        }}
        .list-item {{
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 专利分析报告</h1>
            <p>关键词: {', '.join(keywords)}</p>
            <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="section">
            <h2>📊 总体概况</h2>
            <div class="metric">
                <div>总专利数量</div>
                <div class="metric-value">{trend['total_patents']} 件</div>
            </div>
            <div class="metric">
                <div>主要申请人数量</div>
                <div class="metric-value">{competition['total_applicants']} 个</div>
            </div>
            <div class="metric">
                <div>技术领域数量</div>
                <div class="metric-value">{technology['diversity']} 个</div>
            </div>
            <div class="metric">
                <div>覆盖国家/地区</div>
                <div class="metric-value">{geographic['total_countries']} 个</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📈 趋势分析</h2>
            <p><strong>发展趋势:</strong> {trend['summary']}</p>
            <h3>年度申请量分布:</h3>
            <div>
"""
    
    # 添加年度数据
    for year, count in sorted(trend['yearly_counts'].items()):
        html += f'                <div class="list-item">{year}年: {count} 件</div>\n'
    
    html += f"""            </div>
        </div>
        
        <div class="section">
            <h2>🏢 竞争分析</h2>
            <p><strong>市场集中度 (HHI):</strong> {competition['market_concentration']:.3f}</p>
            <h3>主要申请人排名:</h3>
            <div>
"""
    
    # 添加申请人排名
    for i, (applicant, count) in enumerate(competition['top_applicants'][:10], 1):
        percentage = (count / trend['total_patents']) * 100
        html += f'                <div class="list-item">{i}. {applicant}: {count} 件 ({percentage:.1f}%)</div>\n'
    
    html += f"""            </div>
        </div>
        
        <div class="section">
            <h2>🔬 技术分析</h2>
            <h3>主要技术领域分布:</h3>
            <div>
"""
    
    # 添加技术领域
    for tech_area, count in technology['main_areas']:
        percentage = (count / trend['total_patents']) * 100
        html += f'                <div class="list-item">{tech_area}: {count} 件 ({percentage:.1f}%)</div>\n'
    
    html += f"""            </div>
        </div>
        
        <div class="section">
            <h2>🌍 地域分析</h2>
            <h3>国家/地区分布:</h3>
            <div>
"""
    
    # 添加地域分布
    for country, count in sorted(geographic['distribution'].items(), key=lambda x: x[1], reverse=True):
        percentage = (count / trend['total_patents']) * 100
        html += f'                <div class="list-item">{country}: {count} 件 ({percentage:.1f}%)</div>\n'
    
    html += f"""            </div>
        </div>
        
        <div class="section">
            <h2>💡 分析结论</h2>
            <div class="metric">
                <h3>关键发现:</h3>
                <ul>
                    <li>专利申请{trend['summary']}</li>
                    <li>市场竞争格局{'相对集中' if competition['market_concentration'] > 0.15 else '较为分散'}</li>
                    <li>技术发展呈现{'多元化' if technology['diversity'] > 5 else '集中化'}特征</li>
                    <li>地域分布覆盖{geographic['total_countries']}个国家/地区</li>
                </ul>
            </div>
            <div class="metric">
                <h3>发展建议:</h3>
                <ul>
                    <li>关注主要技术领域的发展动态</li>
                    <li>分析主要竞争对手的专利布局策略</li>
                    <li>考虑在技术活跃地区加强专利申请</li>
                    <li>持续监控行业技术发展趋势</li>
                </ul>
            </div>
        </div>
        
        <div class="footer">
            <p>📄 本报告由专利分析系统自动生成</p>
            <p>🕒 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>"""
    
    return html

def display_detailed_results(analysis_result):
    """显示详细分析结果."""
    print("📊 详细分析结果:")
    print()
    
    # 趋势分析结果
    trend = analysis_result['trend']
    print("📈 趋势分析:")
    print(f"  • 总专利数: {trend['total_patents']} 件")
    print(f"  • 发展趋势: {trend['summary']}")
    print("  • 年度分布:")
    for year, count in sorted(trend['yearly_counts'].items()):
        print(f"    - {year}年: {count} 件")
    
    # 竞争分析结果
    competition = analysis_result['competition']
    print(f"\n🏢 竞争分析:")
    print(f"  • 申请人总数: {competition['total_applicants']} 个")
    print(f"  • 市场集中度: {competition['market_concentration']:.3f}")
    print("  • 前5名申请人:")
    for i, (applicant, count) in enumerate(competition['top_applicants'][:5], 1):
        print(f"    {i}. {applicant}: {count} 件")
    
    # 技术分析结果
    technology = analysis_result['technology']
    print(f"\n🔬 技术分析:")
    print(f"  • 技术领域数: {technology['diversity']} 个")
    print("  • 主要技术领域:")
    for tech, count in technology['main_areas'][:5]:
        print(f"    - {tech}: {count} 件")
    
    # 地域分析结果
    geographic = analysis_result['geographic']
    print(f"\n🌍 地域分析:")
    print(f"  • 覆盖国家数: {geographic['total_countries']} 个")
    print("  • 主要国家/地区:")
    for country, count in sorted(geographic['distribution'].items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"    - {country}: {count} 件")

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)