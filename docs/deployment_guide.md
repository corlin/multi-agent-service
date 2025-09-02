# 部署指南

## 概述

本文档提供了Multi-Agent LangGraph Service的完整部署指南，包括开发环境、测试环境和生产环境的部署方案。

## 环境要求

### 系统要求
- **操作系统**: Windows 10+, Ubuntu 18.04+, macOS 10.15+
- **Python版本**: 3.12+
- **内存**: 最小4GB，推荐8GB+
- **磁盘空间**: 最小2GB可用空间
- **网络**: 需要访问外部API服务

### 依赖软件
- **uv**: Python包管理器
- **Git**: 版本控制
- **Docker** (可选): 容器化部署
- **Nginx** (生产环境): 反向代理
- **Supervisor** (生产环境): 进程管理

## 开发环境部署

### 1. 环境准备

```bash
# 安装uv (如果尚未安装)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 验证安装
uv --version
```

### 2. 项目设置

```bash
# 克隆项目
git clone <repository-url>
cd multi-agent-service

# 创建虚拟环境并安装依赖
uv sync

# 复制环境变量模板
cp .env.example .env
```

### 3. 配置环境变量

编辑 `.env` 文件：

```env
# 开发环境配置
DEBUG=true
LOG_LEVEL=DEBUG
HOST=127.0.0.1
PORT=8000

# 模型API配置
QWEN_API_KEY=your_qwen_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
GLM_API_KEY=your_glm_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# 数据库配置 (如果使用)
DATABASE_URL=sqlite:///./dev.db

# 日志配置
LOG_FORMAT=json
LOG_FILE=logs/multi_agent_service.log
```

### 4. 启动开发服务器

```bash
# 启动开发服务器（自动重载）
uv run uvicorn src.multi_agent_service.main:app --reload --host 127.0.0.1 --port 8000

# 或使用快捷脚本
uv run python -m src.multi_agent_service.main --dev
```

### 5. 验证部署

```bash
# 健康检查
curl http://localhost:8000/api/v1/health

# 查看API文档
open http://localhost:8000/docs
```

## 测试环境部署

### 1. 环境配置

```env
# 测试环境配置
DEBUG=false
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000

# 使用测试API密钥
QWEN_API_KEY=test_qwen_key
DEEPSEEK_API_KEY=test_deepseek_key
GLM_API_KEY=test_glm_key
OPENAI_API_KEY=test_openai_key

# 测试数据库
DATABASE_URL=sqlite:///./test.db
```

### 2. 运行测试

```bash
# 运行完整测试套件
uv run pytest tests/ -v

# 运行集成测试
uv run pytest tests/test_*_integration.py -v

# 生成测试报告
uv run pytest tests/ --html=reports/test_report.html --self-contained-html
```

### 3. 启动测试服务

```bash
# 启动测试服务器
uv run uvicorn src.multi_agent_service.main:app --host 0.0.0.0 --port 8000
```

## 生产环境部署

### 方案一：直接部署

#### 1. 系统准备

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3.12 python3.12-venv git nginx supervisor

# CentOS/RHEL
sudo yum update
sudo yum install -y python3.12 python3.12-venv git nginx supervisor
```

#### 2. 用户和目录设置

```bash
# 创建应用用户
sudo useradd -m -s /bin/bash multiagent
sudo usermod -aG sudo multiagent

# 创建应用目录
sudo mkdir -p /opt/multi-agent-service
sudo chown multiagent:multiagent /opt/multi-agent-service

# 切换到应用用户
sudo su - multiagent
```

#### 3. 应用部署

```bash
# 进入应用目录
cd /opt/multi-agent-service

# 克隆代码
git clone <repository-url> .

# 安装uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# 安装依赖
uv sync --frozen
```

#### 4. 生产环境配置

```bash
# 创建生产环境配置
cat > .env << EOF
# 生产环境配置
DEBUG=false
LOG_LEVEL=INFO
HOST=127.0.0.1
PORT=8000

# 模型API配置
QWEN_API_KEY=${QWEN_API_KEY}
DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
GLM_API_KEY=${GLM_API_KEY}
OPENAI_API_KEY=${OPENAI_API_KEY}

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost/multiagent

# 安全配置
SECRET_KEY=${SECRET_KEY}
ALLOWED_HOSTS=your-domain.com,localhost

