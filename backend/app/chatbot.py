from app.retrieval.retriever import retrieve_context
from app.llm.groq_client import generate_response, stream_response


def chat(query, history):
    """
    Non-streaming chat (kept for fallback/debug)
    """
    context = retrieve_context(query)
    return generate_response(query, context, history)


def chat_stream(query, history):
    """
    Streaming chat generator (token-by-token)
    """
    context = retrieve_context(query)

    # stream_response MUST yield tokens
    for token in stream_response(query, context, history):
        yield token
