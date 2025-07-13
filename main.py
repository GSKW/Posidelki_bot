import logging
import uuid
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN
from datetime import datetime
from collections import defaultdict

logging.basicConfig(level=logging.INFO)

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)
dp = Dispatcher()

tusovki = {}
user_sessions = {}


class AddExpense(StatesGroup):
    waiting_for_amount = State()
    waiting_for_description = State()
    waiting_for_targets = State()

def get_main_menu_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu")]]
    )

def is_user_in_tusa(user_id: int) -> bool:
    if user_id not in user_sessions:
        return False
    tusa_id = user_sessions[user_id]
    return tusa_id in tusovki and user_id in tusovki[tusa_id]['participants']


async def send_main_menu(chat_id: int, tusa_id: str):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить расход", callback_data="add_expense")],
        [InlineKeyboardButton(text="📊 Показать долги", callback_data="show_debts")],
        [InlineKeyboardButton(text="📋 Список расходов", callback_data="expenses_list")]
    ])
    await bot.send_message(
        chat_id,
        f"Тусовка: <code>{tusa_id}</code>",
        reply_markup=kb
    )


async def show_expense_menu(chat_id: int):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить ещё расход", callback_data="add_expense")],
        [InlineKeyboardButton(text="📋 Список расходов", callback_data="expenses_list")],
        [InlineKeyboardButton(text="📊 Показать долги", callback_data="show_debts")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ])
    await bot.send_message(chat_id, "Выберите действие:", reply_markup=kb)


@dp.message(CommandStart(deep_link=True))
async def start_with_deeplink(message: Message, command: CommandStart):
    try:
        payload = command.args
        if not payload or not payload.startswith("join_"):
            await message.answer("❌ Некорректная ссылка.")
            return

        tusa_id = payload.split("_")[1]
        if tusa_id not in tusovki:
            await message.answer("❌ Тусовка не найдена.")
            return

        user_id = message.from_user.id
        username = message.from_user.username or message.from_user.first_name or "User"

        tusovki[tusa_id]['participants'][user_id] = username
        user_sessions[user_id] = tusa_id

        await message.answer(f"✅ {username}, ты в тусовке <code>{tusa_id}</code>!")
        await send_main_menu(message.chat.id, tusa_id)

        for uid in tusovki[tusa_id]['participants']:
            if uid != user_id:
                try:
                    await bot.send_message(uid, f"👤 {username} присоединился!")
                except Exception as e:
                    logging.error(f"Не удалось уведомить {uid}: {e}")

    except Exception as e:
        logging.error(f"Ошибка в deep link: {e}")
        await message.answer("❌ Ошибка при обработке ссылки.")


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "Привет! Я помогу учитывать общие траты.\n"
        "Создай тусовку /create_tusa или перейди по ссылке от друга."
    )


@dp.message(Command("create_tusa"))
async def create_tusa(message: Message):
    try:
        user_id = message.from_user.id
        username = message.from_user.username or message.from_user.first_name or "User"
        tusa_id = str(uuid.uuid4())[:8]

        tusovki[tusa_id] = {
            'participants': {user_id: username},
            'expenses': []
        }
        user_sessions[user_id] = tusa_id

        link = f"https://t.me/{(await bot.me()).username}?start=join_{tusa_id}"
        await message.answer(
            f"🎉 Тусовка создана! ID: <code>{tusa_id}</code>\n"
            f"Пригласи друзей: {link}"
        )
        await send_main_menu(message.chat.id, tusa_id)

    except Exception as e:
        logging.error(f"Ошибка создания тусовки: {e}")
        await message.answer("❌ Не удалось создать тусовку.")


@dp.callback_query(F.data == "main_menu")
async def main_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    if not is_user_in_tusa(user_id):
        await callback.answer("❌ Ты не в тусовке!", show_alert=True)
        return

    tusa_id = user_sessions[user_id]
    await callback.message.delete()
    await send_main_menu(callback.message.chat.id, tusa_id)
    await callback.answer()


