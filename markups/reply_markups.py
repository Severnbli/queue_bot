from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from math import ceil

async def get_yes_or_no_keyboard(placeholder: str = 'Любишь пельмешки?') -> ReplyKeyboardMarkup:
    kb = [
        [
            KeyboardButton(text='Да'),
            KeyboardButton(text='Нет')
         ],
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder=placeholder
    )
    return keyboard


async def build_markup(content: tuple, adjust_param: int) -> ReplyKeyboardMarkup:
    content = [str(element) for element in content]
    builder = ReplyKeyboardBuilder()
    for element in content:
        builder.add(KeyboardButton(text=element))
    builder.adjust(adjust_param)
    keyboard = builder.as_markup(resize_keyboard=True)
    return keyboard


async def parse_some_information_to_make_easy_navigation(content: tuple, adjust_param: int) -> tuple:
    quantity_of_rows = 10
    len_of_information = len(content)
    quantity_of_getting_rows: float = len_of_information / adjust_param
    quantity_of_pages: float = quantity_of_getting_rows / quantity_of_rows
    quantity_of_pages: int = ceil(quantity_of_pages)
    list_of_markups = []
    for i in range(quantity_of_pages):
        piece_of_content_to_make_markup = []
        start_index = i * quantity_of_rows * adjust_param
        end_index = min(start_index + quantity_of_rows * adjust_param, len_of_information)
        piece_of_content_to_make_markup.extend(content[start_index:end_index])
        if i < quantity_of_pages - 1:
            if i == 0:
                piece_of_content_to_make_markup.append('▶️ Вперёд')
            else:
                piece_of_content_to_make_markup.append('▶️ Вперёд')
                piece_of_content_to_make_markup.append('◀️ Назад')
        elif quantity_of_pages != 1:
            piece_of_content_to_make_markup.append('◀️ Назад')
        piece_of_content_to_make_markup.append('⛔️ Выход / отмена')
        markup = await build_markup(tuple(piece_of_content_to_make_markup), adjust_param)
        list_of_markups.append(markup)
    return tuple(list_of_markups), quantity_of_pages


async def get_main_keyboard(placeholder: str = 'Нажми кнопку меню или используй команду') -> ReplyKeyboardMarkup:
    kb = [
        [
            KeyboardButton(text='👤 Профиль'),
            KeyboardButton(text='👥 Группа')
        ],
        [
            KeyboardButton(text='🔗 Очереди')
        ],
        [
            KeyboardButton(text='⚡️ Команды'),
            KeyboardButton(text='💬 Репорт')
        ],
        [
            KeyboardButton(text='🎲 Развлечения')
        ]
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder=placeholder
    )
    return keyboard


async def get_join_or_create_group_keyboard(placeholder: str = 'Что ты выберешь их '
                                                               'или нас? Нас или их?') -> ReplyKeyboardMarkup:
    kb = [
        [
            KeyboardButton(text='➕ Создать группу'),
            KeyboardButton(text='👥 Вступить в группу')
        ],
        [
            KeyboardButton(text='◀️ В главное меню')
        ]
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder=placeholder
    )
    return keyboard


async def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    kb = [
        [
            KeyboardButton(text='⛔️ Выход / отмена')
        ]
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )
    return keyboard


async def get_manage_profile_keyboard() -> ReplyKeyboardMarkup:
    kb = [
        [
            KeyboardButton(text='🧾 Информация о тебе')
        ],
        [
            KeyboardButton(text='✏️ Сменить имя')
        ],
        [
            KeyboardButton(text='🌐 Подгрузить ссылку')
        ],
        [
            KeyboardButton(text='✏️ Включение / отключение подписки на обновления')
        ],
        [
            KeyboardButton(text='◀️ В главное меню')
        ]
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )
    return keyboard


async def get_manage_group_keyboard(position: str) -> ReplyKeyboardMarkup:
    kb = [
        [
            KeyboardButton(text='🧾 Информация о группе'),
            KeyboardButton(text='✏️ Сменить подгруппу')
        ],
        [
            KeyboardButton(text='👥 Участники')
        ],
        [
            KeyboardButton(text='🚪 Выход из группы')
        ],
        [
            KeyboardButton(text='◀️ В главное меню')
        ]
    ]
    if position in ['depute', 'leader']:
        kb_depute_additional = [
            [
                KeyboardButton(text='🔑 Получить ключ'),
                KeyboardButton(text='✏️ Сменить ключ')
            ],
            [
                KeyboardButton(text='⚙️ Управление участниками')
            ],
            [
                KeyboardButton(text='⚙️ Настройка очередей')
            ]
        ]
        kb[2:2] = kb_depute_additional
    if position == 'leader':
        kb.pop(5)
        kb_leader_additional = [
            [
                KeyboardButton(text='✏️ Сменить название'),
                KeyboardButton(text='⚠️ Удалить группу')
            ]
        ]
        kb[5:5] = kb_leader_additional
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
    )
    return keyboard


