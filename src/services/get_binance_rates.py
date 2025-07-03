import aiohttp
import asyncio
import logging

logger = logging.getLogger(__name__)

async def get_binance_rates(pair: str):
    try:
        if "/" not in pair:
            raise ValueError("Неверный формат валютной пары. Используй формат 'USDT/USD'")

        asset, fiat = pair.upper().split("/")

        url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
        payload = {
            "asset": asset,
            "fiat": fiat,
            "page": 1,
            "rows": 20,
            "tradeType": "SELL"
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate, br"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=20) as response:
                if response.status != 200:
                    return f"Ошибка Binance API: HTTP {response.status}"

                data = await response.json()
                offers = data.get("data", [])

                if not offers:
                    if fiat == "RUB":
                        return f"Binance не возвращает офферы для {pair} — возможно, рубль больше не поддерживается."
                    return f"Нет офферов для пары {pair} на Binance."

                prices = []
                for item in offers:
                    try:
                        raw_price = item["adv"]["price"]
                        clean_price = float(raw_price.replace(",", "").replace(" ", ""))
                        prices.append(clean_price)
                    except Exception as e:
                        logger.warning(f"Binance: Ошибка парсинга цены: {e}")
                        continue

                if not prices:
                    return f"Не удалось извлечь цены для {pair}."

                avg_price = round(sum(prices) / len(prices), 2)

                return avg_price

    except Exception as e:
        logger.error(f"Binance error: {e}")
        return f"Ошибка получения данных для {pair}: {e}"


