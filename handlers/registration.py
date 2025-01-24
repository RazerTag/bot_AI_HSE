from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states import RegistrationStates
from csv_utils import save_user, is_registered

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    if is_registered(message.from_user.id):
        await message.answer("Вы уже зарегистрированы! Используйте /events, /checkin, /ranking.")
    else:
        await message.answer("Здравствуйте! Введите ваше имя:")
        await state.set_state(RegistrationStates.waiting_for_firstname)

@router.message(RegistrationStates.waiting_for_firstname)
async def reg_firstname(message: types.Message, state: FSMContext):
    await state.update_data(firstname=message.text)
    await message.answer("Отлично. Теперь введите фамилию:")
    await state.set_state(RegistrationStates.waiting_for_lastname)

@router.message(RegistrationStates.waiting_for_lastname)
async def reg_lastname(message: types.Message, state: FSMContext):
    await state.update_data(lastname=message.text)
    await message.answer("Введите, пожалуйста, ваш возраст (числом).")
    await state.set_state(RegistrationStates.waiting_for_age)

@router.message(RegistrationStates.waiting_for_age)
async def reg_age(message: types.Message, state: FSMContext):
    text = message.text.strip()
    # Проверяем, ввёл ли пользователь число
    if not text.isdigit():
        await message.answer("Пожалуйста, введите только число. Попробуйте ещё раз или /cancel.")
        return

    age = int(text)

    # Если хотите задать ограничения, например, возраст >= 14:
    if age < 14 or age > 120:
        await message.answer("Возраст кажется некорректным. Попробуйте ещё раз или /cancel.")
        return

    data = await state.get_data()
    firstname = data["firstname"]
    lastname = data["lastname"]

    # Сохраняем в CSV. Не забудьте, если хотите хранить возраст, 
    # расширить структуру users.csv (и функции в csv_utils.py).
    save_user(
        user_id=message.from_user.id,
        first_name=firstname,
        last_name=lastname
    )

    await state.clear()
    await message.answer(
        f"Регистрация успешно завершена!\n"
        f"Имя: {firstname}, Фамилия: {lastname}, Возраст: {age}\n"
        "Доступные команды: /events, /checkin, /ranking."
    )