# 🚀 Инструкция по развертыванию

## Локальный запуск

### 1. Подготовка окружения

```bash
# Перейдите в папку проекта
cd /home/roman/projects/showe_car

# Создайте виртуальное окружение
python3 -m venv venv

# Активируйте окружение
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3. Получение токена бота

1. Откройте Telegram
2. Найдите @BotFather
3. Отправьте `/newbot`
4. Следуйте инструкциям:
   - Введите имя бота (например: "Showe Car Bot")
   - Введите username бота (например: "showe_car_bot")
5. Скопируйте полученный токен

### 4. Конфигурация

Отредактируйте файл `.env`:

```
BOT_TOKEN=YOUR_TOKEN_HERE
```

Замените `YOUR_TOKEN_HERE` на ваш токен от BotFather.

### 5. Запуск бота

```bash
python bot.py
```

Вы должны увидеть сообщение:
```
INFO:telegram.ext._application:Application started
```

---

## Развертывание на сервере

### Вариант 1: VPS (Ubuntu/Debian)

#### 1. Подключитесь к серверу

```bash
ssh root@your_server_ip
```

#### 2. Установите Python и зависимости

```bash
apt update
apt install python3 python3-pip python3-venv git
```

#### 3. Клонируйте проект

```bash
cd /home
git clone https://github.com/your-repo/showe_car.git
cd showe_car
```

#### 4. Создайте виртуальное окружение

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 5. Настройте переменные окружения

```bash
nano .env
```

Добавьте:
```
BOT_TOKEN=YOUR_TOKEN_HERE
```

#### 6. Создайте systemd сервис

```bash
sudo nano /etc/systemd/system/showe-car-bot.service
```

Добавьте:
```ini
[Unit]
Description=Showe Car Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/showe_car
Environment="PATH=/home/showe_car/venv/bin"
ExecStart=/home/showe_car/venv/bin/python /home/showe_car/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 7. Запустите сервис

```bash
sudo systemctl daemon-reload
sudo systemctl enable showe-car-bot
sudo systemctl start showe-car-bot
```

#### 8. Проверьте статус

```bash
sudo systemctl status showe-car-bot
```

---

### Вариант 2: Docker

#### 1. Создайте Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
```

#### 2. Создайте docker-compose.yml

```yaml
version: '3.8'

services:
  bot:
    build: .
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
    volumes:
      - ./carwash_bot.db:/app/carwash_bot.db
    restart: always
```

#### 3. Запустите контейнер

```bash
docker-compose up -d
```

#### 4. Проверьте логи

```bash
docker-compose logs -f bot
```

---

### Вариант 3: Heroku

#### 1. Установите Heroku CLI

```bash
curl https://cli-assets.heroku.com/install.sh | sh
```

#### 2. Создайте Procfile

```
worker: python bot.py
```

#### 3. Создайте приложение

```bash
heroku login
heroku create your-app-name
```

#### 4. Установите переменные окружения

```bash
heroku config:set BOT_TOKEN=YOUR_TOKEN_HERE
```

#### 5. Разверните приложение

```bash
git push heroku main
```

#### 6. Запустите worker

```bash
heroku ps:scale worker=1
```

---

## Мониторинг и логирование

### Просмотр логов на сервере

```bash
# Последние 100 строк
sudo journalctl -u showe-car-bot -n 100

# В реальном времени
sudo journalctl -u showe-car-bot -f
```

### Настройка логирования в файл

Отредактируйте `bot.py`:

```python
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
```

---

## Резервное копирование БД

### Автоматическое резервное копирование

Создайте скрипт `backup.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/home/showe_car/backups"
DB_FILE="/home/showe_car/carwash_bot.db"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
cp $DB_FILE $BACKUP_DIR/carwash_bot_$DATE.db

# Удаляем старые резервные копии (старше 30 дней)
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
```

Добавьте в crontab:

```bash
crontab -e
```

Добавьте строку:

```
0 2 * * * /home/showe_car/backup.sh
```

---

## Обновление бота

### Получение обновлений

```bash
cd /home/showe_car
git pull origin main
```

### Перезагрузка сервиса

```bash
sudo systemctl restart showe-car-bot
```

---

## Решение проблем

### Бот не отвечает

1. Проверьте токен в `.env`
2. Проверьте интернет соединение
3. Проверьте логи: `sudo journalctl -u showe-car-bot -f`

### Ошибка БД

```bash
# Удалите старую БД
rm carwash_bot.db

# Перезагрузите бота
sudo systemctl restart showe-car-bot
```

### Высокое использование памяти

Перезагрузите бота:

```bash
sudo systemctl restart showe-car-bot
```

---

## Безопасность

### Защита переменных окружения

Никогда не коммитьте `.env` файл:

```bash
echo ".env" >> .gitignore
```

### Использование переменных окружения

Вместо хардкода используйте:

```python
import os
BOT_TOKEN = os.getenv('BOT_TOKEN')
```

### Ограничение доступа к БД

```bash
chmod 600 carwash_bot.db
```

---

## Масштабирование

Для большого количества пользователей рекомендуется:

1. Использовать PostgreSQL вместо SQLite
2. Добавить кэширование (Redis)
3. Использовать webhook вместо polling
4. Развернуть несколько инстансов бота

---

## Контакты и поддержка

При возникновении проблем:
1. Проверьте логи
2. Прочитайте документацию
3. Откройте issue на GitHub
