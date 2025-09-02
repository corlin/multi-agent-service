# 运维指南

## 概述

本文档提供Multi-Agent LangGraph Service的日常运维指南，包括监控、维护、故障排除和性能优化等内容。

## 系统监控

### 1. 服务状态监控

#### 健康检查端点
```bash
# 基础健康检查
curl http://localhost:8000/api/v1/health

# 详细健康检查
curl http://localhost:8000/api/v1/health?detailed=true
```

#### 服务进程监控
```bash
# 检查服务进程
ps aux | grep uvicorn

# 检查Supervisor状态
sudo supervisorctl status multi-agent-service

# 检查端口监听
sudo netstat -tlnp | grep 8000
```

### 2. 性能指标监控

#### 系统资源监控
```bash
# CPU和内存使用情况
htop

# 磁盘使用情况
df -h

# 磁盘I/O监控
iotop

# 网络连接监控
ss -tuln
```

#### 应用性能指标
```bash
# 获取性能指标
curl http://localhost:8000/api/v1/monitoring/metrics

# 智能体状态
curl http://localhost:8000/api/v1/agents/status

# 工作流状态
curl http://localhost:8000/api/v1/workflows/status
```

### 3. 日志监控

#### 实时日志监控
```bash
# 查看应用日志
tail -f /var/log/multi-agent-service/app.log

# 查看Supervisor日志
tail -f /var/log/multi-agent-service/supervisor.log

# 查看Nginx访问日志
tail -f /var/log/nginx/multi-agent-service.access.log

# 查看Nginx错误日志
tail -f /var/log/nginx/multi-agent-service.error.log
```

#### 日志分析
```bash
# 统计错误日志
grep "ERROR" /var/log/multi-agent-service/app.log | wc -l

# 查看最近的错误
grep "ERROR" /var/log/multi-agent-service/app.log | tail -10

# 分析API响应时间
grep "api.request_duration" /var/log/multi-agent-service/app.log | \
  jq '.context.execution_time' | \
  awk '{sum+=$1; count++} END {print "Average:", sum/count, "seconds"}'

# 统计API调用频率
grep "Request started" /var/log/multi-agent-service/app.log | \
  grep $(date +%Y-%m-%d) | wc -l
```

## 日常维护

### 1. 服务管理

#### 启动/停止/重启服务
```bash
# 使用Supervisor管理
sudo supervisorctl start multi-agent-service
sudo supervisorctl stop multi-agent-service
sudo supervisorctl restart multi-agent-service

# 重新加载配置
sudo supervisorctl reread
sudo supervisorctl update

# 查看服务状态
sudo supervisorctl status
```

#### 配置热重载
```bash
# 重新加载智能体配置
curl -X POST http://localhost:8000/api/v1/config/reload

# 重新加载模型配置
curl -X POST http://localhost:8000/api/v1/config/models/reload

# 查看配置状态
curl http://localhost:8000/api/v1/config/status
```

### 2. 日志管理

#### 日志轮转
```bash
# 手动执行日志轮转
sudo logrotate -f /etc/logrotate.d/multi-agent-service

# 检查日志轮转配置
sudo logrotate -d /etc/logrotate.d/multi-agent-service
```

#### 日志清理
```bash
#!/bin/bash
# log_cleanup.sh - 日志清理脚本

LOG_DIR="/var/log/multi-agent-service"
RETENTION_DAYS=30

# 清理应用日志
find $LOG_DIR -name "*.log" -mtime +$RETENTION_DAYS -delete

# 清理压缩日志
find $LOG_DIR -name "*.log.gz" -mtime +$RETENTION_DAYS -delete

# 清理Nginx日志
find /var/log/nginx -name "*multi-agent-service*" -mtime +$RETENTION_DAYS -delete

echo "Log cleanup completed at $(date)"
```

### 3. 数据库维护

#### 数据库备份
```bash
#!/bin/bash
# db_backup.sh - 数据库备份脚本

BACKUP_DIR="/backup/database"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="multiagent"

mkdir -p $BACKUP_DIR

# PostgreSQL备份
pg_dump $DB_NAME > $BACKUP_DIR/backup_$DATE.sql

# 压缩备份文件
gzip $BACKUP_DIR/backup_$DATE.sql

# 清理旧备份（保留30天）
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete

echo "Database backup completed: backup_$DATE.sql.gz"
```

