# CBG FastAPI Docker 部署指南（Linux环境）

## 📋 部署概述

本项目采用 Docker Compose 方式部署，适用于 Linux 生产环境，具有以下特点：
- 镜像只需首次构建，后续代码更新通过文件映射实现快速重启
- 使用清华源加速 pip 包下载，提升构建速度
- 提供完善的部署和管理脚本，简化运维流程
- 支持健康检查和自动重启策略，保证服务高可用

## 🚀 快速部署（Linux环境）

### 前置要求
- Docker 20.10+
- Docker Compose 2.0+
- Git（用于拉取代码）
- 外部 MySQL 5.7+ 或 8.0+ 数据库服务
- 外部 MinIO 对象存储服务（或自建）

### 一键部署步骤
1. **克隆项目代码**
   ```bash
   git clone <repository-url>
   cd cbg-fast-api
   ```

2. **配置环境变量**
   编辑 `.env` 文件，修改数据库、MinIO和JWT配置：
   ```bash
   vim .env
   # 或使用其他编辑器
   nano .env
   ```

3. **给脚本添加执行权限**
   ```bash
   chmod +x deploy.sh manage.sh
   ```

4. **运行部署脚本**
   ```bash
   ./deploy.sh
   ```
   脚本会自动完成：检查环境 → 构建镜像 → 启动服务 → 验证健康状态

## 📁 项目结构

```
cbg-fast-api/
├── app/                 # 应用代码目录
├── Dockerfile          # Docker 镜像构建文件
├── docker-compose.yml  # Docker Compose 配置
├── .env               # 环境变量配置
├── .dockerignore      # Docker 构建忽略文件
├── deploy.sh          # Linux一键部署脚本
├── manage.sh          # Linux容器管理脚本
├── init_db.py         # 数据库初始化脚本
└── logs/              # 日志目录（自动生成）
```

## ⚙️ 环境配置

### 外部依赖配置（在 .env 文件中修改）

```bash
# MySQL数据库配置
MYSQL_HOST=192.168.3.121
MYSQL_PORT=3308
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=cbg_db

# MinIO配置
MINIO_ENDPOINT=172.16.30.115:9000
MINIO_ACCESS_KEY=your_access_key
MINIO_SECRET_KEY=your_secret_key
MINIO_BUCKET_NAME=cbg-bucket
MINIO_SECURE=False

# JWT配置
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 应用配置
HOST=0.0.0.0
PORT=8000
DEBUG=False
```

## 🔧 部署流程

### 首次部署步骤

1. **检查环境**
   - 确保已安装 Docker 和 docker-compose
   - 确认 .env 配置文件正确

2. **运行部署脚本**
   ```bash
   ./deploy.sh
   ```
   脚本会自动完成：检查环境 → 构建镜像 → 启动服务 → 验证健康状态

5. **验证部署**
   - 访问应用: http://localhost:8000
   - API文档: http://localhost:8000/docs
   - 健康检查: http://localhost:8000/health
   - ReDoc文档: http://localhost:8000/redoc

6. **初始化数据库**（首次部署必需）
   ```bash
   # 进入容器执行数据库初始化
   docker exec -it cbg-fastapi-app python init_db.py
   
   # 默认管理员账户: admin / admin123
   ```

## 🔄 代码更新与重启

由于采用了文件映射机制（volume mounts），更新代码后无需重新构建镜像，只需重启容器即可生效：

### 方式一：使用管理脚本（推荐）
```bash
./manage.sh
# 选择选项 7: 重启服务
```

### 方式二：直接使用命令
```bash
# 重启单个服务
docker-compose restart cbg-app

# 或重启所有服务
docker-compose restart
```

### 方式三：停止后重新启动（完全重载）
```bash
docker-compose down
docker-compose up -d
```

## 🛠️ 容器管理命令

### 使用管理脚本（推荐）

运行管理脚本，根据交互式菜单操作：
```bash
./manage.sh
```