@dp.callback_query(F.data == "add_expense")
async def add_expense_handler(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if not is_user_in_tusa(user_id):
        await callback.answer("❌ Ты не в тусовке!", show_alert=True)
        return

    tusa_id = user_sessions[user_id]
    participants = tusovki[tusa_id]['participants']

    buttons = [
        [InlineKeyboardButton(text=name, callback_data=f"payer:{uid}")]
        for uid, name in participants.items()
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text("Кто платил?", reply_markup=kb)
    await callback.answer()


@dp.callback_query(F.data == "expenses_list")
async def expenses_list(callback: CallbackQuery):
    user_id = callback.from_user.id
    if not is_user_in_tusa(user_id):
        await callback.answer("❌ Ты не в тусовке!", show_alert=True)
        return

    tusa_id = user_sessions[user_id]
    expenses = tusovki[tusa_id]['expenses']

    if not expenses:
        await callback.message.edit_text("📋 Список расходов пуст")
        await callback.answer()
        return

    text = "📋 Все расходы:\n\n"
    for i, exp in enumerate(expenses, 1):
        payer_name = tusovki[tusa_id]['participants'][exp['payer_id']]
        targets = ", ".join(tusovki[tusa_id]['participants'][uid] for uid in exp['targets'])
        text += (
            f"{i}. {exp['description']}\n"
            f"💸 {payer_name} потратил {exp['amount']:.2f} ₽\n"
            f"👥 Участники: {targets}\n"
            f"🕒 {exp['datetime'][:16]}\n\n"
        )

    await callback.message.edit_text(text, reply_markup=get_main_menu_button())
    await callback.answer()


@dp.callback_query(F.data == "show_debts")
async def show_debts(callback: CallbackQuery):
    user_id = callback.from_user.id
    if not is_user_in_tusa(user_id):
        await callback.answer("❌ Ты не в тусовке!", show_alert=True)
        return

    tusa_id = user_sessions[user_id]
    participants = tusovki[tusa_id]['participants']
    expenses = tusovki[tusa_id]['expenses']

    if not expenses:
        await callback.message.edit_text("Нет расходов для расчёта долгов")
        await callback.answer()
        return

    # Рассчитываем долги
    debts = defaultdict(float)
    for exp in expenses:
        share = exp['amount'] / len(exp['targets'])
        for uid in exp['targets']:
            if uid == exp['payer_id']:
                debts[uid] += exp['amount'] - share
            else:
                debts[uid] -= share

    # Формируем списки должников и кредиторов
    debtors = []
    creditors = []
    for uid, amount in debts.items():
        if amount < -0.01:
            debtors.append((uid, -amount))
        elif amount > 0.01:
            creditors.append((uid, amount))

    debtors.sort(key=lambda x: x[1], reverse=True)
    creditors.sort(key=lambda x: x[1], reverse=True)

    text = "📊 Итоговые долги:\n\n"

    if not debtors and not creditors:
        text += "Все расчеты сведены 🎉"
    else:
        i, j = 0, 0
        while i < len(debtors) and j < len(creditors):
            debtor_id, debt = debtors[i]
            creditor_id, credit = creditors[j]

            amount = min(debt, credit)

            debtor_name = participants[debtor_id]
            creditor_name = participants[creditor_id]

            text += f"• {debtor_name} ➝ {creditor_name}: {amount:.2f} ₽\n"

            debtors[i] = (debtor_id, debt - amount)
            creditors[j] = (creditor_id, credit - amount)

            if debtors[i][1] < 0.01:
                i += 1
            if creditors[j][1] < 0.01:
                j += 1

    await callback.message.edit_text(text, reply_markup=get_main_menu_button())
    await callback.answer()



@dp.callback_query(F.data.startswith("payer:"))
async def select_payer(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if not is_user_in_tusa(user_id):
        await callback.answer("❌ Ты не в тусовке!", show_alert=True)
        return

    payer_id = int(callback.data.split(":")[1])
    tusa_id = user_sessions[user_id]

    if payer_id not in tusovki[tusa_id]['participants']:
        await callback.answer("❌ Этот участник не в тусовке!", show_alert=True)
        return

    payer_name = tusovki[tusa_id]['participants'][payer_id]

    await state.update_data(payer_id=payer_id, payer_name=payer_name)
    await state.set_state(AddExpense.waiting_for_amount)

    await callback.message.edit_text(
        f"Плательщик: {payer_name}\n\n"
        "💰 Введите сумму расхода:"
    )
    await callback.answer()


@dp.message(AddExpense.waiting_for_amount)
async def process_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректную сумму (число больше 0)")
        return

    await state.update_data(amount=amount)
    await state.set_state(AddExpense.waiting_for_description)
    await message.answer("📝 Введите описание расхода (например, 'Ужин в кафе'):")


@dp.message(AddExpense.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    description = message.text.strip()
    if not description:
        await message.answer("❌ Описание не может быть пустым")
        return

    await state.update_data(description=description)
    await state.set_state(AddExpense.waiting_for_targets)

    user_id = message.from_user.id
    tusa_id = user_sessions[user_id]
    participants = tusovki[tusa_id]['participants']

    buttons = []
    row = []
    for uid, name in participants.items():
        row.append(InlineKeyboardButton(text=name, callback_data=f"target:{uid}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([
        InlineKeyboardButton(text="✅ Готово", callback_data="targets_done"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="main_menu")
    ])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Выберите участников, на которых делится расход:", reply_markup=kb)


@dp.callback_query(F.data.startswith("target:"), AddExpense.waiting_for_targets)
async def select_target(callback: CallbackQuery, state: FSMContext):
    target_id = int(callback.data.split(":")[1])
    data = await state.get_data()

    if "targets" not in data:
        data["targets"] = set()

    if target_id in data["targets"]:
        data["targets"].remove(target_id)
    else:
        data["targets"].add(target_id)

    await state.update_data(targets=data["targets"])

    tusa_id = user_sessions[callback.from_user.id]
    selected_names = [
        tusovki[tusa_id]['participants'][uid]
        for uid in data["targets"]
    ]

    text = "Выбранные участники:\n" + ("\n".join(selected_names) if selected_names else "❌ Никого не выбрано")
    await callback.message.edit_text(
        text + "\n\nПродолжайте выбирать или нажмите 'Готово'",
        reply_markup=callback.message.reply_markup
    )
    await callback.answer()


@dp.callback_query(F.data == "targets_done", AddExpense.waiting_for_targets)
async def finish_targets(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    if not data.get("targets"):
        await callback.answer("❌ Нужно выбрать хотя бы одного участника!", show_alert=True)
        return

    tusa_id = user_sessions[callback.from_user.id]
    payer_name = data["payer_name"]
    amount = data["amount"]
    description = data.get("description", "без описания")

    tusovki[tusa_id]['expenses'].append({
        "payer_id": data["payer_id"],
        "amount": amount,
        "description": description,
        "targets": set(data["targets"]),
        "datetime": datetime.now().isoformat()
    })

    target_names = [
        tusovki[tusa_id]['participants'][uid]
        for uid in data["targets"]
    ]

    await callback.message.edit_text(
        f"✅ Расход добавлен!\n\n"
        f"💸 {payer_name} потратил {amount:.2f} ₽\n"
        f"📝 {description}\n"
        f"👥 Участники: {', '.join(target_names)}"
    )

    await state.clear()
    await show_expense_menu(callback.message.chat.id)
    await callback.answer()


@dp.message(Command("debug"))
async def debug(message: Message):
    debug_info = (
        f"Тусовки: {list(tusovki.keys())}\n"
        f"Сессии: {user_sessions}\n"
        f"Ваш ID: {message.from_user.id}"
    )
    await message.answer(f"<code>{debug_info}</code>")


if __name__ == "__main__":
    import asyncio

    logging.info("Бот запускается...")
    asyncio.run(dp.start_polling(bot))