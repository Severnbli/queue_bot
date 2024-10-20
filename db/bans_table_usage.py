from db.root import cur
from utils.status_codes import StatusCode as sc
import db.groups_table_usage as groupsdb


async def is_user_in_ban_by_group_id_(banned_user_id, group_id):
    await cur.execute('''SELECT COUNT(*) FROM bans WHERE banned_user_id = ? AND group_id = ?''',
                      (banned_user_id, group_id))
    row = await cur.fetchone()
    if row[0] != 0:
        return True
    else:
        return False


async def is_user_in_ban_by_key_(banned_user_id, key):
    status_code, group_id = await groupsdb.get_group_id_by_key(key)
    if status_code != sc.OPERATION_SUCCESS:
        return False
    is_user_in_ban = await is_user_in_ban_by_group_id_(banned_user_id, group_id)
    return is_user_in_ban
