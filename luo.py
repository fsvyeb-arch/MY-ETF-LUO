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

# 全局提示訊息狀態
if 'update_success' in st.session_state and st.session_state.update_success:
    st.toast(st.session_state.update_success, icon="✅")
    st.session_state.update_success = False

# 自定義 CSS
st.markdown("""
    <style>
    /* 🔥 終極暴力隱藏表格右上角浮動工具列 */
    [data-testid="stElementToolbar"], 
    [data-testid="stDataFrameToolbar"],
    [data-testid="stToolbar"],
    .stDataFrame [data-testid="stElementToolbar"] { 
        display: none !important; 
        opacity: 0 !important; 
        visibility: hidden !important; 
        pointer-events: none !important;
    }
    
    [data-testid="stMetricDelta"] svg { fill: red; }
    
    [data-testid="stMetric"] { 
        background-color: var(--secondary-background-color); 
        padding: 12px; 
        border-radius: 10px; 
        box-shadow: 1px 1px 4px rgba(0,0,0,0.05);
    }
    
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

    @keyframes lightning-strike {
        0% { box-shadow: 0 0 10px rgba(241, 196, 15, 0.5); background-color: #fffdf5; border-color: #f1c40f; transform: scale(1); }
        50% { box-shadow: 0 0 40px rgba(255, 235, 59, 1), inset 0 0 25px rgba(255, 235, 59, 0.9); background-color: #ffffe0; border-color: #ffeb3b; transform: scale(1.03); }
        100% { box-shadow: 0 0 10px rgba(241, 196, 15, 0.5); background-color: #fffdf5; border-color: #f1c40f; transform: scale(1); }
    }
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

ETF_FULL_DATABASE = {
    "0050": ["元大台灣50", [1, 7], "0.32%", "0.035%"], "0051": ["元大中型100", [11], "0.4%", "0.035%"],
    "0052": ["富邦台灣科技指數", [4], "0.15%", "0.035%"], "0053": ["元大台灣電子科技", [11], "0.3%", "0.035%"],
    "0055": ["元大MSCI金融", [11], "0.3%", "0.035%"], "0056": ["元大台灣高股息", [1, 4, 7, 10], "0.3%", "0.035%"],
    "0057": ["富邦摩台", [6], "0.15%", "0.035%"], "006201": ["元大富櫃50", [12], "0.4%", "0.035%"],
    "006203": ["元大摩臺台灣", [1, 7], "0.3%", "0.035%"], "006204": ["永豐臺灣加權", [10], "0.32%", "0.035%"],
    "006208": ["富邦台50", [7, 11], "0.15%", "0.035%"], "00690": ["兆豐藍籌30", [2, 5, 8, 11], "0.32%", "0.035%"],
    "00692": ["富邦臺灣公司治理", [7, 11], "0.15%", "0.035%"], "00701": ["國泰股利精選30", [1, 8], "0.3%", "0.035%"],
    "00713": ["元大台灣高息低波", [3, 6, 9, 12], "0.3%", "0.035%"], "00728": ["第一金工業30", [3, 6, 9, 12], "0.4%", "0.035%"],
    "00730": ["富邦臺灣優質高息", list(range(1, 13)), "0.45%", "0.035%"], "00731": ["復華富時高息低波", [2, 5, 8, 11], "0.3%", "0.035%"],
    "00733": ["富邦臺灣中小", [5, 10], "0.4%", "0.035%"], "00850": ["元大臺灣ESG永續", [2, 5, 8, 11], "0.3%", "0.035%"],
    "00878": ["國泰永續ESG高股息", [2, 5, 8, 11], "0.25%", "0.035%"], "00881": ["國泰台灣5G+", [1, 8], "0.4%", "0.035%"],
    "00888": ["永豐台灣ESG永續優質", [1, 4, 7, 10], "0.25%", "0.03%"], "00891": ["中信關鍵半導體", [2, 5, 8, 11], "0.4%", "0.035%"],
    "00892": ["富邦台灣核心半導體", [], "0.4%", "0.035%"], "00894": ["中信特選小資高價30", [2, 5, 8, 11], "0.4%", "0.035%"],
    "00896": ["中信綠能及電動車", [3, 6, 9, 12], "0.4%", "0.035%"], "00900": ["富邦特選高股息30", [2, 5, 8, 11], "0.3%", "0.035%"],
    "00901": ["永豐台灣智能車供應鏈", [10], "0.4%", "0.04%"], "00904": ["新光臺灣半導體30", [1, 4, 7, 10], "0.4%", "0.035%"],
    "00905": ["FT臺灣Smart", [1, 4, 7, 10], "0.4%", "0.035%"], "00907": ["永豐優選存股", [2, 4, 6, 8, 10, 12], "0.4%", "0.03%"],
    "00912": ["中信台灣智慧50", [1, 4, 7, 10], "0.3%", "0.035%"], "00913": ["兆豐晶圓製造", [1, 7], "0.4%", "0.03%"],
    "00915": ["凱基優選高股息30", [3, 6, 9, 12], "0.3%", "0.035%"], "00918": ["大華優利高填息30", [3, 6, 9, 12], "0.35%", "0.035%"],
    "00919": ["群益台灣精選高息", [3, 6, 9, 12], "0.3%", "0.035%"], "00921": ["兆豐龍頭等權重", [3, 6, 9, 12], "0.45%", "0.030%"],
    "00922": ["國泰台灣領袖50", [3, 10], "0.20%", "0.035%"], "00923": ["群益台灣ESG低碳50", [2, 8], "0.32%", "0.035%"],
    "00927": ["群益台灣半導體收益", [1, 4, 7, 10], "0.4%", "0.035%"], "00928": ["中信上櫃ESG30", [1, 7], "0.4%", "0.035%"],
    "00929": ["復華台灣科技優息", list(range(1, 13)), "0.30%", "0.030%"], "00930": ["永豐ESG低碳高息", [1, 3, 5, 7, 9, 11], "0.35%", "0.035%"],
    "00932": ["兆豐永續高息等權", [2, 5, 8, 11], "0.15%", "0.030%"], "00934": ["中信成長高股息", list(range(1, 13)), "0.3%", "0.035%"],
    "00935": ["野村臺灣創新科技50", [3, 9], "0.4%", "0.035%"], "00936": ["台新永續高息中小", list(range(1, 13)), "0.4%", "0.035%"],
    "00938": ["凱基優選30", [2, 5, 8, 11], "0.3%", "0.35%"], "00939": ["統一台灣高息動力", list(range(1, 13)), "0.3%", "0.035%"],
    "00940": ["元大臺灣價值高息", list(range(1, 13)), "0.3%", "0.030%"], "00943": ["兆豐電子高息等權", list(range(1, 13)), "0.25%", "0.03%"],
    "00944": ["野村臺灣趨勢動能高股息", list(range(1, 13)), "0.4%", "0.035%"], "00946": ["群益台灣科技高息成長", list(range(1, 13)), "0.3%", "0.030%"],
    "00947": ["台新臺灣IC設計動能", [1, 4, 7, 10], "0.40%", "0.030%"], "00952": ["凱基台灣AI 50", list(range(1, 13)), "0.40%", "0.030%"],
    "00961": ["FT臺灣永續高息", list(range(1, 13)), "0.30%", "0.035%"], "00962": ["台新臺灣AI優息動能", list(range(1, 13)), "0.40%", "0.035%"],
    "009802": ["富邦旗艦50", [3, 6, 9, 12], "0.15%", "0.03%"], "009803": ["保德信市值動能50", [3, 6, 9, 12], "0.25%", "0.035%"],
    "009804": ["聯邦台灣精彩50", [4, 7], "0.15%", "0.035%"], "009808": ["華南永昌台灣優選50", [2, 5, 8, 11], "0.05%", "0.035%"],
    "009809": ["富邦台灣淨零轉型 ESG 50", [3, 6, 9, 12], "0.30%", "0.035%"], "00980A": ["野村臺灣智慧優選主動式", [2, 5, 8, 11], "0.75%", "0.035%"],
    "00981A": ["統一台股增長主動式", [3, 6, 9, 12], "1.0%", "0.10%"], "00982A": ["群益台灣精選強棒主動式", [2, 5, 8, 11], "0.8%", "0.035%"],
    "00984A": ["安聯台灣高息成長主動式", [1, 4, 7, 10], "0.7%", "0.04%"], "00985A": ["野村台灣增強50主動式", [1], "0.45%", "0.035%"],
    "00981T": ["平衡凱基雙核收息", [], "0.60%", "0.10%"]
}

EXTRA_ETFS = {
    "00631L": "00631L 元大台灣50正2", "00673R": "00673R 期元大S&P原油反1", 
    "00632R": "00632R 元大台灣50反1", "009819": "009819 中信數據及電力", 
    "00712": "00712 復華富時不動產", "00992A": "00992A 主推群益科技創新",
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

ETF_NAME_DB, DIVIDEND_SCHEDULE, ETF_FEES_DB = {}, {}, {}
for k, v in EXTRA_ETFS.items(): ETF_NAME_DB[k] = v
for k, v in ETF_FULL_DATABASE.items():
    ETF_NAME_DB[k] = f"{k} {v[0]}"
    DIVIDEND_SCHEDULE[f"{k}.TW"] = v[1]
    ETF_FEES_DB[f"{k}.TW"] = {"經理費": v[2], "保管費": v[3]}

ETF_CONSTITUENTS_DB = {
    "0056.TW": [{"name": "鴻海", "weight": 6.5}, {"name": "聯發科", "weight": 5.2}, {"name": "聯詠", "weight": 4.8}, {"name": "中信金", "weight": 4.5}, {"name": "聯電", "weight": 4.1}, {"name": "其他", "weight": 74.9}],
    "00878.TW": [{"name": "聯發科", "weight": 5.5}, {"name": "國泰金", "weight": 5.1}, {"name": "富邦金", "weight": 4.9}, {"name": "廣達", "weight": 4.5}, {"name": "聯電", "weight": 4.2}, {"name": "其他", "weight": 75.8}],
    "00919.TW": [{"name": "長榮", "weight": 11.5}, {"name": "聯電", "weight": 6.2}, {"name": "瑞昱", "weight": 5.8}, {"name": "聯發科", "weight": 5.1}, {"name": "聯詠", "weight": 4.8}, {"name": "其他", "weight": 66.6}],
    "00927.TW": [{"name": "台積電", "weight": 31.2}, {"name": "聯發科", "weight": 15.5}, {"name": "聯電", "weight": 6.5}, {"name": "日月光投控", "weight": 5.8}, {"name": "瑞昱", "weight": 5.2}, {"name": "其他", "weight": 35.8}],
    "00891.TW": [{"name": "台積電", "weight": 30.5}, {"name": "聯發科", "weight": 14.2}, {"name": "聯電", "weight": 6.1}, {"name": "日月光投控", "weight": 5.5}, {"name": "瑞昱", "weight": 5.0}, {"name": "其他", "weight": 38.7}],
    "00929.TW": [{"name": "聯發科", "weight": 9.5}, {"name": "聯電", "weight": 7.2}, {"name": "日月光投控", "weight": 6.8}, {"name": "瑞昱", "weight": 6.5}, {"name": "聯詠", "weight": 6.1}, {"name": "其他", "weight": 63.9}],
    "0050.TW": [{"name": "台積電", "weight": 52.5}, {"name": "鴻海", "weight": 5.5}, {"name": "聯發科", "weight": 4.8}, {"name": "廣達", "weight": 2.1}, {"name": "台達電", "weight": 1.9}, {"name": "其他", "weight": 33.2}],
    "006208.TW": [{"name": "台積電", "weight": 52.6}, {"name": "鴻海", "weight": 5.4}, {"name": "聯發科", "weight": 4.9}, {"name": "廣達", "weight": 2.0}, {"name": "台達電", "weight": 1.8}, {"name": "其他", "weight": 33.3}],
    "00713.TW": [{"name": "統一", "weight": 8.5}, {"name": "台灣大", "weight": 7.2}, {"name": "遠傳", "weight": 6.8}, {"name": "華碩", "weight": 6.1}, {"name": "仁寶", "weight": 5.5}, {"name": "其他", "weight": 65.9}],
    "00940.TW": [{"name": "長榮", "weight": 9.5}, {"name": "聯電", "weight": 6.5}, {"name": "聯發科", "weight": 5.8}, {"name": "中美晶", "weight": 5.2}, {"name": "神基", "weight": 4.8}, {"name": "其他", "weight": 68.2}]
}

def load_settings():
    default_data = {
        "etfs": [], "pledge": {"borrowed_amount": 0, "months_passed": 1, "total_months": 18},
        "watchlist": [],
        "custom_divs": {
            "00891.TW": {"v": 1.250, "d": "2026-05-20", "p": "2026-06-15"},
            "00878.TW": {"v": 0.510, "d": "2026-05-18", "p": "2026-06-12"},
            "00982A.TW": {"v": 0.377, "d": "2026-05-21", "p": "2026-06-18"}
        },
        "personal_finance": {"incomes": [], "expenses": []}
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f: 
                data = json.load(f)
                for k, v in default_data.items():
                    if k not in data: data[k] = v
                data['custom_divs'].update(default_data['custom_divs'])
                return data
        except: pass
    return default_data

def save_to_json(data):
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4, ensure_ascii=False)

if 'my_data' not in st.session_state: st.session_state.my_data = load_settings()

# --- 自動展期共用邏輯 ---
def auto_advance_months(entry_dict, default_paid, default_total, key_paid="months_paid", key_total="total_months"):
    if key_paid not in entry_dict: entry_dict[key_paid] = default_paid
    if key_total not in entry_dict: entry_dict[key_total] = default_total
    
    now_str = datetime.now().strftime("%Y-%m")
    last_m = entry_dict.get('last_updated_month', now_str)
    
    if last_m != now_str:
        y_curr, m_curr = map(int, now_str.split('-'))
        y_last, m_last = map(int, last_m.split('-'))
        diff_months = (y_curr - y_last) * 12 + (m_curr - m_last)
        if diff_months > 0:
            entry_dict[key_paid] = min(entry_dict[key_total], entry_dict[key_paid] + diff_months)
            entry_dict['last_updated_month'] = now_str
            return True
    return False

data_changed = False
if 'loan' not in st.session_state.my_data: st.session_state.my_data['loan'] = {"months_paid": 1, "regular_amount": 15000, "total_months": 84, "last_updated_month": datetime.now().strftime("%Y-%m")}
if auto_advance_months(st.session_state.my_data['loan'], 1, 84): data_changed = True

if 'loan_chb' not in st.session_state.my_data: st.session_state.my_data['loan_chb'] = {"months_paid": 21, "regular_amount": 0, "total_months": 60, "last_updated_month": datetime.now().strftime("%Y-%m")}
if auto_advance_months(st.session_state.my_data['loan_chb'], 21, 60): data_changed = True

if 'pledge' not in st.session_state.my_data: st.session_state.my_data['pledge'] = {"borrowed_amount": 0, "months_passed": 1, "total_months": 18, "last_updated_month": datetime.now().strftime("%Y-%m")}
if auto_advance_months(st.session_state.my_data['pledge'], 1, 18, key_paid="months_passed"): data_changed = True

for etf in st.session_state.my_data['etfs']:
    if 'pledged_shares' not in etf: etf['pledged_shares'] = 0.0

if data_changed: save_to_json(st.session_state.my_data)

# --- 樣式設定輔助函數 ---
def color_profit_loss(val):
    if isinstance(val, str):
        if val.startswith('+'): return 'color: #d32f2f; font-weight: bold;' 
        elif val.startswith('-'): return 'color: #388e3c; font-weight: bold;' 
    return ''

def color_months(val):
    if not isinstance(val, str): return ''
    if val == '1,4,7,10月': return 'background-color: #e3f2fd; color: #1565c0; font-weight: bold; text-align: center;' 
    if val == '2,5,8,11月': return 'background-color: #f3e5f5; color: #6a1b9a; font-weight: bold; text-align: center;' 
    if val == '3,6,9,12月': return 'background-color: #e8f5e9; color: #2e7d32; font-weight: bold; text-align: center;' 
    if val == '月配息': return 'background-color: #fff8e1; color: #f57f17; font-weight: bold; text-align: center;' 
    return 'color: #555; text-align: center;'

def color_diff(val):
    if isinstance(val, str) and '%' in val:
        if val.startswith('+'): return 'color: #d32f2f; font-weight: bold;'
        elif val.startswith('-'): return 'color: #388e3c; font-weight: bold;'
    elif isinstance(val, (int, float)):
        if val > 0: return 'color: #d32f2f; font-weight: bold;'
        elif val < 0: return 'color: #388e3c; font-weight: bold;'
    return ''

def color_pnl(df_to_style):
    css = pd.DataFrame('', index=df_to_style.index, columns=df_to_style.columns)
    for idx in df_to_style.index:
        for col in df_to_style.columns:
            if col == '股票代號': continue
            val = df_to_style.loc[idx, col]
            if pd.notna(val) and isinstance(val, (int, float)):
                if val > 0: css.loc[idx, col] = 'color: #d32f2f; font-weight: bold;'
                elif val < 0: css.loc[idx, col] = 'color: #388e3c; font-weight: bold;'
    return css

# --- 🚀 Callback 函數區 ---
def auto_fill_etf_name():
    raw_sym = st.session_state.get('add_sym_bot', '')
    clean_sym = raw_sym.strip().upper().replace(".TW", "")
    st.session_state.add_name_bot = ETF_NAME_DB.get(clean_sym, f"{clean_sym} ETF") if clean_sym else ""

def add_new_etf_bot():
    raw_sym = st.session_state.get('add_sym_bot', '')
    new_name = st.session_state.get('add_name_bot', '')
    new_h, new_c = st.session_state.get('add_h_bot', 0.0), st.session_state.get('add_c_bot', 0.0)
    clean_symbol = raw_sym.strip().upper().replace(".TW", "")
    if clean_symbol and new_name:
        st.session_state.my_data['etfs'].append({"symbol": f"{clean_symbol}.TW", "name": new_name, "holdings": new_h, "cost": new_c, "alert_high": 0.0, "alert_low": 0.0, "pledged_shares": 0.0})
        save_to_json(st.session_state.my_data)
        st.cache_data.clear() 
        st.session_state.add_sym_bot, st.session_state.add_name_bot, st.session_state.add_h_bot, st.session_state.add_c_bot = "", "", 0.0, 0.0
        st.session_state.update_success = "已成功新增庫存，配息資料已同步更新！"

def delete_etf(index):
    if 0 <= index < len(st.session_state.my_data['etfs']):
        st.session_state.my_data['etfs'].pop(index)
        save_to_json(st.session_state.my_data)
        st.cache_data.clear() 
        st.session_state.update_success = "已成功刪除庫存！"

def save_edits():
    temp_list = []
    for i, item in enumerate(st.session_state.my_data['etfs']):
        h_val = st.session_state.get(f"edit_h_{i}", item['holdings'])
        c_val = st.session_state.get(f"edit_c_{i}", item['cost'])
        temp_list.append({
            "symbol": item['symbol'], "name": item['name'], "holdings": h_val, "cost": c_val,
            "alert_high": item.get('alert_high', 0.0), "alert_low": item.get('alert_low', 0.0), "pledged_shares": item.get('pledged_shares', 0.0)
        })
    st.session_state.my_data['etfs'] = temp_list
    save_to_json(st.session_state.my_data)
    st.cache_data.clear() 
    st.session_state.update_success = "庫存數量已自動更新！"

def auto_fill_wl_name():
    raw_sym = st.session_state.get('add_sym_wl', '')
    clean_sym = raw_sym.strip().upper().replace(".TW", "")
    st.session_state.add_name_wl = ETF_NAME_DB.get(clean_sym, f"{clean_sym}") if clean_sym else ""

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
        st.session_state.add_sym_wl, st.session_state.add_name_wl = "", ""

def delete_wl(index):
    if 0 <= index < len(st.session_state.my_data['watchlist']):
        st.session_state.my_data['watchlist'].pop(index)
        save_to_json(st.session_state.my_data)

def execute_trade():
    trade_etf_name, trade_type, trade_shares = st.session_state.calc_selected_etf, st.session_state.calc_trade_type, st.session_state.calc_trade_shares
    for i, item in enumerate(st.session_state.my_data['etfs']):
        if item['name'] == trade_etf_name:
            current_holdings, current_cost = item['holdings'], item['cost']
            current_price = df[df['名稱'] == trade_etf_name].iloc[0]['現價']
            if trade_type == "賣出 (計算已實現損益)":
                actual_sell_shares = min(trade_shares, current_holdings)
                new_holdings = current_holdings - actual_sell_shares
                if new_holdings <= 0:
                    st.session_state.my_data['etfs'].pop(i)
                    st.success(f"已全數賣出 {trade_etf_name}，並從庫存中移除！")
                else:
                    item['holdings'] = new_holdings
                    st.success(f"成功賣出 {actual_sell_shares} 張 {trade_etf_name}！庫存剩餘 {new_holdings} 張。")
            else:
                buy_cost_total = current_price * trade_shares * 1000
                new_total_shares = current_holdings + trade_shares
                new_total_cost_val = (current_cost * current_holdings * 1000) + buy_cost_total
                item['holdings'] = new_total_shares
                item['cost'] = round(new_total_cost_val / (new_total_shares * 1000) if new_total_shares > 0 else 0, 2)
                st.success(f"成功買進 {trade_shares} 張 {trade_etf_name}！最新均價更新為 ${item['cost']}。")
            save_to_json(st.session_state.my_data)
            st.cache_data.clear() 
            break

# UI 開關狀態
ui_toggles = ['show_us', 'show_tw', 'show_calendar', 'show_div_db', 'show_tech', 'show_holdings', 'show_constituents', 'show_pledge', 'show_secret', 'is_unlocked']
for t in ui_toggles:
    if t not in st.session_state: st.session_state[t] = False

def toggle_us(): st.session_state.show_us = not st.session_state.show_us
def toggle_tw(): st.session_state.show_tw = not st.session_state.show_tw
def toggle_calendar(): st.session_state.show_calendar = not st.session_state.show_calendar
def toggle_div_db(): st.session_state.show_div_db = not st.session_state.show_div_db
def toggle_tech(): st.session_state.show_tech = not st.session_state.show_tech
def toggle_holdings(): st.session_state.show_holdings = not st.session_state.show_holdings
def toggle_constituents(): st.session_state.show_constituents = not st.session_state.show_constituents
def toggle_pledge(): st.session_state.show_pledge = not st.session_state.show_pledge 
def toggle_secret(): st.session_state.show_secret = not st.session_state.show_secret

# --- 4. 核心數據獲取函數 ---
@st.cache_data(ttl=10800) 
def fetch_taiwan_upcoming_dividends():
    tw_div_data = {}
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        data = requests.get("https://www.twse.com.tw/exchangeReport/TWT49U?response=json", headers=headers, timeout=5).json()
        if data.get('stat') == 'OK':
            import re
            for row in data.get('data', []):
                if len(row) >= 8: 
                    symbol = str(row[1]).strip() 
                    match = re.search(r'(\d+)年(\d+)月(\d+)日', str(row[0]))
                    if match:
                        tw_year, month, day = match.groups()
                        ex_date = f"{int(tw_year) + 1911}-{month.zfill(2)}-{day.zfill(2)}"
                        cash_div_str = str(row[7]).replace(',', '').strip()
                        amount = float(cash_div_str) if cash_div_str and cash_div_str.replace('.', '', 1).isdigit() else 0.0
                        tw_div_data[symbol] = {"ex_date": ex_date, "pay_date": (datetime.strptime(ex_date, '%Y-%m-%d') + timedelta(days=28)).strftime('%Y-%m-%d'), "amount": amount}
    except: pass

    try:
        data_tpex = requests.get("https://www.tpex.org.tw/web/stock/exright/preAnnounce/PrePost_result.php?l=zh-tw&o=json", headers=headers, timeout=5).json()
        if 'aaData' in data_tpex:
            for row in data_tpex['aaData']:
                if len(row) >= 6:
                    symbol = str(row[1]).strip()
                    parts = str(row[0]).split('/')
                    if len(parts) == 3:
                        ex_date = f"{int(parts[0]) + 1911}-{parts[1].zfill(2)}-{parts[2].zfill(2)}"
                        cash_div_str = str(row[5]).replace(',', '').strip()
                        amount = float(cash_div_str) if cash_div_str and cash_div_str.replace('.', '', 1).isdigit() else 0.0
                        tw_div_data[symbol] = {"ex_date": ex_date, "pay_date": (datetime.strptime(ex_date, '%Y-%m-%d') + timedelta(days=28)).strftime('%Y-%m-%d'), "amount": amount}
    except: pass
    return tw_div_data

@st.cache_data(ttl=86400) 
def get_fund_size(symbol):
    try:
        tk = yf.Ticker(symbol)
        cap = tk.fast_info.get('marketCap')
        if cap and cap > 0: return cap
        shares = tk.fast_info.get('shares')
        price = tk.fast_info.get('lastPrice') or tk.fast_info.get('previousClose')
        if shares and price: return shares * price
        info = tk.info
        cap = info.get('totalAssets') or info.get('marketCap')
        if cap and cap > 0: return cap
    except: pass
    return None

@st.cache_data(ttl=43200)
def get_div_data(symbol, custom_div_info=None):
    is_announced = False
    div_amount = 0.0
    ex_date, pay_date, fill_status, status_msg = "待官方公告", "待官方公告", "-", "⏳ 依前次估算"
    clean_sym = symbol.replace('.TW', '')
    taiwan_div_data = fetch_taiwan_upcoming_dividends()
    today = datetime.today()
    
    try:
        tk = yf.Ticker(symbol)
        if custom_div_info and custom_div_info.get('v', 0) > 0:
            div_amount, ex_date, pay_date = custom_div_info['v'], custom_div_info['d'], custom_div_info['p']
            is_announced = True
            status_msg = "✅ 已公告 (手動)" if datetime.strptime(ex_date, '%Y-%m-%d').date() >= today.date() else "✅ 前次紀錄 (手動)"
        elif clean_sym in taiwan_div_data:
            is_announced = True
            ex_date, pay_date, div_amount = taiwan_div_data[clean_sym]['ex_date'], taiwan_div_data[clean_sym]['pay_date'], taiwan_div_data[clean_sym]['amount']
            if div_amount == 0:
                actions = tk.actions
                if not actions.empty: div_amount = float(actions.sort_index(ascending=False).head(1)['Dividends'].values[0])
            status_msg = "✅ 已公告 (台灣官方)" if datetime.strptime(ex_date, '%Y-%m-%d').date() >= today.date() else "✅ 前次配息 (台灣官方)"
        else:
            divs = tk.dividends
            if not divs.empty:
                latest_div = divs.sort_index(ascending=False).head(1)
                div_amount = float(latest_div.values[0]) 
                last_ex_date_obj = latest_div.index[0].replace(tzinfo=None)
                ex_date = last_ex_date_obj.strftime('%Y-%m-%d')
                pay_date = (last_ex_date_obj + timedelta(days=28)).strftime('%Y-%m-%d') 
                is_announced = True
                status_msg = "✅ 已公告 (近期)" if last_ex_date_obj.date() >= today.date() else "✅ 前次配息紀錄"

        hist = tk.history(period='1y')
        divs = tk.dividends
        if not divs.empty and not hist.empty:
            now_ts = pd.Timestamp.now(tz=divs.index.tzinfo) if divs.index.tzinfo else pd.Timestamp.now()
            past_divs = divs[divs.index < now_ts].sort_index(ascending=False)
            if not past_divs.empty:
                last_ex_date = past_divs.index[0]
                pre_ex, post_ex = hist[hist.index < last_ex_date], hist[hist.index >= last_ex_date]
                if not pre_ex.empty and not post_ex.empty:
                    target_price = pre_ex['Close'].iloc[-1]
                    t_days, filled = 0, False
                    for d, r in post_ex.iterrows():
                        t_days += 1
                        if r['High'] >= target_price:
                            fill_status = f"{d.month}/{d.day} 填息完成 ({t_days}天)"
                            filled = True
                            break
                    if not filled: fill_status = f"未填息 ({t_days}天)"
    except: pass
    return is_announced, div_amount, ex_date, pay_date, fill_status, status_msg

@st.cache_data(ttl=10)
def fetch_watchlist_data(wl_list):
    if not wl_list: return pd.DataFrame()
    results = []
    for item in wl_list:
        try:
            tk = yf.Ticker(item['symbol'])
            hist = tk.history(period="2d")
            if hist.empty: continue
            curr_p = tk.fast_info.get('lastPrice') or hist['Close'].iloc[-1]
            prev_close = tk.fast_info.get('previousClose') or (hist['Close'].iloc[-2] if len(hist) >= 2 else curr_p)
            diff = curr_p - prev_close
            pct = (diff / prev_close * 100) if prev_close else 0
            results.append({"代號": item['symbol'].replace('.TW', ''), "名稱": item['name'], "現價": round(curr_p, 2), "漲跌": round(diff, 2), "漲跌幅": f"{pct:+.2f}%", "狀態": "🔴" if diff > 0 else "🟢" if diff < 0 else "⚪"})
        except: continue
    return pd.DataFrame(results)

@st.cache_data(ttl=43200)
def fetch_watchlist_dividend(wl_list, custom_divs):
    if not wl_list: return pd.DataFrame()
    results = []
    for item in wl_list:
        sym = item['symbol']
        try:
            cap_raw = get_fund_size(sym)
            is_announced, div_amount, ex_date, pay_date, fill_status, status_msg = get_div_data(sym, custom_divs.get(sym))
            months = DIVIDEND_SCHEDULE.get(sym, [])
            freq = "月配息" if len(months)==12 else "季配息" if len(months)==4 else "半年配" if len(months)==2 else "年配息" if len(months)==1 else "未知"
            results.append({
                "類別": "👀 自選", "ETF 名稱": item['name'], "基金規模": f"{cap_raw / 100000000:.2f} 億" if cap_raw else "系統無資料",  
                "配息頻率": freq, "配息月份": "、".join(map(str, months)) + " 月" if months else "未設定",
                "狀態": status_msg, "除息日": ex_date, "發放日": pay_date, "每股金額": f"${div_amount:.3f}", "最新填息紀錄": fill_status
            })
        except: continue
    return pd.DataFrame(results)

@st.cache_data(ttl=10)
def fetch_data(etf_list, custom_divs):
    if not etf_list: return pd.DataFrame(), pd.DataFrame(), 0, 0, 0, 0, [], [], [], {i: {"amount": 0, "sources": []} for i in range(1, 13)}
    results, tech_results = [], []
    total_mkt, total_cost, total_div, total_today_pnl = 0, 0, 0, 0
    radar_ex, radar_pay, price_alerts = [], [], []
    monthly_calendar = {i: {"amount": 0, "sources": []} for i in range(1, 13)} 
    today = datetime.today()

    for item in etf_list:
        try:
            tk = yf.Ticker(item['symbol'])
            cap_raw = get_fund_size(item['symbol'])
            hist = tk.history(period='5d') 
            if hist.empty: continue
            
            curr_p = tk.fast_info.get('lastPrice') or hist['Close'].iloc[-1]
            prev_close = tk.fast_info.get('previousClose') or (hist['Close'].iloc[-2] if len(hist) >= 2 else curr_p)
            day_high = tk.fast_info.get('dayHigh') or hist['High'].iloc[-1]
            day_low = tk.fast_info.get('dayLow') or hist['Low'].iloc[-1]
            vol = tk.fast_info.get('lastVolume') or hist['Volume'].iloc[-1]
            
            shares = item['holdings'] * 1000
            mkt_val, cost_val = shares * curr_p, shares * item['cost']
            profit = mkt_val - cost_val - (mkt_val * 0.00235)
            
            today_diff = curr_p - prev_close
            today_profit = shares * today_diff
            total_today_pnl += today_profit
            
            a_high, a_low = float(item.get('alert_high', 0.0)), float(item.get('alert_low', 0.0))
            if a_high > 0 and curr_p >= a_high: price_alerts.append({"name": item['name'], "price": curr_p, "target": a_high, "type": "high"})
            if a_low > 0 and curr_p <= a_low: price_alerts.append({"name": item['name'], "price": curr_p, "target": a_low, "type": "low"})

            is_announced, div_amount, ex_date, pay_date, fill_status, status_msg = get_div_data(item['symbol'], custom_divs.get(item['symbol']))
            months_to_pay = DIVIDEND_SCHEDULE.get(item['symbol'], [])
            
            if is_announced and ex_date != "待官方公告" and 0 <= (datetime.strptime(ex_date, '%Y-%m-%d').date() - today.date()).days <= 20:
                radar_ex.append({"symbol": item['symbol'].split('.')[0], "date": ex_date, "days": (datetime.strptime(ex_date, '%Y-%m-%d').date() - today.date()).days})
            if is_announced and pay_date != "待官方公告" and 0 <= (datetime.strptime(pay_date, '%Y-%m-%d').date() - today.date()).days <= 20:
                radar_pay.append({"symbol": item['symbol'].split('.')[0], "date": pay_date, "amount": shares * div_amount, "days": (datetime.strptime(pay_date, '%Y-%m-%d').date() - today.date()).days})

            if div_amount > 0 and shares > 0:
                explicit_pay_month = datetime.strptime(pay_date, '%Y-%m-%d').month if is_announced and pay_date != "待官方公告" else None
                if explicit_pay_month:
                    monthly_calendar[explicit_pay_month]["amount"] += (shares * div_amount)
                    if item['name'] not in monthly_calendar[explicit_pay_month]["sources"]: monthly_calendar[explicit_pay_month]["sources"].append(item['name'])
                for m in months_to_pay:
                    pay_m = m + 1 if m < 12 else 1
                    if pay_m != explicit_pay_month:
                        monthly_calendar[pay_m]["amount"] += (shares * div_amount)
                        if item['name'] not in monthly_calendar[pay_m]["sources"]: monthly_calendar[pay_m]["sources"].append(item['name'])

            total_mkt += mkt_val; total_cost += cost_val; total_div += (shares * div_amount)
            fee_info = ETF_FEES_DB.get(item['symbol'], {"經理費": "-", "保管費": "-"})

            results.append({
                "代號": item['symbol'], "名稱": item['name'], "現價": curr_p, "均價": item['cost'],
                "張數": item['holdings'], "市值": mkt_val, "損益": profit, "報酬率": (profit / cost_val * 100) if cost_val != 0 else 0,
                "經理費": fee_info["經理費"], "保管費": fee_info["保管費"], 
                "單次預估領息": shares * div_amount, "每股配息": div_amount,
                "最新公告除息日": ex_date, "預估發放日": pay_date, "已公告": is_announced,
                "狀態": status_msg, "最新填息紀錄": fill_status, "基金規模": f"{cap_raw / 100000000:.2f} 億" if cap_raw else "系統無資料"
            })
            
            tech_results.append({
                "ETF 名稱": f"{'🔴' if curr_p > prev_close else '🟢' if curr_p < prev_close else '⚪'} {item['name']}", 
                "配息月份": "月配息" if len(months_to_pay) == 12 else ",".join(map(str, months_to_pay)) + "月" if months_to_pay else "-", 
                "股票張數": item['holdings'], 
                "現價": round(curr_p, 2),
                "基金規模": f"{cap_raw / 100000000:.2f} 億" if cap_raw else "系統無資料",
                "今日損益": f"+${today_profit:,.0f}" if today_profit >= 0 else f"-${abs(today_profit):,.0f}", 
                "今日漲跌幅": f"+{(today_diff / prev_close * 100):.2f}%" if today_diff >= 0 else f"{(today_diff / prev_close * 100):.2f}%", 
                "今日交易量": f"{vol:,.0f}" if vol > 0 else "無資料",
                "年殖利率": f"{(div_amount * len(months_to_pay)) / curr_p * 100:.2f}%" if len(months_to_pay) > 0 and div_amount > 0 and curr_p > 0 else "0.00%", 
                "今日最高/最低": f"${day_high:.2f} / ${day_low:.2f}",
                "52週最高/最低": f"${tk.fast_info.get('yearHigh', 0):.2f} / ${tk.fast_info.get('yearLow', 0):.2f}"
            })
        except: continue
        
    return pd.DataFrame(results), pd.DataFrame(tech_results), total_mkt, total_cost, total_div, total_today_pnl, radar_ex, radar_pay, price_alerts, monthly_calendar

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
                news_list.append({"title": f"{today_str} {title}", "link": item.find('link').text})
    except: pass
    return news_list or [
        {"title": f"{today_str} 盤前觀察：半導體龍頭動向 (影響 00927 走勢)", "link": "#"},
        {"title": f"{today_str} 高股息標的篩選：關注 00878、0056 成分股調整", "link": "#"},
        {"title": f"{today_str} 焦點情報：多檔新上市主動式 ETF 展開募集與掛牌", "link": "#"},
        {"title": f"{today_str} 大盤壓力測試：正二 (00631L) 槓桿風險控管建議", "link": "#"}
    ]

@st.cache_data(ttl=300) 
def fetch_macro_data():
    tickers = {"us": {"道瓊工業": "^DJI", "那斯達克": "^IXIC", "費城半導體": "^SOX", "輝達 NVIDIA": "NVDA", "台積電 ADR": "TSM"},
               "tw": {"台股加權 (大盤)": "^TWII", "台積電 (台股)": "2330.TW", "聯發科 (台股)": "2454.TW", "台指期 (近月)": "WTX&P"}}
    res = {"us": {}, "tw": {}}
    for region, t_dict in tickers.items():
        for name, symbol in t_dict.items():
            try:
                hist = yf.Ticker(symbol).history(period="5d")
                if len(hist) >= 2:
                    curr, prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
                    res[region][name] = {"price": curr, "diff": curr - prev, "pct": ((curr - prev) / prev) * 100, "date": hist.index[-1].strftime("%m/%d")}
            except: pass
    return res

def render_macro_cards(data_dict, region_prefix):
    cols = st.columns(3)
    for idx, (name, data) in enumerate(data_dict.items()):
        is_up = data['diff'] >= 0
        color_hex, sign = ("#e74c3c", "+") if is_up else ("#2ecc71", "")
        with cols[idx % 3]:
            st.markdown(f"""
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
            """, unsafe_allow_html=True)

# 執行核心數據載入
df, df_tech, g_mkt, g_cost, g_div, g_today_pnl, radar_ex, radar_pay, price_alerts, monthly_calendar = fetch_data(st.session_state.my_data['etfs'], st.session_state.my_data.get('custom_divs', {}))
macro_data = fetch_macro_data()

# --- 5. 介面呈現 ---
st.title("📈 實戰資產戰情室")
st.caption(f"最後更新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

news_html = "<div class='news-box'><div class='news-title'>📰 今日財經焦點</div>"
for news in fetch_etf_news(): news_html += f"<div class='news-item'>👉 📍 <a href='{news['link']}' target='_blank'>{news['title']}</a></div>"
st.markdown(news_html + "</div>", unsafe_allow_html=True)

st.markdown("### 📢 近期新募集 / 即將上市主動式 ETF 追蹤")
upcoming_list = [{"date": "2026/05/20", "symbol": "00992A", "name": "主動群益科技創新"}, {"date": "2026/05/25", "symbol": "00400A", "name": "主動國泰動能高息"}, {"date": "2026/05/28", "symbol": "00997A", "name": "主動群益美國增長"}, {"date": "2026/06/05", "symbol": "00988A", "name": "主動統一全球創新"}]
up_cols = st.columns(4)
for i, etf in enumerate(upcoming_list):
    with up_cols[i]:
        st.markdown(f"<div class='upcoming-box'><div class='upcoming-title'>🚀 掛牌/募集：{etf['date']}</div><div class='upcoming-item'>{etf['symbol']} {etf['name']}</div><div class='upcoming-price'>發行價：$15.00</div></div>", unsafe_allow_html=True)

if price_alerts:
    for alert in price_alerts:
        st.markdown(f"<div class='alert-{'high' if alert['type'] == 'high' else 'low'}'>{'🚨 突破停利高標' if alert['type'] == 'high' else '⚠️ 跌破停損低標'}：【{alert['name']}】 現價 ${alert['price']:.2f} 已{'突破' if alert['type'] == 'high' else '跌破'}設定的 ${alert['target']}！</div>", unsafe_allow_html=True)

st.markdown("### 👾 羅小翔專用：雙重雷達戰情室")
col1, col2, _ = st.columns([1, 1, 1])
with col1:
    if radar_ex:
        ex_content = "".join([f"<div style='margin-bottom: 4px; font-weight:bold;'>標的 {r['symbol']} 將於 {r['date'][5:7]}/{r['date'][8:10]} 除息 (倒數 {r['days']} 天)</div>" for r in sorted(radar_ex, key=lambda x: x['days'])])
        st.markdown(f"<div class='ex-div-box'><div class='ex-div-title'>⚡ 除息雷達提醒 ⚡</div><div class='ex-div-text'>{ex_content}</div></div>", unsafe_allow_html=True)
    else:
        current_m = datetime.today().month
        next_m = current_m + 1 if current_m < 12 else 1
        this_m_etfs = [e['symbol'].split('.')[0] for e in st.session_state.my_data['etfs'] if current_m in DIVIDEND_SCHEDULE.get(e['symbol'], [])]
        next_m_etfs = [e['symbol'].split('.')[0] for e in st.session_state.my_data['etfs'] if next_m in DIVIDEND_SCHEDULE.get(e['symbol'], [])]
        msg = f"本月 ({current_m}月) 預備除息標的：<br><span style='color:#d32f2f; font-size:16px;'>{', '.join(this_m_etfs)}</span>" if this_m_etfs else f"下個月 ({next_m}月) 預備除息標的：<br><span style='color:#d32f2f; font-size:16px;'>{', '.join(next_m_etfs)}</span>" if next_m_etfs else "近期無表定除息標的"
        st.markdown(f"<div class='ex-div-box' style='background-color: #f4f6f8; border: 1.5px dashed #adb5bd;'><div class='ex-div-title' style='color: #6c757d;'>📡 預測雷達</div><div class='ex-div-text' style='color: #495057;'>{msg}</div></div>", unsafe_allow_html=True)

with col2:
    if radar_pay:
        pay_content = "".join([f"<div style='margin-bottom: 4px; font-weight:bold;'>標的 {r['symbol']} 股息 ${r['amount']:,.0f} 於 {r['date'][5:7]}/{r['date'][8:10]} 入帳 (倒數 {r['days']} 天)！</div>" for r in sorted(radar_pay, key=lambda x: x['days'])])
        st.markdown(f"<div class='pay-div-box'><div class='pay-div-title'>💰 領息雷達提醒 💰</div><div class='pay-div-text'>{pay_content}</div></div>", unsafe_allow_html=True)
    else: 
        st.markdown(f"<div class='pay-div-box' style='background-color: #fafafa; border: 1.5px dashed #ddd;'><div class='pay-div-title' style='color: #888;'>💰 領息雷達提醒 💰</div><div class='pay-div-text' style='color:#666;'>目前無 20 天內領息雷達提示</div></div>", unsafe_allow_html=True)

total_net_profit = df['損益'].sum() if not df.empty else 0
r_total = (total_net_profit / g_cost * 100) if g_cost != 0 else 0
today_pct = (g_today_pnl / (g_mkt - g_today_pnl) * 100) if (g_mkt - g_today_pnl) != 0 else 0
current_month_num = datetime.today().month
current_month_div_amount = monthly_calendar[current_month_num]["amount"]
div_sources = monthly_calendar[current_month_num]["sources"]

st.markdown(f"""
<div class="triple-box">
    <div class="triple-col">
        <div class="triple-title">今日損益</div>
        <div class="{'triple-val-r' if g_today_pnl >= 0 else 'triple-val-g'}">{f"+{g_today_pnl:,.0f}" if g_today_pnl >= 0 else f"{g_today_pnl:,.0f}"}</div>
        <div class="{'triple-pct-r' if g_today_pnl >= 0 else 'triple-pct-g'}">{f"+{today_pct:.2f}%" if today_pct >= 0 else f"{today_pct:.2f}%"}</div>
    </div>
    <div class="triple-col">
        <div class="triple-title">累積預估淨損益</div>
        <div class="{'triple-val-r' if total_net_profit >= 0 else 'triple-val-g'}">{f"+{total_net_profit:,.0f}" if total_net_profit >= 0 else f"{total_net_profit:,.0f}"}</div>
        <div class="{'triple-pct-r' if total_net_profit >= 0 else 'triple-pct-g'}">{f"+{r_total:.2f}%" if r_total >= 0 else f"{r_total:.2f}%"}</div>
    </div>
    <div class="triple-col flash-gold-box">
        <div class="triple-title" style="color: #b48608; margin-bottom: 5px;">⚡ {current_month_num} 月預估領息總額</div>
        <div class="triple-val-gold">${current_month_div_amount:,.0f}</div>
        <div class="triple-sub-gold">{'來自：' + '、'.join([s.split(' ')[0] for s in div_sources]) if div_sources else '本月無現金流入預定'}</div>
    </div>
</div>
""", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
c1.metric("股票總市值", f"${g_mkt:,.0f}")
c2.metric("投資總成本", f"${g_cost:,.0f}")
c3.metric("全年預估總領息", f"${sum([monthly_calendar[m]['amount'] for m in range(1, 13)]):,.0f}")
st.write("---")

us_icon = "🔴" if "us" in macro_data and sum(1 for v in macro_data["us"].values() if v['diff'] >= 0) >= len(macro_data["us"])/2 else "🟢"
tw_icon = "🔴" if "tw" in macro_data and sum(1 for v in macro_data["tw"].values() if v['diff'] >= 0) >= len(macro_data["tw"])/2 else "🟢"

r1 = st.columns(3)
r1[0].button(f"🔽 收起美股 {us_icon}" if st.session_state.show_us else f"{us_icon} 展開美股", on_click=toggle_us, type="primary" if st.session_state.show_us else "secondary", use_container_width=True)
r1[1].button(f"🔽 收起台股 {tw_icon}" if st.session_state.show_tw else f"{tw_icon} 展開台股", on_click=toggle_tw, type="primary" if st.session_state.show_tw else "secondary", use_container_width=True)
r1[2].button("🔽 收起領息日曆" if st.session_state.show_calendar else "📅 展開領息日曆", on_click=toggle_calendar, type="primary" if st.session_state.show_calendar else "secondary", use_container_width=True)

r2 = st.columns(3)
r2[0].button("🔽 收起除權息" if st.session_state.show_div_db else "📂 展開除權息", on_click=toggle_div_db, type="primary" if st.session_state.show_div_db else "secondary", use_container_width=True)
r2[1].button("🔽 收控股價監控" if st.session_state.show_tech else "📡 展開股價監控", on_click=toggle_tech, type="primary" if st.session_state.show_tech else "secondary", use_container_width=True)
r2[2].button("🔽 收起持股明細" if st.session_state.show_holdings else "📊 展開持股明細", on_click=toggle_holdings, type="primary" if st.session_state.show_holdings else "secondary", use_container_width=True)

r3 = st.columns(3)
r3[0].button("🔽 收起成份股" if st.session_state.show_constituents else "🧩 展開成份股", on_click=toggle_constituents, type="primary" if st.session_state.show_constituents else "secondary", use_container_width=True) 
r3[1].button("🔽 收起質押專區" if st.session_state.show_pledge else "🏦 展開質押專區", on_click=toggle_pledge, type="primary" if st.session_state.show_pledge else "secondary", use_container_width=True) 
r3[2].button("🔽 收起機密面板" if st.session_state.show_secret else "🔐 展開機密面板", on_click=toggle_secret, type="primary" if st.session_state.show_secret else "secondary", use_container_width=True) 
st.write("---")

if st.session_state.show_us and "us" in macro_data:
    st.markdown("#### 🌏 關鍵美股指標"); render_macro_cards(macro_data["us"], "us"); st.write("")
if st.session_state.show_tw and "tw" in macro_data:
    st.markdown("#### 🇹🇼 關鍵台股點數"); render_macro_cards(macro_data["tw"], "tw"); st.write("---")

if st.session_state.show_calendar:
    st.markdown("#### 📅 1~12月 預估領息日曆")
    selected_month = int(st.selectbox("請選擇您想查詢的月份：", [f"{m} 月" for m in range(1, 13)], index=datetime.today().month - 1).replace(" 月", ""))
    data = monthly_calendar[selected_month]
    st.columns([1, 2, 1])[1].markdown(f"<div class='month-card'><div class='month-title'>{selected_month} 月預估領息</div><div class='month-amount'>${data['amount']:,.0f}</div><div class='month-sources'>ETF 來源：{'、'.join(data['sources']) if data['sources'] else '無'}</div></div>", unsafe_allow_html=True)
    st.write("---")

if st.session_state.show_div_db:
    st.columns([7, 3])[0].markdown("#### 📚 專屬 ETF 與自選股 除權息時程總覽")
    if st.columns([7, 3])[1].button("🔄 強制抓取最新公告", type="primary", use_container_width=True):
        st.cache_data.clear(); st.session_state.update_success = "已強制重新抓取！"; st.rerun()

    db_list = [{"類別": "💼 庫存", "ETF 名稱": row['名稱'], "基金規模": row.get('基金規模', '系統無資料'), "配息頻率": "月配息" if len(DIVIDEND_SCHEDULE.get(row['代號'], []))==12 else "季配息" if len(DIVIDEND_SCHEDULE.get(row['代號'], []))==4 else "其他", "配息月份": "、".join(map(str, DIVIDEND_SCHEDULE.get(row['代號'], []))) + " 月" if DIVIDEND_SCHEDULE.get(row['代號'], []) else "-", "狀態": row['狀態'], "除息日": row['最新公告除息日'], "發放日": row['預估發放日'], "每股金額": f"${row['每股配息']:.3f}", "最新填息紀錄": row['最新填息紀錄']} for _, row in df.iterrows()] if not df.empty else []
    df_wl_div = fetch_watchlist_dividend(st.session_state.my_data.get('watchlist', []), st.session_state.my_data.get('custom_divs', {}))
    final_div_df = pd.concat([pd.DataFrame(db_list), df_wl_div], ignore_index=True) if db_list and not df_wl_div.empty else df_wl_div if not df_wl_div.empty else pd.DataFrame(db_list)
    
    st.dataframe(final_div_df, use_container_width=True, hide_index=True) if not final_div_df.empty else st.info("目前尚無資料可顯示。")
        
    with st.expander("🛠️ 手動配息覆蓋面板 (修正 Yahoo 資料庫延遲)", expanded=False):
        edited_custom = st.data_editor(pd.DataFrame([{"代號": k, "每股配息": v['v'], "除息日": v['d'], "發放日": v['p']} for k, v in st.session_state.my_data.get('custom_divs', {}).items()]), num_rows="dynamic", use_container_width=True)
        if st.button("💾 儲存手動覆蓋資料並套用", type="primary"):
            st.session_state.my_data['custom_divs'] = {str(row['代號']).strip() + (".TW" if not str(row['代號']).strip().endswith(".TW") else ""): {"v": float(row['每股配息']) if pd.notna(row['每股配息']) else 0.0, "d": str(row['除息日']) if pd.notna(row['除息日']) else "", "p": str(row['發放日']) if pd.notna(row['發放日']) else ""} for _, row in edited_custom.iterrows() if str(row['代號']).strip() and str(row['代號']) != "nan"}
            save_to_json(st.session_state.my_data); st.cache_data.clear(); st.rerun()
    st.write("---")

if st.session_state.show_tech:
    if not df.empty:
        st.markdown("#### 📡 庫存價格區間監控與技術分析")
        
        try: styled_df_tech = df_tech.style.map(color_profit_loss, subset=['今日損益', '今日漲跌幅']).map(color_months, subset=['配息月份'])
        except AttributeError: styled_df_tech = df_tech.style.applymap(color_profit_loss, subset=['今日損益', '今日漲跌幅']).applymap(color_months, subset=['配息月份'])

        st.dataframe(styled_df_tech, use_container_width=True, hide_index=True)

        st.markdown("#### 💰 近一個月每日損益金額")
        try:
            tickers = [item['symbol'] for item in st.session_state.my_data['etfs']]
            if tickers:
                hist_data = pd.DataFrame(yf.download(tickers, period="1mo")['Close'])
                if len(tickers) == 1: hist_data.columns = [tickers[0]]
                diff_data = hist_data.diff().fillna(0)
                
                pnl_df = pd.DataFrame(index=diff_data.index)
                for item in st.session_state.my_data['etfs']:
                    if item['symbol'] in diff_data.columns: pnl_df[item['name']] = diff_data[item['symbol']] * (item['holdings'] * 1000)
                
                pnl_df = pnl_df.sort_index(ascending=False)
                pnl_df.index = pnl_df.index.strftime('%Y-%m-%d')
                
                pnl_df_t = pnl_df.T
                pnl_df_t.loc['📊 每日合計'] = pnl_df_t.sum()
                pnl_df_t = pnl_df_t.reset_index().rename(columns={'index': '股票代號'})
                
                st.dataframe(pnl_df_t.style.apply(color_pnl, axis=None).format(lambda x: f"+${x:,.0f}" if isinstance(x, (int, float)) and x > 0 else (f"-${abs(x):,.0f}" if isinstance(x, (int, float)) and x < 0 else ("$0" if isinstance(x, (int, float)) else x))), use_container_width=True, hide_index=True)
        except Exception as e: st.error(f"資料載入失敗: {e}")

    else: st.info("目前無庫存標的。")
    st.write("---")
    
    st.markdown("#### 👀 自選股觀察清單")
    col_w1, col_w2, col_w3 = st.columns([2, 2, 1])
    with col_w1: st.text_input("輸入代碼 (不需手打 .TW)", key="add_sym_wl", on_change=auto_fill_wl_name)
    with col_w2: st.text_input("自定義名稱", key="add_name_wl")
    with col_w3: st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True); st.button("➕ 加入名單", on_click=add_new_wl, use_container_width=True)

    wl_df = fetch_watchlist_data(st.session_state.my_data.get('watchlist', []))
    if not wl_df.empty:
        try: styled_wl = wl_df.style.map(color_diff, subset=['漲跌', '漲跌幅'])
        except AttributeError: styled_wl = wl_df.style.applymap(color_diff, subset=['漲跌', '漲跌幅'])
        st.dataframe(styled_wl, use_container_width=True, hide_index=True)
        
        with st.expander("🗑️ 管理與刪除自選股"):
            for i, item in enumerate(st.session_state.my_data['watchlist']):
                cols = st.columns([3, 1, 6])
                cols[0].markdown(f"📍 **{item['name']}**"); cols[1].button("刪除", key=f"del_wl_{i}", on_click=delete_wl, args=(i,), use_container_width=True)
    st.write("---")

if st.session_state.show_holdings:
    if not df.empty:
        st.markdown("#### 📊 持股動態明細")
        for _, row in df.iterrows():
            with st.expander(f"💎 {row['名稱']} | 預估淨報酬: :{'red' if row['損益'] >= 0 else 'green'}[{row['報酬率']:+.2f}%]", expanded=True):
                col_l, col_m, col_r = st.columns(3)
                col_l.write(f"張數: **{row['張數']}**\n現價: **{row['現價']:.2f}**\n均價: {row['均價']:.2f}")
                col_m.markdown(f"市值: **${row['市值']:,.0f}**\n預估淨利: :{'red' if row['損益'] >= 0 else 'green'}[**${row['損益']:,.0f}**]")
                col_r.markdown(f"單次領息估算: :orange[**${row['單次預估領息']:,.0f}**]\n📅 最新除息日: {row['最新公告除息日']} ({row['狀態']})")
    else: st.info("⚠️ 目前尚無持股資料。")
    st.write("---")

if st.session_state.show_constituents:
    if not df.empty:
        st.markdown("#### 🧩 專屬庫存 ETF 核心成分股佔比")
        c_cols = st.columns(3)
        for idx, item in enumerate(st.session_state.my_data['etfs']):
            df_comp = pd.DataFrame(ETF_CONSTITUENTS_DB.get(item['symbol'], [{"name": "其他成分股", "weight": 100.0}]))
            df_comp['label'] = df_comp['weight'].apply(lambda w: f"{w:.1f}%" if w >= 2.0 else "")
            
            base = alt.Chart(df_comp).encode(theta=alt.Theta("weight:Q", stack=True), color=alt.Color("name:N", sort=alt.EncodingSortField(field="weight", op="sum", order="descending"), legend=alt.Legend(title=None, orient="right")))
            chart = alt.layer(base.mark_arc(outerRadius=100, innerRadius=0), base.mark_text(radius=125, size=13, fontWeight="bold").encode(text="label:N")).properties(height=280).configure_view(strokeWidth=0)
            
            with c_cols[idx % 3]:
                st.markdown(f"<div style='font-weight:900; color:#1e3c72; font-size:16px; margin-bottom:5px;'>🛡️ {item['name']}</div>", unsafe_allow_html=True)
                st.altair_chart(chart, use_container_width=True)
    st.write("---")

if st.session_state.show_pledge:
    if not df.empty:
        st.markdown("#### 🏦 股票質押專區 (維持率監控)")
        pledge_data = st.session_state.my_data['pledge']
        
        col_b1, col_b2, col_b3 = st.columns([2, 2, 1.5])
        borrowed_input = col_b1.number_input("💸 已借款總額", min_value=0, value=int(pledge_data.get('borrowed_amount', 0)), step=10000)
        months_input = col_b2.number_input("📅 合約期數", min_value=1, max_value=18, value=int(pledge_data.get('months_passed', 1)))
        col_b3.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        if col_b3.button("💾 儲存", use_container_width=True):
            st.session_state.my_data['pledge']['borrowed_amount'], st.session_state.my_data['pledge']['months_passed'] = borrowed_input, months_input
            save_to_json(st.session_state.my_data); st.rerun()

        pledge_df_list, total_pledge_mkt, total_borrowable, borrowed = [], 0, 0, st.session_state.my_data['pledge'].get('borrowed_amount', 0)
        for item in st.session_state.my_data['etfs']:
            curr_p = df[df['代號'] == item['symbol']]['現價'].values[0] if not df[df['代號'] == item['symbol']].empty else 0
            p_mkt = item.get('pledged_shares', 0.0) * 1000 * curr_p
            total_pledge_mkt += p_mkt; total_borrowable += p_mkt * 0.6
            pledge_df_list.append({"ETF 名稱": item['name'], "總庫存 (張)": item['holdings'], "質押張數": item.get('pledged_shares', 0.0), "現價": round(curr_p, 2), "質押市值 (元)": round(p_mkt, 0), "可借上限 (60%)": round(p_mkt * 0.6, 0)})
            
        margin_ratio = (total_pledge_mkt / borrowed * 100) if borrowed > 0 else 0
        col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
        col_m1.metric("擔保品總市值", f"${total_pledge_mkt:,.0f}"); col_m2.metric("🎯 總可借款上限", f"${total_borrowable:,.0f}")
        col_m3.metric("💸 已借入總額", f"${borrowed:,.0f}"); col_m4.metric("💰 每月利息(3.25%)", f"${(borrowed * 0.0325 / 12):,.0f}")
        col_m5.metric("維持率", f"{margin_ratio:.2f}%" if borrowed > 0 else "0.00%", "危險" if margin_ratio > 0 and margin_ratio < 130 else "正常")
        
        st.markdown(f"**📜 合約進度：第 {st.session_state.my_data['pledge'].get('months_passed', 1)} 個月 / 共 18 個月**")
        st.progress(st.session_state.my_data['pledge'].get('months_passed', 1) / 18.0)

        edited_pledge = st.data_editor(pd.DataFrame(pledge_df_list), column_config={"質押張數": st.column_config.NumberColumn(format="%.1f")}, disabled=["ETF 名稱", "總庫存 (張)", "現價", "質押市值 (元)", "可借上限 (60%)"], use_container_width=True, hide_index=True)
        
        has_p_changes = False
        for _, row in edited_pledge.iterrows():
            for etf in st.session_state.my_data['etfs']:
                if etf['name'] == row['ETF 名稱'] and etf.get('pledged_shares', 0.0) != row['質押張數']:
                    etf['pledged_shares'] = row['質押張數']; has_p_changes = True; break
        if has_p_changes: save_to_json(st.session_state.my_data); st.rerun()
    st.write("---")

if st.session_state.show_secret:
    st.markdown("<div class='secret-box'>", unsafe_allow_html=True)
    st.markdown("#### 🔐 總司令專屬機密戰情區")
    if not st.session_state.is_unlocked:
        if st.button("解鎖 🔓") if st.text_input("輸入密碼：", type="password") == "1030" else False:
            st.session_state.is_unlocked = True; st.rerun()
    else:
        st.success("✅ 機密面板已解鎖！系統將自動推進期數。")
        
        # 信貸戰情
        st.markdown("##### 💳 核心信貸還款戰情 (每月 $15,000 / 共84期)")
        new_paid = st.number_input("🤖 自動推進期數：", min_value=1, max_value=84, value=int(st.session_state.my_data['loan']['months_paid']))
        if new_paid != st.session_state.my_data['loan']['months_paid']: st.session_state.my_data['loan']['months_paid'] = new_paid; save_to_json(st.session_state.my_data); st.rerun()
        
        lc1, lc2, lc3 = st.columns(3)
        lc1.metric("信貸總額", f"${(84 * 15000):,.0f}"); lc2.metric("已繳納", f"${(new_paid * 15000):,.0f}"); lc3.metric("剩餘未繳", f"${((84 - new_paid) * 15000):,.0f}")
        st.progress(new_paid / 84)
        
        st.markdown("##### 🤝 應收帳款戰情：彰銀信貸 (共 60 期)")
        chb_amount = st.number_input("設定每月應還：", value=int(st.session_state.my_data['loan_chb'].get('regular_amount', 0)), step=1000)
        new_paid_chb = st.number_input("🤖 已還期數：", min_value=0, max_value=60, value=int(st.session_state.my_data['loan_chb']['months_paid']))
        if chb_amount != st.session_state.my_data['loan_chb'].get('regular_amount', 0) or new_paid_chb != st.session_state.my_data['loan_chb']['months_paid']:
            st.session_state.my_data['loan_chb']['regular_amount'], st.session_state.my_data['loan_chb']['months_paid'] = chb_amount, new_paid_chb
            save_to_json(st.session_state.my_data); st.rerun()
            
        cc1, cc2, cc3 = st.columns(3)
        cc1.metric("彰銀信貸總額", f"${(60 * chb_amount):,.0f}"); cc2.metric("對方已還", f"${(new_paid_chb * chb_amount):,.0f}"); cc3.metric("剩餘未還", f"${((60 - new_paid_chb) * chb_amount):,.0f}")
        
        # 收支紀錄
        st.markdown("##### 💰 個人獨立收支簿")
        pf_data = st.session_state.my_data['personal_finance']
        col_type, col_ex1, col_ex2, col_ex3, col_ex4 = st.columns([1.5, 2, 3, 2, 2])
        rec_type = col_type.selectbox("類型", ["支出", "收入"])
        rec_date = col_ex1.date_input("日期", datetime.today())
        rec_item = col_ex2.text_input("項目", placeholder="例如: 買咖啡")
        rec_amount = col_ex3.number_input("金額 (元)", min_value=0, step=10, value=0)
        col_ex4.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        if col_ex4.button("➕ 記一筆", use_container_width=True) and rec_amount > 0 and rec_item:
            pf_data['expenses' if rec_type == "支出" else 'incomes'].append({"date": rec_date.strftime("%Y-%m-%d"), "item": rec_item, "amount": rec_amount})
            save_to_json(st.session_state.my_data); st.rerun()

        curr_str = datetime.today().strftime("%Y-%m")
        curr_expenses, curr_incomes = [e for e in pf_data.get('expenses', []) if e['date'].startswith(curr_str)], [i for i in pf_data.get('incomes', []) if i['date'].startswith(curr_str)]
        rem_budget = sum(i['amount'] for i in curr_incomes) - sum(e['amount'] for e in curr_expenses)

        bc1, bc2, bc3 = st.columns(3)
        bc1.metric("本月收入", f"${sum(i['amount'] for i in curr_incomes):,.0f}"); bc2.metric("本月支出", f"${sum(e['amount'] for e in curr_expenses):,.0f}"); bc3.metric("可用餘額", f"${rem_budget:,.0f}")

        tab_in, tab_ex = st.tabs(["💰 收入明細", "💸 支出明細"])
        with tab_in:
            if curr_incomes:
                df_in = pd.DataFrame(curr_incomes).rename(columns={"date": "日期", "item": "項目", "amount": "金額"})
                df_in.insert(0, "🗑️ 刪除", False)
                if st.button("💾 確認更新收入", use_container_width=True):
                    pf_data['incomes'] = [i for i in pf_data['incomes'] if not i['date'].startswith(curr_str)] + [{"date": str(r['日期']), "item": str(r['項目']), "amount": int(r['金額'])} for _, r in st.data_editor(df_in, key="in_e").iterrows() if not r.get("🗑️ 刪除", False)]
                    save_to_json(st.session_state.my_data); st.rerun()
                else: st.data_editor(df_in, hide_index=True)
        with tab_ex:
            if curr_expenses:
                df_ex = pd.DataFrame(curr_expenses).rename(columns={"date": "日期", "item": "項目", "amount": "金額"})
                df_ex.insert(0, "🗑️ 刪除", False)
                if st.button("💾 確認更新支出", use_container_width=True):
                    pf_data['expenses'] = [e for e in pf_data['expenses'] if not e['date'].startswith(curr_str)] + [{"date": str(r['日期']), "item": str(r['項目']), "amount": int(r['金額'])} for _, r in st.data_editor(df_ex, key="ex_e").iterrows() if not r.get("🗑️ 刪除", False)]
                    save_to_json(st.session_state.my_data); st.rerun()
                else: st.data_editor(df_ex, hide_index=True)

        st.markdown(f"<div class='net-worth-box'><h3>👑 總司令大局淨資產</h3><h1>${(g_mkt - rem_budget + ((60 - new_paid_chb) * chb_amount)):,.0f}</h1></div>", unsafe_allow_html=True)
        if st.button("🔐 重新上鎖", use_container_width=True): st.session_state.is_unlocked = False; st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    st.write("---")

with st.expander("💰 買賣損益試算器", expanded=False):
    if not df.empty:
        calc_options = [row['名稱'] for _, row in df.iterrows()]
        if 'calc_selected_etf' not in st.session_state: st.session_state.calc_selected_etf = calc_options[0]
        if 'calc_trade_type' not in st.session_state: st.session_state.calc_trade_type = "賣出 (計算已實現損益)"
        if 'calc_trade_shares' not in st.session_state: st.session_state.calc_trade_shares = 1.0
        
        st.selectbox("選擇庫存：", calc_options, key="calc_selected_etf")
        target_row = df[df['名稱'] == st.session_state.calc_selected_etf].iloc[0]
        st.info(f"📍 庫存：{target_row['張數']} 張 | 均價：${target_row['均價']:.2f} | 即時現價：${target_row['現價']:.2f}")
        
        c1, c2 = st.columns(2)
        c1.radio("動作：", ["賣出 (計算已實現損益)", "買進 (計算買入成本與新均價)"], key="calc_trade_type")
        c2.number_input("張數", min_value=0.1, step=1.0, key="calc_trade_shares")
        
        if st.session_state.calc_trade_type == "賣出 (計算已實現損益)":
            realized_profit = (target_row['現價'] - target_row['均價']) * min(st.session_state.calc_trade_shares, target_row['張數']) * 1000
            st.write(f"📝 預估已實現損益：**${realized_profit:,.0f}**")
            st.button("💾 確認賣出", on_click=execute_trade, type="primary")
        else:
            new_shares = target_row['張數'] + st.session_state.calc_trade_shares
            new_cost = ((target_row['均價'] * target_row['張數']) + (target_row['現價'] * st.session_state.calc_trade_shares)) / new_shares
            st.write(f"📝 買入花費：**${(target_row['現價'] * st.session_state.calc_trade_shares * 1000):,.0f}** | 全新均價：**${new_cost:.2f}**")
            st.button("💾 確認買進", on_click=execute_trade, type="primary")
    else: st.warning("請先新增庫存")

st.write("---")

bot_c1, bot_c2, bot_c3 = st.columns([2, 5, 3])
if bot_c1.button("🔄 重整股價", use_container_width=True): st.cache_data.clear(); st.rerun()

with bot_c2.expander("⚙️ 標的管理 (庫存與資料備份)", expanded=True):
    st.markdown("#### ➕ 新增庫存標的")
    st.text_input("輸入代碼 (不需手打 .TW)", key="add_sym_bot", on_change=auto_fill_etf_name)
    st.text_input("自定義名稱", key="add_name_bot")
    a1, a2 = st.columns(2)
    a1.number_input("張數", step=1.0, key="add_h_bot")
    a2.number_input("均價", step=0.1, key="add_c_bot")
    st.button("確認新增", key="btn_add_bot", use_container_width=True, on_click=add_new_etf_bot)

    if st.session_state.my_data['etfs']:
        st.write("---")
        st.markdown("#### 📝 修改與刪除")
        for i, item in enumerate(st.session_state.my_data['etfs']):
            with st.expander(f"📍 {item['name']}"):
                e1, e2 = st.columns(2)
                e1.number_input("張數", value=float(item['holdings']), step=1.0, key=f"edit_h_{i}", on_change=save_edits)
                e2.number_input("均價", value=float(item['cost']), step=0.1, key=f"edit_c_{i}", on_change=save_edits)
                st.button(f"🗑️ 刪除", key=f"del_{i}", on_click=delete_etf, args=(i,), use_container_width=True)
        st.button("💾 儲存上方修改", use_container_width=True, type="secondary", on_click=save_edits)
    
    st.write("---")
    st.markdown("#### 🛡️ 資料庫備份與還原 (改 Code 前必備)")
    
    # 下載備份
    json_string = json.dumps(st.session_state.my_data, ensure_ascii=False, indent=4)
    st.download_button(
        label="📥 下載完整資料庫備份 (settings.json)",
        data=json_string,
        file_name="settings.json",
        mime="application/json",
        use_container_width=True,
        type="primary"
    )
    
    # 上傳還原
    uploaded_file = st.file_uploader("📂 如果資料遺失，請在此上傳備份檔還原", type="json")
    if uploaded_file is not None:
        if st.button("🚨 確認覆蓋並還原資料", use_container_width=True):
            try:
                restored_data = json.load(uploaded_file)
                st.session_state.my_data = restored_data
                save_to_json(restored_data)
                st.success("✅ 資料庫已成功還原！正在重新載入...")
                time.sleep(1)
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"還原失敗，檔案格式可能錯誤：{e}")

with bot_c3:
    st.markdown("<div class='auto-refresh-box'>#### ⚡ 自動更新<br><span style='font-size:12px;color:gray;'>每 5 秒重整即時股價</span></div>", unsafe_allow_html=True)
    if st.radio("即時更新", ["❌ 關閉", "✅ 開啟"], horizontal=True, label_visibility="collapsed") == "✅ 開啟":
        time.sleep(5); st.cache_data.clear(); st.rerun()
