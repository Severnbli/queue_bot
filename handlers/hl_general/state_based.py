from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from fsm.general_states import GeneralStatesGroup
import db.groups_table_usage as groupsdb
import db.reports_table_usage as reportsdb
import db.members_table_usage as membersdb
import db.users_table_usage as usersdb
import db.queues_table_usage as queuesdb
import db.queues_info_table_usage as queues_info_db
import db.trades_table_usage as tradesdb
from status_codes import StatusCode as sc
from status_codes import get_message_about_status_code
from markups import reply_markups
import decorators
import schedule
from general_usage_funcs import make_easy_navigation, get_image_captcha

router = Router()


@router.message(F.text.lower() == '⛔️ выход / отмена')
@router.message(Command('cancel'))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    user_data = await state.get_data()
    is_non_stop = user_data.get('non_stop')
    if is_non_stop is not None and is_non_stop == True:
        await message.reply('Я не могу отменить. Это нечто важное.')
    else:
        back_step = user_data.get('back_step')
        await state.clear()
        if back_step is not None:
            if back_step == 'manage_profile':
                markup = await reply_markups.get_manage_profile_keyboard()
            elif back_step == 'manage_group':
                status_code, position = await membersdb.get_user_position_in_group(message.from_user.id)
                markup = await reply_markups.get_manage_group_keyboard(position)
            elif back_step == 'manage_queues':
                markup = await reply_markups.get_manage_queues_keyboard()
            elif back_step == 'queues_menu':
                markup = await reply_markups.get_queues_menu_keyboard()
            elif back_step == 'games':
                markup = await reply_markups.get_games_keyboard()
            else:
                markup = await reply_markups.get_main_keyboard()
        else:
            markup = await reply_markups.get_main_keyboard()
        await message.reply('Действие отменено успешно!', reply_markup=markup)


@router.message(GeneralStatesGroup.nick_input, F.text)
async def nick_input(message: Message, state: FSMContext) -> None:
    nick = message.text
    max_len = 10
    if len(nick) > max_len:
        output_message = f'Ник слишком длинный (максимум {max_len} символов).\n\nПопробуй придумать что-нибудь другое.'
        await message.answer(output_message)
        return
    nicks = await usersdb.get_all_nicks()
    if nick in nicks:
        await message.answer(
            text='Пользователь с таким ником существует. Придумай другой, пожалуйста.'
        )
        return
    output_message = f'Я запомню тебя как <b>{nick}</b>. Ты согласен?'
    await state.set_state(GeneralStatesGroup.nick_accepting)
    await state.update_data(nick=nick)
    await message.answer(
        output_message,
        parse_mode='HTML',
        reply_markup=await reply_markups.get_yes_or_no_keyboard()
    )


@router.message(GeneralStatesGroup.nick_accepting, F.text)
async def nick_accepting(message: Message, state: FSMContext) -> None:
    if message.text.lower() == 'да':
        user_data = await state.get_data()
        nick = user_data.get('nick')
        await state.clear()
        is_user_exist = await usersdb.is_user_exist_(user_id=message.from_user.id)
        if not is_user_exist:
            status_code = await usersdb.reg_user_(
                user_id=message.from_user.id,
                nick=nick,
                username=message.from_user.username
            )
            if status_code == sc.OPERATION_SUCCESS:
                output_message = (f'Хорошо, <b>{nick}</b>, ты теперь есть в моём секретном списочке.\n\n'
                                  f'Чего изволишь сделать?')
                await message.answer(
                    output_message,
                    parse_mode='HTML',
                    reply_markup=await reply_markups.get_main_keyboard()
                )
            else:
                output_message = (f'<b>{nick}</b>, произошла ошибка при попытке регистрации: '
                                  f'{await get_message_about_status_code(status_code)}.'
                                  f'\n\nРегистрация критически важна в моей исправной работе.'
                                  f'Срочно напиши моему создателю: https://t.me/g_een.')
                await message.answer(output_message, parse_mode='HTML', reply_markup=ReplyKeyboardRemove())
        else:
            status_code = await usersdb.update_nick_(user_id=message.from_user.id, nick=nick)
            if status_code != sc.OPERATION_SUCCESS:
                output_message = (f'Мне не удалось обновить твой ник. Причина: '
                                  f'{await get_message_about_status_code(status_code)}.')
                await message.answer(output_message, reply_markup=await reply_markups.get_manage_profile_keyboard())
            else:
                output_message = f'Твой ник успешно сменён на <b>{nick}</b>, возрадуйся же!'
                await message.answer(
                    output_message,
                    parse_mode='HTML',
                    reply_markup=await reply_markups.get_manage_profile_keyboard()
                )
    elif message.text.lower() == 'нет':
        user_data = await state.get_data()
        is_non_stop = user_data.get('non_stop')
        if is_non_stop is not None and is_non_stop == True:
            output_message = 'Придумай себе другой ник в следующем сообщении.'
            await state.set_state(GeneralStatesGroup.nick_input)
            await message.answer(output_message, reply_markup=ReplyKeyboardRemove())
        else:
            await state.clear()
            await message.answer(
                'Обновление ника отменено.',
                reply_markup=await reply_markups.get_manage_profile_keyboard()
            )
    else:
        await message.answer('Я хз, что ты написал.\n\nПопробуй хомяка, то есть кнопки, потапать.')


