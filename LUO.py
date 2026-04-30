import streamlit as st
import yfinance as yf
import pandas as pd
import json
import os
from datetime import datetime

# --- 1. 網頁基礎設定 ---
st.set_page_config(page_title="ETF 投資戰情室", layout="wide")

# 自定義 CSS：確保紅漲綠跌符合台灣習慣 (漲=紅, 跌=綠)
st.markdown("""
    <style>
    [data-testid="stMetricDelta"] svg { fill: red; }
    .stMetric { background-color: #f8f9fa; padding: 10px; border-radius: 10px; }
    .red-text { color: #ff4b4b; font-weight: bold; }
    .green-text { color: #008000; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. JSON 檔案讀寫邏輯 ---
SETTINGS_FILE = 'settings.json'

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    # 預設初始資料
    return {
        "etfs": [
            {"symbol": "0050.TW", "name": "元大台灣50", "holdings": 2.0, "cost": 90.58},
            {"symbol": "0056.TW", "name": "元大高股息", "holdings": 25.0, "cost": 38.77},
            {"symbol": "00631L.TW", "name": "元大台灣50正2", "holdings": 13.0, "cost": 27.25},
            {"symbol": "00878.TW", "name": "國泰永續高股息", "holdings": 13.0, "cost": 23.07},
            {"symbol": "00919.TW", "name": "群益台灣精選高息", "holdings": 12.0, "cost": 22.73},
            {"symbol": "00927.TW", "name": "群益半導體收益", "holdings": 20.0, "cost": 28.65},
            {"symbol": "00493U.TW", "name": "統一台股增長", "holdings": 12.0, "cost": 27.77}
        ]
    }

def save_to_json(data):
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# 初始化 Session State
if 'my_data' not in st.session_state:
    st.session_state.my_data = load_settings()

# --- 3. 側邊欄：管理功能 (新增/修改/刪除) ---
st.sidebar.header("🚀 投資組合管理")

# A. 新增標的
with st.sidebar.expander("➕ 新增標的 (股票/ETF)", expanded=False):
    new_symbol = st.text_input("代碼 (需加 .TW)", placeholder="例如: 2330.TW")
    new_name = st.text_input("自定義名稱", placeholder="例如: 台積電")
    new_h = st.number_input("張數", value=0.0, step=1.0, key="add_h")
    new_c = st.number_input("均價", value=0.0, step=0.1, key="add_c")
    if st.button("確認新增"):
        if new_symbol and new_name:
            st.session_state.my_data['etfs'].append({
                "symbol": new_symbol.upper(), "name": new_name, 
                "holdings": new_h, "cost": new_c
            })
            save_to_json(st.session_state.my_data)
            st.rerun()

st.sidebar.write("---")

# B. 編輯與刪除
st.sidebar.subheader("📝 修改與刪除")
temp_list = []
to_delete = -1

for i, item in enumerate(st.session_state.my_data['etfs']):
    with st.sidebar.expander(f"📍 {item['name']}"):
        edit_h = st.number_input(f"張數", value=float(item['holdings']), key=f"h_{i}")
        edit_c = st.number_input(f"均價", value=float(item['cost']), key=f"c_{i}")
        temp_list.append({
            "symbol": item['symbol'], "name": item['name'], 
            "holdings": edit_h, "cost": edit_c
        })
        if st.button(f"🗑️ 刪除標的", key=f"del_{i}"):
            to_delete = i

if to_delete != -1:
    st.session_state.my_data['etfs'].pop(to_delete)
    save_to_json(st.session_state.my_data)
    st.rerun()

if st.sidebar.button("💾 儲存所有修改"):
    st.session_state.my_data['etfs'] = temp_list
    save_to_json(st.session_state.my_data)
    st.sidebar.success("已存檔！")
    st.rerun()

# --- 4. 核心數據計算 ---
@st.cache_data(ttl=300)
def fetch_data(etf_list):
    if not etf_list: return pd.DataFrame(), 0, 0, 0
    results = []
    total_mkt, total_cost, total_div = 0, 0, 0
    for item in etf_list:
        try:
            tk = yf.Ticker(item['symbol'])
            hist = tk.history(period='2d')
            if hist.empty: continue
            curr_p = hist['Close'].iloc[-1]
            shares = item['holdings'] * 1000
            mkt_val, cost_val = shares * curr_p, shares * item['cost']
            profit = mkt_val - cost_val
            roi = (profit / cost_val * 100) if cost_val != 0 else 0
            
            # 抓取配息與除息日
            actions = tk.actions
            div_amount, ex_date = 0, "待公告"
            if not actions.empty:
                latest = actions.sort_index(ascending=False).head(1)
                div_amount = latest['Dividends'].values[0]
                ex_date = latest.index[0].strftime('%Y-%m-%d')
            
            total_mkt += mkt_val
            total_cost += cost_val
            total_div += (shares * div_amount)
            results.append({
                "名稱": item['name'], "現價": curr_p, "均價": item['cost'],
                "張數": item['holdings'], "市值": mkt_val, "損益": profit,
                "報酬率": roi, "預估領息": shares * div_amount, "除息日": ex_date
            })
        except: continue
    return pd.DataFrame(results), total_mkt, total_cost, total_div

df, g_mkt, g_cost, g_div = fetch_data(st.session_state.my_data['etfs'])

# --- 5. 介面呈現 ---
st.title("📈 實戰資產戰情室")
st.caption(f"最後更新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if not df.empty:
    # 總覽指標
    c1, c2, c3 = st.columns(3)
    c1.metric("股票總市值", f"${g_mkt:,.0f}")
    p_total = g_mkt - g_cost
    r_total = (p_total / g_cost * 100) if g_cost != 0 else 0
    c2.metric("總報酬 (未實現)", f"${p_total:,.0f}", f"{r_total:+.2f}%")
    c3.metric("預計領息總額", f"${g_div:,.0f}")

    st.write("---")
    
    # 標的明細卡片
    for _, row in df.iterrows():
        # 判斷顏色 (紅漲綠跌)
        p_color = "red" if row['損益'] >= 0 else "green"
        roi_str = f"{row['報酬率']:+.2f}%"
        
        with st.expander(f"💎 {row['名稱']} | 報酬: :{p_color}[{roi_str}]", expanded=True):
            col_l, col_m, col_r = st.columns(3)
            with col_l:
                st.write(f"張數: **{row['張數']}**")
                st.write(f"現價: **{row['現價']:.2f}**")
                st.caption(f"均價: {row['均價']:.2f}")
            with col_m:
                st.markdown(f"市值: **${row['市值']:,.0f}**")
                st.markdown(f"損益: :{p_color}[**${row['損益']:,.0f}**]")
            with col_r:
                st.markdown(f"預估領息: :orange[**${row['預估領息']:,.0f}**]")
                st.caption(f"📅 除息日: {row['除息日']}")

st.write("---")
if st.button("🔄 重新整理股價"):
    st.cache_data.clear()
    st.rerun()
