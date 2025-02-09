from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from config import BOT_TOKEN
from models import Client, Appointment, Availability # Добавили импорт Availability
from database import get_session
from keyboards import main_menu_keyboard, date_keyboard, time_keyboard, service_keyboard, confirmation_keyboard, appointments_keyboard, master_keyboard # Добавили импорт master_keyboard
from datetime import datetime, timedelta
import logging

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Словарь цен на услуги
service_prices = {
    "Маникюр": 500,  # Пример цены
    "Педикюр": 800,  # Пример цены
}

MASTER_TELEGRAM_ID = 1058019303  # Замените на реальный Telegram ID мастера

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.message.from_user
    session = get_session()

    client = session.query(Client).filter_by(telegram_id=user.id).first()
    if not client:
        # Новый пользователь. Запросим доступ к данным.
        keyboard = [
            [KeyboardButton("Предоставить доступ к данным", request_contact=True)],
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text("Привет! Для начала работы, пожалуйста, предоставьте доступ к вашему номеру телефона.", reply_markup=reply_markup)

    else:
        await update.message.reply_text(f"С возвращением, {client.name}!", reply_markup=ReplyKeyboardRemove())

        # Проверяем, является ли пользователь мастером
        if context.user_data.get('is_master'):
            await update.message.reply_text("Режим мастера активирован.", reply_markup=master_keyboard())
        else:
            await update.message.reply_text("Выберите действие:", reply_markup=main_menu_keyboard())

async def contact_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик получения контактных данных."""
    user = update.message.from_user
    contact = update.message.contact
    session = get_session()

    client = session.query(Client).filter_by(telegram_id=user.id).first()
    if not client: # Дополнительная проверка, вдруг контакт пришел раньше /start
        client = Client(telegram_id=user.id, name=user.first_name, phone_number=contact.phone_number) # Берем имя из user.first_name
        session.add(client)
        session.commit()

        await update.message.reply_text(f"Спасибо, {user.first_name}! Ваши данные сохранены.", reply_markup=ReplyKeyboardRemove())
        # Проверяем, является ли пользователь мастером
        if context.user_data.get('is_master'):
            await update.message.reply_text("Режим мастера активирован.", reply_markup=master_keyboard())
        else:
            await update.message.reply_text("Выберите действие:", reply_markup=main_menu_keyboard())


    else:
        await update.message.reply_text("Что-то пошло не так. Пожалуйста, попробуйте еще раз команду /start.", reply_markup=ReplyKeyboardRemove())

async def delete_message_if_exists(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id_key: str):
    """Удаляет сообщение, если его message_id сохранен в context.user_data."""
    if message_id_key in context.user_data:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=context.user_data[message_id_key])
        except Exception as e:
            logger.error(f"Не удалось удалить сообщение (key={message_id_key}): {e}")
        del context.user_data[message_id_key]


async def create_appointment(context: ContextTypes.DEFAULT_TYPE, client_id: int, selected_datetime: datetime, selected_service: str, price: int):
    """Создает запись в базе данных."""
    appointment = Appointment(client_id=client_id, date_time=selected_datetime, service=selected_service, price=price)
    session = get_session()
    session.add(appointment)
    session.commit()

async def master_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /master_login (или аналогичной)"""
    user = update.message.from_user
    if user.id == MASTER_TELEGRAM_ID:
        context.user_data['is_master'] = True  # Устанавливаем флаг, что пользователь - мастер
        await update.message.reply_text("Режим мастера активирован.", reply_markup=master_keyboard())
    else:
        await update.message.reply_text("У вас нет прав для выполнения этой команды.")


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатия на кнопки"""
    query = update.callback_query
    await query.answer() # Обязательно нужно подтвердить нажатие

    logger.info(f"Нажата кнопка: {query.data}")  # Логируем нажатие кнопки

    try:
        # Проверяем, является ли пользователь мастером
        if context.user_data.get('is_master'):
            # Обработка кнопок мастера
            if query.data == "master_add_availability":
                await query.edit_message_text("Функция добавления доступного времени пока не реализована.", reply_markup=main_menu_keyboard())
            elif query.data == "master_delete_availability":
                await query.edit_message_text("Функция удаления доступного времени пока не реализована.", reply_markup=main_menu_keyboard())
            elif query.data == "master_edit_contacts":
                await query.edit_message_text("Функция редактирования контактов пока не реализована.", reply_markup=main_menu_keyboard())
            elif query.data == "master_edit_prices":
                await query.edit_message_text("Функция редактирования прайс-листа пока не реализована.", reply_markup=main_menu_keyboard())
        else:
            # Обработка кнопок клиента
            if query.data == "make_appointment":
                await query.edit_message_text("Выберите дату для записи:", reply_markup=date_keyboard())
            elif query.data == "view_appointments":
                # Получаем записи пользователя из базы данных
                user = update.callback_query.from_user
                session = get_session()
                client = session.query(Client).filter_by(telegram_id=user.id).first()

                if client:
                    appointments = session.query(Appointment).filter_by(client_id=client.id).all()

                    if appointments:
                        # Формируем список записей с кнопками "Удалить"
                        message_text = "Ваши записи:\n"
                        keyboard = []
                        for appointment in appointments:
                            keyboard.append([
                                InlineKeyboardButton(
                                    f"{appointment.date_time.strftime('%d.%m.%Y %H:%M')} - {appointment.service} - {appointment.price} руб.",
                                    callback_data="no_action"),
                                InlineKeyboardButton("Удалить", callback_data=f"cancel_{appointment.id}")
                            ])

                        reply_markup = InlineKeyboardMarkup(keyboard)
                        message = await query.edit_message_text(message_text, reply_markup=reply_markup)
                        context.user_data["appointments_message_id"] = message.message_id

                    else:
                        message = await query.edit_message_text("У вас нет записей.", reply_markup=appointments_keyboard())
                        context.user_data["no_appointments_message_id"] = message.message_id
                else:
                    await query.edit_message_text("Произошла ошибка. Пожалуйста, попробуйте еще раз.")

            elif query.data == "services_and_prices":
                 await query.edit_message_text("Наши услуги и цены:",reply_markup = main_menu_keyboard())
            elif query.data.startswith("date_"):  # Обрабатываем выбор даты
                selected_date = query.data[5:]  # Извлекаем дату из callback_data
                context.user_data["selected_date"] = selected_date # Сохраняем дату во временном хранилище
                await query.edit_message_text(f"Вы выбрали дату: {selected_date}. Теперь выберите время:", reply_markup=time_keyboard())
            elif query.data.startswith("time_"): # Обрабатываем выбор времени
                selected_time = query.data[5:] # Извлекаем время из callback_data
                context.user_data["selected_time"] = selected_time # Сохраняем время во временном хранилище
                selected_date = context.user_data["selected_date"] # Извлекаем дату из временного хранилища
                await query.edit_message_text(f"Вы выбрали {selected_date} в {selected_time}. Теперь выберите услугу:", reply_markup=service_keyboard()) # Отправляем клавиатуру выбора услуги
            elif query.data.startswith("service_"): # Обрабатываем выбор услуги
                selected_service = query.data[8:] # Извлекаем услугу из callback_data
                context.user_data["selected_service"] = selected_service # Сохраняем услугу во временном хранилище

                selected_date_str = context.user_data["selected_date"]
                selected_time = context.user_data["selected_time"]

                # Преобразуем дату и время в datetime объект
                selected_datetime_str = f"{selected_date_str} {selected_time}"
                selected_datetime = datetime.strptime(selected_datetime_str, "%d.%m.%Y %H:%M")

                # Получаем цену услуги из словаря
                price = service_prices.get(selected_service, 0)  # Если услуга не найдена, цена будет 0

                # Формируем сообщение с подтверждением
                confirmation_message = (
                    f"Подтвердите запись:\n"
                    f"Дата: {selected_date_str}\n"
                    f"Время: {selected_time}\n"
                    f"Услуга: {selected_service}\n"
                    f"Цена: {price} руб." # Добавляем цену в сообщение
                )
                await query.edit_message_text(confirmation_message, reply_markup=confirmation_keyboard()) # Отправляем клавиатуру подтверждения
            elif query.data == "back_to_date":  # Обрабатываем нажатие кнопки "Назад" к дате
                await query.edit_message_text("Выберите дату для записи:", reply_markup=date_keyboard()) # Возвращаемся к выбору даты
            elif query.data == "back_to_time": # Обрабатываем нажатие кнопки "Назад" к времени
                await query.edit_message_text("Выберите время:", reply_markup=time_keyboard()) # Возвращаемся к выбору времени
            elif query.data == "back_to_service": # Обрабатываем нажатие кнопки "Назад" к услугам
                await query.edit_message_text("Выберите услугу:", reply_markup=service_keyboard()) # Возвращаемся к выбору услуги
            elif query.data == "confirm_appointment": # Обрабатываем подтверждение записи
                selected_date_str = context.user_data["selected_date"]
                selected_time = context.user_data["selected_time"]
                selected_service = context.user_data["selected_service"]

                # Преобразуем дату и время в datetime объект
                selected_datetime_str = f"{selected_date_str} {selected_time}"
                selected_datetime = datetime.strptime(selected_datetime_str, "%d.%m.%Y %H:%M")

                user = query.from_user
                session = get_session()
                client = session.query(Client).filter_by(telegram_id=user.id).first()

                # Получаем цену услуги из словаря
                price = service_prices.get(selected_service, 0)  # Если услуга не найдена, цена будет 0

                if client:
                    await create_appointment(context, client.id, selected_datetime, selected_service, price)
                    await query.edit_message_text("Запись успешно создана!", reply_markup=main_menu_keyboard())

                else:
                    await query.edit_message_text("Произошла ошибка. Пожалуйста, попробуйте еще раз.", reply_markup=main_menu_keyboard())
            elif query.data == "cancel_appointment":
                await query.edit_message_text("Действие отменено, возвращаюсь в главное меню.", reply_markup=main_menu_keyboard())
            elif query.data.startswith("cancel_"): # Обрабатываем отмену записи
                appointment_id = int(query.data[7:]) # Извлекаем ID записи
                session = get_session()
                appointment = session.query(Appointment).filter_by(id=appointment_id).first()

                if appointment:
                    session.delete(appointment)
                    session.commit()

                    await delete_message_if_exists(context, query.message.chat_id, "appointments_message_id")
                    await delete_message_if_exists(context, query.message.chat_id, "appointments_keyboard_message_id")
                    # Отправляем новое сообщение вместо редактирования старого
                    await context.bot.send_message(chat_id=query.message.chat_id, text="Запись успешно отменена.", reply_markup=main_menu_keyboard())
                else:
                    await query.edit_message_text("Произошла ошибка при отмене записи.", reply_markup=main_menu_keyboard())
            elif query.data == "no_action":
                 await query.answer()
            elif query.data == "main_menu":
                await delete_message_if_exists(context, query.message.chat_id, "appointments_message_id")
                await delete_message_if_exists(context, query.message.chat_id, "appointments_keyboard_message_id")
                await delete_message_if_exists(context, query.message.chat_id, "no_appointments_message_id")
                # Отправляем новое сообщение вместо редактирования старого
                await context.bot.send_message(chat_id=query.message.chat_id, text="Главное меню", reply_markup=main_menu_keyboard())

    except Exception as e:
        logger.error(f"Произошла ошибка: {e}") # Логируем ошибку
        if query and query.message:
            await query.edit_message_text("Произошла непредвиденная ошибка. Пожалуйста, попробуйте позже.", reply_markup=main_menu_keyboard())
        else:
            logger.error("Не удалось отправить сообщение об ошибке пользователю.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("master_login", master_login)) # Обработчик для команды /master_login
    app.add_handler(MessageHandler(filters.CONTACT, contact_callback)) # Обработчик для получения контакта
    app.add_handler(CallbackQueryHandler(button))

    app.run_polling()

if __name__ == "__main__":
    main()
