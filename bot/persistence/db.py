import json
from datetime import date, timedelta
from pathlib import Path

import aiosqlite

from bot.config import DB_PATH


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS workout_log (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id         INTEGER NOT NULL,
                day_key         TEXT NOT NULL,
                completed_at    TEXT NOT NULL,
                exercises_done  INTEGER NOT NULL,
                exercises_total INTEGER NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS progression (
                user_id        INTEGER NOT NULL,
                day_key        TEXT NOT NULL,
                exercise_name  TEXT NOT NULL,
                extra_reps     INTEGER NOT NULL DEFAULT 0,
                extra_seconds  INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (user_id, day_key, exercise_name)
            )
        """)
        await db.commit()


async def log_workout(
    user_id: int,
    day_key: str,
    exercises_done: int,
    exercises_total: int,
) -> None:
    today = date.today().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO workout_log (user_id, day_key, completed_at, exercises_done, exercises_total) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, day_key, today, exercises_done, exercises_total),
        )
        await db.commit()


async def get_history(user_id: int, days: int = 7) -> list[dict]:
    since = (date.today() - timedelta(days=days - 1)).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT day_key, completed_at FROM workout_log "
            "WHERE user_id = ? AND completed_at >= ? ORDER BY completed_at DESC",
            (user_id, since),
        ) as cursor:
            rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def get_streak(user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT DISTINCT completed_at FROM workout_log WHERE user_id = ? ORDER BY completed_at DESC",
            (user_id,),
        ) as cursor:
            rows = await cursor.fetchall()

    if not rows:
        return 0

    streak = 0
    check_date = date.today()
    dates = {row["completed_at"] for row in rows}

    while check_date.isoformat() in dates:
        streak += 1
        check_date -= timedelta(days=1)

    return streak


async def get_progression(user_id: int, day_key: str, exercise_name: str) -> tuple[int, int]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT extra_reps, extra_seconds FROM progression "
            "WHERE user_id = ? AND day_key = ? AND exercise_name = ?",
            (user_id, day_key, exercise_name),
        ) as cursor:
            row = await cursor.fetchone()
    if row:
        return row["extra_reps"], row["extra_seconds"]
    return 0, 0


async def set_progression(
    user_id: int,
    day_key: str,
    exercise_name: str,
    extra_reps: int,
    extra_seconds: int,
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO progression (user_id, day_key, exercise_name, extra_reps, extra_seconds) "
            "VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(user_id, day_key, exercise_name) DO UPDATE SET "
            "extra_reps = excluded.extra_reps, extra_seconds = excluded.extra_seconds",
            (user_id, day_key, exercise_name, extra_reps, extra_seconds),
        )
        await db.commit()
