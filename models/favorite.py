from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, ForeignKey, Integer, String
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Index, Text, ForeignKey, Enum, UniqueConstraint
from sqlalchemy import TIMESTAMP, text
from models.news import Base

class Favorite(Base):
    """收藏表的ORM模型，对应数据库中的favorites表
    """
    __tablename__ = "favorite"

    __table_args__ = (
        # UniqueConstraint 表示唯一约束，表示当前用户的当前新闻只能收藏一次
        UniqueConstraint('user_id', 'news_id', name='user_news_unique'),
        Index('fk_favorite_user_idx', 'user_id'),
        Index('fk_favorite_news_idx', 'news_id'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False)
    news_id: Mapped[int] = mapped_column(Integer, ForeignKey("news.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    
    def __repr__(self) -> str:
        return f"<Favorite(id={self.id}, user_id={self.user_id}, news_id={self.news_id}, created_at={self.created_at})>"

