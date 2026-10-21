from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config.settings import settings
from app.logging import get_logger

logger = get_logger("database")

engine: AsyncEngine | None = None
async_session_factory: async_sessionmaker[AsyncSession] | None = None


async def init_db() -> None:
    global engine, async_session_factory

    db_url = settings.database_url
    logger.info("database_connecting", url=db_url.split("@")[-1])

    engine = create_async_engine(
        db_url,
        echo=False,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
    )

    async_session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    logger.info("database_connected")


async def close_db() -> None:
    global engine, async_session_factory

    if engine:
        logger.info("database_disconnecting")
        await engine.dispose()
        engine = None
        async_session_factory = None
        logger.info("database_disconnected")


async def get_db() -> AsyncSession:
    if async_session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
