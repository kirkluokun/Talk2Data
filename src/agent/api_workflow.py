"""
金融数据查询API工作流模块

此模块使用FastAPI框架提供金融数据查询的API接口，封装了整个查询处理流程：
1. 查询解析 (QueryParserAgent)
2. 数据获取 (DataFetcherAgent)
3. 数据分析和可视化 (PandasAIAgent)

主要功能：
1. 提供API接口处理金融数据查询
2. 管理查询工作流的每个步骤
3. 提供查询状态的监测点
4. 保存和管理查询结果
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import (
    FastAPI, HTTPException, Body, Query, Depends, status
)
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from celery.result import AsyncResult
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession

# 获取项目根目录
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(parent_dir)  # 项目根目录
sys.path.insert(0, parent_dir)

# 导入配置和类型
from core.config import ProgressStages, ProgressPercentage

# 导入Celery应用
from tasks.celery_app import celery_app
try:
    from tasks.financial_query import process_financial_query
except ImportError:
    # 为了处理潜在的导入问题
    print("警告: 无法直接导入process_financial_query，将使用celery_app.send_task")
    process_financial_query = None

# 导入认证依赖和数据库
from src.api.deps import get_current_active_user, get_db
from src.db.models.user import User
from src.db import crud

# 导入认证路由
from src.api.api import api_router


# API请求和响应模型
class QueryRequest(BaseModel):
    """查询请求模型"""
    query: str = Field(..., description="用户的自然语言查询")
    save_intermediate: bool = Field(True, description="是否保存中间结果")
    conversation_id: Optional[int] = Field(None, description="对话ID，不提供则创建新对话")


class QueryResponse(BaseModel):
    """查询响应模型"""
    job_id: str = Field(..., description="查询任务ID")
    status: str = Field(
        ..., 
        description="任务状态：pending, processing, completed, error"
    )
    message: str = Field(..., description="状态消息")
    query: str = Field(..., description="原始查询")
    timestamp: str = Field(..., description="查询时间戳")
    output_dir: str = Field(..., description="输出目录路径")
    conversation_id: int = Field(..., description="对话ID")


class JobStatusResponse(BaseModel):
    """任务状态响应模型"""
    job_id: str = Field(..., description="查询任务ID")
    status: str = Field(..., description="任务状态")
    stage: str = Field(..., description="当前处理阶段")
    progress: float = Field(..., description="进度百分比")
    files: Dict[str, List[str]] = Field(
        default_factory=dict, 
        description="生成的文件"
    )
    results: Optional[Dict[str, Any]] = Field(None, description="查询结果")
    error: Optional[str] = Field(None, description="错误信息")


# 创建FastAPI应用
app = FastAPI(
    title="金融数据查询API",
    description="提供金融数据查询和分析的API接口",
    version="1.0.0"
)


# 健康检查接口
@app.get("/health")
async def health_check():
    """健康检查接口
    
    Returns:
        Dict: 状态信息
    """
    return {"status": "ok", "message": "服务正常运行"}

# 添加认证路由
app.include_router(api_router, prefix="/api")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建静态文件目录
os.makedirs("output", exist_ok=True)

# 添加静态文件服务
app.mount("/output", StaticFiles(directory="output"), name="output")


def get_timestamp() -> str:
    """获取当前时间戳
    
    Returns:
        str: 格式化的时间戳字符串
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def map_celery_state_to_job_status(celery_state: str) -> str:
    """将Celery任务状态映射到作业状态
    
    Args:
        celery_state: Celery任务状态
        
    Returns:
        str: 作业状态
    """
    status_map = {
        'PENDING': 'pending',
        'STARTED': 'processing',
        'PROGRESS': 'processing',
        'SUCCESS': 'completed',
        'FAILURE': 'failed',
        'REVOKED': 'cancelled',
        'RETRY': 'processing'
    }
    return status_map.get(celery_state, 'unknown')


def convert_absolute_to_relative_path(path, root_dir):
    """将绝对路径转换为相对路径
    
    Args:
        path: 绝对路径
        root_dir: 项目根目录
        
    Returns:
        str: 转换后的相对路径
    """
    if not path or not isinstance(path, str):
        return path
        
    # 去除路径中可能包含的项目根目录部分
    if path.startswith(root_dir):
        path = path[len(root_dir):].lstrip('/')
    
    # 确保路径不包含 ./output/ 或 ../output/ 前缀
    path = path.replace('./output/', 'output/')
    path = path.replace('../output/', 'output/')
    
    # 处理 output 路径
    if not path.startswith('output/') and 'output/' in path:
        path = path[path.index('output/'):]
        
    return path


