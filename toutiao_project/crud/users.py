from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,update
from models.users import User,UserToken
from schemas.users import userRequest, UserUpdateRequest
from utils import security
import uuid
from  datetime import datetime,timedelta

async def get_users(db: AsyncSession,username:str):
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

#创建用户
async def create_user(db: AsyncSession,user_data:userRequest):
    #先密码加密处理 -> add
    hashed_password = security.get_hash_password(user_data.password)
    user = User(username = user_data.username, password = hashed_password)
    db.add(user)
    await db.commit()
    await db.refresh(user) #从数据库读回最新的 user
    return user

#生成Token
async def create_token(db: AsyncSession,user_id: int):
    #生成Token + 设置过期时间 -> 查询数据库当前用户是否有Token -> 有：更新； 没有：添加
    token = str(uuid.uuid4())
    #timedelta(days=7,hours=2,minures=30,seconds=10) 7天2小时30分钟10秒后过期
    expires_at = datetime.now() + timedelta(days=7)
    query = select(UserToken).where(UserToken.user_id == user_id)
    result = await db.execute(query)
    user_token = result.scalar_one_or_none()
    if user_token:
        user_token.token = token
        user_token.expires_at = expires_at
    else:
        user_token = UserToken(user_id=user_id,token=token,expires_at=expires_at)
        db.add(user_token)
        await db.commit()
    return token

async def authenticate_user(db: AsyncSession,username:str,password:str):
    user = await get_users(db,username)
    if not user:
        return None
    if not security.verify_password(password,user.password):
        return None
    return user

#根据Token查询用户：验证Token -> 查询用户
async def get_user_by_token(db: AsyncSession,token:str):
    query = select(UserToken).where(UserToken.token == token)
    result = await db.execute(query)
    db_token = result.scalar_one_or_none()
    if not db_token or db_token.expires_at < datetime.now():
        return None
    query = select(User).where(User.id == db_token.user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()

#更新用户信息: update更新 -> 检查是否命中 -> 获取更新后的用户返回
async def update_user(db:AsyncSession,username:str,user_data:UserUpdateRequest):
    #user_data 是一个Pydantic类型，得到字典 -> ** 解包
    #user_data.model_dump() 把user_data 转成字典， ** 解包：字典 -> 字段=值，字段=值
    #没有设置值的不更新
    query = update(User).where(User.username==username).values(**user_data.model_dump(
        exclude_unset=True,
        exclude_none=True
    ))
    result = await db.execute(query)
    await db.commit()
    #检查更新
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="用户不存在")
    #获取一下更新后的用户
    updated_user = await get_users(db,username)
    return updated_user

#修改密码：验证密码 -> 新密码加密 -> 修改密码
async def Change_password(db:AsyncSession,user:User,old_password:str,new_password:str):
    if not security.verify_password(old_password, user.password):
        return False
    hash_new_pwd = security.get_hash_password(new_password)
    user.password = hash_new_pwd
    #更新：由sqlalchemy真正接管这个user对象，确保可以commit
    #规避 session 过期或关闭导致的不能提交的问题
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return True


