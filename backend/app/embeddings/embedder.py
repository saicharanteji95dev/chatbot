
# Lazy-load everything — torch + sentence-transformers are huge (~2GB)
# Importing them at module level crashes Render free tier (512MB RAM)
_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def embed_texts(texts):
    return _get_model().encode(texts).tolist()