@router.message(GeneralStatesGroup.captcha, F.text)
@decorators.user_exists_required
async def captcha(message: Message, state: FSMContext) -> None:
    user_data = await state.get_data()
    captcha_text = user_data.get('captcha_text')
    if message.text == captcha_text:
        next_state = user_data.get('next_state')
        await state.clear()
        if next_state == 'report_writing':
            await state.set_state(GeneralStatesGroup.report_input)
            output_message = 'Изложи суть своего репорта в своём следующем сообщении.'
            await message.answer(output_message, reply_markup=await reply_markups.get_cancel_keyboard())
        elif next_state == 'trade_info_input':
            await state.set_state(GeneralStatesGroup.trade_info_input)
            await state.update_data(back_step='queues_menu')
            await message.answer(
                text='Введи информацию о трейде в формате <b>queue_id - required_place</b>.\n\n'
                     'queue_id ты сможешь найти во вкладке с информацией об очереди в строке "Айди для трейда"',
                parse_mode='HTML',
                reply_markup=await reply_markups.get_cancel_keyboard()
            )
        else:
            output_message = 'Проблемка вышла. Я не знаю, что дальше делать.'
            await message.answer(output_message, reply_markup=await reply_markups.get_main_keyboard())
    else:
        captcha_try = user_data.get('captcha_try')
        if captcha_try < 2:
            captcha_try += 1
            await state.update_data(captcha_try=captcha_try)
            output_message = f'Каптча введена неверно. У тебя ещё {3 - captcha_try} попытки.'
            await message.answer(output_message, reply_markup=await reply_markups.get_cancel_keyboard())
        else:
            await state.clear()
            output_message = 'Попытки ввода каптчи исчерпаны. Действие отменено.'
            await message.answer(output_message, reply_markup=await reply_markups.get_main_keyboard())


@router.message(GeneralStatesGroup.report_input, F.text)
@decorators.user_exists_required
async def report_input(message: Message, state: FSMContext) -> None:
    report_content = message.text
    if len(report_content) > 3900:
        output_message = (f'Твой репорт слишком большой (у тебя <b>{len(report_content)}</b> символов, а максимум <b>3900</b>).'
                           f'\n\nПопробуй ужать свой текст.')
        await message.answer(
            output_message,
            parse_mode='HTML',
            reply_markup=await reply_markups.get_cancel_keyboard()
        )
    else:
        await state.update_data(report_content=report_content)
        output_message = f'<b>Твой репорт</b>:\n{report_content}\n\n<b>Отправляем?</b>'
        await state.set_state(GeneralStatesGroup.report_accepting)
        await state.update_data(accept_info='report')
        await message.answer(
            output_message,
            parse_mode='HTML',
            reply_markup=await reply_markups.get_yes_or_no_keyboard()
        )


@router.message(GeneralStatesGroup.report_accepting, F.text)
@decorators.user_exists_required
async def report_accepting(message: Message, state: FSMContext) -> None:
    if message.text.lower() == 'да':
        user_data = await state.get_data()
        report_content = user_data.get('report_content')
        await state.clear()
        status_code, quantity_of_notified_admins, report_id = await reportsdb.reg_report(message.from_user.id, report_content)
        if status_code == sc.OPERATION_SUCCESS:
            quantity_of_unchecked_reports = await reportsdb.get_quantity_of_unchecked_reports()
            output_message = (f'<b>Репорт №{report_id} зарегистрирован</b>'
                              f'\n\nКоличество админов, извещённых о поступлении репорта: '
                              f'<b>{quantity_of_notified_admins}</b>.'
                              f' Репортов в очереди на настоящее время: <b>{quantity_of_unchecked_reports}</b>.'
                              f'\n\nОжидайте ответа.')
            await message.answer(
                output_message,
                parse_mode='HTML',
                reply_markup=await reply_markups.get_main_keyboard())
        else:
            output_message = (f'Возникла ошибка при отправке репорта: '
                               f'{await get_message_about_status_code(status_code)}.')
            await message.answer(output_message, reply_markup=await reply_markups.get_main_keyboard())
    elif message.text.lower() == 'нет':
        await state.clear()
        output_message = 'Отправка репорта отменена.'
        await message.answer(output_message, reply_markup=await reply_markups.get_main_keyboard())
    else:
        await message.answer('Я хз, что ты написал.\n\nПопробуй хомяка, то есть кнопки, потапать.')


