from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from schemas.base import NewsItemBase

class FavoriteCheckResponse(BaseModel):
    is_favorite: bool = Field(..., description="是否收藏了该新闻", alias="isFavorite")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )

class FavoriteAddRequest(BaseModel):
    news_id: int = Field(..., description="新闻ID", alias="newsId")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )

# 一个新闻模型类 + 收藏的模型类
class FavoriteNewsItemResponse(NewsItemBase):
    favorite_id: int = Field(description="收藏ID", alias="favoriteId")
    favorite_time: datetime = Field(description="收藏时间", alias="favoriteTime")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )

#  收藏列表响应的模型类
class FavoriteListResponse(BaseModel):
    list: list[FavoriteNewsItemResponse]
    total: int 
    has_more: bool = Field(..., description="是否还有更多数据", alias="hasMore")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )
