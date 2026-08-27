from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from models.news import Base


class ResearchRun(Base):
    __tablename__ = "research_run"

    __table_args__ = (
        Index("thread_id_UNIQUE", "thread_id", unique=True),
        Index("idx_research_run_user_status", "user_id", "status"),
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="任务ID"
    )
    thread_id: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, comment="LangGraph thread_id"
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id"), nullable=False, comment="用户ID"
    )
    user_input: Mapped[str] = mapped_column(
        Text, nullable=False, comment="研究主题"
    )
    status: Mapped[str] = mapped_column(
        Enum("waiting_review", "completed", "abandoned"),
        nullable=False,
        default="waiting_review",
        comment="任务状态",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间"
    )

    def __repr__(self) -> str:
        return (
            f"<ResearchRun(id={self.id}, thread_id='{self.thread_id}', "
            f"user_id={self.user_id}, status='{self.status}')>"
        )