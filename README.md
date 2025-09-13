# Multi-Agent LangGraph Service

基于LangGraph和FastAPI的多智能体协作后台服务系统，提供企业级的智能体协同工作平台。

## 🌟 功能特性

- 🤖 **多智能体协作**: 支持多个专业角色智能体协同工作
- 🔀 **智能路由**: 基于意图识别的智能体路由系统  
- 🔄 **多种协作模式**: Sequential、Parallel、Hierarchical
- 🌐 **OpenAI兼容API**: 支持多种大语言模型服务提供商
- 📊 **监控与日志**: 完整的系统监控和日志记录
- ⚙️ **灵活配置**: 支持动态配置和热更新
- 🔥 **热重载**: 支持配置和智能体的热重载
- 🛡️ **容错机制**: 完善的故障转移和异常处理
- 🌐 **浏览器自动化**: 集成browser-use技术，支持Google Patents等网站的智能访问
- 📊 **专利数据收集**: 支持多数据源的专利信息收集和分析

## 🛠️ 技术栈

- **Python**: 3.12+
- **Web框架**: FastAPI
- **AI框架**: LangGraph
- **包管理**: uv
- **异步处理**: asyncio
- **数据验证**: Pydantic
- **日志系统**: 结构化JSON日志
- **监控**: 内置性能指标收集
- **浏览器自动化**: browser-use + Playwright
- **专利数据**: PatentsView API + Google Patents

## 🚀 快速开始

### 环境要求

- Python 3.12+
- uv (Python包管理器)
- Windows/Linux/macOS

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd multi-agent-service
```

2. **安装依赖**
```bash
uv sync
```

3. **配置环境变量**
```bash
cp .env.example .env
```

编辑 `.env` 文件，配置必要的环境变量：
```env
# 模型API配置
QWEN_API_KEY=your_qwen_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
GLM_API_KEY=your_glm_api_key
OPENAI_API_KEY=your_openai_api_key

# 服务配置
HOST=0.0.0.0
PORT=8000
DEBUG=true

# 日志配置
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### 运行服务

```bash
# 开发模式（自动重载）
uv run uvicorn src.multi_agent_service.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uv run uvicorn src.multi_agent_service.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 验证安装

访问以下端点验证服务是否正常运行：

- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/api/v1/health
- **根路径**: http://localhost:8000/

## 📖 使用指南

### 基本API调用

#### 1. 智能体对话接口

```bash
curl -X POST "http://localhost:8000/api/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "我想了解你们的产品价格"}
    ],
    "model": "multi-agent-service"
  }'
```

#### 2. 智能体路由接口

```bash
curl -X POST "http://localhost:8000/api/v1/agents/route" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "我需要技术支持",
    "user_id": "user123",
    "priority": "high"
  }'
```

#### 3. 工作流执行接口

```bash
curl -X POST "http://localhost:8000/api/v1/workflows/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_type": "sequential",
    "task_description": "处理客户投诉",
    "participating_agents": ["customer_support", "manager"]
  }'
