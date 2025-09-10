# Patent MVP System 文档中心

欢迎使用Patent MVP System文档中心！这里包含了系统的完整文档，帮助您快速上手和深入了解系统功能。

## 📚 文档目录

### 🚀 快速开始
- **[用户指南](PATENT_MVP_USER_GUIDE.md)** - 完整的用户使用指南
  - 系统概述和核心特性
  - 快速安装和配置
  - 系统架构详解
  - Agent配置和工作流
  - 最佳实践和性能优化

### 🔧 技术文档
- **[API参考文档](API_REFERENCE.md)** - 详细的API接口文档
  - 专利分析API
  - 报告生成API
  - 系统管理API
  - 配置管理API
  - SDK和示例代码

- **[部署指南](DEPLOYMENT_GUIDE.md)** - 全面的部署指南
  - 开发环境部署
  - 生产环境部署
  - Docker容器化部署
  - 云平台部署 (AWS, Azure, GCP)
  - 配置管理和安全设置

### 🛠️ 运维文档
- **[故障排除指南](TROUBLESHOOTING_GUIDE.md)** - 运维和故障排除
  - 常见问题诊断
  - 系统监控和日志分析
  - 性能调优
  - 备份和恢复
  - 应急响应

## 🎯 文档使用指南

### 新用户推荐阅读顺序

1. **首次使用**
   - 阅读 [用户指南](PATENT_MVP_USER_GUIDE.md) 的"快速开始"部分
   - 按照步骤完成环境验证和系统安装
   - 验证系统正常运行

2. **深入了解**
   - 学习系统架构和Agent工作流
   - 了解API接口和使用方法
   - 掌握配置管理和最佳实践

3. **生产部署**
   - 参考 [部署指南](DEPLOYMENT_GUIDE.md) 进行生产环境部署
   - 配置监控和日志系统
   - 实施安全措施

4. **运维管理**
   - 学习 [故障排除指南](TROUBLESHOOTING_GUIDE.md)
   - 建立监控和告警机制
   - 制定备份和应急响应计划

### 开发者推荐阅读顺序

1. **API开发**
   - 详细阅读 [API参考文档](API_REFERENCE.md)
   - 了解认证机制和错误处理
   - 使用SDK进行开发

2. **系统集成**
   - 学习Agent配置和工作流定制
   - 了解外部API集成方法
   - 掌握数据模型和接口规范

3. **部署和运维**
   - 选择合适的部署方式
   - 配置CI/CD流水线
   - 实施监控和日志收集

## 📋 系统概览

### 核心功能

- **🔍 智能搜索**: 集成CNKI学术搜索和博查AI搜索
- **📊 数据分析**: 专利趋势、竞争格局、技术分类分析
- **📈 可视化**: 丰富的图表和数据可视化
- **📄 报告生成**: 自动生成专业分析报告
- **🤖 多Agent协作**: 5个专业化Agent协同工作
- **⚡ 高性能**: 基于uv和异步架构的高性能系统

### 技术栈

- **后端**: Python 3.12+, FastAPI, uv包管理
- **数据库**: PostgreSQL, Redis
- **容器化**: Docker, Docker Compose
- **监控**: Prometheus, Grafana
- **部署**: 支持多种部署方式

## 🔗 快速链接

### 常用操作

| 操作 | 链接 |
|------|------|
| 快速安装 | [用户指南 - 快速开始](PATENT_MVP_USER_GUIDE.md#快速开始) |
| API调用示例 | [API参考 - SDK示例](API_REFERENCE.md#sdk和示例) |
| Docker部署 | [部署指南 - Docker部署](DEPLOYMENT_GUIDE.md#docker部署) |
| 故障诊断 | [故障排除 - 常见问题](TROUBLESHOOTING_GUIDE.md#常见问题诊断) |

### 配置文件

| 文件 | 用途 | 位置 |
|------|------|------|
| `.env.development` | 开发环境配置 | 项目根目录 |
| `.env.production` | 生产环境配置 | 项目根目录 |
| `config/patent_agents.json` | Agent配置 | config目录 |
| `config/patent_workflows.json` | 工作流配置 | config目录 |

### 重要端点

| 端点 | 用途 | 文档链接 |
|------|------|----------|
| `/health` | 健康检查 | [API参考](API_REFERENCE.md#健康检查) |
| `/docs` | API文档 | 系统自动生成 |
| `/api/v1/patent/analyze` | 专利分析 | [API参考](API_REFERENCE.md#专利分析api) |
| `/api/v1/system/status` | 系统状态 | [API参考](API_REFERENCE.md#系统管理api) |

## 🆘 获取帮助

### 问题排查步骤

1. **检查系统状态**
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8000/api/v1/system/status
   ```

2. **查看日志**
   ```bash
   tail -f logs/patent-mvp.log
   tail -f logs/patent-mvp-error.log
   ```

3. **运行诊断脚本**
   ```bash
   # Linux/macOS
   ./scripts/validate-environment.sh
   
   # Windows
   .\scripts\validate-environment.ps1
   ```

4. **查阅相关文档**
   - 查看 [故障排除指南](TROUBLESHOOTING_GUIDE.md) 中的相关章节
   - 搜索错误信息和解决方案

### 支持渠道

- **文档**: 本文档中心包含了详细的使用和故障排除信息
- **日志**: 系统日志提供了详细的错误信息和调试信息
- **健康检查**: 使用内置的健康检查端点监控系统状态
- **社区**: 查看项目仓库的Issues和讨论区

## 📝 文档贡献

### 文档结构

```
docs/
├── README.md                    # 文档中心首页 (本文件)
├── PATENT_MVP_USER_GUIDE.md    # 用户指南
├── API_REFERENCE.md            # API参考文档
├── DEPLOYMENT_GUIDE.md         # 部署指南
└── TROUBLESHOOTING_GUIDE.md    # 故障排除指南
```

### 贡献指南

1. **文档更新**
   - 保持文档与代码同步
   - 使用清晰的标题和结构
   - 提供实际的示例代码

2. **格式规范**
   - 使用Markdown格式
   - 遵循现有的文档风格
   - 包含必要的代码高亮

3. **内容要求**
   - 准确性: 确保信息准确无误
   - 完整性: 提供完整的操作步骤
   - 实用性: 包含实际可用的示例

## 🔄 文档版本

| 版本 | 发布日期 | 主要更新 |
|------|----------|----------|
| 1.0.0 | 2024-01 | 初始版本，包含完整的用户指南、API文档、部署指南和故障排除指南 |

## 📊 文档统计

- **总页数**: 4个主要文档
- **总字数**: 约50,000字
- **代码示例**: 100+个
- **配置示例**: 50+个
- **故障排除场景**: 30+个

## 🎉 开始使用

准备好开始使用Patent MVP System了吗？

1. **新用户**: 从 [用户指南](PATENT_MVP_USER_GUIDE.md) 开始
2. **开发者**: 查看 [API参考文档](API_REFERENCE.md)
3. **运维人员**: 参考 [部署指南](DEPLOYMENT_GUIDE.md)
4. **遇到问题**: 查阅 [故障排除指南](TROUBLESHOOTING_GUIDE.md)

---

**💡 提示**: 建议将本文档中心加入书签，以便随时查阅。所有文档都支持全文搜索，您可以使用浏览器的搜索功能快速找到所需信息。

---

**版本**: 1.0.0  
**更新日期**: 2024年1月  
**维护团队**: Patent MVP Documentation Team