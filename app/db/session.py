from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from collections.abc import AsyncGenerator

DATABASE_URL = "postgresql+asyncpg://app:app@localhost:5432/appdb"

engine = create_async_engine(DATABASE_URL, echo=False, pool_size=10, max_overflow=20)

# session factory; expire_on_commit=False keeps objects usable after commit
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()          # commit if the request succeeded
        except Exception:
            await session.rollback()         # rollback on any error
            raise
        finally:
            await session.close()
