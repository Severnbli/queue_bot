import asyncio
from datetime import time, datetime, timedelta

from general_usage_funcs import get_day_by_num
import db.queues_info_table_usage as queues_info_db
from db.members_table_usage import get_members_by_group_id_and_subgroup_id, simple_get_members_by_group_id
from db.users_table_usage import notify_admins_, notify_users_if_news_turned_on_
from status_codes import StatusCode as sc
from status_codes import get_message_about_status_code


async def prerelease_queues(time_to_release: time):
    status_code, info_about_users_to_notify = await queues_info_db.prerelease_queues_from_active_schedules()
    if status_code != sc.OPERATION_SUCCESS:
        await notify_admins_(
            text=f'Prerelease state mistake: {get_message_about_status_code(status_code)}'
        )
        return

    try:
        async with asyncio.TaskGroup() as tg:
            for info in info_about_users_to_notify:
                group_id = info[0]
                subgroup_id = info[1]
                subject = info[2]
                lesson_type = info[3]
                day_of_week = info[4]
                text_header = '[АНОНС]'
                text_ender = f'в ожидании (регистрация откроется в {time_to_release}): {subject} [{lesson_type}] - {day_of_week}'

                tg.create_task(
                    notify_members_about_queues(
                        group_id=group_id,
                        subgroup_id=subgroup_id,
                        text=f'{text_header} Новая очередь {text_ender}'
                    )
                )

                tg.create_task(
                    notify_members_about_queues(
                        group_id=group_id,
                        subgroup_id=subgroup_id,
                        text=f'{text_header} Очередь {text_ender}',
                        delay=3000
                    )
                )
    except Exception as e:
        await notify_admins_(
            text=f'Prerelease state mistake: {e}'
        )


async def release_queues():
    status_code, info_about_users_to_notify = await queues_info_db.release_queues()
    if status_code not in [sc.OPERATION_SUCCESS, sc.NO_QUEUES_IN_PRERELEASE]:
        await notify_admins_(
            text=f'Release state mistake: {get_message_about_status_code(status_code)}'
        )
        return
    try:
        async with asyncio.TaskGroup() as tg:
            for info in info_about_users_to_notify:
                subject = info[2]
                lesson_type = info[3]
                day_of_week = await get_day_by_num(info[4])
                tg.create_task(
                    notify_members_about_queues(
                        group_id=info[0],
                        subgroup_id=info[1],
                        text=f'[РЕЛИЗ] Открыта регистрация на очередь: {subject} [{lesson_type}] - {day_of_week}'
                    )
                )
    except Exception as e:
        await notify_admins_(
            text=f'Release state mistake: {e}'
        )


async def obsolete_queues():
    status_code = await queues_info_db.obsolete_queues_()
    if status_code != sc.OPERATION_SUCCESS:
        await notify_admins_(
            text='Obsolete state mistake: '
                 f'{get_message_about_status_code(status_code)}'
        )


async def notify_members_about_queues(group_id: int, subgroup_id, text: str, delay: int = 0):
    try:
        await asyncio.sleep(delay)

        if subgroup_id == 0:
            members_ids = await simple_get_members_by_group_id(group_id=group_id)
            text += ' - вся группа'
        else:
            members_ids = await get_members_by_group_id_and_subgroup_id(group_id=group_id, subgroup_id=subgroup_id)
            text += f' - {subgroup_id} подгруппа'
        await notify_users_if_news_turned_on_(members_ids, text)
    except Exception as e:
        await notify_admins_(
            text=f'Error in notify_members_about_queues: {e}'
        )


async def timer():
    time_to_prerelease = '19:0:0'
    time_to_release = '20:0:0'
    time_to_obsolete = '22:0:0'
    time_range: int = 5

    dt = datetime.strptime(time_to_prerelease, '%H:%M:%S')
    time_to_prerelease = dt.time()
    time_to_prerelease_range = (dt + timedelta(seconds=time_range)).time()

    dt = datetime.strptime(time_to_release, '%H:%M:%S')
    time_to_release = dt.time()
    time_to_release_range = (dt + timedelta(seconds=time_range)).time()

    notify_release_time = (dt + timedelta(hours=1)).time()

    dt = datetime.strptime(time_to_obsolete, '%H:%M:%S')
    time_to_obsolete = dt.time()
    time_to_obsolete_range = (dt + timedelta(seconds=time_range)).time()

    while True:
        now = datetime.now()
        now_time = time(now.hour, now.minute, now.second)

        if time_to_prerelease <= now_time <= time_to_prerelease_range:
            await prerelease_queues(notify_release_time)
            await asyncio.sleep(time_range * 2)

        elif time_to_release <= now_time <= time_to_release_range:
            await release_queues()
            await asyncio.sleep(time_range * 2)

        elif time_to_obsolete <= now_time <= time_to_obsolete_range:
            await obsolete_queues()
            await asyncio.sleep(time_range * 2)

        await asyncio.sleep(1)
