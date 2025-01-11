from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from models import session, Salon, BarberService


def main_menu_button():
    rkb = ReplyKeyboardBuilder()
    rkb.add(KeyboardButton(text='Соч олдириш 💇'), KeyboardButton(text='Салонлар 💇🏻'))
    rkb.adjust(2)
    return rkb.as_markup(resize_keyboard=True)


def salon_list_button():
    rkb = ReplyKeyboardBuilder()
    salons = session.query(Salon).all()

    if not salons:
        print("Датабазада салонлар топилмади.")
    else:
        print(f"Топилган {len(salons)} салон.")

    for salon in salons:
        rkb.add(KeyboardButton(text=salon.name))

    rkb.adjust(2)
    return rkb.as_markup(resize_keyboard=True)


def service_list_button(barber_id):
    rkb = ReplyKeyboardBuilder()

    # Fetch the services related to the specified barber
    barber_services = session.query(BarberService).filter(BarberService.barber_id == barber_id).all()

    # If no barber services are found, log a message
    if not barber_services:
        print("Бу сартарошга тегишли хизматлар топилмади.")
        return None  # Return None if no services are found

    # Log the number of services found
    print(f"Топилган {len(barber_services)} хизмат.")

    # Add each service name to the reply keyboard
    for barber_service in barber_services:
        service = barber_service.service
        rkb.add(KeyboardButton(text=f"{service.name}"))

    # Adjust the keyboard layout (you can change the number depending on how many buttons you want per row)
    rkb.adjust(2)

    # Return the generated keyboard markup
    return rkb.as_markup(resize_keyboard=True)



