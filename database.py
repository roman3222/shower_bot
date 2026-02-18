import sqlite3
from datetime import datetime, timedelta
from config import DB_PATH, MAX_BOOKINGS_PER_SLOT, DAYS_AHEAD, WORKING_HOURS


class Database:
    def __init__(self):
        self.db_path = DB_PATH
        self.init_db()

    def get_connection(self):
        """Получить подключение к БД"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Инициализировать базу данных"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Таблица записей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                booking_date DATE NOT NULL,
                booking_time TEXT NOT NULL,
                service TEXT NOT NULL,
                phone TEXT NOT NULL,
                car_body_type TEXT,
                wash_type TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                UNIQUE(booking_date, booking_time, user_id)
            )
        ''')

        conn.commit()
        conn.close()

    def add_user(self, user_id, username, first_name):
        """Добавить или обновить пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, username, first_name)
            VALUES (?, ?, ?)
        ''', (user_id, username, first_name))

        conn.commit()
        conn.close()

    def get_all_bookings(self):
        """Получить только активные (будущие) записи"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT b.*, u.username, u.first_name 
            FROM bookings b
            LEFT JOIN users u ON b.user_id = u.user_id
            WHERE b.status = 'active'
            AND (
                b.booking_date > date('now') 
                OR (b.booking_date = date('now') AND b.booking_time > time('now'))
            )
            ORDER BY b.booking_date, b.booking_time
        ''')

        columns = [description[0] for description in cursor.description]
        bookings = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return bookings

    def update_user_phone(self, user_id, phone):
        """Обновить номер телефона пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE users SET phone = ? WHERE user_id = ?
        ''', (phone, user_id))

        conn.commit()
        conn.close()

    def get_available_dates(self):
        """Получить список доступных дат"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        available_dates = []
        today = datetime.now().date()
        
        for i in range(0, DAYS_AHEAD):
            date = today + timedelta(days=i)
            
            # Пропускаем понедельники
            if date.weekday() == 0:  # 0 - понедельник
                continue
            
            # Проверяем, есть ли свободные слоты в этот день
            cursor.execute('''
                SELECT COUNT(*) as count FROM bookings 
                WHERE booking_date = ? AND status = 'active'
            ''', (date.strftime('%Y-%m-%d'),))
            
            result = cursor.fetchone()
            booked_slots = result['count']
            
            # Всего слотов в день: 10 (с 9:00 до 19:00)
            if booked_slots < 10:
                available_dates.append(date)
        
        conn.close()
        return available_dates

    def get_available_times(self, date_str):
        """Получить доступное время для конкретной даты"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        available_times = []
        
        # Генерируем все возможные времена с интервалом из конфига
        start_hour = WORKING_HOURS['start']
        end_hour = WORKING_HOURS['end']
        interval = WORKING_HOURS['interval']
        
        current_time = start_hour * 60  # Переводим в минуты
        end_time = end_hour * 60
        
        # ✅ Получаем текущую дату и время для проверки
        today = datetime.now().date()
        current_datetime = datetime.now()
        
        # ✅ Проверяем, является ли дата сегодняшней
        is_today = (date_str == today.strftime('%Y-%m-%d'))
        
        while current_time < end_time:
            hours = current_time // 60
            minutes = current_time % 60
            time_str = f"{hours:02d}:{minutes:02d}"
            
            # ✅ Если сегодня, пропускаем прошедшее время
            if is_today:
                slot_datetime = current_datetime.replace(hour=hours, minute=minutes, second=0, microsecond=0)
                if slot_datetime <= current_datetime:
                    current_time += int(interval * 60)
                    continue
            
            # Проверяем, сколько записей на это время
            cursor.execute('''
                SELECT COUNT(*) as count FROM bookings 
                WHERE booking_date = ? AND booking_time = ? AND status = 'active'
            ''', (date_str, time_str))
            
            result = cursor.fetchone()
            booked_count = result['count']
            
            # Если есть свободные места
            if booked_count < MAX_BOOKINGS_PER_SLOT:
                available_times.append({
                    'time': time_str,
                    'available': MAX_BOOKINGS_PER_SLOT - booked_count
                })
            
            current_time += int(interval * 60)  # Добавляем интервал в минутах
        
        conn.close()
        return available_times

    def add_booking(self, user_id, booking_date, booking_time, service, phone, car_body_type=None, wash_type=None):
        """Добавить новую запись"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO bookings (user_id, booking_date, booking_time, service, phone, car_body_type, wash_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, booking_date, booking_time, service, phone, car_body_type, wash_type))

            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False

    def get_user_bookings(self, user_id):
        """Получить все записи пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM bookings 
            WHERE user_id = ? 
            AND status = 'active'
            AND (booking_date > date('now') OR (booking_date = date('now') AND booking_time > time('now')))
            ORDER BY booking_date, booking_time
        ''', (user_id,))

        bookings = cursor.fetchall()
        conn.close()
        return bookings

    def cancel_booking(self, booking_id, user_id):
        """Отменить запись"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE bookings SET status = 'cancelled' 
            WHERE id = ? AND user_id = ?
        ''', (booking_id, user_id))

        conn.commit()
        conn.close()

    def remove_expired_bookings(self):
        """Перевести прошедшие записи в статус completed"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE bookings 
            SET status = 'completed' 
            WHERE status = 'active' 
            AND (
                booking_date < date('now') 
                OR (booking_date = date('now') AND booking_time < time('now'))
            )
        ''')
        conn.commit()
        conn.close()