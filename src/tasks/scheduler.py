import asyncio
import logging
from aiogram import Bot

from handlers.live import send_or_edit_rates, USER_IDS

logger = logging.getLogger(__name__)

async def periodic_update(bot: Bot):
    while True:
        try:
            for uid in USER_IDS:
                await send_or_edit_rates(uid, bot)
        except Exception as e:
            logger.error(f"[!] Ошибка автообновления сообщений: {e}")
        await asyncio.sleep(300) 
