import os
import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

API_KEY = os.environ.get("FMP_API_KEY", "").strip()

CANDIDATES = [
    "BTCUSD", "ETHUSD", "USDTUSD", "BNBUSD", "SOLUSD", "XRPUSD",
    "USDCUSD", "ADAUSD", "DOGEUSD", "TRXUSD", "AVAXUSD", "SHIBUSD",
    "DOTUSD", "LINKUSD", "BCHUSD", "LTCUSD", "MATICUSD", "UNIUSD",
    "ATOMUSD", "XLMUSD", "ETCUSD", "FILUSD", "APTUSD", "ARBUSD",
    "OPUSD", "NEARUSD", "VETUSD", "ICPUSD", "AAVEUSD", "ALGOUSD",
    "XMRUSD", "HBARUSD", "GRTUSD", "SANDUSD", "MANAUSD", "AXSUSD",
    "EOSUSD", "FTMUSD", "THETAUSD", "FLOWUSD",
]

CATEGORY_MAP = {
    "BTCUSD": "메이저", "ETHUSD": "메이저",
    "USDTUSD": "스테이블", "USDCUSD": "스테이블",
    "BNBUSD": "거래소", "SOLUSD": "레이어1", "XRPUSD": "결제",
    "ADAUSD": "레이어1", "DOGEUSD": "밈", "SHIBUSD": "밈",
    "TRXUSD": "레이어1", "AVAXUSD": "레이어1", "DOTUSD": "레이어1",
    "LINKUSD": "오라클", "BCHUSD": "결제", "LTCUSD": "결제",
    "MATICUSD": "레이어2", "ARBUSD": "레이어2", "OPUSD": "레이어2",
    "UNIUSD": "디파이", "AAVEUSD": "디파이", "GRTUSD": "디파이",
    "ATOMUSD": "레이어1", "XLMUSD": "결제", "ETCUSD": "레이어1",
    "FILUSD": "스토리지", "APTUSD": "레이어1", "NEARUSD": "레이어1",
    "VETUSD": "레이어1", "ICPUSD": "레이어1", "ALGOUSD": "레이어1",
    "XMRUSD": "프라이버시", "HBARUSD": "레이어1",
    "SANDUSD": "메타버스", "MANAUSD": "메타버스", "AXSUSD": "게임",
    "EOSUSD": "레이어1", "FTMUSD": "레이어1", "THETAUSD": "미디어",
    "FLOWUSD": "레이어1",
}

NAME_MAP = {
    "BTCUSD": "비트코인", "ETHUSD": "이더리움", "USDTUSD": "테더",
    "BNBUSD": "BNB", "SOLUSD": "솔라나", "XRPUSD": "리플",
    "USDCUSD": "USD코인", "ADAUSD": "카르다노", "DOGEUSD": "도지코인",
    "TRXUSD": "트론", "AVAXUSD": "아발란체", "SHIBUSD": "시바이누",
    "DOTUSD": "폴카닷", "LINKUSD": "체인링크", "BCHUSD": "비트코인캐시",
    "LTCUSD": "라이트코인", "MATICUSD": "폴리곤", "UNIUSD": "유니스왑",
    "ATOMUSD": "코스모스", "XLMUSD": "스텔라루멘", "ETCUSD": "이더리움클래식",
    "FILUSD": "파일코인", "APTUSD": "앱토스", "ARBUSD": "아비트럼",
    "OPUSD": "옵티미즘", "NEARUSD": "니어프로토콜", "VETUSD": "비체인",
    "ICPUSD": "인터넷컴퓨터", "AAVEUSD": "에이브", "ALGOUSD": "알고랜드",
    "XMRUSD": "모네로", "HBARUSD": "헤데라", "GRTUSD": "더그래프",
    "SANDUSD": "샌드박스", "MANAUSD": "디센트럴랜드", "AXSUSD": "엑시인피니티",
    "EOSUSD": "이오스", "FTMUSD": "팬텀", "THETAUSD": "쎄타", "FLOWUSD": "플로우",
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

    display_price = round(price, 2) if price >= 1 else round(price, 6)

    return {
        "symbol": symbol.replace("USD", ""),
        "name": NAME_MAP.get(symbol, q.get("name", symbol)),
        "sector": CATEGORY_MAP.get(symbol, "기타"),
        "price": display_price,
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

    with open("crypto-data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(rows)} cryptos. Skipped {len(skipped)}: {skipped}")


if __name__ == "__main__":
    main()
