import streamlit as st
import google.generativeai as genai
import yfinance as yf
import time

# --- PAGE SETUP ---
st.set_page_config(page_title="My AI Team", page_icon="🤖")
st.title("🤖 Trading & Healing Mate (Lite)")
st.caption("Powered by Gemini 1.5 Flash (Fast & Free)")

# --- 1. API KEY CHECK ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("❌ API Key missing!")
    st.stop()

# --- 2. LIVE MARKET DATA ---
st.sidebar.header("🔴 Live Nifty Status")
def get_market_data():
    try:
        nifty = yf.Ticker("^NSEI")
        data = nifty.history(period="1d")
        if not data.empty:
            current = data['Close'].iloc[-1]
            change = current - data['Open'].iloc[-1]
            color = "green" if change >= 0 else "red"
            st.sidebar.metric("Nifty 50", f"{current:.2f}")
            st.sidebar.markdown(f"Change: :{color}[{change:.2f}]")
            return f"Current Nifty Price: {current:.2f}"
        return "Market Data Unavailable"
    except:
        return "Data Error"

market_status = get_market_data()

# --- 3. CHAT HISTORY ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "model",
        "content": "You are a helpful AI Assistant for Trading Psychology and Healing. Keep answers short and practical."
    })

for msg in st.session_state.messages:
    if msg["role"] != "model":
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

# --- 4. USER INPUT ---
if prompt := st.chat_input("Puchiye..."):
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    full_prompt = f"Live Market Data: {market_status}. User Query: {prompt}"

    with st.chat_message("assistant"):
        status_box = st.empty()
        status_box.text("Thinking...")
        
        try:
            # 🛑 FORCE USE: Gemini 1.5 Flash (Sabse Safe Model)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(full_prompt)
            
            status_box.empty()
            st.write(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})

        except Exception as e:
            status_box.empty()
            # Agar error aaye toh saaf batao
            st.error(f"⚠️ Error aaya: {e}")
            if "429" in str(e) or "Quota" in str(e):
                st.warning("Quota Limit Hit: Thodi der ruk kar try karein.")
