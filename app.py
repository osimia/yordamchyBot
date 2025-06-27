import os
import logging
import telegram
import asyncio
from telegram.ext import (
    Application, ConversationHandler, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters
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

# ✅ Проверка версии PTB
assert telegram.__version__ == "21.9", f"PTB version mismatch: {telegram.__version__}"

# ✅ Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Переменные окружения
BOT_TOKEN = "7887045864:AAHGhqn23Z9oUzaZJO3fnzSr6FH5st4g22U"
WEBHOOK_DOMAIN = "https://yordamchybot.onrender.com"
WEBHOOK_PATH = "/webhook"
PORT = int(os.environ.get("PORT", 10000))  # Render автоматически задаёт переменную PORT

# ✅ Проверка переменных
if not BOT_TOKEN or not WEBHOOK_DOMAIN:
    raise Exception("❌ BOT_TOKEN или WEBHOOK_DOMAIN не установлены в переменных окружения!")

# ✅ Telegram Application
application = Application.builder().token(BOT_TOKEN).build()

# ✅ Состояния
AMOUNT, TYPE, CATEGORY, DESCRIPTION = range(4)
EDIT_CHOOSE, EDIT_TYPE, EDIT_CATEGORY, EDIT_AMOUNT, EDIT_DESCRIPTION, EDIT_CONFIRM = range(10, 16)

# ✅ Обработчики команд
application.add_handler(CommandHandler("start", start_handler))
application.add_handler(CommandHandler("balance", balance_handler))
application.add_handler(CommandHandler("report", report_handler))
application.add_handler(CommandHandler("lang", lang_handler))

# ✅ Добавление доходов/расходов
application.add_handler(ConversationHandler(
    entry_points=[CommandHandler("add", add_start)],
    states={
        AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_amount)],
        TYPE: [CallbackQueryHandler(add_type, pattern="^(income|expense)$")],
        CATEGORY: [CallbackQueryHandler(add_category)],
        DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_description)],
    },
    fallbacks=[CommandHandler("cancel", cancel_add)]
))

# ✅ Редактирование последней записи
application.add_handler(ConversationHandler(
    entry_points=[CommandHandler("edit_last", edit_last_start)],
    states={
        EDIT_CHOOSE: [CallbackQueryHandler(edit_last_choose_field)],
        EDIT_TYPE: [CallbackQueryHandler(edit_last_edit_type)],
        EDIT_CATEGORY: [CallbackQueryHandler(edit_last_edit_category)],
        EDIT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_last_edit_amount)],
        EDIT_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_last_edit_description)],
    },
    fallbacks=[CommandHandler("cancel", cancel_add)]
))

# ✅ Кнопки и текст
application.add_handler(CallbackQueryHandler(lang_set, pattern="^(ru|en|tg)$"))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, button_text_handler))

# ✅ Создание таблиц
Base.metadata.create_all(bind=engine)
logger.info("✅ Таблицы созданы или уже существуют.")


# ✅ Главный запуск с webhook
async def main():
    webhook_url = f"{WEBHOOK_DOMAIN}{WEBHOOK_PATH}"
    logger.info(f"📡 Устанавливаем webhook на: {webhook_url}")

    await application.initialize()
    await application.bot.set_webhook(url=webhook_url)
    await application.start()

    logger.info("🚀 Бот запущен через webhook!")

    await application.updater.start_webhook(
        listen="0.0.0.0",
        port=PORT
    )

    await application.updater.idle()


if __name__ == "__main__":
    asyncio.run(main())
