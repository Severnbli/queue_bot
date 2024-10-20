class StatusCode:
    OPERATION_SUCCESS = 0
    USER_EXIST = 101
    USER_NOT_EXIST = 102
    ROLE_NOT_EXIST = 103
    GROUP_NOT_EXIST = 104
    DB_VALUE_ERROR = 105
    GIVEN_VALUE_TYPE_ERROR = 106
    GROUP_WITH_SUCH_NAME_EXIST = 107
    GROUP_EXIST = 108
    USER_IN_GROUP = 109
    USER_NOT_IN_GROUP = 110
    TELEGRAM_ERROR = 111
    GROUP_WITH_SUCH_KEY_NOT_EXIST = 112
    USER_NOTIFY_SUCCESSFULLY = 113
    USER_NOTIFY_ERROR = 114
    BAD_REQUEST = 115
    UNKNOWN_SOURCE = 116
    SAME_SCHEDULE_EXIST = 117
    NO_QUEUES_IN_PRERELEASE = 118
    NO_QUEUES_IN_RELEASE = 119
    NO_QUEUES_TO_PARTICIPATE = 120
    NOTHING_NEEDED_TO_DO = 121
    NEEDED_TEXT_PROCESSING = 122
    QUEUES_INFO_NOT_EXIST = 123
    USER_PARTICIPATE_IN_QUEUE = 124
    USER_NOT_PARTICIPATE_IN_QUEUE = 125
    UNKNOWN_STATUS_CODE = 126
    USER_ADD_TO_QUEUE_SUCCESSFULLY = 127
    USER_DELETE_FROM_QUEUE_SUCCESSFULLY = 128
    USER_NOT_PARTICIPATE_IN_ANY_QUEUES = 129
    NO_USERS_THAT_PARTICIPATE_ENTERED_QUEUE_INFO = 130
    TRADE_SENDER_NOT_IN_GIVEN_QUEUE = 131
    TRADE_RECEIVER_NOT_IN_GIVEN_QUEUE = 132
    NO_TRADES_WITH_SUCH_IDS = 134
    ACCEPT_TRADE_CAN_ONLY_RECEIVER = 135
    TRADE_INFO_OUT_OF_DATE = 136
    QUEUE_INFO_NOT_SUITABLE = 137
    USER_WITH_SUCH_PLACE_IN_SUCH_QUEUE_NOT_EXIST = 138
    TRADE_EXIST = 139
    NO_REPORTS_TO_CHECK = 140
    SEND_TRADE_TO_YOURSELF = 141

    DB_ERROR = 404


