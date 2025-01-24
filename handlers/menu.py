from aiogram import Router, types
from aiogram.filters import Command

router = Router()

@router.message(Command("menu"))
async def cmd_menu(message: types.Message):
    kb = [
        [types.KeyboardButton(text="Мероприятия")],
        [types.KeyboardButton(text="Отметиться")],
        [types.KeyboardButton(text="Рейтинг")],
        [types.KeyboardButton(text="Отмена (/cancel)")]
    ]
    # resize_keyboard=True, чтобы кнопки были компактнее
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer("Выберите действие:", reply_markup=keyboard)

# Далее нужно отловить нажатия
@router.message()
async def menu_replies(message: types.Message):
    if message.text == "Мероприятия":
        # вместо отправки текста выполним логику /events
        await message.answer("/events (для inline-клавы нужно другой подход)")
    elif message.text == "Отметиться":
        await message.answer("/checkin")
    elif message.text == "Рейтинг":
        await message.answer("/ranking")
    # и т.д.