from config import settings

WELCOME_TEXT = (
    "👋 <b>Привет!</b>\n\n"
    "Я — <b>агрегатор бесплатных нейросетей</b>. Через меня ты можешь:\n\n"
    "🖼 Генерировать картинки\n"
    "📝 Писать тексты\n"
    "🔊 Озвучивать текст\n"
    "🎤 Распознавать голос\n"
    "🎬 Делать выжимку из YouTube\n\n"
    f"🎁 Бесплатно: <b>{settings.free_daily_limit} запросов в день</b>\n"
    f"💎 Premium: <b>безлимит</b> за {settings.premium_price_stars} ⭐ на {settings.premium_days} дней\n\n"
    "Выбери действие в меню 👇"
)

HELP_TEXT = (
    "ℹ️ <b>Помощь</b>\n\n"
    "<b>Как пользоваться:</b>\n"
    "1. Нажми на нужную кнопку в меню\n"
    "2. Отправь запрос (текст, голосовое или ссылку)\n"
    "3. Получи результат\n\n"
    "<b>Лимиты:</b>\n"
    f"• Бесплатно — {settings.free_daily_limit} запросов в сутки\n"
    "• Premium — безлимит на 30 дней\n\n"
    "<b>Команды:</b>\n"
    "/start — главное меню\n"
    "/profile — профиль\n"
    "/buy — купить Premium\n"
    "/help — эта справка"
)

PREMIUM_ALREADY_TEXT = "💎 У тебя уже активен <b>Premium</b>. Наслаждайся безлимитом!"

PREMIUM_SUCCESS_TEXT = (
    "🎉 <b>Оплата получена!</b>\n\n"
    "Тебе активирован <b>Premium</b> на {days} дней.\n"
    "Теперь у тебя <b>безлимитный</b> доступ ко всем сервисам!"
)


def premium_info_text(premium_until: str | None = None) -> str:
    base = (
        "💎 <b>Premium</b>\n\n"
        f"• Безлимит на все сервисы\n"
        f"• Срок: {settings.premium_days} дней\n"
        f"• Цена: {settings.premium_price_stars} ⭐ (Telegram Stars)\n\n"
    )
    if premium_until:
        base += f"📅 Активен до: <b>{premium_until}</b>"
    else:
        base += "Нажми кнопку ниже, чтобы оплатить 👇"
    return base


def limit_exceeded_text(limit: int) -> str:
    return (
        "🚫 <b>Лимит исчерпан</b>\n\n"
        f"Ты использовал все <b>{limit}</b> бесплатных запросов на сегодня.\n\n"
        "💎 Оформи <b>Premium</b> — и получи безлимит на 30 дней.\n"
        "Или подожди до следующего сброса лимита (раз в 24 часа)."
    )