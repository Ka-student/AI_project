from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,func,update
from models.news import category,News
from cache import news_cache
from schemas.base import NewsItemBase

async def get_category(db:AsyncSession,skip:int=0,limit:int=100):
    #先尝试从缓存中获取数据
    cache_categories = await news_cache.get_cached_categories()
    if cache_categories:
        return cache_categories
    result = await db.execute(
        select(category).offset(skip).limit(limit)
    )
    cache_categories = result.scalars().all() #ORM结果
    #写入缓存
    if cache_categories:
        cache_categories = jsonable_encoder(cache_categories) #将复杂格式（ORM对象）转为json能认识的格式
        await news_cache.set_cache_categories(cache_categories)
    #返回数据
    return cache_categories

async def get_news_list(db:AsyncSession,category_id:int,skip:int=0,limit:int=10):
    #先尝试从缓存获取新闻列表
    page = skip//limit+1 #skip 跳过的数量
    cache_list = await news_cache.get_cache_news_list(category_id,page,limit) #缓存数据JSON
    if cache_list:
        #需要返回ORM
        return [News(**item) for item in cache_list]
    #查询指定分类下的所有新闻
    stmt = select(News).where(News.category_id == category_id).offset(skip).limit(limit)
    result = await db.execute(stmt)
    news_result = result.scalars().all()
    #写入缓存
    if news_result:
        #先把ORM数据转换字典才能写入缓存
        #news_data = jsonable_encoder(news_result) #ORM 转成 JSON 方法一
        #ORM 转成pydantic，再转为字典  方法二   NewsItemBase.model_validate(item) 转为pydantic
        #by_alias=False 不使用别名，保存python风格，因为redis数据是给后端用的
        news_data = [NewsItemBase.model_validate(item).model_dump(mode="json",by_alias=False) for item in news_result]
        await news_cache.set_cache_news_list(category_id,page,limit,news_data)
    return news_result

async def get_news_count(db:AsyncSession,category_id:int):

    stmt = select(func.count(News.category_id)).where(News.category_id == category_id)
    result = await db.execute(stmt)
    return result.scalar_one() #只能有一个结果，否则报错

async def get_news_detail(db:AsyncSession,news_id:int):
    #尝试读取缓存
    cache_detail = await news_cache.get_news_detail(news_id)
    if cache_detail:
        return News(**cache_detail)
    stmt = select(News).where(News.id == news_id)
    result = await db.execute(stmt)
    news_detail = result.scalar_one_or_none()
    #写入缓存
    if news_detail:
        news_dict = jsonable_encoder(news_detail)
        await news_cache.set_news_detail(news_id,news_dict)
    return news_detail


async def increase_news_views(db:AsyncSession,news_id:int):
    stmt = update(News).where(News.id == news_id).values(views = News.views + 1)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0 #获取修改了多少条数据


async def get_related_news(db:AsyncSession,news_id:int,category_id:int,limit:int=5):
    # 尝试读取缓存
    cached_related = await news_cache.get_related_news(news_id,category_id)
    if cached_related:
        return cached_related
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
    related_news = result.scalars().all()
    # 写入缓存
    if related_news:
        related_cache = jsonable_encoder(related_news)
        await news_cache.set_related_news(news_id,category_id,related_cache)
    return related_news