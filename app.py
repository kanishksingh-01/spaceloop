"""
app.py
Streamlit UI for the Exam & Academic Support Chatbot.
Run with: streamlit run app.py
"""

import streamlit as st
from chatbot import FAQChatbot

st.set_page_config(page_title="Exam & Academic Support Chatbot", page_icon="🎓")

st.title("🎓 Exam & Academic Support Chatbot")
st.caption("Ask me about exam schedules, syllabus, internal assessment, study material, or results.")


@st.cache_resource
def load_bot():
    return FAQChatbot("faqs.csv")


bot = load_bot()

# Sidebar: show what categories the bot can help with
with st.sidebar:
    st.header("What I can help with")
    for cat in bot.get_categories():
        st.write(f"• {cat}")
    st.divider()
    st.caption("This chatbot uses TF-IDF + Cosine Similarity to match your question to the closest known FAQ.")

# Chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! Ask me anything about exams, syllabus, results, or study material."}
    ]

# Render past messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Chat input
user_input = st.chat_input("Type your question here...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    result = bot.get_response(user_input)

    with st.chat_message("assistant"):
        st.write(result["answer"])
        if result["matched"]:
            st.caption(f"Matched category: {result['category']} · Confidence: {result['confidence']}")

    st.session_state.messages.append({"role": "assistant", "content": result["answer"]})
