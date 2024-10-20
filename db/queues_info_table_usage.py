from db.root import cur, try_commit
from db.schedules_table_usage import get_active_schedules, del_schedules
from general_usage_funcs import get_next_day_of_week, get_day_of_week, get_day_by_num
from status_codes import StatusCode as sc
import db.queues_table_usage as queuesdb
import db.members_table_usage as membersdb


async def prerelease_queues_from_active_schedules():
    active_schedules = await get_active_schedules()
    info_to_notify = []
    for schedule in active_schedules:
        group_id = schedule[0]
        if group_id is None:
            return sc.DB_VALUE_ERROR, None
        subject = schedule[1]
        if subject is None:
            return sc.DB_VALUE_ERROR, None
        lesson_type = schedule[2]
        if lesson_type is None:
            return sc.DB_VALUE_ERROR, None
        subgroup = schedule[3]
        if subgroup is None:
            return sc.DB_VALUE_ERROR, None
        day_of_week = schedule[4]
        if day_of_week is None:
            return sc.DB_VALUE_ERROR, None
        info_to_notify.append((group_id, subgroup, subject, lesson_type, await get_day_by_num(day_of_week)))
        await cur.execute('INSERT INTO queues_info '
                          '(group_id, subject, lesson_type, subgroup, status, day_of_week) '
                          'VALUES (?, ?, ?, ?, ?, ?)',
                          (group_id, subject, lesson_type, subgroup, 'prerelease', day_of_week))
        if not await try_commit():
            return sc.DB_ERROR, None
    return sc.OPERATION_SUCCESS, info_to_notify


async def release_queues():
    await cur.execute('SELECT group_id, subgroup, subject, lesson_type, day_of_week '
                      "FROM queues_info WHERE status = 'prerelease'")
    info_about_users = await cur.fetchall()
    if info_about_users is None:
        return sc.NO_QUEUES_IN_PRERELEASE, None
    await cur.execute('UPDATE queues_info '
                      "SET status = 'release' "
                      "WHERE status = 'prerelease'"
                      "AND day_of_week = ?", (await get_next_day_of_week(),))
    if not await try_commit():
        return sc.DB_ERROR, None
    return sc.OPERATION_SUCCESS, info_about_users


async def obsolete_queues_():
    await cur.execute('UPDATE queues_info '
                      "SET status = 'obsolete' "
                      "WHERE status = 'release' "
                      "AND day_of_week = ?", (await get_day_of_week(),))
    if not await try_commit():
        return sc.DB_ERROR
    return sc.OPERATION_SUCCESS


async def get_information_about_queues_with_user_participation(user_id: int):
    status_code, group_id = await membersdb.get_group_id_by_user_id(user_id=user_id)
    if status_code != sc.OPERATION_SUCCESS:
        return status_code, None
    await cur.execute('SELECT id, subject, lesson_type, subgroup, day_of_week '
                      'FROM queues_info '
                      'WHERE group_id = ?'
                      "AND status = 'release'", (group_id,))
    rows = await cur.fetchall()
    if len(rows) == 0:
        return sc.NO_QUEUES_TO_PARTICIPATE, None
    else:
        information_about_queues = []
        for row in rows:
            status_code = await queuesdb.status_of_participating_in_queue_(
                user_id=user_id,
                queue_info_id=row[0]
            )
            if status_code not in [sc.USER_PARTICIPATE_IN_QUEUE, sc.USER_NOT_PARTICIPATE_IN_QUEUE]:
                return status_code, None
            if status_code == sc.USER_PARTICIPATE_IN_QUEUE:
                buffer = '✅ '
            else:
                buffer = '❌ '
            status_code, info = await get_information_to_make_button(row[0])
            if status_code != sc.OPERATION_SUCCESS:
                return status_code, None
            buffer += info
            information_about_queues.append(buffer)
        return sc.OPERATION_SUCCESS, information_about_queues


