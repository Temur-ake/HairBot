import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ParseMode
from aiogram.fsm import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Set up logging
logging.basicConfig(level=logging.INFO)

API_TOKEN = 'YOUR_BOT_API_TOKEN'
HAIRDRESSER_CHAT_ID = -1001898131334  # Replace with your hairdresser's group/channel ID

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# SQLAlchemy Setup
DATABASE_URL = "sqlite:///appointments.db"  # SQLite database file

Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()


# Define the models
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)

    appointments = relationship("Appointment", back_populates="user")


class Salon(Base):
    __tablename__ = 'salons'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)

    barbers = relationship("Barber", back_populates="salon")
    appointments = relationship("Appointment", back_populates="salon")


class Barber(Base):
    __tablename__ = 'barbers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    salon_id = Column(Integer, ForeignKey('salons.id'), nullable=False)

    salon = relationship("Salon", back_populates="barbers")
    appointments = relationship("Appointment", back_populates="barber")


class Appointment(Base):
    __tablename__ = 'appointments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    salon_id = Column(Integer, ForeignKey('salons.id'), nullable=False)
    barber_id = Column(Integer, ForeignKey('barbers.id'), nullable=False)
    time = Column(String, nullable=False)

    user = relationship("User", back_populates="appointments")
    salon = relationship("Salon", back_populates="appointments")
    barber = relationship("Barber", back_populates="appointments")


# Create the tables in the database (if they don't already exist)
Base.metadata.create_all(engine)


# States for the bot
class Booking(StatesGroup):
    name = State()  # State for user name
    salon = State()  # State for choosing salon
    barber = State()  # State for choosing barber
    time = State()  # State for choosing the time
    phone = State()  # State for phone number
    confirmation = State()  # State for confirming the booking


# Available time slots for the day (fixed for simplicity)
AVAILABLE_TIMES = [
    "12:00 - 13:00", "13:00 - 14:00", "14:00 - 15:00",
    "15:00 - 16:00", "16:00 - 17:00", "17:00 - 18:00"
]


# Command to start interaction with the bot
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer(
        "Xush kelibsiz! Ismingizni kiriting:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Orqaga")]], resize_keyboard=True)
    )
    await Booking.name.set()


# Handle name input
@dp.message_handler(state=Booking.name)
async def get_name(message: types.Message, state: FSMContext):
    user_name = message.text
    await state.update_data(name=user_name)

    # Show salon list
    salons = session.query(Salon).all()
    salon_names = [salon.name for salon in salons]
    keyboard = [[KeyboardButton(salon_name)] for salon_name in salon_names]
    await message.answer("Tanlang, sartaroshxona:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    await Booking.salon.set()


# Handle salon selection
@dp.message_handler(state=Booking.salon)
async def choose_salon(message: types.Message, state: FSMContext):
    salon_name = message.text
    salon = session.query(Salon).filter(Salon.name == salon_name).first()
    await state.update_data(salon_id=salon.id)

    # Show barber list for the selected salon
    barbers = session.query(Barber).filter(Barber.salon_id == salon.id).all()
    barber_names = [barber.name for barber in barbers]
    keyboard = [[KeyboardButton(barber_name)] for barber_name in barber_names]
    await message.answer("Tanlang, sartarosh:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    await Booking.barber.set()


# Handle barber selection and show available time slots
@dp.message_handler(state=Booking.barber)
async def choose_barber(message: types.Message, state: FSMContext):
    barber_name = message.text
    barber = session.query(Barber).filter(Barber.name == barber_name).first()
    await state.update_data(barber_id=barber.id)

    # Ask the user to pick a date (we assume today for simplicity)
    today = datetime.today().strftime('%Y-%m-%d')
    await message.answer(f"Bugungi sana: {today}. Iltimos, bo'sh vaqtni tanlang.",
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[[KeyboardButton(time)] for time in AVAILABLE_TIMES], resize_keyboard=True))

    await Booking.time.set()


# Handle time selection based on available slots
@dp.message_handler(state=Booking.time)
async def choose_time(message: types.Message, state: FSMContext):
    # Get the selected time and date
    selected_time = message.text
    user_data = await state.get_data()
    barber_id = user_data.get("barber_id")
    selected_date = datetime.today().strftime('%Y-%m-%d')  # assume the user selects today's date

    # Get already booked appointments for this barber on the selected day
    existing_appointments = session.query(Appointment).filter(
        Appointment.barber_id == barber_id,
        Appointment.time.like(f'{selected_date}%')  # Match only today's appointments
    ).all()

    # Extract all already occupied times
    booked_times = [appointment.time for appointment in existing_appointments]

    # Filter out booked times from available times
    available_times = [time for time in AVAILABLE_TIMES if time not in booked_times]

    # If the user selects a time that is already booked, inform them
    if selected_time not in available_times:
        await message.answer("Bu vaqt band. Iltimos, boshqa vaqtni tanlang.")
        return

    # Save the selected time in the state
    await state.update_data(time=selected_time)

    # Ask for the phone number
    await message.answer("Iltimos, telefon raqamingizni kiriting:")
    await Booking.phone.set()


# Handle phone number input
@dp.message_handler(state=Booking.phone)
async def get_phone(message: types.Message, state: FSMContext):
    phone = message.text
    await state.update_data(phone=phone)

    # Confirm booking
    data = await state.get_data()
    name = data.get("name")
    salon_id = data.get("salon_id")
    barber_id = data.get("barber_id")
    time = data.get("time")
    phone = data.get("phone")

    confirmation_message = f"Yangi buyurtma:\nIsm: {name}\nSartaroshxona: {salon_id}\nSartarosh: {barber_id}\nVaqt: {time}\nTelefon: {phone}"

    keyboard = [
        [KeyboardButton("Tasdiqlash")],
        [KeyboardButton("Bekor qilish")]
    ]
    await message.answer(confirmation_message, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    await Booking.confirmation.set()


# Handle booking confirmation or cancellation
@dp.message_handler(state=Booking.confirmation)
async def confirm_booking(message: types.Message, state: FSMContext):
    if message.text == "Tasdiqlash":
        # Get the user data
        data = await state.get_data()
        name = data.get("name")
        salon_id = data.get("salon_id")
        barber_id = data.get("barber_id")
        time = data.get("time")
        phone = data.get("phone")

        # Create a new user if not exists
        user = session.query(User).filter(User.phone == phone).first()
        if not user:
            user = User(name=name, phone=phone)
            session.add(user)
            session.commit()

        # Create new appointment
        appointment = Appointment(user_id=user.id, salon_id=salon_id, barber_id=barber_id, time=time)
        session.add(appointment)
        session.commit()

        # Send to hairdresser's chat
        appointment_details = f"Yangi buyurtma:\nIsm: {name}\nSartaroshxona: {salon_id}\nSartarosh: {barber_id}\nVaqt: {time}\nTelefon: {phone}"
        await bot.send_message(HAIRDRESSER_CHAT_ID, appointment_details)

        # Confirm with the user
        await message.answer("Buyurtmangiz tasdiqlandi! Sizni kutib qolamiz.")
        await state.finish()

    elif message.text == "Bekor qilish":
        await message.answer("Buyurtma bekor qilindi.")
        await state.finish()


if __name__ == '__main__':
    dp.middleware.setup(LoggingMiddleware())
    executor.start_polling(dp, skip_updates=True)
