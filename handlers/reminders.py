from aiogram import Router
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from utils.database import get_all_users
from aiogram.types import Bot

router = Router()

scheduler = AsyncIOScheduler()

async def send_reminder(bot: Bot, user_id: int, message: str):
    await bot.send_message(chat_id=user_id, text=message)

# Планируем отправку напоминаний
def schedule_reminders(bot: Bot):
    users = get_all_users()
    for user in users:
        scheduler.add_job(send_reminder, "interval", hours=1, args=[bot, user["id"], "Напоминание!"])
    scheduler.start()