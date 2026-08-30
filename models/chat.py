from datetime import datetime

from sqlalchemy import TIMESTAMP, ForeignKey, Index, Integer, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from models.news import Base


class AIChat(Base):
    __tablename__ = "ai_chat"

    __table_args__ = (
        Index("fk_ai_chat_user_idx", "user_id"),
        Index("idx_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="聊天记录ID"
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id"), nullable=False, comment="用户ID"
    )
    message: Mapped[str] = mapped_column(
        Text, nullable=False, comment="用户消息"
    )
    response: Mapped[str] = mapped_column(
        Text, nullable=False, comment="AI回复"
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        comment="创建时间",
    )

    def __repr__(self) -> str:
        return (
            f"<AIChat(id={self.id}, user_id={self.user_id}, "
            f"created_at={self.created_at})>"
        )