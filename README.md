# Swim Trainer — 1% лучше каждый день

Платформа физической подготовки для юного пловца (10 лет).

## Возможности

- Папин дашборд: управление упражнениями, расписанием, наградами, результатами заплывов
- Детский интерфейс: задания дня, прогресс, накопленные награды
- Telegram-бот: уведомления сыну, ввод результатов кнопкой
- Упражнения по стилям: кроль, брасс, баттерфляй, спина, универсальные
- Схемы мышц для каждого упражнения
- Система вознаграждений в USD
- Прогресс заплывов по времени и стилю

## Стек

- Backend: Python 3.11 + FastAPI + SQLite
- Frontend: React 18 + Vite
- Telegram Bot: python-telegram-bot
- Deploy: Docker Compose

## Порты

- Frontend: `0.0.0.0:8020`
- Backend: `127.0.0.1:8021`

## Быстрый старт

```bash
git clone https://github.com/sychev23021983-design/swim-trainer
cd swim-trainer
cp .env.example .env
# заполни .env своими данными
docker-compose up -d --build
```

## Переменные окружения

| Переменная | Описание |
|---|---|
| `SECRET_KEY` | JWT секрет |
| `PARENT_PASSWORD` | Пароль папы |
| `CHILD_NAME` | Имя сына |
| `TELEGRAM_BOT_TOKEN` | Токен Telegram бота |
| `TELEGRAM_CHAT_ID` | Chat ID сына в Telegram |

