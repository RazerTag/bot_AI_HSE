from aiogram.fsm.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    enter_name = State()
    enter_age = State()
    confirm = State()