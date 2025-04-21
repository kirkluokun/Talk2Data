from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from src.core.config import settings

# 异步数据库引擎
async_engine = create_async_engine(
    "postgresql+asyncpg://finance:finance123@localhost:5432/finance_chat",
    echo=False,  # 设置为True可以看到SQL查询日志
    future=True,
    pool_pre_ping=True,  # 确保连接池中的连接是有效的
)

# 创建异步会话
AsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# 模型基类
Base = declarative_base()


# 依赖注入函数，用于获取数据库会话
async def get_db() -> AsyncSession:
    """获取异步数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close() 