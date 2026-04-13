from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import math, requests, re

app = Flask(__name__)
CORS(app)

# [데이터] 한국어 명칭이 추가된 100개 공항 DB (이름, 위도, 경도)
AIRPORTS_DB = {
    "ICN": {"name": "인천/서울", "lat": 37.469, "lon": 126.451},
    "JFK": {"name": "뉴욕 JFK", "lat": 40.641, "lon": -73.778},
    "LHR": {"name": "런던 히드로", "lat": 51.470, "lon": -0.454},
    "NRT": {"name": "도쿄 나리타", "lat": 35.772, "lon": 140.385},
    "HND": {"name": "도쿄 하네다", "lat": 35.549, "lon": 139.779},
    "LAX": {"name": "로스앤젤레스", "lat": 33.941, "lon": -118.408},
    "CDG": {"name": "파리 샤를드골", "lat": 49.009, "lon": 2.547},
    "SIN": {"name": "싱가포르 창이", "lat": 1.364, "lon": 103.991},
    "DXB": {"name": "두바이", "lat": 25.253, "lon": 55.365},
    "HKG": {"name": "홍콩", "lat": 22.308, "lon": 113.914},
    "SFO": {"name": "샌프란시스코", "lat": 37.619, "lon": -122.375},
    "SYD": {"name": "시드니", "lat": 33.939, "lon": 151.175},
    "FRA": {"name": "프랑크푸르트", "lat": 50.037, "lon": 8.562},
    "AMS": {"name": "암스테르담", "lat": 52.310, "lon": 4.768},
    "BKK": {"name": "방콕 수완나품", "lat": 13.690, "lon": 100.750},
    "FCO": {"name": "로마 피우미치노", "lat": 41.800, "lon": 12.238},
    "CAN": {"name": "광저우", "lat": 23.392, "lon": 113.299},
    "IST": {"name": "이스탄불", "lat": 41.275, "lon": 28.741},
    "ORD": {"name": "시카고 오헤어", "lat": 41.974, "lon": -87.907},
    "DFW": {"name": "달라스", "lat": 32.899, "lon": -97.040},
    "PVG": {"name": "상하이 푸동", "lat": 31.144, "lon": 121.808},
    "PEK": {"name": "베이징 서도", "lat": 40.079, "lon": 116.590},
    "KIX": {"name": "오사카 간사이", "lat": 34.434, "lon": 135.244},
    "BNE": {"name": "브리즈번", "lat": 27.384, "lon": 153.117},
    "MEL": {"name": "멜버른", "lat": 37.673, "lon": 144.843},
    "AKL": {"name": "오클랜드", "lat": 37.008, "lon": 174.792},
    "YYZ": {"name": "토론토", "lat": 43.677, "lon": -79.630},
    "YVR": {"name": "밴쿠버", "lat": 49.196, "lon": -123.181},
    "MEX": {"name": "멕시코시티", "lat": 19.436, "lon": -99.072},
    "GRU": {"name": "상파울루", "lat": -23.435, "lon": -46.473},
    "EZE": {"name": "부에노스아이레스", "lat": -34.822, "lon": -58.535},
    "MAD": {"name": "마드리드", "lat": 40.494, "lon": -3.567},
    "BCN": {"name": "바르셀로나", "lat": 41.297, "lon": 2.078},
    "ZRH": {"name": "취리히", "lat": 47.458, "lon": 8.548},
    "MUC": {"name": "뮌헨", "lat": 48.353, "lon": 11.775},
    "VIE": {"name": "비엔나", "lat": 48.110, "lon": 16.569},
    "CPH": {"name": "코펜하겐", "lat": 55.618, "lon": 12.650},
    "ARN": {"name": "스톡홀름", "lat": 59.651, "lon": 17.918},
    "HEL": {"name": "헬싱키", "lat": 60.317, "lon": 24.963},
    "OSL": {"name": "오슬로", "lat": 60.197, "lon": 11.100},
    "DUB": {"name": "더블린", "lat": 53.421, "lon": -6.270},
    "LIS": {"name": "리스본", "lat": 38.774, "lon": -9.134},
    "ATH": {"name": "아테네", "lat": 37.936, "lon": 23.944},
    "WAW": {"name": "바르샤바", "lat": 52.165, "lon": 20.967},
    "PRG": {"name": "프라하", "lat": 50.101, "lon": 14.263},
    "BRU": {"name": "브뤼셀", "lat": 50.901, "lon": 4.484},
    "DEL": {"name": "델리", "lat": 28.566, "lon": 77.103},
    "BOM": {"name": "뭄바이", "lat": 19.089, "lon": 72.868},
    "BJS": {"name": "베이징", "lat": 39.904, "lon": 116.407},
    "SHA": {"name": "상하이 홍차오", "lat": 31.230, "lon": 121.473},
    "SZX": {"name": "심천", "lat": 22.639, "lon": 113.811},
    "KUL": {"name": "쿠알라룸푸르", "lat": 2.745, "lon": 101.709},
    "MNL": {"name": "마닐라", "lat": 14.508, "lon": 121.019},
    "CGK": {"name": "자카르타", "lat": -6.125, "lon": 106.655},
    "SGN": {"name": "호치민", "lat": 10.818, "lon": 106.663},
    "HAN": {"name": "하노이", "lat": 21.221, "lon": 105.807},
    "TPE": {"name": "타이베이 타오위안", "lat": 25.079, "lon": 121.234},
    "GMP": {"name": "김포/서울", "lat": 37.558, "lon": 126.790},
    "PUS": {"name": "김해/부산", "lat": 35.179, "lon": 128.938},
    "CJU": {"name": "제주", "lat": 33.511, "lon": 126.493},
    "CTS": {"name": "삿포로 신치토세", "lat": 42.775, "lon": 141.692},
    "FUK": {"name": "후쿠오카", "lat": 33.585, "lon": 130.450},
    "OKA": {"name": "오키나와 나하", "lat": 26.206, "lon": 127.646},
    "SEA": {"name": "시애틀", "lat": 47.448, "lon": -122.309},
    "SJC": {"name": "산호세", "lat": 37.363, "lon": -121.928},
    "SAN": {"name": "샌디에이고", "lat": 32.733, "lon": -117.189},
    "PHX": {"name": "피닉스", "lat": 33.434, "lon": -112.008},
    "DEN": {"name": "덴버", "lat": 39.856, "lon": -104.673},
    "IAH": {"name": "휴스턴", "lat": 29.980, "lon": -95.339},
    "ATL": {"name": "애틀랜타", "lat": 33.640, "lon": -84.427},
    "MIA": {"name": "마이애미", "lat": 25.795, "lon": -80.287},
    "MCO": {"name": "올랜도", "lat": 28.428, "lon": -81.308},
    "IAD": {"name": "워싱턴 덜레스", "lat": 38.953, "lon": -77.456},
    "BOS": {"name": "보스턴", "lat": 42.364, "lon": -71.005},
    "PHL": {"name": "필라델피아", "lat": 39.872, "lon": -75.241},
    "CLT": {"name": "샬럿", "lat": 35.214, "lon": -80.943},
    "MSP": {"name": "미니애폴리스", "lat": 44.884, "lon": -93.222},
    "DTW": {"name": "디트로이트", "lat": 42.212, "lon": -83.353},
    "SLC": {"name": "솔트레이크시티", "lat": 40.789, "lon": -111.979},
    "LAS": {"name": "라스베가스", "lat": 36.084, "lon": -115.153},
    "PDX": {"name": "포틀랜드", "lat": 45.589, "lon": -122.597},
    "AUH": {"name": "아부다비", "lat": 24.433, "lon": 54.651},
    "DOH": {"name": "도하", "lat": 25.273, "lon": 51.608},
    "RUH": {"name": "리야드", "lat": 24.957, "lon": 46.698},
    "JED": {"name": "제다", "lat": 21.679, "lon": 39.156},
    "MCT": {"name": "무스카트", "lat": 23.593, "lon": 58.284},
    "KWI": {"name": "쿠웨이트", "lat": 29.226, "lon": 47.969},
    "CAI": {"name": "카이로", "lat": 30.121, "lon": 31.405},
    "JNB": {"name": "요하네스버그", "lat": -26.139, "lon": 28.246},
    "CPT": {"name": "케이프타운", "lat": -33.971, "lon": 18.602},
    "NBO": {"name": "나이로비", "lat": -1.319, "lon": 36.927},
    "ADD": {"name": "아디스아바바", "lat": 8.977, "lon": 38.799},
    "CMN": {"name": "카사블랑카", "lat": 33.367, "lon": -7.589},
    "PER": {"name": "퍼스", "lat": -31.940, "lon": 115.967},
    "CHC": {"name": "크라이스트처치", "lat": -43.489, "lon": 172.532},
    "CEB": {"name": "세부", "lat": 10.307, "lon": 123.979},
    "BKI": {"name": "코타키나발루", "lat": 5.937, "lon": 116.051},
    "DPS": {"name": "발리", "lat": -8.748, "lon": 115.167}
}

