"""工具函式"""

from datetime import datetime, timedelta


def get_last_n_trading_days(n: int = 10) -> list[str]:
    """
    取得最近 N 個交易日（排除週末）

    Args:
        n: 天數（預設 10）

    Returns:
        交易日期列表，格式 YYYY-MM-DD，降序排列（最新日期在前）
    """
    days: list[str] = []
    current = datetime.now()

    while len(days) < n:
        # 排除週末：weekday() 回傳 0-6，其中 5=週六, 6=週日
        if current.weekday() < 5:  # 週一=0 ~ 週五=4
            days.append(current.strftime("%Y-%m-%d"))
        current -= timedelta(days=1)

    return days


def is_trading_day(date_str: str) -> bool:
    """
    判斷是否為交易日（排除週末）

    Args:
        date_str: 日期字串，格式 YYYY-MM-DD

    Returns:
        是否為交易日
    """
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    return date_obj.weekday() < 5