```

### 智能体角色说明

| 智能体 | 职责 | 适用场景 |
|--------|------|----------|
| **智能体总协调员** | 统筹管理其他智能体，制定协作策略 | 复杂任务分解、资源调度 |
| **销售代表智能体** | 处理销售相关询问和业务 | 产品咨询、报价、客户关系管理 |
| **公司管理者智能体** | 处理管理决策和战略规划 | 决策分析、资源配置、政策制定 |
| **现场服务人员智能体** | 处理现场服务和技术支持 | 故障诊断、维修指导、服务调度 |
| **客服专员智能体** | 处理客户咨询和问题解决 | 问题诊断、解决方案提供、客户安抚 |

### 协作模式详解

#### Sequential（顺序模式）
智能体按照预定顺序依次执行任务，适用于有明确步骤依赖的场景。

```python
# 示例：客户投诉处理流程
# 客服专员 → 现场服务人员 → 管理者 → 销售代表
```

#### Parallel（并行模式）
多个智能体同时并行处理不同任务，适用于可以并行处理的独立任务。

```python
# 示例：产品发布准备
# 销售代表（准备营销材料） || 现场服务人员（准备技术文档） || 管理者（制定策略）
```

#### Hierarchical（分层模式）
分层管理结构，由协调员智能体统筹管理，适用于复杂的多层级任务。

```python
# 示例：大型项目管理
# 协调员智能体
# ├── 销售团队（销售代表）
# ├── 技术团队（现场服务人员）
# └── 管理团队（管理者）
```

## 🔧 开发指南

### 项目结构

```
multi-agent-service/
├── src/multi_agent_service/
│   ├── main.py                 # FastAPI应用入口
│   ├── api/                    # API路由定义
│   │   ├── chat.py            # 聊天接口
│   │   ├── agents.py          # 智能体接口
│   │   └── workflows.py       # 工作流接口
│   ├── agents/                 # 智能体实现
│   │   ├── base.py            # 基础智能体类
│   │   ├── sales_agent.py     # 销售智能体
│   │   └── ...
│   ├── workflows/              # 工作流引擎
│   │   ├── sequential.py      # 顺序工作流
│   │   ├── parallel.py        # 并行工作流
│   │   └── hierarchical.py    # 分层工作流
│   ├── services/               # 核心服务
│   │   ├── intent_analyzer.py # 意图识别
│   │   ├── agent_router.py    # 智能体路由
│   │   └── model_router.py    # 模型路由
│   ├── models/                 # 数据模型
│   ├── utils/                  # 工具函数
│   └── config/                 # 配置管理
├── tests/                      # 测试代码
├── config/                     # 配置文件
└── docs/                       # 文档
```

### 开发环境设置

```bash
# 安装开发依赖
uv sync --dev

# 运行测试
uv run pytest tests/ -v

# 代码格式化
uv run black src/ tests/
uv run isort src/ tests/

# 类型检查
uv run mypy src/

# 代码质量检查
uv run flake8 src/ tests/
```

### 添加新智能体

1. 创建智能体类：
```python
# src/multi_agent_service/agents/my_agent.py
from .base import BaseAgent

class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="my_agent_001",
            agent_type=AgentType.CUSTOM,
            name="我的智能体",
            description="自定义智能体描述"
        )
    
    async def process_request(self, request: AgentRequest) -> AgentResponse:
        # 实现具体的处理逻辑
        pass
```

2. 注册智能体：
```python
# 在 agents/registry.py 中注册
registry.register_agent(MyAgent())
```

### 配置管理

系统支持多层级配置：

1. **环境变量** (最高优先级)
2. **配置文件** (`config/`)
3. **默认配置** (代码中定义)

配置文件示例：
```json
{
  "agents": {
    "sales_agent": {
      "enabled": true,
      "model": "qwen-turbo",
      "max_tokens": 2000,
      "temperature": 0.7
    }
  },
  "models": {
    "qwen-turbo": {
      "provider": "qwen",
      "base_url": "https://dashscope.aliyuncs.com/api/v1",
      "api_key": "${QWEN_API_KEY}"
    }
  }
}
```

## 📊 监控和日志

### 日志系统

系统使用结构化JSON日志，支持以下日志级别：
- `DEBUG`: 调试信息
- `INFO`: 一般信息
- `WARNING`: 警告信息
- `ERROR`: 错误信息
- `CRITICAL`: 严重错误

日志示例：
```json
{
  "timestamp": "2025-09-02T17:00:47.061997",
  "level": "INFO",
  "category": "api",
  "message": "Request started: POST /api/v1/agents/route",
  "logger_name": "multi_agent_service.api",
  "context": {
    "method": "POST",
    "url": "http://localhost:8000/api/v1/agents/route",
    "user_id": "user123"
  },
  "request_id": "3f78c13e-6c7e-46a1-9fdf-c01876c79a09"
}
```

### 性能监控

系统内置性能指标收集：
- API请求响应时间
- 智能体执行时间
- 系统资源使用情况
- 错误率统计

访问监控接口：
```bash
curl http://localhost:8000/api/v1/monitoring/metrics
```

## 🚀 部署指南

### Docker部署

1. 构建镜像：
```bash
docker build -t multi-agent-service .
```

2. 运行容器：
```bash
docker run -d \
  --name multi-agent-service \
  -p 8000:8000 \
  -e QWEN_API_KEY=your_key \
  -e DEEPSEEK_API_KEY=your_key \
  multi-agent-service
