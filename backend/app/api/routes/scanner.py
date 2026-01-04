"""股票掃描器 API 路由"""

import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, JSONResponse
from app.models import ScanRequest, ScanResponse, StockData
from sj_trading import execute_scan, generate_csv

router = APIRouter()
logger = logging.getLogger(__name__)

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


@router.post("/scan", response_model=ScanResponse)
async def scan_stocks(request: ScanRequest):
    """
    執行股票掃描

    Args:
        request: 掃描請求參數

    Returns:
        掃描結果

    Raises:
        HTTPException: 當掃描失敗時
    """
    try:
        logger.info(
            f"開始掃描: type={request.scanner_type}, date={request.date}, "
            f"count={request.count}, ascending={request.ascending}"
        )

        # 執行掃描
        results, execution_time, usage_data = execute_scan(
            scanner_type=request.scanner_type,
            date=request.date,
            count=request.count,
            ascending=request.ascending,
            simulation=request.simulation,
            config_file="config.txt",
        )

        # 轉換為 Pydantic 模型
        stock_data = [StockData(**item) for item in results]

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
            elif usage_data["remaining_percent"] < 10:
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
        logger.error(f"配置檔案錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"配置檔案錯誤: {str(e)}")

    except ValueError as e:
        logger.error(f"參數錯誤: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except TimeoutError:
        logger.error("掃描逾時")
        raise HTTPException(status_code=504, detail="掃描逾時，請稍後再試")

    except Exception as e:
        logger.error(f"掃描失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"掃描失敗: {str(e)}")


@router.post("/export")
async def export_csv(request: ScanRequest):
    """
    匯出 CSV 檔案

    Args:
        request: 掃描請求參數

    Returns:
        CSV 檔案

    Raises:
        HTTPException: 當匯出失敗時
    """
    try:
        logger.info(f"開始匯出 CSV: date={request.date}, count={request.count}")

        # 執行掃描
        results, _, _ = execute_scan(
            scanner_type=request.scanner_type,
            date=request.date,
            count=request.count,
            ascending=request.ascending,
            simulation=request.simulation,
            config_file="config.txt",
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
        raise HTTPException(status_code=500, detail=f"CSV 匯出失敗: {str(e)}")
