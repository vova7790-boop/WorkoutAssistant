from telegram import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bot.data import DAY_LABELS, WORKOUT_DATA
from bot.persistence.db import get_progression, set_progression
from bot.states import State
from bot.utils import parse_progression_input


def _prog_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏋️ Одно упражнение", callback_data="prog_one")],
        [InlineKeyboardButton("📋 Все упражнения сразу", callback_data="prog_all")],
        [InlineKeyboardButton("🏠 Назад в меню", callback_data="menu")],
    ])


def _day_select_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(DAY_LABELS[k], callback_data=f"prog_day:{k}")]
        for k in DAY_LABELS
    ]
    rows.append([InlineKeyboardButton("◀️ Назад", callback_data="prog_back_main")])
    return InlineKeyboardMarkup(rows)


def _exercise_select_keyboard(day_key: str) -> InlineKeyboardMarkup:
    exercises = WORKOUT_DATA[day_key]["exercises"]
    rows = [
        [InlineKeyboardButton(ex["name"], callback_data=f"prog_ex:{i}")]
        for i, ex in enumerate(exercises)
    ]
    rows.append([InlineKeyboardButton("◀️ Назад", callback_data="prog_back_day")])
    return InlineKeyboardMarkup(rows)


async def progression_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query: CallbackQuery = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "⚙️ *Настройка прогрессии*\n\n"
        "Здесь ты можешь увеличить количество повторений или секунд удержания для упражнений.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=_prog_main_keyboard(),
    )
    context.user_data.pop("prog_mode", None)
    context.user_data.pop("prog_day_key", None)
    context.user_data.pop("prog_ex_index", None)
    return State.PROG_MENU


async def prog_one_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query: CallbackQuery = update.callback_query
    await query.answer()

    context.user_data["prog_mode"] = "one"
    await query.edit_message_text(
        "Выбери день тренировки:",
        reply_markup=_day_select_keyboard(),
    )
    return State.PROG_SELECT_DAY


async def prog_all_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query: CallbackQuery = update.callback_query
    await query.answer()

    context.user_data["prog_mode"] = "all"
    await query.edit_message_text(
        "Выбери день тренировки для изменения *всех* упражнений:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=_day_select_keyboard(),
    )
    return State.PROG_SELECT_DAY


async def prog_day_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query: CallbackQuery = update.callback_query
    await query.answer()

    day_key = query.data.split(":")[1]
    context.user_data["prog_day_key"] = day_key
    day = WORKOUT_DATA[day_key]

    if context.user_data.get("prog_mode") == "all":
        exercises = day["exercises"]
        user_id = update.effective_user.id
        lines = []
        for ex in exercises:
            er, es = await get_progression(user_id, day_key, ex["name"])
            if ex["reps"] > 0:
                base = ex["reps"]
                current = base + er
                lines.append(f"• {ex['name']}: {current} повт.")
            else:
                base = ex["duration"]
                current = base + es
                lines.append(f"• {ex['name']}: {current} сек")

        exercise_list = "\n".join(lines)
        await query.edit_message_text(
            f"📋 *{day['display_name']}*\n\n"
            f"Текущие значения:\n{exercise_list}\n\n"
            f"Введи число (например, `5`) или процент (например, `20%`) "
            f"для увеличения *всех* упражнений:",
            parse_mode=ParseMode.MARKDOWN,
        )
        return State.PROG_INPUT_ALL

    else:
        await query.edit_message_text(
            f"Выбери упражнение из *{day['display_name']}*:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=_exercise_select_keyboard(day_key),
        )
        return State.PROG_SELECT_EX


async def prog_ex_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query: CallbackQuery = update.callback_query
    await query.answer()

    ex_index = int(query.data.split(":")[1])
    context.user_data["prog_ex_index"] = ex_index

    day_key = context.user_data["prog_day_key"]
    exercise = WORKOUT_DATA[day_key]["exercises"][ex_index]
    user_id = update.effective_user.id
    extra_reps, extra_seconds = await get_progression(user_id, day_key, exercise["name"])

    if exercise["reps"] > 0:
        base = exercise["reps"]
        current = base + extra_reps
        unit = "повт."
    else:
        base = exercise["duration"]
        current = base + extra_seconds
        unit = "сек"

    await query.edit_message_text(
        f"🏋️ *{exercise['name']}*\n"
        f"Базовое значение: {base} {unit}\n"
        f"Текущее значение: {current} {unit}\n\n"
        f"Введи число (например, `5`) или процент (например, `20%`) для увеличения:",
        parse_mode=ParseMode.MARKDOWN,
    )
    return State.PROG_INPUT_ONE


