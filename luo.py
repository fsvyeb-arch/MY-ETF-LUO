# --- 🎯 抓取自選股資料 ---
@st.cache_data(ttl=10)
def fetch_watchlist_data(wl_list):
    if not wl_list: return pd.DataFrame()
    results = []
    
    # --- 🚀 批量獲取富果 API 即時報價 ---
    fugle_quotes = {}
    tw_ids = [item['symbol'].split('.')[0] for item in wl_list]
    
    if 'FUGLE_API_KEY' in globals() and FUGLE_API_KEY and FUGLE_API_KEY != "請在此填入您的富果API金鑰":
        headers = {"X-API-KEY": FUGLE_API_KEY}
        for stock_id in set(tw_ids):
            try:
                url = f"https://api.fugle.tw/marketdata/v1.0/stock/intraday/quote/{stock_id}"
                res = requests.get(url, headers=headers, timeout=2)
                if res.status_code == 200:
                    fugle_quotes[stock_id] = res.json()
            except:
                continue

    for item in wl_list:
        sym = item['symbol']
        stock_id = sym.replace('.TW', '')
        
        # 預設變數，避免當機
        curr_p, prev_close = 0, 0
        
        # --- 1. 先嘗試用 yfinance 抓取 (作為雙重備援) ---
        try:
            tk = yf.Ticker(sym)
            hist = tk.history(period="2d")
            if not hist.empty and 'Close' in hist.columns:
                rt_curr = tk.fast_info.get('lastPrice')
                curr_p = rt_curr if rt_curr is not None else float(hist['Close'].iloc[-1])
                rt_prev = tk.fast_info.get('previousClose')
                prev_close = rt_prev if rt_prev is not None else float(hist['Close'].iloc[-2] if len(hist) >= 2 else curr_p)
        except Exception: 
            pass

        # --- 2. 🌟 富果 API 精準覆蓋 (零延遲現價與平盤價) ---
        fg_data = fugle_quotes.get(stock_id, {})
        if fg_data:
            # 取得即時現價
            last_trade = fg_data.get('lastTrade', {})
            if last_trade and last_trade.get('price') is not None: 
                curr_p = float(last_trade['price'])
            elif fg_data.get('closePrice') is not None: 
                curr_p = float(fg_data['closePrice'])
            
            # 取得平盤價/昨收價
            if fg_data.get('referencePrice') is not None: 
                prev_close = float(fg_data['referencePrice'])
            elif fg_data.get('previousClose') is not None: 
                prev_close = float(fg_data['previousClose'])
                
        # 確保兩邊 API 都徹底失效時，才略過該檔標的
        if curr_p == 0:
            continue
            
        diff = curr_p - prev_close
        pct = (diff / prev_close * 100) if prev_close else 0
        status_light = "🔴" if diff > 0 else ("🟢" if diff < 0 else "⚪")
        
        results.append({
            "代號": stock_id, "名稱": item['name'],
            "現價": round(curr_p, 2), "漲跌": round(diff, 2), "漲跌幅": f"{pct:+.2f}%", "狀態": status_light
        })
        
    return pd.DataFrame(results)
