from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import URL

from config.env import require_env

DATABASE_URL = URL.create(
    drivername="mysql+aiomysql",
    username=require_env("MYSQL_USER"),
    password=require_env("MYSQL_PASSWORD", allow_empty=True),
    host=require_env("MYSQL_HOST"),
    port=int(require_env("MYSQL_PORT")),
    database=require_env("MYSQL_DATABASE"),
    query={"charset": "utf8mb4"},
)

async_engine = create_async_engine(
    DATABASE_URL, echo=True, pool_size=10, max_overflow=20
)
async_session = async_sessionmaker(
    async_engine, expire_on_commit=False, class_=AsyncSession
)


async def get_database():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
