"""匯入歷史股票資料腳本"""

import asyncio
import logging
import time

from app.crud import upsert_daily_stocks
from app.database import async_session_maker, close_db, init_db
from app.utils import get_last_n_trading_days
from sj_trading import execute_scan

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def import_historical_data(days: int = 10):
    """
    匯入最近 N 個交易日的股票資料

    Args:
        days: 天數（預設 10）
    """
    try:
        # 初始化資料庫
        logger.info("初始化資料庫...")
        await init_db()

        # 取得最近 N 個交易日
        trading_days = get_last_n_trading_days(days)
        logger.info(f"準備匯入最近 {days} 個交易日的資料")
        logger.info(f"交易日列表: {trading_days}")

        success_count = 0
        failed_count = 0

        # 逐日抓取資料
        for date in trading_days:
            try:
                logger.info(f"\n{'=' * 50}")
                logger.info(f"開始處理 {date} 的資料...")

                # 呼叫 Shioaji API 取得 top 200 股票（按成交金額排名）
                results, execution_time, usage_data = execute_scan(
                    scanner_type="AmountRank",  # 成交金額排名
                    date=date,
                    count=200,
                    ascending=False,  # 降序：最高金額在前
                    simulation=True,
                    config_file="config.txt",
                )

                if not results:
                    logger.warning(f"{date} 沒有資料（可能是假日或資料未更新）")
                    failed_count += 1
                    continue

                # 加上排名欄位
                for idx, stock in enumerate(results, 1):
                    stock["rank"] = idx

                logger.info(f"{date} 取得 {len(results)} 筆資料")

                # 顯示第一筆資料的欄位（用於確認 amount/total_amount）
                if results and success_count == 0:
                    logger.info(f"第一筆資料欄位: {list(results[0].keys())}")
                    logger.info(
                        f"第一筆資料範例: code={results[0].get('code')}, "
                        f"name={results[0].get('name')}, "
                        f"total_amount={results[0].get('total_amount')}, "
                        f"amount={results[0].get('amount')}"
                    )

                # 儲存到資料庫
                async with async_session_maker() as db:
                    saved_count = await upsert_daily_stocks(db, date, results)
                    logger.info(f"{date} 成功儲存 {saved_count} 筆資料")

                success_count += 1

                # 顯示進度
                logger.info(f"進度: {success_count + failed_count}/{days}")

                # 加入延遲避免連線過多（等待 10 秒確保舊連線完全關閉）
                if success_count + failed_count < days:
                    logger.info("等待 10 秒後繼續...")
                    time.sleep(10)

            except Exception as e:
                logger.error(f"{date} 處理失敗: {e}", exc_info=True)
                failed_count += 1

        # 總結
        logger.info(f"\n{'=' * 50}")
        logger.info("匯入完成！")
        logger.info(f"成功: {success_count} 天")
        logger.info(f"失敗: {failed_count} 天")
        logger.info(f"總計: {success_count + failed_count} 天")

    except Exception as e:
        logger.error(f"匯入過程發生錯誤: {e}", exc_info=True)
    finally:
        await close_db()


if __name__ == "__main__":
    # 匯入最近 10 個交易日的資料
    asyncio.run(import_historical_data(days=10))
