"""
专利系统性能基准测试运行器

提供统一的性能测试执行、结果收集和报告生成功能。
"""

import asyncio
import json
import time
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
import psutil
import argparse
import sys
from dataclasses import dataclass, asdict

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from tests.performance.test_patent_performance import PerformanceMonitor, PerformanceMetrics
from tests.performance.test_patent_stress import StressTestRunner, StressTestConfig


@dataclass
class BenchmarkConfig:
    """基准测试配置"""
    test_name: str
    description: str
    enabled: bool = True
    timeout: int = 300  # 秒
    retry_count: int = 3
    warm_up_requests: int = 5
    benchmark_requests: int = 50
    concurrent_users: int = 10
    target_response_time: float = 5.0  # 秒
    target_success_rate: float = 0.95
    target_throughput: float = 10.0  # RPS


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    config: BenchmarkConfig
    start_time: datetime
    end_time: datetime
    duration: float
    success: bool
    metrics: Dict[str, Any]
    error_message: str = ""


class BenchmarkRunner:
    """基准测试运行器"""
    
    def __init__(self, output_dir: str = "tests/performance/results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[BenchmarkResult] = []
        
    async def run_all_benchmarks(self, configs: List[BenchmarkConfig]) -> Dict[str, Any]:
        """运行所有基准测试"""
        print(f"开始运行 {len(configs)} 个基准测试...")
        
        overall_start = datetime.now()
        
        for config in configs:
            if not config.enabled:
                print(f"跳过测试: {config.test_name} (已禁用)")
                continue
                
            print(f"\n{'='*60}")
            print(f"运行基准测试: {config.test_name}")
            print(f"描述: {config.description}")
            print(f"{'='*60}")
            
            result = await self._run_single_benchmark(config)
            self.results.append(result)
            
            if result.success:
                print(f"✅ {config.test_name} 测试通过")
            else:
                print(f"❌ {config.test_name} 测试失败: {result.error_message}")
        
        overall_end = datetime.now()
        
        # 生成综合报告
        report = self._generate_comprehensive_report(overall_start, overall_end)
        
        # 保存报告
        await self._save_report(report)
        
        return report
    
    async def _run_single_benchmark(self, config: BenchmarkConfig) -> BenchmarkResult:
        """运行单个基准测试"""
        start_time = datetime.now()
        
        try:
            # 根据测试类型选择执行方法
            if "stress" in config.test_name.lower():
                metrics = await self._run_stress_benchmark(config)
            elif "load" in config.test_name.lower():
                metrics = await self._run_load_benchmark(config)
            elif "memory" in config.test_name.lower():
                metrics = await self._run_memory_benchmark(config)
            else:
                metrics = await self._run_standard_benchmark(config)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # 验证性能指标
            success = self._validate_performance(config, metrics)
            
            return BenchmarkResult(
                config=config,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                success=success,
                metrics=metrics
            )
            
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            return BenchmarkResult(
                config=config,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                success=False,
                metrics={},
                error_message=str(e)
            )
    
    async def _run_standard_benchmark(self, config: BenchmarkConfig) -> Dict[str, Any]:
        """运行标准性能基准测试"""
        from unittest.mock import AsyncMock, patch
        
        # 模拟Agent
        with patch('src.multi_agent_service.patent.agents.coordinator.PatentCoordinatorAgent') as mock_coordinator:
            mock_coordinator.return_value.process_request = AsyncMock(return_value={
                'status': 'success',
                'analysis_id': 'benchmark-test',
                'results': {'patents_found': 100}
            })
            
            monitor = PerformanceMonitor()
            
            # 预热
            print(f"预热阶段: {config.warm_up_requests} 个请求")
            await self._run_warm_up(config, monitor)
            
            # 基准测试
            print(f"基准测试阶段: {config.benchmark_requests} 个请求")
            benchmark_metrics = await self._run_benchmark_requests(config, monitor)
            
            return benchmark_metrics
    
    async def _run_stress_benchmark(self, config: BenchmarkConfig) -> Dict[str, Any]:
        """运行压力测试基准"""
        from unittest.mock import AsyncMock, patch
        
        with patch('src.multi_agent_service.patent.agents.coordinator.PatentCoordinatorAgent') as mock_coordinator:
            mock_coordinator.return_value.process_request = AsyncMock(return_value={
                'status': 'success',
                'analysis_id': 'stress-test',
                'results': {'patents_found': 100}
            })
            
            stress_config = StressTestConfig(
                concurrent_users=config.concurrent_users,
                requests_per_user=config.benchmark_requests // config.concurrent_users,
                ramp_up_time=10,
                test_duration=60,
                max_response_time=config.target_response_time,
                min_success_rate=config.target_success_rate
            )
            
            async def stress_test_function(user_id: int, request_id: int):
                from src.multi_agent_service.patent.agents.coordinator import PatentCoordinatorAgent
                from src.multi_agent_service.patent.models.requests import PatentAnalysisRequest
                
                agent_config = {'agent_id': f'benchmark-{user_id}', 'model_config': {}}
                coordinator = PatentCoordinatorAgent(agent_config)
                
                request = PatentAnalysisRequest(
                    keywords=[f'benchmark-{user_id}-{request_id}'],
                    analysis_type='basic',
                    limit=50
                )
                
                return await coordinator.process_request(request.dict())
            
            runner = StressTestRunner(stress_config)
            result = await runner.run_stress_test(stress_test_function)
            
            return {
                'total_requests': result.total_requests,
                'successful_requests': result.successful_requests,
                'success_rate': result.success_rate,
                'avg_response_time': result.avg_response_time,
                'max_response_time': result.max_response_time,
                'requests_per_second': result.requests_per_second,
                'peak_memory_usage': result.peak_memory_usage,
                'peak_cpu_usage': result.peak_cpu_usage,
                'test_duration': result.test_duration
            }
    
    async def _run_load_benchmark(self, config: BenchmarkConfig) -> Dict[str, Any]:
        """运行负载测试基准"""
        # 实现负载测试逻辑
        return await self._run_standard_benchmark(config)
    
    async def _run_memory_benchmark(self, config: BenchmarkConfig) -> Dict[str, Any]:
        """运行内存测试基准"""
        from unittest.mock import AsyncMock, patch
        
        with patch('src.multi_agent_service.patent.agents.coordinator.PatentCoordinatorAgent') as mock_coordinator:
            mock_coordinator.return_value.process_request = AsyncMock(return_value={
                'status': 'success',
                'analysis_id': 'memory-test',
                'results': {'patents_found': 100}
            })
            
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            memory_samples = [initial_memory]
            
            # 执行内存密集型操作
            for cycle in range(5):
                from src.multi_agent_service.patent.agents.coordinator import PatentCoordinatorAgent
                
                agents = []
                for i in range(10):
                    agent_config = {'agent_id': f'memory-test-{cycle}-{i}', 'model_config': {}}
                    agent = PatentCoordinatorAgent(agent_config)
                    agents.append(agent)
                
                # 并发执行
                tasks = []
                for i, agent in enumerate(agents):
                    request = {'keywords': [f'memory-{cycle}-{i}'], 'limit': 100}
                    tasks.append(agent.process_request(request))
                
                await asyncio.gather(*tasks, return_exceptions=True)
                
                # 清理
                del agents
                del tasks
                import gc
                gc.collect()
                
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_samples.append(current_memory)
                
                await asyncio.sleep(1)
            
            final_memory = memory_samples[-1]
            memory_increase = final_memory - initial_memory
            
            return {
                'initial_memory': initial_memory,
                'final_memory': final_memory,
                'memory_increase': memory_increase,
                'memory_samples': memory_samples,
                'max_memory': max(memory_samples),
                'avg_memory': statistics.mean(memory_samples)
            }
    
    async def _run_warm_up(self, config: BenchmarkConfig, monitor: PerformanceMonitor):
        """预热阶段"""
        from unittest.mock import AsyncMock
        from src.multi_agent_service.patent.agents.coordinator import PatentCoordinatorAgent
        
        agent_config = {'agent_id': 'warmup', 'model_config': {}}
        
        for i in range(config.warm_up_requests):
            coordinator = PatentCoordinatorAgent(agent_config)
            request = {'keywords': [f'warmup-{i}'], 'limit': 10}
            
            start_state = monitor.start_monitoring()
            try:
                await coordinator.process_request(request)
                success = True
            except Exception:
                success = False
            
            monitor.end_monitoring(start_state, f'warmup_{i}', success)
    
    async def _run_benchmark_requests(self, config: BenchmarkConfig, monitor: PerformanceMonitor) -> Dict[str, Any]:
        """执行基准测试请求"""
        from src.multi_agent_service.patent.agents.coordinator import PatentCoordinatorAgent
        
        agent_config = {'agent_id': 'benchmark', 'model_config': {}}
        
        # 并发执行基准请求
        semaphore = asyncio.Semaphore(config.concurrent_users)
        
        async def single_request(request_id: int):
            async with semaphore:
                coordinator = PatentCoordinatorAgent(agent_config)
                request = {'keywords': [f'benchmark-{request_id}'], 'limit': 50}
                
                start_state = monitor.start_monitoring()
                try:
                    result = await coordinator.process_request(request)
                    success = result.get('status') == 'success'
                except Exception:
                    success = False
                
                return monitor.end_monitoring(start_state, f'benchmark_{request_id}', success)
        
        # 执行所有请求
        tasks = [single_request(i) for i in range(config.benchmark_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 计算统计信息
        successful_results = [r for r in results if isinstance(r, PerformanceMetrics) and r.success]
        
        if successful_results:
            response_times = [r.duration for r in successful_results]
            memory_usages = [r.memory_usage for r in successful_results]
            
            return {
                'total_requests': len(results),
                'successful_requests': len(successful_results),
                'success_rate': len(successful_results) / len(results),
                'avg_response_time': statistics.mean(response_times),
                'median_response_time': statistics.median(response_times),
                'min_response_time': min(response_times),
                'max_response_time': max(response_times),
                'p95_response_time': self._percentile(response_times, 95),
                'p99_response_time': self._percentile(response_times, 99),
                'avg_memory_usage': statistics.mean(memory_usages),
                'max_memory_usage': max(memory_usages),
                'requests_per_second': len(successful_results) / max(response_times) if response_times else 0
            }
        else:
            return {
                'total_requests': len(results),
                'successful_requests': 0,
                'success_rate': 0,
                'error': 'No successful requests'
            }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """计算百分位数"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def _validate_performance(self, config: BenchmarkConfig, metrics: Dict[str, Any]) -> bool:
        """验证性能指标是否达标"""
        try:
            # 检查成功率
            if metrics.get('success_rate', 0) < config.target_success_rate:
                return False
            
            # 检查响应时间
            if metrics.get('avg_response_time', float('inf')) > config.target_response_time:
                return False
            
            # 检查吞吐量（如果有的话）
            if 'requests_per_second' in metrics:
                if metrics['requests_per_second'] < config.target_throughput:
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _generate_comprehensive_report(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """生成综合报告"""
        total_duration = (end_time - start_time).total_seconds()
        
        successful_tests = [r for r in self.results if r.success]
        failed_tests = [r for r in self.results if not r.success]
        
        report = {
            'summary': {
                'test_start_time': start_time.isoformat(),
                'test_end_time': end_time.isoformat(),
                'total_duration': total_duration,
                'total_tests': len(self.results),
                'successful_tests': len(successful_tests),
                'failed_tests': len(failed_tests),
                'success_rate': len(successful_tests) / len(self.results) if self.results else 0
            },
            'system_info': {
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': psutil.virtual_memory().total / 1024 / 1024 / 1024,
                'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                'platform': sys.platform
            },
            'test_results': []
        }
        
        # 添加每个测试的详细结果
        for result in self.results:
            test_result = {
                'test_name': result.config.test_name,
                'description': result.config.description,
                'success': result.success,
                'duration': result.duration,
                'start_time': result.start_time.isoformat(),
                'end_time': result.end_time.isoformat(),
                'metrics': result.metrics,
                'error_message': result.error_message
            }
            report['test_results'].append(test_result)
        
        # 计算聚合指标
        if successful_tests:
            all_response_times = []
            all_success_rates = []
            all_throughputs = []
            
            for result in successful_tests:
                metrics = result.metrics
                if 'avg_response_time' in metrics:
                    all_response_times.append(metrics['avg_response_time'])
                if 'success_rate' in metrics:
                    all_success_rates.append(metrics['success_rate'])
                if 'requests_per_second' in metrics:
                    all_throughputs.append(metrics['requests_per_second'])
            
            if all_response_times:
                report['aggregate_metrics'] = {
                    'avg_response_time': statistics.mean(all_response_times),
                    'median_response_time': statistics.median(all_response_times),
                    'max_response_time': max(all_response_times),
                    'min_response_time': min(all_response_times)
                }
            
            if all_success_rates:
                report['aggregate_metrics']['avg_success_rate'] = statistics.mean(all_success_rates)
            
            if all_throughputs:
                report['aggregate_metrics']['avg_throughput'] = statistics.mean(all_throughputs)
                report['aggregate_metrics']['max_throughput'] = max(all_throughputs)
        
        return report
    
    async def _save_report(self, report: Dict[str, Any]):
        """保存测试报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存JSON报告
        json_file = self.output_dir / f"benchmark_report_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 保存HTML报告
        html_file = self.output_dir / f"benchmark_report_{timestamp}.html"
        html_content = self._generate_html_report(report)
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\n📊 测试报告已保存:")
        print(f"   JSON: {json_file}")
        print(f"   HTML: {html_file}")
    
    def _generate_html_report(self, report: Dict[str, Any]) -> str:
        """生成HTML格式的报告"""
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>专利系统性能基准测试报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ margin: 20px 0; }}
        .test-result {{ margin: 10px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .success {{ background-color: #d4edda; }}
        .failure {{ background-color: #f8d7da; }}
        .metrics {{ margin: 10px 0; }}
        .metric {{ display: inline-block; margin: 5px 10px; padding: 5px; background-color: #e9ecef; border-radius: 3px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>专利系统性能基准测试报告</h1>
        <p>生成时间: {report['summary']['test_start_time']}</p>
        <p>测试持续时间: {report['summary']['total_duration']:.2f} 秒</p>
    </div>
    
    <div class="summary">
        <h2>测试概要</h2>
        <div class="metrics">
            <span class="metric">总测试数: {report['summary']['total_tests']}</span>
            <span class="metric">成功测试: {report['summary']['successful_tests']}</span>
            <span class="metric">失败测试: {report['summary']['failed_tests']}</span>
            <span class="metric">成功率: {report['summary']['success_rate']:.2%}</span>
        </div>
    </div>
    
    <div class="system-info">
        <h2>系统信息</h2>
        <div class="metrics">
            <span class="metric">CPU核心数: {report['system_info']['cpu_count']}</span>
            <span class="metric">内存总量: {report['system_info']['memory_total_gb']:.2f} GB</span>
            <span class="metric">Python版本: {report['system_info']['python_version']}</span>
            <span class="metric">平台: {report['system_info']['platform']}</span>
        </div>
    </div>
    
    <div class="test-results">
        <h2>测试结果详情</h2>
"""
        
        for result in report['test_results']:
            status_class = 'success' if result['success'] else 'failure'
            status_text = '✅ 通过' if result['success'] else '❌ 失败'
            
            html += f"""
        <div class="test-result {status_class}">
            <h3>{result['test_name']} - {status_text}</h3>
            <p><strong>描述:</strong> {result['description']}</p>
            <p><strong>执行时间:</strong> {result['duration']:.2f} 秒</p>
"""
            
            if result['success'] and result['metrics']:
                html += "<div class='metrics'><strong>性能指标:</strong><br>"
                for key, value in result['metrics'].items():
                    if isinstance(value, (int, float)):
                        html += f"<span class='metric'>{key}: {value:.3f}</span>"
                    else:
                        html += f"<span class='metric'>{key}: {value}</span>"
                html += "</div>"
            
            if result['error_message']:
                html += f"<p><strong>错误信息:</strong> {result['error_message']}</p>"
            
            html += "</div>"
        
        # 添加聚合指标
        if 'aggregate_metrics' in report:
            html += """
        <div class="aggregate-metrics">
            <h2>聚合性能指标</h2>
            <div class="metrics">
"""
            for key, value in report['aggregate_metrics'].items():
                html += f"<span class='metric'>{key}: {value:.3f}</span>"
            
            html += """
            </div>
        </div>
"""
        
        html += """
    </div>
</body>
</html>
"""
        return html


def create_default_benchmark_configs() -> List[BenchmarkConfig]:
    """创建默认的基准测试配置"""
    return [
        BenchmarkConfig(
            test_name="single_agent_performance",
            description="单个Agent性能基线测试",
            benchmark_requests=50,
            concurrent_users=1,
            target_response_time=5.0,
            target_success_rate=0.95
        ),
        BenchmarkConfig(
            test_name="concurrent_analysis_stress",
            description="并发专利分析压力测试",
            benchmark_requests=100,
            concurrent_users=10,
            target_response_time=10.0,
            target_success_rate=0.9,
            target_throughput=5.0
        ),
        BenchmarkConfig(
            test_name="large_dataset_load",
            description="大数据量处理负载测试",
            benchmark_requests=20,
            concurrent_users=5,
            target_response_time=30.0,
            target_success_rate=0.85
        ),
        BenchmarkConfig(
            test_name="memory_usage_benchmark",
            description="内存使用基准测试",
            benchmark_requests=30,
            concurrent_users=3,
            target_response_time=15.0,
            target_success_rate=0.9
        ),
        BenchmarkConfig(
            test_name="sustained_load_stress",
            description="持续负载压力测试",
            benchmark_requests=200,
            concurrent_users=15,
            target_response_time=12.0,
            target_success_rate=0.88,
            target_throughput=8.0
        )
    ]


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="专利系统性能基准测试运行器")
    parser.add_argument("--config", help="基准测试配置文件路径")
    parser.add_argument("--output", default="tests/performance/results", help="输出目录")
    parser.add_argument("--tests", nargs="+", help="指定要运行的测试名称")
    
    args = parser.parse_args()
    
    # 加载配置
    if args.config and Path(args.config).exists():
        with open(args.config, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        configs = [BenchmarkConfig(**cfg) for cfg in config_data]
    else:
        configs = create_default_benchmark_configs()
    
    # 过滤指定的测试
    if args.tests:
        configs = [cfg for cfg in configs if cfg.test_name in args.tests]
    
    # 运行基准测试
    runner = BenchmarkRunner(args.output)
    report = await runner.run_all_benchmarks(configs)
    
    # 输出摘要
    print(f"\n{'='*60}")
    print("基准测试完成")
    print(f"{'='*60}")
    print(f"总测试数: {report['summary']['total_tests']}")
    print(f"成功测试: {report['summary']['successful_tests']}")
    print(f"失败测试: {report['summary']['failed_tests']}")
    print(f"成功率: {report['summary']['success_rate']:.2%}")
    print(f"总耗时: {report['summary']['total_duration']:.2f} 秒")
    
    if 'aggregate_metrics' in report:
        print(f"\n聚合性能指标:")
        for key, value in report['aggregate_metrics'].items():
            print(f"  {key}: {value:.3f}")


if __name__ == "__main__":
    asyncio.run(main())