提供的功能包括：
- ✅ 启动/停止/重启服务
- ✅ 查看服务状态和实时日志
- ✅ 进入容器进行调试
- ✅ 清理容器和镜像资源
- ✅ 查看资源使用情况

### 常用 docker-compose 命令速查

```bash
# 启动服务（后台运行）
docker-compose up -d

# 停止并删除容器
docker-compose down

# 停止服务（保留容器）
docker-compose stop

# 查看服务状态
docker-compose ps

# 查看所有日志
docker-compose logs

# 实时跟踪日志输出
docker-compose logs -f cbg-app

# 查看最近100行日志
docker-compose logs --tail=100 cbg-app

# 重启服务
docker-compose restart cbg-app

# 进入容器执行命令
docker exec -it cbg-fastapi-app /bin/bash

# 在容器内执行Python命令
docker exec -it cbg-fastapi-app python --version

# 查看容器资源使用
docker stats cbg-fastapi-app

# 重新构建镜像
docker-compose build --no-cache

# 拉取最新代码后重启
git pull && docker-compose restart
```

## 📊 性能优化

### 构建优化
- 使用 `.dockerignore` 排除不必要的文件
- 采用多阶段构建减少镜像大小
- 配置清华源加速依赖下载

### 运行优化
- 文件映射避免重复构建
- 健康检查确保服务稳定
- 自动重启策略保证高可用

## 🔒 生产环境安全建议

### 1. 敏感信息保护
- ✅ 修改默认的 `SECRET_KEY`，使用强随机字符串（至少32位）
- ✅ 不要在代码中硬编码密码和密钥，全部通过 `.env` 文件管理
- ✅ 将 `.env` 文件加入 `.gitignore`，避免提交到版本控制
- ✅ 定期轮换 JWT 密钥和数据库密码

### 2. 网络安全加固
- ✅ 启用 HTTPS（建议使用 Nginx 反向代理 + Let's Encrypt 证书）
- ✅ 配置防火墙规则，仅开放必要端口（80/443）
- ✅ 限制数据库和 MinIO 的访问IP白名单
- ✅ 使用 Docker 网络隔离内部服务

### 3. 容器运行时安全
- ✅ 定期更新基础镜像和依赖包（`docker-compose build --pull`）
- ✅ 考虑使用非 root 用户运行容器（修改 Dockerfile）
- ✅ 限制容器资源使用（在 docker-compose.yml 中添加 `deploy.resources`）
- ✅ 启用 Docker Content Trust 确保镜像完整性

## 🐛 故障排查指南

### 常见问题及解决方案

#### 1. 端口被占用
**错误信息**: `Error: port is already allocated`

**解决方案**:
```bash
# 查看端口占用情况
sudo lsof -i :8000
# 或
netstat -tuln | grep 8000

# 方案一：停止占用端口的进程
sudo kill -9 <PID>

# 方案二：修改 .env 中的 PORT 配置为其他端口（如8080）
PORT=8080

# 重启服务
docker-compose down && docker-compose up -d
```

#### 2. 权限不足
**错误信息**: `Permission denied` 或 `Cannot connect to the Docker daemon`

**解决方案**:
```bash
# 给脚本添加执行权限
chmod +x deploy.sh manage.sh

# 如果Docker需要sudo，将当前用户加入docker组
sudo usermod -aG docker $USER
# 退出重新登录后生效
groups  # 确认已加入docker组

# 临时使用sudo
sudo ./deploy.sh
```

#### 3. 依赖下载缓慢或失败
**现象**: pip install 长时间卡住或超时

**解决方案**:
```bash
# 已配置清华源，如仍有问题可尝试以下方法：

# 方案一：手动指定pip源
docker exec -it cbg-fastapi-app pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 方案二：更换其他国内镜像源
# 阿里云: https://mirrors.aliyun.com/pypi/simple/
# 豆瓣: https://pypi.douban.com/simple/

# 方案三：检查网络连接
docker exec -it cbg-fastapi-app ping pypi.tuna.tsinghua.edu.cn
```

