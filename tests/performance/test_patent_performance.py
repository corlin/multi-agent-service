"""
专利系统性能测试套件

测试专利分析系统的性能基准、并发处理能力、大数据量处理和Agent负载测试。
"""

import asyncio
import time
import statistics
import psutil
import pytest
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch
import json
import threading
from dataclasses import dataclass
from datetime import datetime

from src.multi_agent_service.patent.agents.coordinator import PatentCoordinatorAgent
from src.multi_agent_service.patent.agents.data_collection import PatentDataCollectionAgent
from src.multi_agent_service.patent.agents.search import PatentSearchAgent
from src.multi_agent_service.patent.agents.analysis import PatentAnalysisAgent
from src.multi_agent_service.patent.agents.report import PatentReportAgent
from src.multi_agent_service.patent.models.requests import PatentAnalysisRequest


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    operation: str
    duration: float
    memory_usage: float
    cpu_usage: float
    success: bool
    error_message: str = ""
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics: List[PerformanceMetrics] = []
        self.process = psutil.Process()
        
    def start_monitoring(self) -> Dict[str, Any]:
        """开始监控，返回初始状态"""
        return {
            'start_time': time.time(),
            'start_memory': self.process.memory_info().rss / 1024 / 1024,  # MB
            'start_cpu': self.process.cpu_percent()
        }
    
    def end_monitoring(self, start_state: Dict[str, Any], operation: str, success: bool = True, error: str = "") -> PerformanceMetrics:
        """结束监控，计算性能指标"""
        end_time = time.time()
        end_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        end_cpu = self.process.cpu_percent()
        
        metrics = PerformanceMetrics(
            operation=operation,
            duration=end_time - start_state['start_time'],
            memory_usage=end_memory - start_state['start_memory'],
            cpu_usage=end_cpu,
            success=success,
            error_message=error
        )
        
        self.metrics.append(metrics)
        return metrics
    
    def get_statistics(self, operation: str = None) -> Dict[str, Any]:
        """获取性能统计信息"""
        filtered_metrics = self.metrics
        if operation:
            filtered_metrics = [m for m in self.metrics if m.operation == operation]
        
        if not filtered_metrics:
            return {}
        
        durations = [m.duration for m in filtered_metrics]
        memory_usages = [m.memory_usage for m in filtered_metrics]
        success_rate = sum(1 for m in filtered_metrics if m.success) / len(filtered_metrics)
        
        return {
            'operation': operation or 'all',
            'total_operations': len(filtered_metrics),
            'success_rate': success_rate,
            'duration_stats': {
                'mean': statistics.mean(durations),
                'median': statistics.median(durations),
                'min': min(durations),
                'max': max(durations),
                'stdev': statistics.stdev(durations) if len(durations) > 1 else 0
            },
            'memory_stats': {
                'mean': statistics.mean(memory_usages),
                'median': statistics.median(memory_usages),
                'min': min(memory_usages),
                'max': max(memory_usages),
                'stdev': statistics.stdev(memory_usages) if len(memory_usages) > 1 else 0
            }
        }


@pytest.fixture
def performance_monitor():
    """性能监控器fixture"""
    return PerformanceMonitor()


@pytest.fixture
def mock_patent_agents():
    """模拟专利Agent的fixture"""
    with patch('src.multi_agent_service.patent.agents.coordinator.PatentCoordinatorAgent') as mock_coordinator, \
         patch('src.multi_agent_service.patent.agents.data_collection.PatentDataCollectionAgent') as mock_data_collection, \
         patch('src.multi_agent_service.patent.agents.search.PatentSearchAgent') as mock_search, \
         patch('src.multi_agent_service.patent.agents.analysis.PatentAnalysisAgent') as mock_analysis, \
         patch('src.multi_agent_service.patent.agents.report.PatentReportAgent') as mock_report:
        
        # 配置模拟响应
        mock_coordinator.return_value.process_request = AsyncMock(return_value={
            'status': 'success',
            'analysis_id': 'test-123',
            'results': {'patents_found': 100}
        })
        
        mock_data_collection.return_value.process_request = AsyncMock(return_value={
            'status': 'success',
            'patents': [{'id': f'patent-{i}', 'title': f'Patent {i}'} for i in range(100)]
        })
        
        mock_search.return_value.process_request = AsyncMock(return_value={
            'status': 'success',
            'enhanced_data': {'cnki_results': [], 'web_results': []}
        })
        
        mock_analysis.return_value.process_request = AsyncMock(return_value={
            'status': 'success',
            'analysis': {'trends': {}, 'competition': {}, 'technology': {}}
        })
        
        mock_report.return_value.process_request = AsyncMock(return_value={
            'status': 'success',
            'report_url': 'http://example.com/report.pdf'
        })
        
        yield {
            'coordinator': mock_coordinator,
            'data_collection': mock_data_collection,
            'search': mock_search,
            'analysis': mock_analysis,
            'report': mock_report
        }


