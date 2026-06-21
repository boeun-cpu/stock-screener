import os
import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

API_KEY = os.environ.get("FMP_API_KEY", "").strip()

CANDIDATES = [
    "AAPL", "MSFT", "AMZN", "GOOGL", "GOOG", "META", "NVDA", "TSLA",
    "AVGO", "AMD", "INTC", "QCOM", "MU", "TXN", "AMAT", "ADBE",
    "CRM", "ORCL", "CSCO", "IBM", "NFLX", "PYPL", "JPM", "BAC",
    "WFC", "GS", "MS", "C", "V", "MA", "AXP", "WMT",
    "COST", "HD", "MCD", "NKE", "SBUX", "KO", "PEP", "PG",
    "JNJ", "PFE", "MRK", "ABBV", "UNH", "CVS", "XOM", "CVX",
    "BA", "CAT", "GE", "DIS", "VZ", "T", "CMCSA", "F",
    "GM", "UBER", "ABNB", "PLTR", "SHOP", "SQ", "COIN", "SOFI",
]

SECTOR_MAP = {
    "AAPL": "빅테크·플랫폼", "MSFT": "빅테크·플랫폼", "AMZN": "빅테크·플랫폼",
    "GOOGL": "빅테크·플랫폼", "GOOG": "빅테크·플랫폼", "META": "빅테크·플랫폼",
    "NVDA": "반도체·AI", "AVGO": "반도체·AI", "AMD": "반도체·AI",
    "INTC": "반도체·AI", "QCOM": "반도체·AI", "MU": "반도체·AI",
    "TXN": "반도체·AI", "AMAT": "반도체·AI",
    "TSLA": "전기차·모빌리티", "F": "전기차·모빌리티", "GM": "전기차·모빌리티",
    "UBER": "전기차·모빌리티",
    "ADBE": "소프트웨어", "CRM": "소프트웨어", "ORCL": "소프트웨어",
    "CSCO": "소프트웨어", "IBM": "소프트웨어", "NFLX": "소프트웨어",
    "PLTR": "소프트웨어", "SHOP": "소프트웨어",
    "JPM": "금융", "BAC": "금융", "WFC": "금융", "GS": "금융",
    "MS": "금융", "C": "금융", "V": "금융", "MA": "금융",
    "AXP": "금융", "PYPL": "금융", "SQ": "금융", "COIN": "금융", "SOFI": "금융",
    "WMT": "소비재", "COST": "소비재", "HD": "소비재", "MCD": "소비재",
    "NKE": "소비재", "SBUX": "소비재", "KO": "소비재", "PEP": "소비재",
    "PG": "소비재", "DIS": "소비재", "ABNB": "소비재",
    "JNJ": "헬스케어", "PFE": "헬스케어", "MRK": "헬스케어",
    "ABBV": "헬스케어", "UNH": "헬스케어", "CVS": "헬스케어",
    "XOM": "에너지", "CVX": "에너지",
    "BA": "산업재", "CAT": "산업재", "GE": "산업재",
    "VZ": "통신", "T": "통신", "CMCSA": "통신",
}


def fetch_quote(symbol):
    url = f"https://financialmodelingprep.com/stable/quote?symbol={symbol}&apikey={API_KEY}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
        data = json.loads(raw)
        if isinstance(data, list) and len(data) > 0 and "price" in data[0]:
            return data[0]
        return None
    except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        return None


def build_row(q):
    symbol = q.get("symbol")
    price = q.get("price")
    volume = q.get("volume")
    year_high = q.get("yearHigh")
    year_low = q.get("yearLow")
    market_cap = q.get("marketCap")
    change_pct = q.get("changePercentage")

    if price is None or volume is None:
        return None

    turnover = price * volume

    pos52 = None
    if year_high is not None and year_low is not None and year_high > year_low:
        pos52 = round((price - year_low) / (year_high - year_low) * 100)
        pos52 = max(0, min(100, pos52))

    from_high = None
    if year_high is not None and year_high > 0:
        from_high = round((price - year_high) / year_high * 100, 1)

    near_high = pos52 is not None and pos52 >= 95

    return {
        "symbol": symbol,
        "name": q.get("name", symbol),
        "sector": SECTOR_MAP.get(symbol, "기타"),
        "price": round(price, 2),
        "change": round(change_pct, 2) if change_pct is not None else 0,
        "volume": volume,
        "turnover": round(turnover),
        "marketCap": round(market_cap / 1_000_000) if market_cap else 0,
        "yearHigh": year_high,
        "yearLow": year_low,
        "pos52": pos52 if pos52 is not None else 0,
        "fromHigh": from_high if from_high is not None else 0,
        "nearHigh": near_high,
    }


def main():
    if not API_KEY:
        print("ERROR: FMP_API_KEY not set")
        raise SystemExit(1)

    rows = []
    skipped = []
    for symbol in CANDIDATES:
        q = fetch_quote(symbol)
        if q is None:
            skipped.append(symbol)
            continue
        row = build_row(q)
        if row is None:
            skipped.append(symbol)
            continue
        rows.append(row)
        time.sleep(0.3)

    rows.sort(key=lambda r: r["turnover"], reverse=True)

    output = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "count": len(rows),
        "stocks": rows,
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(rows)} stocks. Skipped {len(skipped)}: {skipped}")


if __name__ == "__main__":
    main()
