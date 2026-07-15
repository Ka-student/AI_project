from sqlalchemy.ext.asyncio import async_sessionmaker,AsyncSession,create_async_engine

#数据库URL
ASYNC_DATABASE_URL = "mysql+aiomysql://root:root@localhost:3306/news_app?charset=utf8mb4"
#异步引擎
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=True, #输出sql日志
    pool_size=10, #设置连接池中保持的持久连接数
    max_overflow=5, #设置连接池允许创建的额外连接数
    future=True,
)
#异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind = async_engine, #绑定数据库引擎
    class_ = AsyncSession, #指定会话类
    expire_on_commit = False #会话对象不过期，不会重新查询数据库
)
#依赖项
async def get_db():
    async with AsyncSessionLocal() as conn:
        try:
            yield conn #返回数据库会话给路由处理函数
            await conn.commit() #提交事务
        except Exception:
            await conn.rollback() #异常回滚
            raise
