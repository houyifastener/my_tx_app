import streamlit as st
from FinMind.data import DataLoader
import pandas as pd
from datetime import datetime, timedelta

# ==========================================
# 1. 設定 Token (陳大哥，請務必確認這串字有沒有貼完整)
# ==========================================
MY_FINMIND_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiaG91eWkiLCJlbWFpbCI6ImhvdXlpZmFzdGVuZXJAZ21haWwuY29tIn0.Z4a9jwT26acoN-OEBjbFu_VDneVrmN9iSpC3YxigBDg"

st.set_page_config(page_title="台指期戰情室", layout="centered")
st.title("🏹 台指期量能決策系統")

def get_data_with_debug():
    dl = DataLoader()
    try:
        # 嘗試登入
        dl.login(token=MY_FINMIND_TOKEN)
    except Exception as e:
        return None, f"登入失敗：{str(e)}", None

    # 嘗試抓取最近三天的資料 (包含昨天夜盤)
    for i in range(3):
        target_date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        try:
            df = dl.taiwan_futures_tick(
                futures_id="TX",
                date=target_date
            )
            if df is not None and not df.empty:
                return df, f"成功獲取 {target_date} 資料", target_date
        except Exception as e:
            continue
            
    return None, "過去三天皆查無成交資料 (週末維護中或 Token 額度受限)", None

# --- 執行並顯示 ---
df, status_msg, data_date = get_data_with_debug()

if df is not None:
    st.success(f"✅ {status_msg}")
    price = df.iloc[-1]['close']
    st.metric("台指期最後點位", f"{price:.0f}")
    
    # 簡易邏輯判斷
    recent = df.tail(100)
    out_vol = recent[recent['diff'] > 0]['volume'].sum()
    in_vol = recent[recent['diff'] < 0]['volume'].sum()
    ratio = out_vol / (out_vol + in_vol) if (out_vol + in_vol) > 0 else 0.5
    
    if ratio > 0.6:
        st.error(f"### 🔥 短多訊號 (外盤 {ratio:.1%})")
    elif ratio < 0.4:
        st.success(f"### 🩸 短空訊號 (內盤 {1-ratio:.1%})")
    else:
        st.warning("### ⚖️ 多空力道均衡")
else:
    st.error("❌ 目前無法連線至數據源")
    st.info(f"🔍 系統訊息：{status_msg}")
    st.write("---")
    st.write("### 📢 老闆請檢查：")
    st.write("1. **Token 是否貼對？** (請確認開頭和結尾沒有多餘的空格)")
    st.write("2. **FinMind 額度？** (如果是免費版，每天有存取限制，可能剛才測試太多次被暫時鎖定了)")
    st.write("3. **週末因素：** 如果系統訊息顯示『查無資料』，請等下午三點後再試，那是 FinMind 在整理週五夜盤數據。")