@router.message(GeneralStatesGroup.group_name_input, F.text)
@decorators.user_exists_required
async def group_name_input(message: Message, state: FSMContext) -> None:
    group_name = message.text
    if len(group_name) > 20:
        output_message = (f'Слишком длинное название для группы (у тебя {len(group_name)} символов, а максимум 20). '
                           f'\n\nПопробуй снова.')
        await message.answer(
            output_message,
            reply_markup=await reply_markups.get_cancel_keyboard()
        )
    elif await groupsdb.is_group_with_such_name_exist(group_name):
        output_message = 'Группа с таким названием уже существует. Попробуй снова.'
        await message.answer(
            output_message,
            reply_markup=await reply_markups.get_cancel_keyboard()
        )
    else:
        status_code, position = await membersdb.get_user_position_in_group(message.from_user.id)
        await state.clear()
        is_in_group = await membersdb.is_user_in_group_(message.from_user.id)
        if not is_in_group:
            status_code = await groupsdb.reg_group_(message.from_user.id, group_name)
            if status_code != sc.OPERATION_SUCCESS:
                output_message = (f'При регистрации группы возникла ошибка: '
                                  f'{await get_message_about_status_code(status_code)}.')
                await message.answer(
                    output_message,
                    reply_markup=await reply_markups.get_manage_group_keyboard(position)
                )
                return
            status_code, key = await groupsdb.get_key_by_group_name(group_name)
            output_message = (f'Группа с названием <b>{group_name}</b> успешно зарегистрирована.'
                               f'\n\nУникальный ключ группы: <code>{key}</code>.')
            await message.answer(
                output_message,
                parse_mode='HTML',
                reply_markup=await reply_markups.get_manage_group_keyboard('leader')
            )
        else:
            status_code, group_id = await membersdb.get_group_id_by_user_id(message.from_user.id)
            if status_code != sc.OPERATION_SUCCESS:
                output_message = (f'При попытке изменении названии группы возникла ошибка: '
                                  f'{await get_message_about_status_code(status_code)}.')
                await message.answer(
                    output_message,
                    reply_markup=await reply_markups.get_manage_group_keyboard(position)
                )
                return
            status_code, old_name = await groupsdb.get_group_name_by_id(group_id)
            status_code = await groupsdb.set_group_name_by_group_id_(group_id=group_id, name=message.text)
            if status_code != sc.OPERATION_SUCCESS:
                output_message = (f'При попытке изменении названии группы возникла ошибка: '
                                  f'{await get_message_about_status_code(status_code)}.')
                await message.answer(
                    output_message,
                    reply_markup=await reply_markups.get_manage_group_keyboard(position)
                )
                return
            output_message = f'Название группы <b>{old_name}</b> сменено на <b>{group_name}</b>.'
            await message.answer(
                output_message,
                parse_mode='HTML',
                reply_markup=await reply_markups.get_manage_group_keyboard(position)
            )


@router.message(GeneralStatesGroup.subgroup_input, F.text)
@decorators.user_exists_required
@decorators.user_in_group_required
async def subgroup_input(message: Message, state: FSMContext) -> None:
    status_code, position = await membersdb.get_user_position_in_group(message.from_user.id)
    if message.text.lower() in ['1️⃣ подгруппа', '2️⃣ подгруппа']:
        await state.clear()
        if message.text.lower() == '1️⃣ подгруппа':
            status_code = await membersdb.set_subgroup(user_id=message.from_user.id, subgroup=1)
        elif message.text.lower() == '2️⃣ подгруппа':
            status_code = await membersdb.set_subgroup(user_id=message.from_user.id, subgroup=2)
        else:
            status_code = await membersdb.set_subgroup(user_id=message.from_user.id, subgroup=0)
        if status_code != sc.OPERATION_SUCCESS:
            output_message = (f'Во время установки номера подгруппы возникла ошибка: '
                              f'{await get_message_about_status_code(status_code)}.')
            await message.answer(
                output_message,
                reply_markup=await reply_markups.get_manage_group_keyboard(position)
            )
            return
        output_message = 'Номер подгруппы установлен успешно.'
        await message.answer(
            output_message,
            reply_markup=await reply_markups.get_manage_group_keyboard(position)
        )
    else:
        await message.answer('Я хз, что ты написал.\n\nПопробуй хомяка, то есть кнопки, потапать.')


