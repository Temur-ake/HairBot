from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, Message, ReplyKeyboardRemove, CallbackQuery, InlineKeyboardMarkup, \
    InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from keyboards import main_menu_button, salon_list_button, service_list_button
from models import User, session, Appointment, Barber, Salon, BarberAvailability, BarberService, Service
from state import Booking

inform_router = Router()


def get_available_times(barber_id, selected_date):
    selected_date_obj = datetime.strptime(selected_date, '%Y-%m-%d').date()

    # Tanlangan barber uchun tanlangan kunda bo'sh vaqtlarni olish
    available_times = session.query(BarberAvailability).filter(
        BarberAvailability.barber_id == barber_id,
        func.date(BarberAvailability.available_date) == selected_date_obj
    ).all()

    if not available_times:
        return []

    existing_appointments = session.query(Appointment).filter(
        Appointment.barber_id == barber_id
    ).all()

    # Band bo'lgan vaqtlarni olish
    booked_times = [appointment.time.strftime('%H:%M') for appointment in existing_appointments]

    available_time_slots = [
        availability.free_time.strftime('%H:%M') for availability in available_times
        if availability.free_time.strftime('%H:%M') not in booked_times
    ]

    return available_time_slots



@inform_router.message(F.text == 'Соч олдириш 💇')
async def choose_salon(message: Message, state: FSMContext):
    await message.answer('Сартарошхона танланг:', reply_markup=salon_list_button())
    await state.set_state(Booking.salon)


# Salonni tanlash
@inform_router.message(Booking.salon)
async def choose_salon(message: Message, state: FSMContext):
    salon_name = message.text
    salon = session.query(Salon).filter(Salon.name == salon_name).first()

    if not salon:
        await message.answer("Бу сартарошхона топилмади. Илтимос, бошқа номини танланг.")
        return

    await state.update_data(salon_name=salon.name, salon_id=salon.id)

    selected_date = str(datetime.today().date())

    # Salonning barberlarini va bo'sh vaqtlarini tekshirish
    available_barbers = []
    for barber in salon.barbers:
        available_times = get_available_times(barber.id, selected_date)
        if available_times:
            available_barbers.append(barber)

    if not available_barbers:
        await message.answer(f"Бу сартарошхонада {selected_date} кунда буш сартарошлар мавжуд эмас.", reply_markup=main_menu_button())
        await state.clear()
        return

    rkb = ReplyKeyboardBuilder()
    for barber in available_barbers:
        rkb.add(KeyboardButton(text=barber.name))

    rkb.adjust(2)
    await message.answer(
        "Сартарош танланг :",
        reply_markup=rkb.as_markup(resize_keyboard=True)
    )
    await state.set_state(Booking.barber)


# Barberni tanlash
@inform_router.message(Booking.barber)
async def choose_barber(message: Message, state: FSMContext):
    barber_name = message.text
    selected_date = str(datetime.today().date())

    # Barberni tanlash
    barber = session.query(Barber).filter(Barber.name == barber_name).first()

    if not barber:
        await message.answer("Бу сартарош топилмади. Илтимос, бошқа номини танланг.")
        return

    # Barberning bo'sh vaqtlarini tekshirish
    available_times = get_available_times(barber.id, selected_date)

    if not available_times:
        await message.answer(f"Бу сартарошнинг {selected_date} кунда бўш вақти йўқ. Илтимос, бошқа сартарошни танланг.")
        return

    # Barberni saqlash
    await state.update_data(barber_name=barber.name, barber_id=barber.id)

    # Xizmatlar ro'yxatini olish
    services_keyboard = service_list_button(barber.id)
    await message.answer("Илтимос, хизматни танланг:", reply_markup=services_keyboard)
    await state.set_state(Booking.service)


@inform_router.message(Booking.service)
async def choose_service(message: Message, state: FSMContext):
    service_name = message.text
    user_data = await state.get_data()
    barber_id = user_data.get("barber_id")

    barber = session.query(Barber).filter(Barber.id == barber_id).first()

    if not barber:
        await message.answer("Сартарош топилмади. Илтимос, қайтадан уринган кўринг.")
        return

    barber_service = session.query(BarberService).join(Service).filter(
        BarberService.barber_id == barber.id,
        Service.name == service_name
    ).first()

    if not barber_service:
        await message.answer("Бу хизмат сартарошда мавжуд эмас. Илтимос, бошқа хизматни танланг.")
        return

    await state.update_data(service_name=service_name, service_id=barber_service.service_id)

    available_dates = get_available_dates(barber_id)

    if not available_dates:
        await message.answer(
            f"Ҳозирда {barber.name} нинг бўш кунлар мавжуд эмас. Илтимос, кейинроқ қайта уринган кўринг.")
        return

    rkb = ReplyKeyboardBuilder()
    for date in available_dates:
        rkb.add(KeyboardButton(text=date))

    rkb.adjust(2)
    await message.answer(
        "Сана танланг:",
        reply_markup=rkb.as_markup(resize_keyboard=True)
    )
    await state.set_state(Booking.date)


from datetime import datetime, timedelta
from sqlalchemy.sql import func


def get_available_dates(barber_id):
    today = datetime.today()
    next_7_days = [today + timedelta(days=i) for i in range(6)]  # Keyingi 7 kun
    available_dates = []

    for day in next_7_days:
        day_start = datetime.combine(day, datetime.min.time())  # Kun boshlanishi
        day_end = datetime.combine(day, datetime.max.time())  # Kun oxiri

        # Ushbu kunga sartaroshning bo'sh vaqtlarini olish
        barber_availability = session.query(BarberAvailability).filter(
            BarberAvailability.barber_id == barber_id,
            func.date(BarberAvailability.available_date) == day.date()
        ).all()

        if barber_availability:
            # Ushbu kunga allaqachon band qilingan uchrashuvlarni tekshirish
            existing_appointments = session.query(Appointment).filter(
                Appointment.barber_id == barber_id,
                Appointment.time >= day_start,
                Appointment.time <= day_end
            ).all()

            # Agar band bo'lmagan vaqtlar mavjud bo'lsa, sanani qo'shish
            if not existing_appointments:
                available_dates.append(day.strftime('%Y-%m-%d'))

    return available_dates