```

### 生产环境部署

1. 使用进程管理器（如Supervisor）：
```ini
[program:multi-agent-service]
command=uv run uvicorn src.multi_agent_service.main:app --host 0.0.0.0 --port 8000 --workers 4
directory=/path/to/multi-agent-service
user=www-data
autostart=true
autorestart=true
```

2. 使用反向代理（Nginx）：
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🔍 故障排除

### 常见问题

1. **服务启动失败**
   - 检查Python版本是否为3.12+
   - 确认所有依赖已正确安装
   - 检查端口是否被占用

2. **API调用失败**
   - 验证API密钥配置
   - 检查网络连接
   - 查看日志文件获取详细错误信息

3. **智能体响应异常**
   - 检查模型服务状态
   - 验证配置文件格式
   - 查看智能体日志

### 日志查看

```bash
# 查看实时日志
tail -f logs/multi_agent_service.log

# 查看错误日志
grep "ERROR" logs/multi_agent_service.log

# 查看特定请求的日志
grep "request_id" logs/multi_agent_service.log
```

## 🧪 测试

### 运行测试套件

```bash
# 运行所有测试
uv run pytest tests/ -v

# 运行特定测试文件
uv run pytest tests/test_agents_api.py -v

# 运行覆盖率测试
uv run pytest tests/ --cov=src --cov-report=html
```

### 测试分类

- **单元测试**: 测试单个组件功能
- **集成测试**: 测试组件间交互
- **端到端测试**: 测试完整业务流程
- **性能测试**: 测试系统性能指标

## 📚 API文档

完整的API文档可通过以下方式访问：

1. **Swagger UI**: http://localhost:8000/docs
2. **ReDoc**: http://localhost:8000/redoc
3. **OpenAPI JSON**: http://localhost:8000/openapi.json

### 主要API端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/chat/completions` | POST | OpenAI兼容的聊天接口 |
| `/api/v1/agents/route` | POST | 智能体路由接口 |
| `/api/v1/agents/status` | GET | 智能体状态查询 |
| `/api/v1/agents/types` | GET | 获取智能体类型列表 |
| `/api/v1/workflows/execute` | POST | 执行工作流 |
| `/api/v1/workflows/{id}/status` | GET | 查询工作流状态 |
| `/api/v1/config/agents` | GET/POST | 智能体配置管理 |
| `/api/v1/monitoring/metrics` | GET | 系统监控指标 |
| `/api/v1/health` | GET | 健康检查 |

## 🤝 贡献指南

我们欢迎社区贡献！请遵循以下步骤：

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

### 代码规范

- 遵循PEP 8代码风格
- 添加适当的类型注解
- 编写单元测试
- 更新相关文档

## 📄 许可证

本项目采用 [MIT License](LICENSE) 许可证。

## 📞 支持

如果您遇到问题或有疑问，请：

1. 查看[FAQ文档](docs/FAQ.md)
2. 搜索[已有Issues](https://github.com/your-repo/issues)
3. 创建新的Issue描述问题
4. 联系维护团队

---

**Multi-Agent LangGraph Service** - 让智能体协作变得简单高效！ 🚀
#
# 🔍 Google Patents Browser-Use 集成

本项目已集成browser-use技术来优化Google Patents的数据收集功能。

### 快速设置

1. **安装browser-use依赖**
```bash
python setup_browser_use.py
```

2. **运行测试**
```bash
python test_google_patents_browser.py
```

3. **查看演示**
```bash
python demo_google_patents_browser.py
```

### 主要优势

- ✅ **真实浏览器环境**: 完全支持JavaScript渲染
- ✅ **反爬虫能力**: 模拟真实用户行为
- ✅ **动态内容支持**: 处理AJAX和动态加载
- ✅ **详细信息提取**: 深入专利详情页面

### 使用示例

```python
from multi_agent_service.patent.services.google_patents_browser import GooglePatentsBrowserService

async def collect_patents():
    async with GooglePatentsBrowserService(headless=True) as browser_service:
        patents = await browser_service.search_patents(
            keywords=["artificial intelligence"],
            limit=50,
            date_range={"start_year": "2022", "end_year": "2024"}
        )
        return patents
```

### 详细文档

查看 [Google Patents Browser-Use 集成指南](GOOGLE_PATENTS_BROWSER_USE_README.md) 获取完整的使用说明和配置选项。

---

*最后更新: 2024年12月*