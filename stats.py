"""
Функции статистики Woolzy Bot
Здесь находятся все функции для работы со статистикой
"""

import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List
from config import DB_PATH

# ---------------- ПЕРИОДЫ СТАТИСТИКИ ----------------
STATS_PERIODS: Dict[str, int | None] = {
    "24h": 24 * 3600,
    "7d": 7 * 86400,
    "all": None,
}

# ---------------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ----------------
def utcnow_iso() -> str:
    """Возвращает текущее время в UTC в формате ISO"""
    return datetime.now(timezone.utc).isoformat()

def db_connect() -> sqlite3.Connection:
    """Создает соединение с базой данных"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

def period_cutoff_iso(period_key: str) -> str | None:
    """Возвращает время отсечения для периода в формате ISO"""
    seconds = STATS_PERIODS.get(period_key)
    if seconds is None:
        return None
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=seconds)
    return cutoff.isoformat()

# ---------------- ФУНКЦИИ СТАТИСТИКИ ----------------
def build_stats_text(period_key: str, detailed: bool) -> str:
    """Строит текст статистики для указанного периода"""
    cutoff_iso = period_cutoff_iso(period_key)
    where_clause = ""
    params: List[Any] = []
    if cutoff_iso is not None:
        where_clause = " AND created_at >= ?"
        params.append(cutoff_iso)

    with db_connect() as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM events WHERE type='start'" + where_clause, params)
        total_starts = cur.fetchone()[0] or 0

        cur.execute(
            f"SELECT COUNT(*) FROM events WHERE type='button_click' AND payload='btn_group'" + where_clause,
            params,
        )
        group_clicks = cur.fetchone()[0] or 0

        cur.execute(
            f"SELECT COUNT(*) FROM events WHERE type='button_click' AND payload='btn_kaspi'" + where_clause,
            params,
        )
        kaspi_clicks = cur.fetchone()[0] or 0

        lines: List[str] = []
        header = {
            "24h": "за 24 часа",
            "7d": "за 7 дней",
            "all": "за весь период",
        }.get(period_key, "за период")
        lines.append(f"📊 Статистика {header}")
        lines.append(f"– Стартовали бота: <b>{total_starts}</b>")
        lines.append(f"– Перешли в группу: <b>{group_clicks}</b>")
        lines.append(f"– Кликнули на Kaspi: <b>{kaspi_clicks}</b>")

        if detailed:
            lines.append("")
            lines.append("Последние события (до 50):")

            # Читаем последние события вместе с профилем пользователя
            q = (
                "SELECT e.created_at, e.user_id, e.type, IFNULL(e.payload, ''), "
                "IFNULL(u.first_name,''), IFNULL(u.last_name,''), IFNULL(u.username,''), IFNULL(u.language_code,''), IFNULL(u.is_premium,0), IFNULL(u.is_bot,0) "
                "FROM events e LEFT JOIN users u ON u.user_id = e.user_id"
                + (" WHERE e.created_at >= ?" if cutoff_iso is not None else "")
                + " ORDER BY e.created_at DESC LIMIT 50"
            )
            cur.execute(q, params)
            recent = cur.fetchall()

            def format_time_short(iso_str: str) -> str:
                try:
                    dt = datetime.fromisoformat(iso_str)
                except Exception:
                    return iso_str
                return dt.strftime("%m-%d %H:%M")

            def action_name(ev_type: str, payload: str) -> str:
                if ev_type == "start":
                    return "Старт"
                if ev_type == "button_click":
                    mapping = {
                        "btn_group": "Кнопка: Перейти в группу",
                        "btn_kaspi": "Кнопка: Оформить в Kaspi",
                        "btn_guide": "Кнопка: Сначала посмотрю гайд",
                    }
                    return mapping.get(payload, f"Кнопка: {payload}")
                if ev_type == "message_sent":
                    return f"Отправлено: {payload}"
                return ev_type

            for created_at, uid, etype, payload, first_name, last_name, username, lang, is_premium, is_bot in recent:
                display = first_name
                if last_name:
                    display = f"{display} {last_name}" if display else last_name
                if username:
                    at = f"@{username}"
                    display = f"{display} ({at})" if display else at
                if not display:
                    display = str(uid)
                info_bits = []
                if lang:
                    info_bits.append(lang)
                if is_premium:
                    info_bits.append("premium")
                if is_bot:
                    info_bits.append("bot")
                extra = f" • {'/'.join(info_bits)}" if info_bits else ""
                lines.append(f"{format_time_short(created_at)} • {display}{extra} • {action_name(etype, payload)}")

        return "\n".join(lines)

def get_users_list() -> str:
    """Возвращает список пользователей (до 200)"""
    with db_connect() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT u.user_id, IFNULL(u.first_name,''), IFNULL(u.last_name,''), IFNULL(u.username,''),
                   IFNULL(u.language_code,''), IFNULL(u.is_premium,0), IFNULL(u.is_bot,0),
                   MAX(e.created_at) as last_seen
            FROM users u
            LEFT JOIN events e ON e.user_id = u.user_id
            GROUP BY u.user_id
            ORDER BY last_seen DESC
            LIMIT 200
            """
        )
        rows = cur.fetchall()

    def format_time_short(iso_str: str | None) -> str:
        if not iso_str:
            return "—"
        try:
            dt = datetime.fromisoformat(iso_str)
            return dt.strftime("%m-%d %H:%M")
        except Exception:
            return iso_str

    lines = ["👥 Пользователи (до 200):"]
    for uid, first_name, last_name, username, lang, is_premium, is_bot, last_seen in rows:
        display = first_name
        if last_name:
            display = f"{display} {last_name}" if display else last_name
        if username:
            at = f"@{username}"
            display = f"{display} ({at})" if display else at
        if not display:
            display = str(uid)
        info_bits = []
        if lang:
            info_bits.append(lang)
        if is_premium:
            info_bits.append("premium")
        if is_bot:
            info_bits.append("bot")
        extra = f" • {'/'.join(info_bits)}" if info_bits else ""
        lines.append(f"{format_time_short(last_seen)} • {display}{extra}")

    return "\n".join(lines)

def reset_statistics() -> None:
    """Обнуляет всю статистику (удаляет все события)"""
    with db_connect() as conn:
        conn.execute("DELETE FROM events")
        conn.commit()
