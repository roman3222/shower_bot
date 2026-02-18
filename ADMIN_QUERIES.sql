"""
SQL запросы для администратора
Используйте эти запросы для анализа данных и управления ботом
"""

# ============================================
# СТАТИСТИКА
# ============================================

# Всего пользователей
SELECT COUNT(*) as total_users FROM users;

# Всего активных записей
SELECT COUNT(*) as total_bookings FROM bookings WHERE status = 'active';

# Всего отмененных записей
SELECT COUNT(*) as cancelled_bookings FROM bookings WHERE status = 'cancelled';

# Записи на сегодня
SELECT COUNT(*) as today_bookings FROM bookings 
WHERE booking_date = DATE('now') AND status = 'active';

# Записи на завтра
SELECT COUNT(*) as tomorrow_bookings FROM bookings 
WHERE booking_date = DATE('now', '+1 day') AND status = 'active';

# Записи на неделю
SELECT COUNT(*) as week_bookings FROM bookings 
WHERE booking_date BETWEEN DATE('now') AND DATE('now', '+7 days') 
AND status = 'active';

# ============================================
# АНАЛИЗ УСЛУГ
# ============================================

# Популярность услуг
SELECT service, COUNT(*) as count 
FROM bookings 
WHERE status = 'active' 
GROUP BY service 
ORDER BY count DESC;

# Доход по услугам (если добавить цены)
SELECT 
    service,
    COUNT(*) as bookings,
    CASE 
        WHEN service = 'Базовая мойка' THEN COUNT(*) * 500
        WHEN service = 'Стандартная мойка' THEN COUNT(*) * 800
        WHEN service = 'Премиум мойка' THEN COUNT(*) * 1200
        WHEN service = 'Полная детализация' THEN COUNT(*) * 2000
    END as revenue
FROM bookings 
WHERE status = 'active' 
GROUP BY service;

# ============================================
# АНАЛИЗ ВРЕМЕНИ
# ============================================

# Загруженность по времени
SELECT booking_time, COUNT(*) as count 
FROM bookings 
WHERE status = 'active' 
GROUP BY booking_time 
ORDER BY booking_time;

# Самое популярное время
SELECT booking_time, COUNT(*) as count 
FROM bookings 
WHERE status = 'active' 
GROUP BY booking_time 
ORDER BY count DESC 
LIMIT 1;

# Самое свободное время
SELECT booking_time, COUNT(*) as count 
FROM bookings 
WHERE status = 'active' 
GROUP BY booking_time 
ORDER BY count ASC 
LIMIT 1;

# ============================================
# АНАЛИЗ ДАТ
# ============================================

# Загруженность по датам
SELECT booking_date, COUNT(*) as count 
FROM bookings 
WHERE status = 'active' 
GROUP BY booking_date 
ORDER BY booking_date;

# Самый загруженный день
SELECT booking_date, COUNT(*) as count 
FROM bookings 
WHERE status = 'active' 
GROUP BY booking_date 
ORDER BY count DESC 
LIMIT 1;

# Самый свободный день
SELECT booking_date, COUNT(*) as count 
FROM bookings 
WHERE status = 'active' 
GROUP BY booking_date 
ORDER BY count ASC 
LIMIT 1;

# ============================================
# ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЯХ
# ============================================

# Все пользователи
SELECT * FROM users ORDER BY created_at DESC;

# Пользователи с номерами телефонов
SELECT user_id, first_name, phone, created_at 
FROM users 
WHERE phone IS NOT NULL 
ORDER BY created_at DESC;

# Пользователи без номеров телефонов
SELECT user_id, first_name, created_at 
FROM users 
WHERE phone IS NULL 
ORDER BY created_at DESC;

# Самые активные пользователи
SELECT u.user_id, u.first_name, COUNT(b.id) as bookings 
FROM users u 
LEFT JOIN bookings b ON u.user_id = b.user_id AND b.status = 'active' 
GROUP BY u.user_id 
ORDER BY bookings DESC 
LIMIT 10;

# ============================================
# ИНФОРМАЦИЯ О ЗАПИСЯХ
# ============================================

# Все активные записи
SELECT * FROM bookings 
WHERE status = 'active' 
ORDER BY booking_date, booking_time;

# Все отмененные записи
SELECT * FROM bookings 
WHERE status = 'cancelled' 
ORDER BY booking_date, booking_time;

# Записи конкретного пользователя
SELECT * FROM bookings 
WHERE user_id = ? 
ORDER BY booking_date, booking_time;