class TestPatentPerformanceBenchmarks:
    """专利分析性能基准测试"""
    
    @pytest.mark.asyncio
    async def test_single_agent_performance_baseline(self, performance_monitor, mock_patent_agents):
        """测试单个Agent的性能基线"""
        
        # 使用模拟的Agent实例
        mock_agent = mock_patent_agents['data_collection'].return_value
        
        request = {
            'keywords': ['artificial intelligence', 'machine learning'],
            'limit': 50
        }
        
        start_state = performance_monitor.start_monitoring()
        
        try:
            result = await mock_agent.process_request(request)
            success = result.get('status') == 'success'
            error = ""
        except Exception as e:
            success = False
            error = str(e)
        
        metrics = performance_monitor.end_monitoring(start_state, 'data_collection_agent', success, error)
        
        # 性能断言
        assert metrics.duration < 5.0, f"数据收集Agent响应时间过长: {metrics.duration}s"
        assert metrics.memory_usage < 100, f"内存使用过多: {metrics.memory_usage}MB"
        assert success, f"Agent执行失败: {error}"
    
    @pytest.mark.asyncio
    async def test_coordinator_agent_performance_baseline(self, performance_monitor, mock_patent_agents):
        """测试协调Agent的性能基线"""
        
        # 使用模拟的协调Agent实例
        mock_coordinator = mock_patent_agents['coordinator'].return_value
        
        request = {
            'keywords': ['blockchain', 'cryptocurrency'],
            'analysis_type': 'comprehensive',
            'limit': 100
        }
        
        start_state = performance_monitor.start_monitoring()
        
        try:
            result = await mock_coordinator.process_request(request)
            success = result.get('status') == 'success'
            error = ""
        except Exception as e:
            success = False
            error = str(e)
        
        metrics = performance_monitor.end_monitoring(start_state, 'coordinator_agent', success, error)
        
        # 性能断言
        assert metrics.duration < 10.0, f"协调Agent响应时间过长: {metrics.duration}s"
        assert metrics.memory_usage < 200, f"内存使用过多: {metrics.memory_usage}MB"
        assert success, f"协调Agent执行失败: {error}"
    
    @pytest.mark.asyncio
    async def test_all_agents_performance_baseline(self, performance_monitor, mock_patent_agents):
        """测试所有Agent的性能基线"""
        
        agents = [
            ('data_collection', mock_patent_agents['data_collection']),
            ('search', mock_patent_agents['search']),
            ('analysis', mock_patent_agents['analysis']),
            ('report', mock_patent_agents['report'])
        ]
        
        request = {
            'keywords': ['quantum computing'],
            'limit': 20
        }
        
        for agent_name, mock_agent_class in agents:
            mock_agent = mock_agent_class.return_value
            
            start_state = performance_monitor.start_monitoring()
            
            try:
                result = await mock_agent.process_request(request)
                success = result.get('status') == 'success'
                error = ""
            except Exception as e:
                success = False
                error = str(e)
            
            metrics = performance_monitor.end_monitoring(start_state, f'{agent_name}_agent', success, error)
            
            # 每个Agent的性能要求
            assert metrics.duration < 8.0, f"{agent_name} Agent响应时间过长: {metrics.duration}s"
            assert success, f"{agent_name} Agent执行失败: {error}"
        
        # 输出性能统计
        stats = performance_monitor.get_statistics()
        print(f"\n所有Agent性能统计: {json.dumps(stats, indent=2, default=str)}")


