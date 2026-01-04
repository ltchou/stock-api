# Stock API - 永豐金證券股票掃描系統

> **目前版本**: v1.0.0

這是一個使用永豐金證券 Shioaji API 進行股票市場掃描的全端專案，包含 Vue3 網頁前端和 FastAPI 後端。

## 專案功能

- 🎯 網頁介面操作股票掃描器
- 📊 即時顯示股票漲跌幅、成交量等資訊
- 📥 匯出掃描結果為 CSV 檔案
- 🔒 本地開發環境，無需身份驗證
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

## API 文件

FastAPI 自動產生的 API 文件：

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### API 端點

**POST /api/scan** - 執行股票掃描

請求體：

```json
{
  "scanner_type": "ChangePercentRank",
  "date": "2026-01-04",
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
  "execution_time": 45.2
}
```

**POST /api/export** - 匯出 CSV

請求體：同上

回應：CSV 檔案下載

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

- **目前版本**: `1.0.0`
- 版本定義位置：
  - [version.json](version.json) - 單一真實來源
  - [frontend/package.json](frontend/package.json) - 前端應用版本
  - [backend/sj-trading/pyproject.toml](backend/sj-trading/pyproject.toml) - Python 套件版本
  - [backend/app/__init__.py](backend/app/__init__.py) - FastAPI 應用版本

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

**遞增 MINOR 版本**：`1.0.0 → 1.1.0`

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
