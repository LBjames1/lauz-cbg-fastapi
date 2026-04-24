#!/bin/bash
# CBG FastAPI 容器管理脚本 (Linux/macOS版本)
# 作者: Lingma
# 日期: 2026-03-02

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查是否在项目根目录
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}错误: 请在项目根目录运行此脚本${NC}"
    exit 1
fi

show_menu() {
    clear
    echo "========================================"
    echo "   CBG FastAPI 容器管理工具"
    echo "========================================"
    echo ""
    echo "请选择操作："
    echo "1. 启动服务"
    echo "2. 停止服务"
    echo "3. 重启服务"
    echo "4. 查看服务状态"
    echo "5. 查看日志"
    echo "6. 进入容器bash"
    echo "7. 更新代码并重启"
    echo "8. 清理不必要容器"
    echo "9. 删除所有容器和镜像"
    echo "10. 退出"
    echo ""
}

start_service() {
    echo -e "${BLUE}[操作] 正在启动服务...${NC}"
    docker-compose up -d
    echo -e "${GREEN}✅ 服务启动完成！${NC}"
    show_status
}

stop_service() {
    echo -e "${BLUE}[操作] 正在停止服务...${NC}"
    docker-compose down
    echo -e "${GREEN}✅ 服务已停止！${NC}"
}

restart_service() {
    echo -e "${BLUE}[操作] 正在重启服务...${NC}"
    docker-compose down
    docker-compose up -d
    echo -e "${GREEN}✅ 服务重启完成！${NC}"
    show_status
}

show_status() {
    echo ""
    echo -e "${BLUE}当前服务状态：${NC}"
    echo "========================================"
    docker-compose ps
    echo "========================================"
    
    # 显示访问信息
    if docker-compose ps | grep -q "Up"; then
        PORT=$(grep "^PORT=" .env | cut -d'=' -f2)
        if [ -z "$PORT" ]; then
            PORT="8000"
        fi
        echo ""
        echo -e "${GREEN}应用查看地址:${NC} http://localhost:$PORT"
        echo -e "${GREEN}API文档地址:${NC} http://localhost:$PORT/docs"
        echo -e "${GREEN}健康检查地址:${NC} http://localhost:$PORT/health"
    fi
}

show_logs() {
    echo ""
    echo -e "${BLUE}实时查看日志 (按 Ctrl+C 退出):${NC}"
    echo "========================================"
    docker-compose logs -f
}

enter_container() {
    echo ""
    echo -e "${BLUE}进入容器 bash 环境:${NC}"
    echo "========================================"
    if docker exec -it cbg-fastapi-app /bin/bash; then
        echo -e "${GREEN}已退出容器${NC}"
    else
        echo -e "${RED}无法进入容器，请检查服务是否运行${NC}"
    fi
}

update_code() {
    echo ""
    echo -e "${BLUE}[操作] 正在更新代码并重启服务...${NC}"
    echo "注意：由于使用了文件映射，代码更新会自动生效"
    docker-compose restart
    echo -e "${GREEN}✅ 代码更新并重启完成！${NC}"
    show_status
}

clean_containers() {
    echo ""
    echo -e "${BLUE}[操作] 正在清理不必要容器...${NC}"
    
    # 清理已停止的非项目容器
    stopped_non_project=$(docker ps -aq --filter "status=exited" --filter "name!=cbg-fastapi-app" --filter "name!=cbg-fastapi-app-alt")
    if [ ! -z "$stopped_non_project" ]; then
        docker rm $stopped_non_project 2>/dev/null || true
        echo -e "${GREEN}✅ 已清理已停止的非项目容器${NC}"
    else
        echo "没有需要清理的已停止容器"
    fi
    
    # 清理悬空镜像
    dangling_images=$(docker images -q -f dangling=true)
    if [ ! -z "$dangling_images" ]; then
        docker rmi $dangling_images 2>/dev/null || true
        echo -e "${GREEN}✅ 已清理悬空镜像${NC}"
    fi
    
    # 清理构建缓存
    docker builder prune -f 2>/dev/null || true
    echo -e "${GREEN}✅ 已清理构建缓存${NC}"
    
    # 清理未使用的卷
    docker volume prune -f 2>/dev/null || true
    echo -e "${GREEN}✅ 已清理未使用卷${NC}"
    
    echo ""
    echo -e "${BLUE}清理后容器状态:${NC}"
    echo "========================================"
    docker ps -a
    echo "========================================"
}

clean_all() {
    echo ""
    echo -e "${YELLOW}⚠️  警告：此操作将删除所有容器和镜像！${NC}"
    read -p "确认继续吗？(输入 YES 确认): " confirm
    if [[ "$confirm" == "YES" ]]; then
        echo -e "${BLUE}[操作] 正在清理...${NC}"
        docker-compose down -v --remove-orphans
        docker rmi cbg-fast-api_cbg-app 2>/dev/null || true
        echo -e "${GREEN}✅ 清理完成！${NC}"
    else
        echo -e "${YELLOW}已取消操作${NC}"
    fi
}

# 主循环
while true; do
    show_menu
    read -p "请输入选项 (1-10): " choice
    
    case $choice in
        1) start_service ;;
        2) stop_service ;;
        3) restart_service ;;
        4) show_status ;;
        5) show_logs ;;
        6) enter_container ;;
        7) update_code ;;
        8) clean_containers ;;
        9) clean_all ;;
        10) 
            echo "再见！"
            exit 0
            ;;
        *)
            echo -e "${RED}无效选项，请重新选择${NC}"
            sleep 2
            ;;
    esac
    
    echo ""
    read -p "按回车键继续..." dummy
done