from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, ReplyKeyboardRemove, FSInputFile
from aiogram.fsm.context import FSMContext
import os
import random

from fsm.general_states import GeneralStatesGroup
import db.users_table_usage as usersdb
import db.members_table_usage as membersdb
import db.groups_table_usage as groupsdb
import db.queues_info_table_usage as queues_info_db
import db.queues_table_usage as queuesdb
import db.trades_table_usage as tradesdb
from utils.status_codes import StatusCode as sc, get_message_about_status_code
from utils.status_codes import get_message_about_error
from utils.general_usage_funcs import (get_image_captcha)
from markups import reply_markups
from utils import decorators

router = Router()
router.message.filter(StateFilter(None))


@router.message(F.text.lower() == '🐈 мяу-мяу')
@router.message(Command('meow'))
async def cmd_meow(message: Message):
    folder_path = 'photos/memes'
    files = os.listdir(folder_path)
    images = [f for f in files if f.endswith(('.jpg', '.jpeg', '.png'))]
    if not images:
        await message.answer('Мяу-мяу')
        return
    random_image = random.choice(images)
    photo_path = os.path.join(folder_path, random_image)
    await message.answer_photo(photo=FSInputFile(photo_path))


@router.message(F.text.lower() == '⛔️ выход / отмена')
@router.message(Command('cancel'))
@decorators.user_exists_required
async def cmd_cancel_no_state(message: Message, state: FSMContext):
    user_data = await state.get_data()
    is_non_stop = user_data.get('non_stop')
    if is_non_stop is not None and is_non_stop == True:
        await message.reply('Я не могу отменить. Это нечто важное.')
    else:
        await state.clear()
        await message.reply('Ты по-моему перепутал. Тут нечего отменять.\n\nХотя... Отменяю первую пару!',
                        reply_markup=await reply_markups.get_main_keyboard())


@router.message(F.text.lower() == '◀️ в главное меню')
@router.message(Command('main_menu'))
@decorators.user_exists_required
async def cmd_main_menu(message: Message):
    await message.answer(
        text='Главное меню вызвано успешно.',
        reply_markup=await reply_markups.get_main_keyboard()
    )


@router.message(F.text.lower() == '®️ зарегистрироваться')
@router.message(Command('start'))
async def cmd_start(message: Message, state: FSMContext) -> None:
    is_user_exist = await usersdb.is_user_exist_(user_id=message.from_user.id)

    quantity_of_total_users = await usersdb.get_quantity_of_total_users_()

    if is_user_exist:
        status_code, nick = await usersdb.get_nick(user_id=message.from_user.id)

        if status_code != sc.OPERATION_SUCCESS:
            output_message = await get_message_about_error(status_code=status_code)

        else:
            output_message = (f'Привет, <b>{nick}</b>. '
                              f'Нас уже <b>{quantity_of_total_users}</b>!'
                              f'\n\nСписок команд: /help.')

        await message.answer(
            text=output_message,
            parse_mode='HTML',
            reply_markup=await reply_markups.get_main_keyboard()
        )

    else:
        await state.set_state(GeneralStatesGroup.nick_input)
        await state.update_data(non_stop=True)

        output_message = (f'Я бот для создания очередей. Список команд: /help.'
                          f'\n\nПрисоединяйся, нас уже <b>{quantity_of_total_users}</b>!'
                          f'\n\nКак я могу тебя называть? Ты всегда сможешь сменить ник с помощью /nick.')

        await message.answer(
            text=output_message,
            parse_mode='HTML',
            reply_markup=ReplyKeyboardRemove()
        )


