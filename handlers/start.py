from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger

from config import settings
from database.crud import create_or_update_user, get_user, reset_daily_limit_if_needed
from database.session import async_session
from keyboards.main_menu import back_to_menu_kb, main_menu_kb, premium_kb
from utils.texts import HELP_TEXT, WELCOME_TEXT, premium_info_text

router = Router(name='start')


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await create_or_update_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    is_admin = message.from_user.id in settings.admin_ids
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_kb(is_admin=is_admin))


@router.message(Command('help'))
@router.message(F.text == 'ℹ️ Помощь')
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT)


@router.message(Command('profile'))
@router.message(F.text == '👤 Мой профиль')
async def cmd_profile(message: Message) -> None:
    async with async_session() as session:
        db_user = await get_user(session, message.from_user.id)
        if db_user is None:
            db_user = await create_or_update_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
        db_user = await reset_daily_limit_if_needed(session, db_user)
    if db_user.is_premium:
        status = f'💎 Premium до {db_user.premium_until:%d.%m.%Y %H:%M} UTC'
        left = '∞'
    else:
        status = '🆓 Бесплатный'
        left = f'{max(0, settings.free_daily_limit - db_user.requests_today)} / {settings.free_daily_limit}'
    text = f'👤 <b>Профиль</b>\n\nID: <code>{db_user.id}</code>\nСтатус: {status}\nЗапросов сегодня: {left}'
    if not db_user.is_premium:
        await message.answer(text, reply_markup=premium_kb())
    else:
        await message.answer(text, reply_markup=back_to_menu_kb())


@router.callback_query(F.data == 'back_to_menu')
async def back_to_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    is_admin = callback.from_user.id in settings.admin_ids
    await callback.message.answer('🏠 Главное меню', reply_markup=main_menu_kb(is_admin=is_admin))
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data == 'cancel')
async def cancel_action(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text('❌ Отменено.')
    await callback.answer()


@router.message(F.text == '💎 Купить Premium')
async def buy_premium_button(message: Message) -> None:
    async with async_session() as session:
        db_user = await get_user(session, message.from_user.id)
    if db_user and db_user.is_premium:
        await message.answer(premium_info_text(f'{db_user.premium_until:%d.%m.%Y %H:%M} UTC'))
        return
    await message.answer(premium_info_text(), reply_markup=premium_kb())


@router.message(F.text == '🛠 Админ-панель')
async def admin_panel_button(message: Message) -> None:
    if message.from_user.id not in settings.admin_ids:
        await message.answer('⛔ Нет доступа.')
        return
    await message.answer('🛠 <b>Админ-панель</b>\n\n/stats\n/broadcast <текст>\n/give <id> <days>', reply_markup=back_to_menu_kb())


@router.message()
async def fallback(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    if current is not None:
        return
    logger.debug(f'Fallback from {message.from_user.id}: {message.text}')
    await message.answer('🤔 Не понял команду.', reply_markup=main_menu_kb(is_admin=message.from_user.id in settings.admin_ids))
