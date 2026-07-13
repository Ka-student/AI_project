from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from config.db_config import get_db
from schemas.users import userRequest, UserAuthRequest, UserInfoResponse, UserUpdateRequest,UserChangePasswordRequest
from crud import users
from starlette import status
from utils.response import success_response
from utils.auth import get_current_user
from models.users import User

router = APIRouter(prefix = "/api/user",tags=["users"])

@router.post("/register")
async def register(user_data:userRequest,db:AsyncSession = Depends(get_db)):
    #注册逻辑：验证用户是否存在 -> 创建用户 ->生成Token -> 响应结果
    #Token: 服务器发给客户端的一段字符串，用来在后续请求中证明“你已经登录过了”
    existing_user = await users.get_users(db, user_data.username)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="用户已存在")
    user = await users.create_user(db,user_data)
    token = await users.create_token(db,user.id)
    # return {
    #     "code": 200,
    #     "message":"注册成功",
    #     "data":{
    #         "token":token,
    #         "userinfo":{
    #             "id":user.id,
    #             "username":user.username,
    #             "bio": user.bio,
    #             "avatar":user.avatar,
    #         }
    #     }
    # }
    response_data = UserAuthRequest(token=token,userInfo=UserInfoResponse.model_validate(user))
    return success_response(message="注册成功",data=response_data)

@router.post("/login")
async def login_user(login_data:userRequest,db:AsyncSession = Depends(get_db)):
    #登录逻辑： 验证用户是否存在 -> 验证密码 -> 生成Token ->响应结果
    user = await users.authenticate_user(db,login_data.username,login_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="用户名或密码错误")
    token = await users.create_token(db,user.id)
    response_data = UserAuthRequest(token=token,userInfo=UserInfoResponse.model_validate(user))
    return success_response(message="登录成功",data=response_data)

#查Token查用户 -> 封装crud -> 功能整合成一个工具函数 ->路由导入使用(依赖注入)
@router.get("/info")
async def get_user_info(user:User = Depends(get_current_user)):
    return success_response(message="获取用户信息成功",data=UserInfoResponse.model_validate(user))


#修改用户信息：验证Token -> 更新(用户输入数据 put提交 -> 请求体参数 -> 定义Pydantic模型类) -> 响应结果
#参数：用户输入的 + 验证Token的 + db(调用更新的方法)
@router.put("/update")
async def put_user_update(
        user_data:UserUpdateRequest,
        user:User = Depends(get_current_user),
        db:AsyncSession = Depends(get_db)):
    user = await users.update_user(db,user.username,user_data)
    return success_response(message="更新用户信息成功",data=UserInfoResponse.model_validate(user))

@router.put("/password")
async def update_password(
        user_data:UserChangePasswordRequest,
        user:User = Depends(get_current_user),
        db:AsyncSession = Depends(get_db)):
    res_change_pwd = await users.Change_password(db,user,user_data.old_password,user_data.new_password)
    if not res_change_pwd:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="修改密码失败，请稍后再试")
    return success_response(message="修改密码成功")