def process_paths_in_dict(data, root_dir):
    """递归处理字典中的文件路径
    
    Args:
        data: 需要处理的数据
        root_dir: 项目根目录
        
    Returns:
        dict: 处理后的数据
    """
    if not isinstance(data, dict):
        return data
        
    for key, value in data.items():
        if isinstance(value, dict):
            data[key] = process_paths_in_dict(value, root_dir)
        elif isinstance(value, list):
            data[key] = [
                convert_absolute_to_relative_path(item, root_dir) 
                if isinstance(item, str) else item 
                for item in value
            ]
        elif isinstance(value, str) and (
            'path' in key.lower() or key in ['output_dir']
        ):
            data[key] = convert_absolute_to_relative_path(value, root_dir)
            
    return data


@app.post("/api/query", response_model=QueryResponse)
async def submit_query(
    request: QueryRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> QueryResponse:
    """提交查询请求
    
    Args:
        request: 查询请求
        current_user: 当前认证用户
        db: 数据库会话
        
    Returns:
        QueryResponse: 查询响应，包含 conversation_id
    """
    try:
        # 处理conversation_id
        conversation_id = request.conversation_id
        if conversation_id is None:
            # 如果未提供对话ID，创建新对话
            from src.schemas.conversation import ConversationCreate
            conversation = await crud.conversation.create_conversation(
                db=db,
                conv_in=ConversationCreate(
                    title=f"查询: {request.query[:30]}..."
                ),
                user=current_user
            )
            await db.flush()  # 确保数据库分配了ID
            await db.refresh(conversation) # 获取最新状态，包括ID
            conversation_id = conversation.id 
            # 提交事务，以便后续 Job 可以关联到它
            await db.commit()
        else:
            # 验证对话归属
            conversation = await crud.conversation.get_conversation_by_id(
                db=db,
                conversation_id=conversation_id,
                user_id=current_user.id
            )
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="未找到指定的对话或该对话不属于当前用户"
                )
        
        # 获取任务名称 (与 Celery 装饰器中的 name 保持一致)
        task_name = 'tasks.financial_query.process_financial_query'
        
        # 检查任务是否已注册
        if task_name not in celery_app.tasks:
            registered_tasks = list(celery_app.tasks.keys())
            print(
                f"警告: 任务 '{task_name}' 未注册。"
                f"已注册的任务: {registered_tasks}"
            )
            
            # 尝试使用我们在开头导入的任务，或者使用备用名称
            if process_financial_query:
                print("使用已导入的process_financial_query任务")
                task = process_financial_query.delay(
                    query=request.query,
                    user_id=current_user.id,
                    conversation_id=conversation_id,
                    save_intermediate=request.save_intermediate
                )
            else:
                # 尝试使用可能的备用名称
                alternate_name = (
                    'tasks.financial_query.process_financial_query'
                )
                if alternate_name in celery_app.tasks:
                    print(f"使用备用任务名称: {alternate_name}")
                    task_name = alternate_name
                    task = celery_app.send_task(
                        task_name,
                        kwargs={
                            "query": request.query,
                            "user_id": current_user.id,
                            "conversation_id": conversation_id,
                            "save_intermediate": request.save_intermediate
                        }
                    )
                else:
                    # 如果所有尝试都失败，仍然使用原始名称，但提供警告
                    print(f"未找到任务，尝试使用原始名称: {task_name}")
                    task = celery_app.send_task(
                        task_name,
                        kwargs={
                            "query": request.query,
                            "user_id": current_user.id,
                            "conversation_id": conversation_id,
                            "save_intermediate": request.save_intermediate
                        }
                    )
        else:
            # 任务已注册，直接使用
            print(f"任务 '{task_name}' 已注册，发送请求")
            task = celery_app.send_task(
                task_name,
                kwargs={
                    "query": request.query,
                    "user_id": current_user.id,
                    "conversation_id": conversation_id,
                    "save_intermediate": request.save_intermediate
                }
            )
        
        # 任务处理异常时返回错误
        if not task or not task.id:
            return QueryResponse(
                    job_id="error",
                    status="error",
                    message="无法启动查询任务，请检查Celery Worker是否运行",
                    query=request.query,
                    timestamp=get_timestamp(),
                    output_dir="error",
                    conversation_id=conversation_id
                )
        
        # 启动任务
        job_id = task.id
    
        # 记录查询时间戳
        timestamp = get_timestamp()
    
        # 创建输出目录
        output_dir = os.path.join(root_dir, f"output/{timestamp}_{job_id}")
        os.makedirs(output_dir, exist_ok=True)
    
        # 返回任务信息
        return QueryResponse(
            job_id=job_id,
            status="pending",
            message="查询已提交，正在处理中",
            query=request.query,
            timestamp=timestamp,
            output_dir=output_dir,
            conversation_id=conversation_id
        )
    except Exception as e:
        # 处理异常
        print(f"启动任务异常: {str(e)}")
        return QueryResponse(
            job_id="error",
            status="error",
            message=f"启动任务异常: {str(e)}",
            query=request.query,
            timestamp=get_timestamp(),
            output_dir="error",
            conversation_id=conversation_id
        )


