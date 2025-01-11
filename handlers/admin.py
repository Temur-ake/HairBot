import asyncio
import os
from datetime import datetime

import aiogram
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from dotenv import load_dotenv

from handlers.inform import get_available_times
from keyboards import main_menu_button
from models import session, User, Barber, Salon, Service
from state import AdminState


def admin_button():
    rkb = ReplyKeyboardBuilder()
    rkb.add(
        KeyboardButton(text='Reklama 🔊'),
        KeyboardButton(text="Admin Bo'limi")
    )
    return rkb.as_markup(resize_keyboard=True)


load_dotenv()
admin_router = Router()


@admin_router.message(F.text == "Admin Bo'limi")
async def admin(message: Message):
    link = 'http://k.feniks.best:8050'
    await message.answer(text=f'Admin Bolimi ga otish {link}')


@admin_router.message(F.text == 'Reklama 🔊', F.from_user.id == int(os.getenv('ADMIN_ID')))
async def admin(message: Message, state: FSMContext):
    await message.answer("Reklama rasmini kiriting !")
    await state.set_state(AdminState.photo)


# Handle photo upload for the ad
@admin_router.message(AdminState.photo, F.from_user.id == int(os.getenv('ADMIN_ID')), ~F.text, F.photo)
async def admin(message: Message, state: FSMContext):
    photo = message.photo[-1].file_id
    await state.update_data({"photo": photo})
    await state.set_state(AdminState.title)
    await message.answer("Reklama haqida to'liq malumot bering !")


@admin_router.message(AdminState.title, F.from_user.id == int(os.getenv('ADMIN_ID')), ~F.photo)
async def admin(message: Message, state: FSMContext):
    title = message.text
    await state.update_data({"title": title})

    data = await state.get_data()
    await state.clear()

    users = session.query(User).filter(User.user_id.isnot(None)).all()

    if not users:
        await message.answer("Hech kimga reklama yuborilmadi. Foydalanuvchilar mavjud emas.")
        return

    tasks = []
    for user in users:
        if user.user_id:
            try:

                chat_member = await message.bot.get_chat_member(user.user_id, user.user_id)

                if chat_member.status == 'left' or chat_member.status == 'kicked':
                    print(f'User {user.user_id} has blocked the bot or left the chat. Skipping.')
                    continue

                tasks.append(message.bot.send_photo(
                    chat_id=user.user_id,
                    photo=data['photo'],
                    caption=data['title']
                ))

            except aiogram.exceptions.TelegramForbiddenError:

                print(f'User {user.user_id} has blocked the bot. Skipping this user.')
                continue

            except aiogram.exceptions.TelegramBadRequest as e:

                if "chat not found" in str(e):
                    print(f'User {user.user_id} not found. Skipping.')
                else:
                    print(f'Failed to send to user {user.user_id}: {e}')
                continue
    await message.answer("Reklama yuborildi !")
    if tasks:
        await asyncio.gather(*tasks)


@admin_router.message(F.text == 'Ортга')
async def back_to(message: Message):
    await message.answer('Бош меню ✅', reply_markup=main_menu_button())


@admin_router.message(F.text == 'Салонлар 💇🏻')
async def show_salon_list(message: Message):
    salons = session.query(Salon).all()
    if salons:
        rkb = ReplyKeyboardBuilder()
        for salon in salons:
            rkb.add(KeyboardButton(text=salon.name))  # List salon names

        rkb.add(KeyboardButton(text="Ортга"))  # Back button
        rkb.adjust(2)
        await message.answer(
            "Сартарошхоналардан бирини танланг:",
            reply_markup=rkb.as_markup(resize_keyboard=True)
        )
    else:
        await message.answer("Ҳозирда сартарошхоналар мавжуд эмас.")