async def get_message_about_status_code(status_code: int) -> str:
    if status_code == StatusCode.USER_EXIST:
        return 'пользователь уже зарегистрирован'
    elif status_code == StatusCode.USER_NOT_EXIST:
        return 'пользователь не зарегистрирован'
    elif status_code == StatusCode.DB_ERROR:
        return 'база данных приняла ислам'
    elif status_code == StatusCode.ROLE_NOT_EXIST:
        return 'несуществующая роль'
    elif status_code == StatusCode.GROUP_NOT_EXIST:
        return 'несуществующая группа'
    elif status_code == StatusCode.DB_VALUE_ERROR:
        return 'получено неверное значение из базы данных'
    elif status_code == StatusCode.GIVEN_VALUE_TYPE_ERROR:
        return 'введено значение неверного типа'
    elif status_code == StatusCode.GROUP_WITH_SUCH_NAME_EXIST:
        return 'группа с введённым названием уже существует'
    elif status_code == StatusCode.GROUP_EXIST:
        return 'группа существует'
    elif status_code == StatusCode.USER_IN_GROUP:
        return 'пользователь состоит в группе'
    elif status_code == StatusCode.USER_NOT_IN_GROUP:
        return 'пользователь не состоит в группе'
    elif status_code == StatusCode.OPERATION_SUCCESS:
        return 'операция проведена успешно'
    elif status_code == StatusCode.TELEGRAM_ERROR:
        return 'ошибка на стороне телеграма'
    elif status_code == StatusCode.GROUP_WITH_SUCH_KEY_NOT_EXIST:
        return 'группы с таким уникальным ключом не существует'
    elif status_code == StatusCode.USER_NOTIFY_SUCCESSFULLY:
        return 'пользователь успешно уведомлён'
    elif status_code == StatusCode.USER_NOTIFY_ERROR:
        return 'пользователь не уведомлён'
    elif status_code == StatusCode.BAD_REQUEST:
        return 'ошибка в отправке запроса на сервер'
    elif status_code == StatusCode.UNKNOWN_SOURCE:
        return 'неизвестна цель отправки запроса'
    elif status_code == StatusCode.SAME_SCHEDULE_EXIST:
        return 'аналогичная запись в расписании уже находится в БД'
    elif status_code == StatusCode.NO_QUEUES_IN_PRERELEASE:
        return 'нет ни одной очереди со статусом "пререлиз"'
    elif status_code == StatusCode.NO_QUEUES_IN_RELEASE:
        return 'нет ни одной очереди со статусом "релиз"'
    elif status_code == StatusCode.NO_QUEUES_TO_PARTICIPATE:
        return 'нет ни одной очереди для регистрации'
    elif status_code == StatusCode.NOTHING_NEEDED_TO_DO:
        return 'не требуется никакого действия'
    elif status_code == StatusCode.NEEDED_TEXT_PROCESSING:
        return 'требуется обработка текста'
    elif status_code == StatusCode.QUEUES_INFO_NOT_EXIST:
        return 'в БД с информацией об очередях данная очередь не найдена'
    elif status_code == StatusCode.USER_PARTICIPATE_IN_QUEUE:
        return 'пользователь участвует в очереди'
    elif status_code == StatusCode.USER_NOT_PARTICIPATE_IN_QUEUE:
        return 'пользователь не участвует в очереди'
    elif status_code == StatusCode.UNKNOWN_STATUS_CODE:
        return 'обнаружен неизвестный статус-код'
    elif status_code == StatusCode.USER_ADD_TO_QUEUE_SUCCESSFULLY:
        return 'пользователь успешно зарегистрирован на очередь'
    elif status_code == StatusCode.USER_DELETE_FROM_QUEUE_SUCCESSFULLY:
        return 'регистрация пользователя на очередь успешно отменена'
    elif status_code == StatusCode.USER_NOT_PARTICIPATE_IN_ANY_QUEUES:
        return 'пользователь не участвует ни в одной очереди'
    elif status_code == StatusCode.NO_USERS_THAT_PARTICIPATE_ENTERED_QUEUE_INFO:
        return 'нет пользователей, которые бы принимали участие в данной очереди'
    elif status_code == StatusCode.TRADE_SENDER_NOT_IN_GIVEN_QUEUE:
        return 'отправитель трейда не участвует в введённой очереди'
    elif status_code == StatusCode.TRADE_RECEIVER_NOT_IN_GIVEN_QUEUE:
        return 'получатель трейда не участвует в введённой очереди'
    elif status_code == StatusCode.NO_TRADES_WITH_SUCH_IDS:
        return 'нет трейдов с введённым айди'
    elif status_code == StatusCode.ACCEPT_TRADE_CAN_ONLY_RECEIVER:
        return 'одобрить трейд может только его получатель'
    elif status_code == StatusCode.TRADE_INFO_OUT_OF_DATE:
        return 'информация о трейде устарела'
    elif status_code == StatusCode.QUEUE_INFO_NOT_SUITABLE:
        return 'очередь не подходит для трейда'
    elif status_code == StatusCode.USER_WITH_SUCH_PLACE_IN_SUCH_QUEUE_NOT_EXIST:
        return 'пользователя с введённым местом в ведённой очереди не существует'
    elif status_code == StatusCode.TRADE_EXIST:
        return 'трейд с аналогичными параметрами уже создан'
    elif status_code == StatusCode.NO_REPORTS_TO_CHECK:
        return 'нет репортов для проверки'
    elif status_code == StatusCode.SEND_TRADE_TO_YOURSELF:
        return 'отправка трейда самому себе'
    else:
        return f'неизвестный статусный код: {status_code}'


async def get_message_about_error(status_code: int) -> str:
    output_message = f'Выявлена ошибка: {await get_message_about_status_code(status_code=status_code)}'
    return output_message