#### 数据库优化
```sql
-- 分析表统计信息
ANALYZE;

-- 重建索引
REINDEX DATABASE multiagent;

-- 清理死元组
VACUUM FULL;

-- 查看数据库大小
SELECT pg_size_pretty(pg_database_size('multiagent'));
```

## 性能优化

### 1. 应用层优化

#### 连接池配置
```python
# config/database.py
DATABASE_CONFIG = {
    "pool_size": 20,
    "max_overflow": 30,
    "pool_timeout": 30,
    "pool_recycle": 3600,
    "pool_pre_ping": True
}
```

#### 缓存配置
```python
# config/cache.py
CACHE_CONFIG = {
    "backend": "redis",
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "default_timeout": 300,
    "key_prefix": "multi_agent:"
}
```

### 2. 系统层优化

#### 内核参数调优
```bash
# /etc/sysctl.conf
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 1200
net.ipv4.tcp_max_tw_buckets = 5000
fs.file-max = 100000
vm.swappiness = 10

# 应用配置
sudo sysctl -p
```

#### 文件描述符限制
```bash
# /etc/security/limits.conf
* soft nofile 65535
* hard nofile 65535
* soft nproc 65535
* hard nproc 65535

# 验证配置
ulimit -n
ulimit -u
```

### 3. Nginx优化

```nginx
# /etc/nginx/nginx.conf
worker_processes auto;
worker_connections 4096;
worker_rlimit_nofile 65535;

http {
    # 连接优化
    keepalive_timeout 65;
    keepalive_requests 1000;
    
    # 缓冲区优化
    client_body_buffer_size 128k;
    client_max_body_size 10m;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 4k;
    
    # 压缩优化
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript;
    
    # 缓存优化
    open_file_cache max=1000 inactive=20s;
    open_file_cache_valid 30s;
    open_file_cache_min_uses 2;
    open_file_cache_errors on;
}
```

## 故障排除

### 1. 常见问题诊断

#### 服务无法启动
```bash
# 检查配置文件语法
uv run python -c "from src.multi_agent_service.config import settings; print('Config OK')"

# 检查端口占用
sudo lsof -i :8000

# 检查权限问题
sudo -u multiagent ls -la /opt/multi-agent-service

# 检查依赖问题
uv run python -c "import src.multi_agent_service.main"
```

#### API响应慢
```bash
# 检查系统负载
uptime
iostat 1 5

# 检查数据库连接
psql -h localhost -U multiagent -d multiagent -c "SELECT version();"

# 检查网络延迟
ping -c 5 api.openai.com
curl -w "@curl-format.txt" -o /dev/null -s https://api.openai.com/v1/models
```

#### 内存泄漏
```bash
# 监控内存使用趋势
while true; do
    ps aux | grep uvicorn | grep -v grep | awk '{print $6}' | head -1
    sleep 60
done

# 生成内存转储
kill -USR1 $(pgrep -f uvicorn)

# 分析内存使用
uv run python -m memory_profiler src/multi_agent_service/main.py
```

### 2. 错误日志分析

#### 常见错误模式
```bash
# API调用失败
grep "Model API error" /var/log/multi-agent-service/app.log | tail -10

# 智能体路由失败
grep "Agent routing failed" /var/log/multi-agent-service/app.log | tail -10

# 工作流执行失败
grep "Workflow execution failed" /var/log/multi-agent-service/app.log | tail -10

# 数据库连接问题
grep "Database connection" /var/log/multi-agent-service/app.log | tail -10
```

#### 错误统计脚本
```bash
#!/bin/bash
# error_analysis.sh - 错误分析脚本

LOG_FILE="/var/log/multi-agent-service/app.log"
TODAY=$(date +%Y-%m-%d)

echo "=== Error Analysis for $TODAY ==="

echo "Total errors:"
grep "ERROR" $LOG_FILE | grep $TODAY | wc -l

echo -e "\nTop error types:"
grep "ERROR" $LOG_FILE | grep $TODAY | \
  jq -r '.message' | \
  sort | uniq -c | sort -nr | head -10

echo -e "\nError timeline (hourly):"
grep "ERROR" $LOG_FILE | grep $TODAY | \
  jq -r '.timestamp' | \
  cut -d'T' -f2 | cut -d':' -f1 | \
  sort | uniq -c
```

### 3. 性能问题诊断

