import streamlit as st
import yfinance as yf
import pandas as pd
import json
import os
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import time
import altair as alt

# --- 1. 網頁基礎設定 ---
st.set_page_config(page_title="ETF 投資戰情室", layout="wide")

# 自定義 CSS
st.markdown("""
    <style>
    [data-testid="stMetricDelta"] svg { fill: red; }
    .stMetric { background-color: #f8f9fa; padding: 10px; border-radius: 10px; }
    
    .news-box { background-color: #f0f7ff; border-left: 6px solid #4a90e2; padding: 20px; border-radius: 8px; margin-bottom: 25px; box-shadow: 1px 1px 4px rgba(0,0,0,0.05); }
    .news-title { font-size: 20px; font-weight: bold; color: #1e3c72; margin-bottom: 15px; display: flex; align-items: center; }
    .news-item { font-size: 16px; color: #333; margin-bottom: 12px; line-height: 1.5; font-weight: 500;}
    .news-item a { text-decoration: none; color: #1e3c72; transition: color 0.2s;}
    .news-item a:hover { text-decoration: underline; color: #d32f2f; }

    .ex-div-box { background-color: #ffeaea; border: 2px solid #e06666; border-radius: 10px; padding: 25px 15px; text-align: center; margin-bottom: 15px; height: 100%; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);}
    .ex-div-title { color: #cc0000; font-weight: bold; font-size: 16px; margin-bottom: 10px; }
    .ex-div-text { color: #783f04; font-size: 14px; font-weight: bold; }
    
    .pay-div-box { background-color: #fff2cc; border: 2px solid #f6b26b; border-radius: 10px; padding: 15px; text-align: center; margin-bottom: 15px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);}
    .pay-div-title { color: #b45f06; font-weight: bold; font-size: 16px; margin-bottom: 8px; }
    .pay-div-text { color: #783f04; font-size: 14px; font-weight: bold; }

    /* 三拼損益與領息橫列大看板樣式 */
    .triple-box { background-color: #ffffff; border-radius: 16px; border: 1px solid #e0e0e0; padding: 30px; display: flex; align-items: center; margin-bottom: 25px; box-shadow: 2px 2px 10px rgba(0,0,0,0.04); }
    .triple-col { flex: 1; text-align: left; padding: 0 15px; }
    .triple-divider { width: 1px; background-color: #e0e0e0; height: 100px; margin: 0 15px; }
    .triple-title { font-size: 18px; color: #757575; font-weight: bold; margin-bottom: 12px; }
    .triple-val-r { font-size: 48px; font-weight: 900; color: #b71c1c; font-family: Arial, sans-serif; line-height: 1.1; }
    .triple-val-g { font-size: 48px; font-weight: 900; color: #2e7d32; font-family: Arial, sans-serif; line-height: 1.1; }
    .triple-val-gold { font-size: 48px; font-weight: 900; color: #f39c12; font-family: Arial, sans-serif; line-height: 1.1; }
    .triple-pct-r { font-size: 20px; font-weight: bold; color: #b71c1c; margin-top: 10px; }
    .triple-pct-g { font-size: 20px; font-weight: bold; color: #2e7d32; margin-top: 10px; }
    .triple-sub-gold { font-size: 15px; font-weight: bold; color: #7f8c8d; margin-top: 10px; }

    .alert-high { background-color: #ffebee; border: 2px solid #ef5350; border-left: 8px solid #d32f2f; padding: 15px; border-radius: 8px; margin-bottom: 15px; color: #b71c1c; font-size: 16px; font-weight: bold; animation: pulse-red 2s infinite;}
    .alert-low { background-color: #e8f5e9; border: 2px solid #66bb6a; border-left: 8px solid #388e3c; padding: 15px; border-radius: 8px; margin-bottom: 15px; color: #1b5e20; font-size: 16px; font-weight: bold; animation: pulse-green 2s infinite;}

    @keyframes pulse-red { 0% { box-shadow: 0 0 0 0 rgba(239, 83, 80, 0.7); } 70% { box-shadow: 0 0 0 15px rgba(239, 83, 80, 0); } 100% { box-shadow: 0 0 0 0 rgba(239, 83, 80, 0); } }
    @keyframes pulse-green { 0% { box-shadow: 0 0 0 0 rgba(102, 187, 106, 0.7); } 70% { box-shadow: 0 0 0 15px rgba(102, 187, 106, 0); } 100% { box-shadow: 0 0 0 0 rgba(102, 187, 106, 0); } }

    .month-card { background-color: #e9ecef; padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 10px; border: 1px solid #ced4da; }
    .month-title { font-size: 20px; font-weight: bold; color: #495057; }
    .month-amount { font-size: 28px; font-weight: bold; color: #d9534f; margin: 10px 0; }
    .month-sources { font-size: 14px; color: #6c757d; }
    
    div.stButton > button { font-weight: bold; border-radius: 8px; }
    .secret-box { padding: 25px; border: 2px dashed #dc3545; border-radius: 12px; background-color: #fffafb; }
    .net-worth-box { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; margin-top: 15px; }

    /* 即將掛牌 ETF 樣式 */
    .upcoming-box { background-color: #fff4e6; border: 2px solid #ffd8a8; border-radius: 10px; padding: 15px; text-align: center; margin-bottom: 25px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    .upcoming-title { color: #d9480f; font-weight: bold; font-size: 18px; margin-bottom: 10px; }
    .upcoming-item { color: #862e01; font-size: 15px; font-weight: bold; margin-bottom: 5px; }
    
    /* 🧩 成分股標籤樣式 */
    .tag-pill { display: inline-block; background-color: #e3f2fd; color: #1565c0; padding: 5px 12px; border-radius: 15px; font-size: 14px; font-weight: bold; margin: 4px; border: 1px solid #90caf9; transition: all 0.2s;}
    .tag-pill:hover { background-color: #1e3c72; color: #fff; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 系統設定與資料庫 ---
SETTINGS_FILE = 'settings.json'

ETF_NAME_DB = {
    "0050": "0050 元大台灣50", "006208": "006208 富邦台50", "00692": "00692 富邦公司治理", 
    "00850": "00850 元大台灣ESG永續", "00922": "00922 國泰台灣領袖50", "00923": "00923 群益台ESG低碳50",
    "0056": "0056 元大高股息", "00878": "00878 國泰永續高股息", "00713": "00713 元大台灣高息低波",
    "00900": "00900 富邦特選高股息30", "00915": "00915 凱基優選高股息30", "00918": "00918 大華優利高填息30",
    "00919": "00919 群益台灣精選高息", "00929": "00929 復華台灣科技優息", "00939": "00939 統一台灣高息動能",
    "00940": "00940 元大台灣價值高息", "00944": "00944 野村趨勢動能高息", "00946": "00946 群益科技高息成長",
    "0052": "0052 富邦科技", "00881": "00881 國泰台灣5G+", "00891": "00891 中信關鍵半導體",
    "00892": "00892 富邦台灣半導體", "00927": "00927 群益半導體收益",
    "00679B": "00679B 元大美債20年", "00687B": "00687B 國泰20年美債", "00720B": "00720B 元大投資級公司債",
    "00751B": "00751B 元大AAA至A公司債", "00937B": "00937B 群益ESG投等債20+",
    "00981A": "00981A 主動統一台股增長 ETF", "00400A": "00400A 台灣主動型 ETF", "00992A": "00992A 台灣主動型 ETF",
    "00962": "00962 洲際美國大型龍頭", "00963": "00963 中信全球高股息", "00964": "00964 中信亞太高股息",
    "2330": "2330 台積電", "2454": "2454 聯發科", "2317": "2317 鴻海"
}

DIVIDEND_SCHEDULE = {
    "0050.TW": [1, 7], "0056.TW": [1, 4, 7, 10], "00878.TW": [2, 5, 8, 11],
    "00891.TW": [2, 5, 8, 11], "00919.TW": [3, 6, 9, 12], "00927.TW": [1, 4, 7, 10],
    "00929.TW": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], "00940.TW": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
}

DIVIDEND_DB = {
    "0056.TW": {"v": 1.07, "d": "2026-04-16", "p": "2026-05-15"}, 
    "00927.TW": {"v": 0.94, "d": "2026-04-18", "p": "2026-05-15"}  
}

# 🆕 戰情室專屬：熱門 ETF 核心成分股資料庫 (Top 5)
ETF_CONSTITUENTS_DB = {
    "0056.TW": ["鴻海 (2317)", "聯發科 (2454)", "聯詠 (3034)", "中信金 (2891)", "聯電 (2303)"],
    "00878.TW": ["聯發科 (2454)", "國泰金 (2882)", "富邦金 (2881)", "廣達 (2382)", "聯電 (2303)"],
    "00919.TW": ["長榮 (2603)", "聯電 (2303)", "瑞昱 (2379)", "聯發科 (2454)", "聯詠 (3034)"],
    "00927.TW": ["台積電 (2330)", "聯發科 (2454)", "聯電 (2303)", "日月光投控 (3711)", "瑞昱 (2379)"],
    "00891.TW": ["台積電 (2330)", "聯發科 (2454)", "聯電 (2303)", "日月光投控 (3711)", "瑞昱 (2379)"],
    "00929.TW": ["聯發科 (2454)", "聯電 (2303)", "日月光投控 (3711)", "瑞昱 (2379)", "聯詠 (3034)"],
    "0050.TW": ["台積電 (2330)", "鴻海 (2317)", "聯發科 (2454)", "廣達 (2382)", "台達電 (2308)"],
    "006208.TW": ["台積電 (2330)", "鴻海 (2317)", "聯發科 (2454)", "廣達 (2382)", "台達電 (2308)"],
    "00713.TW": ["統一 (1216)", "台灣大 (3045)", "遠傳 (4904)", "華碩 (2357)", "仁寶 (2324)"],
    "00940.TW": ["長榮 (2603)", "聯電 (2303)", "聯發科 (2454)", "中美晶 (5483)", "神基 (3005)"]
}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: pass
    return {
        "etfs": [
            {"symbol": "0056.TW", "name": "0056 元大高股息", "holdings": 4.1, "cost": 41.11, "alert_high": 0.0, "alert_low": 0.0},
            {"symbol": "00891.TW", "name": "00891 中信關鍵半導體", "holdings": 5.0, "cost": 31.30, "alert_high": 0.0, "alert_low": 0.0},
            {"symbol": "00919.TW", "name": "00919 群益台灣精選高息", "holdings": 10.0, "cost": 23.04, "alert_high": 0.0, "alert_low": 0.0},
            {"symbol": "00927.TW", "name": "00927 群益半導體收益", "holdings": 6.0, "cost": 27.63, "alert_high": 0.0, "alert_low": 0.0}
        ],
        "loan": {"months_paid": 1, "first_amount": 6000, "regular_amount": 15000, "total_months": 84}
    }

def save_to_json(data):
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

if 'my_data' not in st.session_state: st.session_state.my_data = load_settings()
if 'loan' not in st.session_state.my_data:
    st.session_state.my_data['loan'] = {"months_paid": 1, "first_amount": 6000, "regular_amount": 15000, "total_months": 84}
    save_to_json(st.session_state.my_data)

# 初始化所有按鈕的開關狀態 (預設收起)
if 'show_us' not in st.session_state: st.session_state.show_us = False
if 'show_tw' not in st.session_state: st.session_state.show_tw = False
if 'show_calendar' not in st.session_state: st.session_state.show_calendar = False
if 'show_div_db' not in st.session_state: st.session_state.show_div_db = False
if 'show_tech' not in st.session_state: st.session_state.show_tech = False
if 'show_holdings' not in st.session_state: st.session_state.show_holdings = False
if 'show_constituents' not in st.session_state: st.session_state.show_constituents = False # 🆕 新增成分股開關
if 'show_secret' not in st.session_state: st.session_state.show_secret = False
if 'is_unlocked' not in st.session_state: st.session_state.is_unlocked = False

def toggle_us(): st.session_state.show_us = not st.session_state.show_us
def toggle_tw(): st.session_state.show_tw = not st.session_state.show_tw
def toggle_calendar(): st.session_state.show_calendar = not st.session_state.show_calendar
def toggle_div_db(): st.session_state.show_div_db = not st.session_state.show_div_db
def toggle_tech(): st.session_state.show_tech = not st.session_state.show_tech
def toggle_holdings(): st.session_state.show_holdings = not st.session_state.show_holdings
def toggle_constituents(): st.session_state.show_constituents = not st.session_state.show_constituents # 🆕 新增切換邏輯
def toggle_secret(): st.session_state.show_secret = not st.session_state.show_secret

# --- 📡 抓取 ETF 焦點新聞 ---
@st.cache_data(ttl=3600)
def fetch_etf_news():
    news_list = []
    today_str = datetime.now().strftime("%m/%d")
    try:
        url = "https://news.google.com/rss/search?q=%E5%8F%B0%E7%81%A3+ETF+%E6%96%B0%E4%B8%8A%E5%B8%82+OR+%E9%85%8D%E6%81%AF+OR+%E6%88%90%E5%88%86%E8%82%A1&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as response:
            root = ET.fromstring(response.read())
            for item in root.findall('.//item')[:4]:
                title = item.find('title').text
                if " - " in title: title = title.rsplit(" - ", 1)[0]
                link = item.find('link').text
                news_list.append({"title": f"{today_str} {title}", "link": link})
    except Exception: pass
    
    if not news_list:
        news_list = [
            {"title": f"{today_str} 盤前觀察：半導體龍頭動向 (影響 00927 走勢)", "link": "#"},
            {"title": f"{today_str} 高股息標的篩選：關注 00878、0056 成分股調整", "link": "#"},
            {"title": f"{today_str} 焦點情報：多檔新上市 ETF 展開募集與掛牌", "link": "#"},
            {"title": f"{today_str} 大盤壓力測試：正二 (00631L) 槓桿風險控管建議", "link": "#"}
        ]
    return news_list

# --- 📈 抓取美台股大盤指標 ---
@st.cache_data(ttl=60)
def fetch_macro_data():
    tickers = {
        "us": {"道瓊工業": "^DJI", "那斯達克": "^IXIC", "費城半導體": "^SOX", "輝達 NVIDIA": "NVDA", "台積電 ADR": "TSM"},
        "tw": {"台股加權 (大盤)": "^TWII", "台積電 (台股)": "2330.TW", "聯發科 (台股)": "2454.TW", "台指期 (近月)": "WTX&P"}
    }
    res = {"us": {}, "tw": {}}
    for region, t_dict in tickers.items():
        for name, symbol in t_dict.items():
            try:
                tk = yf.Ticker(symbol)
                hist = tk.history(period="5d")
                if len(hist) >= 2:
                    curr = hist['Close'].iloc[-1]
                    prev = hist['Close'].iloc[-2]
                    diff = curr - prev
                    pct = (diff / prev) * 100
                    date_str = hist.index[-1].strftime("%m/%d")
                    res[region][name] = {"price": curr, "diff": diff, "pct": pct, "date": date_str}
            except: pass
    return res

def render_macro_cards(data_dict, region_prefix):
    cols = st.columns(3)
    idx = 0
    for name, data in data_dict.items():
        is_up = data['diff'] >= 0
        color_hex = "#e74c3c" if is_up else "#2ecc71" 
        sign = "+" if is_up else ""
        
        html = f"""
        <div style="border:1px solid #e0e0e0; border-radius:8px; border-left:6px solid {color_hex}; padding:15px; margin-bottom:15px; background:#fff; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                <div style="color:{color_hex}; font-size:15px; display:flex; align-items:center;">
                    <div style="width:10px; height:10px; border-radius:50%; background-color:{color_hex}; margin-right:6px;"></div>
                    <span style="font-weight:900; margin-right:4px;">{region_prefix}</span> <span style="font-weight:bold;">{name}</span>
                </div>
                <div style="color:#888; font-size:12px;">🕒 {data['date']}</div>
            </div>
            <div style="font-size:26px; font-weight:900; color:#111; margin-bottom:5px;">{data['price']:,.2f}</div>
            <div style="font-size:14px; font-weight:bold; color:{color_hex};">{sign}{data['diff']:,.2f} ({sign}{data['pct']:.2f}%)</div>
        </div>
        """
        with cols[idx % 3]:
            st.markdown(html, unsafe_allow_html=True)
        idx += 1

# --- 3. 側邊欄：管理功能 ---
st.sidebar.header("🚀 投資組合管理")
with st.sidebar.expander("➕ 新增標的 (股票/ETF)", expanded=False):
    raw_symbol = st.text_input("輸入代碼 (不需手打 .TW)", placeholder="例如: 00878 或 00981a")
    clean_symbol = raw_symbol.strip().upper().replace(".TW", "")
    default_name = ETF_NAME_DB.get(clean_symbol, f"{clean_symbol} ETF" if clean_symbol else "")
    
    new_name = st.text_input("自定義名稱", value=default_name, placeholder="例如: 00878 國泰永續高股息")
    new_h = st.number_input("張數", value=0.0, step=1.0, key="add_h")
    new_c = st.number_input("均價", value=0.0, step=0.1, key="add_c")
    
    if st.button("確認新增"):
        if clean_symbol and new_name:
            final_symbol = f"{clean_symbol}.TW" 
            
            st.session_state.my_data['etfs'].append({
                "symbol": final_symbol, "name": new_name, 
                "holdings": new_h, "cost": new_c, "alert_high": 0.0, "alert_low": 0.0
            })
            save_to_json(st.session_state.my_data)
            st.rerun()

st.sidebar.write("---")
st.sidebar.subheader("📝 修改與刪除")
temp_list = []
to_delete = -1
for i, item in enumerate(st.session_state.my_data['etfs']):
    with st.sidebar.expander(f"📍 {item['name']}"):
        edit_h = st.number_input(f"張數", value=float(item['holdings']), key=f"h_{i}")
        edit_c = st.number_input(f"均價", value=float(item['cost']), key=f"c_{i}")
        temp_list.append({"symbol": item['symbol'], "name": item['name'], "holdings": edit_h, "cost": edit_c, "alert_high": item.get('alert_high', 0.0), "alert_low": item.get('alert_low', 0.0)})
        if st.button(f"🗑️ 刪除標的", key=f"del_{i}"): to_delete = i

if to_delete != -1:
    st.session_state.my_data['etfs'].pop(to_delete)
    save_to_json(st.session_state.my_data)
    st.rerun()

if st.sidebar.button("💾 儲存所有修改"):
    st.session_state.my_data['etfs'] = temp_list
    save_to_json(st.session_state.my_data)
    st.sidebar.success("已存檔！")
    st.rerun()

st.sidebar.write("---")
st.sidebar.subheader("⏱️ 系統設定")
auto_refresh = st.sidebar.checkbox("開啟股價自動更新 (每 60 秒)", value=False, help="開啟後網頁將會每分鐘自動重新整理最新報價。")

# --- 4. 核心數據計算 ---
@st.cache_data(ttl=60)
def fetch_data(etf_list):
    if not etf_list: return pd.DataFrame(), pd.DataFrame(), 0, 0, 0, 0, [], [], [], {}
    results, tech_results = [], []
    total_mkt, total_cost, total_div, total_today_pnl = 0, 0, 0, 0
    radar_ex, radar_pay, price_alerts = [], [], []
    monthly_calendar = {i: {"amount": 0, "sources": []} for i in range(1, 13)} 
    today = datetime.today()

    for item in etf_list:
        try:
            tk = yf.Ticker(item['symbol'])
            hist = tk.history(period='1y') 
            if hist.empty: continue
            
            curr_p = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2] if len(hist) >= 2 else curr_p
            
            shares = item['holdings'] * 1000
            mkt_val = shares * curr_p
            cost_val = shares * item['cost']
            profit = mkt_val - cost_val
            roi = (profit / cost_val * 100) if cost_val != 0 else 0
            
            today_profit = shares * (curr_p - prev_close)
            total_today_pnl += today_profit
            
            vol = tk.fast_info.get('lastVolume', 0)
            day_high = tk.fast_info.get('dayHigh', 0)
            day_low = tk.fast_info.get('dayLow', 0)
            year_high = tk.fast_info.get('yearHigh', 0)
            year_low = tk.fast_info.get('yearLow', 0)

            a_high = float(item.get('alert_high', 0.0))
            a_low = float(item.get('alert_low', 0.0))
            if a_high > 0 and curr_p >= a_high:
                price_alerts.append({"name": item['name'], "price": curr_p, "target": a_high, "type": "high"})
            if a_low > 0 and curr_p <= a_low:
                price_alerts.append({"name": item['name'], "price": curr_p, "target": a_low, "type": "low"})

            # --- 🎯 絕對精準現金流抓取區塊 ---
            is_announced, div_amount, ex_date, pay_date = False, 0, "待官方公告", "待官方公告"
            
            cfg = DIVIDEND_DB.get(item['symbol'])
            if cfg:
                div_amount = cfg['v']
                ex_date = cfg['d']
                pay_date = cfg['p']
                is_announced = True
            else:
                actions = tk.actions
                if not actions.empty:
                    latest = actions.sort_index(ascending=False).head(1)
                    div_amount = float(latest['Dividends'].values[0]) 
                    last_ex_date_obj = latest.index[0].replace(tzinfo=None)
                    if last_ex_date_obj.date() >= today.date():
                        ex_date = last_ex_date_obj.strftime('%Y-%m-%d')
                        pay_date = (last_ex_date_obj + timedelta(days=28)).strftime('%Y-%m-%d') 
                        is_announced = True

            est_yield = 0.0
            months_to_pay = DIVIDEND_SCHEDULE.get(item['symbol'], [])
            if len(months_to_pay) > 0 and div_amount > 0 and curr_p > 0:
                est_yield = (div_amount * len(months_to_pay)) / curr_p * 100

            if is_announced:
                ex_date_obj = datetime.strptime(ex_date, '%Y-%m-%d')
                days_diff_ex = (ex_date_obj.date() - today.date()).days
                if 0 <= days_diff_ex <= 20: radar_ex.append({"symbol": item['symbol'].split('.')[0], "date": ex_date, "days": days_diff_ex})
                
                pay_date_obj = datetime.strptime(pay_date, '%Y-%m-%d')
                days_diff_pay = (pay_date_obj.date() - today.date()).days
                if 0 <= days_diff_pay <= 20: radar_pay.append({"symbol": item['symbol'].split('.')[0], "date": pay_date, "amount": shares * div_amount, "days": days_diff_pay})

            # --- 📅 終極精準：入帳日計算邏輯 ---
            if div_amount > 0 and shares > 0:
                explicit_pay_month = None
                if is_announced and pay_date != "待官方公告":
                    explicit_pay_month = datetime.strptime(pay_date, '%Y-%m-%d').month
                    monthly_calendar[explicit_pay_month]["amount"] += (shares * div_amount)
                    if item['name'] not in monthly_calendar[explicit_pay_month]["sources"]:
                        monthly_calendar[explicit_pay_month]["sources"].append(item['name'])

                for m in months_to_pay:
                    pay_m = m + 1 if m < 12 else 1
                    if pay_m != explicit_pay_month:
                        monthly_calendar[pay_m]["amount"] += (shares * div_amount)
                        if item['name'] not in monthly_calendar[pay_m]["sources"]:
                            monthly_calendar[pay_m]["sources"].append(item['name'])

            # --- ⏳ 智能計算「最新填息天數」 ---
            fill_status = "-"
            try:
                divs = tk.dividends
                if not divs.empty:
                    now_ts = pd.Timestamp.now(tz=divs.index.tzinfo) if divs.index.tzinfo else pd.Timestamp.now()
                    past_divs = divs[divs.index < now_ts].sort_index(ascending=False)
                    
                    if not past_divs.empty:
                        last_ex_date = past_divs.index[0]
                        pre_ex = hist[hist.index < last_ex_date]
                        post_ex = hist[hist.index >= last_ex_date]
                        
                        if not pre_ex.empty and not post_ex.empty:
                            target_price = pre_ex['Close'].iloc[-1]
                            filled = False
                            t_days = 0
                            for d, r in post_ex.iterrows():
                                t_days += 1
                                if r['High'] >= target_price:
                                    fill_status = f"{t_days} 天"
                                    filled = True
                                    break
                            if not filled:
                                fill_status = f"未填息 ({t_days}天)"
            except Exception:
                pass

            total_mkt += mkt_val; total_cost += cost_val; total_div += (shares * div_amount)
            
            results.append({
                "代號": item['symbol'], "名稱": item['name'], "現價": curr_p, "均價": item['cost'],
                "張數": item['holdings'], "市值": mkt_val, "損益": profit, "報酬率": roi,
                "單次預估領息": shares * div_amount, "每股配息": div_amount,
                "最新公告除息日": ex_date, "預估發放日": pay_date, "已公告": is_announced,
                "最新填息紀錄": fill_status 
            })
            
            tech_results.append({
                "ETF 名稱": item['name'], "現價": round(curr_p, 2),
                "今日交易量": f"{vol:,.0f}" if vol > 0 else "無資料",
                "預估年化殖利率": f"{est_yield:.2f}%",
                "今日最高/最低": f"${day_high:.2f} / ${day_low:.2f}",
                "52週最高/最低": f"${year_high:.2f} / ${year_low:.2f}",
                "設定高標(停利)": a_high,
                "設定低標(停損)": a_low
            })
            
        except Exception as e: continue
        
    return pd.DataFrame(results), pd.DataFrame(tech_results), total_mkt, total_cost, total_div, total_today_pnl, radar_ex, radar_pay, price_alerts, monthly_calendar

df, df_tech, g_mkt, g_cost, g_div, g_today_pnl, radar_ex, radar_pay, price_alerts, monthly_calendar = fetch_data(st.session_state.my_data['etfs'])
macro_data = fetch_macro_data()

# --- 5. 介面呈現 ---
st.title("📈 實戰資產戰情室")
st.caption(f"最後更新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# --- 📰 頂部模組：今日財經焦點 ---
news_data = fetch_etf_news()
news_html = "<div class='news-box'><div class='news-title'>📰 今日財經焦點</div>"
for news in news_data:
    news_html += f"<div class='news-item'>👉 📍 <a href='{news['link']}' target='_blank'>{news['title']}</a></div>"
news_html += "</div>"
st.markdown(news_html, unsafe_allow_html=True)

# --- 🆕 追加區塊：即將掛牌 ETF 觀測區 ---
st.markdown("### 🗓️ 即將掛牌 ETF 追蹤")
upcoming_list = [
    {"date": "2024/11/14", "symbol": "00963", "name": "中信全球高股息", "price": "15.00"},
    {"date": "2024/11/14", "symbol": "00964", "name": "中信亞太高股息", "price": "10.00"},
    {"date": "2024/12/05", "symbol": "00962", "name": "洲際美國大型龍頭", "price": "15.00"},
]
up_cols = st.columns(len(upcoming_list))
for i, etf in enumerate(upcoming_list):
    with up_cols[i]:
        st.markdown(f"""
        <div class='upcoming-box'>
            <div class='upcoming-title'>🚀 預計掛牌日：{etf['date']}</div>
            <div class='upcoming-item'>{etf['symbol']} {etf['name']}</div>
            <div style='font-size:12px; color:#888;'>發行價：${etf['price']}</div>
        </div>
        """, unsafe_allow_html=True)
st.write("")

if not df.empty:
    
    # 🚨 動態脈衝價格越界警報
    if price_alerts:
        for alert in price_alerts:
            if alert['type'] == "high":
                st.markdown(f"<div class='alert-high'>🚨 突破停利高標：【{alert['name']}】 現價 ${alert['price']:.2f} 已突破您設定的 ${alert['target']}！</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='alert-low'>⚠️ 跌破停損低標：【{alert['name']}】 現價 ${alert['price']:.2f} 已跌破您設定的 ${alert['target']}！</div>", unsafe_allow_html=True)

    # 👾 雙重雷達戰情室 
    st.markdown("### 👾 羅小翔專用：雙重雷達戰情室")
    col1, col2 = st.columns(2)
    with col1:
        if radar_ex:
            radar_ex = sorted(radar_ex, key=lambda x: x['days'])
            ex_content = "".join([f"<div style='margin-bottom: 8px; font-weight:bold;'>標的 {r['symbol']} 將於 {r['date'][5:7]}/{r['date'][8:10]} 除息 (倒數 {r['days']} 天)</div>" for r in radar_ex])
            st.markdown(f"<div class='ex-div-box'><div class='ex-div-title'>⚡ 除息雷達提醒 ⚡</div><div class='ex-div-text'>{ex_content}</div></div>", unsafe_allow_html=True)
        else:
            current_m = datetime.today().month
            next_m = current_m + 1 if current_m < 12 else 1
            this_m_etfs = [etf['symbol'].split('.')[0] for etf in st.session_state.my_data['etfs'] if current_m in DIVIDEND_SCHEDULE.get(etf['symbol'], [])]
            next_m_etfs = [etf['symbol'].split('.')[0] for etf in st.session_state.my_data['etfs'] if next_m in DIVIDEND_SCHEDULE.get(etf['symbol'], [])]
            
            if this_m_etfs:
                msg = f"本月 ({current_m}月) 預備除息標的：<br><span style='color:#d32f2f; font-size:18px;'>{', '.join(this_m_etfs)}</span><br><span style='font-size:12px; color:#888;'>雷達持續掃描官方公告中...</span>"
            elif next_m_etfs:
                msg = f"下個月 ({next_m}月) 預備除息標的：<br><span style='color:#d32f2f; font-size:18px;'>{', '.join(next_m_etfs)}</span><br><span style='font-size:12px; color:#888;'>雷達持續掃描官方公告中...</span>"
            else:
                msg = "目前無 20 天內已公告之除息<br><span style='font-size:12px; color:#888;'>近期亦無表定除息標的</span>"
                
            st.markdown(f" <div class='ex-div-box' style='background-color: #f4f6f8; border: 2px dashed #adb5bd; box-shadow: none;'><div class='ex-div-title' style='color: #6c757d;'>📡 預測雷達 (等待官方公告)</div><div class='ex-div-text' style='color: #495057;'>{msg}</div></div>", unsafe_allow_html=True)

    with col2:
        if radar_pay:
            radar_pay = sorted(radar_pay, key=lambda x: x['days'])
            pay_content = "".join([f"<div style='margin-bottom: 8px; font-weight:bold;'>標的 {r['symbol']} 股息約 ${r['amount']:,.0f} 將於 {r['date'][5:7]}/{r['date'][8:10]} 入帳 (倒數 {r['days']} 天)！</div>" for r in radar_pay])
            st.markdown(f"<div class='pay-div-box'><div class='pay-div-title'>💰 領息雷達提醒 💰</div><div class='pay-div-text'>{pay_content}</div></div>", unsafe_allow_html=True)
        else: st.info("目前無 20 天內領息雷達提示")

    # --- 💰 終極損益與現金流黃金大看板 ---
    p_total = g_mkt - g_cost
    r_total = (p_total / g_cost * 100) if g_cost != 0 else 0
    prev_mkt = g_mkt - g_today_pnl
    today_pct = (g_today_pnl / prev_mkt * 100) if prev_mkt != 0 else 0

    today_val_str = f"+{g_today_pnl:,.0f}" if g_today_pnl >= 0 else f"{g_today_pnl:,.0f}"
    today_pct_str = f"+{today_pct:.2f}%" if today_pct >= 0 else f"{today_pct:.2f}%"
    today_c_val = "triple-val-r" if g_today_pnl >= 0 else "triple-val-g"
    today_c_pct = "triple-pct-r" if g_today_pnl >= 0 else "triple-pct-g"

    total_val_str = f"+{p_total:,.0f}" if p_total >= 0 else f"{p_total:,.0f}"
    total_pct_str = f"+{r_total:.2f}%" if r_total >= 0 else f"{r_total:.2f}%"
    total_c_val = "triple-val-r" if p_total >= 0 else "triple-val-g"
    total_c_pct = "triple-pct-r" if p_total >= 0 else "triple-pct-g"

    current_month_num = datetime.today().month
    current_month_div_amount = monthly_calendar[current_month_num]["amount"]
    current_month_div_str = f"${current_month_div_amount:,.0f}"
    div_sources = monthly_calendar[current_month_num]["sources"]
    if div_sources:
        sources_str = "、".join([s.split(' ')[0] for s in div_sources]) 
        sub_title = f"來自：{sources_str}"
    else:
        sub_title = "本月無現金流入預定"

    html_triple_pnl = f"""
<div class="triple-box">
    <div class="triple-col">
        <div class="triple-title">今日損益</div>
        <div class="{today_c_val}">{today_val_str}</div>
        <div class="{today_c_pct}">{today_pct_str}</div>
    </div>
    <div class="triple-divider"></div>
    <div class="triple-col">
        <div class="triple-title">累積損益</div>
        <div class="{total_c_val}">{total_val_str}</div>
        <div class="{total_c_pct}">{total_pct_str}</div>
    </div>
    <div class="triple-divider"></div>
    <div class="triple-col" style="background-color: #fffdf5; border-radius: 12px; padding: 20px; border: 1px solid #f1c40f; text-align: center;">
        <div class="triple-title" style="color: #b48608; margin-bottom: 5px; font-size: 16px;">🗓️ {current_month_num} 月預估領息總額</div>
        <div class="triple-val-gold">{current_month_div_str}</div>
        <div class="triple-sub-gold">{sub_title}</div>
    </div>
</div>
"""
    st.markdown(html_triple_pnl, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("股票總市值", f"${g_mkt:,.0f}")
    c2.metric("投資總成本", f"${g_cost:,.0f}")
    c3.metric("全年預估總領息", f"${sum([monthly_calendar[m]['amount'] for m in range(1, 13)]):,.0f}")
    st.write("---")
    
    # --- 🗄️ 動態切換控制台 (🌟 擴充為 8 顆按鈕) ---
    us_icon = "🌏"
    if "us" in macro_data and macro_data["us"]:
        us_up = sum(1 for v in macro_data["us"].values() if v['diff'] >= 0)
        us_down = len(macro_data["us"]) - us_up
        us_icon = "🔴" if us_up >= us_down else "🟢"

    tw_icon = "🇹🇼"
    if "tw" in macro_data and macro_data["tw"]:
        tw_up = sum(1 for v in macro_data["tw"].values() if v['diff'] >= 0)
        tw_down = len(macro_data["tw"]) - tw_up
        tw_icon = "🔴" if tw_up >= tw_down else "🟢"

    # 調整為 8 欄
    cols_btn = st.columns(8)
    
    b1_lbl, b1_typ = (f"🔽 收起美股 {us_icon}", "primary") if st.session_state.show_us else (f"{us_icon} 展開美股", "secondary")
    b2_lbl, b2_typ = (f"🔽 收起台股 {tw_icon}", "primary") if st.session_state.show_tw else (f"{tw_icon} 展開台股", "secondary")
    b3_lbl, b3_typ = ("🔽 收起日曆", "primary") if st.session_state.show_calendar else ("📅 展開日曆", "secondary")
    b4_lbl, b4_typ = ("🔽 收起除權息", "primary") if st.session_state.show_div_db else ("📂 展開除權息", "secondary")
    b5_lbl, b5_typ = ("🔽 收起監控", "primary") if st.session_state.show_tech else ("📡 展開監控", "secondary")
    b6_lbl, b6_typ = ("🔽 收起明細", "primary") if st.session_state.show_holdings else ("📊 展開明細", "secondary")
    b7_lbl, b7_typ = ("🔽 收起成分", "primary") if st.session_state.show_constituents else ("🧩 展開成分", "secondary") # 🆕 新按鈕
    b8_lbl, b8_typ = ("🔽 收起機密", "primary") if st.session_state.show_secret else ("🔐 展開機密", "secondary")

    with cols_btn[0]: st.button(b1_lbl, on_click=toggle_us, type=b1_typ, use_container_width=True)
    with cols_btn[1]: st.button(b2_lbl, on_click=toggle_tw, type=b2_typ, use_container_width=True)
    with cols_btn[2]: st.button(b3_lbl, on_click=toggle_calendar, type=b3_typ, use_container_width=True)
    with cols_btn[3]: st.button(b4_lbl, on_click=toggle_div_db, type=b4_typ, use_container_width=True)
    with cols_btn[4]: st.button(b5_lbl, on_click=toggle_tech, type=b5_typ, use_container_width=True)
    with cols_btn[5]: st.button(b6_lbl, on_click=toggle_holdings, type=b6_typ, use_container_width=True)
    with cols_btn[6]: st.button(b7_lbl, on_click=toggle_constituents, type=b7_typ, use_container_width=True) # 🆕 綁定成分股
    with cols_btn[7]: st.button(b8_lbl, on_click=toggle_secret, type=b8_typ, use_container_width=True)
    st.write("---")

    if st.session_state.show_us and "us" in macro_data and macro_data["us"]:
        st.markdown("#### 🌏 關鍵美股指標")
        render_macro_cards(macro_data["us"], "us")
        st.write("")

    if st.session_state.show_tw and "tw" in macro_data and macro_data["tw"]:
        st.markdown("#### 🇹🇼 關鍵台股點數")
        render_macro_cards(macro_data["tw"], "tw")
        st.write("---")

    if st.session_state.show_calendar:
        st.markdown("#### 📅 1~12月 預估領息日曆")
        month_options = [f"{m} 月" for m in range(1, 13)]
        default_index = datetime.today().month - 1
        selected_month_str = st.selectbox("請選擇您想查詢的月份：", month_options, index=default_index)
        selected_month = int(selected_month_str.replace(" 月", ""))
        data = monthly_calendar[selected_month]
        sources_text = "、".join(data["sources"]) if data["sources"] else "本月無除息預定"
        amount_text = f"${data['amount']:,.0f}" if data["amount"] > 0 else "$0"
        col_space1, col_center, col_space2 = st.columns([1, 2, 1])
        with col_center:
            st.markdown(f"""
            <div class='month-card'>
                <div class='month-title'>{selected_month} 月預估領息</div>
                <div class='month-amount'>{amount_text}</div>
                <div class='month-sources'>ETF 來源：{sources_text}</div>
            </div>
            """, unsafe_allow_html=True)
        st.write("---")

    if st.session_state.show_div_db:
        st.markdown("#### 📚 專屬 ETF 除權息時程總覽")
        db_list = []
        for _, row in df.iterrows():
            sym = row['代號']; months = DIVIDEND_SCHEDULE.get(sym, [])
            freq = "月配息" if len(months)==12 else "季配息" if len(months)==4 else "半年配" if len(months)==2 else "年配息" if len(months)==1 else "未知"
            db_list.append({
                "ETF 名稱": row['名稱'], 
                "配息頻率": freq, 
                "配息月份": "、".join(map(str, months)) + " 月" if months else "未設定",
                "狀態": "✅ 已公告" if row['已公告'] else "⏳ 依前次估算", 
                "除息日": row['最新公告除息日'], 
                "發放日": row['預估發放日'], 
                "每股金額": f"${row['每股配息']:.3f}",
                "最新填息紀錄": row['最新填息紀錄']
            })
        st.dataframe(pd.DataFrame(db_list), use_container_width=True, hide_index=True)
        st.write("---")

    if st.session_state.show_tech:
        st.markdown("#### 📡 價格區間監控與技術分析 (👉 雙擊表格中的數值即可設定警報，設 0 代表關閉)")
        edited_tech = st.data_editor(
            df_tech,
            column_config={
                "設定高標(停利)": st.column_config.NumberColumn("設定高標(停利)", help="雙擊輸入，超過觸發紅色警報", min_value=0.0, format="%.2f"),
                "設定低標(停損)": st.column_config.NumberColumn("設定低標(停損)", help="雙擊輸入，低於觸發綠色警報", min_value=0.0, format="%.2f"),
            },
            disabled=["ETF 名稱", "現價", "今日交易量", "預估年化殖利率", "今日最高/最低", "52週最高/最低"],
            use_container_width=True, hide_index=True
        )

        has_changes = False
        for _, row in edited_tech.iterrows():
            name = row['ETF 名稱']
            for etf in st.session_state.my_data['etfs']:
                if etf['name'] == name:
                    if etf.get('alert_high', 0.0) != row['設定高標(停利)'] or etf.get('alert_low', 0.0) != row['設定低標(停損)']:
                        etf['alert_high'] = row['設定高標(停利)']
                        etf['alert_low'] = row['設定低標(停損)']
                        has_changes = True
                    break
        if has_changes:
            save_to_json(st.session_state.my_data)
            st.cache_data.clear()
            st.rerun()
        st.write("---")
    
    if st.session_state.show_holdings:
        st.markdown("#### 📊 持股動態明細")
        for _, row in df.iterrows():
            p_color = "red" if row['損益'] >= 0 else "green"; roi_str = f"{row['報酬率']:+.2f}%"
            status_badge = "✅ 已公告" if row['已公告'] else "⏳ 依前次估算"
            with st.expander(f"💎 {row['名稱']} | 報酬: :{p_color}[{roi_str}]", expanded=True):
                col_l, col_m, col_r = st.columns(3)
                with col_l: st.write(f"張數: **{row['張數']}**"); st.write(f"現價: **{row['現價']:.2f}**"); st.caption(f"均價: {row['均價']:.2f}")
                with col_m: st.markdown(f"市值: **${row['市值']:,.0f}**"); st.markdown(f"損益: :{p_color}[**${row['損益']:,.0f}**]")
                with col_r: st.markdown(f"單次領息估算: :orange[**${row['單次預估領息']:,.0f}**]"); st.caption(f"📅 最新除息日: {row['最新公告除息日']} ({status_badge})")
        st.write("---")

    # 🆕 區塊：專屬庫存 ETF 核心成分股
    if st.session_state.show_constituents:
        st.markdown("#### 🧩 專屬庫存 ETF 核心成分股 (Top 5 權重)")
        st.caption("透過檢視成分股，可避免資金過度集中於單一個股（例如台積電或聯發科），降低系統性風險。")
        
        c_cols = st.columns(3)
        for idx, item in enumerate(st.session_state.my_data['etfs']):
            sym = item['symbol']
            name = item['name']
            # 從自建資料庫抓取成分股，找不到就給預設提示
            comps = ETF_CONSTITUENTS_DB.get(sym, ["暫無成分股資料，請手動查詢"])
            
            # 將成分股轉換為標籤 (Pill) 樣式
            tags_html = "".join([f"<span class='tag-pill'>{c}</span>" for c in comps])
            
            card_html = f"""
            <div style="background:#fff; border:1px solid #e0e0e0; border-radius:12px; padding:20px; margin-bottom:20px; box-shadow: 2px 2px 8px rgba(0,0,0,0.06); height:90%;">
                <div style="font-weight:900; color:#1e3c72; font-size:16px; margin-bottom:12px;">🛡️ {name}</div>
                <div>{tags_html}</div>
            </div>
            """
            with c_cols[idx % 3]:
                st.markdown(card_html, unsafe_allow_html=True)
        st.write("---")

    if st.session_state.show_secret:
        st.markdown("<div class='secret-box'>", unsafe_allow_html=True)
        st.markdown("#### 🔐 總司令專屬機密戰情區")
        
        if not st.session_state.is_unlocked:
            st.warning("您即將進入機密區域，請輸入授權密碼。")
            pwd = st.text_input("輸入 4 位數密碼：", type="password", key="secret_pwd")
            if st.button("解鎖 🔓"):
                if pwd == "1030":
                    st.session_state.is_unlocked = True
                    st.rerun()
                else:
                    st.error("密碼錯誤，拒絕存取。")
        else:
            st.success("✅ 密碼正確，機密面板已解鎖！")
            st.markdown("##### 💰 隱藏資產結算 (ETF)")
            sc1, sc2 = st.columns(2)
            sc1.metric("總投入本金 (成本)", f"${g_cost:,.0f}")
            sc2.metric("總未實現淨利", f"${(g_mkt - g_cost):,.0f}", f"{(g_mkt - g_cost) / g_cost * 100:.2f}%")
            st.write("---")
            
            st.markdown("##### 💳 信貸還款戰情 (7年 / 84期)")
            loan_data = st.session_state.my_data['loan']
            new_paid = st.slider("調整已繳納期數 (目前為第幾個月？)", min_value=1, max_value=84, value=int(loan_data['months_paid']))
            if new_paid != loan_data['months_paid']:
                st.session_state.my_data['loan']['months_paid'] = new_paid
                save_to_json(st.session_state.my_data)
                st.rerun()

            total_loan = loan_data['first_amount'] + (loan_data['total_months'] - 1) * loan_data['regular_amount']
            amount_paid = loan_data['first_amount'] + max(0, new_paid - 1) * loan_data['regular_amount']
            remaining_balance = total_loan - amount_paid
            remaining_months = loan_data['total_months'] - new_paid
            
            lc1, lc2, lc3 = st.columns(3)
            lc1.metric("信貸合約總額", f"${total_loan:,.0f}")
            lc2.metric("已繳納本息總額", f"${amount_paid:,.0f}", f"已繳 {new_paid} 期", delta_color="off")
            lc3.metric("剩餘未繳餘額", f"${remaining_balance:,.0f}", f"剩餘 {remaining_months} 期", delta_color="inverse")
            st.progress(new_paid / loan_data['total_months'])
            
            true_net_worth = g_mkt - remaining_balance
            st.markdown(f"<div class='net-worth-box'><h3>👑 總司令真實淨資產 (ETF 總市值 - 信貸剩餘餘額)</h3><h1>${true_net_worth:,.0f}</h1></div>", unsafe_allow_html=True)
            st.write("")
            if st.button("🔐 重新上鎖並關閉"):
                st.session_state.is_unlocked = False
                st.session_state.show_secret = False
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        st.write("---")

st.write("---")
if st.button("🔄 手動重新整理股價"):
    st.cache_data.clear()
    st.rerun()

if auto_refresh:
    time.sleep(60)
    st.cache_data.clear()
    st.rerun()

# --- 🚀 追加區塊：使用 Altair 進行進階歷史漲跌圖渲染 ---
st.write("---")
st.markdown("### 📈 持股歷史股價趨勢 (近 30 日)")

current_etfs = [item['symbol'] for item in st.session_state.my_data.get('etfs', [])]

if current_etfs:
    with st.spinner("正在繪製高精度股價戰報..."):
        try:
            price_history = yf.download(current_etfs, period="1mo")['Close']
            
            if len(current_etfs) == 1:
                price_history = price_history.to_frame()
                price_history.columns = [st.session_state.my_data['etfs'][0]['name']]
            else:
                name_map = {item['symbol']: item['name'] for item in st.session_state.my_data['etfs']}
                price_history = price_history.rename(columns=name_map)
            
            # --- 將資料轉為 Altair 需要的長格式 ---
            df_chart = price_history.reset_index()
            date_col = df_chart.columns[0]
            df_melted = df_chart.melt(id_vars=[date_col], var_name='ETF', value_name='Price')

            # --- 建立 Altair 互動圖表 ---
            chart = alt.Chart(df_melted).mark_line().encode(
                x=alt.X(f'{date_col}:T',
                        axis=alt.Axis(
                            format='%d日',      # 🎯 強制格式化為 30日、01日
                            title=None,
                            grid=False
                        )),
                y=alt.Y('Price:Q',
                        scale=alt.Scale(zero=False), # 不強制從 0 開始，讓細節更清楚
                        axis=alt.Axis(
                            title=None,
                            labelFontSize=10,  # 🎯 字體縮小
                            tickMinStep=1,     # 🎯 最小間距為 1 
                            tickCount=40,      # 🎯 強制增加刻度數量，逼近 0,1,2,3... 的密度
                            gridColor='#f0f2f6'
                        )),
                color=alt.Color('ETF:N', legend=alt.Legend(title=None, orient="bottom")),
                tooltip=[
                    alt.Tooltip(f'{date_col}:T', format='%Y/%m/%d', title='日期'),
                    alt.Tooltip('ETF:N', title='標的'),
                    alt.Tooltip('Price:Q', format='.2f', title='收盤價')
                ]
            ).properties(
                height=450
            ).interactive()

            # 渲染圖表
            st.altair_chart(chart, use_container_width=True)
            st.caption("數據來源：Yahoo Finance (近一個月每日收盤價趨勢)")
        except Exception as e:
            st.error(f"圖表產生失敗：{e}")
            st.info("提示：請確認網路連線正常或 ETF 代碼是否正確。")
else:
    st.info("目前庫存中沒有標的。")