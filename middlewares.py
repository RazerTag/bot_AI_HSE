import csv
import os
from aiogram import BaseMiddleware, types
from aiogram.fsm.context import FSMContext
from csv_utils import is_registered
from states import RegistrationStates

class RegistrationMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        if isinstance(event, types.Message):
            msg = event
            state: FSMContext = data["state"]
            current_state = await state.get_state()

            # 1. Если пользователь в процессе регистрации (RegistrationStates), пропускаем
            if current_state and current_state.startswith("RegistrationStates:"):
                return await handler(event, data)

            # 2. Разрешаем /start и /help вне зависимости от регистрации
            if msg.text and (msg.text.startswith("/start") or msg.text.startswith("/help")):
                return await handler(event, data)

            # 3. Иначе проверяем, зарегистрирован ли пользователь (CSV)
            if not is_registered(msg.from_user.id):
                await msg.answer("Сначала зарегистрируйтесь командой /start.")
                return

        return await handler(event, data)