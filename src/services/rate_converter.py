import logging
from core.calculator import calculate_aed_rate
from services.get_bybit_rates import get_bybit_average_price
from services.get_binance_rates import get_binance_rates

logger = logging.getLogger(__name__)

SOURCE_MAP = {
    "RUB": "bybit",
    "KZT": "binance",
    "KGS": "binance",
    "AED": "bybit"
}

async def get_fiat_price(currency: str) -> float | None:
    """Получает цену USDT в заданной фиатной валюте"""
    source = SOURCE_MAP.get(currency.upper(), "bybit")
    pair = f"USDT/{currency.upper()}"

    if source == "bybit":
        return get_bybit_average_price(pair)
    elif source == "binance":
        return await get_binance_rates(pair)
    else:
        logger.warning(f"Неизвестный источник для {currency}, использую bybit")
        return get_bybit_average_price(pair)

async def convert_fiat_to_fiat(fiat_from: str, fiat_to: str, markup: float = 0.035) -> dict | None:
    """
    Расчёт курса между двумя фиатами через USDT:
    fiat_from → USDT → fiat_to
    """
    buy_price = await get_fiat_price(fiat_from)
    sell_price = await get_fiat_price(fiat_to)

    return calculate_aed_rate(buy_price, sell_price, markup)
