# Sales Performance Agentic AI — POC

A small, fully working proof-of-concept showing the standard agentic stack,
end to end, running **entirely locally** (no external API keys, no cloud LLM):

```
 ┌─────────────┐     ┌────────────────┐     ┌──────────────┐     ┌───────────┐
 │  Frontend   │ --> │  Orchestration │ --> │  MCP Server  │ --> │  sales_   │
 │  (Streamlit)│     │  (LangGraph)   │     │  (tools)     │     │  data.json│
 └─────────────┘     └───────┬────────┘     └──────────────┘     └───────────┘
                              │
                              ▼
                        ┌───────────┐
                        │  Ollama   │  (local LLM, e.g. llama3.1)
                        └───────────┘
```

The sales manager types a question in plain English. The LangGraph agent
(running on a local Ollama model) decides which tool it needs, calls the
MCP server to get real numbers from the dataset, and replies in plain
English with the actual figures — never a guess.

## Files

| File | Layer | What it does |
|---|---|---|
| `data/sales_data.json` | Data | 20 sample sales reps: name, region, target, achieved |
| `data_utils.py` | Business logic | Pure Python analytics (no framework deps) — testable on its own |
| `mcp_server.py` | Tools (MCP) | Wraps `data_utils.py` as 9 MCP tools over stdio |
| `graph.py` | Orchestration | LangGraph agent: Ollama ↔ MCP tools, loops until it has an answer |
| `app.py` | Frontend | Streamlit chat UI |

## What questions it can answer

Out of the box (and anything phrased similarly):
- "What's the team target for this month?"
- "Who's the top performer?"
- "Who's an average performer?"
- "Who reached their target?"
- "Who missed their target?" *(added — useful for coaching conversations)*
- "How is each region doing?" *(added — regional rollups)*
- "How is [rep name] doing?"
- "Show me the full leaderboard"

The agent can combine these too, e.g. "How far is the bottom performer from
target, and which region are they in?" — it will call more than one tool if
needed.

## Setup

**1. Install Ollama and pull a tool-calling capable model** (one-time):
```bash
# https://ollama.com/download
ollama pull llama3.1
ollama serve   # if not already running as a background service
```
Other good options: `qwen2.5`, `llama3.2`, `mistral-nemo` — anything with
function/tool-calling support in Ollama.

**2. Install Python dependencies:**
```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**3. Run the app:**
```bash
streamlit run app.py
```
Opens at http://localhost:8501

If you pulled a model other than `llama3.1`, set it before launching:
```bash
export OLLAMA_MODEL=qwen2.5
streamlit run app.py
```

## Testing pieces independently

```bash
python data_utils.py     # sanity-checks the analytics logic, no LLM needed
python mcp_server.py     # runs the MCP server standalone (Ctrl+C to quit)
```

## Extending it

- **More data**: just add rows to `data/sales_data.json` — everything else
  reads from it dynamically.
- **More tools**: add a function to `data_utils.py`, then expose it with a
  `@mcp.tool()` wrapper in `mcp_server.py`. No changes needed in `graph.py`
  — new tools are picked up automatically.
- **Multi-turn memory / persistence**: `graph.py` already supports passing
  message history between turns (`st.session_state.history` in `app.py`).
  For durability across restarts, add a LangGraph checkpointer.
- **Swap MCP transport**: this POC uses stdio (simplest, no server process
  to manage). For a shared/remote setup, switch `mcp_server.py` to
  `mcp.run(transport="streamable-http")` and update the connection config
  in `graph.py` accordingly.