@app.get("/api/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> JobStatusResponse:
    """获取任务状态
    
    Args:
        job_id: 任务ID
        current_user: 当前认证用户
        db: 数据库会话
        
    Returns:
        JobStatusResponse: 任务状态响应
    """
    # 首先从数据库获取任务
    db_job = await crud.job.get_job_by_id_and_user(
        db=db,
        job_id=job_id,
        user_id=current_user.id
    )
    
    # 若任务不存在或不属于当前用户，则检查Celery
    if not db_job:
        # 使用Celery的AsyncResult获取任务状态
        result = AsyncResult(job_id)
        
        # 获取任务元数据
        task_meta = result.info or {}
        
        # 如果任务成功完成，result.info会包含任务的返回值
        if result.state == 'SUCCESS':
            task_result = result.get()
        else:
            task_result = {}
        
        # 从元数据或结果中获取信息
        if isinstance(task_meta, dict):
            # 使用.get方法以避免键不存在的错误
            progress = task_meta.get('progress', 0.0)
            stage = task_meta.get('stage', ProgressStages.INIT)
            files = task_meta.get('files', {})
            results = task_meta.get('results', {})
            error = task_meta.get('error', None)
            
            # 处理文件路径，将绝对路径转换为相对路径
            files = process_paths_in_dict(files, root_dir)
            results = process_paths_in_dict(results, root_dir)
        else:
            # 元数据不是字典，可能是任务返回的值
            progress = 100.0 if result.state == 'SUCCESS' else 0.0
            stage = (
                ProgressStages.ANALYSIS_COMPLETE if result.state == 'SUCCESS' 
                else ProgressStages.INIT
            )
            files = (
                task_result.get('files', {}) if isinstance(task_result, dict) 
                else {}
            )
            results = (
                task_result.get('results', {}) if isinstance(task_result, dict) 
                else {}
            )
            error = str(task_meta) if result.state == 'FAILURE' else None
            
            # 处理文件路径，将绝对路径转换为相对路径
            files = process_paths_in_dict(files, root_dir)
            results = process_paths_in_dict(results, root_dir)
        
        # 将Celery任务状态映射到作业状态
        status_str = map_celery_state_to_job_status(result.state)
    else:
        # 从数据库获取的任务信息
        status_str = map_celery_state_to_job_status(str(db_job.status))
        progress = db_job.progress or 0.0
        stage = db_job.stage or ProgressStages.INIT
        error = db_job.error_message
        
        # --- 修正文件和结果路径处理 ---
        files = {}
        results = {}
        relative_path = None
        if db_job.result_path:
            relative_path = convert_absolute_to_relative_path(
                db_job.result_path, root_dir
            )
        
        # 根据数据库中的 result_type 填充 files 字典
        if db_job.result_type == "dataframe_csv_path" and relative_path:
            files['dataframe'] = [relative_path]
        elif db_job.result_type == "plot_file_path" and relative_path:
            files['plots'] = [relative_path]
        elif db_job.result_type == "text" and relative_path: # 如果文本也保存了文件
            files['ai_text'] = [relative_path]

        # 构建结果字典
        if db_job.result_content or db_job.result_path:
            results['pda'] = {
                "response": db_job.result_content,
                "error": db_job.error_message
            }
            if db_job.result_type == "dataframe_csv_path" and relative_path:
                 results['pda']["dataframe_path"] = relative_path # 添加明确的dataframe路径
            elif db_job.result_type == "plot_file_path" and relative_path:
                results['pda']["plot_path"] = relative_path
            elif db_job.result_type == "text" and relative_path:
                 results['pda']["text_file_path"] = relative_path

            # 兼容旧的或简单的结果结构 (如果需要的话)
            # if relative_path and 'plot_path' not in results['pda'] and 'dataframe_path' not in results['pda']:
            #    results['pda']['file_path'] = relative_path
        # --- 结束修正 ---
    
    # 构建响应
    return JobStatusResponse(
        job_id=job_id,
        status=status_str,
        stage=stage,
        progress=progress,
        files=files,
        results=results,
        error=error
    )


@app.get("/api/jobs", response_model=List[Dict[str, Any]])
async def list_jobs(
    limit: int = Query(10, description="返回的最大任务数"),
    status: Optional[str] = Query(None, description="按状态筛选任务"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> List[Dict[str, Any]]:
    """列出用户的所有任务
    
    Args:
        limit: 返回的最大任务数
        status: 按状态筛选任务
        current_user: 当前认证用户
        db: 数据库会话
        
    Returns:
        List[Dict[str, Any]]: 任务列表
    """
    # 从数据库获取用户任务
    jobs = await crud.job.get_jobs_by_user(
        db=db,
        user_id=current_user.id,
        skip=0,
        limit=limit
    )
    
    # 如果请求中包含status参数，按状态筛选
    if status:
        from src.schemas.job import JobStatus
        try:
            status_enum = JobStatus(status.upper())  # 尝试转换为枚举
            jobs = [job for job in jobs if job.status == status_enum]
        except ValueError:
            # 如果无法转换为枚举，使用映射后的状态进行字符串比较
            mapped_status = status.lower()
            jobs = [
                job for job in jobs 
                if map_celery_state_to_job_status(str(job.status)) == 
                   mapped_status
            ]
    
    # 转换为字典列表并处理路径
    result = []
    for job in jobs:
        job_dict = {
            "job_id": job.id,
            "status": map_celery_state_to_job_status(str(job.status)),
            "progress": job.progress or 0,
            "stage": job.stage or "",
            "query": job.query_text,
            "created_at": (
                job.created_at.isoformat() if job.created_at else None
            ),
            "completed_at": (
                job.completed_at.isoformat() if job.completed_at else None
            ),
            "conversation_id": job.conversation_id,
            "result_type": job.result_type,
            "error": job.error_message
        }
        
        # 添加结果路径（如果有）
        if job.result_path:
            job_dict["result_path"] = convert_absolute_to_relative_path(
                job.result_path, root_dir
            )
        
        result.append(job_dict)
    
    return result


@app.get("/api/file/{file_path:path}")
async def get_file(
    file_path: str,
    current_user: User = Depends(get_current_active_user)
):
    """获取文件内容
    
    Args:
        file_path: 文件路径
        current_user: 当前认证用户
        
    Returns:
        FileResponse: 文件响应
    """
    # 2. 确保路径以 output/ 开头 (前端传来的相对路径应该已经是这样)
    if not file_path.startswith('output/'):
        # 如果不是，可能路径有问题，但尝试加上
        clean_path = f"output/{file_path}"
    else:
        clean_path = file_path
    
    # 3. 构建完整路径
    full_path = os.path.join(root_dir, clean_path)
    print(f"请求文件: {file_path}, 处理后: {clean_path}, 完整路径: {full_path}")
    
    # 检查文件是否存在
    if not os.path.exists(full_path):
        # 简化错误处理，因为路径现在应该是可靠的相对路径
        raise HTTPException(
            status_code=404, 
            detail=f"文件未找到: {clean_path}"
        )
        
    return FileResponse(full_path)


# 简单的测试接口
@app.post("/api/test")
async def test_workflow(
    current_user: User = Depends(get_current_active_user)
):
    """测试工作流程
    
    Args:
        current_user: 当前认证用户
        
    Returns:
        Dict: 测试响应
    """
    # 创建输出目录（基于时间戳）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(root_dir, f"output/{timestamp}")
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存查询记录
    with open(
        os.path.join(output_dir, "query.txt"), "w", encoding="utf-8"
    ) as f:
        f.write("这是一个测试查询")
    
    # 创建测试结果
    result = {
        "status": "success",
        "message": "工作流测试成功",
        "test_data": {
            "timestamp": timestamp,
            "output_dir": output_dir
        }
    }
    
    # 保存测试结果
    with open(
        os.path.join(output_dir, "result.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    return result


if __name__ == "__main__":
    import uvicorn
    import socket
    
    # 默认端口
    default_port = 8000
    max_port_attempts = 5
    
    # 尝试找到可用端口
    for port_offset in range(max_port_attempts):
        port = default_port + port_offset
        try:
            # 尝试绑定端口来检查是否可用
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('0.0.0.0', port))
            sock.close()
            
            print(f"使用端口 {port} 启动服务...")
            uvicorn.run(
                "api_workflow:app", 
                host="0.0.0.0", 
                port=port, 
                reload=True,
                # 添加这行来忽略 .venv 目录的变化
                reload_excludes=[".venv/*"]
            )
            break
        except OSError as err:  # 捕获异常实例
            print(f"端口 {port} 已被占用 ({err})，尝试下一个端口...")
            if port_offset == max_port_attempts - 1:
                print("无法找到可用端口。请手动终止占用端口的进程。")
                print(f"可以使用命令: lsof -i :{default_port}")  # F-string 正常
                import sys
                sys.exit(1) 