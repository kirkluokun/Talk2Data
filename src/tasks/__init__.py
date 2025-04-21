"""
任务包初始化文件
确保Celery可以正确发现和注册所有任务
"""

# 显式导入所有任务模块
from . import financial_query
