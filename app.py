import streamlit as st
import google.generativeai as genai
import yfinance as yf
import re

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="My Thinking AI", page_icon="🧠")
st.title("🧠 Nifty & Healing Mate (Thinking Mode)")
st.caption("Powered by Gemini 1.5 Pro • Live Data • Chain of Thought")

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
            return f"Current Nifty Price: {current:.2f}, Day Change: {change:.2f}"
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

# --- 4. CHAT LOGIC ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    # System Prompt with "Thinking" Instruction
    st.session_state.messages.append({
        "role": "model",
        "content": """You are a smart AI. 
        IMPORTANT RULE: For every answer, you MUST first 'think' about the user's situation, market data, and psychology. 
        Write your deep reasoning inside <think> and </think> tags, then provide the final polite answer outside the tags.
        Example: <think>User is panicking. Market is down 1%. I need to calm them.</think> Hey, relax..."""
    })

# Display History
for msg in st.session_state.messages:
    if msg["role"] != "model":
        with st.chat_message(msg["role"]):
            # History mein Thinking ko Expander mein dikhana
            content = msg["content"]
            thought_match = re.search(r'<think>(.*?)</think>', content, re.DOTALL)
            if thought_match:
                thought_text = thought_match.group(1).strip()
                final_text = content.replace(thought_match.group(0), "").strip()
                with st.expander("🧠 AI Thought Process (Tap to view)"):
                    st.markdown(thought_text)
                st.markdown(final_text)
            else:
                st.markdown(content)

# --- 5. USER INPUT ---
if prompt := st.chat_input("Puchiye... (Main soch kar jawab dunga)"):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    full_prompt = f"Live Market Data: {market_status}. User Query: {prompt}"

    with st.chat_message("assistant"):
        status_text = st.empty() # Placeholder for 'Thinking...'
        status_text.status("🧠 Gehari soch vichar kar raha hoon...", expanded=True)
        
        try:
            model = genai.GenerativeModel("gemini-1.5-pro")
            response = model.generate_content(full_prompt)
            text = response.text
            
            # Logic to separate Thought vs Answer
            status_text.empty() # Remove loading status
            
            thought_match = re.search(r'<think>(.*?)</think>', text, re.DOTALL)
            if thought_match:
                thought_content = thought_match.group(1).strip()
                final_answer = text.replace(thought_match.group(0), "").strip()
                
                # 1. Pehle Thinking dikhao (Hidden box mein)
                with st.expander("🧠 AI Thought Process (Analysis)", expanded=True):
                    st.markdown(thought_content)
                
                # 2. Phir Final Answer
                st.markdown(final_answer)
            else:
                st.markdown(text)
                
            st.session_state.messages.append({"role": "assistant", "content": text})

        except Exception as e:
            st.error(f"Error: {e}")
