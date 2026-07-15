from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column
from sqlalchemy import DateTime
from datetime import datetime
from sqlalchemy import Integer,String,Index,Text,ForeignKey
from typing import Optional


class Base(DeclarativeBase):
    created_at:Mapped[datetime]=mapped_column(
        DateTime,
        default=datetime.now,
        comment="创建时间"
    )
    updated_at:Mapped[datetime]=mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        comment="更新时间"
    )
class News(Base):  
    __tablename__="news"

    #创建索引：提升查询速度(添加目录)
    __table_args__ = (
        Index('fk_news_category_idx','category_id'), #高频查询场景
        Index('idx_publish_time','publish_time') #按发布时间排序
    )

    id:Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="新闻ID"
    )
    title:Mapped[str] = mapped_column(
        String(255),
        comment="新闻标题"
    )
    description:Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="新闻简介"
    )
    content: Mapped[str] = mapped_column(
        Text,
        comment="新闻内容"
    )
    image: Mapped[Optional[str]] = mapped_column(
        String(255),
        comment="封面图片URL"
    )
    author: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="作者"
    )
    category_id:Mapped[int] = mapped_column(
        Integer,
        comment="分类ID")
    views:Mapped[int] = mapped_column(
        Integer,
        ForeignKey("news_category.id"), #副键
        comment="浏览量"
    )
    publish_time:Mapped[datetime] = mapped_column(
        comment="出版时间"
    )
    def __repr__(self):
        return f"<New(id={self.id},title='{self.title}',views={self.views}>"

class category(Base):
    __tablename__="news_category"
    id:Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    name:Mapped[str] = mapped_column(
        String(50),
        unique=True, #名称不能重复
        nullable=False, #不能为空
        comment="分类名称"
    )
    sort_order:Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="排序"
    )
    #打印（在命令行中）
    def __repr__(self):
        return f"<category{self.id},name={self.name},sort_order={self.sort_order}>"
