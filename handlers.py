from telegram import Update
from telegram.ext import ContextTypes
from db import SessionLocal
from models import User
from lang import get_text
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from models import Transaction
from decimal import Decimal
from sqlalchemy import func
from telegram.ext import CommandHandler
import matplotlib.pyplot as plt
import io
from telegram import ReplyKeyboardMarkup


from telegram import ReplyKeyboardMarkup

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = SessionLocal()
    telegram_id = update.effective_user.id
    name = update.effective_user.first_name
    lang_code = update.effective_user.language_code[:2]

    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        user = User(telegram_id=telegram_id, name=name, lang=lang_code)
        session.add(user)
        session.commit()
    lang = user.lang or "en"

    keyboard = [
        [get_text(lang, "btn_add"), get_text(lang, "btn_balance")],
        [get_text(lang, "btn_report"), get_text(lang, "btn_lang")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(get_text(lang, "start"), reply_markup=reply_markup)
    session.close()

from telegram.ext import ConversationHandler

async def button_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.effective_user.id)
    text = update.message.text

    if text == get_text(lang, "btn_add"):
        # Автоматически запускаем сценарий через команду /add
        await update.message.chat.send_message("/add")
        return

    elif text == get_text(lang, "btn_balance"):
        return await balance_handler(update, context)

    elif text == get_text(lang, "btn_report"):
        return await report_handler(update, context)

    elif text == get_text(lang, "btn_lang"):
        return await lang_handler(update, context)

    else:
        await update.message.reply_text(get_text(lang, "unknown_command"))




from telegram.ext import ConversationHandler

AMOUNT, TYPE, CATEGORY, DESCRIPTION = range(4)

user_data = {}  # временное хранилище

async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.effective_user.id)
    keyboard = [
        [InlineKeyboardButton(get_text(lang, "income"), callback_data="income"),
         InlineKeyboardButton(get_text(lang, "expense"), callback_data="expense")]
    ]
    await update.message.reply_text(get_text(lang, "choose_type"), reply_markup=InlineKeyboardMarkup(keyboard))
    return TYPE

async def add_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("add_type called", update.callback_query.data)
    await update.callback_query.answer()
    context.user_data["type"] = update.callback_query.data
    lang = get_lang(update.effective_user.id)
    if context.user_data["type"] == "income":
        keyboard = [
            [InlineKeyboardButton(get_text(lang, "salary"), callback_data="salary")],
            [InlineKeyboardButton(get_text(lang, "bonus"), callback_data="bonus")],
            [InlineKeyboardButton(get_text(lang, "gift"), callback_data="gift")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton(get_text(lang, "food"), callback_data="food")],
            [InlineKeyboardButton(get_text(lang, "transport"), callback_data="transport")],
            [InlineKeyboardButton(get_text(lang, "rent"), callback_data="rent")]
        ]
    await update.callback_query.message.reply_text(get_text(lang, "choose_category"), reply_markup=InlineKeyboardMarkup(keyboard))
    return CATEGORY

async def add_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    context.user_data["category"] = update.callback_query.data
    lang = get_lang(update.effective_user.id)
    await update.callback_query.message.reply_text(get_text(lang, "add_amount"))
    return AMOUNT

async def add_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = Decimal(update.message.text.replace(",", "."))
        context.user_data["amount"] = amount
    except Exception:
        await update.message.reply_text("⚠️ Введите корректную сумму, например: 123.45")
        return AMOUNT
    lang = get_lang(update.effective_user.id)
    await update.message.reply_text(get_text(lang, "add_description"))
    return DESCRIPTION

async def add_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    description = update.message.text
    context.user_data["description"] = description
    session = SessionLocal()
    telegram_id = update.effective_user.id
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    txn = Transaction(
        user_id=user.id,
        amount=context.user_data["amount"],
        type=context.user_data["type"],
        category=context.user_data["category"],
        description=description,
    )
    session.add(txn)
    session.commit()
    session.close()
    lang = get_lang(update.effective_user.id)
    await update.message.reply_text(get_text(lang, "saved"))
    return ConversationHandler.END

async def cancel_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Добавление отменено.")
    return ConversationHandler.END

# вспомогательная функция
def get_lang(user_id: int):
    session = SessionLocal()
    user = session.query(User).filter_by(telegram_id=user_id).first()
    session.close()
    return user.lang if user else "en"

# /balance
async def balance_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = SessionLocal()
    telegram_id = update.effective_user.id
    user = session.query(User).filter_by(telegram_id=telegram_id).first()

    income_sum = session.query(func.sum(Transaction.amount)) \
        .filter(Transaction.user_id == user.id, Transaction.type == "income").scalar() or 0
    expense_sum = session.query(func.sum(Transaction.amount)) \
        .filter(Transaction.user_id == user.id, Transaction.type == "expense").scalar() or 0

    balance = income_sum - expense_sum
    session.close()

    text = (
        f"💵 Доход: {income_sum:.2f}\n"
        f"💸 Расход: {expense_sum:.2f}\n"
        f"📊 Баланс: {balance:.2f}"
    )
    await update.message.reply_text(text)

# /report (pie chart по категориям)
async def report_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = SessionLocal()
    telegram_id = update.effective_user.id
    user = session.query(User).filter_by(telegram_id=telegram_id).first()

    data = session.query(Transaction.category, func.sum(Transaction.amount)) \
        .filter(Transaction.user_id == user.id, Transaction.type == "expense") \
        .group_by(Transaction.category).all()
    session.close()

    if not data:
        await update.message.reply_text("Нет расходов для построения отчёта.")
        return

    labels, values = zip(*data)

    fig, ax = plt.subplots()
    ax.pie(values, labels=labels, autopct='%1.1f%%')
    ax.set_title("Расходы по категориям")

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    await update.message.reply_photo(buf)
    buf.close()

async def lang_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="ru")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="en")],
        [InlineKeyboardButton("🇹🇯 Тоҷикӣ", callback_data="tg")]
    ]
    await update.message.reply_text(
        "🌍 Выберите язык интерфейса:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def lang_set(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_code = update.callback_query.data
    telegram_id = update.effective_user.id

    session = SessionLocal()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if user:
        user.lang = lang_code
        session.commit()
    session.close()

    await update.callback_query.message.reply_text(get_text(lang_code, "language_changed"))

    # Обновляем меню на выбранном языке
    keyboard = [
        [get_text(lang_code, "btn_add"), get_text(lang_code, "btn_balance")],
        [get_text(lang_code, "btn_report"), get_text(lang_code, "btn_lang")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.callback_query.message.reply_text(get_text(lang_code, "start"), reply_markup=reply_markup)
