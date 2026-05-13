# Stock API - 永豐金證券股票掃描系統

> **目前版本**: v1.1.0

這是一個使用永豐金證券 Shioaji API 進行股票市場掃描的全端專案，包含 Vue3 網頁前端和 FastAPI 後端。

## 專案功能

- 🎯 網頁介面操作股票掃描器
- 📊 即時顯示股票漲跌幅、成交量等資訊
- 📥 匯出掃描結果為 CSV 檔案
- � **資料庫快取** - 優先從本地資料庫讀取，大幅提升速度
- 📈 **每日股票資料** - 儲存歷史成交金額排名前 200 檔股票
- 📜 **掃描歷史追蹤** - 記錄所有 API 呼叫，便於除錯
- �🔒 本地開發環境，無需身份驗證
- ⚡ 前後端分離架構

## 技術架構

### Frontend (前端)

- **框架**: Vue3 + TypeScript + Vite
- **UI 元件**: Element Plus
- **狀態管理**: Pinia
- **HTTP 客戶端**: Axios
- **開發工具**: ESLint 9 (Flat Config) + Prettier

### Backend (後端)

- **框架**: FastAPI + Python 3.13+
- **API 客戶端**: Shioaji (永豐金證券)
- **資料庫**: SQLite + SQLAlchemy 2.0 (async)
- **資料驗證**: Pydantic
- **開發工具**: Ruff + Mypy + Pytest

## 目錄結構

```
stock-api/
├── frontend/                # Vue3 前端
│   ├── src/
│   │   ├── api/            # API clients
│   │   ├── components/     # Vue 元件
│   │   ├── views/          # 頁面
│   │   ├── stores/         # Pinia stores
│   │   └── main.ts
│   ├── eslint.config.js    # ESLint 9 flat config
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── package.json
├── backend/                # Python 後端
│   ├── app/
│   │   ├── main.py         # FastAPI 應用
│   │   ├── models.py       # Pydantic 模型
│   │   └── api/routes/     # API 路由
│   ├── sj-trading/         # Python 套件
│   │   └── src/sj_trading/
│   │       ├── config.py   # 配置讀取
│   │       ├── scanner.py  # 掃描邏輯
│   │       └── api_client.py # Shioaji wrapper
│   ├── config.txt          # 配置檔（不提交）
│   ├── config.txt.example  # 配置範本
│   └── requirements.txt
├── README.md
└── .gitignore
```

## 環境需求

### Frontend

- Node.js >= 18
- npm >= 9

### Backend

- Python >= 3.13
- 永豐金證券帳戶和 API 金鑰
- 憑證檔案 (Sinopac.pfx)

## 安裝與啟動

### 1. 後端設定

```bash
# 進入後端目錄
cd backend

# 建立配置檔案（複製範本）
cp config.txt.example config.txt

# 編輯 config.txt，填入你的 API 資訊
# API_KEY=your_api_key
# SECRET_KEY=your_secret_key
# CA_PATH=path/to/Sinopac.pfx
# CA_PASSWD=your_ca_password

# 安裝 Python 依賴
pip install -r requirements.txt

# 或使用 uv（推薦）
uv pip install -r requirements.txt
```

### 2. 前端設定

```bash
# 進入前端目錄
cd frontend

# 安裝 Node.js 依賴
npm install
```

### 3. 啟動應用

#### 方法一：使用兩個終端機（推薦）

**終端機 1 - 啟動後端：**

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

後端將運行在 `http://localhost:8000`

**終端機 2 - 啟動前端：**

```bash
cd frontend
npm run dev
```

前端將運行在 `http://localhost:5173`

#### 方法二：使用 PowerShell 同時啟動（Windows）

在專案根目錄執行以下命令，將同時開啟兩個新視窗分別執行前後端：

```powershell
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; uvicorn app.main:app --reload"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"
```

**提示**：要停止服務，在各個終端機視窗按 `Ctrl+C`

### 4. 使用應用

1. 開啟瀏覽器訪問 `http://localhost:5173`
2. 在介面上選擇：
   - 掃描器類型（漲跌幅排名 / 成交量排名 / 金額排名）
   - 查詢日期
   - 查詢數量（1-200）
   - 排序方式（升序/降序）
3. 點擊「開始掃描」按鈕
4. 等待 30-60 秒，結果將顯示在表格中
5. 可點擊「匯出 CSV」下載結果

