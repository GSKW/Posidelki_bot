from aiogram import Router, F, Dispatcher
from aiogram.types import CallbackQuery
from collections import defaultdict
from utils.helpers import is_user_in_tusa
from bot import tusovki, user_sessions
from keyboards import get_main_menu_button

router = Router()

@router.callback_query(F.data == "show_debts")
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

    debts = defaultdict(float)
    for exp in expenses:
        share = exp['amount'] / len(exp['targets'])
        for uid in exp['targets']:
            if uid == exp['payer_id']:
                debts[uid] += exp['amount'] - share
            else:
                debts[uid] -= share

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

def register_handlers(dp: Dispatcher):
    dp.include_router(router)