#### 4. 容器启动失败或不断重启
**现象**: 容器状态为 `Restarting` 或 `Exited`

**诊断步骤**:
```bash
# 1. 查看详细日志
docker-compose logs --tail=100 cbg-app

# 2. 检查容器状态
docker inspect cbg-fastapi-app | grep -A 10 State

# 3. 进入容器调试（如果容器还在运行）
docker exec -it cbg-fastapi-app /bin/bash

# 4. 检查环境变量是否正确
docker exec -it cbg-fastapi-app env | grep MYSQL
docker exec -it cbg-fastapi-app env | grep MINIO

# 5. 测试数据库连接
docker exec -it cbg-fastapi-app python -c "
import pymysql
try:
    conn = pymysql.connect(
        host='$MYSQL_HOST',
        port=int('$MYSQL_PORT'),
        user='$MYSQL_USER',
        password='$MYSQL_PASSWORD',
        database='$MYSQL_DATABASE'
    )
    print('✅ 数据库连接成功')
    conn.close()
except Exception as e:
    print(f'❌ 数据库连接失败: {e}')
"

# 6. 测试MinIO连接
docker exec -it cbg-fastapi-app python -c "
from minio import Minio
try:
    client = Minio('$MINIO_ENDPOINT',
                   access_key='$MINIO_ACCESS_KEY',
                   secret_key='$MINIO_SECRET_KEY',
                   secure=False)
    buckets = client.list_buckets()
    print(f'✅ MinIO连接成功，共有 {len(list(buckets))} 个存储桶')
except Exception as e:
    print(f'❌ MinIO连接失败: {e}')
"
```

**常见原因**:
- ❌ 数据库连接失败：检查MySQL服务是否运行、网络是否可达、凭据是否正确
- ❌ MinIO连接失败：检查MinIO服务状态、endpoint地址、access key
- ❌ 端口冲突：修改 `.env` 中的 PORT 配置
- ❌ 内存不足：增加服务器内存或限制容器资源使用

### 高级调试技巧

#### 实时监控应用运行状态
```bash
# 实时查看应用日志（带时间戳）
docker-compose logs -f --timestamps cbg-app

# 只查看错误日志
docker-compose logs cbg-app 2>&1 | grep -i error

# 监控容器资源使用
docker stats cbg-fastapi-app

# 查看容器详细信息
docker inspect cbg-fastapi-app
```

#### 在容器内执行交互式调试
```bash
# 进入容器bash环境
docker exec -it cbg-fastapi-app /bin/bash

# 在容器内执行Python交互模式
docker exec -it cbg-fastapi-app python

# 测试导入模块
docker exec -it cbg-fastapi-app python -c "from app.models import User; print('Models OK')"

# 检查文件是否存在
docker exec -it cbg-fastapi-app ls -la /app/app/

# 查看配置文件
docker exec -it cbg-fastapi-app cat /app/.env
```

#### 网络和连接性测试
```bash
# 在容器内测试DNS解析
docker exec -it cbg-fastapi-app nslookup $MYSQL_HOST

# 测试端口连通性
docker exec -it cbg-fastapi-app python -c "
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex(('$MYSQL_HOST', $MYSQL_PORT))
if result == 0:
    print('✅ 端口可达')
else:
    print('❌ 端口不可达')
sock.close()
"

# 检查Docker网络
docker network inspect cbg-fast-api_cbg-network

# 测试从容器访问外部服务
docker exec -it cbg-fastapi-app curl -I http://$MINIO_ENDPOINT:9000
```

## 📊 性能优化最佳实践

### 构建阶段优化

- ✅ 使用 `.dockerignore` 排除不必要的文件（__pycache__, .git, logs等）
- ✅ 采用多阶段构建减少最终镜像大小（当前已实现）
- ✅ 配置清华源加速依赖下载（已在Dockerfile中配置）
- ✅ 合理组织Dockerfile指令，利用层缓存机制

