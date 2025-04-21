"""
Celery应用模块，用于配置和创建Celery实例
"""

from celery import Celery
import sys
import os

# 添加上级目录到Python路径
current_path = os.path.dirname(os.path.abspath(__file__))
parent_path = os.path.dirname(current_path)
sys.path.insert(0, parent_path)

from core.config import RedisConfig

# 创建Celery实例
celery_app = Celery(
    'financial_data_chat',
    broker=RedisConfig.get_broker_url(),
    backend=RedisConfig.get_backend_url()
)

# 配置Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=False,
    task_track_started=True,
    task_publish_retry=True,
    task_publish_retry_policy={
        'max_retries': 3,
        'interval_start': 0,
        'interval_step': 0.2,
        'interval_max': 0.5,
    },
)

# 自动发现任务
celery_app.autodiscover_tasks(['tasks'])

# 显式导入任务模块以确保任务被注册 - 不再需要，autodiscover会处理
# import tasks.financial_query

if __name__ == '__main__':
    celery_app.start() 