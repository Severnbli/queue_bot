import json
import aiohttp

from utils.status_codes import StatusCode as sc
import db.schedules_table_usage as schedulesdb
from utils.general_usage_funcs import get_num_of_day


async def get_schedule_by_request_(source: str, source_number: str):
    if source == 'bsuir':
        link = f'https://iis.bsuir.by/api/v1/schedule?studentGroup={source_number}'
        async with aiohttp.ClientSession() as session:
            async with session.get(link) as response:
                if response.status != 200 or not len(await response.text()):
                    return sc.BAD_REQUEST, None
            schedule: json = await response.json()
        return sc.OPERATION_SUCCESS, schedule
    else:
        return sc.UNKNOWN_SOURCE, None



async def upload_schedule(group_id: int, source: str, source_number: str):
    status_code, schedule = await get_schedule_by_request_(source, source_number)
    if status_code != sc.OPERATION_SUCCESS:
        return status_code
    for day in schedule['schedules']:
        num_of_day = await get_num_of_day(day)
        for lesson in schedule['schedules'][day]:
            lesson_type = lesson['lessonTypeAbbrev']
            subject = lesson['subject']
            subgroup = lesson['numSubgroup']
            week_numbers = lesson['weekNumber']
            status_code = await schedulesdb.add_schedule(
                group_id=group_id,
                subject=subject,
                lesson_type=lesson_type,
                subgroup=subgroup,
                weeks_of_month=week_numbers,
                day_of_week=num_of_day,
                is_in_schedule='false'
            )
            if status_code not in [sc.OPERATION_SUCCESS, sc.SAME_SCHEDULE_EXIST]:
                return status_code
    return sc.OPERATION_SUCCESS
