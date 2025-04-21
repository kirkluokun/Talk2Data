"""
配置模块，包含应用程序的各种配置项
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path

# 获取项目根目录
ROOT_DIR = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    # 应用设置
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Financial Data Chat App"
    ENVIRONMENT: str

    # 安全设置
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # 数据库
    DATABASE_URL: str
    ASYNC_DATABASE_URL: str

    # Redis
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    REDIS_PASSWORD: Optional[str] = None

    # 日志
    LOG_LEVEL: str

    # 缓存
    CACHE_DIR: str
    CHARTS_DIR: str
    LOGS_DIR: str

    # API Keys
    OPENAI_API_KEY: str
    DEEPSEEK_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    DASHSCOPE_API_KEY: Optional[str] = None
    SILICONFLOW_API_KEY: Optional[str] = None
    ARK_API_KEY: Optional[str] = None
    TOGETHERAI_API_KEY: Optional[str] = None
    
    class Config:
        env_file = os.path.join(ROOT_DIR, ".env")
        case_sensitive = True


settings = Settings()

# Redis配置
class RedisConfig:
    """Redis配置"""
    REDIS_HOST = settings.REDIS_HOST
    REDIS_PORT = settings.REDIS_PORT
    REDIS_DB = settings.REDIS_DB
    REDIS_PASSWORD = settings.REDIS_PASSWORD
    
    # Celery Broker URL
    @classmethod
    def get_broker_url(cls) -> str:
        """获取Celery Broker URL"""
        if cls.REDIS_PASSWORD:
            return f"redis://:{cls.REDIS_PASSWORD}@{cls.REDIS_HOST}:{cls.REDIS_PORT}/{cls.REDIS_DB}"
        return f"redis://{cls.REDIS_HOST}:{cls.REDIS_PORT}/{cls.REDIS_DB}"
    
    # Celery Result Backend URL
    @classmethod
    def get_backend_url(cls) -> str:
        """获取Celery Result Backend URL"""
        return cls.get_broker_url()
    
    # 缓存目录
    CACHE_DIR = settings.CACHE_DIR
    
    # 图表目录
    CHARTS_DIR = settings.CHARTS_DIR
    
    # 日志目录
    LOGS_DIR = settings.LOGS_DIR
    
    # 日志级别
    LOG_LEVEL = settings.LOG_LEVEL
    
    # API前缀
    API_PREFIX = settings.API_V1_STR

# 应用配置
class AppConfig:
    """应用配置"""
    # 输出目录
    OUTPUT_DIR = "output"
    
    # 日志级别
    LOG_LEVEL = "INFO"
    
    # API前缀
    API_PREFIX = settings.API_V1_STR

# 任务进度阶段定义
class ProgressStages:
    """任务进度阶段"""
    # 查询解析阶段 (0-33%)
    INIT = "初始化"
    QUERY_PARSE_START = "开始解析查询"
    QUERY_EXTRACT_INFO = "提取查询关键信息"
    QUERY_STANDARDIZE = "标准化财务指标"
    QUERY_PARSE_COMPLETE = "查询解析完成"
    
    # 数据获取阶段 (33-66%)
    DATA_FETCH_START = "开始准备数据获取"
    DATA_SQL_GENERATING = "生成SQL查询"
    DATA_SQL_EXECUTING = "执行数据库查询"
    DATA_PROCESSING = "处理查询结果"
    DATA_FETCH_COMPLETE = "数据获取完成"
    
    # 数据分析阶段 (66-100%)
    ANALYSIS_INIT = "初始化分析环境"
    ANALYSIS_PROCESSING = "分析数据中"
    ANALYSIS_VISUALIZING = "生成分析结果"
    ANALYSIS_FORMATTING = "格式化输出结果"
    ANALYSIS_COMPLETE = "分析完成"

# 任务进度百分比
class ProgressPercentage:
    """任务进度百分比"""
    # 查询解析阶段 (0-33%)
    INIT = 0.0
    QUERY_PARSE_START = 5.0
    QUERY_EXTRACT_INFO = 15.0
    QUERY_STANDARDIZE = 25.0
    QUERY_PARSE_COMPLETE = 33.0
    
    # 数据获取阶段 (33-66%)
    DATA_FETCH_START = 38.0
    DATA_SQL_GENERATING = 45.0
    DATA_SQL_EXECUTING = 50.0
    DATA_PROCESSING = 60.0
    DATA_FETCH_COMPLETE = 66.0
    
    # 数据分析阶段 (66-100%)
    ANALYSIS_INIT = 70.0
    ANALYSIS_PROCESSING = 75.0
    ANALYSIS_VISUALIZING = 85.0
    ANALYSIS_FORMATTING = 95.0
    ANALYSIS_COMPLETE = 100.0 