@router.message(GeneralStatesGroup.key_input, F.text)
@decorators.user_exists_required
@decorators.user_not_in_group_required
async def key_input(message: Message, state: FSMContext) -> None:
    status_code, group_id = await groupsdb.get_group_id_by_key(message.text)
    if status_code == sc.GROUP_WITH_SUCH_KEY_NOT_EXIST:
        output_message = 'Группы с введёным уникальным ключом не существует. Попробуй снова.'
        await message.answer(
            output_message,
            reply_markup=await reply_markups.get_cancel_keyboard()
        )
    elif status_code == sc.OPERATION_SUCCESS:
        await state.clear()
        status_code = await membersdb.add_user_to_group_(
            user_id=message.from_user.id,
            group_id=group_id,
            position='default'
        )
        if status_code != sc.OPERATION_SUCCESS:
            output_message = (f'Во время добавления тебя в группу определилась ошибка:'
                              f'{await get_message_about_status_code(status_code)}.')
            await message.answer(
                output_message,
                reply_markup=await reply_markups.get_main_keyboard()
            )
            return
        status_code, group_name = await groupsdb.get_group_name_by_id(group_id)
        status_code, position = await membersdb.get_user_position_in_group(message.from_user.id)
        output_message = f'Ты успешно вступил в группу с названием <b>{group_name}</b>.'
        await message.answer(
            output_message,
            parse_mode='HTML',
            reply_markup=await reply_markups.get_manage_group_keyboard(position)
        )
    else:
        output_message = (f'Во время определения принадлежности уникального ключа определилась ошибка:'
                          f'{await get_message_about_status_code(status_code)}.')
        await message.answer(
            output_message,
            reply_markup=await reply_markups.get_cancel_keyboard()
        )


@router.message(GeneralStatesGroup.quit_accepting, F.text)
@decorators.user_exists_required
@decorators.user_in_group_required
@decorators.user_not_group_leader_required
async def quit_accepting(message: Message, state: FSMContext) -> None:
    status_code, position = await membersdb.get_user_position_in_group(message.from_user.id)
    if message.text.lower() == 'да':
        await state.clear()
        status_code = await membersdb.del_user_from_group_(message.from_user.id)
        if status_code == sc.OPERATION_SUCCESS:
            output_message = 'Ты успешно вышел из группы.'
            await message.answer(
                output_message,
                reply_markup=await reply_markups.get_main_keyboard()
            )
        else:
            output_message = (f'При попытке выхода из группы произошла ошибка: '
                              f'{await get_message_about_status_code(status_code)}.')
            await message.answer(
                output_message,
                reply_markup=await reply_markups.get_manage_group_keyboard(position)
            )
    elif message.text.lower() == 'нет':
        await state.clear()
        output_message = 'Выход из группы отменён.'
        await message.answer(
            output_message,
            reply_markup=await reply_markups.get_manage_group_keyboard(position)
        )
    else:
        await message.answer('Я хз, что ты написал.\n\nПопробуй хомяка, то есть кнопки, потапать.')


@router.message(GeneralStatesGroup.del_group_accepting, F.text)
@decorators.user_exists_required
@decorators.user_in_group_required
@decorators.user_group_leader_required
async def del_group_accepting(message: Message, state: FSMContext) -> None:
    status_code, position = await membersdb.get_user_position_in_group(message.from_user.id)
    if message.text.lower() == 'да':
        await state.clear()
        status_code, group_id = await membersdb.get_group_id_by_user_id(message.from_user.id)
        if status_code != sc.OPERATION_SUCCESS:
            output_message = (f'При определении группы, в которой ты состоишь, произошла ошибка: '
                              f'{await get_message_about_status_code(status_code)}.')
            await message.answer(
                output_message,
                reply_markup=await reply_markups.get_manage_group_keyboard(position)
            )
            return
        status_code = await groupsdb.del_group_(group_id)
        if status_code != sc.OPERATION_SUCCESS:
            output_message = (f'При удалении группы произошла ошибка: '
                              f'{await get_message_about_status_code(status_code)}.')
            await message.answer(
                output_message,
                reply_markup=await reply_markups.get_manage_group_keyboard(position)
            )
            return
        await queues_info_db.del_queues_info_by_group_id(group_id)
        output_message = 'Удаление группы завершено успешно.'
        await message.answer(
            output_message,
            reply_markup=await reply_markups.get_main_keyboard()
        )
    elif message.text.lower() == 'нет':
        await state.clear()
        output_message = 'Удаление группы отменено.'
        await message.answer(
            output_message,
            reply_markup=await reply_markups.get_manage_group_keyboard(position)
        )
    else:
        await message.answer('Я хз, что ты написал.\n\nПопробуй хомяка, то есть кнопки, потапать.')


