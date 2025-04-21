"""
财务查询任务模块，包含处理财务数据查询的Celery任务
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional
import traceback
from celery import Task
import asyncio
from sqlalchemy import text

# 添加上级目录到Python路径
current_path = os.path.dirname(os.path.abspath(__file__))
parent_path = os.path.dirname(current_path)
root_path = os.path.dirname(parent_path)  # 项目根目录
sys.path.insert(0, parent_path)

from tasks.celery_app import celery_app
from core.config import ProgressStages, ProgressPercentage

# 导入数据库相关模块
from db.base import AsyncSessionLocal
from db import crud
from schemas.job import JobStatus, JobUpdate
from schemas.message import MessageCreate

# 导入工作流组件
from agent.QueryParserAgent import query_parser_agent
from agent.DataFetcherAgent import DataFetcherAgent
from agent.PandasAIAgent import PandasAIAgent


def get_timestamp() -> str:
    """获取当前时间戳
    
    Returns:
        str: 格式化的时间戳字符串
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


class FinancialQueryTask(Task):
    """财务查询任务基类，添加错误处理和进度追踪"""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任务失败时的处理"""
        # 记录详细错误信息
        error_detail = {
            "error": str(exc),
            "traceback": einfo.traceback,
            "task_id": task_id,
            "args": args,
            "kwargs": kwargs
        }
        print(f"任务失败: {error_detail}")
        
        # 将错误信息保存到数据库
        try:
            loop = asyncio.get_event_loop_policy().get_event_loop()
            # Run async function in the existing/new loop
            loop.run_until_complete(
                self._update_job_failure(task_id, str(exc))
            )
        except Exception as db_err:
            print(f"更新任务失败状态到数据库出错: {db_err}")
            
        return super().on_failure(exc, task_id, args, kwargs, einfo)
    
    async def _update_job_failure(self, task_id: str, error_message: str):
        """更新任务失败状态到数据库
        
        Args:
            task_id: 任务ID
            error_message: 错误信息
        """
        async with AsyncSessionLocal() as db:
            # 获取任务，不检查user_id
            sql = text(f"SELECT user_id FROM jobs WHERE id = '{task_id}'")
            result = await db.execute(sql)
            row = result.first()
            if not row:
                print(f"无法找到任务ID: {task_id}")
                return
                
            user_id = row[0]
            await crud.create_or_update_job(
                db=db,
                job_id=task_id,
                user_id=user_id,
                job_data=JobUpdate(
                    status=JobStatus.FAILURE,
                    error_message=error_message,
                    completed_at=datetime.now()
                )
            )
            await db.commit()


@celery_app.task(bind=True, base=FinancialQueryTask, name='tasks.financial_query.process_financial_query')
def process_financial_query(
    self, query: str, user_id: int, conversation_id: int,
    output_dir: Optional[str] = None, save_intermediate: bool = True
) -> Dict[str, Any]:
    """处理财务数据查询的Celery任务
    
    Args:
        query: 用户的自然语言查询
        user_id: 用户ID
        conversation_id: 对话ID
        output_dir: 输出目录路径
        save_intermediate: 是否保存中间结果
        
    Returns:
        Dict[str, Any]: 查询结果
    """
    # Get or create event loop for this task execution
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    job_id = self.request.id
    timestamp = get_timestamp()
    
    # 如果没有提供输出目录，创建一个
    if not output_dir:
        output_dir = os.path.join(root_path, f"output/{timestamp}_{job_id}")
    os.makedirs(output_dir, exist_ok=True)
    
    # 任务结果初始化
    result = {
        "status": "pending",
        "stage": ProgressStages.INIT,
        "progress": ProgressPercentage.INIT,
        "query": query,
        "timestamp": timestamp,
        "output_dir": output_dir,
        "files": {},
        "results": {},
        "error": None
    }
    
    # 创建异步函数来更新数据库
    async def _init_job_in_db():
        """初始化任务在数据库中的记录"""
        async with AsyncSessionLocal() as db:
            # 创建任务记录
            await crud.create_or_update_job(
                db=db,
                job_id=job_id,
                user_id=user_id,
                job_data=JobUpdate(
                    status=JobStatus.RECEIVED,
                    query_text=query,
                    progress=ProgressPercentage.INIT,
                    stage=ProgressStages.INIT
                ),
                conversation_id=conversation_id
            )
            
            # 创建用户消息记录
            await crud.create_message(
                db=db,
                message_in=MessageCreate(
                    conversation_id=conversation_id,
                    content=query,
                    is_from_user=True
                ),
                user_id=user_id
            )
            
            await db.commit()
    
    # 执行初始化数据库任务 using the managed loop
    loop.run_until_complete(_init_job_in_db())
    
    # 将 _save_success_result_to_db 的定义移到调用之前
    # 异步函数保存成功结果到数据库 - Updated signature
    async def _save_success_result_to_db(
        content: Optional[str],
        content_type: str,  # 直接使用传入的类型
        file_path: Optional[str]  # 直接使用传入的路径
    ):
        """保存成功的结果到数据库
        
        Args:
            content: AI分析的文本结果
            content_type: 最终确定的内容类型
            file_path: 关联的文件路径 (CSV 或 Plot)
        """
        async with AsyncSessionLocal() as db:
            # 更新任务状态
            await crud.create_or_update_job(
                db=db,
                job_id=job_id,
                user_id=user_id,
                job_data=JobUpdate(
                    status=JobStatus.SUCCESS,
                    progress=100,
                    stage=ProgressStages.ANALYSIS_COMPLETE,
                    completed_at=datetime.now(),
                    result_type=content_type,  # 使用传入的类型
                    result_content=content,   # 保存文本内容
                    result_path=file_path     # 保存文件路径 (CSV或Plot)
                )
            )
            
            # 创建AI回复消息
            await crud.create_message(
                db=db,
                message_in=MessageCreate(
                    conversation_id=conversation_id,
                    content=content or "(分析完成，请查看文件)",  # 改进无文本时的提示
                    content_type=content_type,  # 使用传入的类型
                    file_path=file_path,       # 使用传入的路径
                    is_from_user=False
                )
            )
            
            await db.commit()

    try:
        # 创建进度回调函数
        def update_progress(progress: float, stage: str):
            """更新任务进度和阶段
            
            Args:
                progress: 进度百分比
                stage: 当前阶段
            """
            # 使用Celery的update_state更新任务状态
            self.update_state(
                state='PROGRESS',
                meta={
                    'progress': progress,
                    'stage': stage,
                    'job_id': job_id,
                    'files': result['files'],
                    'results': result['results'],
                    'error': None
                }
            )
            
            # 更新本地结果
            result['progress'] = progress
            result['stage'] = stage
            print(f"任务进度更新: {progress}%, 阶段: {stage}")
            
            # 异步更新数据库中的任务状态 using the managed loop
            try:
                # Use loop.run_until_complete instead of asyncio.run
                loop.run_until_complete(
                    _update_progress_in_db(progress, stage)
                )
            except Exception as e:
                print(f"更新进度到数据库出错: {str(e)}")
        
        # 异步函数来更新数据库中的进度
        async def _update_progress_in_db(progress: float, stage: str):
            """更新数据库中的任务进度
            
            Args:
                progress: 进度百分比
                stage: 当前阶段
            """
            async with AsyncSessionLocal() as db:
                await crud.update_job_status(
                    db=db,
                    job_id=job_id,
                    status=JobStatus.PROCESSING,
                    progress=int(progress),
                    stage=stage
                )
                await db.commit()
            
        # 第1步：查询解析
        try:
            # 更新状态为处理中
            update_progress(
                ProgressPercentage.QUERY_PARSE_START,
                ProgressStages.QUERY_PARSE_START
            )
            
            # 进行查询解析
            query_result = query_parser_agent(
                query, progress_callback=update_progress
            )
            
            # 保存查询解析结果
            timestamp = get_timestamp()
            qpa_output_path = os.path.join(
                output_dir,
                f"{timestamp}_QPA_result.json"
            )
            with open(qpa_output_path, "w", encoding="utf-8") as f:
                json.dump(query_result, f, ensure_ascii=False, indent=2)
            
            # 更新文件和结果
            result['files']['qpa'] = [qpa_output_path]
            result['results']['qpa'] = query_result
            
            # 更新进度
            update_progress(
                ProgressPercentage.QUERY_PARSE_COMPLETE,
                ProgressStages.QUERY_PARSE_COMPLETE
            )
            
        except Exception as e:
            error_msg = f"查询解析失败: {str(e)}"
            result['error'] = error_msg
            raise Exception(error_msg)
        
        # 第2步：数据获取
        try:
            update_progress(
                ProgressPercentage.DATA_FETCH_START,
                ProgressStages.DATA_FETCH_START
            )
            
            # 创建DataFetcherAgent并处理查询
            data_fetcher = DataFetcherAgent()
            query_json_str = json.dumps(query_result, ensure_ascii=False)
            
            # 获取数据
            dataframe = data_fetcher.process_query(
                query_json_str, progress_callback=update_progress
            )
            
            # 保存数据结果
            timestamp = get_timestamp()
            dfa_output_path = os.path.join(
                output_dir,
                f"{timestamp}_DFA_result.csv"
            )
            dataframe.to_csv(dfa_output_path, index=False, encoding="utf-8")
            
            # 更新文件和结果
            result['files']['dfa'] = [dfa_output_path]
            
            # 保存dataframe的预览信息
            preview = {
                "columns": dataframe.columns.tolist(),
                "shape": dataframe.shape,
                "dtypes": {
                    col: str(dataframe[col].dtype)
                    for col in dataframe.columns
                },
                "head": dataframe.head(10).to_dict(orient="records")
            }
            result['results']['dfa_preview'] = preview
            
            # 更新进度
            update_progress(
                ProgressPercentage.DATA_FETCH_COMPLETE,
                ProgressStages.DATA_FETCH_COMPLETE
            )
            
        except Exception as e:
            error_msg = f"数据获取失败: {str(e)}"
            result['error'] = error_msg
            raise Exception(error_msg)
        
        # 第3步：数据分析
        try:
            update_progress(
                ProgressPercentage.ANALYSIS_INIT,
                ProgressStages.ANALYSIS_INIT
            )
            
            # 创建PandasAIAgent并处理数据
            pandas_ai = PandasAIAgent()
            pandas_ai.initialize_agent(dataframe, output_dir=output_dir)
            ai_result = pandas_ai.analyze(
                query, progress_callback=update_progress
            )
            
            # 初始化结果变量
            ai_response_content = None
            ai_plot_path = None
            ai_dataframe_path = None
            final_content_type = "unknown"

            # 检查 ai_result 类型并处理
            if isinstance(ai_result, pd.DataFrame):
                # 处理 DataFrame 结果
                timestamp = get_timestamp()
                csv_filename = f"{timestamp}_PDA_dataframe.csv"
                ai_dataframe_path = os.path.join(output_dir, csv_filename)
                try:
                    ai_result.to_csv(
                        ai_dataframe_path, 
                        index=False, 
                        encoding='utf-8-sig'  # 使用 utf-8-sig 避免 Excel 打开乱码
                    )
                    result['files']['dataframe'] = [ai_dataframe_path]
                    final_content_type = "dataframe_csv_path"
                    ai_response_content = "数据已生成表格，请查看或下载文件。"
                    # 存储可序列化的预览，而不是原始 DataFrame
                    result['results']['pda'] = (
                        ai_result.head().to_dict(orient='records')
                    )
                except Exception as df_err:
                    print(f"保存 DataFrame 到 CSV 时出错: {df_err}")
                    ai_response_content = f"生成了表格数据，但保存为CSV文件时出错: {df_err}"
                    final_content_type = "text"  # 出错时降级为文本
                    result['results']['pda'] = { 
                        "error": "Failed to save DataFrame to CSV" 
                    }
            
            elif isinstance(ai_result, str):
                # --- 修正: 检查字符串是否为绘图路径 ---
                potential_path = ai_result
                is_plot = False
                # 简单检查是否像一个文件路径并以图片扩展名结尾
                # 注意：PandasAI 返回的路径可能是相对的 'output/...'
                if potential_path.startswith('output/') and \
                   potential_path.lower().endswith(
                       ('.png', '.jpg', '.jpeg', '.svg')
                   ):
                    # 假设这是一个绘图路径
                    is_plot = True
                    ai_plot_path = potential_path  # 将字符串视为路径
                    final_content_type = "plot_file_path"
                    ai_response_content = "(图表已生成)"  # 可以提供一个默认文本
                    result['files']['plots'] = [ai_plot_path]
                    result['results']['pda'] = {
                        'type': 'plot', 
                        'value': ai_plot_path
                    }  # 存储结构化信息
                
                if not is_plot:
                    # 如果不是绘图路径，则按原样处理为文本
                    ai_response_content = ai_result
                    final_content_type = "text"
                    result['results']['pda'] = ai_result  # 字符串是可序列化的
                # --- 结束修正 ---
            
            elif isinstance(ai_result, dict):
                # 保持对 {'type':'plot'} 的检查作为备用
                if ai_result.get('type') == 'plot' and \
                   isinstance(ai_result.get('value'), str):
                    ai_plot_path = ai_result.get('value')
                    final_content_type = "plot_file_path"
                    result['files']['plots'] = [ai_plot_path]
                    ai_response_content = ai_result.get("response", "(图表已生成)") 
                    result['results']['pda'] = ai_result 
                else:  # 处理其他字典 (主要是文本或其他复杂结构)
                    ai_response_content = ai_result.get("response")
                    ai_plot_path = ai_result.get("plot_path")  # 旧键检查
                    result['results']['pda'] = ai_result
                    if ai_plot_path and isinstance(ai_plot_path, str):  # 理论上不太可能走到这里了
                        final_content_type = "plot_file_path"
                        result['files']['plots'] = [ai_plot_path]
                    elif ai_response_content:
                        final_content_type = "text"
                    else:
                        final_content_type = "unknown"
                        ai_response_content = str(ai_result)  # Fallback
            
            elif ai_result is not None:
                # 处理其他非 None 类型，转换为字符串
                ai_response_content = str(ai_result)
                final_content_type = "text"
                result['results']['pda'] = ai_response_content  # 字符串是可序列化的

            # --- 保存AI回复文本文件逻辑调整 ---
            # 只有当最终类型确实是 text 时才保存 .txt 文件
            if ai_response_content and final_content_type == "text":
                timestamp = get_timestamp()
                ai_text_file = os.path.join(
                    output_dir,
                    f"{timestamp}_AI_response.txt"
                )
                with open(ai_text_file, "w", encoding="utf-8") as f:
                    f.write(ai_response_content)
                result['files']['ai_text'] = [ai_text_file]
            # --- 结束调整 ---

            # 确定最终要保存的文件路径 (优先 DataFrame，其次 Plot)
            # 注意：现在 ai_plot_path 可能在 str 分支中被赋值
            final_file_path = ai_dataframe_path or ai_plot_path
            
            # 更新进度为完成
            update_progress(
                ProgressPercentage.ANALYSIS_COMPLETE,
                ProgressStages.ANALYSIS_COMPLETE
            )
            
            # 将成功结果保存到数据库 using the managed loop
            loop.run_until_complete(_save_success_result_to_db(
                ai_response_content, final_content_type, final_file_path
            ))
            
        except Exception as e:
            error_msg = f"数据分析失败: {str(e)}"
            result['error'] = error_msg
            raise Exception(error_msg)
        
        return result
        
    except Exception as e:
        # 保存错误信息
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        
        print(f"任务处理错误: {error_msg}")
        print(traceback_str)
        
        # 更新错误状态到数据库 using the managed loop
        async def _save_error_to_db():
            """保存错误信息到数据库"""
            async with AsyncSessionLocal() as db:
                await crud.create_or_update_job(
                    db=db,
                    job_id=job_id,
                    user_id=user_id,
                    job_data=JobUpdate(
                        status=JobStatus.FAILURE,
                        error_message=error_msg,
                        completed_at=datetime.now(),
                        progress=result['progress'],
                        stage=result['stage']
                    )
                )
                await db.commit()
        
        # Use loop.run_until_complete instead of asyncio.run
        loop.run_until_complete(_save_error_to_db())
        
        # 重新抛出异常以便Celery任务失败处理
        raise 