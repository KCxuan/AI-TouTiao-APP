from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from schemas.base import NewsItemBase

class HistoryAddRequest(BaseModel):
    news_id: int = Field(..., description="新闻ID", alias="newsId")
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class HistoryNewsItemResponse(NewsItemBase):
    view_time: datetime = Field(..., description="浏览时间", alias="viewTime")
    history_id: int = Field(..., description="历史新闻ID", alias="historyId")
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class HistoryListResponse(BaseModel):
    list: list[HistoryNewsItemResponse]
    total: int = Field(..., description="历史新闻总数")
    has_more: bool = Field(..., description="是否还有更多历史新闻", alias="hasMore")
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

