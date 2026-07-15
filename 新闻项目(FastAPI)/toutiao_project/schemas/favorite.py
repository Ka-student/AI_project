from pydantic import BaseModel, Field, ConfigDict
from schemas.base import NewsItemBase
from datetime import datetime

class FavoriteCheckResponse(BaseModel):
    is_favorite: bool = Field(...,alias="isFavorite")

class FavoriteAddResponse(BaseModel):
    news_id: int = Field(...,alias="newsId")

#收藏列表中的新闻项响应
class FavoriteNewsItemResponse(NewsItemBase):
    favorite_id:int = Field(...,alias="favoriteId")
    favorite_time:datetime = Field(...,alias="favoriteTime")

    model_config = ConfigDict(
        populate_by_name=True,  # 字段名兼容
        from_attributes=True  # 允许从ORM对象属性中取值
    )

#收藏列表接口响应模型类
class FavoriteListResponse(BaseModel):
    list: list[FavoriteNewsItemResponse]
    total: int
    has_more: bool = Field(...,alias="hasMore")

    model_config = ConfigDict(
        populate_by_name=True, #字段名兼容
        from_attributes=True #允许从ORM对象属性中取值
    )

