# PatentsView API 专利搜索智能体集成指南

## 概述

本指南介绍了如何将基于 PatentsView API 的专利搜索智能体集成到现有的 patent agent 体系中。PatentsView 是美国专利商标局（USPTO）提供的专利数据 API 服务，提供丰富的专利信息检索功能。

## 新增组件

### 1. 核心智能体
- **文件**: `src/multi_agent_service/patent/agents/patent_search.py`
- **类**: `PatentsViewSearchAgent`
- **功能**: 基于 PatentsView API 的专利搜索和数据检索

### 2. 数据模型
- **文件**: `src/multi_agent_service/patent/models/patentsview_data.py`
- **主要模型**:
  - `PatentRecord`: 专利基础信息
  - `PatentSummary`: 专利摘要
  - `PatentClaim`: 专利权利要求
  - `AssigneeRecord`: 专利权人信息
  - `InventorRecord`: 发明人信息
  - `CPCClass`, `IPCClass`: 专利分类信息
  - `PatentsViewSearchResult`: 搜索结果集合
  - `PatentsViewAPIResponse`: API 响应模型

### 3. 服务层
- **文件**: `src/multi_agent_service/patent/services/patentsview_service.py`
- **类**: `PatentsViewService`
- **功能**: PatentsView API 的底层调用和数据处理

### 4. 配置管理
- **文件**: `src/multi_agent_service/patent/config/patentsview_config.py`
- **主要配置**:
  - `PatentsViewAPIConfig`: API 基础配置
  - `PatentsViewEndpoints`: 端点定义
  - `PatentsViewQueryBuilder`: 查询构建器配置

## API 端点支持

### 专利文本相关
- `/g_brf_sum_text/`: 专利摘要文本
- `/g_claim/`: 专利权利要求
- `/g_detail_desc_text/`: 专利详细说明
- `/g_draw_desc_text/`: 专利附图说明

### 发布文本相关
- `/pg_brf_sum_text/`: 发布摘要文本
- `/pg_claim/`: 发布权利要求
- `/pg_detail_desc_text/`: 发布详细说明
- `/pg_draw_desc_text/`: 发布附图说明

### 专利信息相关
- `/patent/`: 专利基础信息
- `/publication/`: 专利发布信息
- `/assignee/`: 专利权人信息
- `/inventor/`: 发明人信息
- `/location/`: 地理位置信息

### 分类相关
- `/cpc_class/`, `/cpc_subclass/`, `/cpc_group/`: CPC 分类
- `/ipc/`: IPC 分类
- `/uspc_mainclass/`, `/uspc_subclass/`: USPC 分类
- `/wipo/`: WIPO 分类

### 引用相关
- `/patent/foreign_citation/`: 外国引用
- `/patent/us_application_citation/`: 美国申请引用
- `/patent/us_patent_citation/`: 美国专利引用
- `/patent/other_reference/`: 其他引用

## 配置说明

### 环境变量配置

```bash
# PatentsView API 配置
PATENT_VIEW_API_KEY=your_api_key_here  # API密钥
PATENT_VIEW_BASE_URL=https://search.patentsview.org/api/v1
PATENT_VIEW_TIMEOUT=30
PATENT_VIEW_MAX_RETRIES=3
PATENT_VIEW_RATE_LIMIT_DELAY=1.0
PATENT_VIEW_DEFAULT_PAGE_SIZE=100
PATENT_VIEW_MAX_PAGE_SIZE=1000
PATENT_VIEW_ENABLE_CACHE=true
PATENT_VIEW_CACHE_TTL=3600
PATENT_VIEW_ENABLE_REQUEST_LOGGING=true
PATENT_VIEW_LOG_LEVEL=INFO
```

### Agent 配置示例

```python
from src.multi_agent_service.models.config import AgentConfig
from src.multi_agent_service.models.enums import AgentType

config = AgentConfig(
    agent_id="patentsview_search_agent",
    agent_type=AgentType.PATENT_SEARCH,
    name="PatentsView搜索智能体",
    description="基于PatentsView API的专利搜索智能体",
    capabilities=["专利搜索", "数据检索", "API集成"],
    metadata={
        "patentsview_api": {
            "base_url": "https://search.patentsview.org/api/v1",
            "timeout": 30,
            "max_retries": 3,
            "rate_limit_delay": 1.0,
            "default_page_size": 100,
            "max_page_size": 1000
        }
    }
)
```

## 使用示例

### 1. 基本专利搜索

```python
from src.multi_agent_service.patent.agents.patent_search import PatentsViewSearchAgent
from src.multi_agent_service.patent.models.requests import PatentAnalysisRequest

# 创建搜索请求
request = PatentAnalysisRequest(
    request_id="search_001",
    keywords=["artificial intelligence", "machine learning"],
    analysis_types=["search", "comprehensive"],
    date_range={"start": "2020-01-01", "end": "2024-12-31"},
    countries=["US", "CN", "EP"],
    max_patents=500
)

# 创建并初始化智能体
agent = PatentsViewSearchAgent(config, model_client)
await agent.initialize()

# 处理搜索请求
response = await agent.process_request(request)
print(response.response_content)
```

