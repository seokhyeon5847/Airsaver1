import time
import requests
import pandas as pd
import os
import math
import sqlite3
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, jsonify, redirect
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# [설정] 2026년 4월 고유가/고환율 실시간 반영 (기장님 피드백 반영)
API_KEY = "bada62991cd7670a6866ed59"
exchange_cache = {"rate": 1472.0, "last_updated": 0} 
fuel_cache = {"price": 3.15, "last_updated": 0}    

# [DB] 노선 분석 데이터 관리
def init_db():
    try:
        conn = sqlite3.connect('analytics.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS routes 
                     (route_id TEXT PRIMARY KEY, count INTEGER, max_bagaji REAL)''')
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"⚠️ DB 초기화 실패: {e}")

init_db()

# [디테일] 전 세계 주요 공항 한글 매핑 (누락 없이 유지)
KOREAN_NAMES = {
    "ICN": "인천", "GMP": "김포", "PUS": "부산 김해", "CJU": "제주", "UBN": "울란바토르",
    "JFK": "뉴욕 JFK", "LHR": "런던 히드로", "NRT": "도쿄 나리타", "HND": "도쿄 하네다",
    "LAX": "로스앤젤레스", "CDG": "파리 샤를드골", "SIN": "싱가포르 창이", "DXB": "두바이",
    "HKG": "홍콩", "SFO": "샌프란시스코", "SYD": "시드니", "FRA": "프랑크푸르트",
    "AMS": "암스테르담", "BKK": "방콕 수완나폼", "FCO": "로마 피우미치노", "CAN": "광저우",
    "IST": "이스탄불", "ORD": "시카고 오헤어", "DFW": "달라스", "PVG": "상하이 푸동",
    "PEK": "베이징 서도", "KIX": "오사카 간사이", "BNE": "브리즈번", "MEL": "멜버른",
    "AKL": "오클랜드", "YYZ": "토론토", "YVR": "밴쿠버", "MEX": "멕시코시티",
    "GRU": "상파울루", "EZE": "부에노스아이레스", "MAD": "마드리드", "BCN": "바르셀로나",
    "ZRH": "취리히", "MUC": "뮌헨", "VIE": "비엔나", "CPH": "코펜하겐", "ARN": "스톡홀름",
    "HEL": "헬싱키", "OSL": "오슬로", "DUB": "더블린", "LIS": "리스본", "ATH": "아테네",
    "WAW": "바르샤바", "PRG": "프라하", "BRU": "브뤼셀", "DEL": "델리", "BOM": "뭄바이",
    "SHA": "상하이 홍차오", "SZX": "심천", "KUL": "쿠알라룸푸르", "MNL": "마닐라",
    "CGK": "자카르타", "SGN": "호치민", "HAN": "하노이", "TPE": "타이페이 타오위안",
    "CTS": "삿포로 치토세", "FUK": "후쿠오카", "OKA": "오키나와", "SEA": "시애틀",
    "GUM": "괌", "SPN": "사이판", "HNL": "호놀룰루 하와이", "CEB": "세부", "DAD": "다낭"
}

def get_live_fuel_price():
    now = time.time()
    if now - fuel_cache["last_updated"] < 3600:
        return fuel_cache["price"]
    try:
        url = "https://www.indexmundi.com/commodities/?commodity=jet-fuel"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        price_val = soup.find("td", {"style": "font-weight:bold; font-size: 1.2em; text-align:right"}).text
        fuel_cache["price"] = float(price_val.replace("$", "").strip())
        fuel_cache["last_updated"] = now
    except: pass
    return fuel_cache["price"]

def load_airports():
    try:
        base_path = os.path.dirname(__file__)
        csv_path = os.path.join(base_path, 'locations.csv')
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            return df.drop_duplicates(subset=['iata']).set_index('iata').to_dict('index')
        return {}
    except: return {}

AIRPORTS_DB = load_airports()

def get_rate():
    now = time.time()
    if now - exchange_cache["last_updated"] < 3600:
        return exchange_cache["rate"]
    try:
        url = f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/USD"
        res = requests.get(url, timeout=5).json()
        if res.get("result") == "success":
            exchange_cache["rate"] = res["conversion_rates"]["KRW"]
            exchange_cache["last_updated"] = now
    except: pass
    return exchange_cache["rate"]

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    dlat, dlon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    return 2 * R * math.asin(math.sqrt(a))

@app.route('/')
def index():
    display_list = [f"{code} - {info['name']} ({KOREAN_NAMES.get(code, '')})" if KOREAN_NAMES.get(code) else f"{code} - {info['name']}" for code, info in AIRPORTS_DB.items()]
    hot_routes = []
    try:
        conn = sqlite3.connect('analytics.db')
        c = conn.cursor()
        c.execute("SELECT route_id FROM routes ORDER BY count DESC LIMIT 5")
        hot_routes = [row[0] for row in c.fetchall()]
        conn.close()
    except: pass
    
    return render_template('index.html', rate=get_rate(), airports=display_list, fuel_price=get_live_fuel_price(), hot_routes=hot_routes, seo_title=None, pre_dep=None, pre_arr=None)

@app.route('/route/<dep_arr>')
def route_seo(dep_arr):
    try:
        dep_code, arr_code = dep_arr.split('-')
        dep_code, arr_code = dep_code.upper(), arr_code.upper()
        dep, arr = AIRPORTS_DB.get(dep_code), AIRPORTS_DB.get(arr_code)
        if not dep or not arr: return redirect('/')

        dep_k, arr_k = KOREAN_NAMES.get(dep_code, dep_code), KOREAN_NAMES.get(arr_code, arr_code)
        page_title = f"{dep_k} to {arr_k} 유류할증료 원가 계산 및 바가지 지수 검증"
        display_list = [f"{code} - {info['name']} ({KOREAN_NAMES.get(code, '')})" if KOREAN_NAMES.get(code) else f"{code} - {info['name']}" for code, info in AIRPORTS_DB.items()]
        
        return render_template('index.html', rate=get_rate(), airports=display_list, fuel_price=get_live_fuel_price(), hot_routes=[], seo_title=page_title, pre_dep=f"{dep_code} - {dep['name']}", pre_arr=f"{arr_code} - {arr['name']}")
    except: return redirect('/')

@app.route('/calculate')
def calculate():
    dep_raw, arr_raw = request.args.get('dep', '').upper(), request.args.get('arr', '').upper()
    dep_code, arr_code = dep_raw.split(' - ')[0].strip(), arr_raw.split(' - ')[0].strip()
    dep, arr = AIRPORTS_DB.get(dep_code), AIRPORTS_DB.get(arr_code)
    if not dep or not arr: return jsonify({"error": "공항 코드를 확인하세요."}), 400

    dist = calculate_distance(dep['lat'], dep['lon'], arr['lat'], arr['lon']) * 1.03
    load_factor = 0.82 

    # [디테일] 비행시간 계산 (순항 850km/h + 이착륙 30분)
    flight_hours_raw = (dist / 850) + 0.5
    f_hours, f_minutes = int(flight_hours_raw), int((flight_hours_raw - int(flight_hours_raw)) * 60)
    flight_time_str = f"약 {f_hours}시간 {f_minutes}분"

    if dist < 3000: plane, eff = "A321neo / B737-8", 2.0
    elif dist < 7500: plane, eff = "B787-9 Dreamliner", 2.2
    else: plane, eff = "A350-900 / B747-8i", 2.4

    fuel_p, rate = get_live_fuel_price(), get_rate()
    cost_krw = ((dist / 100) * eff / load_factor) * 0.264172 * fuel_p * rate

    # 2026 현행화 할증료 대조군
    actual_fee = 42000 if dist < 1000 else 98000 if dist < 3000 else 195000 if dist < 7500 else 338000
    bagaji_index = (actual_fee / cost_krw) * 100

    try:
        route_id = f"{dep_code}→{arr_code}"
        conn = sqlite3.connect('analytics.db'); c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO routes (route_id, count, max_bagaji) VALUES (?, COALESCE((SELECT count FROM routes WHERE route_id=?), 0) + 1, ?)", (route_id, route_id, bagaji_index))
        conn.commit(); conn.close()
    except: pass

    return jsonify({
        "distance": f"{dist:,.0f} km",
        "flight_time": flight_time_str,
        "airplane": plane,
        "fuel_cost_krw": f"₩{cost_krw:,.0f}",
        "exchange_rate": f"{int(rate):,}",
        "fuel_price": f"${fuel_p:,.2f}",
        "bagaji_index": f"{bagaji_index:,.0f}%",
        "coords": {"dep": [dep['lat'], dep['lon']], "arr": [arr['lat'], arr['lon']]}
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
