from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import db.reports_table_usage as reportsdb
from fsm.general_states import GeneralStatesGroup
from status_codes import StatusCode as sc
from status_codes import get_message_about_status_code
from markups import reply_markups


router = Router()
router.message.filter(StateFilter(None))


@router.message(Command('areport'))
async def cmd_areport(message: Message, state: FSMContext):
    status_code, unchecked_reports = await reportsdb.get_unchecked_report()
    if status_code != sc.OPERATION_SUCCESS:
        await message.answer(
            text='Не смог подгрузить репорты для проверки: '
                 f'{await get_message_about_status_code(status_code)}'
        )
        return
    info_for_make_buttons = []
    for report in unchecked_reports:
        info_for_make_buttons.append(report["report_id"])
    print(info_for_make_buttons)
    markups, quantity_of_pages = await reply_markups.parse_some_information_to_make_easy_navigation(
        content=tuple(info_for_make_buttons),
        adjust_param=4
    )
    now_page = 0
    await state.set_state(GeneralStatesGroup.report_checking)
    await state.update_data(markups=markups, quantity_of_pages=quantity_of_pages, now_page=now_page, 
                            unchecked_reports=unchecked_reports, info_for_make_buttons=info_for_make_buttons)
    await message.answer(
        text='Выбери репорт для формирования ответа.',
        reply_markup=markups[now_page]
    )


@router.message(Command('say'))
async def cmd_say(message: Message, state: FSMContext):
    await state.set_state(GeneralStatesGroup.say_input)
    await message.answer(
        text='Отправь сообщение, которое хочешь разослать всем пользователям.',
        reply_markup=await reply_markups.get_cancel_keyboard()
    )