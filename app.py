import streamlit as st
from backend import chatbot
from langchain_core.messages import HumanMessage
import uuid
from datetime import datetime


# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Chatbot",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ── Utility functions ─────────────────────────────────────────────────────────
def generate_thread_id():
    return str(uuid.uuid4())


def get_conversation_title(messages):
    """Generate a title from the first user message."""
    for msg in messages:
        if msg["role"] == "user":
            title = msg["content"][:30]
            return title + "..." if len(msg["content"]) > 30 else title
    return "New Conversation"


def load_conversation(tid):
    """Load a past conversation into the active session."""
    if tid in st.session_state["all_conversations"]:
        st.session_state["thread_id"] = tid
        st.session_state["message_history"] = st.session_state["all_conversations"][tid]["messages"]


def save_current_conversation():
    """Save the current conversation to all_conversations store."""
    tid = st.session_state["thread_id"]
    if st.session_state["message_history"]:
        existing_timestamp = st.session_state["all_conversations"].get(tid, {}).get("timestamp")
        st.session_state["all_conversations"][tid] = {
            "messages": st.session_state["message_history"],
            "timestamp": existing_timestamp or datetime.now().strftime("%b %d, %H:%M")
        }


def start_new_chat():
    """Reset session for a new conversation."""
    st.session_state["message_history"] = []
    st.session_state["thread_id"] = generate_thread_id()


# ── Session setup ─────────────────────────────────────────────────────────────
if "message_history" not in st.session_state:
    st.session_state["message_history"] = []

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = generate_thread_id()

if "all_conversations" not in st.session_state:
    st.session_state["all_conversations"] = {}

# Auto-save current conversation on every rerun
save_current_conversation()


# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("🤖 Langgraph Chatbot")

if st.sidebar.button("➕ New Chat", use_container_width=True):
    start_new_chat()
    st.rerun()

st.sidebar.divider()
st.sidebar.subheader("💬 My Conversations")

if not st.session_state["all_conversations"]:
    st.sidebar.caption("No conversations yet.")
else:
    sorted_convos = sorted(
        st.session_state["all_conversations"].items(),
        key=lambda x: x[1]["timestamp"],
        reverse=True
    )

    for tid, convo in sorted_convos:
        title = get_conversation_title(convo["messages"])
        timestamp = convo["timestamp"]
        is_active = tid == st.session_state["thread_id"]
        label = f"{'🟢 ' if is_active else ''}{title}\n{timestamp}"

        if st.sidebar.button(label, key=f"convo_{tid}", use_container_width=True):
            load_conversation(tid)
            st.rerun()


# ── Main Chat Area ────────────────────────────────────────────────────────────
for message in st.session_state["message_history"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input("Type here...")

if user_input:

    st.session_state["message_history"].append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.markdown(user_input)

    CONFIG = {
        "configurable": {
            "thread_id": st.session_state["thread_id"]
        }
    }

    with st.chat_message("assistant"):
        def response_generator():
            for message_chunk, metadata in chatbot.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode="messages",
            ):
                if hasattr(message_chunk, "content") and message_chunk.content:
                    yield message_chunk.content

        ai_message = st.write_stream(response_generator())

    st.session_state["message_history"].append({
        "role": "assistant",
        "content": ai_message
    })

    save_current_conversation()
    st.rerun()