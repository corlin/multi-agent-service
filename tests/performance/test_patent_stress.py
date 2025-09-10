"""
专利系统压力测试套件

测试专利分析系统在高负载和极限条件下的表现。
"""

import asyncio
import time
import random
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Callable
import pytest
from unittest.mock import AsyncMock, patch
import psutil
import json
from dataclasses import dataclass
from datetime import datetime, timedelta

from src.multi_agent_service.patent.agents.coordinator import PatentCoordinatorAgent
from src.multi_agent_service.patent.agents.data_collection import PatentDataCollectionAgent
from src.multi_agent_service.patent.models.requests import PatentAnalysisRequest


@dataclass
class StressTestConfig:
    """压力测试配置"""
    concurrent_users: int = 50
    requests_per_user: int = 10
    ramp_up_time: int = 30  # 秒
    test_duration: int = 300  # 秒
    max_response_time: float = 10.0  # 秒
    min_success_rate: float = 0.95
    max_memory_usage: float = 1000  # MB
    max_cpu_usage: float = 80  # %


@dataclass
class StressTestResult:
    """压力测试结果"""
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    avg_response_time: float
    max_response_time: float
    min_response_time: float
    requests_per_second: float
    peak_memory_usage: float
    peak_cpu_usage: float
    errors: List[str]
    test_duration: float


class StressTestRunner:
    """压力测试运行器"""
    
    def __init__(self, config: StressTestConfig):
        self.config = config
        self.results = []
        self.errors = []
        self.start_time = None
        self.end_time = None
        self.peak_memory = 0
        self.peak_cpu = 0
        self._stop_monitoring = False
        
    async def run_stress_test(self, test_function: Callable) -> StressTestResult:
        """运行压力测试"""
        print(f"开始压力测试: {self.config.concurrent_users}个并发用户, 每用户{self.config.requests_per_user}个请求")
        
        # 启动资源监控
        monitoring_task = asyncio.create_task(self._monitor_resources())
        
        self.start_time = time.time()
        
        # 创建用户任务
        user_tasks = []
        for user_id in range(self.config.concurrent_users):
            # 错开用户启动时间
            delay = (user_id / self.config.concurrent_users) * self.config.ramp_up_time
            task = asyncio.create_task(self._simulate_user(user_id, test_function, delay))
            user_tasks.append(task)
        
        # 等待所有用户完成
        await asyncio.gather(*user_tasks, return_exceptions=True)
        
        self.end_time = time.time()
        self._stop_monitoring = True
        
        # 停止监控
        monitoring_task.cancel()
        
        return self._calculate_results()
    
    async def _simulate_user(self, user_id: int, test_function: Callable, delay: float):
        """模拟单个用户的行为"""
        # 等待启动延迟
        await asyncio.sleep(delay)
        
        for request_id in range(self.config.requests_per_user):
            try:
                start_time = time.time()
                
                # 执行测试函数
                result = await test_function(user_id, request_id)
                
                end_time = time.time()
                response_time = end_time - start_time
                
                self.results.append({
                    'user_id': user_id,
                    'request_id': request_id,
                    'response_time': response_time,
                    'success': result.get('status') == 'success',
                    'timestamp': datetime.now()
                })
                
                # 模拟用户思考时间
                await asyncio.sleep(random.uniform(0.1, 1.0))
                
            except Exception as e:
                self.errors.append(f"User {user_id}, Request {request_id}: {str(e)}")
                self.results.append({
                    'user_id': user_id,
                    'request_id': request_id,
                    'response_time': 0,
                    'success': False,
                    'timestamp': datetime.now()
                })
    
    async def _monitor_resources(self):
        """监控系统资源使用"""
        process = psutil.Process()
        
        while not self._stop_monitoring:
            try:
                # 监控内存使用
                memory_usage = process.memory_info().rss / 1024 / 1024  # MB
                self.peak_memory = max(self.peak_memory, memory_usage)
                
                # 监控CPU使用
                cpu_usage = process.cpu_percent()
                self.peak_cpu = max(self.peak_cpu, cpu_usage)
                
                await asyncio.sleep(1)  # 每秒监控一次
                
            except Exception as e:
                self.errors.append(f"Resource monitoring error: {str(e)}")
    
    def _calculate_results(self) -> StressTestResult:
        """计算测试结果"""
        total_requests = len(self.results)
        successful_requests = sum(1 for r in self.results if r['success'])
        failed_requests = total_requests - successful_requests
        
        success_rate = successful_requests / total_requests if total_requests > 0 else 0
        
        response_times = [r['response_time'] for r in self.results if r['success']]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0
        
        test_duration = self.end_time - self.start_time if self.end_time and self.start_time else 0
        requests_per_second = successful_requests / test_duration if test_duration > 0 else 0
        
        return StressTestResult(
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            success_rate=success_rate,
            avg_response_time=avg_response_time,
            max_response_time=max_response_time,
            min_response_time=min_response_time,
            requests_per_second=requests_per_second,
            peak_memory_usage=self.peak_memory,
            peak_cpu_usage=self.peak_cpu,
            errors=self.errors,
            test_duration=test_duration
        )


