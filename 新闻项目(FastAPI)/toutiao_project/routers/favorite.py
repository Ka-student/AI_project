from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from config.db_config import get_db
from models.users import User
from schemas.favorite import FavoriteCheckResponse, FavoriteAddResponse,FavoriteListResponse
from utils.auth import get_current_user
from utils.response import success_response
from crud import favorite
from starlette import status

router = APIRouter(prefix="/api/favorite",tags=["favorite"])

@router.get("/check")
async def get_check_favorite(
        news_id:int =Query(...,alias="newsId"),
        user:User = Depends(get_current_user),
        db:AsyncSession = Depends(get_db)
):
    is_favorite = await favorite.is_news_favorite(db,user.id,news_id)
    return success_response(message="检查收藏状态成功",data=FavoriteCheckResponse(isFavorite=is_favorite))

@router.post("/add")
async def add_favorite(
        data: FavoriteAddResponse,
        user:User = Depends(get_current_user),
        db:AsyncSession = Depends(get_db)
):
    result = await favorite.add_favorite(db,user.id,data.news_id)
    return success_response(message="收藏成功", data=result)

@router.delete("/remove")
async def remove_favorite(
        db:AsyncSession = Depends(get_db),
        user:User = Depends(get_current_user),
        news_id:int = Query(...,alias="newsId")
):
    result = await favorite.remove_favorite(db,user.id,news_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="收藏记录不存在")
    return success_response(message="取消收藏成功")

@router.get("/list")
async def get_favorite_list(
        db:AsyncSession = Depends(get_db),
        user:User = Depends(get_current_user),
        page:int =Query(1,ge=1),
        page_size:int =Query(10,ge=1,le=100)
):
    rows,total = await favorite.get_favorite_list(db,user.id,page,page_size)
    favorite_list = [{
        **news.__dict__,
        "favorite_time":favorite_time,
        "favorite_id":favorite_id
    } for news,favorite_time,favorite_id in rows ]
    has_more = total > page*page_size
    data = FavoriteListResponse(list=favorite_list,total=total,hasMore=has_more)
    return success_response(message="获取收藏列表",data=data)

@router.delete("/clear")
async def clear_favorite(
        db:AsyncSession = Depends(get_db),
        user:User = Depends(get_current_user)
):
    count = await favorite.clear_favorite(db,user.id)
    return success_response(message=f"成功删除{count}条收藏记录")
