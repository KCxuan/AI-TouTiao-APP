# 本文件存放用户的pydantic模型类
from typing import Optional
from pydantic import Field
from pydantic import BaseModel, ConfigDict

class UserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    password: str = Field(..., min_length=6, max_length=100)

# user_info 对应的类 ： 基础类 + Info类（id 用户名）
class UserInfoBase(BaseModel):
    """
    用户基础信息数据模型
    """
    nickname: Optional[str] = Field(None, max_length=50, description="昵称")
    avatar: Optional[str] = Field(None, max_length=255, description="头像URL")
    gender: Optional[str] = Field(None, max_length=10, description="性别")
    bio: Optional[str] = Field(None, max_length=500, description="个人简介")

class UserInfoResponse(UserInfoBase):
    id: int = Field(..., description="用户ID")
    username: str = Field(..., max_length=20, description="用户名")

    model_config = ConfigDict(
        from_attributes=True # 允许从属性中获取字段值ORM对象中取值
    )

# data 数据类型
class UserAuthResponse(BaseModel):
    token: str
    user_info: UserInfoResponse = Field(...,alias="userInfo")

    # 模型类配置
    model_config = ConfigDict(
        populate_by_name=True, # alias / 字段名兼容
        from_attributes=True # 允许从属性中获取字段值ORM对象中取值
    )

class UserUpdateRequest(BaseModel):
    nickname: Optional[str] = Field(None, max_length=50, description="昵称")
    avatar: Optional[str] = Field(None, max_length=255, description="头像URL")
    gender: Optional[str] = Field(None, max_length=10, description="性别")
    bio: Optional[str] = Field(None, max_length=500, description="个人简介")
    phone: Optional[str] = Field(None, max_length=15, description="手机号")

class UserChangePasswordRequest(BaseModel):
    old_password: str = Field(..., description="旧密码", alias="oldPassword")
    new_password: str = Field(..., min_length=6, description="新密码", alias="newPassword")
    
