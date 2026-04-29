import asyncio
import logging

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot.config import BOT_TOKEN
from bot.handlers.menu import (
    day_selected_callback,
    start_handler,
    stats_handler,
    today_callback,
)
from bot.handlers.progression import (
    prog_all_callback,
    prog_back_day,
    prog_back_main,
    prog_day_callback,
    prog_ex_callback,
    prog_input_all_handler,
    prog_input_one_handler,
    prog_one_callback,
    progression_entry,
)
from bot.handlers.workout import (
    done_callback,
    skip_exercise_callback,
    skip_rest_callback,
    start_set_callback,
)
from bot.persistence.db import init_db
from bot.states import State

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def build_conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CommandHandler("start", start_handler),
            CommandHandler("menu", start_handler),
        ],
        states={
            State.DAY_MENU: [
                CallbackQueryHandler(day_selected_callback, pattern="^day:"),
                CallbackQueryHandler(today_callback, pattern="^today$"),
                CallbackQueryHandler(stats_handler, pattern="^stats$"),
                CallbackQueryHandler(progression_entry, pattern="^progression$"),
                CallbackQueryHandler(start_handler, pattern="^menu$"),
            ],
            State.EXERCISE_INTRO: [
                CallbackQueryHandler(start_set_callback, pattern="^start_set$"),
                CallbackQueryHandler(skip_exercise_callback, pattern="^skip_exercise$"),
            ],
            State.SET_IN_PROGRESS: [
                CallbackQueryHandler(done_callback, pattern="^done$"),
            ],
            State.RESTING: [
                CallbackQueryHandler(skip_rest_callback, pattern="^skip_rest$"),
            ],
            State.WORKOUT_DONE: [
                CallbackQueryHandler(start_handler, pattern="^menu$"),
            ],
            State.STATS_VIEW: [
                CallbackQueryHandler(start_handler, pattern="^menu$"),
            ],
            State.PROG_MENU: [
                CallbackQueryHandler(prog_one_callback, pattern="^prog_one$"),
                CallbackQueryHandler(prog_all_callback, pattern="^prog_all$"),
                CallbackQueryHandler(start_handler, pattern="^menu$"),
                CallbackQueryHandler(progression_entry, pattern="^progression$"),
            ],
            State.PROG_SELECT_DAY: [
                CallbackQueryHandler(prog_day_callback, pattern="^prog_day:"),
                CallbackQueryHandler(prog_back_main, pattern="^prog_back_main$"),
            ],
            State.PROG_SELECT_EX: [
                CallbackQueryHandler(prog_ex_callback, pattern="^prog_ex:"),
                CallbackQueryHandler(prog_back_day, pattern="^prog_back_day$"),
            ],
            State.PROG_INPUT_ONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, prog_input_one_handler),
            ],
            State.PROG_INPUT_ALL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, prog_input_all_handler),
            ],
        },
        fallbacks=[CommandHandler("start", start_handler)],
        per_user=True,
        per_chat=True,
        allow_reentry=True,
    )


async def main() -> None:
    await init_db()
    logger.info("База данных инициализирована.")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(build_conversation_handler())

    logger.info("Бот запущен. Ожидание сообщений...")
    async with app:
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        try:
            await asyncio.Event().wait()
        finally:
            await app.updater.stop()
            await app.stop()


if __name__ == "__main__":
    asyncio.run(main())
