from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app import __version__
from app.api.routes import scanner

app = FastAPI(
    title="Stock Scanner API",
    description="永豐金證券股票掃描 API",
    version=__version__,
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # 前端開發伺服器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 註冊路由
app.include_router(scanner.router, prefix="/api", tags=["scanner"])


@app.get("/")
async def root():
    """
    根路徑
    """
    return {"message": "Stock Scanner API is running"}


@app.get("/api/version")
async def get_version():
    """
    取得 API 版本資訊
    """
    return {"version": __version__}
