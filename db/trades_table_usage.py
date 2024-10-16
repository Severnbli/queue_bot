from db.root import cur, try_commit
from status_codes import StatusCode as sc
import db.queues_table_usage as queuesdb
import db.users_table_usage as usersdb
import db.queues_info_table_usage as queues_info_db


async def check_for_trade(sender_id: int, receiver_id: int, queue_info_id: int):
    status_code, queues_list_sender = await queuesdb.simple_get_queues_info_ids_which_user_participate(sender_id)
    if status_code != sc.OPERATION_SUCCESS:
        return status_code
    status_code, queues_list_receiver = await queuesdb.simple_get_queues_info_ids_which_user_participate(receiver_id)
    if status_code != sc.OPERATION_SUCCESS:
        return status_code
    if queue_info_id not in queues_list_sender:
        return sc.TRADE_SENDER_NOT_IN_GIVEN_QUEUE
    if queue_info_id not in queues_list_receiver:
        return sc.TRADE_RECEIVER_NOT_IN_GIVEN_QUEUE
    return sc.OPERATION_SUCCESS


async def get_sender_and_receiver_places_in_queue(sender_id: int, receiver_id: int, queue_info_id: int):
    status_code, sender_place = await queuesdb.get_user_place_in_queue(user_id=sender_id, queue_info_id=queue_info_id)
    if status_code != sc.OPERATION_SUCCESS:
        return status_code, None
    status_code, receiver_place = await queuesdb.get_user_place_in_queue(user_id=receiver_id,
                                                                         queue_info_id=queue_info_id)
    if status_code != sc.OPERATION_SUCCESS:
        return status_code, None
    trade_places = {
        "sender_place": sender_place,
        "receiver_place": receiver_place
    }
    return sc.OPERATION_SUCCESS, trade_places


async def reg_trade_(sender_id: int, receiver_id: int, queue_info_id: int):
    status_code, queue_info_status = await queues_info_db.simple_get_status_of_queue_info(queue_info_id)
    if status_code != sc.OPERATION_SUCCESS:
        return status_code
    if queue_info_status != 'release':
        return sc.QUEUE_INFO_NOT_SUITABLE
    status_code = await check_for_trade(sender_id, receiver_id, queue_info_id)
    if status_code != sc.OPERATION_SUCCESS:
        return status_code
    status_code, trade_places = await get_sender_and_receiver_places_in_queue(sender_id, receiver_id, queue_info_id)
    if status_code != sc.OPERATION_SUCCESS:
        return status_code
    sender_place = trade_places["sender_place"]
    receiver_place = trade_places["receiver_place"]
    await cur.execute('SELECT COUNT(*) '
                      'FROM trades '
                      'WHERE sender_id = ? '
                      'AND sender_place = ? '
                      'AND receiver_id = ? '
                      'AND receiver_place = ? '
                      'AND queue_info_id = ? ' ,(sender_id, sender_place, receiver_id, receiver_place, queue_info_id))
    row = await cur.fetchone()
    if row is None:
        return sc.DB_ERROR
    is_trade_exist = bool(row[0])
    if is_trade_exist:
        return sc.TRADE_EXIST
    await cur.execute('INSERT INTO trades (sender_id, sender_place, receiver_id, receiver_place, queue_info_id) '
                      'VALUES (?, ?, ?, ?, ?)', (sender_id, sender_place, receiver_id, receiver_place, queue_info_id))
    if not await try_commit():
        return sc.DB_ERROR
    trade_id = cur.lastrowid
    status_code, sender_nick = await usersdb.get_nick(sender_id)
    status_code, queue_info = await queues_info_db.get_information_to_make_button(queues_info_id=queue_info_id)
    await usersdb.notify_user_(user_id=receiver_id, text=f'Пользователь с ником {sender_nick} предлагает тебе поменяться '
                                                 f'местами в очереди {queue_info}: ты на {sender_place} место, а он '
                                                 f'на {receiver_place}. Для подтверждения отправь /accept {trade_id}')
    return sc.OPERATION_SUCCESS


async def accept_trade_(trade_id, accept_sender_id):
    await cur.execute('SELECT sender_id, sender_place, receiver_id, receiver_place, queue_info_id, is_up_to_date '
                      'FROM trades '
                      'WHERE id = ?', (trade_id,))
    row = await cur.fetchone()
    if row is None:
        return sc.DB_ERROR
    trade_info = row
    if trade_info[2] != accept_sender_id:
        return sc.ACCEPT_TRADE_CAN_ONLY_RECEIVER
    if trade_info[5] == 'false':
        return sc.TRADE_INFO_OUT_OF_DATE
    queue_info_id = trade_info[4]
    sender_id = trade_info[0]
    sender_known_place = trade_info[1]
    receiver_id = trade_info[2]
    receiver_known_place = trade_info[3]
    status_code = await check_for_trade(sender_id, receiver_id, queue_info_id)
    if status_code != sc.OPERATION_SUCCESS:
        return status_code
    status_code, trade_places = await get_sender_and_receiver_places_in_queue(sender_id, receiver_id, queue_info_id)
    sender_place = trade_places["sender_place"]
    receiver_place = trade_places["receiver_place"]
    if (sender_place != sender_known_place) or (receiver_place != receiver_known_place):
        return sc.TRADE_INFO_OUT_OF_DATE
    status_code, queue_info_status = await queues_info_db.simple_get_status_of_queue_info(queue_info_id)
    if status_code != sc.OPERATION_SUCCESS:
        return status_code
    if queue_info_status != 'release':
        return sc.TRADE_INFO_OUT_OF_DATE
    await cur.execute('UPDATE trades '
                      "SET is_up_to_date = 'false' "
                      "WHERE id = ?", (trade_id,))
    status_code = await queuesdb.swap_places_(sender_id, receiver_id, queue_info_id)
    if status_code != sc.OPERATION_SUCCESS:
        return status_code
    status_code, queue_info = await queues_info_db.get_information_to_make_button(queues_info_id=queue_info_id)
    await usersdb.notify_user_(
        user_id=sender_id,
        text=f'Трейд в очереди {queue_info} завершён успешно: ты теперь на {receiver_place} месте вместо '
             f'{sender_place}.'
    )
    return sc.OPERATION_SUCCESS


async def reg_trade_by_place_in_queue_(sender_id: int, place: int, queue_info_id: int):
    status_code, receiver_id = await queuesdb.get_user_id_by_place_in_queue(place, queue_info_id)
    if status_code != sc.OPERATION_SUCCESS:
        return status_code
    return await reg_trade_(sender_id, receiver_id, queue_info_id)