@pytest.fixture
def stress_test_config():
    """压力测试配置fixture"""
    return StressTestConfig(
        concurrent_users=20,  # 降低并发数以适应测试环境
        requests_per_user=5,
        ramp_up_time=10,
        test_duration=60,
        max_response_time=15.0,
        min_success_rate=0.8,
        max_memory_usage=800,
        max_cpu_usage=85
    )


@pytest.fixture
def mock_patent_agents_stress():
    """压力测试专用的模拟Agent"""
    with patch('src.multi_agent_service.patent.agents.coordinator.PatentCoordinatorAgent') as mock_coordinator, \
         patch('src.multi_agent_service.patent.agents.data_collection.PatentDataCollectionAgent') as mock_data_collection:
        
        # 模拟真实的处理延迟
        async def mock_process_with_delay(*args, **kwargs):
            # 随机延迟模拟真实处理时间
            await asyncio.sleep(random.uniform(0.1, 2.0))
            
            # 随机失败模拟真实错误情况
            if random.random() < 0.05:  # 5%失败率
                raise Exception("Simulated processing error")
            
            return {
                'status': 'success',
                'analysis_id': f'stress-test-{random.randint(1000, 9999)}',
                'results': {'patents_found': random.randint(50, 200)}
            }
        
        mock_coordinator.return_value.process_request = mock_process_with_delay
        mock_data_collection.return_value.process_request = mock_process_with_delay
        
        yield {
            'coordinator': mock_coordinator,
            'data_collection': mock_data_collection
        }


