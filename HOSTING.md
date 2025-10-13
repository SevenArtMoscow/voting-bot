# 🚀 РУКОВОДСТВО ПО ХОСТИНГУ БОТА

## 📋 Варианты хостинга

### 1. 🐳 Docker (Рекомендуется)

```bash
# Клонируйте проект
git clone <your-repo>
cd vote-bot

# Настройте переменные окружения
cp env.production .env
# Отредактируйте .env файл

# Запустите через Docker Compose
docker-compose up -d
```

### 2. 🖥️ VPS/Сервер

```bash
# Установите Python 3.11+
sudo apt update
sudo apt install python3.11 python3.11-pip

# Клонируйте проект
git clone <your-repo>
cd vote-bot

# Запустите скрипт развертывания
chmod +x deploy.sh
./deploy.sh
```

### 3. ☁️ Облачные платформы

#### Heroku:
```bash
# Установите Heroku CLI
# Создайте Procfile:
echo "worker: python run.py" > Procfile

# Разверните
git push heroku main
```

#### Railway:
```bash
# Подключите GitHub репозиторий
# Установите переменные окружения в панели
# Автоматическое развертывание
```

#### Render:
```bash
# Создайте Web Service
# Укажите команду: python run.py
# Установите переменные окружения
```

## ⚙️ Переменные окружения

Создайте файл `.env` со следующими переменными:

```env
BOT_TOKEN=ваш_токен_бота
ADMIN_IDS=802373523,665509323
DATABASE_PATH=data/voting_bot.db
VOTING_ACTIVE=true
```

## 📁 Структура проекта

```
vote-bot/
├── bot.py              # Основной файл бота
├── config.py           # Конфигурация
├── database.py         # База данных
├── captcha.py          # CAPTCHA
├── run.py              # Скрипт запуска
├── requirements.txt    # Зависимости
├── Dockerfile          # Docker образ
├── docker-compose.yml  # Docker Compose
├── deploy.sh           # Скрипт развертывания
├── env.production      # Пример переменных
├── data/               # Папка для данных
├── logs/               # Папка для логов
├── captcha_images/     # Временные CAPTCHA
└── exports/            # Экспорт данных
```

## 🔧 Настройка

### 1. Получите токен бота:
- Напишите @BotFather в Telegram
- Создайте нового бота командой `/newbot`
- Скопируйте токен

### 2. Узнайте ID администраторов:
- Напишите боту @userinfobot
- Скопируйте ваш ID

### 3. Настройте переменные:
- Отредактируйте `.env` файл
- Укажите токен и ID администраторов

## 🚀 Запуск

### Локально:
```bash
python run.py
```

### Docker:
```bash
docker-compose up -d
```

### Системный сервис (Linux):
```bash
# Создайте systemd сервис
sudo nano /etc/systemd/system/voting-bot.service

[Unit]
Description=Voting Bot
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/vote-bot
ExecStart=/usr/bin/python3 run.py
Restart=always

[Install]
WantedBy=multi-user.target

# Запустите сервис
sudo systemctl enable voting-bot
sudo systemctl start voting-bot
```

## 📊 Мониторинг

### Логи:
```bash
# Просмотр логов
tail -f bot.log

# Docker логи
docker-compose logs -f
```

### Статус:
```bash
# Проверка статуса
ps aux | grep python

# Docker статус
docker-compose ps
```

## 🔒 Безопасность

1. **Никогда не коммитьте `.env` файл**
2. **Используйте сильные пароли**
3. **Регулярно обновляйте зависимости**
4. **Настройте файрвол**
5. **Используйте HTTPS для веб-интерфейса**

## 🆘 Поддержка

При возникновении проблем:
1. Проверьте логи: `tail -f bot.log`
2. Убедитесь в правильности токена
3. Проверьте переменные окружения
4. Убедитесь в доступности интернета

## 📈 Масштабирование

Для высоких нагрузок:
- Используйте Redis для кеширования
- Настройте балансировщик нагрузки
- Используйте несколько экземпляров бота
- Настройте мониторинг (Prometheus + Grafana)
