import logging
import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from handlers import basic

# Расширенная конфигурация логирования
logger = logging.getLogger()
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Файловый обработчик
file_handler = logging.FileHandler("bot.log", encoding="utf-8")
file_handler.setFormatter(formatter)

# Консольный обработчик
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)

async def main():
    load_dotenv()
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN environment variable is not set!")
        raise ValueError("BOT_TOKEN environment variable is not set!")

    logger.info("Starting bot...")
    
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    
    dp = Dispatcher()
    dp.include_router(basic.router)
    
    # Запускаем фоновую задачу для периодического обновления
    asyncio.create_task(basic.periodic_update(bot))
    
    logger.info("Bot is ready to receive messages")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.exception(f"Critical error: {e}")