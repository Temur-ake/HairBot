import os

from aiogram import Router, html, Bot
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from handlers.admin import admin_button
from keyboards import main_menu_button
from models import session, User

start_router = Router()


# CHANNELS = [
#     # "@socholish"
# ]
#
#
# async def is_user_subscribed(user_id, bot: Bot):
#     not_subscribed_channels = []
#
#     for channel in CHANNELS:
#         try:
#             status = await bot.get_chat_member(channel, user_id)
#             print(f'User {user_id} status in {channel}: {status.status}')
#             if status.status not in ['member', 'administrator', 'creator']:
#                 print(f'User {user_id} is not subscribed to {channel}.')
#                 not_subscribed_channels.append(channel)
#         except Exception as e:
#             if "Bad Request: chat not found" in str(e):
#                 print(
#                     f'Could not check subscription for channel {channel}. The channel might be private or the bot does not have permission.')
#             not_subscribed_channels.append(channel)
#
#     return not_subscribed_channels

#
# async def get_subscription_check_markup(user_id, bot: Bot):
#     inline_buttons = []
#
#     not_subscribed_channels = await is_user_subscribed(user_id, bot)
#
#     for channel in not_subscribed_channels:
#         button = InlineKeyboardButton(
#             text=f"{channel}",
#             url=f"t.me/{channel.strip('@')}"
#         )
#         inline_buttons.append([button])
#
#     ikb = InlineKeyboardMarkup(inline_keyboard=inline_buttons)
#     return ikb


@start_router.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext, bot: Bot) -> None:
    user_id = message.from_user.id
    full_name = html.bold(message.from_user.full_name)
    username = message.from_user.username

    existing_user = session.query(User).filter_by(user_id=user_id).first()
    if not existing_user:
        new_user = User(user_id=user_id, username=username)
        session.add(new_user)
        session.commit()

    if int(message.from_user.id) == int(os.getenv('ADMIN_ID')):
        await message.answer(
            f'Салом админ {full_name}',
            reply_markup=admin_button()
        )
        print(f"Userning id si {user_id}")
        return

    await message.answer(
        f'{"Ассалому алайкум"}, {full_name}\n\n{"Бизнинг ботга хуш келибсиз"}',
        reply_markup=main_menu_button()
    )
    print(f"Temurning id si {user_id}")
    # else:
    # not_subscribed_channels = await is_user_subscribed(user_id, bot)

    # Admin check

    # if not not_subscribed_channels:
    #
    #     await message.answer(
    #         f'{"Ассалому алайкум"}, {full_name}\n\n{"Бизнинг ботга хуш келибсиз"}',
    #         reply_markup=main_button()
    #     )
    # # else:
    #     markup = await get_subscription_check_markup(user_id, bot)
    #     await message.answer("Ассалому алайкум! Обуна бўлинг: ", reply_markup=markup)
    #
    #     await state.set_state('awaiting_subscription')
