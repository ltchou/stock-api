"""資料庫配置與連線管理"""

from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

# 資料庫路徑
DB_DIR = Path(__file__).parent.parent / "data"
DB_FILE = DB_DIR / "stocks.db"
DATABASE_URL = f"sqlite+aiosqlite:///{DB_FILE}"

# 建立資料庫目錄
DB_DIR.mkdir(parents=True, exist_ok=True)

# 建立 async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # 設為 True 可以看到 SQL 語句
    future=True,
)

# 建立 async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# 建立 Base class
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession]:
    """
    取得資料庫 session

    Yields:
        AsyncSession: 資料庫 session
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """
    初始化資料庫，建立所有表格
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    關閉資料庫連線
    """
    await engine.dispose()
