"""
金融数据查询流程模块

此模块封装了整个金融数据查询的工作流程，包括：
1. 查询解析 (QueryParserAgent)
2. 数据获取 (DataFetcherAgent)
3. 数据分析和可视化 (PandasAIAgent)

主要入口点是 FinancialDataChatFlow 类，它提供了一个统一的接口来处理用户查询。
"""

import os
import json
import pandas as pd
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

from QueryParserAgent import QueryParserAgent, query_parser_agent
from DataFetcherAgent import DataFetcherAgent
from PandasAIAgent import PandasAIAgent


class FinancialDataChatFlow:
    """金融数据聊天机器人工作流管理类
    
    此类封装了从查询解析到数据分析的完整流程，提供统一的接口给前端调用。
    """
    
    def __init__(self, 
                 query_model: str = "deepseek-chat",
                 save_intermediate_results: bool = True,
                 output_dir: str = "src/output"):
        """初始化金融数据聊天流程
        
        Args:
            query_model (str): 查询解析使用的模型，默认为 "deepseek-chat"
            save_intermediate_results (bool): 是否保存中间结果，默认为 True
            output_dir (str): 输出目录，默认为 "src/output"
        """
        self.query_model = query_model
        self.save_intermediate_results = save_intermediate_results
        self.output_dir = output_dir
        
        # 确保输出目录存在
        if self.save_intermediate_results:
            os.makedirs(output_dir, exist_ok=True)
        
        # 初始化代理
        self.data_fetcher = DataFetcherAgent()
        self.pandas_ai = PandasAIAgent()
        
        # 用于保存最近的查询结果
        self.latest_query_result = None
        self.latest_dataframe = None
        self.latest_analysis = None
        
    def _get_timestamp(self) -> str:
        """获取当前时间戳
        
        Returns:
            str: 格式化的时间戳字符串
        """
        return datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def _save_intermediate_result(self, stage: str, data: Any) -> str:
        """保存中间结果
        
        Args:
            stage (str): 处理阶段名称
            data (Any): 要保存的数据
            
        Returns:
            str: 保存的文件路径
        """
        if not self.save_intermediate_results:
            return ""
            
        timestamp = self._get_timestamp()
        
        # 确定文件后缀和格式化方法
        if isinstance(data, pd.DataFrame):
            file_ext = "csv"
            save_fn = lambda d, p: d.to_csv(p, index=False, encoding="utf-8")
        elif isinstance(data, dict) or isinstance(data, list):
            file_ext = "json"
            save_fn = lambda d, p: json.dump(d, open(p, "w", encoding="utf-8"), 
                                      ensure_ascii=False, indent=2)
        else:
            file_ext = "txt"
            save_fn = lambda d, p: open(p, "w", encoding="utf-8").write(str(d))
            
        # 构建文件路径
        file_path = os.path.join(
            self.output_dir, 
            f"{timestamp}_{stage}.{file_ext}"
        )
        
        # 保存数据
        try:
            save_fn(data, file_path)
            return file_path
        except Exception as e:
            print(f"保存中间结果时出错: {str(e)}")
            return ""
    
    def process_query(self, 
                      user_query: str, 
                      save_charts: bool = True,
                      charts_dir: str = "src/output/charts") -> Dict[str, Any]:
        """处理用户查询的主要方法
        
        Args:
            user_query (str): 用户的自然语言查询
            save_charts (bool): 是否保存生成的图表，默认为 True
            charts_dir (str): 图表保存目录，默认为 "src/output/charts"
            
        Returns:
            Dict[str, Any]: 包含以下字段的结果字典：
                - status (str): 处理状态，"success" 或 "error"
                - query (str): 原始查询
                - result (Dict/str): 分析结果
                - charts (List[str]): 生成的图表文件路径列表
                - error (str, 可选): 如果发生错误，包含错误信息
        """
        result = {
            "status": "success",
            "query": user_query,
            "timestamp": self._get_timestamp(),
            "result": None,
            "charts": [],
            "intermediate_files": {}
        }
        
        try:
            # 第1步：查询解析
            print(f"步骤1: 解析查询 - '{user_query}'")
            query_result = query_parser_agent(user_query, model=self.query_model)
            self.latest_query_result = query_result
            
            if self.save_intermediate_results:
                result["intermediate_files"]["query_result"] = self._save_intermediate_result(
                    "query_result", query_result
                )
                
            # 第2步：数据获取
            print("步骤2: 获取数据")
            # 将解析结果转换为字符串以传递给DataFetcherAgent
            query_json_str = json.dumps(query_result, ensure_ascii=False)
            dataframe = self.data_fetcher.process_query(query_json_str)
            self.latest_dataframe = dataframe
            
            if self.save_intermediate_results:
                result["intermediate_files"]["dataframe"] = self._save_intermediate_result(
                    "dataframe", dataframe
                )
                
            # 第3步：数据分析
            print("步骤3: 分析数据")
            # 初始化PandasAI代理
            self.pandas_ai.initialize_agent(df=dataframe)
            
            # 执行分析，添加更好的错误处理
            try:
                print("开始执行PandasAI分析...")
                analysis_result = self.pandas_ai.analyze(user_query)
                print("PandasAI分析完成")
                
                # 检查分析结果是否为None
                if analysis_result is None:
                    raise ValueError("PandasAI返回了空结果")
                    
                self.latest_analysis = analysis_result
            except Exception as e:
                error_msg = f"PandasAI分析出错: {str(e)}"
                print(error_msg)
                import traceback
                trace = traceback.format_exc()
                print(trace)
                
                # 构建错误结果
                analysis_result = {
                    "error": str(e),
                    "traceback": trace,
                    "response": f"分析数据时出错: {str(e)}"
                }
                self.latest_analysis = analysis_result
            
            # 处理分析结果
            if "error" in analysis_result:
                result["status"] = "error"
                result["error"] = analysis_result["error"]
                if "traceback" in analysis_result:
                    result["error_details"] = analysis_result["traceback"]
            else:
                result["result"] = analysis_result["response"]
                
                # 处理图表
                if save_charts and "charts" in analysis_result:
                    # 确保图表目录存在
                    os.makedirs(charts_dir, exist_ok=True)
                    
                    # 复制生成的图表到输出目录
                    timestamp = self._get_timestamp()
                    for i, chart_path in enumerate(analysis_result["charts"]):
                        if os.path.exists(chart_path):
                            # 获取图表文件扩展名
                            _, ext = os.path.splitext(chart_path)
                            # 构建新路径
                            new_path = os.path.join(
                                charts_dir, 
                                f"{timestamp}_chart_{i+1}{ext}"
                            )
                            # 复制文件
                            import shutil
                            shutil.copy2(chart_path, new_path)
                            # 添加到结果中
                            result["charts"].append(new_path)
            
            return result
            
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            
            result["status"] = "error"
            result["error"] = str(e)
            result["error_details"] = error_traceback
            
            print(f"处理查询时出错: {str(e)}")
            print(error_traceback)
            
            return result
    
    def get_latest_results(self) -> Dict[str, Any]:
        """获取最近一次查询的所有结果
        
        Returns:
            Dict[str, Any]: 包含最近查询所有结果的字典
        """
        return {
            "query_result": self.latest_query_result,
            "dataframe": self.latest_dataframe,
            "analysis": self.latest_analysis
        }


