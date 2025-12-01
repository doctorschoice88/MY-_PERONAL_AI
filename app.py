import streamlit as st
import google.generativeai as genai
import yfinance as yf

# --- PAGE SETUP ---
st.set_page_config(page_title="My AI Team", page_icon="🤖")
st.title("🤖 Trading & Healing Mate (Lite)")

# IMPORTANT: caption generic rakho, model version change hota rehta hai
st.caption("Powered by Google Gemini (Fast & Lite)")

# --- 1. API KEY CHECK ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("❌ API Key missing! Go to .streamlit/secrets.toml and set GEMINI_API_KEY.")
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
    except Exception:
        return "Data Error"

market_status = get_market_data()

# --- 3. CHAT HISTORY ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "system",
        "content": (
            "You are a helpful AI Assistant for Trading Psychology and Healing. "
            "Keep answers short, practical, and stress-free. "
            "Avoid financial advice; focus on mindset, risk control, and emotional balance."
        )
    })

# Show only user + assistant messages in UI
for msg in st.session_state.messages:
    if msg["role"] in ["user", "assistant"]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

# --- 4. USER INPUT ---
user_input = st.chat_input("Puchiye...")

if user_input:
    st.chat_message("user").write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    full_prompt = (
        f"{st.session_state.messages[0]['content']}\n\n"
        f"Live Market Data: {market_status}\n\n"
        f"User Query: {user_input}"
    )

    with st.chat_message("assistant"):
        status_box = st.empty()
        status_box.text("Gehari soch vichar kar raha hoon...")

        try:
            # 🔁 TRY NEW LIGHT MODEL FIRST
            #   Tum yahan alag models try kar sakte ho:
            #   - "gemini-2.0-flash" (fast, cheap)
            #   - "gemini-1.5-flash-latest" (agar account me enabled ho)
            #   - "gemini-2.0-flash-lite-preview" (bahut light)
            model_name = "gemini-2.0-flash"

            model = genai.GenerativeModel(model_name)
            response = model.generate_content(full_prompt)

            status_box.empty()

            reply = response.text if hasattr(response, "text") else str(response)
            st.write(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})

        except Exception as e:
            status_box.empty()
            err = str(e)
            st.error(f"⚠️ Error aaya: {err}")

            # --- FRIENDLY MESSAGES ---
            if "404" in err and "models/" in err:
                st.warning(
                    "Model name galat ya unavailable hai. "
                    "Backend code me model_name ko kisi supported model se replace karo "
                    "(jaise 'gemini-2.0-flash')."
                )
            elif "Quota" in err or "429" in err:
                st.warning(
                    "Free quota khatam ho chuka hai ya limit bahut low hai. "
                    "Google Cloud Console me billing / quota check karo."
                )
            else:
                st.info("Thoda der baad dobara try karo, ya console me full error log dekho.")
