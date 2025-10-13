# Модуль для работы с базой данных SQLite
import sqlite3
import datetime
from config import DATABASE_PATH

class Database:
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных и создание таблиц"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                course INTEGER NOT NULL,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                has_voted BOOLEAN DEFAULT FALSE,
                vote_timestamp TIMESTAMP
            )
        ''')
        
        # Создаем индексы для быстрого поиска
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_has_voted ON users(has_voted)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_full_name ON users(full_name)')
        
        # Таблица голосов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                candidate_id INTEGER NOT NULL,
                vote_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (telegram_id)
            )
        ''')
        
        # Создаем индексы для голосов
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_votes_user_id ON votes(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_votes_candidate_id ON votes(candidate_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_votes_timestamp ON votes(vote_timestamp)')
        
        # Таблица результатов (для накрутки голосов)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id INTEGER UNIQUE NOT NULL,
                real_votes INTEGER DEFAULT 0,
                fake_votes INTEGER DEFAULT 0,
                total_votes INTEGER DEFAULT 0
            )
        ''')
        
        # Таблица сессий CAPTCHA
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS captcha_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                captcha_code TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_used BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # Таблица настроек
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Инициализация результатов для кандидатов
        for candidate_id in range(1, 5):
            cursor.execute('''
                INSERT OR IGNORE INTO results (candidate_id, real_votes, fake_votes, total_votes)
                VALUES (?, 0, 0, 0)
            ''', (candidate_id,))
        
        conn.commit()
        conn.close()
        
        # Очищаем дублирующиеся записи в results
        self.cleanup_duplicate_results()
    
    def cleanup_duplicate_results(self):
        """Очистка дублирующихся записей в таблице results"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Удаляем дублирующиеся записи, оставляя только одну для каждого candidate_id
        cursor.execute('''
            DELETE FROM results 
            WHERE id NOT IN (
                SELECT MIN(id) 
                FROM results 
                GROUP BY candidate_id
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_user(self, telegram_id, full_name, course):
        """Добавление нового пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Проверяем, не существует ли уже пользователь с таким telegram_id
            cursor.execute('SELECT telegram_id FROM users WHERE telegram_id = ?', (telegram_id,))
            if cursor.fetchone():
                conn.close()
                return "telegram_id_exists"  # Пользователь с таким ID уже существует
            
            # Проверяем, не существует ли уже пользователь с таким ФИО
            cursor.execute('SELECT full_name FROM users WHERE full_name = ?', (full_name,))
            if cursor.fetchone():
                conn.close()
                return "name_exists"  # Пользователь с таким ФИО уже существует
            
            # Если все проверки пройдены, добавляем пользователя
            cursor.execute('''
                INSERT INTO users (telegram_id, full_name, course)
                VALUES (?, ?, ?)
            ''', (telegram_id, full_name, course))
            conn.commit()
            conn.close()
            return "success"  # Успешно добавлен
            
        except Exception as e:
            conn.close()
            return f"error: {str(e)}"  # Ошибка базы данных
    
    def get_user(self, telegram_id):
        """Получение информации о пользователе"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT telegram_id, full_name, course, has_voted, vote_timestamp
            FROM users WHERE telegram_id = ?
        ''', (telegram_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'telegram_id': result[0],
                'full_name': result[1],
                'course': result[2],
                'has_voted': bool(result[3]),
                'vote_timestamp': result[4]
            }
        return None
    
    def add_vote(self, telegram_id, candidate_id):
        """Добавление голоса"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Добавляем голос
            cursor.execute('''
                INSERT INTO votes (user_id, candidate_id)
                VALUES (?, ?)
            ''', (telegram_id, candidate_id))
            
            # Обновляем статус пользователя
            cursor.execute('''
                UPDATE users SET has_voted = TRUE, vote_timestamp = CURRENT_TIMESTAMP
                WHERE telegram_id = ?
            ''', (telegram_id,))
            
            # Обновляем результаты
            cursor.execute('''
                UPDATE results SET 
                    real_votes = real_votes + 1, 
                    total_votes = real_votes + fake_votes + 1
                WHERE candidate_id = ?
            ''', (candidate_id,))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_voting_stats(self):
        """Получение статистики голосования"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Общее количество пользователей
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        # Количество проголосовавших
        cursor.execute('SELECT COUNT(*) FROM users WHERE has_voted = TRUE')
        voted_users = cursor.fetchone()[0]
        
        # Результаты по кандидатам
        cursor.execute('''
            SELECT candidate_id, total_votes FROM results
            ORDER BY total_votes DESC
        ''')
        results = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_users': total_users,
            'voted_users': voted_users,
            'not_voted': total_users - voted_users,
            'activity_percent': (voted_users / total_users * 100) if total_users > 0 else 0,
            'results': results
        }
    
    def get_all_users(self):
        """Получение списка всех пользователей"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT telegram_id, full_name, course, has_voted, vote_timestamp
            FROM users ORDER BY registered_at DESC
        ''')
        
        users = cursor.fetchall()
        conn.close()
        
        return [{
            'telegram_id': user[0],
            'full_name': user[1],
            'course': user[2],
            'has_voted': bool(user[3]),
            'vote_timestamp': user[4]
        } for user in users]
    
    def get_all_votes(self):
        """Получение всех голосов с деталями"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.full_name, u.course, u.telegram_id, v.vote_timestamp, v.candidate_id
            FROM votes v
            JOIN users u ON v.user_id = u.telegram_id
            ORDER BY v.vote_timestamp DESC
        ''')
        
        votes = cursor.fetchall()
        conn.close()
        
        return [{
            'full_name': vote[0],
            'course': vote[1],
            'telegram_id': vote[2],
            'vote_timestamp': vote[3],
            'candidate_id': vote[4]
        } for vote in votes]
    
    def add_fake_votes(self, candidate_id, count):
        """Добавление накрученных голосов"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE results SET 
                fake_votes = fake_votes + ?, 
                total_votes = real_votes + fake_votes + ?
            WHERE candidate_id = ?
        ''', (count, count, candidate_id))
        
        conn.commit()
        conn.close()
        return True
    
    def remove_fake_votes(self, candidate_id, count):
        """Удаление накрученных голосов"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE results SET 
                fake_votes = MAX(0, fake_votes - ?),
                total_votes = real_votes + MAX(0, fake_votes - ?)
            WHERE candidate_id = ?
        ''', (count, count, candidate_id))
        
        conn.commit()
        conn.close()
        return True
    
    def save_captcha_session(self, telegram_id, captcha_code):
        """Сохранение сессии CAPTCHA"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO captcha_sessions (telegram_id, captcha_code)
            VALUES (?, ?)
        ''', (telegram_id, captcha_code))
        
        conn.commit()
        conn.close()
    
    def verify_captcha(self, telegram_id, user_input):
        """Проверка CAPTCHA"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT captcha_code FROM captcha_sessions
            WHERE telegram_id = ? AND is_used = FALSE
            ORDER BY created_at DESC LIMIT 1
        ''', (telegram_id,))
        
        result = cursor.fetchone()
        
        if result and result[0] == user_input:
            # Помечаем CAPTCHA как использованную
            cursor.execute('''
                UPDATE captcha_sessions SET is_used = TRUE
                WHERE telegram_id = ? AND captcha_code = ?
            ''', (telegram_id, user_input))
            conn.commit()
            conn.close()
            return True
        
        conn.close()
        return False
    
    def export_to_csv(self):
        """Экспорт данных в CSV"""
        import csv
        from datetime import datetime
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Экспорт пользователей
        cursor.execute('''
            SELECT telegram_id, full_name, course, has_voted, vote_timestamp, registered_at
            FROM users ORDER BY registered_at
        ''')
        users = cursor.fetchall()
        
        # Экспорт голосов
        cursor.execute('''
            SELECT u.full_name, u.course, u.telegram_id, v.candidate_id, v.vote_timestamp
            FROM votes v
            JOIN users u ON v.user_id = u.telegram_id
            ORDER BY v.vote_timestamp
        ''')
        votes = cursor.fetchall()
        
        # Экспорт результатов
        cursor.execute('''
            SELECT candidate_id, real_votes, fake_votes, total_votes
            FROM results ORDER BY candidate_id
        ''')
        results = cursor.fetchall()
        
        conn.close()
        
        # Создание CSV файла
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"exports/voting_export_{timestamp}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Заголовок
            writer.writerow(['ЭКСПОРТ ДАННЫХ ГОЛОСОВАНИЯ'])
            writer.writerow([f'Дата экспорта: {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}'])
            writer.writerow([])
            
            # Пользователи
            writer.writerow(['ПОЛЬЗОВАТЕЛИ'])
            writer.writerow(['ID', 'ФИО', 'Курс', 'Проголосовал', 'Время голоса', 'Дата регистрации'])
            for user in users:
                writer.writerow(user)
            
            writer.writerow([])
            
            # Голоса
            writer.writerow(['ГОЛОСА'])
            writer.writerow(['ФИО', 'Курс', 'Telegram ID', 'Кандидат', 'Время голоса'])
            for vote in votes:
                writer.writerow(vote)
            
            writer.writerow([])
            
            # Результаты
            writer.writerow(['РЕЗУЛЬТАТЫ'])
            writer.writerow(['Кандидат', 'Реальные голоса', 'Накрученные голоса', 'Всего голосов'])
            for result in results:
                writer.writerow(result)
        
        return filename
    
    def check_duplicate_users(self):
        """Проверка дублирующихся пользователей"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Проверяем дублирующиеся ФИО
        cursor.execute('''
            SELECT full_name, COUNT(*) as count
            FROM users 
            GROUP BY full_name 
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        ''')
        duplicate_names = cursor.fetchall()
        
        # Проверяем дублирующиеся telegram_id
        cursor.execute('''
            SELECT telegram_id, COUNT(*) as count
            FROM users 
            GROUP BY telegram_id 
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        ''')
        duplicate_ids = cursor.fetchall()
        
        conn.close()
        
        return {
            'duplicate_names': duplicate_names,
            'duplicate_ids': duplicate_ids
        }
