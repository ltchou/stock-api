"""資料庫 CRUD 操作"""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import delete, desc, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_db import ScanHistory, StockDailyData

logger = logging.getLogger(__name__)


async def create_scan_history(
    db: AsyncSession,
    scanner_type: str,
    scan_date: str | None,
    count: int,
    ascending: bool,
    simulation: bool,
    success: bool,
    result_count: int,
    execution_time: float | None = None,
    raw_response: list[dict[str, Any]] | None = None,
    processed_results: list[dict[str, Any]] | None = None,
    usage_data: dict[str, Any] | None = None,
    error_message: str | None = None,
) -> ScanHistory:
    """
    建立掃描歷史記錄

    Args:
        db: 資料庫 session
        scanner_type: 掃描器類型
        scan_date: 掃描日期
        count: 查詢數量
        ascending: 是否升序
        simulation: 是否模擬模式
        success: 是否成功
        result_count: 結果數量
        execution_time: 執行時間（秒）
        raw_response: Shioaji API 原始回應
        processed_results: 處理後的結果
        usage_data: 流量使用資訊
        error_message: 錯誤訊息

    Returns:
        建立的記錄
    """
    scan_record = ScanHistory(
        timestamp=datetime.utcnow(),
        scanner_type=scanner_type,
        scan_date=scan_date,
        count=count,
        ascending=ascending,
        simulation=simulation,
        success=success,
        result_count=result_count,
        execution_time=int(execution_time) if execution_time is not None else None,
        raw_response=raw_response,
        processed_results=processed_results,
        usage_data=usage_data,
        error_message=error_message,
    )

    db.add(scan_record)
    await db.commit()
    await db.refresh(scan_record)

    logger.info(
        f"已儲存掃描記錄: id={scan_record.id}, success={success}, count={result_count}"
    )

    return scan_record


