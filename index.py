import shioaji as sj
import os

# 讀取配置檔案
config = {}
config_file = "config.txt"

if os.path.exists(config_file):
    with open(config_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()
else:
    raise FileNotFoundError(f"請建立 {config_file} 並填入你的 API 資訊")

api = sj.Shioaji(simulation=True)
accounts = api.login(
    config.get("API_KEY"),
    config.get("SECRET_KEY")
)
api.activate_ca(
    ca_path=config.get("CA_PATH"),
    ca_passwd=config.get("CA_PASSWD")
)
print(accounts)

scanners = api.scanners(
    scanner_type='ChangePercentRank',
    ascending=True,
    date='2026-01-02',
    count=100,  # 0 <= count <= 200
    timeout=30000,
    cb=None
)

# process scanner to output.txt
with open("output.txt", "w") as f:
    for scanner in scanners:
        f.write(f"{scanner}\n")
