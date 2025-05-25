from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

vllm_api_base = "https://51.250.28.28:10000/gpb_gpt_hack_2025/v1"

llm = ChatOpenAI(
    model="leon-se/gemma-3-27b-it-FP8-Dynamic",
    openai_api_base=vllm_api_base,
    openai_api_key="EMPTY",
    temperature=0.7,
    max_tokens=512,
)

def _convert_history(history: list[dict]) -> list:
    converted = []
    for msg in history:
        role = msg["role"]
        content = msg["content"]
        if role == "system":
            converted.append(SystemMessage(content=content))
        elif role == "user":
            converted.append(HumanMessage(content=content))
        elif role == "assistant":
            converted.append(AIMessage(content=content))
    return converted

async def ask_llm(history: list[dict]) -> str:
    normalized_history = normalize_roles(history)
    messages = _convert_history(normalized_history)
    response = await llm.ainvoke(messages)
    if history[-1]["role"] != "user":
        print("Последнее сообщение не от пользователя. Не вызываем LLM.")
        return
    return response.content


def normalize_roles(messages: list[dict]) -> list[dict]:
    if not messages:
        return []

    normalized = [messages[0]]
    for msg in messages[1:]:
        if msg["role"] != normalized[-1]["role"]:
            normalized.append(msg)
    return normalized
