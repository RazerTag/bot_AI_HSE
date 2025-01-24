from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states import AddEventStates
from csv_utils import load_events, save_event, load_users
from csv_utils import update_user_points
from gigachat_integration import generate_text_gigachat
import os

router = Router()

def is_admin(user_id: int) -> bool:
    return str(user_id) == os.getenv("ADMIN_ID")

@router.message(Command("addevent"))
async def cmd_addevent(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав администратора.")
        return
    await message.answer("Введите название мероприятия:")
    await state.set_state(AddEventStates.waiting_for_name)

@router.message(AddEventStates.waiting_for_name)
async def add_event_name(message: types.Message, state: FSMContext):
    event_name = message.text
    await state.update_data(event_name=event_name)

    # Генерируем автоописание через GigaChat
    prompt = f"Сгенерируй короткое описание мероприятия по названию: {event_name}"
    description = generate_text_gigachat(prompt)

    # Сохраняем в data
    await state.update_data(description=description)

    await message.answer(
        f"Сгенерированное описание:\n\n{description}\n\n"
        "Введите дату в формате YYYY-MM-DD:"
    )
    await state.set_state(AddEventStates.waiting_for_date)

@router.message(AddEventStates.waiting_for_date)
async def add_event_date(message: types.Message, state: FSMContext):
    await state.update_data(event_date=message.text)
    await message.answer("Введите место проведения:")
    await state.set_state(AddEventStates.waiting_for_place)

@router.message(AddEventStates.waiting_for_place)
async def add_event_place(message: types.Message, state: FSMContext):
    await state.update_data(event_place=message.text)
    await message.answer("Сколько баллов начислять за посещение?")
    await state.set_state(AddEventStates.waiting_for_points)

@router.message(AddEventStates.waiting_for_points)
async def add_event_points(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введите число (баллы).")
        return
    points = int(message.text)
    data = await state.get_data()
    name = data["event_name"]
    date_str = data["event_date"]
    place = data["event_place"]
    desc = data["description"]  # из GigaChat

    events = load_events()
    new_id = max(events.keys(), default=0) + 1

    # Теперь в save_event() нужно иметь поле description (см. ниже)
    save_event(new_id, name, date_str, place, points, description=desc)

    await message.answer(
        f"Мероприятие добавлено:\n"
        f"ID: {new_id}\n{name} ({date_str}), {place}\n"
        f"Баллы: {points}\n\nОписание:\n{desc}"
    )
    await state.clear()

@router.message(Command("setpoints"))
async def cmd_setpoints(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав администратора.")
        return
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("Формат: /setpoints <user_id> <points>")
        return

    target_uid, pts_str = parts[1], parts[2]
    if not pts_str.isdigit():
        await message.answer("Баллы должны быть числом.")
        return

    update_user_points(target_uid, int(pts_str))
    await message.answer(f"У пользователя {target_uid} установлено {pts_str} баллов.")