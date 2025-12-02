import streamlit as st
import yfinance as yf

from google import genai
from google.genai import types

# =========================
# PAGE SETUP
# =========================
st.set_page_config(page_title="My AI Team", page_icon="🤖", layout="wide")
st.title("🤖 Trading & Healing Mate (Lite)")
st.caption("Powered by Google Gemini (Gemini 3 / 2.5 / 2.0 fallback)")

# =========================
# GEMINI CLIENT SETUP
# =========================
if "GEMINI_API_KEY" not in st.secrets:
    st.error("❌ GEMINI_API_KEY missing in Streamlit secrets.")
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
    st.write("Live data nahi aa paya.")
    if market_err:
        st.caption(f"Debug info: {market_err}")
    market_status = "Nifty live data is currently unavailable."

# =========================
# CHAT / MEMORY SETUP
# =========================
SYSTEM_PROMPT = (
    "You are Rajat's personal Trading Psychology & Healing Assistant.\n"
    "- Focus on mindset, risk management, and calm behaviour.\n"
    "- Do NOT give direct financial advice or specific trade calls.\n"
    "- Keep answers short, practical and in simple Hinglish (Hindi+English).\n"
)

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

# render chat history
for msg in st.session_state.messages:
    if msg["role"] in ["user", "assistant"]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

# =========================
# USER INPUT
# =========================
user_input = st.chat_input("Puchiye... (Main soch kar jawab dunga)")

if user_input:
    st.chat_message("user").write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # build prompt for model
    convo_lines = [SYSTEM_PROMPT, f"Live Market: {market_status}", ""]
    for m in st.session_state.messages:
        if m["role"] == "user":
            convo_lines.append(f"User: {m['content']}")
        elif m["role"] == "assistant":
            convo_lines.append(f"Assistant: {m['content']}")
    convo_lines.append("Assistant:")
    full_prompt = "\n".join(convo_lines)

    # optional: if you want explicit chain-of-thought style, prepend:
    # full_prompt = "Think step-by-step, then answer briefly.\n" + full_prompt

    with st.chat_message("assistant"):
        status_box = st.empty()
        status_box.text("🧠 Gehri soch-vichar kar raha hoon...")

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
                            temperature=0.6,
                            max_output_tokens=400,
                        ),
                    )
                    response = resp
                    used_model = model_name
                    break
                except Exception as e_inner:
                    last_error = e_inner
                    # continue to next model
                    continue

            if response is None:
                raise last_error or Exception("No Gemini model could be used.")

            # -------------------------
            # Robust extraction of text
            # -------------------------
            status_box.empty()
            reply = None

            # common simple attribute
            if hasattr(response, "text") and response.text:
                reply = response.text

            # newer shape: response.candidates (list)
            elif hasattr(response, "candidates") and getattr(response, "candidates"):
                try:
                    cand0 = response.candidates[0]
                    # candidate may have 'content' or 'message'
                    reply = getattr(cand0, "content", None) or getattr(cand0, "message", None) or str(cand0)
                except Exception:
                    reply = str(response.candidates[0])

            # another possible shape: response.output (list)
            elif hasattr(response, "output") and getattr(response, "output"):
                try:
                    out0 = response.output[0]
                    reply = getattr(out0, "content", None) or getattr(out0, "text", None) or str(out0)
                except Exception:
                    reply = str(response.output)

            # fallback: repr
            if not reply:
                reply = str(response)

            # display
            st.markdown(f"🧠 _Model used: **{used_model}**_")
            st.write(reply)
            # small debug (optional) - uncomment if you want raw
            # st.caption("Debug response: " + repr(response))

            st.session_state.messages.append({"role": "assistant", "content": reply})

        except Exception as e:
            status_box.empty()
            err = str(e)
            st.error(f"⚠️ Error aaya: {err}")

            if "404" in err and "models/" in err:
                st.warning(
                    "Lagta hai Gemini 3/2.5 model aapke project me enabled nahi hai. "
                    "Google AI Studio / Cloud Console me check karo."
                )
            elif "Quota" in err or "429" in err or "quota" in err.lower():
                st.warning(
                    "Free/trial quota hit ho gaya. Billing ya higher quota enable karo."
                )
            else:
                st.info("Temporary issue ho sakta hai. Console logs dekh kar batao.")
