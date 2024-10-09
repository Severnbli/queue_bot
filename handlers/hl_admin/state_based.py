from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from fsm.general_states import GeneralStatesGroup
from general_usage_funcs import make_easy_navigation
from status_codes import StatusCode as sc
from status_codes import get_message_about_status_code
from markups import reply_markups
import db.reports_table_usage as reportsdb
import db.users_table_usage as usersdb


router = Router()


@router.message(F.text.lower() == '⛔️ выход / отмена')
@router.message(Command('cancel'))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        text='Действие успешно отменено.',
        reply_markup=await reply_markups.get_main_keyboard()
    )

@router.message(F.text.lower() == '◀️ к выбору действия с репортом')
async def return_to_report_manage(message: Message, state: FSMContext) -> None:
    await state.set_state(GeneralStatesGroup.report_checking)
    user_data = await state.get_data()
    report_id = user_data['now_report_id']
    sender_id = user_data['now_report_sender_id']
    content = user_data['now_report_content']
    await message.answer(
        text=f'<b>Репорт №{report_id} от {sender_id}</b>\n\n{content}',
        parse_mode='HTML',
        reply_markup=await reply_markups.get_manage_report_keyboard()
    )


@router.message(GeneralStatesGroup.report_checking, F.text.lower() == '◀️ к выбору репорта')
async def return_to_report_choose(message: Message, state: FSMContext) -> None:
    user_data = await state.get_data()
    markups = user_data['markups']
    now_page = user_data['now_page']
    await message.answer(
        text='Выбери репорт для свершения какого-либо действия.',
        reply_markup=markups[now_page]
    )


@router.message(GeneralStatesGroup.report_checking, F.text.lower() == '✏️ написать ответ')
async def report_answer(message: Message, state: FSMContext):
    await state.set_state(GeneralStatesGroup.report_answer_input)
    await message.answer(
        text='Напиши ответ на репорт в следующем сообщении.',
        reply_markup=await reply_markups.get_return_to_manage_report_keyboard()
    )


@router.message(GeneralStatesGroup.report_checking, F.text.lower() == '✅ пометить прочитанным')
async def report_make_checked(message: Message, state: FSMContext):
    user_data = await state.get_data()
    report_id = user_data['now_report_id']
    status_code = await reportsdb.make_report_checked_(report_id)
    await message.answer(
        text='Пометка репорта прочитанным завершилась со статусом: '
             f'{await get_message_about_status_code(status_code)}.',
    )
    await get_new_keyboard_for_report_checking(message, state, report_id)


@router.message(GeneralStatesGroup.report_answer_input)
async def report_answer_input(message: Message, state: FSMContext):
    await state.set_state(GeneralStatesGroup.report_answer_accepting)
    await state.update_data(report_answer=message.text)
    await message.answer(
        text=f'<b>Ответим на репорт так?</b>\n\n{message.text}',
        parse_mode='HTML',
        reply_markup=await reply_markups.get_yes_or_no_for_report_answering()
    )


async def get_new_keyboard_for_report_checking(message: Message, state: FSMContext, report_id_to_remove: int):
    user_data = await state.get_data()
    quantity_of_now_pages = user_data['quantity_of_pages']
    now_page = user_data['now_page']
    info_for_make_buttons: list = user_data['info_for_make_buttons']
    unchecked_reports = user_data['unchecked_reports']
    await state.clear()
    info_for_make_buttons.remove(report_id_to_remove)
    if len(info_for_make_buttons) == 0:
        await message.answer(
            text='Репорты для проверки закончились.',
            reply_markup=await reply_markups.get_main_keyboard()
        )
        return
    await state.set_state(GeneralStatesGroup.report_checking)
    markups, quantity_of_new_pages = await reply_markups.parse_some_information_to_make_easy_navigation(
        content=tuple(info_for_make_buttons),
        adjust_param=4
    )
    if quantity_of_now_pages != quantity_of_new_pages:
        now_page = 0
    await state.update_data(markups=markups, quantity_of_pages=quantity_of_new_pages, now_page=now_page,
                            unchecked_reports=unchecked_reports, info_for_make_buttons=info_for_make_buttons)
    await message.answer(
        text='Выбери репорт для дальнейшего просмотра.',
        reply_markup=markups[now_page]
    )


@router.message(GeneralStatesGroup.report_answer_accepting)
async def report_answer_accepting(message: Message, state: FSMContext):
    if message.text.lower() == 'да':
        user_data = await state.get_data()
        report_id = user_data['now_report_id']
        sender_id = user_data['now_report_sender_id']
        answer_content = user_data['report_answer']
        status_code = await reportsdb.send_answer_on_report_(
            report_id=report_id,
            sender_id=sender_id,
            answer_content=answer_content
        )
        await message.answer(
            text=f'Ответ на репорт завершён со статусом: {await get_message_about_status_code(status_code)}'
        )
        await get_new_keyboard_for_report_checking(message, state, report_id)
    elif message.text.lower() == 'нет':
        await state.set_state(GeneralStatesGroup.report_answer_input)
        await message.answer(
            text='Напиши ответ на репорт в следующем сообщении',
            reply_markup=await reply_markups.get_return_to_manage_report_keyboard()
        )
    else:
        await message.answer(
            text='Тапай кнопки, bull shit!'
        )


@router.message(GeneralStatesGroup.report_checking)
async def report_checking(message: Message, state: FSMContext):
    user_data = await state.get_data()
    now_page = user_data['now_page']
    markups = user_data['markups']
    quantity_of_pages = user_data['quantity_of_pages']
    status_code = await make_easy_navigation(
        message=message,
        now_page=now_page,
        quantity_of_pages=quantity_of_pages,
        markups=markups,
        state=state
    )
    if status_code == sc.NOTHING_NEEDED_TO_DO:
        return
    elif status_code == sc.NEEDED_TEXT_PROCESSING:
        info_in_buttons = user_data['info_for_make_buttons']
        try:
           report_id = int(message.text)
        except ValueError:
            await message.answer(
                text='Приведение типа сработало некорректно.'
            )
            return
        if report_id not in info_in_buttons:
            await message.answer(
                text='Я хз, что ты написал.\n\nПопробуй хомяка, то есть кнопки, потапать.'
            )
            return
        sender_id = None
        content = None
        unchecked_reports = user_data['unchecked_reports']
        for unchecked_report in unchecked_reports:
            if unchecked_report['report_id'] == report_id:
                sender_id = unchecked_report['sender_id']
                content = unchecked_report['content']
                break
        await state.update_data(now_report_id=report_id, now_report_sender_id=sender_id,
                                now_report_content=content)
        await message.answer(
            text=f'<b>Репорт №{report_id} от {sender_id}</b>\n\n{content}',
            parse_mode='HTML',
            reply_markup=await reply_markups.get_manage_report_keyboard()
        ),
    else:
        await message.answer(
            text=f'Непредвиденный статус-код: {await get_message_about_status_code(status_code)}.',
        )


@router.message(GeneralStatesGroup.say_input)
async def say_input(message: Message, state: FSMContext):
    await state.set_state(GeneralStatesGroup.say_accepting)
    await state.update_data(say_text=message.text)

    await message.answer(
        text=f'<b>Следующая информация будет разослана всем пользователям</b>\n\n{message.text}\n\n<b>Отправляем?</b>',
        parse_mode='HTML',
        reply_markup=await reply_markups.get_yes_or_no_keyboard()
    )
