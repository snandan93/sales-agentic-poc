"""
graph.py
--------
The ORCHESTRATION layer. This is the "agentic" brain of the POC:

    Sales Manager question
        -> [agent node: Ollama LLM decides if/which tool to call]
        -> [tools node: executes the MCP tool over stdio]
        -> back to [agent node] with the tool result
        -> repeats until the LLM has enough info to answer in plain English

It's a small, explicit LangGraph graph (not the hidden prebuilt agent) so the
control flow is easy to see and explain in a demo.

Requires:
  - Ollama running locally (https://ollama.com) with a tool-calling capable
    model pulled, e.g.:   ollama pull llama3.1
  - mcp_server.py in the same folder (spawned automatically as a subprocess)
"""

import os
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_ollama import ChatOllama
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

SYSTEM_PROMPT = (
    "You are a helpful sales operations assistant for a sales manager. "
    "You have tools that give you real, live numbers about this month's team "
    "sales performance (targets, achieved amounts, top/bottom performers, "
    "who reached target, and breakdowns by region, product, channel, city, or manager). "
    "The dataset can be filtered by region, product, and channel. Large lists are "
    "paginated, so request only the page and page size needed for the answer. "
    "Always call a tool to get real numbers before answering — never guess "
    "or make up figures. Answer in short, clear, management-friendly language, "
    "and include the concrete numbers (₹ amounts and %) in your answer."
)


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


async def build_graph():
    """
    Build and compile the LangGraph app. Async because loading MCP tools
    requires spawning the MCP server subprocess and talking to it.
    """
    # 1. Connect to the MCP tool server (spawned as a local subprocess over stdio)
    mcp_client = MultiServerMCPClient(
        {
            "sales": {
                "transport": "stdio",
                "command": "python",
                "args": [os.path.join(os.path.dirname(__file__), "mcp_server.py")],
            }
        }
    )
    tools = await mcp_client.get_tools()

    # 2. Local Ollama model, bound to the MCP tools
    llm = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL, temperature=0)
    llm_with_tools = llm.bind_tools(tools)

    # 3. Graph nodes
    async def agent_node(state: AgentState):
        response = await llm_with_tools.ainvoke(state["messages"])
        return {"messages": [response]}

    tool_node = ToolNode(tools)

    # 4. Wire the graph: agent -> (tools -> agent)* -> END
    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()


async def ask(app, question: str, history: list | None = None):
    """
    Run one question through the compiled graph.
    `history` is a list of prior LangChain messages (for multi-turn chat).
    Returns (answer_text, updated_message_history).
    """
    from langchain_core.messages import SystemMessage, HumanMessage

    messages = history[:] if history else [SystemMessage(content=SYSTEM_PROMPT)]
    messages.append(HumanMessage(content=question))

    result = await app.ainvoke({"messages": messages})
    updated_history = result["messages"]
    answer = updated_history[-1].content
    return answer, updated_history
