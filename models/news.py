from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, ForeignKey, Integer, String
from datetime import datetime
from typing import Optional
from sqlalchemy import Index, Text, ForeignKey


class Base(DeclarativeBase):
    pass

class Category(Base):
    __tablename__ = "news_category"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="分类ID")
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="分类名称")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="排序")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.now, 
        comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.now, 
        onupdate=datetime.now, 
        comment="更新时间"
    )

    def __repr__(self):
        return f"<Category id={self.id}, name={self.name}, sort_order={self.sort_order}>"

class News(Base):
    __tablename__ = "news"

    # 创建索引，提高查询效率
    __table_args__ = (
        Index('fk_news_category_idx', 'category_id'), # 高频查询
        Index('idx_publish_time', 'publish_time') # 按发布时间来排序
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="新闻ID")
    title: Mapped[str] = mapped_column(String(255), nullable=False, comment="新闻标题")
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=False, comment="新闻简述")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="新闻内容")
    image: Mapped[Optional[str]] = mapped_column(String(255), nullable=False, comment="封面图片URL")
    author: Mapped[Optional[str]] = mapped_column(String(50), nullable=False, comment="作者")
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id'), comment="用户ID")
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey('news_category.id'),nullable=False, comment="分类ID")
    views: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="浏览次数")
    publish_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False, comment="发布时间")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.now, 
        comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.now, 
        onupdate=datetime.now, 
        comment="更新时间"
    )

    def __repr__(self):
        return f"<News id={self.id}, title={self.title}, description={self.description}, content={self.content}, image={self.image}, author={self.author}, category_id={self.category_id}, views={self.views}, publish_time={self.publish_time}>"
