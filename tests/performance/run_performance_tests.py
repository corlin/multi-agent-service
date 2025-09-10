#!/usr/bin/env python3
"""
专利系统性能测试执行脚本

使用uv run执行完整的专利系统性能测试套件，包括：
- 性能基准测试
- 并发压力测试  
- 大数据量处理测试
- Agent负载测试
- 资源监控测试
"""

import asyncio
import sys
import os
import argparse
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.performance.benchmark_runner import BenchmarkRunner, BenchmarkConfig


class PerformanceTestSuite:
    """性能测试套件管理器"""
    
    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or "tests/performance/results"
        self.results_dir = Path(self.output_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建时间戳目录
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.results_dir / f"session_{self.timestamp}"
        self.session_dir.mkdir(exist_ok=True)
        
    async def run_full_performance_suite(self, config_file: str = None, test_filter: List[str] = None) -> Dict[str, Any]:
        """运行完整的性能测试套件"""
        
        print(f"{'='*80}")
        print("专利系统性能测试套件")
        print(f"{'='*80}")
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"结果目录: {self.session_dir}")
        print(f"{'='*80}")
        
        # 加载测试配置
        configs = self._load_test_configs(config_file)
        
        # 应用测试过滤器
        if test_filter:
            configs = [cfg for cfg in configs if cfg.test_name in test_filter]
            print(f"应用测试过滤器，运行 {len(configs)} 个测试")
        
        # 系统信息检查
        await self._check_system_requirements()
        
        # 运行基准测试
        benchmark_runner = BenchmarkRunner(str(self.session_dir))
        benchmark_report = await benchmark_runner.run_all_benchmarks(configs)
        
        # 运行专项性能测试
        specialized_results = await self._run_specialized_tests()
        
        # 生成综合报告
        comprehensive_report = self._generate_comprehensive_report(
            benchmark_report, 
            specialized_results
        )
        
        # 保存最终报告
        await self._save_comprehensive_report(comprehensive_report)
        
        # 输出测试总结
        self._print_test_summary(comprehensive_report)
        
        return comprehensive_report
    
    def _load_test_configs(self, config_file: str = None) -> List[BenchmarkConfig]:
        """加载测试配置"""
        if config_file and Path(config_file).exists():
            config_path = Path(config_file)
        else:
            config_path = Path("tests/performance/config/benchmark_config.json")
        
        if config_path.exists():
            print(f"加载配置文件: {config_path}")
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            return [BenchmarkConfig(**cfg) for cfg in config_data]
        else:
            print("使用默认配置")
            from tests.performance.benchmark_runner import create_default_benchmark_configs
            return create_default_benchmark_configs()
    
    async def _check_system_requirements(self):
        """检查系统要求"""
        import psutil
        
        print("\n系统环境检查:")
        print(f"  CPU核心数: {psutil.cpu_count()}")
        print(f"  内存总量: {psutil.virtual_memory().total / 1024 / 1024 / 1024:.2f} GB")
        print(f"  可用内存: {psutil.virtual_memory().available / 1024 / 1024 / 1024:.2f} GB")
        print(f"  Python版本: {sys.version}")
        print(f"  平台: {sys.platform}")
        
        # 检查最低要求
        if psutil.virtual_memory().available < 2 * 1024 * 1024 * 1024:  # 2GB
            print("⚠️  警告: 可用内存不足2GB，可能影响测试结果")
        
        if psutil.cpu_count() < 2:
            print("⚠️  警告: CPU核心数少于2个，并发测试可能受限")
        
        print("✅ 系统环境检查完成\n")
    
    async def _run_specialized_tests(self) -> Dict[str, Any]:
        """运行专项性能测试"""
        print(f"\n{'='*60}")
        print("运行专项性能测试")
        print(f"{'='*60}")
        
        specialized_results = {}
        
        # 1. 内存泄漏检测测试
        print("\n🔍 运行内存泄漏检测测试...")
        try:
            memory_leak_result = await self._run_memory_leak_test()
            specialized_results['memory_leak_test'] = memory_leak_result
            print("✅ 内存泄漏检测测试完成")
        except Exception as e:
            print(f"❌ 内存泄漏检测测试失败: {e}")
            specialized_results['memory_leak_test'] = {'error': str(e)}
        
        # 2. 性能回归检测测试
        print("\n📊 运行性能回归检测测试...")
        try:
            regression_result = await self._run_regression_test()
            specialized_results['regression_test'] = regression_result
            print("✅ 性能回归检测测试完成")
        except Exception as e:
            print(f"❌ 性能回归检测测试失败: {e}")
            specialized_results['regression_test'] = {'error': str(e)}
        
        # 3. 极限压力测试
        print("\n🚀 运行极限压力测试...")
        try:
            extreme_stress_result = await self._run_extreme_stress_test()
            specialized_results['extreme_stress_test'] = extreme_stress_result
            print("✅ 极限压力测试完成")
        except Exception as e:
            print(f"❌ 极限压力测试失败: {e}")
            specialized_results['extreme_stress_test'] = {'error': str(e)}
        
        return specialized_results
    
    async def _run_memory_leak_test(self) -> Dict[str, Any]:
        """运行内存泄漏检测测试"""
        from unittest.mock import AsyncMock, patch
        import psutil
        import gc
        
        with patch('src.multi_agent_service.patent.agents.coordinator.PatentCoordinatorAgent') as mock_coordinator:
            mock_coordinator.return_value.process_request = AsyncMock(return_value={
                'status': 'success',
                'analysis_id': 'memory-leak-test',
                'results': {'patents_found': 50}
            })
            
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            memory_samples = [initial_memory]
            
            # 执行多轮内存密集型操作
            for cycle in range(8):
                from src.multi_agent_service.patent.agents.coordinator import PatentCoordinatorAgent
                
                # 创建多个Agent实例
                agents = []
                for i in range(15):
                    agent_config = {'agent_id': f'memory-leak-{cycle}-{i}', 'model_config': {}}
                    agent = PatentCoordinatorAgent(agent_config)
                    agents.append(agent)
                
                # 并发执行任务
                tasks = []
                for i, agent in enumerate(agents):
                    request = {
                        'keywords': [f'memory-leak-{cycle}-{i}', 'test'],
                        'limit': 80
                    }
                    tasks.append(agent.process_request(request))
                
                await asyncio.gather(*tasks, return_exceptions=True)
                
                # 清理引用
                del agents
                del tasks
                
                # 强制垃圾回收
                gc.collect()
                
                # 记录内存使用
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_samples.append(current_memory)
                
                # 短暂等待
                await asyncio.sleep(0.5)
            
            # 分析内存使用趋势
            final_memory = memory_samples[-1]
            memory_increase = final_memory - initial_memory
            
            # 计算内存增长趋势
            n = len(memory_samples)
            x_sum = sum(range(n))
            y_sum = sum(memory_samples)
            xy_sum = sum(i * memory_samples[i] for i in range(n))
            x2_sum = sum(i * i for i in range(n))
            
            slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
            
            return {
                'initial_memory_mb': initial_memory,
                'final_memory_mb': final_memory,
                'memory_increase_mb': memory_increase,
                'memory_growth_trend': slope,
                'memory_samples': memory_samples,
                'cycles_tested': len(memory_samples) - 1,
                'leak_detected': memory_increase > 100 or slope > 3.0,
                'max_memory_mb': max(memory_samples),
                'avg_memory_mb': sum(memory_samples) / len(memory_samples)
            }
    
    async def _run_regression_test(self) -> Dict[str, Any]:
        """运行性能回归检测测试"""
        from tests.performance.test_patent_stress import StressTestRunner, StressTestConfig
        from unittest.mock import AsyncMock, patch
        
        with patch('src.multi_agent_service.patent.agents.coordinator.PatentCoordinatorAgent') as mock_coordinator:
            mock_coordinator.return_value.process_request = AsyncMock(return_value={
                'status': 'success',
                'analysis_id': 'regression-test',
                'results': {'patents_found': 75}
            })
            
            # 基准测试配置
            baseline_config = StressTestConfig(
                concurrent_users=8,
                requests_per_user=6,
                ramp_up_time=5,
                test_duration=30,
                max_response_time=8.0,
                min_success_rate=0.9
            )
            
            async def regression_test_function(user_id: int, request_id: int):
                from src.multi_agent_service.patent.agents.coordinator import PatentCoordinatorAgent
                from src.multi_agent_service.patent.models.requests import PatentAnalysisRequest
                
                agent_config = {'agent_id': f'regression-{user_id}', 'model_config': {}}
                coordinator = PatentCoordinatorAgent(agent_config)
                
                request = PatentAnalysisRequest(
                    keywords=[f'regression-{user_id}-{request_id}'],
                    analysis_type='basic',
                    limit=60
                )
                
                return await coordinator.process_request(request.dict())
            
            # 运行基准测试
            baseline_runner = StressTestRunner(baseline_config)
            baseline_result = await baseline_runner.run_stress_test(regression_test_function)
            
            # 运行当前测试
            current_runner = StressTestRunner(baseline_config)
            current_result = await current_runner.run_stress_test(regression_test_function)
            
            # 计算回归指标
            response_time_regression = (
                (current_result.avg_response_time - baseline_result.avg_response_time) 
                / baseline_result.avg_response_time
            ) if baseline_result.avg_response_time > 0 else 0
            
            success_rate_regression = baseline_result.success_rate - current_result.success_rate
            
            throughput_regression = (
                (baseline_result.requests_per_second - current_result.requests_per_second) 
                / baseline_result.requests_per_second
            ) if baseline_result.requests_per_second > 0 else 0
            
            return {
                'baseline_avg_response_time': baseline_result.avg_response_time,
                'current_avg_response_time': current_result.avg_response_time,
                'response_time_regression_pct': response_time_regression * 100,
                'baseline_success_rate': baseline_result.success_rate,
                'current_success_rate': current_result.success_rate,
                'success_rate_regression_pct': success_rate_regression * 100,
                'baseline_throughput': baseline_result.requests_per_second,
                'current_throughput': current_result.requests_per_second,
                'throughput_regression_pct': throughput_regression * 100,
                'regression_detected': (
                    abs(response_time_regression) > 0.15 or 
                    success_rate_regression > 0.05 or 
                    throughput_regression > 0.15
                )
            }
    
    async def _run_extreme_stress_test(self) -> Dict[str, Any]:
        """运行极限压力测试"""
        from tests.performance.test_patent_stress import StressTestRunner, StressTestConfig
        from unittest.mock import AsyncMock, patch
        import random
        
        with patch('src.multi_agent_service.patent.agents.coordinator.PatentCoordinatorAgent') as mock_coordinator:
            # 模拟更真实的处理延迟和偶发错误
            async def extreme_mock_process(*args, **kwargs):
                # 随机延迟
                await asyncio.sleep(random.uniform(0.2, 3.0))
                
                # 随机失败
                if random.random() < 0.08:  # 8%失败率
                    raise Exception("Extreme stress test simulated error")
                
                return {
                    'status': 'success',
                    'analysis_id': f'extreme-{random.randint(1000, 9999)}',
                    'results': {'patents_found': random.randint(30, 150)}
                }
            
            mock_coordinator.return_value.process_request = extreme_mock_process
            
            # 极限压力测试配置
            extreme_config = StressTestConfig(
                concurrent_users=25,  # 高并发
                requests_per_user=8,
                ramp_up_time=15,
                test_duration=90,  # 较长时间
                max_response_time=20.0,
                min_success_rate=0.75  # 降低成功率要求
            )
            
            async def extreme_test_function(user_id: int, request_id: int):
                from src.multi_agent_service.patent.agents.coordinator import PatentCoordinatorAgent
                from src.multi_agent_service.patent.models.requests import PatentAnalysisRequest
                
                agent_config = {'agent_id': f'extreme-{user_id}', 'model_config': {}}
                coordinator = PatentCoordinatorAgent(agent_config)
                
                # 随机复杂度请求
                complexity = random.choice(['basic', 'standard', 'comprehensive'])
                limit = {'basic': 40, 'standard': 80, 'comprehensive': 150}[complexity]
                
                request = PatentAnalysisRequest(
                    keywords=[f'extreme-{complexity}-{user_id}-{request_id}'],
                    analysis_type=complexity,
                    limit=limit
                )
                
                return await coordinator.process_request(request.dict())
            
            # 运行极限压力测试
            extreme_runner = StressTestRunner(extreme_config)
            extreme_result = await extreme_runner.run_stress_test(extreme_test_function)
            
            return {
                'total_requests': extreme_result.total_requests,
                'successful_requests': extreme_result.successful_requests,
                'failed_requests': extreme_result.failed_requests,
                'success_rate': extreme_result.success_rate,
                'avg_response_time': extreme_result.avg_response_time,
                'max_response_time': extreme_result.max_response_time,
                'requests_per_second': extreme_result.requests_per_second,
                'peak_memory_usage': extreme_result.peak_memory_usage,
                'peak_cpu_usage': extreme_result.peak_cpu_usage,
                'test_duration': extreme_result.test_duration,
                'error_count': len(extreme_result.errors),
                'system_survived': extreme_result.success_rate > 0.5 and extreme_result.requests_per_second > 1.0
            }
    
    def _generate_comprehensive_report(self, benchmark_report: Dict[str, Any], specialized_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成综合报告"""
        return {
            'test_session': {
                'timestamp': self.timestamp,
                'session_dir': str(self.session_dir),
                'start_time': benchmark_report['summary']['test_start_time'],
                'end_time': benchmark_report['summary']['test_end_time'],
                'total_duration': benchmark_report['summary']['total_duration']
            },
            'benchmark_results': benchmark_report,
            'specialized_results': specialized_results,
            'overall_assessment': self._assess_overall_performance(benchmark_report, specialized_results),
            'recommendations': self._generate_recommendations(benchmark_report, specialized_results)
        }
    
    def _assess_overall_performance(self, benchmark_report: Dict[str, Any], specialized_results: Dict[str, Any]) -> Dict[str, Any]:
        """评估整体性能"""
        assessment = {
            'overall_grade': 'A',  # A, B, C, D, F
            'performance_score': 0,  # 0-100
            'critical_issues': [],
            'warnings': [],
            'strengths': []
        }
        
        # 基准测试评估
        benchmark_success_rate = benchmark_report['summary']['success_rate']
        if benchmark_success_rate >= 0.95:
            assessment['strengths'].append("基准测试成功率优秀")
            assessment['performance_score'] += 25
        elif benchmark_success_rate >= 0.85:
            assessment['performance_score'] += 20
        elif benchmark_success_rate >= 0.75:
            assessment['warnings'].append("基准测试成功率偏低")
            assessment['performance_score'] += 15
        else:
            assessment['critical_issues'].append("基准测试成功率过低")
            assessment['performance_score'] += 5
        
        # 聚合指标评估
        if 'aggregate_metrics' in benchmark_report:
            metrics = benchmark_report['aggregate_metrics']
            
            # 响应时间评估
            if 'avg_response_time' in metrics:
                avg_rt = metrics['avg_response_time']
                if avg_rt <= 5.0:
                    assessment['strengths'].append("平均响应时间优秀")
                    assessment['performance_score'] += 25
                elif avg_rt <= 10.0:
                    assessment['performance_score'] += 20
                elif avg_rt <= 20.0:
                    assessment['warnings'].append("平均响应时间偏高")
                    assessment['performance_score'] += 15
                else:
                    assessment['critical_issues'].append("平均响应时间过高")
                    assessment['performance_score'] += 5
            
            # 吞吐量评估
            if 'avg_throughput' in metrics:
                throughput = metrics['avg_throughput']
                if throughput >= 5.0:
                    assessment['strengths'].append("系统吞吐量优秀")
                    assessment['performance_score'] += 25
                elif throughput >= 2.0:
                    assessment['performance_score'] += 20
                elif throughput >= 1.0:
                    assessment['warnings'].append("系统吞吐量偏低")
                    assessment['performance_score'] += 15
                else:
                    assessment['critical_issues'].append("系统吞吐量过低")
                    assessment['performance_score'] += 5
        
        # 专项测试评估
        if 'memory_leak_test' in specialized_results:
            memory_result = specialized_results['memory_leak_test']
            if not memory_result.get('error'):
                if not memory_result.get('leak_detected', False):
                    assessment['strengths'].append("未检测到内存泄漏")
                    assessment['performance_score'] += 25
                else:
                    assessment['critical_issues'].append("检测到潜在内存泄漏")
        
        # 确定总体等级
        if assessment['performance_score'] >= 90:
            assessment['overall_grade'] = 'A'
        elif assessment['performance_score'] >= 80:
            assessment['overall_grade'] = 'B'
        elif assessment['performance_score'] >= 70:
            assessment['overall_grade'] = 'C'
        elif assessment['performance_score'] >= 60:
            assessment['overall_grade'] = 'D'
        else:
            assessment['overall_grade'] = 'F'
        
        return assessment
    
    def _generate_recommendations(self, benchmark_report: Dict[str, Any], specialized_results: Dict[str, Any]) -> List[str]:
        """生成性能优化建议"""
        recommendations = []
        
        # 基于基准测试结果的建议
        if benchmark_report['summary']['success_rate'] < 0.9:
            recommendations.append("建议优化错误处理机制，提高系统稳定性")
        
        if 'aggregate_metrics' in benchmark_report:
            metrics = benchmark_report['aggregate_metrics']
            
            if metrics.get('avg_response_time', 0) > 10.0:
                recommendations.append("建议优化Agent处理逻辑，减少响应时间")
                recommendations.append("考虑增加缓存机制以提高响应速度")
            
            if metrics.get('avg_throughput', 0) < 2.0:
                recommendations.append("建议增加并发处理能力，提高系统吞吐量")
                recommendations.append("考虑使用连接池和异步处理优化")
        
        # 基于专项测试结果的建议
        if 'memory_leak_test' in specialized_results:
            memory_result = specialized_results['memory_leak_test']
            if not memory_result.get('error') and memory_result.get('leak_detected'):
                recommendations.append("检测到内存泄漏，建议检查Agent生命周期管理")
                recommendations.append("建议添加定期垃圾回收机制")
        
        if 'extreme_stress_test' in specialized_results:
            extreme_result = specialized_results['extreme_stress_test']
            if not extreme_result.get('error') and not extreme_result.get('system_survived', True):
                recommendations.append("系统在极限压力下表现不佳，建议增强容错能力")
                recommendations.append("考虑实现熔断器和限流机制")
        
        # 通用建议
        recommendations.extend([
            "建议定期运行性能测试以监控系统性能趋势",
            "考虑建立性能监控告警机制",
            "建议在生产环境中部署APM工具进行实时监控"
        ])
        
        return recommendations
    
    async def _save_comprehensive_report(self, report: Dict[str, Any]):
        """保存综合报告"""
        # 保存JSON格式
        json_file = self.session_dir / "comprehensive_performance_report.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        # 保存HTML格式
        html_file = self.session_dir / "comprehensive_performance_report.html"
        html_content = self._generate_html_comprehensive_report(report)
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\n📋 综合性能报告已保存:")
        print(f"   JSON: {json_file}")
        print(f"   HTML: {html_file}")
    
    def _generate_html_comprehensive_report(self, report: Dict[str, Any]) -> str:
        """生成HTML格式的综合报告"""
        assessment = report['overall_assessment']
        
        grade_colors = {
            'A': '#28a745', 'B': '#6f42c1', 'C': '#fd7e14', 'D': '#dc3545', 'F': '#6c757d'
        }
        
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>专利系统综合性能报告</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f8f9fa; }}
        .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 40px; }}
        .grade-badge {{ display: inline-block; padding: 15px 30px; border-radius: 50px; color: white; font-size: 24px; font-weight: bold; margin: 20px 0; }}
        .section {{ margin: 30px 0; padding: 20px; border: 1px solid #dee2e6; border-radius: 8px; }}
        .section h2 {{ color: #495057; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric-card {{ background-color: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #007bff; }}
        .metric-label {{ color: #6c757d; margin-top: 5px; }}
        .issue-list {{ list-style: none; padding: 0; }}
        .issue-item {{ padding: 10px; margin: 5px 0; border-radius: 5px; }}
        .critical {{ background-color: #f8d7da; color: #721c24; }}
        .warning {{ background-color: #fff3cd; color: #856404; }}
        .strength {{ background-color: #d4edda; color: #155724; }}
        .recommendation {{ background-color: #e2e3e5; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007bff; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #dee2e6; padding: 12px; text-align: left; }}
        th {{ background-color: #e9ecef; font-weight: bold; }}
        .success {{ color: #28a745; }}
        .failure {{ color: #dc3545; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>专利系统综合性能测试报告</h1>
            <p>测试时间: {report['test_session']['start_time']} - {report['test_session']['end_time']}</p>
            <div class="grade-badge" style="background-color: {grade_colors.get(assessment['overall_grade'], '#6c757d')}">
                总体评级: {assessment['overall_grade']}
            </div>
            <p>性能得分: {assessment['performance_score']}/100</p>
        </div>
        
        <div class="section">
            <h2>📊 测试概览</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{report['benchmark_results']['summary']['total_tests']}</div>
                    <div class="metric-label">总测试数</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{report['benchmark_results']['summary']['success_rate']:.1%}</div>
                    <div class="metric-label">成功率</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{report['benchmark_results']['summary']['total_duration']:.1f}s</div>
                    <div class="metric-label">总耗时</div>
                </div>
"""
        
        if 'aggregate_metrics' in report['benchmark_results']:
            metrics = report['benchmark_results']['aggregate_metrics']
            if 'avg_response_time' in metrics:
                html += f"""
                <div class="metric-card">
                    <div class="metric-value">{metrics['avg_response_time']:.2f}s</div>
                    <div class="metric-label">平均响应时间</div>
                </div>
"""
            if 'avg_throughput' in metrics:
                html += f"""
                <div class="metric-card">
                    <div class="metric-value">{metrics['avg_throughput']:.2f}</div>
                    <div class="metric-label">平均吞吐量 (RPS)</div>
                </div>
"""
        
        html += """
            </div>
        </div>
        
        <div class="section">
            <h2>🎯 性能评估</h2>
"""
        
        if assessment['critical_issues']:
            html += """
            <h3>🚨 严重问题</h3>
            <ul class="issue-list">
"""
            for issue in assessment['critical_issues']:
                html += f'<li class="issue-item critical">❌ {issue}</li>'
            html += "</ul>"
        
        if assessment['warnings']:
            html += """
            <h3>⚠️ 警告</h3>
            <ul class="issue-list">
"""
            for warning in assessment['warnings']:
                html += f'<li class="issue-item warning">⚠️ {warning}</li>'
            html += "</ul>"
        
        if assessment['strengths']:
            html += """
            <h3>✅ 优势</h3>
            <ul class="issue-list">
"""
            for strength in assessment['strengths']:
                html += f'<li class="issue-item strength">✅ {strength}</li>'
            html += "</ul>"
        
        html += """
        </div>
        
        <div class="section">
            <h2>🔧 优化建议</h2>
"""
        
        for i, recommendation in enumerate(report['recommendations'], 1):
            html += f'<div class="recommendation">{i}. {recommendation}</div>'
        
        html += """
        </div>
        
        <div class="section">
            <h2>📈 基准测试详情</h2>
            <table>
                <thead>
                    <tr>
                        <th>测试名称</th>
                        <th>状态</th>
                        <th>耗时(s)</th>
                        <th>成功率</th>
                        <th>平均响应时间(s)</th>
                    </tr>
                </thead>
                <tbody>
"""
        
        for result in report['benchmark_results']['test_results']:
            status_class = 'success' if result['success'] else 'failure'
            status_text = '✅ 通过' if result['success'] else '❌ 失败'
            
            success_rate = result['metrics'].get('success_rate', 0)
            avg_response_time = result['metrics'].get('avg_response_time', 0)
            
            html += f"""
                    <tr>
                        <td>{result['test_name']}</td>
                        <td class="{status_class}">{status_text}</td>
                        <td>{result['duration']:.2f}</td>
                        <td>{success_rate:.1%}</td>
                        <td>{avg_response_time:.3f}</td>
                    </tr>
"""
        
        html += """
                </tbody>
            </table>
        </div>
"""
        
        # 专项测试结果
        if report['specialized_results']:
            html += """
        <div class="section">
            <h2>🔬 专项测试结果</h2>
"""
            
            for test_name, result in report['specialized_results'].items():
                if 'error' not in result:
                    html += f"<h3>{test_name}</h3>"
                    html += "<div class='metrics-grid'>"
                    
                    # 根据测试类型显示不同指标
                    if test_name == 'memory_leak_test':
                        html += f"""
                        <div class="metric-card">
                            <div class="metric-value">{'❌' if result.get('leak_detected') else '✅'}</div>
                            <div class="metric-label">内存泄漏检测</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{result.get('memory_increase_mb', 0):.2f}MB</div>
                            <div class="metric-label">内存增长</div>
                        </div>
"""
                    elif test_name == 'extreme_stress_test':
                        html += f"""
                        <div class="metric-card">
                            <div class="metric-value">{result.get('success_rate', 0):.1%}</div>
                            <div class="metric-label">极限压力成功率</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{result.get('requests_per_second', 0):.2f}</div>
                            <div class="metric-label">极限压力吞吐量</div>
                        </div>
"""
                    
                    html += "</div>"
        
        html += """
        </div>
        
        <div class="section">
            <h2>ℹ️ 系统信息</h2>
            <div class="metrics-grid">
"""
        
        system_info = report['benchmark_results']['system_info']
        html += f"""
                <div class="metric-card">
                    <div class="metric-value">{system_info['cpu_count']}</div>
                    <div class="metric-label">CPU核心数</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{system_info['memory_total_gb']:.1f}GB</div>
                    <div class="metric-label">内存总量</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{system_info['python_version']}</div>
                    <div class="metric-label">Python版本</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{system_info['platform']}</div>
                    <div class="metric-label">平台</div>
                </div>
"""
        
        html += """
            </div>
        </div>
        
        <div style="text-align: center; margin-top: 40px; color: #6c757d;">
            <p>报告生成时间: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
        </div>
    </div>
</body>
</html>
"""
        return html
    
    def _print_test_summary(self, report: Dict[str, Any]):
        """打印测试总结"""
        assessment = report['overall_assessment']
        
        print(f"\n{'='*80}")
        print("🎯 专利系统性能测试总结")
        print(f"{'='*80}")
        print(f"总体评级: {assessment['overall_grade']}")
        print(f"性能得分: {assessment['performance_score']}/100")
        print(f"测试成功率: {report['benchmark_results']['summary']['success_rate']:.1%}")
        print(f"总测试时间: {report['benchmark_results']['summary']['total_duration']:.1f} 秒")
        
        if 'aggregate_metrics' in report['benchmark_results']:
            metrics = report['benchmark_results']['aggregate_metrics']
            if 'avg_response_time' in metrics:
                print(f"平均响应时间: {metrics['avg_response_time']:.3f} 秒")
            if 'avg_throughput' in metrics:
                print(f"平均吞吐量: {metrics['avg_throughput']:.2f} RPS")
        
        if assessment['critical_issues']:
            print(f"\n🚨 严重问题 ({len(assessment['critical_issues'])}个):")
            for issue in assessment['critical_issues']:
                print(f"   ❌ {issue}")
        
        if assessment['warnings']:
            print(f"\n⚠️  警告 ({len(assessment['warnings'])}个):")
            for warning in assessment['warnings']:
                print(f"   ⚠️  {warning}")
        
        if assessment['strengths']:
            print(f"\n✅ 优势 ({len(assessment['strengths'])}个):")
            for strength in assessment['strengths']:
                print(f"   ✅ {strength}")
        
        print(f"\n📋 详细报告已保存至: {self.session_dir}")
        print(f"{'='*80}")


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="专利系统性能测试套件")
    parser.add_argument("--config", help="测试配置文件路径")
    parser.add_argument("--output", help="结果输出目录")
    parser.add_argument("--tests", nargs="+", help="指定要运行的测试名称")
    parser.add_argument("--quick", action="store_true", help="快速测试模式（减少测试数量）")
    
    args = parser.parse_args()
    
    # 创建测试套件
    suite = PerformanceTestSuite(args.output)
    
    # 如果是快速模式，过滤测试
    test_filter = args.tests
    if args.quick and not test_filter:
        test_filter = [
            "single_agent_baseline",
            "coordinator_agent_baseline", 
            "concurrent_analysis_light",
            "memory_usage_monitoring"
        ]
    
    try:
        # 运行完整测试套件
        report = await suite.run_full_performance_suite(args.config, test_filter)
        
        # 根据结果设置退出码
        if report['overall_assessment']['overall_grade'] in ['A', 'B']:
            sys.exit(0)  # 成功
        elif report['overall_assessment']['overall_grade'] in ['C', 'D']:
            sys.exit(1)  # 警告
        else:
            sys.exit(2)  # 失败
            
    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 测试执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())