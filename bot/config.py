import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
EXERCISE_DIR = BASE_DIR / "Exercise"
DB_PATH = BASE_DIR / "bot" / "workout_history.db"

load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не задан. Создай файл .env с BOT_TOKEN=<твой токен>")
