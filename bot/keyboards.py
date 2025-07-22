from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from bot import bot

def get_main_menu_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад в меню", callback_data="main_menu")]]
    )

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