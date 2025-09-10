# 专利系统性能测试套件

本目录包含专利分析系统的完整性能测试套件，用于评估系统在各种负载条件下的表现。

## 📁 目录结构

```
tests/performance/
├── README.md                           # 本文档
├── test_patent_performance.py          # 基础性能测试
├── test_patent_stress.py              # 压力测试
├── benchmark_runner.py                 # 基准测试运行器
├── run_performance_tests.py            # 综合测试执行器
├── config/
│   └── benchmark_config.json          # 基准测试配置
└── results/                           # 测试结果输出目录
    └── session_YYYYMMDD_HHMMSS/       # 按时间戳组织的测试会话
        ├── benchmark_report_*.json     # JSON格式报告
        ├── benchmark_report_*.html     # HTML格式报告
        └── comprehensive_performance_report.*  # 综合报告
```

## 🚀 快速开始

### 使用uv运行完整性能测试套件

```bash
# 运行完整性能测试套件
uv run python tests/performance/run_performance_tests.py

# 快速测试模式（推荐用于开发环境）
uv run python tests/performance/run_performance_tests.py --quick

# 运行特定测试
uv run python tests/performance/run_performance_tests.py --tests single_agent_baseline concurrent_analysis_light

# 使用自定义配置
uv run python tests/performance/run_performance_tests.py --config tests/performance/config/benchmark_config.json
```

### 使用便捷脚本

```bash
# 运行默认性能测试
uv run python scripts/run_patent_performance_tests.py

# 运行特定测试
uv run python scripts/run_patent_performance_tests.py specific

# 使用pytest运行
uv run python scripts/run_patent_performance_tests.py pytest
```

### 使用pytest直接运行

```bash
# 运行所有性能测试
uv run pytest tests/performance/ -v

# 运行特定测试文件
uv run pytest tests/performance/test_patent_performance.py -v

# 运行压力测试
uv run pytest tests/performance/test_patent_stress.py -v
```

## 📊 测试类型

### 1. 基础性能测试 (`test_patent_performance.py`)

- **单Agent性能基线测试**: 测试单个Agent的响应时间和资源使用
- **并发分析请求测试**: 测试系统处理并发请求的能力
- **大数据量处理测试**: 测试系统处理大量专利数据的性能
- **Agent负载均衡测试**: 测试多Agent实例的负载分配
- **资源监控测试**: 监控内存和CPU使用情况

### 2. 压力测试 (`test_patent_stress.py`)

- **高并发压力测试**: 模拟大量并发用户访问
- **持续负载测试**: 长时间持续负载下的系统表现
- **内存泄漏检测**: 检测长期运行中的内存泄漏问题
- **性能回归检测**: 对比基准性能，检测性能退化

### 3. 基准测试 (`benchmark_runner.py`)

- **可配置的基准测试**: 支持自定义测试参数
- **多维度性能指标**: 响应时间、吞吐量、成功率、资源使用
- **自动化报告生成**: JSON和HTML格式的详细报告
- **性能趋势分析**: 历史性能数据对比

## ⚙️ 配置说明

### 基准测试配置 (`config/benchmark_config.json`)

```json
{
  "test_name": "single_agent_baseline",
  "description": "单个专利Agent性能基线测试",
  "enabled": true,
  "timeout": 120,
  "retry_count": 2,
  "warm_up_requests": 5,
  "benchmark_requests": 30,
  "concurrent_users": 1,
  "target_response_time": 3.0,
  "target_success_rate": 0.95,
  "target_throughput": 1.0
}
```

**配置参数说明**:
- `test_name`: 测试名称
- `description`: 测试描述
- `enabled`: 是否启用该测试
- `timeout`: 测试超时时间（秒）
- `retry_count`: 失败重试次数
- `warm_up_requests`: 预热请求数量
- `benchmark_requests`: 基准测试请求数量
- `concurrent_users`: 并发用户数
- `target_response_time`: 目标响应时间（秒）
- `target_success_rate`: 目标成功率（0-1）
- `target_throughput`: 目标吞吐量（RPS）

## 📈 性能指标

### 核心指标

1. **响应时间指标**
   - 平均响应时间
   - 中位数响应时间
   - 95%分位数响应时间
   - 99%分位数响应时间
   - 最大/最小响应时间

