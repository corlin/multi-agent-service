# Patent MVP System 部署指南

## 目录

1. [部署概述](#部署概述)
2. [环境准备](#环境准备)
3. [开发环境部署](#开发环境部署)
4. [生产环境部署](#生产环境部署)
5. [Docker部署](#docker部署)
6. [云平台部署](#云平台部署)
7. [配置管理](#配置管理)
8. [监控和日志](#监控和日志)
9. [安全配置](#安全配置)
10. [性能优化](#性能优化)

## 部署概述

Patent MVP System支持多种部署方式，适应不同的环境需求：

- **开发环境**: 本地开发和测试
- **生产环境**: 单机或集群部署
- **Docker部署**: 容器化部署
- **云平台部署**: AWS、Azure、GCP等

### 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Load Balancer (Nginx)                   │
├─────────────────────────────────────────────────────────────┤
│  Patent MVP Application Instances                          │
│  ├── Instance 1 (uv + uvicorn)                            │
│  ├── Instance 2 (uv + uvicorn)                            │
│  └── Instance N (uv + uvicorn)                            │
├─────────────────────────────────────────────────────────────┤
│  Shared Services                                           │
│  ├── PostgreSQL Database                                  │
│  ├── Redis Cache                                          │
│  └── File Storage                                         │
└─────────────────────────────────────────────────────────────┘
```

## 环境准备

### 系统要求

#### 最低配置
- **CPU**: 2核心
- **内存**: 4GB RAM
- **存储**: 20GB可用空间
- **操作系统**: Ubuntu 20.04+, CentOS 8+, Windows 10+, macOS 11+

#### 推荐配置
- **CPU**: 4核心或更多
- **内存**: 8GB RAM或更多
- **存储**: 50GB SSD
- **网络**: 稳定的互联网连接

### 软件依赖

#### 必需软件
- Python 3.12+
- uv包管理器
- Git
- curl

#### 可选软件
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+
- Nginx

### 环境验证

使用提供的验证脚本检查环境：

```bash
# Linux/macOS
./scripts/validate-environment.sh

# Windows
.\scripts\validate-environment.ps1
```

## 开发环境部署

### 1. 快速开始

```bash
# 1. 克隆项目
git clone <repository-url>
cd patent-mvp-system

# 2. 安装uv (如果未安装)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. 安装依赖
uv sync --dev

# 4. 配置环境变量
cp .env.example .env.development
# 编辑 .env.development 文件

# 5. 启动开发服务器
./scripts/start-development.sh
```

### 2. 详细配置

#### 环境变量配置

编辑 `.env.development` 文件：

```bash
# 应用配置
APP_ENV=development
DEBUG=true
LOG_LEVEL=DEBUG

# 数据库配置 (开发环境使用SQLite)
DATABASE_URL=sqlite:///./data/patent_dev.db

# Redis配置 (可选)
REDIS_URL=redis://localhost:6379/0

# 外部API配置 (开发环境可使用测试密钥)
CNKI_API_KEY=test_key
BOCHA_AI_API_KEY=test_key
MOCK_EXTERNAL_APIS=true

# Agent配置
AGENT_REGISTRY_AUTO_RELOAD=true
HOT_RELOAD_ENABLED=true
```

#### 开发服务启动

```bash
# 方式1: 使用启动脚本
./scripts/start-development.sh

# 方式2: 手动启动
uv run uvicorn src.multi_agent_service.main:app \
    --reload \
    --host 0.0.0.0 \
    --port 8000 \
    --log-level debug

# 方式3: 使用Docker (开发模式)
docker-compose -f docker-compose.windows.yml up -d
```

### 3. 开发工具配置

#### IDE配置 (VS Code)

创建 `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": "./.venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": false,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"],
    "files.exclude": {
        "**/__pycache__": true,
        "**/.pytest_cache": true,
        ".venv": true
    }
}
```

#### 预提交钩子

```bash
# 安装pre-commit
uv add --dev pre-commit

# 创建 .pre-commit-config.yaml
cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.12
  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
EOF

# 安装钩子
uv run pre-commit install
```

## 生产环境部署

### 1. 服务器准备

#### 系统配置

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装必需软件
sudo apt install -y \
    python3.12 \
    python3.12-venv \
    python3.12-dev \
    build-essential \
    curl \
    git \
    nginx \
    postgresql-15 \
    redis-server \
    supervisor

# 安装uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### 用户和目录设置

```bash
# 创建应用用户
sudo useradd -r -s /bin/bash -m patent-mvp

# 创建应用目录
sudo mkdir -p /opt/patent-mvp
sudo chown patent-mvp:patent-mvp /opt/patent-mvp

# 创建日志目录
sudo mkdir -p /var/log/patent-mvp
sudo chown patent-mvp:patent-mvp /var/log/patent-mvp

# 创建数据目录
sudo mkdir -p /var/lib/patent-mvp
sudo chown patent-mvp:patent-mvp /var/lib/patent-mvp
```

### 2. 应用部署

#### 代码部署

```bash
# 切换到应用用户
sudo su - patent-mvp

# 克隆代码
cd /opt/patent-mvp
git clone <repository-url> .

# 安装依赖
uv sync --no-dev

# 配置环境变量
cp .env.production.example .env.production
# 编辑生产环境配置
```

#### 生产环境配置

编辑 `/opt/patent-mvp/.env.production`:

```bash
# 应用配置
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO

# 数据库配置
DATABASE_URL=postgresql://patent_user:secure_password@localhost:5432/patent_db
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Redis配置
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_TTL=3600

# 安全配置
API_KEY_REQUIRED=true
API_KEY=your_secure_api_key_here
CORS_ORIGINS=https://yourdomain.com
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# 外部API配置
CNKI_API_KEY=your_real_cnki_api_key
BOCHA_AI_API_KEY=your_real_bocha_ai_key
GOOGLE_PATENTS_API_KEY=your_google_patents_key

# 性能配置
UVICORN_WORKERS=4
PATENT_MAX_CONCURRENT_ANALYSES=5
PATENT_BATCH_SIZE=100
```

### 3. 数据库设置

#### PostgreSQL配置

```bash
# 切换到postgres用户
sudo su - postgres

# 创建数据库和用户
psql << EOF
CREATE DATABASE patent_db;
CREATE USER patent_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE patent_db TO patent_user;
ALTER USER patent_user CREATEDB;
\q
EOF

# 配置PostgreSQL
sudo nano /etc/postgresql/15/main/postgresql.conf
```

PostgreSQL优化配置：

```bash
# /etc/postgresql/15/main/postgresql.conf

# 内存设置
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# 连接设置
max_connections = 100
listen_addresses = 'localhost'

# 性能设置
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100

# 日志设置
log_min_duration_statement = 1000
log_checkpoints = on
log_connections = on
log_disconnections = on
```

#### 数据库初始化

```bash
# 运行数据库迁移
cd /opt/patent-mvp
sudo -u patent-mvp uv run alembic upgrade head
```

### 4. 服务配置

#### Systemd服务配置

创建 `/etc/systemd/system/patent-mvp.service`:

```ini
[Unit]
Description=Patent MVP System
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service

[Service]
Type=exec
User=patent-mvp
Group=patent-mvp
WorkingDirectory=/opt/patent-mvp
Environment=PATH=/opt/patent-mvp/.venv/bin:/usr/local/bin:/usr/bin:/bin
EnvironmentFile=/opt/patent-mvp/.env.production
ExecStart=/opt/patent-mvp/.venv/bin/uv run uvicorn src.multi_agent_service.main:app --host 0.0.0.0 --port 8000 --workers 4
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=patent-mvp

# 安全设置
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=/opt/patent-mvp/logs /opt/patent-mvp/reports /opt/patent-mvp/data /var/lib/patent-mvp

[Install]
WantedBy=multi-user.target
```

#### 启动服务

```bash
# 重新加载systemd配置
sudo systemctl daemon-reload

# 启用并启动服务
sudo systemctl enable patent-mvp
sudo systemctl start patent-mvp

# 检查服务状态
sudo systemctl status patent-mvp

# 查看日志
sudo journalctl -u patent-mvp -f
```

### 5. Nginx配置

#### 反向代理配置

创建 `/etc/nginx/sites-available/patent-mvp`:

```nginx
upstream patent_mvp {
    server 127.0.0.1:8000;
    # 如果有多个实例，添加更多server
    # server 127.0.0.1:8001;
    # server 127.0.0.1:8002;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL配置
    ssl_certificate /etc/ssl/certs/patent-mvp.crt;
    ssl_certificate_key /etc/ssl/private/patent-mvp.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # 客户端最大请求大小
    client_max_body_size 10M;
    
    # 静态文件
    location /static/ {
        alias /opt/patent-mvp/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # 报告文件下载
    location /reports/ {
        alias /opt/patent-mvp/reports/;
        internal;
        add_header Content-Disposition "attachment";
    }
    
    # API代理
    location / {
        proxy_pass http://patent_mvp;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # 缓冲设置
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        
        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # 健康检查
    location /health {
        proxy_pass http://patent_mvp;
        access_log off;
    }
    
    # 限制访问敏感路径
    location ~ ^/(admin|config)/ {
        deny all;
        return 404;
    }
}
```

#### 启用Nginx配置

```bash
# 启用站点
sudo ln -s /etc/nginx/sites-available/patent-mvp /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重新加载Nginx
sudo systemctl reload nginx
```

## Docker部署

### 1. 单机Docker部署

#### 使用Docker Compose

```bash
# 克隆项目
git clone <repository-url>
cd patent-mvp-system

# 配置环境变量
cp .env.production.example .env.production
# 编辑 .env.production

# 启动服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f patent-service
```

#### 自定义Docker Compose配置

创建 `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  patent-service:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    container_name: patent-mvp-prod
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - APP_ENV=production
      - DATABASE_URL=postgresql://patent_user:${DB_PASSWORD}@postgres:5432/patent_db
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - .env.production
    volumes:
      - patent_reports:/app/reports/patent
      - patent_logs:/app/logs
      - patent_data:/app/data
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - patent-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  postgres:
    image: postgres:15-alpine
    container_name: patent-postgres-prod
    restart: unless-stopped
    environment:
      POSTGRES_DB: patent_db
      POSTGRES_USER: patent_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql:ro
    networks:
      - patent-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U patent_user -d patent_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: patent-redis-prod
    restart: unless-stopped
    command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    networks:
      - patent-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

  nginx:
    image: nginx:alpine
    container_name: patent-nginx-prod
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - patent_static:/var/www/static
    depends_on:
      - patent-service
    networks:
      - patent-network

volumes:
  postgres_data:
  redis_data:
  patent_reports:
  patent_logs:
  patent_data:
  patent_static:

networks:
  patent-network:
    driver: bridge
```

### 2. Docker Swarm集群部署

#### 初始化Swarm

```bash
# 在管理节点初始化Swarm
docker swarm init --advertise-addr <MANAGER-IP>

# 在工作节点加入Swarm
docker swarm join --token <TOKEN> <MANAGER-IP>:2377
```

#### Docker Stack配置

创建 `docker-stack.yml`:

```yaml
version: '3.8'

services:
  patent-service:
    image: patent-mvp:latest
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
        failure_action: rollback
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      placement:
        constraints:
          - node.role == worker
    environment:
      - APP_ENV=production
      - DATABASE_URL=postgresql://patent_user:${DB_PASSWORD}@postgres:5432/patent_db
      - REDIS_URL=redis://redis:6379/0
    networks:
      - patent-network
    volumes:
      - patent_reports:/app/reports/patent
      - patent_logs:/app/logs

  postgres:
    image: postgres:15-alpine
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.role == manager
    environment:
      POSTGRES_DB: patent_db
      POSTGRES_USER: patent_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - patent-network

  redis:
    image: redis:7-alpine
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.role == manager
    networks:
      - patent-network

  nginx:
    image: nginx:alpine
    deploy:
      replicas: 2
      placement:
        constraints:
          - node.role == worker
    ports:
      - "80:80"
      - "443:443"
    networks:
      - patent-network

networks:
  patent-network:
    driver: overlay
    attachable: true

volumes:
  postgres_data:
  patent_reports:
  patent_logs:
```

#### 部署Stack

```bash
# 部署Stack
docker stack deploy -c docker-stack.yml patent-mvp

# 查看服务状态
docker stack services patent-mvp

# 查看服务日志
docker service logs patent-mvp_patent-service
```

## 云平台部署

### 1. AWS部署

#### 使用ECS (Elastic Container Service)

1. **创建ECS集群**

```bash
# 使用AWS CLI创建集群
aws ecs create-cluster --cluster-name patent-mvp-cluster
```

2. **创建任务定义**

创建 `task-definition.json`:

```json
{
  "family": "patent-mvp-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "patent-mvp",
      "image": "your-account.dkr.ecr.region.amazonaws.com/patent-mvp:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "APP_ENV",
          "value": "production"
        },
        {
          "name": "DATABASE_URL",
          "value": "postgresql://user:pass@rds-endpoint:5432/patent_db"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/patent-mvp",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

3. **创建服务**

```bash
# 注册任务定义
aws ecs register-task-definition --cli-input-json file://task-definition.json

# 创建服务
aws ecs create-service \
    --cluster patent-mvp-cluster \
    --service-name patent-mvp-service \
    --task-definition patent-mvp-task:1 \
    --desired-count 2 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-12345,subnet-67890],securityGroups=[sg-abcdef],assignPublicIp=ENABLED}"
```

#### 使用Terraform部署

创建 `main.tf`:

```hcl
provider "aws" {
  region = var.aws_region
}

# VPC和网络配置
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  
  name = "patent-mvp-vpc"
  cidr = "10.0.0.0/16"
  
  azs             = ["${var.aws_region}a", "${var.aws_region}b"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]
  
  enable_nat_gateway = true
  enable_vpn_gateway = false
}

# RDS数据库
resource "aws_db_instance" "patent_db" {
  identifier = "patent-mvp-db"
  
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.t3.micro"
  
  allocated_storage     = 20
  max_allocated_storage = 100
  storage_encrypted     = true
  
  db_name  = "patent_db"
  username = "patent_user"
  password = var.db_password
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.patent_db.name
  
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  skip_final_snapshot = true
}

# ElastiCache Redis
resource "aws_elasticache_subnet_group" "patent_redis" {
  name       = "patent-mvp-redis-subnet"
  subnet_ids = module.vpc.private_subnets
}

resource "aws_elasticache_cluster" "patent_redis" {
  cluster_id           = "patent-mvp-redis"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.patent_redis.name
  security_group_ids   = [aws_security_group.redis.id]
}

# ECS集群
resource "aws_ecs_cluster" "patent_mvp" {
  name = "patent-mvp-cluster"
  
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# Application Load Balancer
resource "aws_lb" "patent_mvp" {
  name               = "patent-mvp-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = module.vpc.public_subnets
  
  enable_deletion_protection = false
}

# ECS服务
resource "aws_ecs_service" "patent_mvp" {
  name            = "patent-mvp-service"
  cluster         = aws_ecs_cluster.patent_mvp.id
  task_definition = aws_ecs_task_definition.patent_mvp.arn
  desired_count   = 2
  launch_type     = "FARGATE"
  
  network_configuration {
    subnets          = module.vpc.private_subnets
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }
  
  load_balancer {
    target_group_arn = aws_lb_target_group.patent_mvp.arn
    container_name   = "patent-mvp"
    container_port   = 8000
  }
  
  depends_on = [aws_lb_listener.patent_mvp]
}
```

### 2. Azure部署

#### 使用Azure Container Instances

```bash
# 创建资源组
az group create --name patent-mvp-rg --location eastus

# 创建容器实例
az container create \
    --resource-group patent-mvp-rg \
    --name patent-mvp-container \
    --image your-registry.azurecr.io/patent-mvp:latest \
    --cpu 2 \
    --memory 4 \
    --ports 8000 \
    --environment-variables \
        APP_ENV=production \
        DATABASE_URL="postgresql://user:pass@server.postgres.database.azure.com:5432/patent_db" \
    --secure-environment-variables \
        CNKI_API_KEY="your-api-key" \
    --dns-name-label patent-mvp-app
```

### 3. Google Cloud Platform部署

#### 使用Cloud Run

```bash
# 构建并推送镜像
gcloud builds submit --tag gcr.io/PROJECT-ID/patent-mvp

# 部署到Cloud Run
gcloud run deploy patent-mvp \
    --image gcr.io/PROJECT-ID/patent-mvp \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars APP_ENV=production \
    --set-env-vars DATABASE_URL="postgresql://user:pass@/patent_db?host=/cloudsql/PROJECT-ID:REGION:INSTANCE-ID" \
    --add-cloudsql-instances PROJECT-ID:REGION:INSTANCE-ID
```

## 配置管理

### 1. 环境变量管理

#### 使用环境变量文件

```bash
# 开发环境
.env.development

# 测试环境
.env.testing

# 生产环境
.env.production
```

#### 使用配置管理工具

**Ansible配置管理**:

```yaml
# playbook.yml
---
- hosts: patent_mvp_servers
  become: yes
  vars:
    app_user: patent-mvp
    app_dir: /opt/patent-mvp
    
  tasks:
    - name: Create application user
      user:
        name: "{{ app_user }}"
        system: yes
        shell: /bin/bash
        home: "{{ app_dir }}"
        
    - name: Clone application repository
      git:
        repo: "{{ app_repo_url }}"
        dest: "{{ app_dir }}"
        version: "{{ app_version | default('main') }}"
      become_user: "{{ app_user }}"
      
    - name: Install dependencies
      shell: uv sync --no-dev
      args:
        chdir: "{{ app_dir }}"
      become_user: "{{ app_user }}"
      
    - name: Configure environment
      template:
        src: env.production.j2
        dest: "{{ app_dir }}/.env.production"
        owner: "{{ app_user }}"
        group: "{{ app_user }}"
        mode: '0600'
        
    - name: Configure systemd service
      template:
        src: patent-mvp.service.j2
        dest: /etc/systemd/system/patent-mvp.service
      notify: restart patent-mvp
      
  handlers:
    - name: restart patent-mvp
      systemd:
        name: patent-mvp
        state: restarted
        daemon_reload: yes
```

### 2. 密钥管理

#### 使用HashiCorp Vault

```bash
# 启动Vault开发服务器
vault server -dev

# 设置环境变量
export VAULT_ADDR='http://127.0.0.1:8200'
export VAULT_TOKEN='dev-token'

# 存储密钥
vault kv put secret/patent-mvp \
    database_password="secure_password" \
    cnki_api_key="your_cnki_key" \
    bocha_ai_key="your_bocha_key"

# 读取密钥
vault kv get secret/patent-mvp
```

#### 在应用中使用Vault

```python
# vault_client.py
import hvac
import os

class VaultClient:
    def __init__(self):
        self.client = hvac.Client(
            url=os.getenv('VAULT_ADDR', 'http://localhost:8200'),
            token=os.getenv('VAULT_TOKEN')
        )
    
    def get_secret(self, path):
        """获取密钥"""
        try:
            response = self.client.secrets.kv.v2.read_secret_version(path=path)
            return response['data']['data']
        except Exception as e:
            print(f"Failed to read secret from Vault: {e}")
            return None

# 使用示例
vault_client = VaultClient()
secrets = vault_client.get_secret('patent-mvp')
if secrets:
    os.environ['DATABASE_PASSWORD'] = secrets['database_password']
    os.environ['CNKI_API_KEY'] = secrets['cnki_api_key']
```

## 监控和日志

### 1. 应用监控

#### Prometheus + Grafana

**Prometheus配置** (`prometheus.yml`):

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'patent-mvp'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s
```

**在应用中添加指标**:

```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Response

# 定义指标
REQUEST_COUNT = Counter('patent_mvp_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('patent_mvp_request_duration_seconds', 'Request duration')
ACTIVE_ANALYSES = Gauge('patent_mvp_active_analyses', 'Active analysis tasks')

@app.middleware("http")
async def metrics_middleware(request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path
    ).inc()
    
    REQUEST_DURATION.observe(time.time() - start_time)
    
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### 2. 日志聚合

#### ELK Stack配置

**Filebeat配置** (`filebeat.yml`):

```yaml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /opt/patent-mvp/logs/*.log
  fields:
    service: patent-mvp
  fields_under_root: true

output.elasticsearch:
  hosts: ["localhost:9200"]
  index: "patent-mvp-%{+yyyy.MM.dd}"

setup.template.name: "patent-mvp"
setup.template.pattern: "patent-mvp-*"
```

**Logstash配置** (`logstash.conf`):

```ruby
input {
  beats {
    port => 5044
  }
}

filter {
  if [service] == "patent-mvp" {
    grok {
      match => { "message" => "%{TIMESTAMP_ISO8601:timestamp} - %{LOGLEVEL:level} - %{GREEDYDATA:message}" }
    }
    
    date {
      match => [ "timestamp", "yyyy-MM-dd HH:mm:ss" ]
    }
  }
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "patent-mvp-%{+YYYY.MM.dd}"
  }
}
```

## 安全配置

### 1. 网络安全

#### 防火墙配置

```bash
# UFW防火墙配置
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 允许SSH
sudo ufw allow ssh

# 允许HTTP和HTTPS
sudo ufw allow 80
sudo ufw allow 443

# 允许应用端口 (仅本地)
sudo ufw allow from 127.0.0.1 to any port 8000

# 启用防火墙
sudo ufw enable
```

#### SSL/TLS配置

```bash
# 使用Let's Encrypt获取SSL证书
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 自动续期
sudo crontab -e
# 添加: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 2. 应用安全

#### 安全中间件

```python
# security.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import time

app = FastAPI()

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# 受信任主机
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["yourdomain.com", "www.yourdomain.com"]
)

# 速率限制
from collections import defaultdict
from datetime import datetime, timedelta

rate_limit_storage = defaultdict(list)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    now = datetime.now()
    
    # 清理过期记录
    rate_limit_storage[client_ip] = [
        timestamp for timestamp in rate_limit_storage[client_ip]
        if now - timestamp < timedelta(minutes=1)
    ]
    
    # 检查速率限制
    if len(rate_limit_storage[client_ip]) >= 100:  # 每分钟100请求
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    rate_limit_storage[client_ip].append(now)
    
    response = await call_next(request)
    return response
```

## 性能优化

### 1. 应用性能优化

#### 异步优化

```python
# 使用连接池
import asyncpg
import aioredis

class DatabaseManager:
    def __init__(self):
        self.pg_pool = None
        self.redis_pool = None
    
    async def initialize(self):
        # PostgreSQL连接池
        self.pg_pool = await asyncpg.create_pool(
            dsn=DATABASE_URL,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
        
        # Redis连接池
        self.redis_pool = aioredis.ConnectionPool.from_url(
            REDIS_URL,
            max_connections=20
        )
    
    async def get_pg_connection(self):
        return await self.pg_pool.acquire()
    
    async def get_redis_connection(self):
        return aioredis.Redis(connection_pool=self.redis_pool)
```

#### 缓存策略

```python
# cache.py
import asyncio
from functools import wraps
import json
import hashlib

def cache_result(ttl=3600):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{func.__name__}:{hashlib.md5(str(args + tuple(kwargs.items())).encode()).hexdigest()}"
            
            # 尝试从缓存获取
            redis = await get_redis_connection()
            cached_result = await redis.get(cache_key)
            
            if cached_result:
                return json.loads(cached_result)
            
            # 执行函数并缓存结果
            result = await func(*args, **kwargs)
            await redis.setex(cache_key, ttl, json.dumps(result, default=str))
            
            return result
        return wrapper
    return decorator

# 使用示例
@cache_result(ttl=7200)
async def analyze_patents(keywords):
    # 执行分析逻辑
    pass
```

### 2. 数据库性能优化

#### 查询优化

```sql
-- 创建复合索引
CREATE INDEX CONCURRENTLY idx_patents_date_keywords 
ON patents(application_date, keywords) 
WHERE application_date >= '2020-01-01';

-- 分区表
CREATE TABLE patents_2024 PARTITION OF patents 
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

-- 物化视图
CREATE MATERIALIZED VIEW patent_stats AS
SELECT 
    DATE_TRUNC('month', application_date) as month,
    COUNT(*) as patent_count,
    COUNT(DISTINCT applicants) as unique_applicants
FROM patents 
GROUP BY DATE_TRUNC('month', application_date);

-- 定期刷新物化视图
CREATE OR REPLACE FUNCTION refresh_patent_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY patent_stats;
END;
$$ LANGUAGE plpgsql;
```

---

## 总结

本部署指南涵盖了Patent MVP System的各种部署场景，从开发环境到生产环境，从单机部署到云平台集群部署。选择适合您需求的部署方式，并根据实际情况调整配置参数。

关键要点：
1. 使用uv进行依赖管理，提高部署效率
2. 合理配置数据库和缓存，确保性能
3. 实施适当的安全措施，保护系统安全
4. 建立完善的监控和日志系统
5. 定期备份重要数据
6. 制定应急响应计划

---

**版本**: 1.0.0  
**更新日期**: 2024年1月  
**维护团队**: Patent MVP DevOps Team