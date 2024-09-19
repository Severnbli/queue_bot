from aiogram import Router, F

from handlers.hl_general import non_state
from handlers.hl_general import state_based

hl_general_main_router = Router()
hl_general_main_router.message.filter(F.chat.type == 'private')
hl_general_main_router.include_routers(non_state.router, state_based.router)