@router.message(F.text.lower() == '⚡️ команды')
@router.message(Command('help'))
@decorators.user_exists_required
async def cmd_help(message: Message) -> None:
    output_message = (
        '<b>Основные команды</b>\n'
        '/cancel - отменить что-либо\n'
        '/report - написать админам (жалобы, предложения)\n'
        '/main_menu - вызов главного меню\n'
        '/captcha_game - игра в каптчу\n'
        '\n<b>Взаимодействие с очередями</b>\n'
        '/queues - вызов меню очередей\n'
        '/reg - регистрация / отмена регистрации\n'
        '/view - просмотр твоих регистраций и информации об очередях\n'
        '/trade - вызов меню трейда\n'
        '/accept trade_id - одобрить трейд\n'
        '\n<b>Взаимодействие с профилем</b>\n'
        '/manage_profile - управление информацией о тебе\n'
        '/profile - отобразить информацию о тебе\n'
        '/nick - изменить имя\n'
        '/link - обновить ссылку на тебя (подгружается автоматически)\n'
        '/subscription - включение / отключение подписки на обновления\n'
        '\n<b>Взаимодействие с группой</b>\n'
        '/join - присоединиться к группе\n'
        '/quit - выход из группы\n'
        '/members - просмотреть состав группы\n'
        '/subgroup - изменение своего номера подгруппы\n'
        '/new_group - создать группу\n'
        '/group_info - информация о группе, в которой ты состоишь\n'
        '\n<b>Лидеры и замы группы</b>\n'
        '/manage_group - управление группой\n'
        '/manage_members - управление участниками\n'
        '/manage_queues - управление очередями\n'
        '/key - информация об уникальном ключе группы\n'
        '/keygen - генерация нового уникального ключа\n'
        '/source - подгрузка очереди с официального сайта\n'
        '/hand_made - ручная настройка расписания\n'
        '/rename - переименование группы\n'
        '/del_group - удаление группы\n'
        ''
    )
    await message.answer(output_message, parse_mode='HTML')


@router.message(F.text.lower() == '✏️ сменить имя')
@router.message(Command('nick'))
@decorators.user_exists_required
async def cmd_nick(message: Message, state: FSMContext):
    await state.set_state(GeneralStatesGroup.nick_input)
    await state.update_data(back_step='manage_profile')
    output_message = 'Хорошенько подумай над ником и представь его мне в следующем сообщении.'
    await message.answer(output_message, reply_markup=await reply_markups.get_cancel_keyboard())


@router.message(F.text.lower() == '💬 репорт')
@router.message(Command('report'))
@decorators.user_exists_required
async def cmd_report(message: Message, state: FSMContext) -> None:
    await state.set_state(GeneralStatesGroup.captcha)
    await state.update_data(next_state='report_writing')
    captcha_image, captcha_text = await get_image_captcha(6)
    await state.update_data(captcha_text=captcha_text, captcha_try=0)
    await message.answer_photo(
        photo=captcha_image,
        caption='Реши каптчу, чтобы отправить репорт.',
        reply_markup=await reply_markups.get_cancel_keyboard()
    )


@router.message(F.text.lower() == '👤 профиль')
@router.message(Command('manage_profile'))
@decorators.user_exists_required
async def cmd_manage_profile(message: Message) -> None:
    output_message = 'Выбери, что ты хочешь сделать со своим профилем.'
    await message.answer(output_message, reply_markup=await reply_markups.get_manage_profile_keyboard())


@router.message(F.text.lower() == '🧾 информация о тебе')
@router.message(Command('profile'))
@decorators.user_exists_required
async def cmd_profile(message: Message) -> None:
    status_code, info_about_user = await usersdb.get_user_info(message.from_user.id)
    if status_code == sc.OPERATION_SUCCESS:
        output_message = f'<b>Информация о тебе</b>\n\n{info_about_user}'
        await message.answer(
            output_message,
            parse_mode='HTML',
            disable_web_page_preview=True
        )
    else:
        output_message = f'Я не смог найти информацию о тебе: {await get_message_about_status_code(status_code)}.'
        await message.answer(output_message)


@router.message(F.text.lower() == '🌐 подгрузить ссылку')
@router.message(Command('link'))
@decorators.user_exists_required
async def cmd_link(message: Message) -> None:
    if message.from_user.username is None:
        output_message = ('Для того, чтобы я мог подгрузить твою ссылку, <u>тебе нужно настроить свой телеграм-аккаунт</u>: '
                          '<i>Главное окно -> Три палки (слева сверху) -> Настройки -> Имя пользователя (под номером '
                          'телефона)</i>.')
        await message.answer(
            output_message,
            parse_mode='HTML'
        )
        return
    status_code = await usersdb.update_link_(message.from_user.id, message.from_user.username)
    if status_code == sc.OPERATION_SUCCESS:
        output_message = f'Твоя ссылка теперь выглядит следующим образом: @{message.from_user.username}.'
        await message.answer(
            output_message
        )
    else:
        output_message = f'При подгрузке ссылки возникла ошибка: {await get_message_about_status_code(status_code)}.'
        await message.answer(
            output_message
        )


