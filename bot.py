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

logging.basicConfig(level=logging.INFO)

# Кнопочное меню
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("📥 Купить"), KeyboardButton("📤 Продать")],
        [KeyboardButton("📄 Все заявки")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Добро пожаловать! Выберите действие:", reply_markup=reply_markup)

# Обработка текстовых кнопок
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "📥 Купить":
        await update.message.reply_text("Используй /buy USDT 1000 Monobank 38.5")
    elif text == "📤 Продать":
        await update.message.reply_text("Используй /sell USDT 500 PrivatBank 39.2")
    elif text == "📄 Все заявки":
        await show_orders(update, context)

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

# Запуск
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("buy", buy))
app.add_handler(CommandHandler("sell", sell))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("clear_old", clear_old))
app.add_handler(CommandHandler("orders", show_orders))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))
app.add_handler(CallbackQueryHandler(handle_callback))

# Фоновая очистка
async def cleaner_callback(context: ContextTypes.DEFAULT_TYPE):
    remove_old_orders()

app.job_queue.run_repeating(cleaner_callback, interval=3600, first=10)
if __name__ == "__main__":
    app.run_polling()
