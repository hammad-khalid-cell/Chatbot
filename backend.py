from langgraph.graph import StateGraph, END, START
from typing import TypedDict , Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from  langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

print(os.getenv("GROQ_API_KEY"))
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
)




class ChatState(TypedDict):
    messages :Annotated[list[BaseMessage], add_messages]



def chat_node(state: ChatState):
    response = llm.invoke(state["messages"])
    return {"messages": [response]}


checkpointer  =  MemorySaver()
graph = StateGraph(ChatState)

graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge( "chat_node", END)

chatbot =  graph.compile(checkpointer = checkpointer)