# @router.message(GeneralStatesGroup.member_select, F.text)
# @decorators.user_exists_required
# @decorators.user_in_group_required
# @decorators.user_group_leader_or_depute_required
# async def manage_members(message: Message, state: FSMContext) -> None:
#     user_data = await state.get_data()
#     markups = user_data.get('markups')
#     now_page = user_data.get('now_page')
#     quantity_of_pages = user_data.get('quantity_of_pages')
#     nicks = user_data.get('nicks')
#     if message.forward_from:
#         status_code, expected_nick = await usersdb.get_nick(message.forward_from.id)
#         if status_code != sc.OPERATION_SUCCESS:
#             await message.answer(
#                 text='Произошла проблема при определении ника автора сообщения: '
#                      f'{await get_message_about_status_code(status_code)}.'
#             )
#             return
#     else:
#         parsed_entered_info = message.text.split(' ')
#         if len(parsed_entered_info) > 1:
#             expected_nick = parsed_entered_info[1]
#         else:
#             expected_nick = parsed_entered_info[0]
#     if message.text.lower() == '◀️ назад':
#         if now_page == 0:
#             await message.answer(
#                 text='Ты сейчас находишься на первой странице.'
#             )
#             return
#         now_page -= 1
#         await message.answer(
#             text=f'Выбрана <b>{now_page + 1}</b> страница. Всего страниц: <b>{quantity_of_pages}</b>.',
#             parse_mode='HTML',
#             reply_markup=markups[now_page]
#         )
#     elif message.text.lower() == '▶️ вперёд':
#         if now_page == quantity_of_pages - 1:
#             await message.answer(
#                 text='Ты сейчас находишься на последней странице.'
#             )
#             return
#         now_page += 1
#         await message.answer99(
#             text=f'Выбрана <b>{now_page + 1}</b> страница. Всего страниц: <b>{quantity_of_pages}</b>.',
#             parse_mode='HTML',
#             reply_markup=markups[now_page]
#         )
#     elif expected_nick is not None and expected_nick in nicks:
#         nick = expected_nick
#         await state.update_data(nick=nick, now_page=0)
#         await state.set_state(GeneralStatesGroup.manage_members)
#         status_code, position = await membersdb.get_user_position_in_group(message.from_user.id)
#         await message.answer(
#             text=f'Выбран участник с ником <b>{nick}</b>. Выбери действие, которое хочешь над ним совершить.',
#             parse_mode='HTML',
#             reply_markup=await reply_markups.get_manage_group_keyboard(position)
#         )
#     else:
#         await message.answer('Я хз, что ты написал.\n\nПопробуй хомяка, то есть кнопки, потапать.')


# @router.message(GeneralStatesGroup.manage_members, F.text)
# @decorators.user_exists_required
# @decorators.user_in_group_required
# @decorators.user_group_leader_or_depute_required
# async def member_edit(message: Message, state: FSMContext) -> None:
#     user_data = await state.get_data()
#     markups = user_data.get('markups')
#     nick = user_data.get('nick')
#     status_code, affected_user_id = await usersdb.get_user_id_by_nick(nick)
#     if status_code != sc.OPERATION_SUCCESS:
#         await state.set_state(GeneralStatesGroup.manage_members)
#         await message.answer(
#             text='На этапе определения данных пользователя, с которым производятся манипуляции, произошла ошибка: '
#                  f'{await get_message_about_status_code(status_code)}.',
#             reply_markup=markups[0]
#         )
#         return
#     is_users_in_same_group = await membersdb.is_users_in_same_group_(
#         user1_id=affected_user_id,
#         user2_id=message.from_user.id
#     )
#     if not is_users_in_same_group:
#         await state.set_state(GeneralStatesGroup.manage_members)
#         await message.answer(
#             text = 'Обнаружилась ошибка. Возможные причины:\n'
#                    '1. Редактируемый пользователь находится в иной подгруппе.\n'
#                    '2. Редактируемого пользователя не существует.\n'
#                    '3. Редактируемый пользователь вышел из группы / был забанен во время ваших манипуляций.',
#             reply_markup = markups[0]
#         )
#         return
#     status_code, affected_user_position = await membersdb.get_user_position_in_group(affected_user_id)
#     status_code, user_position = await membersdb.get_user_position_in_group(message.from_user.id)
#     if user_position not in ['leader', 'depute'] or affected_user_position not in ['leader', 'depute', 'default']:
#         await state.set_state(GeneralStatesGroup.manage_members)
#         await message.answer(
#             text='Произошла ошибка. Возможные причины:\n'
#                  '1. Не определена роль редактируемого пользователя.\n'
#                  '2. Ваша роль в группе недостаточна для редактирования других пользователей.',
#             reply_markup = markups[0]
#         )
#         return
#     if message.text.lower() == '🏴 добавление в чс':
#         if user_position == 'depute' and affected_user_position in ['leader', 'depute']:
#             await state.set_state(GeneralStatesGroup.manage_members)
#             await message.answer(
#                 text='Ты не можешь добавить в чс этого пользователя'
#             )


