import asyncio
import os
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

from middlewares import RegistrationMiddleware
from csv_utils import init_csv_files
from scheduler_tasks import send_upcoming_events

# Подключаем наши роутеры (обработчики команд)
from handlers.registration import router as registration_router
from handlers.checkin import router as checkin_router
from handlers.events import router as events_router
from handlers.ranking import router as ranking_router
from handlers.admin import router as admin_router
from handlers.common import router as common_router

logging.basicConfig(level=logging.INFO)

async def main():
    # 1. Загружаем переменные окружения (BOT_TOKEN, ADMIN_ID и т.д.)
    load_dotenv()
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise ValueError("BOT_TOKEN не найден в .env")

    # 2. Инициализируем файлы CSV (если нет, создадутся)
    init_csv_files()

    # 3. Создаём бота + диспетчер
    # parse_mode="HTML" -- если используем HTML-разметку, иначе None
    bot = Bot(token=bot_token, parse_mode=None)
    dp = Dispatcher(storage=MemoryStorage())

    # 4. Регистрируем middleware (проверяет регистрацию, но пропускает FSM-состояния)
    dp.message.middleware(RegistrationMiddleware())

    # 5. Регистрируем все роутеры (хендлеры)
    # Порядок не критичен, но обычно /cancel или общие идут первыми/последними.
    dp.include_router(common_router)       # /help, /cancel и т.д.
    dp.include_router(registration_router) # /start (FSM для регистрации)
    dp.include_router(checkin_router)      # /checkin (FSM для чек-ина)
    dp.include_router(events_router)       # /events
    dp.include_router(ranking_router)      # /ranking
    dp.include_router(admin_router)        # /addevent, /setpoints (админ-функции)

    # 6. Настраиваем APScheduler (пример задачи каждые 2 минуты)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_upcoming_events, "interval", minutes=2, args=[bot])
    scheduler.start()

    logging.info("Bot started. Press Ctrl+C to stop.")

    # 7. Запускаем диспетчер (polling)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())