@inform_router.message(Booking.date)
async def choose_date(message: Message, state: FSMContext):
    selected_date = message.text
    user_data = await state.get_data()
    barber_id = user_data.get("barber_id")

    available_times = get_available_times(barber_id, selected_date)

    if not available_times:
        await message.answer("Ушбу санада бу Сартарошнинг бўш вақти мавжуд эмас. Илтимос, бошқа сана танланг.",
                             reply_markup=ReplyKeyboardRemove())
        await state.set_state(Booking.date)
        return

    await state.update_data(selected_date=selected_date)  # Sana saqlanadi

    rkb = ReplyKeyboardBuilder()
    for time in available_times:
        rkb.add(KeyboardButton(text=time))

    rkb.adjust(2)
    await message.answer(
        f"Ушбу санадаги: {selected_date}. Бўш вақтлардан бирини танланг:",
        reply_markup=rkb.as_markup(resize_keyboard=True)
    )
    await state.set_state(Booking.time)


@inform_router.message(Booking.time)
async def choose_time(message: Message, state: FSMContext):
    selected_time = message.text
    user_data = await state.get_data()
    barber_id = user_data.get("barber_id")
    selected_date = user_data.get("selected_date")

    await state.update_data(time=selected_time)

    await message.answer("Исмингизни киритинг:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Booking.name)


@inform_router.message(Booking.name)
async def get_name(message: Message, state: FSMContext):
    user_name = message.text
    await state.update_data(name=user_name)

    await message.answer("Телефон рақамингизни киритинг:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Booking.phone)


@inform_router.message(Booking.phone)
async def get_phone(message: Message, state: FSMContext):
    phone = message.text
    await state.update_data(phone=phone)

    data = await state.get_data()
    name = data.get("name")
    salon_name = data.get("salon_name")
    barber_name = data.get("barber_name")
    selected_date = data.get("selected_date")
    start_time = data.get("time")
    service_name = data.get("service_name")
    phone = data.get("phone")

    confirmation_message = f"🆕 Янги буюртма:\n👤 Исм: {name}\n🏠 Сартарошхона: {salon_name}\n💈 Сартарош: {barber_name}\n💇‍♂️ Хизмат: {service_name}\n🌞Кун: {selected_date}\n⏰ Вақт: {start_time}\n📞 Телефон: {phone}"

    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Тасдиқлаш ✅", callback_data="confirm_booking"),
            InlineKeyboardButton(text="Бекор қилиш ❌", callback_data="cancel_booking")
        ]
    ])

    await message.answer(confirmation_message, reply_markup=inline_kb)


@inform_router.callback_query(F.data == "confirm_booking")
async def confirm_booking(callback_query: CallbackQuery, state: FSMContext, bot: Bot):
    user_id = callback_query.from_user.id
    data = await state.get_data()
    name = data.get("name")
    salon_id = int(data.get("salon_id"))
    salon_name = data.get("salon_name")
    barber_id = int(data.get("barber_id"))
    barber_name = data.get("barber_name")
    service_name = data.get("service_name")
    time_str = data['time']  # Time as a string (e.g., '14:30')
    phone = data.get("phone")
    service = data.get("service_id")
    day = data.get("selected_date")  # Assuming day is a string or datetime

    # Convert the time string to a time object (HH:MM)
    time_obj = datetime.strptime(time_str, '%H:%M').time()

    # Combine time with today's date (use a specific date if needed)
    today = datetime.today()
    time_with_date = datetime.combine(today, time_obj)

    # Check if the user exists in the database
    user = session.query(User).filter(User.user_id == user_id).first()

    if not user:
        user = User(user_id=user_id, name=name, phone=phone)
        session.add(user)
        session.commit()

    try:
        # Fetch the barber's user ID using the barber's ID
        barber_user = session.query(Barber).filter(Barber.id == barber_id).first()

        # Create the appointment details message
        appointment_details = f"🆕 Янги буюртма:\n👤 Исм: {name}\n🏠 Сартарошхона: {salon_name}\n💈 Сартарош: {barber_name}\n💇‍♂️ Хизмат: {service_name}\n🌞Кун: {day}\n⏰ Вақт: {time_with_date.strftime('%H:%M')}\n📞 Телефон: {phone}"

        # Send confirmation to the barber if available
        if barber_user and barber_user.user_id:
            await bot.send_message(barber_user.user_id, appointment_details)

        # Send confirmation to the user
        if user_id:
            await bot.send_message(user_id, appointment_details)
            await bot.send_message(callback_query.from_user.id, "Буюртмангиз муваффақиятли тасдиқланди!")

        # Create the appointment in the database
        appointment = Appointment(
            user_id=user.id,
            salon_id=salon_id,
            barber_id=barber_id,
            time=time_with_date,  # Use the combined datetime object
            name=name,
            phone=phone,
            service_id=service
        )
        session.add(appointment)
        session.commit()

    except Exception as e:
        await callback_query.answer("Хатолик юз берди. Илтимос, қайта уриниб кўринг.", show_alert=True)
        print(e)


@inform_router.callback_query(F.data == "cancel_booking")
async def cancel_booking(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer("Буюртма бекор қилинди.", show_alert=True)
    await state.clear()
    await callback_query.message.delete()
