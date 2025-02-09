from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from config import BOT_TOKEN, MASTER_TELEGRAM_ID
from models import Client, Appointment, Availability
from database import session_scope
from keyboards import main_menu_keyboard, date_keyboard, time_keyboard, service_keyboard, confirmation_keyboard, appointments_keyboard, master_keyboard
from datetime import datetime, timedelta
import logging
from functools import wraps

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Словарь цен на услуги
service_prices = {
    "Маникюр": 500,
    "Педикюр": 800,
}

def master_required(func):
    """Декоратор для проверки, является ли пользователь мастером."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.callback_query.from_user.id  # Получаем ID пользователя, вызвавшего callback
        with session_scope() as session:
            client = session.query(Client).filter_by(telegram_id=user_id).first()
            if client and client.role == "master":  # Проверяем роль в базе данных
                # *** ВАЖНО: вызываем оригинальную функцию ***
                return await func(update, context, *args, **kwargs)
            else:
                await update.effective_message.reply_text("У вас нет прав для выполнения этого действия.", reply_markup=main_menu_keyboard())
                return

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.message.from_user
    with session_scope() as session:
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

            # Проверяем, является ли пользователь мастером (из базы данных)
            if client.role == "master":
                await update.message.reply_text("Режим мастера активирован.", reply_markup=master_keyboard())
            else:
                await update.message.reply_text("Выберите действие:", reply_markup=main_menu_keyboard())


async def contact_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик получения контактных данных."""
    user = update.message.from_user
    contact = update.message.contact
    with session_scope() as session:
        client = session.query(Client).filter_by(telegram_id=user.id).first()
        if not client:
            client = Client(telegram_id=user.id, name=user.first_name, phone_number=contact.phone_number)
            # Проверяем, является ли пользователь мастером по ID
            if user.id == MASTER_TELEGRAM_ID:
                client.role = "master"  # Устанавливаем роль мастера
            session.add(client)
            session.commit()

            await update.message.reply_text(f"Спасибо, {user.first_name}! Ваши данные сохранены.", reply_markup=ReplyKeyboardRemove())
             # Проверяем, является ли пользователь мастером (из базы данных)
            if client.role == "master":
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
    with session_scope() as session:
        appointment = Appointment(client_id=client_id, date_time=selected_datetime, service=selected_service, price=price)
        session.add(appointment)
        session.commit()


async def master_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /master_login (или аналогичной)"""
    user = update.message.from_user
    if user.id == MASTER_TELEGRAM_ID:
       with session_scope() as session:
            client = session.query(Client).filter_by(telegram_id=user.id).first()
            if client:
                client.role = "master"
                session.commit()
                await update.message.reply_text("Режим мастера активирован.", reply_markup=master_keyboard())
            else:
                await update.message.reply_text("Пользователь не найден. Сначала используйте /start.", reply_markup=main_menu_keyboard())

    else:
        await update.message.reply_text("У вас нет прав для выполнения этой команды.")


@master_required
async def add_availability(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавляет доступное время (функционал для мастера)."""
    await update.message.reply_text("Введите дату и время в формате ДД.ММ.ГГГГ ЧЧ:ММ, а также услугу (например, 20.07.2024 14:00 Маникюр):")
    context.user_data['awaiting_availability_data'] = True  # Устанавливаем флаг ожидания данных

