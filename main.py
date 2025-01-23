import asyncio
import csv
import os
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)

###############################################################################
# 1) Состояния (FSM) для регистрации и добавления мероприятий
###############################################################################
class RegistrationStates(StatesGroup):
    waiting_for_firstname = State()
    waiting_for_lastname = State()

class AddEventStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_date = State()
    waiting_for_place = State()
    waiting_for_points = State()

###############################################################################
# 2) Вспомогательные функции (чтение/запись CSV)
###############################################################################
USERS_CSV = "users.csv"        # user_id, first_name, last_name, total_points
EVENTS_CSV = "events.csv"      # event_id, name, date, place, points
ATTENDANCE_CSV = "attend.csv"  # user_id, event_id, checkin_time, points_earned

def ensure_csv_headers(filename, fieldnames):
    """Создаёт CSV-файл с заголовками, если он отсутствует."""
    if not os.path.exists(filename):
        with open(filename, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

def load_users():
    """Возвращает словарь {user_id (str/int): {first_name, last_name, total_points}}"""
    ensure_csv_headers(USERS_CSV, ["user_id", "first_name", "last_name", "total_points"])
    data = {}
    with open(USERS_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            uid = row["user_id"]
            data[uid] = {
                "first_name": row["first_name"],
                "last_name": row["last_name"],
                "total_points": int(row["total_points"])
            }
    return data

def save_user(user_id, first_name, last_name, total_points=0):
    """Добавляет или обновляет пользователя в users.csv."""
    users = load_users()
    users[str(user_id)] = {
        "first_name": first_name,
        "last_name": last_name,
        "total_points": total_points
    }
    # перезаписываем файл полностью
    with open(USERS_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["user_id","first_name","last_name","total_points"])
        writer.writeheader()
        for uid, info in users.items():
            writer.writerow({
                "user_id": uid,
                "first_name": info["first_name"],
                "last_name": info["last_name"],
                "total_points": info["total_points"]
            })

def is_registered(user_id):
    """Проверка, зарегистрирован ли пользователь."""
    users = load_users()
    return str(user_id) in users

def update_user_points(user_id, points_to_add):
    users = load_users()
    if str(user_id) in users:
        users[str(user_id)]["total_points"] += points_to_add
        # сохранить обратно
        with open(USERS_CSV, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["user_id","first_name","last_name","total_points"])
            writer.writeheader()
            for uid, info in users.items():
                writer.writerow({
                    "user_id": uid,
                    "first_name": info["first_name"],
                    "last_name": info["last_name"],
                    "total_points": info["total_points"]
                })

def load_events():
    """Возвращает словарь {event_id (int): {name, date, place, points}}"""
    ensure_csv_headers(EVENTS_CSV, ["event_id","name","date","place","points"])
    data = {}
    with open(EVENTS_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            e_id = int(row["event_id"])
            data[e_id] = {
                "name": row["name"],
                "date": row["date"],    # формат строки, можно парсить datetime
                "place": row["place"],
                "points": int(row["points"])
            }
    return data

def save_event(event_id, name, date_str, place, points):
    """Добавляет мероприятие в events.csv."""
    events = load_events()
    events[event_id] = {
        "name": name,
        "date": date_str,
        "place": place,
        "points": points
    }
    # перезапись
    with open(EVENTS_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["event_id","name","date","place","points"])
        writer.writeheader()
        for e_id, info in events.items():
            writer.writerow({
                "event_id": e_id,
                "name": info["name"],
                "date": info["date"],
                "place": info["place"],
                "points": info["points"]
            })

def load_attendance():
    """Список посещений: [{user_id, event_id, checkin_time, points_earned}, ...]"""
    ensure_csv_headers(ATTENDANCE_CSV, ["user_id","event_id","checkin_time","points_earned"])
    rows = []
    with open(ATTENDANCE_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["points_earned"] = int(row["points_earned"])
            rows.append(row)
    return rows

def save_attendance_entry(user_id, event_id, points):
    """Сохраняет запись о посещении."""
    with open(ATTENDANCE_CSV, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["user_id","event_id","checkin_time","points_earned"])
        # если файл пуст - заголовок
        if os.path.getsize(ATTENDANCE_CSV) == 0:
            writer.writeheader()
        writer.writerow({
            "user_id": user_id,
            "event_id": event_id,
            "checkin_time": datetime.now().isoformat(),
            "points_earned": points
        })

###############################################################################
# 3) Мидлварь для проверки регистрации (кроме /start и /help)
###############################################################################
from aiogram import BaseMiddleware

class RegistrationMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        if isinstance(event, types.Message):
            msg = event
            # Разрешаем свободный доступ к командам /start и /help
            if msg.text and (msg.text.startswith("/start") or msg.text.startswith("/help")):
                return await handler(event, data)
            # Проверяем регистрацию
            if not is_registered(msg.from_user.id):
                await msg.answer("Сначала зарегистрируйтесь командой /start.")
                return
        return await handler(event, data)

###############################################################################
# 4) Функции для админа и планировщик APScheduler
###############################################################################
def is_admin(user_id):
    """Сравниваем user_id с ADMIN_ID из .env"""
    return str(user_id) == str(os.getenv("ADMIN_ID"))

async def send_upcoming_events(bot: Bot):
    """
    Пример фоновой задачи: рассылка всем пользователям событий,
    которые начинаются в ближайшие N дней (для примера — 1 день).
    """
    users = load_users()
    events = load_events()
    # Условно считаем "ближайшие сутки"
    tomorrow = (datetime.now() + timedelta(days=1)).date()

    # Соберём события, которые начинаются сегодня или завтра
    # (В реальном проекте парсите date из events и сравнивайте)
    upcoming = []
    for e_id, info in events.items():
        # Пытаемся распарсить info["date"] как YYYY-MM-DD
        try:
            event_date = datetime.fromisoformat(info["date"]).date()
            if event_date <= tomorrow:
                upcoming.append((e_id, info))
        except:
            # если формат неправильный - пропускаем
            pass

    if not upcoming:
        return  # нет событий для анонса

    # Формируем текст
    text_parts = ["Ближайшие события:\n"]
    for e_id, ev in upcoming:
        text_parts.append(f"• {ev['name']} ({ev['date']}), {ev['place']} – {ev['points']} баллов")
    text = "\n".join(text_parts)

    # Рассылаем каждому пользователю
    for uid in users.keys():
        try:
            await bot.send_message(uid, text)
        except:
            pass

###############################################################################
# 5) Основной код бота
###############################################################################
async def main():
    load_dotenv()
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise ValueError("BOT_TOKEN не найден в .env")

    bot = Bot(token=bot_token)
    dp = Dispatcher(storage=MemoryStorage())

    # Регистрируем middleware
    dp.message.middleware(RegistrationMiddleware())

    # Инициализируем файлы CSV (если нет - создадутся)
    ensure_csv_headers(USERS_CSV, ["user_id","first_name","last_name","total_points"])
    ensure_csv_headers(EVENTS_CSV, ["event_id","name","date","place","points"])
    ensure_csv_headers(ATTENDANCE_CSV, ["user_id","event_id","checkin_time","points_earned"])

    # -------------------------------
    # APScheduler (фоновая задача)
    # -------------------------------
    scheduler = AsyncIOScheduler()
    # Запускаем задачу раз в сутки (каждые 24 часа) - пример в 9:00
    # scheduler.add_job(send_upcoming_events, "cron", hour=9, args=[bot])
    # Для теста каждые 2 минуты:
    scheduler.add_job(send_upcoming_events, "interval", minutes=2, args=[bot])
    scheduler.start()

    # -------------------------------
    # Хендлеры /start, /help
    # -------------------------------
    @dp.message(Command("start"))
    async def cmd_start(message: types.Message, state: FSMContext):
        if is_registered(message.from_user.id):
            await message.answer("Вы уже зарегистрированы! Можете использовать /events, /checkin, /ranking")
        else:
            await message.answer("Здравствуйте! Введите ваше имя:")
            await state.set_state(RegistrationStates.waiting_for_firstname)

    @dp.message(RegistrationStates.waiting_for_firstname)
    async def reg_firstname(message: types.Message, state: FSMContext):
        await state.update_data(firstname=message.text)
        await message.answer("Отлично. Теперь введите фамилию:")
        await state.set_state(RegistrationStates.waiting_for_lastname)

    @dp.message(RegistrationStates.waiting_for_lastname)
    async def reg_lastname(message: types.Message, state: FSMContext):
        data = await state.get_data()
        firstname = data["firstname"]
        lastname = message.text
        # Сохраняем в CSV
        save_user(
            user_id=message.from_user.id,
            first_name=firstname,
            last_name=lastname,
            total_points=0
        )
        await state.clear()
        await message.answer("Регистрация успешно завершена! Используйте /events, /checkin, /ranking.")

    @dp.message(Command("help"))
    async def cmd_help(message: types.Message):
        text = (
            "Доступные команды:\n"
            "/start – регистрация (если не зарегистрированы)\n"
            "/help – помощь\n"
            "/checkin – отметить посещение мероприятия\n"
            "/events – список мероприятий\n"
            "/ranking – рейтинг участников\n"
            "\n"
            "Команды админа:\n"
            "/addevent – добавить новое мероприятие\n"
            "/setpoints <user_id> <points> – вручную установить баллы\n"
        )
        await message.answer(text)

    # -------------------------------
    # Хендлер: /events - показать список мероприятий
    # -------------------------------
    @dp.message(Command("events"))
    async def cmd_events(message: types.Message):
        events = load_events()
        if not events:
            await message.answer("Пока нет мероприятий.")
            return
        text_parts = ["Список мероприятий:\n"]
        for e_id, info in events.items():
            text_parts.append(f"ID {e_id}: {info['name']} ({info['date']}), {info['place']}, {info['points']} баллов")
        await message.answer("\n".join(text_parts))

    # -------------------------------
    # Хендлер: /checkin - отметить посещение
    # -------------------------------
    @dp.message(Command("checkin"))
    async def cmd_checkin(message: types.Message):
        """
        Запросим ID мероприятия. Можно было бы парсить аргументы, 
        либо просить ввести отдельно.
        """
        await message.answer("Введите ID мероприятия, которое вы посещаете:")

        # В простом случае ждём следующий message:
        @dp.message(F.text, flags={"checkin_waiting": True})
        async def get_event_id_for_checkin(m: types.Message):
            event_id_str = m.text.strip()
            if not event_id_str.isdigit():
                await m.answer("Неверный формат. Введите число (ID). /cancel для отмены.")
                return
            event_id = int(event_id_str)
            events = load_events()
            if event_id not in events:
                await m.answer("Такого мероприятия нет. Попробуйте ещё раз.")
                return

            # Проверяем, не отмечался ли уже?
            attendance = load_attendance()
            for a in attendance:
                if a["user_id"] == str(m.from_user.id) and int(a["event_id"]) == event_id:
                    await m.answer("Вы уже отмечены на этом мероприятии.")
                    return

            # Начисляем баллы
            ev = events[event_id]
            points = ev["points"]
            update_user_points(m.from_user.id, points)
            save_attendance_entry(m.from_user.id, event_id, points)

            await m.answer(f"Вы успешно отметились на событии {ev['name']}! Вам начислено {points} баллов.")
            # Снимаем флаг обработчика
            dp.message.outer_middleware_registry.unregister("checkin_waiting")

        # Регистрируем временный обработчик (чтобы после одного ответа отключить)
        dp.message.bind_filter_to_handler(get_event_id_for_checkin)

    # -------------------------------
    # Рейтинг участников
    # -------------------------------
    @dp.message(Command("ranking"))
    async def cmd_ranking(message: types.Message):
        users = load_users()
        # сортируем по total_points убыв
        sorted_users = sorted(users.items(), key=lambda x: x[1]["total_points"], reverse=True)
        text_parts = ["Рейтинг участников:\n"]
        place = 1
        for uid, info in sorted_users:
            text_parts.append(f"{place}. {info['first_name']} {info['last_name']} – {info['total_points']} баллов")
            place += 1
        await message.answer("\n".join(text_parts))

    # -------------------------------
    # Админ-команда: /addevent
    # -------------------------------
    @dp.message(Command("addevent"))
    async def cmd_addevent(message: types.Message, state: FSMContext):
        if not is_admin(message.from_user.id):
            await message.answer("У вас нет прав администратора.")
            return
        await message.answer("Введите название мероприятия:")
        await state.set_state(AddEventStates.waiting_for_name)

    @dp.message(AddEventStates.waiting_for_name)
    async def add_event_name(message: types.Message, state: FSMContext):
        await state.update_data(event_name=message.text)
        await message.answer("Введите дату в формате YYYY-MM-DD:")
        await state.set_state(AddEventStates.waiting_for_date)

    @dp.message(AddEventStates.waiting_for_date)
    async def add_event_date(message: types.Message, state: FSMContext):
        # Можно сделать проверку формата
        await state.update_data(event_date=message.text)
        await message.answer("Введите место проведения:")
        await state.set_state(AddEventStates.waiting_for_place)

    @dp.message(AddEventStates.waiting_for_place)
    async def add_event_place(message: types.Message, state: FSMContext):
        await state.update_data(event_place=message.text)
        await message.answer("Сколько баллов начислять за посещение?")
        await state.set_state(AddEventStates.waiting_for_points)

    @dp.message(AddEventStates.waiting_for_points)
    async def add_event_points(message: types.Message, state: FSMContext):
        if not message.text.isdigit():
            await message.answer("Введите число (баллы).")
            return
        points = int(message.text)
        data = await state.get_data()
        name = data["event_name"]
        date_str = data["event_date"]
        place = data["event_place"]

        # Генерируем event_id (например, берем текущее кол-во +1)
        events = load_events()
        if events:
            new_id = max(events.keys()) + 1
        else:
            new_id = 1

        # сохраняем
        save_event(new_id, name, date_str, place, points)

        await message.answer(f"Мероприятие добавлено:\nID: {new_id}\n{name} ({date_str}), {place}\nБаллы: {points}")
        await state.clear()

    # -------------------------------
    # Админ: /setpoints <user_id> <points>
    # -------------------------------
    @dp.message(Command("setpoints"))
    async def cmd_setpoints(message: types.Message):
        if not is_admin(message.from_user.id):
            await message.answer("У вас нет прав администратора.")
            return
        parts = message.text.split()
        if len(parts) != 3:
            await message.answer("Формат: /setpoints <user_id> <points>")
            return
        target_uid, new_points_str = parts[1], parts[2]
        if not new_points_str.isdigit():
            await message.answer("Второй аргумент должен быть числом.")
            return
        new_points = int(new_points_str)
        users = load_users()
        if target_uid not in users:
            await message.answer("Нет пользователя с таким user_id.")
            return
        users[target_uid]["total_points"] = new_points
        # Сохраняем всех
        with open(USERS_CSV, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["user_id","first_name","last_name","total_points"])
            writer.writeheader()
            for uid, info in users.items():
                writer.writerow({
                    "user_id": uid,
                    "first_name": info["first_name"],
                    "last_name": info["last_name"],
                    "total_points": info["total_points"]
                })
        await message.answer(f"У пользователя {target_uid} теперь {new_points} баллов.")

    # Запускаем обработку
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())