@router.message(F.text.lower() == '✏️ включение / отключение подписки на обновления')
@router.message(Command('subscription'))
@decorators.user_exists_required
async def cmd_subscription(message: Message) -> None:
    status_code = await usersdb.turn_on_off_subscription_(user_id=message.from_user.id)
    if status_code != sc.OPERATION_SUCCESS:
        await message.answer(
            text='При смене статуса подписки произошла ошибка: '
                 f'{await get_message_about_status_code(status_code)}.'
        )
        return
    status_code, info_about_status_of_news = await usersdb.get_info_about_status_of_news(user_id=message.from_user.id)
    if status_code != sc.OPERATION_SUCCESS:
        await message.answer(
            text='При получении статуса подписки произошла ошибка: '
                 f'{await get_message_about_status_code(status_code)}.'
        )
        return
    await message.answer(
        text=info_about_status_of_news,
        parse_mode='HTML'
    )

@router.message(F.text.lower() == '◀️ в группу')
@router.message(F.text.lower() == '👥 группа')
@router.message(Command('manage_group'))
@decorators.user_exists_required
async def cmd_manage_group(message: Message) -> None:
    is_in_group = await membersdb.is_user_in_group_(message.from_user.id)
    if not is_in_group:
        output_message = 'Ты не в группе. Выбери действие, которое хочешь совершить.'
        await message.answer(
            output_message,
            reply_markup=await reply_markups.get_join_or_create_group_keyboard()
        )
    else:
        status_code, user_position = await membersdb.get_user_position_in_group(message.from_user.id)
        if status_code != sc.OPERATION_SUCCESS:
            output_message = (f'Возникла проблема с определением твоего места в группе: '
                              f'{get_message_about_status_code(status_code)}.')
            await message.answer(
                output_message,
                reply_markup=await reply_markups.get_main_keyboard()
            )
            return
        if user_position == 'leader':
            output_message = 'Твоя роль в группе: <b>Создатель</b>. Выбери действия, которые хочешь выполнить.'
            await message.answer(
                output_message,
                parse_mode='HTML',
                reply_markup=await reply_markups.get_manage_group_keyboard(position=user_position)
            )
        elif user_position == 'depute':
            output_message = 'Твоя роль в группе: <b>Заместитель</b>. Выбери действия, которые хочешь выполнить.'
            await message.answer(
                output_message,
                parse_mode='HTML',
                reply_markup=await reply_markups.get_manage_group_keyboard(position=user_position)
            )
        else:
            output_message = 'Выбери действия, которые хочешь выполнить.'
            await message.answer(
                output_message,
                reply_markup=await reply_markups.get_manage_group_keyboard(position=user_position)
            )


@router.message(F.text.lower() == '➕ создать группу')
@router.message(Command('new_group'))
@decorators.user_exists_required
@decorators.user_not_in_group_required
async def cmd_new_group(message: Message, state: FSMContext) -> None:
    await message.answer(
        text='Эта возможность будет реализована в будущем.'
    )
    return
    # await state.set_state(GeneralStatesGroup.group_name_input)
    # output_message = 'Придумай название группы и напиши его ниже!'
    # await message.answer(
    #     output_message,
    #     reply_markup=await reply_markups.get_cancel_keyboard()
    # )


@router.message(F.text.lower() == '✏️ сменить название')
@router.message(Command('rename'))
@decorators.user_exists_required
@decorators.user_in_group_required
@decorators.user_group_leader_required
async def cmd_rename(message: Message, state: FSMContext) -> None:
    await state.set_state(GeneralStatesGroup.group_name_input)
    await state.update_data(back_step='manage_group')
    output_message = 'Придумай новое имя для группы в своём следующем сообщении.'
    await message.answer(
        output_message,
        reply_markup=await reply_markups.get_cancel_keyboard()
    )


