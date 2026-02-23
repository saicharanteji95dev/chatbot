import os
from groq import Groq

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = Groq()
    return _client


def _load_system_prompt():
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "system_prompt.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read().strip()


_system_prompt = None


def _get_system_prompt():
    global _system_prompt
    if _system_prompt is None:
        _system_prompt = _load_system_prompt()
    return _system_prompt


# -------------------------
# NON-STREAMING RESPONSE
# -------------------------

def generate_response(query: str, context: str, history: list) -> str:

    messages = [
        {"role": "system", "content": _get_system_prompt()},
        {
            "role": "system",
            "content": f"Relevant i95Dev context:\n{context}"
        }
    ]

    for msg in history:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    messages.append({
        "role": "user",
        "content": query
    })

    completion = _get_client().chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.2
    )

    return completion.choices[0].message.content


# -------------------------
# STREAMING RESPONSE
# -------------------------

def stream_response(query: str, context: str, history: list):

    messages = [
        {"role": "system", "content": _get_system_prompt()},
        {
            "role": "system",
            "content": f"Relevant i95Dev context:\n{context}"
        }
    ]

    for msg in history:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    messages.append({
        "role": "user",
        "content": query
    })

    completion = _get_client().chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.2,
        stream=True
    )

    for chunk in completion:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
