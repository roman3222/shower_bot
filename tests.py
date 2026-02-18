"""
Тесты для бота автомойки
"""

import unittest
import os
from datetime import datetime, timedelta
from database import Database

class TestDatabase(unittest.TestCase):
    """Тесты для работы с БД"""
    
    def setUp(self):
        """Подготовка к тестам"""
        # Используем тестовую БД
        self.test_db_path = 'test_carwash.db'
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        
        # Переопределяем путь к БД
        import config
        config.DB_PATH = self.test_db_path
        
        self.db = Database()
    
    def tearDown(self):
        """Очистка после тестов"""
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    def test_add_user(self):
        """Тест добавления пользователя"""
        self.db.add_user(123, 'testuser', 'Test')
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (123,))
        user = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(user)
        self.assertEqual(user['username'], 'testuser')
        self.assertEqual(user['first_name'], 'Test')
    
    def test_update_phone(self):
        """Тест обновления номера телефона"""
        self.db.add_user(123, 'testuser', 'Test')
        self.db.update_user_phone(123, '+79991234567')
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT phone FROM users WHERE user_id = ?', (123,))
        result = cursor.fetchone()
        conn.close()
        
        self.assertEqual(result['phone'], '+79991234567')
    
    def test_add_booking(self):
        """Тест добавления записи"""
        tomorrow = (datetime.now().date() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        success = self.db.add_booking(
            user_id=123,
            booking_date=tomorrow,
            booking_time='10:00',
            service='Базовая мойка',
            phone='+79991234567'
        )
        
        self.assertTrue(success)
        
        # Проверяем, что запись добавлена
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM bookings WHERE user_id = ? AND booking_date = ?',
            (123, tomorrow)
        )
        booking = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(booking)
        self.assertEqual(booking['booking_time'], '10:00')
    
    def test_duplicate_booking(self):
        """Тест предотвращения дублирования записей"""
        tomorrow = (datetime.now().date() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Первая запись должна пройти
        success1 = self.db.add_booking(
            user_id=123,
            booking_date=tomorrow,
            booking_time='10:00',
            service='Базовая мойка',
            phone='+79991234567'
        )
        self.assertTrue(success1)
        
        # Вторая запись на то же время должна не пройти
        success2 = self.db.add_booking(
            user_id=456,
            booking_date=tomorrow,
            booking_time='10:00',
            service='Стандартная мойка',
            phone='+79991234568'
        )
        self.assertFalse(success2)
    
    def test_get_available_times(self):
        """Тест получения доступного времени"""
        tomorrow = (datetime.now().date() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        times = self.db.get_available_times(tomorrow)
        
        # Должно быть 10 слотов (9:00 - 19:00)
        self.assertEqual(len(times), 10)
        
        # Проверяем формат времени
        for time_slot in times:
            self.assertIn('time', time_slot)
            self.assertIn('available', time_slot)
            self.assertEqual(time_slot['available'], 3)  # Максимум 3 записи
    
    def test_get_user_bookings(self):
        """Тест получения записей пользователя"""
        tomorrow = (datetime.now().date() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Добавляем несколько записей
        self.db.add_booking(123, tomorrow, '10:00', 'Базовая мойка', '+79991234567')
        self.db.add_booking(123, tomorrow, '11:00', 'Стандартная мойка', '+79991234567')
        
        bookings = self.db.get_user_bookings(123)
        
        self.assertEqual(len(bookings), 2)
    
    def test_cancel_booking(self):
        """Тест отмены записи"""
        tomorrow = (datetime.now().date() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        self.db.add_booking(123, tomorrow, '10:00', 'Базовая мойка', '+79991234567')
        
        # Получаем ID записи
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM bookings WHERE user_id = ?', (123,))
        booking_id = cursor.fetchone()['id']
        conn.close()
        
        # Отменяем запись
        self.db.cancel_booking(booking_id, 123)
        
        # Проверяем статус
        bookings = self.db.get_user_bookings(123)
        self.assertEqual(len(bookings), 0)  # Активных записей не должно быть


class TestPhoneValidation(unittest.TestCase):
    """Тесты для валидации номера телефона"""
    
    def test_valid_phone(self):
        """Тест валидного номера"""
        from bot import CarWashBot
        
        self.assertTrue(CarWashBot.validate_phone('+79991234567'))
        self.assertTrue(CarWashBot.validate_phone('+71234567890'))
    
    def test_invalid_phone(self):
        """Тест невалидного номера"""
        from bot import CarWashBot
        
        self.assertFalse(CarWashBot.validate_phone('79991234567'))  # Без +
        self.assertFalse(CarWashBot.validate_phone('+7999123456'))   # Короткий
        self.assertFalse(CarWashBot.validate_phone('+799912345678')) # Длинный
        self.assertFalse(CarWashBot.validate_phone('abc'))           # Буквы


if __name__ == '__main__':
    unittest.main()
