from aiogram import Router, F, Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from models.states import AddExpense
from utils.helpers import is_user_in_tusa
from bot import tusovki, user_sessions
from keyboards import get_main_menu_button, show_expense_menu
from datetime import datetime

router = Router()

@router.callback_query(F.data == "add_expense")
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

@router.callback_query(F.data.startswith("payer:"))
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

@router.message(AddExpense.waiting_for_amount)
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

@router.message(AddExpense.waiting_for_description)
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

@router.callback_query(F.data.startswith("target:"), AddExpense.waiting_for_targets)
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

@router.callback_query(F.data == "targets_done", AddExpense.waiting_for_targets)
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

def register_handlers(dp: Dispatcher):
    dp.include_router(router)