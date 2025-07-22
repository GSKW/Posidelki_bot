from utils.logger import setup_logger
from utils.arts import banner
from aiogram import Dispatcher
from bot import bot
from handlers import commands, callbacks, expenses, debts

logger = setup_logger()

dp = Dispatcher()

logger.banner(banner)

# Регистрация обработчиков
commands.register_handlers(dp)
logger.info("💦 Commands success!")

callbacks.register_handlers(dp)
logger.info("🍆 Callbacks success!")

expenses.register_handlers(dp)
logger.info("🍑 Expenses success!")

debts.register_handlers(dp)
logger.info("🍒 Debts success!\n")

async def main():
    logger.info("🥵 Bot polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())