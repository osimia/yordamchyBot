import os
import logging
import asyncio
import nest_asyncio
from aiohttp import web
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, ConversationHandler,
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

# === НАСТРОЙКИ ===
BOT_TOKEN = "7340534866:AAG3TC62ASvJJqqd_ZCGdI4klvN-BmCw9bc"
WEBHOOK_DOMAIN = "https://yordamchybot.onrender.com"
WEBHOOK_PATH = "/webhook"
PORT = 10000

# === ЛОГИ ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === ИНИЦИАЛИЗАЦИЯ PTB ===
application = Application.builder().token(BOT_TOKEN).build()

# === СОСТОЯНИЯ ДЛЯ ConversationHandler ===
AMOUNT, TYPE, CATEGORY, DESCRIPTION = range(4)
EDIT_CHOOSE, EDIT_TYPE, EDIT_CATEGORY, EDIT_AMOUNT, EDIT_DESCRIPTION, EDIT_CONFIRM = range(10, 16)

# === ОБРАБОТЧИКИ ===
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
    fallbacks=[CommandHandler("cancel", cancel_add)]
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
    fallbacks=[CommandHandler("cancel", cancel_add)]
))

application.add_handler(CallbackQueryHandler(lang_set, pattern="^(ru|en|tg)$"))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, button_text_handler))

# === СОЗДАНИЕ ТАБЛИЦ В БД ===
Base.metadata.create_all(bind=engine)
logger.info("✅ Таблицы созданы или уже существуют.")


# === ОБРАБОТЧИК WEBHOOK-ЗАПРОСОВ ===
async def handle(request):
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.update_queue.put(update)
        return web.Response(text="OK")
    except Exception as e:
        logger.exception("❌ Ошибка в обработке webhook")
        return web.Response(status=500)


# === ГЛАВНАЯ АСИНХРОННАЯ ФУНКЦИЯ ===
async def main():
    webhook_url = f"{WEBHOOK_DOMAIN}{WEBHOOK_PATH}"
    logger.info(f"📡 Устанавливаем Webhook: {webhook_url}")

    await application.initialize()
    await application.bot.set_webhook(url=webhook_url)

    # Запускаем aiohttp веб-сервер
    app = web.Application()
    app.router.add_post(WEBHOOK_PATH, handle)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    logger.info(f"🚀 Бот слушает порт {PORT} на {WEBHOOK_PATH}")
    await application.start()
    await application.updater.start_polling()  # опционально
    await application.updater.idle()


# === ЗАПУСК ===
if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
