from functools import wraps
from aiogram.types import Message, ReplyKeyboardRemove

import db.users_table_usage as usersdb
import db.members_table_usage as membersdb
from status_codes import StatusCode as sc, get_message_about_error
from markups import reply_markups


def user_exists_required(func):
    @wraps(func)
    async def wrapper(message: Message, *args, **kwargs):
        if not await usersdb.is_user_exist_(message.from_user.id):
            output_message = 'Тебя нет в базе моих знаний. Попробуй зарегистрироваться: /start.'
            await message.answer(output_message, reply_markup=await reply_markups.get_register_keyboard())
            return
        return await func(message, *args, **kwargs)
    return wrapper


def user_group_leader_or_depute_required(func):
    @wraps(func)
    async def wrapper(message: Message, *args, **kwargs):
        status_code, user_position = await membersdb.get_user_position_in_group(message.from_user.id)
        if status_code != sc.OPERATION_SUCCESS:
            output_message = (f'Возникла ошибка при определении твоей роли в группе: '
                              f'{await get_message_about_error(status_code)}.')
            await message.answer(output_message, reply_markup=await reply_markups.get_main_keyboard())
            return
        elif user_position not in ['leader', 'depute']:
            output_message = 'У тебя недостаточно прав на это действие.'
            await message.answer(output_message, reply_markup=await reply_markups.get_main_keyboard())
            return
        return await func(message, *args, **kwargs)
    return wrapper


def user_group_leader_required(func):
    @wraps(func)
    async def wrapper(message: Message, *args, **kwargs):
        status_code, user_position = await membersdb.get_user_position_in_group(message.from_user.id)
        if status_code != sc.OPERATION_SUCCESS:
            output_message = (f'Возникла ошибка при определении твоей роли в группе: '
                              f'{await get_message_about_error(status_code)}.')
            await message.answer(output_message, reply_markup=await reply_markups.get_main_keyboard())
            return
        elif user_position != 'leader':
            output_message = 'У тебя недостаточно прав на это действие.'
            await message.answer(output_message, reply_markup=await reply_markups.get_main_keyboard())
            return
        return await func(message, *args, **kwargs)
    return wrapper


def user_in_group_required(func):
    @wraps(func)
    async def wrapper(message: Message, *args, **kwargs):
        is_user_in_group = await membersdb.is_user_in_group_(message.from_user.id)
        if not is_user_in_group:
            output_message = 'Для выполнения этого действия ты должен быть в группе.'
            await message.answer(output_message, reply_markup=await reply_markups.get_main_keyboard())
            return
        return await func(message, *args, **kwargs)
    return wrapper


def user_not_in_group_required(func):
    @wraps(func)
    async def wrapper(message: Message, *args, **kwargs):
        is_user_in_group = await membersdb.is_user_in_group_(message.from_user.id)
        if is_user_in_group:
            output_message = 'Для выполнения этого действия ты не должен состоять в группе.'
            await message.answer(output_message, reply_markup=await reply_markups.get_main_keyboard())
            return
        return await func(message, *args, **kwargs)
    return wrapper


def user_not_group_leader_required(func):
    @wraps(func)
    async def wrapper(message: Message, *args, **kwargs):
        status_code, user_position = await membersdb.get_user_position_in_group(message.from_user.id)
        if status_code != sc.OPERATION_SUCCESS:
            output_message = (f'Возникла ошибка при определении твоей роли в группе: '
                              f'{await get_message_about_error(status_code)}.')
            await message.answer(output_message, reply_markup=await reply_markups.get_main_keyboard())
            return
        elif user_position == 'leader':
            output_message = 'Ты не можешь совершить это, так как ты лидер.'
            await message.answer(output_message, reply_markup=await reply_markups.get_main_keyboard())
            return
        return await func(message, *args, **kwargs)
    return wrapper
