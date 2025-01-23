from datetime import datetime, timedelta
from csv_utils import load_users, load_events
from aiogram import Bot

async def send_upcoming_events(bot: Bot):
    # Пример: за сутки до события
    users = load_users()
    events = load_events()

    tomorrow = (datetime.now() + timedelta(days=1)).date()
    upcoming = []
    for eid, info in events.items():
        # Пытаемся распарсить дату
        try:
            d = datetime.fromisoformat(info["date"]).date()
            if d <= tomorrow:
                upcoming.append(info)
        except:
            pass

    if not upcoming:
        return

    text_lines = ["Ближайшие события:\n"]
    for ev in upcoming:
        text_lines.append(f"• {ev['name']} ({ev['date']}) — {ev['points']} баллов")

    text = "\n".join(text_lines)

    for uid in users.keys():
        try:
            await bot.send_message(uid, text)
        except:
            pass