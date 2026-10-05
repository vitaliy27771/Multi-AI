from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, Message
from loguru import logger

from config import settings
from database.crud import get_user, increment_requests, reset_daily_limit_if_needed
from database.session import async_session
from keyboards.main_menu import back_to_menu_kb, cancel_kb
from services.tts_service import TTSError, synthesize_speech
from states.states import TTSStates
from utils.texts import limit_exceeded_text

router = Router(name='tts')
MAX_TTS_CHARS = 3000


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


@router.message(F.text == '🔊 Озвучка текста')
async def tts_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(TTSStates.waiting_for_text)
    await message.answer('🔊 <b>Озвучка</b>\n\nПришли текст.', reply_markup=cancel_kb())


@router.message(TTSStates.waiting_for_text, F.text)
async def tts_process(message: Message, state: FSMContext) -> None:
    text = (message.text or '').strip()
    if not text:
        await message.answer('✏️ Пришли текст.')
        return
    if len(text) > MAX_TTS_CHARS:
        text = text[:MAX_TTS_CHARS]
    if not await _check_and_consume_limit(message):
        await state.clear()
        return
    await state.clear()
    wait_msg = await message.answer('🎙 Синтезирую…')
    try:
        audio = await synthesize_speech(text)
    except TTSError as e:
        logger.error(f'TTS: {e}')
        try:
            await wait_msg.delete()
        except Exception:
            pass
        await message.answer('😔 Не удалось озвучить.', reply_markup=back_to_menu_kb())
        return
    try:
        await wait_msg.delete()
    except Exception:
        pass
    voice = BufferedInputFile(audio, filename='voice.mp3')
    await message.answer_voice(voice, caption='🔊 Готово!')
    await message.answer('Что-нибудь ещё?', reply_markup=back_to_menu_kb())


@router.message(TTSStates.waiting_for_text)
async def tts_wrong_input(message: Message) -> None:
    await message.answer('✏️ Текст сообщением.')
