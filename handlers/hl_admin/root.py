from aiogram import Router, F

from handlers.hl_admin import non_state
from handlers.hl_admin import state_based
from filters import is_admin

hl_admin_main_router = Router()
hl_admin_main_router.message.filter(F.chat.type == 'private', is_admin.IsAdminFilter())
hl_admin_main_router.include_routers(non_state.router, state_based.router)