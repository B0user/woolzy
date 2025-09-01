"""
Конфигурация Woolzy Bot
Здесь настраиваются все основные параметры бота
"""

import os
from typing import List

# ---------------- ОСНОВНЫЕ НАСТРОЙКИ ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    raise SystemExit("BOT_TOKEN env var is required")

DB_PATH = os.getenv("DB_PATH", "bot_metrics.sqlite3")

# ---------------- ССЫЛКИ (ОБЯЗАТЕЛЬНО ЗАМЕНИТЬ НА РЕАЛЬНЫЕ) ----------------
REVIEW24_LINK = "https://t.me/c/2329306914/1/369"  
REVIEW48_LINK = "https://t.me/c/2329306914/1/402" 
GROUP_LINK = "https://t.me/+TpyDg13ExDNjNTJi"  
GUIDE_LINK = "https://drive.google.com/file/d/1w8QdSr4_QnAGd1yftHll3CtjNwPaYkOQ/view?usp=sharing"  
VIDEO_LINK = "https://example.com/video"  # 👈 заменить
SHOP_LINK = "https://kaspi.kz/shop/p/woolzy-wy01-mnogorazovye-vkladyshi-razmer-m-12-sm-4-sht-119074032/?c=710000000&sr=1&qid=bd4723386fa95f635325c25f167f9031&ref=shared_link" 

# ---------------- АДМИНЫ ----------------
# Список админов (ID пользователей/чатов Telegram) как строки
# Пример: ["123456789", "987654321"]
ADMIN_IDS: List[str] = [
    "1031580076",
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
