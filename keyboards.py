from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timedelta

def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("Записаться на прием", callback_data="make_appointment")],
        [InlineKeyboardButton("Мои записи", callback_data="view_appointments")],
        [InlineKeyboardButton("Услуги и цены", callback_data="services_and_prices")],
    ]
    return InlineKeyboardMarkup(keyboard)

def appointment_keyboard():
    # TODO:  Создать клавиатуру для выбора даты и времени.
    # Можно использовать календарь или список доступных слотов.
    pass

def date_keyboard():
    """Создает клавиатуру с кнопками для следующих 7 дней."""
    today = datetime.now().date()
    keyboard = []
    for i in range(7):
        date = today + timedelta(days=i)
        date_str = date.strftime("%d.%m.%Y")
        keyboard.append([InlineKeyboardButton(date_str, callback_data=f"date_{date_str}")])  # callback_data содержит дату
    keyboard.append([InlineKeyboardButton("Отмена", callback_data="cancel_appointment")])
    return InlineKeyboardMarkup(keyboard)

def time_keyboard():
    """Создает клавиатуру с кнопками для выбора времени."""
    time_slots = ["10:00", "12:00", "14:00", "16:00", "18:00"]
    keyboard = []
    for time in time_slots:
        keyboard.append([InlineKeyboardButton(time, callback_data=f"time_{time}")]) # callback_data содержит время
    keyboard.append([InlineKeyboardButton("Назад", callback_data="back_to_date")])
    return InlineKeyboardMarkup(keyboard)

def service_keyboard():
    """Создает клавиатуру с кнопками для выбора услуги."""
    services = ["Маникюр", "Педикюр"]  # Измененный список услуг
    keyboard = []
    for service in services:
        keyboard.append([InlineKeyboardButton(service, callback_data=f"service_{service}")]) # callback_data содержит услугу
    keyboard.append([InlineKeyboardButton("Назад", callback_data="back_to_time")]) # Кнопка "Назад"
    return InlineKeyboardMarkup(keyboard)

def confirmation_keyboard():
    """Создает клавиатуру для подтверждения записи."""
    keyboard = [
        [InlineKeyboardButton("Подтвердить", callback_data="confirm_appointment")],
        [InlineKeyboardButton("Отменить", callback_data="back_to_service")],
    ]
    return InlineKeyboardMarkup(keyboard)

def appointments_keyboard():
    """Создает клавиатуру для отображения списка записей."""
    keyboard = [[InlineKeyboardButton("Назад", callback_data="main_menu")]]
    return InlineKeyboardMarkup(keyboard)

def master_keyboard():
    """Создает клавиатуру для мастера."""
    keyboard = [
        [InlineKeyboardButton("Добавить доступное время", callback_data="master_add_availability")],
        [InlineKeyboardButton("Удалить доступное время", callback_data="master_delete_availability")],
        [InlineKeyboardButton("Редактировать контакты", callback_data="master_edit_contacts")],
        [InlineKeyboardButton("Редактировать прайс", callback_data="master_edit_prices")],
    ]
    return InlineKeyboardMarkup(keyboard)
