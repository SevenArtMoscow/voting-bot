#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт запуска бота для голосования
Используйте этот файл для запуска на хостинге
"""

import os
import sys
import logging
from bot import main

# Настройка логирования для продакшена
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Проверяем переменные окружения
if not os.getenv('BOT_TOKEN'):
    print("❌ Ошибка: Не установлена переменная окружения BOT_TOKEN")
    sys.exit(1)

if __name__ == '__main__':
    print("🚀 Запуск бота для голосования...")
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️ Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)
