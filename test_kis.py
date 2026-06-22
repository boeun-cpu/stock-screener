import os
import json
import urllib.request
import urllib.error

APP_KEY = os.environ.get("KIS_APP_KEY", "").strip()
APP_SECRET = os.environ.get("KIS_APP_SECRET", "").strip()

BASE = "https://openapi.koreainvestment.com:9443"


def get_token():
    url = f"{BASE}/oauth2/tokenP"
    body = json.dumps({
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("content-type", "application/json")
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("access_token")


def get_price(token, code):
    url = f"{BASE}/uapi/domestic-stock/v1/quotations/inquire-price?fid_cond_mrkt_div_code=J&fid_input_iscd={code}"
    req = urllib.request.Request(url, method="GET")
    req.add_header("content-type", "application/json")
    req.add_header("authorization", f"Bearer {token}")
    req.add_header("appkey", APP_KEY)
    req.add_header("appsecret", APP_SECRET)
    req.add_header("tr_id", "FHKST01010100")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    if not APP_KEY or not APP_SECRET:
        print("ERROR: KIS_APP_KEY 또는 KIS_APP_SECRET 가 설정되지 않았습니다")
        raise SystemExit(1)

    print("1) 토큰 발급 시도...")
    try:
        token = get_token()
    except urllib.error.HTTPError as e:
        print(f"토큰 발급 실패 (HTTP {e.code}): {e.read().decode('utf-8', 'ignore')}")
        raise SystemExit(1)
    if not token:
        print("토큰을 받지 못했습니다")
        raise SystemExit(1)
    print("   토큰 발급 성공!")

    print("2) 삼성전자(005930) 시세 조회 시도...")
    try:
        result = get_price(token, "005930")
    except urllib.error.HTTPError as e:
        print(f"시세 조회 실패 (HTTP {e.code}): {e.read().decode('utf-8', 'ignore')}")
        raise SystemExit(1)

    output = result.get("output", {})
    if not output:
        print("응답에 데이터가 없습니다. 전체 응답:")
        print(json.dumps(result, ensure_ascii=False, indent=2)[:1000])
        raise SystemExit(1)

    print("   시세 조회 성공! 주요 항목:")
    print(f"   현재가: {output.get('stck_prpr')}")
    print(f"   등락률: {output.get('prdy_ctrt')}%")
    print(f"   거래량: {output.get('acml_vol')}")
    print(f"   거래대금: {output.get('acml_tr_pbmn')}")
    print(f"   시가총액: {output.get('hts_avls')}")
    print(f"   52주최고: {output.get('w52_hgpr')}")
    print(f"   52주최저: {output.get('w52_lwpr')}")
    print()
    print("=== 사용 가능한 전체 항목 목록 ===")
    for k in sorted(output.keys()):
        print(f"   {k} = {output[k]}")


if __name__ == "__main__":
    main()