@router.message(F.text.lower() == '🧾 информация о группе')
@router.message(Command('group_info'))
@decorators.user_exists_required
@decorators.user_in_group_required
async def cmd_group_info(message: Message) -> None:
    status_code, group_id = await membersdb.get_group_id_by_user_id(message.from_user.id)
    if status_code != sc.OPERATION_SUCCESS:
        output_message = (f'При определении, в какой группе ты находишься, возникла ошибка: '
                          f'{await get_message_about_status_code(status_code)}.')
        await message.answer(
            output_message
        )
        return
    status_code, info_about_group = await groupsdb.get_group_info(group_id=group_id)
    if status_code != sc.OPERATION_SUCCESS:
        output_message = (f'При получении информации о группе в которой ты находишься, возникла ошибка: '
                          f'{await get_message_about_status_code(status_code)}.')
        await message.answer(
            output_message
        )
        return
    output_message = f'<b>Информация о группе</b>\n\n{info_about_group}'
    await message.answer(
        output_message,
        parse_mode='HTML',
        disable_web_page_preview=True
    )


@router.message(F.text.lower() == '✏️ сменить подгруппу')
@router.message(Command('subgroup'))
@decorators.user_exists_required
@decorators.user_in_group_required
async def cmd_subgroup(message: Message, state: FSMContext) -> None:
    await state.set_state(GeneralStatesGroup.subgroup_input)
    await state.update_data(back_step='manage_group')
    output_message = 'Выбери номер подгруппы.'
    await message.answer(
        output_message,
        reply_markup=await reply_markups.get_subgroup_keyboard()
    )


@router.message(F.text.lower() == '👥 вступить в группу')
@router.message(Command('join'))
@decorators.user_exists_required
@decorators.user_not_in_group_required
async def cmd_join(message: Message, state: FSMContext) -> None:
    await state.set_state(GeneralStatesGroup.key_input)
    output_message = ('В следующем сообщении отправь уникальный ключ группы.'
                       '\n\nУзнать его ты можешь у главы и замов группы, в которую хочешь вступить.')
    await message.answer(
        output_message,
        reply_markup=await reply_markups.get_cancel_keyboard()
    )


@router.message(F.text.lower() == '🔑 получить ключ')
@router.message(Command('key'))
@decorators.user_exists_required
@decorators.user_in_group_required
@decorators.user_group_leader_or_depute_required
async def cmd_key(message: Message) -> None:
    status_code, group_id = await membersdb.get_group_id_by_user_id(message.from_user.id)
    if status_code != sc.OPERATION_SUCCESS:
        output_message = (f'Произошла ошибка при определении группы, в которой ты состоишь: '
                          f'{await get_message_about_status_code(status_code)}.')
        await message.answer(
            output_message
        )
        return
    status_code, key = await groupsdb.get_key_by_group_id(group_id)
    if status_code != sc.OPERATION_SUCCESS:
        output_message = (f'Произошла ошибка при получении уникального ключа: '
                          f'{await get_message_about_status_code(status_code)}.')
        await message.answer(
            output_message
        )
        return

    output_message = f'Уникальный код группы: <code>{key}</code>.'
    await message.answer(
        output_message,
        parse_mode='HTML'
    )


@router.message(F.text.lower() == '✏️ сменить ключ')
@router.message(Command('keygen'))
@decorators.user_exists_required
@decorators.user_in_group_required
@decorators.user_group_leader_or_depute_required
async def cmd_keygen(message: Message) -> None:
    status_code, group_id = await membersdb.get_group_id_by_user_id(message.from_user.id)
    if status_code != sc.OPERATION_SUCCESS:
        output_message = (f'Произошла ошибка при определении группы, в которой ты состоишь: '
                          f'{await get_message_about_status_code(status_code)}.')
        await message.answer(
            output_message
        )
        return
    status_code = await groupsdb.gen_new_key_to_group_(group_id)
    if status_code != sc.OPERATION_SUCCESS:
        output_message = (f'Произошла ошибка при генерации уникального ключа: '
                          f'{await get_message_about_status_code(status_code)}.')
        await message.answer(
            output_message
        )
        return
    status_code, key = await groupsdb.get_key_by_group_id(group_id)
    output_message = f'Уникальный ключ группы успешно обновлён: <code>{key}</code>.'
    await message.answer(
        output_message,
        parse_mode='HTML'
    )


