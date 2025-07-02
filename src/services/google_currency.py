import os
import logging
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

EXCHANGE_RATE_API_KEY = os.getenv('EXCHANGE_RATE_API_KEY') # ← вставь свой ключ
EXCHANGE_BASE_URL = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_RATE_API_KEY}/pair"
FRANKFURTER_URL = "https://api.frankfurter.app/latest"

async def fetch_from_exchange_api(from_cur: str, to_cur: str) -> str:
    url = f"{EXCHANGE_BASE_URL}/{from_cur.upper()}/{to_cur.upper()}"
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(url)
            data = r.json()
            if data["result"] == "success":
                return str(data["conversion_rate"])
            else:
                logger.warning(f"ExchangeRate API error for {from_cur}->{to_cur}: {data.get('error-type')}")
                return None
        except Exception as e:
            logger.error(f"ExchangeRate API exception for {from_cur}->{to_cur}: {e}")
            return None

async def fetch_from_frankfurter(from_cur: str, to_cur: str) -> str:
    url = f"{FRANKFURTER_URL}?from={from_cur.upper()}&to={to_cur.upper()}"
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(url)
            data = r.json()
            rate = data.get("rates", {}).get(to_cur.upper())
            if rate:
                return str(rate)
            else:
                logger.warning(f"Frankfurter.app no rate for {from_cur}->{to_cur}")
                return "N/A"
        except Exception as e:
            logger.error(f"Frankfurter.app error for {from_cur}->{to_cur}: {e}")
            return "N/A"

async def fetch_rate(from_cur: str, to_cur: str) -> tuple:
    rate = await fetch_from_exchange_api(from_cur, to_cur)
    if not rate:
        logger.info(f"Switching to Frankfurter for {from_cur}->{to_cur}")
        rate = await fetch_from_frankfurter(from_cur, to_cur)
    return (from_cur, to_cur, rate or "N/A")

async def get_currency_rates():
    pairs = [
        ("KZT", "AED"),  # тенге → дирхам
        ("KZT", "RUB"),  # тенге → рубль
        ("KZT", "KGS"),  # тенге → сом
        ("AED", "RUB"),
        ("AED", "KGS"),
        ("RUB", "KGS")
    ]
    
    semaphore = asyncio.Semaphore(5)  # одновременные запросы
    
    async def limited_fetch(pair):
        async with semaphore:
            return await fetch_rate(pair[0], pair[1])
    
    tasks = [limited_fetch(pair) for pair in pairs]
    return await asyncio.gather(*tasks)
