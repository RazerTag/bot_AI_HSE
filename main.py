import asyncio
import os
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

from middlewares import RegistrationMiddleware
from csv_utils import init_csv_files
from scheduler_tasks import send_upcoming_events

# Подключаем роутеры (обработчики команд)
from handlers.registration import router as registration_router
from handlers.checkin import router as checkin_router
from handlers.events import router as events_router
from handlers.ranking import router as ranking_router
from handlers.admin import router as admin_router
from handlers.common import router as common_router

logging.basicConfig(level=logging.INFO)

async def setup_bot_commands(bot: Bot):
    """
    Устанавливаем список команд, чтобы в Telegram при вводе "/"
    отображалось меню с описаниями.
    """
    commands = [
        BotCommand(command="start", description="Начать регистрацию"),
        BotCommand(command="help", description="Помощь / меню команд"),
        BotCommand(command="events", description="Список мероприятий"),
        BotCommand(command="checkin", description="Отметиться на мероприятии"),
        BotCommand(command="ranking", description="Рейтинг участников"),
        BotCommand(command="cancel", description="Отменить текущее действие"),
        # Если есть дополнительная команда, например "/menu":
        # BotCommand(command="menu", description="Показать клавиатуру"),
        # и т.д.
    ]
    await bot.set_my_commands(commands)


async def main():
    # 1. Загружаем переменные окружения (BOT_TOKEN, ADMIN_ID и т.д.)
    load_dotenv()
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise ValueError("BOT_TOKEN не найден в .env")

    # 2. Инициализируем файлы CSV (если их нет — создадутся)
    init_csv_files()

    # 3. Создаём бота + диспетчер
    # Если не нужен HTML или Markdown, оставляем parse_mode=None
    bot = Bot(token=bot_token, parse_mode=None)
    dp = Dispatcher(storage=MemoryStorage())

    # 4. Регистрируем middleware (проверяет регистрацию, но пропускает FSM)
    dp.message.middleware(RegistrationMiddleware())

    # 5. Подключаем роутеры (хендлеры)
    dp.include_router(common_router)       # /help, /cancel ...
    dp.include_router(registration_router) # /start (FSM регистрации)
    dp.include_router(checkin_router)      # /checkin (FSM отметки)
    dp.include_router(events_router)       # /events
    dp.include_router(ranking_router)      # /ranking
    dp.include_router(admin_router)        # /addevent, /setpoints

    # 6. Устанавливаем команды для меню ("/start", "/help" и т.д.)
    await setup_bot_commands(bot)

    # 7. Настраиваем APScheduler (пример задания каждые 2 минуты)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_upcoming_events, "interval", minutes=2, args=[bot])
    scheduler.start()

    logging.info("Bot started. Press Ctrl+C to stop.")

    # 8. Запускаем бота (polling)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())