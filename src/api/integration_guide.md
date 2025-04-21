# API认证集成指南

本文档提供将认证功能集成到现有API中的指导。

## 1. 集成方式

有两种方式可以集成认证功能:

### 方式1: 直接修改现有API路由

这种方式是直接在现有API路由中添加认证依赖项。例如，在`src/agent/api_workflow.py`中:

```python
from src.api.deps import get_current_active_user
from src.db.models.user import User

# 修改前
@app.post("/api/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    # 原有逻辑...

# 修改后
@app.post("/api/query", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    current_user: User = Depends(get_current_active_user)
):
    # 原有逻辑...
    # 可以使用current_user获取当前用户信息
```

### 方式2: 使用APIRouter替代直接装饰器

这种方式是将现有API路由重构为使用APIRouter:

```python
from fastapi import APIRouter, Depends
from src.api.deps import get_current_active_user
from src.db.models.user import User

router = APIRouter()

@router.post("/query", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    current_user: User = Depends(get_current_active_user)
):
    # 原有逻辑...

# 在主应用中
app.include_router(
    router,
    prefix="/api",
    dependencies=[Depends(get_current_active_user)]  # 为所有路由添加认证
)
```

## 2. 需要保护的API列表

根据项目要求，以下API接口需要添加认证保护:

1. `POST /api/query` - 查询接口
2. `GET /api/jobs/{job_id}` - 获取任务状态
3. `GET /api/jobs` - 获取任务列表
4. `GET /api/file/{file_path:path}` - 文件下载接口
5. `POST /api/test` - 测试接口

## 3. 集成步骤

1. **确保数据库和认证服务正常运行**
   - 数据库容器需要启动
   - 认证相关的代码已经添加到项目中

2. **在主应用中添加认证路由**
   ```python
   from src.api.api import api_router
   
   # 添加API路由
   app.include_router(api_router)
   ```

3. **为需要保护的接口添加认证依赖**
   ```python
   from src.api.deps import get_current_active_user
   
   @app.post("/api/query", response_model=QueryResponse)
   async def query(
       request: QueryRequest,
       current_user: User = Depends(get_current_active_user)
   ):
       # 原有逻辑...
   ```

4. **处理前端认证**
   - 前端需要在请求头中添加认证信息:
   ```javascript
   fetch('/api/query', {
     method: 'POST',
     headers: {
       'Authorization': `Bearer ${token}`,
       'Content-Type': 'application/json'
     },
     body: JSON.stringify(data)
   })
   ```

5. **测试认证功能**
   - 使用认证接口创建用户并获取令牌
   - 使用令牌请求受保护的API接口

## 4. 注意事项

1. **平滑迁移**
   - 可以先为一部分不太关键的API添加认证
   - 测试无误后再逐步添加到其他API

2. **错误处理**
   - 认证失败时返回401错误
   - 提供清晰的错误信息

3. **令牌过期处理**
   - 前端需要处理令牌过期的情况
   - 令牌过期时自动跳转到登录页面

4. **日志记录**
   - 记录认证相关的日志，便于问题排查

## 5. 示例代码

假设我们要为`/api/query`接口添加认证:

```python
# 现有代码
@app.post("/api/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    # 处理查询请求
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "PENDING", "result": None}
    query_task.delay(job_id, request.query)
    return {"job_id": job_id}

# 修改后的代码
@app.post("/api/query", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    current_user: User = Depends(get_current_active_user)
):
    # 处理查询请求
    job_id = str(uuid.uuid4())
    # 可以关联任务和用户
    jobs[job_id] = {
        "status": "PENDING", 
        "result": None,
        "user_id": current_user.id
    }
    query_task.delay(job_id, request.query)
    return {"job_id": job_id}
``` 