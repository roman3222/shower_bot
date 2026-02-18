import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)
from config import BOT_TOKEN, ADMIN_USER_ID, CAR_BODY_TYPES, WASH_TYPES
from database import Database

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация БД
db = Database()

# Глобальная переменная для хранения объекта приложения
app = None

# Состояния для ConversationHandler
SELECT_ACTION, SELECT_CAR_BODY, SELECT_WASH_TYPE, SELECT_DATE, SELECT_TIME, ENTER_PHONE, CONFIRM_BOOKING = range(7)


class CarWashBot:
    def __init__(self):
        pass

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        db.add_user(user.id, user.username, user.first_name)
        logger.info(f"👤 Пользователь {user.first_name} (ID: {user.id}) запустил бота")

        welcome_text = (
            f"👋 Добро пожаловать, {user.first_name}!\n\n"
            f"🚗 <b>Автомойка Бот</b> — ваш помощник для быстрой записи на автомойку.\n\n"
            f"<b>📌 Что умеет бот:</b>\n"
            f"• 📝 Запись на мойку в удобное время\n"
            f"• 📋 Просмотр ваших активных записей\n"
            f"• ❌ Отмена записей онлайн\n\n"
            f"<b>❓ Нужна помощь?</b> Нажмите сюда /help\n\n"
            f"Что вы хотите сделать?"
        )

        keyboard = [
            [InlineKeyboardButton("📝 Записаться", callback_data="book_wash")],
            [InlineKeyboardButton("📋 Мои записи", callback_data="my_bookings")],
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.message:
            await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='HTML')
        elif update.callback_query:
            await update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup, parse_mode='HTML')

        return SELECT_ACTION

    # ============================================================
    # 🆕 КОМАНДА /help
    # ============================================================
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_text = (
            "📖 <b>Инструкция по использованию бота</b>\n\n"
            "<b>🚗 Основные команды:</b>\n"
            "<code>/start</code> — Запустить бота и вернуться в главное меню\n"
            "<code>/help</code> — Показать эту инструкцию\n"
            "<code>/admin</code> — Показать все активные записи (только для администратора)\n\n"
            "<b>📝 Как записаться на мойку:</b>\n"
            "1. Нажмите кнопку <b>📝 Записаться</b>\n"
            "2. Выберите тип кузова вашего автомобиля\n"
            "3. Выберите тип мойки\n"
            "4. Выберите удобную дату и время\n"
            "5. Введите номер телефона в формате <code>+7XXXXXXXXXX</code>\n"
            "6. Подтвердите запись\n\n"
            "<b>📋 Управление записями:</b>\n"
            "• <b>Мои записи</b> — просмотр всех активных записей\n"
            "• <b>Отменить запись</b> — нажмите на кнопку ❌ рядом с записью\n\n"
            "🚗 Ждём вас на мойке!"
        )

        keyboard = [
            [InlineKeyboardButton("📝 Записаться", callback_data="book_wash")],
            [InlineKeyboardButton("📋 Мои записи", callback_data="my_bookings")],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.message:
            await update.message.reply_text(help_text, reply_markup=reply_markup, parse_mode='HTML')
        elif update.callback_query:
            await update.callback_query.edit_message_text(help_text, reply_markup=reply_markup, parse_mode='HTML')

        return SELECT_ACTION

    async def help_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик кнопки помощи из меню"""
        return await self.help_command(update, context)
    # ============================================================

    async def back_to_main_menu(self, query):
        """Вернуться в главное меню"""
        welcome_text = (
            "👋 Главное меню\n\n"
            "<b>📌 Доступные действия:</b>\n"
            "• 📝 Записаться на мойку\n"
            "• 📋 Просмотреть свои записи\n"
            "• ❓ Получить помощь\n\n"
            "Что вы хотите сделать?"
        )

        keyboard = [
            [InlineKeyboardButton("📝 Записаться", callback_data="book_wash")],
            [InlineKeyboardButton("📋 Мои записи", callback_data="my_bookings")],
            [InlineKeyboardButton("❓ Помощь", callback_data="help_info")],
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(welcome_text, reply_markup=reply_markup, parse_mode='HTML')
        return SELECT_ACTION

    async def select_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора действия"""
        query = update.callback_query
        await query.answer()

        if query.data == "cancel":
            await query.edit_message_text("❌ Операция отменена.")
            return ConversationHandler.END

        if query.data == "my_bookings":
            return await self.show_my_bookings(query, context)

        if query.data == "back_to_menu":
            return await self.back_to_main_menu(query)

        # 🆕 Обработчик кнопки помощи
        if query.data == "help_info":
            return await self.help_callback(update, context)

        if query.data.startswith("cancel_booking_"):
            return await self.cancel_booking_handler(update, context)

        if query.data == "book_wash":
            keyboard = []
            for body_key, body_name in CAR_BODY_TYPES.items():
                keyboard.append([InlineKeyboardButton(body_name, callback_data=f"body_{body_key}")])
            keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu")])

            reply_markup = InlineKeyboardMarkup(keyboard)
            text = "🚗 Выберите тип кузова вашего автомобиля:"
            await query.edit_message_text(text, reply_markup=reply_markup)
            return SELECT_CAR_BODY

        return SELECT_ACTION

    async def select_car_body(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора типа кузова"""
        query = update.callback_query
        await query.answer()

        if query.data == "back_to_menu":
            return await self.back_to_main_menu(query)

        body_key = query.data.replace("body_", "")
        context.user_data['car_body_type'] = body_key
        context.user_data['car_body_name'] = CAR_BODY_TYPES[body_key]

        keyboard = []
        for wash_key, wash_name in WASH_TYPES.items():
            keyboard.append([InlineKeyboardButton(wash_name, callback_data=f"wash_{wash_key}")])
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_body")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        text = f"🚗 Тип кузова: {context.user_data['car_body_name']}\n\n💧 Выберите тип мойки:"
        await query.edit_message_text(text, reply_markup=reply_markup)
        return SELECT_WASH_TYPE

    async def select_wash_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора типа мойки"""
        query = update.callback_query
        await query.answer()

        if query.data == "back_to_body":
            keyboard = []
            for body_key, body_name in CAR_BODY_TYPES.items():
                keyboard.append([InlineKeyboardButton(body_name, callback_data=f"body_{body_key}")])
            keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu")])

            reply_markup = InlineKeyboardMarkup(keyboard)
            text = "🚗 Выберите тип кузова вашего автомобиля:"
            await query.edit_message_text(text, reply_markup=reply_markup)
            return SELECT_CAR_BODY

        wash_key = query.data.replace("wash_", "")
        context.user_data['wash_type'] = wash_key
        context.user_data['wash_type_name'] = WASH_TYPES[wash_key]

        available_dates = db.get_available_dates()
        if not available_dates:
            await query.edit_message_text("😞 К сожалению, нет доступных дат для записи.")
            return ConversationHandler.END

        keyboard = []
        for date in available_dates:
            date_str = date.strftime('%d.%m.%Y')
            day_name = self.get_day_name(date.weekday())
            keyboard.append([
                InlineKeyboardButton(f"{day_name}, {date_str}", callback_data=f"date_{date.strftime('%Y-%m-%d')}")
            ])
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_wash")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        text = (
            f"🚗 Тип кузова: {context.user_data['car_body_name']}\n"
            f"💧 Тип мойки: {context.user_data['wash_type_name']}\n\n"
            f"📅 Выберите дату:"
        )
        await query.edit_message_text(text, reply_markup=reply_markup)
        return SELECT_DATE

    async def select_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора даты"""
        query = update.callback_query
        await query.answer()

        if query.data == "back_to_wash":
            keyboard = []
            for wash_key, wash_name in WASH_TYPES.items():
                keyboard.append([InlineKeyboardButton(wash_name, callback_data=f"wash_{wash_key}")])
            keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_body")])

            reply_markup = InlineKeyboardMarkup(keyboard)
            text = f"🚗 Тип кузова: {context.user_data['car_body_name']}\n\n💧 Выберите тип мойки:"
            await query.edit_message_text(text, reply_markup=reply_markup)
            return SELECT_WASH_TYPE

        date_str = query.data.replace("date_", "")
        context.user_data['booking_date'] = date_str

        available_times = db.get_available_times(date_str)
        if not available_times:
            await query.edit_message_text("😞 К сожалению, на эту дату нет свободного времени.")
            return SELECT_DATE

        keyboard = []
        for time_slot in available_times:
            keyboard.append([
                InlineKeyboardButton(
                    f"⏰ {time_slot['time']} ({time_slot['available']} мест)",
                    callback_data=f"time_{time_slot['time']}"
                )
            ])
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_dates")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        date_formatted = date_obj.strftime('%d.%m.%Y')
        day_name = self.get_day_name(date_obj.weekday())

        text = (
            f"🚗 Тип кузова: {context.user_data['car_body_name']}\n"
            f"💧 Тип мойки: {context.user_data['wash_type_name']}\n"
            f"📅 Дата: {day_name}, {date_formatted}\n\n"
            f"⏰ Выберите время:"
        )
        await query.edit_message_text(text, reply_markup=reply_markup)
        return SELECT_TIME

    async def select_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора времени"""
        query = update.callback_query
        await query.answer()

        if query.data == "back_to_dates":
            available_dates = db.get_available_dates()
            keyboard = []
            for date in available_dates:
                date_str = date.strftime('%d.%m.%Y')
                day_name = self.get_day_name(date.weekday())
                keyboard.append([
                    InlineKeyboardButton(f"{day_name}, {date_str}", callback_data=f"date_{date.strftime('%Y-%m-%d')}")
                ])
            keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_wash")])
            reply_markup = InlineKeyboardMarkup(keyboard)

            text = (
                f"🚗 Тип кузова: {context.user_data['car_body_name']}\n"
                f"💧 Тип мойки: {context.user_data['wash_type_name']}\n\n"
                f"📅 Выберите дату:"
            )
            await query.edit_message_text(text, reply_markup=reply_markup)
            return SELECT_DATE

        time_str = query.data.replace("time_", "")
        context.user_data['booking_time'] = time_str

        date_obj = datetime.strptime(context.user_data['booking_date'], '%Y-%m-%d').date()
        date_formatted = date_obj.strftime('%d.%m.%Y')
        day_name = self.get_day_name(date_obj.weekday())

        text = (
            f"📞 Введите ваш номер телефона в формате: +7XXXXXXXXXX\n\n"
            f"🚗 Тип кузова: {context.user_data['car_body_name']}\n"
            f"💧 Тип мойки: {context.user_data['wash_type_name']}\n"
            f"📅 Дата: {day_name}, {date_formatted}\n"
            f"⏰ Время: {context.user_data['booking_time']}"
        )
        await query.edit_message_text(text)
        return ENTER_PHONE

    async def enter_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ввода номера телефона"""
        phone = update.message.text.strip()

        if not self.validate_phone(phone):
            await update.message.reply_text(
                "❌ Неверный формат номера телефона.\n"
                "Пожалуйста, введите номер в формате: +7XXXXXXXXXX"
            )
            return ENTER_PHONE

        context.user_data['phone'] = phone
        db.update_user_phone(update.effective_user.id, phone)

        date_obj = datetime.strptime(context.user_data['booking_date'], '%Y-%m-%d').date()
        date_formatted = date_obj.strftime('%d.%m.%Y')
        day_name = self.get_day_name(date_obj.weekday())

        confirmation_text = (
            f"✅ Подтвердите вашу запись:\n\n"
            f"🚗 Тип кузова: {context.user_data['car_body_name']}\n"
            f"💧 Тип мойки: {context.user_data['wash_type_name']}\n"
            f"📅 Дата: {day_name}, {date_formatted}\n"
            f"⏰ Время: {context.user_data['booking_time']}\n"
            f"📞 Телефон: {phone}\n\n"
            f"Все верно?"
        )

        keyboard = [
            [
                InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_yes"),
                InlineKeyboardButton("❌ Отменить", callback_data="confirm_no")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(confirmation_text, reply_markup=reply_markup)
        return CONFIRM_BOOKING

    async def send_admin_notification(self, user_id: int, user_name: str, booking_data: dict):
        """Отправить уведомление администратору о новой записи"""
        if not ADMIN_USER_ID or ADMIN_USER_ID == 0:
            logger.warning("ADMIN_USER_ID не установлен, уведомление не отправлено")
            return
        try:
            date_obj = datetime.strptime(booking_data['booking_date'], '%Y-%m-%d').date()
            date_formatted = date_obj.strftime('%d.%m.%Y')
            day_name = self.get_day_name(date_obj.weekday())

            notification_text = (
                f"📢 <b>Новая запись на автомойку!</b>\n\n"
                f"👤 <b>Клиент:</b> {user_name}\n"
                f"🆔 <b>ID:</b> {user_id}\n"
                f"📞 <b>Телефон:</b> {booking_data['phone']}\n"
                f"🚗 <b>Тип кузова:</b> {booking_data['car_body_name']}\n"
                f"💧 <b>Тип мойки:</b> {booking_data['wash_type_name']}\n"
                f"📅 <b>Дата:</b> {day_name}, {date_formatted}\n"
                f"⏰ <b>Время:</b> {booking_data['booking_time']}\n"
            )
            await app.bot.send_message(chat_id=ADMIN_USER_ID, text=notification_text, parse_mode='HTML')
            logger.info(f"✅ Уведомление отправлено администратору о записи пользователя {user_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке уведомления администратору: {e}")

    async def send_admin_cancellation_notification(self, user_id: int, user_name: str, booking_data: dict):
        """Отправить уведомление администратору об отмене записи"""
        if not ADMIN_USER_ID or ADMIN_USER_ID == 0:
            logger.warning("ADMIN_USER_ID не установлен, уведомление об отмене не отправлено")
            return
        try:
            date_obj = datetime.strptime(booking_data['booking_date'], '%Y-%m-%d').date()
            date_formatted = date_obj.strftime('%d.%m.%Y')
            day_name = self.get_day_name(date_obj.weekday())

            notification_text = (
                f"❌ <b>Отмена записи на автомойку!</b>\n\n"
                f"👤 <b>Клиент:</b> {user_name}\n"
                f"🆔 <b>ID:</b> {user_id}\n"
                f"📞 <b>Телефон:</b> {booking_data['phone']}\n"
                f"🚗 <b>Тип кузова:</b> {booking_data['car_body_name']}\n"
                f"💧 <b>Тип мойки:</b> {booking_data['wash_type_name']}\n"
                f"📅 <b>Дата:</b> {day_name}, {date_formatted}\n"
                f"⏰ <b>Время:</b> {booking_data['booking_time']}\n"
            )
            await app.bot.send_message(chat_id=ADMIN_USER_ID, text=notification_text, parse_mode='HTML')
            logger.info(f"✅ Уведомление об отмене отправлено администратору о пользователе {user_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке уведомления об отмене администратору: {e}")

    async def confirm_booking(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик подтверждения записи"""
        query = update.callback_query
        await query.answer()

        if query.data == "confirm_no":
            await query.edit_message_text("❌ Запись отменена.")
            return ConversationHandler.END

        success = db.add_booking(
            user_id=update.effective_user.id,
            booking_date=context.user_data['booking_date'],
            booking_time=context.user_data['booking_time'],
            service=f"{context.user_data['car_body_name']} - {context.user_data['wash_type_name']}",
            phone=context.user_data['phone'],
            car_body_type=context.user_data['car_body_type'],
            wash_type=context.user_data['wash_type']
        )

        if success:
            date_obj = datetime.strptime(context.user_data['booking_date'], '%Y-%m-%d').date()
            date_formatted = date_obj.strftime('%d.%m.%Y')
            day_name = self.get_day_name(date_obj.weekday())

            success_text = (
                f"🎉 Спасибо! Ваша запись подтверждена!\n\n"
                f"🚗 Тип кузова: {context.user_data['car_body_name']}\n"
                f"💧 Тип мойки: {context.user_data['wash_type_name']}\n"
                f"📅 Дата: {day_name}, {date_formatted}\n"
                f"⏰ Время: {context.user_data['booking_time']}\n"
                f"📞 Телефон: {context.user_data['phone']}\n\n"
                f"Мы ждем вас! 🚗✨"
            )
            await query.edit_message_text(success_text)

            await self.send_admin_notification(
                user_id=update.effective_user.id,
                user_name=update.effective_user.first_name,
                booking_data={
                    'booking_date': context.user_data['booking_date'],
                    'booking_time': context.user_data['booking_time'],
                    'car_body_name': context.user_data['car_body_name'],
                    'wash_type_name': context.user_data['wash_type_name'],
                    'phone': context.user_data['phone']
                }
            )
        else:
            await query.edit_message_text("❌ Ошибка при создании записи. Это время уже занято. Пожалуйста, выберите другое время.")

        return ConversationHandler.END

    async def show_my_bookings(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Показать записи пользователя"""
        bookings = db.get_user_bookings(query.from_user.id)

        if not bookings:
            await query.edit_message_text(
                "📋 У вас нет активных записей.\n\n"
                "Нажмите /start для возврата в меню или /help для инструкции."
            )
            return ConversationHandler.END

        text = "📋 Ваши записи:\n\n"
        keyboard = []

        for booking in bookings:
            date_obj = datetime.strptime(booking['booking_date'], '%Y-%m-%d').date()
            date_formatted = date_obj.strftime('%d.%m.%Y')
            day_name = self.get_day_name(date_obj.weekday())
            car_body_name = CAR_BODY_TYPES.get(booking['car_body_type'], 'Неизвестно')
            wash_type_name = WASH_TYPES.get(booking['wash_type'], 'Неизвестно')

            text += (
                f"🆔 ID: {booking['id']}\n"
                f"🚗 Тип кузова: {car_body_name}\n"
                f"💧 Тип мойки: {wash_type_name}\n"
                f"📅 Дата: {day_name}, {date_formatted}\n"
                f"⏰ Время: {booking['booking_time']}\n"
                f"📞 Телефон: {booking['phone']}\n"
                f"{'─' * 40}\n"
            )
            keyboard.append([
                InlineKeyboardButton(f"❌ Отменить запись #{booking['id']}", callback_data=f"cancel_booking_{booking['id']}")
            ])

        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)
        return SELECT_ACTION

    async def show_all_bookings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать все активные записи (только для администратора)"""
        user_id = update.effective_user.id

        if user_id != ADMIN_USER_ID:
            await update.message.reply_text("❌ Доступ запрещён. Эта команда только для администратора.")
            return ConversationHandler.END

        bookings = db.get_all_bookings()

        if not bookings:
            await update.message.reply_text("📋 На данный момент нет активных записей.")
            return ConversationHandler.END

        text = f"📊 <b>Все активные записи ({len(bookings)}):</b>\n\n"

        for booking in bookings:
            date_obj = datetime.strptime(booking['booking_date'], '%Y-%m-%d').date()
            date_formatted = date_obj.strftime('%d.%m.%Y')
            day_name = self.get_day_name(date_obj.weekday())
            car_body_name = CAR_BODY_TYPES.get(booking['car_body_type'], 'Неизвестно')
            wash_type_name = WASH_TYPES.get(booking['wash_type'], 'Неизвестно')
            user_name = booking.get('username', 'Неизвестно') or 'Неизвестно'

            text += (
                f"🆔 <b>Запись #{booking['id']}</b>\n"
                f"👤 <b>Клиент:</b> {user_name} (ID: {booking['user_id']})\n"
                f"📞 <b>Телефон:</b> {booking['phone']}\n"
                f"🚗 <b>Тип кузова:</b> {car_body_name}\n"
                f"💧 <b>Тип мойки:</b> {wash_type_name}\n"
                f"📅 <b>Дата:</b> {day_name}, {date_formatted}\n"
                f"⏰ <b>Время:</b> {booking['booking_time']}\n"
                f"{'─' * 40}\n"
            )

        if len(text) > 4096:
            parts = [text[i:i+4000] for i in range(0, len(text), 4000)]
            for part in parts:
                await update.message.reply_text(part, parse_mode='HTML')
        else:
            await update.message.reply_text(text, parse_mode='HTML')

        return ConversationHandler.END

    async def cancel_booking_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик отмены записи"""
        query = update.callback_query
        await query.answer()

        if query.data == "back_to_menu":
            return await self.back_to_main_menu(query)

        booking_id = int(query.data.replace("cancel_booking_", ""))

        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM bookings WHERE id = ? AND user_id = ?', (booking_id, query.from_user.id))
        booking = cursor.fetchone()
        conn.close()

        if booking:
            await self.send_admin_cancellation_notification(
                user_id=query.from_user.id,
                user_name=query.from_user.first_name,
                booking_data={
                    'booking_date': booking['booking_date'],
                    'booking_time': booking['booking_time'],
                    'car_body_name': CAR_BODY_TYPES.get(booking['car_body_type'], 'Неизвестно'),
                    'wash_type_name': WASH_TYPES.get(booking['wash_type'], 'Неизвестно'),
                    'phone': booking['phone']
                }
            )

        db.cancel_booking(booking_id, query.from_user.id)
        await query.edit_message_text("✅ Запись отменена.")
        return ConversationHandler.END

    @staticmethod
    def get_day_name(weekday):
        days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        return days[weekday]

    @staticmethod
    def validate_phone(phone):
        import re
        pattern = r'^\+7\d{10}$'
        return re.match(pattern, phone) is not None


def main():
    """Главная функция"""
    global app
    bot = CarWashBot()

    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    app = application  # Сохраняем глобальную ссылку на приложение

    # Создаем ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', bot.start)],
        states={
            SELECT_ACTION: [
                CallbackQueryHandler(bot.select_action, pattern='^book_wash|^my_bookings|^cancel|^back_to_menu|^cancel_booking_')
            ],
            SELECT_CAR_BODY: [
                CallbackQueryHandler(bot.select_car_body, pattern='^body_|^back_to_menu')
            ],
            SELECT_WASH_TYPE: [
                CallbackQueryHandler(bot.select_wash_type, pattern='^wash_|^back_to_body')
            ],
            SELECT_DATE: [
                CallbackQueryHandler(bot.select_date, pattern='^date_|^back_to_wash')
            ],
            SELECT_TIME: [
                CallbackQueryHandler(bot.select_time, pattern='^time_|^back_to_dates')
            ],
            ENTER_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.enter_phone)
            ],
            CONFIRM_BOOKING: [
                CallbackQueryHandler(bot.confirm_booking, pattern='^confirm_')
            ]
        },
        # Исправлено: добавлен CommandHandler для /start в fallbacks
        fallbacks=[
            CommandHandler('start', bot.start),
            CallbackQueryHandler(bot.cancel_booking_handler, pattern='^cancel_booking_|^back_to_menu')
        ]
    )

    application.add_handler(conv_handler)
    
    # === КОМАНДЫ ДЛЯ АДМИНИСТРАТОРА ===
    application.add_handler(CommandHandler('admin', bot.show_all_bookings))
    application.add_handler(CommandHandler('help', bot.help_command))
    # ========================================

    # Запускаем бота
    logger.info("🚗 Бот запущен и готов к работе!")

    async def cleanup_old_bookings(context):
        db.remove_expired_bookings()

    # Запуск проверки каждые 60 минут
        application.job_queue.run_repeating(cleanup_old_bookings, interval=3600, first=10)
    application.run_polling()


if __name__ == '__main__':
    main()