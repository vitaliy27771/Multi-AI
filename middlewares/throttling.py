import time
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, User


class ThrottlingMiddleware(BaseMiddleware):
    """Не больше 1 действия в rate_limit секунд на пользователя."""

    def __init__(self, rate_limit: float = 3.0) -> None:
        self.rate_limit = rate_limit
        self._cache: dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user: User | None = data.get("event_from_user")
        if user is None:
            return await handler(event, data)

        # не троттлим админов
        from config import settings
        if user.id in settings.admin_ids:
            return await handler(event, data)

        now = time.monotonic()
        last = self._cache.get(user.id, 0.0)
        if now - last < self.rate_limit:
            wait = self.rate_limit - (now - last)
            if isinstance(event, Message):
                await event.answer(
                    f"⏳ Слишком быстро. Подожди {wait:.1f} сек."
                )
            elif isinstance(event, CallbackQuery):
                await event.answer(
                    f"⏳ Подожди {wait:.1f} сек.", show_alert=False
                )
            return None

        self._cache[user.id] = now
        return await handler(event, data)