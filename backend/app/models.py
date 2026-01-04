from pydantic import BaseModel, Field
from typing import Any


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
