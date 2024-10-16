from db.root import cur, try_commit
from status_codes import StatusCode as sc
from status_codes import get_message_about_status_code
from general_usage_funcs import get_day_by_num
import db.queues_info_table_usage as queues_info_db


async def status_of_participating_in_queue_(user_id: int, queue_info_id: int):
    await cur.execute('SELECT COUNT(*) '
                      'FROM queues '
                      'WHERE queues_info_id = ? '
                      'AND user_id = ?', (queue_info_id, user_id))
    row = await cur.fetchone()
    if row is None:
        return sc.DB_ERROR
    is_participating_in_queue = bool(row[0])
    if is_participating_in_queue:
        return sc.USER_PARTICIPATE_IN_QUEUE
    else:
        return sc.USER_NOT_PARTICIPATE_IN_QUEUE


async def add_user_to_queue_(queue_info_id: int, user_id: int):
    is_queue_info_exist = await queues_info_db.is_queue_info_exist_(queue_info_id)
    if not is_queue_info_exist:
        return sc.QUEUES_INFO_NOT_EXIST
    await cur.execute('SELECT MAX(place) '
                      'FROM queues '
                      'WHERE queues_info_id = ?', (queue_info_id,))
    row = await cur.fetchone()
    if row[0] is None:
        await cur.execute('INSERT INTO queues (queues_info_id, user_id, place) '
                          'VALUES (?, ?, ?)', (queue_info_id, user_id, 1))
    else:
        max_place = row[0]
        await cur.execute('INSERT INTO queues (queues_info_id, user_id, place) '
                          'VALUES (?, ?, ?)', (queue_info_id, user_id, max_place + 1))
    if not await try_commit():
        return sc.DB_ERROR
    return sc.OPERATION_SUCCESS


async def get_user_place_in_queue(user_id: int, queue_info_id: int):
    status_code = await status_of_participating_in_queue_(user_id, queue_info_id)
    if status_code != sc.USER_PARTICIPATE_IN_QUEUE:
        return status_code, None
    await cur.execute('SELECT place '
                      'FROM queues '
                      'WHERE queues_info_id = ? '
                      'AND user_id = ?', (queue_info_id, user_id))
    row = await cur.fetchone()
    if row is None:
        return sc.DB_ERROR, None
    place = row[0]
    return sc.OPERATION_SUCCESS, place


async def del_user_from_queue_(queue_info_id: int, user_id: int):
    status_code = await status_of_participating_in_queue_(
        user_id=user_id,
        queue_info_id=queue_info_id
    )
    if status_code != sc.USER_PARTICIPATE_IN_QUEUE:
        return status_code
    status_code, place = await get_user_place_in_queue(user_id=user_id, queue_info_id=queue_info_id)
    if status_code != sc.OPERATION_SUCCESS:
        return status_code
    await cur.execute('UPDATE queues '
                      'SET place = place - 1 '
                      'WHERE queues_info_id = ? '
                      'AND place > ?', (queue_info_id, place))
    await cur.execute('DELETE FROM queues '
                      'WHERE user_id = ? '
                      'AND queues_info_id = ?', (user_id, queue_info_id))
    if not await try_commit():
        return sc.DB_ERROR
    return sc.OPERATION_SUCCESS


async def del_or_add_user_to_queue(user_id: int, queue_info_id: int):
    status_code = await status_of_participating_in_queue_(user_id=user_id, queue_info_id=queue_info_id)
    if status_code == sc.USER_PARTICIPATE_IN_QUEUE:
        status_code = await del_user_from_queue_(queue_info_id=queue_info_id, user_id=user_id)
        if status_code != sc.OPERATION_SUCCESS:
            return status_code
        else:
            return sc.USER_DELETE_FROM_QUEUE_SUCCESSFULLY
    elif status_code == sc.USER_NOT_PARTICIPATE_IN_QUEUE:
        status_code = await add_user_to_queue_(queue_info_id=queue_info_id, user_id=user_id)
        if status_code != sc.OPERATION_SUCCESS:
            return status_code
        else:
            return sc.USER_ADD_TO_QUEUE_SUCCESSFULLY
    else:
        return sc.UNKNOWN_STATUS_CODE