# 日志配置
LOG_FORMAT=json
LOG_FILE=/var/log/multi-agent-service/app.log
EOF
```

#### 5. Supervisor配置

```bash
# 创建Supervisor配置
sudo cat > /etc/supervisor/conf.d/multi-agent-service.conf << EOF
[program:multi-agent-service]
command=/home/multiagent/.local/bin/uv run uvicorn src.multi_agent_service.main:app --host 127.0.0.1 --port 8000 --workers 4
directory=/opt/multi-agent-service
user=multiagent
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/multi-agent-service/supervisor.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=5
environment=PATH="/home/multiagent/.local/bin:%(ENV_PATH)s"

[program:multi-agent-worker]
command=/home/multiagent/.local/bin/uv run python -m src.multi_agent_service.worker
directory=/opt/multi-agent-service
user=multiagent
autostart=true
autorestart=true
numprocs=2
process_name=%(program_name)s_%(process_num)02d
redirect_stderr=true
stdout_logfile=/var/log/multi-agent-service/worker.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=5
environment=PATH="/home/multiagent/.local/bin:%(ENV_PATH)s"
EOF

# 创建日志目录
sudo mkdir -p /var/log/multi-agent-service
sudo chown multiagent:multiagent /var/log/multi-agent-service

# 重新加载Supervisor配置
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start multi-agent-service
```

#### 6. Nginx配置

```bash
# 创建Nginx配置
sudo cat > /etc/nginx/sites-available/multi-agent-service << EOF
server {
    listen 80;
    server_name your-domain.com;
    
    # 重定向到HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL配置
    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
    
    # 日志配置
    access_log /var/log/nginx/multi-agent-service.access.log;
    error_log /var/log/nginx/multi-agent-service.error.log;
    
    # 客户端配置
    client_max_body_size 10M;
    client_body_timeout 60s;
    client_header_timeout 60s;
    
    # 代理配置
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # 超时配置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # 缓冲配置
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }
    
    # 静态文件缓存
    location /static/ {
        alias /opt/multi-agent-service/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # 健康检查
    location /health {
        proxy_pass http://127.0.0.1:8000/api/v1/health;
        access_log off;
    }
}
EOF

# 启用站点
sudo ln -s /etc/nginx/sites-available/multi-agent-service /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 方案二：Docker部署

#### 1. 创建Dockerfile

```dockerfile
# Dockerfile
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 安装uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# 复制项目文件
COPY . .

# 安装Python依赖
RUN uv sync --frozen

# 创建非root用户
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# 启动命令
CMD ["uv", "run", "uvicorn", "src.multi_agent_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. 创建docker-compose.yml

```yaml
# docker-compose.yml
version: '3.8'

services:
  multi-agent-service:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=false
      - LOG_LEVEL=INFO
      - QWEN_API_KEY=${QWEN_API_KEY}
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - GLM_API_KEY=${GLM_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./logs:/app/logs
      - ./config:/app/config
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - multi-agent-service
    restart: unless-stopped

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

#### 3. 部署命令

```bash
# 构建和启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f multi-agent-service

# 扩展服务实例
docker-compose up -d --scale multi-agent-service=3

# 更新服务
docker-compose pull
docker-compose up -d
```

### 方案三：Kubernetes部署

#### 1. 创建Kubernetes配置

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: multi-agent-service

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: multi-agent-config
  namespace: multi-agent-service
data:
  DEBUG: "false"
  LOG_LEVEL: "INFO"
  HOST: "0.0.0.0"
  PORT: "8000"

---
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: multi-agent-secrets
  namespace: multi-agent-service
type: Opaque
data:
  QWEN_API_KEY: <base64-encoded-key>
  DEEPSEEK_API_KEY: <base64-encoded-key>
  GLM_API_KEY: <base64-encoded-key>
  OPENAI_API_KEY: <base64-encoded-key>

---
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: multi-agent-service
  namespace: multi-agent-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: multi-agent-service
  template:
    metadata:
      labels:
        app: multi-agent-service
    spec:
      containers:
      - name: multi-agent-service
        image: multi-agent-service:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: multi-agent-config
        - secretRef:
            name: multi-agent-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: multi-agent-service
  namespace: multi-agent-service
spec:
  selector:
    app: multi-agent-service
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP

---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: multi-agent-ingress
  namespace: multi-agent-service
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - your-domain.com
    secretName: multi-agent-tls
  rules:
  - host: your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: multi-agent-service
            port:
              number: 80
```

#### 2. 部署到Kubernetes

```bash
# 应用配置
kubectl apply -f k8s/

# 查看部署状态
kubectl get pods -n multi-agent-service

# 查看日志
kubectl logs -f deployment/multi-agent-service -n multi-agent-service

# 扩展副本
kubectl scale deployment multi-agent-service --replicas=5 -n multi-agent-service
```

## 监控和日志

### 1. 日志配置

```bash
# 配置日志轮转
sudo cat > /etc/logrotate.d/multi-agent-service << EOF
/var/log/multi-agent-service/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 multiagent multiagent
    postrotate
        supervisorctl restart multi-agent-service
    endscript
}
EOF
```

### 2. 监控配置

```bash
# 安装监控工具
pip install prometheus-client grafana-api

