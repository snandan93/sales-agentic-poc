"""Dependency-free execution metrics for LangChain-style messages."""


def summarize_trace(messages: list, elapsed_seconds: float) -> dict:
    """Build UI-safe observability metrics from one graph execution."""
    metrics = {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "llm_calls": 0,
        "tool_calls": 0,
        "tool_names": [],
        "elapsed_seconds": round(elapsed_seconds, 2),
    }
    for message in messages:
        message_type = getattr(message, "type", "")
        if message_type == "ai":
            metrics["llm_calls"] += 1
            usage = getattr(message, "usage_metadata", None) or {}
            response = getattr(message, "response_metadata", None) or {}
            input_tokens = usage.get("input_tokens", response.get("prompt_eval_count", 0)) or 0
            output_tokens = usage.get("output_tokens", response.get("eval_count", 0)) or 0
            metrics["input_tokens"] += input_tokens
            metrics["output_tokens"] += output_tokens
            metrics["total_tokens"] += usage.get("total_tokens", input_tokens + output_tokens) or 0
        elif message_type == "tool":
            metrics["tool_calls"] += 1
            name = getattr(message, "name", None) or "unknown_tool"
            metrics["tool_names"].append(name)
    return metrics
