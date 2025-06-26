import logging
import asyncio
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from config import BOT_TOKEN, ADMIN_IDS
from db import (
    add_order, get_orders, close_order,
    add_escrow, confirm_escrow,
    remove_old_orders
)
from db import get_all_users
from db import save_user
logging.basicConfig(level=logging.INFO)
user_data = {}  # { user_id: {"phone": "...", "username": "..." } }

   

    
# Кнопочное меню
from telegram import KeyboardButton, ReplyKeyboardMarkup

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    if user_id in user_data and "phone" in user_data[user_id]:
        # Телефон уже есть — показываем меню
        await send_main_menu(update, context)
    else:
        # Нет телефона — просим поделиться
        button = KeyboardButton("📱 Поделиться номером", request_contact=True)
        keyboard = ReplyKeyboardMarkup([[button]], one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text("Пожалуйста, поделитесь своим номером телефона:", reply_markup=keyboard)


async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    keyboard = [
        [KeyboardButton("📥 Купить"), KeyboardButton("📤 Продать")],
        [KeyboardButton("📄 Все заявки")]
    ]

    if user_id in ADMIN_IDS:
        keyboard.append([KeyboardButton("🔐 Панель админа")])

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("📋 Главное меню:", reply_markup=reply_markup)

# Обработка текстовых кнопок
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    if text == "📥 Купить":
        await update.message.reply_text("Введите: /buy USDT 1000 Monobank 38.5")

    elif text == "📤 Продать":
        await update.message.reply_text("Введите: /sell USDT 500 Monobank 39.2")

    elif text == "📄 Все заявки":
        await show_orders(update, context)

    elif text == "🔐 Панель админа" and user_id in ADMIN_IDS:
        await show_users(update)

    elif text == "🏠 На головну":
        await start(update, context)

    else:
        await update.message.reply_text("Команда не распознана.")


async def show_users(update: Update):
    users = get_all_users()
    if not users:
        await update.message.reply_text("Нет пользователей.")
        return

    msg = "👤 Список пользователей:\n\n"
    for user_id, username, phone in users:
        msg += f"🆔 {user_id}\n🔸 @{username}\n📞 {phone}\n\n"

    await update.message.reply_text(msg)

# Добавить заявку
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 4:
        await update.message.reply_text("Пример: /buy USDT 1000 Monobank 38.5")
        return
    user = update.effective_user
    add_order(user.username, user.id, "buy", args[0], float(args[1]), args[2], float(args[3]))
    await update.message.reply_text("✅ Заявка на покупку добавлена")

async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 4:
        await update.message.reply_text("Пример: /sell USDT 500 PrivatBank 38.5")
        return
    user = update.effective_user
    add_order(user.username, user.id, "sell", args[0], float(args[1]), args[2], float(args[3]))
    await update.message.reply_text("✅ Заявка на продажу добавлена")

# Отобразить заявки
async def show_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    orders = get_orders()
    if not orders:
        await update.message.reply_text("Заявок нет.")
        return
    for o in orders:
        keyboard = [
            [
                InlineKeyboardButton("✅ Принять", callback_data=f"accept:{o[0]}"),
                InlineKeyboardButton("❌ Закрыть", callback_data=f"close:{o[0]}")
            ]
        ]
        markup = InlineKeyboardMarkup(keyboard)
        msg = f"#{o[0]} {o[3].upper()} {o[5]} {o[4]} через {o[6]} по {o[7]} грн\n👤 @{o[1]}"
        await update.message.reply_text(msg, reply_markup=markup)

# Обработка нажатий на inline-кнопки
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    data = query.data

    if data.startswith("accept:"):
        order_id = int(data.split(":")[1])
        add_escrow(order_id, buyer_id=user.id, seller_id=None)
        await query.edit_message_text(f"🛡 Сделка #{order_id} начата. Ожидается подтверждение.")

    elif data.startswith("close:"):
        order_id = int(data.split(":")[1])
        close_order(order_id)
        await query.edit_message_text(f"❌ Заявка #{order_id} закрыта.")

# Админ-панель
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Нет доступа.")
        return
    await update.message.reply_text("👨‍💼 Админ-панель:\n- /clear_old — удалить заявки старше 24ч\n- /orders — все заявки")

async def clear_old(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    remove_old_orders()
    await update.message.reply_text("🧹 Старые заявки удалены.")

async def sendphone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from telegram import KeyboardButton, ReplyKeyboardMarkup

    button = KeyboardButton(text="📱 Поделиться номером", request_contact=True)
    keyboard = ReplyKeyboardMarkup([[button]], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Нажми кнопку ниже, чтобы поделиться номером телефона:", reply_markup=keyboard)

async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    user = update.effective_user
    user_id = user.id
    username = user.username or "—"
    phone = contact.phone_number

    save_user(user_id, username, phone)

    await update.message.reply_text("✅ Спасибо! Номер телефона сохранён.")
    await send_main_menu(update, context)


async def userinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ У вас нет доступа к этой команде.")
        return
    if not context.args:
        await update.message.reply_text("Использование: /userinfo <user_id>")
        return
    try:
        uid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Некорректный user_id.")
        return
    data = user_data.get(uid)
    if not data:
        await update.message.reply_text("Нет данных о пользователе.")
        return
    await update.message.reply_text(f"Номер телефона пользователя: {data.get('phone', 'неизвестен')}")

# Запуск
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("sendphone", sendphone))
app.add_handler(MessageHandler(filters.CONTACT, contact_handler))

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("buy", buy))
app.add_handler(CommandHandler("sell", sell))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("clear_old", clear_old))
app.add_handler(CommandHandler("orders", show_orders))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))
app.add_handler(CallbackQueryHandler(handle_callback))
app.add_handler(CommandHandler("userinfo", userinfo))

# Фоновая очистка
async def cleaner_callback(context: ContextTypes.DEFAULT_TYPE):
    remove_old_orders()

app.job_queue.run_repeating(cleaner_callback, interval=3600, first=10)
if __name__ == "__main__":
    app.run_polling()
