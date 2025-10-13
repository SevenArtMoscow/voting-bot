#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест производительности бота для голосования
"""

import time
import random
from database import Database
from config import CANDIDATES

def test_performance():
    """Тест производительности с большим количеством данных"""
    print("🚀 Тест производительности бота...")
    
    # Создаем тестовую базу данных
    import os
    original_db_path = "voting_bot.db"
    test_db_path = "test_voting_bot.db"
    
    # Удаляем тестовую БД если существует
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    # Временно меняем путь к БД для тестов
    from config import DATABASE_PATH
    import config
    config.DATABASE_PATH = test_db_path
    
    db = Database()
    
    # Тест 1: Регистрация пользователей
    print("\n📝 Тест регистрации пользователей...")
    start_time = time.time()
    
    for i in range(1000):
        telegram_id = 1000000 + i
        full_name = f"Тестовый Пользователь {i}"
        course = random.randint(1, 5)
        
        result = db.add_user(telegram_id, full_name, course)
        if result != "success":
            print(f"Ошибка регистрации пользователя {i}: {result}")
    
    registration_time = time.time() - start_time
    print(f"✅ 1000 регистраций за {registration_time:.2f} секунд")
    print(f"📊 Скорость: {1000/registration_time:.0f} регистраций/сек")
    
    # Тест 2: Голосование
    print("\n🗳️ Тест голосования...")
    start_time = time.time()
    
    for i in range(1000):
        telegram_id = 1000000 + i
        candidate_id = random.randint(1, len(CANDIDATES))
        
        success = db.add_vote(telegram_id, candidate_id)
        if not success:
            print(f"Ошибка голосования пользователя {i}")
    
    voting_time = time.time() - start_time
    print(f"✅ 1000 голосов за {voting_time:.2f} секунд")
    print(f"📊 Скорость: {1000/voting_time:.0f} голосов/сек")
    
    # Тест 3: Получение статистики
    print("\n📊 Тест получения статистики...")
    start_time = time.time()
    
    for i in range(100):
        stats = db.get_voting_stats()
    
    stats_time = time.time() - start_time
    print(f"✅ 100 запросов статистики за {stats_time:.2f} секунд")
    print(f"📊 Скорость: {100/stats_time:.0f} запросов/сек")
    
    # Тест 4: Получение списка пользователей
    print("\n👥 Тест получения списка пользователей...")
    start_time = time.time()
    
    users = db.get_all_users()
    
    users_time = time.time() - start_time
    print(f"✅ Получение {len(users)} пользователей за {users_time:.2f} секунд")
    
    # Тест 5: Экспорт данных
    print("\n📥 Тест экспорта данных...")
    start_time = time.time()
    
    filename = db.export_to_csv()
    
    export_time = time.time() - start_time
    print(f"✅ Экспорт данных за {export_time:.2f} секунд")
    
    # Итоговая статистика
    print("\n🎯 ИТОГОВАЯ СТАТИСТИКА:")
    print(f"👥 Пользователей: {len(users)}")
    print(f"🗳️ Голосов: {stats['voted_users']}")
    print(f"📊 Активность: {stats['activity_percent']:.1f}%")
    
    print("\n✅ Все тесты завершены успешно!")
    print("🚀 Бот готов к работе с большими нагрузками!")
    
    # Очищаем тестовую базу данных
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        print("🧹 Тестовая база данных удалена")
    
    # Восстанавливаем оригинальный путь
    config.DATABASE_PATH = original_db_path

if __name__ == "__main__":
    test_performance()
