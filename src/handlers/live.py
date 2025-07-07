import asyncio
from aiogram import Bot, Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.markdown import hbold
from datetime import datetime
from tasks.generator import generate_exchange_text
from utils.user_storage import load_user_ids, save_user_ids

router = Router()
active_message: dict[int, int] = {}  # user_id: message_id
USER_IDS: set[int] = load_user_ids()

REFRESH_BUTTON = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_rates")]
    ]
)

def get_now_ts() -> str:
    return datetime.now().strftime("⏱ Последнее обновление: %d.%m.%Y %H:%M")

async def send_or_edit_rates(user_id: int, bot: Bot):
    try:
        text = await generate_exchange_text()
        text += f"\n\n{get_now_ts()}"

        if user_id in active_message:
            await bot.edit_message_text(
                chat_id=user_id,
                message_id=active_message[user_id],
                text=text,
                reply_markup=REFRESH_BUTTON
            )
        else:
            sent = await bot.send_message(
                chat_id=user_id,
                text=text,
                reply_markup=REFRESH_BUTTON
            )
            active_message[user_id] = sent.message_id
    except Exception as e:
        await bot.send_message(chat_id=user_id, text=f"❌ Ошибка при обновлении: {e}")

@router.message(F.text == "/start")
async def cmd_start(message: Message, bot: Bot):
    user_id = message.from_user.id
    if user_id not in USER_IDS:
        USER_IDS.add(user_id)
        save_user_ids(USER_IDS)  # сохраняем в user_data.json

    await message.answer("⏳ Данные загружаются...")
    await send_or_edit_rates(user_id, bot)

@router.callback_query(F.data == "refresh_rates")
async def refresh_callback(callback: CallbackQuery, bot: Bot):
    await callback.answer("Обновляем...")
    await send_or_edit_rates(callback.from_user.id, bot)
