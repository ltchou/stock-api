"""股票掃描器模組"""

import csv
import logging
import time
from io import StringIO
from typing import Any

from sj_trading.api_client import ShioajiClient
from sj_trading.config import load_config

logger = logging.getLogger(__name__)

# 配置 logging level 為 DEBUG 以顯示詳細資訊
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def scanner_to_dict(scanner: Any) -> dict[str, Any]:
    """
    將 scanner 物件轉換為字典

    使用官方文件建議的方法：使用 __dict__ 屬性
    參考：https://sinotrade.github.io/tutor/market_data/scanners/

    Args:
        scanner: Shioaji scanner 物件

    Returns:
        包含 scanner 屬性的字典
    """
    result = scanner.__dict__.copy()
    logger.debug(f"Scanner object keys: {list(result.keys())}")
    logger.debug(f"Sample scanner data: {result}")

    # 欄位名稱映射（處理可能的命名差異）
    field_mapping = {
        "changePercent": "change_percent",
        "changePrice": "change_price",
        "totalVolume": "total_volume",
        "totalAmount": "total_amount",
        "averagePrice": "average_price",
        "buyPrice": "buy_price",
        "buyVolume": "buy_volume",
        "sellPrice": "sell_price",
        "sellVolume": "sell_volume",
    }

    # 應用欄位映射
    for old_key, new_key in field_mapping.items():
        if old_key in result:
            result[new_key] = result[old_key]

    return result


def scanners_to_list(scanners: list[Any]) -> list[dict[str, Any]]:
    """
    將 scanner 列表轉換為字典列表

    Args:
        scanners: Shioaji scanner 物件列表

    Returns:
        字典列表
    """
    logger.debug(f"收到 {len(scanners)} 個 scanner 物件")
    if scanners:
        logger.debug(f"第一個 scanner 物件類型: {type(scanners[0])}")
    result = [scanner_to_dict(scanner) for scanner in scanners]
    logger.debug(f"轉換完成，共 {len(result)} 筆資料")
    return result


def normalize_scanner_fields(
    results: list[dict[str, Any]], scanner_type: str
) -> list[dict[str, Any]]:
    """
    依掃描器類型補齊前端與快取使用的標準欄位。
    """
    for item in results:
        if (
            scanner_type == "ChangePercentRank"
            and item.get("change_percent") is None
            and item.get("rank_value") is not None
        ):
            item["change_percent"] = item["rank_value"]

    return results


def execute_scan(
    scanner_type: str,
    date: str,
    count: int = 100,
    ascending: bool = True,
    simulation: bool = True,
    config_file: str = "config.txt",
) -> tuple[list[dict[str, Any]], float, dict[str, Any] | None]:
    """
    執行股票掃描

    Args:
        scanner_type: 掃描器類型
        date: 查詢日期
        count: 查詢數量
        ascending: 是否升序
        simulation: 是否模擬模式
        config_file: 配置檔案路徑

    Returns:
        (掃描結果列表, 執行時間, 流量使用資訊)

    Raises:
        Exception: 執行失敗時
    """
    start_time = time.time()

    # 讀取配置
    config = load_config(config_file)

    # 初始化客戶端
    client = ShioajiClient(config, simulation=simulation)

    try:
        # 登入
        client.login()

        # 啟用憑證
        client.activate_ca()

        # 查詢流量使用狀況
        usage_info = client.get_usage()
        usage_data = None

        if usage_info:
            bytes_used = usage_info.bytes
            limit_bytes = usage_info.limit_bytes
            remaining_bytes = limit_bytes - bytes_used
            remaining_pct = (
                (remaining_bytes / limit_bytes * 100) if limit_bytes > 0 else 0
            )
            is_over_limit = bytes_used >= limit_bytes

            usage_data = {
                "bytes_used": bytes_used,
                "limit_bytes": limit_bytes,
                "remaining_bytes": remaining_bytes,
                "remaining_percent": round(remaining_pct, 2),
                "is_over_limit": is_over_limit,
                "warning": (
                    f"警告：流量已達上限！已使用 {bytes_used} bytes，"
                    f"上限為 {limit_bytes} bytes"
                    if is_over_limit
                    else None
                ),
            }

            if is_over_limit:
                logger.warning(f"API 流量已達上限：{bytes_used}/{limit_bytes} bytes")
            else:
                logger.info(
                    f"流量使用狀況：{bytes_used}/{limit_bytes} bytes "
                    f"({remaining_pct:.2f}% 剩餘)"
                )

        # 執行掃描
        # 注意：Shioaji API 的 ascending 參數語義與預期相反
        # ascending=True 在 Shioaji 中代表從大到小（降序）
        # ascending=False 在 Shioaji 中代表從小到大（升序）
        # 因此這裡需要反轉參數
        shioaji_ascending = not ascending
        logger.info(
            f"呼叫 Shioaji API scanners: "
            f"type={scanner_type}, date={date}, count={count}, "
            f"user_ascending={ascending}, shioaji_ascending={shioaji_ascending}"
        )
        scanners = client.scanners(
            scanner_type=scanner_type,
            date=date,
            count=count,
            ascending=shioaji_ascending,
            timeout=30000,
        )

        num_scanners = len(scanners) if scanners else 0
        logger.info(f"Shioaji API 回傳 {num_scanners} 個 scanner 物件")
        if scanners:
            logger.debug(f"第一筆 scanner 原始物件: {scanners[0]}")

        # 轉換為字典列表
        results = scanners_to_list(scanners)
        results = normalize_scanner_fields(results, scanner_type)

        if results:
            logger.info(f"轉換後第一筆資料預覽: {results[0]}")
        else:
            logger.warning("警告：轉換後沒有資料！")

        execution_time = time.time() - start_time
        logger.info(f"掃描完成，共 {len(results)} 筆資料，耗時 {execution_time:.2f} 秒")

        return results, execution_time, usage_data

    finally:
        # 確保登出
        client.logout()


def generate_csv(data: list[dict[str, Any]]) -> str:
    """
    產生 CSV 內容

    Args:
        data: 資料列表

    Returns:
        CSV 字串（UTF-8-BOM 編碼）
    """
    if not data:
        return ""

    output = StringIO()

    # 取得所有欄位名稱
    fieldnames = list(data[0].keys())

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for row in data:
        writer.writerow(row)

    # 加上 BOM 以便 Excel 正確識別 UTF-8
    csv_content = "\ufeff" + output.getvalue()
    output.close()

    return csv_content


def save_csv(data: list[dict[str, Any]], filename: str = "output.csv") -> None:
    """
    儲存資料為 CSV 檔案

    Args:
        data: 資料列表
        filename: 檔案名稱
    """
    if not data:
        logger.warning("沒有資料可儲存")
        return

    csv_content = generate_csv(data)

    with open(filename, "w", encoding="utf-8-sig") as f:
        f.write(csv_content.lstrip("\ufeff"))  # 移除字串開頭的 BOM，因為檔案編碼已處理

    logger.info(f"已將 {len(data)} 筆資料儲存至 {filename}")
