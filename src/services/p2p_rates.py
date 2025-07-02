import logging
import aiohttp
import asyncio
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

async def get_binance_rate():
    try:
        url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
        payload = {
            "proMerchantAds": False,
            "page": 1,
            "rows": 20,
            "payTypes": ["Tinkoff", "RosBank"],
            "countries": [],
            "publisherType": None,
            "asset": "USDT",
            "fiat": "RUB",
            "tradeType": "SELL"
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=20) as response:
                data = await response.json()
                
                # Проверка наличия данных
                if not data.get("data") or not isinstance(data["data"], list):
                    logger.warning("Binance: Invalid response structure")
                    return "N/A"
                
                # Ищем первый действительный курс
                for item in data["data"]:
                    try:
                        if "adv" in item and "price" in item["adv"]:
                            price = item["adv"]["price"]
                            # Удаление возможных разделителей тысяч
                            price = price.replace(',', '').replace(' ', '')
                            return float(price)
                    except (KeyError, ValueError, TypeError) as e:
                        logger.warning(f"Binance item error: {e}")
                        continue
                
                logger.warning("Binance: No valid offers found")
                return "N/A"
                
    except asyncio.TimeoutError:
        logger.warning("Binance timeout")
        return "N/A"
    except Exception as e:
        logger.error(f"Binance error: {e}")
        return "N/A"

async def get_bybit_rate():
    try:
        url = "https://www.bybit.com/fiat/trade/otc/?actionType=sell&token=USDT&fiat=RUB"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=20) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Сохраняем объект soup в файл
                with open('bybit_soup.pkl', 'wb') as f:
                    import pickle
                    pickle.dump(soup, f)
                
                # Расширенный поиск элементов
                price_elements = soup.select(
                    ".amount, .fiat-otc-list__table-price-amount, .price-amount, .bybit-web-fiat-price__price"
                )
                
                if price_elements:
                    return float(price_elements[0].text.strip())
                
                logger.warning("Bybit: No price element found")
                return "N/A"
                
    except asyncio.TimeoutError:
        logger.warning("Bybit timeout")
        return "N/A"
    except Exception as e:
        logger.error(f"Bybit error: {e}")
        return "N/A"

async def get_okx_rate():
    try:
        url = "https://www.okx.com/ru/p2p-markets/rub/sell/usdt"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=20) as response:
                html = await response.text()
                
                # Сохраняем HTML для отладки
                with open('debug_okx.html', 'w', encoding='utf-8') as f:
                    f.write(html)
                
                soup = BeautifulSoup(html, 'html.parser')
                
                # Новые селекторы для 2025 года
                price_div = soup.select_one(
                    ".market-price, .price-amount, .okui-typography-number, .price-value"
                )
                
                if price_div:
                    price_text = price_div.text.strip()
                    # Очистка текста
                    price_text = price_text.replace(',', '.').replace('\xa0', '').replace(' ', '')
                    return float(price_text)
                
                logger.warning("OKX: No price element found")
                return "N/A"
                
    except asyncio.TimeoutError:
        logger.warning("OKX timeout")
        return "N/A"
    except Exception as e:
        logger.error(f"OKX error: {e}")
        return "N/A"
    
async def get_p2p_rates():
    binance_task = asyncio.create_task(get_binance_rate())
    bybit_task = asyncio.create_task(get_bybit_rate())
    okx_task = asyncio.create_task(get_okx_rate())
    
    binance = await binance_task
    bybit = await bybit_task
    okx = await okx_task
    
    return [
        ("Binance", binance),
        ("Bybit", bybit),
        ("OKX", okx)
    ]