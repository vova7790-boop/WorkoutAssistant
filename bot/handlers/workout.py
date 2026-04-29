from telegram import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputFile,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bot.data import WORKOUT_DATA
from bot.persistence.db import get_progression, log_workout
from bot.states import State
from bot.utils import (
    format_exercise_caption,
    format_set_in_progress,
    random_motivation,
)


def _exercise_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("▶️ Начать подход", callback_data="start_set"),
            InlineKeyboardButton("⏭ Пропустить упражнение", callback_data="skip_exercise"),
        ]
    ])


def _set_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Готово", callback_data="done")]
    ])


def _menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Вернуться в меню", callback_data="menu")]
    ])


async def show_exercise(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> int:
    user_id = context.user_data["user_id"]
    day_key = context.user_data["day_key"]
    ex_index = context.user_data["exercise_index"]
    day = WORKOUT_DATA[day_key]
    exercises = day["exercises"]

    if ex_index >= len(exercises):
        return await _finish_workout(context, chat_id)

    exercise = exercises[ex_index]
    set_index = context.user_data.get("set_index", 0)
    extra_reps, extra_seconds = await get_progression(user_id, day_key, exercise["name"])

    caption = format_exercise_caption(
        exercise,
        set_num=set_index + 1,
        total_sets=exercise["sets"],
        extra_reps=extra_reps,
        extra_seconds=extra_seconds,
    )

    prev_msg_id = context.user_data.get("exercise_message_id")
    if prev_msg_id:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=prev_msg_id)
        except Exception:
            pass

    with open(exercise["image"], "rb") as photo_file:
        msg = await context.bot.send_photo(
            chat_id=chat_id,
            photo=InputFile(photo_file),
            caption=caption,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=_exercise_keyboard(),
        )

    context.user_data["exercise_message_id"] = msg.message_id
    return State.EXERCISE_INTRO


async def show_current_set(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> int:
    user_id = context.user_data["user_id"]
    day_key = context.user_data["day_key"]
    ex_index = context.user_data["exercise_index"]
    day = WORKOUT_DATA[day_key]
    exercises = day["exercises"]

    if ex_index >= len(exercises):
        return await _finish_workout(context, chat_id)

    exercise = exercises[ex_index]
    set_index = context.user_data.get("set_index", 0)

    if set_index >= exercise["sets"]:
        context.user_data["exercise_index"] = ex_index + 1
        context.user_data["set_index"] = 0
        return await show_exercise(context, chat_id)

    extra_reps, extra_seconds = await get_progression(user_id, day_key, exercise["name"])

    text = format_set_in_progress(
        exercise,
        set_num=set_index + 1,
        total_sets=exercise["sets"],
        extra_reps=extra_reps,
        extra_seconds=extra_seconds,
    )

    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=_set_keyboard(),
    )
    return State.SET_IN_PROGRESS


async def start_set_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query: CallbackQuery = update.callback_query
    await query.answer()

    user_id = context.user_data["user_id"]
    day_key = context.user_data["day_key"]
    ex_index = context.user_data["exercise_index"]
    set_index = context.user_data.get("set_index", 0)
    exercise = WORKOUT_DATA[day_key]["exercises"][ex_index]

    extra_reps, extra_seconds = await get_progression(user_id, day_key, exercise["name"])

    text = format_set_in_progress(
        exercise,
        set_num=set_index + 1,
        total_sets=exercise["sets"],
        extra_reps=extra_reps,
        extra_seconds=extra_seconds,
    )

    await query.edit_message_caption(
        caption=text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=_set_keyboard(),
    )
    return State.SET_IN_PROGRESS


async def done_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query: CallbackQuery = update.callback_query
    await query.answer()

    from bot.handlers.timer import start_rest_timer

    chat_id = query.message.chat_id
    day_key = context.user_data["day_key"]
    ex_index = context.user_data["exercise_index"]
    set_index = context.user_data.get("set_index", 0)
    exercise = WORKOUT_DATA[day_key]["exercises"][ex_index]

    context.user_data["set_index"] = set_index + 1

    await query.edit_message_reply_markup(reply_markup=None)

    if context.user_data["set_index"] < exercise["sets"]:
        rest_secs = WORKOUT_DATA[day_key]["rest_seconds"]
        await start_rest_timer(context, chat_id, rest_secs)
        return State.RESTING
    else:
        context.user_data["exercise_index"] = ex_index + 1
        context.user_data["set_index"] = 0
        return await show_exercise(context, chat_id)


async def skip_rest_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query: CallbackQuery = update.callback_query
    await query.answer()

    from bot.handlers.timer import cancel_timer

    chat_id = query.message.chat_id
    await cancel_timer(context)

    try:
        await query.edit_message_text("⏭ Отдых пропущен.")
    except Exception:
        pass

    return await show_current_set(context, chat_id)


async def skip_exercise_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query: CallbackQuery = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    ex_index = context.user_data["exercise_index"]
    context.user_data.setdefault("skipped", []).append(ex_index)
    context.user_data["exercise_index"] = ex_index + 1
    context.user_data["set_index"] = 0

    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception:
        pass

    return await show_exercise(context, chat_id)


async def _finish_workout(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> int:
    user_id = context.user_data["user_id"]
    day_key = context.user_data["day_key"]
    day = WORKOUT_DATA[day_key]
    total = len(day["exercises"])
    skipped = len(context.user_data.get("skipped", []))
    done = total - skipped

    await log_workout(user_id, day_key, done, total)

    motivation = random_motivation()

    text = (
        f"🎉 *Тренировка завершена!*\n\n"
        f"📋 {day['display_name']}\n"
        f"✅ Выполнено упражнений: {done} из {total}\n\n"
        f"{motivation}"
    )

    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=_menu_keyboard(),
    )
    context.user_data.clear()
    return State.WORKOUT_DONE
