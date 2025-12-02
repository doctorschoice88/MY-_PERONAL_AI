import streamlit as st
import google.generativeai as genai
import yfinance as yf
import re

# --- PAGE SETUP ---
st.set_page_config(page_title="Trading & Healing Mate", page_icon="🧠")
st.title("🧠 Trading & Healing Mate")
st.caption("Powered by Gemini 2.5 (Thinking Mode) • Live Nifty Data")

# --- 1. LIVE NIFTY DATA ---
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
            st.sidebar.markdown(f"Change: :{color}[{change:.2f}]")
            return f"Current Nifty Price: {current:.2f}, Change: {change:.2f}"
        return "Market Data Unavailable"
    except:
        return "Data Error"

market_status = get_market_data()

# --- 2. API KEY SETUP ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("❌ API Key missing!")
    st.stop()

# --- 3. CHAT HISTORY ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    # SPECIAL SYSTEM PROMPT (Isse AI "Sochna" seekhega)
    st.session_state.messages.append({
        "role": "model",
        "content": """You are a smart AI companion for a trader healing from trauma.
        
        RULES:
        1. **THINK FIRST**: Before answering, you MUST think deeply about the user's emotion and market situation. Put your thoughts inside <think> ... </think> tags.
        2. **Trading**: Today is Tuesday (Nifty Expiry). Use the live data provided.
        3. **Healing**: Be calm. If user panics, guide them with breathing techniques.
        
        Example Format:
        <think>User is anxious about Nifty drop. I should check the data (-50 points). I need to calm them down first.</think>
        Hey, take a deep breath..."""
    })

# --- 4. DISPLAY CHAT ---
for msg in st.session_state.messages:
    if msg["role"] != "model":
        with st.chat_message(msg["role"]):
            # Agar purane messages mein thinking hai toh usse dikhao
            content = msg["content"]
            if "<think>" in content:
                parts = content.split("</think>")
                thought = parts[0].replace("<think>", "").strip()
                answer = parts[1].strip() if len(parts) > 1 else ""
                
                with st.expander("🧠 AI ki Soch (Thoughts)"):
                    st.info(thought)
                st.markdown(answer)
            else:
                st.markdown(content)

# --- 5. USER INPUT ---
if prompt := st.chat_input("Puchiye... (Main soch kar jawab dunga)"):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    full_prompt = f"Live Nifty Data: {market_status}. User Query: {prompt}"

    with st.chat_message("assistant"):
        status_box = st.status("🧠 Gehari soch vichar (Thinking)...", expanded=True)
        
        try:
            # Hum wahi Model use karenge jo aapke screenshot mein chala tha
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(full_prompt)
            text = response.text
            
            status_box.update(label="✅ Jawab Taiyaar!", state="complete", expanded=False)
            
            # Thinking aur Answer ko alag-alag karke dikhana
            if "<think>" in text:
                parts = text.split("</think>")
                thought = parts[0].replace("<think>", "").strip()
                answer = parts[1].strip() if len(parts) > 1 else ""
                
                with st.expander("🧠 AI ki Soch (Thoughts)", expanded=True):
                    st.info(thought)
                
                st.markdown(answer)
            else:
                st.markdown(text)
                
            st.session_state.messages.append({"role": "assistant", "content": text})

        except Exception as e:
            status_box.update(label="❌ Error", state="error")
            st.error(f"Error: {e}")
