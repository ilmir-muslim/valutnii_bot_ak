from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import logging
import time


def get_okx_average_price(pair: str):
    """Возвращает среднюю цену для заданной валютной пары на OKX"""
    try:
        if "/" not in pair:
            raise ValueError("Формат пары должен быть 'USDT/USD'")

        asset, fiat = pair.upper().split("/")
        base_url = f"https://www.okx.com/ru/p2p-markets/{fiat.lower()}/buy-{asset.lower()}"
        logging.info(f"Загрузка страницы OKX: {base_url}")

        # Настройка Chrome
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )

        # Автоматическая установка драйвера
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        try:
            # Загрузка страницы
            driver.get(base_url)
            logging.info(f"Фактический URL: {driver.current_url}")

            # Ожидание появления контейнера с ценами
            WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span.price"))
            )

            # Сбор цен
            price_elements = driver.find_elements(By.CSS_SELECTOR, "span.price")

            prices = []
            for element in price_elements:
                try:
                    text = element.text.strip()
                    # Удаляем текст валюты и пробелы
                    price_text = (
                        text.replace(fiat, "").replace(" ", "").replace(",", ".")
                    )
                    # Извлекаем число
                    price = float(price_text)
                    prices.append(price)
                    logging.info(f"Найдена цена на OKX: {price} {fiat}")
                except Exception as e:
                    logging.warning(
                        f"Ошибка обработки элемента OKX: '{text}' - {str(e)}"
                    )
                    continue

            # Расчет средней цены
            if prices:
                avg_price = round(sum(prices) / len(prices), 2)
                logging.info(
                    f"Найдено {len(prices)} цен на OKX, средняя: {avg_price} {fiat}"
                )
                return avg_price
            else:
                logging.warning("Цены на OKX не найдены")
                return None

        except Exception as e:
            logging.error(f"Ошибка при работе с OKX: {str(e)}", exc_info=True)
            return None
        finally:
            driver.quit()
            logging.info("Браузер OKX закрыт")

    except Exception as e:
        logging.error(f"Критическая ошибка при работе с OKX: {str(e)}", exc_info=True)
        return None


if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # Пример использования
    pair = "USDT/EGP"
    average_price = get_okx_average_price(pair)

    if average_price is not None:
        print(f"Средняя цена на OKX {pair}: {average_price}")
    else:
        print("Не удалось получить цену с OKX")