async def get_scan_history(
    db: AsyncSession,
    limit: int = 10,
    offset: int = 0,
) -> list[ScanHistory]:
    """
    取得掃描歷史記錄

    Args:
        db: 資料庫 session
        limit: 查詢數量
        offset: 偏移量

    Returns:
        掃描歷史記錄列表
    """
    result = await db.execute(
        select(ScanHistory)
        .order_by(desc(ScanHistory.timestamp))
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def get_latest_scan(db: AsyncSession) -> ScanHistory | None:
    """
    取得最新一筆掃描記錄

    Args:
        db: 資料庫 session

    Returns:
        最新掃描記錄，若無則回傳 None
    """
    result = await db.execute(
        select(ScanHistory).order_by(desc(ScanHistory.timestamp)).limit(1)
    )
    return result.scalar_one_or_none()


async def cleanup_old_scans(db: AsyncSession, keep_count: int = 10) -> int:
    """
    清理舊的掃描記錄，只保留最近 N 筆

    Args:
        db: 資料庫 session
        keep_count: 保留數量（預設 10 筆）

    Returns:
        刪除的記錄數量
    """
    # 查詢所有記錄，按時間倒序
    result = await db.execute(select(ScanHistory).order_by(desc(ScanHistory.timestamp)))
    all_records = list(result.scalars().all())

    # 如果總數小於等於保留數量，不刪除
    if len(all_records) <= keep_count:
        return 0

    # 取得要刪除的記錄（保留前 N 筆，刪除其餘）
    records_to_delete = all_records[keep_count:]
    deleted_count = len(records_to_delete)

    # 刪除舊記錄
    for record in records_to_delete:
        await db.delete(record)

    await db.commit()

    logger.info(f"已清理 {deleted_count} 筆舊掃描記錄，保留最近 {keep_count} 筆")

    return deleted_count


async def upsert_daily_stocks(
    db: AsyncSession,
    date: str,
    stocks_data: list[dict[str, Any]],
    scanner_type: str = "AmountRank",
    ascending: bool = False,
) -> int:
    """
    批次插入或更新每日股票資料

    Args:
        db: 資料庫 session
        date: 交易日期
        stocks_data: 股票資料列表
        scanner_type: 掃描器類型
        ascending: 此批快取資料的排序方向

    Returns:
        插入/更新的記錄數量
    """
    # 先刪除該日期、掃描器類型與排序方向的舊資料（如果存在）
    await db.execute(
        delete(StockDailyData).where(
            StockDailyData.date == date,
            StockDailyData.scanner_type == scanner_type,
            StockDailyData.cache_ascending == ascending,
        )
    )

    # 去重複：對於同一個股票代碼，保留時間戳最新的那筆
    unique_stocks: dict[str, tuple[int, dict[str, Any]]] = {}
    for index, stock in enumerate(stocks_data):
        code = stock.get("code")
        ts = stock.get("ts", 0)
        if not isinstance(code, str) or not code:
            continue

        # 如果這個代碼還沒見過，或者這筆資料的時間戳更新，就更新記錄
        if code not in unique_stocks or ts > unique_stocks[code][1].get("ts", 0):
            unique_stocks[code] = (index, stock)

    # Shioaji 已依 scanner_type 與 canonical ascending 參數排好序。
    # 以 API 回傳順序建立 rank，避免後端猜錯新 scanner_type 的排序欄位。
    sorted_stocks = [
        stock for _, stock in sorted(unique_stocks.values(), key=lambda item: item[0])
    ]

    # 批次插入去重後的資料（帶有正確的排名）
    for rank, stock in enumerate(sorted_stocks, start=1):
        daily_record = StockDailyData(
            date=date,
            scanner_type=scanner_type,
            cache_ascending=ascending,
            code=stock.get("code"),
            name=stock.get("name"),
            rank=rank,  # 使用計算出的排名（1-based）
            open=stock.get("open"),
            high=stock.get("high"),
            low=stock.get("low"),
            close=stock.get("close"),
            volume=stock.get("volume"),
            total_volume=stock.get("total_volume"),
            amount=stock.get("amount"),
            total_amount=stock.get("total_amount"),
            change_price=stock.get("change_price"),
            change_percent=stock.get("change_percent"),
            average_price=stock.get("average_price"),
            buy_price=stock.get("buy_price"),
            buy_volume=stock.get("buy_volume"),
            sell_price=stock.get("sell_price"),
            sell_volume=stock.get("sell_volume"),
            ts=stock.get("ts"),
        )
        db.add(daily_record)

    await db.commit()

    count = len(sorted_stocks)
    logger.info(
        f"已儲存 {date} 的 {count} 筆股票資料（原始 {len(stocks_data)} 筆，去重後 {count} 筆）"
    )

    return count


async def get_daily_stocks(
    db: AsyncSession,
    date: str,
    limit: int = 200,
    ascending: bool = False,
    scanner_type: str = "AmountRank",
) -> list[StockDailyData]:
    """
    取得指定日期的股票資料

    Args:
        db: 資料庫 session
        date: 交易日期
        limit: 查詢數量
        ascending: 快取資料的排序方向（False=大到小，True=小到大）
        scanner_type: 掃描器類型（用於決定排序欄位）

    Returns:
        股票資料列表（按指定欄位排序）
    """
    # 快取資料的 rank 代表該排序方向下的 upstream scanner 排名。
    order_clause = StockDailyData.rank.asc()

    result = await db.execute(
        select(StockDailyData)
        .where(
            StockDailyData.date == date,
            StockDailyData.scanner_type == scanner_type,
            StockDailyData.cache_ascending == ascending,
        )
        .order_by(order_clause)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_daily_stock_count(
    db: AsyncSession,
    date: str,
    scanner_type: str = "AmountRank",
    ascending: bool = False,
) -> int:
    """
    取得指定日期與掃描器類型的快取資料筆數。

    Args:
        db: 資料庫 session
        date: 交易日期
        scanner_type: 掃描器類型
        ascending: 快取資料的排序方向

    Returns:
        快取資料筆數
    """
    result = await db.execute(
        select(func.count())
        .select_from(StockDailyData)
        .where(
            StockDailyData.date == date,
            StockDailyData.scanner_type == scanner_type,
            StockDailyData.cache_ascending == ascending,
        )
    )
    return int(result.scalar_one())


async def get_available_scanner_types(db: AsyncSession, date: str) -> list[str]:
    """
    取得指定日期中有資料的掃描器類型列表。

    Args:
        db: 資料庫 session
        date: 交易日期

    Returns:
        掃描器類型列表
    """
    result = await db.execute(
        select(distinct(StockDailyData.scanner_type))
        .where(StockDailyData.date == date)
        .order_by(StockDailyData.scanner_type)
    )
    return [row[0] for row in result.all()]


async def get_available_dates(db: AsyncSession) -> list[str]:
    """
    取得資料庫中有資料的日期列表

    Args:
        db: 資料庫 session

    Returns:
        日期列表（降序排列）
    """
    result = await db.execute(
        select(distinct(StockDailyData.date)).order_by(desc(StockDailyData.date))
    )
    return [row[0] for row in result.all()]
