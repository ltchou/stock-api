from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ScanRequest(BaseModel):
    """
    股票掃描請求模型

    Attributes:
        scanner_type: 掃描器類型（例如：ChangePercentRank）
        date: 查詢日期（格式：YYYY-MM-DD）
        count: 查詢數量（1-200）
        ascending: 是否升序排列
        simulation: 是否使用模擬模式
    """

    scanner_type: str = Field(..., description="掃描器類型")
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="日期")
    count: int = Field(100, ge=1, le=200, description="查詢數量")
    ascending: bool = Field(False, description="是否升序")
    simulation: bool = Field(True, description="模擬模式")


class StockData(BaseModel):
    """
    股票資料模型

    注意：Shioaji scanner 物件的欄位可能因掃描器類型而異
    因此使用靈活的模型定義，接受任意欄位
    """

    class Config:
        extra = "allow"  # 允許額外欄位

    # 以下欄位為可選，根據 Shioaji API 實際返回而定
    code: str | None = None
    name: str | None = None
    date: str | None = None
    open: float | None = None
    close: float | None = None
    high: float | None = None
    low: float | None = None
    volume: int | None = None
    change_percent: float | None = None
    change_price: float | None = None
    rank_value: float | None = None
    ts: int | None = None

    def __init__(self, **data: Any):
        """允許接受任意欄位"""
        super().__init__(**data)


class ScanResponse(BaseModel):
    """
    掃描回應模型
    """

    status: str = "success"
    data: list[StockData]
    total_count: int
    execution_time: float
    message: str | None = None  # 額外訊息（例如：從資料庫讀取）


class ScanHistoryItem(BaseModel):
    """
    掃描歷史記錄項目
    """

    id: int
    timestamp: datetime
    scanner_type: str
    scan_date: str | None
    count: int
    ascending: bool
    simulation: bool
    success: bool
    error_message: str | None
    result_count: int
    execution_time: int | None
    raw_response: list[dict[str, Any]] | None
    processed_results: list[dict[str, Any]] | None
    usage_data: dict[str, Any] | None

    class Config:
        from_attributes = True


class ScanHistoryResponse(BaseModel):
    """
    掃描歷史查詢回應
    """

    status: str = "success"
    data: list[ScanHistoryItem]
    total_count: int


class DailyStockItem(BaseModel):
    """
    每日股票資料項目
    """

    id: int
    date: str
    code: str
    name: str | None
    rank: int
    open: float | None
    high: float | None
    low: float | None
    close: float | None
    volume: int | None
    total_volume: int | None
    amount: float | None
    total_amount: float | None
    change_price: float | None
    change_percent: float | None
    average_price: float | None
    buy_price: float | None
    buy_volume: int | None
    sell_price: float | None
    sell_volume: int | None
    ts: int | None
    created_at: datetime

    class Config:
        from_attributes = True


class DailyStockResponse(BaseModel):
    """
    每日股票資料回應
    """

    status: str = "success"
    date: str
    data: list[DailyStockItem]
    total_count: int


class AvailableDatesResponse(BaseModel):
    """
    可用日期列表回應
    """

    status: str = "success"
    dates: list[str]
    total_count: int
