import os
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from loguru import logger

from config import settings
from database.models import Base


# Создаём папку для БД, если её нет (актуально для Railway Volume)
def _ensure_db_dir() -> None:
    url = settings.sqlalchemy_url
    if url.startswith("sqlite"):
        # Ищем путь: sqlite+aiosqlite:///path или sqlite+aiosqlite:////path
        if ":///" in url:
            path = url.split(":///", 1)[1]
            if path and path != ":memory:":
                # Если путь абсолютный (начинается с /), удаляем первый слэш
                if path.startswith("/"):
                    path = path
                else:
                    path = path
                db_dir = os.path.dirname(path)
                if db_dir and not os.path.exists(db_dir):
                    try:
                        Path(db_dir).mkdir(parents=True, exist_ok=True)
                        logger.info(f"Created DB directory: {db_dir}")
                    except Exception as e:
                        logger.warning(f"Cannot create DB dir {db_dir}: {e}")


_ensure_db_dir()

engine = create_async_engine(
    settings.sqlalchemy_url,
    echo=False,
    future=True,
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info(f"Database initialized: {settings.sqlalchemy_url}")