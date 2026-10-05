import asyncio

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from loguru import logger

from config import settings
from database.crud import (
    get_premium_users,
    get_stats,
    get_user_full_info,
    get_users_for_broadcast,
    grant_premium,
    revoke_premium,
)
from keyboards.admin_kb import admin_panel_kb
from keyboards.main_menu import back_to_menu_kb

router = Router(name='admin')


def _is_admin(user_id: int) -> bool:
    return int(user_id) in [int(x) for x in settings.admin_ids]


async def _deny(message):
    await message.answer('\u26d4 \u041a\u043e\u043c\u0430\u043d\u0434\u0430 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u0430.', parse_mode=None)


# ============ КОМАНДЫ ============


@router.message(Command('stats'))
async def cmd_stats(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        return await _deny(message)
    stats = await get_stats()
    text = '\U0001f4ca \u0421\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u043a\u0430\n\n'
    text += '\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u0435\u0439: ' + str(stats['total_users']) + '\n'
    text += 'Premium: ' + str(stats['premium_users']) + '\n'
    text += '\u0417\u0430\u043f\u0440\u043e\u0441\u043e\u0432: ' + str(stats['total_requests']) + '\n'
    text += '\u041f\u043b\u0430\u0442\u0435\u0436\u0435\u0439: ' + str(stats['total_payments']) + '\n'
    text += 'Stars: ' + str(stats['stars_earned'])
    await message.answer(text, parse_mode=None, reply_markup=admin_panel_kb())


@router.message(Command('give'))
async def cmd_give(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        return await _deny(message)
    parts = (message.text or '').split()
    if len(parts) != 3:
        await message.answer('\u26a0\ufe0f \u0418\u0441\u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u043d\u0438\u0435: /give user_id days', parse_mode=None)
        return
    try:
        target_id = int(parts[1])
        days = int(parts[2])
        if days <= 0 or days > 3650:
            raise ValueError('range')
    except ValueError:
        await message.answer('\u26a0\ufe0f \u041d\u0435\u0432\u0435\u0440\u043d\u044b\u0435 \u0430\u0440\u0433\u0443\u043c\u0435\u043d\u0442\u044b.', parse_mode=None)
        return
    updated = await grant_premium(target_id, days)
    if updated is None:
        await message.answer('\u274c \u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c ' + str(target_id) + ' \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d.', parse_mode=None)
        return
    await message.answer('\u2705 \u0412\u044b\u0434\u0430\u043d Premium ' + str(target_id) + ' \u043d\u0430 ' + str(days) + ' \u0434\u043d\u0435\u0439.\n\u0414\u043e: ' + str(updated.premium_until), parse_mode=None)
    try:
        await message.bot.send_message(target_id, '\U0001f381 \u0422\u0435\u0431\u0435 \u0432\u044b\u0434\u0430\u043d Premium \u043d\u0430 ' + str(days) + ' \u0434\u043d\u0435\u0439!', parse_mode=None)
    except Exception as e:
        logger.warning(f'Cannot notify {target_id}: {e}')


@router.message(Command('take'))
async def cmd_take(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        return await _deny(message)
    parts = (message.text or '').split()
    if len(parts) != 2:
        await message.answer('\u26a0\ufe0f \u0418\u0441\u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u043d\u0438\u0435: /take user_id', parse_mode=None)
        return
    try:
        target_id = int(parts[1])
    except ValueError:
        await message.answer('\u26a0\ufe0f user_id \u0434\u043e\u043b\u0436\u0435\u043d \u0431\u044b\u0442\u044c \u0447\u0438\u0441\u043b\u043e\u043c.', parse_mode=None)
        return
    ok = await revoke_premium(target_id)
    if not ok:
        await message.answer('\u274c \u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c ' + str(target_id) + ' \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d.', parse_mode=None)
        return
    await message.answer('\u2705 Premium \u0441\u043d\u044f\u0442 \u0441 ' + str(target_id), parse_mode=None)
    try:
        await message.bot.send_message(target_id, '\u2139\ufe0f \u0422\u0432\u043e\u0439 Premium \u0431\u044b\u043b \u043e\u0442\u043e\u0437\u0432\u0430\u043d \u0430\u0434\u043c\u0438\u043d\u0438\u0441\u0442\u0440\u0430\u0442\u043e\u0440\u043e\u043c.', parse_mode=None)
    except Exception as e:
        logger.warning(f'Cannot notify {target_id}: {e}')


@router.message(Command('premium_info'))
async def cmd_premium_info(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        return await _deny(message)
    parts = (message.text or '').split()
    if len(parts) != 2:
        await message.answer('\u26a0\ufe0f \u0418\u0441\u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u043d\u0438\u0435: /premium_info user_id', parse_mode=None)
        return
    try:
        target_id = int(parts[1])
    except ValueError:
        await message.answer('\u26a0\ufe0f user_id \u0434\u043e\u043b\u0436\u0435\u043d \u0431\u044b\u0442\u044c \u0447\u0438\u0441\u043b\u043e\u043c.', parse_mode=None)
        return
    info = await get_user_full_info(target_id)
    if not info:
        await message.answer('\u274c \u041d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d ' + str(target_id), parse_mode=None)
        return
    text = '\U0001f464 \u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044c ' + str(info['id']) + '\n'
    text += 'Username: @' + (info['username'] or '-') + '\n'
    text += '\u0418\u043c\u044f: ' + (info['full_name'] or '-') + '\n'
    text += 'Premium: ' + ('\u2705 \u0434\u0430' if info['is_premium'] else '\u274c \u043d\u0435\u0442') + '\n'
    if info['premium_until']:
        text += '\u0414\u043e: ' + str(info['premium_until']) + '\n'
    text += '\u0417\u0430\u043f\u0440\u043e\u0441\u043e\u0432 \u0441\u0435\u0433\u043e\u0434\u043d\u044f: ' + str(info['requests_today']) + '\n'
    text += '\u0412\u0441\u0435\u0433\u043e: ' + str(info['total_requests'])
    await message.answer(text, parse_mode=None)


@router.message(Command('premium_list'))
async def cmd_premium_list(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        return await _deny(message)
    users = await get_premium_users()
    if not users:
        await message.answer('\U0001f4cb \u041d\u0435\u0442 \u0430\u043a\u0442\u0438\u0432\u043d\u044b\u0445 Premium-\u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u0435\u0439.', parse_mode=None)
        return
    lines = ['\U0001f4cb Premium: ' + str(len(users)) + '\n']
    for u in users:
        uname = '@' + u.username if u.username else str(u.id)
        lines.append(uname + ' \u2014 ' + str(u.premium_until))
    await message.answer('\n'.join(lines), parse_mode=None)


@router.message(Command('reset_user'))
async def cmd_reset_user(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        return await _deny(message)
    parts = (message.text or '').split()
    if len(parts) != 2:
        await message.answer('\u26a0\ufe0f /reset_user user_id', parse_mode=None)
        return
    try:
        target_id = int(parts[1])
    except ValueError:
        await message.answer('\u26a0\ufe0f \u0427\u0438\u0441\u043b\u0430.', parse_mode=None)
        return
    from datetime import datetime
    from sqlalchemy import update
    from database.models import User
    from database.session import async_session
    async with async_session() as session:
        await session.execute(update(User).where(User.id == target_id).values(requests_today=0, last_reset=datetime.utcnow()))
        await session.commit()
    await message.answer('\u2705 \u041b\u0438\u043c\u0438\u0442\u044b ' + str(target_id) + ' \u0441\u0431\u0440\u043e\u0448\u0435\u043d\u044b.', parse_mode=None)


@router.message(Command('broadcast'))
async def cmd_broadcast(message: Message, bot: Bot) -> None:
    if not _is_admin(message.from_user.id):
        return await _deny(message)
    text = (message.text or '').replace('/broadcast', '', 1).strip()
    if not text:
        await message.answer('\u26a0\ufe0f /broadcast \u0442\u0435\u043a\u0441\u0442', parse_mode=None)
        return
    user_ids = await get_users_for_broadcast()
    sent = 0
    failed = 0
    await message.answer('\U0001f4e2 \u0420\u0430\u0441\u0441\u044b\u043b\u043a\u0430 ' + str(len(user_ids)) + '...', parse_mode=None)
    for uid in user_ids:
        try:
            await bot.send_message(uid, text)
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)
    await message.answer('\u2705 \u041e\u0442\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u043e: ' + str(sent) + ', \u043e\u0448\u0438\u0431\u043e\u043a: ' + str(failed), parse_mode=None)


# ============ АДМИН-ПАНЕЛЬ (кнопка) ============


@router.message(F.text == '\U0001f6e0 \u0410\u0434\u043c\u0438\u043d-\u043f\u0430\u043d\u0435\u043b\u044c')
async def admin_panel(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        return await _deny(message)
    text = (
        '\U0001f6e0 \u0410\u0434\u043c\u0438\u043d-\u043f\u0430\u043d\u0435\u043b\u044c\n\n'
        '\u041a\u043e\u043c\u0430\u043d\u0434\u044b:\n'
        '/give user_id days \u2014 \u0432\u044b\u0434\u0430\u0442\u044c Premium\n'
        '/take user_id \u2014 \u0441\u043d\u044f\u0442\u044c Premium\n'
        '/premium_info user_id \u2014 \u0441\u0442\u0430\u0442\u0443\u0441 \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044f\n'
        '/premium_list \u2014 \u0432\u0441\u0435 Premium-\u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u0438\n'
        '/stats \u2014 \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u043a\u0430\n'
        '/broadcast \u0442\u0435\u043a\u0441\u0442 \u2014 \u0440\u0430\u0441\u0441\u044b\u043b\u043a\u0430\n'
    )
    await message.answer(text, parse_mode=None, reply_markup=admin_panel_kb())


# ============ INLINE-КНОПКИ ============


@router.callback_query(F.data == 'adm_stats')
async def cb_stats(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id):
        return await callback.answer('\u26d4 \u041d\u0435\u0442 \u0434\u043e\u0441\u0442\u0443\u043f\u0430.', show_alert=True)
    stats = await get_stats()
    text = '\U0001f4ca \u0421\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u043a\u0430\n\n'
    text += '\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u0435\u0439: ' + str(stats['total_users']) + '\n'
    text += 'Premium: ' + str(stats['premium_users']) + '\n'
    text += '\u0417\u0430\u043f\u0440\u043e\u0441\u043e\u0432: ' + str(stats['total_requests']) + '\n'
    text += '\u041f\u043b\u0430\u0442\u0435\u0436\u0435\u0439: ' + str(stats['total_payments']) + '\n'
    text += 'Stars: ' + str(stats['stars_earned'])
    await callback.message.answer(text, parse_mode=None, reply_markup=admin_panel_kb())
    await callback.answer()


@router.callback_query(F.data == 'adm_prem_list')
async def cb_prem_list(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id):
        return await callback.answer('\u26d4 \u041d\u0435\u0442 \u0434\u043e\u0441\u0442\u0443\u043f\u0430.', show_alert=True)
    users = await get_premium_users()
    if not users:
        await callback.message.answer('\U0001f4cb \u041d\u0435\u0442 \u0430\u043a\u0442\u0438\u0432\u043d\u044b\u0445 Premium-\u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u0435\u0439.', parse_mode=None, reply_markup=admin_panel_kb())
        return await callback.answer()
    lines = ['\U0001f4cb Premium: ' + str(len(users)) + '\n']
    for u in users:
        uname = '@' + u.username if u.username else str(u.id)
        lines.append(uname + ' \u2014 ' + str(u.premium_until))
    await callback.message.answer('\n'.join(lines), parse_mode=None, reply_markup=admin_panel_kb())
    await callback.answer()


@router.callback_query(F.data == 'adm_help')
async def cb_help(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id):
        return await callback.answer('\u26d4 \u041d\u0435\u0442 \u0434\u043e\u0441\u0442\u0443\u043f\u0430.', show_alert=True)
    text = (
        '\u2753 \u041a\u043e\u043c\u0430\u043d\u0434\u044b \u0430\u0434\u043c\u0438\u043d\u0430\n\n'
        '/give user_id days \u2014 \u0432\u044b\u0434\u0430\u0442\u044c Premium \u043d\u0430 N \u0434\u043d\u0435\u0439\n'
        '   \u041f\u0440\u0438\u043c\u0435\u0440: /give 123456789 30\n\n'
        '/take user_id \u2014 \u0441\u043d\u044f\u0442\u044c Premium\n'
        '   \u041f\u0440\u0438\u043c\u0435\u0440: /take 123456789\n\n'
        '/premium_info user_id \u2014 \u0441\u0442\u0430\u0442\u0443\u0441 \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044f\n\n'
        '/premium_list \u2014 \u0441\u043f\u0438\u0441\u043e\u043a \u0432\u0441\u0435\u0445 Premium\n\n'
        '/stats \u2014 \u043e\u0431\u0449\u0430\u044f \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u043a\u0430\n\n'
        '/reset_user user_id \u2014 \u0441\u0431\u0440\u043e\u0441\u0438\u0442\u044c \u0434\u043d\u0435\u0432\u043d\u044b\u0435 \u043b\u0438\u043c\u0438\u0442\u044b\n\n'
        '/broadcast \u0442\u0435\u043a\u0441\u0442 \u2014 \u0440\u0430\u0441\u0441\u044b\u043b\u043a\u0430 \u0432\u0441\u0435\u043c'
    )
    await callback.message.answer(text, parse_mode=None, reply_markup=admin_panel_kb())
    await callback.answer()
