# SJ Trading - 永豐金證券 API 股票掃描工具

這是一個使用永豐金證券 Shioaji API 來獲取股票市場掃描資料的 Python 專案。

## 專案功能

- 使用永豐金證券 API 進行模擬交易登入
- 啟用憑證驗證 (CA)
- 掃描股票市場，取得漲跌幅排名資料
- 將掃描結果輸出到文字檔案

## 目錄結構

```markdown
stock-api/
├── apikey.txt              # API 金鑰和密鑰儲存檔案
├── index.py                # 主要執行程式
├── output.txt              # 股票掃描結果輸出檔案
└── sj-trading/             # Python 套件目錄
    ├── pyproject.toml      # 專案配置和依賴項
    ├── README.md           # 專案說明文件
    └── src/
        └── sj_trading/
            └── __init__.py
```

## 環境需求

- Python >= 3.13
- 永豐金證券帳戶和 API 金鑰
- 憑證檔案 (Sinopac.pfx)

## 安裝方式

1. 安裝依賴套件：

```bash
pip install shioaji
```

或使用 uv（若已安裝）：

```bash
cd sj-trading
uv sync
```

## 設定說明

### 1. API 金鑰設定

在 `apikey.txt` 中儲存你的 API 金鑰：

```txt
API Key: YOUR_API_KEY
Secret Key: YOUR_SECRET_KEY
```

### 2. 憑證檔案

確保你的永豐金證券憑證檔案 (`Sinopac.pfx`) 放置在正確的路徑。

### 3. 程式碼設定

在 `index.py` 中需要設定的參數：

- **API 金鑰和密鑰**：從 apikey.txt 獲取
- **憑證路徑**：`ca_path` 指向你的 .pfx 檔案
- **憑證密碼**：`ca_passwd` 你的憑證密碼
- **掃描日期**：`date` 參數設定查詢日期
- **掃描數量**：`count` 參數（範圍 0-200）

## 執行方式

在專案根目錄執行：

```bash
python index.py
```

## 主要功能說明

### 股票掃描器 (Scanner)

程式使用 `api.scanners()` 方法來掃描股票市場：

- **scanner_type**: `'ChangePercentRank'` - 漲跌幅排名
- **ascending**: `True` - 升序排列
- **date**: 查詢特定日期的資料
- **count**: 返回的股票數量（最多 200）
- **timeout**: 請求超時時間（毫秒）

### 輸出格式

掃描結果會輸出到 `output.txt`，包含以下資訊：

- 股票代碼 (code)
- 股票名稱 (name)
- 日期 (date)
- 開盤價 (open)
- 最高價 (high)
- 最低價 (low)
- 收盤價 (close)
- 漲跌價格 (change_price)
- 成交量 (volume)
- 漲跌幅排名 (rank_value)
- 等更多交易資訊

## 注意事項

⚠️ **安全性提醒**：

- 請勿將 API 金鑰、密鑰和憑證密碼上傳到公開的版本控制系統
- 建議使用環境變數或加密方式儲存敏感資訊
- `apikey.txt` 和憑證檔案應加入 `.gitignore`

⚠️ **使用提醒**：

- 此程式使用模擬交易模式 (`simulation=True`)
- 確保網路連線穩定
- 注意 API 呼叫頻率限制

## 套件資訊

此專案使用 [Shioaji](https://sinotrade.github.io/) - 永豐金證券提供的 Python API。

## 開發者

- ltchou (<leochoulfc@gmail.com>)

## 授權

請遵守永豐金證券 API 使用條款。
