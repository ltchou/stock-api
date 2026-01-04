"""配置檔案讀取模組"""

from pathlib import Path


def load_config(config_file: str = "config.txt") -> dict[str, str]:
    """
    讀取配置檔案

    Args:
        config_file: 配置檔案路徑

    Returns:
        配置字典

    Raises:
        FileNotFoundError: 當配置檔案不存在時
    """
    config: dict[str, str] = {}
    config_path = Path(config_file)

    if not config_path.exists():
        raise FileNotFoundError(f"配置檔案不存在: {config_file}")

    with config_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()

    return config
