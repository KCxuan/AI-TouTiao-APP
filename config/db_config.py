from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import URL

DATABASE_URL = URL.create(
    drivername="mysql+aiomysql",
    username="root",
    password="Aa20051030",
    host="127.0.0.1",
    port="3306",
    database="news_app",
    query={"charset": "utf8mb4"}
)

async_engine = create_async_engine(DATABASE_URL, echo=True, pool_size=10, max_overflow=20)
async_session = async_sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)


# 写一个依赖项，用户获取数据库会话
async def get_database():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
    
