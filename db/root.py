import aiosqlite
import asyncio


async def get_connection():
    connection = await aiosqlite.connect('database_queue_bot.sqlite')
    return connection


async def get_cursor(connection):
    cursor = await connection.cursor()
    return cursor


async def connect_to_db():
    connection = await get_connection()
    cursor = await get_cursor(connection)
    return connection, cursor

conn, cur = asyncio.run(connect_to_db())


async def try_commit() -> bool:
    try:
        await conn.commit()
        return True
    except aiosqlite.DatabaseError as e:
        with open('log.txt', 'a') as log_file:
            import datetime
            log_file.write(f'{str(e)}. Time: {str(datetime.datetime.now())}.\n\n')
        return False
