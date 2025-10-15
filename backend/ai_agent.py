import re
from typing import Optional, List, Dict
from langchain_nvidia_ai_endpoints import ChatNVIDIA

# Define your available models
MODEL_CATALOG = {
    
    "nvidia_chatqa_8b": "nvidia/llama3-chatqa-1.5-8b",
    "bielik_11b_26": "speakleash/bielik-11b-v2.6-instruct",
    "bielik_11b_23": "speakleash/bielik-11b-v2.3-instruct",
    "chatglm3_6b": "thudm/chatglm3-6b",
    "meta_llama_405b": "meta/llama-3.1-405b-instruct",
    "breeze_7b": "mediatek/breeze-7b-instruct"
}



def sanitize_query(query: str) -> str:
    """
    Replace the reserved word 'context' with 'provided information' to avoid
    NVIDIA endpoint parsing errors.
    """
    return re.sub(r"\bcontext\b", "provided information", query, flags=re.IGNORECASE)


def choose_model(query: str) -> str:
    """
    Agentic model selection heuristics.
    Can be extended to more advanced intent detection.
    """
    q = query.lower()

    # Language hints
    if any(ch in q for ch in "ąćęłńóśźż"):
        return MODEL_CATALOG["bielik_11b_26"]
    if any('\u4e00' <= c <= '\u9fff' for c in q):
        return MODEL_CATALOG["breeze_7b"]

    # Intent routing
    if any(k in q for k in ["qa", "retrieval", "question answer", "document", "rag"]):
        return MODEL_CATALOG["nvidia_chatqa_70b"]

    if any(k in q for k in ["math", "reasoning", "logic", "code", "analysis"]):
        return MODEL_CATALOG["meta_llama_405b"]

    if any(k in q for k in ["chat", "assistant", "conversation", "talk", "discuss"]):
        return MODEL_CATALOG["chatglm3_6b"]

    # Default fallback
    return MODEL_CATALOG["nvidia_chatqa_8b"]


def choose_model_with_agent(query: str) -> str:
    """
    Uses a meta-agent to choose the best model for a given query.
    """
    model_options = "\n".join([f"- {name}: {path}" for name, path in MODEL_CATALOG.items()])
    
    prompt = f"""
You are an expert AI model router. Your task is to choose the best model to answer the following user query.
Here are the available models:
{model_options}

{descriptions}

Based on the user's query, which model would be the most appropriate?
User Query: "{query}"

Return only the name of the best model (e.g., "nvidia_chatqa_8b").
"""
    
    try:
        # Use a powerful model for the meta-agent
        meta_agent = ChatNVIDIA(model=MODEL_CATALOG["meta_llama_405b"])
        response = meta_agent.invoke(prompt)
        chosen_model_name = getattr(response, "content", str(response)).strip()
        print(f"Meta-agent chose model: {chosen_model_name}")
        # Validate the chosen model
        if chosen_model_name in MODEL_CATALOG:
            return MODEL_CATALOG[chosen_model_name]
        else:
            # Fallback to default if the model name is not valid
            return MODEL_CATALOG["nvidia_chatqa_8b"]
            
    except Exception as e:
        print(f"Meta-agent call failed: {e}")
        # Fallback to default model in case of an error
        return MODEL_CATALOG["nvidia_chatqa_8b"]


async def agent_respond(
    user_query: str,
    retrieved_docs: Optional[List[str]] = None,
    model: Optional[str] = None,
    agent_mode: bool = False
) -> Dict[str, str]:
    """
    Main AI agent wrapper.
    - user_query: the query from the user
    - retrieved_docs: optional list of RAG documents
    - model: optional explicit model override
    - agent_mode: if True, use agentic model selection
    Returns dict with keys: 'model_used', 'response'
    """
    # Step 1: sanitize query
    safe_query = sanitize_query(user_query)

    # Step 2: pick model
    model_id = choose_model_with_agent(safe_query) if agent_mode else (model or MODEL_CATALOG["nvidia_chatqa_70b"])

    # Step 3: build context
    context_text = ""
    if retrieved_docs:
        context_text = "\n".join(retrieved_docs)

    # Step 4: build prompt
    prompt = f"""
You are a helpful AI assistant. Use the following provided information to answer the user's question.
If the answer is not in the provided information, say you don't know.

Provided information:
{context_text}

Question: {safe_query}
"""

    # Step 5: call the LLM
    try:
        llm = ChatNVIDIA(model=model_id)
        response = llm.invoke(prompt)
        answer = getattr(response, "content", str(response))
    except Exception as e:
        answer = f"LLM call failed: {e}"

    return {"model_used": model_id, "response": answer}

descriptions = """
{
  "models": [
    {
      "id": "bielik_11b_26",
      "name": "Bielik-11B-v2.6-Instruct",
      "developer": "Speakleash",
      "parameters": 11000000000,
      "language": "Polish",
      "description": "Generative text model designed to process and understand the Polish language with high precision. Linear merge of Bielik-11B-v2.0-Instruct, v2.1-Instruct, and v2.2-Instruct. Ready for commercial/non-commercial use."
    },
    {
      "id": "bielik_11b_23",
      "name": "Bielik-11B-v2.3-Instruct",
      "developer": "Speakleash",
      "parameters": 11000000000,
      "language": "Polish",
      "description": "Generative text model designed to process and understand the Polish language with high precision. Linear merge of Bielik-11B-v2.0-Instruct, v2.1-Instruct, and v2.2-Instruct. Ready for commercial/non-commercial use."
    },
    {
      "id": "chatglm3_6b",
      "name": "ChatGLM3-6B",
      "developer": "Zhipu AI / Tsinghua KEG",
      "parameters": 6000000000,
      "language": "Multilingual",
      "description": "Open-source pre-trained dialogue model. Maintains smooth dialogue, low deployment threshold, diverse training dataset, and newly designed prompt format. Free for academic research; commercial use allowed after registration."
    },
    {
      "id": "meta_llama_405b",
      "name": "Meta Llama 3.1",
      "developer": "Meta",
      "parameters": "8B, 70B, 405B",
      "language": "Multilingual",
      "description": "Pretrained and instruction-tuned generative models optimized for multilingual dialogue use cases. Outperforms many open-source and closed chat models on industry benchmarks."
    },
    {
      "id": "nvidia_chatqa_8b",
      "name": "Llama3-ChatQA-1.5-8B",
      "developer": "NVIDIA",
      "parameters": 8000000000,
      "language": "English",
      "description": "Conversational question answering and retrieval-augmented generation (RAG). Built on Llama-3 base model with enhanced tabular and arithmetic capabilities."
    },
    {
      "id": "nvidia_chatqa_70b",
      "name": "Llama3-ChatQA-1.5-70B",
      "developer": "NVIDIA",
      "parameters": 70000000000,
      "language": "English",
      "description": "Conversational question answering and retrieval-augmented generation (RAG). Built on Llama-3 base model with enhanced tabular and arithmetic capabilities."
    },
    {
      "id": "breeze_7b",
      "name": "Breeze-7B-Instruct",
      "developer": "Mediatek",
      "parameters": 7000000000,
      "language": "English / Traditional Chinese",
      "description": "Derived from Breeze-7B-Base, suitable for commonly seen tasks. v1.0 release improves performance in both English and Traditional Chinese."
    }
  ]
}
"""