async def is_queue_info_exist_(queue_info_id: int):
    await cur.execute('SELECT COUNT(*) '
                      'FROM queues_info '
                      'WHERE id = ?', (queue_info_id,))
    row = await cur.fetchone()
    if row is None:
        return False
    is_exist = bool(row[0])
    return is_exist


async def get_information_about_queue_info(queue_info_id: int):
    is_exist = await is_queue_info_exist_(queue_info_id)
    if not is_exist:
        return sc.QUEUES_INFO_NOT_EXIST, None
    await cur.execute('SELECT subject, lesson_type, subgroup, day_of_week '
                      'FROM queues_info '
                      'WHERE id = ?', (queue_info_id,))
    row = await cur.fetchone()
    if row is None:
        return sc.DB_ERROR, None
    info = f'{row[0]} [{row[1]}] - '
    if row[2] == 0:
        info += 'вся группа'
    else:
        info += f'{row[2]} подгруппа'
    info += f' {await get_day_by_num(row[3])}'
    return sc.OPERATION_SUCCESS, info


async def del_queues_info_by_group_id(group_id: int):
    await cur.execute('SELECT id '
                      'FROM queues_info '
                      'WHERE group_id = ?', (group_id,))
    rows = await cur.fetchall()
    for row in rows:
        await cur.execute('DELETE FROM queues '
                          'WHERE queues_info_id = ?', (row[0],))
    await cur.execute('DELETE FROM queues_info '
                      'WHERE group_id = ?', (group_id,))
    await try_commit()
    await del_schedules(group_id)


async def get_information_to_make_button(queues_info_id: int):
    is_exist = await is_queue_info_exist_(queues_info_id)
    if not is_exist:
        return sc.QUEUES_INFO_NOT_EXIST, None
    await cur.execute('SELECT id, subject, lesson_type, subgroup, day_of_week '
                      'FROM queues_info '
                      'WHERE id = ?', (queues_info_id,))
    row = await cur.fetchone()
    if row is None:
        return sc.DB_ERROR, None
    buffer = f'{row[1]} [{row[2]}] - '
    if row[3] == 0:
        buffer += 'вся'
    else:
        buffer += f'{row[3]} п.'
    buffer += f' - {await get_day_by_num(row[4])} - {row[0]}'
    return sc.OPERATION_SUCCESS, buffer


async def get_information_to_make_header(queues_info_id: int):
    is_exist = await is_queue_info_exist_(queues_info_id)
    if not is_exist:
        return sc.QUEUES_INFO_NOT_EXIST, None
    await cur.execute('SELECT subject, lesson_type, subgroup, day_of_week, id '
                      'FROM queues_info '
                      'WHERE id = ?', (queues_info_id,))
    row = await cur.fetchone()
    if row is None:
        return sc.DB_ERROR, None
    buffer = f'<b>Информация об очереди {row[0]} [{row[1]}] - '
    if row[2] == 0:
        buffer += 'вся группа'
    else:
        buffer += f'{row[2]} подгруппа'
    buffer += f' - {await get_day_by_num(row[3])}</b>\n\nАйди для трейда: {row[4]}'
    return sc.OPERATION_SUCCESS, buffer


async def simple_get_status_of_queue_info(queue_info_id: int):
    await cur.execute('SELECT status '
                      'FROM queues_info '
                      'WHERE id = ?', (queue_info_id,))
    row = await cur.fetchone()
    if row is None:
        return sc.QUEUES_INFO_NOT_EXIST, None
    queue_info_status = row[0]
    return sc.OPERATION_SUCCESS, queue_info_status


async def get_release_queues_info():
    await cur.execute('SELECT group_id, subject, lesson_type, subgroup, day_of_week '
                      'FROM queues_info '
                      'WHERE status = ?', ('prerelease',))

    rows = await cur.fetchall()

    if len(rows) == 0:
        return sc.NO_QUEUES_IN_RELEASE, None

    return sc.OPERATION_SUCCESS, rows
