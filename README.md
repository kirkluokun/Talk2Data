# 金融数据聊天应用

基于 FastAPI、Celery 和 LLM 构建的金融数据查询分析聊天应用，提供自然语言查询金融数据的能力。

## 功能特点

- 自然语言查询解析
- 金融数据获取与分析
- 数据可视化展示
- 异步任务处理
- 实时进度监控
- Web 前端界面

## 系统架构

- **前端**：基于 React/Next.js 构建的 Web 界面
- **后端**：FastAPI 提供 RESTful API
- **任务队列**：Celery + Redis 处理异步任务
- **数据库**：PostgreSQL 存储用户数据和查询记录
- **LLM 引擎**：集成多种 LLM 模型，用于自然语言处理

## 环境要求

- Python 3.10+
- Node.js 18+
- Docker 和 Docker Compose
- Redis
- PostgreSQL

## 安装指南

### macOS 系统

1. **克隆项目**
   ```bash
   git clone https://github.com/yourusername/FinancialDataChatApp.git
   cd FinancialDataChatApp
   ```

2. **安装 Python 依赖**
   ```bash
   # 创建并激活虚拟环境
   python -m venv .venv
   source .venv/bin/activate
   
   # 安装依赖
   pip install -r requirements.txt
   ```

3. **安装 Node.js 依赖**
   ```bash
   cd src/web
   npm install
   cd ../..
   ```

4. **安装 Docker**
   - 从 [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/) 下载并安装

5. **环境配置**
   ```bash
   # 复制环境变量示例文件
   cp .env.example .env
   
   # 编辑 .env 文件，填入所需的 API 密钥和配置
   vi .env  # 或使用其他编辑器
   ```

### Windows 系统

1. **克隆项目**
   ```cmd
   git clone https://github.com/yourusername/FinancialDataChatApp.git
   cd FinancialDataChatApp
   ```

2. **安装 Python 依赖**
   ```cmd
   # 创建并激活虚拟环境
   python -m venv .venv
   .venv\Scripts\activate
   
   # 安装依赖
   pip install -r requirements.txt
   
   # 安装 gevent (Windows 上运行 Celery 需要)
   pip install gevent
   ```

3. **安装 Node.js 依赖**
   ```cmd
   cd src\web
   npm install
   cd ..\..
   ```

4. **安装 Docker**
   - 从 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) 下载并安装
   - 确保开启 WSL 2 后端和 Hyper-V 功能

5. **环境配置**
   ```cmd
   # 复制环境变量示例文件
   copy .env.example .env
   
   # 编辑 .env 文件，填入所需的 API 密钥和配置
   notepad .env  # 或使用其他编辑器
   ```

## 数据库初始化

### macOS 和 Linux
```bash
# 启动 PostgreSQL 容器
docker-compose up -d postgres

# 运行数据库迁移
alembic upgrade head
```

### Windows
```cmd
# 启动 PostgreSQL 容器
docker-compose up -d postgres

# 运行数据库迁移
alembic upgrade head
```

## 启动应用

### macOS 和 Linux

使用提供的启动脚本一键启动所有服务：
```bash
# 添加执行权限
chmod +x start_all.sh

# 执行启动脚本
./start_all.sh
```

或手动启动各个组件：

```bash
# 启动 Redis 和 PostgreSQL
docker-compose up -d redis postgres

# 启动 Celery Worker
celery -A src.tasks.celery_app worker --loglevel=info

# 启动 FastAPI 后端
uvicorn src.agent.api_workflow:app --reload --port 8010

# 启动前端开发服务器
cd src/web
npm run dev
```

### Windows

Windows 系统可以使用提供的批处理脚本一键启动所有服务：

```cmd
# 执行启动脚本
start_windows.bat
```

该脚本将：
- 启动 Redis 和 PostgreSQL 容器
- 自动检测并激活虚拟环境
- 在单独的窗口中启动 Celery Worker (使用 gevent 池)
- 在单独的窗口中启动 FastAPI 后端
- 在单独的窗口中启动前端开发服务器

或手动启动各个组件：

```cmd
# 启动 Redis 和 PostgreSQL
docker-compose up -d redis postgres

# 启动 Celery Worker (在一个命令行窗口中)
celery -A src.tasks.celery_app worker --loglevel=info --pool=gevent

# 启动 FastAPI 后端 (在另一个命令行窗口中)
uvicorn src.agent.api_workflow:app --reload --port 8010

# 启动前端开发服务器 (在第三个命令行窗口中)
cd src\web
npm run dev
```

## 访问应用

服务启动后，可通过以下地址访问：

- **Web 前端**：http://localhost:3000
- **API 文档**：http://localhost:8010/docs
- **API 健康检查**：http://localhost:8010/health

## 常见问题

### macOS 和 Linux

1. **Redis 或 PostgreSQL 无法启动**
   - 检查 Docker 服务是否运行
   - 检查端口是否被占用：`lsof -i :6379` 或 `lsof -i :5432`
   - 尝试重启 Docker：`docker-compose down && docker-compose up -d`

2. **Celery Worker 无法启动**
   - 确认 Redis 已启动
   - 检查环境变量配置是否正确
   - 尝试使用 `--pool=solo` 选项：`celery -A src.tasks.celery_app worker --loglevel=info --pool=solo`

### Windows

1. **Redis 或 PostgreSQL 无法启动**
   - 检查 Docker Desktop 是否运行
   - 检查端口是否被占用：`netstat -ano | findstr 6379` 或 `netstat -ano | findstr 5432`
   - 尝试重启 Docker：`docker-compose down && docker-compose up -d`

2. **Celery Worker 无法启动**
   - Windows 系统运行 Celery 需要额外配置
   - 确保已安装 gevent：`pip install gevent`
   - 使用 gevent 池：`celery -A src.tasks.celery_app worker --loglevel=info --pool=gevent`
   - 如果仍有问题，尝试：`set FORKED_BY_MULTIPROCESSING=1` 后再启动 Celery

3. **批处理脚本不显示彩色文本**
   - Windows 命令提示符默认不支持ANSI颜色代码
   - 考虑使用 Windows Terminal 代替默认 CMD

## 许可证

此项目采用 MIT 许可证 - 详细信息请查看 LICENSE 文件
# Talk2Data
# Talk2Data