@admin_router.message(lambda message: message.text in [salon.name for salon in session.query(Salon).all()])
async def show_salon_details(message: Message):
    salon_name = message.text
    salon = session.query(Salon).filter(Salon.name == salon_name).first()

    if salon:
        # Get services for the selected salon
        services = session.query(Service).filter(Service.salon_id == salon.id).all()

        # Get barbers who have available times
        barbers = session.query(Barber).filter(Barber.salon_id == salon.id).all()

        # Filter barbers that have at least one available time slot
        barbers_with_available_times = []
        for barber in barbers:
            available_times = get_available_times(barber.id, str(datetime.today().date()))
            if available_times:  # Barber has available time slots
                barbers_with_available_times.append(barber)

        # Format services and barbers into lists
        services_list = '\n'.join(
            [f"- {service.name}: {service.price}" for service in services]) if services else "Хизматлар мавжуд эмас."
        barbers_list = '\n'.join([f"- {barber.name}" for barber in barbers_with_available_times]) if barbers_with_available_times else "Буш вақтли сартарошлар мавжуд эмас."

        # Format the response
        salon_info = \
            f"""
🌟 <b>{salon.name}</b> ҳақида маълумот:

📞 <b>Телефон:</b> {salon.phone}

🛠️ <b>Хизматлар:</b>\n
{services_list}

💇‍♂️ <b>Сартарошлар:</b>\n
{barbers_list}
        """

        # Send salon information
        await message.answer(salon_info)

        # Check if latitude and longitude are valid numbers before sending location
        if salon.latitude and salon.longtitude:
            try:
                # Validate latitude and longitude as float
                latitude = float(salon.latitude)
                longitude = float(salon.longtitude)

                # Send location if valid
                await message.answer_location(latitude, longitude)
            except (ValueError, TypeError):
                await message.answer("Локатсия маълумотлари нотўғри ёки мавжуд эмас.")

        # Back button
        rkb = ReplyKeyboardBuilder()
        rkb.add(KeyboardButton(text="Ортга"))
        await message.answer(reply_markup=rkb.as_markup(resize_keyboard=True))

    else:
        await message.answer("Салон топилмади.")



# @admin_router.message(F.text == 'Сартарошлар ✂️‍')
# async def show_barber_list(message: Message):
#     barbers = session.query(Barber).all()
#     if barbers:
#         rkb = ReplyKeyboardBuilder()
#         for barber in barbers:
#             rkb.add(KeyboardButton(text=barber.name))  # List all barbers
#
#         rkb.add(KeyboardButton(text="Ортга"))  # Back button
#         rkb.adjust(2)
#         await message.answer(
#             "Танланг, сартарош:",
#             reply_markup=rkb.as_markup(resize_keyboard=True)
#         )
#     else:
#         await message.answer("Ҳозирда сартарошлар мавжуд эмас.")
#
#
# @admin_router.message(lambda message: message.text in [barber.name for barber in session.query(Barber).all()])
# async def show_barber_details(message: Message):
#     barber_name = message.text
#     barber = session.query(Barber).filter(Barber.name == barber_name).first()
#
#     if barber:
#         # Get the services the barber provides
#         barber_services = session.query(BarberService).filter(BarberService.barber_id == barber.id).all()
#         barber_services_list = '\n'.join([f"- {service.service.name}" for service in
#                                           barber_services]) if barber_services else "Хизматлар мавжуд эмас."
#
#         # Format the response
#         barber_info = f"""
# 💇‍♂️ <b>{barber.name}</b> ҳақида маълумот:
#
# 💼 <b>Сарторашхона:</b> {barber.salon.name}
#
# 🛠️ <b>Хизматлар:</b>\n
#         {barber_services_list}
#         """
#
#         # Send the barber information with a sticker and back button
#         await message.answer(barber_info)
#
#         # Back button
#         rkb = ReplyKeyboardBuilder()
#         rkb.add(KeyboardButton(text="Ортга"))
#     else:
#         await message.answer("Сартарош топилмади.")

#
# @admin_router.message(F.text == 'Хизматларимиз 💼')
# async def show_services(message: Message):
#     services = session.query(Service).all()
#     if services:
#         rkb = ReplyKeyboardBuilder()
#         for service in services:
#             rkb.add(KeyboardButton(text=service.name))  # List all services
#
#         rkb.add(KeyboardButton(text="Ортга"))  # Back button
#         rkb.adjust(2)
#         await message.answer(
#             "Хизматларимиздан бирини танланг:",
#             reply_markup=rkb.as_markup(resize_keyboard=True)
#         )
#     else:
#         await message.answer("Ҳозирда хизматлар мавжуд эмас.")
#
#
# @admin_router.message(lambda message: message.text in [service.name for service in session.query(Service).all()])
# async def show_service_details(message: Message):
#     service_name = message.text
#     service = session.query(Service).filter(Service.name == service_name).first()
#
#     if service:
#         service_info = f"""
# 🛠️ <b>{service.name}</b> ҳақида маълумот:
#
# 💰 <b>Нарх:</b> {service.price} сўм\n
# ✨ <b>Тавсиф:</b> {service.description}
#         """
#
#         # Send the service information with a sticker and back button
#         await message.answer(service_info)
#
#         # Back button
#         rkb = ReplyKeyboardBuilder()
#         rkb.add(KeyboardButton(text="Ортга"))
#     else:
#         await message.answer("Хизмат топилмади.")