@app.route('/')
def home():
    # 리스트 생성 (한국어 우선: "한국어명 (IATA)")
    air_list = sorted([f"{v['name']} ({k})" for k, v in AIRPORTS_DB.items()])
    
    try:
        rate = requests.get('https://open.er-api.com/v6/latest/USD', timeout=2).json()['rates']['KRW']
    except:
        rate = 1450.0 # 환율 서버 에러 시 기본값
    
    return render_template('index.html', airports=air_list, rate=rate)

@app.route('/calculate')
def calculate():
    dep_raw = request.args.get('dep', '').strip()
    arr_raw = request.args.get('arr', '').strip()

    # 정규식으로 괄호 안의 IATA 코드 추출 (한국어/영어 모두 대응)
    def extract_code(text):
        match = re.search(r'\(([A-Z]{3})\)', text.upper())
        return match.group(1) if match else None

    d_code = extract_code(dep_raw)
    a_code = extract_code(arr_raw)

    if not d_code or d_code not in AIRPORTS_DB:
        return jsonify({"status": "error", "message": "출발 공항을 리스트에서 정확히 선택해주세요!"})
    if not a_code or a_code not in AIRPORTS_DB:
        return jsonify({"status": "error", "message": "도착 공항을 리스트에서 정확히 선택해주세요!"})
    if d_code == a_code:
        return jsonify({"status": "error", "message": "출발지와 도착지가 같습니다!"})

    p1, p2 = AIRPORTS_DB[d_code], AIRPORTS_DB[a_code]
    
    # 하버사인 공식 (지구 곡률 반영 거리 계산)
    dist = 6371 * 2 * math.asin(math.sqrt(math.sin(math.radians(p2['lat']-p1['lat'])/2)**2 + 
           math.cos(math.radians(p1['lat']))*math.cos(math.radians(p2['lat']))*math.sin(math.radians(p2['lon']-p1['lon'])/2)**2))
    
    # 항공로 보정 계수 (8%)
    dist = dist * 1.08

    # 거리별 투입 기종 및 연비 설정
    if dist > 11000: air, seat, f = "Airbus A380-800", 407, 0.72
    elif dist > 8000: air, seat, f = "Boeing 787-9 Dreamliner", 269, 0.60
    elif dist > 4000: air, seat, f = "Airbus A330-300", 284, 0.65
    else: air, seat, f = "Airbus A321neo", 182, 0.52

    # 유류비 계산 (갤런당 $2.84 기준)
    cost_usd = (dist / 100) * f * 2.84
    
    try:
        r_val = requests.get('https://open.er-api.com/v6/latest/USD', timeout=2).json()['rates']['KRW']
    except:
        r_val = 1450.0

    return jsonify({
        "status": "success",
        "distance": f"{dist:,.0f} km",
        "airplane": f"{air} ({seat}석)",
        "total_cost_display": f"{(cost_usd * r_val * seat)/10000:,.0f}만원",
        "per_person_display": f"{(cost_usd * r_val)/10000:,.1f}만원",
        "coords": {"dep": [p1['lat'], p1['lon']], "arr": [p2['lat'], p2['lon']]}
    })

if __name__ == '__main__':
    # 기장님 맥북 환경에 맞춰 포트 5001로 설정 (에어플레이 간섭 방지)
    app.run(debug=True, port=5001)