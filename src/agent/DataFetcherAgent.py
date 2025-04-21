"""数据收集器脚本说明

此模块实现：根据外部命令输入一个sql数据抽取指令，调用smolagents的CodeAgent，生成一段sql查询语句，并执行数据抽取，并且把数据保存为dataframe表格保存在内存中，并且另存为csv文件在本地文件夹。
主要功能包括：
1、读取用户提出的财务数据查询指令
把这个脚本封装成一个名字叫做DataFectherAgent的函数，应引用这个函数的时候，DataFectherAgent(query_parser_result)输入的为一段从上一个agent传递过来的result，也是一个自然语言组成的财务数据查询指令。
2、根据抽取命令调用smolagent
调用smolagents的CodeAgent，设置一下它的description来定义它的任务和功能，根据前面收集到的用户的财务数据查询指令、生成sql查询抽取代码、并且链接sql数据库执行查询。
3、抽取数据后保存、输出数据
经过查询迭代后，smolagent输出并且把抽取出来的数据格式转换为保存为dataframe表格保存在内存中供下一步pandasai-agent调用使用，并且另存为csv文件在本地文件夹。
其余大模型设置、环境数据库设置、日志配置设置同前。所有文件命名都改为【时间戳-DFA-log类型】
"""

import os
import yaml
from datetime import datetime
from typing import Optional, ClassVar

import pandas as pd
from sqlalchemy import create_engine, inspect
from smolagents import tool, CodeAgent, LiteLLMModel
from dotenv import load_dotenv

load_dotenv()

class DatabaseConfig:
    """数据库配置类"""
    # 获取项目根目录
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))
    # 使用绝对路径定位数据库文件
    DB_PATH = os.path.join(ROOT_DIR, "data/Astock_financial_data.db")
    CONNECTION_STRING = f"sqlite:///{DB_PATH}"


class LogConfig:
    """日志配置类"""
    OUTPUT_DIR = "output/DFA"
    LOG_DIR = "logs"
    TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"


def get_timestamp() -> str:
    """获取当前时间戳
    
    Returns:
        str: 格式化的时间戳字符串
    """
    return datetime.now().strftime(LogConfig.TIMESTAMP_FORMAT)


# 创建数据库连接
engine = create_engine(DatabaseConfig.CONNECTION_STRING)


class DatabaseTools:
    """数据库工具类，提供数据库操作相关的方法"""

    @staticmethod
    @tool
    def get_table_info() -> str:
        """获取数据库中所有表的结构信息
        
        Returns:
            str: 格式化的表结构信息字符串
        """
        inspector = inspect(engine)
        table_info = []
        
        for table_name in inspector.get_table_names():
            columns = inspector.get_columns(table_name)
            table_info.append(f"\n表名: {table_name}")
            table_info.append("列信息:")
            for col in columns:
                table_info.append(f"  - {col['name']}: {col['type']}")
                
        return "\n".join(table_info)

    @staticmethod
    @tool 
    def sql_query(query: str) -> str:
        """执行SQL查询并将结果输出为Markdown格式
        
        Args:
            query: SQL查询语句
            
        Returns:
            str: 查询执行状态和结果预览
            
        Raises:
            Exception: 当SQL查询执行失败时抛出
        """
        try:
            # 执行查询
            df = pd.read_sql_query(query, engine)
            
            # 生成输出文件路径
            # timestamp = get_timestamp()
            # output_path = os.path.join(
            #     LogConfig.OUTPUT_DIR,
            #     f"{timestamp}_DFA_result.csv"
            # )
            # os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # # 保存为CSV
            # df.to_csv(output_path, index=False, encoding='utf-8')
            
            # 保存结果到类变量
            DataFetcherAgent._last_result = df
            
            col_info = [f'- {col}: {df[col].dtype}' for col in df.columns]
            col_info_str = chr(10).join(col_info)
            
            return (
                # f"查询结果已保存到: {output_path}\n"
                f"数据结构预览:\n列名和数据类型:\n"
                f"{col_info_str}\n\n"
            )
            
        except Exception as e:
            return f"查询执行失败: {str(e)}"


