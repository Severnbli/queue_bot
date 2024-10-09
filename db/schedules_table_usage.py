from db.root import cur, try_commit
from status_codes import StatusCode as sc
from general_usage_funcs import get_next_day_of_week, get_next_day_week_of_month


async def add_schedule(
        group_id: int,
        subject: str,
        lesson_type: str,
        day_of_week: int,
        weeks_of_month: tuple,
        subgroup: int,
        is_in_schedule: str
):
    weeks_of_month = tuple(map(str, weeks_of_month))
    parsed_wom = ' '.join(weeks_of_month)
    await cur.execute('SELECT COUNT(*) '
                      'FROM schedules '
                      'WHERE group_id = ? '
                      'AND subject = ? '
                      'AND lesson_type = ? '
                      'AND subgroup = ? '
                      'AND day_of_week = ? '
                      'AND weeks_of_month = ? ',
                      (group_id, subject, lesson_type, subgroup, day_of_week, parsed_wom))
    row = await cur.fetchone()
    if row is None:
        return sc.DB_ERROR
    is_same_schedule_exists = bool(row[0])
    if is_same_schedule_exists:
        return sc.SAME_SCHEDULE_EXIST
    await cur.execute('INSERT INTO schedules '
                      '(group_id, subject, lesson_type, day_of_week, weeks_of_month, subgroup, is_in_schedule) '
                      'VALUES (?, ?, ?, ?, ?, ?, ?)', (group_id, subject, lesson_type, day_of_week, parsed_wom, subgroup,
                                                    is_in_schedule))
    if not await try_commit():
        return sc.DB_ERROR
    return sc.OPERATION_SUCCESS


async def get_active_schedules():
    next_dow = await get_next_day_of_week()
    next_wom = await get_next_day_week_of_month()
    formated_wom = f'%{next_wom}%'
    await cur.execute("SELECT group_id, subject, lesson_type, subgroup, day_of_week "
                      "FROM schedules "
                      "WHERE is_in_schedule = 'true' "
                      "AND day_of_week = ? "
                      "AND weeks_of_month LIKE ?",
                      (next_dow, formated_wom))
    schedules = await cur.fetchall()
    return schedules


async def del_schedules(group_id: int):
    await cur.execute('DELETE FROM schedules '
                      'WHERE group_id = ?', (group_id,))
    await try_commit()