#### 响应时间分析
```bash
#!/bin/bash
# performance_analysis.sh - 性能分析脚本

LOG_FILE="/var/log/multi-agent-service/app.log"
TODAY=$(date +%Y-%m-%d)

echo "=== Performance Analysis for $TODAY ==="

echo "API response times (seconds):"
grep "api.request_duration" $LOG_FILE | grep $TODAY | \
  jq '.context.execution_time' | \
  awk '
  {
    sum += $1
    count++
    if ($1 > max) max = $1
    if (min == 0 || $1 < min) min = $1
  }
  END {
    print "Average:", sum/count
    print "Min:", min
    print "Max:", max
  }'

echo -e "\nSlow requests (>5s):"
grep "api.request_duration" $LOG_FILE | grep $TODAY | \
  jq 'select(.context.execution_time > 5) | {time: .timestamp, duration: .context.execution_time, url: .context.url}' | \
  head -10
```

## 安全管理

### 1. 访问控制

#### API密钥管理
```bash
# 轮换API密钥
./scripts/rotate_api_keys.sh

# 检查密钥有效性
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models

# 监控API使用量
grep "Model API call" /var/log/multi-agent-service/app.log | \
  grep $(date +%Y-%m-%d) | wc -l
```

#### 访问日志分析
```bash
# 分析访问模式
awk '{print $1}' /var/log/nginx/multi-agent-service.access.log | \
  sort | uniq -c | sort -nr | head -20

# 检测异常访问
grep "POST /api/v1" /var/log/nginx/multi-agent-service.access.log | \
  awk '{print $1}' | sort | uniq -c | \
  awk '$1 > 100 {print "Suspicious IP:", $2, "Requests:", $1}'
```

### 2. 安全监控

#### 入侵检测
```bash
# 检查失败的登录尝试
grep "Failed password" /var/log/auth.log | tail -10

# 检查异常网络连接
netstat -an | grep :8000 | wc -l

# 检查文件完整性
find /opt/multi-agent-service -type f -name "*.py" -exec md5sum {} \; > /tmp/checksums.txt
```

#### 安全更新
```bash
# 检查系统更新
sudo apt list --upgradable

# 更新系统包
sudo apt update && sudo apt upgrade -y

# 更新Python依赖
uv sync --upgrade
```

## 备份和恢复

### 1. 自动备份

#### 备份脚本
```bash
#!/bin/bash
# full_backup.sh - 完整备份脚本

BACKUP_ROOT="/backup/multi-agent-service"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$BACKUP_ROOT/$DATE"

mkdir -p $BACKUP_DIR

echo "Starting backup at $(date)"

# 备份应用代码
echo "Backing up application..."
tar -czf $BACKUP_DIR/application.tar.gz /opt/multi-agent-service

# 备份配置文件
echo "Backing up configuration..."
tar -czf $BACKUP_DIR/config.tar.gz \
  /etc/nginx/sites-available/multi-agent-service \
  /etc/supervisor/conf.d/multi-agent-service.conf \
  /opt/multi-agent-service/.env

# 备份数据库
echo "Backing up database..."
pg_dump multiagent | gzip > $BACKUP_DIR/database.sql.gz

# 备份日志
echo "Backing up logs..."
tar -czf $BACKUP_DIR/logs.tar.gz /var/log/multi-agent-service

# 创建备份清单
echo "Creating backup manifest..."
cat > $BACKUP_DIR/manifest.txt << EOF
Backup Date: $(date)
Hostname: $(hostname)
Application Version: $(cd /opt/multi-agent-service && git rev-parse HEAD)
Files:
$(ls -la $BACKUP_DIR)
EOF

# 清理旧备份（保留7天）
find $BACKUP_ROOT -maxdepth 1 -type d -mtime +7 -exec rm -rf {} \;

echo "Backup completed at $(date)"
echo "Backup location: $BACKUP_DIR"
```

#### 定时备份
```bash
# 添加到crontab
crontab -e

# 每天凌晨2点执行备份
0 2 * * * /opt/multi-agent-service/scripts/full_backup.sh >> /var/log/backup.log 2>&1

# 每小时备份数据库
0 * * * * pg_dump multiagent | gzip > /backup/hourly/db_$(date +\%H).sql.gz
```

### 2. 灾难恢复

