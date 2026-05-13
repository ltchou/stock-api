"""SQLAlchemy 資料庫模型"""

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from app.database import Base


class ScanHistory(Base):
    """
    掃描歷史記錄表
    """

    __tablename__ = "scan_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    scanner_type = Column(String(100), nullable=False)
    scan_date = Column(String(20), nullable=True)
    count = Column(Integer, nullable=False)
    ascending = Column(Boolean, nullable=False)
    simulation = Column(Boolean, nullable=False)

    # 執行結果
    success = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)
    result_count = Column(Integer, nullable=False, default=0)
    execution_time = Column(Integer, nullable=True)  # 執行時間（秒）

    # 原始資料（JSON）
    raw_response = Column(JSON, nullable=True)  # Shioaji API 回傳的原始資料
    processed_results = Column(JSON, nullable=True)  # 處理後的結果

    # 流量資訊（JSON）
    usage_data = Column(JSON, nullable=True)

    def __repr__(self):
        return (
            f"<ScanHistory(id={self.id}, timestamp={self.timestamp}, "
            f"scanner_type={self.scanner_type}, success={self.success}, "
            f"result_count={self.result_count})>"
        )


class StockDailyData(Base):
    """
    每日股票資料表（儲存每日股票掃描結果，支援多種掃描器類型）
    """

    __tablename__ = "stock_daily_data"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    date = Column(String(20), nullable=False, index=True)  # 交易日期 YYYY-MM-DD
    scanner_type = Column(String(50), nullable=False, index=True)  # 掃描器類型
    code = Column(String(20), nullable=False, index=True)  # 股票代碼
    name = Column(String(100), nullable=True)  # 股票名稱
    rank = Column(Integer, nullable=False)  # 排名（1-200）

    # 價格資訊
    open = Column(Float, nullable=True)  # 開盤價
    high = Column(Float, nullable=True)  # 最高價
    low = Column(Float, nullable=True)  # 最低價
    close = Column(Float, nullable=True)  # 收盤價

    # 交易資訊
    volume = Column(Integer, nullable=True)  # 成交量
    total_volume = Column(Integer, nullable=True)  # 總成交量
    amount = Column(Float, nullable=True)  # 成交金額
    total_amount = Column(Float, nullable=True)  # 總成交金額

    # 技術指標
    change_price = Column(Float, nullable=True)  # 漲跌價差
    change_percent = Column(Float, nullable=True)  # 漲跌幅
    average_price = Column(Float, nullable=True)  # 均價

    # 買賣資訊
    buy_price = Column(Float, nullable=True)  # 委買價
    buy_volume = Column(Integer, nullable=True)  # 委買量
    sell_price = Column(Float, nullable=True)  # 委賣價
    sell_volume = Column(Integer, nullable=True)  # 委賣量

    # 時間戳記
    ts = Column(Integer, nullable=True)  # timestamp
    created_at = Column(
        DateTime, default=datetime.utcnow, nullable=False
    )  # 資料建立時間

    # 確保同一天同一股票同一掃描器類型只有一筆記錄
    __table_args__ = (
        UniqueConstraint("date", "scanner_type", "code", name="uq_date_scanner_code"),
    )

    def __repr__(self):
        return (
            f"<StockDailyData(date={self.date}, scanner_type={self.scanner_type}, "
            f"code={self.code}, name={self.name}, rank={self.rank})>"
        )
