from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from config import settings
from database.crud import (
    create_or_update_user,
    get_user,
    reset_daily_limit_if_needed,
)
from database.session import async_session
from keyboards.main_menu import premium_kb
from utils.texts import limit_exceeded_text


class LimitsMiddleware(BaseMiddleware):
    """
    Проверяет и обновляет лимиты для запросов, требующих AI-сервисов.
    Пропускает команды, /start, навигацию, оплату.
    """

    SKIP_COMMANDS = {"/start", "/help", "/profile", "/buy", "/stats", "/broadcast", "/give"}
    SKIP_TEXTS_PREFIX = (
        "💎", "👤", "ℹ️", "🛠", "🖼", "📝", "🔊", "🎤", "🎬",
    )

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        user = data.get("event_from_user")
        if user is None:
            return await handler(event, data)

        text = event.text or ""

        # Пропускаем команды и навигацию
        if text.startswith("/"):
            cmd = text.split()[0].split("@")[0].lower()
            if cmd in self.SKIP_COMMANDS:
                return await handler(event, data)

        # Пропускаем сообщения, начинающиеся с эмодзи меню (навигация)
        # (когда пользователь только что нажал кнопку, middleware лимитов не должна блокировать,
        #  так как это не AI-запрос. Блокировка происходит при самом вызове API в хендлере.)
        # Но т.к. лимит проверяется в хендлере перед вызовом API — здесь мы только
        # обновляем данные пользователя в data, не расходуя лимит.
        async with async_session() as session:
            db_user = await get_user(session, user.id)
            if db_user is None:
                db_user = await create_or_update_user(
                    user.id, user.username, user.full_name
                )
            db_user = await reset_daily_limit_if_needed(session, db_user)
            data["db_user"] = db_user

        # Проверка лимита — только для сообщений, которые не являются навигацией/командой
        if text and not text.startswith("/") and not any(text.startswith(p) for p in self.SKIP_TEXTS_PREFIX):
            if not db_user.is_premium and db_user.requests_today >= settings.free_daily_limit:
                await event.answer(
                    limit_exceeded_text(settings.free_daily_limit),
                    reply_markup=premium_kb(),
                )
                return None

        return await handler(event, data)