async def get_info_about_user_participation_in_queues(user_id: int):
    await cur.execute('SELECT q_i.subject, q_i.lesson_type, q_i.subgroup, q_i.day_of_week, q.place  '
                      'FROM queues AS q '
                      'INNER JOIN queues_info AS q_i  ON q.queues_info_id = q_i.id '
                      'WHERE q.user_id = ? '
                      "AND q_i.status != 'obsolete'", (user_id,))
    rows = await cur.fetchall()
    if rows is not None and len(rows) > 0:
        info_about_user_participation = '<b>Активные очереди, в которых ты участвуешь</b>\n\n'
        for row in rows:
            info_about_user_participation += f'🔹 <b>{row[0]}</b> [<b>{row[1]}</b>] - '
            if row[2] == 0:
                info_about_user_participation += '<b>вся группа</b>'
            else:
                info_about_user_participation += f'<b>{row[2]} подгруппа</b>'
            info_about_user_participation += f' - <b>{row[4]} место</b> - <b>{await get_day_by_num(row[3])}</b>\n'
    else:
        info_about_user_participation = 'Ты не участвуешь ни в одной очереди.'
    return info_about_user_participation


async def simple_get_queues_info_ids_which_user_participate(user_id: int):
    await cur.execute('SELECT q.queues_info_id '
                      'FROM queues AS q '
                      'INNER JOIN queues_info AS q_i ON q.queues_info_id = q_i.id '
                      'WHERE q.user_id = ? '
                      'AND q_i.status = ?', (user_id, 'release'))
    rows = await cur.fetchall()
    if rows is None:
        return sc.DB_ERROR, None
    if len(rows) == 0:
        return sc.USER_NOT_PARTICIPATE_IN_ANY_QUEUES, None
    queues_info_ids = []
    for row in rows:
        queues_info_ids.append(row[0])
    return sc.OPERATION_SUCCESS, queues_info_ids


async def get_information_users_participate_queue(queue_info_id: int):
    await cur.execute('SELECT q.place, u.nick, u.username, q.user_note '
                      'FROM queues AS q '
                      'INNER JOIN users AS u ON q.user_id = u.id '
                      'WHERE queues_info_id = ? '
                      'ORDER BY place', (queue_info_id,))
    rows = await cur.fetchall()
    if rows is None:
        return sc.DB_ERROR, None
    if len(rows) == 0:
        return sc.NO_USERS_THAT_PARTICIPATE_ENTERED_QUEUE_INFO, None
    info = ''
    for row in rows:
        info += f'🔹 <b>{row[0]}</b>. '
        if row[2] is not None:
            info += f'<a href="{row[2]}">{row[1]}</a>'
        else:
            info += f'{row[1]}'
        if row[3] is not None:
            info += f' [{row[3]}]'
        info += '\n'
    return sc.OPERATION_SUCCESS, info


async def swap_places_(first_user_id: int, second_user_id: int, queue_info_id: int):
    await cur.execute('SELECT user_id, place '
                      'FROM queues '
                      'WHERE queues_info_id = ? '
                      'AND (user_id = ? '
                      'OR user_id = ?) ', (queue_info_id, first_user_id, second_user_id))
    rows = await cur.fetchall()
    if rows is None:
        return sc.DB_ERROR
    if len(rows) < 2:
        return sc.TRADE_INFO_OUT_OF_DATE
    first_user_id = rows[0][0]
    first_user_place = rows[0][1]
    second_user_id = rows[1][0]
    second_user_place = rows[1][1]
    await cur.execute('UPDATE queues '
                      'SET place = ? '
                      'WHERE user_id = ? '
                      'AND queues_info_id = ? ', (second_user_place, first_user_id, queue_info_id))
    if not await try_commit():
        return sc.DB_ERROR
    await cur.execute('UPDATE queues '
                      'SET place = ? '
                      'WHERE user_id = ? '
                      'AND queues_info_id = ? ', (first_user_place, second_user_id, queue_info_id))
    if not await try_commit():
        return sc.DB_ERROR
    return sc.OPERATION_SUCCESS


async def get_user_id_by_place_in_queue(place: int, queue_info_id: int):
    await cur.execute('SELECT user_id '
                      'FROM queues '
                      'WHERE place = ? '
                      'AND queues_info_id = ?', (place, queue_info_id))
    row = await cur.fetchone()
    if row is None:
        return sc.USER_WITH_SUCH_PLACE_IN_SUCH_QUEUE_NOT_EXIST, None
    user_id = row[0]
    return sc.OPERATION_SUCCESS, user_id


async def update_user_note_for_queue_(user_id: int, queue_info_id: int, note):
    await cur.execute('UPDATE queues '
                      'SET user_note = ? '
                      'WHERE user_id = ? '
                      'AND queues_info_id = ?', (note, user_id, queue_info_id))
    return await try_commit()
