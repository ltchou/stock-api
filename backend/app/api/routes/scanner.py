"""股票掃描器 API 路由"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import (
    cleanup_old_scans,
    create_scan_history,
    get_available_dates,
    get_available_scanner_types,
    get_daily_stock_count,
    get_daily_stocks,
    get_latest_scan,
    get_scan_history,
    upsert_daily_stocks,
)
from app.database import get_db
from app.models import (
    AvailableDatesResponse,
    DailyStockItem,
    DailyStockResponse,
    ScanHistoryItem,
    ScanHistoryResponse,
    ScanRequest,
    ScanResponse,
    StockData,
)
from sj_trading import execute_scan, generate_csv  # type: ignore[import-untyped]

router = APIRouter()
logger = logging.getLogger(__name__)
CACHE_FILL_COUNT = 200
CACHE_FILL_ASCENDING = False

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def daily_stock_to_stock_data(item) -> StockData:
    """
    將資料庫每日股票資料轉成 API 回應格式。
    """
    return StockData(
        code=item.code,
        name=item.name,
        open=item.open,
        high=item.high,
        low=item.low,
        close=item.close,
        volume=item.volume,
        total_volume=item.total_volume,
        amount=item.amount,
        total_amount=item.total_amount,
        change_price=item.change_price,
        change_percent=item.change_percent,
        average_price=item.average_price,
        buy_price=item.buy_price,
        buy_volume=item.buy_volume,
        sell_price=item.sell_price,
        sell_volume=item.sell_volume,
        ts=item.ts,
    )


def daily_stock_to_dict(item) -> dict:
    """
    將資料庫每日股票資料轉成 CSV 匯出使用的 dict。
    """
    return {
        "code": item.code,
        "name": item.name,
        "date": item.date,
        "open": item.open,
        "high": item.high,
        "low": item.low,
        "close": item.close,
        "volume": item.volume,
        "total_volume": item.total_volume,
        "amount": item.amount,
        "total_amount": item.total_amount,
        "change_price": item.change_price,
        "change_percent": item.change_percent,
        "average_price": item.average_price,
        "buy_price": item.buy_price,
        "buy_volume": item.buy_volume,
        "sell_price": item.sell_price,
        "sell_volume": item.sell_volume,
        "ts": item.ts,
    }


def get_stock_sort_value(stock: dict, scanner_type: str):
    """
    取得掃描器類型對應的排序值。
    """
    if scanner_type == "ChangePercentRank":
        change_percent = stock.get("change_percent")
        if change_percent is not None:
            return change_percent
        rank_value = stock.get("rank_value")
        if rank_value is not None:
            return rank_value
        return 0
    if scanner_type == "VolumeRank":
        total_volume = stock.get("total_volume")
        return total_volume if total_volume is not None else 0
    total_amount = stock.get("total_amount")
    return total_amount if total_amount is not None else 0


def select_requested_results(
    stocks: list[dict],
    scanner_type: str,
    count: int,
    ascending: bool,
) -> list[dict]:
    """
    從抓回來的 canonical 快取資料中，依使用者要求排序並取出指定筆數。
    """
    return sorted(
        stocks,
        key=lambda item: get_stock_sort_value(item, scanner_type),
        reverse=not ascending,
    )[:count]


@router.post("/scan", response_model=ScanResponse)
async def scan_stocks(
    request: ScanRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    執行股票掃描（優先從資料庫讀取）

    如果資料庫已有該日期的資料，直接返回資料庫中的記錄。
    只有當資料庫沒有資料時，才會呼叫 Shioaji API。

    Args:
        request: 掃描請求參數
        db: 資料庫 session

    Returns:
        掃描結果

    Raises:
        HTTPException: 當掃描失敗時
    """
    raw_scanners = None
    results = None
    execution_time = None
    usage_data = None
    error_msg = None

    try:
        logger.info(
            f"開始掃描: type={request.scanner_type}, date={request.date}, "
            f"count={request.count}, ascending={request.ascending}"
        )

        # 首先檢查資料庫是否已有足夠筆數（支援所有掃描器類型）
        cached_count = await get_daily_stock_count(
            db,
            request.date,
            scanner_type=request.scanner_type,
        )
        db_results = []
        if cached_count >= request.count:
            db_results = await get_daily_stocks(
                db,
                request.date,
                limit=request.count,
                ascending=request.ascending,
                scanner_type=request.scanner_type,
            )
        elif cached_count > 0:
            logger.info(
                f"資料庫僅有 {cached_count} 筆 {request.date} 的 "
                f"{request.scanner_type} 資料，少於要求的 {request.count} 筆，將重新呼叫 API"
            )

        if db_results:
            logger.info(
                f"從資料庫讀取 {request.date} 的 {request.scanner_type} 資料，共 {len(db_results)} 筆"
            )
            execution_time = 0.0

            # 轉換資料庫結果為 StockData 格式
            stock_data = [daily_stock_to_stock_data(item) for item in db_results]

            # 資料已經按照 ascending 參數正確排序，不需要額外處理

            response_data = ScanResponse(
                status="success",
                data=stock_data,
                total_count=len(stock_data),
                execution_time=execution_time,
                message=f"從資料庫讀取（共 {len(db_results)} 筆）",
            )

            return response_data

        # 資料庫沒有足夠資料，抓滿 200 筆後寫入快取，再回傳使用者要求的筆數
        logger.info(
            f"資料庫無足夠資料，呼叫 Shioaji API 抓取 {CACHE_FILL_COUNT} 筆 "
            f"canonical 資料（ascending={CACHE_FILL_ASCENDING}）"
        )
        results, execution_time, usage_data = execute_scan(
            scanner_type=request.scanner_type,
            date=request.date,
            count=CACHE_FILL_COUNT,
            ascending=CACHE_FILL_ASCENDING,
            simulation=request.simulation,
            config_file="config.txt",
        )

        # 記錄原始資料（用於除錯）
        raw_scanners = results.copy() if results else []
        logger.debug(f"收到 {len(raw_scanners)} 筆原始掃描資料")

        # 儲存所有掃描器類型的資料到每日股票資料表
        cache_write_succeeded = False
        if results:
            try:
                count = await upsert_daily_stocks(
                    db, request.date, results, scanner_type=request.scanner_type
                )
                cache_write_succeeded = True
                logger.info(
                    f"已將 {count} 筆 {request.scanner_type} 資料儲存到每日股票資料表"
                )
            except Exception as e:
                await db.rollback()
                logger.error(f"儲存每日股票資料失敗: {e}")
                # 不影響主流程，繼續執行

        stock_data = []
        if cache_write_succeeded:
            db_results = await get_daily_stocks(
                db,
                request.date,
                limit=request.count,
                ascending=request.ascending,
                scanner_type=request.scanner_type,
            )
            stock_data = [daily_stock_to_stock_data(item) for item in db_results]
        if not stock_data:
            requested_results = select_requested_results(
                results or [],
                request.scanner_type,
                request.count,
                request.ascending,
            )
            stock_data = [StockData(**item) for item in requested_results]

        # 儲存成功的掃描記錄到資料庫
        await create_scan_history(
            db=db,
            scanner_type=request.scanner_type,
            scan_date=request.date,
            count=request.count,
            ascending=request.ascending,
            simulation=request.simulation,
            success=True,
            result_count=len(stock_data),
            execution_time=execution_time,
            raw_response=raw_scanners,
            processed_results=[item.dict() for item in stock_data],
            usage_data=usage_data,
        )

        # 清理舊記錄，只保留最近 10 筆
        await cleanup_old_scans(db, keep_count=10)

        response_data = ScanResponse(
            status="success",
            data=stock_data,
            total_count=len(stock_data),
            execution_time=execution_time,
        )

        # 檢查流量狀況並設定適當的 status code
        if usage_data:
            if usage_data["is_over_limit"]:
                # 流量已超限，回傳 429 Too Many Requests
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": usage_data["warning"],
                        "bytes_used": usage_data["bytes_used"],
                        "limit_bytes": usage_data["limit_bytes"],
                    },
                )
            if usage_data["remaining_percent"] < 10:
                # 流量剩餘不足 10%，回傳 206 Partial Content（帶警告和完整資料）
                return JSONResponse(
                    status_code=206,
                    content={
                        "status": "success",
                        "data": [item.dict() for item in stock_data],
                        "total_count": len(stock_data),
                        "execution_time": execution_time,
                        "warning": f"警告：流量即將用盡，剩餘 {usage_data['remaining_percent']:.2f}%",
                    },
                )

        return response_data

    except FileNotFoundError as e:
        error_msg = f"配置檔案錯誤: {e!s}"
        logger.error(error_msg)

        # 儲存失敗記錄
        await create_scan_history(
            db=db,
            scanner_type=request.scanner_type,
            scan_date=request.date,
            count=request.count,
            ascending=request.ascending,
            simulation=request.simulation,
            success=False,
            result_count=0,
            error_message=error_msg,
        )

        raise HTTPException(status_code=500, detail=error_msg)

    except ValueError as e:
        error_msg = f"參數錯誤: {e!s}"
        logger.error(error_msg)

        # 儲存失敗記錄
        await create_scan_history(
            db=db,
            scanner_type=request.scanner_type,
            scan_date=request.date,
            count=request.count,
            ascending=request.ascending,
            simulation=request.simulation,
            success=False,
            result_count=0,
            error_message=error_msg,
        )

        raise HTTPException(status_code=400, detail=str(e))

    except TimeoutError:
        error_msg = "掃描逾時"
        logger.error(error_msg)

        # 儲存失敗記錄
        await create_scan_history(
            db=db,
            scanner_type=request.scanner_type,
            scan_date=request.date,
            count=request.count,
            ascending=request.ascending,
            simulation=request.simulation,
            success=False,
            result_count=0,
            error_message=error_msg,
        )

        raise HTTPException(status_code=504, detail="掃描逾時，請稍後再試")

    except Exception as e:
        error_msg = f"掃描失敗: {e!s}"
        logger.error(error_msg, exc_info=True)

        # 儲存失敗記錄
        await create_scan_history(
            db=db,
            scanner_type=request.scanner_type,
            scan_date=request.date,
            count=request.count,
            ascending=request.ascending,
            simulation=request.simulation,
            success=False,
            result_count=0,
            error_message=error_msg,
        )

        raise HTTPException(status_code=500, detail=error_msg)


