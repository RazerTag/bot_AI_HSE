from aiogram import Router, types
from aiogram.filters import Command
from csv_utils import load_users

router = Router()

@router.message(Command("ranking"))
async def cmd_ranking(message: types.Message):
    users = load_users()
    if not users:
        await message.answer("Нет зарегистрированных пользователей.")
        return
    # Сортируем
    sorted_users = sorted(users.items(), key=lambda x: x[1]["total_points"], reverse=True)
    text_lines = ["Рейтинг участников:\n"]
    place = 1
    for uid, info in sorted_users:
        text_lines.append(f"{place}. {info['first_name']} {info['last_name']} – {info['total_points']} баллов")
        place += 1
    await message.answer("\n".join(text_lines))