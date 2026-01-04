"""Shioaji API 客戶端包裝類別"""

import logging
from typing import Any

import shioaji as sj

logger = logging.getLogger(__name__)


class ShioajiClient:
    """
    Shioaji API 客戶端包裝類別

    Attributes:
        api: Shioaji API 實例
        config: 配置字典
        is_logged_in: 是否已登入
    """

    def __init__(self, config: dict[str, str], simulation: bool = True):
        """
        初始化 Shioaji 客戶端

        Args:
            config: 配置字典，包含 API_KEY、SECRET_KEY、CA_PATH、CA_PASSWD
            simulation: 是否使用模擬模式
        """
        self.config = config
        self.simulation = simulation
        self.api = sj.Shioaji(simulation=simulation)
        self.is_logged_in = False

    def login(self) -> Any:
        """
        登入 Shioaji API

        Returns:
            帳戶資訊

        Raises:
            Exception: 登入失敗時
        """
        try:
            api_key = self.config.get("API_KEY")
            secret_key = self.config.get("SECRET_KEY")

            if not api_key or not secret_key:
                raise ValueError("API_KEY 或 SECRET_KEY 未設定")

            accounts = self.api.login(api_key, secret_key)
            logger.info("Shioaji 登入成功")
            self.is_logged_in = True
            return accounts
        except Exception as e:
            logger.error(f"Shioaji 登入失敗: {e}")
            raise

    def activate_ca(self) -> None:
        """
        啟用憑證

        Raises:
            Exception: 啟用失敗時
        """
        try:
            ca_path = self.config.get("CA_PATH")
            ca_passwd = self.config.get("CA_PASSWD")

            if not ca_path or not ca_passwd:
                raise ValueError("CA_PATH 或 CA_PASSWD 未設定")

            self.api.activate_ca(ca_path=ca_path, ca_passwd=ca_passwd)
            logger.info("憑證啟用成功")
        except Exception as e:
            logger.error(f"憑證啟用失敗: {e}")
            raise

    def get_usage(self) -> Any | None:
        """
        取得 API 流量使用狀況

        Returns:
            UsageStatus 物件，包含 bytes、limit_bytes 等屬性

        Raises:
            Exception: 查詢失敗時
        """
        try:
            usage_info = self.api.usage()
            logger.debug(f"流量使用狀況: {usage_info}")
            return usage_info
        except Exception as e:
            logger.error(f"查詢流量使用狀況失敗: {e}")
            return None

    def scanners(
        self,
        scanner_type: str,
        date: str,
        count: int = 100,
        ascending: bool = True,
        timeout: int = 30000,
    ) -> list[Any]:
        """
        執行股票掃描

        Args:
            scanner_type: 掃描器類型（例如：ChangePercentRank）
            date: 查詢日期（格式：YYYY-MM-DD）
            count: 查詢數量（0-200）
            ascending: 是否升序排列
            timeout: 逾時時間（毫秒）

        Returns:
            掃描結果列表

        Raises:
            Exception: 掃描失敗時
        """
        if not self.is_logged_in:
            raise RuntimeError("尚未登入，請先呼叫 login()")

        try:
            results = self.api.scanners(
                scanner_type=scanner_type,
                ascending=ascending,
                date=date,
                count=count,
                timeout=timeout,
                cb=None,
            )
            logger.info(f"掃描完成，共 {len(results) if results else 0} 筆結果")
            return results or []
        except Exception as e:
            logger.error(f"股票掃描失敗: {e}")
            raise

    def logout(self) -> None:
        """
        登出 Shioaji API
        """
        try:
            if self.is_logged_in:
                self.api.logout()
                self.is_logged_in = False
                logger.info("Shioaji 登出成功")
        except Exception as e:
            logger.warning(f"Shioaji 登出時發生錯誤: {e}")
