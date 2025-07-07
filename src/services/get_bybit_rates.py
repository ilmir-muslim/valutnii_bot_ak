from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging
import re

# services/get_bybit_rates.py

def get_bybit_prices(pair: str) -> dict | None:
    """Возвращает первую цену покупки и продажи для заданной валютной пары на Bybit"""
    try:
        if "/" not in pair:
            raise ValueError("Формат пары должен быть 'USDT/USD'")

        asset, fiat = pair.upper().split("/")
        url_template = "https://www.bybit.com/ru-RU/fiat/trade/otc/{trade_type}/{asset}/{fiat}"

        def fetch_price(trade_type):
            chrome_options = Options()
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("user-agent=Mozilla/5.0 ...")

            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            driver.get(url_template.format(trade_type=trade_type, asset=asset, fiat=fiat))

            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "span.price-amount"))
                )
                price_el = driver.find_elements(By.CSS_SELECTOR, "span.price-amount")
                if not price_el:
                    return None
                text = price_el[0].text.replace(fiat, "").replace(",", ".").strip()
                return float(re.sub(r"[^\d.]", "", text))
            finally:
                driver.quit()

        return {
            "buy": fetch_price("buy"),    # USDT покупают — ты продаёшь фиат
            "sell": fetch_price("sell"),  # USDT продают — ты покупаешь фиат
        }

    except Exception as e:
        logging.error(f"Bybit error: {e}", exc_info=True)
        return None