### 运行阶段优化
- ✅ 文件映射（volume）避免重复构建，代码更新只需重启容器
- ✅ 配置健康检查确保服务异常时自动恢复（已配置）
- ✅ 设置自动重启策略 `restart: unless-stopped`（已配置）
- ✅ 限制容器资源使用（建议在docker-compose.yml中添加）:
  ```yaml
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 2G
      reservations:
        cpus: '0.5'
        memory: 512M
  ```

### 数据库查询优化
- ✅ 使用SQLAlchemy的 `joinedload` 和 `selectinload` 预加载关联数据
- ✅ 列表接口选择性加载关联字段，避免N+1查询问题
- ✅ 为常用查询字段添加索引（已在模型中配置）
- ✅ 分页查询限制最大page_size（当前最大100）

## 🔄 版本升级与维护

### 应用版本升级流程

1. **备份当前状态**
   ```bash
   # 备份数据库（根据实际情况调整）
   mysqldump -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE > backup_$(date +%Y%m%d_%H%M%S).sql
   
   # 备份配置文件
   cp .env .env.backup_$(date +%Y%m%d_%H%M%S)
   
   # 备份当前镜像标签（可选）
   docker tag cbg-fastapi-app:latest cbg-fastapi-app:backup_$(date +%Y%m%d)
   ```

2. **拉取最新代码**
   ```bash
   git pull origin main
   # 或
git fetch && git checkout <target-version>
   ```

3. **检查依赖变化**
   ```bash
   # 查看requirements.txt是否有变化
   git diff HEAD@{1} requirements.txt
   
   # 如有变化，重新构建镜像
docker-compose build --no-cache
   ```

4. **重启服务并验证**
   ```bash
   # 滚动重启（零停机）
   docker-compose up -d --no-deps cbg-app
   
   # 等待健康检查通过
docker-compose ps
   
   # 验证API是否正常
curl http://localhost:8000/health
   ```

5. **运行数据库迁移**（如需要）
   ```bash
   docker exec -it cbg-fastapi-app alembic upgrade head
   ```

### 紧急回滚方案

如果升级后出现严重问题，立即执行回滚：

```bash
# 1. 停止当前服务
docker-compose down

# 2. 恢复代码到之前版本
git reset --hard <previous-commit-hash>
# 或
git checkout <previous-tag>

# 3. 恢复配置文件（如已修改）
cp .env.backup_<timestamp> .env

# 4. 恢复数据库（如执行了迁移）
mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE < backup_<timestamp>.sql

# 5. 重新启动服务
docker-compose up -d

# 6. 验证服务恢复正常
curl http://localhost:8000/health
docker-compose logs -f cbg-app
```

### 日常维护任务
- **每日**: 检查应用日志，关注错误和警告信息
  ```bash
  docker-compose logs --tail=50 cbg-app | grep -i "error\|warning"
  ```
  
- **每周**: 检查磁盘空间使用情况，清理旧日志文件
  ```bash
  # 查看Docker占用空间
  docker system df
  
  # 清理未使用的镜像和容器
  docker system prune -a
  
  # 清理日志文件
  find ./logs -name "*.log" -mtime +7 -delete
  ```
  
- **每月**: 更新基础镜像和依赖包，修复安全漏洞
  ```bash
  # 拉取最新基础镜像
  docker pull python:3.9-slim
  
  # 重新构建应用镜像
  docker-compose build --pull --no-cache
  
  # 重启服务
  docker-compose up -d
  ```
  
- **每季度**: 审查和优化数据库索引，清理无用数据
  ```bash
  # 进入数据库执行分析
  mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p$MYSQL_PASSWORD $MYSQL_DATABASE
  
  # 在MySQL中执行
  SHOW INDEX FROM fabrics;
  ANALYZE TABLE fabrics, projects, patterns, items;
  ```

---
**部署完成！** 🎉

有任何问题请及时反馈。