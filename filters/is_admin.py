from aiogram.filters import BaseFilter
from aiogram.types import Message
from aiogram import Bot

from db.users_table_usage import is_user_admin_


class IsAdminFilter(BaseFilter):
    async def __call__(self, message: Message, bot: Bot):
        return await is_user_admin_(message.from_user.id)