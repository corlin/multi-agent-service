# 真实环境测试场景

基于 `validate_patent_system.py` 开发的综合性真实环境测试工具，用于全面验证专利分析系统在真实环境下的功能、性能和稳定性。

## 🎯 测试目标

- **功能完整性**: 验证所有核心功能正常工作
- **性能基准**: 确保系统性能满足预期标准
- **稳定性**: 验证长时间运行的稳定性
- **可靠性**: 测试故障恢复和容错能力
- **可扩展性**: 验证大数据量处理能力
- **集成性**: 确保各组件协同工作正常

## 📁 文件结构

```
├── test_real_environment_scenarios.py    # 主测试脚本
├── run_real_environment_test.py          # 简化运行脚本
├── real_environment_test_config.json     # 测试配置文件
├── generate_test_data.py                 # 测试数据生成器
├── REAL_ENVIRONMENT_TEST_README.md       # 本说明文档
└── test_data/                            # 测试数据目录（自动生成）
    ├── patent_test_data.json
    ├── query_scenarios.json
    └── performance_test_data.json
```

## 🚀 快速开始

### 1. 生成测试数据

```bash
# 生成测试数据
python generate_test_data.py
```

### 2. 运行测试

```bash
# 快速测试（仅关键功能）
python run_real_environment_test.py --mode quick

# 标准测试（推荐）
python run_real_environment_test.py --mode standard

# 完整测试（包含长时间稳定性测试）
python run_real_environment_test.py --mode full

# 自定义测试
python run_real_environment_test.py --mode custom --categories system functionality performance
```

### 3. 直接运行主测试脚本

```bash
# 运行完整测试套件
python test_real_environment_scenarios.py

# 使用 uv 运行
uv run python test_real_environment_scenarios.py
```

## 📊 测试场景详解

### 1. 系统基础功能测试
- **目标**: 验证系统启动和初始化
- **内容**: 
  - 系统组件初始化
  - Agent注册验证
  - 健康检查
- **预期时间**: 30秒
- **成功标准**: 所有组件正常启动

### 2. 基础专利查询测试
- **目标**: 验证简单查询功能
- **内容**:
  - 关键词查询
  - 响应质量检查
  - 基本功能验证
- **预期时间**: 15秒
- **成功标准**: 查询成功，置信度 > 0.7

### 3. 复杂专利分析工作流测试
- **目标**: 验证多Agent协作分析
- **内容**:
  - 全流程工作流执行
  - 多阶段协作验证
  - 分析质量评估
- **预期时间**: 120秒
- **成功标准**: 工作流完成，分析质量 > 0.8

### 4. 并发处理测试
- **目标**: 验证并发处理能力
- **内容**:
  - 多请求并发执行
  - 资源使用监控
  - 响应时间统计
- **预期时间**: 60秒
- **成功标准**: 成功率 > 90%，平均响应时间 < 20秒

### 5. 大数据处理测试
- **目标**: 验证大数据集处理能力
- **内容**:
  - 批量数据处理
  - 内存效率监控
  - 处理速度测试
- **预期时间**: 180秒
- **成功标准**: 处理速度 > 100专利/秒，内存使用合理

### 6. 故障恢复测试
- **目标**: 验证系统容错能力
- **内容**:
  - 超时故障模拟
  - 内存压力测试
  - Agent故障恢复
- **预期时间**: 60秒
- **成功标准**: 故障检测和恢复成功

### 7. API接口集成测试
- **目标**: 验证API接口完整性
- **内容**:
  - 端点可访问性
  - 响应格式验证
  - 错误处理测试
- **预期时间**: 30秒
- **成功标准**: 所有端点正常响应

### 8. 长时间稳定性测试
- **目标**: 验证长期运行稳定性
- **内容**:
  - 持续请求处理
  - 内存泄漏检测
  - 性能稳定性监控
- **预期时间**: 300秒（可配置）
- **成功标准**: 无内存泄漏，性能稳定

## ⚙️ 配置说明

