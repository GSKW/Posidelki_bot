from aiogram import Router, F, Dispatcher
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from models.states import AddExpense
from utils.helpers import is_user_in_tusa
from bot import tusovki, user_sessions, bot
from bot.keyboards import send_main_menu
import uuid
from utils.logger import setup_logger
import logging

router = Router()
logger = setup_logger()

def message_log(text, user_id):
    return f'''
    Message sent to:
        {user_id}
    Message: 
        {text}
    '''

@router.message(CommandStart(deep_link=True))
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

        text_message = f"✅ {username}, ты в тусовке <code>{tusa_id}</code>!"

        await message.answer(text_message)
        await send_main_menu(message.chat.id, tusa_id)

        logger.info(message_log(text_message, user_id))

        for uid in tusovki[tusa_id]['participants']:
            if uid != user_id:
                try:
                    await bot.send_message(uid, f"👤 {username} присоединился!")
                except Exception as e:
                    logger.error(f"Не удалось уведомить {uid}: {e}")

    except Exception as e:
        logger.error(f"Ошибка в deep link: {e}")
        await message.answer("❌ Ошибка при обработке ссылки.")

@router.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "Привет! Я помогу учитывать общие траты.\n"
        "Создай тусовку /create_tusa или перейди по ссылке от друга."
    )

@router.message(Command("create_tusa"))
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

@router.message(Command("debug"))
async def debug(message: Message):
    debug_info = (
        f"Тусовки: {list(tusovki.keys())}\n"
        f"Сессии: {user_sessions}\n"
        f"Ваш ID: {message.from_user.id}"
    )
    await message.answer(f"<code>{debug_info}</code>")

def register_handlers(dp: Dispatcher):
    dp.include_router(router)