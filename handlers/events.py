from aiogram import Router, types
from aiogram.filters import Command
from csv_utils import load_events

router = Router()

@router.message(Command("events"))
async def cmd_events(message: types.Message):
    events = load_events()
    if not events:
        await message.answer("Пока нет мероприятий.")
        return
    text_lines = ["Список мероприятий:\n"]
    for eid, info in events.items():
        text_lines.append(f"ID {eid}: {info['name']} ({info['date']}), {info['place']} – {info['points']} баллов")
    await message.answer("\n".join(text_lines))