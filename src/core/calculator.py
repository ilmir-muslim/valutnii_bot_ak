def calculate_aed_rate(buy_price: float, sell_price: float, markup: float = 0.035) -> dict | None:
    if not buy_price or not sell_price or sell_price == 0:
        return None

    raw = buy_price / sell_price
    final = round(raw * (1 + markup), 2)

    return {
        "buy_price": round(buy_price, 4),
        "sell_price": round(sell_price, 4),
        "raw_rate": round(raw, 4),
        "final_rate": final,
        "markup_percent": round(markup * 100, 2)
    }