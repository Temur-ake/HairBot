from aiogram.fsm.state import StatesGroup, State


class Booking(StatesGroup):
    name = State()  # State for user name
    salon = State()  # State for choosing salon
    barber = State()  # State for choosing barber
    service = State()
    date = State()
    time = State()  # State for choosing the time
    phone = State()  # State for phone number


class AdminState(StatesGroup):
    title = State()
    photo = State()
    end = State()
