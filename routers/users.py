from fastapi import APIRouter, Depends, Query, HTTPException
from config import db_config
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.users import UserInfoResponse, UserRequest, UserAuthResponse, UserUpdateRequest, UserChangePasswordRequest
from crud.users import create_user, get_user_by_username, create_token, authenticate_user, update_user, change_password
from utils.response import success_response
from utils.auth import get_current_user
from models.users import User


router = APIRouter(prefix="/api/user", tags=["users"])

# 用户注册
@router.post("/register")
async def register(
    user_data: UserRequest,
    db: AsyncSession = Depends(db_config.get_database)
):
    # 验证用户是否存在-》创建用户-》生成token-》响应结果
    existing_user = await get_user_by_username(user_data.username, db)
    if existing_user:
        raise HTTPException(status_code=400, detail="用户已存在")
    
    user = await create_user(user_data, db)
    token = await create_token(user.id, db)

    """
    return {
        "code": 200,
        "message": "注册成功",
        "data": {
            "token": token,
            "userInfo": {
                "id": user.id,
                "username": user.username,
                "bio": user.bio,
                "avatar": user.avatar
            }
        }
    }"""
    response_data = UserAuthResponse(token=token, user_info=UserInfoResponse.model_validate(user))
    return success_response("注册成功", data=response_data)

# 用户登录
@router.post("/login")
async def login(
    user_data: UserRequest,
    db: AsyncSession = Depends(db_config.get_database)
):
    # 验证用户是否存在 -》 如果存在则验证密码 -》 生成token -》 响应结果
    # 验证用户是否存在 -》 如果不存在则返回提示 -》 先去注册用户
    user = await authenticate_user(user_data.username, user_data.password, db)
    if not user:
        raise HTTPException(status_code=400, detail="用户名或者密码错误")
    
    token = await create_token(user.id, db)
    response_data = UserAuthResponse(token=token, user_info=UserInfoResponse.model_validate(user))
    return success_response("登录成功", data=response_data)

# 获取用户的信息
# 查Token用户 -》 封装crud -》 功能整合成一个工具函数 -》 路由导入使用 依赖注入
@router.get("/info")
async def get_user_info(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(db_config.get_database)
):
    # 首先要确认是否登录token是否过期 -》验证用户是否存在 -》 获取用户信息 -》 响应结果
    if not user:
        raise HTTPException(status_code=401, detail="用户未登录")
    return success_response("获取信息成功", data=UserInfoResponse.model_validate(user))

# 更新用户信息
@router.put("/update")
async def update_user_info(
    user_data: UserUpdateRequest,
    user: User = Depends(get_current_user), # 验证用户是否登录
    db: AsyncSession = Depends(db_config.get_database)
):
    user = await update_user(user_data, user.username, db)
    response_data = UserInfoResponse.model_validate(user)
    return success_response("更新用户信息成功", data=response_data)

# 设置修改密码的功能
@router.put("/password")
async def update_password(
    password_data: UserChangePasswordRequest,
    user: User = Depends(get_current_user), # 验证用户是否登录
    db: AsyncSession = Depends(db_config.get_database)
):
    res_change_pwd = await change_password(user, password_data.old_password, password_data.new_password, db)

    if res_change_pwd:
        return success_response("修改密码成功")
    else:
        raise HTTPException(status_code=400, detail="修改密码失败")
