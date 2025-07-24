from aiogram import Router, F, Dispatcher
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from models.states import AddExpense
from utils.helpers import is_user_in_tusa
from bot import tusovki, user_sessions
from keyboards import get_main_menu_button, send_main_menu, show_expense_menu

router = Router()

@router.callback_query(F.data == "main_menu")
async def main_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    if not is_user_in_tusa(user_id):
        await callback.answer("❌ Ты не в тусовке!", show_alert=True)
        return

    tusa_id = user_sessions[user_id]
    await callback.message.delete()
    await send_main_menu(callback.message.chat.id, tusa_id)
    await callback.answer()

@router.callback_query(F.data == "expenses_list")
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
            f"🕒 {exp['datetime'][:16].replace('T', ' ')}\n\n"
        )

    await callback.message.edit_text(text, reply_markup=get_main_menu_button())
    await callback.answer()

def register_handlers(dp: Dispatcher):
    dp.include_router(router)