# Записи с информацией о пользователе
SELECT 
    b.id,
    u.first_name,
    u.phone,
    b.service,
    b.booking_date,
    b.booking_time,
    b.status
FROM bookings b 
JOIN users u ON b.user_id = u.user_id 
WHERE b.status = 'active' 
ORDER BY b.booking_date, b.booking_time;

# ============================================
# УПРАВЛЕНИЕ ЗАПИСЯМИ
# ============================================

# Отмена записи
UPDATE bookings SET status = 'cancelled' WHERE id = ?;

# Удаление записи (осторожно!)
DELETE FROM bookings WHERE id = ?;

# Удаление всех отмененных записей
DELETE FROM bookings WHERE status = 'cancelled';

# ============================================
# ПРОВЕРКА ДОСТУПНОСТИ
# ============================================

# Проверка доступности конкретного слота
SELECT COUNT(*) as count 
FROM bookings 
WHERE booking_date = '2024-01-15' 
AND booking_time = '10:00' 
AND status = 'active';

# Все занятые слоты на дату
SELECT booking_time, COUNT(*) as count 
FROM bookings 
WHERE booking_date = '2024-01-15' 
AND status = 'active' 
GROUP BY booking_time;

# Все свободные слоты на дату
SELECT 
    CASE 
        WHEN booking_time IS NULL THEN '09:00'
        WHEN booking_time = '09:00' THEN '10:00'
        WHEN booking_time = '10:00' THEN '11:00'
        -- ... и так далее
    END as free_time
FROM (
    SELECT DISTINCT booking_time FROM bookings 
    WHERE booking_date = '2024-01-15'
) 
WHERE booking_time NOT IN (
    SELECT booking_time FROM bookings 
    WHERE booking_date = '2024-01-15' AND status = 'active'
);

# ============================================
# ОТЧЕТЫ
# ============================================

# Дневной отчет
SELECT 
    DATE('now') as date,
    COUNT(*) as total_bookings,
    COUNT(DISTINCT user_id) as unique_users,
    GROUP_CONCAT(DISTINCT service) as services
FROM bookings 
WHERE booking_date = DATE('now') AND status = 'active';

# Недельный отчет
SELECT 
    strftime('%Y-%W', booking_date) as week,
    COUNT(*) as total_bookings,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(DISTINCT service) as unique_services
FROM bookings 
WHERE status = 'active' 
GROUP BY week 
ORDER BY week DESC;

# Месячный отчет
SELECT 
    strftime('%Y-%m', booking_date) as month,
    COUNT(*) as total_bookings,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(DISTINCT service) as unique_services
FROM bookings 
WHERE status = 'active' 
GROUP BY month 
ORDER BY month DESC;

# ============================================
# ЭКСПОРТ ДАННЫХ
# ============================================

# Экспорт всех записей в CSV
.mode csv
.output bookings.csv
SELECT 
    b.id,
    u.first_name,
    u.phone,
    b.service,
    b.booking_date,
    b.booking_time,
    b.status,
    b.created_at
FROM bookings b 
JOIN users u ON b.user_id = u.user_id 
ORDER BY b.booking_date, b.booking_time;
.output stdout

# ============================================
# ��ЧИСТКА ДАННЫХ
# ============================================

# Удаление старых отмененных записей (старше 30 дней)
DELETE FROM bookings 
WHERE status = 'cancelled' 
AND created_at < datetime('now', '-30 days');

# Удаление записей в прошлом
DELETE FROM bookings 
WHERE booking_date < DATE('now') 
AND status = 'active';

# ============================================
# ОПТИМИЗАЦИЯ БД
# ============================================

# Проверка целостности БД
PRAGMA integrity_check;

# Оптимизация БД
VACUUM;

# Анализ производительности
ANALYZE;

# ============================================
# ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ В PYTHON
# ============================================

"""
from database import Database

db = Database()
conn = db.get_connection()
cursor = conn.cursor()

# Пример 1: Получить все записи на сегодня
cursor.execute('''
    SELECT * FROM bookings 
    WHERE booking_date = DATE('now') AND status = 'active'
''')
today_bookings = cursor.fetchall()

# Пример 2: Получить статистику
cursor.execute('''
    SELECT service, COUNT(*) as count 
    FROM bookings 
    WHERE status = 'active' 
    GROUP BY service
''')
stats = cursor.fetchall()

# Пример 3: Получить популярность услуг
cursor.execute('''
    SELECT service, COUNT(*) as count 
    FROM bookings 
    WHERE status = 'active' 
    GROUP BY service 
    ORDER BY count DESC
''')
popular_services = cursor.fetchall()

conn.close()
"""
