from datetime import datetime, timedelta

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Payment, User
from database.session import async_session


async def get_user(session: AsyncSession, user_id: int) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_or_update_user(
    user_id: int,
    username: str | None = None,
    full_name: str | None = None,
) -> User:
    async with async_session() as session:
        user = await get_user(session, user_id)
        if user is None:
            user = User(id=user_id, username=username, full_name=full_name)
            session.add(user)
        else:
            user.username = username or user.username
            user.full_name = full_name or user.full_name
        await session.commit()
        await session.refresh(user)
        return user


async def reset_daily_limit_if_needed(session: AsyncSession, user: User) -> User:
    now = datetime.utcnow()
    last = user.last_reset.replace(tzinfo=None) if user.last_reset.tzinfo else user.last_reset
    if now - last >= timedelta(hours=24):
        user.requests_today = 0
        user.last_reset = now
        await session.commit()
        await session.refresh(user)
    return user


async def increment_requests(user_id: int) -> None:
    async with async_session() as session:
        await session.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                requests_today=User.requests_today + 1,
                total_requests=User.total_requests + 1,
            )
        )
        await session.commit()


async def grant_premium(user_id: int, days: int) -> User | None:
    async with async_session() as session:
        user = await get_user(session, user_id)
        if user is None:
            return None
        now = datetime.utcnow()
        current = (
            user.premium_until.replace(tzinfo=None)
            if user.premium_until and user.premium_until.tzinfo
            else user.premium_until
        )
        base = current if current and current > now else now
        user.premium_until = base + timedelta(days=days)
        await session.commit()
        await session.refresh(user)
        return user


async def set_premium(user_id: int, until: datetime) -> None:
    async with async_session() as session:
        await session.execute(
            update(User).where(User.id == user_id).values(premium_until=until)
        )
        await session.commit()


async def add_payment(
    user_id: int,
    amount_stars: int,
    days: int,
    charge_id: str | None = None,
) -> Payment:
    async with async_session() as session:
        payment = Payment(
            user_id=user_id,
            amount_stars=amount_stars,
            days=days,
            telegram_payment_charge_id=charge_id,
        )
        session.add(payment)
        await session.commit()
        await session.refresh(payment)
        return payment


async def get_stats() -> dict:
    async with async_session() as session:
        total_users = (await session.execute(select(func.count(User.id)))).scalar_one()
        total_requests = (
            await session.execute(select(func.coalesce(func.sum(User.total_requests), 0)))
        ).scalar_one()
        premium_users = (
            await session.execute(
                select(func.count(User.id)).where(User.premium_until > datetime.utcnow())
            )
        ).scalar_one()
        total_payments = (
            await session.execute(select(func.count(Payment.id)))
        ).scalar_one()
        stars_earned = (
            await session.execute(select(func.coalesce(func.sum(Payment.amount_stars), 0)))
        ).scalar_one()
    return {
        "total_users": int(total_users),
        "total_requests": int(total_requests),
        "premium_users": int(premium_users),
        "total_payments": int(total_payments),
        "stars_earned": int(stars_earned),
    }


async def get_users_for_broadcast() -> list[int]:
    async with async_session() as session:
        result = await session.execute(select(User.id))
        return [row[0] for row in result.all()]

async def revoke_premium(user_id: int) -> bool:
    """Снимает Premium у пользователя. True если снят."""
    from datetime import datetime
    async with async_session() as session:
        user = await get_user(session, user_id)
        if user is None:
            return False
        user.premium_until = None
        await session.commit()
        return True


async def get_premium_users() -> list:
    """Возвращает список активных Premium-пользователей."""
    from datetime import datetime
    from sqlalchemy import select
    async with async_session() as session:
        result = await session.execute(
            select(User)
            .where(User.premium_until.isnot(None))
            .where(User.premium_until > datetime.utcnow())
            .order_by(User.premium_until.desc())
        )
        return list(result.scalars().all())


async def get_user_full_info(user_id: int) -> dict:
    """Полная информация о пользователе для админки."""
    async with async_session() as session:
        user = await get_user(session, user_id)
        if user is None:
            return {}
        return {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "is_premium": user.is_premium,
            "premium_until": user.premium_until,
            "requests_today": user.requests_today,
            "total_requests": user.total_requests,
            "created_at": user.created_at,
        }
