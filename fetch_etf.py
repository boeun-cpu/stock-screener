import os
import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

API_KEY = os.environ.get("FMP_API_KEY", "").strip()

CANDIDATES = [
    "SPY", "VOO", "IVV", "QQQ", "DIA", "IWM", "VTI", "VEA",
    "VWO", "EFA", "EEM", "VUG", "VTV", "IWF", "IWD", "RSP",
    "SMH", "SOXX", "XLK", "VGT", "XLF", "KRE", "XLE", "XLV",
    "XLY", "XLP", "XLI", "XLU", "XLB", "XLC", "XLRE", "IBB",
    "XBI", "ITA", "JETS", "TAN", "ICLN", "ARKK", "ARKG", "HACK",
    "TQQQ", "SQQQ", "SOXL", "SOXS", "UPRO", "SPXU", "TNA", "TZA",
    "FAS", "FAZ", "TSLL", "NVDL", "GLD", "SLV", "IAU", "USO",
    "UNG", "DBC", "PDBC", "GDX", "GDXJ", "CORN", "WEAT", "URA",
    "LIT", "COPX", "TLT", "IEF", "SHY", "HYG", "LQD", "AGG",
    "BND", "TIP", "MUB", "SCHD", "VYM", "DVY", "VIG", "JEPI",
]

CATEGORY_MAP = {
    "SPY": "대표지수", "VOO": "대표지수", "IVV": "대표지수", "QQQ": "대표지수",
    "DIA": "대표지수", "IWM": "대표지수", "VTI": "대표지수", "RSP": "대표지수",
    "VEA": "해외주식", "VWO": "해외주식", "EFA": "해외주식", "EEM": "해외주식",
    "VUG": "스타일", "VTV": "스타일", "IWF": "스타일", "IWD": "스타일",
    "SMH": "반도체", "SOXX": "반도체",
    "XLK": "기술", "VGT": "기술", "XLC": "통신",
    "XLF": "금융", "KRE": "금융",
    "XLE": "에너지", "XLV": "헬스케어", "IBB": "헬스케어", "XBI": "헬스케어",
    "XLY": "소비재", "XLP": "소비재", "XLI": "산업재", "XLU": "유틸리티",
    "XLB": "소재", "XLRE": "리츠", "ITA": "산업재", "JETS": "항공",
    "TAN": "친환경", "ICLN": "친환경",
    "ARKK": "테마", "ARKG": "테마", "HACK": "테마",
    "TQQQ": "레버리지", "SQQQ": "인버스", "SOXL": "레버리지", "SOXS": "인버스",
    "UPRO": "레버리지", "SPXU": "인버스", "TNA": "레버리지", "TZA": "인버스",
    "FAS": "레버리지", "FAZ": "인버스", "TSLL": "레버리지", "NVDL": "레버리지",
    "GLD": "원자재", "SLV": "원자재", "IAU": "원자재", "USO": "원자재",
    "UNG": "원자재", "DBC": "원자재", "PDBC": "원자재", "GDX": "원자재",
    "GDXJ": "원자재", "CORN": "원자재", "WEAT": "원자재", "URA": "원자재",
    "LIT": "원자재", "COPX": "원자재",
    "TLT": "채권", "IEF": "채권", "SHY": "채권", "HYG": "채권",
    "LQD": "채권", "AGG": "채권", "BND": "채권", "TIP": "채권",
    "MUB": "채권",
    "SCHD": "배당", "VYM": "배당", "DVY": "배당", "VIG": "배당", "JEPI": "배당",
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
        "sector": CATEGORY_MAP.get(symbol, "기타"),
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

    with open("etf-data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(rows)} ETFs. Skipped {len(skipped)}: {skipped}")


if __name__ == "__main__":
    main()
