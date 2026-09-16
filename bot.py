# Основной файл бота для голосования
import logging
import os
import sys
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

import config
from config import BOT_TOKEN, ADMIN_IDS, CANDIDATES, VOTING_ACTIVE, SITE_URL
from database import Database
from captcha import CaptchaGenerator
from web_server import start_web_server

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация
db = Database()
captcha_gen = CaptchaGenerator()

# Состояния пользователей
user_states = {}

class UserState:
    REGISTRATION_NAME = "registration_name"
    REGISTRATION_COURSE = "registration_course"
    REGISTRATION_CAPTCHA = "registration_captcha"
    VOTING = "voting"
    ADMIN_ADD_VOTES = "admin_add_votes"
    ADMIN_REMOVE_VOTES = "admin_remove_votes"
    ADMIN_ANNOUNCE = "admin_announce"

BTN_VOTE = "🗳️ Голосование"
BTN_STATS = "📊 Статистика"
BTN_ADMIN = "👑 Админ-панель"
BTN_HELP = "ℹ️ Помощь"
BTN_SITE = "📖 Ознакомление"

BUSY_STATES = {
    UserState.REGISTRATION_NAME,
    UserState.REGISTRATION_COURSE,
    UserState.REGISTRATION_CAPTCHA,
    UserState.ADMIN_ADD_VOTES,
    UserState.ADMIN_REMOVE_VOTES,
}


def is_admin(user_id):
    """Проверка прав администратора"""
    return user_id in ADMIN_IDS


def main_keyboard(user_id):
    """Постоянная клавиатура внизу экрана"""
    if is_admin(user_id):
        rows = [
            [BTN_VOTE, BTN_STATS],
            [BTN_SITE, BTN_ADMIN],
            [BTN_HELP],
        ]
    else:
        rows = [
            [BTN_VOTE, BTN_SITE],
            [BTN_HELP],
        ]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def site_link_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Ознакомление", url=SITE_URL)],
        [InlineKeyboardButton("Голосование", callback_data="open_vote")],
    ])


def admin_inline_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton("🗳️ Голоса", callback_data="admin_votes")],
        [InlineKeyboardButton("➕ Накрутить голоса", callback_data="admin_add_votes")],
        [InlineKeyboardButton("➖ Отнять голоса", callback_data="admin_remove_votes")],
        [InlineKeyboardButton("🏆 Объявить победителя", callback_data="admin_announce")],
        [InlineKeyboardButton("📥 Экспорт данных", callback_data="admin_export")],
        [InlineKeyboardButton("🔄 Сброс голосования", callback_data="admin_reset")],
        [InlineKeyboardButton("🧹 Очистить дубли", callback_data="admin_cleanup")],
        [InlineKeyboardButton("🔍 Проверить дубли", callback_data="admin_check_duplicates")],
        [InlineKeyboardButton("⏸️ Остановить голосование", callback_data="admin_stop_voting")],
        [InlineKeyboardButton("▶️ Запустить голосование", callback_data="admin_start_voting")],
    ])


def get_reply_target(update: Update):
    if update.message:
        return update.message
    if update.callback_query and update.callback_query.message:
        return update.callback_query.message
    return None


def voting_status_text():
    status = "🟢 урна открыта" if config.VOTING_ACTIVE else "🔴 урна закрыта"
    stats = db.get_voting_stats()
    return (
        f"🗳️ Система голосования\n\n"
        f"Статус: {status}\n"
        f"Кандидатов: {len(CANDIDATES)}\n"
        f"Всего голосов: {stats['voted_users']}"
    )

