"""
app.py
------
The FRONTEND layer — a simple chat UI for the sales manager.

Run with:
    streamlit run app.py

This file only knows how to render a chat and pass questions to the
orchestration layer (graph.py). It has no idea how the answer was produced
(which tool got called, which LLM, etc.) — that's the whole point of
layering.
"""

import asyncio
import streamlit as st
from graph import build_graph, ask, OLLAMA_MODEL

st.set_page_config(page_title="Sales Performance Agent", page_icon="📊", layout="centered")

st.title("📊 Sales Performance Agent (POC)")
st.caption(
    "Ask about this month's team target, top/bottom performers, who hit target, "
    "and more — answered live from real sales data by a local LLM (Ollama)."
)

SUGGESTIONS = [
    "What's the team target for this month?",
    "Who is the top performer?",
    "Who is an average performer?",
    "Who reached their target?",
    "Who missed their target and by how much?",
    "How is each region performing?",
]


def get_app(force_rebuild=False):
    if force_rebuild and "agent_app" in st.session_state:
        del st.session_state["agent_app"]
    if "agent_app" not in st.session_state:
        with st.spinner("Starting agent (loading MCP tools)..."):
            st.session_state.agent_app = asyncio.run(build_graph())
    return st.session_state.agent_app


if "history" not in st.session_state:
    st.session_state.history = None  # LangChain message history, built on first question
if "display_messages" not in st.session_state:
    st.session_state.display_messages = []  # (role, text) for rendering only

with st.sidebar:
    st.subheader("Try asking")
    for s in SUGGESTIONS:
        if st.button(s, use_container_width=True):
            st.session_state.pending_question = s
    st.divider()
    # st.caption("Architecture")
    # st.markdown(
    #     "**Frontend** (this page) \n→ **Orchestration** (LangGraph) \n"
    #     "→ **Tools** (MCP server, sales_data.json) \n→ **Local LLM** (Ollama)"
    # )

for role, text in st.session_state.display_messages:
    with st.chat_message(role):
        st.markdown(text)

question = st.chat_input("Ask about this month's sales performance...")
if "pending_question" in st.session_state:
    question = st.session_state.pop("pending_question")

if question:
    st.session_state.display_messages.append(("user", question))
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Checking the numbers..."):
            try:
                app = get_app()
                answer, updated_history = asyncio.run(
                    ask(app, question, st.session_state.history)
                )
                st.session_state.history = updated_history
            except Exception as e:
                try:
                    app = get_app(force_rebuild=True)
                    answer, updated_history = asyncio.run(
                        ask(app, question, st.session_state.history)
                    )
                    st.session_state.history = updated_history
                except Exception as e2:
                    answer = (
                        f"⚠️ Couldn't reach the agent: {e2}\n\n"
                        "Make sure Ollama is running locally (`ollama serve`) and that "
                        f"the model set in `OLLAMA_MODEL` has been pulled (e.g. `ollama pull {OLLAMA_MODEL}`)."
                    )
        st.markdown(answer)
    st.session_state.display_messages.append(("assistant", answer))
