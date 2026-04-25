import streamlit as st
from FinMind.data import DataLoader
import pandas as pd
import time
from datetime import datetime

# ==========================================
# 1. 設定 Token (請確保引號內正確)
# ==========================================
MY_FINMIND_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiaG91eWkiLCJlbWFpbCI6ImhvdXlpZmFzdGVuZXJAZ21haWwuY29tIn0.Z4a9jwT26acoN-OEBjbFu_VDneVrmN9iSpC3YxigBDg"

st.set_page_config(page_title="台指期戰情室", layout="centered")
st.title("🏹 台指期量能決策系統")

# 建立顯示容器
placeholder = st.empty()

def get_decision():
    dl = DataLoader()
    try:
        # 抓取即時資料
        df = dl.taiwan_futures_tick(
            futures_id="TX",
            date=datetime.now().strftime("%Y-%m-%d"),
            token=MY_FINMIND_TOKEN
        )
    except:
        return "📡 連線異常，等待數據中...", None, None, None

    if df is None or df.empty:
        return "📡 目前非開盤時間，或正在等待數據...", None, None, None

    # --- 核心邏輯：手動計算力道 ---
    recent = df.tail(50)
    out_vol = recent[recent['diff'] > 0]['volume'].sum()
    in_vol = recent[recent['diff'] < 0]['volume'].sum()
    total_vol = out_vol + in_vol
    delta_ratio = out_vol / total_vol if total_vol > 0 else 0.5
    
    price = df.iloc[-1]['close']
    
    # 動態失效時間公式： $T_{timeout} = \frac{15}{V_{momentum}}$
    if delta_ratio > 0.6:
        res = "🔥 【短多預測】"
        msg = f"買氣積極 (外盤 {delta_ratio:.1%})"
        advice = "建議沿支撐進場，限時跌破則撤。"
    else:
        res = "⚖️ 【觀望/偏空】"
        msg = "目前力道均衡，無明顯攻擊訊號。"
        advice = "建議暫時觀望，等量能放大。"

    return res, msg, advice, price

# --- 循環執行 ---
while True:
    res, msg, advice, price = get_decision()
    with placeholder.container():
        if price:
            st.metric("台指期當前價", f"{price:.0f}")
            st.error(f"### {res}")
            st.info(f"**戰略分析：** {msg}")
            st.success(f"**動作建議：** {advice}")
        else:
            st.warning(res)
    time.sleep(15)
