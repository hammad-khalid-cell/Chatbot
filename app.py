import streamlit as st
from backend import chatbot
from langchain_core.messages import HumanMessage
import uuid
from datetime import datetime


# Page config
st.set_page_config(
    page_title="Chatbot",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Utility functions
def generateThreadID():
    return str(uuid.uuid4())

def get_conversation_title(messages):
    """Generate a title from the first user message."""
    for msg in messages:
        if msg["role"] == "user":
            title = msg["content"][:30]
            return title + "..." if len(msg["content"]) > 30 else title
    return "New Conversation"


# Session setup
if "message_history" not in st.session_state:
    st.session_state["message_history"] = []

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = generateThreadID()

if "all_conversations" not in st.session_state:
    st.session_state["all_conversations"] = {}  # {thread_id: {messages, timestamp}}

# Save current conversation to history whenever it has messages
current_tid = st.session_state["thread_id"]
if st.session_state["message_history"]:
    st.session_state["all_conversations"][current_tid] = {
        "messages": st.session_state["message_history"],
        "timestamp": st.session_state["all_conversations"].get(current_tid, {}).get(
            "timestamp", datetime.now().strftime("%b %d, %H:%M")
        )
    }


# ── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.title("Chatbot")

if st.sidebar.button("➕ New Chat", use_container_width=True):
    st.session_state["message_history"] = []
    st.session_state["thread_id"] = generateThreadID()
    st.rerun()

st.sidebar.divider()
st.sidebar.subheader("💬 My Conversations")

if not st.session_state["all_conversations"]:
    st.sidebar.caption("No conversations yet.")
else:
    # Show conversations newest first
    sorted_convos = sorted(
        st.session_state["all_conversations"].items(),
        key=lambda x: x[1]["timestamp"],
        reverse=True
    )

    for tid, convo in sorted_convos:
        title = get_conversation_title(convo["messages"])
        timestamp = convo["timestamp"]
        is_active = tid == st.session_state["thread_id"]

        # Highlight active conversation
        label = f"{'🟢 ' if is_active else ''}{title}\n{timestamp}"

        if st.sidebar.button(label, key=f"convo_{tid}", use_container_width=True):
            st.session_state["thread_id"] = tid
            st.session_state["message_history"] = convo["messages"]
            st.rerun()


# ── Main Chat Area ────────────────────────────────────────────────────────────
st.title("💬 Chat")

# Display previous messages
for message in st.session_state["message_history"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])  # markdown instead of text for better rendering

# Chat input
user_input = st.chat_input("Type here...")

if user_input:
    # Save user message
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

    # Assistant response
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

    # Save assistant message
    st.session_state["message_history"].append({
        "role": "assistant",
        "content": ai_message
    })

    # Update conversation store
    st.session_state["all_conversations"][st.session_state["thread_id"]] = {
        "messages": st.session_state["message_history"],
        "timestamp": st.session_state["all_conversations"].get(
            st.session_state["thread_id"], {}
        ).get("timestamp", datetime.now().strftime("%b %d, %H:%M"))
    }

    st.rerun()  # Refresh sidebar to show updated conversation title