### 2. 使用服务层直接调用

```python
from src.multi_agent_service.patent.services.patentsview_service import PatentsViewService

async with PatentsViewService() as service:
    # 搜索专利
    query = {
        "_text_any": {
            "patent_title": "artificial intelligence",
            "patent_abstract": "machine learning"
        }
    }
    
    response = await service.search_patents(query)
    patents = response.patents
    
    # 搜索专利摘要
    summaries_response = await service.search_patent_summaries(query)
    summaries = summaries_response.g_brf_sum_texts
    
    # 综合搜索
    search_result = await service.comprehensive_search(
        keywords=["AI", "ML"],
        date_range={"start": "2020-01-01", "end": "2024-12-31"},
        countries=["US"],
        max_results=100
    )
```

### 3. 查询构建

```python
from src.multi_agent_service.patent.services.patentsview_service import PatentsViewService

service = PatentsViewService()

# 文本搜索查询
text_query = service.build_text_search_query(
    keywords=["neural network", "deep learning"],
    search_fields=["patent_title", "patent_abstract"]
)

# 日期范围查询
date_query = service.build_date_range_query(
    start_date="2020-01-01",
    end_date="2024-12-31"
)

# 分类查询
classification_query = service.build_classification_query(
    ipc_classes=["G06F", "G06N"],
    cpc_classes=["G06F15", "G06N3"]
)

# 组合查询
combined_query = service.combine_queries(
    text_query, date_query, classification_query
)
```

## 集成到现有系统

### 1. 更新 Agent 注册

在 `src/multi_agent_service/patent/agents/__init__.py` 中已添加：

```python
from .patent_search import PatentsViewSearchAgent

__all__ = [
    "PatentBaseAgent",
    "PatentDataCollectionAgent",
    "PatentsViewSearchAgent"  # 新增
]
```

### 2. 更新模型导入

在 `src/multi_agent_service/patent/models/__init__.py` 中已添加 PatentsView 相关模型。

### 3. 更新服务注册

在 `src/multi_agent_service/patent/services/__init__.py` 中已添加：

```python
from .patentsview_service import PatentsViewService

__all__ = [
    # ... 其他服务
    "PatentsViewService"  # 新增
]
```

### 4. Agent 工厂集成

需要在 Agent 工厂中注册新的智能体类型：

```python
# 在相应的工厂类中添加
from src.multi_agent_service.patent.agents import PatentsViewSearchAgent

def create_patent_search_agent(config, model_client):
    return PatentsViewSearchAgent(config, model_client)
```

## 特性和优势

### 1. 丰富的数据源
- 美国专利商标局官方数据
- 实时更新的专利信息
- 多维度专利数据（文本、分类、引用等）

### 2. 灵活的查询能力
- 支持复杂的查询条件组合
- 文本搜索、日期范围、分类筛选
- 多字段联合搜索

### 3. 高性能设计
- 异步 API 调用
- 并行数据获取
- 智能缓存机制
- 错误重试和恢复

### 4. 标准化集成
- 遵循现有 Agent 架构
- 统一的数据模型
- 一致的错误处理

## 测试和验证

运行测试脚本验证集成：

```bash
python test_patentsview_agent.py
```

测试内容包括：
- 配置加载和验证
- 数据模型创建和序列化
- 服务层查询构建
- Agent 基本功能测试

## 注意事项

### 1. API 限制
- PatentsView API 可能有速率限制
- 某些端点可能需要 API 密钥
- 大量数据请求需要分页处理

### 2. 数据质量
- API 返回的数据可能不完整
- 需要进行数据质量评估
- 建议结合多个数据源

### 3. 网络依赖
- 需要稳定的网络连接
- 建议配置适当的超时和重试机制
- 考虑离线缓存策略

### 4. 性能考虑
- 大量并发请求可能影响性能
- 建议配置合适的请求间隔
- 使用缓存减少重复请求

## 扩展建议

### 1. 数据增强
- 结合其他专利数据源
- 添加专利价值评估
- 集成专利引用分析

### 2. 智能化功能
- 自动关键词扩展
- 智能分类推荐
- 相似专利发现

### 3. 可视化支持
- 专利趋势图表
- 技术领域分布
- 竞争对手分析

### 4. 实时监控
- API 调用监控
- 数据质量监控
- 性能指标跟踪

## 总结

PatentsView 专利搜索智能体为现有的 patent agent 体系提供了强大的专利数据检索能力。通过标准化的接口和灵活的配置，可以轻松集成到现有系统中，为专利分析提供更丰富、更准确的数据支持。