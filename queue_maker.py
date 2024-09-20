import asyncio
from datetime import datetime, time, timedelta

from general_usage_funcs import notify_user_
import db.queues_info_table_usage as queues_info_db
from db.members_table_usage import get_members_by_group_id_and_subgroup_id, simple_get_members_by_group_id
from db.users_table_usage import notify_admins_
from status_codes import StatusCode as sc
from status_codes import get_message_about_status_code


async def timer():
    time_to_prerelease = datetime.now().replace(hour=19, minute=50, second=0)
    time_to_release = datetime.now().replace(hour=20, minute=0, second=0)
    time_to_obsolete = datetime.now().replace(hour=22, minute=59, second=0)

    prerelease_done = False
    release_done = False
    obsolete_done = False

    while True:
        now_time = datetime.now()

        if time_to_prerelease <= now_time <= time_to_prerelease.replace(second=5) and not prerelease_done:
            await prerelease_queues()
            prerelease_done = True
            await asyncio.sleep(30)
            prerelease_done = False

        elif time_to_release <= now_time <= time_to_release.replace(second=5) and not release_done:
            await release_queues()
            release_done = True
            await asyncio.sleep(30)
            release_done = False

        elif time_to_obsolete <= now_time <= time_to_obsolete.replace(second=5) and not obsolete_done:
            await obsolete_queues()
            obsolete_done = True
            await asyncio.sleep(30)
            obsolete_done = False

        await asyncio.sleep(5)


async def prerelease_queues():
    status_code, info_about_users_to_notify = await queues_info_db.prerelease_queues_from_active_schedules()
    if status_code != sc.OPERATION_SUCCESS:
        await notify_admins_(
            text='Prerelease state mistake: '
                 f'{get_message_about_status_code(status_code)}'
        )
        return
    for info in info_about_users_to_notify:
        subject = info[2]
        lesson_type = info[3]
        await notify_members_about_queues(
            group_id=info[0],
            subgroup_id=info[1],
            text=f'[АНОНС] Новая очередь в ожидании (регистрация откроется в 21:00): {subject} [{lesson_type}]'
        )


async def release_queues():
    status_code, info_about_users_to_notify = await queues_info_db.release_queues()
    if status_code not in [sc.OPERATION_SUCCESS, sc.NO_QUEUES_IN_PRERELEASE]:
        await notify_admins_(
            text='Release state mistake: '
                 f'{get_message_about_status_code(status_code)}'
        )
        return
    for info in info_about_users_to_notify:
        subject = info[2]
        lesson_type = info[3]
        await notify_members_about_queues(
            group_id=info[0],
            subgroup_id=info[1],
            text=f'[РЕЛИЗ] Открыта регистрация на очередь: {subject} [{lesson_type}]'
        )


async def obsolete_queues():
    status_code, info_about_users_to_notify = await queues_info_db.release_queues()
    if status_code != sc.OPERATION_SUCCESS:
        await notify_admins_(
            text='Obsolete state mistake: '
                 f'{get_message_about_status_code(status_code)}'
        )


async def notify_members_about_queues(group_id: int, subgroup_id, text: str):
    if subgroup_id == 0:
        members_ids = await simple_get_members_by_group_id(group_id=group_id)
        text += ' - вся группа'
    else:
        members_ids = await get_members_by_group_id_and_subgroup_id(group_id=group_id, subgroup_id=subgroup_id)
        text += f' - {subgroup_id} подгруппа'
    for member_id in members_ids:
        await notify_user_(
            user_id=member_id,
            text=text
        )