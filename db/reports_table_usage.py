from db.root import cur, try_commit
from status_codes import StatusCode as sc
import db.users_table_usage as usersdb

async def reg_report(sender_id, content):
    await cur.execute('''INSERT INTO reports (sender_id, content) VALUES (?, ?)''', (sender_id, content))
    if not await try_commit():
        return sc.DB_ERROR, None
    report_id = cur.lastrowid
    text = (f'Прилетел новый репорт. В данный момент непроверенных репортов: '
            f'{await get_quantity_of_unchecked_reports()}.')
    admins = await usersdb.get_admins_ids()
    quantity_of_notified_admins = await usersdb.notify_users_(admins, text)
    return sc.OPERATION_SUCCESS, quantity_of_notified_admins, report_id


async def get_quantity_of_unchecked_reports():
    await cur.execute('''SELECT COUNT(*) FROM reports WHERE is_checked = ?''', ('false',))
    row = await cur.fetchone()
    quantity_of_unchecked_reports = row[0]
    return quantity_of_unchecked_reports


async def get_unchecked_report():
    await cur.execute('SELECT id, sender_id, content FROM reports WHERE is_checked = ?', ('false',))
    rows = await cur.fetchall()
    if rows is None:
        return sc.DB_ERROR, None
    if len(rows) == 0:
        return sc.NO_REPORTS_TO_CHECK, None
    unchecked_reports = []
    for row in rows:
        unchecked_reports.append({
            'report_id': row[0],
            'sender_id': row[1],
            'content': row[2]
        })
    return sc.OPERATION_SUCCESS, unchecked_reports


async def send_answer_on_report_(report_id: int, sender_id: int, answer_content: str):
    await usersdb.notify_user_(user_id=sender_id, text=f'На твой репорт №{report_id} пришёл ответ: {answer_content}')
    return await make_report_checked_(report_id)


async def make_report_checked_(report_id: int):
    await cur.execute('UPDATE reports SET is_checked = ? WHERE id = ?', ('true', report_id))
    if not await try_commit():
        return sc.DB_ERROR
    return sc.OPERATION_SUCCESS
