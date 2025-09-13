# Google Patents 中文关键词搜索使用说明

## 概述

优化后的 `final_google_patents_demo.py` 现在支持中文关键词搜索，能够自动将中文技术术语映射为对应的英文关键词，提高专利搜索的准确性和覆盖面。

## 主要功能

### 1. 中文关键词自动映射
- 支持30+个常用中文技术术语
- 自动扩展为多个相关英文关键词
- 提高搜索结果的准确性和完整性

### 2. 优化的搜索关键词
重点优化了以下热门技术领域：
- **具身智能**: embodied intelligence, embodied AI, physical AI, robotics intelligence
- **大语言模型**: large language model, LLM, transformer, GPT, BERT
- **客户细分**: customer segmentation, user profiling, market segmentation
- **多模态AI**: multimodal AI, vision language model, cross-modal
- **联邦学习**: federated learning, distributed learning, privacy-preserving learning

### 3. 灵活的配置系统
- 支持从 `chinese_keywords_config.json` 加载自定义映射
- 可以轻松添加新的中文关键词
- 支持热门搜索组合

## 使用方法

### 基本使用

```bash
# 运行完整演示（包含中文关键词搜索）
python final_google_patents_demo.py

# 快速测试中文关键词功能
python final_google_patents_demo.py --quick
```

### 自定义关键词映射

1. 编辑 `chinese_keywords_config.json` 文件
2. 在 "关键词映射" 部分添加新的中文关键词
3. 为每个中文关键词提供对应的英文关键词数组

示例：
```json
{
  "关键词映射": {
    "你的中文关键词": [
      "english keyword 1",
      "english keyword 2",
      "related term"
    ]
  }
}
```

### 程序化使用

```python
from final_google_patents_demo import get_chinese_keyword_mapping, expand_keywords_with_chinese

# 获取关键词映射
mapping = get_chinese_keyword_mapping()

# 扩展中文关键词
chinese_keywords = ["具身智能", "大语言模型"]
expanded_keywords = expand_keywords_with_chinese(chinese_keywords, mapping)

print(f"扩展后的关键词: {expanded_keywords}")
```

## 演示内容

### 1. 完整功能演示
- 具身智能专利搜索（5个结果）
- 大语言模型专利搜索（5个结果）
- 客户细分专利搜索（4个结果）
- 多模态AI专利搜索（4个结果）
- 智能推荐系统专利搜索（3个结果）
- 计算机视觉专利搜索（3个结果）
- 自然语言处理专利搜索（3个结果）
- 高级搜索演示（带日期和申请人过滤）

### 2. 中文关键词专门演示
- 专门测试中文关键词映射功能
- 展示关键词扩展过程
- 验证搜索结果质量

### 3. 服务特性演示
- 不同初始化选项测试
- 搜索配置展示
- 错误处理机制验证

## 输出文件

运行演示后会生成以下文件：
- `google_patents_demo_results_YYYYMMDD_HHMMSS.json`: 完整演示结果
- `chinese_keywords_patents_YYYYMMDD_HHMMSS.json`: 中文关键词搜索结果

## 支持的中文关键词

### AI核心技术
- 具身智能, 大语言模型, 多模态AI, 深度学习, 机器学习, 人工智能

### 应用领域
- 客户细分, 推荐系统, 计算机视觉, 自然语言处理, 语音识别, 情感分析

### 算法技术
- 强化学习, 联邦学习, 聚类分析, 分类算法, 回归分析, 异常检测

### 基础设施
- 边缘计算, 云计算, 区块链, 物联网, 数据挖掘, 优化算法

### 安全隐私
- 加密技术, 隐私保护, 异常检测

## 性能优化

1. **搜索间隔**: 每次搜索间隔1-2秒，避免被限制
2. **结果限制**: 合理设置每次搜索的结果数量
3. **超时设置**: 60秒超时，适应网络环境
4. **错误处理**: 完善的异常处理和重试机制

## 扩展建议

1. **添加更多领域**: 可以扩展到医疗、金融、制造等特定行业
2. **语义匹配**: 考虑使用词向量或语义相似度进行更智能的关键词扩展
3. **结果过滤**: 根据专利质量、引用次数等指标过滤结果
4. **批量处理**: 支持批量关键词文件处理

## 故障排除

### 常见问题

1. **搜索结果为空**
   - 检查网络连接
   - 尝试更通用的关键词
   - 检查关键词映射是否正确

2. **程序运行缓慢**
   - 减少搜索结果数量限制
   - 检查网络延迟
   - 考虑使用更快的网络环境

3. **关键词映射不生效**
   - 检查 `chinese_keywords_config.json` 文件格式
   - 确认文件编码为UTF-8
   - 查看日志中的警告信息

### 调试模式

启用详细日志：
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 更新日志

### v1.0 (2025-01-13)
- 添加中文关键词自动映射功能
- 优化搜索关键词，重点关注热门技术领域
- 添加配置文件支持
- 增加快速测试模式
- 完善错误处理和日志记录

## 联系支持

如有问题或建议，请查看项目文档或提交issue。