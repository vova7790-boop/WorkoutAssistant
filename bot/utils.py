import math
import random

MOTIVATIONAL_MESSAGES = [
    "Отличная работа! Ты становишься сильнее с каждой тренировкой! 💪",
    "Тренировка завершена! Твоё тело скажет тебе спасибо. 🏆",
    "Молодец! Последовательность — ключ к результату. 🔑",
    "Готово! Сегодня ты сделал шаг к лучшей версии себя. ⭐",
    "Тренировка в кармане! Отдыхай и восстанавливайся. 🌟",
    "Ещё один день — ещё один шаг вперёд. Так держать! 🚀",
    "Сила приходит к тем, кто не сдаётся. Ты доказал это сегодня! 🔥",
]


def random_motivation() -> str:
    return random.choice(MOTIVATIONAL_MESSAGES)


def parse_progression_input(text: str, base_value: int) -> int | None:
    """
    Parse user input for reps/seconds progression.
    Accepts: "5" -> +5 absolute, "20%" -> ceil(base * 0.20).
    Returns the integer delta or None if invalid.
    """
    text = text.strip()
    try:
        if text.endswith("%"):
            pct = float(text[:-1]) / 100
            if pct <= 0:
                return None
            return math.ceil(base_value * pct)
        else:
            val = int(text)
            if val <= 0:
                return None
            return val
    except (ValueError, ZeroDivisionError):
        return None


def format_exercise_caption(
    exercise: dict,
    set_num: int,
    total_sets: int,
    extra_reps: int = 0,
    extra_seconds: int = 0,
) -> str:
    name = exercise["name"]
    if exercise["reps"] > 0:
        target = exercise["reps"] + extra_reps
        unit = "повт."
        extra_note = f" (+{extra_reps})" if extra_reps > 0 else ""
    else:
        target = exercise["duration"] + extra_seconds
        unit = "сек"
        extra_note = f" (+{extra_seconds}с)" if extra_seconds > 0 else ""

    tip = exercise.get("tip", "")
    tip_line = f"\n\n💡 {tip}" if tip else ""

    return (
        f"*{name}*\n"
        f"Подход {set_num} из {total_sets}\n"
        f"Цель: {target} {unit}{extra_note}"
        f"{tip_line}"
    )


def format_set_in_progress(exercise: dict, set_num: int, total_sets: int, extra_reps: int = 0, extra_seconds: int = 0) -> str:
    name = exercise["name"]
    if exercise["reps"] > 0:
        target = exercise["reps"] + extra_reps
        unit = "повт."
    else:
        target = exercise["duration"] + extra_seconds
        unit = "сек"

    return (
        f"*{name}*\n"
        f"Подход {set_num} из {total_sets} — В ПРОЦЕССЕ\n"
        f"Цель: {target} {unit}\n\n"
        f"Выполни подход и нажми *Готово* ✓"
    )
