from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery
from loguru import logger

from config import settings
from database.crud import add_payment, get_user, grant_premium
from database.session import async_session
from keyboards.main_menu import back_to_menu_kb, main_menu_kb
from utils.texts import PREMIUM_ALREADY_TEXT, premium_info_text

router = Router(name='payments')


@router.message(Command('buy'))
@router.callback_query(F.data == 'buy_premium')
async def buy_premium(event):
    user = event.from_user
    async with async_session() as session:
        db_user = await get_user(session, user.id)
    if db_user and db_user.is_premium:
        if isinstance(event, CallbackQuery):
            await event.message.answer(PREMIUM_ALREADY_TEXT)
            await event.answer()
        else:
            await event.answer(PREMIUM_ALREADY_TEXT)
        return
    prices = [LabeledPrice(label='Premium', amount=settings.premium_price_stars)]
    payload = f'premium_{user.id}_{int(datetime.utcnow().timestamp())}'
    await event.bot.send_invoice(
        chat_id=user.id,
        title='💎 Premium',
        description=f'Безлимит на {settings.premium_days} дней за {settings.premium_price_stars} ⭐',
        payload=payload,
        provider_token='',
        currency='XTR',
        prices=prices,
        start_parameter='premium',
    )
    if isinstance(event, CallbackQuery):
        await event.answer()


@router.pre_checkout_query()
async def pre_checkout_handler(query: PreCheckoutQuery) -> None:
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message) -> None:
    sp = message.successful_payment
    user_id = message.from_user.id
    logger.success(f'Payment: user={user_id}, amount={sp.total_amount}')
    await add_payment(user_id=user_id, amount_stars=sp.total_amount, days=settings.premium_days, charge_id=sp.telegram_payment_charge_id)
    updated = await grant_premium(user_id, settings.premium_days)
    text = f'🎉 Оплата получена! Premium на {settings.premium_days} дней.'
    if updated:
        text += f'\n📅 До: {updated.premium_until:%d.%m.%Y %H:%M} UTC'
    await message.answer(text)
    await message.answer('🚀 Готово!', reply_markup=main_menu_kb(is_admin=user_id in settings.admin_ids))


@router.callback_query(F.data == 'premium_info')
async def premium_info_cb(callback: CallbackQuery) -> None:
    async with async_session() as session:
        db_user = await get_user(session, callback.from_user.id)
    if db_user and db_user.is_premium:
        await callback.message.edit_text(premium_info_text(f'{db_user.premium_until:%d.%m.%Y %H:%M} UTC'), reply_markup=back_to_menu_kb())
    else:
        from keyboards.main_menu import premium_kb
        await callback.message.edit_text(premium_info_text(), reply_markup=premium_kb())
    await callback.answer()
