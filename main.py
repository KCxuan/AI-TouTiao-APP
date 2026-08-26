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


app = FastAPI()

# 注册全局异常处理
register_exception_handlers(app)

# 设置允许跨域的源列表
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # 允许访问源
    allow_credentials=True, #允许携带cookie
    allow_methods=["*"], #允许的请求方法
    allow_headers=["*"], #允许的请求头
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


