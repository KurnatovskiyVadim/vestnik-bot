import asyncio
import logging
import os
import random
import uvicorn
import psycopg2

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route

from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Define configuration constants
URL = os.getenv("RENDER_EXTERNAL_URL")
PORT = 8000
TOKEN = os.getenv("TOKEN")

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

WELCOME_TEXT = "Добро пожаловать в редакцию Владожского Вестика! Мы рады приветствовать новых сплетников и сплетниц в наших рядах!"
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
    "Прямо сейчас в редакции зашебуршались",
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
    "Ты в деле! Вы официально стали частью лагерной легенды!",
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

MOUSE_OF_DAY_RESPONSES = [
  "https://i.ibb.co/k6qtKzW/photo-1-2025-01-02-17-06-42.jpg",
  "https://ibb.co/fFdwJQ4",
  "https://ibb.co/4jc9gP0",
  "https://ibb.co/0JJwDLT",
  "https://ibb.co/wyHf90X",
  "https://ibb.co/9rhMwc0",
  "https://ibb.co/myYzXpQ",
  "https://ibb.co/S3MPbt4",
  "https://ibb.co/k5WgdKC",
  "https://ibb.co/2q8t9dT",
  "https://ibb.co/JC341ML",
  "https://ibb.co/k48qDf1",
  "https://ibb.co/MgB5Hgz",
  "https://ibb.co/w0XXZds",
  "https://ibb.co/9g8c5Yp",
  "https://ibb.co/SBFZMpf",
  "https://ibb.co/s3ncQ7g",
  "https://ibb.co/4JFVR0K",
  "https://ibb.co/vhz2W0d",
  "https://ibb.co/p3cVLSg",
  "https://ibb.co/ZmS0RR2",
  "https://ibb.co/7CfH2w8",
  "https://ibb.co/W024mPX",
  "https://ibb.co/tsz9xbX",
  "https://ibb.co/yk5w4FH",
  "https://ibb.co/pn29L6X",
  "https://ibb.co/M9Gh9mq",
  "https://ibb.co/SJrq0V5",
  "https://ibb.co/n7qJ6g8",
  "https://ibb.co/qsSSTRJ",
  "https://ibb.co/qk3WXsk",
  "https://ibb.co/n1yDxPY",
  "https://ibb.co/XVFCnS1",
  "https://ibb.co/M50bjDC",
  "https://ibb.co/c179WDM",
  "https://ibb.co/hW1RTjQ",
  "https://ibb.co/rcS7bGz",
  "https://ibb.co/jzLs8zY",
  "https://ibb.co/CJgG0J6",
  "https://ibb.co/wzrhWVY",
  "https://ibb.co/NSX6xh3",
  "https://ibb.co/p3GFjTp",
  "https://ibb.co/CMSMKNv",
  "https://ibb.co/48QVFHV",
  "https://ibb.co/k3xg1pd",
  "https://ibb.co/1GK35PR",
  "https://ibb.co/LPFNZVh",
  "https://ibb.co/98V4TPv",
  "https://ibb.co/Ln8zVND",
  "https://ibb.co/zXFXdds",
  "https://ibb.co/LSBV6fG",
  "https://ibb.co/VMCt45F",
  "https://ibb.co/f2cn8HF",
  "https://ibb.co/kK9c2z7",
  "https://ibb.co/hcMLrbK",
  "https://ibb.co/J3NBYYS",
  "https://ibb.co/0C1jLb6"
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
    cursor.execute("INSERT INTO messages (username, message_text, file_path) VALUES (%s, %s, %s);", (username, message_text, file_path))
    conn.commit()
    cursor.close()
    conn.close()

def sample_response():
  return random.choice(RESPONSES)

def sample_mouse_of_day_response():
  return random.choice(MOUSE_OF_DAY_RESPONSES)

# Обработчик команды /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Руководство", callback_data="rules")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(WELCOME_TEXT, reply_markup=reply_markup)

# Обработчик команды /rules
async def rules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(INSTRUCTION_TEXT)

# Обработчик команды /rules
async def mouse_of_day_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("[](https://i.ibb.co/k6qtKzW/photo-1-2025-01-02-17-06-42.jpg)", parse_mode='MarkdownV2')

# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message_text = update.message.text

    # Ответ на сообщение
    await update.message.reply_text(sample_response())

    # Сохранение сообщения в базу данных
    save_message(user.username, message_text)

# Обработчик медиафайлов
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    file = update.message.document or update.message.photo[-1] or update.message.video

    caption = update.message.caption if update.message.caption else None
    file_path = f"https://api.telegram.org/bot{TOKEN}/getFile?file_id={file.file_id}"

    await update.message.reply_text(sample_response())

    # Сохранение данных в базу
    save_message(user.username, caption, file_path)

# Обработчик нажатий кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "rules":
        await query.edit_message_text(INSTRUCTION_TEXT)


###

async def main() -> None:
    """Set up PTB application and a web application for handling the incoming requests."""
    application = Application.builder().token(TOKEN).updater(None).build()

    # register handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("rules", rules_command))
    application.add_handler(CommandHandler("mouse_of_day", mouse_of_day_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO | filters.VIDEO, handle_file))
    application.add_handler(CallbackQueryHandler(button_handler))

    # Pass webhook settings to telegram
    await application.bot.set_webhook(url=f"{URL}/telegram", allowed_updates=Update.ALL_TYPES)

    # Set up webserver
    async def telegram(request: Request) -> Response:
        """Handle incoming Telegram updates by putting them into the `update_queue`"""
        await application.update_queue.put(
            Update.de_json(data=await request.json(), bot=application.bot)
        )
        return Response()

    async def health(_: Request) -> PlainTextResponse:
        return PlainTextResponse(content="OK")

    starlette_app = Starlette(
        routes=[
            Route("/telegram", telegram, methods=["POST"]),
            Route("/healthcheck", health, methods=["GET"]),
        ]
    )
    webserver = uvicorn.Server(
        config=uvicorn.Config(
            app=starlette_app,
            port=PORT,
            use_colors=False,
            host="0.0.0.0",  # NOTE: Render requires you to bind your webserver to 0.0.0.0
        )
    )

    # Run application and webserver together
    async with application:
        await application.start()
        await webserver.serve()
        await application.stop()


if __name__ == "__main__":
    asyncio.run(main())
