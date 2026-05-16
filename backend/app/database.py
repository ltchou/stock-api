"""資料庫配置與連線管理"""

import logging
from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

# 資料庫路徑
DB_DIR = Path(__file__).parent.parent / "data"
DB_FILE = DB_DIR / "stocks.db"
DATABASE_URL = f"sqlite+aiosqlite:///{DB_FILE}"
logger = logging.getLogger(__name__)

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
        await migrate_stock_daily_data_cache_direction(conn)


async def migrate_stock_daily_data_cache_direction(conn: AsyncConnection) -> None:
    """
    將舊版每日快取表升級為可依排序方向分開儲存。
    """
    table_info = await conn.execute(text("PRAGMA table_info(stock_daily_data)"))
    columns = {row[1] for row in table_info.fetchall()}
    if not columns or "cache_ascending" in columns:
        return

    logger.warning("升級 stock_daily_data schema：新增 cache_ascending 快取方向欄位")
    await conn.execute(
        text("ALTER TABLE stock_daily_data RENAME TO stock_daily_data_old")
    )
    await conn.run_sync(Base.metadata.create_all)

    await conn.execute(
        text(
            """
            INSERT INTO stock_daily_data (
                id, date, scanner_type, cache_ascending, code, name, rank,
                open, high, low, close, volume, total_volume, amount,
                total_amount, change_price, change_percent, average_price,
                buy_price, buy_volume, sell_price, sell_volume, ts, created_at
            )
            SELECT
                id, date, scanner_type, 0, code, name, rank,
                open, high, low, close, volume, total_volume, amount,
                total_amount, change_price, change_percent, average_price,
                buy_price, buy_volume, sell_price, sell_volume, ts, created_at
            FROM stock_daily_data_old
            """
        )
    )
    await conn.execute(text("DROP TABLE stock_daily_data_old"))


async def close_db() -> None:
    """
    關閉資料庫連線
    """
    await engine.dispose()
