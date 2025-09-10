# Patent MVP System 故障排除和运维指南

## 目录

1. [常见问题诊断](#常见问题诊断)
2. [系统监控](#系统监控)
3. [日志分析](#日志分析)
4. [性能调优](#性能调优)
5. [备份和恢复](#备份和恢复)
6. [安全维护](#安全维护)
7. [升级指南](#升级指南)
8. [应急响应](#应急响应)

## 常见问题诊断

### 1. 启动问题

#### 问题: uv命令未找到

**症状**:
```bash
bash: uv: command not found
```

**诊断步骤**:
1. 检查uv是否已安装
2. 验证PATH环境变量
3. 检查shell配置

**解决方案**:
```bash
# 安装uv (Linux/macOS)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装uv (Windows)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 重新加载shell配置
source ~/.bashrc  # 或 ~/.zshrc

# 验证安装
uv --version
```

#### 问题: Python版本不兼容

**症状**:
```
ERROR: Python 3.11 is not supported. Python 3.12+ is required.
```

**诊断步骤**:
```bash
python --version
python3 --version
which python
which python3
```

**解决方案**:
```bash
# 使用pyenv安装Python 3.12
pyenv install 3.12.1
pyenv global 3.12.1

# 或使用系统包管理器
# Ubuntu/Debian
sudo apt update
sudo apt install python3.12

# macOS
brew install python@3.12
```

#### 问题: 依赖安装失败

**症状**:
```
ERROR: Failed to resolve dependencies
```

**诊断步骤**:
1. 检查网络连接
2. 验证pyproject.toml文件
3. 检查uv缓存

**解决方案**:
```bash
# 清理uv缓存
uv cache clean

# 重新同步依赖
uv sync --reinstall

# 如果仍然失败，尝试手动安装
uv add fastapi uvicorn
```

### 2. 数据库连接问题

#### 问题: 数据库连接失败

**症状**:
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not connect to server
```

**诊断步骤**:
```bash
# 检查数据库服务状态
sudo systemctl status postgresql

# 测试连接
psql -h localhost -U patent_user -d patent_db

# 检查端口
netstat -tuln | grep 5432
```

**解决方案**:
```bash
# 启动PostgreSQL服务
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 创建数据库和用户
sudo -u postgres psql
CREATE DATABASE patent_db;
CREATE USER patent_user WITH PASSWORD 'patent_pass';
GRANT ALL PRIVILEGES ON DATABASE patent_db TO patent_user;
\q

# 更新连接字符串
export DATABASE_URL="postgresql://patent_user:patent_pass@localhost:5432/patent_db"
```

#### 问题: 数据库迁移失败

**症状**:
```
alembic.util.exc.CommandError: Can't locate revision identified by 'head'
```

**解决方案**:
```bash
# 初始化Alembic
uv run alembic init alembic

# 创建初始迁移
uv run alembic revision --autogenerate -m "Initial migration"

# 应用迁移
uv run alembic upgrade head
```

### 3. Redis连接问题

#### 问题: Redis连接失败

**症状**:
```
redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379
```

**诊断步骤**:
```bash
# 检查Redis服务状态
sudo systemctl status redis

# 测试连接
redis-cli ping

# 检查配置
redis-cli config get "*"
```

**解决方案**:
```bash
# 启动Redis服务
sudo systemctl start redis
sudo systemctl enable redis

# 如果使用Docker
docker run -d -p 6379:6379 redis:alpine

# 测试连接
redis-cli ping
# 应该返回 PONG
```

### 4. Agent初始化问题

#### 问题: Agent注册失败

**症状**:
```
ERROR: Failed to register agent 'patent_coordinator_agent'
```

**诊断步骤**:
1. 检查Agent配置文件
2. 验证Agent类路径
3. 检查依赖项

**解决方案**:
```bash
# 验证配置文件语法
python -m json.tool config/patent_agents.json

# 检查Agent类是否存在
uv run python -c "
from src.multi_agent_service.agents.patent.coordinator_agent import PatentCoordinatorAgent
print('Agent class found')
"

# 重新加载配置
curl -X POST http://localhost:8000/api/v1/config/reload
```

### 5. 外部API问题

#### 问题: CNKI API调用失败

**症状**:
```
ERROR: CNKI API request failed with status 401
```

**诊断步骤**:
1. 检查API密钥
2. 验证网络连接
3. 检查API配额

**解决方案**:
```bash
# 验证API密钥
curl -H "Authorization: Bearer $CNKI_API_KEY" \
     "https://api.cnki.net/v1/test"

# 检查环境变量
echo $CNKI_API_KEY

# 更新配置
export CNKI_API_KEY="your_valid_api_key"
```

## 系统监控

### 1. 健康检查

#### 基础健康检查

```bash
# 系统健康检查
curl http://localhost:8000/health

# 详细系统状态
curl http://localhost:8000/api/v1/system/status

# Agent状态检查
curl http://localhost:8000/api/v1/agents/status
```

#### 自动化健康检查脚本

```bash
#!/bin/bash
# health_monitor.sh

HEALTH_URL="http://localhost:8000/health"
STATUS_URL="http://localhost:8000/api/v1/system/status"
LOG_FILE="/var/log/patent-mvp/health.log"

check_health() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # 基础健康检查
    if curl -f -s "$HEALTH_URL" > /dev/null; then
        echo "$timestamp - Health check: OK" >> "$LOG_FILE"
    else
        echo "$timestamp - Health check: FAILED" >> "$LOG_FILE"
        send_alert "Health check failed"
        return 1
    fi
    
    # 系统状态检查
    local status=$(curl -s "$STATUS_URL" | jq -r '.status')
    if [ "$status" = "healthy" ]; then
        echo "$timestamp - System status: $status" >> "$LOG_FILE"
    else
        echo "$timestamp - System status: $status (WARNING)" >> "$LOG_FILE"
        send_alert "System status warning: $status"
    fi
}

send_alert() {
    local message="$1"
    # 发送邮件或Slack通知
    echo "$message" | mail -s "Patent MVP Alert" admin@company.com
}

# 每5分钟执行一次
while true; do
    check_health
    sleep 300
done
```

### 2. 性能监控

#### 系统资源监控

```bash
#!/bin/bash
# resource_monitor.sh

LOG_FILE="/var/log/patent-mvp/resources.log"

monitor_resources() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # CPU使用率
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    
    # 内存使用率
    local mem_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    
    # 磁盘使用率
    local disk_usage=$(df -h / | awk 'NR==2 {print $5}' | cut -d'%' -f1)
    
    # 记录到日志
    echo "$timestamp,CPU:${cpu_usage}%,MEM:${mem_usage}%,DISK:${disk_usage}%" >> "$LOG_FILE"
    
    # 检查阈值
    if (( $(echo "$cpu_usage > 80" | bc -l) )); then
        send_alert "High CPU usage: ${cpu_usage}%"
    fi
    
    if (( $(echo "$mem_usage > 85" | bc -l) )); then
        send_alert "High memory usage: ${mem_usage}%"
    fi
    
    if [ "$disk_usage" -gt 90 ]; then
        send_alert "High disk usage: ${disk_usage}%"
    fi
}

# 每分钟执行一次
while true; do
    monitor_resources
    sleep 60
done
```

#### 应用性能监控

```python
# performance_monitor.py
import asyncio
import aiohttp
import time
import json
from datetime import datetime

class PerformanceMonitor:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.metrics = []
    
    async def check_api_performance(self):
        """检查API响应时间"""
        endpoints = [
            "/health",
            "/api/v1/system/status",
            "/api/v1/agents/status"
        ]
        
        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints:
                start_time = time.time()
                try:
                    async with session.get(f"{self.base_url}{endpoint}") as response:
                        response_time = (time.time() - start_time) * 1000
                        status = response.status
                        
                        metric = {
                            "timestamp": datetime.now().isoformat(),
                            "endpoint": endpoint,
                            "response_time": response_time,
                            "status_code": status,
                            "success": status == 200
                        }
                        
                        self.metrics.append(metric)
                        print(f"{endpoint}: {response_time:.2f}ms (HTTP {status})")
                        
                        # 警告阈值
                        if response_time > 5000:  # 5秒
                            self.send_alert(f"Slow response: {endpoint} took {response_time:.2f}ms")
                            
                except Exception as e:
                    print(f"Error checking {endpoint}: {e}")
                    self.send_alert(f"API error: {endpoint} - {e}")
    
    def send_alert(self, message):
        """发送警报"""
        print(f"ALERT: {message}")
        # 实现邮件或Slack通知
    
    async def run_monitoring(self):
        """运行监控循环"""
        while True:
            await self.check_api_performance()
            await asyncio.sleep(60)  # 每分钟检查一次

if __name__ == "__main__":
    monitor = PerformanceMonitor()
    asyncio.run(monitor.run_monitoring())
```

## 日志分析

### 1. 日志文件位置

```
logs/
├── patent-mvp.log          # 主应用日志
├── patent-mvp-error.log    # 错误日志
├── patent-mvp-access.log   # 访问日志
├── agent-coordinator.log   # 协调Agent日志
├── agent-analysis.log      # 分析Agent日志
└── performance.log         # 性能日志
```

### 2. 日志分析脚本

#### 错误分析脚本

```bash
#!/bin/bash
# analyze_errors.sh

LOG_FILE="logs/patent-mvp-error.log"
REPORT_FILE="logs/error_report_$(date +%Y%m%d).txt"

echo "Patent MVP Error Analysis Report - $(date)" > "$REPORT_FILE"
echo "================================================" >> "$REPORT_FILE"

# 统计错误类型
echo -e "\n1. Error Types:" >> "$REPORT_FILE"
grep "ERROR" "$LOG_FILE" | awk -F' - ' '{print $3}' | sort | uniq -c | sort -nr >> "$REPORT_FILE"

# 最近24小时的错误
echo -e "\n2. Recent Errors (Last 24 hours):" >> "$REPORT_FILE"
grep "$(date -d '1 day ago' '+%Y-%m-%d')" "$LOG_FILE" | grep "ERROR" >> "$REPORT_FILE"

# 高频错误
echo -e "\n3. Most Frequent Errors:" >> "$REPORT_FILE"
grep "ERROR" "$LOG_FILE" | awk -F' - ' '{print $3}' | sort | uniq -c | sort -nr | head -10 >> "$REPORT_FILE"

# Agent相关错误
echo -e "\n4. Agent Errors:" >> "$REPORT_FILE"
grep "Agent" "$LOG_FILE" | grep "ERROR" >> "$REPORT_FILE"

echo "Error analysis complete. Report saved to: $REPORT_FILE"
```

#### 性能分析脚本

```python
# analyze_performance.py
import re
import json
from datetime import datetime, timedelta
from collections import defaultdict

class PerformanceAnalyzer:
    def __init__(self, log_file="logs/patent-mvp-access.log"):
        self.log_file = log_file
        self.metrics = defaultdict(list)
    
    def parse_access_logs(self):
        """解析访问日志"""
        with open(self.log_file, 'r') as f:
            for line in f:
                # 解析日志格式: timestamp - client_addr - "request" status response_time
                match = re.match(
                    r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - ([\d.]+) - "([^"]+)" (\d+) ([\d.]+)',
                    line
                )
                if match:
                    timestamp, client, request, status, response_time = match.groups()
                    
                    # 提取端点
                    endpoint = request.split()[1] if len(request.split()) > 1 else "unknown"
                    
                    self.metrics[endpoint].append({
                        'timestamp': datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S'),
                        'status': int(status),
                        'response_time': float(response_time),
                        'client': client
                    })
    
    def analyze_performance(self):
        """分析性能指标"""
        report = {}
        
        for endpoint, requests in self.metrics.items():
            if not requests:
                continue
                
            response_times = [r['response_time'] for r in requests]
            statuses = [r['status'] for r in requests]
            
            # 计算统计指标
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
            
            # 成功率
            success_count = sum(1 for s in statuses if 200 <= s < 400)
            success_rate = success_count / len(statuses) * 100
            
            # 最近1小时的请求
            recent_requests = [
                r for r in requests 
                if r['timestamp'] > datetime.now() - timedelta(hours=1)
            ]
            
            report[endpoint] = {
                'total_requests': len(requests),
                'recent_requests': len(recent_requests),
                'avg_response_time': round(avg_response_time, 2),
                'max_response_time': round(max_response_time, 2),
                'min_response_time': round(min_response_time, 2),
                'success_rate': round(success_rate, 2)
            }
        
        return report
    
    def generate_report(self):
        """生成性能报告"""
        self.parse_access_logs()
        analysis = self.analyze_performance()
        
        print("Performance Analysis Report")
        print("=" * 50)
        
        for endpoint, metrics in analysis.items():
            print(f"\nEndpoint: {endpoint}")
            print(f"  Total Requests: {metrics['total_requests']}")
            print(f"  Recent Requests (1h): {metrics['recent_requests']}")
            print(f"  Avg Response Time: {metrics['avg_response_time']}ms")
            print(f"  Max Response Time: {metrics['max_response_time']}ms")
            print(f"  Success Rate: {metrics['success_rate']}%")
            
            # 性能警告
            if metrics['avg_response_time'] > 1000:
                print(f"  ⚠️  WARNING: High average response time")
            if metrics['success_rate'] < 95:
                print(f"  ⚠️  WARNING: Low success rate")

if __name__ == "__main__":
    analyzer = PerformanceAnalyzer()
    analyzer.generate_report()
```

### 3. 日志轮转配置

```bash
# /etc/logrotate.d/patent-mvp
/var/log/patent-mvp/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 patent-mvp patent-mvp
    postrotate
        systemctl reload patent-mvp
    endscript
}
```

## 性能调优

### 1. 数据库优化

#### PostgreSQL配置优化

```sql
-- postgresql.conf 优化建议

-- 内存设置
shared_buffers = 256MB                  -- 系统内存的25%
effective_cache_size = 1GB              -- 系统内存的75%
work_mem = 4MB                          -- 每个查询操作的内存
maintenance_work_mem = 64MB             -- 维护操作内存

-- 连接设置
max_connections = 100                   -- 最大连接数
shared_preload_libraries = 'pg_stat_statements'

-- 日志设置
log_min_duration_statement = 1000      -- 记录慢查询(>1秒)
log_checkpoints = on
log_connections = on
log_disconnections = on

-- 性能设置
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
```

#### 索引优化

```sql
-- 为专利表创建索引
CREATE INDEX CONCURRENTLY idx_patents_application_date 
ON patents(application_date);

CREATE INDEX CONCURRENTLY idx_patents_keywords_gin 
ON patents USING gin(keywords);

CREATE INDEX CONCURRENTLY idx_patents_applicants_gin 
ON patents USING gin(applicants);

CREATE INDEX CONCURRENTLY idx_patents_ipc_classes 
ON patents(ipc_classes);

-- 分析表统计信息
ANALYZE patents;

-- 查看索引使用情况
SELECT schemaname, tablename, indexname, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_tup_read DESC;
```

### 2. Redis优化

#### Redis配置优化

```bash
# redis.conf 优化设置

# 内存设置
maxmemory 512mb
maxmemory-policy allkeys-lru

# 持久化设置
save 900 1
save 300 10
save 60 10000

# 网络设置
tcp-keepalive 300
timeout 0

# 性能设置
hash-max-ziplist-entries 512
hash-max-ziplist-value 64
list-max-ziplist-size -2
set-max-intset-entries 512
```

### 3. 应用层优化

#### uv和Python优化

```bash
# 环境变量优化
export PYTHONOPTIMIZE=1                 # 启用字节码优化
export PYTHONUNBUFFERED=1               # 禁用输出缓冲
export UV_COMPILE_BYTECODE=1            # uv编译字节码
export UV_LINK_MODE=copy                # uv链接模式

# 内存优化
export PYTHONMALLOC=malloc
export MALLOC_ARENA_MAX=2
```

#### Uvicorn配置优化

```python
# 生产环境Uvicorn配置
uvicorn_config = {
    "host": "0.0.0.0",
    "port": 8000,
    "workers": 4,                       # CPU核心数
    "worker_class": "uvicorn.workers.UvicornWorker",
    "loop": "uvloop",                   # 高性能事件循环
    "http": "httptools",                # 高性能HTTP解析器
    "access_log": True,
    "log_level": "info",
    "keepalive": 2,
    "max_requests": 1000,               # 工作进程重启阈值
    "max_requests_jitter": 100,
    "preload_app": True,                # 预加载应用
}
```

## 备份和恢复

### 1. 数据库备份

#### 自动备份脚本

```bash
#!/bin/bash
# backup_database.sh

DB_NAME="patent_db"
DB_USER="patent_user"
BACKUP_DIR="/var/backups/patent-mvp"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/patent_db_$DATE.sql"

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 执行备份
pg_dump -U "$DB_USER" -h localhost "$DB_NAME" > "$BACKUP_FILE"

# 压缩备份文件
gzip "$BACKUP_FILE"

# 删除7天前的备份
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete

echo "Database backup completed: ${BACKUP_FILE}.gz"
```

#### 数据库恢复

```bash
#!/bin/bash
# restore_database.sh

BACKUP_FILE="$1"
DB_NAME="patent_db"
DB_USER="patent_user"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

# 停止应用服务
systemctl stop patent-mvp

# 删除现有数据库
dropdb -U "$DB_USER" "$DB_NAME"

# 创建新数据库
createdb -U "$DB_USER" "$DB_NAME"

# 恢复数据
if [[ "$BACKUP_FILE" == *.gz ]]; then
    gunzip -c "$BACKUP_FILE" | psql -U "$DB_USER" "$DB_NAME"
else
    psql -U "$DB_USER" "$DB_NAME" < "$BACKUP_FILE"
fi

# 启动应用服务
systemctl start patent-mvp

echo "Database restore completed"
```

### 2. 应用数据备份

```bash
#!/bin/bash
# backup_application.sh

APP_DIR="/opt/patent-mvp"
BACKUP_DIR="/var/backups/patent-mvp"
DATE=$(date +%Y%m%d_%H%M%S)

# 备份配置文件
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" \
    "$APP_DIR/config/" \
    "$APP_DIR/.env.production" \
    "$APP_DIR/logging.conf"

# 备份报告文件
tar -czf "$BACKUP_DIR/reports_$DATE.tar.gz" \
    "$APP_DIR/reports/"

# 备份日志文件
tar -czf "$BACKUP_DIR/logs_$DATE.tar.gz" \
    "$APP_DIR/logs/"

echo "Application backup completed"
```

## 安全维护

### 1. 安全检查清单

#### 定期安全检查

```bash
#!/bin/bash
# security_check.sh

echo "Patent MVP Security Check - $(date)"
echo "=================================="

# 1. 检查开放端口
echo "1. Open Ports:"
netstat -tuln | grep LISTEN

# 2. 检查运行进程
echo -e "\n2. Running Processes:"
ps aux | grep -E "(uvicorn|python|redis|postgres)"

# 3. 检查文件权限
echo -e "\n3. File Permissions:"
ls -la /opt/patent-mvp/config/
ls -la /opt/patent-mvp/.env*

# 4. 检查日志中的可疑活动
echo -e "\n4. Suspicious Activities:"
grep -i "failed\|error\|unauthorized" logs/patent-mvp-access.log | tail -10

# 5. 检查磁盘使用
echo -e "\n5. Disk Usage:"
df -h

# 6. 检查内存使用
echo -e "\n6. Memory Usage:"
free -h
```

### 2. 安全更新

#### 依赖更新脚本

```bash
#!/bin/bash
# update_dependencies.sh

echo "Updating Patent MVP dependencies..."

# 备份当前环境
cp uv.lock uv.lock.backup

# 更新依赖
uv sync --upgrade

# 运行测试
uv run pytest tests/ -v

if [ $? -eq 0 ]; then
    echo "Dependencies updated successfully"
else
    echo "Tests failed, rolling back..."
    cp uv.lock.backup uv.lock
    uv sync
    exit 1
fi
```

## 升级指南

### 1. 应用升级流程

```bash
#!/bin/bash
# upgrade_application.sh

NEW_VERSION="$1"
BACKUP_DIR="/var/backups/patent-mvp/upgrade_$(date +%Y%m%d_%H%M%S)"

if [ -z "$NEW_VERSION" ]; then
    echo "Usage: $0 <new_version>"
    exit 1
fi

echo "Upgrading Patent MVP to version $NEW_VERSION"

# 1. 创建备份
mkdir -p "$BACKUP_DIR"
cp -r /opt/patent-mvp "$BACKUP_DIR/"

# 2. 停止服务
systemctl stop patent-mvp

# 3. 备份数据库
pg_dump -U patent_user patent_db > "$BACKUP_DIR/database.sql"

# 4. 更新代码
cd /opt/patent-mvp
git fetch origin
git checkout "v$NEW_VERSION"

# 5. 更新依赖
uv sync

# 6. 运行迁移
uv run alembic upgrade head

# 7. 运行测试
uv run pytest tests/test_startup.py -v

# 8. 启动服务
systemctl start patent-mvp

# 9. 验证升级
sleep 10
curl -f http://localhost:8000/health

if [ $? -eq 0 ]; then
    echo "Upgrade completed successfully"
else
    echo "Upgrade failed, rolling back..."
    systemctl stop patent-mvp
    cp -r "$BACKUP_DIR/patent-mvp" /opt/
    psql -U patent_user patent_db < "$BACKUP_DIR/database.sql"
    systemctl start patent-mvp
    exit 1
fi
```

## 应急响应

### 1. 服务中断响应

#### 快速恢复脚本

```bash
#!/bin/bash
# emergency_recovery.sh

echo "Emergency Recovery Procedure Started - $(date)"

# 1. 检查服务状态
systemctl status patent-mvp

# 2. 检查端口占用
netstat -tuln | grep 8000

# 3. 检查进程
ps aux | grep uvicorn

# 4. 强制重启服务
systemctl stop patent-mvp
sleep 5
pkill -f uvicorn
sleep 2
systemctl start patent-mvp

# 5. 验证恢复
sleep 10
curl -f http://localhost:8000/health

if [ $? -eq 0 ]; then
    echo "Service recovered successfully"
else
    echo "Service recovery failed, escalating..."
    # 发送紧急通知
    echo "Patent MVP service recovery failed" | mail -s "URGENT: Service Down" admin@company.com
fi
```

### 2. 数据库紧急恢复

```bash
#!/bin/bash
# emergency_db_recovery.sh

echo "Database Emergency Recovery - $(date)"

# 1. 检查数据库状态
systemctl status postgresql

# 2. 尝试连接数据库
pg_isready -h localhost -p 5432

# 3. 如果数据库无响应，重启
if [ $? -ne 0 ]; then
    echo "Database not responding, restarting..."
    systemctl restart postgresql
    sleep 10
fi

# 4. 检查数据完整性
psql -U patent_user -d patent_db -c "SELECT COUNT(*) FROM patents;"

# 5. 如果数据损坏，从最新备份恢复
if [ $? -ne 0 ]; then
    echo "Database corruption detected, restoring from backup..."
    LATEST_BACKUP=$(ls -t /var/backups/patent-mvp/patent_db_*.sql.gz | head -1)
    
    if [ -n "$LATEST_BACKUP" ]; then
        dropdb -U patent_user patent_db
        createdb -U patent_user patent_db
        gunzip -c "$LATEST_BACKUP" | psql -U patent_user patent_db
        echo "Database restored from: $LATEST_BACKUP"
    else
        echo "No backup found, manual intervention required"
        exit 1
    fi
fi
```

### 3. 监控和告警

#### 告警脚本

```python
# alert_system.py
import smtplib
import requests
from email.mime.text import MIMEText
from datetime import datetime

class AlertSystem:
    def __init__(self):
        self.smtp_server = "smtp.company.com"
        self.smtp_port = 587
        self.email_user = "alerts@company.com"
        self.email_pass = "password"
        self.admin_emails = ["admin@company.com"]
        self.slack_webhook = "https://hooks.slack.com/services/..."
    
    def send_email_alert(self, subject, message):
        """发送邮件告警"""
        try:
            msg = MIMEText(message)
            msg['Subject'] = subject
            msg['From'] = self.email_user
            msg['To'] = ', '.join(self.admin_emails)
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_pass)
            server.send_message(msg)
            server.quit()
            
            print(f"Email alert sent: {subject}")
        except Exception as e:
            print(f"Failed to send email alert: {e}")
    
    def send_slack_alert(self, message):
        """发送Slack告警"""
        try:
            payload = {
                "text": f"🚨 Patent MVP Alert: {message}",
                "username": "Patent MVP Monitor",
                "icon_emoji": ":warning:"
            }
            
            response = requests.post(self.slack_webhook, json=payload)
            if response.status_code == 200:
                print("Slack alert sent")
            else:
                print(f"Failed to send Slack alert: {response.status_code}")
        except Exception as e:
            print(f"Failed to send Slack alert: {e}")
    
    def critical_alert(self, message):
        """发送严重告警"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_message = f"[{timestamp}] CRITICAL: {message}"
        
        self.send_email_alert("CRITICAL: Patent MVP System Alert", full_message)
        self.send_slack_alert(full_message)
    
    def warning_alert(self, message):
        """发送警告告警"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_message = f"[{timestamp}] WARNING: {message}"
        
        self.send_slack_alert(full_message)

# 使用示例
if __name__ == "__main__":
    alert_system = AlertSystem()
    alert_system.critical_alert("Service is down")
    alert_system.warning_alert("High memory usage detected")
```

---

## 联系支持

如果遇到本指南未涵盖的问题，请联系技术支持：

- **邮箱**: support@patent-mvp.com
- **电话**: +86-xxx-xxxx-xxxx
- **在线支持**: https://support.patent-mvp.com
- **紧急热线**: +86-xxx-xxxx-xxxx (24/7)

---

**版本**: 1.0.0  
**更新日期**: 2024年1月  
**维护团队**: Patent MVP Operations Team