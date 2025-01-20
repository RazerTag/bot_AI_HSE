import logging
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web
from config import BOT_TOKEN
from handlers import registration, reminders
from middleware.registration import RegistrationMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO)
load_dotenv()

# Создаем бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Подключаем обработчики
dp.include_router(registration.router)
dp.include_router(reminders.router)

# Middleware для проверки регистрации
dp.update.middleware(RegistrationMiddleware())

# Создаем планировщик
scheduler = AsyncIOScheduler()
scheduler.start()

# Запуск веб-сервера
app = web.Application()
SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/webhook")

if __name__ == "__main__":
    from pyngrok import ngrok

    # Настраиваем ngrok
    ngrok.set_auth_token(os.getenv("NGROK_AUTH_TOKEN"))
    public_url = ngrok.connect(8000)
    print(f"Webhook URL: {public_url}/webhook")

    web.run_app(app, port=8000)