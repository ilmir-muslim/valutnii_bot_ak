# test_selenium.py
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.google_currency import get_currency_rate_sync


if __name__ == "__main__":
    print("Тенге → Дирхам:", get_currency_rate_sync("тенге", "дирхам"))
    print("Тенге → Рубль:", get_currency_rate_sync("тенге", "рубль"))
    print("Рубль → Сом:", get_currency_rate_sync("рубль", "сом"))