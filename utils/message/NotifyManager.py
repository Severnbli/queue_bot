import asyncio
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from utils.status_codes import StatusCode as sc, get_message_about_status_code
from db.users_table_usage import simple_get_status_of_news, get_admins_ids, get_all_ids_
from utils.message.Message import Message


class NotifyManager:
    messages: list[Message] = []
    bot: Bot = None

    @staticmethod
    async def send_messages() -> None:
        while True:
            affected_users_id: list[int] = []

            messages_to_be_sent: list[Message] = []

            quantity_of_messages: int = 0

            for message in NotifyManager.messages:
                if message.get_user_id() not in affected_users_id:
                    quantity_of_messages += 1

                    messages_to_be_sent.append(message)
                    NotifyManager.messages.remove(message)

                    affected_users_id.append(await message.get_user_id())

                if quantity_of_messages == 30:
                    break

            affected_users_id.clear()

            for message in messages_to_be_sent:
                status_code = await NotifyManager.notify_user_(message)

                if status_code != sc.OPERATION_SUCCESS:
                    await NotifyManager.notify_admins(f'Error. Function: send_messages(): '
                                                      f'user_id: {await message.get_user_id()}, '
                                                      f'text: {await message.get_text()}!\n\n'
                                                      f'Error: {await get_message_about_status_code(status_code)}.')

            await asyncio.sleep(1)

    @staticmethod
    async def add_message(message: Message) -> None:
        NotifyManager.messages.append(message)

    @staticmethod
    async def notify_user_(message: Message) -> int:
        if message.is_check_news():
            status_code, is_news = await simple_get_status_of_news(await message.get_user_id())

            if status_code != sc.OPERATION_SUCCESS:
                return status_code

            if not is_news:
                return sc.OPERATION_SUCCESS

        try:
            await NotifyManager.bot.send_message(
                chat_id=await message.get_user_id(),
                text=await message.get_text(),
                parse_mode='HTML',
                reply_markup=await message.get_markup()
            )
        except TelegramAPIError | Exception:
            return sc.USER_NOTIFY_ERROR

        return sc.OPERATION_SUCCESS

    @staticmethod
    async def notify_admins(text: str) -> None:
        admins_ids = await get_admins_ids()

        for admin_id in admins_ids:
            await NotifyManager.add_message(
                Message(
                    user_id=admin_id,
                    text=text,
                    is_check_news=False
                )
            )

    @staticmethod
    async def notify_all(text: str) -> None:
        user_ids = await get_all_ids_()

        for user_id in user_ids:
            await NotifyManager.add_message(
                Message(
                    user_id=user_id,
                    text=text,
                    is_check_news=True
                )
            )