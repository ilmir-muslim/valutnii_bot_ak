import aiohttp
import asyncio
import logging

logger = logging.getLogger(__name__)

# services/get_binance_rates.py

async def get_binance_prices(pair: str) -> dict | str:
    try:
        if "/" not in pair:
            raise ValueError("Формат пары должен быть 'USDT/USD'")
        asset, fiat = pair.upper().split("/")

        async def fetch_price(trade_type: str):
            url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
            payload = {
                "asset": asset,
                "fiat": fiat,
                "tradeType": trade_type,
                "page": 1,
                "rows": 1
            }
            headers = {
                "User-Agent": "Mozilla/5.0", "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    data = await response.json()
                    offers = data.get("data", [])
                    if not offers:
                        return None
                    raw_price = offers[0]["adv"]["price"]
                    return float(raw_price.replace(",", "").replace(" ", ""))

        buy_price = await fetch_price("BUY")
        sell_price = await fetch_price("SELL")

        return {"buy": buy_price, "sell": sell_price}

    except Exception as e:
        logger.error(f"Binance error: {e}")
        return f"Ошибка получения данных для {pair}: {e}"



