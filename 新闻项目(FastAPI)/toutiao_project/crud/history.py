from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,func,delete
from models.history import History
from models.news import News


async def add_news_history(
        db:AsyncSession,
        user_id: int,
        news_id: int,
):
    query = select(History).where(History.news_id == news_id,History.user_id == user_id)
    result = await db.execute(query)
    existing_history = result.scalar_one_or_none()
    if existing_history:
        existing_history.view_time = datetime.now()
        await db.commit()
        await db.refresh(existing_history)
        return existing_history
    else:
        history = History(news_id=news_id,user_id=user_id)
        db.add(history)
        await db.commit()
        await db.refresh(history)
        return history


async def get_history_list(
        db:AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 10,
):

    offset = (page-1)*page_size
    count_query = select(func.count(History.id)).where(History.user_id == user_id)
    result = await db.execute(count_query)
    total_count = result.scalar_one_or_none()
    #联合查询 [ (News,浏览时间,浏览ID) ]
    query = (select(News,History.view_time.label("view_time"),History.id.label("history_id"))
             .join(History,History.news_id == News.id)
             .where(History.user_id == user_id)
             .order_by(History.view_time.desc())
             .offset(offset).limit(page_size))
    result = await db.execute(query)
    rows = result.all()
    return  total_count,rows


async def remove_history(
        db:AsyncSession,
        user_id: int,
        news_id: int
):
    query = delete(History).where(History.news_id == news_id,History.user_id == user_id)
    result = await db.execute(query)
    await db.commit()
    return result.rowcount > 0

async def clear_history_news(
        db:AsyncSession,
        user_id: int,
):
    query = delete(History).where(History.user_id == user_id)
    result = await db.execute(query)
    await db.commit()
    return result.rowcount or 0