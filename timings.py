from typing import List, Tuple

# ---------------- ТАЙМИНГИ СООБЩЕНИЙ (в секундах) ----------------
# формат: (delay_seconds, key)
TIMELINE: List[Tuple[int, str]] = [
    (20, "remind_group"),   # 20 сек после старта
    (35, "reviews"),        # 35 сек после старта  
    (60, "check_in"),       # 1 минута после старта
    (95, "video"),          # 1.5 минуты после старта
]