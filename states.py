from aiogram.fsm.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    waiting_for_firstname = State()
    waiting_for_lastname = State()

class AddEventStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_date = State()
    waiting_for_place = State()
    waiting_for_points = State()

# Новое состояние:
class CheckinStates(StatesGroup):
    waiting_for_event_id = State()