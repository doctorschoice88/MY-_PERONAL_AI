import streamlit as st
import google.generativeai as genai
import yfinance as yf
import re

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="My Smart AI", page_icon="🧠")
st.title("🧠 Auto-Pilot Trading & Healing Mate")
st.caption("Auto-Switching Models • Live Data • Thinking Mode")

# --- 2. LIVE DATA ANTENNA ---
st.sidebar.header("🔴 Live Market Status")

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

# --- 3. API CONFIG ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("API Key missing!")
    st.stop()

# --- 4. SMART MODEL SELECTOR (BRAHMASTRA LOGIC) ---
def get_smart_response(full_prompt):
    # Ye list mein se ek-ek karke try karega
    models_to_try = [
        "gemini-1.5-flash",       # Sabse tez
        "gemini-1.5-pro",         # Sabse smart
        "gemini-1.5-flash-001",   # Specific version
        "gemini-1.5-pro-001",     # Specific version
        "gemini-pro"              # Sabse purana aur stable (Ye pakka chalta hai)
    ]
    
    last_error = ""
    
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(full_prompt)
            # Agar safalta mili, toh model ka naam aur jawab wapas karo
            return response.text, model_name
        except Exception as e:
            last_error = e
            continue # Agla model try karo
            
    # Agar saare fail ho gaye
    raise Exception(f"All models failed. Last error: {last_error}")

# --- 5. CHAT LOGIC ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "model",
        "content": "You are a helpful AI. Think deeply before answering using <think> tags."
    })

# History Display
for msg in st.session_state.messages:
    if msg["role"] != "model":
        with st.chat_message(msg["role"]):
            content = msg["content"]
            # Thinking box logic
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
if prompt := st.chat_input("Kuch bhi puchiye..."):
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    full_prompt = f"Live Market Data: {market_status}. User Query: {prompt}"

    with st.chat_message("assistant"):
        status_box = st.status("🧠 Dimag laga raha hoon (Finding best model)...", expanded=True)
        
        try:
            # Smart Function call kar rahe hain
            response_text, used_model = get_smart_response(full_prompt)
            
            status_box.update(label=f"✅ Success! Used Model: {used_model}", state="complete", expanded=False)
            
            # Formatting Response
            if "<think>" in response_text:
                parts = response_text.split("</think>")
                thought = parts[0].replace("<think>", "").strip()
                answer = parts[1].strip() if len(parts) > 1 else ""
                with st.expander("🧠 AI Thought Process"):
                    st.write(thought)
                st.write(answer)
            else:
                st.write(response_text)
                
            st.session_state.messages.append({"role": "assistant", "content": response_text})

        except Exception as e:
            status_box.update(label="❌ Failed", state="error")
            st.error(f"Bhai abhi bhi issue hai: {e}")
