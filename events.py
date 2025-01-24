from aiogram import Router, types
from aiogram.filters import Command
from csv_utils import load_events, load_attendance, save_attendance, update_user_points

router = Router()

@router.message(Command("events"))
async def cmd_events(message: types.Message):
    """
    Показываем список мероприятий, каждое с inline-кнопкой "Отметиться".
    """
    events = load_events()
    if not events:
        await message.answer("Пока нет мероприятий.")
        return

    # Перебираем все события и отправляем пользователю
    for eid, info in events.items():
        # Текст описания мероприятия
        text = (
            f"ID {eid}: {info['name']} ({info['date']})\n"
            f"Место: {info['place']}\n"
            f"Баллы за посещение: {info['points']}"
        )

        # Создаём inline-кнопку, при нажатии на неё callback_data="checkin:<eid>"
        button = types.InlineKeyboardButton(
            text="Отметиться",
            callback_data=f"checkin:{eid}"
        )
        # Оформляем клавиатуру
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[[button]])

        # Отправляем сообщение с кнопкой
        await message.answer(text, reply_markup=keyboard)

@router.callback_query(lambda c: c.data.startswith("checkin:"))
async def cb_checkin(callback: types.CallbackQuery):
    """
    Обработка нажатия на кнопку "Отметиться".
    Здесь c.data будет в формате: "checkin:<eid>"
    """
    # Извлекаем <eid> (ID мероприятия)
    parts = callback.data.split(":")
    if len(parts) != 2:
        await callback.answer("Неверные данные кнопки.")
        return

    event_id_str = parts[1]
    if not event_id_str.isdigit():
        await callback.answer("Неверный формат ID мероприятия.")
        return

    event_id = int(event_id_str)
    events = load_events()
    if event_id not in events:
        await callback.answer("Такого мероприятия нет.")
        return

    # Проверяем, не отмечался ли пользователь уже
    attendance = load_attendance()
    user_id = str(callback.from_user.id)
    for row in attendance:
        if row["user_id"] == user_id and int(row["event_id"]) == event_id:
            await callback.answer("Вы уже отмечены на этом мероприятии!")
            return

    # Если ещё не отмечался — начисляем баллы, сохраняем
    ev = events[event_id]
    points = ev["points"]
    update_user_points(user_id, points)
    save_attendance(user_id, event_id, points)

    # Выводим всплывающее уведомление
    await callback.answer("Отметка сохранена, баллы начислены!", show_alert=False)
    # Или можно изменить текст сообщения:
    # await callback.message.edit_text(f"Отметились на мероприятии: {ev['name']}! (+{points} баллов)")