import asyncio
import logging
from aiogram import Router, types, Bot
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
from services import google_currency, p2p_rates
from datetime import datetime

router = Router()
logger = logging.getLogger(__name__)

# Состояние активных пользователей
active_users = {}  # {chat_id: message_id}

@router.message(Command("start"))
async def cmd_start(message: types.Message, bot: Bot):
    # Отправляем сообщение с котировками
    sent_message = await message.answer("⌛ Загружаю данные...")
    active_users[message.chat.id] = sent_message.message_id
    
    # Обновляем данные
    await update_and_send_rates(message.chat.id, bot)

@router.message(Command("stop"))
async def cmd_stop(message: types.Message):
    if message.chat.id in active_users:
        del active_users[message.chat.id]
        await message.answer("✅ Обновления остановлены. Для возобновления отправьте /start")
    else:
        await message.answer("ℹ️ Обновления не были запущены. Отправьте /start для начала")

async def update_and_send_rates(chat_id: int, bot: Bot):
    try:
        # Получаем свежие данные
        response = await fetch_new_rates()
        
        # Обновляем сообщение
        if chat_id in active_users:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=active_users[chat_id],
                text=response
            )
            logger.info(f"Updated rates for user {chat_id}")
    except TelegramBadRequest as e:
        if "message to edit not found" in str(e).lower():
            logger.warning(f"Message not found for user {chat_id}, removing from active")
            if chat_id in active_users:
                del active_users[chat_id]
    except Exception as e:
        logger.error(f"Update error for user {chat_id}: {e}")

async def fetch_new_rates():
    logger.info("Fetching new rates data...")
    update_time = datetime.now().strftime("%H:%M:%S")
    response = f"👋 <b>Актуальные курсы валют</b> ({update_time})\n\n"
    
    try:
        # Запускаем задачи
        currency_task = asyncio.create_task(google_currency.get_currency_rates())
        
        # ВРЕМЕННО: Фиктивные P2P-данные для тестов
        p2p_data = [("Binance", 90.5), ("Bybit", 91.2), ("OKX", 90.8)]
        
        # Получаем валютные курсы
        currency_rates = await asyncio.wait_for(currency_task, timeout=30.0)
        
        # Форматируем ответ
        if currency_rates:
            currency_lines = []
            for from_cur, to_cur, rate in currency_rates:
                currency_lines.append(f"{from_cur.upper():<5} → {to_cur.upper():<5} {rate:>8}")
            response += "📊 <b>Валютные курсы:</b>\n<code>" + "\n".join(currency_lines) + "</code>\n\n"
        else:
            response += "⚠️ <b>Валютные курсы временно недоступны</b>\n\n"
        
        # Форматируем P2P данные
        if p2p_data:
            p2p_lines = []
            for exchange, rate in p2p_data:
                rate_str = f"{rate:.2f}" if isinstance(rate, float) else str(rate)
                p2p_lines.append(f"{exchange:<8} {rate_str:>10}")
            response += "💱 <b>P2P USDT/RUB:</b>\n<code>" + "\n".join(p2p_lines) + "</code>"
        else:
            response += "⚠️ <b>P2P курсы временно недоступны</b>"
            
    except Exception as e:
        logger.exception(f"Error fetching rates: {e}")
        response = "⚠️ Произошла ошибка при получении данных. Попробуйте позже."
    
    return response

async def periodic_update(bot: Bot):
    """Фоновая задача для периодического обновления"""
    while True:
        try:
            logger.info("Running periodic update...")
            
            # Обновляем всех активных пользователей
            users = list(active_users.items())
            for chat_id, message_id in users:
                await update_and_send_rates(chat_id, bot)
                
            # Интервал обновления - 30 секунд
            await asyncio.sleep(30)
            
        except Exception as e:
            logger.exception(f"Periodic update error: {e}")
            await asyncio.sleep(10)