@router.post("/export")
async def export_csv(
    request: ScanRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    匯出 CSV 檔案（優先從資料庫讀取）

    Args:
        request: 掃描請求參數
        db: 資料庫 session

    Returns:
        CSV 檔案

    Raises:
        HTTPException: 當匯出失敗時
    """
    try:
        logger.info(
            f"開始匯出 CSV: type={request.scanner_type}, date={request.date}, count={request.count}"
        )

        # 先嘗試從資料庫讀取足夠筆數
        cached_count = await get_daily_stock_count(
            db,
            request.date,
            scanner_type=request.scanner_type,
        )
        db_results = []
        if cached_count >= request.count:
            db_results = await get_daily_stocks(
                db,
                request.date,
                limit=request.count,
                ascending=request.ascending,
                scanner_type=request.scanner_type,
            )
        elif cached_count > 0:
            logger.info(
                f"資料庫僅有 {cached_count} 筆 {request.date} 的 "
                f"{request.scanner_type} 資料，少於要求的 {request.count} 筆，將重新呼叫 API 匯出"
            )

        if db_results:
            logger.info(
                f"從資料庫讀取 {request.date} 的資料用於匯出，共 {len(db_results)} 筆"
            )
            # 轉換為字典列表
            results = [daily_stock_to_dict(item) for item in db_results]
        else:
            # 資料庫沒有足夠資料，抓滿 200 筆後寫入快取，再匯出使用者要求的筆數
            logger.info(
                f"資料庫無足夠資料，呼叫 Shioaji API 抓取 {CACHE_FILL_COUNT} 筆 "
                f"canonical 資料進行匯出（ascending={CACHE_FILL_ASCENDING}）"
            )
            fetched_results, _, _ = execute_scan(
                scanner_type=request.scanner_type,
                date=request.date,
                count=CACHE_FILL_COUNT,
                ascending=CACHE_FILL_ASCENDING,
                simulation=request.simulation,
                config_file="config.txt",
            )

            cache_write_succeeded = False
            if fetched_results:
                try:
                    await upsert_daily_stocks(
                        db,
                        request.date,
                        fetched_results,
                        scanner_type=request.scanner_type,
                    )
                    cache_write_succeeded = True
                    logger.info(
                        f"已將匯出取得的 {len(fetched_results)} 筆資料儲存到每日股票資料表"
                    )
                except Exception as e:
                    await db.rollback()
                    logger.error(f"儲存匯出取得的每日股票資料失敗: {e}")

            results = []
            if cache_write_succeeded:
                db_results = await get_daily_stocks(
                    db,
                    request.date,
                    limit=request.count,
                    ascending=request.ascending,
                    scanner_type=request.scanner_type,
                )
                results = [daily_stock_to_dict(item) for item in db_results]
            if not results:
                results = select_requested_results(
                    fetched_results or [],
                    request.scanner_type,
                    request.count,
                    request.ascending,
                )

        # 產生 CSV
        csv_content = generate_csv(results)

        # 返回 CSV 檔案
        return Response(
            content=csv_content.encode("utf-8-sig"),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=stock_scan_{request.date}.csv"
            },
        )

    except Exception as e:
        logger.error(f"CSV 匯出失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"CSV 匯出失敗: {e!s}")


@router.get("/scan/history", response_model=ScanHistoryResponse)
async def get_history(
    limit: int = 10,
    offset: int = 0,
    *,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    取得掃描歷史記錄

    Args:
        limit: 查詢數量（預設 10）
        offset: 偏移量（預設 0）
        db: 資料庫 session

    Returns:
        掃描歷史記錄列表

    Raises:
        HTTPException: 當查詢失敗時
    """
    try:
        logger.info(f"查詢掃描歷史: limit={limit}, offset={offset}")

        # 查詢歷史記錄
        history = await get_scan_history(db, limit=limit, offset=offset)

        # 轉換為 Pydantic 模型
        history_items = [ScanHistoryItem.model_validate(item) for item in history]

        return ScanHistoryResponse(
            status="success",
            data=history_items,
            total_count=len(history_items),
        )

    except Exception as e:
        logger.error(f"查詢歷史失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查詢歷史失敗: {e!s}")


@router.get("/scan/latest")
async def get_latest(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    取得最新一筆掃描記錄

    Args:
        db: 資料庫 session

    Returns:
        最新掃描記錄

    Raises:
        HTTPException: 當查詢失敗時
    """
    try:
        logger.info("查詢最新掃描記錄")

        # 查詢最新記錄
        latest = await get_latest_scan(db)

        if not latest:
            raise HTTPException(status_code=404, detail="沒有掃描記錄")

        # 轉換為 Pydantic 模型
        latest_item = ScanHistoryItem.model_validate(latest)

        return {
            "status": "success",
            "data": latest_item,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查詢最新記錄失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查詢最新記錄失敗: {e!s}")


@router.get("/daily/{date}", response_model=DailyStockResponse)
async def get_daily_data(
    date: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 200,
    scanner_type: str | None = None,
):
    """
    取得指定日期的股票資料

    Args:
        date: 交易日期（格式：YYYY-MM-DD）
        limit: 查詢數量（預設 200）
        db: 資料庫 session

    Returns:
        該日期的股票資料

    Raises:
        HTTPException: 當查詢失敗時
    """
    try:
        logger.info(f"查詢每日資料: date={date}, limit={limit}")

        selected_scanner_type = scanner_type
        if selected_scanner_type is None:
            scanner_types = await get_available_scanner_types(db, date)
            if not scanner_types:
                raise HTTPException(status_code=404, detail=f"找不到 {date} 的資料")
            selected_scanner_type = (
                "AmountRank" if "AmountRank" in scanner_types else scanner_types[0]
            )

        # 查詢資料
        stocks = await get_daily_stocks(
            db, date=date, limit=limit, scanner_type=selected_scanner_type
        )

        if not stocks:
            raise HTTPException(status_code=404, detail=f"找不到 {date} 的資料")

        # 轉換為 Pydantic 模型
        stock_items = [DailyStockItem.model_validate(stock) for stock in stocks]

        return DailyStockResponse(
            status="success",
            date=date,
            data=stock_items,
            total_count=len(stock_items),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查詢每日資料失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查詢失敗: {e!s}")


@router.get("/daily/dates/list", response_model=AvailableDatesResponse)
async def get_dates(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    取得資料庫中有資料的日期列表

    Args:
        db: 資料庫 session

    Returns:
        可用日期列表

    Raises:
        HTTPException: 當查詢失敗時
    """
    try:
        logger.info("查詢可用日期列表")

        # 查詢日期
        dates = await get_available_dates(db)

        return AvailableDatesResponse(
            status="success",
            dates=dates,
            total_count=len(dates),
        )

    except Exception as e:
        logger.error(f"查詢日期列表失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查詢失敗: {e!s}")
