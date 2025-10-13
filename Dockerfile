# Dockerfile для бота голосования
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY . .

# Создаем необходимые папки
RUN mkdir -p captcha_images exports

# Устанавливаем права доступа
RUN chmod +x run.py

# Переменные окружения
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Команда запуска
CMD ["python", "run.py"]
