import sqlite3
from langgraph.graph import StateGraph, END, START
from typing import TypedDict , Annotated
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from  langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
import sqlite3


load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
)




class ChatState(TypedDict):
    messages :Annotated[list[BaseMessage], add_messages]



def chat_node(state: ChatState):
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

conn  =  sqlite3.connect("chatbot.db", check_same_thread=False)

checkpointer  =  SqliteSaver(conn = conn)
graph = StateGraph(ChatState)

graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge( "chat_node", END)

chatbot =  graph.compile(checkpointer = checkpointer)
def retrieve_all_threads():

    unique_threads = set()

    for checkpoint in checkpointer.list(None):

        thread_id = checkpoint.config["configurable"]["thread_id"]

        unique_threads.add(thread_id)

    return list(unique_threads)

def retrieve_thread_messages(thread_id):

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    checkpoint = checkpointer.get(config)

    raw_messages = checkpoint["channel_values"]["messages"]

    formatted_messages = []

    for msg in raw_messages:

        if isinstance(msg, HumanMessage):

            formatted_messages.append({
                "role": "user",
                "content": msg.content
            })

        elif isinstance(msg, AIMessage):

            formatted_messages.append({
                "role": "assistant",
                "content": msg.content
            })

    return formatted_messages

