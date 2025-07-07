from services.fiat_rates import fetch_rate
from services.get_bybit_rates import get_bybit_prices
from services.get_binance_rates import get_binance_prices

P2P_CORRECTION = 1        # буфер на первую цену
MARKUP_BUY = 0.035           # Наценка клиента при продаже AED (получает фиат)
MARKDOWN_SELL = 0.035        # Скидка клиенту при покупке AED (отдаёт фиат)
GOOGLE_MARKUP = 0.03         # Наценка на Google курс
CURRENCIES = {
    "RUB": "bybit",
    "KZT": "binance",
    "KGS": "binance",
}

async def generate_exchange_text() -> str:
    results = []
    aed_prices = get_bybit_prices("USDT/AED")  # AED продают/покупают

    if not aed_prices or not aed_prices.get("buy") or not aed_prices.get("sell"):
        return "❌ Не удалось получить цены для USDT/AED"

    for fiat, source in CURRENCIES.items():
        if source == "bybit":
            fiat_prices = get_bybit_prices(f"USDT/{fiat}")
        else:
            fiat_prices = await get_binance_prices(f"USDT/{fiat}")

        if not fiat_prices or isinstance(fiat_prices, str):
            results.append(f"❌ Не удалось получить цены для USDT/{fiat}")
            continue

        try:
            # Покупка AED за фиат (отдаём фиат → получаем AED) — добавляем 3.5%
            raw_buy = fiat_prices["sell"] / aed_prices["buy"]
            adjusted_buy = raw_buy * P2P_CORRECTION
            final_buy = round(adjusted_buy * (1 + MARKUP_BUY), 2)

            # Покупка фиата за AED (отдаём AED → получаем фиат) — вычитаем 3.5%
            raw_sell = fiat_prices["buy"] / aed_prices["sell"]
            adjusted_sell = raw_sell * P2P_CORRECTION
            final_sell = round(adjusted_sell * (1 - MARKDOWN_SELL), 4)

            # Курс от Google: AED → фиат
            _, _, google_raw = await fetch_rate("AED", fiat)
            if google_raw and google_raw != "N/A":
                google_raw = float(google_raw)
                google_up = round(google_raw * (1 + GOOGLE_MARKUP), 2)
                google_down = round(google_raw * (1 - GOOGLE_MARKUP), 4)
                google_block = (
                    f"\n📌 Курс от Google:\n"
                    f"Покупка AED за {fiat}: = {google_raw} +3% = {google_up}\n"
                    f"Покупка {fiat} за AED: = {google_raw} -3% = {google_down}"
                )
            else:
                google_block = "\n📌 Курс от Google: недоступен"

            results.append(
                f"<b>💱 Обмен {fiat} ↔ AED ({source})</b>\n"
                f"🔸 Покупка AED за {fiat} = {round(raw_buy, 4)} +3.5% = {final_buy}\n"
                f"🔸 Покупка {fiat} за AED = {round(raw_sell, 4)} -3.5% = {final_sell}"
                f"{google_block}\n"
            )
        except Exception as e:
            results.append(f"❌ Ошибка расчёта для {fiat}: {e}")

    return "\n".join(results)
