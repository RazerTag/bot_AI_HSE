from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from state.registration import RegistrationStates
from utils.database import save_user_data

router = Router()

@router.message(commands="start")
async def start_registration(message: Message, state: FSMContext):
    await message.answer("Привет! Давай начнем регистрацию. Как тебя зовут?")
    await state.set_state(RegistrationStates.enter_name)

@router.message(RegistrationStates.enter_name)
async def enter_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Сколько тебе лет?")
    await state.set_state(RegistrationStates.enter_age)

@router.message(RegistrationStates.enter_age)
async def enter_age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введи корректный возраст.")
        return
    await state.update_data(age=int(message.text))
    data = await state.get_data()
    await message.answer(f"Твое имя: {data['name']}, возраст: {data['age']}. Всё верно? (да/нет)")
    await state.set_state(RegistrationStates.confirm)

@router.message(RegistrationStates.confirm)
async def confirm_registration(message: Message, state: FSMContext):
    if message.text.lower() == "да":
        data = await state.get_data()
        save_user_data(data["name"], data["age"])  # Сохранение данных в базу
        await message.answer("Регистрация завершена! Добро пожаловать.")
        await state.clear()
    else:
        await message.answer("Давай попробуем снова. Как тебя зовут?")
        await state.set_state(RegistrationStates.enter_name)