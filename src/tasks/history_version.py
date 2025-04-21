"""
财务查询任务模块，包含处理财务数据查询的Celery任务
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime
from typing import Dict, Any
import traceback
from celery import Task

# 添加上级目录到Python路径
current_path = os.path.dirname(os.path.abspath(__file__))
parent_path = os.path.dirname(current_path)
root_path = os.path.dirname(parent_path)  # 项目根目录
sys.path.insert(0, parent_path)

from tasks.celery_app import celery_app
from core.config import ProgressStages, ProgressPercentage

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
        return super().on_failure(exc, task_id, args, kwargs, einfo)


@celery_app.task(bind=True, base=FinancialQueryTask, name='tasks.financial_query.process_financial_query')
def process_financial_query(self, query: str) -> Dict[str, Any]:
    """处理财务数据查询的Celery任务
    
    Args:
        query: 用户的自然语言查询
        
    Returns:
        Dict[str, Any]: 查询结果
    """
    job_id = self.request.id
    timestamp = get_timestamp()
    output_dir = os.path.join(root_path, f"output/{timestamp}_{job_id}")
    os.makedirs(output_dir, exist_ok=True)
    
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
    
    try:
        # 创建进度回调函数
        def update_progress(progress: float, stage: str):
            """更新任务进度和阶段
            
            Args:
                progress: 进度百分比
                stage: 当前阶段
            """
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
            
            # 创建PandasAIAgent并处理查询
            pandas_ai = PandasAIAgent()
            pandas_ai.initialize_agent(df=dataframe, output_dir=output_dir)
            
            # 分析数据
            analysis_result = pandas_ai.analyze(
                query, progress_callback=update_progress
            )
            
            # 处理分析结果
            timestamp = get_timestamp()
            pda_result_text = ""
            main_md_path = os.path.join(
                output_dir,
                f"{timestamp}_PDA_result.md"
            )
            error_occurred = False
            
            # 处理不同类型的返回结果
            if isinstance(analysis_result, dict) and "error" in analysis_result:
                # 处理错误结果
                error_msg = analysis_result['error']
                traceback_info = analysis_result.get('traceback', 'N/A')
                pda_result_text = (
                    f"数据分析阶段出错: {error_msg}\n\n"
                    f"Traceback:\n{traceback_info}"
                )
                result['error'] = error_msg
                error_occurred = True
                
            elif isinstance(analysis_result, pd.DataFrame):
                # 处理DataFrame结果
                response_df = analysis_result
                df_output_path = os.path.join(
                    output_dir,
                    f"{timestamp}_PDA_dataframe.csv"
                )
                
                # 保存DataFrame
                response_df.to_csv(
                    df_output_path,
                    index=False,
                    encoding="utf-8"
                )
                
                # 更新文件列表
                if "dataframes" not in result['files']:
                    result['files']["dataframes"] = []
                result['files']["dataframes"].append(df_output_path)
                
                # 设置结果文本
                preview = response_df.head().to_string()
                pda_result_text = (
                    f"成功生成DataFrame数据，请查看文件："
                    f"`{os.path.basename(df_output_path)}`\n\n"
                    f"以下是数据预览：\n\n```\n{preview}\n```"
                )
                
                # 设置结果类型
                result['results']['output_type'] = "dataframe_csv_path"
                result['results']['output_path'] = df_output_path
                
            elif isinstance(analysis_result, str):
                # 处理字符串结果
                response_value = analysis_result
                is_plot_path = False
                
                # 检查是否是图表路径
                if (response_value.lower().endswith(('.png', '.jpg', '.jpeg', '.svg')) 
                        and os.path.exists(response_value)):
                    
                    # 更新文件列表
                    if "plots" not in result['files']:
                        result['files']["plots"] = []
                    result['files']["plots"].append(response_value)
                    
                    # 设置结果文本
                    pda_result_text = f"成功生成图表，请查看文件：`{response_value}`"
                    
                    # 设置结果类型
                    result['results']['output_type'] = "plot_file_path"
                    result['results']['output_path'] = response_value
                    is_plot_path = True
                
                # 如果不是图表路径，则作为文本处理
                if not is_plot_path:
                    pda_result_text = response_value
                    result['results']['output_type'] = "text"
                    result['results']['output_content'] = response_value
            
            elif isinstance(analysis_result, (int, float)):
                # 处理数值结果
                pda_result_text = str(analysis_result)
                result['results']['output_type'] = "text"
                result['results']['output_content'] = pda_result_text
            
            else:
                # 处理其他未预期的类型
                type_name = type(analysis_result).__name__
                pda_result_text = (
                    f"收到非预期的PandasAI响应类型: {type_name}。"
                    f"响应内容：\n```\n{str(analysis_result)}\n```"
                )
                result['error'] = f"PandasAI返回了非预期的响应类型: {type_name}"
                error_occurred = True
            
            # 保存结果MD文件
            with open(main_md_path, "w", encoding="utf-8") as f:
                f.write(f"# 数据分析结果 ({timestamp})\n\n{pda_result_text}")
            
            # 更新文件列表
            if "pda" not in result['files']:
                result['files']["pda"] = []
            result['files']["pda"].append(main_md_path)
            
            # 更新结果
            result['results']['pda'] = {
                "response": pda_result_text,
                "error": result.get('error')
            }
            
            # 更新状态
            if error_occurred:
                result['status'] = "failed"
                update_progress(
                    ProgressPercentage.ANALYSIS_COMPLETE,
                    ProgressStages.ANALYSIS_COMPLETE + " (失败)"
                )
            else:
                result['status'] = "completed"
                update_progress(
                    ProgressPercentage.ANALYSIS_COMPLETE,
                    ProgressStages.ANALYSIS_COMPLETE
                )
            
        except Exception as e:
            error_msg = f"数据分析失败: {str(e)}"
            result['error'] = error_msg
            result['status'] = "failed"
            update_progress(
                ProgressPercentage.ANALYSIS_COMPLETE,
                ProgressStages.ANALYSIS_COMPLETE + " (失败)"
            )
            raise Exception(error_msg)
            
    except Exception as e:
        # 处理整体异常
        error_msg = str(e)
        result['status'] = "error"
        result['error'] = error_msg
        result['error_details'] = traceback.format_exc()
        
        # 更新任务状态
        self.update_state(
            state='FAILURE',
            meta={
                'progress': result['progress'],
                'stage': result['stage'],
                'error': error_msg,
                'job_id': job_id
            }
        )
        
        # 重新抛出异常，让Celery处理
        raise
        
    # 返回最终结果
    return result 