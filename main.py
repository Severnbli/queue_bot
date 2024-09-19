import asyncio
import logging
from aiogram import Bot, Dispatcher

from fsm import general_states
from configs import token
import handlers.hl_general.root
import handlers.hl_admin.root

from queue_maker import timer


async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=token)
    dp = Dispatcher(storage=general_states.storage)

    dp.include_routers(handlers.hl_admin.root.hl_admin_main_router, handlers.hl_general.root.hl_general_main_router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


async def parse_processes():
    await asyncio.gather(main(), timer())


if __name__ == '__main__':
    try:
        asyncio.run(parse_processes())
    except KeyboardInterrupt:
        print('Interrupted')