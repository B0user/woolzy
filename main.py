"""
Woolzy Bot - Основной файл
Telegram бот для автоматической рассылки сообщений с таймингом
"""

import asyncio
import logging
import os
import sqlite3
from datetime import datetime, timezone
from typing import List

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    AIORateLimiter,
    Application,
    ApplicationBuilder,
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

# Импорты из модулей
from config import BOT_TOKEN, DB_PATH, is_admin, GROUP_LINK, GUIDE_LINK, SHOP_LINK
from timings import TIMELINE
from messages import MESSAGES
from buttons import BUTTON_SETS, get_special_buttons
from stats import utcnow_iso, db_connect, build_stats_text, get_users_list, reset_statistics

# ---------------- БАЗА ДАННЫХ ----------------
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    user_id     INTEGER PRIMARY KEY,
    username    TEXT,
    first_name  TEXT,
    last_name   TEXT,
    language_code TEXT,
    is_premium  INTEGER DEFAULT 0,
    is_bot      INTEGER DEFAULT 0,
    last_start  TEXT
);

CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    type        TEXT NOT NULL,
    payload     TEXT,
    created_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_events_user_time ON events(user_id, created_at);
"""

def db_init() -> None:
    """Инициализация базы данных"""
    with db_connect() as conn:
        conn.executescript(SCHEMA_SQL)

# ---------------- БОТ ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    if not update.effective_user or not update.effective_chat:
        return
    user = update.effective_user
    chat_id = update.effective_chat.id

    with db_connect() as conn:
        # Лёгкая миграция для новых колонок
        try:
            conn.execute("ALTER TABLE users ADD COLUMN language_code TEXT")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE users ADD COLUMN is_premium INTEGER DEFAULT 0")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE users ADD COLUMN is_bot INTEGER DEFAULT 0")
        except Exception:
            pass

        # Сохраняем расширенную информацию о пользователе
        language_code = getattr(user, "language_code", None)
        is_premium = 1 if getattr(user, "is_premium", False) else 0
        is_bot = 1 if getattr(user, "is_bot", False) else 0

        conn.execute(
            """
            INSERT INTO users (user_id, username, first_name, last_name, language_code, is_premium, is_bot, last_start)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username=excluded.username,
                first_name=excluded.first_name,
                last_name=excluded.last_name,
                language_code=excluded.language_code,
                is_premium=excluded.is_premium,
                is_bot=excluded.is_bot,
                last_start=excluded.last_start
            """,
            (
                user.id,
                user.username,
                user.first_name,
                user.last_name,
                language_code,
                is_premium,
                is_bot,
                utcnow_iso(),
            ),
        )
        conn.execute(
            "INSERT INTO events (user_id, type, payload, created_at) VALUES (?, ?, ?, ?)",
            (user.id, "start", None, utcnow_iso()),
        )
        conn.commit()

    # Планируем таймеры
    for delay, key in TIMELINE:
        context.job_queue.run_once(
            send_timed_message,
            when=delay,
            data={"chat_id": chat_id, "user_id": user.id, "key": key},
            name=f"msg_{user.id}_{key}_{delay}",
        )

    # Отправляем приветствие сразу (кроме админов)
    if not is_admin(user.id, chat_id):
        await send_timed_message(
            CallbackContext.from_update(update, context),
            data={"chat_id": chat_id, "user_id": user.id, "key": "welcome"},
        )

async def send_timed_message(context: CallbackContext, data: dict | None = None) -> None:
    """Отправка сообщения по таймеру"""
    if not data:
        data = context.job.data
    chat_id = data.get("chat_id")
    user_id = data.get("user_id")
    key = data.get("key")
    if not chat_id or not key:
        return

    text = MESSAGES.get(key)
    keyboard = None

    # Базовые кнопки из набора
    rows: List[List[InlineKeyboardButton]] = []
    if key in BUTTON_SETS:
        for row in BUTTON_SETS[key]:
            btn_row = [InlineKeyboardButton(text=txt, callback_data=payload) for txt, payload in row]
            rows.append(btn_row)

    # Специальные кнопки для конкретных сообщений
    special_buttons = get_special_buttons(key)
    rows.extend(special_buttons)

    # Админская кнопка статистики (видна только админам)
    if is_admin(user_id, chat_id):
        rows.append([
            InlineKeyboardButton(text="📊 Статистика", callback_data="btn_stats"),
        ])

    if rows:
        keyboard = InlineKeyboardMarkup(rows)

    await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

    if user_id:
        with db_connect() as conn:
            conn.execute(
                "INSERT INTO events (user_id, type, payload, created_at) VALUES (?, ?, ?, ?)",
                (user_id, "message_sent", key, utcnow_iso()),
            )
            conn.commit()

async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатий на кнопки"""
    if not update.callback_query or not update.effective_user:
        return

    query = update.callback_query
    user = update.effective_user
    payload = query.data or ""

    with db_connect() as conn:
        # Обновим профиль пользователя на случай изменений
        try:
            conn.execute("ALTER TABLE users ADD COLUMN language_code TEXT")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE users ADD COLUMN is_premium INTEGER DEFAULT 0")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE users ADD COLUMN is_bot INTEGER DEFAULT 0")
        except Exception:
            pass

        language_code = getattr(user, "language_code", None)
        is_premium = 1 if getattr(user, "is_premium", False) else 0
        is_bot = 1 if getattr(user, "is_bot", False) else 0

        conn.execute(
            """
            INSERT INTO users (user_id, username, first_name, last_name, language_code, is_premium, is_bot, last_start)
            VALUES (?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT last_start FROM users WHERE user_id = ?), NULL))
            ON CONFLICT(user_id) DO UPDATE SET
                username=excluded.username,
                first_name=excluded.first_name,
                last_name=excluded.last_name,
                language_code=excluded.language_code,
                is_premium=excluded.is_premium,
                is_bot=excluded.is_bot
            """,
            (
                user.id,
                user.username,
                user.first_name,
                user.last_name,
                language_code,
                is_premium,
                is_bot,
                user.id,
            ),
        )
        conn.execute(
            "INSERT INTO events (user_id, type, payload, created_at) VALUES (?, ?, ?, ?)",
            (user.id, "button_click", payload, utcnow_iso()),
        )
        conn.commit()

    if payload == "btn_group":
        await query.message.reply_text(f"Вот ссылка на закрытую группу: <a href='{GROUP_LINK}'>Перейти в группу</a>", parse_mode=ParseMode.HTML)
    elif payload == "btn_guide":
        await query.message.reply_text(f"Вот твой PDF-гайд: <a href='{GUIDE_LINK}'>Скачать PDF</a>", parse_mode=ParseMode.HTML)
    elif payload == "btn_kaspi":
        await query.message.reply_text(f"Оформить заказ в Kaspi: <a href='{SHOP_LINK}'>Перейти в Kaspi</a>", parse_mode=ParseMode.HTML)
    elif payload == "btn_stats" or payload.startswith("stats_"):
        if not is_admin(user.id, update.effective_chat.id if update.effective_chat else None):
            await query.answer("Недоступно", show_alert=False)
            return

        if payload == "btn_stats":
            # Показать меню статистики
            kb = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(text="📊 Кратко 24h", callback_data="stats_short_24h"),
                    InlineKeyboardButton(text="📊 Подробно 24h", callback_data="stats_full_24h"),
                ],
                [
                    InlineKeyboardButton(text="📊 Кратко 7d", callback_data="stats_short_7d"),
                    InlineKeyboardButton(text="📊 Подробно 7d", callback_data="stats_full_7d"),
                ],
                [
                    InlineKeyboardButton(text="📊 Кратко всё", callback_data="stats_short_all"),
                    InlineKeyboardButton(text="📊 Подробно всё", callback_data="stats_full_all"),
                ],
                [
                    InlineKeyboardButton(text="👥 Все пользователи", callback_data="stats_users"),
                ],
                [
                    InlineKeyboardButton(text="♻️ Обнулить статистику", callback_data="stats_reset_confirm"),
                ],
            ])
            await query.message.reply_text("Выберите отчёт:", reply_markup=kb)
            return

        if payload == "stats_users":
            # Показать список пользователей
            text = get_users_list()
            await query.message.reply_text(text)
            return

        if payload == "stats_reset_confirm":
            # Кнопки подтверждения сброса
            kb = InlineKeyboardMarkup(
                [[
                    InlineKeyboardButton("Да, обнулить", callback_data="stats_reset_yes"),
                    InlineKeyboardButton("Отмена", callback_data="stats_reset_no"),
                ]]
            )
            await query.message.reply_text("Вы уверены, что хотите обнулить статистику?", reply_markup=kb)
            return

        if payload == "stats_reset_yes":
            # Удаляем все события
            reset_statistics()
            await query.message.reply_text("Статистика обнулена.")
            return

        if payload == "stats_reset_no":
            await query.answer("Отменено", show_alert=False)
            return

        # Формат: stats_{short|full}_{24h|7d|all}
        try:
            _, mode, period = payload.split("_")
        except ValueError:
            await query.answer("Неверный формат", show_alert=False)
            return

        detailed = (mode == "full")
        if period not in ("24h", "7d", "all"):
            await query.answer("Неверный период", show_alert=False)
            return

        text = build_stats_text(period, detailed)
        await query.message.reply_text(text, parse_mode=ParseMode.HTML)
    else:
        await query.answer("Зафиксировал! ✅")

# ---------------- ЗАПУСК ----------------
async def on_startup(app: Application) -> None:
    """Действия при запуске приложения"""
    db_init()
    logging.info("Database initialized at %s", DB_PATH)

def build_app() -> Application:
    """Создание и настройка приложения"""
    rate_limiter = AIORateLimiter()
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .rate_limiter(rate_limiter)
        .concurrent_updates(True)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_button))
    app.post_init = on_startup
    return app

def main() -> None:
    """Главная функция"""
    # Reduce logging verbosity
    logging.basicConfig(
        format="%(asctime)s %(levelname)s: %(message)s",
        level=logging.WARNING,  # Only show warnings and errors
    )
    
    # Suppress verbose library logs
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("telegram.ext").setLevel(logging.WARNING)
    
    # Keep our own logs at INFO level
    logging.getLogger("root").setLevel(logging.INFO)
    
    app = build_app()
    app.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    main()
