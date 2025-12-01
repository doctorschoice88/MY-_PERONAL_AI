import streamlit as st
import google.generativeai as genai
import yfinance as yf

# --- PAGE SETUP ---
st.set_page_config(page_title="Gemini 3 Trading Mate", page_icon="⚡")
st.title("⚡ Gemini 3.0: Nifty & Healing")
st.caption("Powered strictly by Google Gemini 3.0 Pro")

# --- LIVE MARKET DATA (Nifty) ---
st.sidebar.header("🔴 Live Nifty Status")

def get_market_data():
    try:
        nifty = yf.Ticker("^NSEI")
        data = nifty.history(period="1d")
        if not data.empty:
            current_price = data['Close'].iloc[-1]
            change = current_price - data['Open'].iloc[-1]
            color = "green" if change >= 0 else "red"
            st.sidebar.markdown(f"**Price:** {current_price:.2f}")
            st.sidebar.markdown(f":{color}[Change: {change:.2f}]")
            return f"Current Nifty Price: {current_price:.2f}"
        return "Market Data Unavailable"
    except:
        return "Data Error"

market_status = get_market_data()

# --- API SETUP ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("API Key missing in Secrets!")
    st.stop()

# --- CHAT HISTORY ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "model",
        "content": "You are Gemini 3.0, an expert in Trading Psychology and Trauma Healing. Be direct and powerful."
    })

for message in st.session_state.messages:
    if message["role"] != "model":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# --- MAIN LOGIC (STRICT GEMINI 3) ---
if prompt := st.chat_input("Gemini 3 se puchiye..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    full_prompt = f"Context: {market_status}. User Question: {prompt}"

    with st.chat_message("assistant"):
        with st.spinner("Gemini 3.0 soch raha hai..."):
            try:
                # ⚡ SIRF GEMINI 3.0 PRO MODEL
                model = genai.GenerativeModel("gemini-3.0-pro") 
                # Note: Agar ye naam na chale toh 'gemini-1.5-pro-002' try karna
                
                response = model.generate_content(full_prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            
            except Exception as e:
                st.error(f"❌ Gemini 3 Error: {e}")
                st.error("Shayad apki API Key par abhi Gemini 3 activate nahi hua hai.")
