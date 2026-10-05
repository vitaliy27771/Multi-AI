import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from loguru import logger

from config import settings
from database import init_db
from handlers import (
    admin,
    ai_chat,
    image_gen,
    payments,
    start,
    stt,
    text_gen,
    tts,
)

from middlewares.limits import LimitsMiddleware
from middlewares.throttling import ThrottlingMiddleware


def setup_logging() -> None:
    logger.remove()
    logger.add(
        sink=lambda msg: print(msg, end=""),
        level=settings.log_level,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> — "
        "<level>{message}</level>",
    )
    logger.add(
        "logs/bot.log",
        rotation="10 MB",
        retention="7 days",
        level=settings.log_level,
        encoding="utf-8",
        enqueue=True,
    )


async def main() -> None:
    setup_logging()
    logger.info("Starting Neuro Aggregator Bot...")

    await init_db()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Middlewares (порядок важен: сначала throttling, потом limits)
    dp.message.middleware(ThrottlingMiddleware(rate_limit=3.0))
    dp.message.middleware(LimitsMiddleware())
    dp.callback_query.middleware(ThrottlingMiddleware(rate_limit=3.0))

        # Routers — ВАЖНО: start с catch-all @router.message() подключается ПОСЛЕДНИМ
    dp.include_router(payments.router)
    dp.include_router(image_gen.router)
    dp.include_router(text_gen.router)
    dp.include_router(tts.router)
    dp.include_router(stt.router)
    dp.include_router(ai_chat.router)
    dp.include_router(admin.router)
    dp.include_router(start.router)   # ← последним, из-за fallback

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.warning("Bot stopped by user.")