@router.message(GeneralStatesGroup.source_choose)
@decorators.user_exists_required
@decorators.user_in_group_required
@decorators.user_group_leader_or_depute_required
async def source_choose(message: Message, state: FSMContext) -> None:
    if message.text.lower() == 'bsuir':
        await state.set_state(GeneralStatesGroup.group_source_input)
        await state.update_data(source='bsuir')
        await message.answer(
            text='Введи номер своей группы.',
            reply_markup=await reply_markups.get_cancel_keyboard()
        )
    else:
        await message.answer(
            text='Я не знаю этого университета.',
            reply_markup=await reply_markups.get_source_keyboard()
        )


@router.message(GeneralStatesGroup.group_source_input)
@decorators.user_exists_required
@decorators.user_in_group_required
@decorators.user_group_leader_or_depute_required
async def group_source_input(message: Message, state: FSMContext) -> None:
    group_source = message.text
    await state.set_state(GeneralStatesGroup.group_source_accepting)
    await state.update_data(source_number=group_source)
    await message.answer(
        text=f'Номер твоей группы <b>{group_source}</b>. Я правильно тебя понял?',
        parse_mode='HTML',
        reply_markup=await reply_markups.get_yes_or_no_keyboard('Ты должен сделать выбор!')
    )


@router.message(GeneralStatesGroup.group_source_accepting)
@decorators.user_exists_required
@decorators.user_in_group_required
@decorators.user_group_leader_or_depute_required
async def group_source_accepting(message: Message, state: FSMContext) -> None:
    if message.text.lower() == 'да':
        status_code, group_id = await membersdb.get_group_id_by_user_id(message.from_user.id)
        if status_code != sc.OPERATION_SUCCESS:
            await state.clear()
            await message.answer(
                text='Произошла ошибка с определением группы, в которой ты состоишь: '
                     f'{await get_message_about_status_code(status_code)}.',
                reply_markup=await reply_markups.get_main_keyboard()
            )
            return
        user_data = await state.get_data()
        source = user_data['source']
        source_number = user_data['source_number']
        status_code = await schedule.upload_schedule(group_id, source, source_number)
        if status_code != sc.OPERATION_SUCCESS:
            await state.set_state(GeneralStatesGroup.group_source_input)
            await message.answer(
                text='При попытке получить / заполнить расписание определилась ошибка: '
                     f'{await get_message_about_status_code(status_code)}.\n\n'
                     f'Попробуй заново ввести номер группы.',
                reply_markup=await reply_markups.get_cancel_keyboard()
            )
            return
        await state.clear()
        await message.answer(
            text='Расписание загружено успешно. Чтобы его настроить, переходи в ручную настройку.',
            reply_markup=await reply_markups.get_manage_queues_keyboard()
        )
    elif message.text.lower() == 'нет':
        await state.set_state(GeneralStatesGroup.group_source_input)
        await message.answer(
            text='Напиши корректный номер своей группы ниже.',
            reply_markup=await reply_markups.get_cancel_keyboard()
        )
    else:
        await message.answer(
            text='Я хз, что ты написал.\n\nПопробуй хомяка, то есть кнопки, потапать.'
        )


