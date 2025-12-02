# -*- coding: utf-8 -*-
import streamlit as st
import yfinance as yf

from google import genai
from google.genai import types

# PAGE SETUP
st.set_page_config(page_title="Trading Mate (Lite)", page_icon=":chart_with_upwards_trend:", layout="wide")
st.title("Trading Mate (Lite)")
st.caption("Powered by Google Gemini (3.0 / 2.5 / 2.0 fallback) — Trading guidance only")

# GEMINI CLIENT SETUP
if "GEMINI_API_KEY" not in st.secrets:
    st.error("GEMINI_API_KEY missing in Streamlit secrets. Add GEMINI_API_KEY and redeploy.")
    st.stop()

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# LIVE NIFTY DATA
st.sidebar.header("Live Nifty Status")

def get_market_data():
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
    st.subheader("Live Nifty Snapshot")
    st.write(f"Nifty 50: {current:.2f}  |  Change: {change:+.2f}  ({pct:+.2f}%)")
    market_status = f"Nifty {current:.2f} ({change:+.2f}, {pct:+.2f}%)"
else:
    st.sidebar.write("Nifty data: unavailable")
    st.subheader("Live Nifty Snapshot")
    st.write("Live data currently unavailable.")
    if market_err:
        st.caption(f"Debug: {market_err}")
    market_status = "Nifty data unavailable."

# SYSTEM PROMPT AND SESSION
SYSTEM_PROMPT = (
    "You are Rajat's personal Trading Coach.\n"
    "Speak in calm practical Hinglish. Keep answers short and focused only on trading: bias, levels, entry/exit framework, and risk management.\n"
    "Do NOT provide guaranteed financial advice or exact buy/sell orders."
)

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

for msg in st.session_state.messages:
    if msg["role"] in ["user", "assistant"]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

# ROBUST EXTRACTOR
def extract_reply(response):
    try:
        if hasattr(response, "text") and response.text:
            return response.text
        if hasattr(response, "candidates") and response.candidates:
            c = response.candidates[0]
            if hasattr(c, "content") and c.content:
                return c.content
            if hasattr(c, "parts") and c.parts:
                texts = []
                for p in c.parts:
                    if hasattr(p, "text") and p.text:
                        texts.append(p.text)
                    elif isinstance(p, dict) and p.get("text"):
                        texts.append(p.get("text"))
                if texts:
                    return "\n".join(texts)
            if hasattr(c, "message") and c.message:
                return str(c.message)
            return str(c)
        if hasattr(response, "output") and response.output:
            out_texts = []
            for out in response.output:
                if hasattr(out, "content") and out.content:
                    out_texts.append(out.content)
                elif hasattr(out, "text") and out.text:
                    out_texts.append(out.text)
                elif isinstance(out, dict) and out.get("text"):
                    out_texts.append(out.get("text"))
            if out_texts:
                return "\n".join(out_texts)
        if hasattr(response, "parts") and response.parts:
            parts = []
            for p in response.parts:
                if hasattr(p, "text") and p.text:
                    parts.append(p.text)
                elif isinstance(p, dict) and p.get("text"):
                    parts.append(p.get("text"))
            if parts:
                return "\n".join(parts)
        return "Response unavailable"
    except Exception:
        return "Response unavailable"

# USER INPUT & MODEL CALL
user_input = st.chat_input("Puchiye...")

if user_input:
    st.chat_message("user").write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    convo_lines = [SYSTEM_PROMPT, f"Live Market: {market_status}", ""]
    for m in st.session_state.messages:
        if m["role"] == "user":
            convo_lines.append(f"User: {m['content']}")
        elif m["role"] == "assistant":
            convo_lines.append(f"Assistant: {m['content']}")
    convo_lines.append("Assistant:")
    full_prompt = "Think step-by-step and then answer briefly in simple Hinglish.\n" + "\n".join(convo_lines)

    with st.chat_message("assistant"):
        status_box = st.empty()
        status_box.text("Thinking...")

        try:
            candidate_models = ["gemini-3.0-pro", "gemini-2.5-flash", "gemini-2.0-flash"]
            last_error = None
            used_model = None
            response = None

            for model_name in candidate_models:
                try:
                    resp = client.models.generate_content(
                        model=model_name,
                        contents=full_prompt,
                        config=types.GenerateContentConfig(temperature=0.45, max_output_tokens=400),
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
            st.markdown(f"Model used: **{used_model}**")
            st.write(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})

        except Exception as e:
            status_box.empty()
            err = str(e)
            st.error(f"Error: {err}")
            if "404" in err and "models/" in err:
                st.warning("Model not enabled for this project. Check Google AI Studio.")
            elif "Quota" in err or "429" in err or "quota" in err.lower():
                st.warning("Quota/billing issue. Check Google Cloud console.")
            else:
                st.info("Temporary issue. Check logs.")
