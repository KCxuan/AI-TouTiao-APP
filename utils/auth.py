# 整合 根据token获取用户， 返回用户信息
from fastapi import Header, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
from config import db_config
from crud import users

async def get_current_user(
    authorization: str = Header(..., alias="Authorization"),
    db: AsyncSession = Depends(db_config.get_database)
):
    # 获取token，去掉前缀"Bearer "，并返回用户信息
    token = authorization.split(" ")[1]
    user = await users.get_user_by_token(token, db)
    if not user: 
        raise HTTPException(status_code=401, detail="无效的token")
    return user
