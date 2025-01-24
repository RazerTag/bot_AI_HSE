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
    """Начинаем процесс добавления нового мероприятия (только для админа)."""
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав администратора.")
        return

    await message.answer("Введите название мероприятия:")
    await state.set_state(AddEventStates.waiting_for_name)


@router.message(AddEventStates.waiting_for_name)
async def add_event_name(message: types.Message, state: FSMContext):
    """После ввода названия генерируем автоописание (через GigaChat)."""
    event_name = message.text.strip()
    await state.update_data(event_name=event_name)

    # Генерируем автоописание
    prompt = f"Сгенерируй короткое описание мероприятия по названию: {event_name}"
    description = generate_text_gigachat(prompt)

    # Сохраняем в FSM
    await state.update_data(description=description)

    await message.answer(
        f"Сгенерированное описание:\n\n{description}\n\n"
        "Введите дату в формате YYYY-MM-DD:"
    )
    await state.set_state(AddEventStates.waiting_for_date)


@router.message(AddEventStates.waiting_for_date)
async def add_event_date(message: types.Message, state: FSMContext):
    """Сохраняем дату."""
    date_str = message.text.strip()
    await state.update_data(event_date=date_str)
    await message.answer("Введите место проведения:")
    await state.set_state(AddEventStates.waiting_for_place)


@router.message(AddEventStates.waiting_for_place)
async def add_event_place(message: types.Message, state: FSMContext):
    """Сохраняем место проведения."""
    place = message.text.strip()
    await state.update_data(event_place=place)
    await message.answer("Сколько баллов начислять за посещение?")
    await state.set_state(AddEventStates.waiting_for_points)


@router.message(AddEventStates.waiting_for_points)
async def add_event_points(message: types.Message, state: FSMContext):
    """
    Сохраняем кол-во баллов, вызываем save_event(...) и завершаем FSM.
    Проверяем, что введено число (целое).
    """
    text = message.text.strip()
    if not text.isdigit():
        await message.answer("Введите число (баллы).")
        return
    points = int(text)

    data = await state.get_data()
    # Берём name, date, place; description — через .get() на случай отсутствия
    name = data.get("event_name", "Без названия")
    date_str = data.get("event_date", "0000-00-00")
    place = data.get("event_place", "Не указано")
    desc = data.get("description", "")  # <--- защита от KeyError

    # Загружаем текущие события, находим новый ID
    events = load_events()
    new_id = max(events.keys(), default=0) + 1

    # Вызываем save_event(...). Убедитесь, что в csv_utils.py есть поле description
    save_event(
        event_id=new_id,
        name=name,
        date_str=date_str,
        place=place,
        points=points,
        description=desc
    )

    await message.answer(
        f"Мероприятие добавлено:\n"
        f"ID: {new_id}\n"
        f"{name} ({date_str}), {place}\n"
        f"Баллы: {points}\n\n"
        f"Описание:\n{desc}"
    )
    # Очищаем состояние
    await state.clear()


@router.message(Command("setpoints"))
async def cmd_setpoints(message: types.Message):
    """Админский метод: вручную установить кол-во баллов для пользователя."""
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