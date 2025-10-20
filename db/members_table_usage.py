from db.root import cur, try_commit
from utils.status_codes import StatusCode as sc
import db.groups_table_usage as groupsdb
import db.users_table_usage as usersdb


async def is_user_in_group_(user_id: int):
    await cur.execute('''SELECT COUNT(*) FROM members WHERE user_id = ?''', (user_id,))
    row = await cur.fetchone()
    if row[0] != 0:
        return True
    else:
        return False


async def get_user_position_in_group(user_id: int):
    await cur.execute('''SELECT position FROM members WHERE user_id = ?''', (user_id,))
    row = await cur.fetchone()
    if row is None:
        return sc.USER_NOT_IN_GROUP, None
    user_position = row[0]
    return sc.OPERATION_SUCCESS, user_position


async def get_quantity_of_group_members(group_id: int):
    if not await groupsdb.is_group_exist_(group_id):
        return sc.GROUP_NOT_EXIST, None
    await cur.execute('''SELECT COUNT(*) FROM members WHERE group_id = ?''', (group_id,))
    row = await cur.fetchone()
    if row is None:
        return sc.DB_VALUE_ERROR, None
    quantity_of_group_members = row[0]
    return sc.OPERATION_SUCCESS, quantity_of_group_members


async def get_group_leaders(group_id: int):
    if not await groupsdb.is_group_exist_(group_id):
        return sc.GROUP_NOT_EXIST, None
    await cur.execute('''SELECT u.nick, u.username, m.position FROM members AS m 
                    INNER JOIN users AS u ON m.user_id = u.id WHERE m.group_id = ? 
                    AND m.position IN ('leader', 'depute')''', (group_id,))
    rows = await cur.fetchall()
    if rows is None or len(rows) == 0:
        return sc.DB_VALUE_ERROR, None
    leaders = []
    for row in rows:
        leader_dict = {
            'nick': row[0],
            'username': row[1],
            'position': row[2],
        }
        leaders.append(leader_dict)
    return sc.OPERATION_SUCCESS, leaders


async def get_group_id_by_user_id(user_id: int):
    if not await usersdb.is_user_exist_(user_id):
        return sc.USER_NOT_EXIST, None
    await cur.execute('''SELECT group_id FROM members WHERE user_id = ?''', (user_id,))
    row = await cur.fetchone()
    if row is None:
        return sc.USER_NOT_IN_GROUP, None
    group_id = row[0]
    return sc.OPERATION_SUCCESS, group_id


async def get_subgroup_id(user_id: int):
    if not await usersdb.is_user_exist_(user_id):
        return sc.USER_NOT_EXIST, None
    await cur.execute('''SELECT subgroup_id FROM members WHERE user_id = ?''', (user_id,))
    row = await cur.fetchone()
    if row is None:
        return sc.USER_NOT_IN_GROUP, None
    subgroup_id = row[0]
    return sc.OPERATION_SUCCESS, subgroup_id


async def del_user_from_group_(user_id: int):
    if not await is_user_in_group_(user_id):
        return sc.USER_NOT_IN_GROUP
    await cur.execute('''DELETE FROM members WHERE user_id = ?''', (user_id,))
    if not await try_commit():
        return sc.DB_ERROR
    return sc.OPERATION_SUCCESS


async def add_user_to_group_(user_id: int, group_id: int, position: str):
    if not await groupsdb.is_group_exist_(group_id):
        return sc.GROUP_NOT_EXIST
    if not await usersdb.is_user_exist_(user_id):
        return sc.USER_NOT_EXIST
    if await is_user_in_group_(user_id):
        return sc.USER_IN_GROUP
    await cur.execute('''INSERT INTO members (group_id, user_id, position) VALUES (?, ?, ?)''',
                      (group_id, user_id, position))
    if not await try_commit():
        return sc.DB_ERROR
    return sc.OPERATION_SUCCESS


async def del_all_users_from_group_(group_id):
    await cur.execute('''DELETE FROM members WHERE group_id = ?''', (group_id,))
    if not await try_commit():
        return sc.DB_ERROR
    return sc.OPERATION_SUCCESS


async def get_all_members_of_group(group_id: int):
    if not await groupsdb.is_group_exist_(group_id):
        return sc.GROUP_NOT_EXIST, None
    await cur.execute('SELECT u.nick, u.username, m.user_id, m.position, m.subgroup_id '
                      'FROM members AS m '
                      'INNER JOIN users AS u ON u.id = m.user_id '
                      'WHERE m.group_id = ?', (group_id,))
    rows = await cur.fetchall()
    if rows is None or len(rows) == 0:
        return sc.DB_VALUE_ERROR, None # Не может быть такой ситуации, что группа пуста
    members = []
    for row in rows:
        members.append(row)
    return sc.OPERATION_SUCCESS, tuple(members)


async def set_subgroup(user_id: int, subgroup: int):
    if not await is_user_in_group_(user_id):
        return sc.USER_NOT_IN_GROUP
    await cur.execute('''UPDATE members SET subgroup_id = ? WHERE user_id = ?''', (subgroup, user_id))
    if not await try_commit():
        return sc.DB_ERROR
    return sc.OPERATION_SUCCESS


async def get_all_nicks_by_group_id(group_id: int):
    if not await groupsdb.is_group_exist_(group_id):
        return sc.GROUP_NOT_EXIST, None
    await cur.execute('SELECT u.nick '
                      'FROM members AS m '
                      'INNER JOIN users AS u ON u.id = m.user_id '
                      'WHERE m.group_id = ?', (group_id,))
    rows = await cur.fetchall()
    if rows is None or len(rows) == 0:
        return sc.DB_VALUE_ERROR, None
    nicks = []
    for row in rows:
        nicks.append(row[0])
    return sc.OPERATION_SUCCESS, tuple(nicks)


async def is_users_in_same_group_(user1_id: int, user2_id: int) -> bool:
    await cur.execute('SELECT COUNT(*) '
                      'FROM members AS m1 '
                      'INNER JOIN members AS m2 ON m1.group_id = m2.group_id '
                      'WHERE m1.user_id = ? AND m2.user_id  =?', (user1_id, user2_id))
    row = await cur.fetchone()
    if row is None:
        return False
    count = row[0]
    if count == 0:
        return False
    return True


async def get_members_by_group_id_and_subgroup_id(group_id: int, subgroup_id: int):
    await cur.execute('SELECT user_id FROM members WHERE group_id = ? AND subgroup_id = ?',
                      (group_id, subgroup_id))
    rows = await cur.fetchall()
    users_ids = []
    if rows is not None:
        for row in rows:
            users_ids.append(row[0])
    return users_ids


async def simple_get_members_by_group_id(group_id: int):
    await cur.execute('SELECT user_id FROM members WHERE group_id = ?', (group_id,))
    rows = await cur.fetchall()
    users_ids = []
    if rows is not None:
        for row in rows:
            users_ids.append(row[0])
    return users_ids