### 5. 每日使用（更新資料庫）

當您重新開啟專案時，可以選擇以下方式之一來更新資料庫：

#### 方式一：透過前端自動更新 ⭐ 推薦

**最簡單的方式！只要透過前端查詢新日期的資料，系統會自動更新資料庫。**

1. 啟動後端和前端（如上述步驟 3）
2. 開啟瀏覽器 `http://localhost:5173`
3. 選擇「**金額排名 (AmountRank)**」類型
4. 選擇今天或想要的日期
5. 點擊「開始掃描」
6. 系統會自動將結果儲存到資料庫 ✅

**優點**：無需執行任何額外指令，透過正常使用即可更新資料庫

#### 方式二：批次匯入多天資料

如果您想一次匯入最近多天的資料（例如停了幾天沒開專案）：

```bash
cd backend
python import_historical_data.py
```

此腳本會：

- 自動計算最近 10 個交易日（排除週末）
- 逐日抓取成交金額排名 top 200 股票
- 儲存到資料庫
- **注意**：每天約等待 10 秒，10 天共需 1-2 分鐘

#### 方式三：匯入單一特定日期

如果只想補某一天的資料，可透過前端查詢該日期，或執行：

```bash
cd backend
python test_single_import.py  # 需先修改腳本中的 test_date
```

#### 💡 使用建議

| 情境 | 建議做法 | 時間 |
|------|---------|------|
| 每天正常使用 | 透過前端查詢即可 | 首次 30-60秒，之後 < 0.1秒 |
| 隔了 2-3 天 | 透過前端查詢新日期 | 每個新日期首次需 30-60秒 |
| 隔了 1-2 週 | 執行 `import_historical_data.py` | 約 1-2 分鐘 |
| 只缺某一天 | 透過前端查詢該日期 | 30-60秒 |

**核心概念**：資料庫是「自動快取」，您只要正常使用前端查詢，系統就會自動管理資料庫！

## API 文件

FastAPI 自動產生的 API 文件：

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🗄️ 資料庫功能

### 自動快取機制

系統使用 SQLite 資料庫來快取股票掃描結果，大幅提升查詢速度：

- **`AmountRank` (成交金額排名)**: 優先從資料庫讀取，若無資料則呼叫 API 並自動儲存
- **執行速度**: 資料庫查詢 < 0.1 秒，API 查詢約 30-60 秒
- **自動儲存**: API 查詢結果會自動存入資料庫，下次查詢時直接讀取

### 資料表結構

#### `stock_daily_data` - 每日股票資料

儲存每日成交金額排名前 200 檔股票的完整資訊：

- 交易日期、股票代碼、名稱、排名
- 價格資訊（開、高、低、收、均價）
- 成交量、成交金額
- 漲跌價差、漲跌幅
- 買賣委託資訊

#### `scan_history` - API 呼叫歷史

追蹤所有 `/api/scan` 的呼叫記錄：

- 掃描參數（類型、日期、數量等）
- 執行結果（成功/失敗、執行時間）
- 原始資料與處理後資料（JSON 格式）
- 自動保留最近 10 筆記錄

### 資料匯入工具

#### 匯入歷史資料

```bash
cd backend
python import_historical_data.py
```

此腳本會：

- 自動計算最近 10 個交易日（排除週末）
- 逐日呼叫 Shioaji API 抓取成交金額排名 top 200
- 儲存到 `stock_daily_data` 表
- 顯示詳細進度和結果

#### 測試單日匯入

```bash
cd backend
python test_single_import.py  # 測試匯入單一日期
python test_setup.py           # 驗證資料庫設置
python test_db.py              # 測試資料庫功能
```

### 查詢範例

**查詢特定日期資料**：

```bash
curl http://localhost:8000/api/daily/2026-01-15
```

**查看可用日期列表**：

```bash
curl http://localhost:8000/api/daily/dates/list
```

**查看掃描歷史**：

```bash
curl http://localhost:8000/api/scan/history?limit=5
```

### API 端點

#### 股票掃描

**POST /api/scan** - 執行股票掃描（優先從資料庫讀取）

- `AmountRank` 類型會優先查詢資料庫
- 若資料庫無資料，則呼叫 Shioaji API 並自動儲存
- 其他類型直接呼叫 API

請求體：

```json
{
  "scanner_type": "AmountRank",
  "date": "2026-01-15",
  "count": 100,
  "ascending": false,
  "simulation": true
}
```

