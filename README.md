# WorkoutAssistant

Telegram-бот для домашних тренировок с собственным весом. Ведёт по программе тренировок, отсчитывает таймер отдыха, показывает фото упражнений и сохраняет историю прогресса.

## Возможности

- Расписание тренировок на неделю (грудь, спина, плечи, пресс, кор)
- Пошаговое выполнение упражнений с фото
- Таймер отдыха между подходами
- Отслеживание прогрессии (кол-во повторений/подходов)
- История тренировок и статистика
- Кнопка «пропустить упражнение» и «пропустить отдых»

## Структура проекта

```
WorkoutAssistant/
├── bot/
│   ├── handlers/
│   │   ├── menu.py        # главное меню, выбор дня
│   │   ├── workout.py     # выполнение тренировки
│   │   ├── progression.py # управление прогрессией
│   │   └── timer.py       # таймер отдыха
│   ├── persistence/
│   │   └── db.py          # SQLite через aiosqlite
│   ├── config.py
│   ├── data.py            # программа тренировок
│   ├── states.py          # состояния ConversationHandler
│   ├── utils.py
│   └── main.py
├── Exercise/              # фото упражнений (.jpg)
├── workout_plan.md        # программа тренировок (текст)
├── requirements.txt
├── setup.sh               # создать venv + установить зависимости
├── start.sh               # запустить бота
└── .env.example
```

## Быстрый старт (Termux / Linux)

```bash
git clone https://github.com/vova7790-boop/WorkoutAssistant ~/WorkoutAssistant
cd ~/WorkoutAssistant
cp .env.example .env
nano .env          # вставь BOT_TOKEN=<твой токен от @BotFather>
chmod +x setup.sh start.sh
./setup.sh
./start.sh
```

### Запуск в фоне

```bash
nohup ./start.sh > bot.log 2>&1 &
tail -f bot.log    # логи
pkill -f "bot.main"  # остановить
```

## Зависимости

| Пакет | Версия |
|-------|--------|
| python-telegram-bot | 21.9 |
| aiosqlite | 0.20.0 |
| python-dotenv | 1.0.1 |

Требуется Python 3.10+. В Termux на Android — Python 3.13.

## Переменные окружения

Создай файл `.env` в корне проекта:

```
BOT_TOKEN=123456:ABC-твой_токен
```

Токен получить у [@BotFather](https://t.me/BotFather).
