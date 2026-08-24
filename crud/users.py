# 这里会封装用户模块增删改查的方法
from models.users import User, UserToken
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, Update
from fastapi import HTTPException
from schemas.users import UserRequest, UserUpdateRequest
from utils import security
import uuid
from datetime import datetime, timedelta

# 根据用户名查询数据库
async def get_user_by_username(username: str, db: AsyncSession):
    result = await db.execute(select(User).where(User.username == username))
    return result.scalars().one_or_none()

# 创建用户
async def create_user(user_data: UserRequest, db: AsyncSession):
    # 先加密处理
    hashed_password = security.get_password_hash(user_data.password)
    user = User(username=user_data.username, password=hashed_password)
    db.add(user)
    await db.flush()
    await db.refresh(user) # 从数据库读回最新的User
    return user

# 生成token
async def create_token(user_id: int, db: AsyncSession):
    # 生成token 设置过期时间 查询数据库当前用户是否有token 有的话更新 没有的话添加
    token = str(uuid.uuid4())
    expires_at = datetime.now() + timedelta(days=7)
    query = select(UserToken).where(UserToken.user_id == user_id)
    result = await db.execute(query)
    user_token = result.scalars().one_or_none()

    if user_token:
        # 更新token
        query = Update(UserToken).where(UserToken.user_id == user_id).values(token=token, expires_at=expires_at)
        await db.execute(query)
    else:
        # 添加token
        user_token = UserToken(user_id=user_id, token=token, expires_at=expires_at)
        db.add(user_token)
    await db.flush()
    await db.refresh(user_token)
    return token

# 用户登录认证
async def authenticate_user(username: str, password: str, db: AsyncSession):
    user = await get_user_by_username(username, db)
    if not user:
        return None
    if not security.verify_password(password, user.password):
        return None
    
    return user

# 根据token查询用户
async def get_user_by_token(token: str, db: AsyncSession):
    query1 = select(UserToken).where(UserToken.token == token)
    result = await db.execute(query1)
    db_token = result.scalars().one_or_none()
    # 如果token存在且未过期，就进一步查询用户信息并返回
    if db_token and db_token.expires_at > datetime.now():
        query2 = select(User).where(User.id == db_token.user_id)
        result = await db.execute(query2)
        return result.scalars().one_or_none()
    else:
        return None

# 更新用户信息
async def update_user(user_data: UserUpdateRequest, username: str, db: AsyncSession):
    # 没有设置值的不更新
    query = Update(User).where(User.username == username).values(**user_data.model_dump(
        exclude_unset=True,
        exclude_none=True
    ))
    result = await db.execute(query)
    await db.flush()
    
    # 检查更新
    if result.rowcount == 0:
        raise HTTPException(status_code=400, detail="更新失败")

    # 获取一下更新后的信息
    updated_user = await get_user_by_username(username, db)
    return updated_user

#  修改密码  验证旧密码 -》新密码加密 -》 修改密码
async def change_password(user: User, old_password: str, new_password: str, db: AsyncSession):
    if not security.verify_password(old_password, user.password): # 验证旧密码
        return False # 旧密码不对
    
    hashed_new_pwd = security.get_password_hash(new_password)
    user.password = hashed_new_pwd
    db.add(user) # 由sqlalchemy真正处理确保可以由后续的commit之类的操作
    await db.flush()
    await db.refresh(user)
    return True
    


