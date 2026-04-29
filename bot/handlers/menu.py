from datetime import date, timedelta

from telegram import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bot.data import DAY_KEY_MAP, DAY_LABELS, REST_DAYS, WORKOUT_DATA
from bot.handlers.timer import cancel_timer
from bot.handlers.workout import show_exercise
from bot.persistence.db import get_history, get_streak
from bot.states import State


def _main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Понедельник 💪", callback_data="day:monday"),
            InlineKeyboardButton("Вторник 🦾", callback_data="day:tuesday"),
        ],
        [
            InlineKeyboardButton("Четверг 🔥", callback_data="day:thursday"),
            InlineKeyboardButton("Суббота ⚡", callback_data="day:saturday"),
        ],
        [InlineKeyboardButton("📅 Тренировка сегодня", callback_data="today")],
        [
            InlineKeyboardButton("📊 Статистика", callback_data="stats"),
            InlineKeyboardButton("⚙️ Прогрессия", callback_data="progression"),
        ],
    ])


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await cancel_timer(context)
    context.user_data.clear()

    text = (
        "👋 *Привет! Я твой тренер.*\n\n"
        "Выбери день тренировки или нажми «Тренировка сегодня» для автоматического выбора:"
    )
    keyboard = _main_menu_keyboard()

    if update.callback_query:
        query: CallbackQuery = update.callback_query
        await query.answer()
        try:
            await query.edit_message_text(
                text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard
            )
        except Exception:
            await context.bot.send_message(
                query.message.chat_id,
                text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard,
            )
    else:
        await update.message.reply_text(
            text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard
        )

    return State.DAY_MENU


async def today_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query: CallbackQuery = update.callback_query
    await query.answer()

    weekday = date.today().weekday()
    day_key = DAY_KEY_MAP.get(weekday)

    if day_key is None:
        rest_msg = REST_DAYS.get(weekday, "Сегодня день отдыха. Дай мышцам восстановиться!")
        await query.edit_message_text(
            f"😴 {rest_msg}\n\nВернись в тренировочный день или выбери любой день вручную:",
            reply_markup=_main_menu_keyboard(),
        )
        return State.DAY_MENU

    return await _start_day(query, context, day_key, query.message.chat_id)


async def day_selected_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query: CallbackQuery = update.callback_query
    await query.answer()

    day_key = query.data.split(":")[1]
    return await _start_day(query, context, day_key, query.message.chat_id)


async def _start_day(
    query: CallbackQuery,
    context: ContextTypes.DEFAULT_TYPE,
    day_key: str,
    chat_id: int,
) -> int:
    context.user_data["day_key"] = day_key
    context.user_data["exercise_index"] = 0
    context.user_data["set_index"] = 0
    context.user_data["skipped"] = []
    context.user_data["user_id"] = query.from_user.id
    context.user_data["chat_id"] = chat_id

    day = WORKOUT_DATA[day_key]
    ex_count = len(day["exercises"])

    await query.edit_message_text(
        f"🏋️ *{day['display_name']}*\n"
        f"Упражнений: {ex_count} | Отдых между подходами: {day['rest_seconds']} сек\n\n"
        f"Начинаем! Удачи! 💪"
    )

    return await show_exercise(context, chat_id)


async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query: CallbackQuery = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    history = await get_history(user_id, days=7)
    streak = await get_streak(user_id)

    completed_dates = {row["completed_at"] for row in history}

    lines = []
    for i in range(6, -1, -1):
        d = date.today() - timedelta(days=i)
        weekday = d.weekday()
        day_key = DAY_KEY_MAP.get(weekday)

        if day_key is None:
            day_label = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"][weekday]
            lines.append(f"{day_label} {d.strftime('%d.%m')} — 😴 Отдых")
        else:
            day_label = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"][weekday]
            status = "✅" if d.isoformat() in completed_dates else "❌"
            lines.append(f"{day_label} {d.strftime('%d.%m')} — {status} {DAY_LABELS[day_key]}")

    week_text = "\n".join(lines)
    streak_text = f"🔥 Серия: {streak} {'день' if streak == 1 else 'дней'} подряд" if streak > 0 else "Начни серию — тренируйся сегодня!"

    total_workouts = len(history)

    text = (
        f"📊 *Статистика за последние 7 дней*\n\n"
        f"{week_text}\n\n"
        f"{streak_text}\n"
        f"Всего тренировок за неделю: {total_workouts}"
    )

    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Назад в меню", callback_data="menu")]
        ]),
    )
    return State.STATS_VIEW
