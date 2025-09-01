from typing import List, Tuple

# ---------------- ТАЙМИНГИ СООБЩЕНИЙ (в секундах) ----------------
# формат: (delay_seconds, key)
TIMELINE: List[Tuple[int, str]] = [
    (30, "remind_group"),       # 30 секунд после старта
    (300, "reviews"),           # 5 минут после старта  
    (3600, "check_in"),         # 1 час после старта
    (86400, "offer"),           # 24 часа после старта
]