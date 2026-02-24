
import streamlit as st
from app.chatbot import chat

st.set_page_config(page_title="i95Dev Chatbot", layout="centered")
st.title("🤖 i95Dev AI Chatbot")

if "messages" not in st.session_state:
    st.session_state.messages = []

user_input = st.chat_input("Ask about i95Dev services...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    response = chat(user_input, st.session_state.messages)
    st.session_state.messages.append({"role": "assistant", "content": response})

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
