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
# 2. 自動尋找數據 (修正登入方式)
# ==========================================
def get_latest_market_data():
    dl = DataLoader()
    # 這裡是用最新版最穩定的登入方式：先登入，再抓資料
    try:
        dl.login(token=MY_FINMIND_TOKEN)
    except:
        # 如果上面失敗，試試另一種可能的名稱 (部分版本用 api_token)
        try:
            dl.login(api_token=MY_FINMIND_TOKEN)
        except:
            pass

    for i in range(5):
        target_date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        try:
            # 💡 修正點：這裡不再傳入 token 參數，因為上面已經 login 過了
            df = dl.taiwan_futures_tick(
                futures_id="TX",
                date=target_date
            )
            if df is not None and not df.empty:
                return df, target_date, (i == 0)
        except:
            continue
    return None, None, False

# ==========================================
# 3. 畫面顯示邏輯
# ==========================================
st.title("🏹 台指期量能決策系統")
placeholder = st.empty()

while True:
    df, data_date, is_live = get_latest_market_data()
    
    with placeholder.container():
        if df is not None:
            st.success(f"📊 數據日期: {data_date} ({'即時' if is_live else '盤後'})")
            
            # 核心邏輯：計算內外盤
            recent = df.tail(100)
            out_vol = recent[recent['diff'] > 0]['volume'].sum()
            in_vol = recent[recent['diff'] < 0]['volume'].sum()
            total_vol = out_vol + in_vol
            delta_ratio = out_vol / total_vol if total_vol > 0 else 0.5
            price = df.iloc[-1]['close']
            
            st.metric("台指期當前點位", f"{price:.0f}")
            
            if delta_ratio > 0.6:
                st.error(f"### 🔥 【短多預測】：買氣積極 ({delta_ratio:.1%})")
            elif delta_ratio < 0.4:
                st.success(f"### 🩸 【短空預測】：賣壓轉強 ({1-delta_ratio:.1%})")
            else:
                st.warning(f"### ⚖️ 【區間震盪】：多空交戰中")
                
            st.divider()
            st.caption(f"數據最後更新時間：{df.iloc[-1]['time']}")
        else:
            st.error("❌ 無法獲取數據。請檢查 Token 是否正確，或稍後再試。")
            
    time.sleep(30 if is_live else 3600)
