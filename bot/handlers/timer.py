import asyncio

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes


def _skip_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("Пропустить отдых ⏭", callback_data="skip_rest")]])


async def start_rest_timer(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    seconds: int,
) -> None:
    if context.user_data.get("timer_task"):
        context.user_data["timer_task"].cancel()

    msg = await context.bot.send_message(
        chat_id=chat_id,
        text=f"😮‍💨 Отдых: {seconds} сек...",
        reply_markup=_skip_keyboard(),
    )
    context.user_data["timer_message_id"] = msg.message_id

    task = asyncio.create_task(
        _countdown_loop(context, chat_id, msg.message_id, seconds)
    )
    context.user_data["timer_task"] = task


async def _countdown_loop(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    message_id: int,
    seconds: int,
) -> None:
    try:
        elapsed = 0
        interval = 5
        while elapsed < seconds:
            await asyncio.sleep(interval)
            elapsed += interval
            remaining = seconds - elapsed
            if remaining > 0:
                try:
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=f"😮‍💨 Отдых: {remaining} сек...",
                        reply_markup=_skip_keyboard(),
                    )
                except Exception:
                    pass

        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="✅ Отдых завершён! Готов к следующему подходу?",
            )
        except Exception:
            pass

        await _trigger_next_set(context, chat_id)

    except asyncio.CancelledError:
        pass


async def _trigger_next_set(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
) -> None:
    from bot.handlers.workout import show_current_set

    context.user_data["timer_task"] = None
    context.user_data["timer_message_id"] = None
    await show_current_set(context, chat_id)


async def cancel_timer(context: ContextTypes.DEFAULT_TYPE) -> None:
    task = context.user_data.get("timer_task")
    if task and not task.done():
        task.cancel()
    context.user_data["timer_task"] = None
    context.user_data["timer_message_id"] = None