def get_candidate_name(candidate_id):
    """Получение имени кандидата по ID"""
    for candidate in CANDIDATES:
        if candidate["id"] == candidate_id:
            return f"{candidate['emoji']} {candidate['name']}"
    return "Неизвестный кандидат"

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Логирование ошибок обработчиков"""
    logger.error("Ошибка при обработке обновления: %s", context.error, exc_info=context.error)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user_id = update.effective_user.id
    logger.info("/start от пользователя %s", user_id)
    user = db.get_user(user_id)

    if not user and not is_admin(user_id):
        user_states[user_id] = UserState.REGISTRATION_NAME
        await update.message.reply_text(
            "👋 Добро пожаловать в систему голосования!\n\n"
            "Для участия в голосовании необходимо пройти регистрацию.\n\n"
            "📝 Введите ваше ФИО (например: Иванов Иван Иванович):"
        )
        return

    user_states.pop(user_id, None)
    await update.message.reply_text(
        voting_status_text() + f"\n\n📖 Ознакомление:\n{SITE_URL}",
        reply_markup=main_keyboard(user_id)
    )
    await update.message.reply_text(
        "Ознакомление — сайт кандидатов. Голосование — только в этом боте.",
        reply_markup=site_link_keyboard()
    )

    if is_admin(user_id):
        await update.message.reply_text(
            "👑 АДМИН ПАНЕЛЬ\n\nВыберите действие:",
            reply_markup=admin_inline_keyboard()
        )

    if user:
        await show_voting_menu(update, context)

async def myid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /myid"""
    user_id = update.effective_user.id
    await update.message.reply_text(f"🆔 Ваш Telegram ID: `{user_id}`", parse_mode=ParseMode.MARKDOWN)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    user_id = update.effective_user.id
    
    if is_admin(user_id):
        # Помощь для администратора
        help_text = """
👑 АДМИН ПАНЕЛЬ

Доступные команды:

📊 /stats - Полная статистика
👥 /users - Список пользователей
🗳️ /votes - Детальные голоса
➕ /addvotes - Накрутить голоса
➖ /removevotes - Отнять голоса
🏆 /announce - Объявить победителя
📥 /export - Экспорт данных
🔄 /reset - Сброс голосования
ℹ️ /help - Помощь

Используйте команды для управления системой голосования.
        """
    else:
        # Помощь для обычных пользователей
        help_text = f"""
📚 ПОМОЩЬ

Доступные команды:

/start - Начать работу / Регистрация
/myid - Узнать свой Telegram ID
/help - Показать эту справку

Сайт для ознакомления: {SITE_URL}
Голосование принимается только в Telegram.
        """
    
    await update.message.reply_text(help_text)

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /admin"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет доступа к этой команде.")
        return
    
    await update.message.reply_text(
        "👑 АДМИН ПАНЕЛЬ\n\n"
        "Выберите действие:",
        reply_markup=admin_inline_keyboard()
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /stats"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет доступа к этой команде.")
        return
    
    await show_stats(update, context)

async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /users"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет доступа к этой команде.")
        return
    
    await show_users(update, context)

async def votes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /votes"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет доступа к этой команде.")
        return
    
    await show_votes(update, context)

async def addvotes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /addvotes"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет доступа к этой команде.")
        return
    
    await show_candidate_selection(update, context, "add")

async def removevotes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /removevotes"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет доступа к этой команде.")
        return
    
    await show_candidate_selection(update, context, "remove")

async def announce_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /announce"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет доступа к этой команде.")
        return
    
    await show_announce_menu(update, context)

