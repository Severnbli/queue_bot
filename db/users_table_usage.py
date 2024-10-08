from db.root import cur, try_commit
from status_codes import StatusCode as sc
import db.roles_table_usage as rolesdb
import db.groups_table_usage as groupsdb
import db.members_table_usage as membersdb
from general_usage_funcs import get_subgroup_name, notify_user_

async def is_user_exist_(user_id: int) -> bool:
    await cur.execute('''SELECT COUNT(*) FROM users WHERE id = ?''', (user_id,))
    row = await cur.fetchone()
    if row[0] != 0:
        return True
    else:
        return False


async def get_nick(user_id: int):
    if not await is_user_exist_(user_id):
        return sc.USER_NOT_EXIST, None
    await cur.execute('''SELECT nick FROM users WHERE id = ?''', (user_id,))
    row = await cur.fetchone()
    if row[0] is None:
        return sc.DB_VALUE_ERROR, None
    nick = row[0]
    return sc.OPERATION_SUCCESS, nick


async def get_user_id_by_nick(nick: str):
    await cur.execute('SELECT id FROM users WHERE nick = ?', (nick,))
    row = await cur.fetchone()
    if row is None:
        return sc.USER_NOT_EXIST, None
    user_id = row[0]
    return sc.OPERATION_SUCCESS, user_id


async def get_all_nicks():
    await cur.execute('''SELECT nick FROM users''')
    rows = await cur.fetchall()
    nicks = []
    for row in rows:
        nicks.append(row[0])
    return nicks


async def reg_user_(user_id: int, nick: str, username: str):
    if await is_user_exist_(user_id):
        return sc.USER_EXIST
    await cur.execute('''INSERT INTO users (id, nick, username) VALUES (?, ?, ?)''', (user_id, nick, username))
    if not await try_commit():
        return sc.DB_ERROR
    return sc.OPERATION_SUCCESS


async def update_nick_(user_id: int, nick: str):
    if not await is_user_exist_(user_id):
        return sc.USER_NOT_EXIST
    await cur.execute('''UPDATE users SET nick = ? WHERE id = ?''', (nick, user_id))
    if not await try_commit():
        return sc.DB_ERROR
    return sc.OPERATION_SUCCESS


async def get_username(user_id: int):
    if not await is_user_exist_(user_id):
        return sc.USER_NOT_EXIST, None
    await cur.execute('''SELECT username FROM users WHERE id = ?''', (user_id,))
    row = await cur.fetchone()
    username = row[0]
    return sc.OPERATION_SUCCESS, username


async def get_user_info(user_id: int):
    await cur.execute('''SELECT * FROM users WHERE id = ?''', (user_id,))
    row = await cur.fetchone()
    if row is None:
        return sc.USER_NOT_EXIST, None
    status_code, role_description = await rolesdb.get_role_description_by_name(row[3])
    if status_code != sc.OPERATION_SUCCESS:
        return status_code, None
    group_name = 'не в группе'
    status_code, group_id = await membersdb.get_group_id_by_user_id(user_id)
    if status_code == sc.OPERATION_SUCCESS:
        status_code, group_name = await groupsdb.get_group_name_by_id(group_id)
        if status_code != sc.OPERATION_SUCCESS:
            return status_code, None
        status_code, subgroup_id = await membersdb.get_subgroup_id(user_id)
        if status_code == sc.OPERATION_SUCCESS:
            group_name += f' ({await get_subgroup_name(subgroup_id)} подгруппа)'
    elif status_code != sc.USER_NOT_IN_GROUP:
        return status_code, None
    if row[4] == 'false':
        is_news = 'отсутствует'
    else:
        is_news = 'присутствует'
    ref = 'отсутствует'
    if row[2] is not None:
        ref = f'@{row[2]}'
    info_about_user = (f'🔹 <b>Ник</b>: {row[1]}\n🔹 <b>Ссылка</b>: {ref}\n🔹 <b>Роль</b>: {role_description}'
                       f'\n🔹 <b>Группа</b>: {group_name}\n🔹 <b>Подписка на обновления очередей</b>: {is_news}')
    return sc.OPERATION_SUCCESS, info_about_user


async def update_link_(user_id: int, username: str):
    if not await is_user_exist_(user_id):
        return sc.USER_NOT_EXIST
    await cur.execute('''UPDATE users SET username = ? WHERE id = ?''', (username, user_id))
    if not await try_commit():
        return sc.DB_ERROR
    return sc.OPERATION_SUCCESS


async def get_admins_ids() -> tuple:
    admins_ids = []
    await cur.execute('''SELECT id FROM users WHERE role_name = ?''', ('admin',))
    rows = await cur.fetchall()
    if rows is not None:
        for row in rows:
            admins_ids.append(row[0])
    return tuple(admins_ids)


async def notify_admins_(text: str) -> None:
    admins_ids = await get_admins_ids()
    for admin_id in admins_ids:
        await notify_user_(admin_id, text)


async def turn_on_off_subscription_(user_id: int):
    if not await is_user_exist_(user_id):
        return sc.USER_NOT_EXIST
    await cur.execute('SELECT is_news FROM users WHERE id = ?', (user_id,))
    row = await cur.fetchone()
    if row is None:
        return sc.DB_ERROR
    is_news = row[0]
    if is_news == 'false':
        is_news = 'true'
    else:
        is_news = 'false'
    await cur.execute('UPDATE users '
                      'SET is_news = ? '
                      'WHERE id = ?', (is_news, user_id))
    if not await try_commit():
        return sc.DB_ERROR
    return sc.OPERATION_SUCCESS


async def get_info_about_status_of_news(user_id: int):
    if not await is_user_exist_(user_id):
        return sc.USER_NOT_EXIST, None
    await cur.execute('SELECT is_news '
                      'FROM users '
                      'WHERE id = ?', (user_id,))
    row = await cur.fetchone()
    if row is None:
        return sc.DB_ERROR, None
    is_news = row[0]
    info_about_status_of_news = 'Состояние подписки на обновление: '
    if is_news == 'true':
        info_about_status_of_news += '<b>включено</b>.'
    else:
        info_about_status_of_news += '<b>выключено</b>.'
    return sc.OPERATION_SUCCESS, info_about_status_of_news


async def is_user_admin_(user_id: int) -> bool:
    await cur.execute('SELECT role_name FROM users WHERE id = ?', (user_id,))
    row = await cur.fetchone()
    if row is None:
        return False
    if row[0] == 'admin':
        return True
    return False
