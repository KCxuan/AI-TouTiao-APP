import os

from fastapi import FastAPI, Path, Query, HTTPException, Request, Depends
from pydantic import BaseModel, Field
from fastapi.responses import HTMLResponse, FileResponse
import time
from routers import news
from routers import users
from routers import favorite
from routers import history
from routers import research
from routers import chat
from routers import auto
from utils.exception_handlers import register_exception_handlers
from fastapi.middleware.cors import CORSMiddleware


DEFAULT_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]


def cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "").strip()
    if not raw:
        return DEFAULT_CORS_ORIGINS
    return [item.strip() for item in raw.split(",") if item.strip()]


app = FastAPI()

# 注册全局异常处理
register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}

# 挂载路由
app.include_router(news.router)
app.include_router(users.router)
app.include_router(favorite.router)
app.include_router(history.router)
app.include_router(research.router)
app.include_router(chat.router)
app.include_router(auto.router)


