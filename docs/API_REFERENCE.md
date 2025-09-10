# Patent MVP System API Reference

## 概述

Patent MVP System提供RESTful API接口，支持专利数据分析、报告生成和系统管理功能。所有API都基于HTTP协议，使用JSON格式进行数据交换。

## 基础信息

- **Base URL**: `http://localhost:8000` (开发环境)
- **API版本**: v1
- **认证方式**: API Key (生产环境)
- **内容类型**: `application/json`
- **字符编码**: UTF-8

## 认证

### API Key认证 (生产环境)

在请求头中包含API密钥：

```http
Authorization: Bearer YOUR_API_KEY
```

### 获取API Key

```http
POST /api/v1/auth/token
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

## 专利分析API

### 1. 提交分析请求

创建新的专利分析任务。

**端点**: `POST /api/v1/patent/analyze`

**请求体**:
```json
{
  "keywords": ["人工智能", "机器学习", "深度学习"],
  "date_range": {
    "start_date": "2020-01-01",
    "end_date": "2024-12-31"
  },
  "analysis_types": ["trend", "competition", "technology", "geographic"],
  "options": {
    "include_web_search": true,
    "include_academic_search": true,
    "max_patents": 1000,
    "language": "zh-CN",
    "priority": "normal"
  }
}
```

**参数说明**:

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| keywords | array | 是 | 搜索关键词列表 |
| date_range | object | 否 | 日期范围 |
| date_range.start_date | string | 否 | 开始日期 (YYYY-MM-DD) |
| date_range.end_date | string | 否 | 结束日期 (YYYY-MM-DD) |
| analysis_types | array | 否 | 分析类型列表 |
| options | object | 否 | 分析选项 |
| options.include_web_search | boolean | 否 | 是否包含网页搜索 |
| options.include_academic_search | boolean | 否 | 是否包含学术搜索 |
| options.max_patents | integer | 否 | 最大专利数量 |
| options.language | string | 否 | 语言设置 |
| options.priority | string | 否 | 任务优先级 |

**响应**:
```json
{
  "status": "success",
  "analysis_id": "analysis_20240115_001",
  "message": "Analysis request submitted successfully",
  "estimated_completion": "2024-01-15T10:30:00Z",
  "queue_position": 1
}
```

**状态码**:
- `200 OK`: 请求成功
- `400 Bad Request`: 请求参数错误
- `401 Unauthorized`: 认证失败
- `429 Too Many Requests`: 请求频率过高

### 2. 查询分析状态

获取分析任务的当前状态和进度。

**端点**: `GET /api/v1/patent/analyze/{analysis_id}/status`

**路径参数**:
- `analysis_id`: 分析任务ID

**响应**:
```json
{
  "analysis_id": "analysis_20240115_001",
  "status": "in_progress",
  "progress": 65,
  "current_stage": "analysis",
  "stages": {
    "data_collection": {
      "status": "completed",
      "progress": 100,
      "completion_time": "2024-01-15T10:15:00Z"
    },
    "search_enhancement": {
      "status": "completed", 
      "progress": 100,
      "completion_time": "2024-01-15T10:18:00Z"
    },
    "analysis": {
      "status": "in_progress",
      "progress": 65,
      "estimated_completion": "2024-01-15T10:25:00Z"
    },
    "report_generation": {
      "status": "pending",
      "progress": 0
    }
  },
  "results_available": false,
  "created_at": "2024-01-15T10:10:00Z",
  "updated_at": "2024-01-15T10:20:00Z"
}
```

**状态值**:
- `pending`: 等待处理
- `in_progress`: 正在处理
- `completed`: 已完成
- `failed`: 处理失败
- `cancelled`: 已取消

### 3. 获取分析结果

获取完成的分析结果。

**端点**: `GET /api/v1/patent/analyze/{analysis_id}/results`

**查询参数**:
- `format`: 结果格式 (`json`, `csv`) - 可选
- `include_raw_data`: 是否包含原始数据 (`true`, `false`) - 可选

**响应**:
```json
{
  "analysis_id": "analysis_20240115_001",
  "status": "completed",
  "completion_time": "2024-01-15T10:25:00Z",
  "results": {
    "summary": {
      "total_patents": 856,
      "date_range": {
        "start_date": "2020-01-01",
        "end_date": "2024-12-31"
      },
      "keywords": ["人工智能", "机器学习", "深度学习"],
      "analysis_duration": "00:15:23"
    },
    "trend_analysis": {
      "yearly_counts": {
        "2020": 120,
        "2021": 185,
        "2022": 245,
        "2023": 306
      },
      "growth_rate": 0.42,
      "trend_direction": "increasing",
      "peak_year": "2023",
      "forecast": {
        "2024": 380,
        "confidence": 0.85
      }
    },
    "competition_analysis": {
      "top_applicants": [
        {
          "name": "腾讯科技有限公司",
          "count": 45,
          "percentage": 5.3,
          "trend": "increasing"
        },
        {
          "name": "阿里巴巴集团",
          "count": 38,
          "percentage": 4.4,
          "trend": "stable"
        }
      ],
      "market_concentration": {
        "hhi_index": 0.12,
        "top_5_share": 0.23,
        "top_10_share": 0.35
      },
      "geographic_distribution": {
        "CN": 456,
        "US": 234,
        "JP": 89,
        "KR": 45,
        "DE": 32
      }
    },
    "technology_analysis": {
      "ipc_distribution": {
        "G06N": 234,
        "G06F": 189,
        "G06K": 123,
        "H04L": 98
      },
      "keyword_clusters": [
        {
          "cluster": "深度学习",
          "patents": 156,
          "keywords": ["深度学习", "神经网络", "卷积网络"],
          "growth_rate": 0.65
        },
        {
          "cluster": "自然语言处理",
          "patents": 98,
          "keywords": ["NLP", "文本分析", "语言模型"],
          "growth_rate": 0.45
        }
      ],
      "emerging_technologies": [
        {
          "technology": "大语言模型",
          "patents": 45,
          "growth_rate": 2.3,
          "emergence_year": "2022"
        }
      ]
    },
    "insights": [
      "人工智能专利申请呈现强劲增长趋势，年均增长率达42%",
      "深度学习技术是当前最热门的研究方向",
      "中国在该领域的专利申请量领先全球",
      "大语言模型是新兴的技术热点"
    ]
  }
}
```

### 4. 取消分析任务

取消正在进行的分析任务。

**端点**: `DELETE /api/v1/patent/analyze/{analysis_id}`

**响应**:
```json
{
  "status": "success",
  "message": "Analysis task cancelled successfully",
  "analysis_id": "analysis_20240115_001"
}
```

### 5. 获取分析历史

获取用户的分析历史记录。

**端点**: `GET /api/v1/patent/analyze/history`

**查询参数**:
- `page`: 页码 (默认: 1)
- `limit`: 每页数量 (默认: 20, 最大: 100)
- `status`: 状态筛选 (`completed`, `failed`, `in_progress`)
- `date_from`: 开始日期
- `date_to`: 结束日期

**响应**:
```json
{
  "total": 156,
  "page": 1,
  "limit": 20,
  "analyses": [
    {
      "analysis_id": "analysis_20240115_001",
      "keywords": ["人工智能", "机器学习"],
      "status": "completed",
      "created_at": "2024-01-15T10:10:00Z",
      "completion_time": "2024-01-15T10:25:00Z",
      "total_patents": 856
    }
  ]
}
```

## 报告生成API

### 1. 生成报告

基于分析结果生成报告。

**端点**: `POST /api/v1/patent/reports/generate`

**请求体**:
```json
{
  "analysis_id": "analysis_20240115_001",
  "report_type": "comprehensive",
  "format": "html",
  "options": {
    "include_charts": true,
    "include_raw_data": false,
    "language": "zh-CN",
    "template": "default",
    "custom_title": "人工智能专利分析报告"
  }
}
```

**参数说明**:

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| analysis_id | string | 是 | 分析任务ID |
| report_type | string | 否 | 报告类型 |
| format | string | 否 | 输出格式 |
| options | object | 否 | 报告选项 |

**报告类型**:
- `summary`: 摘要报告
- `comprehensive`: 综合报告
- `trend_focus`: 趋势分析报告
- `competition_focus`: 竞争分析报告

**输出格式**:
- `html`: HTML格式
- `pdf`: PDF格式
- `docx`: Word文档格式

**响应**:
```json
{
  "status": "success",
  "report_id": "report_20240115_001",
  "message": "Report generation started",
  "estimated_completion": "2024-01-15T10:35:00Z"
}
```

### 2. 查询报告状态

**端点**: `GET /api/v1/patent/reports/{report_id}/status`

**响应**:
```json
{
  "report_id": "report_20240115_001",
  "status": "completed",
  "progress": 100,
  "file_size": 2048576,
  "download_url": "/api/v1/patent/reports/report_20240115_001/download",
  "expires_at": "2024-01-22T10:35:00Z"
}
```

### 3. 下载报告

**端点**: `GET /api/v1/patent/reports/{report_id}/download`

**查询参数**:
- `format`: 下载格式 (如果报告支持多种格式)

**响应**: 文件下载流

### 4. 获取报告列表

**端点**: `GET /api/v1/patent/reports`

**查询参数**:
- `page`: 页码
- `limit`: 每页数量
- `analysis_id`: 分析ID筛选

**响应**:
```json
{
  "total": 45,
  "page": 1,
  "limit": 20,
  "reports": [
    {
      "report_id": "report_20240115_001",
      "analysis_id": "analysis_20240115_001",
      "report_type": "comprehensive",
      "format": "html",
      "status": "completed",
      "created_at": "2024-01-15T10:30:00Z",
      "file_size": 2048576,
      "download_count": 3
    }
  ]
}
```

## 系统管理API

### 1. 系统状态

获取系统整体状态信息。

**端点**: `GET /api/v1/system/status`

**响应**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": "2d 14h 32m",
  "timestamp": "2024-01-15T10:30:00Z",
  "components": {
    "database": {
      "status": "healthy",
      "response_time": 12,
      "connections": {
        "active": 5,
        "max": 20
      }
    },
    "redis": {
      "status": "healthy",
      "response_time": 2,
      "memory_usage": "45%"
    },
    "agents": {
      "status": "healthy",
      "active_agents": 5,
      "total_agents": 5
    },
    "workflows": {
      "status": "healthy",
      "active_workflows": 2,
      "queued_tasks": 3
    }
  },
  "performance": {
    "cpu_usage": "35%",
    "memory_usage": "68%",
    "disk_usage": "42%"
  }
}
```