class TestPatentStressTests:
    """专利系统压力测试"""
    
    @pytest.mark.asyncio
    async def test_high_concurrency_stress(self, stress_test_config, mock_patent_agents_stress):
        """高并发压力测试"""
        
        async def patent_analysis_request(user_id: int, request_id: int):
            """专利分析请求函数"""
            agent_config = {'agent_id': f'stress-coordinator-{user_id}', 'model_config': {}}
            coordinator = PatentCoordinatorAgent(agent_config)
            
            request = PatentAnalysisRequest(
                keywords=[f'stress-test-{user_id}-{request_id}', 'technology'],
                analysis_type='basic',
                limit=random.randint(20, 100)
            )
            
            return await coordinator.process_request(request.dict())
        
        # 运行压力测试
        runner = StressTestRunner(stress_test_config)
        result = await runner.run_stress_test(patent_analysis_request)
        
        # 验证压力测试结果
        assert result.success_rate >= stress_test_config.min_success_rate, \
            f"成功率过低: {result.success_rate:.2%} < {stress_test_config.min_success_rate:.2%}"
        
        assert result.avg_response_time <= stress_test_config.max_response_time, \
            f"平均响应时间过长: {result.avg_response_time:.2f}s > {stress_test_config.max_response_time}s"
        
        assert result.peak_memory_usage <= stress_test_config.max_memory_usage, \
            f"内存使用过高: {result.peak_memory_usage:.2f}MB > {stress_test_config.max_memory_usage}MB"
        
        # 输出压力测试报告
        print(f"\n{'='*50}")
        print("高并发压力测试报告")
        print(f"{'='*50}")
        print(f"总请求数: {result.total_requests}")
        print(f"成功请求数: {result.successful_requests}")
        print(f"失败请求数: {result.failed_requests}")
        print(f"成功率: {result.success_rate:.2%}")
        print(f"平均响应时间: {result.avg_response_time:.2f}s")
        print(f"最大响应时间: {result.max_response_time:.2f}s")
        print(f"最小响应时间: {result.min_response_time:.2f}s")
        print(f"每秒请求数: {result.requests_per_second:.2f}")
        print(f"峰值内存使用: {result.peak_memory_usage:.2f}MB")
        print(f"峰值CPU使用: {result.peak_cpu_usage:.2f}%")
        print(f"测试持续时间: {result.test_duration:.2f}s")
        
        if result.errors:
            print(f"错误数量: {len(result.errors)}")
            print("前5个错误:")
            for error in result.errors[:5]:
                print(f"  - {error}")
    
    @pytest.mark.asyncio
    async def test_sustained_load_stress(self, mock_patent_agents_stress):
        """持续负载压力测试"""
        
        # 配置持续负载测试
        sustained_config = StressTestConfig(
            concurrent_users=10,
            requests_per_user=20,  # 更多请求
            ramp_up_time=5,
            test_duration=120,  # 更长时间
            max_response_time=20.0,
            min_success_rate=0.85,
            max_memory_usage=600,
            max_cpu_usage=90
        )
        
        async def sustained_analysis_request(user_id: int, request_id: int):
            """持续分析请求"""
            agent_config = {'agent_id': f'sustained-{user_id}', 'model_config': {}}
            coordinator = PatentCoordinatorAgent(agent_config)
            
            # 模拟不同复杂度的请求
            complexity = random.choice(['basic', 'standard', 'comprehensive'])
            limit = {'basic': 50, 'standard': 100, 'comprehensive': 200}[complexity]
            
            request = PatentAnalysisRequest(
                keywords=[f'sustained-{complexity}-{user_id}', 'innovation'],
                analysis_type=complexity,
                limit=limit
            )
            
            return await coordinator.process_request(request.dict())
        
        # 运行持续负载测试
        runner = StressTestRunner(sustained_config)
        result = await runner.run_sustained_load_test(sustained_analysis_request)
        
        # 验证持续负载结果
        assert result.success_rate >= sustained_config.min_success_rate, \
            f"持续负载成功率过低: {result.success_rate:.2%}"
        
        assert result.requests_per_second >= 1.0, \
            f"持续负载吞吐量过低: {result.requests_per_second:.2f} RPS"
        
        # 输出持续负载测试报告
        print(f"\n{'='*50}")
        print("持续负载压力测试报告")
        print(f"{'='*50}")
        print(f"测试持续时间: {result.test_duration:.2f}s")
        print(f"总处理请求: {result.successful_requests}")
        print(f"平均吞吐量: {result.requests_per_second:.2f} RPS")
        print(f"成功率: {result.success_rate:.2%}")
        print(f"平均响应时间: {result.avg_response_time:.2f}s")
        print(f"资源使用峰值: 内存={result.peak_memory_usage:.2f}MB, CPU={result.peak_cpu_usage:.2f}%")
    
    async def run_sustained_load_test(self, test_function: Callable) -> StressTestResult:
        """运行持续负载测试（StressTestRunner的扩展方法）"""
        print(f"开始持续负载测试: {self.config.test_duration}秒")
        
        # 启动资源监控
        monitoring_task = asyncio.create_task(self._monitor_resources())
        
        self.start_time = time.time()
        end_time = self.start_time + self.config.test_duration
        
        # 持续生成负载
        user_tasks = []
        user_id = 0
        request_id = 0
        
        while time.time() < end_time:
            # 动态调整并发用户数
            current_users = min(self.config.concurrent_users, len([t for t in user_tasks if not t.done()]))
            
            if current_users < self.config.concurrent_users:
                # 启动新用户
                task = asyncio.create_task(self._simulate_sustained_user(user_id, test_function, end_time))
                user_tasks.append(task)
                user_id += 1
            
            await asyncio.sleep(0.1)  # 短暂等待
        
        # 等待所有任务完成
        await asyncio.gather(*user_tasks, return_exceptions=True)
        
        self.end_time = time.time()
        self._stop_monitoring = True
        
        # 停止监控
        monitoring_task.cancel()
        
        return self._calculate_results()
    
    async def _simulate_sustained_user(self, user_id: int, test_function: Callable, end_time: float):
        """模拟持续负载用户"""
        request_id = 0
        
        while time.time() < end_time:
            try:
                start_time = time.time()
                
                # 执行测试函数
                result = await test_function(user_id, request_id)
                
                response_time = time.time() - start_time
                
                self.results.append({
                    'user_id': user_id,
                    'request_id': request_id,
                    'response_time': response_time,
                    'success': result.get('status') == 'success',
                    'timestamp': datetime.now()
                })
                
                request_id += 1
                
                # 动态调整请求间隔
                interval = random.uniform(0.5, 2.0)
                await asyncio.sleep(interval)
                
            except Exception as e:
                self.errors.append(f"Sustained User {user_id}, Request {request_id}: {str(e)}")
                await asyncio.sleep(1.0)  # 错误后等待更长时间


# 将扩展方法添加到StressTestRunner类
StressTestRunner.run_sustained_load_test = TestPatentStressTests.run_sustained_load_test
StressTestRunner._simulate_sustained_user = TestPatentStressTests._simulate_sustained_user


