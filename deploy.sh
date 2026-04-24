#!/bin/bash
# CBG FastAPI 一键部署脚本 (Linux/macOS版本)
# 作者: Lingma
# 日期: 2026-03-02

set -e  # 遇到错误立即退出

echo "========================================"
echo "   CBG FastAPI 应用一键部署脚本"
echo "========================================"
echo ""

# 检查 Docker 是否安装
echo "[1/6] 检查 Docker 环境..."
if ! command -v docker &> /dev/null; then
    echo "❌ 错误: 未检测到 Docker，请先安装 Docker"
    exit 1
fi
echo "✅ Docker 已安装 ($(docker --version))"

# 检查 docker-compose 是否可用
if ! command -v docker-compose &> /dev/null; then
    echo "❌ 错误: 未检测到 docker-compose"
    exit 1
fi
echo "✅ docker-compose 可用 ($(docker-compose --version))"

# 检查 .env 文件是否存在
echo "[2/6] 检查配置文件..."
if [ ! -f ".env" ]; then
    echo "❌ 错误: 找不到 .env 配置文件"
    echo "请确保 .env 文件存在并包含正确的配置信息"
    exit 1
fi
echo "✅ 配置文件已找到"

# 创建日志目录
echo "[3/6] 创建日志目录..."
mkdir -p logs
echo "✅ 日志目录已创建"

# 构建 Docker 镜像
echo "[4/6] 构建 Docker 镜像..."
echo "正在构建镜像，请稍候..."
# 先清理之前的构建缓存，避免产生过多中间容器
docker builder prune -f > /dev/null 2>&1 || true
docker-compose build --no-cache
echo "✅ 镜像构建成功"

# 启动服务
echo "[5/6] 启动服务..."
# 先停止并移除可能存在的旧容器
docker-compose down -v --remove-orphans > /dev/null 2>&1 || true
docker-compose up -d
echo "✅ 服务启动成功"

# 显示状态
echo "[6/6] 显示服务状态..."
echo ""
echo "========================================"
echo "   部署完成！服务信息如下："
echo "========================================"
docker-compose ps
echo ""
PORT=$(grep "^PORT=" .env | cut -d'=' -f2)
if [ -z "$PORT" ]; then
    PORT="8000"
fi
echo "访问地址: http://localhost:$PORT"
echo "API文档: http://localhost:$PORT/docs"
echo "健康检查: http://localhost:$PORT/health"
echo ""
echo "如需管理服务，请运行 ./manage.sh 脚本"
echo "========================================"