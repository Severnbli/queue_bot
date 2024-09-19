from db.root import cur, try_commit
from status_codes import StatusCode as sc


async def get_role_description_by_name(role_name: str):
    await cur.execute('''SELECT description FROM roles WHERE name = ?''', (role_name,))
    row = await cur.fetchone()
    if row is None:
        return sc.ROLE_NOT_EXIST, None
    role_description = row[0]
    return sc.OPERATION_SUCCESS, role_description