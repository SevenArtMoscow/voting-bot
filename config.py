# Конфигурация бота для голосования
import os

# Токен бота (из переменной окружения или по умолчанию)
BOT_TOKEN = os.getenv('BOT_TOKEN', '8330496751:AAFL26am8DeZrpNoJNPaehQIuP-sYyE-QN0')

# ID администраторов (из переменной окружения или по умолчанию)
admin_ids_str = os.getenv('ADMIN_IDS', '802373523,665509323')
ADMIN_IDS = [int(id.strip()) for id in admin_ids_str.split(',')]

# Настройки базы данных
DATABASE_PATH = os.getenv('DATABASE_PATH', 'voting_bot.db')

# Кандидаты для голосования
CANDIDATES = [
    {"id": 1, "name": "Петров Матвей Владимирович", "emoji": "👨‍💼"},
    {"id": 2, "name": "Пупликов Валентин Александрович", "emoji": "👔"},
    {"id": 3, "name": "Мамедова Дарина Руслановна", "emoji": "👩‍💼"},
    {"id": 4, "name": "Против всех", "emoji": "🚫"}
]

# Настройки голосования (ручной режим)
VOTING_ACTIVE = True  # Админ может включать/выключать голосование вручную

# Настройки CAPTCHA
CAPTCHA_LENGTH = 4
CAPTCHA_WIDTH = 200
CAPTCHA_HEIGHT = 100

# Папки для файлов
CAPTCHA_FOLDER = "captcha_images"
EXPORT_FOLDER = "exports"

# Создание папок если их нет
os.makedirs(CAPTCHA_FOLDER, exist_ok=True)
os.makedirs(EXPORT_FOLDER, exist_ok=True)