### 2. 健康检查

**端点**: `GET /health`

**响应**:
```json
{
  "status": "ok",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 3. Agent状态

**端点**: `GET /api/v1/agents/status`

**响应**:
```json
{
  "agents": [
    {
      "agent_id": "patent_coordinator_agent",
      "status": "active",
      "last_activity": "2024-01-15T10:29:00Z",
      "tasks_completed": 156,
      "average_response_time": 2.3
    },
    {
      "agent_id": "patent_data_collection_agent", 
      "status": "active",
      "last_activity": "2024-01-15T10:28:00Z",
      "tasks_completed": 89,
      "average_response_time": 15.6
    }
  ]
}
```

### 4. 工作流状态

**端点**: `GET /api/v1/workflows/status`

**响应**:
```json
{
  "workflows": [
    {
      "workflow_id": "patent_analysis_workflow",
      "status": "active",
      "running_instances": 2,
      "queued_instances": 1,
      "completed_today": 45
    }
  ]
}
```

### 5. 监控指标

**端点**: `GET /api/v1/monitoring/metrics`

**查询参数**:
- `metric`: 指标名称
- `time_range`: 时间范围 (`1h`, `24h`, `7d`, `30d`)
- `granularity`: 数据粒度 (`minute`, `hour`, `day`)

**响应**:
```json
{
  "metrics": {
    "api_requests": {
      "total": 15678,
      "success_rate": 0.987,
      "average_response_time": 245
    },
    "analysis_tasks": {
      "completed": 234,
      "failed": 3,
      "average_duration": 892
    },
    "system_resources": {
      "cpu_usage": [
        {"timestamp": "2024-01-15T10:00:00Z", "value": 35.2},
        {"timestamp": "2024-01-15T10:05:00Z", "value": 42.1}
      ],
      "memory_usage": [
        {"timestamp": "2024-01-15T10:00:00Z", "value": 67.8},
        {"timestamp": "2024-01-15T10:05:00Z", "value": 68.2}
      ]
    }
  }
}
```

## 配置管理API

### 1. 获取配置

**端点**: `GET /api/v1/config/{config_type}`

**路径参数**:
- `config_type`: 配置类型 (`agents`, `workflows`, `system`)

**响应**:
```json
{
  "config_type": "agents",
  "version": "1.2.3",
  "last_updated": "2024-01-15T09:00:00Z",
  "config": {
    "patent_coordinator_agent": {
      "class": "PatentCoordinatorAgent",
      "config": {
        "max_concurrent_tasks": 5,
        "timeout": 600
      }
    }
  }
}
```

### 2. 更新配置

**端点**: `PUT /api/v1/config/{config_type}`

**请求体**:
```json
{
  "config": {
    "patent_coordinator_agent": {
      "config": {
        "max_concurrent_tasks": 8,
        "timeout": 900
      }
    }
  },
  "reload": true
}
```

**响应**:
```json
{
  "status": "success",
  "message": "Configuration updated successfully",
  "version": "1.2.4",
  "reload_required": false
}
```

## 错误处理

### 错误响应格式

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Invalid analysis request parameters",
    "details": {
      "field": "keywords",
      "issue": "Keywords array cannot be empty"
    },
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_20240115_001"
  }
}
```

