import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.routes import scanner
from app.database import close_db, init_db

logger = logging.getLogger(__name__)

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


@app.on_event("startup")
async def startup_event():
    """
    應用程式啟動時執行
    """
    logger.info("初始化資料庫...")
    await init_db()
    logger.info("資料庫初始化完成")


@app.on_event("shutdown")
async def shutdown_event():
    """
    應用程式關閉時執行
    """
    logger.info("關閉資料庫連線...")
    await close_db()
    logger.info("資料庫連線已關閉")


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
