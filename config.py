import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

# Admin User ID для получения уведомлений
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', '0'))

# Database settings
DB_PATH = 'carwash_bot.db'

# Время работы автомойки (в часах)
WORKING_HOURS = {
    'start': 9,      # 9:00
    'end': 19,       # 19:00
    'interval': 1.5  # интервал 1 час 30 минут
}

# Количество дней вперед, на которые можно записаться
DAYS_AHEAD = 7

# Максимальное количество записей на один слот времени
MAX_BOOKINGS_PER_SLOT = 2

# Типы кузова
CAR_BODY_TYPES = {
    'sedan': 'Седан',
    'suv': 'Внедорожник (SUV)',
    'hatchback': 'Хэтчбек',
    'van': 'Минивэн',
    'truck': 'Грузовик'
}

# Типы мойки
WASH_TYPES = {
    'single': 'Однофазная мойка',
    'double': 'Двухфазная мойка'
}