回應：

```json
{
  "status": "success",
  "data": [...],
  "total_count": 100,
  "execution_time": 0.0,
  "message": "從資料庫讀取（共 200 筆）"
}
```

**POST /api/export** - 匯出 CSV

#### 每日股票資料

**GET /api/daily/{date}** - 查詢指定日期的股票資料

```bash
curl http://localhost:8000/api/daily/2026-01-15
```

**GET /api/daily/dates/list** - 列出資料庫中可用的日期

```bash
curl http://localhost:8000/api/daily/dates/list
```

#### 掃描歷史

**GET /api/scan/history** - 查詢掃描歷史記錄（最近 10 筆）

**GET /api/scan/latest** - 取得最新一筆掃描記錄

## 開發工具

### Frontend

```bash
# Linting
npm run lint

# 自動修復
npm run lint:fix

# 格式化程式碼
npm run format
```

### Backend

```bash
cd backend

# Linting
ruff check .

# 自動修復
ruff check --fix .

# 格式化
ruff format .

# 型別檢查
mypy .

# 執行測試
pytest
```

## 版本管理

專案使用語義化版本 (Semantic Versioning)，版本號格式為 `MAJOR.MINOR.PATCH`。

### 版本資訊

- **目前版本**: `1.2.0`
- 版本定義位置：
  - [version.json](version.json) - 單一真實來源
  - [frontend/package.json](frontend/package.json) - 前端應用版本
  - [backend/sj-trading/pyproject.toml](backend/sj-trading/pyproject.toml) - Python 套件版本
  - [backend/app/\_\_init\_\_.py](backend/app/__init__.py) - FastAPI 應用版本

### 查看版本

**前端顯示**：開啟應用後，在股票掃描器頁面右上角可看到版本號

**後端 API**：訪問 `http://localhost:8000/api/version`

```bash
curl http://localhost:8000/api/version
# 回傳: {"version": "1.0.0"}
```

### 版本遞增

使用 [bump.py](bump.py) 腳本統一更新所有檔案的版本號，並自動建立 Git commit 和 tag。

**遞增 PATCH 版本**（預設）：`1.0.0 → 1.0.1`

```bash
python bump.py
# 或
python bump.py --patch
```

**遞增 MINOR 版本**：`1.0.0 → 1.2.0`

```bash
python bump.py --minor
```

**遞增 MAJOR 版本**：`1.0.0 → 2.0.0`

```bash
python bump.py --major
```

### 自動化檢查

**Pre-commit Hook**：已配置自動檢查版本號一致性

在提交程式碼時，pre-commit hook 會自動驗證四個檔案的版本號是否一致。如果不一致，提交將被中止。

**手動檢查版本一致性**：

```bash
python scripts/check_version.py
```

### 版本管理工作流程

1. **開發新功能或修復 Bug**
2. **提交程式碼**：`git add .` 和 `git commit`（正常流程）
3. **準備發布時執行版本遞增**：

   ```bash
   python bump.py          # 遞增 PATCH（Bug 修復）
   # 或
   python bump.py --minor  # 遞增 MINOR（新功能）
   # 或
   python bump.py --major  # 遞增 MAJOR（重大變更）
   ```

4. **推送到遠端**：

   ```bash
   git push origin main
   git push origin --tags  # 推送 Git tags
   ```

### 版本號規則

- **MAJOR** (主版本號)：重大變更，可能包含不向下相容的 API 修改
- **MINOR** (次版本號)：新增功能，向下相容
- **PATCH** (修訂版本號)：Bug 修復，向下相容

### 更新日誌

#### v1.1.0 (2026-01-18)

**新增功能**：

- ✨ **資料庫快取系統** - 使用 SQLite + SQLAlchemy 2.0 (async)
  - `AmountRank` 掃描結果優先從資料庫讀取
  - 查詢速度從 30-60 秒降至 < 0.1 秒
  - API 結果自動儲存到資料庫
  
- 📊 **每日股票資料表** (`stock_daily_data`)
  - 儲存每日成交金額排名 top 200 股票
  - 支援歷史資料匯入與查詢
  - 自動去重（相同股票代碼保留最新時間戳）
  
- 📝 **掃描歷史追蹤** (`scan_history`)
  - 記錄所有 API 呼叫（成功/失敗）
  - 儲存原始與處理後資料（JSON 格式）
  - 自動保留最近 10 筆記錄
  