class DataFetcherAgent:
    """数据获取代理类，负责处理SQL查询和数据提取"""
    
    # 类变量用于存储最近的查询结果
    _last_result: ClassVar[Optional[pd.DataFrame]] = None

    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    # PROMPT_YAML_PATH = "src/agent/prompt/DatafetcherAgent_prompt.yaml"
    
    # 默认重试次数
    MAX_RETRIES = 3

    def __init__(self, model: Optional[LiteLLMModel] = None, max_retries: int = MAX_RETRIES):
        """初始化数据获取代理
        
        Args:
            model: LiteLLMModel实例，如果为None则使用默认配置创建
            max_retries: 最大重试次数
        """
        self.model = model or self._create_default_model()
        self.agent = self.datafetcher_create_agent()
        self.prompt_template = self._load_prompt_template()
        self.max_retries = max_retries
        
    def _create_default_model(self) -> LiteLLMModel:
        """创建默认的LLM模型"""
        return LiteLLMModel(
            api_key=self.DEEPSEEK_API_KEY,
            model_id="deepseek/deepseek-chat"
        )
    
    def _load_prompt_template(self) -> str:
        """从YAML文件加载prompt模板
        
        Returns:
            str: prompt模板字符串
        """
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            prompt_path = os.path.join(current_dir, "prompt/DatafetcherAgent_prompt.yaml")
            
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt_data = yaml.safe_load(f)
            return prompt_data.get('prompt', '')
        except Exception as e:
            print(f"加载DataFetcherAgent prompt模板失败: {str(e)}")
            return "请根据提供的查询生成SQL语句并执行。"
    
    def datafetcher_create_agent(self) -> CodeAgent:
        """创建并配置CodeAgent"""
        return CodeAgent(
            tools=[DatabaseTools.sql_query],
            model=self.model,
            max_steps=5,
            # 允许导入pandas和numpy
            additional_authorized_imports=["pandas", "numpy", "csv"]
        )
        
    def process_query(self, query: str, progress_callback=None) -> pd.DataFrame:
        """处理查询请求并返回结果，失败时自动重试
        
        Args:
            query: 用户的查询指令
            progress_callback: 可选的进度回调函数，用于报告进度
            
        Returns:
            pd.DataFrame: 查询结果数据框
            
        Raises:
            Exception: 当所有重试都失败时抛出
        """
        errors = []
        retry_count = 0
        
        # 报告开始准备数据获取
        if progress_callback:
            progress_callback(38.0, "开始准备数据获取")
        
        # 重试循环
        while retry_count < self.max_retries:
            try:
                # 构建提示词
                prompt = self.datafetcher_generate_prompt(query)
                
                # 报告正在生成SQL查询
                if progress_callback:
                    progress_callback(45.0, "生成SQL查询")
                
                # 执行查询
                result = self.agent.run(prompt)
                
                # 记录日志
                self._log_query(query, result, retry_count)
                
                # 报告正在处理查询结果
                if progress_callback:
                    progress_callback(60.0, "处理查询结果")
                
                # 检查查询结果
                if self._last_result is not None:
                    # 成功获取结果
                    # 报告数据获取完成
                    if progress_callback:
                        progress_callback(66.0, "数据获取完成")
                    return self._last_result
                else:
                    # 未返回结果，记录错误并重试
                    error_msg = "查询未返回任何结果"
                    errors.append(error_msg)
                    retry_count += 1
                    self._log_error(query, error_msg, retry_count)
                    
            except Exception as e:
                # 捕获异常，记录错误并重试
                error_msg = str(e)
                errors.append(error_msg)
                retry_count += 1
                self._log_error(query, error_msg, retry_count)
        
        # 所有重试都失败
        error_msg = f"达到最大重试次数 ({self.max_retries})，所有尝试均失败"
        if errors:
            final_error = f"{error_msg}。最后一次错误: {errors[-1]}" 
        else:
            final_error = error_msg
        self._log_error(query, final_error, -1)  # -1表示最终错误
        raise Exception(final_error)
            
    def datafetcher_generate_prompt(self, query: str) -> str:
        """生成查询提示词
        
        Args:
            query: 用户查询
            
        Returns:
            str: 格式化的提示词
        """
        return self.prompt_template.format(query=query)
            
    def _log_query(self, query: str, result: str, retry_count: int = 0) -> None:
        """记录查询日志
        
        Args:
            query: 原始查询
            result: 查询结果
            retry_count: 重试计数
        """
        timestamp = get_timestamp()
        retry_suffix = f"_retry{retry_count}" if retry_count > 0 else ""
        log_path = os.path.join(
            LogConfig.LOG_DIR,
            f"{timestamp}-DFA-query{retry_suffix}.log"
        )
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(f"时间: {timestamp}\n")
            f.write(f"查询: {query}\n")
            f.write(f"重试次数: {retry_count}\n")
            f.write(f"结果: {result}\n")
            
    def _log_error(self, query: str, error: str, retry_count: int = 0) -> None:
        """记录错误日志
        
        Args:
            query: 导致错误的查询
            error: 错误信息
            retry_count: 重试计数
        """
        timestamp = get_timestamp()
        retry_suffix = ""
        if retry_count >= 0:
            retry_suffix = f"_retry{retry_count}" 
        else:
            retry_suffix = "_final"
        log_path = os.path.join(
            LogConfig.LOG_DIR,
            f"{timestamp}-DFA-error{retry_suffix}.log"
        )
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(f"时间: {timestamp}\n")
            f.write(f"查询: {query}\n")
            f.write(f"重试次数: {retry_count}\n")
            f.write(f"错误: {error}\n") 


if __name__ == "__main__":
    datafetcher_agent = DataFetcherAgent()
    datafetcher_query = """
{
  "解析结果": {
    "报告日区间": "20200101-20241231",
    "筛选的股票名称": "贵州茅台",
    "行业名称": "食品饮料",
    "需要从sql抽取的财务指标": [
      "营业收入来自:income_table",
      "净利润来自:income_table"
    ]
  }
}
    """
    datafetcher_result = datafetcher_agent.process_query(datafetcher_query)
    # print(datafetcher_result)





