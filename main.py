import os
from dotenv import load_dotenv
from telegram.ext import (
    ConversationHandler, MessageHandler, filters,
    CallbackQueryHandler, ApplicationBuilder, CommandHandler
)
from handlers import (
    start_handler, add_start, add_amount, add_type,
    add_category, add_description, cancel_add,
    balance_handler, report_handler, lang_handler,
    lang_set, button_text_handler
)

# Стейты
AMOUNT, TYPE, CATEGORY, DESCRIPTION = range(4)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Команда /add — ВАЖНО: до CallbackQueryHandler(lang_set)
    add_conv = ConversationHandler(
        entry_points=[CommandHandler("add", add_start)],
        states={
            TYPE: [CallbackQueryHandler(add_type)],
            CATEGORY: [CallbackQueryHandler(add_category)],
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_amount)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_description)],
        },
        fallbacks=[CommandHandler("cancel", cancel_add)],
    )
    app.add_handler(add_conv)

    # Основные команды
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("balance", balance_handler))
    app.add_handler(CommandHandler("report", report_handler))
    app.add_handler(CommandHandler("lang", lang_handler))

    # Обработка выбора языка (после add_conv!)
    app.add_handler(CallbackQueryHandler(lang_set, pattern="^(ru|en|tg)$"))

    # Обработка кнопок меню (reply keyboard)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, button_text_handler))

    print("🤖 Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()