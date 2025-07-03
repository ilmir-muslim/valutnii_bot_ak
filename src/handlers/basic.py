import asyncio
import logging
from datetime import datetime
from aiogram import Router, types, Bot
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
from services import fiat_rates
from services.get_binance_rates import get_binance_rates
from services.get_bybit_rates import get_bybit_average_price
from services.get_okx_rates import get_okx_average_price
from functools import partial
from concurrent.futures import ThreadPoolExecutor

router = Router()
logger = logging.getLogger(__name__)

active_users = {}  # {chat_id: message_id}
executor = ThreadPoolExecutor(max_workers=2)


@router.message(Command("start"))
async def cmd_start(message: types.Message, bot: Bot):
    sent_message = await message.answer("⌛ Загружаю данные...")
    active_users[message.chat.id] = sent_message.message_id
    await update_and_send_rates(message.chat.id, bot)


@router.message(Command("stop"))
async def cmd_stop(message: types.Message):
    if message.chat.id in active_users:
        del active_users[message.chat.id]
        await message.answer("✅ Обновления остановлены. Для возобновления отправьте /start")
    else:
        await message.answer("ℹ️ Обновления не были запущены. Отправьте /start для начала")


async def fetch_current_data():
    """Получает актуальные данные из всех источников"""
    try:
        logger.info("Получение актуальных данных...")
        
        # Асинхронные задачи для API
        currency_task = asyncio.create_task(fiat_rates.get_currency_rates())
        binance_task = asyncio.create_task(get_binance_rates("USDT/AED"))
        
        # Синхронные функции через executor
        loop = asyncio.get_running_loop()
        bybit_func = partial(get_bybit_average_price, "USDT/AED")
        okx_func = partial(get_okx_average_price, "USDT/AED")
        
        bybit_task = loop.run_in_executor(executor, bybit_func)
        okx_task = loop.run_in_executor(executor, okx_func)

        # Ждем завершения всех задач
        results = await asyncio.gather(
            currency_task, 
            binance_task, 
            bybit_task, 
            okx_task,
            return_exceptions=True  # Позволяет продолжить при ошибках в отдельных задачах
        )
        
        return results
    except Exception as e:
        logger.exception(f"Ошибка при получении данных: {e}")
        return [None, None, None, None]


async def format_response(data, update_time):
    """Формирует ответ на основе полученных данных"""
    response = f"👋 <b>Актуальные курсы валют</b> ({update_time})\n\n"
    currency_rates, binance_rate, bybit_rate, okx_rate = data

    if currency_rates and not isinstance(currency_rates, Exception):
        currency_lines = []
        for from_cur, to_cur, rate in currency_rates:
            currency_lines.append(f"{from_cur.upper():<5} → {to_cur.upper():<5} {rate:>8}")
        response += "📊 <b>Валютные курсы:</b>\n<code>" + "\n".join(currency_lines) + "</code>\n\n"
    else:
        response += "⚠️ <b>Валютные курсы временно недоступны</b>\n\n"

    p2p_data = [
        ("Binance", binance_rate),
        ("Bybit", bybit_rate),
        ("OKX", okx_rate)
    ]
    
    p2p_lines = []
    for exchange, rate in p2p_data:
        if isinstance(rate, (float, int)):
            rate_str = f"{rate:.2f}"
        elif isinstance(rate, Exception):
            rate_str = f"Ошибка: {type(rate).__name__}"
        else:
            rate_str = str(rate)
        
        p2p_lines.append(f"{exchange:<8} {rate_str:>10}")
    
    response += "💱 <b>P2P USDT/AED:</b>\n<code>" + "\n".join(p2p_lines) + "</code>"
    
    return response


async def update_and_send_rates(chat_id: int, bot: Bot):
    """Обновляет сообщение с актуальными данными для конкретного пользователя"""
    try:
        # Получаем свежие данные
        current_data = await fetch_current_data()
        update_time = datetime.now().strftime("%H:%M:%S")
        
        # Формируем ответ
        response = await format_response(current_data, update_time)

        # Обновляем сообщение пользователя
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


async def periodic_update(bot: Bot):
    """Периодическое обновление данных для всех активных пользователей"""
    while True:
        try:
            # Получаем актуальные данные
            current_data = await fetch_current_data()
            update_time = datetime.now().strftime("%H:%M:%S")
            
            # Формируем сообщение с актуальными данными
            response = await format_response(current_data, update_time)

            # Обновляем сообщения у активных пользователей
            logger.info("Обновление всех пользователей...")
            users = list(active_users.items())
            for chat_id, message_id in users:
                try:
                    await bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=response
                    )
                except TelegramBadRequest as e:
                    if "message to edit not found" in str(e).lower():
                        logger.warning(f"Message not found for user {chat_id}, removing from active")
                        if chat_id in active_users:
                            del active_users[chat_id]
                except Exception as e:
                    logger.error(f"Error updating user {chat_id}: {e}")

            # Пауза 5 минут до следующего обновления
            await asyncio.sleep(300)
            
        except Exception as e:
            logger.exception(f"Ошибка в periodic_update: {e}")
            await asyncio.sleep(60)  # Пауза при ошибке