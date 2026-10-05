from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from loguru import logger

from config import settings
from database.crud import get_user, increment_requests, reset_daily_limit_if_needed
from database.session import async_session
from keyboards.main_menu import back_to_menu_kb, cancel_kb
from services.gemini_client import GeminiError, generate_text_gemini
from services.groq_client import GroqError, generate_text_groq
from states.states import AIChatStates
from utils.texts import limit_exceeded_text

router = Router(name='ai_chat')

HISTORY_LIMIT = 10  # последних сообщений


async def _check_and_consume_limit(message: Message) -> bool:
    async with async_session() as session:
        db_user = await get_user(session, message.from_user.id)
        if db_user is None:
            return True
        db_user = await reset_daily_limit_if_needed(session, db_user)
        if not db_user.is_premium and db_user.requests_today >= settings.free_daily_limit:
            await message.answer(limit_exceeded_text(settings.free_daily_limit))
            return False
    await increment_requests(message.from_user.id)
    return True


@router.message(F.text == '\U0001f4ac \u0427\u0430\u0442 \u0441 \u0418\u0418')
async def chat_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(AIChatStates.chatting)
    await state.update_data(history=[])
    text = (
        '\U0001f4ac <b>\u0427\u0430\u0442 \u0441 \u0418\u0418</b>\n\n'
        '\u041f\u0438\u0448\u0438 \u043b\u044e\u0431\u043e\u0435 \u0441\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u0435 \u2014 \u044f \u043e\u0442\u0432\u0435\u0447\u0443. '
        '\u041a\u043e\u043d\u0442\u0435\u043a\u0441\u0442 \u043f\u043e\u0441\u043b\u0435\u0434\u043d\u0438\u0445 10 \u0441\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u0439 \u0441\u043e\u0445\u0440\u0430\u043d\u044f\u0435\u0442\u0441\u044f.\n\n'
        '\u0412\u044b\u0439\u0442\u0438 \u2014 \u043a\u043d\u043e\u043f\u043a\u0430 \u00ab\U0001f3e0 \u0412 \u043c\u0435\u043d\u044e\u00bb \u0438\u043b\u0438 /start.'
    )
    await message.answer(text, reply_markup=cancel_kb())


@router.message(AIChatStates.chatting, F.text)
async def chat_process(message: Message, state: FSMContext) -> None:
    prompt = (message.text or '').strip()
    if not prompt:
        return
    if prompt in ('/start', '/menu'):
        await state.clear()
        return

    if not await _check_and_consume_limit(message):
        await state.clear()
        return

    data = await state.get_data()
    history = data.get('history', [])
    history.append({'role': 'user', 'content': prompt})
    # Обрезаем историю
    if len(history) > HISTORY_LIMIT:
        history = history[-HISTORY_LIMIT:]

    wait_msg = await message.answer('\U0001f4ad \u0414\u0443\u043c\u0430\u044e\u2026')

    answer = None
    # Собираем диалог в один промпт для Groq/Gemini
    context_text = '\n'.join(
        ('\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c: ' if m['role'] == 'user' else '\u0410\u0441\u0441\u0438\u0441\u0442\u0435\u043d\u0442: ') + m['content']
        for m in history
    )

    try:
        answer = await generate_text_groq(context_text)
    except GroqError as e:
        logger.warning(f'Groq chat failed: {e}')
        try:
            answer = await generate_text_gemini(context_text)
        except GeminiError as e2:
            logger.error(f'Gemini chat also failed: {e2}')

    try:
        await wait_msg.delete()
    except Exception:
        pass

    if not answer:
        await message.answer(
            '\U0001f614 \u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u043e\u0442\u0432\u0435\u0442\u0438\u0442\u044c. \u041f\u043e\u043f\u0440\u043e\u0431\u0443\u0439 \u0435\u0449\u0451 \u0440\u0430\u0437.',
            reply_markup=cancel_kb(),
        )
        return

    history.append({'role': 'assistant', 'content': answer})
    if len(history) > HISTORY_LIMIT:
        history = history[-HISTORY_LIMIT:]
    await state.update_data(history=history)

    # Разбиваем длинный ответ
    for i in range(0, len(answer), 3800):
        chunk = answer[i:i + 3800]
        try:
            await message.answer(chunk)
        except Exception:
            await message.answer(chunk, parse_mode=None)

    await message.answer('\U0001f4ac \u041f\u0440\u043e\u0434\u043e\u043b\u0436\u0430\u0439 \u0438\u043b\u0438 \u043d\u0430\u0436\u043c\u0438 \u00ab\U0001f3e0 \u0412 \u043c\u0435\u043d\u044e\u00bb.', reply_markup=cancel_kb())


@router.message(AIChatStates.chatting)
async def chat_wrong_input(message: Message) -> None:
    await message.answer('\u270f\ufe0f \u041d\u0443\u0436\u043d\u043e \u0442\u0435\u043a\u0441\u0442\u043e\u0432\u043e\u0435 \u0441\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u0435.')
