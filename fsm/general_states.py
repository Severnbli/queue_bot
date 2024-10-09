from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage

storage = MemoryStorage()


class GeneralStatesGroup(StatesGroup):
    nick_input = State()
    nick_accepting = State()
    captcha = State()
    report_input = State()
    report_accepting = State()
    group_name_input = State()
    subgroup_input = State()
    key_input = State()
    quit_accepting = State()
    del_group_accepting = State()
    manage_members = State()
    member_select = State()
    source_choose = State()
    group_source_input = State()
    group_source_accepting = State()
    queue_choose = State()
    queues_viewing = State()
    trade_info_input = State()
    report_checking = State()
    report_answer_input = State()
    report_answer_accepting = State()
    captcha_game_setup = State()
    captcha_game_process = State()
    say_input = State()
    say_accepting = State()
