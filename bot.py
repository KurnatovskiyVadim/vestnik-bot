import os
import logging
import random
import psycopg2
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup, Application
from telegram.bot import BotCommand
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
INSTRUCTION_TEXT = """Как писать сплетню?

В бот необязательно отправлять готовую для публикации сплетню, редакция «Владожского вестника» может докрутить ее на основе полученной от вас информации.

❕Но! Если вы хотите максимально погрузиться в роль репортера, научиться писать готовые сплетни, придумывать для них рубрику и в конце получить удовольствие, услышав как на утреннем сборе все хихикают от вашей собственной сплетни, предлагаем следовать следующим правилам:

 1. Будьте внимательны к окружающим событиям. Сплетней может стать что угодно, главное проявить креатив.

 2. Заметили что-то интересное? Попробуйте сформулировать, что конкретно произошло, назовите это, выберите синонимы или, возможно, подберите фразеологизм.

 3. Далее постарайтесь раскрутить сплетню ответив на такие вопросы: кто действующие лица? Как они связаны между собой? Почему это случилось? Что следует после этого? Как это повлияет на всех нас?

 4. Не стесняйтесь преувеличивать и обобщать, сплетня должна вызывать эмоцию. Например, если вы услышали, что Маша попросила Сашу купить кофе, так как забыла в корпусе карту, это вполне сойдет за: «ШОК! Маша вынуждена выйти на содержание к Саше»

 5. Если чувствуете, что выжали из себя все, что смогли, перечитайте ваш текст, поправьте тавтологию и уберите лишние слова (при необходимости добавьте лишние слова)

 6. Если хотите, подберите рубрику для сплетни или укажите свою

 7. Не забудьте указать если ваше сообщение адресовано кому то лично!

 8. Отправьте вашу сплетню нам и ждите оваций. Вы великолепны! ✨

❗️Внимание! Любой полученный нами текст будет проходить валидацию и при необходимости может быть дополнен без одобрения автора)

❗️Также любой текст, направленный на то, чтобы оскорбить кого-то, унизить чье либо достоинство или вызвать в окружающих ненависть к кому либо будет не допущен к публикации.
"""

RESPONSES = [
    "Ваше сообщение принято",
    "Крыски побежали работать",
    "Поздравляю! Вы приняты в штаб сплетников",
    "Круто! Продолжай держать ушко шире",
    "Прямо сейчас вредакции зашебуршались",
    "Ты внес вклад в мышиный мир сплетен",
    "Наше издательство благодарит вас",
    "Выбирай, кто ты теперь: мышь или крыса?",
    "В змеином клубке пополнение!",
    "Будем с нетерпением ждать еще инфоповодов",
    "Все что вы написали будет использовано против всех",
    "Кажется, ты начал год Змеи абсолютно верно",
    "Благодарим вас за выбор нашего издательства и будем ждать вас снова",
    "Станки заработали, сплетня ушла в тираж",
    "Наш девиз: полная анонимность, но никакой приватности!",
    "Здорово! Суйте нос в чужие дела и никогда не стесняйтесь этого!",
    "Никто не знает, кто это написал... Но это звучит интересно!",
    "Записано. Хранится под семью замками до первого утреннего обсуждения.",
    "Ваша сплетня добавлена в тайный архив лагерных слухов.",
    "Ты в деле! А теперь слушай, что принесут другие.",
    "Информация обработана, агенты на месте!",
    "Сплетня записана! Теперь лагерь оживет новыми обсуждениями.",
    "Слух пошел гулять по тенистым уголкам лагеря!",
    "Секретная лаборатория слухов начала обработку.",
    "Крысы тихо шепчутся, благодарят за материал.",
    "Засекречено, но обязательно станет известно всем.",
    "Браво! Действуем по плану: слухи в массы!",
    "Мы в восторге! Лагерь зашепчется еще сильнее.",
    "Палаточные крысы уже обсуждают твоё сообщение.",
    "Отличный вклад в великое дело лагерной гласности!"
]

def init_db():
    conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id SERIAL PRIMARY KEY,
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
def save_message(username, message_text, file_path=None):
    conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO messages (username, message_text, file_path)
    VALUES (%s, %s, %s, %s);
    """, (username, message_text, file_path))
    conn.commit()
    cursor.close()
    conn.close()

def sample_response():
  return random.choice(RESPONSES)

async def set_commands(application: Application):
    await application.bot.set_my_commands([
        BotCommand("start","Начало"),
        BotCommand("welcome","Руководство")
      ])

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("Руководство", callback_data="instruction")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"Привет, {user.first_name}!", reply_markup=reply_markup)

# Обработчик команды /instruction
async def instruction_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(INSTRUCTION_TEXT)

# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message_text = update.message.text

    # Сохранение сообщения в базу данных
    save_message(user.username, message_text)

    # Ответ на сообщение
    await update.message.reply_text(sample_response())

# Обработчик медиафайлов
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    file = update.message.document or update.message.photo[-1] or update.message.video

    caption = update.message.caption if update.message.caption else None
    file_path = "https://api.telegram.org/bot".join(TOKEN, "/getFile?file_id=", file.file_id)

    # Сохранение данных в базу
    save_message(user.id, user.username, caption, file_path)

    await update.message.reply_text(sample_response())

# Обработчик нажатий кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "instruction":
        await query.edit_message_text(INSTRUCTION_TEXT)

# Основной запуск бота
if __name__ == "__main__":
    # Инициализация базы данных
    init_db()

    # Создание приложения
    application = ApplicationBuilder().token(TOKEN).build()

    application.job_queue.run_once(lambda _: set_commands(application), 0)

    # Обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("instruction", instruction_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO | filters.VIDEO, handle_file))
    application.add_handler(CallbackQueryHandler(button_handler))

    # Запуск бота
    application.run_polling()
