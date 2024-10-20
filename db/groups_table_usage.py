from db.root import cur, try_commit
from utils.status_codes import StatusCode as sc
import db.users_table_usage as usersdb
import db.members_table_usage as membersdb
from utils.general_usage_funcs import get_random_str


async def gen_key_(length: int) -> str:
    await cur.execute('''SELECT key FROM groups''')
    rows = await cur.fetchall()
    while True:
        key = await get_random_str(length)
        for row in rows:
            if key == row[0]:
                continue
        break
    return str(key)


async def is_group_exist_(group_id: int) -> bool:
    await cur.execute('''SELECT COUNT(*) FROM groups WHERE id = ?''', (group_id,))
    row = await cur.fetchone()
    if row[0] != 0:
        return True
    else:
        return False


async def get_group_name_by_id(group_id: int):
    await cur.execute('''SELECT name FROM groups WHERE id = ?''', (group_id,))
    row = await cur.fetchone()
    if row is None:
        return sc.GROUP_NOT_EXIST, None
    group_name = row[0]
    return sc.OPERATION_SUCCESS, group_name


# эта функция может использоваться для определения, существует ли другая группа с таким названием
async def get_group_id_by_name(group_name: str):
    await cur.execute('''SELECT id FROM groups WHERE name = ?''', (group_name,))
    row = await cur.fetchone()
    if row is None:
        return sc.GROUP_NOT_EXIST, None
    group_id = row[0]
    return sc.OPERATION_SUCCESS, group_id


async def get_group_id_by_key(key: str):
    await cur.execute('''SELECT id FROM groups WHERE key = ?''', (key,))
    row = await cur.fetchone()
    if row is None:
        return sc.GROUP_WITH_SUCH_KEY_NOT_EXIST, None
    group_id = row[0]
    return sc.OPERATION_SUCCESS, group_id


async def get_key_by_group_id(group_id: int):
    await cur.execute('''SELECT key FROM groups WHERE id = ?''', (group_id,))
    row = await cur.fetchone()
    if row is None:
        return sc.GROUP_NOT_EXIST, None
    key = row[0]
    return sc.OPERATION_SUCCESS, key


async def get_key_by_group_name(group_name: str):
    await cur.execute('''SELECT key FROM groups WHERE name = ?''', (group_name,))
    row = await cur.fetchone()
    if row is None:
        return sc.GROUP_NOT_EXIST, None
    key = row[0]
    return sc.OPERATION_SUCCESS, key


async def is_group_with_such_name_exist(group_name: str) -> bool:
    status_code, group_id = await get_group_id_by_name(group_name)
    if status_code == sc.GROUP_NOT_EXIST:
        return False
    else:
        return True


async def reg_group_(tg_id: int, name: str):
    if not await usersdb.is_user_exist_(tg_id):
        return sc.USER_NOT_EXIST
    if name is None:
        return sc.GIVEN_VALUE_TYPE_ERROR
    if await is_group_with_such_name_exist(name):
        return sc.GROUP_WITH_SUCH_NAME_EXIST
    key = await gen_key_(6)
    await cur.execute('''INSERT INTO groups (name, key) VALUES (?, ?)''', (name, key))
    if not await try_commit():
        return sc.DB_ERROR
    status_code, group_id = await get_group_id_by_name(name)
    if status_code != sc.OPERATION_SUCCESS:
        return status_code
    status_code = await membersdb.add_user_to_group_(tg_id, group_id, 'leader')
    if status_code != sc.OPERATION_SUCCESS:
        await cur.execute('''DELETE FROM groups WHERE id = ?''', (group_id,))
        await try_commit()
        return sc.DB_ERROR
    return sc.OPERATION_SUCCESS


async def get_group_info(group_id = None, group_name = None):
    if group_id is None:
        status_code, group_id = await get_group_id_by_name(group_name)
        if status_code != sc.OPERATION_SUCCESS:
            return status_code, None
    else:
        status_code, group_name = await get_group_name_by_id(group_id)
        if status_code != sc.OPERATION_SUCCESS:
            return status_code, None
    status_code, quantity_of_group_members = await membersdb.get_quantity_of_group_members(group_id)
    if status_code != sc.OPERATION_SUCCESS:
        return status_code, None
    status_code, leaders = await membersdb.get_group_leaders(group_id)
    if status_code != sc.OPERATION_SUCCESS:
        return status_code, None
    leaders_info = ''
    for leader in leaders:
        leaders_info += '🔹 '
        if leader['position'] == 'leader':
            leaders_info += '<b>Лидер</b>'
        elif leader['position'] == 'depute':
            leaders_info += '<b>Заместитель</b>'
        else:
            leaders_info += '<b>Хз кто</b>'
        leaders_info += ': '
        if leader["username"] is not None:
            leaders_info += f'<a href="{leader["username"]}">{leader["nick"]}</a>'
        else:
            leaders_info += f'{leader["nick"]}'
        if leader is not leaders[-1]:
            leaders_info += '\n'
    group_info = (f'🔹 <b>Название</b>: {group_name}\n{leaders_info}'
                  f'\n🔹 <b>Количество участников</b>: {quantity_of_group_members}')
    return sc.OPERATION_SUCCESS, group_info


async def del_group_(group_id):
    if not await is_group_exist_(group_id):
        return sc.GROUP_NOT_EXIST
    status_code = await membersdb.del_all_users_from_group_(group_id)
    if status_code != sc.OPERATION_SUCCESS:
        return status_code
    await cur.execute('''DELETE FROM groups WHERE id = ?''', (group_id,))
    if not await try_commit():
        return sc.DB_ERROR
    return sc.OPERATION_SUCCESS


async def gen_new_key_to_group_(group_id):
    if not await is_group_exist_(group_id):
        return sc.GROUP_NOT_EXIST
    key = await gen_key_(6)
    await cur.execute('''UPDATE groups SET key = ? WHERE id = ?''', (key, group_id))
    if not await try_commit():
        return sc.DB_ERROR
    return sc.OPERATION_SUCCESS


async def set_group_name_by_group_id_(group_id, name):
    if not await is_group_exist_(group_id):
        return sc.GROUP_NOT_EXIST
    await cur.execute('''UPDATE groups SET name = ? WHERE id = ?''', (name, group_id))
    if not await try_commit():
        return sc.DB_ERROR
    return sc.OPERATION_SUCCESS