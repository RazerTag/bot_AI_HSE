from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from states import CheckinStates
from csv_utils import (
    load_events, load_attendance,
    update_user_points, save_attendance
)

router = Router()

@router.message(Command("checkin"))
async def cmd_checkin(message: types.Message, state: FSMContext):
    """
    Начало процесса "отметиться на мероприятии".
    Переводим пользователя в состояние waiting_for_event_id.
    """
    await message.answer("Введите ID мероприятия, которое вы посещаете:")
    await state.set_state(CheckinStates.waiting_for_event_id)

@router.message(CheckinStates.waiting_for_event_id)
async def checkin_event_id(message: types.Message, state: FSMContext):
    text = message.text.strip()

    # Проверяем, что text — это число (ID)
    if not text.isdigit():
        await message.answer("Неверный формат. Введите число (ID) или /cancel для отмены.")
        return

    event_id = int(text)
    events = load_events()
    if event_id not in events:
        await message.answer("Такого мероприятия нет. Попробуйте ещё раз или /cancel.")
        return

    # Проверим, отмечался ли уже
    attendance = load_attendance()
    for row in attendance:
        if row["user_id"] == str(message.from_user.id) and int(row["event_id"]) == event_id:
            await message.answer("Вы уже отмечены на этом мероприятии.")
            # Завершаем состояние
            await state.clear()
            return

    # Начисляем баллы
    ev = events[event_id]
    points = ev["points"]
    update_user_points(message.from_user.id, points)
    save_attendance(message.from_user.id, event_id, points)

    await message.answer(f"Вы успешно отметились на событии «{ev['name']}»! Вам начислено {points} баллов.")
    # Завершаем состояние
    await state.clear()

@router.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    """
    Универсальная команда /cancel для прерывания текущего состояния.
    """
    await state.clear()
    await message.answer("Действие отменено. Можете ввести новую команду.")