from sqlalchemy import select,delete,func
from sqlalchemy.ext.asyncio import AsyncSession
from models.favorite import Favorite
from models.news import News

from starlette.exceptions import HTTPException
from starlette import status


#检查收藏状态：当前用户是否收藏了这一条新闻
async def is_news_favorite(
        db: AsyncSession,
        user_id: int,
        news_id: int
):
    query = select(Favorite).where(Favorite.news_id == news_id, Favorite.user_id == user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none() is not None

async def add_favorite(
        db: AsyncSession,
        user_id: int,
        news_id: int
):
    favorite = Favorite(news_id=news_id, user_id=user_id)
    db.add(favorite)
    await db.commit()
    await db.refresh(favorite)
    return favorite

async def remove_favorite(
        db: AsyncSession,
        user_id: int,
        news_id: int
):
    stmt = delete(Favorite).where(Favorite.news_id == news_id, Favorite.user_id == user_id)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0


#获取收藏列表： 获取的是某个用户的收藏列表 + 分页功能
async def get_favorite_list(
        db: AsyncSession,
        user_id: int,
        page: int,
        page_size: int
):
   #总量
    count_query = select(func.count()).where(Favorite.user_id == user_id)
    count_result = await db.execute(count_query)
    total = count_result.scalar_one_or_none()
    #获取收藏列表 - 联表查询join() + 收藏时间排序 + 分页
    #联表查询
    stmt = (page-1)*page_size
    #select(查询主体模型类,字段别名).join(联合查询的模型类,联合查询的条件).where().order_by().offset().limit()
    #别名：Favorite.created_at.label("favorite_time)
    query = (select(News,Favorite.created_at.label("favorite_time"),Favorite.id.label("news_id"))
             .join(Favorite,Favorite.news_id == News.id)
             .where(Favorite.user_id == user_id)
             .order_by(Favorite.created_at.desc())
             .offset(stmt).limit(page_size))
    #[ (新闻对象，收藏时间，收藏id) ]
    result = await db.execute(query)
    rows = result.all()
    return rows,total

async def clear_favorite(
        db: AsyncSession,
        user_id: int
):
    query = delete(Favorite).where(Favorite.user_id == user_id)
    result = await db.execute(query)
    await db.commit()
    return result.rowcount or 0