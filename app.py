import streamlit as st
from FinMind.data import DataLoader
import pandas as pd
from datetime import datetime, timedelta

# 請在此輸入您的 FinMind Token
MY_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiaG91eWkiLCJlbWFpbCI6ImhvdXlpZmFzdGVuZXJAZ21haWwuY29tIn0.Z4a9jwT26acoN-OEBjbFu_VDneVrmN9iSpC3YxigBDg"

st.set_page_config(page_title="台指期戰情室", layout="centered")
st.title("🏹 台指期量能決策系統")

def fetch_tx_data():
    dl = DataLoader()
    # 嘗試往回找 3 天的資料
    for i in range(3):
        target_date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        try:
            # 在此版本中，token 直接寫在函式參數裡
            df = dl.taiwan_futures_tick(
                futures_id="TX",
                date=target_date,
                token=MY_TOKEN
            )
            if df is not None and not df.empty:
                return df, target_date
        except:
            continue
    return None, None

# 執行抓取
df, data_date = fetch_tx_data()

if df is not None:
    st.success(f"✅ 成功獲取資料：{data_date}")
    
    # 取得最新成交價
    current_price = df.iloc[-1]['close']
    st.metric("台指期最後成交價", f"{current_price:.0f}")
    
    # 計算內外盤力道 (取最後 100 筆)
    recent = df.tail(100)
    out_vol = recent[recent['diff'] > 0]['volume'].sum()
    in_vol = recent[recent['diff'] < 0]['volume'].sum()
    
    total = out_vol + in_vol
    if total > 0:
        ratio = out_vol / total
        if ratio > 0.6:
            st.error(f"### 🔥 短多建議 (外盤佔比 {ratio:.1%})")
        elif ratio < 0.4:
            st.success(f"### 🩸 短空建議 (內盤佔比 {1-ratio:.1%})")
        else:
            st.warning("### ⚖️ 多空力道均衡，建議觀望")
    
    st.divider()
    st.caption(f"最後更新時間：{df.iloc[-1]['time']}")
else:
    st.error("❌ 無法讀取數據。")
    st.info("💡 提醒：若目前是週末且 FinMind 正在維護資料庫，可能會暫時無法讀取 Tick 資料，建議週一開盤後再次確認。")