async def prog_input_one_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    day_key = context.user_data.get("prog_day_key")
    ex_index = context.user_data.get("prog_ex_index")

    if day_key is None or ex_index is None:
        await update.message.reply_text("Ошибка сессии. Начни заново /start")
        return State.DAY_MENU

    exercise = WORKOUT_DATA[day_key]["exercises"][ex_index]
    is_reps = exercise["reps"] > 0
    base_value = exercise["reps"] if is_reps else exercise["duration"]
    unit = "повт." if is_reps else "сек"

    delta = parse_progression_input(update.message.text, base_value)
    if delta is None:
        await update.message.reply_text(
            "❌ Неверный формат. Введи целое число (например, `5`) или процент (например, `20%`).\n"
            "Значение должно быть положительным.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return State.PROG_INPUT_ONE

    old_er, old_es = await get_progression(user_id, day_key, exercise["name"])
    if is_reps:
        new_er = old_er + delta
        new_es = old_es
    else:
        new_er = old_er
        new_es = old_es + delta

    await set_progression(user_id, day_key, exercise["name"], new_er, new_es)

    new_val = (exercise["reps"] + new_er) if is_reps else (exercise["duration"] + new_es)
    await update.message.reply_text(
        f"✅ Обновлено!\n"
        f"*{exercise['name']}*: теперь {new_val} {unit} (+{delta})",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⚙️ Ещё изменения", callback_data="progression")],
            [InlineKeyboardButton("🏠 В меню", callback_data="menu")],
        ]),
    )
    return State.PROG_MENU


async def prog_input_all_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    day_key = context.user_data.get("prog_day_key")

    if day_key is None:
        await update.message.reply_text("Ошибка сессии. Начни заново /start")
        return State.DAY_MENU

    exercises = WORKOUT_DATA[day_key]["exercises"]
    text = update.message.text

    updated_lines = []
    errors = []

    for exercise in exercises:
        is_reps = exercise["reps"] > 0
        base_value = exercise["reps"] if is_reps else exercise["duration"]
        unit = "повт." if is_reps else "сек"

        delta = parse_progression_input(text, base_value)
        if delta is None:
            errors.append(exercise["name"])
            continue

        old_er, old_es = await get_progression(user_id, day_key, exercise["name"])
        if is_reps:
            new_er = old_er + delta
            new_es = old_es
        else:
            new_er = old_er
            new_es = old_es + delta

        await set_progression(user_id, day_key, exercise["name"], new_er, new_es)
        new_val = (exercise["reps"] + new_er) if is_reps else (exercise["duration"] + new_es)
        updated_lines.append(f"• {exercise['name']}: {new_val} {unit} (+{delta})")

    if errors and not updated_lines:
        await update.message.reply_text(
            "❌ Неверный формат. Введи целое число (например, `5`) или процент (например, `20%`).",
            parse_mode=ParseMode.MARKDOWN,
        )
        return State.PROG_INPUT_ALL

    result = "\n".join(updated_lines)
    await update.message.reply_text(
        f"✅ *Прогрессия обновлена для всех упражнений:*\n\n{result}",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⚙️ Ещё изменения", callback_data="progression")],
            [InlineKeyboardButton("🏠 В меню", callback_data="menu")],
        ]),
    )
    return State.PROG_MENU


async def prog_back_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query: CallbackQuery = update.callback_query
    await query.answer()
    return await progression_entry(update, context)


async def prog_back_day(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query: CallbackQuery = update.callback_query
    await query.answer()

    mode = context.user_data.get("prog_mode", "one")
    if mode == "one":
        await query.edit_message_text(
            "Выбери день тренировки:",
            reply_markup=_day_select_keyboard(),
        )
    else:
        await query.edit_message_text(
            "Выбери день тренировки для изменения *всех* упражнений:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=_day_select_keyboard(),
        )
    return State.PROG_SELECT_DAY
