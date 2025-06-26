import os
import logging
import telegram
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    Application, ConversationHandler, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters
)
from handlers import (
    start_handler, add_start, add_amount, add_type,
    add_category, add_description, cancel_add,
    balance_handler, report_handler, lang_handler,
    lang_set, button_text_handler,
    edit_last_start, edit_last_choose_field, edit_last_edit_type,
    edit_last_edit_category, edit_last_edit_amount, edit_last_edit_description, edit_last_delete
)
from db import engine, Base
from models import User, Transaction

# Версия PTB
assert telegram.__version__ == "21.9", f"PTB version mismatch: {telegram.__version__}"

# Логгирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)

# Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_DOMAIN = os.getenv("WEBHOOK_DOMAIN")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")


if not BOT_TOKEN or not WEBHOOK_DOMAIN:
    raise Exception("BOT_TOKEN или WEBHOOK_DOMAIN не установлены!")

# Telegram Application
application = Application.builder().token(BOT_TOKEN).build()

# Стейты
AMOUNT, TYPE, CATEGORY, DESCRIPTION = range(4)
EDIT_CHOOSE, EDIT_TYPE, EDIT_CATEGORY, EDIT_AMOUNT, EDIT_DESCRIPTION, EDIT_CONFIRM = range(10, 16)

# Обработчики
application.add_handler(CommandHandler("start", start_handler))
application.add_handler(CommandHandler("balance", balance_handler))
application.add_handler(CommandHandler("report", report_handler))
application.add_handler(CommandHandler("lang", lang_handler))

application.add_handler(ConversationHandler(
    entry_points=[CommandHandler("add", add_start)],
    states={
        AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_amount)],
        TYPE: [CallbackQueryHandler(add_type, pattern="^(income|expense)$")],
        CATEGORY: [CallbackQueryHandler(add_category)],
        DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_description)],
    },
    fallbacks=[CommandHandler("cancel", cancel_add)],
    per_message=True
))

application.add_handler(ConversationHandler(
    entry_points=[CommandHandler("edit_last", edit_last_start)],
    states={
        EDIT_CHOOSE: [CallbackQueryHandler(edit_last_choose_field)],
        EDIT_TYPE: [CallbackQueryHandler(edit_last_edit_type)],
        EDIT_CATEGORY: [CallbackQueryHandler(edit_last_edit_category)],
        EDIT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_last_edit_amount)],
        EDIT_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_last_edit_description)],
    },
    fallbacks=[CommandHandler("cancel", cancel_add)],
    per_message=True
))

application.add_handler(CallbackQueryHandler(lang_set, pattern="^(ru|en|tg)$"))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, button_text_handler))


# Webhook endpoint
@app.route("/")
def home():
    return "✅ Bot is running!"

@app.route(WEBHOOK_PATH, methods=["POST", "GET"])
def webhook():
    if request.method == "GET":
        return "Webhook endpoint — use POST from Telegram", 200

    try:
        logger.info("➡️ Запрос в /webhook получен")
        data = request.get_data(as_text=True)
        logger.info(f"📥 RAW JSON от Telegram:\n{data}")
        json_data = request.get_json(force=True)
        update = Update.de_json(json_data, application.bot)
        application.update_queue.put(update)
        logger.info("✅ Обновление отправлено в очередь")
        return "ok", 200
    except Exception as e:
        logger.exception("❌ Ошибка в обработке webhook")
        return "error", 500


# Асинхронная настройка
async def setup():
    await application.initialize()
    await application.start()  # ← Это обязательно!
    await application.bot.set_webhook(url=f"{WEBHOOK_DOMAIN}{WEBHOOK_PATH}")
    logger.info("✅ Webhook установлен")


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Таблицы созданы или уже существуют.")

    asyncio.run(setup())

    PORT = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=PORT)
