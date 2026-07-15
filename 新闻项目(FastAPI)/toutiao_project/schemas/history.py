from pydantic import BaseModel,Field,ConfigDict
from datetime import datetime
from schemas.base import NewsItemBase


class HistoryAddRequest(BaseModel):
    news_id: int = Field(...,alias="newsId")

#浏览历史列表中的新闻项响应
class HistoryNewsItemResponse(NewsItemBase):
    history_id: int = Field(...,alias="historyId")
    view_time: datetime = Field(...,alias="viewTime")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )
#浏览历史列表接口响应模型类
class HistoryListRequest(BaseModel):
    list:list[HistoryNewsItemResponse]
    total:int
    has_more: bool = Field(...,alias="hasMore")

    model_config = ConfigDict(
        populate_by_name=True,  # 字段名兼容
        from_attributes=True  # 允许从ORM对象属性中取值
    )

