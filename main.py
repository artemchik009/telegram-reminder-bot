import os
import asyncio
import sqlite3
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- Конфигурация ---
TOKEN = os.getenv("TOKEN")
BOT_NAME = os.getenv("BOT_NAME", "tvoyanapominalka_bot")
DB_FILE = "reminders.db"

if not TOKEN:
    print("ERROR: TOKEN environment variable is not set. Set TOKEN in Render (or .env) and restart.")
    raise SystemExit(1)

# --- Инициализация базы данных ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    text TEXT,
                    remind_time TEXT
                )""")
    conn.commit()
    conn.close()

# --- Добавление напоминания ---
def add_reminder(chat_id, text, remind_time):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO reminders (chat_id, text, remind_time) VALUES (?, ?, ?)",
              (chat_id, text, remind_time.isoformat()))
    conn.commit()
    conn.close()

# --- Получение всех напоминаний пользователя ---
def get_user_reminders(chat_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, text, remind_time FROM reminders WHERE chat_id=?", (chat_id,))
    rows = c.fetchall()
    conn.close()
    return rows

# --- Получение всех напоминаний (для проверки) ---
def get_all_reminders():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, chat_id, text, remind_time FROM reminders")
    rows = c.fetchall()
    conn.close()
    return rows

# --- Удаление напоминания ---
def delete_reminder(reminder_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM reminders WHERE id=?", (reminder_id,))
    conn.commit()
    conn.close()

# --- Команда /start ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        f"Привет! Я @{BOT_NAME} — твоя простая напоминалка.\n\n"
        "Команды:\n"
        "/remind <время> <текст> — установить напоминание (пример: /remind 10m выпить воду или /remind 18:30 позвонить)\n"
        "/list — показать активные напоминания\n"
        "/cancel <id> — удалить напоминание по ID\n"
    )
    await update.message.reply_text(msg)

# --- Команда /remind ---
async def remind_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Используй формат: /remind <время> <текст>\nПример: /remind 10m выпить воду")
        return

    time_str = context.args[0]
    text = " ".join(context.args[1:])

    try:
        # Пример: "10m" или "18:30"
        if time_str.endswith("m") and time_str[:-1].isdigit():
            minutes = int(time_str[:-1])
            remind_time = datetime.now() + timedelta(minutes=minutes)
        else:
            target_time = datetime.strptime(time_str, "%H:%M").time()
            now = datetime.now()
            remind_time = datetime.combine(now.date(), target_time)
            if remind_time < now:
                remind_time += timedelta(days=1)
    except Exception:
        await update.message.reply_text("Неправильный формат времени. Используй '10m' или 'HH:MM' (например 18:30).")
        return

    add_reminder(update.effective_chat.id, text, remind_time)
    await update.message.reply_text(f"✅ Напоминание установлено на {remind_time.strftime('%H:%M %d.%m.%Y')} — '{text}'")

# --- Команда /list ---
async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reminders = get_user_reminders(update.effective_chat.id)
    if not reminders:
        await update.message.reply_text("🔹 У тебя нет активных напоминаний.")
        return

    msg_lines = ["📅 Твои активные напоминания:\n"]
    for r in reminders:
        reminder_id, text, remind_time = r
        try:
            time_str = datetime.fromisoformat(remind_time).strftime("%H:%M %d.%m.%Y")
        except Exception:
            time_str = remind_time
        msg_lines.append(f"🆔 {reminder_id}: {text} — ⏰ {time_str}")
    await update.message.reply_text("\n".join(msg_lines))

# --- Команда /cancel ---
async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.message.reply_text("Используй формат: /cancel <id>")
        return

    reminder_id = int(context.args[0])
    # Проверим, принадлежит ли напоминание этому чату
    user_reminders = [r[0] for r in get_user_reminders(update.effective_chat.id)]
    if reminder_id not in user_reminders:
        await update.message.reply_text("Напоминание с таким ID не найдено у тебя.")
        return

    delete_reminder(reminder_id)
    await update.message.reply_text(f"❌ Напоминание #{reminder_id} удалено.")

# --- Фоновая проверка напоминаний ---
async def reminder_checker(app):
    await asyncio.sleep(1)  # дать время на старт
    while True:
        reminders = get_all_reminders()
        now = datetime.now()
        for r in reminders:
            reminder_id, chat_id, text, remind_time_str = r
            try:
                remind_time = datetime.fromisoformat(remind_time_str)
            except Exception:
                # если парсинг не удался — просто удалим некорректную запись
                delete_reminder(reminder_id)
                continue
            if now >= remind_time:
                try:
                    await app.bot.send_message(chat_id=chat_id, text=f"🔔 Напоминание: {text}")
                except Exception as e:
                    print("Ошибка отправки:", e)
                delete_reminder(reminder_id)
        await asyncio.sleep(5)

# --- Запуск приложения ---
async def main():
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("remind", remind_command))
    app.add_handler(CommandHandler("list", list_command))
    app.add_handler(CommandHandler("cancel", cancel_command))

    # запускаем фоновую задачу проверки напоминаний
    asyncio.create_task(reminder_checker(app))

    print("🤖 Бот запущен и готов к работе.")
    await app.run_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError:
        # Если цикл уже запущен (редкие окружения), используем его
        loop = asyncio.get_event_loop()
        loop.create_task(main())
        loop.run_forever()