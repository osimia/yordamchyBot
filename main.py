import os
import logging
import telegram
from flask import Flask, request
from telegram import Update, Bot
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

telegram.__version__  # Убедимся, что всё в порядке
assert telegram.__version__ == "21.9", f"Неподдерживаемая версия PTB: {telegram.__version__}"

# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask-приложение
app = Flask(__name__)

# Telegram токен и webhook
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_DOMAIN = os.getenv("WEBHOOK_DOMAIN")  # Например: https://mybot.up.railway.app
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")
PORT = int(os.getenv("PORT", 8443))

# Проверка
if not BOT_TOKEN or not WEBHOOK_DOMAIN:
    raise Exception("BOT_TOKEN или WEBHOOK_DOMAIN не установлены!")

application = Application.builder().token(BOT_TOKEN).build()

# Регистрация обработчиков
AMOUNT, TYPE, CATEGORY, DESCRIPTION = range(4)
EDIT_CHOOSE, EDIT_TYPE, EDIT_CATEGORY, EDIT_AMOUNT, EDIT_DESCRIPTION, EDIT_CONFIRM = range(10, 16)

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
))

application.add_handler(CallbackQueryHandler(lang_set, pattern="^(ru|en|tg)$"))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, button_text_handler))

@app.route("/")
def home():
    return "✅ Bot is running!"

@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put(update)
    return "ok"

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Таблицы созданы или уже существуют.")
    
    application.bot.set_webhook(url=f"{WEBHOOK_DOMAIN}{WEBHOOK_PATH}")
    logger.info("✅ Webhook установлен")
    
    app.run(host="0.0.0.0", port=PORT)