# 便捷函数，用于直接处理单个查询
def process_financial_query(query: str, 
                           model: str = "deepseek-chat",
                           save_intermediate: bool = True) -> Dict[str, Any]:
    """处理单个金融数据查询
    
    Args:
        query (str): 用户的自然语言查询
        model (str): 使用的模型，默认为 "deepseek-chat"
        save_intermediate (bool): 是否保存中间结果
        
    Returns:
        Dict[str, Any]: 查询处理结果
    """
    flow = FinancialDataChatFlow(
        query_model=model,
        save_intermediate_results=save_intermediate
    )
    return flow.process_query(query)


# 测试代码
if __name__ == "__main__":
    # 创建工作流实例
    flow = FinancialDataChatFlow()
    
    # 测试查询
    test_query = "把20181231-20231231每年的1231年报、机械设备的营业收入获取，然后计算整体的营业收入总和，再计算这个值得同比增速，最后用总值+同比增速的数据输出一个柱状图+折线图给我"
    
    # 处理查询
    result = flow.process_query(test_query)
    
    # 打印结果
    print("\n查询处理结果:")
    print(f"状态: {result['status']}")
    if result['status'] == 'error':
        print(f"错误: {result['error']}")
    else:
        print(f"分析结果: {result['result']}")
        print(f"生成的图表: {result['charts']}")
