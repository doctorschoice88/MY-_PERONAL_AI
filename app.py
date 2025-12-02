import streamlit as st
import yfinance as yf

from google import genai
from google.genai import types

# =========================
# PAGE SETUP
# =========================
st.set_page_config(page_title="Trading Mate (Lite)", page_icon="📈", layout="wide")
st.title("📈 Trading Mate (Lite)")
st.caption("Powered by Google Gemini (3.0 / 2.5 / 2.0 fallback) — Dedicated to trading guidance only")

# =========================
# GEMINI CLIENT SETUP
# =========================
if "GEMINI_API_KEY" not in st.secrets:
    st.error("❌ GEMINI_API_KEY missing in Streamlit secrets. Add GEMINI_API_KEY and redeploy.")
    st.stop()

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# =========================
# LIVE NIFTY DATA
# =========================
st.sidebar.header("🔴 Live Nifty Status")

def get_market_data():
    """
    Try intraday (1m) first, fallback to daily.
    Returns (info_dict, error_message_or_None)
    """
    try:
        ticker = yf.Ticker("^NSEI")
        data = ticker.history(period="1d", interval="1m")
        if data.empty:
            data = ticker.history(period="1d")

        if data.empty:
            return None, "Market data empty."

        last_row = data.iloc[-1]
        current = float(last_row["Close"])
        open_price = float(data["Open"].iloc[0])
        change = current - open_price
        pct = (change / open_price) * 100

        info = {"current": current, "change": change, "pct": pct}
        return info, None

    except Exception as e:
        return None, str(e)

market_info, market_err = get_market_data()

if market_info:
    current = market_info["current"]
    change = market_info["change"]
    pct = market_info["pct"]
    st.sidebar.metric("Nifty 50", f"{current:.2f}", f"{change:+.2f} ({pct:+.2f}%)")
    st.subheader("📈 Live Nifty Snapshot")
    st.write(f"**Nifty 50:** {current:.2f}  |  Change: {change:+.2f}  ({pct:+.2f}%)")
    market_status = f"Nifty 50 live ~ {current:.2f} ({change:+.2f}, {pct:+.2f}%)"
else:
    st.sidebar.write("Nifty data: unavailable")
    st.subheader("📈 Live Nifty Snapshot")
    st.write("Live data currently unavailable.")
    if market_err:
        st.caption(f"Debug info: {market_err}")
    market_status = "Nifty live data is currently unavailable."

# =========================
# SYSTEM PROMPT AND SESSION
# =========================
SYSTEM_PROMPT = (
    "You are Rajat's personal Trading Coach.\n"
    "- Speak in calm, practical Hinglish (Hindi+English).\n"
    "- Keep answers short, structured and focused only on trading: market bias, key levels (support/resistance), entry/exit framework, risk management, and trade idea (educational).\n"
    "- Do NOT provide guaranteed financial advice or exact buy/sell orders. Avoid healing/personal therapy content.\n"
)

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

# render chat history (user + assistant only)
for msg in st.session_state.messages:
    if msg["role"] in ["user", "assistant"]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

# =========================
# RESPONSE EXTRACTION (robust)
# =========================
def extract_reply(response):
    """
    Robust extraction for multiple Gemini response shapes.
    Returns a string reply or "Response unavailable" fallback.
    """
    try:
        # 1) response.text (older/simple)
        if hasattr(response, "text") and response.text:
            return response.text

        # 2) response.candidates (common)
        if hasattr(response, "candidates") and response.candidates:
            c = response.candidates[0]
            # content attribute
            if hasattr(c, "content") and c.content:
                return c.content
            # parts inside candidate
            if hasattr(c, "parts") and c.parts:
                parts_text = []
                for p in c.parts:
                    # p may be object or dict
                    if hasattr(p, "text") and p.text:
                        parts_text.append(p.text)
                    elif isinstance(p, dict) and p.get("text"):
                        parts_text.append(p.get("text"))
                if parts_text:
                    return "\n".join(parts_text)
            # message attribute
            if hasattr(c, "message") and c.message:
                return str(c.message)
            return str(c)

        # 3) response.output (Gemini 2.5/3 shapes)
        if hasattr(response, "output") and response.output:
            out_texts = []
            for out in response.output:
                if hasattr(out, "content") and out.content:
                    out_texts.append(out.content)
                elif hasattr(out, "text") and out.text:
                    out_texts.append(out.text)
                elif isinstance(out, dict):
                    # try common keys
                    if out.get("content"):
                        out_texts.append(out.get("content"))
                    elif out.get("text"):
                        out_texts.append(out.get("text"))
            if out_texts:
                return "\n".join(out_texts)

        # 4) response.parts (message-like)
        if hasattr(response, "parts") and response.parts:
            part_texts = []
            for p in response.parts:
                if hasattr(p, "text") and p.text:
                    part_texts.append(p.text)
                elif isinstance(p, dict) and p.get("text"):
                    part_texts.append(p.get("text"))
            if part_texts:
                return "\n".join(part_texts)

        # 5) fallback to string
        result = str(response)
        if result:
            return result
    except Exception:
        pass

    return "Response unavailable"

# =========================
# USER INPUT & MODEL CALL
# =========================
user_input = st.chat_input("Puchiye... (Main soch kar jawab dunga)")

if user_input:
    st.chat_message("user").write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Build conversation prompt (system + market + recent history)
    convo_lines = [SYSTEM_PROMPT, f"Live Market: {market_status}", ""]
    for m in st.session_state.messages:
        if m["role"] == "user":
            convo_lines.append(f"User: {m['content']}")
        elif m["role"] == "assistant":
            convo_lines.append(f"Assistant: {m['content']}")
    convo_lines.append("Assistant:")
    # Prepend thinking-style instruction
    full_prompt = "Think step-by-step and then answer briefly in simple Hinglish.\n" + "\n".join(convo_lines)

    with st.chat_message("assistant"):
        status_box = st.empty()
        status_box.text("🧠 Soch raha hoon...")

        try:
            candidate_models = [
                "gemini-3.0-pro",
                "gemini-2.5-flash",
                "gemini-2.0-flash",
            ]

            last_error = None
            used_model = None
            response = None

            for model_name in candidate_models:
                try:
                    resp = client.models.generate_content(
                        model=model_name,
                        contents=full_prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.45,
                            max_output_tokens=500,
                        ),
                    )
                    response = resp
                    used_model = model_name
                    break
                except Exception as e_inner:
                    last_error = e_inner
                    continue

            if response is None:
                raise last_error or Exception("No Gemini model could be used.")

            status_box.empty()
            reply = extract_reply(response)

            st.markdown(f"🧠 _Model used: **{used_model}**_")
            st.write(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})

        except Exception as e:
            status_box.empty()
            err = str(e)
            st.error(f"⚠️ Error aaya: {err}")
            if "404" in err and "models/" in err:
                st.warning("Lagta hai Gemini model aapke project me enabled nahi hai. Google AI Studio/Cloud Console check karo.")
            elif "Quota" in err or "429" in err or "quota" in err.lower():
                st.warning("Free/trial quota hit ho gaya. Billing ya higher quota enable karo.")
            else:
                st.info("Temporary issue ho sakta hai. Logs check karo.")
```0
