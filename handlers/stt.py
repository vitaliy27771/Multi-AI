from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from loguru import logger

from config import settings
from database.crud import get_user, increment_requests, reset_daily_limit_if_needed
from database.session import async_session
from keyboards.main_menu import back_to_menu_kb, cancel_kb
from services.stt_service import transcribe_audio
from states.states import STTStates
from utils.texts import limit_exceeded_text

router = Router(name='stt')


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


@router.message(F.text == '🎤 Распознавание голоса')
async def stt_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(STTStates.waiting_for_voice)
    await message.answer('🎤 <b>Распознавание</b>\n\nОтправь голосовое.', reply_markup=cancel_kb())


@router.message(STTStates.waiting_for_voice, F.voice | F.audio)
async def stt_process(message: Message, state: FSMContext) -> None:
    if not await _check_and_consume_limit(message):
        await state.clear()
        return
    await state.clear()
    wait_msg = await message.answer('🧠 Распознаю…')
    try:
        if message.voice:
            file_id = message.voice.file_id
            filename = 'voice.ogg'
        else:
            file_id = message.audio.file_id
            filename = message.audio.file_name or 'audio.mp3'
        tg_file = await message.bot.get_file(file_id)
        file_bytes_io = await message.bot.download_file(tg_file.file_path)
        audio_bytes = file_bytes_io.read()
        text = await transcribe_audio(audio_bytes, filename=filename)
    except Exception as e:
        logger.exception(f'STT: {e}')
        try:
            await wait_msg.delete()
        except Exception:
            pass
        await message.answer('😔 Не удалось распознать.', reply_markup=back_to_menu_kb())
        return
    try:
        await wait_msg.delete()
    except Exception:
        pass
    if not text.strip():
        await message.answer('🤷 Ничего не распознано.', reply_markup=back_to_menu_kb())
        return
    answer = f'📝 <b>Текст:</b>\n\n{text}'
    for i in range(0, len(answer), 4000):
        await message.answer(answer[i:i + 4000])
    await message.answer('Что-нибудь ещё?', reply_markup=back_to_menu_kb())


@router.message(STTStates.waiting_for_voice)
async def stt_wrong_input(message: Message) -> None:
    await message.answer('🎤 Голосовое или аудио.')