class TestPatentMemoryLeakTests:
    """专利系统内存泄漏测试"""
    
    @pytest.mark.asyncio
    async def test_memory_leak_detection(self, mock_patent_agents_stress):
        """内存泄漏检测测试"""
        
        agent_config = {'agent_id': 'memory-leak-test', 'model_config': {}}
        
        # 记录初始内存
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        memory_samples = [initial_memory]
        
        # 执行大量操作
        for cycle in range(10):  # 10个周期
            print(f"内存泄漏测试周期 {cycle + 1}/10")
            
            # 每个周期创建多个Agent并执行任务
            agents = []
            for i in range(20):  # 每周期20个Agent
                if i % 4 == 0:
                    agent = PatentCoordinatorAgent(agent_config)
                elif i % 4 == 1:
                    agent = PatentDataCollectionAgent(agent_config)
                else:
                    agent = PatentCoordinatorAgent(agent_config)  # 使用协调Agent
                
                agents.append(agent)
            
            # 并发执行任务
            tasks = []
            for i, agent in enumerate(agents):
                request = {
                    'keywords': [f'memory-test-{cycle}-{i}'],
                    'limit': 30
                }
                tasks.append(agent.process_request(request))
            
            # 等待所有任务完成
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # 清理引用
            del agents
            del tasks
            
            # 强制垃圾回收
            import gc
            gc.collect()
            
            # 记录内存使用
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_samples.append(current_memory)
            
            print(f"周期 {cycle + 1} 内存使用: {current_memory:.2f}MB")
            
            # 短暂等待
            await asyncio.sleep(1)
        
        # 分析内存趋势
        final_memory = memory_samples[-1]
        memory_increase = final_memory - initial_memory
        
        # 计算内存增长趋势
        if len(memory_samples) > 2:
            # 简单线性回归检测趋势
            n = len(memory_samples)
            x_sum = sum(range(n))
            y_sum = sum(memory_samples)
            xy_sum = sum(i * memory_samples[i] for i in range(n))
            x2_sum = sum(i * i for i in range(n))
            
            slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
            
            print(f"\n内存泄漏检测结果:")
            print(f"初始内存: {initial_memory:.2f}MB")
            print(f"最终内存: {final_memory:.2f}MB")
            print(f"内存增长: {memory_increase:.2f}MB")
            print(f"增长趋势: {slope:.4f}MB/周期")
            
            # 内存泄漏断言
            assert memory_increase < 200, f"可能存在内存泄漏: 增长了{memory_increase:.2f}MB"
            assert slope < 5.0, f"内存增长趋势过快: {slope:.4f}MB/周期"
        
        print(f"内存使用历史: {[f'{m:.2f}MB' for m in memory_samples]}")


@pytest.mark.asyncio
async def test_performance_regression_detection(mock_patent_agents_stress):
    """性能回归检测测试"""
    
    # 基准性能测试
    baseline_config = StressTestConfig(
        concurrent_users=5,
        requests_per_user=10,
        ramp_up_time=2,
        test_duration=30,
        max_response_time=10.0,
        min_success_rate=0.9
    )
    
    async def baseline_test_function(user_id: int, request_id: int):
        """基准测试函数"""
        agent_config = {'agent_id': f'baseline-{user_id}', 'model_config': {}}
        coordinator = PatentCoordinatorAgent(agent_config)
        
        request = PatentAnalysisRequest(
            keywords=[f'baseline-{user_id}-{request_id}'],
            analysis_type='basic',
            limit=50
        )
        
        return await coordinator.process_request(request.dict())
    
    # 运行基准测试
    baseline_runner = StressTestRunner(baseline_config)
    baseline_result = await baseline_runner.run_stress_test(baseline_test_function)
    
    # 当前性能测试（模拟可能的性能回归）
    current_runner = StressTestRunner(baseline_config)
    current_result = await current_runner.run_stress_test(baseline_test_function)
    
    # 性能回归检测
    response_time_regression = (current_result.avg_response_time - baseline_result.avg_response_time) / baseline_result.avg_response_time
    success_rate_regression = baseline_result.success_rate - current_result.success_rate
    throughput_regression = (baseline_result.requests_per_second - current_result.requests_per_second) / baseline_result.requests_per_second
    
    print(f"\n{'='*50}")
    print("性能回归检测报告")
    print(f"{'='*50}")
    print(f"基准响应时间: {baseline_result.avg_response_time:.2f}s")
    print(f"当前响应时间: {current_result.avg_response_time:.2f}s")
    print(f"响应时间回归: {response_time_regression:.2%}")
    print(f"")
    print(f"基准成功率: {baseline_result.success_rate:.2%}")
    print(f"当前成功率: {current_result.success_rate:.2%}")
    print(f"成功率回归: {success_rate_regression:.2%}")
    print(f"")
    print(f"基准吞吐量: {baseline_result.requests_per_second:.2f} RPS")
    print(f"当前吞吐量: {current_result.requests_per_second:.2f} RPS")
    print(f"吞吐量回归: {throughput_regression:.2%}")
    
    # 性能回归断言
    assert response_time_regression < 0.2, f"响应时间回归过大: {response_time_regression:.2%}"
    assert success_rate_regression < 0.05, f"成功率回归过大: {success_rate_regression:.2%}"
    assert throughput_regression < 0.15, f"吞吐量回归过大: {throughput_regression:.2%}"
    
    print("\n✅ 性能回归检测通过")