2. **吞吐量指标**
   - 每秒请求数 (RPS)
   - 每秒成功请求数
   - 总处理请求数

3. **可靠性指标**
   - 成功率
   - 错误率
   - 超时率

4. **资源使用指标**
   - 内存使用量（平均/峰值）
   - CPU使用率
   - 内存增长趋势

### 性能等级评定

- **A级 (90-100分)**: 优秀，所有指标均达到或超过目标
- **B级 (80-89分)**: 良好，大部分指标达标
- **C级 (70-79分)**: 一般，部分指标需要优化
- **D级 (60-69分)**: 较差，多项指标不达标
- **F级 (0-59分)**: 失败，系统性能严重不足

## 📋 测试报告

### 报告类型

1. **JSON报告**: 机器可读的详细测试数据
2. **HTML报告**: 人类友好的可视化报告
3. **综合报告**: 包含所有测试结果的汇总报告

### 报告内容

- **测试概览**: 总体测试结果和统计信息
- **性能评估**: 基于预设目标的性能等级评定
- **详细指标**: 每个测试的具体性能数据
- **问题识别**: 自动识别的性能问题和警告
- **优化建议**: 基于测试结果的性能优化建议
- **系统信息**: 测试环境的硬件和软件信息

## 🔧 开发指南

### 添加新的性能测试

1. **创建测试函数**:
```python
@pytest.mark.asyncio
async def test_new_performance_scenario(performance_monitor, mock_patent_agents):
    """新的性能测试场景"""
    # 测试逻辑
    pass
```

2. **添加基准配置**:
```json
{
  "test_name": "new_performance_test",
  "description": "新的性能测试描述",
  "enabled": true,
  // ... 其他配置
}
```

3. **更新测试套件**:
在 `run_performance_tests.py` 中添加新测试的处理逻辑。

### 自定义性能指标

```python
class CustomPerformanceMetrics:
    def __init__(self):
        self.custom_metric = 0
    
    def collect_metric(self, value):
        self.custom_metric = value
    
    def get_metrics(self):
        return {'custom_metric': self.custom_metric}
```

### 扩展报告格式

可以通过修改 `benchmark_runner.py` 中的报告生成方法来添加新的报告格式或自定义报告内容。

## 🚨 故障排除

### 常见问题

1. **测试超时**
   - 检查系统资源是否充足
   - 调整测试配置中的超时时间
   - 减少并发用户数或请求数量

2. **内存不足**
   - 监控系统内存使用
   - 调整测试参数减少内存压力
   - 检查是否存在内存泄漏

3. **测试失败率高**
   - 检查模拟Agent的配置
   - 验证测试环境的稳定性
   - 调整目标性能指标

### 调试技巧

1. **启用详细日志**:
```bash
uv run python tests/performance/run_performance_tests.py --verbose
```

2. **单独运行失败的测试**:
```bash
uv run pytest tests/performance/test_patent_performance.py::test_specific_function -v -s
```

3. **检查测试结果**:
查看 `tests/performance/results/` 目录下的详细报告。

## 📚 最佳实践

### 测试环境

1. **隔离测试环境**: 在专用的测试环境中运行性能测试
2. **稳定的硬件**: 使用配置一致的硬件环境
3. **最小化干扰**: 关闭不必要的后台进程

### 测试策略

1. **渐进式测试**: 从小负载开始，逐步增加压力
2. **重复测试**: 多次运行确保结果的一致性
3. **基线建立**: 建立性能基线用于回归检测

### 结果分析

1. **趋势分析**: 关注性能指标的变化趋势
2. **瓶颈识别**: 识别系统的性能瓶颈点
3. **优化验证**: 验证性能优化的效果

## 🔗 相关文档

- [专利系统设计文档](../../.kiro/specs/patent-mvp-system/design.md)
- [专利系统需求文档](../../.kiro/specs/patent-mvp-system/requirements.md)
- [专利系统任务清单](../../.kiro/specs/patent-mvp-system/tasks.md)

## 📞 支持

如果在使用性能测试套件时遇到问题，请：

1. 查看本文档的故障排除部分
2. 检查测试结果中的错误信息
3. 查看生成的HTML报告中的详细分析
4. 提交Issue并附上相关的测试报告