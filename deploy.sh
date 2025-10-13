#!/bin/bash
# Скрипт развертывания бота

echo "🚀 Развертывание бота для голосования..."

# Создаем необходимые папки
mkdir -p data logs captcha_images exports

# Устанавливаем права доступа
chmod +x run.py
chmod +x deploy.sh

# Проверяем наличие .env файла
if [ ! -f .env ]; then
    echo "⚠️ Файл .env не найден. Копируем из env.production..."
    cp env.production .env
    echo "📝 Отредактируйте файл .env с вашими настройками!"
fi

# Устанавливаем зависимости
echo "📦 Установка зависимостей..."
pip install -r requirements.txt

# Запускаем бота
echo "🤖 Запуск бота..."
python run.py
