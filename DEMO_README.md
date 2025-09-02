# 多智能体服务演示程序

本目录包含了多个演示程序，展示多智能体LangGraph服务的各种功能。

## 🚀 快速开始

### 1. 环境准备

确保已安装Python 3.12+和uv包管理器：

```bash
# 安装依赖
uv sync

# 复制环境配置文件
cp .env.example .env
```

### 2. 配置API密钥

编辑 `.env` 文件，配置至少一个AI服务提供商的API密钥：

```env
# 至少配置一个
QWEN_API_KEY=your_qwen_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key  
GLM_API_KEY=your_glm_api_key
OPENAI_API_KEY=your_openai_api_key
```

### 3. 运行演示

**推荐方式 - 使用启动器：**
```bash
python run_demo.py
```

**或直接运行特定演示：**
```bash
# 快速演示（无需启动服务）
python quick_demo.py

# API演示（需要先启动服务）
python api_demo.py

# 交互式演示（自动启动服务）
python interactive_demo.py

# 综合演示（模型服务演示）
python comprehensive_demo.py
```

## 📋 演示程序说明

### 1. run_demo.py - 演示启动器
- 🎯 **功能**: 统一的演示启动入口
- 🔧 **特性**: 环境检查、菜单选择、服务管理
- 💡 **推荐**: 首次使用推荐从这里开始

### 2. quick_demo.py - 快速演示
- 🎯 **功能**: 展示核心功能，无需启动HTTP服务
- 🔧 **特性**: 配置加载、意图分析、智能体路由
- ⚡ **优势**: 快速验证系统基础功能
- 📝 **适用**: 开发调试、功能验证

### 3. api_demo.py - API演示
- 🎯 **功能**: 完整的HTTP API接口测试
- 🔧 **特性**: 所有REST API端点测试
- 🌐 **要求**: 需要服务运行在 http://localhost:8000
- 📝 **适用**: API集成测试、接口验证

### 4. interactive_demo.py - 交互式演示
- 🎯 **功能**: 包含交互式聊天的完整演示
- 🔧 **特性**: 自动启动服务、实时对话
- 💬 **亮点**: 可以与智能体进行实时对话
- 📝 **适用**: 功能展示、用户体验测试

### 5. comprehensive_demo.py - 综合演示
- 🎯 **功能**: 多提供商AI模型服务演示
- 🔧 **特性**: 负载均衡、故障转移、性能监控
- 🧠 **重点**: 底层模型路由和管理
- 📝 **适用**: 模型服务测试、性能评估

## 🔧 服务启动

如果需要手动启动服务：

```bash
# 开发模式（自动重载）
uv run uvicorn src.multi_agent_service.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uv run uvicorn src.multi_agent_service.main:app --host 0.0.0.0 --port 8000 --workers 4
```

服务启动后可访问：
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/api/v1/health

## 📊 演示内容

### 核心功能演示
- ✅ 系统健康检查
- ✅ 配置文件加载
- ✅ 智能体信息查询
- ✅ 意图分析功能
- ✅ 智能体路由
- ✅ 工作流执行

### API接口演示
- ✅ `/api/v1/health` - 健康检查
- ✅ `/api/v1/chat/completions` - OpenAI兼容聊天接口
- ✅ `/api/v1/agents/route` - 智能体路由
- ✅ `/api/v1/agents/status` - 智能体状态
- ✅ `/api/v1/agents/types` - 智能体类型
- ✅ `/api/v1/workflows/execute` - 工作流执行

### 智能体类型
- 🤖 **销售代表智能体** - 产品咨询、报价
- 🛠️ **客服专员智能体** - 问题解答、技术支持  
- 🔧 **现场服务人员智能体** - 技术服务、现场支持
- 👔 **管理者智能体** - 决策分析、战略规划
- 🎯 **协调员智能体** - 任务协调、智能体管理

### 工作流类型
- 📋 **Sequential** - 顺序执行工作流
- ⚡ **Parallel** - 并行执行工作流  
- 🏗️ **Hierarchical** - 分层管理工作流

## 🐛 故障排除

### 常见问题

1. **服务启动失败**
   ```bash
   # 检查端口占用
   netstat -an | grep 8000
   
   # 检查Python版本
   python --version
   ```

2. **API密钥错误**
   ```bash
   # 检查环境变量
   python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('QWEN_API_KEY:', os.getenv('QWEN_API_KEY')[:10] if os.getenv('QWEN_API_KEY') else 'Not set')"
   ```

3. **依赖包缺失**
   ```bash
   # 重新安装依赖
   uv sync --reinstall
   ```

4. **配置文件问题**
   ```bash
   # 检查配置文件
   ls -la config/
   python -c "import json; print(json.load(open('config/agents.json')))"
   ```

### 日志查看

```bash
# 查看服务日志
tail -f logs/multi_agent_service.log

# 查看错误日志  
grep "ERROR" logs/multi_agent_service.log
```

## 📚 更多信息

- 📖 **完整文档**: [README.md](README.md)
- 🔧 **配置说明**: [config/](config/)
- 🧪 **测试用例**: [tests/](tests/)
- 📋 **部署指南**: [docs/deployment_guide.md](docs/deployment_guide.md)

## 🤝 贡献

欢迎提交Issue和Pull Request来改进演示程序！

---

**享受多智能体协作的强大功能！** 🚀