@router.message(GeneralStatesGroup.queue_choose, F.text)
@decorators.user_exists_required
@decorators.user_in_group_required
async def queue_choose(message: Message, state: FSMContext) -> None:
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
        info_about_participate = user_data['info_about_participate']
        if message.text not in info_about_participate:
            await message.answer(
                text='Я хз, что ты написал.\n\nПопробуй хомяка, то есть кнопки, потапать.'
            )
            return
        split_message = message.text.split(' ')
        queue_info_id = int(split_message[-1])
        status_code = await queuesdb.del_or_add_user_to_queue(user_id=message.from_user.id, queue_info_id=queue_info_id)
        if status_code not in [sc.USER_ADD_TO_QUEUE_SUCCESSFULLY, sc.USER_DELETE_FROM_QUEUE_SUCCESSFULLY]:
            await message.answer(
                text='При манипуляциях с БД появилась ошибка: '
                     f'{await get_message_about_status_code(status_code)}.',
            )
            return
        status_code_participate, info_about_participate = await queues_info_db.get_information_about_queues_with_user_participation(
            user_id=message.from_user.id
        )
        if status_code_participate != sc.OPERATION_SUCCESS:
            await state.clear()
            await message.answer(
                text='При подгрузке очередей для участия произошла ошибка: '
                     f'{await get_message_about_status_code(status_code_participate)}.',
                reply_markup=await reply_markups.get_queues_menu_keyboard()
            )
            return
        markups, quantity_of_new_pages = \
            await reply_markups.parse_some_information_to_make_easy_navigation(info_about_participate, 2)
        if quantity_of_new_pages != quantity_of_pages:
            now_page = 0
        await state.update_data(markups=markups, now_page=now_page, quantity_of_pages=quantity_of_new_pages,
                                info_about_participate=info_about_participate)
        prepared_information_about_queue_to_message = ' '.join(split_message[1:-2])
        if status_code == sc.USER_ADD_TO_QUEUE_SUCCESSFULLY:
            output_message = (f'Регистрация на очередь <b>{prepared_information_about_queue_to_message}</b> завершена '
                              f'успешно.')
        else:
            output_message = (f'Отмена регистрации на очередь <b>{prepared_information_about_queue_to_message}</b> завершена '
                              f'успешно.')
        await message.answer(
            text=output_message,
            parse_mode='HTML',
            reply_markup=markups[now_page]
        )
    else:
        await message.answer(
            text=f'Непредвиденный статус-код: {await get_message_about_status_code(status_code)}.',
        )


@router.message(GeneralStatesGroup.queues_viewing, F.text)
@decorators.user_exists_required
@decorators.user_in_group_required
async def queues_viewing(message: Message, state: FSMContext) -> None:
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
        info_in_buttons = user_data['info_in_buttons']
        if message.text not in info_in_buttons:
            await message.answer(
                text='Я хз, что ты написал.\n\nПопробуй хомяка, то есть кнопки, потапать.'
            )
            return
        split_message = message.text.split(' ')
        queue_info_id = int(split_message[-1])
        status_code, header = await queues_info_db.get_information_to_make_header(queues_info_id=queue_info_id)
        if status_code != sc.OPERATION_SUCCESS:
            await state.clear()
            await message.answer(
                text='При подгрузке информации об очереди произошла ошибка: '
                     f'{await get_message_about_status_code(status_code)}.',
                reply_markup=await reply_markups.get_queues_menu_keyboard()
            )
            return
        status_code, participants = await queuesdb.get_information_users_participate_queue(queue_info_id=queue_info_id)
        if status_code != sc.OPERATION_SUCCESS:
            await state.clear()
            await message.answer(
                text='При подгрузке информации об очереди произошла ошибка: '
                     f'{await get_message_about_status_code(status_code)}.',
                reply_markup=await reply_markups.get_queues_menu_keyboard()
            )
            return
        await message.answer(
            text=f'{header}\n\n{participants}',
            parse_mode='HTML'
        )
    else:
        await message.answer(
            text=f'Непредвиденный статус-код: {await get_message_about_status_code(status_code)}.',
        )


@router.message(GeneralStatesGroup.trade_info_input, F.text)
@decorators.user_exists_required
@decorators.user_in_group_required
async def trade_info_input(message: Message, state: FSMContext) -> None:
    split_message = message.text.split(' ')
    if len(split_message) < 3:
        await message.answer(
            text='Введи информацию для трейда по предложенному формату: '
                 '<b>queue_id - required_place</b>.',
            parse_mode='HTML'
        )
    try:
        queue_info_id = int(split_message[0])
        required_place = int(split_message[2])
    except ValueError:
        await message.answer(
            text='Введённая информация не соответствует нужным типам: они оба должны быть целочисленными.'
        )
        return
    status_code = await tradesdb.reg_trade_by_place_in_queue_(
        sender_id=message.from_user.id,
        place=required_place,
        queue_info_id=queue_info_id
    )
    if status_code != sc.OPERATION_SUCCESS:
        await message.answer(
            text='При попытке формирования трейда возникла ошибка: '
                 f'{await get_message_about_status_code(status_code)}.'
        )
        return
    await state.clear()
    await message.answer(
        text='Трейд отправлен успешно. Ждём-с ответа от получателя!',
        reply_markup=await reply_markups.get_queues_menu_keyboard()
    )


