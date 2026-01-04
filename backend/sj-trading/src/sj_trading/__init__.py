"""sj_trading 股票交易套件"""

from sj_trading.api_client import ShioajiClient
from sj_trading.config import load_config
from sj_trading.scanner import execute_scan, generate_csv, save_csv

__all__ = [
    "ShioajiClient",
    "load_config",
    "execute_scan",
    "generate_csv",
    "save_csv",
]


def main() -> None:
    """主程式進入點"""
    print("Hello from sj-trading!")
