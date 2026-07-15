from fastapi import APIRouter,Depends,Query,HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from config.db_config import get_db
from crud import news
from crud import news_cache

#创建APIRouter实例
router = APIRouter(prefix="/api/news",tags=["news"]) #prefix 路由前缀， tag 组名

#接口实现流程
#1.模块化路由 -> APIk接口规范文档
#2.定义模型类 -> 数据库表（数据库设计文档）
#3.在crud文件夹里面创建文件，封装操作数据库的方法
#4.在路由处理函数里面调用crud封装好的方法，响应结果

@router.get("/categories")
async def get_categories(skip:int=0,limit:int=100,db:AsyncSession=Depends(get_db)):
    categories = await news_cache.get_category(db,skip,limit)
    return {
        "code":200,
        "message":"获取新闻分类成功",
        "data":categories
    }

@router.get("/list")
async def get_news_list(
    category_id:int = Query(...,alias="categoryId"),
    page:int = 1,
    page_size:int = Query(10,le=100,alias="page_Size"),
    db:AsyncSession=Depends(get_db)
):
    #思路：处理分页规则 -> 查询新闻列表 -> 计算总量 -> 计算是否还有更多
    offset = (page-1)*page_size
    news_list = await news_cache.get_news_list(db,category_id,offset,page_size)
    total = await news.get_news_count(db, category_id)
    has_more = (offset+len(news_list)) < total
    return {
        "code":200,
        "message":"获取新闻列表成功",
        "data":{
            "list":news_list,
            "total": total,
            "hasMore": has_more
        }
    }

@router.get("/detail")
async def get_news_detail(new_id:int = Query(...,alias="id"),db:AsyncSession=Depends(get_db)):
    #获取新闻详情 + 浏览量+1 + 相关新闻
    news_detail = await news_cache.get_news_detail(db,new_id)
    if news_detail is None:
        raise HTTPException(status_code=404,detail="新闻不存在")
    views_res = await news.increase_news_views(db,news_detail.id)
    if not views_res:
        raise HTTPException(status_code=404,detail="新闻不存在")
    related_news = await news_cache.get_related_news(db,news_detail.id,news_detail.category_id)
    return {
        "code":200,
        "message":"获取新闻详情成功",
        "data":{
            "id":news_detail.id,
            "title":news_detail.title,
            "content":news_detail.content,
            "image":news_detail.image,
            "author":news_detail.author,
            "publish_time":news_detail.publish_time,
            "categoryId":news_detail.category_id,
            "views":news_detail.views,
            "relatedNews":related_news
        }
    }