#### 恢复流程
```bash
#!/bin/bash
# disaster_recovery.sh - 灾难恢复脚本

BACKUP_DIR=$1

if [ -z "$BACKUP_DIR" ]; then
    echo "Usage: $0 <backup_directory>"
    exit 1
fi

echo "Starting disaster recovery from $BACKUP_DIR"

# 停止服务
echo "Stopping services..."
sudo supervisorctl stop multi-agent-service
sudo systemctl stop nginx

# 恢复应用
echo "Restoring application..."
sudo tar -xzf $BACKUP_DIR/application.tar.gz -C /

# 恢复配置
echo "Restoring configuration..."
sudo tar -xzf $BACKUP_DIR/config.tar.gz -C /

# 恢复数据库
echo "Restoring database..."
dropdb multiagent
createdb multiagent
gunzip -c $BACKUP_DIR/database.sql.gz | psql multiagent

# 重新安装依赖
echo "Installing dependencies..."
cd /opt/multi-agent-service
uv sync

# 启动服务
echo "Starting services..."
sudo systemctl start nginx
sudo supervisorctl start multi-agent-service

# 验证恢复
echo "Verifying recovery..."
sleep 10
curl -f http://localhost:8000/api/v1/health

echo "Disaster recovery completed at $(date)"
```

## 容量规划

### 1. 资源监控

#### 资源使用趋势
```bash
#!/bin/bash
# resource_monitoring.sh - 资源监控脚本

LOG_FILE="/var/log/resource_usage.log"

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    CPU=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    MEMORY=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    DISK=$(df / | tail -1 | awk '{print $5}' | cut -d'%' -f1)
    CONNECTIONS=$(ss -an | grep :8000 | wc -l)
    
    echo "$TIMESTAMP,CPU:$CPU,Memory:$MEMORY,Disk:$DISK,Connections:$CONNECTIONS" >> $LOG_FILE
    
    sleep 300  # 每5分钟记录一次
done
```

#### 容量预测
```python
#!/usr/bin/env python3
# capacity_planning.py - 容量规划分析

import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

def analyze_capacity():
    # 读取资源使用数据
    df = pd.read_csv('/var/log/resource_usage.log', 
                     names=['timestamp', 'cpu', 'memory', 'disk', 'connections'])
    
    # 数据预处理
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['cpu'] = df['cpu'].str.replace('CPU:', '').astype(float)
    df['memory'] = df['memory'].str.replace('Memory:', '').astype(float)
    
    # 计算趋势
    cpu_trend = df['cpu'].rolling(window=24).mean()  # 24小时移动平均
    memory_trend = df['memory'].rolling(window=24).mean()
    
    # 预测未来7天的资源使用
    future_dates = pd.date_range(start=df['timestamp'].max(), 
                                periods=7*24, freq='H')
    
    # 简单线性预测
    cpu_forecast = cpu_trend.iloc[-1] + (cpu_trend.iloc[-1] - cpu_trend.iloc[-48]) * 7
    memory_forecast = memory_trend.iloc[-1] + (memory_trend.iloc[-1] - memory_trend.iloc[-48]) * 7
    
    print(f"Current CPU usage: {df['cpu'].iloc[-1]:.1f}%")
    print(f"Predicted CPU usage (7 days): {cpu_forecast:.1f}%")
    print(f"Current Memory usage: {df['memory'].iloc[-1]:.1f}%")
    print(f"Predicted Memory usage (7 days): {memory_forecast:.1f}%")
    
    # 容量建议
    if cpu_forecast > 80:
        print("WARNING: CPU usage may exceed 80% in 7 days. Consider scaling up.")
    if memory_forecast > 80:
        print("WARNING: Memory usage may exceed 80% in 7 days. Consider scaling up.")

if __name__ == "__main__":
    analyze_capacity()
```

### 2. 扩容策略

#### 水平扩容
```bash
# 添加新的服务实例
sudo supervisorctl stop multi-agent-service
sudo cp /etc/supervisor/conf.d/multi-agent-service.conf /etc/supervisor/conf.d/multi-agent-service-2.conf

# 修改端口配置
sudo sed -i 's/--port 8000/--port 8001/' /etc/supervisor/conf.d/multi-agent-service-2.conf
sudo sed -i 's/multi-agent-service/multi-agent-service-2/' /etc/supervisor/conf.d/multi-agent-service-2.conf

# 更新Nginx负载均衡配置
sudo cat >> /etc/nginx/sites-available/multi-agent-service << EOF
upstream multi_agent_backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
}
EOF

sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start multi-agent-service multi-agent-service-2
sudo nginx -t && sudo systemctl reload nginx
```

