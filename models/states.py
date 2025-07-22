from aiogram.fsm.state import State, StatesGroup

class AddExpense(StatesGroup):
    waiting_for_amount = State()
    waiting_for_description = State()
    waiting_for_targets = State()