@router.message(F.text.lower() == '🚪 выход из группы')
@router.message(Command('quit'))
@decorators.user_exists_required
@decorators.user_in_group_required
@decorators.user_not_group_leader_required
async def cmd_quit(message: Message, state: FSMContext) -> None:
    await state.set_state(GeneralStatesGroup.quit_accepting)
    await message.answer('Ты точно хочешь выйти из группы?',
                         reply_markup=await reply_markups.get_yes_or_no_keyboard())


@router.message(F.text.lower() == '⚠️ удалить группу')
@router.message(Command('del_group'))
@decorators.user_exists_required
@decorators.user_in_group_required
@decorators.user_group_leader_required
async def cmd_del_group(message: Message, state: FSMContext) -> None:
    await state.set_state(GeneralStatesGroup.del_group_accepting)
    await message.answer(
        'Ты точно хочешь удалить группу?',
        reply_markup=await reply_markups.get_yes_or_no_keyboard()
    )


@router.message(F.text.lower() == '⚙️ управление участниками')
@router.message(Command('manage_members'))
@decorators.user_exists_required
@decorators.user_in_group_required
@decorators.user_group_leader_or_depute_required
async def cmd_manage_members(message: Message, state: FSMContext) -> None:
    await message.answer(
        text='Эта функция будет реализована в последующем.'
    )
    # status_code, group_id = await membersdb.get_group_id_by_user_id(message.from_user.id)
    # if status_code != sc.OPERATION_SUCCESS:
    #     await message.answer(
    #         text='Возникла ошибка при определении группы, в которой ты находишься: '
    #              f'{await get_message_about_status_code(status_code)}.'
    #     )
    #     return
    # status_code, members = await membersdb.get_all_members_of_group(group_id)
    # if status_code != sc.OPERATION_SUCCESS:
    #     await message.answer(
    #         text='Возникла ошибка при выгрузке списка участников группы: '
    #              f'{await get_message_about_status_code(status_code)}.'
    #     )
    #     return
    # status_code, nicks = await membersdb.get_all_nicks_by_group_id(group_id)
    # if status_code != sc.OPERATION_SUCCESS:
    #     await message.answer(
    #         text='Возникла ошибка при выгрузке ников участников группы: '
    #              f'{await get_message_about_status_code(status_code)}.'
    #     )
    #     return
    # await state.set_state(GeneralStatesGroup.member_select)
    # prepared_members = await prepare_all_members_info_to_pretty_form(members)
    # prepared_info = await prepare_tuple_info_for_buttons(prepared_members)
    # markups, quantity_of_pages = \
    #     await reply_markups.parse_some_information_to_make_easy_navigation(prepared_info, 2)
    # now_page = 0
    # await state.update_data(
    #     nicks=nicks,
    #     markups=markups,
    #     now_page=now_page,
    #     quantity_of_pages=quantity_of_pages,
    #     back_step='manage_group'
    # )
    # await message.answer(
    #     text='Выбери участника группы для свершения действия над ним.\n\n'
    #          'Ты также можешь самостоятельно ввести его ник или переслать любое его сообщение.\n\n'
    #          f'Выбрана страница: <b>{now_page + 1}</b>. Всего страниц: <b>{quantity_of_pages}</b>.',
    #     parse_mode='HTML',
    #     reply_markup=markups[now_page]
    # )


@router.message(F.text.lower() == '◀️ к настройкам очередей')
@router.message(F.text.lower() == '⚙️ настройка очередей')
@router.message(Command('manage_queues'))
@decorators.user_exists_required
@decorators.user_in_group_required
@decorators.user_group_leader_or_depute_required
async def cmd_manage_queues(message: Message) -> None:
    await message.answer(
        text='Выбери, что ты хочешь настроить.',
        reply_markup=await reply_markups.get_manage_queues_keyboard()
    )


@router.message(F.text.lower() == '🌐 подгрузить расписание')
@router.message(Command('source'))
@decorators.user_exists_required
@decorators.user_in_group_required
@decorators.user_group_leader_or_depute_required
async def cmd_source(message: Message, state: FSMContext) -> None:
    await state.set_state(GeneralStatesGroup.source_choose)
    await state.update_data(back_step='manage_queues')
    await message.answer(
        text='Выбери свой университет.',
        reply_markup=await reply_markups.get_source_keyboard()
    )


