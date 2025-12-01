import streamlit as st
import google.generativeai as genai
import yfinance as yf
import re

# --- PAGE SETUP ---
st.set_page_config(page_title="My AI Doctor", page_icon="🩺")
st.title("🩺 Self-Healing AI Trading Mate")
st.caption("Auto-Detecting Best Available Model...")

# --- 1. API KEY CHECK ---
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
else:
    st.error("❌ API Key missing in Secrets!")
    st.stop()

# --- 2. DOCTOR LOGIC: FIND WORKING MODEL ---
# Ye function Google se puchega ki "Kaunsa model zinda hai?"
@st.cache_resource
def get_working_model():
    try:
        available_models = []
        # Google se list maango
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        if not available_models:
            return None, "No models found."
            
        # Prefer Gemini 1.5 Flash or Pro
        best_model = available_models[0]
        for m in available_models:
            if "gemini-1.5-flash" in m:
                best_model = m
                break
            elif "gemini-1.5-pro" in m:
                best_model = m
        
        return best_model, available_models
    except Exception as e:
        return None, str(e)

# Model dhundo
active_model_name, all_models = get_working_model()

# --- 3. DISPLAY STATUS (DEBUGGING) ---
if active_model_name:
    st.success(f"✅ Connected to: **{active_model_name}**")
else:
    st.error(f"❌ Could not connect to Google AI. Error: {all_models}")
    st.stop()

# --- 4. LIVE MARKET DATA ---
st.sidebar.header("🔴 Live Market Data")
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

# --- 5. CHAT HISTORY ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "model",
        "content": "You are a helpful AI Assistant. Use <think> tags for reasoning."
    })

for msg in st.session_state.messages:
    if msg["role"] != "model":
        with st.chat_message(msg["role"]):
            content = msg["content"]
            if "<think>" in content:
                parts = content.split("</think>")
                thought = parts[0].replace("<think>", "").strip()
                answer = parts[1].strip() if len(parts) > 1 else ""
                with st.expander("🧠 AI Thought Process"):
                    st.write(thought)
                st.write(answer)
            else:
                st.write(content)

# --- 6. USER INPUT ---
if prompt := st.chat_input("Ab puchiye, ye pakka chalega..."):
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    full_prompt = f"Live Market Data: {market_status}. User Query: {prompt}"

    with st.chat_message("assistant"):
        status_box = st.status(f"🧠 Thinking with {active_model_name}...", expanded=True)
        
        try:
            # Jo model mila, wahi use karenge
            model = genai.GenerativeModel(active_model_name)
            response = model.generate_content(full_prompt)
            
            status_box.update(label="✅ Answer Generated!", state="complete", expanded=False)
            
            text = response.text
            if "<think>" in text:
                parts = text.split("</think>")
                thought = parts[0].replace("<think>", "").strip()
                answer = parts[1].strip() if len(parts) > 1 else ""
                with st.expander("🧠 AI Thought Process"):
                    st.write(thought)
                st.write(answer)
            else:
                st.write(text)
                
            st.session_state.messages.append({"role": "assistant", "content": text})

        except Exception as e:
            status_box.update(label="❌ Failed", state="error")
            st.error(f"Error: {e}")