### 性能基准配置
```json
{
  "performance_baselines": {
    "system_startup_time": 30.0,      // 系统启动时间基准（秒）
    "simple_query_time": 10.0,        // 简单查询时间基准（秒）
    "complex_analysis_time": 120.0,   // 复杂分析时间基准（秒）
    "memory_usage_mb": 1024,          // 内存使用基准（MB）
    "cpu_usage_percent": 80           // CPU使用基准（%）
  }
}
```

### 测试场景配置
```json
{
  "test_scenarios_config": {
    "system_tests": {
      "enabled": true,                // 是否启用
      "timeout_multiplier": 1.0,      // 超时倍数
      "retry_count": 1                // 重试次数
    }
  }
}
```

## 📈 测试报告

测试完成后会生成以下报告文件：

### 1. 详细报告 (`real_environment_test_report.json`)
```json
{
  "overall_status": "PASS",
  "test_statistics": {
    "total_tests": 8,
    "passed_tests": 7,
    "failed_tests": 1,
    "success_rate": 0.875
  },
  "performance_statistics": {
    "average_execution_time": 45.2,
    "max_execution_time": 120.5
  },
  "detailed_results": [...]
}
```

### 2. 简化报告 (`real_environment_test_summary.json`)
```json
{
  "test_date": "2023-12-01T10:30:00",
  "overall_status": "PASS",
  "success_rate": 0.875,
  "failed_tests": [
    {
      "name": "长时间稳定性测试",
      "error": "内存使用超过阈值"
    }
  ]
}
```

### 3. 日志文件 (`real_environment_test.log`)
包含详细的执行日志和调试信息。

## 🔧 自定义测试

### 添加新的测试场景

1. 在 `test_real_environment_scenarios.py` 中的 `_define_test_scenarios()` 方法添加新场景
2. 实现对应的测试方法
3. 更新配置文件中的相关设置

### 修改性能基准

编辑 `real_environment_test_config.json` 中的 `performance_baselines` 部分。

### 自定义测试数据

修改 `generate_test_data.py` 中的数据生成逻辑。

## 🚨 故障排除

### 常见问题

1. **导入模块失败**
   ```
   解决方案: 确保在项目根目录运行，检查Python路径设置
   ```

2. **系统初始化失败**
   ```
   解决方案: 检查环境变量配置，确保所需服务正常运行
   ```

3. **测试超时**
   ```
   解决方案: 调整配置文件中的超时设置，或检查系统性能
   ```

4. **内存使用过高**
   ```
   解决方案: 减少并发数量，优化数据处理逻辑
   ```

### 调试模式

```bash
# 启用详细输出
python run_real_environment_test.py --mode quick --verbose

# 查看日志
tail -f real_environment_test.log
```

## 📋 最佳实践

### 测试前准备
1. 确保系统资源充足（内存 > 2GB，磁盘空间 > 1GB）
2. 关闭不必要的后台程序
3. 检查网络连接稳定性
4. 备份重要数据

### 测试执行
1. 从快速测试开始，逐步增加复杂度
2. 监控系统资源使用情况
3. 记录异常情况和性能数据
4. 定期清理临时文件

### 结果分析
1. 重点关注关键测试的失败情况
2. 分析性能趋势和瓶颈
3. 对比历史测试结果
4. 制定优化改进计划

## 🔄 持续集成

### 集成到CI/CD流程

```yaml
# GitHub Actions 示例
- name: Run Real Environment Tests
  run: |
    python generate_test_data.py
    python run_real_environment_test.py --mode standard
    
- name: Upload Test Reports
  uses: actions/upload-artifact@v2
  with:
    name: test-reports
    path: |
      real_environment_test_report.json
      real_environment_test_summary.json
      real_environment_test.log
```

### 定期测试建议
- **每日**: 快速测试
- **每周**: 标准测试
- **每月**: 完整测试（包含稳定性测试）
- **发布前**: 全面测试验证

## 📞 支持

如遇到问题或需要帮助：

1. 查看日志文件获取详细错误信息
2. 检查配置文件设置是否正确
3. 参考现有的测试用例和文档
4. 联系开发团队获取技术支持

---

**真实环境测试工具** - 确保专利分析系统在真实环境下的可靠运行！ 🚀