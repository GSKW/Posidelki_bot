from aiogram import Bot, Dispatcher, F
from aiogram.filters.command import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging
from config import BOT_TOKEN

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Структура для хранения данных (в памяти)
participants = set()
expenses = []  # список словарей с расходами


# Состояния для FSM
class AddParticipant(StatesGroup):
    waiting_for_name = State()


class AddExpense(StatesGroup):
    waiting_for_payer = State()
    waiting_for_amount = State()
    waiting_for_participants = State()


# Команда /start
@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer(
        "Привет! Я помогу считать долги между друзьями.\n"
        "Команды:\n"
        "/add_participant - добавить участника\n"
        "/add_expense - добавить расход\n"
        "/show - показать итог"
    )


# Добавление участника
@dp.message(Command("add_participant"))
async def cmd_add_participant(message: Message, state: FSMContext):
    await message.answer("Введите имя участника:")
    await state.set_state(AddParticipant.waiting_for_name)


@dp.message(AddParticipant.waiting_for_name)
async def process_participant_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if name in participants:
        await message.answer(f"{name} уже есть в списке.")
    else:
        participants.add(name)
        await message.answer(f"Участник {name} добавлен.")
    await state.clear()


# Добавление расхода
@dp.message(Command("add_expense"))
async def cmd_add_expense(message: Message, state: FSMContext):
    if not participants:
        await message.answer("Сначала добавьте участников через /add_participant")
        return
    await message.answer(f"Кто платил? Введите имя из списка: {', '.join(participants)}")
    await state.set_state(AddExpense.waiting_for_payer)


@dp.message(AddExpense.waiting_for_payer)
async def process_payer(message: Message, state: FSMContext):
    payer = message.text.strip()
    if payer not in participants:
        await message.answer("Такого участника нет, попробуйте ещё раз.")
        return
    await state.update_data(payer=payer)
    await message.answer("Введите сумму (числом):")
    await state.set_state(AddExpense.waiting_for_amount)


@dp.message(AddExpense.waiting_for_amount)
async def process_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Введите корректную сумму (число > 0)")
        return
    await state.update_data(amount=amount)
    await message.answer(f"За кого делим расход? Введите имена через запятую из списка: {', '.join(participants)}\n"
                         "Или 'all' для всех участников.")
    await state.set_state(AddExpense.waiting_for_participants)


@dp.message(AddExpense.waiting_for_participants)
async def process_expense_participants(message: Message, state: FSMContext):
    data = await state.get_data()
    payer = data['payer']
    amount = data['amount']
    text = message.text.strip()

    if text.lower() == 'all':
        involved = participants.copy()
    else:
        involved = {p.strip() for p in text.split(',')}
        if not involved.issubset(participants):
            await message.answer("Некоторые имена отсутствуют в списке участников. Попробуйте снова.")
            return

    expenses.append({
        'payer': payer,
        'amount': amount,
        'participants': involved
    })

    await message.answer(f"Добавлен расход: {payer} заплатил {amount}, делится на {', '.join(involved)}")
    await state.clear()


@dp.message(Command("show"))
async def show_debts(message: Message):
    if not expenses:
        await message.answer("Пока нет расходов.")
        return

    # считаем балансы каждого участника
    debts = {p: 0 for p in participants}
    for exp in expenses:
        share = exp['amount'] / len(exp['participants'])
        for p in exp['participants']:
            if p == exp['payer']:
                debts[p] += exp['amount'] - share
            else:
                debts[p] -= share

    # разбиваем участников на должников и кредиторов
    debtors = {p: -debt for p, debt in debts.items() if debt < 0}  # сколько должен каждый (положительное число)
    creditors = {p: debt for p, debt in debts.items() if debt > 0}  # сколько должен получить каждый

    settlements = []

    # перебираем должников и кредиторов для свода долгов
    for debtor, debt_amount in debtors.items():
        if debt_amount == 0:
            continue
        for creditor, credit_amount in list(creditors.items()):
            if credit_amount == 0:
                continue
            pay = min(debt_amount, credit_amount)
            debt_amount -= pay
            creditors[creditor] -= pay
            settlements.append(f"{debtor} должен {creditor}: {pay:.2f} ₽")
            if debt_amount == 0:
                break

    if not settlements:
        await message.answer("Все долги погашены!")
        return

    await message.answer("Кто кому должен:\n" + "\n".join(settlements))


if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