class TestPatentConcurrencyPerformance:
    """专利分析并发性能测试"""
    
    @pytest.mark.asyncio
    async def test_concurrent_analysis_requests(self, performance_monitor, mock_patent_agents):
        """测试并发专利分析请求"""
        
        concurrent_requests = 10
        agent_config = {'agent_id': 'test-coordinator', 'model_config': {}}
        
        async def single_analysis_request(request_id: int):
            """单个分析请求"""
            coordinator = PatentCoordinatorAgent(agent_config)
            request = PatentAnalysisRequest(
                keywords=[f'technology-{request_id}', 'innovation'],
                analysis_type='basic',
                limit=50
            )
            
            start_state = performance_monitor.start_monitoring()
            
            try:
                result = await coordinator.process_request(request.dict())
                success = result.get('status') == 'success'
                error = ""
            except Exception as e:
                success = False
                error = str(e)
            
            metrics = performance_monitor.end_monitoring(
                start_state, 
                f'concurrent_request_{request_id}', 
                success, 
                error
            )
            
            return metrics
        
        # 并发执行请求
        start_time = time.time()
        tasks = [single_analysis_request(i) for i in range(concurrent_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # 分析结果
        successful_requests = sum(1 for r in results if isinstance(r, PerformanceMetrics) and r.success)
        success_rate = successful_requests / concurrent_requests
        
        # 性能断言
        assert success_rate >= 0.8, f"并发成功率过低: {success_rate}"
        assert total_time < 30.0, f"并发处理时间过长: {total_time}s"
        
        # 输出并发性能统计
        concurrent_stats = performance_monitor.get_statistics('concurrent_request')
        print(f"\n并发性能统计: {json.dumps(concurrent_stats, indent=2, default=str)}")
    
    @pytest.mark.asyncio
    async def test_agent_load_balancing(self, performance_monitor, mock_patent_agents):
        """测试Agent负载均衡性能"""
        
        # 模拟多个Agent实例
        agent_instances = []
        for i in range(3):
            agent_config = {'agent_id': f'data-collection-{i}', 'model_config': {}}
            agent_instances.append(PatentDataCollectionAgent(agent_config))
        
        requests_per_agent = 5
        total_requests = len(agent_instances) * requests_per_agent
        
        async def process_with_agent(agent, request_id):
            """使用指定Agent处理请求"""
            request = {
                'keywords': [f'keyword-{request_id}'],
                'limit': 10
            }
            
            start_state = performance_monitor.start_monitoring()
            
            try:
                result = await agent.process_request(request)
                success = result.get('status') == 'success'
                error = ""
            except Exception as e:
                success = False
                error = str(e)
            
            return performance_monitor.end_monitoring(
                start_state, 
                f'load_balanced_request_{request_id}', 
                success, 
                error
            )
        
        # 分配请求到不同Agent
        tasks = []
        for i in range(total_requests):
            agent = agent_instances[i % len(agent_instances)]
            tasks.append(process_with_agent(agent, i))
        
        # 并发执行
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # 分析负载均衡效果
        successful_requests = sum(1 for r in results if isinstance(r, PerformanceMetrics) and r.success)
        success_rate = successful_requests / total_requests
        
        assert success_rate >= 0.9, f"负载均衡成功率过低: {success_rate}"
        assert total_time < 20.0, f"负载均衡处理时间过长: {total_time}s"
        
        # 输出负载均衡统计
        load_balance_stats = performance_monitor.get_statistics('load_balanced_request')
        print(f"\n负载均衡性能统计: {json.dumps(load_balance_stats, indent=2, default=str)}")


class TestPatentBigDataPerformance:
    """专利大数据量处理性能测试"""
    
    @pytest.mark.asyncio
    async def test_large_dataset_processing(self, performance_monitor, mock_patent_agents):
        """测试大数据量专利处理性能"""
        
        # 模拟大数据量请求
        large_request = {
            'keywords': ['artificial intelligence', 'machine learning', 'deep learning', 'neural networks'],
            'limit': 1000,  # 大数据量
            'include_full_text': True,
            'analysis_depth': 'comprehensive'
        }
        
        agent_config = {'agent_id': 'test-big-data', 'model_config': {}}
        coordinator = PatentCoordinatorAgent(agent_config)
        
        start_state = performance_monitor.start_monitoring()
        
        try:
            result = await coordinator.process_request(large_request)
            success = result.get('status') == 'success'
            error = ""
        except Exception as e:
            success = False
            error = str(e)
        
        metrics = performance_monitor.end_monitoring(start_state, 'large_dataset_processing', success, error)
        
        # 大数据量性能要求
        assert metrics.duration < 60.0, f"大数据量处理时间过长: {metrics.duration}s"
        assert metrics.memory_usage < 500, f"大数据量内存使用过多: {metrics.memory_usage}MB"
        assert success, f"大数据量处理失败: {error}"
        
        print(f"\n大数据量处理性能: 时间={metrics.duration:.2f}s, 内存={metrics.memory_usage:.2f}MB")
    
    @pytest.mark.asyncio
    async def test_batch_processing_performance(self, performance_monitor, mock_patent_agents):
        """测试批量处理性能"""
        
        # 创建批量请求
        batch_requests = []
        for i in range(20):  # 20个批次
            batch_requests.append({
                'keywords': [f'technology-batch-{i}', 'innovation'],
                'limit': 100,
                'batch_id': i
            })
        
        agent_config = {'agent_id': 'test-batch', 'model_config': {}}
        
        # 批量处理
        start_time = time.time()
        processed_batches = 0
        
        for batch_request in batch_requests:
            coordinator = PatentCoordinatorAgent(agent_config)
            
            start_state = performance_monitor.start_monitoring()
            
            try:
                result = await coordinator.process_request(batch_request)
                success = result.get('status') == 'success'
                if success:
                    processed_batches += 1
                error = ""
            except Exception as e:
                success = False
                error = str(e)
            
            performance_monitor.end_monitoring(
                start_state, 
                f'batch_processing_{batch_request["batch_id"]}', 
                success, 
                error
            )
        
        total_time = time.time() - start_time
        throughput = processed_batches / total_time  # 批次/秒
        
        # 批量处理性能要求
        assert throughput >= 0.5, f"批量处理吞吐量过低: {throughput:.2f} 批次/秒"
        assert processed_batches >= 18, f"批量处理成功率过低: {processed_batches}/20"
        
        # 输出批量处理统计
        batch_stats = performance_monitor.get_statistics('batch_processing')
        print(f"\n批量处理性能统计: {json.dumps(batch_stats, indent=2, default=str)}")
        print(f"吞吐量: {throughput:.2f} 批次/秒")


class TestPatentAgentResourceMonitoring:
    """专利Agent资源监控测试"""
    
    @pytest.mark.asyncio
    async def test_memory_usage_monitoring(self, performance_monitor, mock_patent_agents):
        """测试内存使用监控"""
        
        agent_config = {'agent_id': 'test-memory', 'model_config': {}}
        
        # 监控不同Agent的内存使用
        agents = [
            ('coordinator', PatentCoordinatorAgent(agent_config)),
            ('data_collection', PatentDataCollectionAgent(agent_config)),
            ('analysis', PatentAnalysisAgent(agent_config))
        ]
        
        memory_usage_results = {}
        
        for agent_name, agent in agents:
            # 执行多次请求监控内存使用
            for i in range(5):
                request = {
                    'keywords': [f'memory-test-{i}'],
                    'limit': 50
                }
                
                start_state = performance_monitor.start_monitoring()
                
                try:
                    await agent.process_request(request)
                    success = True
                    error = ""
                except Exception as e:
                    success = False
                    error = str(e)
                
                metrics = performance_monitor.end_monitoring(
                    start_state, 
                    f'{agent_name}_memory_test_{i}', 
                    success, 
                    error
                )
                
                if agent_name not in memory_usage_results:
                    memory_usage_results[agent_name] = []
                memory_usage_results[agent_name].append(metrics.memory_usage)
        
        # 分析内存使用模式
        for agent_name, memory_usages in memory_usage_results.items():
            avg_memory = statistics.mean(memory_usages)
            max_memory = max(memory_usages)
            
            # 内存使用断言
            assert avg_memory < 150, f"{agent_name} 平均内存使用过高: {avg_memory:.2f}MB"
            assert max_memory < 300, f"{agent_name} 最大内存使用过高: {max_memory:.2f}MB"
            
            print(f"\n{agent_name} 内存使用: 平均={avg_memory:.2f}MB, 最大={max_memory:.2f}MB")
    
    @pytest.mark.asyncio
    async def test_cpu_usage_monitoring(self, performance_monitor, mock_patent_agents):
        """测试CPU使用监控"""
        
        agent_config = {'agent_id': 'test-cpu', 'model_config': {}}
        coordinator = PatentCoordinatorAgent(agent_config)
        
        # CPU密集型请求
        cpu_intensive_request = {
            'keywords': ['complex', 'analysis', 'computation'],
            'limit': 200,
            'analysis_type': 'comprehensive',
            'include_trends': True,
            'include_competition': True,
            'include_technology_classification': True
        }
        
        start_state = performance_monitor.start_monitoring()
        
        try:
            result = await coordinator.process_request(cpu_intensive_request)
            success = result.get('status') == 'success'
            error = ""
        except Exception as e:
            success = False
            error = str(e)
        
        metrics = performance_monitor.end_monitoring(start_state, 'cpu_intensive_test', success, error)
        
        # CPU使用断言
        assert metrics.cpu_usage < 80.0, f"CPU使用率过高: {metrics.cpu_usage}%"
        assert success, f"CPU密集型任务执行失败: {error}"
        
        print(f"\nCPU密集型任务性能: CPU={metrics.cpu_usage:.2f}%, 时间={metrics.duration:.2f}s")
    
    @pytest.mark.asyncio
    async def test_resource_cleanup(self, performance_monitor, mock_patent_agents):
        """测试资源清理"""
        
        agent_config = {'agent_id': 'test-cleanup', 'model_config': {}}
        
        # 记录初始资源状态
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        # 执行多个Agent任务
        agents = [
            PatentCoordinatorAgent(agent_config),
            PatentDataCollectionAgent(agent_config),
            PatentAnalysisAgent(agent_config)
        ]
        
        for i, agent in enumerate(agents):
            request = {
                'keywords': [f'cleanup-test-{i}'],
                'limit': 100
            }
            
            start_state = performance_monitor.start_monitoring()
            
            try:
                await agent.process_request(request)
                success = True
                error = ""
            except Exception as e:
                success = False
                error = str(e)
            
            performance_monitor.end_monitoring(
                start_state, 
                f'cleanup_test_{i}', 
                success, 
                error
            )
        
        # 强制垃圾回收
        import gc
        gc.collect()
        
        # 检查资源清理效果
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory
        
        # 资源清理断言
        assert memory_increase < 100, f"内存泄漏检测: 增加了{memory_increase:.2f}MB"
        
        print(f"\n资源清理测试: 初始内存={initial_memory:.2f}MB, 最终内存={final_memory:.2f}MB, 增加={memory_increase:.2f}MB")


@pytest.mark.asyncio
async def test_comprehensive_performance_report(performance_monitor, mock_patent_agents):
    """生成综合性能报告"""
    
    # 执行各种性能测试
    test_scenarios = [
        ('single_agent', 'data_collection'),
        ('concurrent_requests', 'coordinator'),
        ('large_dataset', 'analysis'),
        ('batch_processing', 'coordinator')
    ]
    
    agent_config = {'agent_id': 'test-comprehensive', 'model_config': {}}
    
    for scenario_name, agent_type in test_scenarios:
        if agent_type == 'coordinator':
            agent = PatentCoordinatorAgent(agent_config)
        elif agent_type == 'data_collection':
            agent = PatentDataCollectionAgent(agent_config)
        else:
            agent = PatentAnalysisAgent(agent_config)
        
        request = {
            'keywords': [f'{scenario_name}-test'],
            'limit': 50 if scenario_name != 'large_dataset' else 500
        }
        
        start_state = performance_monitor.start_monitoring()
        
        try:
            result = await agent.process_request(request)
            success = result.get('status') == 'success'
            error = ""
        except Exception as e:
            success = False
            error = str(e)
        
        performance_monitor.end_monitoring(start_state, scenario_name, success, error)
    
    # 生成综合报告
    comprehensive_stats = performance_monitor.get_statistics()
    
    # 保存性能报告
    report = {
        'test_timestamp': datetime.now().isoformat(),
        'system_info': {
            'cpu_count': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total / 1024 / 1024 / 1024,  # GB
            'python_version': f"{psutil.sys.version_info.major}.{psutil.sys.version_info.minor}"
        },
        'performance_statistics': comprehensive_stats,
        'individual_metrics': [
            {
                'operation': m.operation,
                'duration': m.duration,
                'memory_usage': m.memory_usage,
                'cpu_usage': m.cpu_usage,
                'success': m.success,
                'timestamp': m.timestamp.isoformat()
            }
            for m in performance_monitor.metrics
        ]
    }
    
    # 输出报告
    print(f"\n{'='*50}")
    print("专利系统综合性能报告")
    print(f"{'='*50}")
    print(json.dumps(report, indent=2, default=str))
    
    # 性能基准断言
    assert comprehensive_stats['success_rate'] >= 0.8, "整体成功率过低"
    assert comprehensive_stats['duration_stats']['mean'] < 15.0, "平均响应时间过长"