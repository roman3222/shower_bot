"""
Примеры использования функций бота и БД
"""

from database import Database
from datetime import datetime, timedelta

# Инициализируем БД
db = Database()

# ============================================
# ПРИМЕРЫ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ
# ============================================

def example_add_user():
    """Пример добавления пользователя"""
    db.add_user(
        user_id=123456789,
        username='john_doe',
        first_name='John'
    )
    print("✅ Пользователь добавлен")


def example_update_phone():
    """Пример обновления номера телефона"""
    db.update_user_phone(
        user_id=123456789,
        phone='+79991234567'
    )
    print("✅ Номер телефона обновлен")


# ============================================
# ПРИМЕРЫ РАБОТЫ С ДАТАМИ И ВРЕМЕНЕМ
# ============================================

def example_get_available_dates():
    """Пример получения доступных дат"""
    dates = db.get_available_dates()
    print(f"📅 Доступные даты ({len(dates)} шт):")
    for date in dates:
        print(f"  - {date.strftime('%d.%m.%Y (%A)')}")


def example_get_available_times():
    """Пример получения доступного времени"""
    date_str = (datetime.now().date() + timedelta(days=1)).strftime('%Y-%m-%d')
    times = db.get_available_times(date_str)
    print(f"⏰ Доступное время на {date_str}:")
    for time_slot in times:
        print(f"  - {time_slot['time']} ({time_slot['available']} мест)")


# ============================================
# ПРИМЕРЫ РАБОТЫ С ЗАПИСЯМИ
# ============================================

def example_add_booking():
    """Пример добавления записи"""
    tomorrow = (datetime.now().date() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    success = db.add_booking(
        user_id=123456789,
        booking_date=tomorrow,
        booking_time='10:00',
        service='Стандартная мойка',
        phone='+79991234567'
    )
    
    if success:
        print("✅ Запись добавлена")
    else:
        print("❌ Ошибка: время уже занято")


def example_get_user_bookings():
    """Пр��мер получения записей пользователя"""
    bookings = db.get_user_bookings(user_id=123456789)
    print(f"📋 Записи пользователя ({len(bookings)} шт):")
    for booking in bookings:
        print(f"  - {booking['booking_date']} {booking['booking_time']}: {booking['service']}")


def example_cancel_booking():
    """Пример отмены записи"""
    db.cancel_booking(booking_id=1, user_id=123456789)
    print("✅ Запись отменена")


# ============================================
# ПРИМЕРЫ СТАТИСТИКИ
# ============================================

def example_get_statistics():
    """Пример получения статистики"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Всего записей
    cursor.execute('SELECT COUNT(*) as count FROM bookings WHERE status = "active"')
    total_bookings = cursor.fetchone()['count']
    
    # Всего пользователей
    cursor.execute('SELECT COUNT(*) as count FROM users')
    total_users = cursor.fetchone()['count']
    
    # Записи на сегодня
    today = datetime.now().date().strftime('%Y-%m-%d')
    cursor.execute(
        'SELECT COUNT(*) as count FROM bookings WHERE booking_date = ? AND status = "active"',
        (today,)
    )
    today_bookings = cursor.fetchone()['count']
    
    conn.close()
    
    print("📊 Статистика:")
    print(f"  - Всего пользователей: {total_users}")
    print(f"  - Всего активных записей: {total_bookings}")
    print(f"  - Записей на сегодня: {today_bookings}")


if __name__ == '__main__':
    print("🚗 Примеры использования бота для автомойки\n")
    
    # Раскомментируйте нужные примеры для тестирования
    
    # example_add_user()
    # example_update_phone()
    # example_get_available_dates()
    # example_get_available_times()
    # example_add_booking()
    # example_get_user_bookings()
    # example_cancel_booking()
    # example_get_statistics()
