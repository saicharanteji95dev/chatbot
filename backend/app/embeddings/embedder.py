
import os
from huggingface_hub import InferenceClient

# Use huggingface_hub SDK (handles URL routing automatically)
# Much more reliable than raw HTTP calls to the inference API
HF_TOKEN = os.getenv("HF_TOKEN", "")

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = InferenceClient(token=HF_TOKEN if HF_TOKEN else None)
    return _client


def embed_texts(texts):
    """
    Embed texts using HuggingFace Inference API via official SDK.
    Returns list of 384-dim vectors (same as local all-MiniLM-L6-v2).
    """
    client = _get_client()
    embeddings = []
    for text in texts:
        result = client.feature_extraction(
            text, model="sentence-transformers/all-MiniLM-L6-v2"
        )
        # Convert numpy array to list if needed
        vec = result.tolist() if hasattr(result, "tolist") else result
        # If 2D (tokens x hidden), mean-pool to get sentence embedding
        if isinstance(vec, list) and vec and isinstance(vec[0], list):
            vec = [sum(col) / len(col) for col in zip(*vec)]
        embeddings.append(vec)
    return embeddings
