from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime



class NewsItemBase(BaseModel):
    id: int 
    title: str
    description: Optional[str] = None
    image: Optional[str] = None
    author: Optional[str] = None
    category_id: int = Field(None, description="分类ID", alias="categoryId")
    views: int
    publish_time: Optional[datetime] = Field(None, alias="publishTime")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )
