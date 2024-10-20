import asyncio
import logging

from aiogram import Bot, Dispatcher

from fsm import general_states
from configs import token
import handlers.hl_general.root
import handlers.hl_admin.root

from utils.queue_maker import timer


async def main():

    bot = Bot(token=token)
    dp = Dispatcher(storage=general_states.storage)

    dp.include_routers(handlers.hl_admin.root.hl_admin_main_router, handlers.hl_general.root.hl_general_main_router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


async def parse_processes():
    try:
        async with asyncio.TaskGroup() as tg:
            bot_task = tg.create_task(main())
            timer_task = tg.create_task(timer())

    except* Exception as e:
        logging.error(f"An error occurred: {e}")

    if bot_task.done() and timer_task.done():
        logging.info(f"Async tasks have completed now: {bot_task.result()}, {timer_task.result()}")
    else:
        logging.warning("One or more tasks did not complete successfully.")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(parse_processes())
    except KeyboardInterrupt:
        logging.error('Interrupted')