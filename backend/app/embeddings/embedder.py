
from sentence_transformers import SentenceTransformer

# Lazy-load the model — only downloaded/loaded on first request
# This prevents blocking uvicorn's port binding on startup (Render fix)
_model = None

def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def embed_texts(texts):
    return _get_model().encode(texts).tolist()
