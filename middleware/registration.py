from aiogram import BaseMiddleware
from aiogram.types import Message
from utils.database import is_user_registered

class RegistrationMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: dict):
        user_id = event.from_user.id
        if not is_user_registered(user_id):
            await event.answer("Сначала нужно зарегистрироваться! Используйте /start.")
            return
        await handler(event, data)