@router.message(F.text.lower() == '✋ ручная настройка')
@router.message(Command('hand_made'))
@decorators.user_exists_required
@decorators.user_in_group_required
@decorators.user_group_leader_or_depute_required
async def cmd_hand_made(message: Message, state: FSMContext) -> None:
    await message.answer(
        text='Выбери вариант настройки.',
        reply_markup=await reply_markups.get_hand_made_keyboard()
    )


@router.message(F.text.lower() == '◀️ к меню очередей')
@router.message(F.text.lower() == '🔗 очереди')
@router.message(Command('queues'))
@decorators.user_exists_required
@decorators.user_in_group_required
async def cmd_queues(message: Message) -> None:
    await message.answer(
        text='Давай-ка посмотрим, что ты можешь сделать.',
        reply_markup=await reply_markups.get_queues_menu_keyboard()
    )


@router.message(F.text.lower() == '✏️ регистрация / отмена')
@router.message(Command('reg'))
@decorators.user_exists_required
@decorators.user_in_group_required
async def cmd_reg(message: Message, state: FSMContext) -> None:
    status_code, info_about_participate = await queues_info_db.get_information_about_queues_with_user_participation(
        user_id=message.from_user.id
    )
    if status_code != sc.OPERATION_SUCCESS:
        if status_code == sc.NO_QUEUES_TO_PARTICIPATE:
            await message.answer(
                text='Я не нашёл ни одной очереди, в которой ты бы мог поучаствовать!'
            )
        else:
            await message.answer(
                text='При подгрузке очередей для участия произошла ошибка: '
                     f'{await get_message_about_status_code(status_code)}.'
            )
        return
    markups, quantity_of_pages = \
            await reply_markups.parse_some_information_to_make_easy_navigation(info_about_participate, 2)
    now_page = 0
    await state.set_state(GeneralStatesGroup.queue_choose)
    await state.update_data(markups=markups, quantity_of_pages=quantity_of_pages, now_page=now_page,
                            back_step='queues_menu', info_about_participate=info_about_participate)
    await message.answer(
        text='Выбери очереди для взаимодействия.',
        reply_markup=markups[now_page]
    )


async def prepare_info_for_managing_queues(message: Message, state: FSMContext, old_page: int = 0):
    output_message = await queuesdb.get_info_about_user_participation_in_queues(user_id=message.from_user.id)

    status_code, queues_info_ids = \
        await queuesdb.simple_get_queues_info_ids_which_user_participate(user_id=message.from_user.id)

    if status_code == sc.USER_NOT_PARTICIPATE_IN_ANY_QUEUES:
        await state.clear()

        await message.answer(
            text=output_message,
            reply_markup=await reply_markups.get_manage_queues_keyboard()
        )
        return sc.STOP

    elif status_code != sc.OPERATION_SUCCESS:
        await state.clear()

        await message.answer(
            text='При получении информации об очередях, в которых ты принимаешь участие, произошла ошибка: '
                 f'{await get_message_about_status_code(status_code)}.',
            reply_markup=await reply_markups.get_manage_queues_keyboard()
        )
        return sc.STOP

    info_in_buttons = ['📦 Информация о всех']

    for queue_info_id in queues_info_ids:
        status_code, info_for_button = await queues_info_db.get_information_to_make_button(queue_info_id)
        if status_code != sc.OPERATION_SUCCESS:
            await state.clear()

            await message.answer(
                text='При получении информации об очередях, в которых ты принимаешь участие, произошла ошибка: '
                     f'{await get_message_about_status_code(status_code)}.',
                reply_markup=await reply_markups.get_manage_queues_keyboard()
            )
            return sc.STOP

        info_in_buttons.append(info_for_button)

    markups, quantity_of_pages = \
        await reply_markups.parse_some_information_to_make_easy_navigation(tuple(info_in_buttons), 2)

    if old_page > quantity_of_pages:
        now_page = quantity_of_pages - 1
    elif old_page < 0:
        now_page = 0
    else:
        now_page = old_page

    await state.set_state(GeneralStatesGroup.queues_viewing)

    await state.update_data(back_step='queues_menu', markups=markups, quantity_of_pages=quantity_of_pages,
                            now_page=now_page, info_in_buttons=info_in_buttons)

    await message.answer(
        text=output_message,
        parse_mode='HTML',
        reply_markup=markups[now_page]
    )

    return sc.OPERATION_SUCCESS


