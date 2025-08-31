"""
Настройки кнопок Woolzy Bot
Здесь настраиваются все кнопки для сообщений
"""

from typing import Dict, List, Tuple
from telegram import InlineKeyboardButton
from config import GROUP_LINK, SHOP_LINK, VIDEO_LINK, REVIEW24_LINK, REVIEW48_LINK

# ---------------- БАЗОВЫЕ НАБОРЫ КНОПОК ----------------
BUTTON_SETS: Dict[str, List[List[Tuple[str, str]]]] = {
    "welcome": [
        [("Да! Хочу в группу", "btn_group")],
        [("Сначала посмотрю гайд", "btn_guide")],
    ],
}

# ---------------- СПЕЦИАЛЬНЫЕ КНОПКИ ДЛЯ СООБЩЕНИЙ ----------------
def get_special_buttons(key: str) -> List[List[InlineKeyboardButton]]:
    """Возвращает специальные кнопки для конкретного сообщения"""
    rows: List[List[InlineKeyboardButton]] = []
    
    if key == "remind_group":
        # Кнопка перейти в группу (callback для отслеживания)
        rows.append([InlineKeyboardButton(text="Перейти в группу", callback_data="btn_group")])
    
    elif key == "reviews":
        # Кнопка перейти в группу с отзывами
        rows.append([InlineKeyboardButton(text="Перейти в группу", callback_data="btn_group")])
    
    elif key == "check_in":
        # Кнопки: Kaspi (callback), отзывы 24/48 (URL)
        rows.append([InlineKeyboardButton(text="Попробуй сама 💜", callback_data="btn_kaspi")])
        rows.append([
            InlineKeyboardButton(text="Отзыв 24 часа", url=REVIEW24_LINK),
            InlineKeyboardButton(text="Отзыв 48 часов", url=REVIEW48_LINK),
        ])
    
    elif key == "video":
        # Кнопки: видео (URL), группа (callback)
        rows.append([InlineKeyboardButton(text="Смотреть видео", url=VIDEO_LINK)])
        rows.append([InlineKeyboardButton(text="Перейти в группу", callback_data="btn_group")])
    
    elif key == "offer":
        # Заказ в Kaspi через callback для отслеживания
        rows.append([InlineKeyboardButton(text="Оформить в Kaspi", callback_data="btn_kaspi")])
    
    return rows
