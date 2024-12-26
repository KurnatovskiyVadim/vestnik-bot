import os
import logging
import psycopg2
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Настройки логгирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Подключение к базе данных
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
TOKEN = os.getenv("TOKEN")

def init_db():
    conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        username TEXT,
        message_text TEXT,
        file_path TEXT,
        message_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    cursor.close()
    conn.close()

# Сохранение сообщения в базу данных
def save_message(user_id, username, message_text, file_path=None):
    conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO messages (user_id, username, message_text, file_path)
    VALUES (%s, %s, %s, %s);
    """, (user_id, username, message_text, file_path))
    conn.commit()
    cursor.close()
    conn.close()

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("Инструкция", callback_data="instruction")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"Привет, {user.first_name}! Я ваш бот.", reply_markup=reply_markup)

# Обработчик команды /instruction
async def instruction_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Инструкция: Вы можете отправлять мне сообщения, документы, фотографии или видео, и я сохраню их в базе данных.")

# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message_text = update.message.text

    # Ответ на сообщение
    response = "Спасибо за ваше сообщение!"
    await update.message.reply_text(response)

    # Сохранение сообщения в базу данных
    save_message(user.id, user.username, message_text)

# Обработчик медиафайлов
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    file = update.message.document or update.message.photo[-1] or update.message.video
    caption = update.message.caption if update.message.caption else None

    # Скачивание файла
    file_id = file.file_id
    file_name = file.file_name if hasattr(file, 'file_name') else f"file_{file_id}"
    file_path = os.path.join("downloads", file_name)

    # Убедимся, что папка существует
    os.makedirs("downloads", exist_ok=True)

    # Сохранение файла
    new_file = await context.bot.get_file(file_id)
    await new_file.download_to_drive(file_path)

    # Ответ пользователю
    await update.message.reply_text(f"Ваш файл сохранен как {file_name}.")

    # Сохранение данных в базу
    save_message(user.id, user.username, caption, file_path)

# Обработчик нажатий кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "instruction":
        await query.edit_message_text("Инструкция: Вы можете отправлять мне сообщения, документы, фотографии или видео, и я сохраню их в базе данных.")

# Основной запуск бота
if __name__ == "__main__":
    # Инициализация базы данных
    init_db()

    # Токен бота
    TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

    # Создание приложения
    application = ApplicationBuilder().token(TOKEN).build()

    # Обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("instruction", instruction_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO | filters.VIDEO, handle_file))
    application.add_handler(CallbackQueryHandler(button_handler))

    # Запуск бота
    application.run_polling()
