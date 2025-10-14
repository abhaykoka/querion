import re
from typing import Optional

# Simple model selection heuristics. Extend as needed.
def choose_model(query: str) -> str:
    q = (query or "").lower()

    # language hints
    if any(ch in q for ch in "ąćęłńóśźż"):
        return "speakleash/bielik-11b-v2.6-instruct"
    if any('\u4e00' <= c <= '\u9fff' for c in q):
        return "mediatek/breeze-7b-instruct"

    # intent routing
    if any(k in q for k in ["qa", "context", "retrieval", "question answer", "document", "rag"]):
        return "nvidia/llama3-chatqa-1.5-70b"

    if any(k in q for k in ["math", "reasoning", "logic", "code", "analysis"]):
        return "meta/llama-3.1-405b-instruct"

    if any(k in q for k in ["chat", "assistant", "conversation", "talk", "discuss"]):
        return "thudm/chatglm3-6b"

    # default
    return "nvidia/llama3-chatqa-1.5-8b"


async def handle_agent_query(query: str, model: Optional[str] = None, agent_mode: bool = False) -> dict:
    """
    Minimal wrapper: choose model if agent_mode=True and return the chosen model id.
    Replace with HTTP client calls to inference services if needed.
    """
    model_id = choose_model(query) if agent_mode else (model or "nvidia/llama3-chatqa-1.5-70b")
    # This wrapper does not call external APIs — main.py will still call ChatNVIDIA.
    return {"model_used": model_id}
