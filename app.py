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
    "Which product is performing best?",
    "Compare our Direct, Partner, and Inside Sales channels.",
    "How is CRM Suite performing in the North region?",
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
if "observability" not in st.session_state:
    st.session_state.observability = []

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

for index, (role, text) in enumerate(st.session_state.display_messages):
    with st.chat_message(role):
        st.markdown(text)
        if role == "assistant":
            turn = index // 2
            if turn < len(st.session_state.observability):
                metrics = st.session_state.observability[turn]
                with st.expander("Execution details"):
                    st.caption(
                        f"{metrics['total_tokens']:,} tokens · "
                        f"{metrics['llm_calls']} LLM call(s) · "
                        f"{metrics['tool_calls']} MCP tool call(s) · "
                        f"{metrics['elapsed_seconds']:.2f}s"
                    )
                    if metrics["tool_names"]:
                        st.code(" → ".join(metrics["tool_names"]), language=None)

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
                answer, updated_history, metrics = asyncio.run(
                    ask(app, question, st.session_state.history)
                )
                st.session_state.history = updated_history
            except Exception as e:
                try:
                    app = get_app(force_rebuild=True)
                    answer, updated_history, metrics = asyncio.run(
                        ask(app, question, st.session_state.history)
                    )
                    st.session_state.history = updated_history
                except Exception as e2:
                    answer = (
                        f"⚠️ Couldn't reach the agent: {e2}\n\n"
                        "Make sure Ollama is running locally (`ollama serve`) and that "
                        f"the model set in `OLLAMA_MODEL` has been pulled (e.g. `ollama pull {OLLAMA_MODEL}`)."
                    )
                    metrics = None
        st.markdown(answer)
        if metrics:
            with st.expander("Execution details"):
                st.caption(
                    f"{metrics['input_tokens']:,} input + {metrics['output_tokens']:,} output "
                    f"= {metrics['total_tokens']:,} tokens · {metrics['llm_calls']} LLM call(s) · "
                    f"{metrics['tool_calls']} MCP tool call(s) · {metrics['elapsed_seconds']:.2f}s"
                )
                if metrics["tool_names"]:
                    st.code(" → ".join(metrics["tool_names"]), language=None)
    st.session_state.display_messages.append(("assistant", answer))
    if metrics:
        st.session_state.observability.append(metrics)

with st.sidebar:
    st.divider()
    st.subheader("Observability")
    if st.session_state.observability:
        runs = st.session_state.observability
        total_tokens = sum(run["total_tokens"] for run in runs)
        input_tokens = sum(run["input_tokens"] for run in runs)
        output_tokens = sum(run["output_tokens"] for run in runs)
        col1, col2 = st.columns(2)
        col1.metric("Total tokens", f"{total_tokens:,}")
        col2.metric("Total time", f"{sum(run['elapsed_seconds'] for run in runs):.1f}s")
        st.caption(f"Input: {input_tokens:,} · Output: {output_tokens:,}")
        st.caption(
            f"LLM calls: {sum(run['llm_calls'] for run in runs)} · "
            f"MCP tool calls: {sum(run['tool_calls'] for run in runs)}"
        )
        if st.button("Reset metrics", use_container_width=True):
            st.session_state.observability = []
            st.rerun()
    else:
        st.caption("Ask a question to see token and call usage.")
    st.caption("Ollama runs locally, so these are local LLM calls—not paid cloud API calls.")
