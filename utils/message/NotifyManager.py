import asyncio

from utils.status_codes import StatusCode as sc
from db.users_table_usage import notify_user_, notify_user_if_news_turned_on_, notify_admins_
from utils.message.Message import Message


class NotifyManager:
    messages: list[Message] = []

    @staticmethod
    async def send_messages():
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
                    status_code = await notify_user_if_news_turned_on_(user_id, text)
                else:
                    status_code = await notify_user_(user_id, text)

                if status_code != sc.USER_NOTIFY_SUCCESSFULLY:
                    await notify_admins_(f'Error. Function: send_messages(): user_id: {user_id}, text: {text}!')

            await asyncio.sleep(1)

    @staticmethod
    async def add_message(message: Message):
        NotifyManager.messages.append(message)