#### 垂直扩容
```bash
# 增加系统资源后，调整应用配置
# 增加worker进程数
sudo sed -i 's/--workers 4/--workers 8/' /etc/supervisor/conf.d/multi-agent-service.conf

# 调整数据库连接池
# 在配置文件中增加pool_size

sudo supervisorctl restart multi-agent-service
```

## 监控告警

### 1. 告警规则

#### 系统告警
```bash
#!/bin/bash
# alert_check.sh - 告警检查脚本

ALERT_EMAIL="admin@company.com"
HOSTNAME=$(hostname)

# CPU使用率告警
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1 | cut -d',' -f1)
if (( $(echo "$CPU_USAGE > 80" | bc -l) )); then
    echo "ALERT: High CPU usage on $HOSTNAME: $CPU_USAGE%" | \
    mail -s "CPU Alert - $HOSTNAME" $ALERT_EMAIL
fi

# 内存使用率告警
MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
if (( $(echo "$MEMORY_USAGE > 80" | bc -l) )); then
    echo "ALERT: High memory usage on $HOSTNAME: $MEMORY_USAGE%" | \
    mail -s "Memory Alert - $HOSTNAME" $ALERT_EMAIL
fi

# 磁盘使用率告警
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | cut -d'%' -f1)
if [ $DISK_USAGE -gt 80 ]; then
    echo "ALERT: High disk usage on $HOSTNAME: $DISK_USAGE%" | \
    mail -s "Disk Alert - $HOSTNAME" $ALERT_EMAIL
fi

# 服务状态告警
if ! curl -f http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    echo "ALERT: Multi-Agent service is down on $HOSTNAME" | \
    mail -s "Service Alert - $HOSTNAME" $ALERT_EMAIL
fi
```

#### 应用告警
```bash
#!/bin/bash
# app_alert_check.sh - 应用告警检查脚本

LOG_FILE="/var/log/multi-agent-service/app.log"
ALERT_EMAIL="admin@company.com"
HOSTNAME=$(hostname)

# 错误率告警
ERROR_COUNT=$(grep "ERROR" $LOG_FILE | grep $(date +%Y-%m-%d) | wc -l)
TOTAL_REQUESTS=$(grep "Request started" $LOG_FILE | grep $(date +%Y-%m-%d) | wc -l)

if [ $TOTAL_REQUESTS -gt 0 ]; then
    ERROR_RATE=$(echo "scale=2; $ERROR_COUNT * 100 / $TOTAL_REQUESTS" | bc)
    if (( $(echo "$ERROR_RATE > 5" | bc -l) )); then
        echo "ALERT: High error rate on $HOSTNAME: $ERROR_RATE%" | \
        mail -s "Error Rate Alert - $HOSTNAME" $ALERT_EMAIL
    fi
fi

# 响应时间告警
AVG_RESPONSE_TIME=$(grep "api.request_duration" $LOG_FILE | grep $(date +%Y-%m-%d) | \
    jq '.context.execution_time' | \
    awk '{sum+=$1; count++} END {if(count>0) print sum/count; else print 0}')

if (( $(echo "$AVG_RESPONSE_TIME > 5" | bc -l) )); then
    echo "ALERT: High response time on $HOSTNAME: ${AVG_RESPONSE_TIME}s" | \
    mail -s "Response Time Alert - $HOSTNAME" $ALERT_EMAIL
fi
```

### 2. 监控仪表板

#### Grafana配置
```json
{
  "dashboard": {
    "title": "Multi-Agent Service Monitoring",
    "panels": [
      {
        "title": "API Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "avg(api_request_duration_seconds)",
            "legendFormat": "Average Response Time"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(api_errors_total[5m])",
            "legendFormat": "Error Rate"
          }
        ]
      },
      {
        "title": "Active Agents",
        "type": "stat",
        "targets": [
          {
            "expr": "count(agent_status{status=\"active\"})",
            "legendFormat": "Active Agents"
          }
        ]
      }
    ]
  }
}
```

## 总结

本运维指南涵盖了Multi-Agent LangGraph Service的完整运维流程，包括：

1. **监控体系**: 全面的系统和应用监控
2. **日常维护**: 标准化的维护流程
3. **性能优化**: 系统和应用层面的优化策略
4. **故障排除**: 常见问题的诊断和解决方案
5. **安全管理**: 访问控制和安全监控
6. **备份恢复**: 完整的备份和灾难恢复方案
7. **容量规划**: 资源监控和扩容策略
8. **监控告警**: 自动化的告警和通知机制

定期执行这些运维任务，可以确保系统的稳定性、安全性和高性能运行。