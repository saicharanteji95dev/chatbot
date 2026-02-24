
import os
import requests

# Use HuggingFace Inference API (free) instead of local sentence-transformers
# This avoids loading torch (~2GB) which doesn't fit in Render free tier (512MB)
HF_API_URL = "https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2"
HF_TOKEN = os.getenv("HF_TOKEN", "")


def embed_texts(texts):
    """
    Embed texts using HuggingFace Inference API.
    Returns the same 384-dim vectors as local all-MiniLM-L6-v2.
    """
    headers = {}
    if HF_TOKEN:
        headers["Authorization"] = f"Bearer {HF_TOKEN}"

    response = requests.post(
        HF_API_URL,
        headers=headers,
        json={"inputs": texts, "options": {"wait_for_model": True}},
        timeout=60,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"HuggingFace embedding API error {response.status_code}: {response.text}"
        )

    return response.json()
