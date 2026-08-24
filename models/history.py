from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, ForeignKey, Integer, String
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Index, Text, ForeignKey, Enum, UniqueConstraint
from sqlalchemy import TIMESTAMP, text
from models.news import Base



class History(Base):
    __tablename__ = "history"

    __table_args__ = (
        Index('idx_view_time', 'view_time'),
        Index('fk_history_user_idx', 'user_id'),
        Index('fk_history_news_idx', 'news_id'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True,comment="历史ID")
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False, comment="用户ID")
    news_id: Mapped[int] = mapped_column(Integer, ForeignKey("news.id"), nullable=False, comment="新闻ID")
    view_time: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        comment="浏览时间"
    )

    def __repr__(self) -> str:
        return f"<History(id={self.id}, user_id={self.user_id}, news_id={self.news_id}, view_time={self.view_time})>"
