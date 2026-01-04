"""股票掃描器模組"""

import csv
import logging
import time
from io import StringIO
from typing import Any

from sj_trading.api_client import ShioajiClient
from sj_trading.config import load_config

logger = logging.getLogger(__name__)


def scanner_to_dict(scanner: Any) -> dict[str, Any]:
    """
    將 scanner 物件轉換為字典

    Args:
        scanner: Shioaji scanner 物件

    Returns:
        包含 scanner 屬性的字典
    """
    return scanner.__dict__.copy()


def scanners_to_list(scanners: list[Any]) -> list[dict[str, Any]]:
    """
    將 scanner 列表轉換為字典列表

    Args:
        scanners: Shioaji scanner 物件列表

    Returns:
        字典列表
    """
    return [scanner_to_dict(scanner) for scanner in scanners]


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
        scanners = client.scanners(
            scanner_type=scanner_type,
            date=date,
            count=count,
            ascending=ascending,
            timeout=30000,
        )

        # 轉換為字典列表
        results = scanners_to_list(scanners)

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
