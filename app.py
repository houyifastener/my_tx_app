import streamlit as st
from FinMind.data import DataLoader
import pandas as pd
import time
from datetime import datetime, timedelta

# ==========================================
# 1. 設定 Token (陳大哥，請再次確認這裡的 Token 是否正確)
# ==========================================
MY_FINMIND_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiaG91eWkiLCJlbWFpbCI6ImhvdXlpZmFzdGVuZXJAZ21haWwuY29tIn0.Z4a9jwT26acoN-OEBjbFu_VDneVrmN9iSpC3YxigBDg"

st.set_page_config(page_title="台指期戰情室", layout="centered")

# ==========================================
# 2. 自動尋找數據 (加上錯誤訊息回報)
# ==========================================
def get_latest_market_data():
    dl = DataLoader()
    last_error = ""
    for i in range(5):
        target_date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        try:
            df = dl.taiwan_futures_tick(
                futures_id="TX",
                date=target_date,
                token=MY_FINMIND_TOKEN
            )
            if df is not None and not df.empty:
                return df, target_date, (i == 0), ""
            else:
                last_error = f"{target_date} 查無資料"
        except Exception as e:
            last_error = str(e)
            continue
    return None, None, False, last_error

# ==========================================
# 3. 畫面顯示
# ==========================================
df, data_date, is_live, error_msg = get_latest_market_data()

if df is not None:
    st.success(f"📊 數據日期: {data_date} ({'即時' if is_live else '盤後'})")
    
    # 核心邏輯 (計算內外盤)
    recent = df.tail(100)
    out_vol = recent[recent['diff'] > 0]['volume'].sum()
    in_vol = recent[recent['diff'] < 0]['volume'].sum()
    total_vol = out_vol + in_vol
    delta_ratio = out_vol / total_vol if total_vol > 0 else 0.5
    price = df.iloc[-1]['close']
    
    st.metric("台指期收盤/現價", f"{price:.0f}")
    
    if delta_ratio > 0.6:
        st.error(f"### 🔥 【短多預測】")
        st.write(f"分析：外盤力道強勁 ({delta_ratio:.1%})")
    elif delta_ratio < 0.4:
        st.success(f"### 🩸 【短空預測】")
        st.write(f"分析：賣壓湧現 ({1-delta_ratio:.1%})")
    else:
        st.warning(f"### ⚖️ 【區間震盪】")
        st.write("分析：多空交戰中")
        
    st.divider()
    st.caption(f"最後成交時間：{df.iloc[-1]['time']}")

else:
    st.error("❌ 系統目前無法獲取數據")
    st.info(f"🔍 錯誤報告：{error_msg}")
    st.write("---")
    st.write("💡 **老闆檢查清單：**")
    st.write("1. 檢查 Token 是否有漏掉引號或貼錯。")
    st.write("2. 檢查 FinMind 官網是否正在維護。")
