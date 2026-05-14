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
import requests

# --- 1. 網頁基礎設定 ---
st.set_page_config(page_title="ETF 投資戰情室", layout="wide")

# 自定義 CSS (美化與隱藏工具列)
st.markdown("""
    <style>
    [data-testid="stElementToolbar"], [data-testid="stDataFrameToolbar"], [data-testid="stToolbar"] { display: none !important; }
    [data-testid="stMetricDelta"] svg { fill: red; }
    [data-testid="stMetric"] { 
        background-color: var(--secondary-background-color); 
        padding: 12px; border-radius: 10px; box-shadow: 1px 1px 4px rgba(0,0,0,0.05);
    }
    .flash-gold-box { 
        background-color: #fffdf5; border-radius: 12px; padding: 15px; border: 2px solid #f1c40f; 
        animation: lightning 0.1s infinite; 
    }
    @keyframes lightning {
        0% { box-shadow: 0 0 5px #f1c40f; }
        50% { box-shadow: 0 0 20px #f1c40f; }
        100% { box-shadow: 0 0 5px #f1c40f; }
    }
    .alert-high { background-color: #ffebee; border: 2px solid #ef5350; border-left: 8px solid #d32f2f; padding: 15px; border-radius: 8px; margin-bottom: 15px; color: #b71c1c; font-size: 16px; font-weight: bold; }
    .alert-low { background-color: #e8f5e9; border: 2px solid #66bb6a; border-left: 8px solid #388e3c; padding: 15px; border-radius: 8px; margin-bottom: 15px; color: #1b5e20; font-size: 16px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 系統設定與資料庫 ---
SETTINGS_FILE = 'settings.json'

# --- 深度校正版 ETF 資料庫 ---
ETF_FULL_DATABASE = {
    "0050": ["元大台灣50", [1, 7], "0.32%", "0.035%"],
    "0051": ["元大中型100", [11], "0.4%", "0.035%"],
    "0052": ["富邦台灣科技指數", [4], "0.15%", "0.035%"],
    "0053": ["元大台灣電子科技", [11], "0.3%", "0.035%"],
    "0055": ["元大MSCI金融", [11], "0.3%", "0.035%"],
    "0056": ["元大台灣高股息", [1, 4, 7, 10], "0.3%", "0.035%"],
    "0057": ["富邦摩台", [6], "0.15%", "0.035%"],
    "006201": ["元大富櫃50", [12], "0.4%", "0.035%"],
    "006203": ["元大摩臺台灣", [1, 7], "0.3%", "0.035%"],
    "006204": ["永豐臺灣加權", [10], "0.32%", "0.035%"],
    "006208": ["富邦台50", [7, 11], "0.15%", "0.035%"],
    "00690": ["兆豐藍籌30", [2, 5, 8, 11], "0.32%", "0.035%"],
    "00692": ["富邦臺灣公司治理", [7, 11], "0.15%", "0.035%"],
    "00701": ["國泰股利精選30", [1, 8], "0.3%", "0.035%"],
    "00713": ["元大台灣高息低波", [3, 6, 9, 12], "0.3%", "0.035%"],
    "00728": ["第一金工業30", [3, 6, 9, 12], "0.4%", "0.035%"],
    "00730": ["富邦臺灣優質高息", list(range(1, 13)), "0.45%", "0.035%"],
    "00731": ["復華富時高息低波", [2, 5, 8, 11], "0.3%", "0.035%"],
    "00733": ["富邦臺灣中小", [5, 10], "0.4%", "0.035%"],
    "00850": ["元大臺灣ESG永續", [2, 5, 8, 11], "0.3%", "0.035%"],
    "00878": ["國泰永續ESG高股息", [2, 5, 8, 11], "0.25%", "0.035%"],
    "00881": ["國泰台灣5G+", [1, 8], "0.4%", "0.035%"],
    "00888": ["永豐台灣ESG永續優質", [1, 4, 7, 10], "0.25%", "0.03%"],
    "00891": ["中信關鍵半導體", [2, 5, 8, 11], "0.4%", "0.035%"],
    "00892": ["富邦台灣核心半導體", [], "0.4%", "0.035%"],
    "00894": ["中信特選小資高價30", [2, 5, 8, 11], "0.4%", "0.035%"],
    "00896": ["中信綠能及電動車", [3, 6, 9, 12], "0.4%", "0.035%"],
    "00900": ["富邦特選高股息30", [2, 5, 8, 11], "0.3%", "0.035%"],
    "00901": ["永豐台灣智能車供應鏈", [10], "0.4%", "0.04%"],
    "00904": ["新光臺灣半導體30", [1, 4, 7, 10], "0.4%", "0.035%"],
    "00905": ["FT臺灣Smart", [1, 4, 7, 10], "0.4%", "0.035%"],
    "00907": ["永豐優選存股", [2, 4, 6, 8, 10, 12], "0.4%", "0.03%"],
    "00912": ["中信台灣智慧50", [1, 4, 7, 10], "0.3%", "0.035%"],
    "00913": ["兆豐晶圓製造", [1, 7], "0.4%", "0.03%"],
    "00915": ["凱基優選高股息30", [3, 6, 9, 12], "0.3%", "0.035%"],
    "00918": ["大華優利高填息30", [3, 6, 9, 12], "0.35%", "0.035%"],
    "00919": ["群益台灣精選高息", [3, 6, 9, 12], "0.3%", "0.035%"],
    "00921": ["兆豐龍頭等權重", [3, 6, 9, 12], "0.45%", "0.030%"],
    "00922": ["國泰台灣領袖50", [3, 10], "0.20%", "0.035%"],
    "00923": ["群益台灣ESG低碳50", [2, 8], "0.32%", "0.035%"],
    "00927": ["群益台灣半導體收益", [1, 4, 7, 10], "0.4%", "0.035%"],
    "00928": ["中信上櫃ESG30", [1, 7], "0.4%", "0.035%"],
    "00929": ["復華台灣科技優息", list(range(1, 13)), "0.30%", "0.030%"],
    "00930": ["永豐ESG低碳高息", [1, 3, 5, 7, 9, 11], "0.35%", "0.035%"],
    "00932": ["兆豐永續高息等權", [2, 5, 8, 11], "0.15%", "0.030%"],
    "00934": ["中信成長高股息", list(range(1, 13)), "0.3%", "0.035%"],
    "00935": ["野村臺灣創新科技50", [3, 9], "0.4%", "0.035%"],
    "00936": ["台新永續高息中小", list(range(1, 13)), "0.4%", "0.035%"],
    "00938": ["凱基優選30", [2, 5, 8, 11], "0.3%", "0.35%"],
    "00939": ["統一台灣高息動力", list(range(1, 13)), "0.3%", "0.035%"],
    "00940": ["元大臺灣價值高息", list(range(1, 13)), "0.3%", "0.030%"],
    "00943": ["兆豐電子高息等權", list(range(1, 13)), "0.25%", "0.03%"],
    "00944": ["野村臺灣趨勢動能高股息", list(range(1, 13)), "0.4%", "0.035%"],
    "00946": ["群益台灣科技高息成長", list(range(1, 13)), "0.3%", "0.030%"],
    "00947": ["台新臺灣IC設計動能", [1, 4, 7, 10], "0.40%", "0.030%"],
    "00952": ["凱基台灣AI 50", list(range(1, 13)), "0.40%", "0.030%"],
    "00961": ["FT臺灣永續高息", list(range(1, 13)), "0.30%", "0.035%"],
    "00962": ["台新臺灣AI優息動能", list(range(1, 13)), "0.40%", "0.035%"],
    "009802": ["富邦旗艦50", [3, 6, 9, 12], "0.15%", "0.03%"],
    "009803": ["保德信市值動能50", [3, 6, 9, 12], "0.25%", "0.035%"],
    "009804": ["聯邦台灣精彩50", [4, 7], "0.15%", "0.035%"],
    "009808": ["華南永昌台灣優選50", [2, 5, 8, 11], "0.05%", "0.035%"],
    "009809": ["富邦台灣淨零轉型 ESG 50", [3, 6, 9, 12], "0.30%", "0.035%"],
    "00980A": ["野村臺灣智慧優選主動式", [2, 5, 8, 11], "0.75%", "0.035%"],
    "00981A": ["統一台股增長主動式", [3, 6, 9, 12], "1.0%", "0.10%"],
    "00982A": ["群益台灣精選強棒主動式", [2, 5, 8, 11], "0.8%", "0.035%"],
    "00984A": ["安聯台灣高息成長主動式", [1, 4, 7, 10], "0.7%", "0.04%"],
    "00985A": ["野村台灣增強50主動式", [1], "0.45%", "0.035%"],
    "00981T": ["平衡凱基雙核收息", [], "0.60%", "0.10%"]
}

EXTRA_ETFS = {
    "00631L": "00631L 元大台灣50正2", "00673R": "00673R 期元大S&P原油反1", 
    "00632R": "00632R 元大台灣50反1", "009819": "009819 中信數據及電力", 
    "00712": "00712 復華富時不動產", "00992A": "00992A 主動群益科技創新",
    "00400A": "00400A 主動國泰動能高息", "00997A": "00997A 主動群益美國增長",
    "00988A": "00988A 主動統一全球創新", "00994A": "00994A 主動第一金台股優",
    "00646": "00646 元大S&P500", "00662": "00662 富邦NASDAQ", 
    "00830": "00830 國泰費城半導體", "00757": "00757 統一FANG+", 
    "00882": "00882 中信中國高股息", "00963": "00963 中信全球高股息", 
    "00964": "00964 中信亞太高股息", "00679B": "00679B 元大美債20年", 
    "00687B": "00687B 國泰20年美債", "00720B": "00720B 元大投資級公司債",
    "00751B": "00751B 元大AAA至A公司債", "00937B": "00937B 群益ESG投等債20+", 
    "00772B": "00772B 中信高評級公司債", "00773B": "00773B 中信優先金融債", 
    "00780B": "00780B 國泰A級金融債", "00795B": "00795B 中信美國公債20年",
    "2330": "2330 台積電", "2454": "2454 聯發科", "2317": "2317 鴻海"
}

ETF_NAME_DB = {}
DIVIDEND_SCHEDULE = {}
ETF_FEES_DB = {}

for k, v in EXTRA_ETFS.items():
    ETF_NAME_DB[k] = v

for k, v in ETF_FULL_DATABASE.items():
    ETF_NAME_DB[k] = f"{k} {v[0]}"
    DIVIDEND_SCHEDULE[f"{k}.TW"] = v[1]
    ETF_FEES_DB[f"{k}.TW"] = {"經理費": v[2], "保管費": v[3]}

def load_settings():
    default_data = {
        "etfs": [], 
        "pledge": {"borrowed_amount": 0},
        "watchlist": [],
        "custom_divs": {},
        "personal_finance": {"incomes": [], "expenses": []}
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f: 
                data = json.load(f)
                for k, v in default_data.items():
                    if k not in data: data[k] = v
                return data
        except: pass
    return default_data

def save_to_json(data):
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

if 'my_data' not in st.session_state: 
    st.session_state.my_data = load_settings()

if 'watchlist' not in st.session_state.my_data:
    st.session_state.my_data['watchlist'] = []
    
if 'personal_finance' not in st.session_state.my_data:
    st.session_state.my_data['personal_finance'] = {"incomes": [], "expenses": []}

if 'pledge' not in st.session_state.my_data: 
    st.session_state.my_data['pledge'] = {"borrowed_amount": 0}

for etf in st.session_state.my_data['etfs']:
    if 'pledged_shares' not in etf: etf['pledged_shares'] = 0.0
    if 'is_pledged' not in etf: etf['is_pledged'] = False 
save_to_json(st.session_state.my_data)

# --- 🚀 Callback 函數區 ---
def auto_fill_etf_name():
    raw_sym = st.session_state.get('add_sym_bot', '')
    clean_sym = raw_sym.strip().upper().replace(".TW", "")
    if clean_sym: st.session_state.add_name_bot = ETF_NAME_DB.get(clean_sym, f"{clean_sym} ETF")
    else: st.session_state.add_name_bot = ""

def add_new_etf_bot():
    raw_sym = st.session_state.get('add_sym_bot', '')
    new_name = st.session_state.get('add_name_bot', '')
    new_h = st.session_state.get('add_h_bot', 0.0)
    new_c = st.session_state.get('add_c_bot', 0.0)

    clean_symbol = raw_sym.strip().upper().replace(".TW", "")
    if clean_symbol and new_name:
        final_symbol = f"{clean_symbol}.TW" 
        st.session_state.my_data['etfs'].append({
            "symbol": final_symbol, "name": new_name, "holdings": new_h, "cost": new_c, "alert_high": 0.0, "alert_low": 0.0, "pledged_shares": 0.0, "is_pledged": False
        })
        save_to_json(st.session_state.my_data)
        st.session_state.add_sym_bot = ""; st.session_state.add_name_bot = ""; st.session_state.add_h_bot = 0.0; st.session_state.add_c_bot = 0.0

def delete_etf(index):
    if 0 <= index < len(st.session_state.my_data['etfs']):
        st.session_state.my_data['etfs'].pop(index)
        save_to_json(st.session_state.my_data)

def save_edits():
    temp_list = []
    for i, item in enumerate(st.session_state.my_data['etfs']):
        h_val = st.session_state.get(f"edit_h_{i}", item['holdings'])
        c_val = st.session_state.get(f"edit_c_{i}", item['cost'])
        temp_list.append({
            "symbol": item['symbol'], "name": item['name'], "holdings": h_val, "cost": c_val,
            "alert_high": item.get('alert_high', 0.0), "alert_low": item.get('alert_low', 0.0), 
            "pledged_shares": item.get('pledged_shares', 0.0), "is_pledged": item.get('is_pledged', False)
        })
    st.session_state.my_data['etfs'] = temp_list
    save_to_json(st.session_state.my_data)

def auto_fill_wl_name():
    raw_sym = st.session_state.get('add_sym_wl', '')
    clean_sym = raw_sym.strip().upper().replace(".TW", "")
    if clean_sym: st.session_state.add_name_wl = ETF_NAME_DB.get(clean_sym, f"{clean_sym}")
    else: st.session_state.add_name_wl = ""

def add_new_wl():
    raw_sym = st.session_state.get('add_sym_wl', '')
    new_name = st.session_state.get('add_name_wl', '')
    clean_symbol = raw_sym.strip().upper().replace(".TW", "")
    if clean_symbol and new_name:
        final_symbol = f"{clean_symbol}.TW"
        if any(x['symbol'] == final_symbol for x in st.session_state.my_data['watchlist']):
            st.warning("該標的已在自選名單中！")
            return
        st.session_state.my_data['watchlist'].append({"symbol": final_symbol, "name": new_name})
        save_to_json(st.session_state.my_data)
        st.session_state.add_sym_wl = ""; st.session_state.add_name_wl = ""

def delete_wl(index):
    if 0 <= index < len(st.session_state.my_data['watchlist']):
        st.session_state.my_data['watchlist'].pop(index)
        save_to_json(st.session_state.my_data)

# 初始化按鈕狀態
if 'show_daily_price' not in st.session_state: st.session_state.show_daily_price = False 
if 'show_pledge' not in st.session_state: st.session_state.show_pledge = False 

def toggle_daily_price(): st.session_state.show_daily_price = not st.session_state.show_daily_price 
def toggle_pledge(): st.session_state.show_pledge = not st.session_state.show_pledge 

# --- 4. 核心數據計算 ---
@st.cache_data(ttl=10)
def fetch_stock_prices(etf_list):
    results = []
    total_today_pnl = 0
    price_alerts = []
    
    for item in etf_list:
        try:
            tk = yf.Ticker(item['symbol'])
            hist = tk.history(period="5d")
            
            curr_p = tk.fast_info.get('lastPrice', 0)
            if curr_p == 0 and not hist.empty:
                curr_p = hist['Close'].iloc[-1]
                
            prev_close = tk.fast_info.get('previousClose', 0)
            if prev_close == 0 and len(hist) >= 2:
                prev_close = hist['Close'].iloc[-2]
                
            shares = item['holdings'] * 1000
            mkt_val = shares * curr_p
            cost_val = shares * item['cost']
            profit = mkt_val - cost_val - (mkt_val * 0.00235)
            
            today_diff = curr_p - prev_close
            today_profit = shares * today_diff
            total_today_pnl += today_profit
            
            a_high = float(item.get('alert_high', 0.0))
            a_low = float(item.get('alert_low', 0.0))
            if a_high > 0 and curr_p >= a_high: price_alerts.append({"name": item['name'], "price": curr_p, "target": a_high, "type": "high"})
            if a_low > 0 and curr_p <= a_low: price_alerts.append({"name": item['name'], "price": curr_p, "target": a_low, "type": "low"})

            results.append({
                "代號": item['symbol'], "名稱": item['name'], "現價": curr_p, 
                "張數": item['holdings'], "均價": item['cost'], "市值": mkt_val, "損益": profit
            })
        except: continue
    return pd.DataFrame(results), total_today_pnl, price_alerts

df, g_today_pnl, price_alerts = fetch_stock_prices(st.session_state.my_data['etfs'])

# --- 5. 介面呈現 ---
st.title("📈 總司令實戰戰情室")
st.caption(f"最後更新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if price_alerts:
    for alert in price_alerts:
        if alert['type'] == "high":
            st.markdown(f"<div class='alert-high'>🚨 突破停利高標：【{alert['name']}】 現價 ${alert['price']:.2f} 已突破您設定的 ${alert['target']}！</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='alert-low'>⚠️ 跌破停損低標：【{alert['name']}】 現價 ${alert['price']:.2f} 已跌破您設定的 ${alert['target']}！</div>", unsafe_allow_html=True)

# 頂部儀表板
if not df.empty:
    c1, c2, c3 = st.columns(3)
    c1.metric("股票總市值", f"${df['市值'].sum():,.0f}")
    c2.metric("累積預估淨損益", f"${df['損益'].sum():,.0f}")
    today_pnl_str = f"+${g_today_pnl:,.0f}" if g_today_pnl >= 0 else f"-${abs(g_today_pnl):,.0f}"
    c3.metric("今日單日總損益", today_pnl_str, delta=today_pnl_str, delta_color="normal")

st.write("---")

cols_btn_r4 = st.columns(3)
b8_lbl, b8_typ = ("🔽 收起質押專區", "primary") if st.session_state.show_pledge else ("🏦 展開質押專區", "secondary") 
b10_lbl, b10_typ = ("🔽 收起每日單日損益", "primary") if st.session_state.show_daily_price else ("🗓️ 展開每日單日損益", "secondary") 

with cols_btn_r4[0]: st.button(b8_lbl, on_click=toggle_pledge, type=b8_typ, use_container_width=True) 
with cols_btn_r4[1]: st.button(b10_lbl, on_click=toggle_daily_price, type=b10_typ, use_container_width=True) 
st.write("---")

# 股價監控與自動更新設定
t_col, refresh_col = st.columns([8, 2])
with t_col:
    st.markdown("#### 📡 庫存持股明細")
    if not df.empty:
        st.dataframe(df.style.format({"現價":"{:.2f}", "均價":"{:.2f}", "市值":"{:,.0f}", "損益":"{:,.0f}"}), use_container_width=True, hide_index=True)
    else:
        st.info("目前無庫存標的。")

with refresh_col:
    st.markdown("<div style='background-color:#f0f7ff; padding:10px; border-radius:5px; text-align: center;'>", unsafe_allow_html=True)
    st.write("⚡ **股價自動更新**")
    sec = st.number_input("更新頻率(秒)", min_value=3, max_value=600, value=st.session_state.get('auto_refresh_sec', 5), key="auto_refresh_sec", label_visibility="collapsed")
    st.markdown(f"<div style='font-size: 11px; color: #6c757d; margin-bottom: 5px;'>每 {sec} 秒重整</div>", unsafe_allow_html=True)
    
    if 'auto_refresh_mode' not in st.session_state:
        st.session_state.auto_refresh_mode = "❌ 關閉"
        
    auto_update = st.radio(
        "即時更新", 
        ["❌ 關閉", "✅ 開啟"], 
        key="auto_refresh_mode",
        horizontal=False,
        label_visibility="collapsed"
    )
    st.markdown("</div>", unsafe_allow_html=True)

st.write("---")

# ==============================================================================
# 🔥 [重磅升級] 🗓️ 近一個月 庫存與自選 ETF 每日收盤價 + 每日損益
# ==============================================================================
if st.session_state.show_daily_price:
    st.markdown("#### 🗓️ 庫存 ETF 近一個月單日損益金額")
    port_map = {}
    wl_map = {}
    port_holdings = {}
    
    for item in st.session_state.my_data.get('etfs', []):
        port_map[item['symbol']] = f"💼 {item['name']}"
        port_holdings[f"💼 {item['name']}"] = item['holdings'] * 1000
        
    for item in st.session_state.my_data.get('watchlist', []):
        if item['symbol'] not in port_map:
            wl_map[item['symbol']] = f"👀 {item['name']}"
            
    all_symbols_map = {**port_map, **wl_map}
    current_symbols = list(all_symbols_map.keys())
    
    if current_symbols:
        with st.spinner("📡 正在向資料庫調閱近一個月每日股價與計算損益..."):
            try:
                # 抓取近 1 個月數據
                hist_data = yf.download(current_symbols, period="1mo")['Close']
                
                if len(current_symbols) == 1:
                    hist_data = hist_data.to_frame()
                    hist_data.columns = [all_symbols_map[current_symbols[0]]]
                else:
                    hist_data = hist_data.rename(columns=all_symbols_map)
                
                # 計算單日漲跌差額
                diff_data = hist_data.diff()
                
                # 轉換日期格式並反轉順序
                hist_data.index = hist_data.index.strftime('%m/%d')
                diff_data.index = hist_data.index 
                
                hist_data = hist_data.iloc[::-1]
                diff_data = diff_data.iloc[::-1]
                
                hist_data = hist_data.T
                diff_data = diff_data.T
                
                valid_port_names = [name for name in port_map.values() if name in hist_data.index]
                valid_wl_names = [name for name in wl_map.values() if name in hist_data.index]
                
                def color_prices(df_to_style):
                    css_df = pd.DataFrame('', index=df_to_style.index, columns=df_to_style.columns)
                    target_diff = diff_data.loc[df_to_style.index] 
                    css_df[target_diff > 0] = 'color: #d32f2f; font-weight: bold;'
                    css_df[target_diff < 0] = 'color: #388e3c; font-weight: bold;'
                    return css_df
                
                # 🔥 繪製庫存專屬表格 (僅顯示單日損益金額)
                if valid_port_names:
                    st.markdown("##### 💼 庫存 ETF (單日賺賠金額)")
                    display_port = pd.DataFrame(index=valid_port_names, columns=hist_data.columns)
                    
                    for etf_name in valid_port_names:
                        shares = port_holdings.get(etf_name, 0)
                        for date_col in hist_data.columns:
                            diff = diff_data.loc[etf_name, date_col]
                            
                            if pd.isna(diff) or shares == 0:
                                display_port.loc[etf_name, date_col] = "-"
                            else:
                                # 只顯示 PnL 金額
                                pnl = diff * shares
                                sign = "+" if pnl > 0 else ""
                                display_port.loc[etf_name, date_col] = f"{sign}{pnl:,.0f}"
                                    
                    styled_port = display_port.style.apply(color_prices, axis=None)
                    st.dataframe(styled_port, use_container_width=True)
                
                # 自選股還是保持純價格
                if valid_wl_names:
                    st.markdown("##### 👀 自選 ETF (僅收盤價)")
                    display_wl = hist_data.loc[valid_wl_names].copy()
                    for col in display_wl.columns:
                        display_wl[col] = display_wl[col].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "-")
                        
                    styled_wl = display_wl.style.apply(color_prices, axis=None)
                    st.dataframe(styled_wl, use_container_width=True)
                    
                st.caption("💡 提示：顯示近 1 個月交易日數據。庫存 ETF 顯示為「該日真實損益金額」。數值呈現紅色代表賺錢，綠色代表虧損。")
            except Exception as e:
                st.error(f"無法抓取每日股價：{e}")
    else:
        st.info("⚠️ 目前尚無持股或自選資料，請至下方「標的管理」新增！")
    st.write("---")

# ==============================================================================
# 🔥 股票質押專區
# ==============================================================================
if st.session_state.show_pledge:
    if not df.empty:
        st.markdown("#### 🏦 股票質押專區 (維持率監控)")
        st.info("💡 股票質押後會從一般券商庫存消失。一般券商最高可借出擔保品市值的 60%。請先「打勾選取」欲質押標的，再輸入已借款項！")
        
        pledge_data = st.session_state.my_data['pledge']
        borrowed = st.number_input("💸 輸入已向券商借入款項總額 (元)", min_value=0, value=int(pledge_data.get('borrowed_amount', 0)), step=10000)
        
        if borrowed != pledge_data.get('borrowed_amount', 0):
            st.session_state.my_data['pledge']['borrowed_amount'] = borrowed
            save_to_json(st.session_state.my_data)
            st.rerun()

        pledge_df_list = []
        total_pledge_mkt = 0
        total_borrowable = 0
        for item in st.session_state.my_data['etfs']:
            sym = item['symbol']
            name = item['name']
            h_total = item['holdings']
            p_shares = item.get('pledged_shares', 0.0)
            is_pledged = item.get('is_pledged', False)
            
            try:
                curr_p = df[df['代號'] == sym]['現價'].values[0]
            except:
                curr_p = 0
                
            original_mkt = h_total * 1000 * curr_p
            p_mkt = p_shares * 1000 * curr_p if is_pledged else 0
            p_limit = p_mkt * 0.6 if is_pledged else 0
            total_pledge_mkt += p_mkt
            total_borrowable += p_limit
            
            pledge_df_list.append({
                "✓ 選取": is_pledged,
                "ETF 名稱": name,
                "總庫存 (張)": h_total,
                "庫存市值 (元)": round(original_mkt, 0),
                "質押張數": p_shares,
                "現價": round(curr_p, 2),
                "質押市值 (元)": round(p_mkt, 0),
                "可借上限 (60%)": round(p_limit, 0) 
            })
            
        pledge_df = pd.DataFrame(pledge_df_list)
        margin_ratio = (total_pledge_mkt / borrowed * 100) if borrowed > 0 else 0
        
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("擔保品總市值", f"${total_pledge_mkt:,.0f}")
        col_m2.metric("🎯 總可借款上限 (60%)", f"${total_borrowable:,.0f}")
        col_m3.metric("💸 已借入總額", f"${borrowed:,.0f}")
        
        if borrowed > 0:
            if margin_ratio < 130:
                col_m4.metric("🚨 目前維持率", f"{margin_ratio:.2f}%", "危險：低於 130% 將面臨斷頭", delta_color="inverse")
            elif margin_ratio < 160:
                col_m4.metric("⚠️ 目前維持率", f"{margin_ratio:.2f}%", "注意：市場波動可能導致風險", delta_color="off")
            else:
                col_m4.metric("✅ 目前維持率", f"{margin_ratio:.2f}%", "安全：維持率處於健康水平", delta_color="normal")
        else:
            col_m4.metric("目前維持率", "0.00%")

        st.write("👇 **請勾選欲質押的標的，並雙擊「質押張數」欄位設定數量：**")
        edited_pledge = st.data_editor(
            pledge_df,
            column_config={
                "✓ 選取": st.column_config.CheckboxColumn("✓ 選取質押", help="勾選後才會計入擔保品總市值"),
                "質押張數": st.column_config.NumberColumn("質押張數 (雙擊編輯)", min_value=0.0, step=1.0, format="%.1f"),
                "庫存市值 (元)": st.column_config.NumberColumn("庫存市值 (元)", format="%.0f"),
                "現價": st.column_config.NumberColumn("現價", format="%.2f"),
                "質押市值 (元)": st.column_config.NumberColumn("質押市值 (元)", format="%.0f"),
                "可借上限 (60%)": st.column_config.NumberColumn("可借上限 (60%)", format="%.0f") 
            },
            disabled=["ETF 名稱", "總庫存 (張)", "庫存市值 (元)", "現價", "質押市值 (元)", "可借上限 (60%)"], 
            use_container_width=True, hide_index=True
        )
        
        has_p_changes = False
        for _, row in edited_pledge.iterrows():
            p_name = row['ETF 名稱']
            new_is_pledged = row['✓ 選取']
            new_p_shares = row['質押張數']
            
            for etf in st.session_state.my_data['etfs']:
                if etf['name'] == p_name:
                    if new_p_shares > etf['holdings']:
                        new_p_shares = etf['holdings']
                        
                    if etf.get('pledged_shares', 0.0) != new_p_shares or etf.get('is_pledged', False) != new_is_pledged:
                        etf['pledged_shares'] = new_p_shares
                        etf['is_pledged'] = new_is_pledged
                        has_p_changes = True
                    break
        if has_p_changes:
            save_to_json(st.session_state.my_data)
            st.rerun()
    else:
        st.info("⚠️ 目前尚無持股資料，無法進行質押計算。")
    st.write("---")

bot_c1, bot_c2, bot_c3 = st.columns([2, 2, 6])

with bot_c1:
    if st.button("🔄 手動更新【股價】", use_container_width=True):
        fetch_stock_prices.clear() 
        st.rerun()

with bot_c3:
    with st.expander("⚙️ 標的管理 (庫存新增 / 修改 / 刪除)", expanded=True):
        st.markdown("#### ➕ 新增庫存標的 (股票/ETF)")
        
        if "add_name_bot" not in st.session_state: st.session_state.add_name_bot = ""
        if "add_sym_bot" not in st.session_state: st.session_state.add_sym_bot = ""
        if "add_h_bot" not in st.session_state: st.session_state.add_h_bot = 0.0
        if "add_c_bot" not in st.session_state: st.session_state.add_c_bot = 0.0

        st.text_input("輸入代碼 (不需手打 .TW)", placeholder="例如: 00878 或 00981A", key="add_sym_bot", on_change=auto_fill_etf_name)
        st.text_input("自定義名稱", placeholder="例如: 00878 國泰永續高股息", key="add_name_bot")
        
        col_add1, col_add2 = st.columns(2)
        with col_add1:
            st.number_input("張數", step=1.0, key="add_h_bot")
        with col_add2:
            st.number_input("均價", step=0.1, key="add_c_bot")
        
        st.button("確認新增庫存", key="btn_add_bot", use_container_width=True, on_click=add_new_etf_bot)

        if st.session_state.my_data['etfs']:
            st.write("---")
            st.markdown("#### 📝 庫存修改與刪除")
            
            for i, item in enumerate(st.session_state.my_data['etfs']):
                with st.expander(f"📍 {item['name']}"):
                    col_e1, col_e2 = st.columns(2)
                    with col_e1:
                        st.number_input("張數", value=float(item['holdings']), step=1.0, key=f"edit_h_{i}")
                    with col_e2:
                        st.number_input("均價", value=float(item['cost']), step=0.1, key=f"edit_c_{i}")

                    st.button(f"🗑️ 刪除 {item['name']}", key=f"del_{i}", on_click=delete_etf, args=(i,), use_container_width=True)

            st.button("💾 儲存所有修改", use_container_width=True, type="primary", on_click=save_edits)

# 自動更新綁定
if st.session_state.get('auto_refresh_mode') == "✅ 開啟":
    time.sleep(st.session_state.get("auto_refresh_sec", 5))
    fetch_stock_prices.clear() 
    st.rerun()
