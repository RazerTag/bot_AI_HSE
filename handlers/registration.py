from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states import RegistrationStates
from csv_utils import save_user, is_registered

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    # Если уже в CSV, сообщим, что регистрация пройдена
    if is_registered(message.from_user.id):
        await message.answer("Вы уже зарегистрированы! Можно пользоваться /events, /checkin, /ranking.")
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
    data = await state.get_data()
    first_name = data["firstname"]
    last_name = message.text

    save_user(message.from_user.id, first_name, last_name)
    await state.clear()
    await message.answer("Регистрация успешно завершена! Используйте /events, /checkin, /ranking.")