- 🔧 **新增 API 端點**：
  - `GET /api/daily/{date}` - 查詢指定日期股票資料
  - `GET /api/daily/dates/list` - 列出可用日期
  - `GET /api/scan/history` - 查詢掃描歷史
  - `GET /api/scan/latest` - 取得最新掃描記錄
  
- 🛠️ **資料匯入工具**：
  - `import_historical_data.py` - 批次匯入歷史資料
  - `test_setup.py` - 驗證資料庫設置
  - `test_db.py` - 測試資料庫功能
  - `test_single_import.py` - 測試單日匯入

**改進**：

- 🔧 完善 Ruff 配置：
  - 新增 `backend/ruff.toml`
  - 自動移除 trailing whitespace
  - 忽略中文相關 linting 警告

**依賴更新**：

- 新增 `sqlalchemy==2.0.35`
- 新增 `aiosqlite==0.20.0`
- 新增 `alembic==1.13.3`
- 新增 `greenlet==3.1.1`

#### v1.0.0 (2026-01-17)

**初始版本**：

- 🎯 Vue3 + TypeScript 前端介面
- ⚡ FastAPI 後端 API
- 📊 Shioaji API 整合
- 📥 CSV 匯出功能
- 🔒 本地開發環境

## 配置說明

### 後端配置檔 (backend/config.txt)

```ini
# 永豐金證券 API 金鑰
API_KEY=your_api_key_here
SECRET_KEY=your_secret_key_here

# CA 憑證設定
CA_PATH=C:/path/to/Sinopac.pfx
CA_PASSWD=your_certificate_password
```

⚠️ **重要**：config.txt 已加入 .gitignore，不會被提交到版本控制系統。

## 注意事項

⚠️ **安全性提醒**：

- 請勿將 API 金鑰、密鑰和憑證密碼上傳到公開的版本控制系統
- config.txt 和 *.pfx 檔案已加入 .gitignore
- 使用 config.txt.example 作為配置範本

📝 **開發環境**：

- 本專案設計為本地開發使用
- 無需身份驗證機制
- **固定使用模擬模式**（simulation=true），無法切換為正式環境

⚠️ **API 限制說明**：

- 本專案使用的 API key 為個人申請的，是否能使用正式交易環境端看使用者申請的權限
- `simulation` 參數目前固定為 `true`，無法使用正式交易環境

## 故障排除

### 後端啟動失敗，提示找不到 config.txt

**解決方案**：確認已建立 `backend/config.txt` 並填入正確的 API 資訊。

```bash
cd backend
cp config.txt.example config.txt
# 然後編輯 config.txt 填入你的 API 金鑰
```

### 前端無法連接後端

**可能原因**：

- 後端未啟動或未在 port 8000 運行
- Vite proxy 配置錯誤

**解決方案**：

- 確認後端已啟動在 port 8000
- 檢查終端機是否有錯誤訊息
- 檢查 [vite.config.ts](frontend/vite.config.ts) 的 proxy 設定

### 後端登入失敗

**可能原因**：

- API 金鑰或密鑰錯誤
- 網路連線問題

**解決方案**：

- 確認 [config.txt](backend/config.txt) 的 API_KEY 和 SECRET_KEY 正確
- 確認永豐金證券帳戶狀態正常
- 檢查網路連線

### 憑證啟用失敗

**可能原因**：

- CA 憑證路徑錯誤
- 憑證密碼錯誤
- 憑證檔案損壞

**解決方案**：

- 檢查 CA_PATH 路徑是否正確（使用絕對路徑）
- 確認憑證密碼 CA_PASSWD 正確
- 重新下載憑證檔案

### 掃描逾時或回應緩慢

**可能原因**：

- Shioaji API 回應較慢
- 網路連線不穩定
- 查詢數量過多

**解決方案**：

- 檢查網路連線
- 減少 count 數量再試（例如從 200 降到 50）
- 等待一段時間後重試

## 相關資源

- [Shioaji 官方文件](https://sinotrade.github.io/)
- [FastAPI 文件](https://fastapi.tiangolo.com/)
- [Vue3 文件](https://vuejs.org/)
- [Element Plus 文件](https://element-plus.org/)

## 開發者

- ltchou (<leochoulfc@gmail.com>)

## 授權

MIT License - 請遵守永豐金證券 API 使用條款。
