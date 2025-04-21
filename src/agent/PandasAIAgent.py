# 柱状图的问题

import os
import pandas as pd
# import matplotlib.pyplot as plt # Unused import
from typing import Union, Dict, Any # Removed Optional
# import matplotlib as mpl # Unused import
import warnings
# import google.generativeai as genai # Unused import
from pandasai.agent import Agent  # 正确的导入路径
from pandasai.llm.local_llm import LocalLLM
from pandasai.llm.google_gemini import GoogleGemini
from pandasai.responses import StreamlitResponse
# from pandasai.skills import skill # Unused import
from dotenv import load_dotenv
# from openai import OpenAI # Unused import
# from datetime import datetime # Unused import
import traceback
import logging # 添加 logging 导入
from agent.config.matplotlib_config import setup_matplotlib_config


# 加载环境变量
load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY")
ARK_API_KEY = os.getenv("ARK_API_KEY")

# 忽略字体警告
warnings.filterwarnings("ignore", category=UserWarning)

# 修改导入方式为条件导入
try:
    # 当作为模块导入时使用相对导入
    from .AgentSkills import AgentSkills
except ImportError:
    # 当直接运行脚本时使用绝对导入
    from AgentSkills import AgentSkills

class PandasAIAgent:
    """PandasAI 代理类，用于处理数据分析请求"""
    
    def __init__(self):
        """初始化 PandasAI 代理"""
        setup_matplotlib_config()  # 改为直接调用导入的函数
        self.llm = self._create_deepseek_llm()
        # self.openai_llm = self._create_openai_llm()
        self.agent = None
        self.max_retries = 3  # 设置最大重试次数
        self.logger = logging.getLogger(__name__) # 初始化 logger
        # 配置基本的日志记录器（如果尚未在其他地方配置）
        if not self.logger.hasHandlers():
            logging.basicConfig(level=logging.INFO)
        
    # def _create_llm(self) -> LocalLLM:
    #     """创建 LocalLLM 实例"""
    #     return LocalLLM(
    #         api_base="https://api.deepseek.com/v1",
    #         model="deepseek-chat",
    #         api_key=DEEPSEEK_API_KEY,
    #         max_tokens=8000,
    #         temperature=0
    #     )
    
    # def _create_openai_llm(self) -> OpenAI:
    #     """硅基流动-openai格式-deepseek R1-API"""
    #     client = OpenAI(
    #         api_key=SILICONFLOW_API_KEY,
    #         base_url="https://api.siliconflow.cn/v1/chat/completions"
    #     )
    #     return client
    
    # def _create_openai_llm(self) -> OpenAI:
    #     """创建 OpenAI 实例，用于调用 deepseek API"""
    #     client = OpenAI(
    #         api_key=DEEPSEEK_API_KEY,
    #         base_url="https://api.deepseek.com/v1"
    #     )
    #     return client
    
    # def _create_openai_llm(self) -> OpenAI:
    #     """ 火山  创建 OpenAI 实例，用于调用 deepseek API"""
    #     client = OpenAI(
    #         api_key=ARK_API_KEY,
    #         base_url="https://ark.cn-beijing.volces.com/api/v3"
    #     )
    #     return client
    
    def _create_deepseek_llm(self) -> LocalLLM:
        """创建 火山-LocalLLM 实例"""
        return LocalLLM(
            api_base="https://ark.cn-beijing.volces.com/api/v3",
            model="deepseek-v3-250324",
            api_key=ARK_API_KEY,
            temperature=0,
            max_tokens=8000
        )
    
    def _create_deepseek_llm_together(self) -> LocalLLM:
        """创建 火山-LocalLLM 实例"""
        return LocalLLM(
            api_base="https://api.together.xyz/v1/chat/completions",
            model="deepseek-ai/DeepSeek-V3",
            api_key=TOGETHER_API_KEY,
            temperature=0,
            max_tokens=8000
        )
    
    def _create_gemini_llm(self) -> GoogleGemini:
        """创建 GoogleGemini 实例"""
        return GoogleGemini(
            api_key=GEMINI_API_KEY,
            model="models/gemini-2.0-flash",
            temperature=0,
            max_tokens=8000
        )
    
    def _get_agent_config(self) -> dict:
        """获取 Agent 配置"""
        return {
            "llm": self.llm,
            "response_parser": StreamlitResponse,
            "verbose": True,
            "custom_whitelisted_dependencies": [
                "plotly", 
                "matplotlib", 
                "seaborn", 
                "numpy", 
                "os", 
                "scikit-learn", 
                "pandas",
                "plotly.express", 
                "plotly.graph_objects",
                "pandas.Timestamp",
                "pandas.to_numeric",
                "mathplotlib.pyplot",
                "self._bar_line_chart_skills",
                "typing",
                "typing.Dict",
                "typing.Any",
                "os.path",
                "typing.Union",
                "io",
                "datetime",
                "tempfile",
            ],
            "save_charts": True,
            "enable_cache": False,
            "open_plot": False,
            "max_retries": 3,
        }

    def _get_agent_description(self) -> str:
        """从yaml文件加载agent描述
        
        Returns:
            str: agent描述内容
        """
        prompt_path = 'prompt/PandasAIAGENT_prompt.yaml'
        return self._load_prompt(prompt_path)

    def _get_safe_path(self, path):
        """
        将可能包含空格的绝对路径转换为PandasAI可处理的路径
        
        Args:
            path: 原始路径
            
        Returns:
            str: 安全处理后的路径
        """
        if not path:
            return None
        
        # 检查是否为绝对路径
        if os.path.isabs(path):
            # 获取当前工作目录
            current_dir = os.getcwd()
            
            # 尝试转换为相对路径
            try:
                return os.path.relpath(path, current_dir)
            except ValueError:
                # 如果在不同驱动器上，无法创建相对路径
                # 使用临时目录作为备选
                import tempfile
                temp_dir = os.path.join(
                    tempfile.gettempdir(), "pandas_ai_plots"
                )
                os.makedirs(temp_dir, exist_ok=True)
                return temp_dir
        
        return path
    
    def initialize_agent(self, df: pd.DataFrame, output_dir: str = None):
        """初始化 Agent 实例"""
        # 创建必要的目录

        self.output_dir = output_dir
        plots_dir = os.path.join(output_dir, "plots")
        os.makedirs(plots_dir, exist_ok=True)
        
        # 修改配置中的保存路径
        config = self._get_agent_config()
        
        if output_dir:
            config["save_charts_path"] = self._get_safe_path(
                os.path.join(output_dir, "plots")
            )
        
        df = self.dataframe_initialization(df)
        
        # 保存 DataFrame 的副本供后续使用
        self._df = df.copy()

        # 创建 Agent
        self.agent = Agent(
            df,
            config=config,
            description=self._get_agent_description()
        )

        # 增加技能
        # self.agent.add_skills(AgentSkills.bar_line_chart_skills)
        self.agent.add_skills(AgentSkills.calculate_quarterly_data)
        self.agent.add_skills(AgentSkills.yoy_or_qoq_growth)
        self.agent.add_skills(AgentSkills.setup_matplotlib_fonts)
        print(self._get_agent_description())
        print("\n=== Agent 初始化完成 ===")

    def _get_generated_plot(self):
        """获取生成的图表文件"""
        chart_dir = "src/output/pandasai/plot"
        if os.path.exists(chart_dir):
            return [
                f for f in os.listdir(chart_dir) 
                if f.endswith(('.png', '.jpg', '.jpeg', '.svg'))
            ]
        return []

    def _get_error_traceback(self):
        """获取错误堆栈信息"""
        return traceback.format_exc()

    def dataframe_initialization(self, df: pd.DataFrame) -> pd.DataFrame:
        """初始化DataFrame
        输入是dataframe格式的表格
        1、把【报告日】列的'yyyymmdd'转为日期格式
        2、把【股票代码】列转为字符串类型，也要确保例如000001这种格式不会转为：1
        
        Args:
            df (pd.DataFrame): 输入的DataFrame
            
        Returns:
            pd.DataFrame: 处理后的DataFrame
        """
        try:
            # 检查是否有报告日列
            if '报告日' in df.columns:
                # 将报告日列转换为datetime格式
                df['报告日'] = pd.to_datetime(df['报告日'], format='%Y%m%d')
            
            # 查找所有包含"股票代码"的列
            code_columns = [
                col for col in df.columns 
                if any(
                    keyword in col.lower() 
                    for keyword in ['股票代码', '代码']
                )
            ]
            
            # 处理股票代码列
            for col in code_columns:
                # 确保股票代码为字符串类型并补齐6位
                df[col] = df[col].astype(str).str.zfill(6)
            
            # 定义不应该转换为数值的列
            non_numeric_columns = (
                code_columns + 
                ['报告日', '股票名称', '申万一级', '申万二级']
            )
            
            # 对数值列进行类型转换
            for col in df.columns:
                if col not in non_numeric_columns:
                    try:
                        # 尝试转换为数值类型
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    except Exception:
                        continue
            
            return df
        
        except Exception as e:
            print(f"DataFrame初始化过程中出错: {str(e)}")
            print(traceback.format_exc())
            return None
        
    def _load_prompt(self, prompt_file: str) -> str:
        """从文件加载 prompt
        
        Args:
            prompt_file (str): prompt 文件的相对路径
            
        Returns:
            str: 加载的 prompt 内容
        """
        try:
            prompt_path = os.path.join(os.path.dirname(__file__), prompt_file)
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            self.logger.error(f"加载 prompt 文件时出错: {str(e)}") # 使用 logger
            return ""

    
    def analyze(self, query: str, progress_callback=None) -> Union[Dict[str, Any], Any]:
        """
        使用PandasAI执行分析请求，并在结果为空DataFrame时自动重试。

        Args:
            query: 用户的查询字符串
            progress_callback: 可选的进度回调函数，用于报告整体进度（非重试状态）。

        Returns:
            PandasAI agent.chat() 的原始输出 (可能是dict, str, DataFrame等)
            或包含错误的字典。
        """
        last_exception = None
        response = None

        for attempt in range(self.max_retries + 1):
            try:
                self.logger.info(f"PandasAI 分析尝试次数: {attempt + 1}/{self.max_retries + 1}")

                # 报告初始化分析环境 (只在第一次尝试时报告)
                if attempt == 0 and progress_callback:
                    progress_callback(70.0, "初始化分析环境")

                # 报告分析数据中 (只在第一次尝试时报告)
                if attempt == 0 and progress_callback:
                    progress_callback(75.0, "分析数据中")

                # 使用PandasAI执行分析
                response = self.agent.chat(query)

                # 检查是否为空DataFrame
                if isinstance(response, pd.DataFrame) and response.empty:
                    if attempt < self.max_retries:
                        self.logger.warning(f"分析结果为空 DataFrame，正在重试 ({attempt + 1}/{self.max_retries})...")
                        # 可选：在这里添加短暂的延迟
                        # import time
                        # time.sleep(1)
                        continue  # 继续下一次尝试
                    else:
                        self.logger.warning(f"分析结果为空 DataFrame，已达到最大重试次数 ({self.max_retries})。")
                        break # 达到最大次数，退出循环，返回空 DataFrame
                else:
                    # 成功获取到非空 DataFrame 或其他类型的结果，退出循环
                    self.logger.info("PandasAI 分析成功或返回非空 DataFrame/其他类型结果。")
                    break

            except Exception as e:
                self.logger.error(f"PandasAI 第 {attempt + 1} 次分析尝试失败: {str(e)}")
                last_exception = e
                # 如果发生异常，继续尝试，除非是最后一次尝试
                if attempt >= self.max_retries:
                    self.logger.error("PandasAI 分析因异常达到最大重试次数。")
                    break # 达到最大次数，退出循环
                else:
                    # 可选：在这里添加短暂的延迟
                    # import time
                    # time.sleep(1)
                    continue # 继续下一次尝试

        # 循环结束后处理结果
        if last_exception and response is None: # 如果循环因异常结束且从未成功获取响应
             self.logger.error(f"PandasAI 分析在所有 {self.max_retries + 1} 次尝试后失败: {str(last_exception)}")
             # 记录详细的回溯信息
             error_traceback = traceback.format_exc()
             self.logger.error(error_traceback)
             # 报告分析失败
             if progress_callback:
                 progress_callback(95.0, "分析失败")
             # 返回错误信息字典
             return {
                 "error": f"PandasAI agent execution failed after {self.max_retries + 1} attempts: {str(last_exception)}",
                 "traceback": error_traceback
             }
        else: # 成功获取响应（可能是空DataFrame或非空结果）或最后一次尝试为空DataFrame
             # 报告生成分析结果
             if progress_callback:
                 progress_callback(85.0, "生成分析结果")

             self.logger.info(f"PandasAI 最终响应类型: {type(response)}") # 打印最终响应类型
             # 对于 DataFrame，可以打印更详细的信息
             if isinstance(response, pd.DataFrame):
                 self.logger.info(f"PandasAI 最终响应 DataFrame shape: {response.shape}, empty: {response.empty}")
             else:
                 # 避免打印过长的字符串响应
                 log_response = str(response)[:200] + ('...' if len(str(response)) > 200 else '')
                 self.logger.info(f"PandasAI 最终响应 (截断): {log_response}")

             # 报告格式化输出结果
             if progress_callback:
                 progress_callback(95.0, "格式化输出结果")

             return response # 返回最终得到的 response (可能是空DataFrame)


