
from sentence_transformers import SentenceTransformer

_model = None

def _get_model():
    global _model
    if _model is None:
        print("Loading SentenceTransformer model...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        print("Model loaded successfully.")
    return _model

def embed_texts(texts):
    return _get_model().encode(texts).tolist()
