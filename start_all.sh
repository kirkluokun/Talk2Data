#!/bin/bash

# 颜色设置
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # 无颜色

# 保存进程ID的数组
declare -a PIDS

# 输出彩色文本的函数
print_color() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# 检查Docker容器是否运行
check_docker_container() {
    local container_name=$1
    if docker ps --filter name=$container_name --format '{{.Names}}' | grep -q $container_name; then
        return 0 # 正在运行
    else
        return 1 # 未运行
    fi
}

# 启动Redis
start_redis() {
    if check_docker_container "redis"; then
        print_color "$GREEN" "Redis已经在运行中"
    else
        print_color "$YELLOW" "正在启动Redis..."
        if docker-compose up -d redis; then
            print_color "$GREEN" "Redis启动成功"
        else
            print_color "$RED" "Redis启动失败"
            return 1
        fi
    fi
    return 0
}

# 启动Postgres
start_postgres() {
    if check_docker_container "postgres"; then
        print_color "$GREEN" "Postgres已经在运行中"
    else
        print_color "$YELLOW" "正在启动Postgres..."
        if docker-compose up -d postgres; then
            print_color "$GREEN" "Postgres启动成功"
        else
            print_color "$RED" "Postgres启动失败"
            return 1
        fi
    fi
    return 0
}

# 检查Celery是否运行
check_celery_running() {
    if pgrep -f "celery -A src.tasks.celery_app worker" > /dev/null; then
        return 0 # 正在运行
    else
        return 1 # 未运行
    fi
}

# 启动Celery Worker
start_celery() {
    if check_celery_running; then
        print_color "$GREEN" "Celery Worker已经在运行中"
    else
        print_color "$YELLOW" "正在启动Celery Worker..."
        python -m celery -A src.tasks.celery_app worker --loglevel=info &
        PIDS+=($!)
        
        # 等待几秒检查是否成功启动
        sleep 3
        if check_celery_running; then
            print_color "$GREEN" "Celery Worker启动成功"
        else
            print_color "$RED" "Celery Worker可能未成功启动，请检查日志"
            return 1
        fi
    fi
    return 0
}

# 检查FastAPI是否运行
check_fastapi_running() {
    if pgrep -f "uvicorn src.agent.api_workflow:app" > /dev/null; then
        return 0 # 正在运行
    else
        # 尝试通过健康检查端点检查
        if curl -s -o /dev/null -w "%{http_code}" http://localhost:8010/health 2>/dev/null | grep -q "200"; then
            return 0 # 正在运行
        else
            return 1 # 未运行
        fi
    fi
}

# 启动FastAPI
start_fastapi() {
    if check_fastapi_running; then
        print_color "$GREEN" "FastAPI后端已经在运行中"
    else
        print_color "$YELLOW" "正在启动FastAPI后端..."
        uvicorn src.agent.api_workflow:app --reload --port 8010 &
        PIDS+=($!)
        
        # 等待API启动
        local max_attempts=5
        local attempt=0
        while [ $attempt -lt $max_attempts ]; do
            sleep 2
            if check_fastapi_running; then
                print_color "$GREEN" "FastAPI后端启动成功"
                return 0
            fi
            attempt=$((attempt + 1))
        done
        
        print_color "$RED" "FastAPI后端可能未成功启动，请检查日志"
        return 1
    fi
    return 0
}

# 检查前端开发服务器是否运行
check_npm_dev_running() {
    if pgrep -f "npm run dev" > /dev/null; then
        return 0 # 正在运行
    else
        return 1 # 未运行
    fi
}

# 启动前端开发服务器
start_npm_dev() {
    if check_npm_dev_running; then
        print_color "$GREEN" "前端开发服务器已经在运行中"
    else
        print_color "$YELLOW" "正在启动前端开发服务器..."
        
        # 确保我们在正确的目录
        if [ -d "src/web" ]; then
            cd src/web
            npm run dev &
            PIDS+=($!)
            cd - > /dev/null  # 返回之前的目录
            
            # 等待几秒检查是否成功启动
            sleep 5
            if check_npm_dev_running; then
                print_color "$GREEN" "前端开发服务器启动成功"
            else
                print_color "$RED" "前端开发服务器可能未成功启动，请检查日志"
                return 1
            fi
        else
            print_color "$RED" "找不到src/web目录"
            return 1
        fi
    fi
    return 0
}

# 清理函数
cleanup() {
    print_color "$YELLOW" "正在关闭所有服务..."
    for pid in "${PIDS[@]}"; do
        if kill -0 $pid 2>/dev/null; then
            kill $pid
            print_color "$YELLOW" "已关闭PID为${pid}的进程"
        fi
    done
    exit 0
}

# 主函数
main() {
    print_color "$GREEN" "=== 服务启动脚本 ==="
    
    # 注册信号处理
    trap cleanup SIGINT SIGTERM
    
    # 启动Redis（必须）
    if ! start_redis; then
        print_color "$RED" "Redis启动失败，终止启动流程"
        exit 1
    fi
    
    # 启动Postgres（如果需要）
    start_postgres
    
    # 启动Celery Worker
    if ! start_celery; then
        print_color "$YELLOW" "警告: Celery Worker未成功启动，但将继续启动其他服务"
    fi
    
    # 启动FastAPI后端
    if ! start_fastapi; then
        print_color "$RED" "FastAPI后端启动失败"
        cleanup
        exit 1
    fi
    
    # 启动前端开发服务器
    if ! start_npm_dev; then
        print_color "$YELLOW" "警告: 前端开发服务器未成功启动，但所有后端服务已启动"
    fi
    
    print_color "$GREEN" "所有服务已启动完成!"
    print_color "$YELLOW" "按 Ctrl+C 可以停止所有服务"
    
    # 保持脚本运行，这样可以通过按Ctrl+C来停止所有服务
    while true; do
        sleep 1
    done
}

# 执行主函数
main 