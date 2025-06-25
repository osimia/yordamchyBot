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
    lang_set, button_text_handler,
    edit_last_start, edit_last_choose_field, edit_last_edit_type,
    edit_last_edit_category, edit_last_edit_amount, edit_last_edit_description, edit_last_delete
)

# Стейты
AMOUNT, TYPE, CATEGORY, DESCRIPTION = range(4)
EDIT_CHOOSE, EDIT_TYPE, EDIT_CATEGORY, EDIT_AMOUNT, EDIT_DESCRIPTION, EDIT_CONFIRM = range(10, 16)

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

    # --- Edit Last Transaction ---
    edit_last_conv = ConversationHandler(
        entry_points=[CommandHandler("edit_last", edit_last_start)],
        states={
            EDIT_CHOOSE: [CallbackQueryHandler(edit_last_choose_field)],
            EDIT_TYPE: [CallbackQueryHandler(edit_last_edit_type)],
            EDIT_CATEGORY: [CallbackQueryHandler(edit_last_edit_category)],
            EDIT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_last_edit_amount)],
            EDIT_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_last_edit_description)],
        },
        fallbacks=[CommandHandler("cancel", cancel_add)],
    )
    app.add_handler(edit_last_conv)

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