import random
import string

from aiogram.fsm.context import FSMContext
from captcha.image import ImageCaptcha
from aiogram.types import BufferedInputFile
from io import BytesIO
import aiohttp
from datetime import datetime, timedelta
from aiogram.types import Message, ReplyKeyboardMarkup

from utils.status_codes import StatusCode as sc


async def get_random_str(length: int) -> str:
    characters = string.ascii_letters + string.digits + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string


async def get_subgroup_name(id_of_subgroup: int) -> str:
    if id_of_subgroup == 0:
        return 'общая'
    elif id_of_subgroup == 1:
        return 'первая'
    elif id_of_subgroup == 2:
        return 'вторая'
    else:
        return 'неизвестная'


async def get_image_captcha(length: int) -> tuple[BufferedInputFile, str]:
    image_captcha = ImageCaptcha(
        width=250,
        height=150,
        fonts=[
            'fonts/2.ttf',
            'fonts/3.ttf',
            'fonts/4.otf'
               ],
        font_sizes=(50, 70, 100, 120, 80)
    )
    captcha_text = await get_random_str(length)
    captcha_text = captcha_text.upper()
    data: BytesIO = image_captcha.generate(captcha_text)
    captcha_image = BufferedInputFile(file=data.read(), filename='captcha.png')
    return captcha_image, captcha_text

async def prepare_tuple_info_for_buttons(content: tuple) -> tuple: # In one tuple another tuple
    iterator = 0
    prepared_info = []
    for info in content:
        iterator += 1
        buffer = f'{iterator}. '
        for part_of_info in info:
            buffer += f'{str(part_of_info)}'
            if part_of_info is not info[-1]:
                buffer += ' '
        prepared_info.append(buffer)
    return tuple(prepared_info)


async def prepare_all_members_info_to_pretty_form(members: list) -> tuple:
    prepared_members = []
    for member in members:
        info_about_member = []
        if member[3] == 'leader':
            rang = '👑 '
        elif member[3] == 'depute':
            rang = '🎖 '
        else:
            rang = ''
        info_about_member.append(f'{rang}{str(member[0])}')
        if member[1] is not None:
            info_about_member.append(f'@{str(member[1])}')
        prepared_members.append(info_about_member)
    return tuple(prepared_members)


async def get_num_of_day(day: str) -> int:
    days_of_week = {
        'Понедельник': 0,
        'Вторник': 1,
        'Среда': 2,
        'Четверг': 3,
        'Пятница': 4,
        'Суббота': 5,
        'Воскресенье': 6
    }
    return days_of_week[day]


async def get_day_by_num(num: int) -> str:
    days_of_week = {
        0: 'ПН',
        1: 'ВТ',
        2: 'СР',
        3: 'ЧТ',
        4: 'ПТ',
        5: 'СБ',
        6: 'ВС'
    }
    return days_of_week[num]


async def get_day_of_week() -> int:
    now_date = datetime.now()
    day_of_week = now_date.weekday()
    return day_of_week


async def get_week_of_month():
    link = 'https://iis.bsuir.by/api/v1/schedule/current-week'
    async with aiohttp.ClientSession() as session:
        async with session.get(link) as response:
            if response.status != 200 or not len(await response.text()):
                return None
            week_of_month = await response.text()
    if week_of_month is not None:
        week_of_month = int(week_of_month)
    return week_of_month


async def get_next_day_of_week():
    date = datetime.now() + timedelta(days=1)
    day_of_week = date.weekday()
    return day_of_week


async def get_next_day_week_of_month():
    now_week_of_month = await get_week_of_month()
    if now_week_of_month is None:
        return None
    now_day_of_week = await get_day_of_week()
    if now_day_of_week == 6:
        if now_week_of_month == 4:
            next_day_week_of_month = 1
        else:
            next_day_week_of_month = now_week_of_month + 1
    else:
        next_day_week_of_month = now_week_of_month
    return next_day_week_of_month


async def make_easy_navigation(
        message: Message,
        now_page: int,
        quantity_of_pages,
        markups: ReplyKeyboardMarkup,
        state: FSMContext) -> int:
    if message.text.lower() == '◀️ назад':
        if now_page == 0:
            await message.answer(
                text='Ты сейчас находишься на первой странице.'
            )
        now_page -= 1
        await state.update_data(now_page=now_page)
        await message.answer(
            text=f'Выбрана <b>{now_page + 1}</b> страница. Всего страниц: <b>{quantity_of_pages}</b>.',
            parse_mode='HTML',
            reply_markup=markups[now_page]
        )
        return sc.NOTHING_NEEDED_TO_DO
    elif message.text.lower() == '▶️ вперёд':
        if now_page == quantity_of_pages - 1:
            await message.answer(
                text='Ты сейчас находишься на последней странице.'
            )
        now_page += 1
        await state.update_data(now_page=now_page)
        await message.answer(
            text=f'Выбрана <b>{now_page + 1}</b> страница. Всего страниц: <b>{quantity_of_pages}</b>.',
            parse_mode='HTML',
            reply_markup=markups[now_page]
        )
        return sc.NOTHING_NEEDED_TO_DO
    else:
        return sc.NEEDED_TEXT_PROCESSING
