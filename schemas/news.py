from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime

class NewsCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="新闻标题")
    description: Optional[str] = Field(None, max_length=500, description="新闻描述")
    content: str = Field(..., min_length=1, description="新闻内容")
    image: Optional[str] = Field(None, max_length=255, description="新闻图片")
    category_id: int = Field(..., description="分类ID", alias="categoryId", gt=0)
    model_config = ConfigDict(populate_by_name=True)
    

class NewsUpdateRequest(BaseModel):
    id: int = Field(..., description="新闻ID", gt=0)
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="新闻标题")
    description: Optional[str] = Field(None, max_length=500, description="新闻描述")
    content: Optional[str] = Field(None, min_length=1, description="新闻内容")
    image: Optional[str] = Field(None, max_length=255, description="新闻图片")
    category_id: Optional[int] = Field(None, description="分类ID", alias="categoryId", gt=0)
    model_config = ConfigDict(populate_by_name=True)