async def get_subgroup_keyboard() -> ReplyKeyboardMarkup:
    kb = [
        [
            KeyboardButton(text='1️⃣ Подгруппа'),
            KeyboardButton(text='2️⃣ Подгруппа')
        ],
        [
            KeyboardButton(text='⛔️ Выход / отмена')
        ]
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )
    return keyboard


async def get_manage_members_keyboard(position: str) -> ReplyKeyboardMarkup:
    kb = [
        [
            KeyboardButton(text='🏴 Добавление в ЧС'),
            KeyboardButton(text='🏳️ Помилование')
        ],
        [
            KeyboardButton(text='◀️ К выбору ника'),
            KeyboardButton(text='⛔️ Выход / отмена')
        ]
    ]
    if position == 'leader':
        kb_leader_additional = [
            [
                KeyboardButton(text='📈 Добавление заместителя'),
                KeyboardButton(text='📉 Снятие заместителя')
            ],
            [
                KeyboardButton(text='👑 Передача лидерства')
            ]
        ]
        kb[1:1] = kb_leader_additional
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )
    return keyboard


async def get_register_keyboard() -> ReplyKeyboardMarkup:
    kb = [
        [
            KeyboardButton(text='®️ Зарегистрироваться'),
            KeyboardButton(text='🐈 Мяу-Мяу')
        ]
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )
    return keyboard



async def get_manage_queues_keyboard() -> ReplyKeyboardMarkup:
    kb = [
        [
            KeyboardButton(text='🌐 Подгрузить расписание')
        ],
        [
            KeyboardButton(text='✋ Ручная настройка')
        ],
        [
            KeyboardButton(text='◀️ В группу')
        ]
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )
    return keyboard


async def get_source_keyboard() -> ReplyKeyboardMarkup:
    kb = [
        [
            KeyboardButton(text='BSUIR')
        ],
        [
            KeyboardButton(text='⛔️ Выход / отмена')
        ]
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )
    return keyboard


async def get_hand_made_keyboard() -> ReplyKeyboardMarkup:
    kb = [
        [
            KeyboardButton(text='⚙️ Настройка имеющегося в БД расписания')
        ],
        [
            KeyboardButton(text='✏️ Создание нового расписания')
        ],
        [
            KeyboardButton(text='◀️ К настройкам очередей')
        ]
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )
    return keyboard


async def get_queues_menu_keyboard() -> ReplyKeyboardMarkup:
    kb = [
        [
            KeyboardButton(text='✏️ Регистрация / отмена')
        ],
        [
            KeyboardButton(text='📋 Просмотр регистраций'),
            KeyboardButton(text='🔃 Поменяться местами')
        ],
        [
            KeyboardButton(text='◀️ В главное меню')
        ]
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )
    return keyboard


async def get_manage_report_keyboard() -> ReplyKeyboardMarkup:
    kb = [
        [
            KeyboardButton(text='✏️ Написать ответ'),
            KeyboardButton(text='✅ Пометить прочитанным')
        ],
        [
            KeyboardButton(text='◀️ К выбору репорта')
        ],
        [
            KeyboardButton(text='⛔️ Выход / отмена')
        ]
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )
    return keyboard


async def get_return_to_manage_report_keyboard() -> ReplyKeyboardMarkup:
    kb = [
        [
            KeyboardButton(text='◀️ К выбору действия с репортом')
        ],
        [
            KeyboardButton(text='⛔️ Выход / отмена')
        ]
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )
    return keyboard


async def get_yes_or_no_for_report_answering() -> ReplyKeyboardMarkup:
    kb = [
        [
            KeyboardButton(text='Да'),
            KeyboardButton(text='Нет')
        ],
        [
            KeyboardButton(text='◀️ К выбору действия с репортом')
        ],
        [
            KeyboardButton(text='⛔️ Выход / отмена')
        ]
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )
    return keyboard


async def get_games_keyboard() -> ReplyKeyboardMarkup:
    kb = [
        [
            KeyboardButton(text='🧩 Каптча'),
            KeyboardButton(text='🤡 Анекдот')
        ],
        [
            KeyboardButton(text='◀️ В главное меню')
        ]
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )
    return keyboard
