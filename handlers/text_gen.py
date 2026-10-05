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
from states.states import TextGenStates
from utils.texts import limit_exceeded_text

router = Router(name='text_gen')
TG_LIMIT = 4000


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


@router.message(F.text == '📝 Генерация текста')
async def text_gen_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(TextGenStates.waiting_for_prompt)
    await message.answer('📝 <b>Генерация текста</b>\n\nНапиши запрос.', reply_markup=cancel_kb())


@router.message(TextGenStates.waiting_for_prompt, F.text)
async def text_gen_process(message: Message, state: FSMContext) -> None:
    prompt = (message.text or '').strip()
    if not prompt:
        await message.answer('✏️ Пришли запрос.')
        return
    if not await _check_and_consume_limit(message):
        await state.clear()
        return
    await state.clear()
    wait_msg = await message.answer('✍️ Думаю…')
    answer = None
    try:
        answer = await generate_text_groq(prompt)
    except GroqError:
        try:
            answer = await generate_text_gemini(prompt)
        except GeminiError:
            pass
    try:
        await wait_msg.delete()
    except Exception:
        pass
    if not answer:
        await message.answer('😔 Не удалось.', reply_markup=back_to_menu_kb())
        return
    for i in range(0, len(answer), TG_LIMIT):
        await message.answer(answer[i:i + TG_LIMIT])
    await message.answer('✅ Готово.', reply_markup=back_to_menu_kb())


@router.message(TextGenStates.waiting_for_prompt)
async def text_gen_wrong_input(message: Message) -> None:
    await message.answer('✏️ Нужен текст.')
