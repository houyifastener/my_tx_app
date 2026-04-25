import streamlit as st
from FinMind.data import DataLoader
import pandas as pd
import time
from datetime import datetime, timedelta

# ==========================================
# 1. 設定 Token
# ==========================================
MY_FINMIND_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiaG91eWkiLCJlbWFpbCI6ImhvdXlpZmFzdGVuZXJAZ21haWwuY29tIn0.Z4a9jwT26acoN-OEBjbFu_VDneVrmN9iSpC3YxigBDg"

st.set_page_config(page_title="台指期戰情室", layout="centered")

# ==========================================
# 2. 自動尋找「最後有資料」的日期
# ==========================================
def get_latest_market_data():
    dl = DataLoader()
    # 從今天開始往回找 5 天，確保能跨過週末或連假
    for i in range(5):
        target_date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        try:
            df = dl.taiwan_futures_tick(
                futures_id="TX",
                date=target_date,
                token=MY_FINMIND_TOKEN
            )
            if df is not None and not df.empty:
                # 判斷是否為「今天」的資料
                is_live = target_date == datetime.now().strftime("%Y-%m-%d")
                return df, target_date, is_live
        except:
            continue
    return None, None, False

# ==========================================
# 3. 畫面邏輯
# ==========================================
placeholder = st.empty()

while True:
    df, data_date, is_live = get_latest_market_data()
    
    with placeholder.container():
        if df is not None:
            # 顯示狀態標籤
            if is_live:
                st.success(f"🟢 即時監控中 (日期: {data_date})")
            else:
                st.info(f"⚪ 盤後回顧 (最後更新: {data_date})")
            
            # --- 核心邏輯計算 ---
            recent = df.tail(100)
            out_vol = recent[recent['diff'] > 0]['volume'].sum()
            in_vol = recent[recent['diff'] < 0]['volume'].sum()
            total_vol = out_vol + in_vol
            delta_ratio = out_vol / total_vol if total_vol > 0 else 0.5
            
            price = df.iloc[-1]['close']
            
            st.metric("台指期點位", f"{price:.0f}")

            # 決策判斷
            if delta_ratio > 0.6:
                st.error(f"### 🔥 【短多預測】")
                st.write(f"戰略分析：買氣積極 (外盤 {delta_ratio:.1%})")
            elif delta_ratio < 0.4:
                st.success(f"### 🩸 【短空預測】")
                st.write(f"戰略分析：賣壓湧現 (內盤 {1-delta_ratio:.1%})")
            else:
                st.warning(f"### ⚖️ 【區間震盪】")
                st.write("戰略分析：內外盤力道均衡")

            st.divider()
            st.caption(f"數據時間：{df.iloc[-1]['time']}")
        else:
            st.error("📡 暫時無法獲取數據，請檢查 Token 或網路。")

    # 如果是即時就刷快一點，如果是盤後就每小時刷一次就好
    wait_time = 15 if is_live else 3600
    time.sleep(wait_time)
