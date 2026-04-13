import math
import requests
import csv
import json
from bs4 import BeautifulSoup

# 1. 실시간 데이터(환율/유가) 가져오기
def get_live_data():
    headers = {"User-Agent": "Mozilla/5.0"}
    rate, fuel_raw = 1480.0, 250.0 # 기본값
    try:
        # 환율 가져오기
        r = requests.get("https://finance.naver.com/marketindex/")
        rate = float(BeautifulSoup(r.text, "html.parser").select_one(".value").text.replace(",", ""))
        # 항공유가 가져오기
        r2 = requests.get("https://www.investing.com/commodities/jet-fuel", headers=headers)
        fuel_raw = float(BeautifulSoup(r2.text, "html.parser").select_one('[data-test="instrument-price-last"]').text.replace(",", ""))
    except Exception as e:
        print(f"데이터 수집 중 오류 발생: {e}")
    
    # 갤런당 가격을 kg당 원화 가격으로 변환
    fuel_price_kg = ((fuel_raw / 100) / 3.06) * rate
    return rate, fuel_price_kg

# 2. 거리 계산 함수 (Haversine 공식)
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi, dlambda = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# --- 메인 실행 로직 ---
ex_rate, fuel_p = get_live_data()
csv_path = '/Users/yoonseokjoon/locations.csv'

# 공항 데이터 로드
try:
    with open(csv_path, mode='r', encoding='utf-8') as f:
        airport_list = list(csv.DictReader(f))
except FileNotFoundError:
    print(f"❌ 파일을 찾을 수 없습니다: {csv_path}")
    airport_list = []

def find_airport(code):
    for row in airport_list:
        if row.get('iata_code') == code:
            return row
    return None

# 🔥 [노선 설정]
departure_code = "FUK" # 후쿠오카
arrival_code = "NRT"   # 나리타(도쿄)

dep = find_airport(departure_code)
arr = find_airport(arrival_code)

if dep and arr:
    dist = haversine(float(dep['latitude_deg']), float(dep['longitude_deg']),
                     float(arr['latitude_deg']), float(arr['longitude_deg']))
    
    # [계산 로직]
    # 1. 유류비 (B737 기준 1인분 분담)
    cost = (dist / 750 * 2500 * fuel_p) / 189
    
    # 2. 비행 시간 (시속 800km 기준)
    hours = int(dist // 800)
    minutes = int((dist % 800) / 800 * 60)
    travel_time = f"{hours}시간 {minutes}분" if hours > 0 else f"{minutes}분"
    
    # 3. 탄소 배출량 (1km당 115g 기준)
    carbon_kg = round((dist * 115) / 1000, 1)
    
    # 📦 웹용 데이터 묶음 만들기
    card_data = {
        "status": "success",
        "departure": {"code": departure_code, "name": dep['name'], "city": dep.get('municipality', 'Unknown')},
        "arrival": {"code": arrival_code, "name": arr['name'], "city": arr.get('municipality', 'Unknown')},
        "distance_km": round(dist, 2),
        "fuel_cost_krw": int(cost),
        "estimated_time": travel_time,
        "carbon_kg": carbon_kg,
        "live_data": {
            "exchange_rate": ex_rate,
            "fuel_price_kg": round(fuel_p, 2)
        }
    }
    
    # ✅ result.json 파일로 저장 (경로 단순화)
    with open('result.json', 'w', encoding='utf-8') as jf:
        json.dump(card_data, jf, ensure_ascii=False, indent=4)
        
    print("---------------------------------------")
    print(f"🎉 {departure_code} -> {arrival_code} 계산 성공!")
    print("🎉 데이터가 result.json에 저장되었습니다.")
    print("---------------------------------------")
else:
    print("❌ 공항 코드를 확인해주세요.")
    