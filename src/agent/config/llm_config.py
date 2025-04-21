# llm_config.py
# 大模型配置模块，用于设置各种LLM API连接和参数

import os
from dotenv import load_dotenv
from pandasai.llm.local_llm import LocalLLM
from pandasai.llm.google_gemini import GoogleGemini
from openai import OpenAI

# 加载环境变量
load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY")
ARK_API_KEY = os.getenv("ARK_API_KEY")

def create_deepseek_llm() -> LocalLLM:
    """创建 火山-LocalLLM 实例"""
    return LocalLLM(
        api_base="https://ark.cn-beijing.volces.com/api/v3",
        model="deepseek-v3-250324",
        api_key=ARK_API_KEY,
        temperature=0,
        max_tokens=8000
    )

def create_openai_llm() -> OpenAI:
    """ 火山 创建 OpenAI 实例，用于调用 API"""
    client = OpenAI(
        api_key=ARK_API_KEY,
        base_url="https://ark.cn-beijing.volces.com/api/v3"
    )
    return client

# 以下是备用的LLM配置，如果需要可以启用
def create_deepseek_original_llm() -> LocalLLM:
    """创建 原始 LocalLLM 实例"""
    return LocalLLM(
        api_base="https://api.deepseek.com/v1",
        model="deepseek-chat",
        api_key=DEEPSEEK_API_KEY,
        max_tokens=8000,
        temperature=0
    )

def create_siliconflow_llm() -> OpenAI:
    """硅基流动-openai格式-deepseek R1-API"""
    client = OpenAI(
        api_key=SILICONFLOW_API_KEY,
        base_url="https://api.siliconflow.cn/v1/chat/completions"
    )
    return client

def create_gemini_llm() -> GoogleGemini:
    """创建 GoogleGemini 实例"""
    return GoogleGemini(
        api_key=GEMINI_API_KEY,
        model="models/gemini-2.0-flash",
        temperature=0,
        max_tokens=8000
    )
