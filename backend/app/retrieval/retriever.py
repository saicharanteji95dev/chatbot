from ..embeddings.embedder import embed_texts
from ..vectorstore.pinecone_client import query_embedding

DEBUG = True  # Turn off in production


def retrieve_context(query, top_k=4):
    # Generate query embedding
    query_vec = embed_texts([query])[0]

    # Query Pinecone
    results = query_embedding(query_vec, top_k)

    if DEBUG:
        print("\n" + "=" * 70)
        print(f"🔍 TOP {top_k} RETRIEVED CHUNKS FOR QUERY:")
        print(f"❓ {query}")
        print("=" * 70)

    contexts = []
    detected_services = set()

    for i, match in enumerate(results.get("matches", []), start=1):
        score = round(match.get("score", 0), 4)
        metadata = match.get("metadata", {})

        text = metadata.get("text", "")
        source = metadata.get("source", "N/A")
        service = metadata.get("service", "UNKNOWN")

        detected_services.add(service)
        contexts.append(text)

        if DEBUG:
            preview = text[:300].replace("\n", " ")
            print(f"\n📌 Rank #{i}")
            print(f"Score   : {score}")
            print(f"Service : {service}")
            print(f"Source  : {source}")
            print(f"Preview : {preview}...")

    if DEBUG and len(detected_services) > 1:
        print("\n⚠️ WARNING: Retrieved chunks span multiple services:")
        for svc in detected_services:
            print(f" - {svc}")

    if DEBUG:
        print("=" * 70 + "\n")

    return "\n".join(contexts)
