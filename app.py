import streamlit as st
from FinMind.data import DataLoader
import pandas as pd
import time
from datetime import datetime, timedelta

# ==========================================
# 1. 基本設定：請在下方引號內貼上你的 Token
# ==========================================
MY_FINMIND_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiaG91eWkiLCJlbWFpbCI6ImhvdXlpZmFzdGVuZXJAZ21haWwuY29tIn0.Z4a9jwT26acoN-OEBjbFu_VDneVrmN9iSpC3YxigBDg"

# --- 網頁頁面配置 ---
st.set_page_config(page_title="台指期戰情決策系統", layout="centered")
st.title("🏹 台指期量能決策戰情室")
st.caption(f"當前使用者：陳先生 | 系統時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 建立畫面的容器，讓數據可以動態刷新
placeholder = st.empty()

# ==========================================
# 2. 核心邏輯：計算內外盤與判斷失效時間
# ==========================================
def get_market_decision():
    dl = DataLoader()
    try:
        # 抓取今日台指期即時 Tick 資料 (TX = 台指期近月)
        target_date = datetime.now().strftime("%Y-%m-%d")
        df = dl.taiwan_futures_tick(
            futures_id="TX",
            date=target_date,
            token=MY_FINMIND_TOKEN
        )
    except Exception as e:
        return f"連線異常：{e}", None, None, None, None

    # 如果沒開盤或抓不到資料
    if df is None or df.empty:
        return "📡 目前非開盤時間，或正在等待即時數據流...", None, None, None, None

    # --- 數據處理 ---
    # 取最後 100 筆成交來分析力道
    recent = df.tail(100).copy()
    
    # 區分內外盤：成交價向上跳動為外盤(Ask)，向下為內盤(Bid)
    out_vol = recent[recent['diff'] > 0]['volume'].sum()
    in_vol = recent[recent['diff'] < 0]['volume'].sum()
    total_vol = out_vol + in_vol
    
    # 計算外盤佔比 (Delta Ratio)
    delta_ratio = out_vol / total_vol if total_vol > 0 else 0.5
    
    curr_price = df.iloc[-1]['close']
    # 計算近 5 分鐘的價格位移 (Momentum)
    price_change = df.iloc[-1]['close'] - df.iloc[-10]['close'] if len(df) > 10 else 0
    
    # --- 動態失效時間計算 (量能與時間成負相關) ---
    # 公式：$ET = \frac{15}{\text{量能倍數}}$，量越大，證明自己的時間越短
    volume_momentum = total_vol / 500  # 以 500 口為基準量
    dynamic_timeout = max(3, 15 / (volume_momentum + 0.1)) 

    # ==========================================
    # 3. 語意化指令判斷 (選項 B：直接給結論)
    # ==========================================
    
    # 情境一：買氣極強 (外盤 > 60%)
    if delta_ratio > 0.6:
        if price_change > 5:
            res = "🔥 未來 1 小時：【短多預測】"
            msg = f"買氣積極 (外盤 {delta_ratio:.1%}) 且價格同步推進，動能一致。"
            entry = f"{curr_price - 3} ~ {curr_price} (強勢噴出，守 EMA10)"
            advice = f"限時 {dynamic_timeout:.1f} 分鐘內須突破前高，否則視為誘多。"
        else:
            # 有量不漲的邏輯
            res = "⚠️ 警示：【短多失效預警】"
            msg = f"偵測到「有量不漲」！外盤達 {delta_ratio:.1%} 但價格停滯，主力可能在出貨。"
            entry = "目前不建議進場，嚴防高位反轉。"
            advice = f"若 {dynamic_timeout:.1f} 分鐘內未過高，預測將轉為【長空】。"
            
    # 情境二：賣壓極強 (內盤 > 60%)
    elif delta_ratio < 0.4:
        res = "🩸 未來 1 小時：【短空預測】"
        msg = f"賣壓湧現 (內盤 {in_vol/(total_vol):.1%})，價格支撐力道轉弱。"
        entry = f"{curr_price} ~ {curr_price + 3} (反彈找空點)"
        advice = f"預計未來 3~5 小時回測今日支撐位。"
        
    # 情境三：震盪盤
    else:
        res = "⚖️ 展望：【區間震盪】"
        msg = "內外盤力道均衡，無明顯主力攻擊跡象。"
        entry = "守候費波納契 0.618 或缺口支撐"
        advice = "目前適合觀望，莫在盤整區過度交易。"

    return res, msg, entry, advice, curr_price

# ==========================================
# 4. 網頁執行與自動刷新
# ==========================================
while True:
    res, msg, entry, advice, price = get_market_decision()
    
    with placeholder.container():
        if price:
            # 顯示當前點位
            st.metric("台指期當前成交價", f"{price:.0f}", delta=None)
            
            # 顯示主要結論標題
            if "🔥" in res:
                st.error(f"### {res}") # 紅色提醒 (做多)
            elif "⚠️" in res or "⚖️" in res:
                st.warning(f"### {res}") # 黃色警告
            else:
                st.success(f"### {res}") # 綠色提醒 (做空)

            # 顯示文字分析
            st.info(f"**戰略分析：** {msg}")
            
            # 顯示進場與失效時間
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### 📍 建議進場位")
                st.code(entry, language="")
            with col2:
                st.markdown("#### 🕒 動態失效倒數")
                st.code(advice, language="")
                
            st.divider()
            st.write("📋 **老闆備註：** 本系統已整合內外盤 Delta 差值與價格背離邏輯。")
        else:
            # 沒開盤時的顯示
            st.warning(res)
            st.write(f"下一個交易日開盤時間：08:45 AM")

    # 設定每 15 秒自動刷新一次 (模擬即時跳動)
    time.sleep(15)