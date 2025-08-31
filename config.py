"""
Конфигурация Woolzy Bot
Здесь настраиваются все основные параметры бота
"""

import os
from typing import List, Tuple

# ---------------- ОСНОВНЫЕ НАСТРОЙКИ ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    raise SystemExit("BOT_TOKEN env var is required")

DB_PATH = os.getenv("DB_PATH", "bot_metrics.sqlite3")

# ---------------- ССЫЛКИ (ОБЯЗАТЕЛЬНО ЗАМЕНИТЬ НА РЕАЛЬНЫЕ) ----------------
REVIEW24_LINK = "https://t.me/c/2329306914/1/369"  # 👈 заменить на реальную ссылку
REVIEW48_LINK = "https://t.me/c/2329306914/1/402"  # 👈 заменить на реальную ссылку
GROUP_LINK = "https://t.me/+TpyDg13ExDNjNTJi"  # 👈 заменить на реальную ссылку
GUIDE_LINK = "https://example.com/woolzy-guide.pdf"  # 👈 заменить на PDF
VIDEO_LINK = "https://example.com/video"  # 👈 заменить
SHOP_LINK = "https://kaspi.kz/shop/p/woolzy-wy01-mnogorazovye-vkladyshi-razmer-m-12-sm-4-sht-119074032/?c=710000000&sr=1&qid=bd4723386fa95f635325c25f167f9031&ref=shared_link"  # 👈 заменить

# ---------------- АДМИНЫ ----------------
# Список админов (ID пользователей/чатов Telegram) как строки
# Пример: ["123456789", "987654321"]
ADMIN_IDS: List[str] = [
    "729235371",
    "1031580076",
]

# ---------------- ТАЙМИНГИ СООБЩЕНИЙ (в секундах) ----------------
# формат: (delay_seconds, key)
TIMELINE: List[Tuple[int, str]] = [
    (20, "remind_group"),   # 20 сек после старта
    (35, "reviews"),        # 35 сек после старта  
    (60, "check_in"),       # 1 минута после старта
    # (95, "video"),        # УБРАНО: теперь отправляется через 24 часа после клика на btn_guide
]

# ---------------- ФУНКЦИИ ----------------
def is_admin(user_id: int | None, chat_id: int | None) -> bool:
    """Проверяет, является ли пользователь админом"""
    if not ADMIN_IDS:
        return False
    if user_id is not None and str(user_id) in ADMIN_IDS:
        return True
    if chat_id is not None and str(chat_id) in ADMIN_IDS:
        return True
    return False