# 配置Prometheus监控端点
# 在应用中添加 /metrics 端点
```

### 3. 健康检查脚本

```bash
#!/bin/bash
# health_check.sh

SERVICE_URL="http://localhost:8000/api/v1/health"
TIMEOUT=10

response=$(curl -s -w "%{http_code}" -o /dev/null --max-time $TIMEOUT $SERVICE_URL)

if [ "$response" = "200" ]; then
    echo "Service is healthy"
    exit 0
else
    echo "Service is unhealthy (HTTP $response)"
    exit 1
fi
```

## 安全配置

### 1. 防火墙配置

```bash
# Ubuntu/Debian
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# CentOS/RHEL
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 2. SSL证书配置

```bash
# 使用Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo crontab -e
# 添加: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 3. 安全加固

```bash
# 禁用root SSH登录
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart ssh

# 配置fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

## 备份和恢复

### 1. 数据备份

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/multi-agent-service"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份应用代码
tar -czf $BACKUP_DIR/app_$DATE.tar.gz /opt/multi-agent-service

# 备份配置文件
tar -czf $BACKUP_DIR/config_$DATE.tar.gz /etc/nginx/sites-available/multi-agent-service /etc/supervisor/conf.d/multi-agent-service.conf

# 备份数据库（如果使用）
pg_dump multiagent > $BACKUP_DIR/db_$DATE.sql

# 清理旧备份（保留30天）
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
```

### 2. 恢复流程

```bash
#!/bin/bash
# restore.sh

BACKUP_FILE=$1
RESTORE_DIR="/opt/multi-agent-service"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

# 停止服务
sudo supervisorctl stop multi-agent-service

# 恢复应用
sudo tar -xzf $BACKUP_FILE -C /

# 重新安装依赖
cd $RESTORE_DIR
uv sync

# 启动服务
sudo supervisorctl start multi-agent-service
```

## 性能优化

### 1. 应用层优化

```python
# 配置连接池
UVICORN_CONFIG = {
    "workers": 4,
    "worker_class": "uvicorn.workers.UvicornWorker",
    "max_requests": 1000,
    "max_requests_jitter": 100,
    "timeout": 60,
    "keepalive": 2
}
```

### 2. 系统层优化

```bash
# 调整系统参数
echo "net.core.somaxconn = 65535" >> /etc/sysctl.conf
echo "net.ipv4.tcp_max_syn_backlog = 65535" >> /etc/sysctl.conf
echo "fs.file-max = 100000" >> /etc/sysctl.conf
sysctl -p

# 调整ulimit
echo "* soft nofile 65535" >> /etc/security/limits.conf
echo "* hard nofile 65535" >> /etc/security/limits.conf
```

## 故障排除

### 常见问题

1. **服务无法启动**
   ```bash
   # 检查日志
   sudo supervisorctl tail -f multi-agent-service
   
   # 检查端口占用
   sudo netstat -tlnp | grep 8000
   
   # 检查权限
   sudo -u multiagent uv run python -c "import src.multi_agent_service.main"
   ```

2. **API响应慢**
   ```bash
   # 检查系统资源
   htop
   iotop
   
   # 检查网络连接
   curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/v1/health
   ```

3. **内存泄漏**
   ```bash
   # 监控内存使用
   ps aux | grep uvicorn
   
   # 重启服务
   sudo supervisorctl restart multi-agent-service
   ```

### 调试工具

```bash
# 性能分析
uv run python -m cProfile -o profile.stats src/multi_agent_service/main.py

# 内存分析
uv run python -m memory_profiler src/multi_agent_service/main.py

# 网络调试
tcpdump -i any -w capture.pcap port 8000
```

## 维护计划

### 日常维护

- 检查服务状态
- 监控系统资源使用
- 查看错误日志
- 验证备份完整性

### 周期性维护

- 更新系统补丁
- 更新应用依赖
- 清理日志文件
- 性能优化调整

### 应急响应

- 服务故障恢复流程
- 数据恢复流程
- 安全事件响应
- 扩容应急方案

---

本部署指南涵盖了从开发到生产的完整部署流程。根据实际需求选择合适的部署方案，并定期更新维护。