from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, Message
from loguru import logger

from config import settings
from database.crud import get_user, increment_requests, reset_daily_limit_if_needed
from database.session import async_session
from keyboards.main_menu import back_to_menu_kb, cancel_kb
from services.pollinations import ImageGenError, generate_image
from states.states import ImageGenStates
from utils.texts import limit_exceeded_text

router = Router(name='image_gen')


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


@router.message(F.text == '🖼 Генерация картинок')
async def image_gen_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(ImageGenStates.waiting_for_prompt)
    await message.answer(
        '🖼 <b>Генерация картинок</b>\n\n'
        'Опиши, что хочешь увидеть. Пиши подробно.\n\n'
        '<i>Пример: «жёлтый банан на белом фоне, фотореализм, крупный план»</i>',
        reply_markup=cancel_kb(),
    )


@router.message(ImageGenStates.waiting_for_prompt, F.text)
async def image_gen_process(message: Message, state: FSMContext) -> None:
    prompt = (message.text or '').strip()
    logger.info(f'Image prompt: {prompt!r}')
    if not prompt:
        await message.answer('✏️ Пришли описание.')
        return
    if len(prompt) > 500:
        prompt = prompt[:500]
    if not await _check_and_consume_limit(message):
        await state.clear()
        return
    await state.clear()
    wait_msg = await message.answer('🎨 Рисую… (до 60 сек)')
    image_bytes = None
    error_msg = ''
    try:
        image_bytes = await generate_image(prompt)
    except ImageGenError as e:
        error_msg = str(e)
        logger.error(f'Image error: {e}')
    except Exception as e:
        error_msg = f'network: {e}'
        logger.exception(f'Image unexpected: {e}')
    try:
        await wait_msg.delete()
    except Exception:
        pass
    if image_bytes is None:
        await message.answer(
            '😔 <b>Не удалось сгенерировать.</b>\n'
            f'<i>{error_msg[:300]}</i>',
            reply_markup=back_to_menu_kb(),
        )
        return
    photo = BufferedInputFile(image_bytes, filename='image.png')
    await message.answer_photo(
        photo,
        caption=f'🖼 Готово! Запрос: {prompt[:200]}',
        reply_markup=back_to_menu_kb(),
    )


@router.message(ImageGenStates.waiting_for_prompt)
async def image_gen_wrong_input(message: Message) -> None:
    await message.answer('✏️ Нужно текстовое описание.')