@router.message(F.text.lower() == '📋 просмотр регистраций')
@router.message(Command('view'))
@decorators.user_exists_required
@decorators.user_in_group_required
async def cmd_view(message: Message, state: FSMContext) -> None:
    await prepare_info_for_managing_queues(message, state)


@router.message(F.text.lower() == '🔃 поменяться местами')
@router.message(Command('trade'))
@decorators.user_exists_required
@decorators.user_in_group_required
async def cmd_trade(message: Message, state: FSMContext) -> None:
    await state.set_state(GeneralStatesGroup.captcha)
    await state.update_data(next_state='trade_info_input', back_step='queues_menu')
    captcha_image, captcha_text = await get_image_captcha(6)
    await state.update_data(captcha_text=captcha_text, captcha_try=0)
    await message.answer_photo(
        photo=captcha_image,
        caption='Реши каптчу, чтобы отправить трейд.',
        reply_markup=await reply_markups.get_cancel_keyboard()
    )


@router.message(Command('accept'))
@decorators.user_exists_required
@decorators.user_in_group_required
async def cmd_accept(message: Message) -> None:
    split_message = message.text.split(' ')
    if len(split_message) < 2:
        await message.answer(
            text='Команда использована неверна. Используй /accept trade_id.'
        )
        return
    try:
        trade_id = split_message[1]
    except ValueError:
        await message.answer(
            text='Введён некорректный номер трейда.'
        )
        return
    status_code = await tradesdb.accept_trade_(trade_id=trade_id, accept_sender_id=message.from_user.id)
    if status_code != sc.OPERATION_SUCCESS:
        await message.answer(
            text='При трейде произошла ошибка: '
                 f'{await get_message_about_status_code(status_code)}.'
        )
        return
    await message.answer(
        text='Трейд осуществлён успешно!'
    )


@router.message(F.text.lower() == '👥 участники')
@router.message(Command('members'))
@decorators.user_exists_required
@decorators.user_in_group_required
async def cmd_members(message: Message) -> None:
    await message.answer(
        text='Эта возможность будет реализована позднее.'
    )
    return


@router.message(F.text.lower() == '🎲 развлечения')
@router.message(Command('games'))
@decorators.user_exists_required
async def cmd_games(message: Message) -> None:
    await message.answer(
        text='Так, посмотрим-с, во что я могу с тобой поиграть...',
        reply_markup=await reply_markups.get_games_keyboard()
    )


@router.message(F.text.lower() == '🧩 каптча')
@router.message(Command('captcha_game'))
@decorators.user_exists_required
async def cmd_captcha_game(message: Message, state: FSMContext) -> None:
    await state.set_state(GeneralStatesGroup.captcha_game_setup)
    await message.answer(
        text='Выбери количество символов в каптче. Отправь мне целое число.',
        reply_markup=await reply_markups.get_cancel_keyboard()
    )


@router.message(F.text.lower() == '🤡 анекдот')
@router.message(Command('joke'))
@decorators.user_exists_required
async def cmd_joke(message: Message) -> None:
    await message.answer(
        text='Эта функциональность будет реализована в последующем.'
    )


@router.message(F.text.lower() == '🏆 таблицы рекордов')
@router.message(Command('records'))
@decorators.user_exists_required
async def cmd_records(message: Message) -> None:
    await message.answer(
        text='Эта функциональность будет реализована в последующем.'
    )


@router.message(F.text.lower() == '🔄 а сейчас работает?')
async def yes_it_works(message: Message) -> None:
    await message.answer(
        text='Да! Я снова работаю!',
        reply_markup=await reply_markups.get_main_keyboard()
    )


@router.message(F.text)
@decorators.user_exists_required
async def unknown_message(message: Message) -> None:
    await message.answer(
        text='Я тебя не понял.\n\nПопробуй взаимодействовать с меню: /main_menu'
    )
