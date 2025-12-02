import streamlit as st
import google.generativeai as genai
import yfinance as yf
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# --- PAGE SETUP ---
st.set_page_config(page_title="Trading & Healing Mate", page_icon="📈")
st.title("🧘‍♂️ Trading & Healing Mate")
st.caption("Powered by Gemini 2.5 Flash (Unlocked) • Live Nifty Data")

# --- 1. API KEY SETUP ---
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
            st.sidebar.markdown(f"Diff: :{color}[{change:.2f}]")
            return f"Current Nifty Price: {current:.2f}"
        return "Market Data Unavailable"
    except:
        return "Data Error"

market_status = get_market_data()

# --- 3. SAFETY SETTINGS (NO FILTERS) ---
# Ye zaroori hai taaki Trading ki baatein block na hon
safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

# --- 4. CHAT HISTORY ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "model",
        "content": """You are a helpful AI assistant for Rajat, a trader healing from trauma.
        1. **Trading**: Use Live Nifty Data. Today is Tuesday (Expiry). Be practical with levels.
        2. **Healing**: Keep Rajat calm. If he panics, guide him.
        3. **Language**: Use Hinglish. Keep answers short and bulleted."""
    })

for msg in st.session_state.messages:
    if msg["role"] != "model":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# --- 5. USER INPUT ---
if prompt := st.chat_input("Nifty ya Healing ke baare mein puchiye..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    full_prompt = f"Live Market Data: {market_status}. User Query: {prompt}"

    with st.chat_message("assistant"):
        with st.spinner("Gemini 2.5 (Unlocked) soch raha hai..."):
            try:
                # 🚀 GEMINI 2.5 FLASH (Jo screenshot mein chala tha)
                model = genai.GenerativeModel("gemini-2.5-flash")
                
                # Safety Settings pass kar rahe hain taaki 'None' na aaye
                response = model.generate_content(full_prompt, safety_settings=safety_settings)
                
                if response.text:
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                else:
                    st.error("Empty response received. Try asking differently.")
            
            except Exception as e:
                # Agar 2.5 fail hua, toh 1.5 Flash try karenge
                try:
                    st.warning("Switching to backup model...")
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    response = model.generate_content(full_prompt, safety_settings=safety_settings)
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                except Exception as e2:
                    st.error(f"Error: {e2}")
