from fastapi import APIRouter, Depends,Query,HTTPException
from starlette import status
from config.db_config import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from models.users import User
from utils.auth import get_current_user
from schemas.history import HistoryAddRequest,HistoryListRequest
from utils.response import success_response
from crud.history import add_news_history,get_history_list,remove_history,clear_history_news

router = APIRouter(prefix="/api/history", tags=["history"])


@router.post("/add")
async def add_history(
        data:HistoryAddRequest,
        user:User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    result = await add_news_history(db,user.id,data.news_id)
    return success_response(message="添加成功",data=result)

@router.get("/list")
async def list_history(
        db: AsyncSession = Depends(get_db),
        user: User = Depends(get_current_user),
        page: int = Query(1,ge=1),
        page_size: int = Query(10,ge=1,le=100,alias="pageSize"),
):
    total,rows = await get_history_list(db,user.id,page,page_size)
    has_more = total > page * page_size
    history_list = [{
        **history.__dict__,
        "view_time":view_time,
        "history_id":history_id,
    }for history,view_time,history_id in rows]
    data = HistoryListRequest(list=history_list,total=total,hasMore=has_more)
    return success_response(data=data)

@router.delete("/delete/{news_id}")
async def delete_history(
        news_id: int,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    result = await remove_history(db,user.id,news_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="历史记录不存在")
    return success_response(message="删除成功")

@router.delete("/clear")
async def clear_history(
        db: AsyncSession = Depends(get_db),
        user: User = Depends(get_current_user)
):
    result = await clear_history_news(db,user.id)
    return success_response(message="清空成功")