@router.message(GeneralStatesGroup.captcha_game_setup, F.text)
@decorators.user_exists_required
async def captcha_game_setup(message: Message, state: FSMContext) -> None:
    CAPTCHA_GAME_MIN_PARAMETER: int = 1
    CAPTCHA_GAME_MAX_PARAMETER: int = 20
    try:
        setup_parameter = int(message.text)
        if setup_parameter < CAPTCHA_GAME_MIN_PARAMETER or setup_parameter > CAPTCHA_GAME_MAX_PARAMETER:
            await message.answer(
                text=f'Введённое число не подходит для игры. Задай число в пределе от {CAPTCHA_GAME_MIN_PARAMETER} '
                     f'до {CAPTCHA_GAME_MAX_PARAMETER}.'
            )
            return
    except ValueError:
        await message.answer(
            text='Введёный параметр не годится для игры. Попробуй придумать другой.'
        )
        return
    captcha_image, captcha_text = await get_image_captcha(setup_parameter)
    await state.set_state(GeneralStatesGroup.captcha_game_process)
    await state.update_data(setup_parameter=setup_parameter, captcha_text=captcha_text, captcha_try=0)
    await message.answer_photo(
        photo=captcha_image,
        caption='Попробуй отгадать каптчу!',
        reply_markup=await reply_markups.get_cancel_keyboard()
    )


@router.message(GeneralStatesGroup.captcha_game_process, F.text)
@decorators.user_exists_required
async def captcha_game_process(message: Message, state: FSMContext) -> None:
    user_data = await state.get_data()
    captcha_text = user_data['captcha_text']
    if message.text != captcha_text:
        captcha_try = user_data['captcha_try']
        captcha_try += 1
        if captcha_try == 3:
            setup_parameter = user_data['setup_parameter']
            captcha_image, captcha_text = await get_image_captcha(setup_parameter)
            await state.update_data(captcha_text=captcha_text, captcha_try=0)
            await message.answer_photo(
                photo=captcha_image,
                caption='Ты исчерпал три попытки. Держи новую каптчу!',
                reply_markup=await reply_markups.get_cancel_keyboard()
            )
            return
        await state.update_data(captcha_try=captcha_try)
        await message.answer(
            text=f'У тебя ещё {3 - captcha_try} попытки. У тебя получится!'
        )
        return
    else:
        setup_parameter = user_data['setup_parameter']
        captcha_image, captcha_text = await get_image_captcha(setup_parameter)
        await state.update_data(captcha_text=captcha_text, captcha_try=0)
        await message.answer_photo(
            photo=captcha_image,
            caption='Ты разгадал каптчу! Держи новую!',
            reply_markup=await reply_markups.get_cancel_keyboard()
        )
        return


@router.message(GeneralStatesGroup.nick_accepting)
@router.message(GeneralStatesGroup.report_accepting)
@router.message(GeneralStatesGroup.subgroup_input)
@router.message(GeneralStatesGroup.quit_accepting)
@router.message(GeneralStatesGroup.del_group_accepting)
@router.message(GeneralStatesGroup.member_select)
@router.message(GeneralStatesGroup.manage_members)
@router.message(GeneralStatesGroup.source_choose)
@router.message(GeneralStatesGroup.group_source_accepting)
@router.message(GeneralStatesGroup.queue_choose)
@router.message(GeneralStatesGroup.queues_viewing)
async def tap_on_button_pls(message: Message) -> None:
    await message.reply('Для свершения какого-либо действия требуется твоё нажатие на представленные кнопки.'
                        '\n\nЕсли передумал, то /cancel.')


@router.message(GeneralStatesGroup.captcha_game_setup)
@router.message(GeneralStatesGroup.captcha_game_process)
@router.message(GeneralStatesGroup.nick_input)
@router.message(GeneralStatesGroup.captcha)
@router.message(GeneralStatesGroup.report_input)
@router.message(GeneralStatesGroup.group_name_input)
@router.message(GeneralStatesGroup.key_input)
@router.message(GeneralStatesGroup.group_name_input)
@router.message(GeneralStatesGroup.trade_info_input)
async def needed_text(message: Message) -> None:
    await message.reply('Отлично. Но я просил отправить мне текст.\n\nПопробуй снова или отмени действие: /cancel.')


@router.message(F.text)
@decorators.user_exists_required
async def unknown_message(message: Message) -> None:
    await message.answer(
        text='Я тебя не понял.\n\nПопробуй отменить действие: /cancel.'
    )