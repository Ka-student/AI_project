from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,func,update
from models.news import category,News

async def get_category(db:AsyncSession,skip:int=0,limit:int=100):
    result = await db.execute(
        select(category).offset(skip).limit(limit)
    )
    return result.scalars().all()

async def get_news_list(db:AsyncSession,category_id:int,skip:int=0,limit:int=10):
    #查询指定分类下的所有新闻
    stmt = select(News).where(News.category_id == category_id).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_news_count(db:AsyncSession,category_id:int):
    stmt = select(func.count(News.category_id)).where(News.category_id == category_id)
    result = await db.execute(stmt)
    return result.scalar_one() #只能有一个结果，否则报错

async def get_news_detail(db:AsyncSession,news_id:int):
    stmt = select(News).where(News.id == news_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def increase_news_views(db:AsyncSession,news_id:int):
    stmt = update(News).where(News.id == news_id).values(views = News.views + 1)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0 #获取修改了多少条数据

async def get_related_news(db:AsyncSession,news_id:int,category_id:int,limit:int=5):
    #order_by 排序 -> 按浏览量和发布时间显示
    stmt = (select(News).where(
        News.category_id == category_id,
        News.id != news_id
    ).order_by(
        News.views.desc(),
        News.publish_time.desc() #默认是升序，desc表示降序
        ).limit(limit))
    result = await db.execute(stmt)
    #return result.scalars().all()
    #列表推导式 推导出新闻的核心数据，然后再return
    return [{
        "id":news_detail.id,
        "title":news_detail.title,
        "content":news_detail.content,
        "image":news_detail.image,
        "author":news_detail.author,
        "publish_time":news_detail.publish_time,
        "categoryId":news_detail.category_id,
        "views":news_detail.views
    } for news_detail in result.scalars().all()]