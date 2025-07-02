import pytest
import asyncio
import sys
import os
from aioresponses import aioresponses

# Исправленный импорт
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.google_currency import get_currency_rates

@pytest.mark.asyncio
async def test_get_currency_rates_success():
    with aioresponses() as m:
        base_url = "https://www.google.com/search?q=1+{}+в+{}"
        pairs = [
            ("тенге", "дирхам"),
            ("тенге", "рубль"),
            ("тенге", "сом"),
            ("дирхам", "рубль"),
            ("дирхам", "сом"),
            ("рубль", "сом")
        ]
        
        # Обновленные фиктивные ответы
        for from_cur, to_cur in pairs:
            url = base_url.format(from_cur, to_cur)
            html_content = """
            <html>
                <body>
                    <div class="BNeawe iBp4i AP7Wnd">0.123</div>
                </body>
            </html>
            """
            m.get(url, status=200, body=html_content)

        results = await get_currency_rates()
        assert len(results) == len(pairs)
        for (from_cur, to_cur, rate) in results:
            assert rate == "0.123"

@pytest.mark.asyncio
async def test_get_currency_rates_html_changed():
    with aioresponses() as m:
        base_url = "https://www.google.com/search?q=1+{}+в+{}"
        pairs = [
            ("тенге", "дирхам"),
            ("тенге", "рубль"),
            ("тенге", "сом"),
            ("дирхам", "рубль"),
            ("дирхам", "сом"),
            ("рубль", "сом")
        ]
        
        for from_cur, to_cur in pairs:
            url = base_url.format(from_cur, to_cur)
            m.get(url, status=200, body='<div class="wrong-class">0.123</div>')

        results = await get_currency_rates()
        assert len(results) == len(pairs)
        for (from_cur, to_cur, rate) in results:
            assert rate == "N/A"

@pytest.mark.asyncio
async def test_get_currency_rates_network_error():
    with aioresponses() as m:
        base_url = "https://www.google.com/search?q=1+{}+в+{}"
        pairs = [
            ("тенге", "дирхам"),
            ("тенге", "рубль"),
            ("тенге", "сом"),
            ("дирхам", "рубль"),
            ("дирхам", "сом"),
            ("рубль", "сом")
        ]
        
        for from_cur, to_cur in pairs:
            url = base_url.format(from_cur, to_cur)
            m.get(url, status=500)

        results = await get_currency_rates()
        assert len(results) == len(pairs)
        for (from_cur, to_cur, rate) in results:
            assert rate == "N/A"