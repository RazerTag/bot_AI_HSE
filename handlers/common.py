from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext


router = Router()

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    text = (
        "Доступные команды:\n"
        "/start — регистрация\n"
        "/help — помощь\n"
        "/events — список мероприятий\n"
        "/checkin — отметить посещение\n"
        "/ranking — рейтинг участников\n\n"
        "Команды админа:\n"
        "/addevent — добавить мероприятие\n"
        "/setpoints <user_id> <points>"
    )
    await message.answer(text)


@router.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Действие отменено.")