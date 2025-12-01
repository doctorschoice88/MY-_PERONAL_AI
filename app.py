import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="My Personal Space", page_icon="🧘‍♂️")
st.title("🧘‍♂️ My Personal AI Space")

# Check for secret key
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
else:
    st.error("API Key missing! Please set it in Streamlit Secrets.")
    st.stop()

# Initialize chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("Likhein..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        with st.chat_message("assistant"):
            response = model.generate_content(prompt)
            st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
    except Exception as e:
        st.error(f"Error: {e}")
