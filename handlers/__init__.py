from aiogram import Dispatcher

from handlers.admin import admin_router
from handlers.inform import inform_router
from handlers.start import start_router

# from handlers.start import start_router

dp = Dispatcher()
dp.include_routers(*[
    start_router,
    inform_router,
    admin_router,

])
