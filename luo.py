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
import twstock  # 🔥 匯入 twstock 套件

# --- 1. 網頁基礎設定 ---
st.set_page_config(page_title="ETF 投資戰情室", layout="wide")

import socket
import qrcode
from PIL import Image
import io

# --- 手機掃碼連線功能 ---
# 建立側邊欄區塊來放 QR Code
st.sidebar.markdown("---")
st.sidebar.markdown("### 📱 手機掃碼即時看")

# 使用 Streamlit Cloud 的固定網址
app_url = "https://my-etf-wind.streamlit.app/"

qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=5,
    border=2,
)
qr.add_data(app_url)
qr.make(fit=True)
img = qr.make_image(fill_color="black", back_color="white")

# 將圖片暫存在記憶體並轉成 PNG 位元組格式，避免 Streamlit Cloud 報錯
buf = io.BytesIO()
img.save(buf, format="PNG")
byte_im = buf.getvalue()

# 顯示在側邊欄
st.sidebar.image(byte_im, caption="請確保手機與電腦連線至同一 Wi-Fi")
# ------------------------

# 全局提示訊息狀態
if 'update_success' in st.session_state and st.session_state.update_success:
    st.toast(st.session_state.update_success, icon="✅")
    st.session_state.update_success = False

# 自定義 CSS (保留您原本的樣式)
st.markdown("""
    <style>
    [data-testid="stElementToolbar"], [data-testid="stDataFrameToolbar"], [data-testid="stToolbar"], .stDataFrame [data-testid="stElementToolbar"] { display: none !important; opacity: 0 !important; visibility: hidden !important; pointer-events: none !important; }
    [data-testid="stMetricDelta"] svg { fill: red; }
    [data-testid="stMetric"] { background-color: var(--secondary-background-color); padding: 12px; border-radius: 10px; box-shadow: 1px 1px 4px rgba(0,0,0,0.05); }
    .news-box { background-color: #f0f7ff; border-left: 6px solid #4a90e2; padding: 20px; border-radius: 8px; margin-bottom: 25px; box-shadow: 1px 1px 4px rgba(0,0,0,0.05); }
    .news-title { font-size: 20px; font-weight: bold; color: #1e3c72; margin-bottom: 15px; display: flex; align-items: center; }
    .news-item { font-size: 16px; color: #333; margin-bottom: 12px; line-height: 1.5; font-weight: 500;}
    .news-item a { text-decoration: none; color: #1e3c72; transition: color 0.2s;}
    .news-item a:hover { text-decoration: underline; color: #d32f2f; }
    .ex-div-box, .pay-div-box { border-radius: 8px; padding: 10px; text-align: center; margin-bottom: 15px; height: 115px; display: flex; flex-direction: column; justify-content: center; box-shadow: 1px 1px 3px rgba(0,0,0,0.05); overflow-y: auto;}
    .ex-div-box { background-color: #ffeaea; border: 1.5px solid #e06666; }
    .pay-div-box { background-color: #fff2cc; border: 1.5px solid #f6b26b; }
    .ex-div-title { color: #cc0000; font-weight: bold; font-size: 13px; margin-bottom: 4px; }
    .ex-div-text, .pay-div-text { color: #783f04; font-size: 12px; font-weight: bold; line-height: 1.4; }
    .pay-div-title { color: #b45f06; font-weight: bold; font-size: 13px; margin-bottom: 4px; }
    .triple-box { background-color: #ffffff; border-radius: 12px; border: 1px solid #e0e0e0; padding: 15px; display: flex; flex-wrap: wrap; justify-content: space-around; align-items: center; margin-bottom: 20px; box-shadow: 2px 2px 8px rgba(0,0,0,0.04); gap: 10px; }
    .triple-col { flex: 1 1 30%; min-width: 140px; text-align: center; padding: 10px 0; }
    .triple-title { font-size: 14px; color: #757575; font-weight: bold; margin-bottom: 5px; }
    .triple-val-r { font-size: 28px; font-weight: 900; color: #b71c1c; font-family: Arial, sans-serif; line-height: 1.1; }
    .triple-val-g { font-size: 28px; font-weight: 900; color: #2e7d32; font-family: Arial, sans-serif; line-height: 1.1; }
    .triple-val-gold { font-size: 28px; font-weight: 900; color: #f39c12; font-family: Arial, sans-serif; line-height: 1.1; text-shadow: 1px 1px 2px rgba(243, 156, 18, 0.3); }
    .triple-pct-r { font-size: 14px; font-weight: bold; color: #b71c1c; margin-top: 5px; }
    .triple-pct-g { font-size: 14px; font-weight: bold; color: #2e7d32; margin-top: 5px; }
    .triple-sub-gold { font-size: 12px; font-weight: bold; color: #7f8c8d; margin-top: 5px; }
    @keyframes lightning-strike { 0% { box-shadow: 0 0 10px rgba(241, 196, 15, 0.5); background-color: #fffdf5; border-color: #f1c40f; transform: scale(1); } 50% { box-shadow: 0 0 40px rgba(255, 235, 59, 1), inset 0 0 25px rgba(255, 235, 59, 0.9); background-color: #ffffe0; border-color: #ffeb3b; transform: scale(1.03); } 100% { box-shadow: 0 0 10px rgba(241, 196, 15, 0.5); background-color: #fffdf5; border-color: #f1c40f; transform: scale(1); } }
    .flash-gold-box { background-color: #fffdf5; border-radius: 12px; padding: 15px; border: 2px solid #f1c40f; animation: lightning-strike 0.1s infinite; }
    .alert-high { background-color: #ffebee; border: 2px solid #ef5350; border-left: 8px solid #d32f2f; padding: 15px; border-radius: 8px; margin-bottom: 15px; color: #b71c1c; font-size: 16px; font-weight: bold; }
    .alert-low { background-color: #e8f5e9; border: 2px solid #66bb6a; border-left: 8px solid #388e3c; padding: 15px; border-radius: 8px; margin-bottom: 15px; color: #1b5e20; font-size: 16px; font-weight: bold; }
    .month-card { background-color: #e9ecef; padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 10px; border: 1px solid #ced4da; }
    .month-title { font-size: 20px; font-weight: bold; color: #495057; }
    .month-amount { font-size: 28px; font-weight: bold; color: #d9534f; margin: 10px 0; }
    .month-sources { font-size: 14px; color: #6c757d; }
    div.stButton > button { font-weight: bold; border-radius: 8px; }
    .upcoming-box { background-color: #fff4e6; border: 1px solid #ffd8a8; border-radius: 8px; padding: 8px 10px; text-align: center; margin-bottom: 15px; box-shadow: 1px 1px 3px rgba(0,0,0,0.05); }
    .upcoming-title { color: #d9480f; font-weight: bold; font-size: 13px; margin-bottom: 4px; }
    .upcoming-item { color: #862e01; font-size: 13px; font-weight: bold; margin-bottom: 2px; }
    .upcoming-price { font-size: 11px; color: #888; }
    .calc-box { background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; padding: 15px; margin-bottom: 15px;}
    .calc-title { color: #495057; font-weight: bold; font-size: 16px; margin-bottom: 10px; }
    .calc-result-profit { font-size: 24px; font-weight: bold; color: #d32f2f; margin-top: 10px;}
    .calc-result-loss { font-size: 24px; font-weight: bold; color: #388e3c; margin-top: 10px;}
    .calc-result-info { font-size: 14px; color: #6c757d; margin-top: 5px;}
    .secret-box { padding: 25px; border: 2px dashed #dc3545; border-radius: 12px; background-color: #fffafb; margin-bottom: 15px; box-shadow: 2px 2px 8px rgba(0,0,0,0.05); }
    .net-worth-box { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; margin-top: 15px; box-shadow: 2px 2px 10px rgba(0,0,0,0.2); }
    .net-worth-box h3 { color: #f8f9fa; font-size: 18px; margin-bottom: 5px; }
    .net-worth-box h1 { color: #ffc107; font-size: 38px; font-weight: 900; margin: 0; text-shadow: 1px 1px 3px rgba(0,0,0,0.5); }
    .auto-refresh-box { background-color: #f0f7ff; border: 1px solid #cce5ff; border-radius: 8px; padding: 15px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 系統設定與資料庫 ---
SETTINGS_FILE = 'settings.json'

def load_settings():
    default_data = {
        "etfs": [], "pledge": {"borrowed_amount": 0, "months_passed": 1, "total_months": 18},
        "watchlist": [], "custom_divs": {}, "personal_finance": {"incomes": [], "expenses": []}
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
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4, ensure_ascii=False)

if 'my_data' not in st.session_state: st.session_state.my_data = load_settings()

def color_profit_loss(val):
    if isinstance(val, str):
        if val.startswith('+'): return 'color: #d32f2f; font-weight: bold;' 
        elif val.startswith('-'): return 'color: #388e3c; font-weight: bold;' 
    return ''
def color_diff(val):
    if isinstance(val, str) and '%' in val: return 'color: #d32f2f; font-weight: bold;' if val.startswith('+') else 'color: #388e3c; font-weight: bold;' if val.startswith('-') else ''
    return ''

ui_toggles = ['show_tech']
for t in ui_toggles:
    if t not in st.session_state: st.session_state[t] = False
def toggle_tech(): st.session_state.show_tech = not st.session_state.show_tech

# --- 4. 核心數據獲取函數 (twstock 整合版) ---

@st.cache_data(ttl=15)
def fetch_watchlist_data(wl_list):
    if not wl_list: return pd.DataFrame()
    results = []
    for item in wl_list:
        try:
            symbol_code = item['symbol'].replace('.TW', '').replace('.TWO', '')
            use_yahoo = True
            curr_p, prev_close = 0, 0
            
            # 🔥 優先使用 twstock
            try:
                if symbol_code.isdigit() or symbol_code.isalnum():
                    tw_data = twstock.realtime.get(symbol_code)
                    if tw_data and tw_data.get('success'):
                        rt = tw_data['realtime']
                        curr_p = float(rt['latest_trade_price']) if rt['latest_trade_price'] != '-' else (float(rt['best_bid_price'][0]) if rt['best_bid_price'] else 0)
                        prev_close = float(tw_data['info']['y_close'])
                        use_yahoo = False
            except Exception:
                use_yahoo = True
            
            # 🛡️ 備用 Yahoo 通道
            if use_yahoo:
                tk = yf.Ticker(item['symbol'])
                hist = tk.history(period="2d")
                if hist.empty: continue
                curr_p = tk.fast_info.get('lastPrice') or hist['Close'].iloc[-1]
                prev_close = tk.fast_info.get('previousClose') or (hist['Close'].iloc[-2] if len(hist) >= 2 else curr_p)
                
            diff = curr_p - prev_close
            pct = (diff / prev_close * 100) if prev_close else 0
            results.append({"代號": symbol_code, "名稱": item['name'], "現價": round(curr_p, 2), "漲跌": round(diff, 2), "漲跌幅": f"{pct:+.2f}%", "狀態": "🔴" if diff > 0 else "🟢" if diff < 0 else "⚪"})
        except: continue
    return pd.DataFrame(results)


@st.cache_data(ttl=15)
def fetch_data(etf_list, custom_divs):
    if not etf_list: return pd.DataFrame(), pd.DataFrame(), 0, 0, 0, 0, [], [], [], {i: {"amount": 0, "sources": []} for i in range(1, 13)}
    results, tech_results = [], []
    total_mkt, total_cost, total_div, total_today_pnl = 0, 0, 0, 0
    radar_ex, radar_pay, price_alerts = [], [], []
    monthly_calendar = {i: {"amount": 0, "sources": []} for i in range(1, 13)} 

    for item in etf_list:
        try:
            symbol_code = item['symbol'].replace('.TW', '').replace('.TWO', '')
            use_yahoo = True
            curr_p, prev_close, day_high, day_low, vol = 0, 0, 0, 0, 0
            
            # 🔥 主力雷達：twstock 即時報價
            try:
                if symbol_code.isdigit() or symbol_code.isalnum():
                    tw_data = twstock.realtime.get(symbol_code)
                    if tw_data and tw_data.get('success'):
                        rt = tw_data['realtime']
                        curr_p = float(rt['latest_trade_price']) if rt['latest_trade_price'] != '-' else (float(rt['best_bid_price'][0]) if rt['best_bid_price'] else 0)
                        prev_close = float(tw_data['info']['y_close'])
                        day_high = float(rt['high']) if rt['high'] != '-' else curr_p
                        day_low = float(rt['low']) if rt['low'] != '-' else curr_p
                        vol = int(rt['accumulate_trade_volume'])
                        use_yahoo = False
            except Exception:
                use_yahoo = True

            # 🛡️ 備用雷達：Yahoo Finance
            if use_yahoo:
                tk = yf.Ticker(item['symbol'])
                hist = tk.history(period='5d') 
                if hist.empty: continue
                curr_p = tk.fast_info.get('lastPrice') or hist['Close'].iloc[-1]
                prev_close = tk.fast_info.get('previousClose') or (hist['Close'].iloc[-2] if len(hist) >= 2 else curr_p)
                day_high = tk.fast_info.get('dayHigh') or hist['High'].iloc[-1]
                day_low = tk.fast_info.get('dayLow') or hist['Low'].iloc[-1]
                vol = tk.fast_info.get('lastVolume') or hist['Volume'].iloc[-1]
            
            shares = item['holdings'] * 1000
            mkt_val = shares * curr_p
            cost_val = shares * item['cost']
            profit = mkt_val - cost_val - (mkt_val * 0.00235)
            today_diff = curr_p - prev_close
            today_profit = shares * today_diff
            total_today_pnl += today_profit
            total_mkt += mkt_val; total_cost += cost_val

            div_amount, ex_date, pay_date, fill_status, status_msg = 0, "待官方公告", "待官方公告", "-", "⏳ 依前次估算"
            is_announced, cap_raw = False, 0
            months_to_pay = []

            results.append({
                "代號": item['symbol'], "名稱": item['name'], "現價": curr_p, "均價": item['cost'],
                "張數": item['holdings'], "市值": mkt_val, "損益": profit, "報酬率": (profit / cost_val * 100) if cost_val != 0 else 0,
                "單次預估領息": shares * div_amount, "每股配息": div_amount,
                "最新公告除息日": ex_date, "預估發放日": pay_date, "已公告": is_announced,
                "狀態": status_msg, "最新填息紀錄": fill_status, "基金規模": f"{cap_raw / 100000000:.2f} 億" if cap_raw else "無資料"
            })
            
            tech_results.append({
                "ETF 名稱": f"{'🔴' if curr_p > prev_close else '🟢' if curr_p < prev_close else '⚪'} {item['name']}", 
                "配息月份": "月配息" if len(months_to_pay) == 12 else ",".join(map(str, months_to_pay)) + "月" if months_to_pay else "-", 
                "股票張數": item['holdings'], "現價": round(curr_p, 2), "基金規模(市值)": f"{cap_raw / 100000000:.2f} 億" if cap_raw else "無資料",
                "今日損益": f"+${today_profit:,.0f}" if today_profit >= 0 else f"-${abs(today_profit):,.0f}", 
                "今日漲跌幅": f"+{(today_diff / prev_close * 100):.2f}%" if today_diff >= 0 else f"{(today_diff / prev_close * 100):.2f}%", 
                "今日交易量": f"{vol:,.0f}" if vol > 0 else "無資料",
                "年殖利率": f"{(div_amount * len(months_to_pay)) / curr_p * 100:.2f}%" if len(months_to_pay) > 0 and div_amount > 0 and curr_p > 0 else "0.00%", 
                "今日最高/最低": f"${day_high:.2f} / ${day_low:.2f}"
            })
        except: continue
        
    return pd.DataFrame(results), pd.DataFrame(tech_results), total_mkt, total_cost, total_div, total_today_pnl, radar_ex, radar_pay, price_alerts, monthly_calendar

df, df_tech, g_mkt, g_cost, g_div, g_today_pnl, radar_ex, radar_pay, price_alerts, monthly_calendar = fetch_data(st.session_state.my_data['etfs'], st.session_state.my_data.get('custom_divs', {}))

# --- 5. 介面呈現 ---
st.title("📈 實戰資產戰情室 (twstock + Yahoo 雙備援)")
st.caption(f"最後更新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (若台灣證交所連線超時，系統將自動切換回 Yahoo 報價)")

r2 = st.columns(3)
r2[1].button("🔽 收控股價監控" if st.session_state.show_tech else "📡 展開股價監控", on_click=toggle_tech, type="primary" if st.session_state.show_tech else "secondary", use_container_width=True)

if st.session_state.show_tech:
    if not df.empty:
        st.markdown("#### 📡 庫存價格區間監控與技術分析")
        try: styled_df_tech = df_tech.style.map(color_profit_loss, subset=['今日損益', '今日漲跌幅'])
        except: styled_df_tech = df_tech.style.applymap(color_profit_loss, subset=['今日損益', '今日漲跌幅'])
        st.dataframe(styled_df_tech, use_container_width=True, hide_index=True)

    st.markdown("#### 👀 自選股觀察清單")
    wl_df = fetch_watchlist_data(st.session_state.my_data.get('watchlist', []))
    if not wl_df.empty:
        try: styled_wl = wl_df.style.map(color_diff, subset=['漲跌', '漲跌幅'])
        except: styled_wl = wl_df.style.applymap(color_diff, subset=['漲跌', '漲跌幅'])
        st.dataframe(styled_wl, use_container_width=True, hide_index=True)

st.write("---")
bot_c1, bot_c2, bot_c3 = st.columns([2, 5, 3])
if bot_c1.button("🔄 強制重整即時股價", use_container_width=True): st.cache_data.clear(); st.rerun()

with bot_c3:
    st.markdown("<div class='auto-refresh-box'>#### ⚡ 自動更新<br><span style='font-size:12px;color:red;'>⚠️ 使用 twstock 容易被證交所封鎖 IP，自動更新已放寬至 15 秒</span></div>", unsafe_allow_html=True)
    if st.radio("即時更新", ["❌ 關閉", "✅ 開啟"], horizontal=True, label_visibility="collapsed") == "✅ 開啟":
        time.sleep(15); st.cache_data.clear(); st.rerun()
