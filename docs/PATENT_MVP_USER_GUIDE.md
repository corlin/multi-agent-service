# Patent MVP System User Guide

## 目录

1. [系统概述](#系统概述)
2. [快速开始](#快速开始)
3. [系统架构](#系统架构)
4. [API接口文档](#api接口文档)
5. [Agent配置指南](#agent配置指南)
6. [工作流配置](#工作流配置)
7. [部署指南](#部署指南)
8. [故障排除](#故障排除)
9. [最佳实践](#最佳实践)
10. [性能优化](#性能优化)

## 系统概述

Patent MVP System是一个基于Multi-Agent-LangGraph架构的专利分析系统，提供全面的专利数据收集、分析和报告生成能力。

### 核心特性

- **多Agent协作**: 5个专业化Agent协同工作
- **智能搜索**: 集成CNKI学术搜索和博查AI搜索
- **数据收集**: 支持多种专利数据源
- **趋势分析**: 专利申请趋势和技术发展分析
- **竞争分析**: 申请人和市场竞争格局分析
- **报告生成**: 自动生成专业分析报告
- **可视化**: 丰富的图表和数据可视化

### 系统组件

1. **PatentCoordinatorAgent**: 协调整个分析流程
2. **PatentDataCollectionAgent**: 收集专利数据
3. **PatentSearchAgent**: 增强搜索和信息收集
4. **PatentAnalysisAgent**: 执行专利分析
5. **PatentReportAgent**: 生成分析报告

## 快速开始

### 环境要求

- Python 3.12+
- uv包管理器
- Redis (可选，用于缓存)
- PostgreSQL (生产环境)

### 安装步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd patent-mvp-system
   ```

2. **验证环境**
   ```bash
   # Linux/macOS
   ./scripts/validate-environment.sh
   
   # Windows
   .\scripts\validate-environment.ps1
   ```

3. **安装依赖**
   ```bash
   uv sync --dev
   ```

4. **配置环境变量**
   ```bash
   cp .env.example .env.development
   # 编辑 .env.development 配置必要的环境变量
   ```

5. **启动开发服务器**
   ```bash
   # Linux/macOS
   ./scripts/start-development.sh
   
   # Windows
   .\scripts\start-development.ps1
   ```

### 验证安装

访问以下URL验证系统正常运行：

- 应用主页: http://localhost:8000
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health
- 系统状态: http://localhost:8000/api/v1/system/status

## 系统架构

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Patent MVP System                        │
├─────────────────────────────────────────────────────────────┤
│  API Layer (FastAPI)                                       │
│  ├── Patent Analysis API                                   │
│  ├── Report Generation API                                 │
│  └── System Management API                                 │
├─────────────────────────────────────────────────────────────┤
│  Agent Layer                                               │
│  ├── PatentCoordinatorAgent                               │
│  ├── PatentDataCollectionAgent                            │
│  ├── PatentSearchAgent                                    │
│  ├── PatentAnalysisAgent                                  │
│  └── PatentReportAgent                                    │
├─────────────────────────────────────────────────────────────┤
│  Service Layer                                             │
│  ├── AgentRegistry                                        │
│  ├── WorkflowEngine                                       │
│  ├── ConfigManager                                        │
│  └── MonitoringSystem                                     │
├─────────────────────────────────────────────────────────────┤
│  Data Layer                                                │
│  ├── PostgreSQL/SQLite                                    │
│  ├── Redis Cache                                          │
│  └── File Storage                                         │
└─────────────────────────────────────────────────────────────┘
```

### Agent工作流

```mermaid
graph TD
    A[用户请求] --> B[PatentCoordinatorAgent]
    B --> C[PatentDataCollectionAgent]
    B --> D[PatentSearchAgent]
    C --> E[专利数据]
    D --> F[增强数据]
    E --> G[PatentAnalysisAgent]
    F --> G
    G --> H[分析结果]
    H --> I[PatentReportAgent]
    I --> J[分析报告]
    J --> K[返回用户]
```

## API接口文档

### 专利分析API

#### 提交分析请求

**POST** `/api/v1/patent/analyze`

请求体:
```json
{
  "keywords": ["人工智能", "机器学习"],
  "date_range": {
    "start_date": "2020-01-01",
    "end_date": "2024-12-31"
  },
  "analysis_types": ["trend", "competition", "technology"],
  "options": {
    "include_web_search": true,
    "include_academic_search": true,
    "max_patents": 1000
  }
}
```

响应:
```json
{
  "status": "success",
  "analysis_id": "analysis_12345",
  "message": "Analysis started successfully",
  "estimated_completion": "2024-01-15T10:30:00Z"
}
```

#### 查询分析状态

**GET** `/api/v1/patent/analyze/{analysis_id}/status`

响应:
```json
{
  "analysis_id": "analysis_12345",
  "status": "completed",
  "progress": 100,
  "current_stage": "report_generation",
  "results_available": true,
  "completion_time": "2024-01-15T10:25:00Z"
}
```

#### 获取分析结果

**GET** `/api/v1/patent/analyze/{analysis_id}/results`

响应:
```json
{
  "analysis_id": "analysis_12345",
  "results": {
    "trend_analysis": {
      "yearly_counts": {"2020": 150, "2021": 200, "2022": 280},
      "growth_rate": 0.35,
      "trend_direction": "increasing"
    },
    "competition_analysis": {
      "top_applicants": [
        {"name": "公司A", "count": 45},
        {"name": "公司B", "count": 32}
      ],
      "market_concentration": 0.65
    },
    "technology_analysis": {
      "main_categories": ["G06N", "G06F"],
      "keyword_clusters": [
        {"cluster": "深度学习", "patents": 120},
        {"cluster": "神经网络", "patents": 95}
      ]
    }
  }
}
```

### 报告生成API

#### 生成报告

**POST** `/api/v1/patent/reports/generate`

请求体:
```json
{
  "analysis_id": "analysis_12345",
  "report_type": "comprehensive",
  "format": "html",
  "options": {
    "include_charts": true,
    "include_raw_data": false,
    "language": "zh-CN"
  }
}
```

#### 下载报告

**GET** `/api/v1/patent/reports/{report_id}/download`

### 系统管理API

#### 系统状态

**GET** `/api/v1/system/status`

#### Agent状态

**GET** `/api/v1/agents/status`

#### 工作流状态

**GET** `/api/v1/workflows/status`

## Agent配置指南

### Agent配置文件结构

Agent配置文件位于 `config/patent_agents.json`:

```json
{
  "patent_coordinator_agent": {
    "class": "PatentCoordinatorAgent",
    "config": {
      "max_concurrent_tasks": 5,
      "timeout": 600,
      "retry_attempts": 3
    }
  },
  "patent_data_collection_agent": {
    "class": "PatentDataCollectionAgent",
    "config": {
      "data_sources": ["google_patents", "patents_view"],
      "cache_ttl": 7200,
      "batch_size": 100
    }
  },
  "patent_search_agent": {
    "class": "PatentSearchAgent",
    "config": {
      "search_engines": ["cnki", "bocha_ai"],
      "max_results_per_source": 50,
      "timeout": 30
    }
  },
  "patent_analysis_agent": {
    "class": "PatentAnalysisAgent",
    "config": {
      "analysis_types": ["trend", "competition", "technology"],
      "parallel_processing": true,
      "cache_results": true
    }
  },
  "patent_report_agent": {
    "class": "PatentReportAgent",
    "config": {
      "template_dir": "templates/patent",
      "output_formats": ["html", "pdf"],
      "chart_engine": "plotly"
    }
  }
}
```

### Agent配置参数说明

#### PatentCoordinatorAgent

- `max_concurrent_tasks`: 最大并发任务数
- `timeout`: 任务超时时间（秒）
- `retry_attempts`: 重试次数

#### PatentDataCollectionAgent

- `data_sources`: 数据源列表
- `cache_ttl`: 缓存生存时间（秒）
- `batch_size`: 批处理大小

#### PatentSearchAgent

- `search_engines`: 搜索引擎列表
- `max_results_per_source`: 每个源的最大结果数
- `timeout`: 搜索超时时间

#### PatentAnalysisAgent

- `analysis_types`: 分析类型列表
- `parallel_processing`: 是否启用并行处理
- `cache_results`: 是否缓存结果

#### PatentReportAgent

- `template_dir`: 模板目录
- `output_formats`: 输出格式列表
- `chart_engine`: 图表引擎

## 工作流配置

### 工作流配置文件

工作流配置文件位于 `config/patent_workflows.json`:

```json
{
  "patent_analysis_workflow": {
    "type": "sequential",
    "steps": [
      {
        "name": "data_collection",
        "agent": "patent_data_collection_agent",
        "timeout": 300
      },
      {
        "name": "search_enhancement",
        "agent": "patent_search_agent",
        "timeout": 180,
        "parallel": true
      },
      {
        "name": "analysis",
        "agent": "patent_analysis_agent",
        "timeout": 600
      },
      {
        "name": "report_generation",
        "agent": "patent_report_agent",
        "timeout": 300
      }
    ]
  },
  "patent_quick_analysis": {
    "type": "parallel",
    "agents": [
      "patent_data_collection_agent",
      "patent_search_agent"
    ],
    "merge_results": true,
    "timeout": 180
  }
}
```

### 工作流类型

1. **Sequential**: 顺序执行工作流
2. **Parallel**: 并行执行工作流
3. **Conditional**: 条件执行工作流

## 部署指南

### 开发环境部署

1. **使用脚本启动**
   ```bash
   # Linux/macOS
   ./scripts/start-development.sh
   
   # Windows
   .\scripts\start-development.ps1
   ```

2. **手动启动**
   ```bash
   uv run uvicorn src.multi_agent_service.main:app --reload --host 0.0.0.0 --port 8000
   ```

### 生产环境部署

#### 原生部署

1. **配置生产环境**
   ```bash
   cp .env.production.example .env.production
   # 编辑 .env.production
   ```

2. **启动生产服务**
   ```bash
   # Linux/macOS
   ./scripts/start-patent-production.sh
   
   # Windows
   .\scripts\start-patent-production.ps1
   ```

#### Docker部署

1. **使用Docker Compose**
   ```bash
   # 启动所有服务
   docker-compose up -d
   
   # 查看服务状态
   docker-compose ps
   
   # 查看日志
   docker-compose logs -f patent-service
   ```

2. **Windows Docker部署**
   ```bash
   docker-compose -f docker-compose.windows.yml up -d
   ```

### 环境变量配置

#### 必需环境变量

```bash
# 应用配置
APP_ENV=production
DATABASE_URL=postgresql://user:pass@localhost:5432/patent_db
REDIS_URL=redis://localhost:6379/0

# 外部API配置
CNKI_API_KEY=your_cnki_api_key
BOCHA_AI_API_KEY=your_bocha_ai_key
GOOGLE_PATENTS_API_KEY=your_google_patents_key
```

#### 可选环境变量

```bash
# 性能配置
PATENT_MAX_CONCURRENT_ANALYSES=5
PATENT_BATCH_SIZE=100
PATENT_CACHE_TTL=7200

# 监控配置
MONITORING_ENABLED=true
LOG_LEVEL=INFO
```

## 故障排除

### 常见问题

#### 1. uv命令未找到

**问题**: `uv: command not found`

**解决方案**:
```bash
# 安装uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### 2. 依赖安装失败

**问题**: `uv sync` 失败

**解决方案**:
```bash
# 清理缓存
uv cache clean

# 重新安装
uv sync --reinstall
```

#### 3. 数据库连接失败

**问题**: Database connection failed

**解决方案**:
1. 检查数据库服务是否运行
2. 验证连接字符串
3. 检查防火墙设置

#### 4. Redis连接失败

**问题**: Redis connection failed

**解决方案**:
1. 启动Redis服务
2. 检查Redis配置
3. 验证网络连接

#### 5. Agent初始化失败

**问题**: Agent initialization failed

**解决方案**:
1. 检查Agent配置文件
2. 验证依赖项
3. 查看详细错误日志

### 日志分析

#### 日志文件位置

- 应用日志: `logs/patent-mvp.log`
- 错误日志: `logs/patent-mvp-error.log`
- 访问日志: `logs/patent-mvp-access.log`

#### 常用日志命令

```bash
# 查看实时日志
tail -f logs/patent-mvp.log

# 搜索错误
grep "ERROR" logs/patent-mvp.log

# 查看最近的错误
tail -100 logs/patent-mvp-error.log
```

### 性能问题诊断

#### 内存使用过高

1. 检查Agent并发数配置
2. 调整缓存设置
3. 监控数据处理批次大小

#### 响应时间过长

1. 检查数据库查询性能
2. 优化缓存策略
3. 调整超时设置

## 最佳实践

### 配置管理

1. **环境分离**: 为不同环境使用不同的配置文件
2. **敏感信息**: 使用环境变量存储API密钥
3. **配置验证**: 启动时验证配置完整性

### 性能优化

1. **缓存策略**: 合理设置缓存TTL
2. **并发控制**: 根据系统资源调整并发数
3. **批处理**: 使用批处理提高数据处理效率

### 安全考虑

1. **API认证**: 启用API密钥认证
2. **访问控制**: 限制API访问频率
3. **数据加密**: 敏感数据传输加密

### 监控和维护

1. **健康检查**: 定期检查系统健康状态
2. **日志监控**: 监控错误日志和性能指标
3. **备份策略**: 定期备份重要数据

## 性能优化

### 系统级优化

#### 内存优化

```bash
# 调整Python内存设置
export PYTHONMALLOC=malloc
export MALLOC_ARENA_MAX=2
```

#### 并发优化

```python
# 在 .env 中配置
UVICORN_WORKERS=4
PATENT_MAX_CONCURRENT_ANALYSES=5
ASYNC_POOL_SIZE=20
```

### 应用级优化

#### 缓存优化

1. **Redis配置优化**
   ```bash
   # redis.conf
   maxmemory 512mb
   maxmemory-policy allkeys-lru
   ```

2. **应用缓存策略**
   ```python
   PATENT_DATA_CACHE_TTL=7200  # 2小时
   PATENT_ANALYSIS_CACHE_TTL=86400  # 24小时
   ```

#### 数据库优化

1. **索引优化**
   ```sql
   CREATE INDEX idx_patent_application_date ON patents(application_date);
   CREATE INDEX idx_patent_keywords ON patents USING gin(keywords);
   ```

2. **连接池配置**
   ```python
   DATABASE_POOL_SIZE=10
   DATABASE_MAX_OVERFLOW=20
   ```

### 监控指标

#### 关键性能指标

- 响应时间: < 2秒 (API调用)
- 吞吐量: > 100 请求/分钟
- 错误率: < 1%
- 内存使用: < 80%
- CPU使用: < 70%

#### 监控工具

1. **内置监控**
   - 访问 `/api/v1/monitoring/metrics`
   - 查看系统状态和性能指标

2. **外部监控**
   - Prometheus + Grafana
   - ELK Stack (Elasticsearch, Logstash, Kibana)

---

## 支持和反馈

如果您在使用过程中遇到问题或有改进建议，请：

1. 查看本文档的故障排除部分
2. 检查系统日志获取详细错误信息
3. 提交Issue到项目仓库
4. 联系技术支持团队

---

**版本**: 1.0.0  
**更新日期**: 2024年1月  
**维护团队**: Patent MVP Development Team