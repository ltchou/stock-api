import shioaji as sj
import os
import csv

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
accounts = api.login(config.get("API_KEY"), config.get("SECRET_KEY"))
api.activate_ca(ca_path=config.get("CA_PATH"), ca_passwd=config.get("CA_PASSWD"))
print(accounts)

scanners = api.scanners(
    scanner_type="ChangePercentRank",
    ascending=True,
    date="2026-01-02",
    count=100,  # 0 <= count <= 200
    timeout=30000,
    cb=None,
)

# 直接將 scanner 物件轉換為 CSV
if scanners:
    # 取得第一個 scanner 的所有屬性作為欄位
    first_scanner = scanners[0]
    fieldnames = list(first_scanner.__dict__.keys())

    with open("output.csv", "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for scanner in scanners:
            writer.writerow(scanner.__dict__)

    print(f"已將 {len(scanners)} 筆資料輸出至 output.csv")
else:
    print("沒有掃描結果")