### 错误代码

| 代码 | HTTP状态 | 说明 |
|------|----------|------|
| INVALID_REQUEST | 400 | 请求参数无效 |
| UNAUTHORIZED | 401 | 认证失败 |
| FORBIDDEN | 403 | 权限不足 |
| NOT_FOUND | 404 | 资源不存在 |
| RATE_LIMITED | 429 | 请求频率过高 |
| INTERNAL_ERROR | 500 | 内部服务器错误 |
| SERVICE_UNAVAILABLE | 503 | 服务不可用 |

## 限制和配额

### API限制

- **请求频率**: 100 请求/分钟 (认证用户)
- **并发分析**: 5个并发分析任务
- **文件大小**: 最大10MB上传
- **结果保留**: 分析结果保留30天

### 数据限制

- **关键词数量**: 最多10个关键词
- **专利数量**: 单次分析最多10,000个专利
- **日期范围**: 最大20年时间跨度

## SDK和示例

### Python SDK示例

```python
import requests

class PatentMVPClient:
    def __init__(self, base_url, api_key=None):
        self.base_url = base_url
        self.headers = {'Content-Type': 'application/json'}
        if api_key:
            self.headers['Authorization'] = f'Bearer {api_key}'
    
    def analyze_patents(self, keywords, **options):
        data = {
            'keywords': keywords,
            'options': options
        }
        response = requests.post(
            f'{self.base_url}/api/v1/patent/analyze',
            json=data,
            headers=self.headers
        )
        return response.json()
    
    def get_analysis_status(self, analysis_id):
        response = requests.get(
            f'{self.base_url}/api/v1/patent/analyze/{analysis_id}/status',
            headers=self.headers
        )
        return response.json()

# 使用示例
client = PatentMVPClient('http://localhost:8000')
result = client.analyze_patents(['人工智能', '机器学习'])
print(f"Analysis ID: {result['analysis_id']}")
```

### JavaScript SDK示例

```javascript
class PatentMVPClient {
    constructor(baseUrl, apiKey = null) {
        this.baseUrl = baseUrl;
        this.headers = {
            'Content-Type': 'application/json'
        };
        if (apiKey) {
            this.headers['Authorization'] = `Bearer ${apiKey}`;
        }
    }
    
    async analyzePatents(keywords, options = {}) {
        const response = await fetch(`${this.baseUrl}/api/v1/patent/analyze`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({
                keywords: keywords,
                options: options
            })
        });
        return await response.json();
    }
    
    async getAnalysisStatus(analysisId) {
        const response = await fetch(
            `${this.baseUrl}/api/v1/patent/analyze/${analysisId}/status`,
            { headers: this.headers }
        );
        return await response.json();
    }
}

// 使用示例
const client = new PatentMVPClient('http://localhost:8000');
const result = await client.analyzePatents(['人工智能', '机器学习']);
console.log(`Analysis ID: ${result.analysis_id}`);
```

---

**版本**: 1.0.0  
**更新日期**: 2024年1月  
**维护团队**: Patent MVP Development Team