@master_required
async def delete_availability(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удаляет доступное время (функционал для мастера)."""
    # TODO: Реализуйте логику удаления доступного времени
    await update.message.reply_text("Функционал удаления доступного времени еще не реализован.")

@master_required
async def edit_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Редактирует контакты (функционал для мастера)."""
    # TODO: Реализуйте логику редактирования контактов
    await update.message.reply_text("Функционал редактирования контактов еще не реализован.")

@master_required
async def edit_prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Редактирует прайс-лист (функционал для мастера)."""
    # TODO: Реализуйте логику редактирования прайс-листа
    await update.message.reply_text("Функционал редактирования прайс-листа еще не реализован.")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает текстовые сообщения."""
    if context.user_data.get('awaiting_availability_data'):
        try:
            text = update.message.text
            date_time_str, service = text.rsplit(' ', 1)  # Разделяем строку на дату/время и услугу
            date_time = datetime.strptime(date_time_str, "%d.%m.%Y %H:%M")

            # Создаем запись в таблице Availability
            with session_scope() as session:
                availability = Availability(date=date_time.date(), start_time=date_time, end_time=date_time + timedelta(hours=1), service=service)  # Пример: длительность 1 час
                session.add(availability)
                session.commit()

            await update.message.reply_text(f"Доступность успешно добавлена: {date_time_str} {service}")
        except ValueError:
            await update.message.reply_text("Неверный формат даты и времени. Пожалуйста, используйте ДД.ММ.ГГГГ ЧЧ:ММ Услуга.")
        except Exception as e:
            await update.message.reply_text(f"Произошла ошибка при добавлении доступности: {e}")
        finally:
            context.user_data['awaiting_availability_data'] = False  # Снимаем флаг ожидания

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатия на кнопки"""
    query = update.callback_query
    await query.answer()

    user_id = update.callback_query.from_user.id  # Получаем ID пользователя, вызвавшего callback
    print(f"button: user_id = {user_id}")

    with session_scope() as session:
        client = session.query(Client).filter_by(telegram_id=user_id).first()
        print(f"button: client = {client}")

        if client and client.role == "master":
            # Обработка кнопок мастера
            if query.data == "master_add_availability":
                print("button: master_add_availability")
                await add_availability(update, context)
            elif query.data == "master_delete_availability":
                print("button: master_delete_availability")
                await delete_availability(update, context)
            elif query.data == "master_edit_contacts":
                print("button: master_edit_contacts")
                await edit_contacts(update, context)
            elif query.data == "master_edit_prices":
                print("button: master_edit_prices")
                await edit_prices(update, context)
        else:
            # Обработка кнопок клиента
            if query.data == "make_appointment":
                print("button: make_appointment")
                await query.edit_message_text("Выберите дату для записи:", reply_markup=date_keyboard())
            elif query.data == "view_appointments":
                print("button: view_appointments")
                # Получаем записи пользователя из базы данных
                user = update.callback_query.from_user
                with session_scope() as session:
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
                     print("button: services_and_prices")
                     await query.edit_message_text("Наши услуги и цены:",reply_markup = main_menu_keyboard())
                elif query.data.startswith("date_"):  # Обрабатываем выбор даты
                    print("button: date_")
                    selected_date = query.data[5:]  # Извлекаем дату из callback_data
                    context.user_data["selected_date"] = selected_date # Сохраняем дату во временном хранилище
                    await query.edit_message_text(f"Вы выбрали дату: {selected_date}. Теперь выберите время:", reply_markup=time_keyboard())
                elif query.data.startswith("time_"): # Обрабатываем выбор времени
                    print("button: time_")
                    selected_time = query.data[5:] # Извлекаем время из callback_data
                    context.user_data["selected_time"] = selected_time # Сохраняем время во временном хранилище
                    selected_date = context.user_data["selected_date"] # Извлекаем дату из временного хранилища
                    await query.edit_message_text(f"Вы выбрали {selected_date} в {selected_time}. Теперь выберите услугу:", reply_markup=service_keyboard()) # Отправляем клавиатуру выбора услуги
                elif query.data.startswith("service_"): # Обрабатываем выбор услуги
                    print("button: service_")
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
                    print("button: back_to_date")
                    await query.edit_message_text("Выберите дату для записи:", reply_markup=date_keyboard()) # Возвращаемся к выбору даты
                elif query.data == "back_to_time": # Обрабатываем нажатие кнопки "Назад" к времени
                    print("button: back_to_time")
                    await query.edit_message_text("Выберите время:", reply_markup=time_keyboard()) # Возвращаемся к выбору времени
                elif query.data == "back_to_service": # Обрабатываем нажатие кнопки "Назад" к услугам
                    print("button: back_to_service")
                    await query.edit_message_text("Выберите услугу:", reply_markup=service_keyboard()) # Возвращаемся к выбору услуги
                elif query.data == "confirm_appointment": # Обрабатываем подтверждение записи
                    print("button: confirm_appointment")
                    selected_date_str = context.user_data["selected_date"]
                    selected_time = context.user_data["selected_time"]
                    selected_service = context.user_data["selected_service"]

                    # Преобразуем дату и время в datetime объект
                    selected_datetime_str = f"{selected_date_str} {selected_time}"
                    selected_datetime = datetime.strptime(selected_datetime_str, "%d.%m.%Y %H:%M")

                    user = query.from_user
                    with session_scope() as session:
                        client = session.query(Client).filter_by(telegram_id=user.id).first()

                        # Получаем цену услуги из словаря
                        price = service_prices.get(selected_service, 0)  # Если услуга не найдена, цена будет 0

                        if client:
                            await create_appointment(context, client.id, selected_datetime, selected_service, price)
                            await query.edit_message_text("Запись успешно создана!", reply_markup=main_menu_keyboard())

                        else:
                            await query.edit_message_text("Произошла ошибка. Пожалуйста, попробуйте еще раз.", reply_markup=main_menu_keyboard())
                elif query.data == "cancel_appointment": # Обрабатываем нажатие кнопки "Отмена"
                    print("button: cancel_appointment")
                    await query.edit_message_text("Действие отменено, возвращаюсь в главное меню.", reply_markup=main_menu_keyboard())
                elif query.data.startswith("cancel_"): # Обрабатываем отмену записи
                    print("button: cancel_")
                    appointment_id = int(query.data[7:]) # Извлекаем ID записи
                    with session_scope() as session:
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
                elif query.data == "no_action": # Обрабатываем "no_action"
                     print("button: no_action")
                     await query.answer()
                elif query.data == "main_menu": # Обрабатываем возврат в главное меню
                    print("button: main_menu")
                    await delete_message_if_exists(context, query.message.chat_id, "appointments_message_id")
                    await delete_message_if_exists(context, query.message_chat_id, "appointments_keyboard_message_id")
                    await delete_message_if_exists(context, query.message.chat_id, "no_appointments_message_id")
                    # Отправляем новое сообщение вместо редактирования старого
                    await context.bot.send_message(chat_id=query.message.chat_id, text="Главное меню", reply_markup=main_menu_keyboard())

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("master_login", master_login))
    app.add_handler(MessageHandler(filters.CONTACT, contact_callback))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    app.run_polling()

if __name__ == "__main__":
    main()