async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /export"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет доступа к этой команде.")
        return
    
    await export_data(update, context)

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /reset"""
    user_id = update.effective_user.id
    message = get_reply_target(update)
    if not message:
        return
    
    if not is_admin(user_id):
        await message.reply_text("❌ У вас нет доступа к этой команде.")
        return
    
    keyboard = [
        [InlineKeyboardButton("✅ Да, сбросить", callback_data="reset_confirm")],
        [InlineKeyboardButton("❌ Отмена", callback_data="reset_cancel")]
    ]
    
    await message.reply_text(
        "⚠️ ВНИМАНИЕ!\n\n"
        "Вы собираетесь сбросить все данные голосования.\n"
        "Это действие нельзя отменить!\n\n"
        "Продолжить?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_voting_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показ меню голосования"""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    message = update.message or (update.callback_query.message if update.callback_query else None)
    if not message:
        return
    
    if not user:
        await message.reply_text("❌ Сначала пройдите регистрацию командой /start")
        return
    
    if user['has_voted'] and not is_admin(user_id):
        await message.reply_text(
            "✅ Вы уже проголосовали!\nВаш голос учтен.",
            reply_markup=main_keyboard(user_id)
        )
        return
    
    if not config.VOTING_ACTIVE:
        await message.reply_text("❌ Голосование приостановлено администратором.")
        return
    
    keyboard = []
    for candidate in CANDIDATES:
        keyboard.append([InlineKeyboardButton(
            f"{candidate['emoji']} {candidate['name']}",
            callback_data=f"vote_{candidate['id']}"
        )])
    
    await message.reply_text(
        f"🗳️ ГОЛОСОВАНИЕ\n\n"
        f"Привет, {user['full_name']}!\n\n"
        f"Выберите кандидата:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показ статистики"""
    import sqlite3
    
    # Определяем, откуда вызвана функция
    if update.message:
        message = update.message
    elif update.callback_query:
        message = update.callback_query.message
        await update.callback_query.answer()
    else:
        return
    
    stats = db.get_voting_stats()
    
    text = "📊 ПОЛНАЯ СТАТИСТИКА\n\n"
    text += "👥 Пользователи:\n"
    text += f"• Всего зарегистрировано: {stats['total_users']}\n"
    text += f"• Проголосовали: {stats['voted_users']}\n"
    text += f"• Не голосовали: {stats['not_voted']}\n\n"
    
    text += "🗳️ Результаты голосования:\n"
    
    # Получаем детальную статистику
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT candidate_id, real_votes, fake_votes, total_votes 
        FROM results ORDER BY total_votes DESC
    ''')
    results = cursor.fetchall()
    conn.close()
    
    total_all_votes = sum(result[3] for result in results)
    
    for i, (candidate_id, real_votes, fake_votes, total_votes) in enumerate(results, 1):
        candidate_name = get_candidate_name(candidate_id)
        percentage = (total_votes / total_all_votes * 100) if total_all_votes > 0 else 0
        text += f"{i}. {candidate_name}\n"
        text += f"   Голосов: {total_votes} ({percentage:.1f}%)\n\n"
    
    text += f"📈 Общая статистика:\n"
    text += f"• Всего голосов: {total_all_votes}\n"
    text += f"• Активность: {stats['activity_percent']:.1f}%"
    
    await message.reply_text(text)

async def show_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показ списка пользователей"""
    # Определяем, откуда вызвана функция
    if update.message:
        message = update.message
    elif update.callback_query:
        message = update.callback_query.message
        await update.callback_query.answer()
    else:
        return
    
    users = db.get_all_users()
    
    if not users:
        await message.reply_text("👥 Пользователи не найдены.")
        return
    
    text = f"👥 ЗАРЕГИСТРИРОВАННЫЕ ПОЛЬЗОВАТЕЛИ ({len(users)})\n\n"
    
    for i, user in enumerate(users[:50], 1):  # Показываем первые 50
        status = "✅ Проголосовал" if user['has_voted'] else "⏳ Не голосовал"
        text += f"{i}. {user['full_name']}\n"
        text += f"   Курс: {user['course']} | {status}\n"
        text += f"   ID: {user['telegram_id']}\n\n"
    
    if len(users) > 50:
        text += f"... и еще {len(users) - 50} пользователей"
    
    await message.reply_text(text)

async def show_votes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показ детальных голосов"""
    # Определяем, откуда вызвана функция
    if update.message:
        message = update.message
    elif update.callback_query:
        message = update.callback_query.message
        await update.callback_query.answer()
    else:
        return
    
    votes = db.get_all_votes()
    
    if not votes:
        await message.reply_text("🗳️ Голоса не найдены.")
        return
    
    text = f"🗳️ ДЕТАЛЬНЫЕ ГОЛОСА ({len(votes)})\n\n"
    
    for i, vote in enumerate(votes[:30], 1):  # Показываем первые 30
        candidate_name = get_candidate_name(vote['candidate_id'])
        vote_time = datetime.fromisoformat(vote['vote_timestamp']).strftime("%d.%m.%Y, %H:%M:%S")
        text += f"{i}. {vote['full_name']}\n"
        text += f"   👤 {candidate_name}\n"
        text += f"   📚 Курс: {vote['course']}\n"
        text += f"   🆔 ID: {vote['telegram_id']}\n"
        text += f"   🕐 Время: {vote_time}\n\n"
    
    if len(votes) > 30:
        text += f"... и еще {len(votes) - 30} голосов"
    
    await message.reply_text(text)

async def show_candidate_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str):
    """Показ выбора кандидата для накрутки/удаления голосов"""
    # Определяем, откуда вызвана функция
    if update.message:
        message = update.message
    elif update.callback_query:
        message = update.callback_query.message
        await update.callback_query.answer()
    else:
        return
    
    action_text = "НАКРУТКА ГОЛОСОВ" if action == "add" else "ОТНЯТЬ ГОЛОСА"
    emoji = "➕" if action == "add" else "➖"
    
    keyboard = []
    for candidate in CANDIDATES:
        keyboard.append([InlineKeyboardButton(
            f"{candidate['emoji']} {candidate['name']}",
            callback_data=f"{action}_votes_{candidate['id']}"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await message.reply_text(
        f"{emoji} {action_text}\n\n"
        f"Выберите кандидата:",
        reply_markup=reply_markup
    )

async def show_announce_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показ меню объявления победителя"""
    import sqlite3
    
    # Определяем, откуда вызвана функция
    if update.message:
        message = update.message
    elif update.callback_query:
        message = update.callback_query.message
        await update.callback_query.answer()
    else:
        return
    
    # Получаем текущие результаты
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT candidate_id, total_votes 
        FROM results ORDER BY total_votes DESC
    ''')
    results = cursor.fetchall()
    conn.close()
    
    text = "🏆 ОБЪЯВЛЕНИЕ ПОБЕДИТЕЛЯ\n\n"
    text += "📊 Текущие результаты:\n\n"
    
    total_votes = sum(result[1] for result in results)
    
    for i, (candidate_id, votes) in enumerate(results, 1):
        candidate_name = get_candidate_name(candidate_id)
        percentage = (votes / total_votes * 100) if total_votes > 0 else 0
        text += f"{i}. {candidate_name}\n"
        text += f"   Процент: {percentage:.1f}%\n\n"
    
    keyboard = [
        [InlineKeyboardButton("👑 Выбрать победителя вручную", callback_data="announce_manual")],
        [InlineKeyboardButton("❌ Отмена", callback_data="announce_cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await message.reply_text(text, reply_markup=reply_markup)

async def export_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экспорт данных"""
    # Определяем, откуда вызвана функция
    if update.message:
        message = update.message
    elif update.callback_query:
        message = update.callback_query.message
        await update.callback_query.answer()
    else:
        return
    
    await message.reply_text("📊 Подготавливаю экспорт данных...")
    
    try:
        filename = db.export_to_csv()
        
        # Получаем статистику для сообщения
        stats = db.get_voting_stats()
        
        text = "📊 Экспорт данных голосования (CSV)\n\n"
        text += f"📈 Статистика:\n"
        text += f"👥 Пользователей: {stats['total_users']}\n"
        text += f"🗳️ Голосов: {stats['voted_users']}\n"
        text += f"📅 Дата: {datetime.now().strftime('%d.%m.%Y, %H:%M:%S')}"
        
        await message.reply_document(
            document=open(filename, 'rb'),
            caption=text
        )
        
        # Удаляем временный файл
        os.remove(filename)
        
    except Exception as e:
        await message.reply_text(f"❌ Ошибка при экспорте: {str(e)}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user_id = update.effective_user.id
    text = update.message.text
    state = user_states.get(user_id)

    if text in {BTN_VOTE, BTN_STATS, BTN_ADMIN, BTN_HELP, BTN_SITE} and state not in BUSY_STATES:
        if text == BTN_VOTE:
            await show_voting_menu(update, context)
        elif text == BTN_STATS:
            if is_admin(user_id):
                await show_stats(update, context)
            else:
                await update.message.reply_text("❌ Статистика доступна только администратору.")
        elif text == BTN_ADMIN:
            await admin_command(update, context)
        elif text == BTN_SITE:
            await update.message.reply_text(
                f"Ознакомление с кандидатами:\n{SITE_URL}\n\nГолосование — только в этом боте.",
                reply_markup=site_link_keyboard()
            )
        elif text == BTN_HELP:
            await help_command(update, context)
        return
    
    if user_id not in user_states:
        await update.message.reply_text(
            "Используйте кнопки меню или /start",
            reply_markup=main_keyboard(user_id)
        )
        return
    
    state = user_states[user_id]
    
    if state == UserState.REGISTRATION_NAME:
        # Проверяем ФИО
        if len(text.strip()) < 5:
            await update.message.reply_text("❌ ФИО должно содержать минимум 5 символов. Попробуйте еще раз:")
            return
        
        # Сохраняем имя и переходим к курсу
        context.user_data['full_name'] = text.strip()
        user_states[user_id] = UserState.REGISTRATION_COURSE
        await update.message.reply_text(
            "✅ ФИО принято!\n\n"
            "📚 Введите ваш курс (например: 1, 2, 3, 4, 5):"
        )
    
    elif state == UserState.REGISTRATION_COURSE:
        # Проверяем курс
        try:
            course = int(text.strip())
            if course < 1 or course > 5:
                await update.message.reply_text("❌ Курс должен быть от 1 до 5. Попробуйте еще раз:")
                return
        except ValueError:
            await update.message.reply_text("❌ Введите корректный номер курса (1-5):")
            return
        
        # Сохраняем курс и переходим к CAPTCHA
        context.user_data['course'] = course
        user_states[user_id] = UserState.REGISTRATION_CAPTCHA
        
        # Генерируем CAPTCHA
        captcha_code, captcha_file = captcha_gen.generate_captcha(user_id)
        db.save_captcha_session(user_id, captcha_code)
        
        await update.message.reply_text(
            "✅ Курс принят!\n\n"
            "🔐 Решите CAPTCHA для завершения регистрации:"
        )
        await update.message.reply_photo(photo=open(captcha_file, 'rb'))
        
        # Удаляем файл CAPTCHA
        captcha_gen.cleanup_captcha(captcha_file)
    
    elif state == UserState.REGISTRATION_CAPTCHA:
        # Проверяем CAPTCHA
        if db.verify_captcha(user_id, text.strip()):
            # Регистрация успешна
            full_name = context.user_data['full_name']
            course = context.user_data['course']
            
            result = db.add_user(user_id, full_name, course)
            
            if result == "success":
                del user_states[user_id]
                del context.user_data['full_name']
                del context.user_data['course']
                
                await update.message.reply_text(
                    "✅ Регистрация успешна!\n\nТеперь вы можете голосовать.",
                    reply_markup=main_keyboard(user_id)
                )
                await show_voting_menu(update, context)
            elif result == "telegram_id_exists":
                await update.message.reply_text(
                    "❌ Вы уже зарегистрированы в системе!\n"
                    "Используйте /start для начала голосования."
                )
                del user_states[user_id]
            elif result == "name_exists":
                await update.message.reply_text(
                    "❌ Пользователь с таким ФИО уже зарегистрирован.\n"
                    "Пожалуйста, проверьте правильность написания или обратитесь к администратору.\n\n"
                    "Попробуйте еще раз с командой /start"
                )
                del user_states[user_id]
            else:
                await update.message.reply_text(
                    f"❌ Ошибка регистрации: {result}\n"
                    "Попробуйте еще раз с командой /start"
                )
                del user_states[user_id]
        else:
            await update.message.reply_text("❌ Неверная CAPTCHA. Попробуйте еще раз:")
    
    elif state == UserState.ADMIN_ADD_VOTES:
        # Обработка добавления голосов
        try:
            count = int(text.strip())
            if count <= 0:
                await update.message.reply_text("❌ Количество должно быть больше 0:")
                return
            
            candidate_id = context.user_data.get('candidate_id')
            if candidate_id:
                db.add_fake_votes(candidate_id, count)
                candidate_name = get_candidate_name(candidate_id)
                await update.message.reply_text(f"✅ Добавлено {count} голосов для {candidate_name}")
                del user_states[user_id]
                del context.user_data['candidate_id']
            else:
                await update.message.reply_text("❌ Ошибка. Попробуйте еще раз.")
                del user_states[user_id]
        except ValueError:
            await update.message.reply_text("❌ Введите корректное число:")
    
    elif state == UserState.ADMIN_REMOVE_VOTES:
        # Обработка удаления голосов
        try:
            count = int(text.strip())
            if count <= 0:
                await update.message.reply_text("❌ Количество должно быть больше 0:")
                return
            
            candidate_id = context.user_data.get('candidate_id')
            if candidate_id:
                db.remove_fake_votes(candidate_id, count)
                candidate_name = get_candidate_name(candidate_id)
                await update.message.reply_text(f"✅ Удалено {count} голосов у {candidate_name}")
                del user_states[user_id]
                del context.user_data['candidate_id']
            else:
                await update.message.reply_text("❌ Ошибка. Попробуйте еще раз.")
                del user_states[user_id]
        except ValueError:
            await update.message.reply_text("❌ Введите корректное число:")

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback запросов"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    # Обработка голосования
    if data == "open_vote":
        await show_voting_menu(update, context)
        return

    if data.startswith("vote_"):
        if not is_admin(user_id):
            # Проверяем, может ли пользователь голосовать
            user = db.get_user(user_id)
            if not user:
                await query.edit_message_text("❌ Сначала пройдите регистрацию командой /start")
                return
            
            if user['has_voted']:
                await query.edit_message_text("✅ Вы уже проголосовали!")
                return
        
        candidate_id = int(data.split("_")[1])
        
        if db.add_vote(user_id, candidate_id):
            candidate_name = get_candidate_name(candidate_id)
            await query.edit_message_text(
                f"✅ ГОЛОС УЧТЁН!\n\n"
                f"Вы проголосовали за:\n"
                f"{candidate_name}\n\n"
                f"Спасибо за участие! 🎉"
            )
        else:
            await query.edit_message_text("❌ Ошибка при голосовании. Попробуйте еще раз.")
    
    # Админские команды
    elif data == "admin_stats":
        await show_stats(update, context)
    
    elif data == "admin_users":
        await show_users(update, context)
    
    elif data == "admin_votes":
        await show_votes(update, context)
    
    elif data == "admin_add_votes":
        await show_candidate_selection(update, context, "add")
    
    elif data == "admin_remove_votes":
        await show_candidate_selection(update, context, "remove")
    
    elif data == "admin_announce":
        await show_announce_menu(update, context)
    
    elif data == "admin_export":
        await export_data(update, context)
    
    elif data == "admin_reset":
        await reset_command(update, context)
    
    elif data == "admin_cleanup":
        # Очищаем дублирующиеся записи
        db.cleanup_duplicate_results()
        await query.edit_message_text("🧹 Дублирующиеся записи очищены!")
    
    elif data == "admin_check_duplicates":
        # Проверяем дублирующихся пользователей
        duplicates = db.check_duplicate_users()
        
        text = "🔍 ПРОВЕРКА ДУБЛИРУЮЩИХСЯ ПОЛЬЗОВАТЕЛЕЙ\n\n"
        
        if duplicates['duplicate_names']:
            text += "📝 Дублирующиеся ФИО:\n"
            for name, count in duplicates['duplicate_names']:
                text += f"• {name} ({count} раз)\n"
            text += "\n"
        else:
            text += "✅ Дублирующихся ФИО не найдено\n\n"
        
        if duplicates['duplicate_ids']:
            text += "🆔 Дублирующиеся Telegram ID:\n"
            for user_id, count in duplicates['duplicate_ids']:
                text += f"• {user_id} ({count} раз)\n"
        else:
            text += "✅ Дублирующихся Telegram ID не найдено"
        
        await query.edit_message_text(text)
    
    elif data == "admin_stop_voting":
        # Останавливаем голосование
        import config
        config.VOTING_ACTIVE = False
        await query.edit_message_text("⏸️ Голосование остановлено администратором.")
    
    elif data == "admin_start_voting":
        # Запускаем голосование
        import config
        config.VOTING_ACTIVE = True
        await query.edit_message_text("▶️ Голосование запущено администратором.")
    
    # Обработка накрутки/удаления голосов
    elif data.startswith("add_votes_") or data.startswith("remove_votes_"):
        candidate_id = int(data.split("_")[2])
        action = "add" if data.startswith("add_") else "remove"
        
        context.user_data['candidate_id'] = candidate_id
        user_states[user_id] = UserState.ADMIN_ADD_VOTES if action == "add" else UserState.ADMIN_REMOVE_VOTES
        
        action_text = "добавления" if action == "add" else "удаления"
        await query.edit_message_text(f"Введите количество голосов для {action_text}:")
    
    # Обработка объявления победителя
    elif data == "announce_manual":
        keyboard = []
        for candidate in CANDIDATES:
            keyboard.append([InlineKeyboardButton(
                f"{candidate['emoji']} {candidate['name']}",
                callback_data=f"announce_winner_{candidate['id']}"
            )])
        keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="announce_cancel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text("Выберите победителя:", reply_markup=reply_markup)
    
    elif data.startswith("announce_winner_"):
        import sqlite3
        candidate_id = int(data.split("_")[2])
        candidate_name = get_candidate_name(candidate_id)
        
        # Получаем статистику для объявления
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT total_votes FROM results WHERE candidate_id = ?', (candidate_id,))
        result = cursor.fetchone()
        conn.close()
        
        votes = result[0] if result else 0
        total_votes = sum(r[1] for r in db.get_voting_stats()['results'])
        percentage = (votes / total_votes * 100) if total_votes > 0 else 0
        
        announcement_text = (
            f"🏆 ГОЛОСОВАНИЕ ЗАВЕРШЕНО!\n\n"
            f"👑 ПОБЕДИТЕЛЬ:\n\n"
            f"🏆 {candidate_name}"
        )
        
        # Отправляем объявление всем пользователям
        users = db.get_all_users()
        sent_count = 0
        
        # Показываем админу, что началась отправка
        await query.edit_message_text("📤 Отправляю объявление всем пользователям...")
        
        for user in users:
            try:
                await context.bot.send_message(
                    chat_id=user['telegram_id'],
                    text=announcement_text
                )
                sent_count += 1
                
                # Добавляем небольшую задержку между отправками
                import asyncio
                await asyncio.sleep(0.1)  # 100ms задержка
                
            except Exception as e:
                # Логируем ошибки для отладки
                print(f"Ошибка отправки пользователю {user['telegram_id']}: {e}")
                pass
        
        # Показываем админу результат отправки
        await query.edit_message_text(
            f"✅ Объявление отправлено!\n\n"
            f"🏆 ПОБЕДИТЕЛЬ:\n\n"
            f"🏆 {candidate_name}\n"
            f"Процент: {percentage:.1f}%\n\n"
            f"📤 Отправлено пользователям: {sent_count}/{len(users)}"
        )
    
    elif data == "announce_cancel":
        await query.edit_message_text("❌ Объявление отменено.")
    
    # Обработка сброса
    elif data == "reset_confirm":
        db.reset_voting()
        await query.edit_message_text("🔄 Сброс данных выполнен. Все голоса обнулены.")
    
    elif data == "reset_cancel":
        await query.edit_message_text("❌ Сброс отменен.")

def main():
    """Основная функция запуска бота"""
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ Ошибка: Необходимо указать токен бота в файле config.py")
        return
    
    # Создаем приложение с настройками таймаута
    application = Application.builder().token(BOT_TOKEN).get_updates_read_timeout(30).get_updates_write_timeout(30).get_updates_connect_timeout(30).build()
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("myid", myid_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("users", users_command))
    application.add_handler(CommandHandler("votes", votes_command))
    application.add_handler(CommandHandler("addvotes", addvotes_command))
    application.add_handler(CommandHandler("removevotes", removevotes_command))
    application.add_handler(CommandHandler("announce", announce_command))
    application.add_handler(CommandHandler("export", export_command))
    application.add_handler(CommandHandler("reset", reset_command))
    
    # Добавляем обработчики callback запросов
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    
    # Добавляем обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)
    
    # Запускаем бота с обработкой ошибок
    start_web_server()
    print("🤖 Бот запущен!")
    try:
        application.run_polling()
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
        print("🔄 Перезапуск через 5 секунд...")
        import time
        time.sleep(5)
        main()  # Рекурсивный перезапуск

if __name__ == '__main__':
    main()
