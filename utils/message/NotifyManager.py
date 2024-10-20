import asyncio

from utils.status_codes import StatusCode as sc
from db.users_table_usage import simple_get_status_of_news, get_admins_ids, get_all_ids_
from utils.message.Message import Message
import aiohttp
from configs import token


class NotifyManager:
    messages: list[Message] = []

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

                    affected_users_id.append(message.get_user_id())

                if quantity_of_messages == 30:
                    break

            affected_users_id.clear()

            for message in messages_to_be_sent:
                user_id = message.get_user_id()
                text = message.get_text()
                is_check_news = message.is_check_news()

                if is_check_news:
                    status_code = await NotifyManager.notify_user_if_news_turned_on_(user_id, text)
                else:
                    status_code = await NotifyManager.notify_user_(user_id, text)

                if status_code != sc.USER_NOTIFY_SUCCESSFULLY:
                    await NotifyManager.notify_admins(f'Error. Function: send_messages(): '
                                                      f'user_id: {user_id}, text: {text}!')

            await asyncio.sleep(1)

    @staticmethod
    async def add_message(message: Message) -> None:
        NotifyManager.messages.append(message)

    @staticmethod
    async def notify_user_(user_id: int, text: str) -> int:
        async with aiohttp.ClientSession() as session:
            url_to_send_message = f'https://api.telegram.org/bot{token}/sendMessage'

            async with session.post(url=f'{url_to_send_message}?chat_id={user_id}&text={text}') as response:
                if response.status != 200:
                    return sc.USER_NOTIFY_ERROR

        return sc.USER_NOTIFY_SUCCESSFULLY

    @staticmethod
    async def notify_user_if_news_turned_on_(user_id: int, text: str) -> int:
        status_code, is_news = await simple_get_status_of_news(user_id)

        if status_code == sc.OPERATION_SUCCESS and is_news:
            return await NotifyManager.notify_user_(user_id, text)

        return status_code

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